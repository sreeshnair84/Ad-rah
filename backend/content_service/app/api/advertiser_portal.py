#!/usr/bin/env python3
"""
Advertiser Portal API - Digital Signage Ad Slot Management System
API endpoints for advertisers to discover slots, book campaigns, and manage content
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.ad_slot_models import (
    SlotSearchQuery, SlotAvailability, Booking, BookingRequest, 
    BookingConfirmation, Campaign, Content, ContentUploadRequest,
    AnalyticsRequest, AnalyticsResponse, PaymentStatus
)
from app.auth_service import get_current_user, require_role
from app.database_service import db_service

router = APIRouter(prefix="/advertiser", tags=["Advertiser Portal"])


# ==============================
# SLOT DISCOVERY
# ==============================

@router.post("/slots/search", response_model=List[SlotAvailability])
async def search_ad_slots(
    search_query: SlotSearchQuery,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Search for available ad slots based on criteria"""
    
    # Build location filter
    location_filter = {"is_active": True, "accepts_advertising": True}
    
    if search_query.city:
        location_filter["city"] = {"$regex": search_query.city, "$options": "i"}
    if search_query.state:
        location_filter["state"] = search_query.state
    if search_query.venue_types:
        location_filter["venue_type"] = {"$in": search_query.venue_types}
    if search_query.categories:
        location_filter["category"] = {"$in": search_query.categories}
    
    # Get matching locations
    matching_locations = await db_service.locations.find(location_filter).to_list(None)
    location_ids = [loc["_id"] for loc in matching_locations]
    
    if not location_ids:
        return []
    
    # Build ad slot filter
    slot_filter = {
        "location_id": {"$in": location_ids},
        "status": "available"
    }
    
    # Price filter
    if search_query.max_price_per_slot:
        slot_filter["base_price_per_slot"] = {"$lte": float(search_query.max_price_per_slot)}
    
    # Get available ad slots
    ad_slots = await db_service.ad_slots.find(slot_filter).to_list(None)
    
    # For each slot, check availability and calculate pricing
    slot_availabilities = []
    for slot in ad_slots:
        # Check time availability
        available_times = await calculate_slot_availability(
            slot["_id"], 
            search_query.start_date, 
            search_query.end_date,
            search_query.days_of_week,
            search_query.hours_start,
            search_query.hours_end
        )
        
        if available_times:
            # Calculate dynamic pricing
            pricing = await calculate_dynamic_pricing(
                slot["_id"],
                search_query.start_date,
                search_query.end_date
            )
            
            # Content restrictions
            restrictions = {
                "allowed_content_types": slot.get("allowed_content_types", []),
                "content_categories": slot.get("content_categories", []),
                "blocked_categories": slot.get("blocked_categories", []),
                "content_rating_limit": slot.get("content_rating_limit", "PG"),
                "requires_approval": slot.get("requires_approval", True)
            }
            
            slot_availabilities.append(SlotAvailability(
                ad_slot=slot,
                available_times=available_times,
                pricing=pricing,
                restrictions=restrictions
            ))
    
    # Apply pagination
    start_idx = (search_query.page - 1) * search_query.limit
    end_idx = start_idx + search_query.limit
    
    return slot_availabilities[start_idx:end_idx]


async def calculate_slot_availability(
    slot_id: str, 
    start_date: Optional[datetime], 
    end_date: Optional[datetime],
    days_of_week: List[int],
    hours_start: Optional[datetime],
    hours_end: Optional[datetime]
) -> List[Dict]:
    """Calculate available time slots"""
    
    # Get existing bookings for the slot
    booking_filter = {
        "ad_slot_id": slot_id,
        "status": {"$in": ["approved", "confirmed", "active"]}
    }
    
    if start_date and end_date:
        booking_filter["$or"] = [
            {
                "start_time": {"$gte": start_date, "$lte": end_date}
            },
            {
                "end_time": {"$gte": start_date, "$lte": end_date}
            },
            {
                "start_time": {"$lte": start_date},
                "end_time": {"$gte": end_date}
            }
        ]
    
    existing_bookings = await db_service.bookings.find(booking_filter).to_list(None)
    
    # Get slot configuration
    slot = await db_service.ad_slots.find_one({"_id": slot_id})
    
    # Generate available time slots
    available_times = []
    
    # This is a simplified version - in production, you'd implement
    # sophisticated slot availability calculation
    if not existing_bookings:
        available_times.append({
            "start_time": start_date or datetime.utcnow() + timedelta(hours=1),
            "end_time": end_date or datetime.utcnow() + timedelta(days=30),
            "duration_seconds": slot.get("slot_duration_seconds", 30),
            "price": float(slot.get("base_price_per_slot", 10.00))
        })
    
    return available_times


