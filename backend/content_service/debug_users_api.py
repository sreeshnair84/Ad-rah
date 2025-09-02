#!/usr/bin/env python3
"""
Debug Users API authentication issue specifically
"""
import asyncio
import os
import sys
import requests
import json

# Set up the path and environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables FIRST
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Environment variables loaded")
except ImportError:
    print("[WARNING] python-dotenv not installed")

async def test_users_api_debug():
    """Debug Users API authentication specifically"""
    print("🔍 Debugging Users API authentication...")
    
    try:
        base_url = "http://localhost:8000"
        
        # 1. Get fresh token
        print("\n1. Getting fresh authentication token...")
        login_data = {
            "email": "admin@openkiosk.com",
            "password": "adminpass"
        }
        
        response = requests.post(
            f"{base_url}/api/auth/login",
            headers={"Content-Type": "application/json"},
            json=login_data
        )
        
        if response.status_code != 200:
            print(f"   ✗ Login failed: {response.text}")
            return
            
        login_response = response.json()
        access_token = login_response.get("access_token")
        print(f"   ✓ Token obtained: {access_token[:20]}...")
        
        # 2. Test different API endpoints
        headers = {"Authorization": f"Bearer {access_token}"}
        
        endpoints_to_test = [
            ("/api/users", "Users API"),
            ("/api/roles", "Roles API"),
            ("/api/companies", "Companies API"),
            ("/api/auth/check-permission", "Check Permission API")
        ]
        
        print(f"\n2. Testing different API endpoints...")
        for endpoint, name in endpoints_to_test:
            try:
                if endpoint == "/api/auth/check-permission":
                    # POST endpoint requires data
                    response = requests.post(
                        f"{base_url}{endpoint}",
                        headers={**headers, "Content-Type": "application/json"},
                        json={"page": "users", "permission": "view"}
                    )
                else:
                    # GET endpoint
                    response = requests.get(f"{base_url}{endpoint}", headers=headers)
                
                print(f"   - {name}: {response.status_code}")
                if response.status_code != 200:
                    print(f"     Error: {response.text[:100]}...")
                else:
                    result = response.json()
                    if isinstance(result, list):
                        print(f"     Success: {len(result)} items returned")
                    elif isinstance(result, dict):
                        print(f"     Success: {type(result).__name__} returned")
                    else:
                        print(f"     Success: {type(result).__name__} returned")
                        
            except Exception as e:
                print(f"   - {name}: Error - {e}")
                
        # 3. Test with manual curl-equivalent
        print(f"\n3. Testing with manual request construction...")
        try:
            import urllib.request
            import urllib.parse
            
            req = urllib.request.Request(f"{base_url}/api/users")
            req.add_header('Authorization', f'Bearer {access_token}')
            
            with urllib.request.urlopen(req) as response:
                content = response.read().decode()
                print(f"   - Manual request status: {response.status}")
                print(f"   - Response: {content[:100]}...")
                
        except Exception as e:
            print(f"   - Manual request failed: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_users_api_debug())
