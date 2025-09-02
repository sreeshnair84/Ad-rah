#!/usr/bin/env python3
"""
Data Seeding Script for OpenKiosk
================================

This script populates the database with initial data for development and testing.
Run this script to seed the database with sample companies, users, roles, and content.

Usage:
    python seed_data.py

Environment Variables:
    MONGO_URI - MongoDB connection string (optional, uses in-memory store if not set)
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid
import secrets
import string

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models import (
    Company, CompanyCreate, User, UserCreate, UserRole,
    Role, RoleGroup, CompanyRoleType, RolePermission, Screen, Permission,
    ContentMeta, ContentMetadata, Review,
    DeviceRegistrationKey
)
# Import new RBAC models
from app.rbac_models import (
    UserType, CompanyRole, Device
)
from app.repo import repo
from app.auth import get_password_hash


def generate_secure_key(length: int = 16) -> str:
    """Generate a secure random registration key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_organization_code() -> str:
    """Generate a unique organization code for a company"""
    return f"ORG-{uuid.uuid4().hex[:8].upper()}"


async def seed_sample_categories():
    """Seed sample content categories for demonstration"""
    print("🌱 Seeding sample content categories...")
    
    # Import the new models
    from app.models import ContentCategory, ContentTag
    
    # Sample categories
    categories_data = [
        {"name": "Food & Beverage", "description": "Restaurant, cafe, and food service advertisements"},
        {"name": "Retail & Shopping", "description": "Store promotions, sales, and retail advertisements"},
        {"name": "Entertainment", "description": "Movies, events, and entertainment promotions"},
        {"name": "Health & Wellness", "description": "Healthcare, fitness, and wellness services"},
        {"name": "Technology", "description": "Tech products, software, and digital services"},
        {"name": "Public Service", "description": "Government announcements and public information"}
    ]
    
    created_categories = []
    for cat_data in categories_data:
        try:
            category = ContentCategory(**cat_data)
            saved = await repo.save_content_category(category)
            created_categories.append(saved)
            print(f"  ✓ Created category: {category.name}")
        except Exception as e:
            print(f"  ✗ Failed to create category {cat_data['name']}: {e}")
    
    return created_categories


async def seed_sample_tags(categories):
    """Seed sample content tags"""
    print("🌱 Seeding sample content tags...")
    
    from app.models import ContentTag
    
    # Sample tags linked to categories
    tags_data = [
        {"name": "Fast Food", "description": "Quick service restaurants", "color": "#FF6B35"},
        {"name": "Coffee", "description": "Coffee shops and cafes", "color": "#8B4513"},
        {"name": "Sale", "description": "Sales and discount promotions", "color": "#FF0000"},
        {"name": "New Product", "description": "New product launches", "color": "#00FF00"},
        {"name": "Family Friendly", "description": "Content suitable for all ages", "color": "#0000FF"},
        {"name": "Premium", "description": "High-end, luxury products/services", "color": "#FFD700"}
    ]
    
    created_tags = []
    for tag_data in tags_data:
        try:
            tag = ContentTag(**tag_data)
            saved = await repo.save_content_tag(tag)
            created_tags.append(saved)
            print(f"  ✓ Created tag: {tag.name}")
        except Exception as e:
            print(f"  ✗ Failed to create tag {tag_data['name']}: {e}")
    
    return created_tags


