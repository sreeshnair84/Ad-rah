import asyncio
from app.auth import init_default_data
from app.repo import repo

async def test_init():
    try:
        print('Before initialization:')
        if hasattr(repo, '_store'):
            roles = repo._store.get('__roles__', {})
            users = repo._store.get('__users__', {})
            print(f'  Roles: {len(roles)}')
            print(f'  Users: {len(users)}')

        print('\nRunning init_default_data...')
        await init_default_data()

        print('\nAfter initialization:')
        if hasattr(repo, '_store'):
            roles = repo._store.get('__roles__', {})
            users = repo._store.get('__users__', {})
            print(f'  Roles: {len(roles)}')
            for role_id, role in roles.items():
                print(f'    {role_id}: {role.get("name")} ({role.get("role_group")})')
            print(f'  Users: {len(users)}')
            for user_id, user in users.items():
                print(f'    {user_id}: {user.get("email")}')

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_init())
