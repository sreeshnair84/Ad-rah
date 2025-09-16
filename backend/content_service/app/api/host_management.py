#!/usr/bin/env python3
"""
Host Management API - Digital Signage Ad Slot Management System
API endpoints for hosts to manage locations, ad slots, approvals, and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.ad_slot_models import (
    Location, Device, AdSlot, Booking, BookingStatus, 
    RevenueShare, AnalyticsAggregation
)
from app.auth_service import get_current_user, require_role
from app.database_service import db_service

router = APIRouter(prefix="/host", tags=["Host Management"])


# ==============================
# LOCATION MANAGEMENT
# ==============================

@router.post("/locations", response_model=Location)
async def create_location(
    location_data: dict,
    current_user = Depends(require_role(["host", "admin"]))
):
    """Create a new location for the host company"""
    location_data["host_company_id"] = current_user.company_id
    
    location = Location(**location_data)
    result = await db_service.locations.insert_one(location.dict())
    location.id = str(result.inserted_id)
    
    return location


@router.get("/locations", response_model=List[Location])
async def get_host_locations(
    current_user = Depends(require_role(["host", "admin"])),
    is_active: Optional[bool] = Query(None),
    venue_type: Optional[str] = Query(None)
):
    """Get all locations for the host company"""
    filter_query = {"host_company_id": current_user.company_id}
    
    if is_active is not None:
        filter_query["is_active"] = is_active
    if venue_type:
        filter_query["venue_type"] = venue_type
    
    locations = await db_service.locations.find(filter_query).to_list(None)
    return [Location(**loc) for loc in locations]


@router.get("/locations/{location_id}", response_model=Location)
async def get_location(
    location_id: str,
    current_user = Depends(require_role(["host", "admin"]))
):
    """Get a specific location"""
    location = await db_service.locations.find_one({
        "_id": location_id,
        "host_company_id": current_user.company_id
    })
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return Location(**location)


@router.put("/locations/{location_id}", response_model=Location)
async def update_location(
    location_id: str,
    location_data: dict,
    current_user = Depends(require_role(["host", "admin"]))
):
    """Update a location"""
    # Verify ownership
    existing = await db_service.locations.find_one({
        "_id": location_id,
        "host_company_id": current_user.company_id
    })
    
    if not existing:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location_data["updated_at"] = datetime.utcnow()
    await db_service.locations.update_one(
        {"_id": location_id},
        {"$set": location_data}
    )
    
    updated_location = await db_service.locations.find_one({"_id": location_id})
    return Location(**updated_location)


# ==============================
# DEVICE MANAGEMENT
# ==============================

@router.post("/locations/{location_id}/devices", response_model=Device)
async def create_device(
    location_id: str,
    device_data: dict,
    current_user = Depends(require_role(["host", "admin"]))
):
    """Create a new device for a location"""
    # Verify location ownership
    location = await db_service.locations.find_one({
        "_id": location_id,
        "host_company_id": current_user.company_id
    })
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    device_data["location_id"] = location_id
    device = Device(**device_data)
    result = await db_service.devices.insert_one(device.dict())
    device.id = str(result.inserted_id)
    
    return device


@router.get("/locations/{location_id}/devices", response_model=List[Device])
async def get_location_devices(
    location_id: str,
    current_user = Depends(require_role(["host", "admin"])),
    is_active: Optional[bool] = Query(None),
    is_online: Optional[bool] = Query(None)
):
    """Get all devices for a location"""
    # Verify location ownership
    location = await db_service.locations.find_one({
        "_id": location_id,
        "host_company_id": current_user.company_id
    })
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    filter_query = {"location_id": location_id}
    if is_active is not None:
        filter_query["is_active"] = is_active
    if is_online is not None:
        filter_query["is_online"] = is_online
    
    devices = await db_service.devices.find(filter_query).to_list(None)
    return [Device(**device) for device in devices]


@router.get("/devices/{device_id}/status")
async def get_device_status(
    device_id: str,
    current_user = Depends(require_role(["host", "admin"]))
):
    """Get real-time device status and health"""
    # Verify device ownership through location
    device = await db_service.devices.find_one({"_id": device_id})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    location = await db_service.locations.find_one({
        "_id": device["location_id"],
        "host_company_id": current_user.company_id
    })
    
    if not location:
        raise HTTPException(status_code=404, detail="Access denied")
    
    # Get latest heartbeat and status
    latest_heartbeat = await db_service.device_heartbeats.find_one(
        {"device_id": device_id},
        sort=[("timestamp", -1)]
    )
    
    return {
        "device": Device(**device),
        "status": {
            "is_online": device.get("is_online", False),
            "last_heartbeat": device.get("last_heartbeat"),
            "battery_level": device.get("battery_level"),
            "software_version": device.get("software_version"),
            "latest_heartbeat": latest_heartbeat
        }
    }


# ==============================
# AD SLOT MANAGEMENT
# ==============================

@router.post("/ad-slots", response_model=AdSlot)
async def create_ad_slot(
    slot_data: dict,
    current_user = Depends(require_role(["host", "admin"]))
):
    """Create a new ad slot"""
    # Verify device ownership
    device = await db_service.devices.find_one({"_id": slot_data["device_id"]})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    location = await db_service.locations.find_one({
        "_id": device["location_id"],
        "host_company_id": current_user.company_id
    })
    
    if not location:
        raise HTTPException(status_code=404, detail="Access denied")
    
    slot_data["location_id"] = device["location_id"]
    slot_data["created_by"] = current_user.id
    
    ad_slot = AdSlot(**slot_data)
    result = await db_service.ad_slots.insert_one(ad_slot.dict())
    ad_slot.id = str(result.inserted_id)
    
    return ad_slot


@router.get("/ad-slots", response_model=List[AdSlot])
async def get_host_ad_slots(
    current_user = Depends(require_role(["host", "admin"])),
    location_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get all ad slots for the host company"""
    # Get all host locations
    host_locations = await db_service.locations.find({
        "host_company_id": current_user.company_id
    }).to_list(None)
    
    location_ids = [loc["_id"] for loc in host_locations]
    
    filter_query = {"location_id": {"$in": location_ids}}
    
    if location_id:
        filter_query["location_id"] = location_id
    if status:
        filter_query["status"] = status
    
    ad_slots = await db_service.ad_slots.find(filter_query).to_list(None)
    return [AdSlot(**slot) for slot in ad_slots]


