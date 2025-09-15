"""
Event Management API - Monitor and manage event-driven architecture
Provides endpoints for monitoring event processing, metrics, and troubleshooting
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.events.event_manager import event_manager
from app.api.auth import get_current_user, require_roles
from app.models import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Event Management"])

@router.get("/health")
async def get_event_system_health(
    current_user: UserProfile = Depends(require_roles("SUPER_USER"))
):
    """Get event system health status (Super User only)"""
    try:
        metrics = event_manager.get_metrics()
        handler_status = await event_manager.get_handler_status()

        return {
            "status": "healthy" if metrics["status"] == "initialized" else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "handlers": handler_status
        }

    except Exception as e:
        logger.error(f"Failed to get event system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_event_metrics(
    current_user: UserProfile = Depends(require_roles("SUPER_USER"))
):
    """Get detailed event processing metrics (Super User only)"""
    try:
        metrics = event_manager.get_metrics()

        # Additional computed metrics
        event_bus_metrics = metrics.get("event_bus", {})
        processed_count = event_bus_metrics.get("events_processed", 0)
        failed_count = event_bus_metrics.get("events_failed", 0)
        total_events = processed_count + failed_count

        success_rate = (processed_count / total_events * 100) if total_events > 0 else 100

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_events": total_events,
                "processed_events": processed_count,
                "failed_events": failed_count,
                "success_rate": round(success_rate, 2),
                "queue_size": event_bus_metrics.get("queue_size", 0),
                "active_handlers": metrics.get("handlers_count", 0)
            },
            "detailed_metrics": metrics,
            "status": metrics.get("status", "unknown")
        }

    except Exception as e:
        logger.error(f"Failed to get event metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-event")
async def publish_test_event(
    event_type: str = Query(..., description="Event type to test"),
    current_user: UserProfile = Depends(require_roles("SUPER_USER"))
):
    """Publish a test event for system validation (Super User only)"""
    try:
        from app.events.event_manager import publish_content_event
        import uuid

        test_payload = {
            "test": True,
            "test_id": str(uuid.uuid4()),
            "initiated_by": current_user.id,
            "timestamp": datetime.utcnow().isoformat()
        }

        await publish_content_event(
            event_type=event_type,
            content_id=f"test_{uuid.uuid4()}",
            company_id=current_user.company_id,
            user_id=current_user.id,
            payload=test_payload,
            correlation_id=f"test_{uuid.uuid4()}"
        )

        return {
            "message": f"Test event '{event_type}' published successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": test_payload
        }

    except Exception as e:
        logger.error(f"Failed to publish test event: {e}")
        raise HTTPException(status_code=500, detail=str(e))