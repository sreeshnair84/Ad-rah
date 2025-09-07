#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_device_keys_rbac():
    """Test device keys endpoint with different user roles"""
    
    print("TESTING DEVICE KEYS RBAC")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Super User Access (create one first)
        print("1. Creating and testing SUPER USER access...")
        
        # First try the existing admin user
        admin_login = {
            "email": "admin@dubaimall-displays.com", 
            "password": "HostAdmin123!"
        }
        
        async with session.post(f"{backend_url}/api/auth/login", json=admin_login) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                admin_token = login_result.get("access_token")
                user_info = login_result.get("user", {})
                print(f"✅ Admin login successful")
                print(f"   User Type: {user_info.get('user_type')}")
                company_info = user_info.get('company') if user_info.get('company') else {}
                print(f"   Company: {company_info.get('name', 'N/A')}")
            else:
                print(f"❌ Admin login failed: {resp.status}")
                admin_token = None
        
        # Test device keys access
        if admin_token:
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            print("\n   Testing admin device keys access...")
            async with session.get(f"{frontend_url}/api/device/keys", headers=headers) as resp:
                if resp.status == 200:
                    keys = await resp.json()
                    print(f"   ✅ Admin can see {len(keys)} keys")
                    for key in keys[:2]:  # Show first 2 keys only
                        print(f"      - Key: {key.get('key')[:8]}... | Company: {key.get('company_name')} | Used: {key.get('used')}")
                else:
                    result_text = await resp.text()
                    print(f"   ❌ Admin keys access failed: {resp.status}")
                    print(f"      Response: {result_text}")
        
        print("\n" + "="*50)
        
        # Test 2: Generate another key to verify functionality
        print("2. Testing key generation...")
        if admin_token:
            headers = {"Authorization": f"Bearer {admin_token}"}
            key_data = {
                "company_id": "company_host_dubai_mall"
            }
            
            async with session.post(f"{frontend_url}/api/device/generate-key", json=key_data, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"   ✅ Key generation successful!")
                    print(f"      New Key: {result.get('registration_key')}")
                    print(f"      Company: {result.get('company_name')}")
                else:
                    result_text = await resp.text()
                    print(f"   ❌ Key generation failed: {resp.status}")
                    print(f"      Response: {result_text}")
        
        print("\n" + "="*50)
        
        # Test 3: Verify updated keys list
        print("3. Verifying updated keys list...")
        if admin_token:
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            async with session.get(f"{frontend_url}/api/device/keys", headers=headers) as resp:
                if resp.status == 200:
                    keys = await resp.json()
                    print(f"   ✅ Admin now sees {len(keys)} keys total")
                    
                    # Show all keys with details
                    for i, key in enumerate(keys, 1):
                        print(f"      {i}. Key: {key.get('key')[:8]}...")
                        print(f"         Company: {key.get('company_name')}")
                        print(f"         Org Code: {key.get('organization_code')}")
                        print(f"         Used: {key.get('used')}")
                        print(f"         Created: {key.get('created_at', 'N/A')[:19]}")
                        print("-" * 30)
                else:
                    print(f"   ❌ Keys list failed: {resp.status}")

if __name__ == "__main__":
    asyncio.run(test_device_keys_rbac())
