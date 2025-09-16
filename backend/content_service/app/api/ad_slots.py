"""
Ad Slot Management API Endpoints
================================

This module provides API endpoints for managing ad slot inventory:
- Location management
- Device registration and management
- Ad slot creation and pricing
- Slot availability tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
import logging

from app.models_ad_slots import (
    Location, LocationCreate, Device, DeviceCreate,
    AdSlot, AdSlotCreate, AdSlotUpdate, AdSlotAvailability,
    AdSlotSearchRequest, AdSlotSearchResponse
)
from app.models import Permission
from app.auth_service import get_current_user
from app.rbac_service import rbac_service
from app.database_service import db_service

router = APIRouter(prefix="/api/ad-slots", tags=["Ad Slots"])
logger = logging.getLogger(__name__)


# ==================== LOCATION MANAGEMENT ====================

@router.post("/locations", response_model=Dict[str, Any])
async def create_location(
    location_data: LocationCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new location for hosting ad slots"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "location",
            "create"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to create locations")

        # Verify user is from HOST company
        user_company = await db_service.get_record("companies", current_user.get("company_id"))
        if not user_company.success or user_company.data.get("type") != "HOST":
            raise HTTPException(status_code=403, detail="Only HOST companies can create locations")

        # Create location
        location = Location(
            **location_data.model_dump(),
            host_company_id=current_user["company_id"]
        )

        result = await db_service.create_record("locations", location.model_dump())
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to create location: {result.error}")

        logger.info(f"Location created: {result.data['id']} by user {current_user['id']}")
        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/locations", response_model=List[Dict[str, Any]])
async def list_locations(
    city: Optional[str] = Query(None),
    venue_type: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """List locations (filtered by company for non-admin users)"""
    try:
        # Build filter
        filters = {"status": "active"}

        # Company isolation (non-super users see only their company's locations)
        if current_user.get("user_type") != "SUPER_USER":
            filters["host_company_id"] = current_user.get("company_id")

        if city:
            filters["city"] = {"$regex": city, "$options": "i"}
        if venue_type:
            filters["venue_type"] = venue_type

        result = await db_service.query_records("locations", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve locations")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing locations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/locations/{location_id}", response_model=Dict[str, Any])
async def get_location(
    location_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get location details"""
    try:
        result = await db_service.get_record("locations", location_id)
        if not result.success:
            raise HTTPException(status_code=404, detail="Location not found")

        location = result.data

        # Check access permissions
        if (current_user.get("user_type") != "SUPER_USER" and
            location.get("host_company_id") != current_user.get("company_id")):
            raise HTTPException(status_code=403, detail="Access denied")

        return location

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== DEVICE MANAGEMENT ====================

