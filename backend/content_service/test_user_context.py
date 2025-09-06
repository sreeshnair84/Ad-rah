"""
Test user company context and permissions
"""

import requests
import json

def test_user_context():
    """Test user company context"""
    
    # Login
    login_data = {
        "email": "editor@dubaimall-displays.com",
        "password": "HostEditor123!"
    }
    
    print("🔐 Login and check user context")
    login_response = requests.post(
        "http://localhost:8000/api/auth/login",
        json=login_data,
        timeout=10
    )
    
    if login_response.status_code != 200:
        print("❌ Login failed!")
        return
    
    token = login_response.json().get('access_token')
    user_data = login_response.json().get('user', {})
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("✅ Login successful")
    print(f"   User ID: {user_data.get('id')}")
    print(f"   Company ID: {user_data.get('company_id')}")
    print(f"   Role: {user_data.get('company_role')}")
    print()
    
    # Check /me endpoint for more details
    print("👤 Getting user profile")
    me_response = requests.get(
        "http://localhost:8000/api/auth/me",
        headers=headers,
        timeout=10
    )
    
    if me_response.status_code == 200:
        me_data = me_response.json()
        print("✅ User profile retrieved:")
        print(f"   Email: {me_data.get('email')}")
        print(f"   User ID: {me_data.get('id')}")
        print(f"   Company ID: {me_data.get('company_id')}")
        print(f"   Role: {me_data.get('company_role')}")
        print(f"   User Type: {me_data.get('user_type')}")
        print(f"   Company: {me_data.get('company')}")
        print(f"   Permissions: {me_data.get('permissions', [])}")
        print()
        
        # Try uploading with the correct user ID
        user_id = me_data.get('id')
        company_id = me_data.get('company_id')
        
        print(f"📤 Testing upload with user_id={user_id}, company_id={company_id}")
        
        # Create test file
        test_file_content = b"Test image content"
        files = {
            'file': ('test.jpg', test_file_content, 'image/jpeg')
        }
        data = {
            'owner_id': user_id
        }
        
        upload_headers = {"Authorization": f"Bearer {token}"}
        
        upload_response = requests.post(
            "http://localhost:8000/api/content/upload-file",
            headers=upload_headers,
            files=files,
            data=data,
            timeout=15
        )
        
        print(f"📡 Upload Response: {upload_response.status_code}")
        if upload_response.status_code != 200:
            try:
                error_data = upload_response.json()
                print(f"❌ Upload Error: {error_data}")
            except:
                print(f"❌ Upload Error (raw): {upload_response.text}")
        else:
            upload_result = upload_response.json()
            print(f"✅ Upload successful: {upload_result}")
    
    else:
        print(f"❌ Failed to get user profile: {me_response.text}")

if __name__ == "__main__":
    test_user_context()
