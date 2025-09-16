#!/usr/bin/env python3
"""
Billing & Invoicing API - Digital Signage Ad Slot Management System
API endpoints for automated billing, proof-of-play verification, and payment processing
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
import stripe

from app.models.ad_slot_models import (
    Invoice, InvoiceStatus, PaymentTransaction, PaymentStatus,
    PlaybackEvent, Booking, BookingStatus
)
from app.auth_service import get_current_user, require_role
from app.database_service import db_service

router = APIRouter(prefix="/billing", tags=["Billing & Invoicing"])

# Configure Stripe (would be in environment variables)
# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# ==============================
# PROOF-OF-PLAY VERIFICATION
# ==============================

@router.post("/proof-of-play/{booking_id}")
async def record_playback_event(
    booking_id: str,
    playback_data: dict,
    current_user = Depends(get_current_user)
):
    """Record a content playback event for billing verification"""
    
    booking = await db_service.bookings.find_one({"_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Verify device authorization
    device_id = playback_data.get("device_id")
    device = await db_service.devices.find_one({"_id": device_id})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Verify booking is active
    if booking.get("status") != BookingStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Booking is not active")
    
    # Verify playback is within booking time slot
    playback_time = datetime.fromisoformat(playback_data.get("played_at", datetime.utcnow().isoformat()))
    slot_start = booking["slot_start_time"]
    slot_end = booking["slot_end_time"]
    
    if not (slot_start <= playback_time <= slot_end):
        raise HTTPException(status_code=400, detail="Playback outside scheduled time slot")
    
    # Create playback event record
    playback_event = PlaybackEvent(
        booking_id=booking_id,
        content_id=booking["content_id"],
        device_id=device_id,
        location_id=device["location_id"],
        host_company_id=device["host_company_id"],
        advertiser_company_id=booking["advertiser_company_id"],
        played_at=playback_time,
        duration_seconds=playback_data.get("duration_seconds", 0),
        ad_slot_id=booking["ad_slot_id"],
        verification_hash=generate_verification_hash(playback_data),
        device_fingerprint=playback_data.get("device_fingerprint"),
        geolocation=playback_data.get("geolocation"),
        audience_count=playback_data.get("audience_count"),
        engagement_metrics=playback_data.get("engagement_metrics", {})
    )
    
    await db_service.playback_events.insert_one(playback_event.dict())
    
    # Update booking play count
    await db_service.bookings.update_one(
        {"_id": booking_id},
        {
            "$inc": {"actual_plays": 1},
            "$set": {"last_played_at": playback_time, "updated_at": datetime.utcnow()}
        }
    )
    
    # Check if billing threshold reached
    await check_billing_threshold(booking_id)
    
    return {
        "message": "Playback event recorded successfully",
        "event_id": str(playback_event.id),
        "verification_hash": playback_event.verification_hash
    }


def generate_verification_hash(playback_data: dict) -> str:
    """Generate cryptographic hash for playback verification"""
    import hashlib
    import json
    
    # Create deterministic hash from key playback data
    hash_data = {
        "device_id": playback_data.get("device_id"),
        "played_at": playback_data.get("played_at"),
        "duration": playback_data.get("duration_seconds"),
        "content_hash": playback_data.get("content_hash"),
        "timestamp": datetime.utcnow().timestamp()
    }
    
    hash_string = json.dumps(hash_data, sort_keys=True)
    return hashlib.sha256(hash_string.encode()).hexdigest()


async def check_billing_threshold(booking_id: str):
    """Check if booking has reached billing threshold and trigger invoice generation"""
    
    booking = await db_service.bookings.find_one({"_id": booking_id})
    if not booking:
        return
    
    # Get total plays for this booking
    total_plays = await db_service.playback_events.count_documents({"booking_id": booking_id})
    
    # Check if we should generate interim invoice (every 1000 plays or weekly)
    billing_frequency = booking.get("billing_frequency", "weekly")
    last_invoice_date = booking.get("last_invoice_date")
    
    should_invoice = False
    
    if billing_frequency == "per_play" and total_plays % 100 == 0:  # Every 100 plays
        should_invoice = True
    elif billing_frequency == "weekly":
        if not last_invoice_date or (datetime.utcnow() - last_invoice_date).days >= 7:
            should_invoice = True
    elif billing_frequency == "monthly":
        if not last_invoice_date or (datetime.utcnow() - last_invoice_date).days >= 30:
            should_invoice = True
    
    if should_invoice:
        await generate_invoice_for_booking(booking_id)


# ==============================
# INVOICE GENERATION
# ==============================

@router.post("/generate-invoice/{booking_id}")
async def generate_invoice_for_booking(
    booking_id: str,
    current_user = Depends(require_role(["admin", "host"]))
):
    """Generate invoice for a specific booking"""
    
    booking = await db_service.bookings.find_one({"_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Get playback events for billing period
    last_invoice_date = booking.get("last_invoice_date", booking["created_at"])
    current_date = datetime.utcnow()
    
    playback_events = await db_service.playback_events.find({
        "booking_id": booking_id,
        "played_at": {"$gte": last_invoice_date, "$lt": current_date}
    }).to_list(None)
    
    if not playback_events:
        return {"message": "No playback events to invoice"}
    
    # Calculate billing amounts
    billing_calculation = await calculate_billing_amount(booking, playback_events)
    
    # Get company information
    advertiser_company = await db_service.companies.find_one({"_id": booking["advertiser_company_id"]})
    host_company = await db_service.companies.find_one({"_id": booking["host_company_id"]})
    
    # Generate invoice
    invoice = Invoice(
        booking_id=booking_id,
        advertiser_company_id=booking["advertiser_company_id"],
        host_company_id=booking["host_company_id"],
        billing_period_start=last_invoice_date,
        billing_period_end=current_date,
        total_plays=len(playback_events),
        billable_plays=billing_calculation["billable_plays"],
        base_amount=billing_calculation["base_amount"],
        platform_fee=billing_calculation["platform_fee"],
        host_revenue_share=billing_calculation["host_revenue"],
        total_amount=billing_calculation["total_amount"],
        currency=booking.get("currency", "USD"),
        invoice_items=billing_calculation["line_items"],
        due_date=current_date + timedelta(days=30)
    )
    
    invoice_id = await db_service.invoices.insert_one(invoice.dict())
    
    # Update booking with invoice reference
    await db_service.bookings.update_one(
        {"_id": booking_id},
        {
            "$set": {
                "last_invoice_date": current_date,
                "updated_at": datetime.utcnow()
            },
            "$push": {"invoice_ids": str(invoice_id.inserted_id)}
        }
    )
    
    # TODO: Send invoice notification email
    # TODO: Integrate with accounting system
    
    return {
        "message": "Invoice generated successfully",
        "invoice_id": str(invoice_id.inserted_id),
        "total_amount": billing_calculation["total_amount"],
        "total_plays": len(playback_events),
        "billable_plays": billing_calculation["billable_plays"]
    }


async def calculate_billing_amount(booking: dict, playback_events: list) -> dict:
    """Calculate billing amounts based on playback events and booking terms"""
    
    # Get ad slot pricing information
    ad_slot = await db_service.ad_slots.find_one({"_id": booking["ad_slot_id"]})
    if not ad_slot:
        raise HTTPException(status_code=404, detail="Ad slot not found")
    
    # Base pricing model
    pricing_model = booking.get("pricing_model", "per_play")
    base_rate = Decimal(str(booking.get("price_per_play", ad_slot.get("base_price_per_play", 0.10))))
    
    # Calculate billable plays (exclude duplicate/invalid plays)
    billable_plays = len(playbook_events)  # TODO: Add fraud detection logic
    
    # Apply time-based pricing multipliers
    total_base_amount = Decimal('0')
    line_items = []
    
    for event in playback_events:
        event_rate = base_rate
        
        # Apply time-of-day multipliers
        play_hour = event["played_at"].hour
        if 6 <= play_hour <= 9:  # Morning rush
            event_rate *= Decimal('1.5')
        elif 17 <= play_hour <= 19:  # Evening rush
            event_rate *= Decimal('1.3')
        elif 22 <= play_hour or play_hour <= 5:  # Late night
            event_rate *= Decimal('0.7')
        
        # Apply day-of-week multipliers
        weekday = event["played_at"].weekday()
        if weekday >= 5:  # Weekend
            event_rate *= Decimal('1.2')
        
        # Apply audience-based multipliers
        audience_count = event.get("audience_count", 1)
        if audience_count > 10:
            event_rate *= Decimal('1.1')
        elif audience_count > 50:
            event_rate *= Decimal('1.2')
        
        total_base_amount += event_rate
        
        line_items.append({
            "event_id": str(event["_id"]),
            "played_at": event["played_at"].isoformat(),
            "base_rate": float(base_rate),
            "applied_rate": float(event_rate),
            "audience_count": audience_count,
            "amount": float(event_rate)
        })
    
    # Calculate platform fee (typically 10-15% of gross revenue)
    platform_fee_rate = Decimal('0.12')  # 12%
    platform_fee = total_base_amount * platform_fee_rate
    
    # Calculate host revenue share (typically 60-70% of net revenue)
    host_revenue_rate = Decimal('0.65')  # 65%
    net_revenue = total_base_amount - platform_fee
    host_revenue = net_revenue * host_revenue_rate
    
    return {
        "billable_plays": billable_plays,
        "base_amount": float(total_base_amount),
        "platform_fee": float(platform_fee),
        "host_revenue": float(host_revenue),
        "total_amount": float(total_base_amount),
        "line_items": line_items
    }


@router.get("/invoices")
async def get_invoices(
    current_user = Depends(get_current_user),
    company_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50)
):
    """Get invoices for a company"""
    
    # Build filter query
    filter_query = {}
    
    if current_user.role == "advertiser":
        filter_query["advertiser_company_id"] = current_user.company_id
    elif current_user.role == "host":
        filter_query["host_company_id"] = current_user.company_id
    elif current_user.role == "admin" and company_id:
        filter_query["$or"] = [
            {"advertiser_company_id": company_id},
            {"host_company_id": company_id}
        ]
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    if status:
        filter_query["status"] = status
    
    if start_date:
        filter_query["created_at"] = {"$gte": datetime.fromisoformat(start_date)}
    
    if end_date:
        if "created_at" not in filter_query:
            filter_query["created_at"] = {}
        filter_query["created_at"]["$lte"] = datetime.fromisoformat(end_date)
    
    invoices = await db_service.invoices.find(filter_query).sort([("created_at", -1)]).limit(limit).to_list(None)
    
    # Enrich with related data
    enriched_invoices = []
    for invoice in invoices:
        # Get booking information
        booking = await db_service.bookings.find_one({"_id": invoice["booking_id"]})
        
        # Get company information
        advertiser_company = await db_service.companies.find_one({"_id": invoice["advertiser_company_id"]})
        host_company = await db_service.companies.find_one({"_id": invoice["host_company_id"]})
        
        enriched_invoices.append({
            "invoice": Invoice(**invoice),
            "booking": booking,
            "advertiser_company": advertiser_company,
            "host_company": host_company
        })
    
    return {
        "invoices": enriched_invoices,
        "total": len(enriched_invoices)
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice_details(
    invoice_id: str,
    current_user = Depends(get_current_user)
):
    """Get detailed invoice information"""
    
    invoice = await db_service.invoices.find_one({"_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check access permissions
    if (current_user.role == "advertiser" and invoice["advertiser_company_id"] != current_user.company_id) or \
       (current_user.role == "host" and invoice["host_company_id"] != current_user.company_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get related data
    booking = await db_service.bookings.find_one({"_id": invoice["booking_id"]})
    advertiser_company = await db_service.companies.find_one({"_id": invoice["advertiser_company_id"]})
    host_company = await db_service.companies.find_one({"_id": invoice["host_company_id"]})
    
    # Get playback events for this billing period
    playback_events = await db_service.playback_events.find({
        "booking_id": invoice["booking_id"],
        "played_at": {
            "$gte": invoice["billing_period_start"],
            "$lt": invoice["billing_period_end"]
        }
    }).to_list(None)
    
    # Get payment transactions
    payment_transactions = await db_service.payment_transactions.find({
        "invoice_id": invoice_id
    }).to_list(None)
    
    return {
        "invoice": Invoice(**invoice),
        "booking": booking,
        "advertiser_company": advertiser_company,
        "host_company": host_company,
        "playback_events": playback_events,
        "payment_transactions": payment_transactions
    }


# ==============================
# PAYMENT PROCESSING
# ==============================

@router.post("/invoices/{invoice_id}/pay")
async def initiate_payment(
    invoice_id: str,
    payment_data: dict,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Initiate payment for an invoice"""
    
    invoice = await db_service.invoices.find_one({"_id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check payment eligibility
    if invoice.get("status") != InvoiceStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invoice is not payable")
    
    # Verify access
    if current_user.role == "advertiser" and invoice["advertiser_company_id"] != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    payment_method = payment_data.get("payment_method", "stripe")
    
    try:
        if payment_method == "stripe":
            payment_result = await process_stripe_payment(invoice, payment_data)
        elif payment_method == "paypal":
            payment_result = await process_paypal_payment(invoice, payment_data)
        else:
            raise HTTPException(status_code=400, detail="Unsupported payment method")
        
        # Create payment transaction record
        transaction = PaymentTransaction(
            invoice_id=invoice_id,
            advertiser_company_id=invoice["advertiser_company_id"],
            amount=invoice["total_amount"],
            currency=invoice["currency"],
            payment_method=payment_method,
            payment_processor_id=payment_result["transaction_id"],
            payment_intent_id=payment_result.get("payment_intent_id"),
            status=PaymentStatus.PROCESSING if payment_result["requires_confirmation"] else PaymentStatus.COMPLETED,
            payment_metadata=payment_result.get("metadata", {})
        )
        
        transaction_id = await db_service.payment_transactions.insert_one(transaction.dict())
        
        # Update invoice status
        if not payment_result["requires_confirmation"]:
            await db_service.invoices.update_one(
                {"_id": invoice_id},
                {
                    "$set": {
                        "status": InvoiceStatus.PAID,
                        "paid_at": datetime.utcnow(),
                        "payment_transaction_id": str(transaction_id.inserted_id),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Trigger revenue distribution
            await distribute_revenue(invoice_id)
        
        return {
            "message": "Payment initiated successfully",
            "transaction_id": str(transaction_id.inserted_id),
            "payment_status": transaction.status,
            "requires_confirmation": payment_result["requires_confirmation"],
            "confirmation_url": payment_result.get("confirmation_url")
        }
    
    except Exception as e:
        # Log payment error
        await db_service.payment_transactions.insert_one({
            "invoice_id": invoice_id,
            "advertiser_company_id": invoice["advertiser_company_id"],
            "amount": invoice["total_amount"],
            "currency": invoice["currency"],
            "payment_method": payment_method,
            "status": PaymentStatus.FAILED,
            "error_message": str(e),
            "created_at": datetime.utcnow()
        })
        
        raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")


async def process_stripe_payment(invoice: dict, payment_data: dict) -> dict:
    """Process payment via Stripe"""
    
    try:
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(invoice["total_amount"] * 100),  # Convert to cents
            currency=invoice["currency"].lower(),
            payment_method=payment_data.get("payment_method_id"),
            confirm=True,
            description=f"Invoice payment for booking {invoice['booking_id']}",
            metadata={
                "invoice_id": str(invoice["_id"]),
                "company_id": invoice["advertiser_company_id"]
            }
        )
        
        return {
            "transaction_id": intent.id,
            "payment_intent_id": intent.id,
            "requires_confirmation": intent.status == "requires_confirmation",
            "confirmation_url": intent.next_action.redirect_to_url.url if intent.next_action else None,
            "metadata": {"stripe_intent": intent.id}
        }
    
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe payment failed: {str(e)}")


async def process_paypal_payment(invoice: dict, payment_data: dict) -> dict:
    """Process payment via PayPal"""
    
    # TODO: Implement PayPal payment processing
    # This would integrate with PayPal's REST API
    
    return {
        "transaction_id": f"paypal_{datetime.utcnow().timestamp()}",
        "requires_confirmation": True,
        "confirmation_url": "https://www.paypal.com/checkout/...",
        "metadata": {"paypal_order": "ORDER_ID"}
    }


async def distribute_revenue(invoice_id: str):
    """Distribute revenue to host company after successful payment"""
    
    invoice = await db_service.invoices.find_one({"_id": invoice_id})
    if not invoice:
        return
    
    # Create revenue distribution record
    host_payout_amount = invoice["host_revenue_share"]
    
    # TODO: Integrate with payment processor for automatic payouts
    # TODO: Create payout transaction record
    # TODO: Update host company balance
    # TODO: Send payout notification
    
    # For now, just log the revenue distribution
    await db_service.revenue_distributions.insert_one({
        "invoice_id": invoice_id,
        "host_company_id": invoice["host_company_id"],
        "payout_amount": host_payout_amount,
        "currency": invoice["currency"],
        "status": "pending",
        "created_at": datetime.utcnow()
    })


# ==============================
# BILLING ANALYTICS
# ==============================

@router.get("/analytics/revenue")
async def get_revenue_analytics(
    current_user = Depends(get_current_user),
    period: str = Query("month"),  # week, month, quarter, year
    company_id: Optional[str] = Query(None)
):
    """Get revenue analytics for a company or system-wide"""
    
    # Determine date range
    end_date = datetime.utcnow()
    if period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    elif period == "year":
        start_date = end_date - timedelta(days=365)
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    # Build filter query
    filter_query = {
        "created_at": {"$gte": start_date, "$lte": end_date},
        "status": InvoiceStatus.PAID
    }
    
    if current_user.role == "advertiser":
        filter_query["advertiser_company_id"] = current_user.company_id
    elif current_user.role == "host":
        filter_query["host_company_id"] = current_user.company_id
    elif company_id and current_user.role == "admin":
        filter_query["$or"] = [
            {"advertiser_company_id": company_id},
            {"host_company_id": company_id}
        ]
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get invoices
    invoices = await db_service.invoices.find(filter_query).to_list(None)
    
    # Calculate metrics
    total_revenue = sum(invoice["total_amount"] for invoice in invoices)
    total_platform_fees = sum(invoice["platform_fee"] for invoice in invoices)
    total_host_revenue = sum(invoice["host_revenue_share"] for invoice in invoices)
    total_plays = sum(invoice["total_plays"] for invoice in invoices)
    
    # Revenue by day
    daily_revenue = {}
    for invoice in invoices:
        date_key = invoice["created_at"].strftime("%Y-%m-%d")
        daily_revenue[date_key] = daily_revenue.get(date_key, 0) + invoice["total_amount"]
    
    # Revenue by company (for admin view)
    company_revenue = {}
    if current_user.role == "admin":
        for invoice in invoices:
            company_id = invoice["advertiser_company_id"]
            company_revenue[company_id] = company_revenue.get(company_id, 0) + invoice["total_amount"]
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_revenue": total_revenue,
        "total_platform_fees": total_platform_fees,
        "total_host_revenue": total_host_revenue,
        "total_plays": total_plays,
        "average_revenue_per_play": total_revenue / total_plays if total_plays > 0 else 0,
        "daily_revenue": daily_revenue,
        "company_revenue": company_revenue if current_user.role == "admin" else None
    }


@router.get("/analytics/payment-trends")
async def get_payment_trends(
    current_user = Depends(require_role(["admin"])),
    days: int = Query(30)
):
    """Get payment processing trends and metrics (admin only)"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get payment transactions
    transactions = await db_service.payment_transactions.find({
        "created_at": {"$gte": start_date}
    }).to_list(None)
    
    # Calculate metrics
    total_transactions = len(transactions)
    successful_transactions = len([t for t in transactions if t.get("status") == "completed"])
    failed_transactions = len([t for t in transactions if t.get("status") == "failed"])
    
    success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
    
    # Payment method breakdown
    payment_methods = {}
    for transaction in transactions:
        method = transaction.get("payment_method", "unknown")
        payment_methods[method] = payment_methods.get(method, 0) + 1
    
    # Daily transaction volume
    daily_volume = {}
    for transaction in transactions:
        date_key = transaction["created_at"].strftime("%Y-%m-%d")
        if date_key not in daily_volume:
            daily_volume[date_key] = {"count": 0, "amount": 0}
        daily_volume[date_key]["count"] += 1
        daily_volume[date_key]["amount"] += transaction.get("amount", 0)
    
    return {
        "period_days": days,
        "total_transactions": total_transactions,
        "successful_transactions": successful_transactions,
        "failed_transactions": failed_transactions,
        "success_rate": success_rate,
        "payment_methods": payment_methods,
        "daily_volume": daily_volume
    }


# ==============================
# AUTOMATED BILLING WORKFLOWS
# ==============================

@router.post("/automation/run-billing-cycle")
async def run_automated_billing_cycle(
    background_tasks: BackgroundTasks,
    current_user = Depends(require_role(["admin"]))
):
    """Run automated billing cycle for all active bookings"""
    
    background_tasks.add_task(process_billing_cycle)
    
    return {"message": "Automated billing cycle initiated"}


async def process_billing_cycle():
    """Process billing for all eligible bookings"""
    
    # Get all active bookings that need billing
    current_time = datetime.utcnow()
    
    # Find bookings that need weekly billing
    weekly_bookings = await db_service.bookings.find({
        "status": BookingStatus.ACTIVE,
        "billing_frequency": "weekly",
        "$or": [
            {"last_invoice_date": {"$lte": current_time - timedelta(days=7)}},
            {"last_invoice_date": {"$exists": False}}
        ]
    }).to_list(None)
    
    # Find bookings that need monthly billing
    monthly_bookings = await db_service.bookings.find({
        "status": BookingStatus.ACTIVE,
        "billing_frequency": "monthly",
        "$or": [
            {"last_invoice_date": {"$lte": current_time - timedelta(days=30)}},
            {"last_invoice_date": {"$exists": False}}
        ]
    }).to_list(None)
    
    all_bookings = weekly_bookings + monthly_bookings
    
    # Process each booking
    for booking in all_bookings:
        try:
            await generate_invoice_for_booking(booking["_id"])
        except Exception as e:
            # Log billing error but continue with other bookings
            print(f"Billing error for booking {booking['_id']}: {str(e)}")
    
    return f"Processed billing for {len(all_bookings)} bookings"