async def seed_companies():
    """Seed comprehensive sample companies with different types"""
    print("🌱 Seeding sample companies with role-based structure...")
    print("  ⚠️  NOTE: These are sample companies for development. Remove for production!")

    # Comprehensive set for development testing - includes multiple companies of each type
    companies_data = [
        # HOST Companies
        {
            "name": "TechCorp Solutions",
            "type": "HOST",
            "address": "123 Tech Street, Dubai, UAE",
            "city": "Dubai",
            "country": "UAE",
            "phone": "+971-4-123-4567",
            "email": "info@techcorp-solutions.com",
            "website": "https://techcorp-solutions.com",
            "organization_code": generate_organization_code(),
            "status": "active"
        },
        {
            "name": "Digital Displays LLC",
            "type": "HOST", 
            "address": "456 Display Avenue, Abu Dhabi, UAE",
            "city": "Abu Dhabi",
            "country": "UAE",
            "phone": "+971-2-987-6543",
            "email": "contact@digitaldisplays.ae",
            "website": "https://digitaldisplays.ae",
            "organization_code": generate_organization_code(),
            "status": "active"
        },
        # ADVERTISER Companies
        {
            "name": "Creative Ads Inc",
            "type": "ADVERTISER",
            "address": "789 Creative Boulevard, Dubai, UAE",
            "city": "Dubai", 
            "country": "UAE",
            "phone": "+971-4-555-0123",
            "email": "hello@creativeads.com",
            "website": "https://creativeads.com",
            "organization_code": generate_organization_code(),
            "status": "active"
        },
        {
            "name": "AdVantage Media",
            "type": "ADVERTISER",
            "address": "321 Media Center, Sharjah, UAE",
            "city": "Sharjah",
            "country": "UAE",
            "phone": "+971-6-777-8888",
            "email": "team@advantage-media.ae",
            "website": "https://advantage-media.ae",
            "organization_code": generate_organization_code(),
            "status": "active"
        }
    ]

    created_companies = []
    for company_data in companies_data:
        try:
            company = Company(**company_data)
            saved = await repo.save_company(company)
            created_companies.append(saved)
            print(f"  ✓ Created {company.type.lower()} company: {company.name} (Org Code: {company.organization_code})")
        except Exception as e:
            print(f"  ✗ Failed to create company {company_data['name']}: {e}")

    return created_companies


async def seed_roles():
    """Seed comprehensive role hierarchy with company-specific roles"""
    print("🌱 Seeding comprehensive role hierarchy...")
    
    # Get companies for role assignment
    companies = await repo.list_companies()
    
    roles_data = [
        # Platform Administrator (Global)
        {
            "name": "Platform Administrator",
            "role_group": RoleGroup.ADMIN,
            "company_role_type": None,  # No company role type for platform admin
            "company_id": "global",
            "is_default": True,
            "status": "active"
        }
    ]

    # Create company-specific roles based on type
    for company in companies:
        company_id = company["id"]
        company_name = company["name"]
        company_type = company.get("type")

        if company_type == "HOST":
            # HOST Company Roles
            roles_data.extend([
                {
                    "name": f"{company_name} - Admin",
                    "role_group": RoleGroup.HOST,
                    "company_role_type": CompanyRoleType.COMPANY_ADMIN,
                    "company_id": company_id,
                    "is_default": True,
                    "status": "active"
                },
                {
                    "name": f"{company_name} - Approver",
                    "role_group": RoleGroup.HOST,
                    "company_role_type": CompanyRoleType.APPROVER,
                    "company_id": company_id,
                    "is_default": False,
                    "status": "active"
                },
                {
                    "name": f"{company_name} - Editor",
                    "role_group": RoleGroup.HOST,
                    "company_role_type": CompanyRoleType.EDITOR,
                    "company_id": company_id,
                    "is_default": False,
                    "status": "active"
                },
                {
                    "name": f"{company_name} - Viewer",
                    "role_group": RoleGroup.HOST,
                    "company_role_type": CompanyRoleType.VIEWER,
                    "company_id": company_id,
                    "is_default": False,
                    "status": "active"
                }
            ])
        
        elif company_type == "ADVERTISER":
            # ADVERTISER Company Roles
            roles_data.extend([
                {
                    "name": f"{company_name} - Admin",
                    "role_group": RoleGroup.ADVERTISER,
                    "company_role_type": CompanyRoleType.COMPANY_ADMIN,
                    "company_id": company_id,
                    "is_default": True,
                    "status": "active"
                },
                {
                    "name": f"{company_name} - Approver", 
                    "role_group": RoleGroup.ADVERTISER,
                    "company_role_type": CompanyRoleType.APPROVER,
                    "company_id": company_id,
                    "is_default": False,
                    "status": "active"
                },
                {
                    "name": f"{company_name} - Editor",
                    "role_group": RoleGroup.ADVERTISER,
                    "company_role_type": CompanyRoleType.EDITOR,
                    "company_id": company_id,
                    "is_default": False,
                    "status": "active"
                },
                {
                    "name": f"{company_name} - Viewer",
                    "role_group": RoleGroup.ADVERTISER,
                    "company_role_type": CompanyRoleType.VIEWER,
                    "company_id": company_id,
                    "is_default": False,
                    "status": "active"
                }
            ])

    created_roles = []
    for role_data in roles_data:
        try:
            role = Role(**role_data)
            saved = await repo.save_role(role)
            created_roles.append(saved)
            
            # Extract role type for cleaner display
            role_type = role_data.get("company_role_type", "PLATFORM_ADMIN")
            company_type = "GLOBAL" if role_data["company_id"] == "global" else companies[0].get("type", "UNKNOWN")
            print(f"  ✓ Created {company_type} {role_type}: {role.name}")
        except Exception as e:
            print(f"  ✗ Failed to create role {role_data['name']}: {e}")

    return created_roles


