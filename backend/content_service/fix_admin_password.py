#!/usr/bin/env python3
"""Fix admin user password directly in database"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def fix_admin_password():
    """Fix admin user password in database"""
    from app.database_service import db_service
    from app.auth_service import auth_service
    
    try:
        # Initialize database
        await db_service.initialize()
        
        # Hash the password using the auth service method
        new_hashed_password = auth_service.hash_password("admin")
        
        # Update the admin user directly in database
        update_result = await db_service.users_collection.update_one(
            {"email": "admin@adara.com"},
            {
                "$set": {
                    "hashed_password": new_hashed_password,
                    "user_type": "SUPER_USER",
                    "is_active": True,
                    "status": "active"
                }
            }
        )
        
        if update_result.modified_count > 0:
            print("Admin password updated successfully")
            
            # Verify the update worked
            admin_user = await db_service.get_user_by_email("admin@adara.com")
            if admin_user:
                password_match = auth_service.verify_password("admin", admin_user.get("hashed_password", ""))
                print(f"Password verification: {password_match}")
                print(f"User type: {admin_user.get('user_type')}")
                print(f"Is active: {admin_user.get('is_active')}")
            else:
                print("Could not retrieve user after update")
        else:
            print("No user was updated - user might not exist")
        
    except Exception as e:
        print(f"Error fixing admin password: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(fix_admin_password())