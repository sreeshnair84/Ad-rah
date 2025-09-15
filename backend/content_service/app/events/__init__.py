"""
Events module for Adara Digital Signage Platform
Provides event-driven architecture to reduce load on primary application
"""

from .event_bus import (
    Event,
    EventType,
    EventHandler,
    AsyncEventBus,
    event_bus,
    publish_content_uploaded,
    publish_content_approved,
    publish_device_sync_started,
    publish_analytics_event
)

from .event_manager import (
    EventManager,
    event_manager,
    event_manager_lifespan,
    publish_content_event,
    publish_device_event,
    publish_analytics_event as publish_analytics_event_helper
)

from .handlers.ai_moderation_handler import AIContentModerationHandler
from .handlers.analytics_handler import AnalyticsHandler
from .handlers.notification_handler import NotificationHandler

__all__ = [
    # Core event system
    "Event",
    "EventType",
    "EventHandler",
    "AsyncEventBus",
    "event_bus",

    # Event manager
    "EventManager",
    "event_manager",
    "event_manager_lifespan",

    # Event handlers
    "AIContentModerationHandler",
    "AnalyticsHandler",
    "NotificationHandler",

    # Helper functions
    "publish_content_uploaded",
    "publish_content_approved",
    "publish_device_sync_started",
    "publish_analytics_event",
    "publish_content_event",
    "publish_device_event",
    "publish_analytics_event_helper"
]