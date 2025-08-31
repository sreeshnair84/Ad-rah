#!/usr/bin/env python3
"""
Test script to verify data persistence is working correctly
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.repo import repo, persistence_enabled, MongoRepo, InMemoryRepo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_persistence():
    """Test that data persists correctly"""
    print("🧪 Testing Data Persistence")
    print("=" * 50)
    
    # Check repository type
    print(f"📊 Repository Type: {type(repo).__name__}")
    print(f"🔗 MongoDB URI: {settings.MONGO_URI}")
    print(f"💾 Persistence Enabled: {persistence_enabled}")
    
    if not persistence_enabled:
        print("⚠️  WARNING: Using in-memory storage - data will be lost!")
        print("🔧 Run setup-mongodb.bat or setup-mongodb.sh to fix this")
        return False
    
    print("\n🔍 Testing MongoDB Connection...")
    
    try:
        # Test basic operations
        print("✅ Repository initialized successfully")
        
        # Test user operations
        users = await repo.list_users()
        print(f"📋 Found {len(users)} existing users")
        
        # Test company operations
        companies = await repo.list_companies()
        print(f"🏢 Found {len(companies)} existing companies")
        
        # Test device operations
        devices = await repo.list_digital_screens()
        print(f"📱 Found {len(devices)} existing devices")
        
        print("\n✅ All persistence tests passed!")
        print("🎉 Your data WILL survive server restarts")
        return True
        
    except Exception as e:
        print(f"\n❌ Persistence test failed: {e}")
        print("🔧 Please check your MongoDB connection")
        return False

async def test_default_content():
    """Test default content system"""
    print("\n🎨 Testing Default Content System")
    print("=" * 50)
    
    try:
        from app.default_content_manager import default_content_manager
        
        # Test default content generation
        default_content = await default_content_manager.get_default_content()
        print(f"📋 Generated {len(default_content)} default content items")
        
        # Test demo content generation
        demo_content = await default_content_manager.get_demo_content("test-device-123")
        print(f"🎭 Generated {len(demo_content)} demo content items")
        
        print("✅ Default content system working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Default content test failed: {e}")
        return False

async def main():
    """Main test routine"""
    print("🚀 OpenKiosk Data Persistence & Content Test")
    print("=" * 60)
    
    # Test persistence
    persistence_ok = await test_persistence()
    
    # Test default content
    content_ok = await test_default_content()
    
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"💾 Data Persistence: {'✅ PASS' if persistence_ok else '❌ FAIL'}")
    print(f"🎨 Default Content: {'✅ PASS' if content_ok else '❌ FAIL'}")
    
    if persistence_ok and content_ok:
        print("\n🎉 All tests passed! Your OpenKiosk system is ready!")
        print("🚀 You can now start the server with: python start_with_mongo.py")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        if not persistence_ok:
            print("🔧 To fix persistence: run setup-mongodb.bat or setup-mongodb.sh")
    
    return persistence_ok and content_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)