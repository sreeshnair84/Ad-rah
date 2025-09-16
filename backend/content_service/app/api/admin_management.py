#!/usr/bin/env python3
"""
Admin Management API - Digital Signage Ad Slot Management System
API endpoints for system administrators to manage users, monitor system, and oversee operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.ad_slot_models import (
    User, Company, Location, AdSlot, Booking, Content, 
    ModerationLog, AnalyticsAggregation, Invoice, PaymentTransaction
)
from app.auth_service import get_current_user, require_role
from app.database_service import db_service

router = APIRouter(prefix="/admin", tags=["Admin Management"])


# ==============================
# USER MANAGEMENT
# ==============================

@router.get("/users", response_model=List[User])
async def get_all_users(
    current_user = Depends(require_role(["admin", "super_admin"])),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    company_id: Optional[str] = Query(None),
    page: int = Query(1),
    limit: int = Query(50)
):
    """Get all users in the system"""
    
    filter_query = {}
    
    if role:
        filter_query["role"] = role
    if is_active is not None:
        filter_query["is_active"] = is_active
    if company_id:
        filter_query["company_id"] = company_id
    
    # Calculate skip for pagination
    skip = (page - 1) * limit
    
    users = await db_service.users.find(filter_query).skip(skip).limit(limit).to_list(None)
    return [User(**user) for user in users]


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user = Depends(require_role(["admin", "super_admin"]))
):
    """Get a specific user"""
    
    user = await db_service.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**user)


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: dict,
    current_user = Depends(require_role(["admin", "super_admin"]))
):
    """Update user information"""
    
    user = await db_service.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow updating certain fields
    restricted_fields = ["id", "password_hash", "created_at"]
    update_data = {k: v for k, v in update_data.items() if k not in restricted_fields}
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db_service.users.update_one(
        {"_id": user_id},
        {"$set": update_data}
    )
    
    return {"message": "User updated successfully"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user = Depends(require_role(["admin", "super_admin"]))
):
    """Deactivate a user account"""
    
    user = await db_service.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db_service.users.update_one(
        {"_id": user_id},
        {"$set": {
            "is_active": False,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # TODO: Log admin action
    # TODO: Notify user of deactivation
    
    return {"message": "User deactivated successfully"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user = Depends(require_role(["admin", "super_admin"]))
):
    """Activate a user account"""
    
    user = await db_service.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db_service.users.update_one(
        {"_id": user_id},
        {"$set": {
            "is_active": True,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "User activated successfully"}


# ==============================
# COMPANY MANAGEMENT
# ==============================

@router.get("/companies", response_model=List[Company])
async def get_all_companies(
    current_user = Depends(require_role(["admin", "super_admin"])),
    company_type: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get all companies in the system"""
    
    filter_query = {}
    
    if company_type:
        filter_query["company_type"] = company_type
    if verification_status:
        filter_query["verification_status"] = verification_status
    if is_active is not None:
        filter_query["is_active"] = is_active
    
    companies = await db_service.companies.find(filter_query).to_list(None)
    return [Company(**company) for company in companies]


