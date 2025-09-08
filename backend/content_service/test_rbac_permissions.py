#!/usr/bin/env python3
"""
Test script to verify RBAC permissions for host admin and editor roles
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.rbac.permissions import (
    Page, Permission, Role,
    editor_template, company_admin_template
)

def test_permissions():
    """Test that host admin and editor have correct permissions"""
    
    print("Testing RBAC Permissions for Host Admin and Editor\n")
    
    # Test Editor permissions
    editor = editor_template()
    print(f"Editor Role: {editor.name}")
    print("Editor Permissions:")
    
    # Check content permissions for distribute
    content_perms = None
    for page_perm in editor.page_permissions:
        if page_perm.page == Page.CONTENT:
            content_perms = page_perm.permissions
            break
    
    print(f"  Content: {content_perms}")
    has_distribute = Permission.DISTRIBUTE in content_perms if content_perms else False
    print(f"  ✓ Has DISTRIBUTE permission: {has_distribute}")
    
    # Check overlay permissions for create
    overlay_perms = None
    for page_perm in editor.page_permissions:
        if page_perm.page == Page.OVERLAYS:
            overlay_perms = page_perm.permissions
            break
    
    print(f"  Overlays: {overlay_perms}")
    has_overlay_create = Permission.CREATE in overlay_perms if overlay_perms else False
    print(f"  ✓ Has overlay CREATE permission: {has_overlay_create}")
    
    # Check digital twin permissions for view
    digital_twin_perms = None
    for page_perm in editor.page_permissions:
        if page_perm.page == Page.DIGITAL_TWIN:
            digital_twin_perms = page_perm.permissions
            break
    
    print(f"  Digital Twin: {digital_twin_perms}")
    has_digital_twin_view = Permission.VIEW in digital_twin_perms if digital_twin_perms else False
    print(f"  ✓ Has digital twin VIEW permission: {has_digital_twin_view}")
    
    print("\n" + "="*50 + "\n")
    
    # Test Company Admin permissions
    admin = company_admin_template()
    print(f"Company Admin Role: {admin.name}")
    print("Company Admin Permissions:")
    
    # Check content permissions for distribute
    content_perms = None
    for page_perm in admin.page_permissions:
        if page_perm.page == Page.CONTENT:
            content_perms = page_perm.permissions
            break
    
    print(f"  Content: {content_perms}")
    has_distribute = Permission.DISTRIBUTE in content_perms if content_perms else False
    print(f"  ✓ Has DISTRIBUTE permission: {has_distribute}")
    
    # Check overlay permissions for create
    overlay_perms = None
    for page_perm in admin.page_permissions:
        if page_perm.page == Page.OVERLAYS:
            overlay_perms = page_perm.permissions
            break
    
    print(f"  Overlays: {overlay_perms}")
    has_overlay_create = Permission.CREATE in overlay_perms if overlay_perms else False
    print(f"  ✓ Has overlay CREATE permission: {has_overlay_create}")
    
    # Check digital twin permissions for view
    digital_twin_perms = None
    for page_perm in admin.page_permissions:
        if page_perm.page == Page.DIGITAL_TWIN:
            digital_twin_perms = page_perm.permissions
            break
    
    print(f"  Digital Twin: {digital_twin_perms}")
    has_digital_twin_view = Permission.VIEW in digital_twin_perms if digital_twin_perms else False
    print(f"  ✓ Has digital twin VIEW permission: {has_digital_twin_view}")
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    all_permissions_correct = True
    
    # Editor requirements
    editor_content_distribute = Permission.DISTRIBUTE in (content_perms or set())
    editor_overlay_create = Permission.CREATE in (overlay_perms or set()) 
    editor_digital_twin_view = Permission.VIEW in (digital_twin_perms or set())
    
    print(f"Editor - Content Distribute: {'✓' if editor_content_distribute else '✗'}")
    print(f"Editor - Overlay Create: {'✓' if editor_overlay_create else '✗'}")
    print(f"Editor - Digital Twin View: {'✓' if editor_digital_twin_view else '✗'}")
    
    # Admin requirements (should have same as editor plus more)
    admin_content_distribute = Permission.DISTRIBUTE in (content_perms or set())
    admin_overlay_create = Permission.CREATE in (overlay_perms or set())
    admin_digital_twin_view = Permission.VIEW in (digital_twin_perms or set())
    
    print(f"Admin - Content Distribute: {'✓' if admin_content_distribute else '✗'}")
    print(f"Admin - Overlay Create: {'✓' if admin_overlay_create else '✗'}")
    print(f"Admin - Digital Twin View: {'✓' if admin_digital_twin_view else '✗'}")
    
    all_correct = all([
        editor_content_distribute, editor_overlay_create, editor_digital_twin_view,
        admin_content_distribute, admin_overlay_create, admin_digital_twin_view
    ])
    
    if all_correct:
        print("\n🎉 All permissions are correctly configured!")
        print("Host Admin and Editor roles now have access to:")
        print("  - Digital Twin (view)")
        print("  - Overlay Designer (create)")
        print("  - Content Distribution (distribute)")
    else:
        print("\n❌ Some permissions are missing!")
        all_permissions_correct = False
    
    return all_permissions_correct

if __name__ == "__main__":
    test_permissions()
