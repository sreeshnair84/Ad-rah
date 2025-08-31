import asyncio
import sys
import os
sys.path.append('.')

from app.repo import repo
from app.models import DigitalScreen, ScreenStatus, ScreenOrientation, DeviceCredentials, Company, CompanyCreate
from app.device_auth import device_auth_service
from datetime import datetime, timedelta
import uuid

async def seed_demo_company():
    """Seed a demo host company"""
    company_data = {
        "name": "Demo Host Company",
        "type": "HOST",
        "address": "123 Demo Street, Test City, TC 12345",
        "city": "Test City",
        "country": "Demo Land",
        "phone": "+1-555-DEMO1",
        "email": "demo@host-company.example",
        "website": "https://demo-host.example",
        "organization_code": f"ORG-{uuid.uuid4().hex[:8].upper()}",
        "status": "active"
    }

    company = Company(
        name=company_data["name"],
        type=company_data["type"],
        address=company_data["address"],
        city=company_data["city"],
        country=company_data["country"],
        phone=company_data["phone"],
        email=company_data["email"],
        website=company_data["website"],
        organization_code=company_data["organization_code"],
        status=company_data["status"]
    )
    saved = await repo.save_company(company)
    print(f"✓ Created demo company: {company.name} (ID: {saved['id']})")
    return saved

async def setup_demo_device():
    try:
        # First seed a demo company
        demo_company = await seed_demo_company()

        device_id = '019bd22d-1851-4125-a46a-096400a94e8b'

        # Create device
        device = DigitalScreen(
            id=device_id,
            name="Demo Kiosk Screen",
            description="Demo digital signage screen for testing",
            company_id=demo_company["id"],
            location="Demo Location - Main Lobby",
            resolution_width=1920,
            resolution_height=1080,
            orientation=ScreenOrientation.LANDSCAPE,
            aspect_ratio="16:9",
            registration_key="DEMO-KEY-12345",
            status=ScreenStatus.ACTIVE,
            ip_address="192.168.1.100",
            mac_address="00:11:22:33:44:55",
            last_seen=datetime.utcnow()
        )

        # Save device
        saved_device = await repo.save_digital_screen(device)
        print("Demo device created successfully!")
        print(f"Device ID: {device_id}")
        print(f"Device Name: {device.name}")
        print(f"Company: {demo_company['name']}")

        # Create JWT token manually
        jwt_token = device_auth_service.create_device_jwt(device_id, demo_company["id"])
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
        saved_credentials = await repo.save_device_credentials(credentials)
        print("Device credentials created successfully!")
        print(f"JWT Token: {jwt_token}")
        print(f"Refresh Token: {refresh_token}")

        # Test device lookup
        test_device = await repo.get_digital_screen(device_id)
        if test_device:
            print(f"✓ Device lookup successful: {test_device.get('name')}")
        else:
            print("✗ Device lookup failed")

        # Test credentials lookup
        test_credentials = await repo.get_device_credentials(device_id)
        if test_credentials:
            print("✓ Credentials lookup successful")
        else:
            print("✗ Credentials lookup failed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(setup_demo_device())
