#!/usr/bin/env python3

import asyncio
import aiohttp
import json
from dotenv import load_dotenv
load_dotenv()

async def test_endpoints():
    """Test the API endpoints to ensure they're working properly"""
    
    print("TESTING API ENDPOINTS")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Login as super user
        print("\n1. Testing Super User Login...")
        login_data = {
            "email": "admin@adara.com",
            "password": "SuperAdmin123!"
        }
        
        async with session.post(f"{base_url}/api/auth/login", json=login_data) as resp:
            if resp.status == 200:
                login_result = await resp.json()
                super_token = login_result.get("access_token")
                print(f"✅ Super user login successful")
            else:
                print(f"❌ Super user login failed: {resp.status}")
                return
        
        # Test 2: Get companies as super user (should see all)
        print("\n2. Testing Companies List as Super User...")
        headers = {"Authorization": f"Bearer {super_token}"}
        
        async with session.get(f"{base_url}/api/auth/companies", headers=headers) as resp:
            if resp.status == 200:
                companies = await resp.json()
                print(f"✅ Super user sees {len(companies)} companies:")
                for company in companies:
                    print(f"   - {company.get('name')} (Org: {company.get('organization_code')})")
            else:
                print(f"❌ Companies list failed: {resp.status}")
        
        # Test 3: Login as company user
        print("\n3. Testing Company User Login...")
        company_login_data = {
            "email": "admin@dubaimall-displays.com",
            "password": "HostAdmin123!"
        }
        
        async with session.post(f"{base_url}/api/auth/login", json=company_login_data) as resp:
            if resp.status == 200:
                company_login_result = await resp.json()
                company_token = company_login_result.get("access_token")
                print(f"✅ Company user login successful")
            else:
                print(f"❌ Company user login failed: {resp.status}")
                return
        
        # Test 4: Get companies as company user (should see only their company)
        print("\n4. Testing Companies List as Company User...")
        company_headers = {"Authorization": f"Bearer {company_token}"}
        
        async with session.get(f"{base_url}/api/auth/companies", headers=company_headers) as resp:
            if resp.status == 200:
                user_companies = await resp.json()
                print(f"✅ Company user sees {len(user_companies)} companies:")
                for company in user_companies:
                    print(f"   - {company.get('name')} (Org: {company.get('organization_code')})")
            else:
                print(f"❌ Company user companies list failed: {resp.status}")
        
        # Test 5: Get company applications as super user
        print("\n5. Testing Company Applications List...")
        
        async with session.get(f"{base_url}/api/company-applications/", headers=headers) as resp:
            if resp.status == 200:
                applications = await resp.json()
                print(f"✅ Found {len(applications)} company applications:")
                for app in applications:
                    print(f"   - {app.get('company_name')} (Status: {app.get('status')}, ID: {app.get('_id')})")
            else:
                print(f"❌ Company applications list failed: {resp.status}")
        
        # Test 6: Test specific application review endpoint
        print("\n6. Testing Application Review Endpoint...")
        
        review_data = {
            "decision": "approved",
            "notes": "Application looks good, approved for testing"
        }
        
        async with session.put(f"{base_url}/api/company-applications/app_001/review", 
                             json=review_data, headers=headers) as resp:
            if resp.status == 200:
                review_result = await resp.json()
                print(f"✅ Application review successful: {review_result.get('message')}")
            else:
                error_text = await resp.text()
                print(f"❌ Application review failed: {resp.status} - {error_text}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
