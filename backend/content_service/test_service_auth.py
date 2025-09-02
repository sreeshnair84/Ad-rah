#!/usr/bin/env python3
"""
Test authentication using the actual service layer
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

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.database import DatabaseProvider

async def test_service_auth():
    """Test authentication using actual service layer"""
    print("🔍 Testing authentication via service layer...")
    
    try:
        # Initialize database
        from app.config import settings
        mongo_uri = getattr(settings, "MONGO_URI", None)
        if mongo_uri:
            print("Initializing database connection...")
            from app.database import initialize_database_from_url
            await initialize_database_from_url(mongo_uri)
        
        # Initialize services (they use lazy initialization)
        user_service = UserService()
        auth_service = AuthService()
        
        # Test user lookup
        email = "admin@openkiosk.com"
        print(f"\n1. Testing user lookup: {email}")
        
        user_result = await user_service.get_user_by_email(email)
        print(f"   - Success: {user_result.success}")
        if user_result.success:
            user_data = user_result.data
            print(f"   - User found: {user_data.get('name', 'Unknown')}")
            print(f"   - Status: {user_data.get('status', 'Unknown')}")
            print(f"   - Active: {user_data.get('is_active', 'Unknown')}")
        else:
            print(f"   - Error: {user_result.error}")
        
        # Test authentication
        print(f"\n2. Testing authentication...")
        password = "adminpass"
        
        auth_result = await user_service.authenticate_user(email, password)
        print(f"   - Success: {auth_result.success}")
        if auth_result.success:
            print(f"   - User authenticated successfully")
            user_profile = auth_result.data
            print(f"   - User ID: {user_profile.get('id')}")
            print(f"   - Name: {user_profile.get('name')}")
        else:
            print(f"   - Error: {auth_result.error}")
        
        # Test full login
        print(f"\n3. Testing full login...")
        login_result = await auth_service.login(email, password)
        print(f"   - Success: {login_result.success}")
        if login_result.success:
            print(f"   - Access token generated: {bool(login_result.data.get('access_token'))}")
            print(f"   - Is super admin: {login_result.data.get('is_super_admin', False)}")
        else:
            print(f"   - Error: {login_result.error}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_service_auth())
