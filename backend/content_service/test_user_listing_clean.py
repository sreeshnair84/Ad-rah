#!/usr/bin/env python3
"""Test user API restrictions - clean version without Unicode"""

import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_user_listing(persona_name, email, password):
    """Test user listing for different personas"""
    print(f"\n{'='*50}")
    print(f"Testing {persona_name}")
    print('='*50)
    
    # Login
    try:
        login_response = requests.post(
            'http://localhost:8000/api/auth/login',
            json={'email': email, 'password': password},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"[FAIL] Login failed: {login_response.status_code}")
            if login_response.status_code == 401:
                print("       Invalid credentials")
            return False
            
        login_data = login_response.json()
        token = login_data['access_token']
        user = login_data['user']
        
        print(f"[PASS] Login successful")
        print(f"       User Type: {user.get('user_type')}")
        print(f"       Company Role: {user.get('company_role', 'None')}")
        company = user.get('company')
        company_name = company.get('name') if company else 'None'
        print(f"       Company: {company_name}")
        
        # Test user listing
        users_response = requests.get(
            'http://localhost:8000/api/auth/users',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10
        )
        
        print(f"       Users API Status: {users_response.status_code}")
        
        if users_response.status_code == 200:
            users_data = users_response.json()
            print(f"       [PASS] Can access users: {len(users_data)} users returned")
            
            # Show summary of users
            for i, user_item in enumerate(users_data[:3]):  # Show first 3
                company_name = user_item.get('company', {}).get('name', 'No Company') if user_item.get('company') else 'No Company'
                print(f"              {i+1}. {user_item.get('email')} ({user_item.get('user_type')}) - {company_name}")
            
            if len(users_data) > 3:
                print(f"              ... and {len(users_data) - 3} more users")
                
        elif users_response.status_code == 403:
            print(f"       [PASS] Correctly restricted: {users_response.json().get('detail', 'Access denied')}")
        else:
            print(f"       [FAIL] Unexpected error: {users_response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

# Test different personas
personas = [
    ("Super User", "admin@adara.com", "SuperAdmin123!"),
    ("HOST Admin", "admin@dubaimall-displays.com", "HostAdmin123!"),
    ("HOST Reviewer", "reviewer@dubaimall-displays.com", "HostReviewer123!"),
    ("ADVERTISER Admin", "admin@emirates-digital.ae", "AdvAdmin123!"),
]

print("RBAC User API Testing")
print("Testing user listing access controls...")

for persona_name, email, password in personas:
    test_user_listing(persona_name, email, password)

print(f"\n{'='*50}")
print("[INFO] RBAC User API Testing Complete")
print('='*50)