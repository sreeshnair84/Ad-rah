"""
Billing and Invoicing API Endpoints
===================================

This module provides API endpoints for billing and financial management:
- Invoice generation and management
- Payment processing
- Revenue sharing and payouts
- Proof-of-play based billing
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
import logging
import uuid
from decimal import Decimal

from app.models_ad_slots import (
    Invoice, InvoiceLineItem, PaymentTransaction, HostPayout,
    InvoiceStatus, PaymentStatus, ProofOfPlayRequest
)
from app.models import Permission
from app.auth_service import get_current_user
from app.rbac_service import rbac_service
from app.database_service import db_service

router = APIRouter(prefix="/api/billing", tags=["Billing"])
logger = logging.getLogger(__name__)


# ==================== INVOICE MANAGEMENT ====================

@router.post("/invoices/generate", response_model=Dict[str, Any])
async def generate_invoices(
    billing_period_start: date = Query(...),
    billing_period_end: date = Query(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Dict = Depends(get_current_user)
):
    """Generate invoices for a billing period based on proof-of-play data"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "invoice",
            "create"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to generate invoices")

        logger.info(f"Generating invoices for period {billing_period_start} to {billing_period_end}")

        # Get all completed bookings in the period
        booking_filters = {
            "status": "active",
            "start_date": {"$lte": billing_period_end.isoformat()},
            "end_date": {"$gte": billing_period_start.isoformat()}
        }

        bookings_result = await db_service.query_records("bookings", booking_filters)
        if not bookings_result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve bookings")

        # Group bookings by advertiser company
        advertiser_bookings = {}
        for booking in bookings_result.data:
            advertiser_id = booking.get("advertiser_company_id")
            if advertiser_id not in advertiser_bookings:
                advertiser_bookings[advertiser_id] = []
            advertiser_bookings[advertiser_id].append(booking)

        generated_invoices = []

        # Generate invoice for each advertiser
        for advertiser_id, bookings in advertiser_bookings.items():
            invoice = await _generate_invoice_for_advertiser(
                advertiser_id,
                bookings,
                billing_period_start,
                billing_period_end,
                current_user["id"]
            )
            if invoice:
                generated_invoices.append(invoice)

        logger.info(f"Generated {len(generated_invoices)} invoices")

        # Queue background tasks
        for invoice in generated_invoices:
            background_tasks.add_task(_send_invoice_notification, invoice["id"])

        return {
            "message": f"Generated {len(generated_invoices)} invoices",
            "invoices": generated_invoices,
            "billing_period": {
                "start": billing_period_start.isoformat(),
                "end": billing_period_end.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating invoices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/invoices", response_model=List[Dict[str, Any]])
async def list_invoices(
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """List invoices (filtered by company for non-admin users)"""
    try:
        # Build filter
        filters = {}

        # Company isolation
        if current_user.get("user_type") != "SUPER_USER":
            user_company = await db_service.get_record("companies", current_user.get("company_id"))
            if user_company.success:
                company_type = user_company.data.get("type")
                if company_type == "ADVERTISER":
                    filters["advertiser_company_id"] = current_user.get("company_id")
                elif company_type == "HOST":
                    filters["host_company_id"] = current_user.get("company_id")

        if status:
            filters["status"] = status
        if start_date:
            filters["billing_period_start"] = {"$gte": start_date.isoformat()}
        if end_date:
            filters["billing_period_end"] = {"$lte": end_date.isoformat()}

        result = await db_service.query_records("invoices", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve invoices")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing invoices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/invoices/{invoice_id}", response_model=Dict[str, Any])
async def get_invoice(
    invoice_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get invoice details"""
    try:
        result = await db_service.get_record("invoices", invoice_id)
        if not result.success:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice = result.data

        # Check access permissions
        user_company_id = current_user.get("company_id")
        if (current_user.get("user_type") != "SUPER_USER" and
            invoice.get("advertiser_company_id") != user_company_id and
            invoice.get("host_company_id") != user_company_id):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get invoice line items
        line_items_result = await db_service.query_records(
            "invoice_line_items",
            {"invoice_id": invoice_id}
        )

        if line_items_result.success:
            invoice["line_items"] = line_items_result.data

        return invoice

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoice: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/invoices/{invoice_id}/send", response_model=Dict[str, Any])
async def send_invoice(
    invoice_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Send invoice to customer"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "invoice",
            "send"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to send invoices")

        # Get invoice
        invoice_result = await db_service.get_record("invoices", invoice_id)
        if not invoice_result.success:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice = invoice_result.data

        # Check if user can send this invoice
        user_company = await db_service.get_record("companies", current_user.get("company_id"))
        if (user_company.success and user_company.data.get("type") == "HOST" and
            invoice.get("host_company_id") != current_user.get("company_id")):
            raise HTTPException(status_code=403, detail="Can only send invoices for your locations")

        # Update invoice status
        update_data = {
            "status": InvoiceStatus.SENT.value,
            "issued_date": date.today().isoformat(),
            "updated_at": datetime.utcnow()
        }

        result = await db_service.update_record("invoices", invoice_id, update_data)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to update invoice")

        # Queue email sending
        background_tasks.add_task(_send_invoice_email, invoice_id)

        logger.info(f"Invoice sent: {invoice_id} by user {current_user['id']}")

        return {
            "message": "Invoice sent successfully",
            "invoice_id": invoice_id,
            "status": InvoiceStatus.SENT.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== PAYMENT PROCESSING ====================

@router.post("/payments/process", response_model=Dict[str, Any])
async def process_payment(
    invoice_id: str,
    payment_method: str,
    amount: float,
    gateway_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Process payment for an invoice"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "payment",
            "process"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to process payments")

        # Get invoice
        invoice_result = await db_service.get_record("invoices", invoice_id)
        if not invoice_result.success:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice = invoice_result.data

        # Check if user can pay this invoice (advertiser)
        if invoice.get("advertiser_company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Can only pay your own invoices")

        # Validate amount
        if amount < invoice.get("total_amount", 0):
            raise HTTPException(status_code=400, detail="Payment amount is less than invoice total")

        # Generate transaction number
        transaction_number = f"PAY-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"

        # Create payment transaction
        transaction = PaymentTransaction(
            transaction_number=transaction_number,
            invoice_id=invoice_id,
            amount=amount,
            payment_method=payment_method,
            payment_gateway=_get_gateway_from_method(payment_method),
            gateway_transaction_id=gateway_data.get("transaction_id", ""),
            gateway_response=gateway_data
        )

        # Process payment with gateway
        success, gateway_response = await _process_payment_with_gateway(
            payment_method,
            amount,
            gateway_data
        )

        if success:
            transaction.status = PaymentStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()

            # Update invoice status
            invoice_update = {
                "status": InvoiceStatus.PAID.value,
                "paid_date": date.today().isoformat(),
                "payment_method": payment_method,
                "payment_reference": transaction_number,
                "updated_at": datetime.utcnow()
            }
            await db_service.update_record("invoices", invoice_id, invoice_update)

            # Trigger host payout process
            await _trigger_host_payout(invoice)

        else:
            transaction.status = PaymentStatus.FAILED
            transaction.failed_at = datetime.utcnow()
            transaction.failure_reason = gateway_response.get("error", "Payment failed")

        # Save transaction
        transaction_result = await db_service.create_record("payment_transactions", transaction.model_dump())
        if not transaction_result.success:
            logger.error(f"Failed to save payment transaction: {transaction_result.error}")

        logger.info(f"Payment {'completed' if success else 'failed'}: {transaction_number}")

        return {
            "success": success,
            "transaction_number": transaction_number,
            "status": transaction.status.value,
            "message": "Payment completed successfully" if success else "Payment failed",
            "gateway_response": gateway_response
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/payments", response_model=List[Dict[str, Any]])
async def list_payments(
    invoice_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """List payment transactions"""
    try:
        # Build filter
        filters = {}

        if invoice_id:
            filters["invoice_id"] = invoice_id
        if status:
            filters["status"] = status

        # Date range filter
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date.isoformat()
            if end_date:
                date_filter["$lte"] = end_date.isoformat()
            filters["initiated_at"] = date_filter

        # Company isolation - get payments for invoices related to user's company
        if current_user.get("user_type") != "SUPER_USER":
            # First get invoices for user's company
            invoice_filters = {}
            user_company = await db_service.get_record("companies", current_user.get("company_id"))
            if user_company.success:
                company_type = user_company.data.get("type")
                if company_type == "ADVERTISER":
                    invoice_filters["advertiser_company_id"] = current_user.get("company_id")
                elif company_type == "HOST":
                    invoice_filters["host_company_id"] = current_user.get("company_id")

            invoices_result = await db_service.query_records("invoices", invoice_filters)
            if invoices_result.success:
                invoice_ids = [inv["id"] for inv in invoices_result.data]
                filters["invoice_id"] = {"$in": invoice_ids}

        result = await db_service.query_records("payment_transactions", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve payments")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing payments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== HOST PAYOUTS ====================

@router.post("/payouts/generate", response_model=Dict[str, Any])
async def generate_host_payouts(
    period_start: date = Query(...),
    period_end: date = Query(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Dict = Depends(get_current_user)
):
    """Generate payouts for host companies"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "payout",
            "process"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to process payouts")

        logger.info(f"Generating host payouts for period {period_start} to {period_end}")

        # Get all paid invoices in the period
        invoice_filters = {
            "status": InvoiceStatus.PAID.value,
            "paid_date": {
                "$gte": period_start.isoformat(),
                "$lte": period_end.isoformat()
            }
        }

        invoices_result = await db_service.query_records("invoices", invoice_filters)
        if not invoices_result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve paid invoices")

        # Group by host company
        host_invoices = {}
        for invoice in invoices_result.data:
            host_id = invoice.get("host_company_id")
            if host_id not in host_invoices:
                host_invoices[host_id] = []
            host_invoices[host_id].append(invoice)

        generated_payouts = []

        # Generate payout for each host
        for host_id, invoices in host_invoices.items():
            payout = await _generate_host_payout(
                host_id,
                invoices,
                period_start,
                period_end,
                current_user["id"]
            )
            if payout:
                generated_payouts.append(payout)

        logger.info(f"Generated {len(generated_payouts)} host payouts")

        return {
            "message": f"Generated {len(generated_payouts)} payouts",
            "payouts": generated_payouts,
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating payouts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/payouts", response_model=List[Dict[str, Any]])
async def list_payouts(
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """List host payouts"""
    try:
        # Build filter
        filters = {}

        # Company isolation for host companies
        if current_user.get("user_type") != "SUPER_USER":
            user_company = await db_service.get_record("companies", current_user.get("company_id"))
            if user_company.success and user_company.data.get("type") == "HOST":
                filters["host_company_id"] = current_user.get("company_id")

        if status:
            filters["status"] = status

        # Date range filter
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date.isoformat()
            if end_date:
                date_filter["$lte"] = end_date.isoformat()
            filters["period_start"] = date_filter

        result = await db_service.query_records("host_payouts", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve payouts")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing payouts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== PROOF OF PLAY REPORTS ====================

@router.post("/proof-of-play", response_model=Dict[str, Any])
async def generate_proof_of_play_report(
    request: ProofOfPlayRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Generate proof-of-play report"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "proof_of_play",
            "view"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view proof-of-play reports")

        # Build query filters
        filters = {
            "actual_start_time": {
                "$gte": request.start_date.isoformat(),
                "$lte": request.end_date.isoformat()
            }
        }

        if request.booking_ids:
            # Get booking slot details for these bookings
            slot_filters = {"booking_id": {"$in": request.booking_ids}}
            slot_result = await db_service.query_records("booking_slot_details", slot_filters)
            if slot_result.success:
                slot_ids = [slot["id"] for slot in slot_result.data]
                filters["booking_slot_detail_id"] = {"$in": slot_ids}

        # Get playback statistics
        stats_result = await db_service.query_records("playback_statistics", filters)
        if not stats_result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve playback statistics")

        # Generate report based on format
        if request.format == "pdf":
            report_url = await _generate_pdf_report(stats_result.data, request)
            return {
                "report_type": "proof_of_play",
                "format": "pdf",
                "download_url": report_url,
                "generated_at": datetime.utcnow().isoformat(),
                "total_records": len(stats_result.data)
            }
        elif request.format == "csv":
            report_url = await _generate_csv_report(stats_result.data, request)
            return {
                "report_type": "proof_of_play",
                "format": "csv",
                "download_url": report_url,
                "generated_at": datetime.utcnow().isoformat(),
                "total_records": len(stats_result.data)
            }
        else:  # json
            return {
                "report_type": "proof_of_play",
                "format": "json",
                "data": stats_result.data,
                "generated_at": datetime.utcnow().isoformat(),
                "total_records": len(stats_result.data)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating proof-of-play report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== HELPER FUNCTIONS ====================

async def _generate_invoice_for_advertiser(
    advertiser_id: str,
    bookings: List[Dict],
    period_start: date,
    period_end: date,
    created_by: str
) -> Optional[Dict]:
    """Generate invoice for an advertiser based on bookings"""
    try:
        # Get advertiser company info
        company_result = await db_service.get_record("companies", advertiser_id)
        if not company_result.success:
            return None

        company = company_result.data

        # Get all playback statistics for these bookings
        total_amount = 0.0
        line_items = []

        for booking in bookings:
            # Get booking slot details
            slot_details_result = await db_service.query_records(
                "booking_slot_details",
                {"booking_id": booking["id"]}
            )

            if not slot_details_result.success:
                continue

            # Calculate actual playback and billing
            for slot_detail in slot_details_result.data:
                # Get playback statistics
                stats_filters = {
                    "booking_slot_detail_id": slot_detail["id"],
                    "actual_start_time": {
                        "$gte": period_start.isoformat(),
                        "$lte": period_end.isoformat()
                    }
                }

                stats_result = await db_service.query_records("playback_statistics", stats_filters)
                if not stats_result.success:
                    continue

                # Calculate billable amount
                for stat in stats_result.data:
                    if stat.get("playback_status") == "success":
                        billable_amount = stat.get("revenue_generated", 0)
                        total_amount += billable_amount

            # Create line item for this booking
            line_item = InvoiceLineItem(
                invoice_id="",  # Will be set after invoice creation
                booking_id=booking["id"],
                description=f"Ad slots for {booking.get('campaign_name', 'Campaign')}",
                ad_slot_name=booking.get("ad_slot_name", "Ad Slot"),
                date_range=f"{period_start} to {period_end}",
                scheduled_slots=booking.get("total_slots_booked", 0),
                played_slots=len([s for s in stats_result.data if s.get("playback_status") == "success"]),
                rate_per_slot=booking.get("price_per_slot", 0),
                gross_amount=booking.get("total_amount", 0),
                net_amount=total_amount
            )
            line_items.append(line_item)

        if total_amount <= 0:
            return None  # No billable content

        # Generate invoice number
        invoice_number = f"INV-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"

        # Create invoice
        invoice = Invoice(
            invoice_number=invoice_number,
            advertiser_company_id=advertiser_id,
            host_company_id=bookings[0].get("host_company_id"),  # Assume same host for simplicity
            billing_period_start=period_start,
            billing_period_end=period_end,
            subtotal=total_amount,
            tax_amount=total_amount * 0.05,  # 5% VAT
            total_amount=total_amount * 1.05,
            payment_due_date=date.today() + timedelta(days=30),
            created_by=created_by
        )

        # Save invoice
        invoice_result = await db_service.create_record("invoices", invoice.model_dump())
        if not invoice_result.success:
            return None

        invoice_id = invoice_result.data["id"]

        # Save line items
        for line_item in line_items:
            line_item.invoice_id = invoice_id
            await db_service.create_record("invoice_line_items", line_item.model_dump())

        return invoice_result.data

    except Exception as e:
        logger.error(f"Error generating invoice for advertiser {advertiser_id}: {e}")
        return None


async def _generate_host_payout(
    host_id: str,
    invoices: List[Dict],
    period_start: date,
    period_end: date,
    created_by: str
) -> Optional[Dict]:
    """Generate payout for a host company"""
    try:
        # Calculate total revenue and platform commission
        gross_revenue = sum(invoice.get("total_amount", 0) for invoice in invoices)
        platform_commission = gross_revenue * 0.3  # Platform takes 30%
        net_payout = gross_revenue - platform_commission

        if net_payout <= 0:
            return None

        # Generate payout number
        payout_number = f"PO-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"

        # Create payout
        payout = HostPayout(
            payout_number=payout_number,
            host_company_id=host_id,
            period_start=period_start,
            period_end=period_end,
            gross_revenue=gross_revenue,
            platform_commission=platform_commission,
            net_payout=net_payout,
            invoice_ids=[inv["id"] for inv in invoices]
        )

        # Save payout
        payout_result = await db_service.create_record("host_payouts", payout.model_dump())
        return payout_result.data if payout_result.success else None

    except Exception as e:
        logger.error(f"Error generating payout for host {host_id}: {e}")
        return None


async def _process_payment_with_gateway(
    payment_method: str,
    amount: float,
    gateway_data: Dict[str, Any]
) -> tuple[bool, Dict[str, Any]]:
    """Process payment with payment gateway"""
    # This is a placeholder for actual payment gateway integration
    # In production, you would integrate with Stripe, PayPal, Razorpay, etc.

    try:
        if payment_method == "stripe":
            # Stripe integration
            return True, {"status": "succeeded", "transaction_id": "stripe_" + str(uuid.uuid4())[:8]}
        elif payment_method == "paypal":
            # PayPal integration
            return True, {"status": "completed", "transaction_id": "pp_" + str(uuid.uuid4())[:8]}
        else:
            return False, {"error": "Unsupported payment method"}
    except Exception as e:
        return False, {"error": str(e)}


def _get_gateway_from_method(payment_method: str) -> str:
    """Get gateway name from payment method"""
    mapping = {
        "stripe": "stripe",
        "paypal": "paypal",
        "razorpay": "razorpay",
        "bank_transfer": "manual"
    }
    return mapping.get(payment_method, "unknown")


async def _trigger_host_payout(invoice: Dict):
    """Trigger host payout when invoice is paid"""
    try:
        # This would trigger the host payout process
        # For now, just log it
        logger.info(f"Triggering host payout for invoice {invoice.get('id')}")
    except Exception as e:
        logger.error(f"Error triggering host payout: {e}")


async def _send_invoice_notification(invoice_id: str):
    """Send invoice notification (background task)"""
    try:
        logger.info(f"Sending invoice notification for {invoice_id}")
        # Implementation would send email/SMS notification
    except Exception as e:
        logger.error(f"Error sending invoice notification: {e}")


async def _send_invoice_email(invoice_id: str):
    """Send invoice via email (background task)"""
    try:
        logger.info(f"Sending invoice email for {invoice_id}")
        # Implementation would send invoice via email
    except Exception as e:
        logger.error(f"Error sending invoice email: {e}")


async def _generate_pdf_report(data: List[Dict], request: ProofOfPlayRequest) -> str:
    """Generate PDF report"""
    # Placeholder for PDF generation
    report_id = str(uuid.uuid4())
    return f"/api/reports/download/{report_id}.pdf"


async def _generate_csv_report(data: List[Dict], request: ProofOfPlayRequest) -> str:
    """Generate CSV report"""
    # Placeholder for CSV generation
    report_id = str(uuid.uuid4())
    return f"/api/reports/download/{report_id}.csv"