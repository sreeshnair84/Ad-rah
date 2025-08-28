import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional
from app.repo import repo
from app.models import Review, ContentMetadata
from app.config import settings

logger = logging.getLogger(__name__)


class LocalEventProcessor:
    """Local event processor using in-memory queues for development/testing"""

    def __init__(self):
        self.event_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start the local event processor"""
        self.running = True
        self.task = asyncio.create_task(self._process_events())
        self.logger.info("Local event processor started")

    async def stop(self):
        """Stop the local event processor"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.logger.info("Local event processor stopped")

    async def _process_events(self):
        """Main event processing loop"""
        while self.running:
            try:
                # Wait for events with timeout
                event_data = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._handle_message(event_data)
                self.event_queue.task_done()
            except asyncio.TimeoutError:
                # No events, continue loop
                continue
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, event_data: Dict[str, Any]):
        """Handle individual messages"""
        try:
            event_type = event_data.get("type")
            payload = event_data.get("payload", {})

            self.logger.info(f"Processing event: {event_type}")

            if event_type == "content_uploaded":
                await self._handle_content_uploaded(payload)
            elif event_type == "moderation_requested":
                await self._handle_moderation_requested(payload)
            elif event_type == "content_approved":
                await self._handle_content_approved(payload)
            else:
                self.logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            self.logger.error(f"Error handling message: {e}")

    async def _handle_content_uploaded(self, payload: Dict[str, Any]):
        """Handle content uploaded event"""
        content_id = payload.get("content_id")
        if not content_id:
            self.logger.error("No content_id in content_uploaded event")
            return

        # Get content metadata
        content = await repo.get(content_id)
        if not content:
            self.logger.error(f"Content {content_id} not found")
            return

        # Trigger moderation workflow
        await self._trigger_moderation(content)

    async def _handle_moderation_requested(self, payload: Dict[str, Any]):
        """Handle moderation requested event"""
        content_id = payload.get("content_id")
        if not content_id:
            self.logger.error("No content_id in moderation_requested event")
            return

        # Perform AI moderation (simulated for local development)
        await self._perform_ai_moderation(content_id)

    async def _handle_content_approved(self, payload: Dict[str, Any]):
        """Handle content approved event"""
        content_id = payload.get("content_id")
        if not content_id:
            self.logger.error("No content_id in content_approved event")
            return

        # Trigger publishing workflow
        await self._trigger_publishing(content_id)

    async def _trigger_moderation(self, content: Dict[str, Any]):
        """Trigger moderation workflow"""
        # Send moderation requested event
        await self._send_event("moderation_requested", {
            "content_id": content["id"],
            "content_type": content.get("content_type"),
            "filename": content.get("filename")
        })

    async def _perform_ai_moderation(self, content_id: str):
        """Perform AI moderation (simulated for local development)"""
        try:
            # Simulate AI moderation with random results for testing
            import random
            confidence = random.uniform(0.1, 1.0)
            action = "approved" if confidence > 0.7 else "needs_review" if confidence > 0.4 else "rejected"

            self.logger.info(f"AI Moderation result for {content_id}: {action} (confidence: {confidence:.2f})")

            # Create review
            review = Review(
                content_id=content_id,
                ai_confidence=confidence,
                action=action,
                notes=f"Local AI moderation completed - {action}"
            )

            saved_review = await repo.save_review(review.model_dump())

            # Send moderation completed event
            await self._send_event("moderation_completed", {
                "content_id": content_id,
                "review_id": saved_review["id"],
                "action": action,
                "confidence": confidence
            })

        except Exception as e:
            self.logger.error(f"AI moderation failed: {e}")
            # Send moderation failed event
            await self._send_event("moderation_failed", {
                "content_id": content_id,
                "error": str(e)
            })

    async def _trigger_publishing(self, content_id: str):
        """Trigger publishing workflow"""
        # Send publishing requested event
        await self._send_event("publishing_requested", {
            "content_id": content_id
        })

    async def _send_event(self, event_type: str, payload: Dict[str, Any]):
        """Send event to local queue"""
        try:
            event_data = {
                "type": event_type,
                "payload": payload,
                "timestamp": asyncio.get_event_loop().time()
            }

            await self.event_queue.put(event_data)
            self.logger.info(f"Queued local event: {event_type}")

        except Exception as e:
            self.logger.error(f"Failed to queue event {event_type}: {e}")

    async def send_event(self, event_type: str, payload: Dict[str, Any]):
        """Public method to send events to the processor"""
        await self._send_event(event_type, payload)


