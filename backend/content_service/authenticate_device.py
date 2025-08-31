import asyncio
import sys
import os
sys.path.append('.')

from app.device_auth import device_auth_service

async def authenticate_device():
    try:
        result = await device_auth_service.authenticate_device('019bd22d-1851-4125-a46a-096400a94e8b', 'Demo Company')
        print('Authentication successful!')
        print(f'JWT Token: {result["jwt_token"]}')
        print(f'Refresh Token: {result["refresh_token"]}')
        print(f'Expires in: {result["expires_in"]} seconds')
    except Exception as e:
        print(f'Authentication failed: {e}')

if __name__ == "__main__":
    asyncio.run(authenticate_device())
