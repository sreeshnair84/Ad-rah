import requests
import json

# Try to login with host credentials again
login_data = {
    'username': 'host@techcorpsolutions.com',
    'password': 'hostpass'
}

try:
    response = requests.post('http://localhost:8000/api/auth/token', data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data['access_token']
        print(f'Login successful, token: {token[:50]}...')

        # Get user info with roles
        headers = {'Authorization': f'Bearer {token}'}
        user_response = requests.get('http://localhost:8000/api/auth/me/with-roles', headers=headers)

        if user_response.status_code == 200:
            user_data = user_response.json()
            print('User data after init:')
            user = user_data['user']
            print(f'Email: {user["email"]}')
            print(f'Roles count: {len(user["roles"])}')
            for role in user['roles']:
                print(f'  Role: {role.get("role")}, Name: {role.get("role_name")}, ID: {role.get("role_id")}')
        else:
            print(f'Failed to get user data: {user_response.status_code}')
            print(user_response.text)
    else:
        print(f'Login failed: {response.status_code}')
        print(response.text)
except Exception as e:
    print(f'Error: {e}')
