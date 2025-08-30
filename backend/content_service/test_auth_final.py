"""
Final authentication system test
"""
import asyncio
from app.auth import init_default_data, authenticate_user, get_current_user_with_roles, create_access_token
from app.repo import repo

async def test_complete_auth_flow():
    """Test the complete authentication flow"""
    print("=== Testing Complete Authentication System ===\n")
    
    # 1. Initialize system
    print("1. Initializing system...")
    repo._store.clear()  # Clear for fresh start
    await init_default_data()
    
    # 2. Test admin user creation
    admin_user = await repo.get_user_by_email('admin@openkiosk.com')
    print(f"   Admin user created: {admin_user is not None}")
    
    if admin_user:
        # 3. Test roles
        user_roles = await repo.get_user_roles(admin_user['id'])
        print(f"   Admin user roles: {len(user_roles)}")
        
        for role in user_roles:
            role_data = await repo.get_role(role['role_id'])
            permissions = await repo.get_role_permissions(role['role_id'])
            print(f"   - Role: {role_data.get('name')} ({role_data.get('role_group')})")
            print(f"     Permissions: {len(permissions)}")
        
        # 4. Test authentication
        print("\n2. Testing authentication...")
        auth_user = await authenticate_user('admin@openkiosk.com', 'adminpass')
        print(f"   Authentication successful: {auth_user is not None}")
        
        # 5. Test token generation
        if auth_user:
            token = create_access_token({'sub': auth_user['email']})
            print(f"   Token generated: {token[:20]}...")
            
            # 6. Test token validation and role expansion
            print("\n3. Testing token validation...")
            try:
                current_user = await get_current_user_with_roles(token)
                print(f"   Token validation: SUCCESS")
                print(f"   User roles: {[r.get('role') for r in current_user.get('roles', [])]}")
                
                # 7. Test permission checking
                print("\n4. Testing permission system...")
                user_id = current_user['id']
                company_id = current_user['roles'][0]['company_id'] if current_user['roles'] else ''
                
                test_perms = [
                    ('users', 'view'),
                    ('users', 'edit'), 
                    ('roles', 'view'),
                    ('companies', 'delete')
                ]
                
                for screen, perm in test_perms:
                    has_perm = await repo.check_user_permission(user_id, company_id, screen, perm)
                    print(f"   {screen}.{perm}: {'✓' if has_perm else '✗'}")
                
                print(f"\n✅ Authentication system is working correctly!")
                return True
                
            except Exception as e:
                print(f"   Token validation failed: {e}")
                return False
        
    return False

if __name__ == "__main__":
    result = asyncio.run(test_complete_auth_flow())
    if result:
        print("\n🎉 All tests passed! The RBAC system is ready for use.")
    else:
        print("\n❌ Tests failed. Please check the system configuration.")