async def seed_role_permissions():
    """Seed comprehensive role-based permissions with company isolation"""
    print("🌱 Seeding comprehensive role-based permissions...")

    roles = await repo.list_roles_by_group("ADMIN") + await repo.list_roles_by_group("HOST") + await repo.list_roles_by_group("ADVERTISER")
    permissions_data = []

    # Define permission templates based on company role type
    permission_templates = {
        # Platform Admin - Full access to everything
        None: {  # Platform admin has no company_role_type
            "dashboard": ["view", "edit", "delete", "access"],
            "users": ["view", "edit", "delete", "access"],
            "companies": ["view", "edit", "delete", "access"], 
            "content": ["view", "edit", "delete", "access"],
            "moderation": ["view", "edit", "delete", "access"],
            "analytics": ["view", "edit", "delete", "access"],
            "settings": ["view", "edit", "delete", "access"],
            "billing": ["view", "edit", "delete", "access"]
        },
        # Company Admin - Full company management
        "COMPANY_ADMIN": {
            "dashboard": ["view", "edit", "access"],
            "users": ["view", "edit", "delete", "access"],  # Can manage company users
            "companies": ["view", "edit", "access"],  # Can edit own company
            "content": ["view", "edit", "delete", "access"],
            "moderation": ["view", "edit", "delete", "access"],
            "analytics": ["view", "edit", "access"],
            "settings": ["view", "edit", "access"]
        },
        # Approver - Content approval and analytics
        "APPROVER": {
            "dashboard": ["view", "access"],
            "content": ["view", "edit", "access"],  # Can approve/reject content
            "moderation": ["view", "edit", "access"],  # Full moderation access
            "analytics": ["view", "access"]
        },
        # Editor/Uploader - Content creation and basic management
        "EDITOR": {
            "dashboard": ["view", "access"],
            "content": ["view", "edit", "access"],  # Can upload/edit own content
            "analytics": ["view", "access"]  # Basic analytics
        },
        # Viewer - Read-only access
        "VIEWER": {
            "dashboard": ["view", "access"],
            "content": ["view", "access"],  # Can only view content
            "analytics": ["view", "access"]  # Basic analytics viewing
        }
    }

    for role in roles:
        role_id = role.get("id")
        role_group = role.get("role_group")
        company_role_type = role.get("company_role_type")
        role_name = role.get("name", "Unknown Role")

        # Get permission template based on role type
        if role_group == "ADMIN" and company_role_type is None:
            # Platform Administrator
            template = permission_templates[None]
        else:
            # Company-specific role
            template = permission_templates.get(company_role_type, permission_templates["VIEWER"])

        # Create permissions based on template
        for screen, permissions in template.items():
            permissions_data.append({
                "role_id": role_id,
                "screen": screen,
                "permissions": permissions
            })

    # Save all permissions
    created_count = 0
    for perm_data in permissions_data:
        try:
            permission = RolePermission(**perm_data)
            await repo.save_role_permission(permission)
            created_count += 1
        except Exception as e:
            print(f"  ✗ Failed to create permission for role {perm_data['role_id']}: {e}")

    print(f"  ✓ Created {created_count} role permissions across {len(roles)} roles")


