"""
Event Integration Test - Tests event-driven architecture without database dependencies
Focuses on testing event publishing, handling, and coordination between components
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Import event system components directly
from app.events.event_bus import Event, EventType, AsyncEventBus, EventHandler
from app.events.handlers.ai_moderation_handler import AIContentModerationHandler
from app.events.handlers.analytics_handler import AnalyticsHandler
from app.events.handlers.notification_handler import NotificationHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockEventHandler(EventHandler):
    """Mock event handler for testing"""

    def __init__(self, name: str, event_types: List[EventType]):
        super().__init__(name, event_types)
        self.processed_events = []
        self.processing_time = 0.1

    async def handle(self, event: Event) -> bool:
        """Mock event handling"""
        logger.info(f"[{self.name}] Processing {event.event_type.value} (ID: {event.event_id})")

        # Simulate processing time
        await asyncio.sleep(self.processing_time)

        # Store processed event
        self.processed_events.append({
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": datetime.utcnow(),
            "payload": event.payload
        })

        logger.info(f"[{self.name}] ✅ Completed {event.event_type.value}")
        return True

async def test_event_bus_basic_functionality():
    """Test basic event bus functionality"""
    logger.info("🧪 Testing Basic Event Bus Functionality")

    # Create event bus
    bus = AsyncEventBus()

    # Create mock handlers
    content_handler = MockEventHandler("content_handler", [
        EventType.CONTENT_UPLOADED,
        EventType.CONTENT_APPROVED,
        EventType.CONTENT_REJECTED
    ])

    analytics_handler = MockEventHandler("analytics_handler", [
        EventType.CONTENT_VIEWED,
        EventType.DEVICE_INTERACTION
    ])

    # Register handlers
    bus.subscribe(content_handler)
    bus.subscribe(analytics_handler)

    # Start processing
    await bus.start_processing()

    try:
        # Create test events
        events = [
            Event(
                event_id="test_upload",
                event_type=EventType.CONTENT_UPLOADED,
                timestamp=datetime.utcnow(),
                source="test",
                company_id="test_company",
                content_id="test_content",
                payload={"filename": "test.jpg"}
            ),
            Event(
                event_id="test_view",
                event_type=EventType.CONTENT_VIEWED,
                timestamp=datetime.utcnow(),
                source="test",
                company_id="test_company",
                device_id="test_device",
                content_id="test_content",
                payload={"duration": 30}
            ),
            Event(
                event_id="test_approval",
                event_type=EventType.CONTENT_APPROVED,
                timestamp=datetime.utcnow(),
                source="test",
                company_id="test_company",
                content_id="test_content",
                payload={"approved_by": "test_user"}
            )
        ]

        # Publish events
        for event in events:
            await bus.publish(event)
            logger.info(f"📤 Published: {event.event_type.value}")

        # Wait for processing
        await asyncio.sleep(2)

        # Verify results
        content_processed = len(content_handler.processed_events)
        analytics_processed = len(analytics_handler.processed_events)

        logger.info(f"📊 Content handler processed: {content_processed} events")
        logger.info(f"📊 Analytics handler processed: {analytics_processed} events")

        # Check metrics
        metrics = bus.get_metrics()
        logger.info(f"📈 Bus Metrics: {metrics}")

        success = (content_processed == 2 and analytics_processed == 1 and
                  metrics['events_published'] == 3 and metrics['events_processed'] >= 3)

        return success

    finally:
        await bus.stop_processing()

async def test_event_handler_coordination():
    """Test coordination between multiple event handlers"""
    logger.info("🧪 Testing Event Handler Coordination")

    bus = AsyncEventBus()

    # Create handlers that respond to the same events
    handler1 = MockEventHandler("handler_1", [EventType.CONTENT_UPLOADED])
    handler2 = MockEventHandler("handler_2", [EventType.CONTENT_UPLOADED])
    handler3 = MockEventHandler("handler_3", [EventType.CONTENT_UPLOADED])

    # Different processing times
    handler1.processing_time = 0.1
    handler2.processing_time = 0.2
    handler3.processing_time = 0.05

    bus.subscribe(handler1)
    bus.subscribe(handler2)
    bus.subscribe(handler3)

    await bus.start_processing()

    try:
        # Create event that all handlers should process
        event = Event(
            event_id="coordination_test",
            event_type=EventType.CONTENT_UPLOADED,
            timestamp=datetime.utcnow(),
            source="coordination_test",
            company_id="test_company",
            content_id="test_content",
            payload={"test": "coordination"}
        )

        start_time = datetime.utcnow()
        await bus.publish(event)

        # Wait for all handlers to complete
        await asyncio.sleep(1)
        end_time = datetime.utcnow()

        # Check all handlers processed the event
        h1_processed = len(handler1.processed_events)
        h2_processed = len(handler2.processed_events)
        h3_processed = len(handler3.processed_events)

        total_time = (end_time - start_time).total_seconds()

        logger.info(f"📊 Handler 1 processed: {h1_processed}")
        logger.info(f"📊 Handler 2 processed: {h2_processed}")
        logger.info(f"📊 Handler 3 processed: {h3_processed}")
        logger.info(f"⏱️ Total processing time: {total_time:.2f}s")

        success = (h1_processed == 1 and h2_processed == 1 and h3_processed == 1)
        return success

    finally:
        await bus.stop_processing()

async def test_event_serialization_and_correlation():
    """Test event serialization and correlation tracking"""
    logger.info("🧪 Testing Event Serialization and Correlation")

    try:
        # Create complex event with all fields
        original_event = Event(
            event_id="serialization_test",
            event_type=EventType.CONTENT_UPLOADED,
            timestamp=datetime.utcnow(),
            source="serialization_test",
            company_id="test_company_123",
            user_id="test_user_456",
            device_id="test_device_789",
            content_id="test_content_abc",
            payload={
                "complex_data": {
                    "nested": {"value": 42},
                    "array": [1, 2, 3],
                    "string": "test"
                },
                "metadata": {
                    "version": "1.0",
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            correlation_id="correlation_123"
        )

        # Test serialization
        serialized = original_event.to_dict()
        deserialized = Event.from_dict(serialized)

        # Verify all fields match
        fields_to_check = [
            "event_id", "event_type", "source", "company_id",
            "user_id", "device_id", "content_id", "correlation_id"
        ]

        all_match = True
        for field in fields_to_check:
            original_val = getattr(original_event, field)
            deserialized_val = getattr(deserialized, field)

            if original_val != deserialized_val:
                logger.error(f"❌ Field {field} mismatch: {original_val} != {deserialized_val}")
                all_match = False

        # Check payload
        if original_event.payload != deserialized.payload:
            logger.error("❌ Payload mismatch")
            all_match = False

        # Check timestamp (with small tolerance)
        time_diff = abs((original_event.timestamp - deserialized.timestamp).total_seconds())
        if time_diff > 1:  # Allow 1 second difference
            logger.error(f"❌ Timestamp difference too large: {time_diff}s")
            all_match = False

        if all_match:
            logger.info("✅ All serialization checks passed")

        return all_match

    except Exception as e:
        logger.error(f"❌ Serialization test failed: {e}")
        return False

async def test_high_throughput_events():
    """Test event system under high throughput"""
    logger.info("🧪 Testing High Throughput Event Processing")

    bus = AsyncEventBus()

    # Fast processing handler
    fast_handler = MockEventHandler("fast_handler", [
        EventType.CONTENT_VIEWED,
        EventType.DEVICE_INTERACTION,
        EventType.PERFORMANCE_METRIC
    ])
    fast_handler.processing_time = 0.01  # Very fast processing

    bus.subscribe(fast_handler)
    await bus.start_processing()

    try:
        event_count = 50
        start_time = datetime.utcnow()

        # Create and publish many events rapidly
        tasks = []
        for i in range(event_count):
            event = Event(
                event_id=f"throughput_test_{i}",
                event_type=EventType.PERFORMANCE_METRIC,
                timestamp=datetime.utcnow(),
                source="throughput_test",
                company_id="test_company",
                payload={
                    "sequence": i,
                    "batch": "throughput_test",
                    "data": f"test_data_{i}"
                }
            )
            tasks.append(bus.publish(event))

        # Publish all events concurrently
        await asyncio.gather(*tasks)
        publish_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info(f"📤 Published {event_count} events in {publish_time:.2f}s")
        logger.info(f"📈 Publish rate: {event_count/publish_time:.2f} events/sec")

        # Wait for processing to complete
        await asyncio.sleep(3)
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Check results
        processed_count = len(fast_handler.processed_events)
        metrics = bus.get_metrics()

        logger.info(f"📊 Processed {processed_count}/{event_count} events")
        logger.info(f"⏱️ Total time: {processing_time:.2f}s")
        logger.info(f"📈 Processing rate: {processed_count/processing_time:.2f} events/sec")
        logger.info(f"📈 Final metrics: {metrics}")

        success = (processed_count >= event_count * 0.9)  # Allow 90% success rate
        return success

    finally:
        await bus.stop_processing()

async def run_all_integration_tests():
    """Run all event integration tests"""
    logger.info("🚀 Starting Event Integration Tests")

    tests = [
        ("Basic Event Bus Functionality", test_event_bus_basic_functionality),
        ("Event Handler Coordination", test_event_handler_coordination),
        ("Event Serialization and Correlation", test_event_serialization_and_correlation),
        ("High Throughput Event Processing", test_high_throughput_events)
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name}...")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status} {test_name}")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))

        # Small delay between tests
        await asyncio.sleep(0.5)

    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)

    logger.info(f"\n📊 Integration Test Summary: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All event integration tests passed!")
        logger.info("✅ Event-driven architecture is working correctly!")
    else:
        logger.error("❌ Some event integration tests failed!")
        for test_name, result in results:
            if not result:
                logger.error(f"  - {test_name}: FAILED")

    return passed == total

async def main():
    """Main test runner"""
    return await run_all_integration_tests()

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'✅ ALL INTEGRATION TESTS PASSED' if success else '❌ SOME INTEGRATION TESTS FAILED'}")
    print("🏁 Event-driven architecture integration testing complete!")
    exit(0 if success else 1)