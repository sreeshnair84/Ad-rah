#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from app.repo import repo

async def test_repo_directly():
    """Test the repository methods directly"""
    
    print("TESTING REPOSITORY METHODS DIRECTLY")
    print("=" * 50)
    
    try:
        # Test list_companies
        print("1. Testing list_companies()...")
        companies = await repo.list_companies()
        print(f"✅ Found {len(companies)} companies:")
        for company in companies:
            print(f"   - ID: {company.get('_id')}, Name: {company.get('name')}")
        
        # Test get_company with the specific ID
        print("\n2. Testing get_company('company_host_dubai_mall')...")
        company = await repo.get_company('company_host_dubai_mall')
        if company:
            print(f"✅ Found company: {company.get('name')}")
            print(f"   Company data: {company}")
        else:
            print("❌ Company not found")
        
        # Test with the ID as it appears in the list
        if companies:
            first_company_id = companies[0].get('_id')
            print(f"\n3. Testing get_company('{first_company_id}')...")
            company2 = await repo.get_company(first_company_id)
            if company2:
                print(f"✅ Found company by first ID: {company2.get('name')}")
            else:
                print(f"❌ Company not found by first ID: {first_company_id}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_repo_directly())