async def seed_devices():
    """Seed sample devices with API keys for testing device authentication"""
    print("🌱 Seeding sample devices with API keys...")

    # Get HOST companies (only they can have devices)
    companies = await repo.list_companies()
    host_companies = [c for c in companies if c.get("type") == "HOST"]

    if not host_companies:
        print("  ⚠ No HOST companies found, skipping device seeding")
        return []

    devices_data = []
    for company in host_companies:
        company_id = company["id"]
        company_name = company["name"]
        
        # Create 2-3 devices per HOST company
        devices_data.extend([
            {
                "name": f"{company_name} - Main Display",
                "company_id": company_id,
                "api_key": generate_secure_key(32),  # Longer API key for devices
                "device_type": "digital_signage_display",
                "location": f"{company_name} Main Lobby",
                "status": "active",
                "metadata": {
                    "resolution": "1920x1080",
                    "orientation": "landscape",
                    "installation_date": "2024-01-15"
                }
            },
            {
                "name": f"{company_name} - Kiosk Terminal",
                "company_id": company_id,
                "api_key": generate_secure_key(32),
                "device_type": "interactive_kiosk",
                "location": f"{company_name} Reception Area",
                "status": "active",
                "metadata": {
                    "resolution": "1080x1920",
                    "orientation": "portrait",
                    "installation_date": "2024-02-01"
                }
            }
        ])

    created_devices = []
    for device_data in devices_data:
        try:
            # Create Device using the rbac_models Device class
            from app.rbac_models import Device
            device = Device(**device_data)
            saved = await repo.save_device(device.model_dump(exclude_none=True))
            created_devices.append(saved)
            print(f"  ✓ Created device: {device.name} (API Key: {device.api_key[:8]}...)")
        except Exception as e:
            print(f"  ✗ Failed to create device {device_data['name']}: {e}")

    print(f"\n📱 Device Creation Summary: {len(created_devices)} devices created")
    return created_devices


