#!/usr/bin/env python3
"""Direct test of user listing API with debugging"""

import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_direct_api():
    """Test the user listing API directly"""
    
    # First, login as super user
    print("=== LOGIN TEST ===")
    login_response = requests.post(
        'http://localhost:8000/api/auth/login',
        json={'email': 'admin@adara.com', 'password': 'SuperAdmin123!'},
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    login_data = login_response.json()
    token = login_data['access_token']
    user = login_data['user']
    
    print(f"Login successful for {user.get('email')}")
    print(f"User Type: {user.get('user_type')}")
    print(f"User ID: {user.get('id')}")
    print(f"Company ID: {user.get('company_id')}")
    
    # Test user listing endpoint
    print(f"\n=== USER LISTING TEST ===")
    users_response = requests.get(
        'http://localhost:8000/api/auth/users',
        headers={'Authorization': f'Bearer {token}'},
        timeout=10
    )
    
    print(f"Status Code: {users_response.status_code}")
    print(f"Response Headers: {dict(users_response.headers)}")
    
    if users_response.status_code == 200:
        users_data = users_response.json()
        print(f"Number of users returned: {len(users_data)}")
        if users_data:
            print("First few users:")
            for user in users_data[:3]:
                print(f"  - {user}")
        else:
            print("Empty user list returned")
    else:
        print(f"Error response: {users_response.text}")

if __name__ == "__main__":
    test_direct_api()