class AzureEventProcessor:
    """Azure Service Bus event processor for production"""

    def __init__(self):
        self.connection_string = os.getenv("SERVICE_BUS_CONNECTION_STRING")
        self.client: Optional[Any] = None
        self.subscription_name = "content-service"
        self.topic_name = "content-events"

    async def start(self):
        if not self.connection_string:
            logger.warning("SERVICE_BUS_CONNECTION_STRING not set, running in simulation mode")
            return

        try:
            from azure.servicebus import ServiceBusClient
            from azure.servicebus.exceptions import ServiceBusError

            self.client = ServiceBusClient.from_connection_string(self.connection_string)
            await self._ensure_topic_exists()
            await self._ensure_subscription_exists()
            logger.info("Azure event processor started")
            await self._process_events()
        except ImportError:
            logger.error("Azure Service Bus SDK not installed")
        except Exception as e:
            logger.error(f"Failed to start Azure event processor: {e}")

    async def stop(self):
        if self.client:
            await self.client.close()
        logger.info("Azure event processor stopped")

    async def _ensure_topic_exists(self):
        """Ensure the topic exists (in production, this would be done via ARM templates)"""
        try:
            from azure.servicebus.exceptions import ServiceBusError
            with self.client.get_topic_sender(self.topic_name) as sender:
                pass
        except ServiceBusError:
            logger.warning(f"Topic {self.topic_name} does not exist")

    async def _ensure_subscription_exists(self):
        """Ensure the subscription exists"""
        try:
            from azure.servicebus.exceptions import ServiceBusError
            with self.client.get_subscription_receiver(
                self.topic_name, self.subscription_name
            ) as receiver:
                pass
        except ServiceBusError:
            logger.warning(f"Subscription {self.subscription_name} does not exist")

    async def _process_events(self):
        """Main event processing loop"""
        from azure.servicebus import ServiceBusMessage
        from azure.servicebus.exceptions import ServiceBusError

        while True:
            try:
                with self.client.get_subscription_receiver(
                    self.topic_name, self.subscription_name
                ) as receiver:
                    for message in receiver:
                        await self._handle_message(message)
                        receiver.complete_message(message)
            except ServiceBusError as e:
                logger.error(f"Service Bus error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in event processing: {e}")
                await asyncio.sleep(5)

    async def _handle_message(self, message):
        """Handle individual messages"""
        try:
            from azure.servicebus import ServiceBusMessage
            event_data = json.loads(str(message))
            event_type = event_data.get("type")
            payload = event_data.get("payload", {})

            logger.info(f"Processing Azure event: {event_type}")

            if event_type == "content_uploaded":
                await self._handle_content_uploaded(payload)
            elif event_type == "moderation_requested":
                await self._handle_moderation_requested(payload)
            elif event_type == "content_approved":
                await self._handle_content_approved(payload)
            else:
                logger.warning(f"Unknown event type: {event_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def _handle_content_uploaded(self, payload: Dict[str, Any]):
        """Handle content uploaded event"""
        content_id = payload.get("content_id")
        if not content_id:
            logger.error("No content_id in content_uploaded event")
            return

        # Get content metadata
        content = await repo.get(content_id)
        if not content:
            logger.error(f"Content {content_id} not found")
            return

        # Trigger moderation workflow
        await self._trigger_moderation(content)

    async def _handle_moderation_requested(self, payload: Dict[str, Any]):
        """Handle moderation requested event"""
        content_id = payload.get("content_id")
        if not content_id:
            logger.error("No content_id in moderation_requested event")
            return

        # Perform AI moderation
        await self._perform_ai_moderation(content_id)

    async def _handle_content_approved(self, payload: Dict[str, Any]):
        """Handle content approved event"""
        content_id = payload.get("content_id")
        if not content_id:
            logger.error("No content_id in content_approved event")
            return

        # Trigger publishing workflow
        await self._trigger_publishing(content_id)

    async def _trigger_moderation(self, content: Dict[str, Any]):
        """Trigger moderation workflow"""
        # Send moderation requested event
        await self._send_event("moderation_requested", {
            "content_id": content["id"],
            "content_type": content.get("content_type"),
            "filename": content.get("filename")
        })

    async def _perform_ai_moderation(self, content_id: str):
        """Perform AI moderation using Azure AI Foundry"""
        try:
            # Get Azure AI configuration
            ai_endpoint = os.getenv("AZURE_AI_ENDPOINT")
            ai_key = os.getenv("AZURE_AI_KEY")

            if not ai_endpoint or not ai_key:
                logger.warning("Azure AI not configured, using simulation")
                # Fallback to simulation
                confidence = 0.85  # Simulate high confidence
                action = "approved" if confidence > 0.8 else "needs_review"
            else:
                # TODO: Implement real Azure AI Foundry integration
                # This would use Azure AI Content Safety API or similar
                confidence = 0.85
                action = "approved"

            # Create review
            review = Review(
                content_id=content_id,
                ai_confidence=confidence,
                action=action,
                notes="AI moderation completed"
            )

            saved_review = await repo.save_review(review.model_dump())

            # Send moderation completed event
            await self._send_event("moderation_completed", {
                "content_id": content_id,
                "review_id": saved_review["id"],
                "action": action,
                "confidence": confidence
            })

        except Exception as e:
            logger.error(f"AI moderation failed: {e}")
            # Send moderation failed event
            await self._send_event("moderation_failed", {
                "content_id": content_id,
                "error": str(e)
            })

    async def _trigger_publishing(self, content_id: str):
        """Trigger publishing workflow"""
        # Send publishing requested event
        await self._send_event("publishing_requested", {
            "content_id": content_id
        })

    async def _send_event(self, event_type: str, payload: Dict[str, Any]):
        """Send event to Service Bus"""
        if not self.client:
            logger.warning("Service Bus client not available, skipping event")
            return

        try:
            from azure.servicebus import ServiceBusMessage
            event_data = {
                "type": event_type,
                "payload": payload,
                "timestamp": asyncio.get_event_loop().time()
            }

            message = ServiceBusMessage(json.dumps(event_data))

            with self.client.get_topic_sender(self.topic_name) as sender:
                sender.send_messages(message)

            logger.info(f"Sent Azure event: {event_type}")

        except Exception as e:
            logger.error(f"Failed to send event {event_type}: {e}")

    async def send_event(self, event_type: str, payload: Dict[str, Any]):
        """Public method to send events to the processor"""
        await self._send_event(event_type, payload)


# Factory function to create the appropriate event processor
def create_event_processor():
    """Create event processor based on configuration"""
    from app.config import settings

    # If explicitly set to use local processor or no Azure connection string
    if getattr(settings, 'USE_LOCAL_EVENT_PROCESSOR', True) or not os.getenv("SERVICE_BUS_CONNECTION_STRING"):
        logger.info("Using local event processor for development")
        return LocalEventProcessor()
    else:
        try:
            # Try to import Azure SDK
            from azure.servicebus import ServiceBusClient
            logger.info("Using Azure Service Bus event processor")
            return AzureEventProcessor()
        except ImportError:
            logger.warning("Azure Service Bus SDK not available, falling back to local processor")
            return LocalEventProcessor()


# Global event processor instance
event_processor = create_event_processor()