async def seed_users():
    """Seed comprehensive users with new RBAC system"""
    print("🌱 Seeding users with enhanced RBAC system...")
    print("  ⚠️  NOTE: Creating users for demo/development. Remove for production!")

    # Get companies for user assignment
    companies = await repo.list_companies()

    users_data = [
        # 1. SUPER_USER - Platform Administrator (no company association)
        {
            "name": "Platform Administrator",
            "email": "admin@openkiosk.com",
            "phone": "+971-4-ADMIN01",
            "hashed_password": get_password_hash("adminpass"),
            "user_type": UserType.SUPER_USER,
            "company_id": None,  # Super users are not tied to a company
            "company_role": None,
            "permissions": [
                # Super users have all permissions
                "company_create", "company_read", "company_update", "company_delete",
                "user_create", "user_read", "user_update", "user_delete",
                "content_create", "content_read", "content_update", "content_delete",
                "content_approve", "content_reject", "content_share",
                "device_create", "device_read", "device_update", "device_delete",
                "device_manage", "analytics_read", "settings_manage"
            ],
            "is_active": True,
            "email_verified": True,
            "last_login": None
        }
    ]

    # Create company-specific users with different RBAC roles
    for company in companies:
        company_id = company["id"]
        company_name = company["name"]
        company_type = company.get("type")

        if company_type == "HOST":
            # HOST company users with different access levels
            users_data.extend([
                # Company Admin - Full company management
                {
                    "name": f"{company_name} - Company Admin",
                    "email": f"admin@{company_name.lower().replace(' ', '').replace('-', '')}.com",
                    "phone": "+971-4-HOST01",
                    "hashed_password": get_password_hash("hostpass"),
                    "user_type": UserType.COMPANY_USER,
                    "company_id": company_id,
                    "company_role": CompanyRole.ADMIN,
                    "permissions": [
                        "user_create", "user_read", "user_update", "user_delete",
                        "content_create", "content_read", "content_update", "content_delete",
                        "content_approve", "content_reject", "content_share",
                        "device_create", "device_read", "device_update", "device_delete",
                        "device_manage", "analytics_read", "settings_manage"
                    ],
                    "is_active": True,
                    "email_verified": True,
                    "last_login": None
                },
                # Content Reviewer - Can approve/reject content
                {
                    "name": f"{company_name} - Content Reviewer",
                    "email": f"reviewer@{company_name.lower().replace(' ', '').replace('-', '')}.com",
                    "phone": "+971-4-HOST02",
                    "hashed_password": get_password_hash("hostpass"),
                    "user_type": UserType.COMPANY_USER,
                    "company_id": company_id,
                    "company_role": CompanyRole.REVIEWER,
                    "permissions": [
                        "content_read", "content_approve", "content_reject",
                        "analytics_read"
                    ],
                    "is_active": True,
                    "email_verified": True,
                    "last_login": None
                },
                # Content Editor - Can create and edit content
                {
                    "name": f"{company_name} - Content Editor",
                    "email": f"editor@{company_name.lower().replace(' ', '').replace('-', '')}.com",
                    "phone": "+971-4-HOST03",
                    "hashed_password": get_password_hash("hostpass"),
                    "user_type": UserType.COMPANY_USER,
                    "company_id": company_id,
                    "company_role": CompanyRole.EDITOR,
                    "permissions": [
                        "content_create", "content_read", "content_update",
                        "device_read", "analytics_read"
                    ],
                    "is_active": True,
                    "email_verified": True,
                    "last_login": None
                },
                # Viewer - Read-only access
                {
                    "name": f"{company_name} - Operations Viewer",
                    "email": f"viewer@{company_name.lower().replace(' ', '').replace('-', '')}.com",
                    "phone": "+971-4-HOST04",
                    "hashed_password": get_password_hash("hostpass"),
                    "user_type": UserType.COMPANY_USER,
                    "company_id": company_id,
                    "company_role": CompanyRole.VIEWER,
                    "permissions": [
                        "content_read", "device_read", "analytics_read"
                    ],
                    "is_active": True,
                    "email_verified": True,
                    "last_login": None
                }
            ])
        
        elif company_type == "ADVERTISER":
            # ADVERTISER company users with different access levels
            users_data.extend([
                # Company Admin - Full company management
                {
                    "name": f"{company_name} - Creative Director",
                    "email": f"director@{company_name.lower().replace(' ', '').replace('-', '')}.com",
                    "phone": "+971-4-ADV001",
                    "hashed_password": get_password_hash("advertiserpass"),
                    "user_type": UserType.COMPANY_USER,
                    "company_id": company_id,
                    "company_role": CompanyRole.ADMIN,
                    "permissions": [
                        "user_create", "user_read", "user_update", "user_delete",
                        "content_create", "content_read", "content_update", "content_delete",
                        "content_share", "analytics_read", "settings_manage"
                    ],
                    "is_active": True,
                    "email_verified": True,
                    "last_login": None
                },
                # Content Reviewer - Can approve content for sharing
                {
                    "name": f"{company_name} - Campaign Approver",
                    "email": f"approver@{company_name.lower().replace(' ', '').replace('-', '')}.com",
                    "phone": "+971-4-ADV002",
                    "hashed_password": get_password_hash("advertiserpass"),
                    "user_type": UserType.COMPANY_USER,
                    "company_id": company_id,
                    "company_role": CompanyRole.REVIEWER,
                    "permissions": [
                        "content_read", "content_approve", "content_share",
                        "analytics_read"
                    ],
                    "is_active": True,
                    "email_verified": True,
                    "last_login": None
                },
                # Content Creator - Can create and edit content
                {
                    "name": f"{company_name} - Content Creator",
                    "email": f"creator@{company_name.lower().replace(' ', '').replace('-', '')}.com",
                    "phone": "+971-4-ADV003",
                    "hashed_password": get_password_hash("advertiserpass"),
                    "user_type": UserType.COMPANY_USER,
                    "company_id": company_id,
                    "company_role": CompanyRole.EDITOR,
                    "permissions": [
                        "content_create", "content_read", "content_update",
                        "analytics_read"
                    ],
                    "is_active": True,
                    "email_verified": True,
                    "last_login": None
                },
                # Analytics Viewer - Read-only access to analytics
                {
                    "name": f"{company_name} - Analytics Viewer",
                    "email": f"analytics@{company_name.lower().replace(' ', '').replace('-', '')}.com",
                    "phone": "+971-4-ADV004",
                    "hashed_password": get_password_hash("advertiserpass"),
                    "user_type": UserType.COMPANY_USER,
                    "company_id": company_id,
                    "company_role": CompanyRole.VIEWER,
                    "permissions": [
                        "content_read", "analytics_read"
                    ],
                    "is_active": True,
                    "email_verified": True,
                    "last_login": None
                }
            ])

    created_users = []
    for user_data in users_data:
        try:
            user = User(**user_data)
            saved = await repo.save_user(user)
            created_users.append(saved)
            user_type = user_data.get("user_type", "UNKNOWN")
            company_role = user_data.get("company_role", "N/A")
            print(f"  ✓ Created {user_type} user: {user.email} (Role: {company_role})")
        except Exception as e:
            print(f"  ✗ Failed to create user {user_data['email']}: {e}")

    print(f"\n📊 User Creation Summary:")
    print(f"   SUPER_USER: 1")
    print(f"   COMPANY_USER: {len(created_users) - 1}")
    print(f"   Total: {len(created_users)}")

    return created_users


