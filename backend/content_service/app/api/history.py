"""
Content History and Audit API Endpoints
Provides comprehensive tracking and querying of content lifecycle events.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.models import (
    ContentHistory, ContentHistoryQuery, ContentLifecycleSummary,
    ContentAuditReport, ContentTimelineView, ContentHistoryEventType
)
from app.history_service import HistoryService
from app.database_service import db_service
from app.api.auth import get_current_user
from app.rbac_service import RBACService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/history", tags=["Content History"])

# Initialize services
history_service = HistoryService(db_service)
rbac_service = RBACService()


@router.get("/content", response_model=List[ContentHistory])
async def get_content_history(
    content_ids: Optional[str] = Query(None, description="Comma-separated content IDs"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types"),
    user_ids: Optional[str] = Query(None, description="Comma-separated user IDs"),
    device_ids: Optional[str] = Query(None, description="Comma-separated device IDs"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    include_system_events: bool = Query(True, description="Include system-generated events"),
    include_error_events: bool = Query(True, description="Include error events"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user=Depends(get_current_user)
):
    """
    Get content history with filtering options.
    Requires content_read permission.
    """
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user.id, current_user.company_id, "content", "read"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view content history")

        # Parse query parameters
        query = ContentHistoryQuery(
            content_ids=content_ids.split(",") if content_ids else None,
            event_types=[ContentHistoryEventType(et.strip()) for et in event_types.split(",")] if event_types else None,
            user_ids=user_ids.split(",") if user_ids else None,
            device_ids=device_ids.split(",") if device_ids else None,
            start_date=start_date,
            end_date=end_date,
            include_system_events=include_system_events,
            include_error_events=include_error_events,
            limit=limit,
            offset=offset,
            sort_order=sort_order
        )

        # Get history events
        history_events = await history_service.get_content_history(query, current_user.company_id)

        return history_events

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get content history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content history")


@router.get("/content/{content_id}/timeline", response_model=ContentTimelineView)
async def get_content_timeline(
    content_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get timeline view for a specific content item.
    Shows complete lifecycle with milestones and performance metrics.
    """
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user.id, current_user.company_id, "content", "read"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view content timeline")

        timeline = await history_service.get_content_timeline(content_id, current_user.company_id)

        return timeline

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content timeline")


@router.get("/content/{content_id}/lifecycle", response_model=ContentLifecycleSummary)
async def get_content_lifecycle_summary(
    content_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get comprehensive lifecycle summary for specific content.
    Includes performance metrics, user involvement, and key timestamps.
    """
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user.id, current_user.company_id, "content", "read"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view content lifecycle")

        summary = await history_service.get_content_lifecycle_summary(content_id, current_user.company_id)

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content lifecycle summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve lifecycle summary")


@router.get("/audit/report", response_model=ContentAuditReport)
async def generate_audit_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    report_type: str = Query("custom", description="Type of report (daily, weekly, monthly, custom)"),
    current_user=Depends(get_current_user)
):
    """
    Generate comprehensive audit report for a date range.
    Requires admin permissions or analytics_read permission.
    """
    try:
        # Check permissions (admin or analytics read)
        is_admin = current_user.company_role == "ADMIN"
        has_analytics = await rbac_service.check_permission(
            current_user.id, current_user.company_id, "analytics", "read"
        )

        if not (is_admin or has_analytics):
            raise HTTPException(status_code=403, detail="Insufficient permissions to generate audit reports")

        # Validate date range
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")

        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")

        # Generate report
        report = await history_service.generate_audit_report(
            company_id=current_user.company_id,
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
            generated_by=current_user.id
        )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate audit report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate audit report")


@router.get("/stats/summary")
async def get_history_stats_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user=Depends(get_current_user)
):
    """
    Get summary statistics for content history over the specified period.
    """
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user.id, current_user.company_id, "analytics", "read"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view history statistics")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get history events for the period
        filters = {
            "company_id": current_user.company_id,
            "event_timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        history_events = await db_service.find_content_history(filters=filters, limit=10000)

        # Calculate statistics
        stats = {
            "total_events": len(history_events),
            "events_by_type": {},
            "events_by_day": {},
            "error_rate": 0,
            "most_active_content": {},
            "recent_activity": [],
            "performance_trends": {}
        }

        # Process events
        for event in history_events:
            event_type = event["event_type"]
            event_date = event["event_timestamp"].date().isoformat()
            content_id = event["content_id"]

            # Count by type
            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1

            # Count by day
            stats["events_by_day"][event_date] = stats["events_by_day"].get(event_date, 0) + 1

            # Track content activity
            stats["most_active_content"][content_id] = stats["most_active_content"].get(content_id, 0) + 1

        # Calculate error rate
        error_events = sum(1 for event in history_events if event.get("error_code"))
        stats["error_rate"] = (error_events / len(history_events) * 100) if history_events else 0

        # Get recent activity (last 10 events)
        recent_events = sorted(history_events, key=lambda x: x["event_timestamp"], reverse=True)[:10]
        stats["recent_activity"] = [
            {
                "content_id": event["content_id"],
                "event_type": event["event_type"],
                "timestamp": event["event_timestamp"],
                "user": event.get("triggered_by_user_name", "System"),
                "success": not event.get("error_code")
            }
            for event in recent_events
        ]

        # Format most active content (top 5)
        stats["most_active_content"] = [
            {"content_id": content_id, "event_count": count}
            for content_id, count in sorted(
                stats["most_active_content"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]

        return stats

    except Exception as e:
        logger.error(f"Failed to get history stats summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history statistics")


@router.get("/events/recent")
async def get_recent_events(
    limit: int = Query(20, ge=1, le=100, description="Number of recent events to return"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types to filter"),
    current_user=Depends(get_current_user)
):
    """
    Get most recent content history events for the current company.
    """
    try:
        # Check permissions
        if not await rbac_service.check_permission(
            current_user.id, current_user.company_id, "content", "read"
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view content events")

        # Build filters
        filters = {"company_id": current_user.company_id}

        if event_types:
            event_type_list = [et.strip() for et in event_types.split(",")]
            filters["event_type"] = {"$in": event_type_list}

        # Get recent events
        history_events = await db_service.find_content_history(
            filters=filters,
            limit=limit,
            sort=[("event_timestamp", -1)]
        )

        # Format response
        formatted_events = []
        for event in history_events:
            formatted_event = {
                "id": event["id"],
                "content_id": event["content_id"],
                "event_type": event["event_type"],
                "timestamp": event["event_timestamp"],
                "user_name": event.get("triggered_by_user_name", "System"),
                "user_type": event.get("triggered_by_user_type", "system"),
                "success": not event.get("error_code"),
                "error_message": event.get("error_message"),
                "device_id": event.get("device_id"),
                "processing_time_ms": event.get("processing_time_ms"),
                "details": event.get("event_details", {})
            }
            formatted_events.append(formatted_event)

        return {
            "events": formatted_events,
            "total_count": len(formatted_events),
            "company_id": current_user.company_id
        }

    except Exception as e:
        logger.error(f"Failed to get recent events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent events")