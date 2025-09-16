#!/usr/bin/env python3
"""
Content Moderation API - Digital Signage Ad Slot Management System
API endpoints for AI-assisted moderation and human review workflow
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio

from app.models.ad_slot_models import (
    Content, ContentStatus, ModerationLog
)
from app.auth_service import get_current_user, require_role
from app.database_service import db_service

router = APIRouter(prefix="/moderation", tags=["Content Moderation"])


# ==============================
# AI MODERATION PIPELINE
# ==============================

@router.post("/ai-review/{content_id}")
async def trigger_ai_moderation(
    content_id: str,
    current_user = Depends(require_role(["admin", "reviewer"]))
):
    """Trigger AI moderation for content"""
    
    content = await db_service.content.find_one({"_id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content.get("status") not in ["submitted", "ai_review"]:
        raise HTTPException(status_code=400, detail="Content not eligible for AI moderation")
    
    # Update status to AI review
    await db_service.content.update_one(
        {"_id": content_id},
        {"$set": {
            "status": ContentStatus.AI_REVIEW,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Trigger AI moderation process
    ai_result = await run_ai_moderation(content)
    
    # Update content with AI results
    update_data = {
        "ai_moderation_score": ai_result["confidence_score"],
        "ai_moderation_flags": ai_result["flags"],
        "updated_at": datetime.utcnow()
    }
    
    # Determine next status based on AI results
    if ai_result["confidence_score"] >= 0.9 and not ai_result["flags"]:
        # High confidence, clean content - auto-approve
        update_data["status"] = ContentStatus.APPROVED
        next_status = ContentStatus.APPROVED
    elif ai_result["confidence_score"] <= 0.3 or "high_risk" in ai_result["flags"]:
        # High risk content - send to human review
        update_data["status"] = ContentStatus.HUMAN_REVIEW
        next_status = ContentStatus.HUMAN_REVIEW
    else:
        # Medium risk - quarantine for review
        update_data["status"] = ContentStatus.QUARANTINED
        next_status = ContentStatus.QUARANTINED
    
    await db_service.content.update_one(
        {"_id": content_id},
        {"$set": update_data}
    )
    
    # Log moderation action
    moderation_log = ModerationLog(
        content_id=content_id,
        moderation_type="ai",
        previous_status=content.get("status"),
        new_status=next_status,
        ai_confidence_score=ai_result["confidence_score"],
        ai_flags=ai_result["flags"],
        ai_model_version=ai_result.get("model_version", "1.0")
    )
    
    await db_service.moderation_logs.insert_one(moderation_log.dict())
    
    return {
        "content_id": content_id,
        "ai_result": ai_result,
        "new_status": next_status,
        "requires_human_review": next_status in [ContentStatus.HUMAN_REVIEW, ContentStatus.QUARANTINED]
    }


async def run_ai_moderation(content: dict) -> dict:
    """Run AI moderation checks on content"""
    
    # This is a placeholder for AI moderation integration
    # In production, this would integrate with services like:
    # - Azure Content Safety
    # - Google Cloud Video Intelligence
    # - AWS Rekognition
    # - Custom ML models
    
    flags = []
    confidence_score = 0.8  # Default safe score
    
    content_type = content.get("content_type", "")
    
    # Text content analysis
    if content.get("title") or content.get("description"):
        text_result = await analyze_text_content(
            content.get("title", "") + " " + content.get("description", "")
        )
        flags.extend(text_result["flags"])
        confidence_score = min(confidence_score, text_result["confidence"])
    
    # Image content analysis
    if content_type.startswith("image/"):
        image_result = await analyze_image_content(content.get("file_path"))
        flags.extend(image_result["flags"])
        confidence_score = min(confidence_score, image_result["confidence"])
    
    # Video content analysis
    elif content_type.startswith("video/"):
        video_result = await analyze_video_content(content.get("file_path"))
        flags.extend(video_result["flags"])
        confidence_score = min(confidence_score, video_result["confidence"])
    
    # HTML content analysis
    elif content_type == "text/html":
        html_result = await analyze_html_content(content.get("file_path"))
        flags.extend(html_result["flags"])
        confidence_score = min(confidence_score, html_result["confidence"])
    
    # Brand safety checks
    brand_safety_result = await check_brand_safety(content)
    flags.extend(brand_safety_result["flags"])
    confidence_score = min(confidence_score, brand_safety_result["confidence"])
    
    return {
        "confidence_score": confidence_score,
        "flags": list(set(flags)),  # Remove duplicates
        "model_version": "ai_moderation_v1.0",
        "processed_at": datetime.utcnow().isoformat()
    }


async def analyze_text_content(text: str) -> dict:
    """Analyze text content for harmful content"""
    
    # Placeholder for text analysis
    # Real implementation would use NLP models to detect:
    # - Hate speech
    # - Violent content
    # - Adult content
    # - Spam/misleading content
    # - Copyright violations
    
    flags = []
    confidence = 0.9
    
    # Simple keyword checks (placeholder)
    harmful_keywords = ["violence", "hate", "spam", "scam", "fake"]
    text_lower = text.lower()
    
    for keyword in harmful_keywords:
        if keyword in text_lower:
            flags.append(f"text_{keyword}")
            confidence = 0.4
    
    return {"flags": flags, "confidence": confidence}


async def analyze_image_content(file_path: str) -> dict:
    """Analyze image content for harmful content"""
    
    # Placeholder for image analysis
    # Real implementation would use computer vision models to detect:
    # - Nudity/adult content
    # - Violence/weapons
    # - Inappropriate content
    # - Copyright violations
    # - Brand logos without permission
    
    flags = []
    confidence = 0.9
    
    # Simulate AI analysis
    await asyncio.sleep(0.1)  # Simulate processing time
    
    return {"flags": flags, "confidence": confidence}


async def analyze_video_content(file_path: str) -> dict:
    """Analyze video content for harmful content"""
    
    # Placeholder for video analysis
    # Real implementation would:
    # 1. Extract frames at intervals
    # 2. Analyze each frame for visual content
    # 3. Extract audio and analyze speech
    # 4. Check for inappropriate scenes
    # 5. Verify copyright compliance
    
    flags = []
    confidence = 0.9
    
    # Simulate AI analysis
    await asyncio.sleep(0.5)  # Simulate processing time
    
    return {"flags": flags, "confidence": confidence}


async def analyze_html_content(file_path: str) -> dict:
    """Analyze HTML content for security and policy violations"""
    
    # Placeholder for HTML analysis
    # Real implementation would check for:
    # - Malicious scripts
    # - Unauthorized redirects
    # - Privacy violations
    # - Inappropriate content
    # - Copyright violations
    
    flags = []
    confidence = 0.9
    
    # Simulate security scan
    await asyncio.sleep(0.2)
    
    return {"flags": flags, "confidence": confidence}


async def check_brand_safety(content: dict) -> dict:
    """Check content against brand safety guidelines"""
    
    # Placeholder for brand safety checks
    # Real implementation would verify:
    # - Advertiser brand guidelines
    # - Industry-specific restrictions
    # - Location-specific content policies
    # - Cultural sensitivity
    
    flags = []
    confidence = 0.95
    
    # Check content rating vs allowed ratings
    content_rating = content.get("content_rating", "G")
    if content_rating in ["R", "NC-17"]:
        flags.append("high_content_rating")
        confidence = 0.3
    
    return {"flags": flags, "confidence": confidence}


# ==============================
# HUMAN REVIEW WORKFLOW
# ==============================

@router.get("/review-queue")
async def get_review_queue(
    current_user = Depends(require_role(["reviewer", "admin"])),
    status: Optional[str] = Query("human_review"),
    priority: Optional[str] = Query("high"),
    limit: int = Query(20)
):
    """Get content items for human review"""
    
    filter_query = {}
    
    if status:
        if status == "pending":
            filter_query["status"] = {"$in": [ContentStatus.HUMAN_REVIEW, ContentStatus.QUARANTINED]}
        else:
            filter_query["status"] = status
    
    # Sort by AI risk score and submission time
    sort_criteria = []
    if priority == "high":
        sort_criteria.append(("ai_moderation_score", 1))  # Low confidence first (higher risk)
    sort_criteria.append(("created_at", 1))  # Older first
    
    content_items = await db_service.content.find(filter_query).sort(sort_criteria).limit(limit).to_list(None)
    
    # Enrich with additional context
    enriched_items = []
    for content in content_items:
        # Get advertiser company info
        company = await db_service.companies.find_one({"_id": content["advertiser_company_id"]})
        
        # Get moderation history
        moderation_logs = await db_service.moderation_logs.find({
            "content_id": content["_id"]
        }).sort([("created_at", -1)]).to_list(None)
        
        # Get related bookings
        related_bookings = await db_service.bookings.find({
            "content_id": content["_id"]
        }).to_list(None)
        
        enriched_items.append({
            "content": Content(**content),
            "company": company,
            "moderation_history": moderation_logs,
            "related_bookings": related_bookings,
            "ai_flags": content.get("ai_moderation_flags", []),
            "ai_confidence": content.get("ai_moderation_score", 1.0),
            "submission_age_hours": (datetime.utcnow() - content["created_at"]).total_seconds() / 3600
        })
    
    return {
        "queue_size": len(enriched_items),
        "items": enriched_items
    }


@router.post("/review/{content_id}/approve")
async def approve_content(
    content_id: str,
    approval_data: dict,
    current_user = Depends(require_role(["reviewer", "admin"]))
):
    """Approve content after human review"""
    
    content = await db_service.content.find_one({"_id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content.get("status") not in [ContentStatus.HUMAN_REVIEW, ContentStatus.QUARANTINED]:
        raise HTTPException(status_code=400, detail="Content not eligible for approval")
    
    # Update content status
    update_data = {
        "status": ContentStatus.APPROVED,
        "reviewed_by": current_user.id,
        "reviewed_at": datetime.utcnow(),
        "human_review_notes": approval_data.get("notes", ""),
        "updated_at": datetime.utcnow()
    }
    
    # Add any approval conditions
    if approval_data.get("conditions"):
        update_data["approval_conditions"] = approval_data["conditions"]
    
    await db_service.content.update_one(
        {"_id": content_id},
        {"$set": update_data}
    )
    
    # Log moderation action
    moderation_log = ModerationLog(
        content_id=content_id,
        moderation_type="human",
        previous_status=content.get("status"),
        new_status=ContentStatus.APPROVED,
        reviewer_id=current_user.id,
        reviewer_notes=approval_data.get("notes", ""),
        decision_reason=approval_data.get("reason", "Content meets guidelines")
    )
    
    await db_service.moderation_logs.insert_one(moderation_log.dict())
    
    # Update any related bookings
    await db_service.bookings.update_many(
        {"content_id": content_id},
        {"$set": {"content_approved": True, "updated_at": datetime.utcnow()}}
    )
    
    # TODO: Send notification to advertiser
    # TODO: Trigger content deployment if bookings are approved
    
    return {
        "message": "Content approved successfully",
        "content_id": content_id,
        "approved_by": current_user.id
    }


@router.post("/review/{content_id}/reject")
async def reject_content(
    content_id: str,
    rejection_data: dict,
    current_user = Depends(require_role(["reviewer", "admin"]))
):
    """Reject content after human review"""
    
    content = await db_service.content.find_one({"_id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if content.get("status") not in [ContentStatus.HUMAN_REVIEW, ContentStatus.QUARANTINED]:
        raise HTTPException(status_code=400, detail="Content not eligible for rejection")
    
    # Update content status
    await db_service.content.update_one(
        {"_id": content_id},
        {"$set": {
            "status": ContentStatus.REJECTED,
            "reviewed_by": current_user.id,
            "reviewed_at": datetime.utcnow(),
            "human_review_notes": rejection_data.get("notes", ""),
            "rejection_reason": rejection_data.get("reason", "Content violates guidelines"),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Log moderation action
    moderation_log = ModerationLog(
        content_id=content_id,
        moderation_type="human",
        previous_status=content.get("status"),
        new_status=ContentStatus.REJECTED,
        reviewer_id=current_user.id,
        reviewer_notes=rejection_data.get("notes", ""),
        decision_reason=rejection_data.get("reason", "Content violates guidelines")
    )
    
    await db_service.moderation_logs.insert_one(moderation_log.dict())
    
    # Cancel any related bookings
    related_bookings = await db_service.bookings.find({"content_id": content_id}).to_list(None)
    
    for booking in related_bookings:
        if booking.get("status") in ["pending", "approved"]:
            await db_service.bookings.update_one(
                {"_id": booking["_id"]},
                {"$set": {
                    "status": "cancelled",
                    "cancellation_reason": "Content rejected during moderation",
                    "updated_at": datetime.utcnow()
                }}
            )
    
    # TODO: Send notification to advertiser with rejection reason
    # TODO: Process refunds for cancelled bookings
    
    return {
        "message": "Content rejected",
        "content_id": content_id,
        "rejected_by": current_user.id,
        "affected_bookings": len(related_bookings)
    }


@router.post("/review/{content_id}/quarantine")
async def quarantine_content(
    content_id: str,
    quarantine_data: dict,
    current_user = Depends(require_role(["reviewer", "admin"]))
):
    """Quarantine content for further investigation"""
    
    content = await db_service.content.find_one({"_id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Update content status
    await db_service.content.update_one(
        {"_id": content_id},
        {"$set": {
            "status": ContentStatus.QUARANTINED,
            "reviewed_by": current_user.id,
            "reviewed_at": datetime.utcnow(),
            "human_review_notes": quarantine_data.get("notes", ""),
            "quarantine_reason": quarantine_data.get("reason", "Requires further investigation"),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Log moderation action
    moderation_log = ModerationLog(
        content_id=content_id,
        moderation_type="human",
        previous_status=content.get("status"),
        new_status=ContentStatus.QUARANTINED,
        reviewer_id=current_user.id,
        reviewer_notes=quarantine_data.get("notes", ""),
        decision_reason=quarantine_data.get("reason", "Requires further investigation")
    )
    
    await db_service.moderation_logs.insert_one(moderation_log.dict())
    
    # Pause any related bookings
    await db_service.bookings.update_many(
        {"content_id": content_id, "status": {"$in": ["pending", "approved"]}},
        {"$set": {
            "status": "paused",
            "pause_reason": "Content under investigation",
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {
        "message": "Content quarantined for investigation",
        "content_id": content_id,
        "quarantined_by": current_user.id
    }


# ==============================
# BATCH MODERATION OPERATIONS
# ==============================

@router.post("/batch-review")
async def batch_review_content(
    batch_data: dict,
    current_user = Depends(require_role(["reviewer", "admin"]))
):
    """Review multiple content items at once"""
    
    content_ids = batch_data.get("content_ids", [])
    action = batch_data.get("action")  # approve, reject, quarantine
    notes = batch_data.get("notes", "")
    reason = batch_data.get("reason", "")
    
    if not content_ids or not action:
        raise HTTPException(status_code=400, detail="Missing content_ids or action")
    
    if action not in ["approve", "reject", "quarantine"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    results = []
    
    for content_id in content_ids:
        try:
            if action == "approve":
                result = await approve_content(content_id, {"notes": notes, "reason": reason}, current_user)
            elif action == "reject":
                result = await reject_content(content_id, {"notes": notes, "reason": reason}, current_user)
            elif action == "quarantine":
                result = await quarantine_content(content_id, {"notes": notes, "reason": reason}, current_user)
            
            results.append({
                "content_id": content_id,
                "status": "success",
                "action": action
            })
        
        except Exception as e:
            results.append({
                "content_id": content_id,
                "status": "error",
                "error": str(e)
            })
    
    successful_actions = len([r for r in results if r["status"] == "success"])
    
    return {
        "message": f"Batch review completed: {successful_actions}/{len(content_ids)} successful",
        "results": results
    }


# ==============================
# MODERATION ANALYTICS
# ==============================

@router.get("/analytics/performance")
async def get_moderation_performance(
    current_user = Depends(require_role(["reviewer", "admin"])),
    days: int = Query(30),
    reviewer_id: Optional[str] = Query(None)
):
    """Get moderation performance metrics"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Build filter for moderation logs
    filter_query = {"created_at": {"$gte": start_date}}
    
    if reviewer_id:
        filter_query["reviewer_id"] = reviewer_id
    elif current_user.role == "reviewer":
        # Reviewers can only see their own performance
        filter_query["reviewer_id"] = current_user.id
    
    # Get moderation logs
    moderation_logs = await db_service.moderation_logs.find(filter_query).to_list(None)
    
    # Calculate metrics
    total_reviews = len(moderation_logs)
    approvals = len([log for log in moderation_logs if log.get("new_status") == "approved"])
    rejections = len([log for log in moderation_logs if log.get("new_status") == "rejected"])
    quarantines = len([log for log in moderation_logs if log.get("new_status") == "quarantined"])
    
    # Calculate processing times
    processing_times = []
    for log in moderation_logs:
        if log.get("moderation_type") == "human":
            # Find original submission
            content = await db_service.content.find_one({"_id": log["content_id"]})
            if content:
                processing_time = (log["created_at"] - content["created_at"]).total_seconds() / 3600  # hours
                processing_times.append(processing_time)
    
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Daily breakdown
    daily_breakdown = {}
    for log in moderation_logs:
        date_key = log["created_at"].strftime("%Y-%m-%d")
        if date_key not in daily_breakdown:
            daily_breakdown[date_key] = {"approvals": 0, "rejections": 0, "quarantines": 0}
        
        if log.get("new_status") == "approved":
            daily_breakdown[date_key]["approvals"] += 1
        elif log.get("new_status") == "rejected":
            daily_breakdown[date_key]["rejections"] += 1
        elif log.get("new_status") == "quarantined":
            daily_breakdown[date_key]["quarantines"] += 1
    
    return {
        "period_days": days,
        "total_reviews": total_reviews,
        "approvals": approvals,
        "rejections": rejections,
        "quarantines": quarantines,
        "approval_rate": (approvals / total_reviews * 100) if total_reviews > 0 else 0,
        "rejection_rate": (rejections / total_reviews * 100) if total_reviews > 0 else 0,
        "avg_processing_time_hours": avg_processing_time,
        "daily_breakdown": daily_breakdown
    }


