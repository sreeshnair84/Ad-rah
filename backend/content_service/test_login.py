"""
Test login functionality and token validation
"""

import requests
import json

def test_login():
    """Test the login endpoint"""
    
    # Test credentials for editor user
    login_data = {
        "email": "editor@dubaimall-displays.com",
        "password": "HostEditor123!"
    }
    
    print("🔐 Testing Login API")
    print(f"Backend URL: http://localhost:8000")
    print(f"Credentials: {login_data['email']}")
    print()
    
    try:
        # Test login
        login_response = requests.post(
            "http://localhost:8000/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📡 Login Response Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print("✅ Login successful!")
            print(f"   Access Token: {login_result.get('access_token', 'None')[:50]}...")
            print(f"   User ID: {login_result.get('user', {}).get('id', 'None')}")
            print(f"   User Email: {login_result.get('user', {}).get('email', 'None')}")
            print(f"   User Role: {login_result.get('user', {}).get('company_role', 'None')}")
            print()
            
            # Test content API with token
            token = login_result.get('access_token')
            if token:
                print("📋 Testing Content API with token...")
                content_response = requests.get(
                    "http://localhost:8000/api/content/",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                print(f"📡 Content API Response Status: {content_response.status_code}")
                
                if content_response.status_code == 200:
                    content_result = content_response.json()
                    print("✅ Content API access successful!")
                    print(f"   Content items found: {len(content_result) if isinstance(content_result, list) else 'Unknown'}")
                else:
                    print("❌ Content API access failed!")
                    try:
                        error_data = content_response.json()
                        print(f"   Error: {error_data}")
                    except:
                        print(f"   Raw response: {content_response.text}")
                        
                # Test /me endpoint
                print("\n👤 Testing /me endpoint...")
                me_response = requests.get(
                    "http://localhost:8000/api/auth/me",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                print(f"📡 /me Response Status: {me_response.status_code}")
                
                if me_response.status_code == 200:
                    me_result = me_response.json()
                    print("✅ /me endpoint successful!")
                    print(f"   User: {me_result.get('email', 'None')}")
                    print(f"   Permissions: {len(me_result.get('permissions', []))}")
                else:
                    print("❌ /me endpoint failed!")
                    try:
                        error_data = me_response.json()
                        print(f"   Error: {error_data}")
                    except:
                        print(f"   Raw response: {me_response.text}")
            
        else:
            print("❌ Login failed!")
            try:
                error_data = login_response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {login_response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - is the backend server running?")
        print("   Make sure the server is running at: http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_login()
