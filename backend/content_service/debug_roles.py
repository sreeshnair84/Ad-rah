import asyncio
from app.repo import repo

async def check_roles():
    try:
        # Get all roles from the store
        if hasattr(repo, '_store'):
            roles_store = repo._store.get("__roles__", {})
            print('All roles in database:')
            for role_id, role in roles_store.items():
                print(f'  ID: {role_id}, Name: {role.get("name")}, Group: {role.get("role_group")}, Company: {role.get("company_id")}')

        # Try to get specific role
        specific_role = await repo.get_role('2-r')
        print(f'\nRole with ID "2-r": {specific_role}')

        # Check user roles
        user_roles = await repo.get_user_roles('68b4537b942ea9111ea9ee68')
        print(f'\nUser roles for host user:')
        for ur in user_roles:
            print(f'  User Role: {ur}')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_roles())