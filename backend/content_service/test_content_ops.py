"""
Test content creation as editor user
"""

import requests
import json
import io

def test_content_operations():
    """Test content operations for editor user"""
    
    # Step 1: Login
    login_data = {
        "email": "editor@dubaimall-displays.com",
        "password": "HostEditor123!"
    }
    
    print("🔐 Step 1: Login as editor")
    login_response = requests.post(
        "http://localhost:8000/api/auth/login",
        json=login_data,
        timeout=10
    )
    
    if login_response.status_code != 200:
        print("❌ Login failed!")
        return
    
    token = login_response.json().get('access_token')
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("✅ Login successful")
    
    # Step 2: List existing content
    print("\n📋 Step 2: List existing content")
    content_response = requests.get(
        "http://localhost:8000/api/content/",
        headers=headers,
        timeout=10
    )
    
    print(f"📡 List Content Status: {content_response.status_code}")
    if content_response.status_code == 200:
        content_list = content_response.json()
        print(f"✅ Found {len(content_list)} content items")
        for item in content_list[:3]:  # Show first 3 items
            print(f"   - {item.get('filename', 'Unknown')} ({item.get('status', 'Unknown')})")
    else:
        print(f"❌ Failed to list content: {content_response.text}")
    
    # Step 3: Test content upload (simulation)
    print("\n📤 Step 3: Test content upload endpoint")
    
    # Get current user ID for upload
    user_data = login_response.json().get('user', {})
    user_id = user_data.get('id')
    
    if not user_id:
        print("❌ Could not get user ID from login")
        return
    
    # Create a simple test file in memory
    test_file_content = b"Test image content for upload"
    files = {
        'file': ('test_image.jpg', io.BytesIO(test_file_content), 'image/jpeg')
    }
    
    data = {
        'owner_id': user_id
    }
    
    upload_headers = {
        "Authorization": f"Bearer {token}"
        # Don't set Content-Type for multipart/form-data
    }
    
    upload_response = requests.post(
        "http://localhost:8000/api/content/upload-file",
        headers=upload_headers,
        files=files,
        data=data,
        timeout=15
    )
    
    print(f"📡 Upload Status: {upload_response.status_code}")
    if upload_response.status_code == 200:
        upload_result = upload_response.json()
        print(f"✅ Upload successful!")
        print(f"   Content ID: {upload_result.get('content_id', 'Unknown')}")
        print(f"   Status: {upload_result.get('status', 'Unknown')}")
        
        # Step 4: Check updated content list
        print("\n📋 Step 4: Check updated content list")
        updated_response = requests.get(
            "http://localhost:8000/api/content/",
            headers=headers,
            timeout=10
        )
        
        if updated_response.status_code == 200:
            updated_list = updated_response.json()
            print(f"✅ Now found {len(updated_list)} content items")
        
    else:
        print(f"❌ Upload failed: {upload_response.text}")
    
    # Step 5: Test user permissions
    print("\n👤 Step 5: Check user permissions")
    me_response = requests.get(
        "http://localhost:8000/api/auth/me",
        headers=headers,
        timeout=10
    )
    
    if me_response.status_code == 200:
        user_data = me_response.json()
        print("✅ User info retrieved:")
        print(f"   Email: {user_data.get('email')}")
        print(f"   Role: {user_data.get('company_role')}")
        print(f"   Permissions: {len(user_data.get('permissions', []))}")
        for perm in user_data.get('permissions', [])[:5]:
            print(f"     - {perm}")
        if len(user_data.get('permissions', [])) > 5:
            print(f"     ... and {len(user_data.get('permissions', [])) - 5} more")

if __name__ == "__main__":
    test_content_operations()
