#!/usr/bin/env python3
import asyncio
import os

# Set environment variable BEFORE importing anything
os.environ['MONGO_URI'] = 'mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin'

from dotenv import load_dotenv
from app.database_service import db_service

# Load environment variables from .env
load_dotenv()

async def test_navigation():
    try:
        await db_service.initialize()
        print('Database connected')
        
        # Test super user navigation
        user_by_email = await db_service.get_user_by_email('admin@adara.com')
        if user_by_email:
            print(f'Super user found: {user_by_email.get("email")}')
            user_id = user_by_email['id']
            print(f'User ID from email lookup: {user_id}')
            print(f'User data keys: {list(user_by_email.keys())}')
            
            # Debug the profile lookup
            print(f'Looking up profile with ID: {user_id}')
            
            # Test direct database query
            direct_user = await db_service.db.users.find_one({"id": user_id, "is_active": True})
            print(f'Direct query result: {"Found" if direct_user else "Not found"}')
            
            # Also check by email to see what's actually stored
            email_user = await db_service.db.users.find_one({"email": "admin@adara.com"})
            print(f'Email query result: {"Found" if email_user else "Not found"}')
            
            if email_user:
                print(f'Email user keys: {list(email_user.keys())}')
                print(f'Email user _id: {email_user.get("_id")}')
                print(f'Email user id field: {email_user.get("id")}')
                print(f'Email user is_active: {email_user.get("is_active")}')
                print(f'Email user type: {email_user.get("user_type")}')
            
            user_profile = await db_service.get_user_profile(user_id)
            if user_profile:
                print(f'User type: {user_profile.user_type}')
                print(f'Navigation count: {len(user_profile.accessible_navigation)}')
                print(f'Navigation items: {user_profile.accessible_navigation}')
                
                # Expected: Should be 23 items for super user, not 6
                expected_items = [
                    "dashboard", "unified", "users", "roles", "registration",
                    "content", "my-content", "my-ads", "upload", "moderation", 
                    "ads-approval", "host-review", "content-overlay",
                    "kiosks", "device-keys", "digital-twin",
                    "analytics", "analytics/real-time", "performance",
                    "schedules", "settings", "master-data", "billing"
                ]
                
                print(f'Expected {len(expected_items)} items, got {len(user_profile.accessible_navigation)}')
                
                if len(user_profile.accessible_navigation) == len(expected_items):
                    print('SUCCESS: Super admin has full navigation access')
                else:
                    print('ISSUE: Super admin has limited navigation access')
                    missing = set(expected_items) - set(user_profile.accessible_navigation)
                    print(f'Missing items: {list(missing)}')
                
            else:
                print('User profile not found')
        else:
            print('Super user not found by email')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_navigation())