#!/usr/bin/env python3
"""Manual seed data for testing"""
import requests
import json

def test_auth_endpoints():
    """Test auth endpoints"""
    base_url = "http://127.0.0.1:8000/api"
    
    # Try to register a user through direct API
    user_data = {
        "email": "admin@adara.com",
        "password": "admin",
        "first_name": "Admin",
        "last_name": "User",
        "user_type": "SUPER_USER"
    }
    
    try:
        # First try the registration endpoint (if available without auth)
        print("Testing registration endpoint...")
        response = requests.get(f"{base_url}/auth", timeout=5)
        if response.status_code == 200:
            print("Auth endpoints available")
        else:
            print(f"Auth endpoints returned: {response.status_code}")
            
        # Try login with some test credentials
        print("Testing login with basic credentials...")
        login_data = {"email": "test@test.com", "password": "test"}
        response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=5)
        print(f"Login response: {response.status_code} - {response.text}")
        
        # Try admin login
        print("Testing admin login...")
        admin_data = {"email": "admin@adara.com", "password": "admin"}
        response = requests.post(f"{base_url}/auth/login", json=admin_data, timeout=5)
        print(f"Admin login response: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_auth_endpoints()