@router.put("/companies/{company_id}/verify")
async def verify_company(
    company_id: str,
    verification_data: dict,
    current_user = Depends(require_role(["admin", "super_admin"]))
):
    """Verify a company's KYC information"""
    
    company = await db_service.companies.find_one({"_id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = {
        "verification_status": "verified",
        "verified_at": datetime.utcnow(),
        "verified_by": current_user.id,
        "updated_at": datetime.utcnow()
    }
    
    if verification_data.get("notes"):
        update_data["verification_notes"] = verification_data["notes"]
    
    await db_service.companies.update_one(
        {"_id": company_id},
        {"$set": update_data}
    )
    
    # TODO: Send verification confirmation email
    # TODO: Log admin action
    
    return {"message": "Company verified successfully"}


@router.put("/companies/{company_id}/reject")
async def reject_company_verification(
    company_id: str,
    rejection_data: dict,
    current_user = Depends(require_role(["admin", "super_admin"]))
):
    """Reject a company's verification"""
    
    company = await db_service.companies.find_one({"_id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    await db_service.companies.update_one(
        {"_id": company_id},
        {"$set": {
            "verification_status": "rejected",
            "rejection_reason": rejection_data.get("reason", "Not specified"),
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": "Company verification rejected"}


# ==============================
# CONTENT MODERATION OVERSIGHT
# ==============================

@router.get("/moderation/queue")
async def get_moderation_queue(
    current_user = Depends(require_role(["admin", "reviewer"])),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query("high"),
    limit: int = Query(50)
):
    """Get content moderation queue"""
    
    filter_query = {}
    
    if status:
        filter_query["status"] = status
    else:
        # Default to items needing review
        filter_query["status"] = {"$in": ["submitted", "ai_review", "human_review"]}
    
    # Sort by priority and submission time
    sort_criteria = []
    if priority == "high":
        sort_criteria.append(("ai_moderation_score", -1))  # High AI risk first
    sort_criteria.append(("created_at", 1))  # Older first
    
    content_items = await db_service.content.find(filter_query).sort(sort_criteria).limit(limit).to_list(None)
    
    # Enrich with company information
    enriched_items = []
    for content in content_items:
        company = await db_service.companies.find_one({"_id": content["advertiser_company_id"]})
        
        # Get moderation history
        moderation_logs = await db_service.moderation_logs.find({
            "content_id": content["_id"]
        }).sort([("created_at", -1)]).to_list(None)
        
        enriched_items.append({
            "content": Content(**content),
            "company": company,
            "moderation_history": moderation_logs,
            "ai_flags": content.get("ai_moderation_flags", []),
            "risk_score": content.get("ai_moderation_score", 0)
        })
    
    return enriched_items


@router.get("/moderation/statistics")
async def get_moderation_statistics(
    current_user = Depends(require_role(["admin", "reviewer"])),
    days: int = Query(30)
):
    """Get moderation system statistics"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get content submitted in period
    content_items = await db_service.content.find({
        "created_at": {"$gte": start_date}
    }).to_list(None)
    
    # Get moderation logs in period
    moderation_logs = await db_service.moderation_logs.find({
        "created_at": {"$gte": start_date}
    }).to_list(None)
    
    # Calculate statistics
    total_submissions = len(content_items)
    ai_moderated = len([c for c in content_items if c.get("ai_moderation_score") is not None])
    human_reviewed = len([c for c in content_items if c.get("reviewed_by") is not None])
    approved = len([c for c in content_items if c.get("status") == "approved"])
    rejected = len([c for c in content_items if c.get("status") == "rejected"])
    
    # Reviewer performance
    reviewer_stats = {}
    for log in moderation_logs:
        if log.get("reviewer_id"):
            reviewer_id = log["reviewer_id"]
            if reviewer_id not in reviewer_stats:
                reviewer_stats[reviewer_id] = {"reviews": 0, "approvals": 0, "rejections": 0}
            
            reviewer_stats[reviewer_id]["reviews"] += 1
            if log.get("new_status") == "approved":
                reviewer_stats[reviewer_id]["approvals"] += 1
            elif log.get("new_status") == "rejected":
                reviewer_stats[reviewer_id]["rejections"] += 1
    
    # Average processing times
    processing_times = []
    for content in content_items:
        if content.get("reviewed_at") and content.get("created_at"):
            processing_time = (content["reviewed_at"] - content["created_at"]).total_seconds() / 3600  # hours
            processing_times.append(processing_time)
    
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    return {
        "period_days": days,
        "total_submissions": total_submissions,
        "ai_moderation_rate": (ai_moderated / total_submissions * 100) if total_submissions > 0 else 0,
        "human_review_rate": (human_reviewed / total_submissions * 100) if total_submissions > 0 else 0,
        "approval_rate": (approved / total_submissions * 100) if total_submissions > 0 else 0,
        "rejection_rate": (rejected / total_submissions * 100) if total_submissions > 0 else 0,
        "avg_processing_time_hours": avg_processing_time,
        "reviewer_performance": reviewer_stats,
        "queue_backlog": len([c for c in content_items if c.get("status") in ["submitted", "ai_review", "human_review"]])
    }


@router.post("/moderation/{content_id}/override")
async def override_moderation_decision(
    content_id: str,
    override_data: dict,
    current_user = Depends(require_role(["admin"]))
):
    """Override a moderation decision (admin only)"""
    
    content = await db_service.content.find_one({"_id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    new_status = override_data.get("status")
    if new_status not in ["approved", "rejected", "quarantined"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    # Update content status
    await db_service.content.update_one(
        {"_id": content_id},
        {"$set": {
            "status": new_status,
            "reviewed_by": current_user.id,
            "reviewed_at": datetime.utcnow(),
            "human_review_notes": override_data.get("notes", "Admin override"),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Log the override
    moderation_log = ModerationLog(
        content_id=content_id,
        moderation_type="admin_override",
        previous_status=content.get("status"),
        new_status=new_status,
        reviewer_id=current_user.id,
        reviewer_notes=override_data.get("notes", "Admin override"),
        decision_reason="Administrative override"
    )
    
    await db_service.moderation_logs.insert_one(moderation_log.dict())
    
    return {"message": "Moderation decision overridden successfully"}


# ==============================
# SYSTEM ANALYTICS
# ==============================

@router.get("/analytics/system-overview")
async def get_system_overview(
    current_user = Depends(require_role(["admin", "super_admin"])),
    days: int = Query(30)
):
    """Get high-level system analytics"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # User statistics
    total_users = await db_service.users.count_documents({})
    active_users = await db_service.users.count_documents({"is_active": True})
    new_users = await db_service.users.count_documents({"created_at": {"$gte": start_date}})
    
    # Company statistics
    total_companies = await db_service.companies.count_documents({})
    verified_companies = await db_service.companies.count_documents({"verification_status": "verified"})
    host_companies = await db_service.companies.count_documents({"company_type": {"$in": ["host", "both"]}})
    advertiser_companies = await db_service.companies.count_documents({"company_type": {"$in": ["advertiser", "both"]}})
    
    # Content statistics
    total_content = await db_service.content.count_documents({})
    approved_content = await db_service.content.count_documents({"status": "approved"})
    pending_moderation = await db_service.content.count_documents({"status": {"$in": ["submitted", "ai_review", "human_review"]}})
    
    # Booking statistics
    total_bookings = await db_service.bookings.count_documents({})
    active_bookings = await db_service.bookings.count_documents({"status": {"$in": ["approved", "confirmed", "active"]}})
    recent_bookings = await db_service.bookings.count_documents({"created_at": {"$gte": start_date}})
    
    # Revenue statistics
    revenue_aggregations = await db_service.analytics_aggregations.find({
        "date": {"$gte": start_date}
    }).to_list(None)
    
    total_revenue = sum(float(a.get("revenue_generated", 0)) for a in revenue_aggregations)
    total_impressions = sum(a.get("total_impressions", 0) for a in revenue_aggregations)
    
    # Location and device statistics
    total_locations = await db_service.locations.count_documents({})
    active_locations = await db_service.locations.count_documents({"is_active": True})
    total_devices = await db_service.devices.count_documents({})
    online_devices = await db_service.devices.count_documents({"is_online": True})
    
    return {
        "period_days": days,
        "users": {
            "total": total_users,
            "active": active_users,
            "new_in_period": new_users,
            "activity_rate": (active_users / total_users * 100) if total_users > 0 else 0
        },
        "companies": {
            "total": total_companies,
            "verified": verified_companies,
            "hosts": host_companies,
            "advertisers": advertiser_companies,
            "verification_rate": (verified_companies / total_companies * 100) if total_companies > 0 else 0
        },
        "content": {
            "total": total_content,
            "approved": approved_content,
            "pending_moderation": pending_moderation,
            "approval_rate": (approved_content / total_content * 100) if total_content > 0 else 0
        },
        "bookings": {
            "total": total_bookings,
            "active": active_bookings,
            "recent": recent_bookings
        },
        "revenue": {
            "total_period": total_revenue,
            "total_impressions": total_impressions,
            "avg_cpm": (total_revenue / total_impressions * 1000) if total_impressions > 0 else 0
        },
        "infrastructure": {
            "locations": {"total": total_locations, "active": active_locations},
            "devices": {"total": total_devices, "online": online_devices},
            "device_uptime": (online_devices / total_devices * 100) if total_devices > 0 else 0
        }
    }


@router.get("/analytics/revenue-trends")
async def get_revenue_trends(
    current_user = Depends(require_role(["admin", "super_admin"])),
    days: int = Query(90),
    granularity: str = Query("daily")
):
    """Get revenue trends and forecasting data"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get aggregated revenue data
    revenue_data = await db_service.analytics_aggregations.find({
        "date": {"$gte": start_date}
    }).sort([("date", 1)]).to_list(None)
    
    # Group by requested granularity
    if granularity == "weekly":
        # Group by week
        weekly_data = {}
        for item in revenue_data:
            week_start = item["date"] - timedelta(days=item["date"].weekday())
            week_key = week_start.strftime("%Y-W%U")
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "period": week_key,
                    "revenue": 0,
                    "impressions": 0,
                    "plays": 0
                }
            
            weekly_data[week_key]["revenue"] += float(item.get("revenue_generated", 0))
            weekly_data[week_key]["impressions"] += item.get("total_impressions", 0)
            weekly_data[week_key]["plays"] += item.get("total_plays", 0)
        
        trend_data = list(weekly_data.values())
    
    elif granularity == "monthly":
        # Group by month
        monthly_data = {}
        for item in revenue_data:
            month_key = item["date"].strftime("%Y-%m")
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "period": month_key,
                    "revenue": 0,
                    "impressions": 0,
                    "plays": 0
                }
            
            monthly_data[month_key]["revenue"] += float(item.get("revenue_generated", 0))
            monthly_data[month_key]["impressions"] += item.get("total_impressions", 0)
            monthly_data[month_key]["plays"] += item.get("total_plays", 0)
        
        trend_data = list(monthly_data.values())
    
    else:  # daily
        trend_data = [
            {
                "period": item["date"].strftime("%Y-%m-%d"),
                "revenue": float(item.get("revenue_generated", 0)),
                "impressions": item.get("total_impressions", 0),
                "plays": item.get("total_plays", 0)
            }
            for item in revenue_data
        ]
    
    # Calculate growth rates
    if len(trend_data) >= 2:
        recent_revenue = sum(item["revenue"] for item in trend_data[-7:])  # Last 7 periods
        previous_revenue = sum(item["revenue"] for item in trend_data[-14:-7])  # Previous 7 periods
        
        growth_rate = ((recent_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
    else:
        growth_rate = 0
    
    return {
        "granularity": granularity,
        "period_days": days,
        "trend_data": trend_data,
        "growth_rate_percent": growth_rate,
        "total_revenue": sum(item["revenue"] for item in trend_data),
        "total_impressions": sum(item["impressions"] for item in trend_data)
    }


# ==============================
# AUDIT LOGS
# ==============================

@router.get("/audit/logs")
async def get_audit_logs(
    current_user = Depends(require_role(["admin", "super_admin"])),
    action_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100)
):
    """Get system audit logs"""
    
    # This would typically be implemented with a dedicated audit log collection
    # For now, we'll aggregate from moderation logs and other system events
    
    filter_query = {}
    
    if start_date:
        filter_query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in filter_query:
            filter_query["created_at"]["$lte"] = end_date
        else:
            filter_query["created_at"] = {"$lte": end_date}
    
    if user_id:
        filter_query["$or"] = [
            {"reviewer_id": user_id},
            {"created_by": user_id},
            {"approved_by": user_id}
        ]
    
    # Get moderation logs as audit events
    moderation_logs = await db_service.moderation_logs.find(filter_query).sort([("created_at", -1)]).limit(limit).to_list(None)
    
    # Format as audit events
    audit_events = []
    for log in moderation_logs:
        audit_events.append({
            "timestamp": log["created_at"],
            "action_type": "content_moderation",
            "user_id": log.get("reviewer_id"),
            "resource_type": "content",
            "resource_id": log["content_id"],
            "details": {
                "previous_status": log.get("previous_status"),
                "new_status": log.get("new_status"),
                "moderation_type": log.get("moderation_type"),
                "notes": log.get("reviewer_notes")
            }
        })
    
    return {
        "total_events": len(audit_events),
        "events": audit_events
    }


# ==============================
# SYSTEM SETTINGS
# ==============================

@router.get("/settings/system")
async def get_system_settings(
    current_user = Depends(require_role(["admin", "super_admin"]))
):
    """Get system-wide settings"""
    
    # This would typically be stored in a settings collection
    # For now, return default settings structure
    
    return {
        "moderation": {
            "ai_moderation_enabled": True,
            "ai_confidence_threshold": 0.8,
            "require_human_review": True,
            "auto_approve_trusted_advertisers": False
        },
        "booking": {
            "advance_booking_days": 30,
            "cancellation_policy_hours": 24,
            "payment_deadline_hours": 24,
            "auto_approve_bookings": False
        },
        "revenue": {
            "default_host_share_percentage": 70.0,
            "platform_fee_percentage": 30.0,
            "minimum_payout_amount": 50.00,
            "payout_frequency": "weekly"
        },
        "content": {
            "max_file_size_mb": 100,
            "allowed_formats": ["video/mp4", "image/jpeg", "image/png", "text/html"],
            "max_duration_seconds": 60,
            "content_retention_days": 365
        }
    }


@router.put("/settings/system")
async def update_system_settings(
    settings_data: dict,
    current_user = Depends(require_role(["super_admin"]))
):
    """Update system-wide settings (super admin only)"""
    
    # TODO: Implement settings update with validation
    # TODO: Log settings changes
    # TODO: Notify relevant system components of changes
    
    return {"message": "System settings updated successfully"}


# ==============================
# FRAUD DETECTION
# ==============================

@router.get("/fraud/detection")
async def get_fraud_detection_alerts(
    current_user = Depends(require_role(["admin", "super_admin"])),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query("open")
):
    """Get fraud detection alerts and suspicious activity"""
    
    # This is a placeholder for fraud detection system
    # In production, this would analyze patterns in bookings, payments, playback events, etc.
    
    # Detect suspicious booking patterns
    suspicious_bookings = await db_service.bookings.aggregate([
        {
            "$group": {
                "_id": "$advertiser_company_id",
                "booking_count": {"$sum": 1},
                "total_amount": {"$sum": "$final_price"},
                "avg_amount": {"$avg": "$final_price"}
            }
        },
        {
            "$match": {
                "booking_count": {"$gt": 50},  # High volume
                "avg_amount": {"$gt": 1000}    # High value
            }
        }
    ]).to_list(None)
    
    # Detect unusual playback patterns
    # This would analyze playback events for inconsistencies
    
    fraud_alerts = []
    
    for booking_pattern in suspicious_bookings:
        company = await db_service.companies.find_one({"_id": booking_pattern["_id"]})
        
        fraud_alerts.append({
            "alert_id": f"booking_pattern_{booking_pattern['_id']}",
            "type": "suspicious_booking_pattern",
            "severity": "medium",
            "company_id": booking_pattern["_id"],
            "company_name": company.get("name", "Unknown") if company else "Unknown",
            "details": {
                "booking_count": booking_pattern["booking_count"],
                "total_amount": float(booking_pattern["total_amount"]),
                "avg_amount": float(booking_pattern["avg_amount"])
            },
            "created_at": datetime.utcnow(),
            "status": "open"
        })
    
    return {
        "total_alerts": len(fraud_alerts),
        "alerts": fraud_alerts
    }