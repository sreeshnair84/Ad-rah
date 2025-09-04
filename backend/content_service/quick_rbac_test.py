#!/usr/bin/env python3
"""Quick RBAC Verification Test"""

import requests
import json

def test_persona(name, email, password):
    try:
        response = requests.post(
            'http://localhost:3000/api/auth/login',
            json={'email': email, 'password': password},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            user = data['user']
            print(f"[OK] {name}")
            print(f"  User Type: {user.get('user_type')}")
            print(f"  Company Role: {user.get('company_role', 'None')}")
            print(f"  Permissions: {len(user.get('permissions', []))}")
            print(f"  Navigation: {user.get('accessible_navigation', [])}")
            return True
        else:
            print(f"[FAIL] {name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return False

# Test key personas
personas = [
    ("Super User", "admin@adara.com", "SuperAdmin123!"),
    ("HOST Admin", "admin@dubaimall-displays.com", "HostAdmin123!"),  
    ("HOST Reviewer", "reviewer@dubaimall-displays.com", "HostReviewer123!"),
    ("ADVERTISER Admin", "admin@emirates-digital.ae", "AdvAdmin123!")
]

print("RBAC Quick Verification Test")
print("=" * 40)

for name, email, password in personas:
    test_persona(name, email, password)
    print()