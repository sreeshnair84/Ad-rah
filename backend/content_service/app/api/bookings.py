"""
Booking Management API Endpoints
================================

This module provides API endpoints for booking ad slots:
- Booking creation and management
- Booking approval workflow
- Campaign management
- Content moderation queue
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import logging
import uuid

from app.models_ad_slots import (
    AdBooking, BookingCreateRequest, BookingUpdateRequest, BookingApprovalRequest,
    BookingSlotDetail, ContentModerationQueue, BookingStatus, PaymentStatus
)
from app.models import Permission
from app.auth_service import get_current_user
from app.rbac_service import rbac_service
from app.database_service import db_service

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])
logger = logging.getLogger(__name__)


# ==================== BOOKING CREATION & MANAGEMENT ====================

@router.post("/", response_model=Dict[str, Any])
async def create_booking(
    booking_request: BookingCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new ad slot booking"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "booking",
            "create"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to create bookings")

        # Verify user is from ADVERTISER company
        user_company = await db_service.get_record("companies", current_user.get("company_id"))
        if not user_company.success or user_company.data.get("type") != "ADVERTISER":
            raise HTTPException(status_code=403, detail="Only ADVERTISER companies can create bookings")

        # Verify ad slot exists and is available
        slot_result = await db_service.get_record("ad_slots", booking_request.ad_slot_id)
        if not slot_result.success:
            raise HTTPException(status_code=404, detail="Ad slot not found")

        slot = slot_result.data
        if slot.get("status") != "available":
            raise HTTPException(status_code=400, detail="Ad slot is not available for booking")

        # Verify content exists and belongs to user's company
        content_result = await db_service.get_record("content_meta", booking_request.content_id)
        if not content_result.success:
            raise HTTPException(status_code=404, detail="Content not found")

        content = content_result.data
        if content.get("owner_id") != current_user["id"]:
            # Check if content belongs to same company
            content_owner = await db_service.get_record("users", content.get("owner_id"))
            if (not content_owner.success or
                content_owner.data.get("company_id") != current_user.get("company_id")):
                raise HTTPException(status_code=403, detail="Content does not belong to your company")

        # Calculate total cost
        total_slots = len(booking_request.time_slots) * (booking_request.end_date - booking_request.start_date).days
        total_amount = total_slots * slot.get("base_price_per_slot", 0)

        if total_amount > booking_request.max_total_budget:
            raise HTTPException(status_code=400, detail="Total cost exceeds maximum budget")

        # Generate booking number
        booking_number = f"BK-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"

        # Create booking
        booking = AdBooking(
            booking_number=booking_number,
            advertiser_company_id=current_user["company_id"],
            host_company_id=slot["host_company_id"],
            ad_slot_id=booking_request.ad_slot_id,
            content_id=booking_request.content_id,
            start_date=booking_request.start_date,
            end_date=booking_request.end_date,
            total_slots_booked=total_slots,
            price_per_slot=slot.get("base_price_per_slot", 0),
            total_amount=total_amount,
            campaign_name=booking_request.campaign_name,
            campaign_description=booking_request.campaign_description,
            created_by=current_user["id"]
        )

        result = await db_service.create_record("bookings", booking.model_dump())
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to create booking: {result.error}")

        booking_id = result.data["id"]

        # Create individual slot details
        slot_details = []
        for single_date in _date_range(booking_request.start_date, booking_request.end_date):
            for time_slot in booking_request.time_slots:
                slot_detail = BookingSlotDetail(
                    booking_id=booking_id,
                    ad_slot_id=booking_request.ad_slot_id,
                    scheduled_date=single_date,
                    scheduled_time_slot=time_slot,
                    slot_rate=slot.get("base_price_per_slot", 0)
                )
                slot_detail_result = await db_service.create_record("booking_slot_details", slot_detail.model_dump())
                if slot_detail_result.success:
                    slot_details.append(slot_detail_result.data)

        # Add content to moderation queue
        background_tasks.add_task(
            _queue_content_for_moderation,
            booking_request.content_id,
            current_user["company_id"],
            booking_id
        )

        logger.info(f"Booking created: {booking_id} by user {current_user['id']}")

        response_data = result.data.copy()
        response_data["slot_details"] = slot_details
        response_data["message"] = "Booking created successfully. Content queued for moderation review."

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[Dict[str, Any]])
async def list_bookings(
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """List bookings (filtered by company for non-admin users)"""
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
            filters["start_date"] = {"$gte": start_date.isoformat()}
        if end_date:
            filters["end_date"] = {"$lte": end_date.isoformat()}

        result = await db_service.query_records("bookings", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve bookings")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing bookings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{booking_id}", response_model=Dict[str, Any])
async def get_booking(
    booking_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get booking details"""
    try:
        result = await db_service.get_record("bookings", booking_id)
        if not result.success:
            raise HTTPException(status_code=404, detail="Booking not found")

        booking = result.data

        # Check access permissions
        user_company_id = current_user.get("company_id")
        if (current_user.get("user_type") != "SUPER_USER" and
            booking.get("advertiser_company_id") != user_company_id and
            booking.get("host_company_id") != user_company_id):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get booking slot details
        slot_details_result = await db_service.query_records(
            "booking_slot_details",
            {"booking_id": booking_id}
        )

        if slot_details_result.success:
            booking["slot_details"] = slot_details_result.data

        return booking

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting booking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{booking_id}", response_model=Dict[str, Any])
async def update_booking(
    booking_id: str,
    booking_update: BookingUpdateRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Update booking details (only before approval)"""
    try:
        # Get current booking
        booking_result = await db_service.get_record("bookings", booking_id)
        if not booking_result.success:
            raise HTTPException(status_code=404, detail="Booking not found")

        booking = booking_result.data

        # Check permissions
        if booking.get("advertiser_company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Can only edit your own bookings")

        # Can only edit draft or pending bookings
        if booking.get("status") not in ["draft", "pending_approval"]:
            raise HTTPException(status_code=400, detail="Cannot edit booking in current status")

        # Update only provided fields
        update_data = {k: v for k, v in booking_update.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()

        result = await db_service.update_record("bookings", booking_id, update_data)
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to update booking: {result.error}")

        logger.info(f"Booking updated: {booking_id} by user {current_user['id']}")
        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating booking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== BOOKING APPROVAL WORKFLOW ====================

@router.get("/pending-approval", response_model=List[Dict[str, Any]])
async def list_pending_approvals(
    current_user: Dict = Depends(get_current_user)
):
    """List bookings pending approval (for HOST companies)"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "booking",
            "approve"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view pending approvals")

        # Filter by HOST company
        filters = {
            "host_company_id": current_user.get("company_id"),
            "status": "pending_approval"
        }

        result = await db_service.query_records("bookings", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve pending approvals")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing pending approvals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{booking_id}/approve", response_model=Dict[str, Any])
async def approve_booking(
    booking_id: str,
    approval_request: BookingApprovalRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Approve or reject a booking"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "booking",
            "approve"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to approve bookings")

        # Get booking
        booking_result = await db_service.get_record("bookings", booking_id)
        if not booking_result.success:
            raise HTTPException(status_code=404, detail="Booking not found")

        booking = booking_result.data

        # Check if user's company is the host
        if booking.get("host_company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Can only approve bookings for your locations")

        # Can only approve pending bookings
        if booking.get("status") != "pending_approval":
            raise HTTPException(status_code=400, detail="Booking is not pending approval")

        # Update booking status
        update_data = {
            "updated_at": datetime.utcnow(),
            "approved_by": current_user["id"],
            "approved_at": datetime.utcnow()
        }

        if approval_request.action == "approve":
            update_data["status"] = BookingStatus.APPROVED.value

            # Apply modifications if provided
            if approval_request.modified_price:
                # Recalculate total amount
                new_total = booking.get("total_slots_booked", 0) * approval_request.modified_price
                update_data["price_per_slot"] = approval_request.modified_price
                update_data["total_amount"] = new_total

        else:  # reject
            update_data["status"] = BookingStatus.REJECTED.value
            update_data["rejection_reason"] = approval_request.notes

        if approval_request.notes:
            update_data["approval_notes"] = approval_request.notes

        result = await db_service.update_record("bookings", booking_id, update_data)
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to update booking: {result.error}")

        logger.info(f"Booking {approval_request.action}d: {booking_id} by user {current_user['id']}")

        return {
            "message": f"Booking {approval_request.action}d successfully",
            "booking_id": booking_id,
            "status": update_data.get("status"),
            "notes": approval_request.notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving booking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== CONTENT MODERATION ====================

@router.get("/moderation/queue", response_model=List[Dict[str, Any]])
async def get_moderation_queue(
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """Get content moderation queue"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "content",
            "moderate"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view moderation queue")

        # Build filters
        filters = {}
        if priority:
            filters["priority"] = priority
        if status:
            filters["review_status"] = status

        result = await db_service.query_records("content_moderation_queue", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve moderation queue")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting moderation queue: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/moderation/{queue_id}/review", response_model=Dict[str, Any])
async def review_content(
    queue_id: str,
    action: str = Query(...),  # approve or reject
    notes: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """Review content in moderation queue"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "content",
            "review"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to review content")

        # Get moderation queue item
        queue_result = await db_service.get_record("content_moderation_queue", queue_id)
        if not queue_result.success:
            raise HTTPException(status_code=404, detail="Moderation queue item not found")

        queue_item = queue_result.data

        if queue_item.get("review_status") != "pending":
            raise HTTPException(status_code=400, detail="Content has already been reviewed")

        # Update queue item
        update_data = {
            "review_status": "approved" if action == "approve" else "rejected",
            "reviewer_id": current_user["id"],
            "review_notes": notes,
            "reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await db_service.update_record("content_moderation_queue", queue_id, update_data)
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to update review: {result.error}")

        # If content is approved, update associated booking status
        if action == "approve" and queue_item.get("booking_id"):
            await _update_booking_after_content_approval(queue_item["booking_id"])

        logger.info(f"Content {action}d: {queue_id} by reviewer {current_user['id']}")

        return {
            "message": f"Content {action}d successfully",
            "queue_id": queue_id,
            "status": update_data["review_status"],
            "notes": notes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== CAMPAIGN MANAGEMENT ====================

@router.get("/campaigns", response_model=List[Dict[str, Any]])
async def list_campaigns(
    status: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """List campaigns (grouped bookings)"""
    try:
        # Build filter for advertiser's bookings
        filters = {"advertiser_company_id": current_user.get("company_id")}
        if status:
            filters["status"] = status

        result = await db_service.query_records("bookings", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve campaigns")

        # Group by campaign name
        campaigns = {}
        for booking in result.data:
            campaign_name = booking.get("campaign_name", "Unnamed Campaign")
            if campaign_name not in campaigns:
                campaigns[campaign_name] = {
                    "campaign_name": campaign_name,
                    "total_bookings": 0,
                    "total_amount": 0,
                    "total_slots": 0,
                    "statuses": {},
                    "bookings": []
                }

            campaign = campaigns[campaign_name]
            campaign["total_bookings"] += 1
            campaign["total_amount"] += booking.get("total_amount", 0)
            campaign["total_slots"] += booking.get("total_slots_booked", 0)

            status = booking.get("status", "unknown")
            campaign["statuses"][status] = campaign["statuses"].get(status, 0) + 1
            campaign["bookings"].append(booking)

        return list(campaigns.values())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== HELPER FUNCTIONS ====================

def _date_range(start_date: date, end_date: date):
    """Generate range of dates"""
    current = start_date
    while current <= end_date:
        yield current
        current = date.fromordinal(current.toordinal() + 1)


async def _queue_content_for_moderation(content_id: str, company_id: str, booking_id: str):
    """Queue content for moderation review"""
    try:
        # Get content details
        content_result = await db_service.get_record("content_meta", content_id)
        if not content_result.success:
            logger.error(f"Content not found for moderation queue: {content_id}")
            return

        content = content_result.data

        # Create moderation queue entry
        queue_item = ContentModerationQueue(
            content_id=content_id,
            advertiser_company_id=company_id,
            booking_id=booking_id,
            content_title=content.get("title", "Untitled"),
            content_type=content.get("content_type", "unknown"),
            file_size_mb=content.get("size", 0) / (1024 * 1024),
            duration_seconds=content.get("duration_seconds"),
            priority="normal"
        )

        await db_service.create_record("content_moderation_queue", queue_item.model_dump())
        logger.info(f"Content queued for moderation: {content_id}")

    except Exception as e:
        logger.error(f"Error queuing content for moderation: {e}")


async def _update_booking_after_content_approval(booking_id: str):
    """Update booking status after content is approved"""
    try:
        # Update booking to pending approval status
        update_data = {
            "status": BookingStatus.PENDING_APPROVAL.value,
            "updated_at": datetime.utcnow()
        }

        await db_service.update_record("bookings", booking_id, update_data)
        logger.info(f"Booking updated to pending approval after content approval: {booking_id}")

    except Exception as e:
        logger.error(f"Error updating booking after content approval: {e}")