#!/usr/bin/env python3
"""Test the list_all_users method issue"""

import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.database_service import db_service
from bson import ObjectId

async def test_list_all_users_issue():
    await db_service.initialize()
    
    print("=== TESTING list_all_users() METHOD ===")
    
    # First, let's check what get_user_profile returns for a known user
    # Get one user from the database
    user_doc = await db_service.db.users.find_one({"email": "admin@adara.com"})
    if user_doc:
        print(f"Raw user document: {user_doc}")
        user_id = str(user_doc["_id"])
        print(f"User ID: {user_id}")
        
        # Test get_user_profile
        try:
            user_profile = await db_service.get_user_profile(user_id)
            print(f"get_user_profile result: {user_profile}")
        except Exception as e:
            print(f"get_user_profile failed: {e}")
    
    # Now test list_all_users
    try:
        users = await db_service.list_all_users()
        print(f"\nlist_all_users() returned: {len(users)} users")
        
        if len(users) == 0:
            print("ERROR: list_all_users returned 0 users but we know there are users in the database!")
            
            # Let's debug step by step
            print("\nDEBUGGING list_all_users()...")
            cursor = db_service.db.users.find({"is_active": True}).sort("created_at", -1)
            
            async for user_doc in cursor:
                print(f"\nProcessing user: {user_doc['email']}")
                user_doc = db_service._object_id_to_str(user_doc)
                print(f"After _object_id_to_str: ID = {user_doc.get('id')}")
                
                try:
                    user_profile = await db_service.get_user_profile(user_doc["id"])
                    if user_profile:
                        print(f"✓ Successfully got profile for {user_doc['email']}")
                    else:
                        print(f"✗ get_user_profile returned None for {user_doc['email']}")
                except Exception as e:
                    print(f"✗ get_user_profile failed for {user_doc['email']}: {e}")
                
                break  # Just test first one
        else:
            for user in users:
                print(f"  - {user.email} ({user.user_type})")
    except Exception as e:
        print(f"list_all_users() failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_list_all_users_issue())