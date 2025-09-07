#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_frontend_companies_endpoint():
    """Test the companies endpoint through the frontend proxy"""
    
    print("TESTING COMPANIES ENDPOINT VIA FRONTEND PROXY")
    print("=" * 50)
    
    # Test via frontend proxy
    frontend_url = "http://localhost:3000"
    backend_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Login via backend to get token
        print("1. Logging in via backend...")
        login_data = {
            "email": "admin@dubaimall-displays.com",
            "password": "HostAdmin123!"
        }
        
        async with session.post(f"{backend_url}/api/auth/login", json=login_data) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                token = login_result.get("access_token")
                print(f"✅ Login successful")
            else:
                print(f"❌ Login failed: {resp.status}")
                return
        
        # Test both endpoints
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\n2. Testing backend /api/companies/ directly...")
        async with session.get(f"{backend_url}/api/companies/", headers=headers) as resp:
            result_text = await resp.text()
            print(f"Backend Status: {resp.status}")
            print(f"Backend Response: {result_text}")
        
        print("\n3. Testing backend /api/auth/companies directly...")
        async with session.get(f"{backend_url}/api/auth/companies", headers=headers) as resp:
            result_text = await resp.text()
            print(f"Auth Backend Status: {resp.status}")
            print(f"Auth Backend Response: {result_text}")
        
        print("\n4. Testing frontend proxy /api/auth/companies...")
        async with session.get(f"{frontend_url}/api/auth/companies", headers=headers) as resp:
            result_text = await resp.text()
            print(f"Frontend Status: {resp.status}")
            print(f"Frontend Response: {result_text}")

if __name__ == "__main__":
    asyncio.run(test_frontend_companies_endpoint())
