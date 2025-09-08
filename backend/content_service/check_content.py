#!/usr/bin/env python3
import requests
import json

# Login and get content details
login_data = {'email': 'admin@adara.com', 'password': 'SuperAdmin123!'}
login_response = requests.post('http://localhost:8000/api/auth/login', json=login_data)

if login_response.status_code == 200:
    token = login_response.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    content_response = requests.get('http://localhost:8000/api/content/', headers=headers)

    if content_response.status_code == 200:
        content_data = content_response.json()
        print('📋 CONTENT ITEMS FOUND:')
        print('=' * 50)
        for i, item in enumerate(content_data, 1):
            print(f'{i}. ID: {item.get("id", "N/A")}')
            print(f'   Filename: {item.get("filename", "N/A")}')
            print(f'   Status: {item.get("status", "N/A")}')
            print(f'   Owner: {item.get("owner_id", "N/A")}')
            print(f'   Size: {item.get("size", 0)} bytes')
            print()

        print(f'✅ Total: {len(content_data)} content items available')
        print('🔗 API Endpoint: http://localhost:8000/api/content/')
        print('🔐 Authentication: Required (JWT Bearer token)')
    else:
        print(f'❌ Failed to get content: {content_response.status_code} - {content_response.text}')
else:
    print(f'❌ Login failed: {login_response.status_code} - {login_response.text}')
