import asyncio
from app.repo import repo
from app.api.init_data import initialize_mock_data

async def test_repo():
    print('Testing repo type...')
    print(f'Repo type: {type(repo)}')
    print(f'Repo: {repo}')

    # Check if it's MongoRepo
    if hasattr(repo, '_db'):
        print('Using MongoRepo')
        print(f'Database: {repo._db.name}')
        collections = await repo._db.list_collection_names()
        print(f'Collections: {collections}')

        # Try to get users
        try:
            users = await repo.list_users()
            print(f'Users found: {len(users)}')
            for user in users:
                print(f'  User: {user.get("email")}')
        except Exception as e:
            print(f'Error getting users: {e}')

        # Try to get roles
        try:
            roles_cursor = repo._role_col.find({})
            roles = []
            async for role in roles_cursor:
                roles.append(role)
            print(f'Roles found: {len(roles)}')
            for role in roles:
                print(f'  Role: {role.get("name")} ({role.get("role_group")})')
        except Exception as e:
            print(f'Error getting roles: {e}')

        # Try to get companies
        try:
            companies_cursor = repo._company_col.find({})
            companies = []
            async for company in companies_cursor:
                companies.append(company)
            print(f'Companies found: {len(companies)}')
            for company in companies:
                print(f'  Company: {company.get("name")}')
        except Exception as e:
            print(f'Error getting companies: {e}')
    else:
        print('Using InMemoryRepo')

asyncio.run(test_repo())