@router.get("/analytics/content-trends")
async def get_content_moderation_trends(
    current_user = Depends(require_role(["admin", "reviewer"])),
    days: int = Query(90)
):
    """Get content moderation trends and patterns"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get content submissions
    content_items = await db_service.content.find({
        "created_at": {"$gte": start_date}
    }).to_list(None)
    
    # Analyze trends
    content_by_type = {}
    content_by_status = {}
    ai_flag_frequency = {}
    
    for content in content_items:
        # Content type distribution
        content_type = content.get("content_type", "unknown")
        content_by_type[content_type] = content_by_type.get(content_type, 0) + 1
        
        # Status distribution
        status = content.get("status", "unknown")
        content_by_status[status] = content_by_status.get(status, 0) + 1
        
        # AI flag analysis
        ai_flags = content.get("ai_moderation_flags", [])
        for flag in ai_flags:
            ai_flag_frequency[flag] = ai_flag_frequency.get(flag, 0) + 1
    
    # Calculate submission trends (weekly)
    weekly_submissions = {}
    for content in content_items:
        week_start = content["created_at"] - timedelta(days=content["created_at"].weekday())
        week_key = week_start.strftime("%Y-W%U")
        weekly_submissions[week_key] = weekly_submissions.get(week_key, 0) + 1
    
    return {
        "period_days": days,
        "total_submissions": len(content_items),
        "content_by_type": content_by_type,
        "content_by_status": content_by_status,
        "ai_flag_frequency": ai_flag_frequency,
        "weekly_submission_trend": weekly_submissions,
        "avg_ai_confidence": sum(c.get("ai_moderation_score", 1.0) for c in content_items) / len(content_items) if content_items else 1.0
    }


# ==============================
# MODERATION RULES MANAGEMENT
# ==============================

@router.get("/rules")
async def get_moderation_rules(
    current_user = Depends(require_role(["admin", "reviewer"]))
):
    """Get current moderation rules and guidelines"""
    
    # This would typically be stored in a database
    # For now, return static rules structure
    
    return {
        "content_policies": {
            "prohibited_content": [
                "Violent or graphic content",
                "Adult or sexually explicit content",
                "Hate speech or discriminatory content",
                "Spam or misleading information",
                "Copyright infringing content",
                "Illegal products or services"
            ],
            "restricted_content": [
                "Political advertising (requires special approval)",
                "Health/medical claims (requires verification)",
                "Financial services (requires compliance check)",
                "Alcohol/tobacco (location restrictions apply)"
            ]
        },
        "ai_moderation_thresholds": {
            "auto_approve_threshold": 0.9,
            "auto_reject_threshold": 0.3,
            "human_review_threshold": 0.7
        },
        "review_timeframes": {
            "standard_review_hours": 24,
            "priority_review_hours": 4,
            "urgent_review_hours": 1
        },
        "escalation_rules": {
            "auto_escalate_to_admin": ["copyright_violation", "legal_concern"],
            "require_senior_review": ["borderline_content", "cultural_sensitivity"]
        }
    }


@router.put("/rules")
async def update_moderation_rules(
    rules_data: dict,
    current_user = Depends(require_role(["admin"]))
):
    """Update moderation rules and guidelines (admin only)"""
    
    # TODO: Implement rules update with validation
    # TODO: Log rules changes
    # TODO: Notify reviewers of rule changes
    
    return {"message": "Moderation rules updated successfully"}