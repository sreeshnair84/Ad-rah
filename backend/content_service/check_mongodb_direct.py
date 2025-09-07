#!/usr/bin/env python3

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_mongodb_directly():
    """Check MongoDB database directly for registration keys"""
    
    print("CHECKING MONGODB DIRECTLY")
    print("=" * 50)
    
    # Connect to MongoDB directly
    mongo_uri = "mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin"
    
    try:
        client = AsyncIOMotorClient(mongo_uri)
        db = client.openkiosk
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        
        # Check device_registration_keys collection
        keys_collection = db.device_registration_keys
        keys_count = await keys_collection.count_documents({})
        print(f"📋 Found {keys_count} device registration keys in MongoDB")
        
        if keys_count > 0:
            print("\nRegistration keys in database:")
            async for key in keys_collection.find():
                print(f"  - Key: {key.get('key', 'N/A')[:8]}...")
                print(f"    ID: {key.get('id', 'N/A')}")
                print(f"    Company ID: {key.get('company_id', 'N/A')}")
                print(f"    Used: {key.get('used', 'N/A')}")
                print(f"    Created: {key.get('created_at', 'N/A')}")
                print("-" * 30)
        
        # Check companies collection
        companies_collection = db.companies
        companies_count = await companies_collection.count_documents({})
        print(f"\n🏢 Found {companies_count} companies in MongoDB")
        
        if companies_count > 0:
            print("\nCompanies in database:")
            async for company in companies_collection.find():
                print(f"  - Name: {company.get('name', 'N/A')}")
                print(f"    ID: {company.get('_id', 'N/A')}")
                print(f"    Type: {company.get('company_type', 'N/A')}")
                print("-" * 30)
        
        client.close()
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")

if __name__ == "__main__":
    asyncio.run(check_mongodb_directly())