async def seed_user_roles():
    """Seed comprehensive user role assignments with proper company mapping"""
    print("🌱 Seeding comprehensive user role assignments...")

    users = await repo.list_users()
    companies = await repo.list_companies()
    all_roles = await repo.list_roles_by_group("ADMIN") + await repo.list_roles_by_group("HOST") + await repo.list_roles_by_group("ADVERTISER")

    user_roles_data = []
    created_count = 0

    for user in users:
        user_id = user["id"]
        user_email = user.get("email", "")
        user_name = user.get("name", "")

        # Platform Administrator
        if "admin@openkiosk.com" in user_email:
            admin_roles = [r for r in all_roles if r.get("role_group") == "ADMIN" and r.get("company_id") == "global"]
            for role in admin_roles:
                user_roles_data.append({
                    "user_id": user_id,
                    "company_id": "global",
                    "role_id": role["id"],
                    "is_default": True,
                    "status": "active"
                })
                created_count += 1

        # Company-specific user role assignments
        for company in companies:
            company_id = company["id"]
            company_name = company["name"]
            company_type = company.get("type")

            # Get all roles for this company
            company_roles = [r for r in all_roles if r.get("company_id") == company_id]

            if company_type == "HOST":
                # Map HOST users to roles based on email pattern
                role_mappings = {
                    f"host-admin@{company_name.lower().replace(' ', '-')}.com": "COMPANY_ADMIN",
                    f"approver@{company_name.lower().replace(' ', '-')}.com": "APPROVER", 
                    f"editor@{company_name.lower().replace(' ', '-')}.com": "EDITOR",
                    f"viewer@{company_name.lower().replace(' ', '-')}.com": "VIEWER"
                }

                for email_pattern, role_type in role_mappings.items():
                    if user_email == email_pattern:
                        # Find matching role for this company and type
                        matching_role = next((r for r in company_roles 
                                            if r.get("company_role_type") == role_type), None)
                        if matching_role:
                            user_roles_data.append({
                                "user_id": user_id,
                                "company_id": company_id,
                                "role_id": matching_role["id"],
                                "is_default": (role_type == "COMPANY_ADMIN"),  # Admin is default
                                "status": "active"
                            })
                            created_count += 1

            elif company_type == "ADVERTISER":
                # Map ADVERTISER users to roles based on email pattern
                role_mappings = {
                    f"director@{company_name.lower().replace(' ', '-')}.com": "COMPANY_ADMIN",
                    f"approver@{company_name.lower().replace(' ', '-')}.com": "APPROVER",
                    f"creator@{company_name.lower().replace(' ', '-')}.com": "EDITOR", 
                    f"analytics@{company_name.lower().replace(' ', '-')}.com": "VIEWER"
                }

                for email_pattern, role_type in role_mappings.items():
                    if user_email == email_pattern:
                        # Find matching role for this company and type
                        matching_role = next((r for r in company_roles 
                                            if r.get("company_role_type") == role_type), None)
                        if matching_role:
                            user_roles_data.append({
                                "user_id": user_id,
                                "company_id": company_id,
                                "role_id": matching_role["id"],
                                "is_default": (role_type == "COMPANY_ADMIN"),  # Admin is default
                                "status": "active"
                            })
                            created_count += 1

    # Save all user roles
    saved_count = 0
    for user_role_data in user_roles_data:
        try:
            user_role = UserRole(**user_role_data)
            await repo.save_user_role(user_role)
            saved_count += 1
        except Exception as e:
            print(f"  ✗ Failed to assign role: {e}")

    print(f"  ✓ Successfully assigned {saved_count} user roles to {len(users)} users")


