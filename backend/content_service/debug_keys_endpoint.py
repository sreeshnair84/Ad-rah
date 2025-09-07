#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def debug_keys_endpoint():
    """Debug the device keys endpoint and user access"""
    
    print("DEBUGGING DEVICE KEYS ENDPOINT")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test backend keys endpoint directly
        print("1. Testing backend keys endpoint directly...")
        admin_login = {
            "email": "admin@dubaimall-displays.com",
            "password": "HostAdmin123!"
        }
        
        async with session.post(f"{backend_url}/api/auth/login", json=admin_login) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                token = login_result.get("access_token")
                print(f"✅ Login successful")
            else:
                print(f"❌ Login failed: {resp.status}")
                return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test backend endpoint directly
        async with session.get(f"{backend_url}/api/device/keys", headers=headers) as resp:
            result_text = await resp.text()
            print(f"Backend /api/device/keys Status: {resp.status}")
            print(f"Backend Response: {result_text}")
        
        # Check what users exist
        print("\n2. Checking available users...")
        async with session.get(f"{backend_url}/api/auth/users", headers=headers) as resp:
            if resp.status == 200:
                users = await resp.json()
                print(f"Found {len(users)} users:")
                for user in users:
                    print(f"  - Email: {user.get('email')}, Type: {user.get('user_type')}, Company: {user.get('company_id', 'None')}")
            else:
                print(f"Failed to get users: {resp.status}")
        
        # Test repo methods directly
        print("\n3. Testing repo device registration keys...")
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            from app.repo import repo
            keys = await repo.list_device_registration_keys()
            print(f"Repo found {len(keys)} registration keys:")
            for key in keys:
                print(f"  - Key: {key.get('key', 'N/A')[:8]}..., Company: {key.get('company_id', 'N/A')}, Used: {key.get('used', 'N/A')}")
        except Exception as e:
            print(f"Failed to test repo: {e}")

if __name__ == "__main__":
    asyncio.run(debug_keys_endpoint())
