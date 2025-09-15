#!/usr/bin/env python3

import asyncio
from app.models import ContentMeta
from app.repo import repo

async def test_content_save():
    # Create a test ContentMeta object
    cm = ContentMeta(
        id='test-content-123',
        owner_id='test-user',
        filename='test.jpg',
        content_type='image/jpeg',
        size=1000,
        status='quarantine'
    )
    
    # Save it
    saved = await repo.save_content_meta(cm)
    print('Saved content:', saved)
    
    # List all content
    content_list = await repo.list_content()
    print('Content list count:', len(content_list))
    for content in content_list:
        print('Content:', content.get('id'), content.get('filename'))

if __name__ == "__main__":
    asyncio.run(test_content_save())