@router.post("/devices", response_model=Dict[str, Any])
async def register_device(
    device_data: DeviceCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Register a new device for ad display"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "device",
            "create"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to register devices")

        # Verify location exists and belongs to user's company
        location_result = await db_service.get_record("locations", device_data.location_id)
        if not location_result.success:
            raise HTTPException(status_code=404, detail="Location not found")

        location = location_result.data
        if location.get("host_company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Location does not belong to your company")

        # Generate API key for device
        import secrets
        api_key = secrets.token_urlsafe(32)
        registration_key = secrets.token_urlsafe(16)

        # Create device
        device = Device(
            **device_data.model_dump(),
            host_company_id=current_user["company_id"],
            api_key=api_key,
            registration_key=registration_key
        )

        result = await db_service.create_record("devices", device.model_dump())
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to register device: {result.error}")

        # Remove sensitive keys from response
        response_data = result.data.copy()
        response_data.pop("api_key", None)

        logger.info(f"Device registered: {result.data['id']} by user {current_user['id']}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/devices", response_model=List[Dict[str, Any]])
async def list_devices(
    location_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """List devices (filtered by company for non-admin users)"""
    try:
        # Build filter
        filters = {}

        # Company isolation
        if current_user.get("user_type") != "SUPER_USER":
            filters["host_company_id"] = current_user.get("company_id")

        if location_id:
            filters["location_id"] = location_id
        if status:
            filters["status"] = status

        result = await db_service.query_records("devices", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve devices")

        # Remove sensitive information
        devices = []
        for device in result.data:
            safe_device = device.copy()
            safe_device.pop("api_key", None)
            devices.append(safe_device)

        return devices

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== AD SLOT MANAGEMENT ====================

@router.post("/slots", response_model=Dict[str, Any])
async def create_ad_slot(
    slot_data: AdSlotCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new ad slot"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "slot",
            "create"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to create ad slots")

        # Verify device exists and belongs to user's company
        device_result = await db_service.get_record("devices", slot_data.device_id)
        if not device_result.success:
            raise HTTPException(status_code=404, detail="Device not found")

        device = device_result.data
        if device.get("host_company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Device does not belong to your company")

        # Verify location
        location_result = await db_service.get_record("locations", slot_data.location_id)
        if not location_result.success:
            raise HTTPException(status_code=404, detail="Location not found")

        # Generate unique slot code
        slot_code = f"{location_result.data.get('name', 'LOC')[:3].upper()}-{device.get('name', 'DEV')[:3].upper()}-{slot_data.slot_name[:3].upper()}-{datetime.now().strftime('%H%M')}"

        # Create ad slot
        ad_slot = AdSlot(
            **slot_data.model_dump(),
            host_company_id=current_user["company_id"],
            slot_code=slot_code
        )

        result = await db_service.create_record("ad_slots", ad_slot.model_dump())
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to create ad slot: {result.error}")

        logger.info(f"Ad slot created: {result.data['id']} by user {current_user['id']}")
        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ad slot: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/slots", response_model=List[Dict[str, Any]])
async def list_ad_slots(
    location_id: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """List ad slots (filtered by company for non-admin users)"""
    try:
        # Build filter
        filters = {}

        # Company isolation for non-super users
        if current_user.get("user_type") != "SUPER_USER":
            filters["host_company_id"] = current_user.get("company_id")

        if location_id:
            filters["location_id"] = location_id
        if device_id:
            filters["device_id"] = device_id
        if status:
            filters["status"] = status

        result = await db_service.query_records("ad_slots", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve ad slots")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing ad slots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/slots/{slot_id}", response_model=Dict[str, Any])
async def get_ad_slot(
    slot_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get ad slot details"""
    try:
        result = await db_service.get_record("ad_slots", slot_id)
        if not result.success:
            raise HTTPException(status_code=404, detail="Ad slot not found")

        slot = result.data

        # Check access permissions
        if (current_user.get("user_type") != "SUPER_USER" and
            slot.get("host_company_id") != current_user.get("company_id")):
            raise HTTPException(status_code=403, detail="Access denied")

        return slot

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ad slot: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/slots/{slot_id}", response_model=Dict[str, Any])
async def update_ad_slot(
    slot_id: str,
    slot_update: AdSlotUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update ad slot details"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "slot",
            "edit"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to edit ad slots")

        # Get current slot
        slot_result = await db_service.get_record("ad_slots", slot_id)
        if not slot_result.success:
            raise HTTPException(status_code=404, detail="Ad slot not found")

        slot = slot_result.data

        # Check ownership
        if slot.get("host_company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Ad slot does not belong to your company")

        # Update only provided fields
        update_data = {k: v for k, v in slot_update.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()

        result = await db_service.update_record("ad_slots", slot_id, update_data)
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to update ad slot: {result.error}")

        logger.info(f"Ad slot updated: {slot_id} by user {current_user['id']}")
        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ad slot: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== SLOT DISCOVERY & SEARCH ====================

@router.post("/slots/search", response_model=AdSlotSearchResponse)
async def search_ad_slots(
    search_request: AdSlotSearchRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Search for available ad slots (for advertisers)"""
    try:
        # Build search filters
        filters = {
            "status": "available"
        }

        # Location filters
        if search_request.city:
            # Join with locations collection to filter by city
            location_filters = {"city": {"$regex": search_request.city, "$options": "i"}}
            location_result = await db_service.query_records("locations", location_filters)
            if location_result.success:
                location_ids = [loc["id"] for loc in location_result.data]
                filters["location_id"] = {"$in": location_ids}
            else:
                # No matching locations, return empty result
                return AdSlotSearchResponse(
                    slots=[],
                    total_count=0,
                    total_pages=0,
                    current_page=search_request.page,
                    price_range={"min": 0, "max": 0},
                    total_impressions=0,
                    average_engagement_rate=0.0
                )

        if search_request.venue_types:
            location_filters = {"venue_type": {"$in": search_request.venue_types}}
            location_result = await db_service.query_records("locations", location_filters)
            if location_result.success:
                location_ids = [loc["id"] for loc in location_result.data]
                if "location_id" in filters:
                    # Intersection of location filters
                    existing_ids = filters["location_id"]["$in"]
                    filters["location_id"]["$in"] = list(set(location_ids) & set(existing_ids))
                else:
                    filters["location_id"] = {"$in": location_ids}

        # Price filters
        if search_request.max_price_per_slot:
            filters["base_price_per_slot"] = {"$lte": search_request.max_price_per_slot}

        # Content filters
        if search_request.content_rating:
            filters["content_rating_limit"] = {"$in": ["G", "PG", "PG-13", "R"][:["G", "PG", "PG-13", "R"].index(search_request.content_rating.value) + 1]}

        # Query slots
        result = await db_service.query_records(
            "ad_slots",
            filters,
            limit=search_request.page_size,
            skip=(search_request.page - 1) * search_request.page_size
        )

        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to search ad slots")

        # Calculate totals and statistics
        total_count = len(result.data)
        total_pages = (total_count + search_request.page_size - 1) // search_request.page_size

        # Calculate price range and other stats
        prices = [slot.get("base_price_per_slot", 0) for slot in result.data]
        price_range = {
            "min": min(prices) if prices else 0,
            "max": max(prices) if prices else 0
        }

        total_impressions = sum(slot.get("average_impressions_per_slot", 0) for slot in result.data)
        engagement_rates = [slot.get("average_engagement_rate", 0) for slot in result.data]
        avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0

        return AdSlotSearchResponse(
            slots=result.data,
            total_count=total_count,
            total_pages=total_pages,
            current_page=search_request.page,
            price_range=price_range,
            total_impressions=total_impressions,
            average_engagement_rate=avg_engagement
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching ad slots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== SLOT AVAILABILITY ====================

@router.get("/slots/{slot_id}/availability", response_model=List[Dict[str, Any]])
async def get_slot_availability(
    slot_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: Dict = Depends(get_current_user)
):
    """Get availability for a specific slot over a date range"""
    try:
        # Verify slot exists
        slot_result = await db_service.get_record("ad_slots", slot_id)
        if not slot_result.success:
            raise HTTPException(status_code=404, detail="Ad slot not found")

        # Query availability records
        filters = {
            "ad_slot_id": slot_id,
            "date": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }

        result = await db_service.query_records("ad_slot_availability", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve availability")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting slot availability: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/slots/{slot_id}/block", response_model=Dict[str, Any])
async def block_slot_dates(
    slot_id: str,
    blocked_dates: List[date],
    reason: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Block specific dates for an ad slot"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "slot",
            "edit"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to block slots")

        # Verify slot ownership
        slot_result = await db_service.get_record("ad_slots", slot_id)
        if not slot_result.success:
            raise HTTPException(status_code=404, detail="Ad slot not found")

        slot = slot_result.data
        if slot.get("host_company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Ad slot does not belong to your company")

        # Update blocked dates
        current_blocked = slot.get("blocked_dates", [])
        new_blocked = list(set(current_blocked + [d.isoformat() for d in blocked_dates]))

        update_data = {
            "blocked_dates": new_blocked,
            "updated_at": datetime.utcnow()
        }

        result = await db_service.update_record("ad_slots", slot_id, update_data)
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to block dates: {result.error}")

        logger.info(f"Blocked dates for slot {slot_id}: {blocked_dates} by user {current_user['id']}")
        return {"message": f"Blocked {len(blocked_dates)} dates", "blocked_dates": blocked_dates}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking slot dates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== SLOT ANALYTICS ====================

@router.get("/slots/{slot_id}/performance", response_model=Dict[str, Any])
async def get_slot_performance(
    slot_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: Dict = Depends(get_current_user)
):
    """Get performance analytics for an ad slot"""
    try:
        # Verify slot access
        slot_result = await db_service.get_record("ad_slots", slot_id)
        if not slot_result.success:
            raise HTTPException(status_code=404, detail="Ad slot not found")

        slot = slot_result.data

        # Check permissions (slot owner or super user)
        if (current_user.get("user_type") != "SUPER_USER" and
            slot.get("host_company_id") != current_user.get("company_id")):
            raise HTTPException(status_code=403, detail="Access denied")

        # Build date filters
        date_filters = {}
        if start_date:
            date_filters["$gte"] = start_date.isoformat()
        if end_date:
            date_filters["$lte"] = end_date.isoformat()

        # Query performance metrics
        filters = {"ad_slot_id": slot_id}
        if date_filters:
            filters["date"] = date_filters

        result = await db_service.query_records("playback_statistics", filters)
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to retrieve performance data")

        # Aggregate performance metrics
        stats = result.data
        total_scheduled = sum(s.get("total_scheduled_slots", 0) for s in stats)
        total_played = sum(s.get("total_played_slots", 0) for s in stats)
        total_revenue = sum(s.get("total_revenue_generated", 0) for s in stats)
        total_impressions = sum(s.get("total_impressions", 0) for s in stats)

        performance = {
            "slot_id": slot_id,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "metrics": {
                "total_scheduled_slots": total_scheduled,
                "total_played_slots": total_played,
                "success_rate": (total_played / total_scheduled * 100) if total_scheduled > 0 else 0,
                "total_revenue": total_revenue,
                "total_impressions": total_impressions,
                "average_revenue_per_slot": total_revenue / total_played if total_played > 0 else 0
            },
            "daily_breakdown": stats
        }

        return performance

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting slot performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== PRICING MANAGEMENT ====================

@router.put("/slots/{slot_id}/pricing", response_model=Dict[str, Any])
async def update_slot_pricing(
    slot_id: str,
    base_price: float,
    peak_multiplier: Optional[float] = None,
    weekend_multiplier: Optional[float] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Update pricing for an ad slot"""
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user["id"],
            current_user.get("company_id"),
            "slot",
            "pricing"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to update pricing")

        # Verify slot ownership
        slot_result = await db_service.get_record("ad_slots", slot_id)
        if not slot_result.success:
            raise HTTPException(status_code=404, detail="Ad slot not found")

        slot = slot_result.data
        if slot.get("host_company_id") != current_user.get("company_id"):
            raise HTTPException(status_code=403, detail="Ad slot does not belong to your company")

        # Update pricing
        update_data = {
            "base_price_per_slot": base_price,
            "updated_at": datetime.utcnow()
        }

        if peak_multiplier is not None:
            update_data["peak_multiplier"] = peak_multiplier
        if weekend_multiplier is not None:
            update_data["weekend_multiplier"] = weekend_multiplier

        result = await db_service.update_record("ad_slots", slot_id, update_data)
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to update pricing: {result.error}")

        logger.info(f"Pricing updated for slot {slot_id} by user {current_user['id']}")
        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating slot pricing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")