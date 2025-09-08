#!/usr/bin/env python3

import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

from app.database_service import db_service
from app.rbac_models import *
from app.auth_service import auth_service

async def seed_test_data():
    """Seed the database with test data from DEPLOYMENT_SUCCESS.md"""
    
    print("SEEDING DATABASE WITH RBAC TEST DATA")
    print("=" * 50)
    
    # Initialize database
    await db_service.initialize()
    
    # Clear existing data
    await db_service.db.users.delete_many({})
    await db_service.db.companies.delete_many({})
    print("Cleared existing data")
    
    # 1. Create companies
    companies = [
        {
            "_id": "company_host_dubai_mall",
            "name": "Dubai Mall Digital Displays",
            "company_type": CompanyType.HOST.value,
            "organization_code": "ORG-DUBAI001",
            "registration_key": "HOST-DUBAI-001",
            "address": "Dubai Mall, Downtown Dubai",
            "city": "Dubai",
            "country": "UAE",
            "phone": "+971-4-123-4567",
            "email": "info@dubaimall-displays.com",
            "website": "https://dubaimall-displays.com",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "company_advertiser_emirates",
            "name": "Emirates Digital Marketing",
            "company_type": CompanyType.ADVERTISER.value,
            "organization_code": "ORG-EMIRATES001",
            "registration_key": "ADV-EMIRATES-001",
            "address": "Sheikh Zayed Road, Dubai",
            "city": "Dubai",
            "country": "UAE",
            "phone": "+971-4-987-6543",
            "email": "info@emirates-digital.ae",
            "website": "https://emirates-digital.ae",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Insert companies
    for company in companies:
        await db_service.db.companies.insert_one(company)
    print(f"Created {len(companies)} companies")
    
    # 2. Create users
    users_data = [
        # Super User
        {
            "email": "admin@adara.com",
            "password": "SuperAdmin123!",
            "first_name": "Platform",
            "last_name": "Administrator", 
            "user_type": UserType.SUPER_USER.value,
            "company_id": None,
            "company_role": None,
            "is_active": True,
            "email_verified": True
        },
        # HOST Company Users
        {
            "email": "admin@dubaimall-displays.com",
            "password": "HostAdmin123!",
            "first_name": "Dubai Mall",
            "last_name": "Administrator",
            "user_type": UserType.COMPANY_USER.value,
            "company_id": "company_host_dubai_mall",
            "company_role": CompanyRole.ADMIN.value,
            "is_active": True,
            "email_verified": True
        },
        {
            "email": "reviewer@dubaimall-displays.com",
            "password": "HostReviewer123!",
            "first_name": "Dubai Mall", 
            "last_name": "Reviewer",
            "user_type": UserType.COMPANY_USER.value,
            "company_id": "company_host_dubai_mall",
            "company_role": CompanyRole.REVIEWER.value,
            "is_active": True,
            "email_verified": True
        },
        {
            "email": "editor@dubaimall-displays.com",
            "password": "HostEditor123!",
            "first_name": "Dubai Mall",
            "last_name": "Editor",
            "user_type": UserType.COMPANY_USER.value,
            "company_id": "company_host_dubai_mall", 
            "company_role": CompanyRole.EDITOR.value,
            "is_active": True,
            "email_verified": True
        },
        {
            "email": "viewer@dubaimall-displays.com",
            "password": "HostViewer123!",
            "first_name": "Dubai Mall",
            "last_name": "Viewer",
            "user_type": UserType.COMPANY_USER.value,
            "company_id": "company_host_dubai_mall",
            "company_role": CompanyRole.VIEWER.value,
            "is_active": True,
            "email_verified": True
        },
        # ADVERTISER Company Users
        {
            "email": "admin@emirates-digital.ae",
            "password": "AdvAdmin123!",
            "first_name": "Emirates Digital",
            "last_name": "Administrator",
            "user_type": UserType.COMPANY_USER.value,
            "company_id": "company_advertiser_emirates",
            "company_role": CompanyRole.ADMIN.value,
            "is_active": True,
            "email_verified": True
        },
        {
            "email": "reviewer@emirates-digital.ae",
            "password": "AdvReviewer123!",
            "first_name": "Emirates Digital",
            "last_name": "Reviewer",
            "user_type": UserType.COMPANY_USER.value,
            "company_id": "company_advertiser_emirates",
            "company_role": CompanyRole.REVIEWER.value,
            "is_active": True,
            "email_verified": True
        },
        {
            "email": "editor@emirates-digital.ae",
            "password": "AdvEditor123!",
            "first_name": "Emirates Digital",
            "last_name": "Editor",
            "user_type": UserType.COMPANY_USER.value,
            "company_id": "company_advertiser_emirates",
            "company_role": CompanyRole.EDITOR.value,
            "is_active": True,
            "email_verified": True
        },
        {
            "email": "viewer@emirates-digital.ae",
            "password": "AdvViewer123!",
            "first_name": "Emirates Digital",
            "last_name": "Viewer",
            "user_type": UserType.COMPANY_USER.value,
            "company_id": "company_advertiser_emirates",
            "company_role": CompanyRole.VIEWER.value,
            "is_active": True,
            "email_verified": True
        }
    ]
    
    # Create users with hashed passwords
    created_users = 0
    for user_data in users_data:
        # Hash the password
        hashed_password = auth_service.hash_password(user_data.pop("password"))
        
        # Create user document
        user_doc = {
            "email": user_data["email"],
            "hashed_password": hashed_password,
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "user_type": user_data["user_type"],
            "company_id": user_data["company_id"],
            "company_role": user_data["company_role"],
            "is_active": user_data["is_active"],
            "email_verified": user_data["email_verified"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await db_service.db.users.insert_one(user_doc)
        created_users += 1
    
    print(f"Created {created_users} users")
    
    # Close database
    await db_service.close()
    
    print("\nSeed data creation completed successfully!")
    print("You can now test authentication with the users listed in DEPLOYMENT_SUCCESS.md")

if __name__ == "__main__":
    asyncio.run(seed_test_data())