@router.put("/ad-slots/{slot_id}", response_model=AdSlot)
async def update_ad_slot(
    slot_id: str,
    slot_data: dict,
    current_user = Depends(require_role(["host", "admin"]))
):
    """Update an ad slot"""
    # Verify ownership
    ad_slot = await db_service.ad_slots.find_one({"_id": slot_id})
    if not ad_slot:
        raise HTTPException(status_code=404, detail="Ad slot not found")
    
    location = await db_service.locations.find_one({
        "_id": ad_slot["location_id"],
        "host_company_id": current_user.company_id
    })
    
    if not location:
        raise HTTPException(status_code=404, detail="Access denied")
    
    slot_data["updated_at"] = datetime.utcnow()
    await db_service.ad_slots.update_one(
        {"_id": slot_id},
        {"$set": slot_data}
    )
    
    updated_slot = await db_service.ad_slots.find_one({"_id": slot_id})
    return AdSlot(**updated_slot)


# ==============================
# BOOKING APPROVAL WORKFLOW
# ==============================

@router.get("/bookings/pending", response_model=List[Dict])
async def get_pending_bookings(
    current_user = Depends(require_role(["host", "admin"]))
):
    """Get all pending booking requests for host approval"""
    # Get all host locations
    host_locations = await db_service.locations.find({
        "host_company_id": current_user.company_id
    }).to_list(None)
    
    location_ids = [loc["_id"] for loc in host_locations]
    
    # Get ad slots for these locations
    ad_slots = await db_service.ad_slots.find({
        "location_id": {"$in": location_ids}
    }).to_list(None)
    
    slot_ids = [slot["_id"] for slot in ad_slots]
    
    # Get pending bookings
    pending_bookings = await db_service.bookings.find({
        "ad_slot_id": {"$in": slot_ids},
        "status": BookingStatus.PENDING,
        "host_approval_required": True
    }).to_list(None)
    
    # Enrich with advertiser and slot details
    enriched_bookings = []
    for booking in pending_bookings:
        # Get advertiser company info
        advertiser = await db_service.companies.find_one({
            "_id": booking["advertiser_company_id"]
        })
        
        # Get ad slot info
        slot = next((s for s in ad_slots if s["_id"] == booking["ad_slot_id"]), None)
        
        # Get location info
        location = next((l for l in host_locations if l["_id"] == slot["location_id"]), None)
        
        # Get content info if available
        content = None
        if booking.get("content_id"):
            content = await db_service.content.find_one({
                "_id": booking["content_id"]
            })
        
        enriched_bookings.append({
            "booking": Booking(**booking),
            "advertiser": advertiser,
            "ad_slot": slot,
            "location": location,
            "content": content
        })
    
    return enriched_bookings


