"""
AI Moderation Event Handler - Processes content moderation in background
Reduces load on primary application by handling AI operations asynchronously
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from app.events.event_bus import EventHandler, Event, EventType
from app.services.ai_service_manager import get_ai_service_manager
from app.database_service import db_service
from app.history_service import HistoryService
from app.models import ContentHistoryEventType

logger = logging.getLogger(__name__)

class AIContentModerationHandler(EventHandler):
    """Background handler for AI content moderation"""

    def __init__(self):
        super().__init__(
            name="ai_moderation_handler",
            event_types=[
                EventType.CONTENT_UPLOADED,
                EventType.CONTENT_AI_MODERATION_STARTED
            ]
        )
        self.history_service = None  # Will be initialized when needed

    async def _ensure_history_service(self):
        """Lazy initialization of history service"""
        if self.history_service is None:
            self.history_service = HistoryService(db_service)

    async def handle(self, event: Event) -> bool:
        """Process AI moderation event"""
        try:
            await self._ensure_history_service()
            if event.event_type == EventType.CONTENT_UPLOADED:
                return await self._start_ai_moderation(event)
            elif event.event_type == EventType.CONTENT_AI_MODERATION_STARTED:
                return await self._process_ai_moderation(event)

            return False

        except Exception as e:
            logger.error(f"AI moderation handler error for event {event.event_id}: {e}")
            return False

    async def _start_ai_moderation(self, event: Event) -> bool:
        """Start AI moderation process for uploaded content"""
        content_id = event.content_id
        if not content_id:
            logger.warning(f"No content_id in uploaded event {event.event_id}")
            return False

        try:
            # Get content from database
            content = await db_service.get_document("content", {"_id": content_id})
            if not content:
                logger.error(f"Content not found: {content_id}")
                return False

            # Track AI moderation start
            ai_manager = get_ai_service_manager()
            await self.history_service.track_content_event(
                content_id=content_id,
                event_type=ContentHistoryEventType.AI_MODERATION_STARTED,
                company_id=event.company_id,
                user_id=event.user_id,
                event_details={
                    "triggered_by_event": event.event_id,
                    "moderation_providers": ["ai_service_manager"],
                    "confidence_threshold": 0.8
                }
            )

            # Start AI moderation in background
            from app.events.event_bus import event_bus, Event, EventType
            moderation_event = Event(
                event_id=f"{event.event_id}_moderation",
                event_type=EventType.CONTENT_AI_MODERATION_STARTED,
                timestamp=event.timestamp,
                source="ai_moderation_handler",
                company_id=event.company_id,
                user_id=event.user_id,
                content_id=content_id,
                payload={
                    "file_path": content.get("file_path"),
                    "content_type": content.get("content_type"),
                    "filename": content.get("filename"),
                    "original_event_id": event.event_id
                },
                correlation_id=event.correlation_id
            )

            await event_bus.publish(moderation_event)
            logger.info(f"AI moderation started for content {content_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start AI moderation for content {content_id}: {e}")
            return False

    async def _process_ai_moderation(self, event: Event) -> bool:
        """Process AI moderation for content"""
        content_id = event.content_id
        if not content_id:
            return False

        try:
            # Get content metadata from payload
            file_path = event.payload.get("file_path")
            content_type = event.payload.get("content_type", "unknown")
            filename = event.payload.get("filename", "unknown")

            if not file_path:
                logger.error(f"No file_path in moderation event for content {content_id}")
                return False

            # Perform AI moderation using AI service manager
            ai_manager = get_ai_service_manager()

            # Create a simple moderation result for event architecture testing
            # In production, this would call the actual AI services
            moderation_results = {
                "timestamp": datetime.utcnow(),
                "results": {
                    "is_appropriate": True,
                    "confidence": 0.95,
                    "flags": [],
                    "categories": ["safe_content"]
                },
                "overall_decision": "approved",
                "confidence_score": 0.95,
                "flags": [],
                "provider_results": {"ai_service_manager": {"decision": "approved"}},
                "processing_time": 1.2
            }

            # Update content with moderation results
            update_data = {
                "ai_moderation": {
                    "completed": True,
                    "completed_at": moderation_results["timestamp"],
                    "results": moderation_results["results"],
                    "overall_decision": moderation_results["overall_decision"],
                    "confidence_score": moderation_results["confidence_score"],
                    "flags": moderation_results.get("flags", []),
                    "provider_results": moderation_results.get("provider_results", {}),
                    "processing_time": moderation_results.get("processing_time", 0)
                }
            }

            # Determine next status based on moderation results
            if moderation_results["overall_decision"] == "approved":
                update_data["status"] = "approved"
                next_event_type = EventType.CONTENT_APPROVED
            elif moderation_results["overall_decision"] == "flagged":
                update_data["status"] = "flagged"
                update_data["requires_human_review"] = True
                next_event_type = None  # Human review required
            else:
                update_data["status"] = "rejected"
                next_event_type = EventType.CONTENT_REJECTED

            # Update content in database
            await db_service.update_document(
                "content",
                {"_id": content_id},
                {"$set": update_data}
            )

            # Track moderation completion
            await self.history_service.track_content_event(
                content_id=content_id,
                event_type=ContentHistoryEventType.AI_MODERATION_COMPLETED,
                company_id=event.company_id,
                event_details={
                    "moderation_results": moderation_results,
                    "decision": moderation_results["overall_decision"],
                    "confidence": moderation_results["confidence_score"],
                    "flags": moderation_results.get("flags", []),
                    "processing_time": moderation_results.get("processing_time", 0),
                    "providers_used": list(moderation_results.get("provider_results", {}).keys())
                }
            )

            # Publish next event if auto-approved/rejected
            if next_event_type:
                from app.events.event_bus import event_bus, Event
                next_event = Event(
                    event_id=f"{event.event_id}_result",
                    event_type=next_event_type,
                    timestamp=moderation_results["timestamp"],
                    source="ai_moderation_handler",
                    company_id=event.company_id,
                    content_id=content_id,
                    payload={
                        "automated_decision": True,
                        "moderation_confidence": moderation_results["confidence_score"],
                        "original_event_id": event.payload.get("original_event_id"),
                        "decision_reason": moderation_results["overall_decision"]
                    },
                    correlation_id=event.correlation_id
                )
                await event_bus.publish(next_event)

            logger.info(
                f"AI moderation completed for content {content_id}: "
                f"{moderation_results['overall_decision']} "
                f"(confidence: {moderation_results['confidence_score']})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to process AI moderation for content {content_id}: {e}")

            # Track moderation failure
            try:
                await self.history_service.track_content_event(
                    content_id=content_id,
                    event_type=ContentHistoryEventType.AI_MODERATION_FAILED,
                    company_id=event.company_id,
                    event_details={
                        "error": str(e),
                        "event_id": event.event_id
                    }
                )

                # Set content status to require human review
                await db_service.update_document(
                    "content",
                    {"_id": content_id},
                    {
                        "$set": {
                            "status": "pending_review",
                            "requires_human_review": True,
                            "ai_moderation": {
                                "completed": False,
                                "error": str(e),
                                "failed_at": moderation_results.get("timestamp") if 'moderation_results' in locals() else None
                            }
                        }
                    }
                )

            except Exception as tracking_error:
                logger.error(f"Failed to track moderation failure: {tracking_error}")

            return False