#!/usr/bin/env python3
"""
Local Event Processor Test Script

This script demonstrates how the local event processor works
and allows you to test event processing without external dependencies.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.event_processor import LocalEventProcessor
from app.repo import InMemoryRepo
from app.models import ContentMetadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_event_processor():
    """Test the local event processor with sample events"""

    logger.info("🚀 Starting Local Event Processor Test")

    # Create components
    processor = LocalEventProcessor()
    repo = InMemoryRepo()

    # Start the processor
    await processor.start()

    try:
        logger.info("📝 Creating sample content...")

        # Create sample content
        content = ContentMetadata(
            title="Test Advertisement",
            description="This is a test advertisement for local development",
            owner_id="test-user-123",
            categories=["advertisement", "test"],
            tags=["demo", "local"]
        )

        # Save content to repository
        saved_content = await repo.save(content)
        content_id = saved_content["id"]

        logger.info(f"✅ Content created with ID: {content_id}")

        # Send content uploaded event
        logger.info("📤 Sending content_uploaded event...")
        await processor.send_event("content_uploaded", {
            "content_id": content_id,
            "content_type": "image/jpeg",
            "filename": "test-ad.jpg"
        })

        # Wait for event processing
        logger.info("⏳ Waiting for event processing...")
        await asyncio.sleep(3)

        # Check moderation results
        logger.info("🔍 Checking moderation results...")
        reviews = await repo.list_reviews()
        if reviews:
            review = reviews[0]
            logger.info(f"📋 Moderation Result: {review['action']} (confidence: {review['ai_confidence']:.2f})")
        else:
            logger.warning("⚠️  No moderation reviews found")

        # Test permission checking
        logger.info("🛡️  Testing permission system...")
        from app.models import Permission, Screen, User

        # Create a test user and role (this would normally be done through API)
        logger.info("👤 Creating test user and role...")
        test_user_model = User(
            name="Test User",
            email="test@example.com",
            hashed_password="hashed_password",
            status="active"
        )
        test_user = await repo.save_user(test_user_model)

        # Check if user has permission (will be False since no roles assigned)
        has_permission = await repo.check_user_permission(
            test_user["id"], "company-123", Screen.DASHBOARD, Permission.VIEW
        )
        logger.info(f"🔒 User permission check result: {has_permission}")

        logger.info("✅ Local Event Processor Test Completed!")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
    finally:
        # Stop the processor
        await processor.stop()


async def interactive_test():
    """Interactive test mode for manual testing"""

    logger.info("🎮 Starting Interactive Test Mode")
    logger.info("This mode allows you to send events manually and see how they're processed")

    processor = LocalEventProcessor()
    await processor.start()

    try:
        while True:
            print("\n" + "="*50)
            print("Local Event Processor - Interactive Test")
            print("="*50)
            print("1. Send content_uploaded event")
            print("2. Send moderation_requested event")
            print("3. Send content_approved event")
            print("4. View processor status")
            print("5. Exit")
            print("="*50)

            choice = input("Enter your choice (1-5): ").strip()

            if choice == "1":
                content_id = input("Enter content ID: ").strip()
                if content_id:
                    await processor.send_event("content_uploaded", {
                        "content_id": content_id,
                        "content_type": "image/jpeg",
                        "filename": "test.jpg"
                    })
                    print(f"✅ Sent content_uploaded event for {content_id}")

            elif choice == "2":
                content_id = input("Enter content ID: ").strip()
                if content_id:
                    await processor.send_event("moderation_requested", {
                        "content_id": content_id
                    })
                    print(f"✅ Sent moderation_requested event for {content_id}")

            elif choice == "3":
                content_id = input("Enter content ID: ").strip()
                if content_id:
                    await processor.send_event("content_approved", {
                        "content_id": content_id
                    })
                    print(f"✅ Sent content_approved event for {content_id}")

            elif choice == "4":
                print(f"📊 Processor running: {processor.running}")
                print(f"📋 Events in queue: {processor.event_queue.qsize()}")

            elif choice == "5":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please try again.")

            # Wait a bit for event processing
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Interactive test failed: {e}")
    finally:
        await processor.stop()


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Interactive mode
        asyncio.run(interactive_test())
    else:
        # Automated test
        asyncio.run(test_event_processor())


if __name__ == "__main__":
    main()
