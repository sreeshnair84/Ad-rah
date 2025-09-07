#!/usr/bin/env python3

import asyncio
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from app.repo import repo
from app.rbac_models import *
from app.auth_service import auth_service

async def seed_in_memory_data():
    """Seed the in-memory repository with test data"""
    
    print("SEEDING IN-MEMORY REPOSITORY WITH TEST DATA")
    print("=" * 50)
    
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
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
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
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    # Insert companies into in-memory store
    for company in companies:
        await repo.create_company(company)
    print(f"Created {len(companies)} companies in memory")
    
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
            "_id": f"user_{user_data['email'].split('@')[0]}_{created_users}",
            "email": user_data["email"],
            "hashed_password": hashed_password,
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "user_type": user_data["user_type"],
            "company_id": user_data["company_id"],
            "company_role": user_data["company_role"],
            "is_active": user_data["is_active"],
            "email_verified": user_data["email_verified"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await repo.create_user(user_doc)
        created_users += 1
    
    print(f"Created {created_users} users in memory")
    
    # Create some test company applications
    applications = [
        {
            "_id": "app_1",
            "company_name": "Test Company 1",
            "company_type": CompanyType.HOST.value,
            "email": "test@company1.com",
            "phone": "+971-4-111-1111",
            "address": "Test Address 1",
            "city": "Dubai",
            "country": "UAE",
            "website": "https://company1.com",
            "business_license": "BL123456",
            "status": "pending",
            "submission_date": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        },
        {
            "_id": "app_2",
            "company_name": "Test Company 2",
            "company_type": CompanyType.ADVERTISER.value,
            "email": "test@company2.com",
            "phone": "+971-4-222-2222",
            "address": "Test Address 2",
            "city": "Dubai",
            "country": "UAE",
            "website": "https://company2.com",
            "business_license": "BL789012",
            "status": "pending",
            "submission_date": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
    ]
    
    # Insert company applications
    for app in applications:
        await repo.create_company_application(app)
    print(f"Created {len(applications)} company applications")
    
    # Verify the data
    companies_check = await repo.list_companies()
    users_check = await repo.list_users()
    print(f"\nVerification:")
    print(f"- Companies in store: {len(companies_check)}")
    print(f"- Users in store: {len(users_check)}")
    for company in companies_check:
        print(f"  * {company.get('name')} (ID: {company.get('_id')}, Org: {company.get('organization_code')})")
    
    print("\nIn-memory seed data creation completed successfully!")
    print("The data is now available for the running server to use.")

if __name__ == "__main__":
    asyncio.run(seed_in_memory_data())
