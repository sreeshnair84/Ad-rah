#!/usr/bin/env python3
"""Test script to verify editor login works via API"""
import requests
import json

def test_editor_login_api():
    """Test editor login via API endpoint"""
    print("Testing Editor Login via API")
    print("=" * 50)
    
    # Test editor login
    login_data = {
        "email": "editor@dubaimall-displays.com",
        "password": "HostEditor123!"
    }
    
    base_url = "http://127.0.0.1:8000"
    
    print(f"Attempting login for: {login_data['email']}")
    print(f"API URL: {base_url}/api/auth/login")
    
    try:
        # Test authentication via API
        response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Authentication successful!")
            print(f"   Response keys: {list(data.keys())}")
            
            # Check if we got a token
            if 'access_token' in data:
                print(f"   ✅ Access token received")
                token = data['access_token']
                
                # Test getting user profile with the token
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                profile_response = requests.get(
                    f"{base_url}/api/auth/me",
                    headers=headers
                )
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    print(f"✅ Profile retrieved successfully!")
                    print(f"   Name: {profile_data.get('name', 'Unknown')}")
                    print(f"   Email: {profile_data.get('email', 'Unknown')}")
                    print(f"   Role: {profile_data.get('role', 'Unknown')}")
                    
                    # Check permissions
                    permissions = profile_data.get('permissions', [])
                    print(f"   Permissions: {permissions}")
                    
                    required_permissions = ['content_distribute', 'overlay_create', 'digital_twin_view']
                    
                    print(f"\n   Required permissions check:")
                    all_permissions_present = True
                    for req_perm in required_permissions:
                        if req_perm in permissions:
                            print(f"     ✅ {req_perm}")
                        else:
                            print(f"     ❌ {req_perm}")
                            all_permissions_present = False
                    
                    if all_permissions_present:
                        print(f"\n🎉 All required permissions are present!")
                        return True
                    else:
                        print(f"\n❌ Some required permissions are missing!")
                        return False
                else:
                    print(f"❌ Profile request failed: {profile_response.status_code}")
                    print(f"   Response: {profile_response.text}")
                    return False
            else:
                print(f"❌ No access token in response")
                print(f"   Response: {data}")
                return False
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Is it running on http://127.0.0.1:8000?")
        return False
    except Exception as e:
        print(f"❌ Error during API test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_editor_login_api()
    if success:
        print("\n🎉 Editor login API test PASSED!")
        print("✅ The editor user can successfully:")
        print("   - Authenticate with correct credentials")
        print("   - Receive access token")
        print("   - Access profile with RBAC permissions")
        print("   - Has all required permissions for sidebar menu")
    else:
        print("\n💥 Editor login API test FAILED!")
    
    exit(0 if success else 1)
