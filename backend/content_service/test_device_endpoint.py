#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_device_generate_key():
    """Test the device generate-key endpoint"""
    
    print("TESTING DEVICE GENERATE-KEY ENDPOINT")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Login to get token
        print("1. Logging in...")
        login_data = {
            "email": "admin@dubaimall-displays.com",
            "password": "HostAdmin123!"
        }
        
        async with session.post(f"{backend_url}/api/auth/login", json=login_data) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                token = login_result.get("access_token")
                print(f"✅ Login successful")
                print(f"User company: {login_result.get('user', {}).get('company', {})}")
            else:
                print(f"❌ Login failed: {resp.status}")
                return
        
        # Test device key generation
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\n2. Testing device key generation...")
        device_key_data = {
            "company_id": "company_host_dubai_mall"
        }
        
        async with session.post(f"{backend_url}/api/device/generate-key", json=device_key_data, headers=headers) as resp:
            result_text = await resp.text()
            print(f"Status: {resp.status}")
            print(f"Response: {result_text}")
        
        # Test with list companies to see what IDs are available
        print("\n3. Checking available companies...")
        async with session.get(f"{backend_url}/api/companies/", headers=headers) as resp:
            if resp.status == 200:
                companies = await resp.json()
                print(f"Available companies:")
                for company in companies:
                    print(f"  - ID: {company.get('id')}, Name: {company.get('name')}")
            else:
                print(f"Failed to get companies: {resp.status}")

if __name__ == "__main__":
    asyncio.run(test_device_generate_key())
