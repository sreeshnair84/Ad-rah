"""
Event-driven architecture for reducing load on primary application
Implements async event publishing and subscription with background processing
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Callable, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    # Content lifecycle events
    CONTENT_UPLOADED = "content.uploaded"
    CONTENT_AI_MODERATION_STARTED = "content.ai_moderation.started"
    CONTENT_AI_MODERATION_COMPLETED = "content.ai_moderation.completed"
    CONTENT_APPROVED = "content.approved"
    CONTENT_REJECTED = "content.rejected"
    CONTENT_SCHEDULED = "content.scheduled"
    CONTENT_DEPLOYED = "content.deployed"

    # User and company events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    COMPANY_CREATED = "company.created"

    # Device events
    DEVICE_REGISTERED = "device.registered"
    DEVICE_SYNC_STARTED = "device.sync.started"
    DEVICE_SYNC_COMPLETED = "device.sync.completed"
    DEVICE_STATUS_CHANGED = "device.status.changed"

    # Analytics events
    CONTENT_VIEWED = "analytics.content.viewed"
    DEVICE_INTERACTION = "analytics.device.interaction"
    PERFORMANCE_METRIC = "analytics.performance.metric"

    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"

@dataclass
class Event:
    """Base event class for all system events"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    source: str
    company_id: Optional[str] = None
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    content_id: Optional[str] = None
    payload: Dict[str, Any] = None
    correlation_id: Optional[str] = None

    def __post_init__(self):
        if self.payload is None:
            self.payload = {}
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['event_type'] = EventType(data['event_type'])
        return cls(**data)

class EventHandler:
    """Base class for event handlers"""

    def __init__(self, name: str, event_types: List[EventType]):
        self.name = name
        self.event_types = event_types

    async def handle(self, event: Event) -> bool:
        """Handle an event. Return True if handled successfully."""
        raise NotImplementedError

    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler can process the given event type"""
        return event_type in self.event_types

class AsyncEventBus:
    """Async event bus for decoupled event processing"""

    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_queue = asyncio.Queue()
        self._processing_task = None
        self._running = False
        self._failed_events: List[Event] = []
        self._metrics = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'handlers_registered': 0
        }

    def subscribe(self, handler: EventHandler):
        """Subscribe an event handler to specific event types"""
        for event_type in handler.event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)

        self._metrics['handlers_registered'] += 1
        logger.info(f"Registered handler '{handler.name}' for events: {[et.value for et in handler.event_types]}")

    async def publish(self, event: Event):
        """Publish an event to the bus (non-blocking)"""
        try:
            await self._event_queue.put(event)
            self._metrics['events_published'] += 1

            logger.debug(f"Published event: {event.event_type.value} (ID: {event.event_id})")

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            self._metrics['events_failed'] += 1

    async def publish_and_wait(self, event: Event, timeout: float = 30.0) -> List[bool]:
        """Publish an event and wait for all handlers to complete"""
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            logger.warning(f"No handlers registered for event type: {event.event_type.value}")
            return []

        tasks = []
        for handler in handlers:
            if handler.can_handle(event.event_type):
                tasks.append(asyncio.create_task(self._handle_event_safely(handler, event)))

        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
            self._metrics['events_processed'] += 1
            return [r for r in results if isinstance(r, bool)]

        except asyncio.TimeoutError:
            logger.error(f"Timeout processing event {event.event_id} after {timeout}s")
            self._metrics['events_failed'] += 1
            return []

    async def start_processing(self):
        """Start background event processing"""
        if self._running:
            return

        self._running = True
        self._processing_task = asyncio.create_task(self._process_events())
        logger.info("Event bus processing started")

    async def stop_processing(self):
        """Stop background event processing"""
        if not self._running:
            return

        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        logger.info("Event bus processing stopped")

    async def _process_events(self):
        """Background event processing loop"""
        while self._running:
            try:
                # Get event with timeout to allow graceful shutdown
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # Process event with all registered handlers
                handlers = self._handlers.get(event.event_type, [])
                if handlers:
                    await self._process_event(event, handlers)
                else:
                    logger.warning(f"No handlers for event: {event.event_type.value}")

                self._event_queue.task_done()

            except asyncio.TimeoutError:
                # Normal timeout for graceful shutdown
                continue
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(1)

    async def _process_event(self, event: Event, handlers: List[EventHandler]):
        """Process an event with multiple handlers concurrently"""
        tasks = []
        for handler in handlers:
            if handler.can_handle(event.event_type):
                tasks.append(asyncio.create_task(self._handle_event_safely(handler, event)))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = sum(1 for r in results if r is True)
            failed = len(results) - successful

            if successful > 0:
                self._metrics['events_processed'] += 1
            if failed > 0:
                self._metrics['events_failed'] += failed
                self._failed_events.append(event)

            logger.debug(f"Event {event.event_id} processed: {successful} success, {failed} failed")

    async def _handle_event_safely(self, handler: EventHandler, event: Event) -> bool:
        """Safely handle an event with error catching"""
        try:
            result = await handler.handle(event)
            if result:
                logger.debug(f"Handler '{handler.name}' processed event {event.event_id}")
            return result

        except Exception as e:
            logger.error(f"Handler '{handler.name}' failed to process event {event.event_id}: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics"""
        return {
            **self._metrics,
            'queue_size': self._event_queue.qsize(),
            'failed_events_count': len(self._failed_events),
            'handlers_by_type': {
                event_type.value: len(handlers)
                for event_type, handlers in self._handlers.items()
            }
        }

    async def get_failed_events(self) -> List[Dict[str, Any]]:
        """Get list of failed events for debugging"""
        return [event.to_dict() for event in self._failed_events]

    async def retry_failed_events(self) -> int:
        """Retry processing failed events"""
        retry_count = 0
        failed_events = self._failed_events.copy()
        self._failed_events.clear()

        for event in failed_events:
            try:
                await self.publish(event)
                retry_count += 1
            except Exception as e:
                logger.error(f"Failed to retry event {event.event_id}: {e}")
                self._failed_events.append(event)

        logger.info(f"Retried {retry_count} failed events")
        return retry_count

