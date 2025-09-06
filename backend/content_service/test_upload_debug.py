"""
Debug upload with exact user ID matching
"""

import requests
import json

def debug_upload():
    """Debug upload with exact user ID matching"""
    
    # Login
    login_data = {
        "email": "editor@dubaimall-displays.com",
        "password": "HostEditor123!"
    }
    
    print("🔐 Login")
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
    user_id_from_login = user_data.get('id')
    
    print(f"✅ Login successful, user_id from login: {user_id_from_login}")
    
    # Get user from /me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_response = requests.get("http://localhost:8000/api/auth/me", headers=headers)
    
    if me_response.status_code == 200:
        me_data = me_response.json()
        user_id_from_me = me_data.get('id')
        print(f"✅ User ID from /me: {user_id_from_me}")
        
        # Check if they match
        ids_match = user_id_from_login == user_id_from_me
        print(f"📋 User IDs match: {ids_match}")
        
        # Use the user ID from /me endpoint for upload
        print(f"\n📤 Testing upload with user_id = {user_id_from_me}")
        
        # Test upload
        files = {'file': ('test.jpg', b'test content', 'image/jpeg')}
        data = {'owner_id': user_id_from_me}
        
        upload_response = requests.post(
            "http://localhost:8000/api/content/upload-file",
            headers=headers,
            files=files,
            data=data,
            timeout=15
        )
        
        print(f"📡 Upload Response: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            print("✅ Upload successful!")
            result = upload_response.json()
            print(f"   Content ID: {result.get('content_id')}")
            print(f"   Status: {result.get('status')}")
        else:
            try:
                error = upload_response.json()
                print(f"❌ Upload Error: {error}")
            except:
                print(f"❌ Upload Error (raw): {upload_response.text}")
                
            # Let's also try to see what the current_user looks like
            print(f"\n🔍 Debug: current_user might be different format")
            print(f"   user_id_from_login: {user_id_from_login} (type: {type(user_id_from_login)})")
            print(f"   user_id_from_me: {user_id_from_me} (type: {type(user_id_from_me)})")

if __name__ == "__main__":
    debug_upload()
