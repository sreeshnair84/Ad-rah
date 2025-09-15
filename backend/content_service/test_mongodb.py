#!/usr/bin/env python3

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mongodb_connection():
    # Check environment variable
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/openkiosk')
    print(f"MONGO_URI: {mongo_uri}")
    
    try:
        # Try to connect
        client = AsyncIOMotorClient(mongo_uri, maxPoolSize=10, serverSelectionTimeoutMS=5000)
        print("Created MongoDB client")
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # List databases
        db_list = await client.list_database_names()
        print(f"Available databases: {db_list}")
        
        # Test our database
        db = client.openkiosk
        collections = await db.list_collection_names()
        print(f"Collections in 'openkiosk' database: {collections}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("Make sure MongoDB is running on localhost:27017")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())