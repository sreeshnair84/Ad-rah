import asyncio
import sys
import os
sys.path.append('.')

from app.repo import repo
from app.device_auth import device_auth_service
from app.models import DeviceCredentials
from datetime import datetime, timedelta

async def create_device_credentials():
    try:
        device_id = '019bd22d-1851-4125-a46a-096400a94e8b'

        # Check if device exists
        device = await repo.get_digital_screen(device_id)
        if not device:
            print(f"Device {device_id} not found in database")
            return

        print(f"Found device: {device.get('name')}")

        # Create JWT token manually
        jwt_token = device_auth_service.create_device_jwt(device_id, device.get('company_id', 'demo-company'))
        refresh_token = device_auth_service.generate_refresh_token()

        # Create DeviceCredentials object
        credentials = DeviceCredentials(
            device_id=device_id,
            jwt_token=jwt_token,
            jwt_expires_at=datetime.utcnow() + timedelta(hours=24),
            refresh_token=refresh_token,
            revoked=False
        )

        # Save credentials
        saved = await repo.save_device_credentials(credentials)
        print("Credentials created successfully!")
        print(f"JWT Token: {jwt_token}")
        print(f"Refresh Token: {refresh_token}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_device_credentials())
