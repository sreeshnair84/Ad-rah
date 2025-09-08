#!/usr/bin/env python3
"""
Test the updated user service with RBAC permissions
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.rbac.permissions import (
    Page, Permission, Role,
    editor_template, company_admin_template
)
from app.services.user_service import convert_permissions_to_frontend_format

def test_permission_conversion():
    """Test that RBAC permissions are correctly converted to frontend format"""
    
    print("Testing Permission Conversion to Frontend Format\n")
    
    # Test Editor permissions
    editor = editor_template()
    print(f"Editor Role: {editor.name}")
    editor_frontend_perms = convert_permissions_to_frontend_format(editor.page_permissions)
    
    print("Editor Frontend Permissions:")
    for perm in sorted(editor_frontend_perms):
        print(f"  - {perm}")
    
    # Check for the specific permissions frontend expects
    required_editor_perms = ["content_distribute", "overlay_create", "digital_twin_view"]
    print(f"\nRequired Frontend Permissions for Editor:")
    for perm in required_editor_perms:
        has_perm = perm in editor_frontend_perms
        print(f"  - {perm}: {'✓' if has_perm else '✗'}")
    
    print("\n" + "="*60 + "\n")
    
    # Test Company Admin permissions
    admin = company_admin_template()
    print(f"Company Admin Role: {admin.name}")
    admin_frontend_perms = convert_permissions_to_frontend_format(admin.page_permissions)
    
    print("Company Admin Frontend Permissions:")
    for perm in sorted(admin_frontend_perms):
        print(f"  - {perm}")
    
    # Check for the specific permissions frontend expects
    required_admin_perms = ["content_distribute", "overlay_create", "digital_twin_view"]
    print(f"\nRequired Frontend Permissions for Company Admin:")
    for perm in required_admin_perms:
        has_perm = perm in admin_frontend_perms
        print(f"  - {perm}: {'✓' if has_perm else '✗'}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    editor_success = all(perm in editor_frontend_perms for perm in required_editor_perms)
    admin_success = all(perm in admin_frontend_perms for perm in required_admin_perms)
    
    print(f"Editor has all required permissions: {'✓' if editor_success else '✗'}")
    print(f"Admin has all required permissions: {'✓' if admin_success else '✗'}")
    
    if editor_success and admin_success:
        print("\n🎉 SUCCESS: Both roles have the required frontend permissions!")
        print("The frontend sidebar should now show:")
        print("  - Digital Twin (digital_twin_view)")
        print("  - Overlay Designer (overlay_create)")
        print("  - Content Distribution (content_distribute)")
        print("\nFor both Host Admin and Editor roles.")
    else:
        print("\n❌ FAILED: Some required permissions are missing.")
    
    return editor_success and admin_success

if __name__ == "__main__":
    test_permission_conversion()
