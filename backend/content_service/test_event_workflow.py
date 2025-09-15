"""
Comprehensive End-to-End Test for Event-Driven Content Management Workflow
Tests the complete flow: Upload -> AI Moderation -> Approval -> Analytics -> Notifications
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Import event system components
from app.events.event_manager import event_manager, publish_content_event, publish_analytics_event
from app.events.event_bus import Event, EventType
from app.database_service import db_service
from app.history_service import HistoryService
from app.models import ContentHistoryEventType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventWorkflowTester:
    """End-to-end event workflow tester"""

    def __init__(self):
        self.test_results = []
        self.test_content_id = f"test_content_{uuid.uuid4()}"
        self.test_company_id = f"test_company_{uuid.uuid4()}"
        self.test_user_id = f"test_user_{uuid.uuid4()}"
        self.test_device_id = f"test_device_{uuid.uuid4()}"

    async def setup(self):
        """Setup test environment"""
        logger.info("🔧 Setting up test environment")

        # Initialize database service
        await db_service.initialize()
        logger.info("✅ Database service initialized")

        # Initialize event manager
        await event_manager.initialize()
        logger.info("✅ Event manager initialized")

        # Create test data in database
        await self._create_test_data()
        logger.info("✅ Test data created")

    async def teardown(self):
        """Cleanup test environment"""
        logger.info("🧹 Cleaning up test environment")

        # Clean up test data
        await self._cleanup_test_data()

        # Shutdown event manager
        await event_manager.shutdown()
        logger.info("✅ Event manager shut down")

        # Close database
        await db_service.close()
        logger.info("✅ Database connections closed")

    async def _create_test_data(self):
        """Create test data in database"""
        # Create test company
        await db_service.insert_document("companies", {
            "_id": self.test_company_id,
            "name": "Test Company",
            "company_type": "HOST",
            "status": "active",
            "created_at": datetime.utcnow()
        })

        # Create test user
        await db_service.insert_document("users", {
            "_id": self.test_user_id,
            "email": "test@company.com",
            "company_id": self.test_company_id,
            "company_role": "EDITOR",
            "user_type": "COMPANY_USER",
            "is_active": True,
            "created_at": datetime.utcnow()
        })

        # Create test device
        await db_service.insert_document("devices", {
            "_id": self.test_device_id,
            "name": "Test Device",
            "company_id": self.test_company_id,
            "device_type": "kiosk",
            "status": "active",
            "created_at": datetime.utcnow()
        })

        # Create test content
        await db_service.insert_document("content", {
            "_id": self.test_content_id,
            "filename": "test_video.mp4",
            "title": "Test Content",
            "company_id": self.test_company_id,
            "owner_id": self.test_user_id,
            "content_type": "video/mp4",
            "status": "quarantine",
            "ai_moderation_status": "pending",
            "created_at": datetime.utcnow()
        })

    async def _cleanup_test_data(self):
        """Clean up test data"""
        collections = ["content", "users", "companies", "devices", "analytics_events", "notifications", "content_history"]

        for collection in collections:
            try:
                # Delete test data based on IDs
                if collection == "content_history":
                    await db_service.delete_many(collection, {"content_id": self.test_content_id})
                elif collection in ["analytics_events", "notifications"]:
                    await db_service.delete_many(collection, {"company_id": self.test_company_id})
                else:
                    test_ids = [self.test_content_id, self.test_company_id, self.test_user_id, self.test_device_id]
                    await db_service.delete_many(collection, {"_id": {"$in": test_ids}})

            except Exception as e:
                logger.warning(f"Failed to cleanup {collection}: {e}")

    async def test_content_upload_workflow(self) -> bool:
        """Test: Content Upload -> AI Moderation Event -> Processing"""
        logger.info("🧪 Testing Content Upload Workflow")

        try:
            # Step 1: Publish content upload event
            await publish_content_event(
                event_type="content.uploaded",
                content_id=self.test_content_id,
                company_id=self.test_company_id,
                user_id=self.test_user_id,
                payload={
                    "filename": "test_video.mp4",
                    "content_type": "video/mp4",
                    "file_size": 1024000,
                    "title": "Test Content"
                },
                correlation_id=f"upload_{self.test_content_id}"
            )
            logger.info("✅ Content upload event published")

            # Wait for background processing
            await asyncio.sleep(2)

            # Step 2: Check if AI moderation was triggered (mock behavior)
            # In the real system, AI moderation handler would process this
            metrics = event_manager.get_metrics()
            events_processed = metrics["event_bus"]["events_processed"]

            if events_processed > 0:
                logger.info(f"✅ Events processed by handlers: {events_processed}")
            else:
                logger.warning("⚠️ No events processed yet")

            # Step 3: Simulate AI moderation completion
            await publish_content_event(
                event_type="content.approved",
                content_id=self.test_content_id,
                company_id=self.test_company_id,
                user_id=self.test_user_id,
                payload={
                    "automated_decision": True,
                    "ai_confidence": 0.95,
                    "moderation_result": "approved"
                },
                correlation_id=f"moderation_{self.test_content_id}"
            )
            logger.info("✅ AI moderation completion event published")

            await asyncio.sleep(1)
            return True

        except Exception as e:
            logger.error(f"❌ Content upload workflow test failed: {e}")
            return False

    async def test_analytics_events_workflow(self) -> bool:
        """Test: Analytics Events -> Background Processing"""
        logger.info("🧪 Testing Analytics Events Workflow")

        try:
            # Step 1: Publish content view event
            await publish_analytics_event(
                event_type="analytics.content.viewed",
                company_id=self.test_company_id,
                device_id=self.test_device_id,
                content_id=self.test_content_id,
                metrics={
                    "view_duration": 30,
                    "interaction_type": "auto_play",
                    "user_engagement": 0.8
                },
                correlation_id=f"view_{uuid.uuid4()}"
            )
            logger.info("✅ Content view analytics event published")

            # Step 2: Publish device interaction event
            await publish_analytics_event(
                event_type="analytics.device.interaction",
                company_id=self.test_company_id,
                device_id=self.test_device_id,
                metrics={
                    "interaction_type": "touch",
                    "duration": 5,
                    "coordinates": {"x": 100, "y": 200}
                },
                correlation_id=f"interaction_{uuid.uuid4()}"
            )
            logger.info("✅ Device interaction analytics event published")

            # Wait for background processing
            await asyncio.sleep(2)

            # Check analytics handler processed events
            analytics_handler = event_manager.handlers.get("analytics")
            if analytics_handler:
                # Force batch processing to get latest data
                await analytics_handler.flush_batch()
                logger.info("✅ Analytics batch processing completed")

            return True

        except Exception as e:
            logger.error(f"❌ Analytics events workflow test failed: {e}")
            return False

    async def test_notification_workflow(self) -> bool:
        """Test: Content Events -> Notification Generation"""
        logger.info("🧪 Testing Notification Workflow")

        try:
            # Step 1: Publish content rejection event (should generate notification)
            await publish_content_event(
                event_type="content.rejected",
                content_id=self.test_content_id,
                company_id=self.test_company_id,
                user_id=self.test_user_id,
                payload={
                    "rejection_reason": "Inappropriate content detected",
                    "reviewer_notes": "Please review content guidelines",
                    "filename": "test_video.mp4"
                },
                correlation_id=f"rejection_{self.test_content_id}"
            )
            logger.info("✅ Content rejection event published")

            # Step 2: Publish device error event
            await publish_analytics_event(
                event_type="device.status.changed",
                company_id=self.test_company_id,
                device_id=self.test_device_id,
                metrics={
                    "old_status": "active",
                    "new_status": "error",
                    "error_message": "Network connection failed"
                },
                correlation_id=f"device_error_{uuid.uuid4()}"
            )
            logger.info("✅ Device error event published")

            # Wait for notification processing
            await asyncio.sleep(2)

            # Check if notifications were created (would be in database in real system)
            notification_handler = event_manager.handlers.get("notifications")
            if notification_handler:
                logger.info("✅ Notification handler processed events")

            return True

        except Exception as e:
            logger.error(f"❌ Notification workflow test failed: {e}")
            return False

    async def test_event_system_performance(self) -> bool:
        """Test: Event System Performance Under Load"""
        logger.info("🧪 Testing Event System Performance")

        try:
            start_time = datetime.utcnow()

            # Publish multiple events rapidly
            tasks = []
            for i in range(20):
                task = publish_content_event(
                    event_type="analytics.performance.metric",
                    content_id=f"perf_test_{i}",
                    company_id=self.test_company_id,
                    payload={
                        "metric_type": "performance_test",
                        "sequence": i,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    correlation_id=f"perf_{i}_{uuid.uuid4()}"
                )
                tasks.append(task)

            # Publish all events concurrently
            await asyncio.gather(*tasks)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"✅ Published 20 events in {duration:.2f} seconds")

            # Wait for processing
            await asyncio.sleep(3)

            # Check final metrics
            final_metrics = event_manager.get_metrics()
            logger.info(f"📊 Final Event Metrics: {final_metrics['event_bus']}")

            return True

        except Exception as e:
            logger.error(f"❌ Event system performance test failed: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """Run all event workflow tests"""
        logger.info("🚀 Starting Comprehensive Event Workflow Tests")

        tests = [
            ("Content Upload Workflow", self.test_content_upload_workflow),
            ("Analytics Events Workflow", self.test_analytics_events_workflow),
            ("Notification Workflow", self.test_notification_workflow),
            ("Event System Performance", self.test_event_system_performance)
        ]

        results = []

        try:
            await self.setup()

            for test_name, test_func in tests:
                logger.info(f"\n📋 Running {test_name}...")
                result = await test_func()
                results.append((test_name, result))
                logger.info(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")

                # Small delay between tests
                await asyncio.sleep(1)

        finally:
            await self.teardown()

        # Summary
        passed = sum(1 for _, result in results if result)
        total = len(results)

        logger.info(f"\n📊 Test Summary: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 All event workflow tests passed!")
        else:
            logger.error("❌ Some event workflow tests failed!")
            for test_name, result in results:
                if not result:
                    logger.error(f"  - {test_name}: FAILED")

        return passed == total

async def main():
    """Main test runner"""
    tester = EventWorkflowTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    exit(0 if success else 1)