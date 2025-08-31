import asyncio
from app.repo import repo
from app.auth import init_default_data

async def init_and_check():
    try:
        print('Initializing data...')
        await init_default_data()

        print('\nChecking stores after initialization:')
        if hasattr(repo, '_store'):
            for key, value in repo._store.items():
                print(f'{key}: {len(value)} items')
                if len(value) > 0 and key == '__roles__':
                    print('Roles:')
                    for role_id, role in value.items():
                        print(f'  {role_id}: {role}')
                elif len(value) > 0 and key == '__user_roles__':
                    print('User Roles:')
                    for ur_id, ur in value.items():
                        print(f'  {ur_id}: user={ur.get("user_id")}, role={ur.get("role_id")}')

        # Test role lookup
        print('\nTesting role lookup:')
        role = await repo.get_role('2-r')
        print(f'get_role("2-r"): {role}')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(init_and_check())
