#!/usr/bin/env python3
"""
Simplified Data Seeding Script
==============================

This script creates a simple RBAC structure:
- Users belong to companies
- Users have roles (SUPER_ADMIN, ADMIN, EDITOR, VIEWER)
- Permissions are tied to roles only, not company-specific
"""

import asyncio
import sys
import os
from datetime import datetime
import uuid
import secrets
import string
from dotenv import load_dotenv
load_dotenv()

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models import Company, User, Role, UserRole, RolePermission
from app.repo import repo
from app.auth import get_password_hash


def generate_secure_key(length: int = 16) -> str:
    """Generate a secure random key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_organization_code() -> str:
    """Generate a unique organization code for a company"""
    return f"ORG-{uuid.uuid4().hex[:8].upper()}"


async def clear_existing_data():
    """Clear all existing data"""
    print("🧹 Clearing existing data...")
    try:
        if hasattr(repo, '_user_col'):
            # MongoDB
            await repo._user_col.delete_many({})
            await repo._role_col.delete_many({})
            await repo._user_role_col.delete_many({})
            await repo._role_permission_col.delete_many({})
            await repo._company_col.delete_many({})
            print("  ✓ All MongoDB collections cleared")
        elif hasattr(repo, '_store'):
            # In-memory
            repo._store.clear()
            print("  ✓ In-memory store cleared")
    except Exception as e:
        print(f"  ⚠ Error clearing data: {e}")


async def seed_companies():
    """Create sample companies"""
    print("🌱 Creating companies...")
    
    companies_data = [
        {
            "name": "TechCorp Solutions",
            "type": "HOST",
            "address": "123 Tech Street, Dubai, UAE",
            "city": "Dubai",
            "country": "UAE",
            "phone": "+971-4-123-4567",
            "email": "info@techcorp.com",
            "organization_code": generate_organization_code(),
            "status": "active"
        },
        {
            "name": "Creative Ads Agency",
            "type": "ADVERTISER",
            "address": "456 Creative Blvd, Dubai, UAE",
            "city": "Dubai",
            "country": "UAE",
            "phone": "+971-4-987-6543",
            "email": "info@creativeads.com",
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
            print(f"  ✓ Created {company.type} company: {company.name}")
        except Exception as e:
            print(f"  ✗ Failed to create company {company_data['name']}: {e}")

    return created_companies


async def seed_roles():
    """Create simple global roles"""
    print("🌱 Creating global roles...")
    
    roles_data = [
        {
            "name": "Super Administrator",
            "role_group": "ADMIN",
            "company_role_type": None,
            "company_id": "global",  # Global role
            "is_default": False,
            "status": "active"
        },
        {
            "name": "Administrator", 
            "role_group": "ADMIN",
            "company_role_type": "COMPANY_ADMIN",
            "company_id": "global",  # Global role
            "is_default": False,
            "status": "active"
        },
        {
            "name": "Editor",
            "role_group": "HOST",  # Use valid enum value
            "company_role_type": "EDITOR", 
            "company_id": "global",  # Global role
            "is_default": False,
            "status": "active"
        },
        {
            "name": "Viewer",
            "role_group": "HOST",  # Use valid enum value
            "company_role_type": "VIEWER",
            "company_id": "global",  # Global role
            "is_default": True,
            "status": "active"
        }
    ]

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
    """Create permissions for roles"""
    print("🌱 Creating role permissions...")
    
    # Get all roles
    if hasattr(repo, '_store'):
        roles = list(repo._store.get("__roles__", {}).values())
    else:
        roles_cursor = repo._role_col.find({})
        roles = await roles_cursor.to_list(length=None)
    
    # Permission templates by role name
    permission_templates = {
        "Super Administrator": {
            "dashboard": ["view", "edit", "delete", "access"],
            "users": ["view", "edit", "delete", "access"],
            "companies": ["view", "edit", "delete", "access"],
            "content": ["view", "edit", "delete", "access"],
            "moderation": ["view", "edit", "delete", "access"],
            "analytics": ["view", "edit", "delete", "access"],
            "settings": ["view", "edit", "delete", "access"]
        },
        "Administrator": {
            "dashboard": ["view", "edit", "access"],
            "users": ["view", "edit", "delete", "access"],
            "content": ["view", "edit", "delete", "access"],
            "moderation": ["view", "edit", "access"],
            "analytics": ["view", "edit", "access"],
            "settings": ["view", "edit", "access"]
        },
        "Editor": {
            "dashboard": ["view", "access"],
            "content": ["view", "edit", "access"],
            "analytics": ["view", "access"]
        },
        "Viewer": {
            "dashboard": ["view", "access"],
            "content": ["view", "access"],
            "analytics": ["view", "access"]
        }
    }

    created_count = 0
    for role in roles:
        role_id = role.get("id") or str(role.get("_id"))
        role_name = role.get("name")
        
        template = permission_templates.get(role_name, {})
        
        for screen, permissions in template.items():
            perm_data = {
                "role_id": role_id,
                "screen": screen,
                "permissions": permissions
            }
            
            try:
                permission = RolePermission(**perm_data)
                await repo.save_role_permission(permission)
                created_count += 1
            except Exception as e:
                print(f"  ✗ Failed to create permission for role {role_name}: {e}")

    print(f"  ✓ Created {created_count} permissions across {len(roles)} roles")


async def seed_users():
    """Create users with simple company + role assignment"""
    print("🌱 Creating users...")
    
    # Get companies and roles for assignment
    companies = await repo.list_companies()
    if hasattr(repo, '_store'):
        roles = list(repo._store.get("__roles__", {}).values())
    else:
        roles_cursor = repo._role_col.find({})
        roles = await roles_cursor.to_list(length=None)
    
    # Find roles by name
    super_admin_role = next((r for r in roles if r.get("name") == "Super Administrator"), None)
    admin_role = next((r for r in roles if r.get("name") == "Administrator"), None)
    editor_role = next((r for r in roles if r.get("name") == "Editor"), None)
    
    users_data = [
        # Super Administrator (not tied to any company)
        {
            "name": "Platform Super Admin",
            "email": "admin@openkiosk.com",
            "phone": "+971-4-000-0001",
            "hashed_password": get_password_hash("adminpass"),
            "user_type": "SUPER_USER",
            "status": "active",
            "is_active": True,
            "email_verified": True,
            "is_deleted": False
        }
    ]

    # Add company-specific admins
    for company in companies:
        company_id = company.get("id") or str(company.get("_id"))
        company_name = company.get("name", "Unknown")
        company_type = company.get("type", "")
        
        # Company admin
        users_data.append({
            "name": f"{company_name} Admin",
            "email": f"admin@{company_name.lower().replace(' ', '').replace('-', '')}.com",
            "phone": f"+971-4-{company_type[:3].upper()}-001",
            "hashed_password": get_password_hash("companypass"),
            "user_type": "COMPANY_USER",
            "company_id": company_id,  # Store company_id in user
            "status": "active",
            "is_active": True,
            "email_verified": True,
            "is_deleted": False
        })
        
        # Company editor
        users_data.append({
            "name": f"{company_name} Editor",
            "email": f"editor@{company_name.lower().replace(' ', '').replace('-', '')}.com",
            "phone": f"+971-4-{company_type[:3].upper()}-002",
            "hashed_password": get_password_hash("editorpass"),
            "user_type": "COMPANY_USER",
            "company_id": company_id,  # Store company_id in user
            "status": "active",
            "is_active": True,
            "email_verified": True,
            "is_deleted": False
        })

    created_users = []
    for user_data in users_data:
        try:
            user = User(**user_data)
            saved = await repo.save_user(user)
            created_users.append(saved)
            user_type = user_data.get("user_type", "USER")
            print(f"  ✓ Created {user_type}: {user.email}")
        except Exception as e:
            print(f"  ✗ Failed to create user {user_data['email']}: {e}")

    return created_users


async def seed_user_roles():
    """Assign roles to users"""
    print("🌱 Assigning roles to users...")
    
    # Get users and roles
    users = await repo.list_users()
    if hasattr(repo, '_store'):
        roles = list(repo._store.get("__roles__", {}).values())
    else:
        roles_cursor = repo._role_col.find({})
        roles = await roles_cursor.to_list(length=None)
    
    # Find roles by name
    super_admin_role = next((r for r in roles if r.get("name") == "Super Administrator"), None)
    admin_role = next((r for r in roles if r.get("name") == "Administrator"), None)
    editor_role = next((r for r in roles if r.get("name") == "Editor"), None)
    viewer_role = next((r for r in roles if r.get("name") == "Viewer"), None)

    created_count = 0
    for user in users:
        user_id = user.get("id") or str(user.get("_id"))
        user_email = user.get("email", "")
        user_type = user.get("user_type", "")
        company_id = user.get("company_id")
        
        # Assign role based on user email pattern
        role_to_assign = None
        if user_email == "admin@openkiosk.com":
            role_to_assign = super_admin_role
            company_id = "global"
        elif "admin@" in user_email:
            role_to_assign = admin_role
        elif "editor@" in user_email:
            role_to_assign = editor_role
        else:
            role_to_assign = viewer_role
        
        if role_to_assign:
            try:
                role_id = role_to_assign.get("id") or str(role_to_assign.get("_id"))
                user_role_data = {
                    "user_id": user_id,
                    "company_id": company_id or "global",
                    "role_id": role_id,
                    "is_default": True,
                    "status": "active"
                }
                
                user_role = UserRole(**user_role_data)
                await repo.save_user_role(user_role)
                created_count += 1
                print(f"  ✓ Assigned {role_to_assign.get('name')} to {user_email}")
            except Exception as e:
                print(f"  ✗ Failed to assign role to {user_email}: {e}")

    print(f"  ✓ Successfully assigned {created_count} role assignments")


async def main():
    """Main seeding function"""
    print("🚀 Starting simplified database seeding...")
    print("=" * 50)

    try:
        # Clear existing data
        await clear_existing_data()
        
        # Create base data
        companies = await seed_companies()
        roles = await seed_roles()
        await seed_role_permissions()
        
        # Create users and assign roles
        users = await seed_users()
        await seed_user_roles()

        print("=" * 50)
        print("✅ Simplified database seeding completed!")
        print(f"   Companies: {len(companies)}")
        print(f"   Roles: {len(roles)}")
        print(f"   Users: {len(users)}")

        print("\n🔐 Login Credentials:")
        print("   Super Admin: admin@openkiosk.com / adminpass")
        print("   Company Admin: admin@techcorpsolutions.com / companypass")
        print("   Company Admin: admin@creativeadsagency.com / companypass")
        print("   Editor: editor@techcorpsolutions.com / editorpass")
        print("   Editor: editor@creativeadsagency.com / editorpass")

    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
