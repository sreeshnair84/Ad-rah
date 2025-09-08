import asyncio
from app.repo import repo

async def check_data():
    companies = await repo.list_companies()
    keys = await repo.list_device_registration_keys()

    print(f'Companies: {len(companies)}')
    for c in companies:
        print(f'  Company ID: {c.get("id")}')
        print(f'  Company Name: {c.get("name")}')
        print(f'  Organization Code: {c.get("organization_code")}')

    print(f'Registration Keys: {len(keys)}')
    for k in keys:
        print(f'  Key: {k.get("key")}')
        print(f'  Company ID: {k.get("company_id")}')
        print(f'  Used: {k.get("used")}')

    # Test key lookup
    test_key = await repo.get_device_registration_key('test-key-123')
    print(f'Key lookup result: {test_key}')

if __name__ == "__main__":
    asyncio.run(check_data())
