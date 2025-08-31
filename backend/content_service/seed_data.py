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
    Role, RoleGroup, RolePermission, Screen, Permission,
    ContentMeta, ContentMetadata, Review,
    DeviceRegistrationKey
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
    """Seed minimal sample companies for development only"""
    print("🌱 Seeding minimal sample companies...")
    print("  ⚠️  NOTE: These are sample companies for development. Remove for production!")

    # Minimal set for development testing
    companies_data = [
        {
            "name": "Demo Host Company",
            "type": "HOST",
            "address": "123 Demo Street, Test City, TC 12345",
            "city": "Test City",
            "country": "Demo Land",
            "phone": "+1-555-DEMO1",
            "email": "demo@host-company.example",
            "website": "https://demo-host.example",
            "organization_code": generate_organization_code(),
            "status": "active"
        },
        {
            "name": "Demo Advertiser Company",
            "type": "ADVERTISER",
            "address": "456 Demo Avenue, Test City, TC 12345",
            "city": "Test City",
            "country": "Demo Land",
            "phone": "+1-555-DEMO2",
            "email": "demo@advertiser-company.example",
            "website": "https://demo-advertiser.example",
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
            print(f"  ✓ Created demo company: {company.name} (Org Code: {company.organization_code})")
        except Exception as e:
            print(f"  ✗ Failed to create company {company_data['name']}: {e}")

    return created_companies


async def seed_roles():
    """Seed roles and permissions"""
    print("🌱 Seeding roles and permissions...")

    # Get companies for role assignment
    companies = await repo.list_companies()

    roles_data = [
        # System Administrator
        {
            "name": "System Administrator",
            "role_group": RoleGroup.ADMIN,
            "company_id": "global",
            "is_default": True,
            "status": "active"
        }
    ]

    # Add company-specific roles
    for company in companies:
        if company.get("type") == "HOST":
            roles_data.extend([
                {
                    "name": f"{company['name']} Manager",
                    "role_group": RoleGroup.HOST,
                    "company_id": company["id"],
                    "is_default": True,
                    "status": "active"
                },
                {
                    "name": f"{company['name']} Screen Operator",
                    "role_group": RoleGroup.HOST,
                    "company_id": company["id"],
                    "is_default": False,
                    "status": "active"
                }
            ])
        elif company.get("type") == "ADVERTISER":
            roles_data.extend([
                {
                    "name": f"{company['name']} Director",
                    "role_group": RoleGroup.ADVERTISER,
                    "company_id": company["id"],
                    "is_default": True,
                    "status": "active"
                },
                {
                    "name": f"{company['name']} Content Creator",
                    "role_group": RoleGroup.ADVERTISER,
                    "company_id": company["id"],
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
            print(f"  ✓ Created role: {role.name}")
        except Exception as e:
            print(f"  ✗ Failed to create role {role_data['name']}: {e}")

    return created_roles


async def seed_role_permissions():
    """Seed role permissions"""
    print("🌱 Seeding role permissions...")

    roles = await repo.list_roles_by_group("ADMIN") + await repo.list_roles_by_group("HOST") + await repo.list_roles_by_group("ADVERTISER")

    permissions_data = []

    for role in roles:
        role_id = role.get("id")
        role_group = role.get("role_group")

        if role_group == "ADMIN":
            # Admin gets all permissions
            screens = ["dashboard", "users", "companies", "content", "moderation", "analytics", "settings", "billing"]
            for screen in screens:
                permissions_data.append({
                    "role_id": role_id,
                    "screen": screen,
                    "permissions": ["view", "edit", "delete", "access"]
                })
        elif role_group == "HOST":
            # Host gets content and screen management permissions
            permissions_data.extend([
                {"role_id": role_id, "screen": "dashboard", "permissions": ["view", "access"]},
                {"role_id": role_id, "screen": "content", "permissions": ["view", "edit", "access"]},
                {"role_id": role_id, "screen": "moderation", "permissions": ["view", "edit", "access"]},
                {"role_id": role_id, "screen": "analytics", "permissions": ["view", "access"]}
            ])
        elif role_group == "ADVERTISER":
            # Advertiser gets content creation and analytics permissions
            permissions_data.extend([
                {"role_id": role_id, "screen": "dashboard", "permissions": ["view", "access"]},
                {"role_id": role_id, "screen": "content", "permissions": ["view", "edit", "access"]},
                {"role_id": role_id, "screen": "analytics", "permissions": ["view", "access"]}
            ])

    for perm_data in permissions_data:
        try:
            permission = RolePermission(**perm_data)
            await repo.save_role_permission(permission)
        except Exception as e:
            print(f"  ✗ Failed to create permission: {e}")

    print(f"  ✓ Created {len(permissions_data)} role permissions")


async def seed_users():
    """Seed only essential admin user for production readiness"""
    print("🌱 Seeding essential users...")
    print("  ⚠️  NOTE: Only creating admin user. Companies register through application process.")

    # Only create admin user - companies and their users will be created through registration
    users_data = [
        # System Admin - ONLY ESSENTIAL USER
        {
            "name": "System Administrator",
            "email": "admin@openkiosk.com",
            "phone": "+1-555-ADMIN",
            "hashed_password": get_password_hash("adminpass"),
            "status": "active",
            "email_verified": True,
            "last_login": None  # Will be set on first login
        }
    ]

    # Only create demo users if we have demo companies (development mode)
    companies = await repo.list_companies()
    if companies:
        print("  ⚠️  Creating demo users for demo companies (development only)")
        roles = await repo.list_roles_by_group("HOST") + await repo.list_roles_by_group("ADVERTISER")
        
        for company in companies:
            if company["type"] == "HOST":
                users_data.append({
                    "name": f"{company['name']} Manager",
                    "email": f"demo-host@example.com",
                    "phone": "+1-555-DEMO-HOST",
                    "hashed_password": get_password_hash("demopass"),
                    "status": "active",
                    "email_verified": True,
                    "last_login": None
                })
            elif company["type"] == "ADVERTISER":
                users_data.append({
                    "name": f"{company['name']} Director",
                    "email": f"demo-advertiser@example.com",
                    "phone": "+1-555-DEMO-ADV",
                    "hashed_password": get_password_hash("demopass"),
                    "status": "active",
                    "email_verified": True,
                    "last_login": None
                })

    created_users = []
    for user_data in users_data:
        try:
            user = User(**user_data)
            saved = await repo.save_user(user)
            created_users.append(saved)
            print(f"  ✓ Created user: {user.email}")
        except Exception as e:
            print(f"  ✗ Failed to create user {user_data['email']}: {e}")

    return created_users


async def seed_user_roles():
    """Seed user role assignments"""
    print("🌱 Seeding user roles...")

    users = await repo.list_users()
    roles = await repo.list_roles_by_group("ADMIN") + await repo.list_roles_by_group("HOST") + await repo.list_roles_by_group("ADVERTISER")

    user_roles_data = []

    for user in users:
        user_email = user.get("email")

        if "admin" in user_email:
            # Admin user gets admin role
            admin_roles = [r for r in roles if r.get("role_group") == "ADMIN"]
            for role in admin_roles:
                user_roles_data.append({
                    "user_id": user["id"],
                    "company_id": "global",
                    "role_id": role["id"],
                    "is_default": True,
                    "status": "active"
                })
        elif "host" in user_email or "operator" in user_email:
            # Host users get host roles
            for role in roles:
                if role.get("role_group") == "HOST":
                    company_id = role.get("company_id")
                    if company_id and company_id != "global":
                        user_roles_data.append({
                            "user_id": user["id"],
                            "company_id": company_id,
                            "role_id": role["id"],
                            "is_default": "manager" in user_email.lower(),
                            "status": "active"
                        })
        elif "director" in user_email or "creator" in user_email:
            # Advertiser users get advertiser roles
            for role in roles:
                if role.get("role_group") == "ADVERTISER":
                    company_id = role.get("company_id")
                    if company_id and company_id != "global":
                        user_roles_data.append({
                            "user_id": user["id"],
                            "company_id": company_id,
                            "role_id": role["id"],
                            "is_default": "director" in user_email.lower(),
                            "status": "active"
                        })

    for user_role_data in user_roles_data:
        try:
            user_role = UserRole(**user_role_data)
            await repo.save_user_role(user_role)
        except Exception as e:
            print(f"  ✗ Failed to create user role: {e}")

    print(f"  ✓ Created {len(user_roles_data)} user role assignments")


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
        
        # Only create registration keys for demo companies
        if companies:
            await seed_registration_keys()

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