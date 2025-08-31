import asyncio
import sys
import os
sys.path.append('.')

from app.repo import repo
from app.models import DigitalScreen, ScreenStatus, ScreenOrientation
from datetime import datetime

async def create_demo_device():
    try:
        # Get demo company
        companies = await repo.list_companies()
        demo_company = next((c for c in companies if c.get("type") == "HOST"), None)

        if not demo_company:
            print("No demo host company found. Run seed_data.py first.")
            return

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
        saved = await repo.save_digital_screen(device)
        print("Demo device created successfully!")
        print(f"Device ID: {device_id}")
        print(f"Device Name: {device.name}")
        print(f"Company: {demo_company['name']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_demo_device())
