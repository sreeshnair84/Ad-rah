#!/usr/bin/env python3
"""Debug user database content"""

import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.database_service import db_service

async def debug_users():
    await db_service.initialize()
    
    print("=== DEBUG USER DATABASE ===")
    
    # Count total users
    total_users = await db_service.db.users.count_documents({})
    print(f"Total users in database: {total_users}")
    
    # Count active users
    active_users = await db_service.db.users.count_documents({"is_active": True})
    print(f"Active users: {active_users}")
    
    # List all users (raw)
    cursor = db_service.db.users.find({})
    async for user in cursor:
        print(f"User: {user['email']} - Type: {user.get('user_type')} - Active: {user.get('is_active')}")
    
    # Test list_all_users function
    print("\n=== Testing list_all_users() ===")
    try:
        users = await db_service.list_all_users()
        print(f"list_all_users() returned: {len(users)} users")
        for user in users:
            print(f"  - {user.email} ({user.user_type})")
    except Exception as e:
        print(f"list_all_users() failed: {e}")
    
    # Test list_users_by_company
    print("\n=== Testing list_users_by_company() ===")
    try:
        # Get first company ID
        company = await db_service.db.companies.find_one({})
        if company:
            company_id = str(company["_id"])
            users = await db_service.list_users_by_company(company_id)
            print(f"list_users_by_company('{company['name']}') returned: {len(users)} users")
            for user in users:
                print(f"  - {user.email} ({user.user_type})")
        else:
            print("No companies found")
    except Exception as e:
        print(f"list_users_by_company() failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_users())