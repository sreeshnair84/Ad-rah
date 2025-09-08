#!/usr/bin/env python3

import asyncio
from app.database_service import db_service

async def check_db():
    await db_service.initialize()
    
    # Check companies
    companies = await db_service.db.companies.find({}).to_list(length=None)
    print('Companies in database:')
    for company in companies:
        print(f'  - Name: {company.get("name", "Unknown")}')
        print(f'    Org code: {company.get("organization_code", "None")}')
        print(f'    ID: {company.get("_id", "None")}')
        print()
    
    # Check device registration keys
    try:
        device_keys = await db_service.db.device_registration_keys.find({}).to_list(length=None)
        print('Device registration keys:')
        for key in device_keys:
            print(f'  - Key: {key.get("key", "Unknown")}')
            print(f'    Company ID: {key.get("company_id", "None")}')
            print(f'    Used: {key.get("used", False)}')
            print()
    except Exception as e:
        print(f'Error checking device keys: {e}')
    
    await db_service.close()

if __name__ == "__main__":
    asyncio.run(check_db())