@router.post("/bookings/{booking_id}/approve")
async def approve_booking(
    booking_id: str,
    approval_data: dict,
    current_user = Depends(require_role(["host", "admin"]))
):
    """Approve a booking request"""
    # Verify booking exists and belongs to host
    booking = await db_service.bookings.find_one({"_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    ad_slot = await db_service.ad_slots.find_one({"_id": booking["ad_slot_id"]})
    location = await db_service.locations.find_one({
        "_id": ad_slot["location_id"],
        "host_company_id": current_user.company_id
    })
    
    if not location:
        raise HTTPException(status_code=404, detail="Access denied")
    
    # Update booking status
    update_data = {
        "status": BookingStatus.APPROVED,
        "approved_by": current_user.id,
        "approved_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    if approval_data.get("conditions"):
        update_data["approval_conditions"] = approval_data["conditions"]
    
    await db_service.bookings.update_one(
        {"_id": booking_id},
        {"$set": update_data}
    )
    
    # TODO: Send notification to advertiser
    # TODO: Update slot availability calendar
    
    return {"message": "Booking approved successfully"}


@router.post("/bookings/{booking_id}/reject")
async def reject_booking(
    booking_id: str,
    rejection_data: dict,
    current_user = Depends(require_role(["host", "admin"]))
):
    """Reject a booking request"""
    # Verify booking exists and belongs to host
    booking = await db_service.bookings.find_one({"_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    ad_slot = await db_service.ad_slots.find_one({"_id": booking["ad_slot_id"]})
    location = await db_service.locations.find_one({
        "_id": ad_slot["location_id"],
        "host_company_id": current_user.company_id
    })
    
    if not location:
        raise HTTPException(status_code=404, detail="Access denied")
    
    # Update booking status
    await db_service.bookings.update_one(
        {"_id": booking_id},
        {"$set": {
            "status": BookingStatus.REJECTED,
            "rejection_reason": rejection_data.get("reason", "Not specified"),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # TODO: Send notification to advertiser
    # TODO: Process refund if payment was already made
    
    return {"message": "Booking rejected successfully"}


# ==============================
# REVENUE ANALYTICS
# ==============================

@router.get("/analytics/revenue")
async def get_revenue_analytics(
    current_user = Depends(require_role(["host", "admin"])),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    location_id: Optional[str] = Query(None)
):
    """Get revenue analytics for host locations"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get host locations
    location_filter = {"host_company_id": current_user.company_id}
    if location_id:
        location_filter["_id"] = location_id
    
    host_locations = await db_service.locations.find(location_filter).to_list(None)
    location_ids = [loc["_id"] for loc in host_locations]
    
    # Get revenue shares for the period
    revenue_shares = await db_service.revenue_shares.find({
        "host_company_id": current_user.company_id,
        "period_start": {"$gte": start_date},
        "period_end": {"$lte": end_date}
    }).to_list(None)
    
    # Get analytics aggregations
    analytics = await db_service.analytics_aggregations.find({
        "location_id": {"$in": location_ids},
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)
    
    # Calculate summary metrics
    total_revenue = sum(rs.get("host_share_amount", 0) for rs in revenue_shares)
    total_impressions = sum(a.get("total_impressions", 0) for a in analytics)
    total_plays = sum(a.get("total_plays", 0) for a in analytics)
    
    # Group by location
    location_breakdown = {}
    for location in host_locations:
        loc_id = location["_id"]
        loc_analytics = [a for a in analytics if a.get("location_id") == loc_id]
        loc_revenue = [rs for rs in revenue_shares if any(
            a.get("location_id") == loc_id for a in analytics 
            if a.get("date") >= rs.get("period_start") and a.get("date") <= rs.get("period_end")
        )]
        
        location_breakdown[loc_id] = {
            "location_name": location["name"],
            "total_impressions": sum(a.get("total_impressions", 0) for a in loc_analytics),
            "total_plays": sum(a.get("total_plays", 0) for a in loc_analytics),
            "total_revenue": sum(r.get("host_share_amount", 0) for r in loc_revenue),
            "avg_cpm": 0  # Calculate based on impressions and revenue
        }
        
        if location_breakdown[loc_id]["total_impressions"] > 0:
            location_breakdown[loc_id]["avg_cpm"] = (
                location_breakdown[loc_id]["total_revenue"] / 
                location_breakdown[loc_id]["total_impressions"] * 1000
            )
    
    return {
        "summary": {
            "total_revenue": total_revenue,
            "total_impressions": total_impressions,
            "total_plays": total_plays,
            "avg_cpm": total_revenue / total_impressions * 1000 if total_impressions > 0 else 0,
            "period_start": start_date,
            "period_end": end_date
        },
        "location_breakdown": location_breakdown,
        "daily_breakdown": analytics  # Group by day if needed
    }


@router.get("/analytics/performance")
async def get_performance_analytics(
    current_user = Depends(require_role(["host", "admin"])),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get performance analytics for host locations"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=7)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get host locations
    host_locations = await db_service.locations.find({
        "host_company_id": current_user.company_id
    }).to_list(None)
    
    location_ids = [loc["_id"] for loc in host_locations]
    
    # Get device uptime and health metrics
    devices = await db_service.devices.find({
        "location_id": {"$in": location_ids}
    }).to_list(None)
    
    # Get recent playback events for error analysis
    playback_events = await db_service.playback_events.find({
        "location_id": {"$in": location_ids},
        "timestamp": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)
    
    # Calculate performance metrics
    total_events = len(playback_events)
    error_events = len([e for e in playback_events if e.get("event_type") == "error"])
    completion_events = len([e for e in playback_events if e.get("event_type") == "complete"])
    
    online_devices = len([d for d in devices if d.get("is_online", False)])
    total_devices = len(devices)
    
    return {
        "device_health": {
            "online_devices": online_devices,
            "total_devices": total_devices,
            "uptime_percentage": (online_devices / total_devices * 100) if total_devices > 0 else 0
        },
        "playback_performance": {
            "total_events": total_events,
            "error_rate": (error_events / total_events * 100) if total_events > 0 else 0,
            "completion_rate": (completion_events / total_events * 100) if total_events > 0 else 0
        },
        "devices": [
            {
                "device_id": device["_id"],
                "device_name": device.get("device_name"),
                "location_name": next((l["name"] for l in host_locations if l["_id"] == device["location_id"]), "Unknown"),
                "is_online": device.get("is_online", False),
                "last_heartbeat": device.get("last_heartbeat"),
                "battery_level": device.get("battery_level")
            }
            for device in devices
        ]
    }


@router.get("/analytics/bookings")
async def get_booking_analytics(
    current_user = Depends(require_role(["host", "admin"])),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get booking analytics and trends"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get host locations and ad slots
    host_locations = await db_service.locations.find({
        "host_company_id": current_user.company_id
    }).to_list(None)
    
    location_ids = [loc["_id"] for loc in host_locations]
    
    ad_slots = await db_service.ad_slots.find({
        "location_id": {"$in": location_ids}
    }).to_list(None)
    
    slot_ids = [slot["_id"] for slot in ad_slots]
    
    # Get bookings for the period
    bookings = await db_service.bookings.find({
        "ad_slot_id": {"$in": slot_ids},
        "created_at": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)
    
    # Calculate metrics
    total_bookings = len(bookings)
    approved_bookings = len([b for b in bookings if b.get("status") == BookingStatus.APPROVED])
    pending_bookings = len([b for b in bookings if b.get("status") == BookingStatus.PENDING])
    rejected_bookings = len([b for b in bookings if b.get("status") == BookingStatus.REJECTED])
    
    total_revenue_potential = sum(float(b.get("final_price", 0)) for b in bookings if b.get("status") == BookingStatus.APPROVED)
    
    return {
        "summary": {
            "total_bookings": total_bookings,
            "approved_bookings": approved_bookings,
            "pending_bookings": pending_bookings,
            "rejected_bookings": rejected_bookings,
            "approval_rate": (approved_bookings / total_bookings * 100) if total_bookings > 0 else 0,
            "total_revenue_potential": total_revenue_potential
        },
        "slot_utilization": [
            {
                "slot_id": slot["_id"],
                "slot_name": slot.get("name"),
                "location_name": next((l["name"] for l in host_locations if l["_id"] == slot["location_id"]), "Unknown"),
                "total_bookings": len([b for b in bookings if b["ad_slot_id"] == slot["_id"]]),
                "approved_bookings": len([b for b in bookings if b["ad_slot_id"] == slot["_id"] and b.get("status") == BookingStatus.APPROVED])
            }
            for slot in ad_slots
        ]
    }