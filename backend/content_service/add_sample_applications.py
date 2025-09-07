#!/usr/bin/env python3

import asyncio
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from app.database_service import db_service
from app.rbac_models import *

async def add_sample_applications():
    """Add sample company applications for testing"""
    
    print("ADDING SAMPLE COMPANY APPLICATIONS")
    print("=" * 50)
    
    # Initialize database
    await db_service.initialize()
    
    # Create sample company applications
    applications = [
        {
            "_id": "app_001",
            "company_name": "Digital Screens LLC",
            "company_type": CompanyType.HOST.value,
            "organization_code": "ORG-DIGITAL001",
            "contact_email": "admin@digitalscreens.ae",
            "contact_phone": "+971-4-555-0001",
            "address": "Business Bay, Dubai",
            "city": "Dubai",
            "country": "UAE",
            "website": "https://digitalscreens.ae",
            "business_license": "BL789456",
            "status": "pending",
            "submission_date": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "_id": "app_002", 
            "company_name": "Metro Advertising Hub",
            "company_type": CompanyType.ADVERTISER.value,
            "organization_code": "ORG-METRO001",
            "contact_email": "contact@metroadhub.com",
            "contact_phone": "+971-4-555-0002",
            "address": "DIFC, Dubai",
            "city": "Dubai", 
            "country": "UAE",
            "website": "https://metroadhub.com",
            "business_license": "BL123789",
            "status": "pending",
            "submission_date": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    # Insert applications
    for app in applications:
        await db_service.db.company_applications.insert_one(app)
    print(f"Created {len(applications)} company applications")
    
    # Verify
    apps_check = await db_service.db.company_applications.count_documents({})
    print(f"Total applications in database: {apps_check}")
    
    # Close database
    await db_service.close()
    
    print("\nSample applications added successfully!")

if __name__ == "__main__":
    asyncio.run(add_sample_applications())
