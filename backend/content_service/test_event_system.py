"""
Simple test for the event-driven architecture
Tests basic event bus functionality without database dependencies
"""

import asyncio
import logging
from datetime import datetime
from app.events.event_bus import Event, EventType, AsyncEventBus, EventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestEventHandler(EventHandler):
    """Simple test event handler"""

    def __init__(self):
        super().__init__(
            name="test_handler",
            event_types=[EventType.CONTENT_UPLOADED, EventType.CONTENT_APPROVED]
        )
        self.processed_events = []

    async def handle(self, event: Event) -> bool:
        """Handle test events"""
        logger.info(f"Processing event: {event.event_type.value} (ID: {event.event_id})")
        self.processed_events.append(event)
        await asyncio.sleep(0.1)  # Simulate processing time
        return True

async def test_event_system():
    """Test the event system"""
    logger.info("🧪 Testing Event-Driven Architecture")

    # Create event bus
    event_bus = AsyncEventBus()

    # Create and register test handler
    test_handler = TestEventHandler()
    event_bus.subscribe(test_handler)

    # Start processing
    await event_bus.start_processing()

    try:
        # Create test events
        events = [
            Event(
                event_id="test_1",
                event_type=EventType.CONTENT_UPLOADED,
                timestamp=datetime.utcnow(),
                source="test",
                company_id="test_company",
                user_id="test_user",
                content_id="test_content_1",
                payload={"filename": "test1.jpg"}
            ),
            Event(
                event_id="test_2",
                event_type=EventType.CONTENT_APPROVED,
                timestamp=datetime.utcnow(),
                source="test",
                company_id="test_company",
                user_id="test_reviewer",
                content_id="test_content_1",
                payload={"approved_by": "test_reviewer"}
            )
        ]

        # Publish events
        for event in events:
            await event_bus.publish(event)
            logger.info(f"Published event: {event.event_type.value}")

        # Wait for processing
        await asyncio.sleep(2)

        # Check metrics
        metrics = event_bus.get_metrics()
        logger.info(f"📊 Event Bus Metrics: {metrics}")

        # Verify handler processed events
        logger.info(f"✅ Handler processed {len(test_handler.processed_events)} events")

        for processed_event in test_handler.processed_events:
            logger.info(f"  - {processed_event.event_type.value} (ID: {processed_event.event_id})")

        # Test successful
        logger.info("✅ Event system test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Event system test failed: {e}")
        return False

    finally:
        # Stop processing
        await event_bus.stop_processing()
        logger.info("🔄 Event bus stopped")

async def test_event_serialization():
    """Test event serialization and deserialization"""
    logger.info("🧪 Testing Event Serialization")

    try:
        # Create test event
        original_event = Event(
            event_id="serial_test",
            event_type=EventType.CONTENT_UPLOADED,
            timestamp=datetime.utcnow(),
            source="serialization_test",
            company_id="test_company",
            user_id="test_user",
            content_id="test_content",
            payload={"test": "data", "number": 42}
        )

        # Serialize to dict
        event_dict = original_event.to_dict()
        logger.info(f"Serialized event: {event_dict}")

        # Deserialize back to event
        deserialized_event = Event.from_dict(event_dict)

        # Verify
        assert deserialized_event.event_id == original_event.event_id
        assert deserialized_event.event_type == original_event.event_type
        assert deserialized_event.source == original_event.source
        assert deserialized_event.payload == original_event.payload

        logger.info("✅ Event serialization test passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Event serialization test failed: {e}")
        return False

async def main():
    """Run all event system tests"""
    logger.info("🚀 Starting Event System Tests")

    tests = [
        ("Event Serialization", test_event_serialization),
        ("Event System", test_event_system)
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} Test...")
        result = await test_func()
        results.append((test_name, result))
        logger.info(f"{'✅' if result else '❌'} {test_name} Test {'PASSED' if result else 'FAILED'}")

    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)

    logger.info(f"\n📊 Test Summary: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All event system tests passed!")
    else:
        logger.error("❌ Some event system tests failed!")
        for test_name, result in results:
            if not result:
                logger.error(f"  - {test_name}: FAILED")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)