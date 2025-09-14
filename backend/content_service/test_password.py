#!/usr/bin/env python3
"""
Test password hashing and verification
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.user_service import hash_password, verify_password

def test_password_functions():
    """Test that password hashing and verification work correctly"""
    
    test_password = "HostEditor123!"
    
    print("Testing password functions...")
    print(f"Original password: {test_password}")
    
    # Hash the password
    hashed = hash_password(test_password)
    print(f"Hashed password: {hashed[:50]}...")
    
    # Verify the password
    is_valid = verify_password(test_password, hashed)
    print(f"Password verification: {'✓ PASS' if is_valid else '✗ FAIL'}")
    
    # Test with wrong password
    wrong_is_valid = verify_password("WrongPassword123!", hashed)
    print(f"Wrong password verification: {'✗ FAIL (expected)' if not wrong_is_valid else '✓ PASS (unexpected)'}")
    
    return is_valid and not wrong_is_valid

if __name__ == "__main__":
    success = test_password_functions()
    if success:
        print("\n🎉 Password functions are working correctly!")
    else:
        print("\n❌ Password functions are not working correctly!")
