#!/usr/bin/env python3

import asyncio
from app.models import Company, DeviceRegistrationKey
from app.repo import repo
from app.database_service import db_service
from datetime import datetime, timedelta
import uuid

async def create_dubai_company_and_key():
    """Create the Dubai company and registration key that Flutter expects"""
    
    # Initialize the repository
    await db_service.initialize()
    
    # Create Dubai Mall company
    company = Company(
        id=str(uuid.uuid4()),
        name='Dubai Mall Digital Displays',
        type='HOST',
        address='Dubai Mall, Downtown Dubai',
        city='Dubai',
        country='UAE',
        organization_code='ORG-DUBAI001',  # This is what Flutter expects
        status='active'
    )
    
    saved_company = await repo.save_company(company)
    print(f"✅ Created company: {saved_company}")
    
    # Create the registration key that Flutter is using
    key = DeviceRegistrationKey(
        id=str(uuid.uuid4()),
        key='nZ2CB2bX472WhaOq',  # This is what Flutter is using
        company_id=saved_company['id'],
        created_by='system',
        expires_at=datetime.utcnow() + timedelta(days=30),  # Valid for 30 days
        used=False,
        used_by_device=None
    )
    
    await repo.save_device_registration_key(key)
    print(f"✅ Created registration key: {key.key} for company: {saved_company['id']}")
    
    await db_service.close()
    print("✅ Setup complete! Flutter app should now be able to register devices.")

if __name__ == "__main__":
    asyncio.run(create_dubai_company_and_key())
