#!/usr/bin/env python3
"""
Fix data integrity issues - reinitialize default data
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.repo import repo
from app.auth import init_default_data

async def fix_data():
    """Check and fix data"""
    print("=== DATA FIX SCRIPT ===")
    
    # Check current state
    if hasattr(repo, '_store'):
        print("Using InMemoryRepo")
        users_count = len(repo._store.get("__users__", {}))
        companies_count = len(repo._store.get("__companies__", {}))
        roles_count = len(repo._store.get("__roles__", {}))
        
        print(f"Current data: Users={users_count}, Companies={companies_count}, Roles={roles_count}")
        
        if users_count == 0 or companies_count == 0 or roles_count == 0:
            print("Data is missing - reinitializing...")
            
            # Clear any partial data
            repo._store.clear()
            
            # Initialize default data
            await init_default_data()
            
            # Check after fix
            users_count = len(repo._store.get("__users__", {}))
            companies_count = len(repo._store.get("__companies__", {}))
            roles_count = len(repo._store.get("__roles__", {}))
            
            print(f"After fix: Users={users_count}, Companies={companies_count}, Roles={roles_count}")
            
            # Display sample data
            print("\nSample users:")
            for user_id, user_data in repo._store.get("__users__", {}).items():
                print(f"  {user_data.get('email')} - {user_data.get('name')}")
                
            print("\nSample companies:")
            for comp_id, comp_data in repo._store.get("__companies__", {}).items():
                print(f"  {comp_data.get('name')} ({comp_data.get('type')})")
                
            print("\nSample roles:")  
            for role_id, role_data in repo._store.get("__roles__", {}).items():
                print(f"  {role_data.get('name')} - {role_data.get('role_group')}")
            
            print("\nData initialization completed successfully!")
        else:
            print("Data looks good - no fix needed.")
    else:
        print("Using MongoRepo - not handled by this script")

if __name__ == "__main__":
    asyncio.run(fix_data())