async def seed_sample_content():
    """Seed sample content for testing"""
    print("🌱 Seeding sample content...")

    users = await repo.list_users()
    host_users = [u for u in users if "host" in u.get("email", "")]

    if not host_users:
        print("  ⚠ No host users found, skipping content seeding")
        return

    content_data = [
        {
            "owner_id": host_users[0]["id"],
            "filename": "sample_ad.mp4",
            "content_type": "video/mp4",
            "size": 1024000,
            "status": "approved"
        },
        {
            "owner_id": host_users[0]["id"] if len(host_users) > 0 else users[0]["id"],
            "filename": "banner.jpg",
            "content_type": "image/jpeg",
            "size": 512000,
            "status": "approved"
        }
    ]

    for content_item in content_data:
        try:
            content_meta = ContentMeta(**content_item)
            saved = await repo.save_content_meta(content_meta)
            print(f"  ✓ Created content: {content_item['filename']}")
        except Exception as e:
            print(f"  ✗ Failed to create content {content_item['filename']}: {e}")


async def seed_default_content():
    """Seed default content that ships with the system"""
    print("🌱 Seeding default content...")

    # Get admin user for default content ownership
    users = await repo.list_users()
    admin_users = [u for u in users if "admin" in u.get("email", "")]

    if not admin_users:
        print("  ⚠ No admin user found, skipping default content seeding")
        return

    admin_user = admin_users[0]

    # Get default categories
    categories = await repo.list_content_categories()
    welcome_category = next((c for c in categories if c.get("name") == "Public Service"), None)

    default_content_data = [
        {
            "owner_id": admin_user["id"],
            "filename": "logo.png",
            "content_type": "image/png",
            "size": 80582,
            "title": "Adara Logo",
            "description": "Official Adara Digital Signage logo",
            "status": "approved",
            "categories": [welcome_category["id"]] if welcome_category else [],
            "tags": [],
            "duration_seconds": 10,
            "content_rating": "G"
        },
        {
            "owner_id": admin_user["id"],
            "filename": "welcome.txt",
            "content_type": "text/plain",
            "size": 200,
            "title": "Welcome Message",
            "description": "Default welcome message for new displays",
            "status": "approved",
            "categories": [welcome_category["id"]] if welcome_category else [],
            "tags": [],
            "duration_seconds": 15,
            "content_rating": "G"
        },
        {
            "owner_id": admin_user["id"],
            "filename": "thank_you.txt",
            "content_type": "text/plain",
            "size": 150,
            "title": "Thank You Message",
            "description": "Thank you message for display viewers",
            "status": "approved",
            "categories": [welcome_category["id"]] if welcome_category else [],
            "tags": [],
            "duration_seconds": 10,
            "content_rating": "G"
        },
        {
            "owner_id": admin_user["id"],
            "filename": "promotion.txt",
            "content_type": "text/plain",
            "size": 300,
            "title": "Service Promotion",
            "description": "Promotional content about Adara services",
            "status": "approved",
            "categories": [welcome_category["id"]] if welcome_category else [],
            "tags": [],
            "duration_seconds": 20,
            "content_rating": "G"
        },
        {
            "owner_id": admin_user["id"],
            "filename": "ad1.jpg",
            "content_type": "image/jpeg",
            "size": 136,
            "title": "Sample Advertisement 1",
            "description": "Sample advertisement image",
            "status": "approved",
            "categories": [],
            "tags": [],
            "duration_seconds": 8,
            "content_rating": "G"
        },
        {
            "owner_id": admin_user["id"],
            "filename": "ad2.jpg",
            "content_type": "image/jpeg",
            "size": 136,
            "title": "Sample Advertisement 2",
            "description": "Sample advertisement image",
            "status": "approved",
            "categories": [],
            "tags": [],
            "duration_seconds": 8,
            "content_rating": "G"
        }
    ]

    created_content = []
    for content_item in default_content_data:
        try:
            # Create ContentMeta
            content_meta = ContentMeta(**content_item)
            saved_meta = await repo.save_content_meta(content_meta)

            # Create ContentMetadata for additional details
            metadata = ContentMetadata(
                id=saved_meta["id"],
                title=content_item["title"],
                description=content_item["description"],
                owner_id=content_item["owner_id"],
                categories=content_item["categories"],
                tags=content_item["tags"],
                duration_seconds=content_item["duration_seconds"],
                content_rating=content_item["content_rating"]
            )
            await repo.save(metadata)

            created_content.append(saved_meta)
            print(f"  ✓ Created default content: {content_item['title']}")
        except Exception as e:
            print(f"  ✗ Failed to create default content {content_item['title']}: {e}")

    return created_content


