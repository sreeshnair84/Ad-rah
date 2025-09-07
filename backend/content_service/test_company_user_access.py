#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_company_user_access():
    """Test company user access to their organization data"""
    
    print("TESTING COMPANY USER ACCESS TO ORGANIZATION DATA")
    print("=" * 55)
    
    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    
    async with aiohttp.ClientSession() as session:
        
        # Login as company user
        print("1. Logging in as company user...")
        login_data = {
            "email": "admin@dubaimall-displays.com",  # Company admin
            "password": "HostAdmin123!"
        }
        
        async with session.post(f"{backend_url}/api/auth/login", json=login_data) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                token = login_result.get("access_token")
                user_data = login_result.get("user")
                print(f"✅ Login successful as {user_data['email']}")
                print(f"   User Type: {user_data['user_type']}")
                print(f"   Company ID: {user_data.get('company_id', 'None')}")
                
                # Check if company data is already included in login response
                if 'company' in user_data:
                    company = user_data['company']
                    print(f"   Company Name: {company['name']}")
                    print(f"   Organization Code: {company['organization_code']}")
                    print("   📋 Company data included in login response!")
                else:
                    print("   ⚠️  No company data in login response")
            else:
                print(f"❌ Login failed: {resp.status}")
                return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test company access via different endpoints
        print("\n2. Testing company access via frontend proxy...")
        async with session.get(f"{frontend_url}/api/auth/companies", headers=headers) as resp:
            if resp.status == 200:
                companies = await resp.json()
                print(f"✅ Frontend proxy returned {len(companies)} companies")
                for company in companies:
                    print(f"   - {company['name']} (Code: {company['organization_code']})")
            else:
                result_text = await resp.text()
                print(f"❌ Frontend proxy failed: {resp.status} - {result_text}")
        
        print("\n3. Testing company access via auth endpoint...")
        async with session.get(f"{backend_url}/api/auth/companies", headers=headers) as resp:
            if resp.status == 200:
                companies = await resp.json()
                print(f"✅ Auth endpoint returned {len(companies)} companies")
                for company in companies:
                    print(f"   - {company['name']} (Code: {company['organization_code']})")
            else:
                result_text = await resp.text()
                print(f"❌ Auth endpoint failed: {resp.status} - {result_text}")
        
        print("\n4. Testing company access via companies endpoint...")
        async with session.get(f"{backend_url}/api/companies/", headers=headers) as resp:
            if resp.status == 200:
                companies = await resp.json()
                print(f"✅ Companies endpoint returned {len(companies)} companies")
                for company in companies:
                    print(f"   - {company['name']} (Code: {company['organization_code']})")
            else:
                result_text = await resp.text()
                print(f"❌ Companies endpoint failed: {resp.status} - {result_text}")

if __name__ == "__main__":
    asyncio.run(test_company_user_access())
