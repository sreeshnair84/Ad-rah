import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.repo import repo
from app.auth import init_default_data

async def check_data():
    # Initialize data first
    await init_default_data()
    
    # Now check what we have
    users = await repo.list_users()
    print(f'Users: {len(users)}')
    for user in users:
        user_id = user.get('id')
        if user_id:
            roles = await repo.get_user_roles(user_id)
            print(f'User: {user.get("email")}, roles: {len(roles)}')
            for role in roles:
                print(f'  Role: company_id={role.get("company_id")}, role_id={role.get("role_id")}')
    
    companies = await repo.list_companies()
    print(f'Companies: {len(companies)}')
    
    all_roles = await repo.list_roles()
    print(f'Roles: {len(all_roles)}')
    for role in all_roles:
        print(f'  Role: id={role.get("id")}, name={role.get("name")}, role_group={role.get("role_group")}, company_id={role.get("company_id")}')

if __name__ == "__main__":
    asyncio.run(check_data())
