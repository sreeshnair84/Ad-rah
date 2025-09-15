#!/usr/bin/env python3

import asyncio
from app.repo import repo

async def check_content():
    content = await repo.list_content()
    print(f'Total content in repo: {len(content)}')
    for c in content:
        print(f'  - {c.get("id")}: {c.get("filename")} (owner: {c.get("owner_id")}, status: {c.get("status")})')

if __name__ == "__main__":
    asyncio.run(check_content())