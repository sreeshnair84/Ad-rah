#!/usr/bin/env python3

import asyncio
import requests
import json

async def test_role_access():
    """Test role access with authentication"""
    
    # First login to get a token
    login_url = "http://localhost:8000/api/auth/login"
    login_data = {
        "email": "admin@openkiosk.com",
        "password": "adminpass"
    }
    
    print("🔐 Attempting login...")
    login_response = requests.post(login_url, json=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    login_result = login_response.json()
    token = login_result.get("access_token")
    user_info = login_result.get("user")
    
    print(f"✅ Login successful!")
    print(f"User: {user_info.get('email')} ({user_info.get('user_type')})")
    print(f"Permissions: {user_info.get('permissions', [])[:5]}...")  # Show first 5 permissions
    print(f"Is Super Admin: {user_info.get('is_super_admin')}")
    
    # Test roles endpoint
    roles_url = "http://localhost:8000/api/roles/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n🔍 Testing roles endpoint...")
    roles_response = requests.get(roles_url, headers=headers)
    print(f"Roles status: {roles_response.status_code}")
    
    if roles_response.status_code == 200:
        roles = roles_response.json()
        print(f"✅ Roles access successful! Found {len(roles)} roles")
        for role in roles[:3]:  # Show first 3 roles
            print(f"  - {role.get('name')} ({role.get('role_group')})")
    else:
        print(f"❌ Roles access failed: {roles_response.text}")

if __name__ == "__main__":
    asyncio.run(test_role_access())
