#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def debug_company_user():
    """Debug why company user isn't seeing their company"""
    
    print("DEBUGGING COMPANY USER ACCESS")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Login as company user
        print("1. Logging in as company user...")
        login_data = {
            "email": "admin@dubaimall-displays.com",
            "password": "HostAdmin123!"
        }
        
        async with session.post(f"{base_url}/api/auth/login", json=login_data) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                token = login_result.get("access_token")
                print(f"✅ Login successful")
                
                # Print user info from token
                user_info = login_result.get("user", {})
                print(f"User info: {user_info}")
                print(f"Company ID from login: {user_info.get('company_id')}")
            else:
                print(f"❌ Login failed: {resp.status}")
                return
        
        # Get companies with detailed headers
        print("\n2. Getting companies...")
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.get(f"{base_url}/api/auth/companies", headers=headers) as resp:
            result_text = await resp.text()
            print(f"Status: {resp.status}")
            print(f"Response: {result_text}")
            
            if resp.status == 200:
                companies = json.loads(result_text)
                print(f"Companies returned: {len(companies)}")
                for company in companies:
                    print(f"  - {company}")
            else:
                print(f"Error response: {result_text}")

if __name__ == "__main__":
    asyncio.run(debug_company_user())
