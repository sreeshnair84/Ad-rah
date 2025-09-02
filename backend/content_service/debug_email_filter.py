#!/usr/bin/env python3
"""
Debug email filtering issue
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

from app.database import get_db_service, QueryFilter, FilterOperation

async def debug_email_filtering():
    """Debug email filtering issue"""
    print("🔍 Debugging email filtering...")
    
    try:
        # Initialize database
        from app.config import settings
        mongo_uri = getattr(settings, "MONGO_URI", None)
        if mongo_uri:
            from app.database import initialize_database_from_url
            await initialize_database_from_url(mongo_uri)
        
        db_service = get_db_service()
        
        # Get all users first to see the exact structure
        print("\n1. Getting all users to examine structure...")
        all_users_result = await db_service.find_records("users", [])
        
        if all_users_result.success:
            users = all_users_result.data
            target_user = None
            
            for user in users:
                if "admin@openkiosk.com" in str(user.get('email', '')):
                    target_user = user
                    break
            
            if target_user:
                print(f"   ✓ Found target user in list:")
                print(f"     - Email: '{target_user.get('email')}'")
                print(f"     - Email type: {type(target_user.get('email'))}")
                print(f"     - Email length: {len(str(target_user.get('email')))}")
                print(f"     - is_deleted: {target_user.get('is_deleted')}")
                print(f"     - is_deleted type: {type(target_user.get('is_deleted'))}")
                
                # Test different filter variations
                test_emails = [
                    "admin@openkiosk.com",
                    "ADMIN@OPENKIOSK.COM",
                    "admin@openkiosk.com".lower(),
                    "admin@openkiosk.com".upper()
                ]
                
                print(f"\n2. Testing different email filter variations...")
                for test_email in test_emails:
                    filters = [
                        QueryFilter("email", FilterOperation.EQUALS, test_email),
                        QueryFilter("is_deleted", FilterOperation.EQUALS, False)
                    ]
                    
                    result = await db_service.find_one_record("users", filters)
                    print(f"   - '{test_email}': {result.success}")
                
                # Test without is_deleted filter
                print(f"\n3. Testing without is_deleted filter...")
                filters = [QueryFilter("email", FilterOperation.EQUALS, "admin@openkiosk.com")]
                result = await db_service.find_one_record("users", filters)
                print(f"   - Email only filter: {result.success}")
                
                # Test with different is_deleted values
                print(f"\n4. Testing different is_deleted values...")
                for is_deleted_val in [False, None, True]:
                    filters = [
                        QueryFilter("email", FilterOperation.EQUALS, "admin@openkiosk.com"),
                        QueryFilter("is_deleted", FilterOperation.EQUALS, is_deleted_val)
                    ]
                    result = await db_service.find_one_record("users", filters)
                    print(f"   - is_deleted={is_deleted_val}: {result.success}")
                
            else:
                print("   ✗ Target user not found in list!")
        else:
            print(f"   ✗ Error getting users: {all_users_result.error}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_email_filtering())
