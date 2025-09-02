#!/usr/bin/env python3
"""
Test complete authentication and authorization flow
"""
import asyncio
import os
import sys
import requests
import json

# Set up the path and environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables FIRST
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Environment variables loaded")
except ImportError:
    print("[WARNING] python-dotenv not installed")

async def test_complete_auth_flow():
    """Test complete authentication and API access flow"""
    print("🔍 Testing complete authentication flow...")
    
    try:
        base_url = "http://localhost:8000"
        
        # 1. Test health endpoint
        print("\n1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        print(f"   - Health status: {response.status_code}")
        if response.status_code == 200:
            print(f"   - Response: {response.json()}")
        
        # 2. Test login
        print("\n2. Testing login...")
        login_data = {
            "email": "admin@openkiosk.com",
            "password": "adminpass"
        }
        
        response = requests.post(
            f"{base_url}/api/auth/login",
            headers={"Content-Type": "application/json"},
            json=login_data
        )
        
        print(f"   - Login status: {response.status_code}")
        if response.status_code == 200:
            login_response = response.json()
            access_token = login_response.get("access_token")
            print(f"   - Access token received: {bool(access_token)}")
            print(f"   - User type: {login_response.get('user', {}).get('user_type')}")
            print(f"   - Is super admin: {login_response.get('is_super_admin')}")
            
            # 3. Test API access with token
            print("\n3. Testing API access...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Test users API
            response = requests.get(f"{base_url}/api/users", headers=headers)
            print(f"   - Users API status: {response.status_code}")
            if response.status_code != 200:
                print(f"   - Error: {response.text}")
            else:
                users = response.json()
                print(f"   - Users found: {len(users) if isinstance(users, list) else 'N/A'}")
            
            # Test roles API
            response = requests.get(f"{base_url}/api/roles", headers=headers)
            print(f"   - Roles API status: {response.status_code}")
            if response.status_code != 200:
                print(f"   - Error: {response.text}")
            else:
                roles = response.json()
                print(f"   - Roles found: {len(roles) if isinstance(roles, list) else 'N/A'}")
                
        else:
            print(f"   - Login failed: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_auth_flow())
