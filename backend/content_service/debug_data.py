#!/usr/bin/env python3
"""
Debug and fix data integrity issues
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.repo import repo
from app.auth import init_default_data

async def check_data_integrity():
    """Check current data state"""
    print("=== DATA INTEGRITY CHECK ===")
    
    # Check what type of repo we're using
    if hasattr(repo, '_store'):
        print("Using InMemoryRepo")
        
        # Check users
        users = repo._store.get("__users__", {})
        print(f"Users: {len(users)}")
        for user_id, user_data in users.items():
            print(f"  {user_id}: {user_data.get('email')} - {user_data.get('name')}")
        
        # Check companies  
        companies = repo._store.get("__companies__", {})
        print(f"Companies: {len(companies)}")
        for comp_id, comp_data in companies.items():
            print(f"  {comp_id}: {comp_data.get('name')} - {comp_data.get('type')}")
        
        # Check roles
        roles = repo._store.get("__roles__", {})
        print(f"Roles: {len(roles)}")
        for role_id, role_data in roles.items():
            print(f"  {role_id}: {role_data.get('name')} - {role_data.get('role_group')} - Company: {role_data.get('company_id')}")
        
        # Check user roles
        user_roles = repo._store.get("__user_roles__", {})
        print(f"User Roles: {len(user_roles)}")
        for ur_id, ur_data in user_roles.items():
            print(f"  {ur_id}: User {ur_data.get('user_id')} -> Role {ur_data.get('role_id')} @ Company {ur_data.get('company_id')}")
            
    else:
        print("Using MongoRepo - would need async iteration")

async def fix_data():
    """Reinitialize data"""
    print("\n=== FIXING DATA ===")
    
    if hasattr(repo, '_store'):
        print("Clearing existing InMemory data...")
        repo._store.clear()
    
    print("Reinitializing default data...")
    await init_default_data()
    
    print("Data reinitialized!")

async def main():
    print("Data Debug Script")
    print("-" * 50)
    
    # Check current state
    await check_data_integrity()
    
    # Ask if we should fix
    fix_choice = input("\nDo you want to reinitialize the data? (y/n): ")
    if fix_choice.lower() == 'y':
        await fix_data()
        print("\nChecking data after fix:")
        await check_data_integrity()
    
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())