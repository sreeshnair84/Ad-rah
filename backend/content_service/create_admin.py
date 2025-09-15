#!/usr/bin/env python3
"""Create admin user directly"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def create_admin_user():
    """Create admin user for testing"""
    from app.database_service import db_service
    from app.auth_service import auth_service
    
    try:
        # Initialize database
        await db_service.initialize()
        
        # Check if admin user already exists
        existing_admin = await db_service.get_user_by_email("admin@adara.com")
        if existing_admin:
            print("✅ Admin user already exists")
            return
        
        # Create admin user directly in database
        hashed_password = auth_service.hash_password("admin")
        
        user_data = {
            "email": "admin@adara.com",
            "first_name": "Admin",
            "last_name": "User",
            "name": "Admin User",
            "hashed_password": hashed_password,
            "user_type": "SUPER_USER",
            "company_id": None,
            "company_role": "ADMIN",
            "permissions": ["*"],
            "is_active": True,
            "status": "active",
            "email_verified": True
        }
        
        # Insert user directly
        result = await db_service.users_collection.insert_one(user_data)
        if result.inserted_id:
            print("✅ Admin user created successfully")
            print("   Email: admin@adara.com")
            print("   Password: admin")
        else:
            print("❌ Failed to create admin user")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())