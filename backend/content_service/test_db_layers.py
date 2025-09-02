#!/usr/bin/env python3
"""
Test database service configuration
"""
import asyncio
import os
import sys

# Set up the path and environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables FIRST
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Environment variables loaded")
except ImportError:
    print("[WARNING] python-dotenv not installed")

from app.database import get_db_service
from app.repo import repo

async def test_database_services():
    """Test both database layers"""
    print("🔍 Testing database service layers...")
    
    try:
        # Test repository layer
        print("\n1. Testing repository layer...")
        user = await repo.get_user_by_email("admin@openkiosk.com")
        if user:
            print(f"   ✓ Repository found user: {user.get('name', 'Unknown')}")
        else:
            print("   ✗ Repository did not find user")
        
        # Test database service layer
        print("\n2. Testing database service layer...")
        from app.config import settings
        mongo_uri = getattr(settings, "MONGO_URI", None)
        if mongo_uri:
            print(f"   - MONGO_URI configured: Yes")
            from app.database import initialize_database_from_url
            await initialize_database_from_url(mongo_uri)
        else:
            print(f"   - MONGO_URI configured: No")
        
        db_service = get_db_service()
        print(f"   - Database service type: {type(db_service).__name__}")
        
        # Test finding user via service layer
        from app.database import QueryFilter, FilterOperation
        filters = [
            QueryFilter("email", FilterOperation.EQUALS, "admin@openkiosk.com"),
            QueryFilter("is_deleted", FilterOperation.EQUALS, False)
        ]
        
        result = await db_service.find_one_record("users", filters)
        print(f"   - Service layer success: {result.success}")
        if result.success:
            user_data = result.data
            print(f"   ✓ Service found user: {user_data.get('name', 'Unknown')}")
        else:
            print(f"   ✗ Service error: {result.error}")
        
        # List all users to see what's in the database
        print("\n3. Listing all users via service layer...")
        all_users_result = await db_service.find_records("users", [])
        print(f"   - Success: {all_users_result.success}")
        if all_users_result.success:
            users = all_users_result.data
            print(f"   - Total users found: {len(users)}")
            for user in users:
                print(f"     - {user.get('email', 'No email')}: {user.get('name', 'No name')}")
        else:
            print(f"   - Error: {all_users_result.error}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_services())