async def seed_registration_keys():
    """Seed sample registration keys for testing"""
    print("🌱 Seeding sample registration keys...")

    companies = await repo.list_companies()
    users = await repo.list_users()
    admin_users = [u for u in users if "admin" in u.get("email", "")]

    if not admin_users:
        print("  ⚠ No admin users found, skipping registration key seeding")
        return

    for company in companies:
        try:
            key_data = {
                "id": str(uuid.uuid4()),
                "key": generate_secure_key(),
                "company_id": company["id"],
                "created_by": admin_users[0]["id"],
                "expires_at": datetime.utcnow() + timedelta(days=30),
                "used": False,
                "used_by_device": None
            }

            key = DeviceRegistrationKey(**key_data)
            await repo.save_device_registration_key(key)
            print(f"  ✓ Created registration key for {company['name']}: {key_data['key']}")
        except Exception as e:
            print(f"  ✗ Failed to create registration key for {company['name']}: {e}")


async def main():
    """Main seeding function - Production ready with minimal data"""
    print("🚀 Starting database seeding...")
    print("=" * 50)
    print("  📝 NOTE: This creates minimal data suitable for production")
    print("  📝 Companies register through the application process")
    print("  📝 Only admin user and sample categories are created")
    print("=" * 50)

    try:
        # Seed sample categories and tags first
        categories = await seed_sample_categories()
        tags = await seed_sample_tags(categories)
        
        # Seed minimal demo companies (for development only)
        companies = await seed_companies()
        
        # Seed roles for admin and any demo companies
        roles = await seed_roles()
        await seed_role_permissions()
        
        # Seed only essential users
        users = await seed_users()
        await seed_user_roles()
        
        # Seed devices for HOST companies (for authentication testing)
        if companies:
            await seed_devices()
        
        # Only create registration keys for demo companies
        if companies:
            await seed_registration_keys()

        # Seed default content that ships with the system
        await seed_default_content()

        print("=" * 50)
        print("✅ Database seeding completed successfully!")
        print(f"   Categories: {len(categories) if categories else 0}")
        print(f"   Tags: {len(tags) if tags else 0}")
        print(f"   Demo Companies: {len(companies) if companies else 0}")
        print(f"   Roles: {len(roles) if roles else 0}")
        print(f"   Users: {len(users) if users else 0}")

        # Print login credentials
        print("\n🔐 Login Credentials:")
        print("   Admin: admin@openkiosk.com / adminpass")
        
        if companies:
            print("\n🧪 Demo Credentials (Development Only):")
            print("   Demo Host: demo-host@example.com / demopass")
            print("   Demo Advertiser: demo-advertiser@example.com / demopass")
            print("\n⚠️  WARNING: Remove demo companies and users before production deployment!")
        
        print("\n📋 Next Steps:")
        print("   1. Companies apply through /api/company-applications")
        print("   2. Admin approves applications in dashboard")
        print("   3. Approved companies can register users")
        print("   4. Host companies configure content preferences")
        print("   5. Advertisers upload content with categories/tags")

    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)