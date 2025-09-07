#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.repo import repo

async def test_repo_companies():
    """Test the repo.list_companies method directly"""
    print("TESTING REPO.LIST_COMPANIES() METHOD")
    print("=" * 50)
    
    try:
        # Test repo.list_companies method
        companies = await repo.list_companies()
        print(f"Found {len(companies)} companies:")
        
        for company in companies:
            print(f"Company data:")
            for key, value in company.items():
                print(f"  {key}: {value}")
            print("-" * 30)
        
        # Test specific company lookup like the device endpoint does
        target_company_id = "company_host_dubai_mall"
        company = next((c for c in companies if c.get("id") == target_company_id), None)
        
        if company:
            print(f"✅ Found company with ID '{target_company_id}':")
            print(f"   Name: {company.get('name')}")
            print(f"   Type: {company.get('type')}")
        else:
            print(f"❌ Could not find company with ID '{target_company_id}'")
            print("Available IDs:")
            for c in companies:
                print(f"   - {c.get('id')} (all keys: {list(c.keys())})")
    
    except Exception as e:
        print(f"Error testing repo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_repo_companies())
