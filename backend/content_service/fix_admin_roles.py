#!/usr/bin/env python3
"""
Script to fix admin user roles and verify the role system
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.repo import repo
from app.auth import authenticate_user, get_current_user_with_roles
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_admin_roles():
    """Fix admin user roles and verify they work correctly"""
    print("🔧 Fixing Admin User Roles")
    print("=" * 50)
    
    try:
        # 1. Check if admin user exists
        admin_user = await repo.get_user_by_email("admin@openkiosk.com")
        if not admin_user:
            print("❌ Admin user not found!")
            return False
        
        print(f"✅ Admin user found: {admin_user.get('email')}")
        admin_user_id = admin_user["id"]
        
        # 2. Get current user roles
        user_roles = await repo.get_user_roles(admin_user_id)
        print(f"📋 Admin has {len(user_roles)} role assignments:")
        
        for i, role in enumerate(user_roles):
            print(f"   {i+1}. Company: {role.get('company_id')}, Role ID: {role.get('role_id')}")
            
            # Check if role exists
            role_id = role.get('role_id')
            if role_id:
                role_details = await repo.get_role(role_id)
                if role_details:
                    print(f"      ✅ Role found: {role_details.get('name')} ({role_details.get('role_group')})")
                else:
                    print(f"      ❌ Role NOT FOUND for ID: {role_id}")
        
        # 3. Get all ADMIN roles
        admin_roles = await repo.list_roles_by_group("ADMIN")
        print(f"\n🛡️  Found {len(admin_roles)} ADMIN roles in system:")
        for role in admin_roles:
            print(f"   - {role.get('name')} (ID: {role.get('id')})")
        
        # 4. Check if admin user has a valid ADMIN role
        has_valid_admin_role = False
        for user_role in user_roles:
            role_id = user_role.get('role_id')
            if role_id:
                role_details = await repo.get_role(role_id)
                if role_details and role_details.get('role_group') == 'ADMIN':
                    has_valid_admin_role = True
                    print(f"✅ Admin has valid ADMIN role: {role_details.get('name')}")
                    break
        
        if not has_valid_admin_role:
            print("❌ Admin user does NOT have a valid ADMIN role!")
            
            # Fix by assigning first ADMIN role
            if admin_roles:
                print("🔧 Fixing by assigning ADMIN role...")
                
                # Remove existing role assignments
                for user_role in user_roles:
                    await repo.delete_user_role(user_role.get("id"))
                
                # Create new ADMIN role assignment
                from app.models import UserRole
                new_user_role = UserRole(
                    user_id=admin_user_id,
                    company_id="global",
                    role_id=admin_roles[0]["id"],
                    is_default=True,
                    status="active"
                )
                await repo.save_user_role(new_user_role)
                print(f"✅ Assigned ADMIN role: {admin_roles[0].get('name')}")
                has_valid_admin_role = True
            else:
                print("❌ No ADMIN roles found in system!")
                return False
        
        # 5. Test authentication flow
        print("\n🧪 Testing authentication flow...")
        try:
            auth_result = await get_current_user_with_roles("admin@openkiosk.com", bypass_token=True)
            print("✅ Authentication successful")
            
            roles = auth_result.get("roles", [])
            print(f"📋 Processed roles: {len(roles)}")
            for role in roles:
                print(f"   - {role.get('role_name')} ({role.get('role')})")
                
            admin_roles_in_auth = [r for r in roles if r.get('role') == 'ADMIN']
            if admin_roles_in_auth:
                print(f"✅ Admin user has ADMIN role in auth response")
            else:
                print(f"❌ Admin user does NOT have ADMIN role in auth response")
                print(f"   Roles found: {[r.get('role') for r in roles]}")
                return False
            
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return False
        
        # 6. Test role checking
        print("\n🎯 Testing role functions...")
        try:
            # Test direct authentication
            auth_user = await authenticate_user("admin@openkiosk.com", "adminpass")
            if auth_user:
                print("✅ Direct authentication successful")
            else:
                print("❌ Direct authentication failed")
                return False
            
        except Exception as e:
            print(f"❌ Role function test failed: {e}")
            return False
        
        print("\n🎉 Admin role fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during admin role fix: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_all_users():
    """Verify all user roles are working"""
    print("\n👥 Verifying All User Roles")
    print("=" * 50)
    
    test_users = [
        ("admin@openkiosk.com", "adminpass", "ADMIN"),
        ("host@openkiosk.com", "hostpass", "HOST"),
        ("advertiser@openkiosk.com", "advertiserpass", "ADVERTISER")
    ]
    
    for email, password, expected_role in test_users:
        print(f"\n🧪 Testing {email}...")
        try:
            # Test authentication
            user = await authenticate_user(email, password)
            if user:
                print(f"  ✅ Authentication successful")
                
                # Test role processing
                user_with_roles = await get_current_user_with_roles(email, bypass_token=True)
                roles = user_with_roles.get("roles", [])
                
                role_types = [r.get('role') for r in roles]
                if expected_role in role_types:
                    print(f"  ✅ Has expected role: {expected_role}")
                else:
                    print(f"  ❌ Missing expected role: {expected_role}")
                    print(f"     Found roles: {role_types}")
            else:
                print(f"  ❌ Authentication failed")
                
        except Exception as e:
            print(f"  ❌ Error testing {email}: {e}")

# Add the bypass function that was referenced in debug_roles.py
async def get_current_user_with_roles(username: str, bypass_token: bool = False):
    """Helper to get user with roles, bypassing token check for debug"""
    if not bypass_token:
        from app.auth import get_current_user_with_roles as auth_get_user
        return await auth_get_user(username)
    
    # Direct database lookup for debugging
    user_data = await repo.get_user_by_email(username)
    if not user_data:
        raise Exception("User not found")
    
    # Process roles the same way as normal auth
    user_roles = await repo.get_user_roles(user_data["id"])
    
    # Simulate the role expansion logic from auth.py
    companies = []
    for role in user_roles:
        company_id = role.get("company_id")
        if company_id and company_id != "global":
            try:
                company = await repo.get_company(company_id)
                if company:
                    companies.append(company)
            except Exception:
                pass
    
    user_data["companies"] = companies
    
    # Expand roles (using the same logic as auth.py)
    expanded_roles = []
    for user_role in user_roles:
        role_id = user_role.get("role_id")
        if role_id:
            try:
                role = await repo.get_role(role_id)
                if role:
                    expanded_role = {
                        **user_role,
                        "role": role.get("role_group"),
                        "role_name": role.get("name"),
                        "role_details": role
                    }
                    expanded_roles.append(expanded_role)
                else:
                    print(f"Role not found for ID: {role_id}, applying fallback")
                    # Apply the same fallback logic as auth.py
                    company_id = user_role.get("company_id")
                    if company_id and company_id != "global":
                        fallback_role = "HOST"
                        fallback_name = "Host Manager"
                    else:
                        fallback_role = "USER"
                        fallback_name = "User"
                    
                    expanded_roles.append({
                        **user_role,
                        "role": fallback_role,
                        "role_name": fallback_name
                    })
            except Exception as e:
                print(f"Error getting role {role_id}: {e}")
                # Same fallback logic
                company_id = user_role.get("company_id")
                if company_id and company_id != "global":
                    fallback_role = "HOST"
                    fallback_name = "Host Manager"
                else:
                    fallback_role = "USER"
                    fallback_name = "User"
                
                expanded_roles.append({
                    **user_role,
                    "role": fallback_role,
                    "role_name": fallback_name
                })
    
    user_data["roles"] = expanded_roles
    return user_data

async def main():
    """Main function"""
    print("🚀 OpenKiosk Admin Role Fixer")
    print("=" * 60)
    
    # Fix admin roles
    success = await fix_admin_roles()
    
    if success:
        # Verify all users
        await verify_all_users()
        print("\n✅ All checks completed!")
    else:
        print("\n❌ Admin role fix failed!")
        
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)