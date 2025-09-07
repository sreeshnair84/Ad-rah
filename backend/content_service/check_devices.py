#!/usr/bin/env python3

import asyncio
import os

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed")

from app.database_service import DatabaseService

async def check_devices():
    """Check devices in the database"""
    # Initialize database service
    db_service = DatabaseService()
    await db_service.initialize()
    
    print('CHECKING DEVICES COLLECTION')
    print('='*50)
    
    # Get devices directly from MongoDB
    devices_cursor = db_service.db.devices.find({})
    devices = await devices_cursor.to_list(length=None)
    
    print(f'📱 Found {len(devices)} devices in MongoDB')

    if devices:
        print('\nDevices in database:')
        for device in devices:
            print(f'  - Device ID: {device.get("device_id", "N/A")}')
            print(f'    Name: {device.get("name", "N/A")}')
            print(f'    Company ID: {device.get("company_id", "N/A")}')
            print(f'    Status: {device.get("status", "N/A")}')
            print(f'    Registration Key ID: {device.get("registration_key_id", "N/A")}')
            print(f'    Created: {device.get("created_at", "N/A")}')
            print('-'*30)
    else:
        print('❌ No devices found in the database.')
        print('\n🔍 This means device registration from Flutter app is not working properly.')
        
        # Let's also check if the registration keys are being used
        keys_cursor = db_service.db.registration_keys.find({})
        keys = await keys_cursor.to_list(length=None)
        
        print(f'\n📋 Found {len(keys)} registration keys:')
        for key in keys:
            print(f'  - Key: {key.get("key", "N/A")[:8]}...')
            print(f'    Used: {key.get("used", "N/A")}')
            print(f'    Company: {key.get("company_id", "N/A")}')
            
    await db_service.close()

if __name__ == "__main__":
    asyncio.run(check_devices())
