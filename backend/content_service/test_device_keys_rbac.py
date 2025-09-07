#!/usr/bin/env py        # Test 1: Super User Access
        print("1. Testing SUPER USER access...")
        super_user_login = {
            "email": "super@admin.com",
            "password": "SuperAdmin123!"
        }
        
        async with session.post(f"{backend_url}/api/auth/login", json=super_user_login) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                super_token = login_result.get("access_token")
                user_info = login_result.get("user", {})
                print(f"✅ Super user login successful")
                print(f"   User Type: {user_info.get('user_type')}")
                company_info = user_info.get('company') if user_info.get('company') else {}
                print(f"   Company: {company_info.get('name', 'N/A')}")
            else:
                print(f"❌ Super user login failed: {resp.status}")
                super_token = None
import aiohttp
import json

async def test_device_keys_rbac():
    """Test device keys endpoint with different user roles"""
    
    print("TESTING DEVICE KEYS RBAC")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Super User Access
        print("1. Testing SUPER USER access...")
        super_user_login = {
            "email": "admin@adara.com",
            "password": "SuperAdmin123!"
        }
        
        async with session.post(f"{backend_url}/api/auth/login", json=super_user_login) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                super_token = login_result.get("access_token")
                user_info = login_result.get("user", {})
                print(f"✅ Super user login successful")
                print(f"   User Type: {user_info.get('user_type')}")
                print(f"   Company: {user_info.get('company', {}).get('name', 'N/A')}")
            else:
                print(f"❌ Super user login failed: {resp.status}")
                super_token = None
        
        if super_token:
            headers = {"Authorization": f"Bearer {super_token}"}
            
            print("\n   Testing super user device keys access...")
            async with session.get(f"{frontend_url}/api/device/keys", headers=headers) as resp:
                if resp.status == 200:
                    keys = await resp.json()
                    print(f"   ✅ Super user can see {len(keys)} keys")
                    for key in keys:
                        print(f"      - Key: {key.get('key')[:8]}... | Company: {key.get('company_name')} | Used: {key.get('used')}")
                else:
                    print(f"   ❌ Super user keys access failed: {resp.status}")
        
        print("\n" + "="*50)
        
        # Test 2: Company Admin Access
        print("2. Testing COMPANY ADMIN access...")
        admin_login = {
            "email": "admin@dubaimall-displays.com",
            "password": "HostAdmin123!"
        }
        
        async with session.post(f"{backend_url}/api/auth/login", json=admin_login) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                admin_token = login_result.get("access_token")
                user_info = login_result.get("user", {})
                print(f"✅ Company admin login successful")
                print(f"   User Type: {user_info.get('user_type')}")
                print(f"   Company: {user_info.get('company', {}).get('name', 'N/A')}")
                print(f"   Company ID: {user_info.get('company', {}).get('id', 'N/A')}")
            else:
                print(f"❌ Company admin login failed: {resp.status}")
                admin_token = None
        
        if admin_token:
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            print("\n   Testing company admin device keys access...")
            async with session.get(f"{frontend_url}/api/device/keys", headers=headers) as resp:
                if resp.status == 200:
                    keys = await resp.json()
                    print(f"   ✅ Company admin can see {len(keys)} keys")
                    for key in keys:
                        print(f"      - Key: {key.get('key')[:8]}... | Company: {key.get('company_name')} | Used: {key.get('used')}")
                else:
                    print(f"   ❌ Company admin keys access failed: {resp.status}")
        
        print("\n" + "="*50)
        
        # Test 3: Generate a new key as company admin
        print("3. Testing key generation as company admin...")
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
        
        # Test 4: Verify RBAC - Check keys again after generation
        print("4. Verifying updated keys list...")
        if admin_token:
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            async with session.get(f"{frontend_url}/api/device/keys", headers=headers) as resp:
                if resp.status == 200:
                    keys = await resp.json()
                    print(f"   ✅ Company admin now sees {len(keys)} keys")
                    for key in keys:
                        print(f"      - Key: {key.get('key')[:8]}... | Company: {key.get('company_name')} | Used: {key.get('used')}")

if __name__ == "__main__":
    asyncio.run(test_device_keys_rbac())
