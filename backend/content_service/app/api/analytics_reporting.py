#!/usr/bin/env python3
"""
Analytics & Reporting API - Digital Signage Ad Slot Management System
API endpoints for comprehensive analytics, reporting, and business intelligence
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

from app.models.ad_slot_models import (
    PlaybackEvent, Booking, Invoice, AdSlot, Device, Location
)
from app.auth_service import get_current_user, require_role
from app.database_service import db_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])


# ==============================
# PLAYBACK ANALYTICS
# ==============================

@router.get("/playback/summary")
async def get_playback_summary(
    current_user = Depends(get_current_user),
    period: str = Query("week"),  # day, week, month, quarter
    location_id: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None)
):
    """Get playback analytics summary"""
    
    # Determine date range
    end_date = datetime.utcnow()
    if period == "day":
        start_date = end_date - timedelta(days=1)
    elif period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    # Build filter query based on user role
    filter_query = {"played_at": {"$gte": start_date, "$lte": end_date}}
    
    if current_user.role == "host":
        filter_query["host_company_id"] = current_user.company_id
    elif current_user.role == "advertiser":
        filter_query["advertiser_company_id"] = current_user.company_id
    elif current_user.role == "admin":
        if company_id:
            filter_query["$or"] = [
                {"host_company_id": company_id},
                {"advertiser_company_id": company_id}
            ]
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Apply additional filters
    if location_id:
        filter_query["location_id"] = location_id
    if device_id:
        filter_query["device_id"] = device_id
    
    # Get playback events
    playback_events = await db_service.playback_events.find(filter_query).to_list(None)
    
    # Calculate metrics
    total_plays = len(playback_events)
    unique_content = len(set(event["content_id"] for event in playback_events))
    unique_devices = len(set(event["device_id"] for event in playback_events))
    unique_locations = len(set(event["location_id"] for event in playback_events))
    
    # Calculate total duration and average audience
    total_duration = sum(event.get("duration_seconds", 0) for event in playback_events)
    total_audience = sum(event.get("audience_count", 1) for event in playback_events)
    avg_audience = total_audience / total_plays if total_plays > 0 else 0
    
    # Hourly distribution
    hourly_distribution = defaultdict(int)
    for event in playback_events:
        hour = event["played_at"].hour
        hourly_distribution[hour] += 1
    
    # Daily distribution
    daily_distribution = defaultdict(int)
    for event in playback_events:
        date_key = event["played_at"].strftime("%Y-%m-%d")
        daily_distribution[date_key] += 1
    
    # Device performance
    device_performance = defaultdict(lambda: {"plays": 0, "duration": 0, "audience": 0})
    for event in playback_events:
        device_id = event["device_id"]
        device_performance[device_id]["plays"] += 1
        device_performance[device_id]["duration"] += event.get("duration_seconds", 0)
        device_performance[device_id]["audience"] += event.get("audience_count", 1)
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "summary": {
            "total_plays": total_plays,
            "unique_content": unique_content,
            "unique_devices": unique_devices,
            "unique_locations": unique_locations,
            "total_duration_hours": total_duration / 3600,
            "average_audience": round(avg_audience, 2)
        },
        "distributions": {
            "hourly": dict(hourly_distribution),
            "daily": dict(daily_distribution)
        },
        "device_performance": dict(device_performance)
    }


@router.get("/playback/heatmap")
async def get_playback_heatmap(
    current_user = Depends(get_current_user),
    period: str = Query("week"),
    metric: str = Query("plays")  # plays, duration, audience
):
    """Get playback heatmap data for time-based visualization"""
    
    # Determine date range
    end_date = datetime.utcnow()
    if period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    # Build filter query
    filter_query = {"played_at": {"$gte": start_date, "$lte": end_date}}
    
    if current_user.role == "host":
        filter_query["host_company_id"] = current_user.company_id
    elif current_user.role == "advertiser":
        filter_query["advertiser_company_id"] = current_user.company_id
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get playback events
    playback_events = await db_service.playback_events.find(filter_query).to_list(None)
    
    # Create heatmap data structure [day_of_week][hour] = value
    heatmap_data = [[0 for _ in range(24)] for _ in range(7)]
    
    for event in playback_events:
        day_of_week = event["played_at"].weekday()
        hour = event["played_at"].hour
        
        if metric == "plays":
            heatmap_data[day_of_week][hour] += 1
        elif metric == "duration":
            heatmap_data[day_of_week][hour] += event.get("duration_seconds", 0)
        elif metric == "audience":
            heatmap_data[day_of_week][hour] += event.get("audience_count", 1)
    
    # Normalize duration to minutes
    if metric == "duration":
        for day in range(7):
            for hour in range(24):
                heatmap_data[day][hour] = round(heatmap_data[day][hour] / 60, 2)
    
    return {
        "period": period,
        "metric": metric,
        "heatmap_data": heatmap_data,
        "days_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "hours": list(range(24))
    }


# ==============================
# AUDIENCE ANALYTICS
# ==============================

@router.get("/audience/demographics")
async def get_audience_demographics(
    current_user = Depends(get_current_user),
    period: str = Query("month"),
    location_id: Optional[str] = Query(None)
):
    """Get audience demographic analytics"""
    
    # Determine date range
    end_date = datetime.utcnow()
    if period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    # Build filter query
    filter_query = {"played_at": {"$gte": start_date, "$lte": end_date}}
    
    if current_user.role == "host":
        filter_query["host_company_id"] = current_user.company_id
    elif current_user.role == "advertiser":
        filter_query["advertiser_company_id"] = current_user.company_id
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    if location_id:
        filter_query["location_id"] = location_id
    
    # Get playback events with engagement metrics
    playback_events = await db_service.playback_events.find(filter_query).to_list(None)
    
    # Aggregate demographic data (this would typically come from audience detection AI)
    total_impressions = sum(event.get("audience_count", 1) for event in playback_events)
    
    # Simulated demographic breakdown (in production, this would come from AI analytics)
    age_groups = {
        "18-24": 0,
        "25-34": 0,
        "35-44": 0,
        "45-54": 0,
        "55-64": 0,
        "65+": 0
    }
    
    gender_distribution = {
        "male": 0,
        "female": 0,
        "unknown": 0
    }
    
    engagement_levels = {
        "high": 0,      # Looked at screen for >3 seconds
        "medium": 0,    # Looked at screen for 1-3 seconds
        "low": 0        # Glanced at screen <1 second
    }
    
    # Analyze engagement metrics from events
    for event in playback_events:
        engagement_metrics = event.get("engagement_metrics", {})
        audience_count = event.get("audience_count", 1)
        
        # Distribute audience across demographics (simplified simulation)
        # In production, this would use actual computer vision analysis
        for age_group in age_groups:
            age_groups[age_group] += audience_count * 0.16  # Roughly even distribution
        
        for gender in gender_distribution:
            if gender == "male":
                gender_distribution[gender] += audience_count * 0.45
            elif gender == "female":
                gender_distribution[gender] += audience_count * 0.45
            else:
                gender_distribution[gender] += audience_count * 0.10
        
        # Analyze engagement levels
        avg_attention_time = engagement_metrics.get("avg_attention_seconds", 2.0)
        if avg_attention_time > 3:
            engagement_levels["high"] += audience_count
        elif avg_attention_time > 1:
            engagement_levels["medium"] += audience_count
        else:
            engagement_levels["low"] += audience_count
    
    # Calculate attention metrics
    total_attention_time = sum(
        event.get("engagement_metrics", {}).get("total_attention_seconds", 0)
        for event in playback_events
    )
    avg_attention_per_impression = total_attention_time / total_impressions if total_impressions > 0 else 0
    
    return {
        "period": period,
        "total_impressions": int(total_impressions),
        "demographics": {
            "age_groups": {k: int(v) for k, v in age_groups.items()},
            "gender_distribution": {k: int(v) for k, v in gender_distribution.items()}
        },
        "engagement": {
            "levels": {k: int(v) for k, v in engagement_levels.items()},
            "avg_attention_seconds": round(avg_attention_per_impression, 2),
            "total_attention_hours": round(total_attention_time / 3600, 2)
        }
    }


# ==============================
# REVENUE ANALYTICS
# ==============================

@router.get("/revenue/performance")
async def get_revenue_performance(
    current_user = Depends(get_current_user),
    period: str = Query("month"),
    breakdown: str = Query("daily")  # daily, weekly, monthly
):
    """Get detailed revenue performance analytics"""
    
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
        "status": "paid"
    }
    
    if current_user.role == "host":
        filter_query["host_company_id"] = current_user.company_id
    elif current_user.role == "advertiser":
        filter_query["advertiser_company_id"] = current_user.company_id
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get paid invoices
    invoices = await db_service.invoices.find(filter_query).to_list(None)
    
    # Calculate total metrics
    total_revenue = sum(invoice["total_amount"] for invoice in invoices)
    total_platform_fees = sum(invoice.get("platform_fee", 0) for invoice in invoices)
    total_host_revenue = sum(invoice.get("host_revenue_share", 0) for invoice in invoices)
    total_plays = sum(invoice.get("total_plays", 0) for invoice in invoices)
    
    # Revenue breakdown by time period
    revenue_breakdown = defaultdict(float)
    
    for invoice in invoices:
        if breakdown == "daily":
            time_key = invoice["created_at"].strftime("%Y-%m-%d")
        elif breakdown == "weekly":
            # Get start of week
            start_of_week = invoice["created_at"] - timedelta(days=invoice["created_at"].weekday())
            time_key = start_of_week.strftime("%Y-W%U")
        elif breakdown == "monthly":
            time_key = invoice["created_at"].strftime("%Y-%m")
        else:
            raise HTTPException(status_code=400, detail="Invalid breakdown")
        
        revenue_breakdown[time_key] += invoice["total_amount"]
    
    # Revenue by location (for hosts)
    location_revenue = defaultdict(float)
    if current_user.role == "host":
        # Get bookings associated with invoices
        booking_ids = [invoice["booking_id"] for invoice in invoices]
        bookings = await db_service.bookings.find({"_id": {"$in": booking_ids}}).to_list(None)
        
        for booking in bookings:
            # Find corresponding invoice
            invoice = next((inv for inv in invoices if inv["booking_id"] == booking["_id"]), None)
            if invoice:
                location_revenue[booking["location_id"]] += invoice["total_amount"]
    
    # Revenue by advertiser (for hosts/admins)
    advertiser_revenue = defaultdict(float)
    if current_user.role in ["host", "admin"]:
        for invoice in invoices:
            advertiser_revenue[invoice["advertiser_company_id"]] += invoice["total_amount"]
    
    # Calculate growth metrics
    prev_period_start = start_date - (end_date - start_date)
    prev_period_invoices = await db_service.invoices.find({
        "created_at": {"$gte": prev_period_start, "$lt": start_date},
        "status": "paid",
        **{k: v for k, v in filter_query.items() if k != "created_at"}
    }).to_list(None)
    
    prev_period_revenue = sum(invoice["total_amount"] for invoice in prev_period_invoices)
    revenue_growth = ((total_revenue - prev_period_revenue) / prev_period_revenue * 100) if prev_period_revenue > 0 else 0
    
    return {
        "period": period,
        "breakdown": breakdown,
        "summary": {
            "total_revenue": total_revenue,
            "total_platform_fees": total_platform_fees,
            "total_host_revenue": total_host_revenue,
            "total_plays": total_plays,
            "revenue_per_play": total_revenue / total_plays if total_plays > 0 else 0,
            "revenue_growth_percent": round(revenue_growth, 2)
        },
        "time_series": dict(revenue_breakdown),
        "location_breakdown": dict(location_revenue) if current_user.role == "host" else None,
        "advertiser_breakdown": dict(advertiser_revenue) if current_user.role in ["host", "admin"] else None
    }


# ==============================
# BOOKING ANALYTICS
# ==============================

@router.get("/bookings/conversion")
async def get_booking_conversion_metrics(
    current_user = Depends(get_current_user),
    period: str = Query("month")
):
    """Get booking conversion funnel analytics"""
    
    # Determine date range
    end_date = datetime.utcnow()
    if period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    # Build filter query
    filter_query = {"created_at": {"$gte": start_date, "$lte": end_date}}
    
    if current_user.role == "host":
        filter_query["host_company_id"] = current_user.company_id
    elif current_user.role == "advertiser":
        filter_query["advertiser_company_id"] = current_user.company_id
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all bookings in period
    all_bookings = await db_service.bookings.find(filter_query).to_list(None)
    
    # Calculate conversion funnel
    total_bookings = len(all_bookings)
    pending_bookings = len([b for b in all_bookings if b.get("status") == "pending"])
    approved_bookings = len([b for b in all_bookings if b.get("status") == "approved"])
    active_bookings = len([b for b in all_bookings if b.get("status") == "active"])
    completed_bookings = len([b for b in all_bookings if b.get("status") == "completed"])
    cancelled_bookings = len([b for b in all_bookings if b.get("status") == "cancelled"])
    
    # Calculate conversion rates
    approval_rate = (approved_bookings + active_bookings + completed_bookings) / total_bookings * 100 if total_bookings > 0 else 0
    completion_rate = completed_bookings / total_bookings * 100 if total_bookings > 0 else 0
    cancellation_rate = cancelled_bookings / total_bookings * 100 if total_bookings > 0 else 0
    
    # Booking value distribution
    booking_values = [b.get("total_amount", 0) for b in all_bookings if b.get("total_amount")]
    avg_booking_value = sum(booking_values) / len(booking_values) if booking_values else 0
    
    # Time to approval analysis
    approval_times = []
    for booking in all_bookings:
        if booking.get("status") in ["approved", "active", "completed"] and booking.get("approved_at"):
            approval_time = (booking["approved_at"] - booking["created_at"]).total_seconds() / 3600  # hours
            approval_times.append(approval_time)
    
    avg_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0
    
    # Booking trends by day
    daily_bookings = defaultdict(int)
    for booking in all_bookings:
        date_key = booking["created_at"].strftime("%Y-%m-%d")
        daily_bookings[date_key] += 1
    
    return {
        "period": period,
        "funnel_metrics": {
            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "approved_bookings": approved_bookings,
            "active_bookings": active_bookings,
            "completed_bookings": completed_bookings,
            "cancelled_bookings": cancelled_bookings
        },
        "conversion_rates": {
            "approval_rate": round(approval_rate, 2),
            "completion_rate": round(completion_rate, 2),
            "cancellation_rate": round(cancellation_rate, 2)
        },
        "value_metrics": {
            "average_booking_value": round(avg_booking_value, 2),
            "total_booking_value": sum(booking_values)
        },
        "timing_metrics": {
            "avg_approval_time_hours": round(avg_approval_time, 2)
        },
        "daily_trends": dict(daily_bookings)
    }


# ==============================
# DEVICE PERFORMANCE ANALYTICS
# ==============================

@router.get("/devices/performance")
async def get_device_performance_analytics(
    current_user = Depends(require_role(["host", "admin"])),
    period: str = Query("week"),
    location_id: Optional[str] = Query(None)
):
    """Get device performance and health analytics"""
    
    # Determine date range
    end_date = datetime.utcnow()
    if period == "day":
        start_date = end_date - timedelta(days=1)
    elif period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    # Build device filter
    device_filter = {}
    if current_user.role == "host":
        device_filter["host_company_id"] = current_user.company_id
    if location_id:
        device_filter["location_id"] = location_id
    
    # Get devices
    devices = await db_service.devices.find(device_filter).to_list(None)
    device_ids = [str(device["_id"]) for device in devices]
    
    # Get playback events for these devices
    playback_events = await db_service.playback_events.find({
        "device_id": {"$in": device_ids},
        "played_at": {"$gte": start_date, "$lte": end_date}
    }).to_list(None)
    
    # Calculate device metrics
    device_metrics = {}
    
    for device in devices:
        device_id = str(device["_id"])
        device_events = [e for e in playback_events if e["device_id"] == device_id]
        
        # Basic metrics
        total_plays = len(device_events)
        total_duration = sum(e.get("duration_seconds", 0) for e in device_events)
        total_audience = sum(e.get("audience_count", 1) for e in device_events)
        
        # Uptime calculation (simplified - would use device heartbeat data in production)
        total_hours = (end_date - start_date).total_seconds() / 3600
        play_hours = total_duration / 3600
        uptime_percentage = min(100, (play_hours / total_hours) * 100) if total_hours > 0 else 0
        
        # Performance score (composite metric)
        expected_plays = total_hours * 6  # Assume 6 plays per hour average
        performance_score = min(100, (total_plays / expected_plays) * 100) if expected_plays > 0 else 0
        
        # Error analysis (would come from device logs in production)
        error_count = 0  # Placeholder
        
        device_metrics[device_id] = {
            "device_name": device.get("name", f"Device {device_id}"),
            "location_id": device.get("location_id"),
            "total_plays": total_plays,
            "total_duration_hours": round(total_duration / 3600, 2),
            "total_audience": total_audience,
            "uptime_percentage": round(uptime_percentage, 2),
            "performance_score": round(performance_score, 2),
            "error_count": error_count,
            "last_activity": max([e["played_at"] for e in device_events]) if device_events else None,
            "status": "online" if device_events and (end_date - max([e["played_at"] for e in device_events])).seconds < 3600 else "offline"
        }
    
    # Overall fleet metrics
    total_devices = len(devices)
    online_devices = len([m for m in device_metrics.values() if m["status"] == "online"])
    avg_performance = sum(m["performance_score"] for m in device_metrics.values()) / total_devices if total_devices > 0 else 0
    avg_uptime = sum(m["uptime_percentage"] for m in device_metrics.values()) / total_devices if total_devices > 0 else 0
    
    return {
        "period": period,
        "fleet_summary": {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": total_devices - online_devices,
            "avg_performance_score": round(avg_performance, 2),
            "avg_uptime_percentage": round(avg_uptime, 2)
        },
        "device_metrics": device_metrics
    }


# ==============================
# CONTENT PERFORMANCE ANALYTICS
# ==============================

@router.get("/content/performance")
async def get_content_performance_analytics(
    current_user = Depends(get_current_user),
    period: str = Query("month"),
    content_type: Optional[str] = Query(None)
):
    """Get content performance analytics"""
    
    # Determine date range
    end_date = datetime.utcnow()
    if period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    # Build filter query
    filter_query = {"played_at": {"$gte": start_date, "$lte": end_date}}
    
    if current_user.role == "advertiser":
        filter_query["advertiser_company_id"] = current_user.company_id
    elif current_user.role == "host":
        filter_query["host_company_id"] = current_user.company_id
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get playback events
    playback_events = await db_service.playback_events.find(filter_query).to_list(None)
    
    # Get content information
    content_ids = list(set(event["content_id"] for event in playback_events))
    content_items = await db_service.content.find({"_id": {"$in": content_ids}}).to_list(None)
    content_lookup = {str(content["_id"]): content for content in content_items}
    
    # Filter by content type if specified
    if content_type:
        filtered_content_ids = [
            cid for cid, content in content_lookup.items() 
            if content.get("content_type", "").startswith(content_type)
        ]
        playback_events = [e for e in playback_events if e["content_id"] in filtered_content_ids]
    
    # Calculate content performance metrics
    content_performance = defaultdict(lambda: {
        "plays": 0,
        "duration": 0,
        "audience": 0,
        "engagement": 0,
        "locations": set(),
        "devices": set()
    })
    
    for event in playback_events:
        content_id = event["content_id"]
        content_performance[content_id]["plays"] += 1
        content_performance[content_id]["duration"] += event.get("duration_seconds", 0)
        content_performance[content_id]["audience"] += event.get("audience_count", 1)
        content_performance[content_id]["engagement"] += event.get("engagement_metrics", {}).get("avg_attention_seconds", 0)
        content_performance[content_id]["locations"].add(event["location_id"])
        content_performance[content_id]["devices"].add(event["device_id"])
    
    # Convert to final format with content details
    performance_results = []
    for content_id, metrics in content_performance.items():
        content_info = content_lookup.get(content_id, {})
        
        performance_results.append({
            "content_id": content_id,
            "content_title": content_info.get("title", "Unknown"),
            "content_type": content_info.get("content_type", "unknown"),
            "total_plays": metrics["plays"],
            "total_duration_hours": round(metrics["duration"] / 3600, 2),
            "total_audience": metrics["audience"],
            "avg_engagement_seconds": round(metrics["engagement"] / metrics["plays"], 2) if metrics["plays"] > 0 else 0,
            "unique_locations": len(metrics["locations"]),
            "unique_devices": len(metrics["devices"]),
            "plays_per_day": round(metrics["plays"] / ((end_date - start_date).days or 1), 2)
        })
    
    # Sort by total plays descending
    performance_results.sort(key=lambda x: x["total_plays"], reverse=True)
    
    # Calculate summary metrics
    total_content_pieces = len(performance_results)
    total_plays = sum(result["total_plays"] for result in performance_results)
    avg_plays_per_content = total_plays / total_content_pieces if total_content_pieces > 0 else 0
    
    # Content type distribution
    type_distribution = defaultdict(int)
    for result in performance_results:
        content_type = result["content_type"].split("/")[0] if "/" in result["content_type"] else result["content_type"]
        type_distribution[content_type] += 1
    
    return {
        "period": period,
        "summary": {
            "total_content_pieces": total_content_pieces,
            "total_plays": total_plays,
            "avg_plays_per_content": round(avg_plays_per_content, 2)
        },
        "content_type_distribution": dict(type_distribution),
        "top_performing_content": performance_results[:20],  # Top 20
        "all_content_performance": performance_results
    }


# ==============================
# CUSTOM REPORTS
# ==============================

@router.post("/reports/custom")
async def generate_custom_report(
    report_config: dict,
    current_user = Depends(get_current_user)
):
    """Generate custom analytics report based on user configuration"""
    
    report_type = report_config.get("type")
    period = report_config.get("period", "month")
    filters = report_config.get("filters", {})
    metrics = report_config.get("metrics", [])
    
    if not report_type or not metrics:
        raise HTTPException(status_code=400, detail="Report type and metrics are required")
    
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
    
    # Build base filter query
    base_filter = {"created_at": {"$gte": start_date, "$lte": end_date}}
    
    # Apply user role restrictions
    if current_user.role == "host":
        base_filter["host_company_id"] = current_user.company_id
    elif current_user.role == "advertiser":
        base_filter["advertiser_company_id"] = current_user.company_id
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Apply additional filters
    for key, value in filters.items():
        if key in ["location_id", "device_id", "content_type"]:
            base_filter[key] = value
    
    report_data = {}
    
    # Generate data based on requested metrics
    if "playback_summary" in metrics:
        playback_filter = dict(base_filter)
        playback_filter["played_at"] = playback_filter.pop("created_at")
        playback_events = await db_service.playback_events.find(playback_filter).to_list(None)
        
        report_data["playback_summary"] = {
            "total_plays": len(playback_events),
            "total_duration_hours": sum(e.get("duration_seconds", 0) for e in playback_events) / 3600,
            "unique_content": len(set(e["content_id"] for e in playback_events)),
            "unique_devices": len(set(e["device_id"] for e in playback_events))
        }
    
    if "revenue_summary" in metrics:
        invoice_filter = dict(base_filter)
        invoice_filter["status"] = "paid"
        invoices = await db_service.invoices.find(invoice_filter).to_list(None)
        
        report_data["revenue_summary"] = {
            "total_revenue": sum(inv["total_amount"] for inv in invoices),
            "total_invoices": len(invoices),
            "avg_invoice_value": sum(inv["total_amount"] for inv in invoices) / len(invoices) if invoices else 0
        }
    
    if "booking_summary" in metrics:
        bookings = await db_service.bookings.find(base_filter).to_list(None)
        
        report_data["booking_summary"] = {
            "total_bookings": len(bookings),
            "active_bookings": len([b for b in bookings if b.get("status") == "active"]),
            "completed_bookings": len([b for b in bookings if b.get("status") == "completed"])
        }
    
    return {
        "report_type": report_type,
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "filters_applied": filters,
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": current_user.id,
        "data": report_data
    }


@router.get("/reports/scheduled")
async def get_scheduled_reports(
    current_user = Depends(get_current_user)
):
    """Get list of scheduled reports for the user"""
    
    # TODO: Implement scheduled reports functionality
    # This would allow users to set up automated report generation
    # and delivery via email or dashboard notifications
    
    return {
        "scheduled_reports": [],
        "message": "Scheduled reports feature coming soon"
    }