# Global event bus instance
event_bus = AsyncEventBus()

# Helper functions for common event publishing
async def publish_content_uploaded(content_id: str, company_id: str, user_id: str,
                                 metadata: Dict[str, Any], correlation_id: str = None):
    """Publish content uploaded event"""
    event = Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.CONTENT_UPLOADED,
        timestamp=datetime.utcnow(),
        source="content_service",
        company_id=company_id,
        user_id=user_id,
        content_id=content_id,
        payload={
            "filename": metadata.get("filename"),
            "file_size": metadata.get("file_size"),
            "content_type": metadata.get("content_type"),
            "tags": metadata.get("tags", []),
            "description": metadata.get("description")
        },
        correlation_id=correlation_id
    )
    await event_bus.publish(event)

async def publish_content_approved(content_id: str, company_id: str, reviewer_id: str,
                                 approval_notes: str = None, correlation_id: str = None):
    """Publish content approved event"""
    event = Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.CONTENT_APPROVED,
        timestamp=datetime.utcnow(),
        source="content_service",
        company_id=company_id,
        user_id=reviewer_id,
        content_id=content_id,
        payload={
            "approval_notes": approval_notes,
            "approved_at": datetime.utcnow().isoformat()
        },
        correlation_id=correlation_id
    )
    await event_bus.publish(event)

async def publish_device_sync_started(device_id: str, company_id: str, content_ids: List[str],
                                    correlation_id: str = None):
    """Publish device sync started event"""
    event = Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.DEVICE_SYNC_STARTED,
        timestamp=datetime.utcnow(),
        source="device_service",
        company_id=company_id,
        device_id=device_id,
        payload={
            "content_ids": content_ids,
            "sync_type": "scheduled"
        },
        correlation_id=correlation_id
    )
    await event_bus.publish(event)

async def publish_analytics_event(event_type: EventType, company_id: str,
                                device_id: str = None, content_id: str = None,
                                metrics: Dict[str, Any] = None, correlation_id: str = None):
    """Publish analytics event"""
    event = Event(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.utcnow(),
        source="analytics_service",
        company_id=company_id,
        device_id=device_id,
        content_id=content_id,
        payload=metrics or {},
        correlation_id=correlation_id
    )
    await event_bus.publish(event)