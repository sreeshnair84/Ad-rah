import asyncio
from app.repo import repo

async def check_role_lookup():
    try:
        # Check if roles exist
        if hasattr(repo, '_store'):
            roles_store = repo._store.get('__roles__', {})
            print('Roles in store:')
            for role_id, role in roles_store.items():
                print(f'  Key: {role_id}, Value: {role}')

        # Try to get role 2-r
        role = await repo.get_role('2-r')
        print(f'\nget_role("2-r") result: {role}')

        # Check the exact key in the store
        if hasattr(repo, '_store'):
            roles_store = repo._store.get('__roles__', {})
            print(f'\nDirect access to __roles__["2-r"]: {roles_store.get("2-r")}')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_role_lookup())