async def calculate_dynamic_pricing(
    slot_id: str,
    start_date: Optional[datetime],
    end_date: Optional[datetime]
) -> Dict:
    """Calculate dynamic pricing based on demand, time, etc."""
    
    slot = await db_service.ad_slots.find_one({"_id": slot_id})
    base_price = float(slot.get("base_price_per_slot", 10.00))
    
    # Get demand metrics (simplified)
    recent_bookings = await db_service.bookings.find({
        "ad_slot_id": slot_id,
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
    }).to_list(None)
    
    demand_multiplier = 1.0
    if len(recent_bookings) > 5:
        demand_multiplier = 1.2
    elif len(recent_bookings) > 10:
        demand_multiplier = 1.5
    
    # Time-based pricing
    peak_multiplier = float(slot.get("peak_hour_multiplier", 1.0))
    weekend_multiplier = float(slot.get("weekend_multiplier", 1.0))
    
    return {
        "base_price": base_price,
        "demand_multiplier": demand_multiplier,
        "peak_hour_multiplier": peak_multiplier,
        "weekend_multiplier": weekend_multiplier,
        "estimated_price_range": {
            "min": base_price,
            "max": base_price * demand_multiplier * peak_multiplier * weekend_multiplier
        }
    }


@router.get("/slots/{slot_id}/details")
async def get_slot_details(
    slot_id: str,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Get detailed information about a specific ad slot"""
    
    slot = await db_service.ad_slots.find_one({"_id": slot_id})
    if not slot:
        raise HTTPException(status_code=404, detail="Ad slot not found")
    
    # Get location details
    location = await db_service.locations.find_one({"_id": slot["location_id"]})
    
    # Get device details
    device = await db_service.devices.find_one({"_id": slot["device_id"]})
    
    # Get recent performance analytics
    analytics = await db_service.analytics_aggregations.find({
        "location_id": slot["location_id"],
        "date": {"$gte": datetime.utcnow() - timedelta(days=30)}
    }).to_list(None)
    
    # Calculate average performance metrics
    avg_impressions = sum(a.get("total_impressions", 0) for a in analytics) / len(analytics) if analytics else 0
    avg_engagement = sum(a.get("engagement_score", 0) for a in analytics) / len(analytics) if analytics else 0
    
    return {
        "slot": slot,
        "location": location,
        "device": device,
        "performance_metrics": {
            "avg_daily_impressions": avg_impressions,
            "avg_engagement_score": avg_engagement,
            "foot_traffic_level": location.get("foot_traffic_level", "medium")
        },
        "pricing": await calculate_dynamic_pricing(slot_id, None, None)
    }


# ==============================
# BOOKING MANAGEMENT
# ==============================

@router.post("/bookings", response_model=BookingConfirmation)
async def create_booking(
    booking_request: BookingRequest,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Create a new booking request"""
    
    # Verify slot exists and is available
    slot = await db_service.ad_slots.find_one({"_id": booking_request.ad_slot_id})
    if not slot:
        raise HTTPException(status_code=404, detail="Ad slot not found")
    
    if slot.get("status") != "available":
        raise HTTPException(status_code=400, detail="Ad slot is not available")
    
    # Check for booking conflicts
    conflicts = await db_service.bookings.find({
        "ad_slot_id": booking_request.ad_slot_id,
        "status": {"$in": ["approved", "confirmed", "active"]},
        "$or": [
            {
                "start_time": {"$lte": booking_request.end_time},
                "end_time": {"$gte": booking_request.start_time}
            }
        ]
    }).to_list(None)
    
    if conflicts:
        raise HTTPException(status_code=409, detail="Time slot conflicts with existing booking")
    
    # Calculate pricing
    duration_minutes = (booking_request.end_time - booking_request.start_time).total_seconds() / 60
    base_price = float(slot.get("base_price_per_slot", 10.00))
    
    # Apply time-based multipliers
    final_price = base_price
    if booking_request.start_time.weekday() >= 5:  # Weekend
        final_price *= float(slot.get("weekend_multiplier", 1.0))
    
    if 9 <= booking_request.start_time.hour <= 17:  # Peak hours
        final_price *= float(slot.get("peak_hour_multiplier", 1.0))
    
    # Create booking
    booking_data = {
        "ad_slot_id": booking_request.ad_slot_id,
        "advertiser_company_id": current_user.company_id,
        "campaign_id": booking_request.campaign_id,
        "start_time": booking_request.start_time,
        "end_time": booking_request.end_time,
        "duration_seconds": int(duration_minutes * 60),
        "base_price": Decimal(str(base_price)),
        "final_price": Decimal(str(final_price)),
        "content_id": booking_request.content_id,
        "host_approval_required": slot.get("requires_approval", True),
        "is_recurring": booking_request.is_recurring,
        "created_by": current_user.id
    }
    
    booking = Booking(**booking_data)
    result = await db_service.bookings.insert_one(booking.dict())
    booking.id = str(result.inserted_id)
    
    # Handle recurring bookings
    if booking_request.is_recurring and booking_request.recurrence_type:
        # Create recurring rule
        recurring_rule = {
            "booking_id": booking.id,
            "recurrence_type": booking_request.recurrence_type,
            "recurrence_interval": booking_request.recurrence_interval or 1,
            "end_date": booking_request.end_recurrence_date
        }
        
        await db_service.recurring_slot_rules.insert_one(recurring_rule)
    
    # Determine next steps
    next_steps = []
    payment_required = True
    payment_deadline = datetime.utcnow() + timedelta(hours=24)
    
    if slot.get("requires_approval", True):
        next_steps.append("Awaiting host approval")
        payment_required = False  # Payment after approval
    else:
        next_steps.append("Payment required to confirm booking")
    
    if booking_request.content_id:
        content = await db_service.content.find_one({"_id": booking_request.content_id})
        if content and content.get("status") != "approved":
            next_steps.append("Content pending moderation approval")
    else:
        next_steps.append("Upload content for this booking")
    
    return BookingConfirmation(
        booking=booking,
        payment_required=payment_required,
        payment_amount=booking.final_price,
        payment_deadline=payment_deadline,
        next_steps=next_steps
    )


@router.get("/bookings", response_model=List[Dict])
async def get_advertiser_bookings(
    current_user = Depends(require_role(["advertiser", "admin"])),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get all bookings for the advertiser"""
    
    filter_query = {"advertiser_company_id": current_user.company_id}
    
    if status:
        filter_query["status"] = status
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        filter_query["start_time"] = date_filter
    
    bookings = await db_service.bookings.find(filter_query).to_list(None)
    
    # Enrich with slot and location details
    enriched_bookings = []
    for booking in bookings:
        slot = await db_service.ad_slots.find_one({"_id": booking["ad_slot_id"]})
        location = await db_service.locations.find_one({"_id": slot["location_id"]}) if slot else None
        
        content = None
        if booking.get("content_id"):
            content = await db_service.content.find_one({"_id": booking["content_id"]})
        
        enriched_bookings.append({
            "booking": Booking(**booking),
            "ad_slot": slot,
            "location": location,
            "content": content
        })
    
    return enriched_bookings


@router.put("/bookings/{booking_id}")
async def update_booking(
    booking_id: str,
    update_data: dict,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Update a booking (limited fields)"""
    
    # Verify booking ownership
    booking = await db_service.bookings.find_one({
        "_id": booking_id,
        "advertiser_company_id": current_user.company_id
    })
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Only allow certain fields to be updated
    allowed_updates = ["content_id", "special_instructions"]
    filtered_updates = {k: v for k, v in update_data.items() if k in allowed_updates}
    
    if not filtered_updates:
        raise HTTPException(status_code=400, detail="No valid updates provided")
    
    filtered_updates["updated_at"] = datetime.utcnow()
    
    await db_service.bookings.update_one(
        {"_id": booking_id},
        {"$set": filtered_updates}
    )
    
    return {"message": "Booking updated successfully"}


@router.delete("/bookings/{booking_id}")
async def cancel_booking(
    booking_id: str,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Cancel a booking"""
    
    # Verify booking ownership
    booking = await db_service.bookings.find_one({
        "_id": booking_id,
        "advertiser_company_id": current_user.company_id
    })
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if cancellation is allowed
    current_status = booking.get("status")
    if current_status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel booking in current status")
    
    # Check cancellation policy (24 hours before start time)
    if booking["start_time"] <= datetime.utcnow() + timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Cannot cancel booking less than 24 hours before start time")
    
    # Update booking status
    await db_service.bookings.update_one(
        {"_id": booking_id},
        {"$set": {
            "status": "cancelled",
            "updated_at": datetime.utcnow()
        }}
    )
    
    # TODO: Process refund based on cancellation policy
    # TODO: Free up the ad slot
    # TODO: Send notifications
    
    return {"message": "Booking cancelled successfully"}


# ==============================
# CAMPAIGN MANAGEMENT
# ==============================

@router.post("/campaigns", response_model=Campaign)
async def create_campaign(
    campaign_data: dict,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Create a new advertising campaign"""
    
    campaign_data["advertiser_company_id"] = current_user.company_id
    campaign_data["created_by"] = current_user.id
    
    campaign = Campaign(**campaign_data)
    result = await db_service.campaigns.insert_one(campaign.dict())
    campaign.id = str(result.inserted_id)
    
    return campaign


@router.get("/campaigns", response_model=List[Campaign])
async def get_campaigns(
    current_user = Depends(require_role(["advertiser", "admin"])),
    status: Optional[str] = Query(None)
):
    """Get all campaigns for the advertiser"""
    
    filter_query = {"advertiser_company_id": current_user.company_id}
    
    if status:
        filter_query["status"] = status
    
    campaigns = await db_service.campaigns.find(filter_query).to_list(None)
    return [Campaign(**campaign) for campaign in campaigns]


@router.get("/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(
    campaign_id: str,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Get a specific campaign"""
    
    campaign = await db_service.campaigns.find_one({
        "_id": campaign_id,
        "advertiser_company_id": current_user.company_id
    })
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return Campaign(**campaign)


@router.put("/campaigns/{campaign_id}", response_model=Campaign)
async def update_campaign(
    campaign_id: str,
    update_data: dict,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Update a campaign"""
    
    # Verify campaign ownership
    existing = await db_service.campaigns.find_one({
        "_id": campaign_id,
        "advertiser_company_id": current_user.company_id
    })
    
    if not existing:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db_service.campaigns.update_one(
        {"_id": campaign_id},
        {"$set": update_data}
    )
    
    updated_campaign = await db_service.campaigns.find_one({"_id": campaign_id})
    return Campaign(**updated_campaign)


# ==============================
# CONTENT MANAGEMENT
# ==============================

@router.post("/content/upload")
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    campaign_id: str = Form(None),
    categories: str = Form("[]"),  # JSON string
    tags: str = Form("[]"),  # JSON string
    content_rating: str = Form("G"),
    call_to_action: str = Form(None),
    landing_url: str = Form(None),
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Upload new content for ads"""
    
    import json
    import os
    from app.services.file_service import save_uploaded_file
    
    # Validate file type and size
    allowed_types = ["video/mp4", "video/mpeg", "image/jpeg", "image/png", "image/gif", "text/html"]
    max_size = 100 * 1024 * 1024  # 100MB
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    if file.size > max_size:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Save file
    file_path = await save_uploaded_file(file, "content")
    
    # Create content record
    content_data = {
        "advertiser_company_id": current_user.company_id,
        "campaign_id": campaign_id,
        "title": title,
        "description": description,
        "content_type": file.content_type,
        "file_path": file_path,
        "file_size": file.size,
        "categories": json.loads(categories),
        "tags": json.loads(tags),
        "content_rating": content_rating,
        "call_to_action": call_to_action,
        "landing_url": landing_url,
        "created_by": current_user.id
    }
    
    # Calculate duration for video content
    if file.content_type.startswith("video/"):
        # TODO: Extract video duration using ffmpeg or similar
        content_data["duration_seconds"] = 30  # Placeholder
    
    content = Content(**content_data)
    result = await db_service.content.insert_one(content.dict())
    content.id = str(result.inserted_id)
    
    # TODO: Trigger AI moderation process
    
    return {
        "content_id": content.id,
        "message": "Content uploaded successfully and submitted for moderation",
        "status": content.status
    }


@router.get("/content", response_model=List[Content])
async def get_advertiser_content(
    current_user = Depends(require_role(["advertiser", "admin"])),
    status: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None)
):
    """Get all content for the advertiser"""
    
    filter_query = {"advertiser_company_id": current_user.company_id}
    
    if status:
        filter_query["status"] = status
    if campaign_id:
        filter_query["campaign_id"] = campaign_id
    
    content_items = await db_service.content.find(filter_query).to_list(None)
    return [Content(**content) for content in content_items]


@router.get("/content/{content_id}", response_model=Content)
async def get_content(
    content_id: str,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Get a specific content item"""
    
    content = await db_service.content.find_one({
        "_id": content_id,
        "advertiser_company_id": current_user.company_id
    })
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return Content(**content)


# ==============================
# ANALYTICS AND REPORTING
# ==============================

@router.post("/analytics", response_model=AnalyticsResponse)
async def get_campaign_analytics(
    analytics_request: AnalyticsRequest,
    current_user = Depends(require_role(["advertiser", "admin"]))
):
    """Get analytics for advertiser campaigns and content"""
    
    # Get advertiser's campaigns and content
    campaigns = await db_service.campaigns.find({
        "advertiser_company_id": current_user.company_id
    }).to_list(None)
    
    campaign_ids = [c["_id"] for c in campaigns]
    
    # Filter analytics request to advertiser's data
    filter_query = {
        "advertiser_company_id": current_user.company_id,
        "date": {
            "$gte": analytics_request.start_date,
            "$lte": analytics_request.end_date
        }
    }
    
    if analytics_request.campaign_ids:
        # Verify campaign ownership
        requested_campaigns = [c for c in analytics_request.campaign_ids if c in campaign_ids]
        filter_query["campaign_id"] = {"$in": requested_campaigns}
    
    if analytics_request.content_ids:
        # Verify content ownership
        content_items = await db_service.content.find({
            "_id": {"$in": analytics_request.content_ids},
            "advertiser_company_id": current_user.company_id
        }).to_list(None)
        verified_content_ids = [c["_id"] for c in content_items]
        filter_query["content_id"] = {"$in": verified_content_ids}
    
    # Get analytics data
    analytics_data = await db_service.analytics_aggregations.find(filter_query).to_list(None)
    
    # Calculate summary metrics
    total_impressions = sum(a.get("total_impressions", 0) for a in analytics_data)
    total_plays = sum(a.get("total_plays", 0) for a in analytics_data)
    total_spend = sum(float(a.get("revenue_generated", 0)) for a in analytics_data)
    
    summary = {
        "total_impressions": total_impressions,
        "total_plays": total_plays,
        "total_spend": total_spend,
        "avg_completion_rate": sum(a.get("completion_rate", 0) for a in analytics_data) / len(analytics_data) if analytics_data else 0,
        "avg_engagement_score": sum(a.get("engagement_score", 0) for a in analytics_data) / len(analytics_data) if analytics_data else 0
    }
    
    # Group by time period
    time_series = []
    if analytics_request.aggregation == "daily":
        # Group by day
        daily_data = {}
        for item in analytics_data:
            date_key = item["date"].strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "date": date_key,
                    "impressions": 0,
                    "plays": 0,
                    "spend": 0,
                    "engagement": 0
                }
            daily_data[date_key]["impressions"] += item.get("total_impressions", 0)
            daily_data[date_key]["plays"] += item.get("total_plays", 0)
            daily_data[date_key]["spend"] += float(item.get("revenue_generated", 0))
            daily_data[date_key]["engagement"] += item.get("engagement_score", 0)
        
        time_series = list(daily_data.values())
    
    # Campaign breakdown
    campaign_breakdown = {}
    for campaign in campaigns:
        campaign_analytics = [a for a in analytics_data if a.get("campaign_id") == campaign["_id"]]
        campaign_breakdown[campaign["_id"]] = {
            "campaign_name": campaign["name"],
            "impressions": sum(a.get("total_impressions", 0) for a in campaign_analytics),
            "spend": sum(float(a.get("revenue_generated", 0)) for a in campaign_analytics),
            "engagement": sum(a.get("engagement_score", 0) for a in campaign_analytics) / len(campaign_analytics) if campaign_analytics else 0
        }
    
    return AnalyticsResponse(
        summary=summary,
        time_series=time_series,
        breakdowns={"campaigns": campaign_breakdown}
    )


@router.get("/analytics/performance")
async def get_performance_summary(
    current_user = Depends(require_role(["advertiser", "admin"])),
    days: int = Query(30, description="Number of days to look back")
):
    """Get performance summary for the advertiser"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get advertiser analytics
    analytics = await db_service.analytics_aggregations.find({
        "advertiser_company_id": current_user.company_id,
        "date": {"$gte": start_date}
    }).to_list(None)
    
    # Get active campaigns
    active_campaigns = await db_service.campaigns.find({
        "advertiser_company_id": current_user.company_id,
        "status": "active"
    }).to_list(None)
    
    # Get content moderation status
    content_items = await db_service.content.find({
        "advertiser_company_id": current_user.company_id
    }).to_list(None)
    
    content_status_counts = {}
    for content in content_items:
        status = content.get("status", "unknown")
        content_status_counts[status] = content_status_counts.get(status, 0) + 1
    
    # Calculate metrics
    total_impressions = sum(a.get("total_impressions", 0) for a in analytics)
    total_spend = sum(float(a.get("revenue_generated", 0)) for a in analytics)
    
    return {
        "period_days": days,
        "total_impressions": total_impressions,
        "total_spend": total_spend,
        "avg_cpm": (total_spend / total_impressions * 1000) if total_impressions > 0 else 0,
        "active_campaigns": len(active_campaigns),
        "content_status": content_status_counts,
        "recent_performance": analytics[-7:] if len(analytics) >= 7 else analytics  # Last 7 days
    }