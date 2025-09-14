#!/usr/bin/env python3
"""Test script to verify editor login works with RBAC permissions"""
import sys
import asyncio
import os
from pathlib import Path
sys.path.append('.')

# Load environment variables from .env file
from dotenv import load_dotenv
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"📁 Loaded environment from: {env_file}")
else:
    print("⚠️  No .env file found")

from app.auth_service import AuthService
from app.services.user_service import UserService
from app.database_service import db_service

async def test_editor_login():
    """Test editor login and verify permissions"""
    print("Testing Editor Login Authentication")
    print("=" * 50)
    
    # Initialize database
    await db_service.initialize()
    
    auth_service = AuthService()
    user_service = UserService()
    
    # Test editor login
    email = "editor@dubaimall-displays.com"
    password = "HostEditor123!"
    
    print(f"Attempting login for: {email}")
    
    try:
        # First check if user exists
        user_result = await user_service.get_user_by_email(email)
        if user_result.success and user_result.data:
            user_data = user_result.data
            print(f"✅ User found: {user_data.get('name', 'Unknown')}")
            print(f"   Role: {user_data.get('role', 'Unknown')}")
            print(f"   Company: {user_data.get('company_name', 'Unknown')}")
            print(f"   Debug - User data keys: {list(user_data.keys())}")
            
            # Get permissions - use _id instead of id
            user_id = user_data.get('_id') or user_data.get('id')
            if user_id:
                user_profile = await user_service.get_user_profile(user_id)
                if user_profile.success and user_profile.data:
                    permissions = user_profile.data.get('permissions', [])
                    print(f"   Permissions: {permissions}")
                else:
                    print("   ❌ Could not get user permissions")
                    permissions = []
            else:
                print("   ❌ No user ID found")
                permissions = []
        else:
            print("❌ User not found")
            return False
        
        # Test authentication
        user = await auth_service.authenticate_user(email, password)
        
        if user:
            print(f"✅ Authentication successful!")
            print(f"   User Email: {user.email}")
            print(f"   Display Name: {user.display_name}")
            
            # Check permissions
            required_permissions = ['content_distribute', 'overlay_create', 'digital_twin_view']
            
            print(f"   Frontend Permissions:")
            for perm in permissions:
                print(f"     - {perm}")
            
            print(f"\n   Required permissions check:")
            for req_perm in required_permissions:
                if req_perm in permissions:
                    print(f"     ✅ {req_perm}")
                else:
                    print(f"     ❌ {req_perm}")
            
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during login test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db_service.close()

if __name__ == "__main__":
    success = asyncio.run(test_editor_login())
    if success:
        print("\n🎉 Editor login test PASSED!")
    else:
        print("\n💥 Editor login test FAILED!")
    
    sys.exit(0 if success else 1)
