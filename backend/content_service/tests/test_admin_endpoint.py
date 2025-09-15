#!/usr/bin/env python3
"""
Test the admin/pending endpoint
"""
import asyncio
import httpx
import json

async def test_admin_endpoint():
    """Test admin endpoints"""
    
    print("Testing Admin Endpoint")
    print("=" * 30)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Authenticate first
        print("1. Authenticating...")
        try:
            login_response = await client.post(
                "http://localhost:8000/api/auth/login",
                json={"email": "admin@adara.com", "password": "SuperAdmin123!"}
            )
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                print("   [OK] Authentication successful")
            else:
                print(f"   [FAIL] Authentication failed: {login_response.status_code}")
                return
        except Exception as e:
            print(f"   [FAIL] Authentication error: {e}")
            return
        
        # Test admin pending endpoint
        print("\n2. Testing admin/pending endpoint...")
        try:
            response = await client.get(
                "http://localhost:8000/api/content/admin/pending",
                headers=headers
            )
            
            print(f"   Admin pending status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)}")
                print("   [OK] Admin pending endpoint working")
            else:
                print(f"   [INFO] Response: {response.text}")
                if response.status_code == 404:
                    print("   [FAIL] Endpoint not found - route may not be registered")
                else:
                    print(f"   [INFO] Status {response.status_code}")
                
        except Exception as e:
            print(f"   [FAIL] Admin endpoint error: {e}")
    
    print("\n" + "=" * 30)
    print("Admin Endpoint Test Completed")

if __name__ == "__main__":
    asyncio.run(test_admin_endpoint())