#!/usr/bin/env python3

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def check_content_meta_data():
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/openkiosk')

    try:
        client = AsyncIOMotorClient(mongo_uri, maxPoolSize=10, serverSelectionTimeoutMS=5000)
        db = client.openkiosk

        # Query content_meta collection
        content_meta_collection = db.content_meta
        cursor = content_meta_collection.find({})
        content_meta_docs = await cursor.to_list(length=None)

        print(f"Found {len(content_meta_docs)} documents in content_meta collection:")
        print("=" * 50)

        for i, doc in enumerate(content_meta_docs, 1):
            print(f"Document {i}:")
            # Convert ObjectId to string for JSON serialization
            doc['_id'] = str(doc['_id'])
            print(json.dumps(doc, indent=2, default=str))
            print("-" * 30)

        # Also check content_metadata collection if it exists
        if 'content_metadata' in await db.list_collection_names():
            print("\nAlso checking content_metadata collection:")
            content_metadata_collection = db.content_metadata
            cursor = content_metadata_collection.find({})
            content_metadata_docs = await cursor.to_list(length=None)

            print(f"Found {len(content_metadata_docs)} documents in content_metadata collection:")
            for i, doc in enumerate(content_metadata_docs, 1):
                print(f"Document {i}:")
                doc['_id'] = str(doc['_id'])
                print(json.dumps(doc, indent=2, default=str))
                print("-" * 30)

        # Check content collection
        if 'content' in await db.list_collection_names():
            print("\nAlso checking content collection:")
            content_collection = db.content
            cursor = content_collection.find({})
            content_docs = await cursor.to_list(length=None)

            print(f"Found {len(content_docs)} documents in content collection:")
            for i, doc in enumerate(content_docs, 1):
                print(f"Document {i}:")
                doc['_id'] = str(doc['_id'])
                print(json.dumps(doc, indent=2, default=str))
                print("-" * 30)

        client.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_content_meta_data())