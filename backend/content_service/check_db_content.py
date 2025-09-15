#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.database_service import db_service

async def check_db():
    await db_service.initialize()

    # Check content_meta collection
    content_meta = await db_service.db.content_meta.find({}).to_list(length=None)
    print(f'Content_meta collection has {len(content_meta)} items:')
    for item in content_meta:
        print(f'  - {item.get("title", "No title")} (ID: {item.get("id", "No ID")})')

    # Check content collection
    content = await db_service.db.content.find({}).to_list(length=None)
    print(f'\nContent collection has {len(content)} items:')
    for item in content:
        print(f'  - {item.get("title", "No title")} (ID: {item.get("id", "No ID")})')

    await db_service.close()

if __name__ == "__main__":
    asyncio.run(check_db())