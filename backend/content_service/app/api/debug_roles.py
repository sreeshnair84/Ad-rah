"""
Debug API endpoints for troubleshooting role and authentication issues
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, List, Optional
import logging

from app.models import UserRole, Role
from app.repo import repo
from app.auth import get_current_user_with_roles, verify_password, get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/user-roles/{user_email}")
async def debug_user_roles(user_email: str) -> Dict:
    """Debug endpoint to examine user roles and detect issues"""
    try:
        # Get user by email
        user = await repo.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user.get("id")
        print(f"[DEBUG] Analyzing roles for user: {user_email} (ID: {user_id})")
        
        # Get user roles
        user_roles = await repo.get_user_roles(user_id)
        print(f"[DEBUG] Found {len(user_roles)} user roles")
        
        # Analyze each role
        role_analysis = []
        issues_found = []
        
        for i, user_role in enumerate(user_roles):
            analysis = {
                "index": i,
                "user_role_data": user_role,
                "issues": [],
                "role_details": None,
                "company_details": None
            }
            
            # Check role_id
            role_id = user_role.get("role_id")
            if not role_id:
                analysis["issues"].append("Missing role_id")
                issues_found.append(f"Role {i}: Missing role_id")
            else:
                # Try to get role details
                try:
                    role_details = await repo.get_role(role_id)
                    if role_details:
                        analysis["role_details"] = role_details
                        print(f"[DEBUG] Role {i}: Found role details - {role_details.get('name')}")
                    else:
                        analysis["issues"].append(f"Role not found for ID: {role_id}")
                        issues_found.append(f"Role {i}: Role ID {role_id} not found in database")
                except Exception as e:
                    analysis["issues"].append(f"Error fetching role: {str(e)}")
                    issues_found.append(f"Role {i}: Database error fetching role {role_id}")
            
            # Check company_id
            company_id = user_role.get("company_id")
            if company_id and company_id != "global":
                try:
                    company = await repo.get_company(company_id)
                    if company:
                        analysis["company_details"] = company
                        print(f"[DEBUG] Role {i}: Found company - {company.get('name')}")
                    else:
                        analysis["issues"].append(f"Company not found for ID: {company_id}")
                        issues_found.append(f"Role {i}: Company ID {company_id} not found")
                except Exception as e:
                    analysis["issues"].append(f"Error fetching company: {str(e)}")
                    issues_found.append(f"Role {i}: Database error fetching company {company_id}")
            
            role_analysis.append(analysis)
        
        # Check what would happen with current auth logic
        try:
            user_with_roles = await get_current_user_with_roles(user_email, bypass_token=True)
            auth_result = {
                "roles_count": len(user_with_roles.get("roles", [])),
                "computed_roles": user_with_roles.get("roles", []),
                "companies_count": len(user_with_roles.get("companies", []))
            }
        except Exception as e:
            auth_result = {
                "error": f"Auth processing failed: {str(e)}"
            }
        
        return {
            "success": True,
            "user_email": user_email,
            "user_id": user_id,
            "raw_user_roles_count": len(user_roles),
            "issues_found": issues_found,
            "has_issues": len(issues_found) > 0,
            "role_analysis": role_analysis,
            "auth_processing_result": auth_result,
            "recommendations": generate_recommendations(issues_found, role_analysis)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug user roles error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

def generate_recommendations(issues: List[str], analysis: List[Dict]) -> List[str]:
    """Generate recommendations based on found issues"""
    recommendations = []
    
    if any("Missing role_id" in issue for issue in issues):
        recommendations.append("Fix user roles with missing role_id by assigning proper roles")
    
    if any("Role ID" in issue and "not found" in issue for issue in issues):
        recommendations.append("Clean up orphaned user roles or recreate missing role records")
    
    if any("Company ID" in issue and "not found" in issue for issue in issues):
        recommendations.append("Fix company references or remove invalid user roles")
    
    # Check for users without proper roles
    valid_roles = [a for a in analysis if not a["issues"]]
    if not valid_roles:
        recommendations.append("User has no valid roles - assign at least one working role")
    
    if not recommendations:
        recommendations.append("No issues detected - roles appear to be properly configured")
    
    return recommendations

@router.post("/fix-user-roles/{user_email}")
async def fix_user_roles(user_email: str) -> Dict:
    """Attempt to fix common role issues for a user"""
    try:
        # Get user
        user = await repo.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user.get("id")
        fixes_applied = []
        
        # Get current user roles
        user_roles = await repo.get_user_roles(user_id)
        
        for user_role in user_roles:
            role_id = user_role.get("role_id")
            company_id = user_role.get("company_id")
            
            # Fix missing role_id by finding default role for company
            if not role_id and company_id:
                try:
                    default_roles = await repo.get_default_roles_by_company(company_id)
                    if default_roles:
                        # Update user role with default role_id
                        user_role_id = user_role.get("id")
                        await repo.delete_user_role(user_role_id)
                        
                        # Create new user role with proper role_id
                        new_user_role = UserRole(
                            user_id=user_id,
                            company_id=company_id,
                            role_id=default_roles[0]["id"],
                            is_default=True,
                            status="active"
                        )
                        await repo.save_user_role(new_user_role)
                        fixes_applied.append(f"Fixed missing role_id for company {company_id}")
                except Exception as e:
                    logger.error(f"Failed to fix role_id for {user_role}: {e}")
        
        return {
            "success": True,
            "user_email": user_email,
            "fixes_applied": fixes_applied,
            "message": f"Applied {len(fixes_applied)} fixes" if fixes_applied else "No fixes needed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fix user roles error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fix failed: {str(e)}")

@router.get("/system-roles")
async def debug_system_roles() -> Dict:
    """Debug endpoint to examine all roles in the system"""
    try:
        # Get all roles
        all_companies = await repo.list_companies()
        admin_roles = await repo.list_roles_by_group("ADMIN")
        host_roles = await repo.list_roles_by_group("HOST") 
        advertiser_roles = await repo.list_roles_by_group("ADVERTISER")
        
        return {
            "success": True,
            "summary": {
                "total_companies": len(all_companies),
                "admin_roles": len(admin_roles),
                "host_roles": len(host_roles),
                "advertiser_roles": len(advertiser_roles)
            },
            "companies": all_companies,
            "roles_by_group": {
                "ADMIN": admin_roles,
                "HOST": host_roles,
                "ADVERTISER": advertiser_roles
            }
        }
        
    except Exception as e:
        logger.error(f"Debug system roles error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

@router.post("/test-auth/{user_email}")
async def test_user_authentication(user_email: str, password: str) -> Dict:
    """Test user authentication and role resolution"""
    try:
        # Test authentication
        user_data = await repo.get_user_by_email(user_email)
        if not user_data:
            return {"success": False, "error": "User not found"}
        
        # Test password
        password_valid = verify_password(password, user_data.get("hashed_password", ""))
        
        # Test role resolution
        try:
            user_with_roles = await get_current_user_with_roles(user_email, bypass_token=True)
            role_resolution_success = True
            role_error = None
        except Exception as e:
            role_resolution_success = False
            role_error = str(e)
            user_with_roles = None
        
        return {
            "success": True,
            "user_found": True,
            "password_valid": password_valid,
            "role_resolution_success": role_resolution_success,
            "role_error": role_error,
            "user_with_roles": user_with_roles,
            "roles_count": len(user_with_roles.get("roles", [])) if user_with_roles else 0
        }
        
    except Exception as e:
        logger.error(f"Test auth error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# Bypass token checking for debug endpoints
async def get_current_user_with_roles(username: str, bypass_token: bool = False):
    """Helper to get user with roles, bypassing token check for debug"""
    if bypass_token:
        # Direct database lookup for debugging
        user_data = await repo.get_user_by_email(username)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process roles the same way as normal auth
        from app.auth import get_current_user_with_roles as auth_get_user
        # We'll need to mock the token verification, but for now let's use the logic
        user_roles = await repo.get_user_roles(user_data["id"])
        
        # Simulate the role expansion logic from auth.py
        companies = []
        for role in user_roles:
            company_id = role.get("company_id")
            if company_id and company_id != "global":
                try:
                    company = await repo.get_company(company_id)
                    if company:
                        companies.append(company)
                except Exception:
                    pass
        
        user_data["companies"] = companies
        
        # Expand roles
        expanded_roles = []
        for user_role in user_roles:
            role_id = user_role.get("role_id")
            if role_id:
                try:
                    role = await repo.get_role(role_id)
                    if role:
                        expanded_role = {
                            **user_role,
                            "role": role.get("role_group"),
                            "role_name": role.get("name"),
                            "role_details": role
                        }
                        expanded_roles.append(expanded_role)
                except Exception:
                    # Apply the new fallback logic
                    company_id = user_role.get("company_id")
                    if company_id and company_id != "global":
                        fallback_role = "HOST"
                        fallback_name = "Host Manager"
                    else:
                        fallback_role = "USER"
                        fallback_name = "User"
                    
                    expanded_roles.append({
                        **user_role,
                        "role": fallback_role,
                        "role_name": fallback_name
                    })
        
        user_data["roles"] = expanded_roles
        return user_data
    else:
        # Use normal auth flow
        from app.auth import get_current_user_with_roles as auth_get_user
        return await auth_get_user(username)