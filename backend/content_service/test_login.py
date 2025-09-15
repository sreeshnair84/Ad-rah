#!/usr/bin/env python3

import httpx
import asyncio
import json

async def test_login():
    """Test the login endpoint to get a token"""
    
    # Test credentials (from seed_data.py)
    login_data = {
        "email": "admin@adara.com",
        "password": "SuperAdmin123!"
    }
    
    print("Testing login endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test login
            response = await client.post(
                "http://127.0.0.1:8000/api/auth/login",
                json=login_data
            )
            
            print(f"Login response status: {response.status_code}")
            print(f"Login response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                token_data = response.json()
                print(f"Login successful!")
                print(f"Token data: {json.dumps(token_data, indent=2)}")
                
                # Test /me endpoint with token
                if "access_token" in token_data:
                    token = token_data["access_token"]
                    print(f"\nTesting /me endpoint with token...")
                    
                    me_response = await client.get(
                        "http://127.0.0.1:8000/api/auth/me",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    print(f"Me response status: {me_response.status_code}")
                    if me_response.status_code == 200:
                        user_data = me_response.json()
                        print(f"User profile: {json.dumps(user_data, indent=2)}")
                    else:
                        print(f"Me response error: {me_response.text}")
                        
            else:
                print(f"Login failed: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())