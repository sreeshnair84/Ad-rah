#!/usr/bin/env python3
"""
Test authentication directly against the database
"""
import asyncio
import os
import sys

# Set up the path and environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables FIRST
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Environment variables loaded")
except ImportError:
    print("[WARNING] python-dotenv not installed")

from app.repo import repo
from app.auth import verify_password, get_password_hash

async def test_auth():
    """Test authentication debugging"""
    print("🔍 Debugging authentication...")
    
    # Try to get user by email
    email = "admin@openkiosk.com"
    print(f"\n1. Looking for user: {email}")
    
    try:
        user = await repo.get_user_by_email(email)
        if user:
            print(f"   ✓ Found user: {user.get('name', 'Unknown')}")
            print(f"   - Status: {user.get('status', 'Unknown')}")
            print(f"   - Active: {user.get('is_active', 'Unknown')}")
            print(f"   - User Type: {user.get('user_type', 'Unknown')}")
            print(f"   - Email Verified: {user.get('email_verified', 'Unknown')}")
            
            # Test password verification
            print(f"\n2. Testing password verification...")
            test_password = "adminpass"
            stored_hash = user.get("hashed_password")
            
            print(f"   - Test password: {test_password}")
            print(f"   - Stored hash exists: {bool(stored_hash)}")
            if stored_hash:
                print(f"   - Hash starts with: {stored_hash[:20]}...")
            
            # Test verification
            is_valid = verify_password(test_password, stored_hash)
            print(f"   - Password valid: {is_valid}")
            
            # Test creating a new hash for comparison
            print(f"\n3. Testing new hash generation...")
            new_hash = get_password_hash(test_password)
            print(f"   - New hash: {new_hash[:20]}...")
            print(f"   - New hash matches: {verify_password(test_password, new_hash)}")
            
        else:
            print("   ✗ User not found!")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth())
