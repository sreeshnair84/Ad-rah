"""
Analytics Event Handler - Processes analytics data in background
Reduces load on primary application by handling analytics operations asynchronously
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from app.events.event_bus import EventHandler, Event, EventType
from app.database_service import db_service

logger = logging.getLogger(__name__)

class AnalyticsHandler(EventHandler):
    """Background handler for analytics data processing"""

    def __init__(self):
        super().__init__(
            name="analytics_handler",
            event_types=[
                EventType.CONTENT_VIEWED,
                EventType.DEVICE_INTERACTION,
                EventType.PERFORMANCE_METRIC,
                EventType.CONTENT_APPROVED,
                EventType.CONTENT_DEPLOYED,
                EventType.DEVICE_SYNC_COMPLETED,
                EventType.USER_LOGIN
            ]
        )
        self._batch_buffer = []
        self._batch_size = 50
        self._batch_timeout = 30  # seconds
        self._last_batch_time = datetime.utcnow()

    async def handle(self, event: Event) -> bool:
        """Process analytics event"""
        try:
            # Add to batch buffer for efficient processing
            self._batch_buffer.append(event)

            # Process batch if conditions are met
            if (len(self._batch_buffer) >= self._batch_size or
                datetime.utcnow() - self._last_batch_time > timedelta(seconds=self._batch_timeout)):
                await self._process_batch()

            # Handle specific event types
            if event.event_type == EventType.CONTENT_VIEWED:
                await self._track_content_view(event)
            elif event.event_type == EventType.DEVICE_INTERACTION:
                await self._track_device_interaction(event)
            elif event.event_type == EventType.PERFORMANCE_METRIC:
                await self._track_performance_metric(event)
            elif event.event_type in [EventType.CONTENT_APPROVED, EventType.CONTENT_DEPLOYED]:
                await self._track_content_lifecycle(event)
            elif event.event_type == EventType.DEVICE_SYNC_COMPLETED:
                await self._track_device_sync(event)
            elif event.event_type == EventType.USER_LOGIN:
                await self._track_user_activity(event)

            return True

        except Exception as e:
            logger.error(f"Analytics handler error for event {event.event_id}: {e}")
            return False

    async def _process_batch(self):
        """Process batched events efficiently"""
        if not self._batch_buffer:
            return

        try:
            # Group events by type for batch processing
            events_by_type = {}
            for event in self._batch_buffer:
                event_type = event.event_type.value
                if event_type not in events_by_type:
                    events_by_type[event_type] = []
                events_by_type[event_type].append(event)

            # Process each event type batch
            tasks = []
            for event_type, events in events_by_type.items():
                tasks.append(self._batch_process_by_type(event_type, events))

            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"Processed batch of {len(self._batch_buffer)} analytics events")

        except Exception as e:
            logger.error(f"Failed to process analytics batch: {e}")

        finally:
            self._batch_buffer.clear()
            self._last_batch_time = datetime.utcnow()

    async def _batch_process_by_type(self, event_type: str, events: List[Event]):
        """Process events of the same type in batch"""
        try:
            # Prepare batch data for database
            analytics_docs = []
            for event in events:
                doc = {
                    "event_id": event.event_id,
                    "event_type": event_type,
                    "timestamp": event.timestamp,
                    "company_id": event.company_id,
                    "user_id": event.user_id,
                    "device_id": event.device_id,
                    "content_id": event.content_id,
                    "payload": event.payload,
                    "correlation_id": event.correlation_id,
                    "processed_at": datetime.utcnow()
                }
                analytics_docs.append(doc)

            # Batch insert to analytics collection
            if analytics_docs:
                await db_service.insert_many("analytics_events", analytics_docs)

            # Update aggregated metrics
            await self._update_aggregated_metrics(event_type, events)

        except Exception as e:
            logger.error(f"Failed to batch process {event_type} events: {e}")

    async def _track_content_view(self, event: Event) -> bool:
        """Track content view event"""
        try:
            content_id = event.content_id
            device_id = event.device_id
            company_id = event.company_id

            if not all([content_id, device_id, company_id]):
                logger.warning(f"Incomplete content view event {event.event_id}")
                return False

            # Update content view metrics
            await db_service.update_document(
                "content",
                {"_id": content_id},
                {
                    "$inc": {
                        "analytics.total_views": 1,
                        "analytics.daily_views": 1
                    },
                    "$set": {
                        "analytics.last_viewed": event.timestamp,
                        "analytics.last_device": device_id
                    },
                    "$addToSet": {
                        "analytics.viewing_devices": device_id
                    }
                }
            )

            # Update device engagement metrics
            await db_service.update_document(
                "devices",
                {"_id": device_id},
                {
                    "$inc": {
                        "analytics.total_content_views": 1
                    },
                    "$set": {
                        "analytics.last_activity": event.timestamp
                    }
                }
            )

            # Update company analytics
            await self._update_company_metrics(company_id, {
                "total_content_views": 1,
                "active_devices": [device_id]
            })

            return True

        except Exception as e:
            logger.error(f"Failed to track content view: {e}")
            return False

    async def _track_device_interaction(self, event: Event) -> bool:
        """Track device interaction event"""
        try:
            device_id = event.device_id
            company_id = event.company_id
            interaction_data = event.payload

            if not all([device_id, company_id]):
                return False

            # Update device interaction metrics
            interaction_type = interaction_data.get("interaction_type", "unknown")
            duration = interaction_data.get("duration", 0)

            await db_service.update_document(
                "devices",
                {"_id": device_id},
                {
                    "$inc": {
                        "analytics.total_interactions": 1,
                        f"analytics.interactions_by_type.{interaction_type}": 1,
                        "analytics.total_interaction_time": duration
                    },
                    "$set": {
                        "analytics.last_interaction": event.timestamp
                    }
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track device interaction: {e}")
            return False

    async def _track_performance_metric(self, event: Event) -> bool:
        """Track performance metrics"""
        try:
            metrics = event.payload
            entity_type = metrics.get("entity_type")  # "device", "content", "company"
            entity_id = metrics.get("entity_id")

            if not all([entity_type, entity_id]):
                return False

            collection = f"{entity_type}s"
            await db_service.update_document(
                collection,
                {"_id": entity_id},
                {
                    "$push": {
                        "performance_metrics": {
                            "timestamp": event.timestamp,
                            "metrics": metrics,
                            "recorded_by": event.source
                        }
                    },
                    "$set": {
                        "last_metrics_update": event.timestamp
                    }
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track performance metric: {e}")
            return False

    async def _track_content_lifecycle(self, event: Event) -> bool:
        """Track content lifecycle events"""
        try:
            content_id = event.content_id
            company_id = event.company_id

            if not all([content_id, company_id]):
                return False

            lifecycle_data = {
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "user_id": event.user_id,
                "payload": event.payload
            }

            await db_service.update_document(
                "content",
                {"_id": content_id},
                {
                    "$push": {
                        "analytics.lifecycle_events": lifecycle_data
                    },
                    "$set": {
                        f"analytics.{event.event_type.value}_at": event.timestamp
                    }
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track content lifecycle: {e}")
            return False

    async def _track_device_sync(self, event: Event) -> bool:
        """Track device sync completion"""
        try:
            device_id = event.device_id
            company_id = event.company_id
            sync_data = event.payload

            if not all([device_id, company_id]):
                return False

            # Update device sync metrics
            content_count = len(sync_data.get("content_ids", []))
            sync_duration = sync_data.get("sync_duration", 0)

            await db_service.update_document(
                "devices",
                {"_id": device_id},
                {
                    "$inc": {
                        "analytics.total_syncs": 1,
                        "analytics.total_sync_time": sync_duration,
                        "analytics.total_content_synced": content_count
                    },
                    "$set": {
                        "analytics.last_sync": event.timestamp,
                        "analytics.last_sync_duration": sync_duration
                    }
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track device sync: {e}")
            return False

    async def _track_user_activity(self, event: Event) -> bool:
        """Track user activity"""
        try:
            user_id = event.user_id
            company_id = event.company_id

            if not all([user_id, company_id]):
                return False

            await db_service.update_document(
                "users",
                {"_id": user_id},
                {
                    "$inc": {
                        "analytics.login_count": 1
                    },
                    "$set": {
                        "analytics.last_login": event.timestamp
                    },
                    "$push": {
                        "analytics.login_history": {
                            "timestamp": event.timestamp,
                            "source": event.source,
                            "ip_address": event.payload.get("ip_address"),
                            "user_agent": event.payload.get("user_agent")
                        }
                    }
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track user activity: {e}")
            return False

    async def _update_company_metrics(self, company_id: str, metrics: Dict[str, Any]):
        """Update company-level aggregated metrics"""
        try:
            update_ops = {}

            # Increment counters
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    if key not in update_ops.get("$inc", {}):
                        update_ops.setdefault("$inc", {})[f"analytics.{key}"] = value

            # Add to sets (for unique values like active devices)
            for key, value in metrics.items():
                if isinstance(value, list):
                    for item in value:
                        update_ops.setdefault("$addToSet", {})[f"analytics.{key}"] = item

            if update_ops:
                await db_service.update_document(
                    "companies",
                    {"_id": company_id},
                    update_ops
                )

        except Exception as e:
            logger.error(f"Failed to update company metrics: {e}")

    async def _update_aggregated_metrics(self, event_type: str, events: List[Event]):
        """Update aggregated metrics for event type"""
        try:
            # Group events by company for aggregation
            company_events = {}
            for event in events:
                company_id = event.company_id
                if company_id:
                    if company_id not in company_events:
                        company_events[company_id] = []
                    company_events[company_id].append(event)

            # Update company-level aggregations
            for company_id, company_event_list in company_events.items():
                await self._update_company_aggregations(company_id, event_type, company_event_list)

        except Exception as e:
            logger.error(f"Failed to update aggregated metrics: {e}")

    async def _update_company_aggregations(self, company_id: str, event_type: str, events: List[Event]):
        """Update company-level event aggregations"""
        try:
            aggregation_data = {
                "event_type": event_type,
                "count": len(events),
                "timestamp": datetime.utcnow(),
                "period": "real_time"
            }

            await db_service.update_document(
                "analytics_aggregations",
                {
                    "company_id": company_id,
                    "event_type": event_type,
                    "date": datetime.utcnow().date().isoformat()
                },
                {
                    "$inc": {
                        "count": len(events)
                    },
                    "$set": {
                        "last_updated": datetime.utcnow()
                    }
                },
                upsert=True
            )

        except Exception as e:
            logger.error(f"Failed to update company aggregations: {e}")

    async def flush_batch(self):
        """Manually flush the current batch"""
        if self._batch_buffer:
            await self._process_batch()
            logger.info("Analytics batch manually flushed")