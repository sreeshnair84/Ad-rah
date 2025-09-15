"""
Event Manager - Central coordinator for event-driven architecture
Initializes event bus and registers all event handlers
"""
import logging
import asyncio
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from app.events.event_bus import event_bus, AsyncEventBus
from app.events.handlers.ai_moderation_handler import AIContentModerationHandler
from app.events.handlers.analytics_handler import AnalyticsHandler
from app.events.handlers.notification_handler import NotificationHandler

logger = logging.getLogger(__name__)

class EventManager:
    """Central manager for event-driven architecture"""

    def __init__(self):
        self.event_bus: AsyncEventBus = event_bus
        self.handlers = {}
        self._initialized = False

    async def initialize(self):
        """Initialize event manager and register all handlers"""
        if self._initialized:
            logger.info("Event manager already initialized")
            return

        try:
            logger.info("🚀 Initializing Event-Driven Architecture")

            # Register event handlers
            await self._register_handlers()

            # Start event bus processing
            await self.event_bus.start_processing()

            self._initialized = True
            logger.info("✅ Event-driven architecture initialized successfully")

            # Log registered handlers
            metrics = self.event_bus.get_metrics()
            logger.info(f"📊 Event Bus Metrics: {metrics}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize event manager: {e}")
            raise

    async def _register_handlers(self):
        """Register all event handlers"""

        # AI Content Moderation Handler
        ai_handler = AIContentModerationHandler()
        self.event_bus.subscribe(ai_handler)
        self.handlers["ai_moderation"] = ai_handler
        logger.info("✅ AI Moderation Handler registered")

        # Analytics Handler
        analytics_handler = AnalyticsHandler()
        self.event_bus.subscribe(analytics_handler)
        self.handlers["analytics"] = analytics_handler
        logger.info("✅ Analytics Handler registered")

        # Notification Handler
        notification_handler = NotificationHandler()
        self.event_bus.subscribe(notification_handler)
        self.handlers["notifications"] = notification_handler
        logger.info("✅ Notification Handler registered")

        logger.info(f"📋 Total handlers registered: {len(self.handlers)}")

    async def shutdown(self):
        """Gracefully shutdown event manager"""
        if not self._initialized:
            return

        try:
            logger.info("🔄 Shutting down Event Manager")

            # Flush any pending analytics
            if "analytics" in self.handlers:
                await self.handlers["analytics"].flush_batch()

            # Stop event bus processing
            await self.event_bus.stop_processing()

            # Process any remaining events
            remaining_events = self.event_bus.get_metrics()["queue_size"]
            if remaining_events > 0:
                logger.info(f"⏳ Processing {remaining_events} remaining events...")
                await asyncio.sleep(2)  # Give time for processing

            self._initialized = False
            logger.info("✅ Event Manager shut down successfully")

        except Exception as e:
            logger.error(f"❌ Error during event manager shutdown: {e}")

    async def publish_event(self, event_type: str, **kwargs):
        """Convenience method to publish events"""
        if not self._initialized:
            logger.warning("Event manager not initialized, cannot publish event")
            return

        try:
            from app.events.event_bus import Event, EventType
            from datetime import datetime
            import uuid

            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType(event_type),
                timestamp=datetime.utcnow(),
                source="event_manager",
                **kwargs
            )

            await self.event_bus.publish(event)

        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get event manager metrics"""
        if not self._initialized:
            return {"status": "not_initialized"}

        base_metrics = self.event_bus.get_metrics()

        return {
            "status": "initialized" if self._initialized else "not_initialized",
            "handlers_count": len(self.handlers),
            "event_bus": base_metrics,
            "handlers": {
                name: {
                    "name": handler.name,
                    "event_types": [et.value for et in handler.event_types]
                }
                for name, handler in self.handlers.items()
            }
        }

    async def get_handler_status(self) -> Dict[str, Any]:
        """Get detailed status of all handlers"""
        status = {}

        for name, handler in self.handlers.items():
            try:
                # Try to get handler-specific metrics if available
                handler_metrics = {}
                if hasattr(handler, "get_metrics"):
                    handler_metrics = await handler.get_metrics()

                status[name] = {
                    "name": handler.name,
                    "event_types": [et.value for et in handler.event_types],
                    "status": "active",
                    "metrics": handler_metrics
                }

            except Exception as e:
                status[name] = {
                    "name": handler.name,
                    "event_types": [et.value for et in handler.event_types],
                    "status": "error",
                    "error": str(e)
                }

        return status

    async def retry_failed_events(self) -> Dict[str, Any]:
        """Retry failed events"""
        if not self._initialized:
            return {"error": "Event manager not initialized"}

        try:
            retry_count = await self.event_bus.retry_failed_events()
            failed_events = await self.event_bus.get_failed_events()

            return {
                "retried_count": retry_count,
                "remaining_failed": len(failed_events),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Failed to retry events: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }

# Global event manager instance
event_manager = EventManager()

@asynccontextmanager
async def event_manager_lifespan():
    """Context manager for event manager lifecycle"""
    try:
        await event_manager.initialize()
        yield event_manager
    finally:
        await event_manager.shutdown()

# Integration helpers for FastAPI
async def publish_content_event(event_type: str, content_id: str, company_id: str,
                               user_id: str = None, payload: Dict[str, Any] = None,
                               correlation_id: str = None):
    """Helper to publish content-related events"""
    await event_manager.publish_event(
        event_type=event_type,
        content_id=content_id,
        company_id=company_id,
        user_id=user_id,
        payload=payload or {},
        correlation_id=correlation_id
    )

async def publish_device_event(event_type: str, device_id: str, company_id: str,
                             payload: Dict[str, Any] = None, correlation_id: str = None):
    """Helper to publish device-related events"""
    await event_manager.publish_event(
        event_type=event_type,
        device_id=device_id,
        company_id=company_id,
        payload=payload or {},
        correlation_id=correlation_id
    )

async def publish_analytics_event(event_type: str, company_id: str,
                                device_id: str = None, content_id: str = None,
                                user_id: str = None, metrics: Dict[str, Any] = None,
                                correlation_id: str = None):
    """Helper to publish analytics events"""
    await event_manager.publish_event(
        event_type=event_type,
        company_id=company_id,
        device_id=device_id,
        content_id=content_id,
        user_id=user_id,
        payload=metrics or {},
        correlation_id=correlation_id
    )