from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Dict, Optional
from datetime import datetime

from app.models import (
    CompanyApplication, 
    CompanyApplicationCreate, 
    CompanyApplicationReview, 
    CompanyApplicationStatus,
    CompanyType,
    Company,
    User,
    Role,
    UserRole
)
from app.repo import repo
from app.api.auth import get_current_user
# from app.services.auth_service import AuthService  # Removed - unused import
from app.auth import get_password_hash  # Import password hashing function

router = APIRouter(prefix="/company-applications", tags=["company-applications"])


def convert_objectid_to_str(data):
    """Recursively convert ObjectId instances to strings in a data structure"""
    if hasattr(data, '__dict__') and hasattr(data, 'get'):  # dict-like object
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    else:
        # Try to convert ObjectId to string, fallback to original data
        try:
            from bson import ObjectId
            if isinstance(data, ObjectId):
                return str(data)
        except ImportError:
            pass
        return data


@router.post("/", response_model=Dict)
async def submit_company_application(application_data: CompanyApplicationCreate):
    """Submit a new company application (public endpoint)"""
    try:
        # Check if company name already exists
        existing_companies = await repo.list_companies()
        if any(c.get("name", "").lower() == application_data.company_name.lower() 
               for c in existing_companies):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A company with this name already exists"
            )
        
        # Check if applicant email already exists
        existing_applications = await repo.list_company_applications()
        if any(app.get("applicant_email", "").lower() == application_data.applicant_email.lower() 
               and app.get("status") in ["pending", "under_review"]
               for app in existing_applications):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An application from this email address is already pending"
            )
        
        # Create application
        application = CompanyApplication(**application_data.model_dump())
        saved_application = await repo.save_company_application(application)
        
        return {
            "message": "Application submitted successfully",
            "application_id": saved_application["id"],
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {str(e)}"
        )


@router.get("/", response_model=List[Dict])
@router.get("", response_model=List[Dict])  # Add route without trailing slash
async def list_company_applications(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    company_type: Optional[str] = Query(None, description="Filter by company type"),
    current_user: dict = Depends(get_current_user)
):
    """List company applications (Admin only)"""
    try:
        print(f"[COMPANY_APPS] INFO: User {current_user.get('email')} requesting company applications list")
        print(f"[COMPANY_APPS] DEBUG: Current user type: {current_user.get('user_type')}")
        
        # Check if user has SUPER_USER access (new authentication system)
        user_type = current_user.get("user_type", "")
        is_admin = user_type == "SUPER_USER"
        
        print(f"[COMPANY_APPS] DEBUG: Is admin: {is_admin}")
        
        if not is_admin:
            print(f"[COMPANY_APPS] WARNING: User {current_user.get('email')} denied company applications access - insufficient permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view company applications"
            )
        
        print("[COMPANY_APPS] INFO: User has admin permissions, proceeding with application listing")
        
        applications = await repo.list_company_applications(status=status_filter, company_type=company_type)
        print(f"[COMPANY_APPS] INFO: Retrieved {len(applications)} applications for user {current_user.get('email')}")
        
        return [convert_objectid_to_str(app) for app in applications]
        
    except HTTPException:
        print("[COMPANY_APPS] ERROR: HTTPException raised")
        raise
    except Exception as e:
        print(f"[COMPANY_APPS] ERROR: Failed to fetch applications: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch applications: {str(e)}"
        )


@router.get("/{application_id}", response_model=Dict)
async def get_company_application(
    application_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific company application details (Admin only)"""
    try:
        # Check if user has SUPER_USER access (new authentication system)
        user_type = current_user.get("user_type", "")
        is_admin = user_type == "SUPER_USER"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view company applications"
            )
        
        application = await repo.get_company_application(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        return convert_objectid_to_str(application)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch application: {str(e)}"
        )


@router.put("/{application_id}/review", response_model=Dict)
async def review_company_application(
    application_id: str,
    review_data: CompanyApplicationReview,
    current_user: dict = Depends(get_current_user)
):
    """Review and approve/reject company application (Admin only)"""
    try:
        # Check if user has ADMIN role
        # Check if user has SUPER_USER access (new authentication system)
        user_type = current_user.get("user_type", "")
        is_admin = user_type == "SUPER_USER"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can review applications"
            )
        
        # Check if application exists
        application = await repo.get_company_application(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check if application can be reviewed
        if application.get("status") not in ["pending", "under_review"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application has already been reviewed"
            )
        
        # Update application status
        new_status = "approved" if review_data.decision == "approved" else "rejected"
        await repo.update_company_application_status(
            application_id=application_id,
            status=new_status,
            reviewer_id=current_user["id"],
            notes=review_data.notes or ""
        )
        
        # If approved, create company and admin user
        if review_data.decision == "approved":
            await _create_company_and_user(application, current_user["id"])
        
        return {
            "message": f"Application {review_data.decision} successfully",
            "status": new_status,
            "reviewer_id": current_user["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review application: {str(e)}"
        )


async def _create_company_and_user(application: dict, reviewer_id: str):
    """Helper function to create company and admin user after approval"""
    try:
        # Create company
        company = Company(
            name=application["company_name"],
            type=application["company_type"],
            address=application["address"],
            city=application["city"],
            country=application["country"],
            phone=application["applicant_phone"],
            email=application["applicant_email"],
            website=application.get("website"),
            status="active"
        )
        
        saved_company = await repo.save_company(company)
        company_id = saved_company["id"]
        
        # Create admin user for the company
        # Generate temporary password (should be sent via email in production)
        temp_password = f"temp_{application['applicant_email'][:5]}123!"
        
        user = User(
            name=application["applicant_name"],
            email=application["applicant_email"],
            phone=application["applicant_phone"],
            hashed_password=get_password_hash(temp_password),
            status="active",
            email_verified=True
        )
        
        saved_user = await repo.save_user(user)
        user_id = saved_user["id"]
        
        # Create default admin role for the company
        from app.models import RoleGroup
        role_group = RoleGroup.HOST if application["company_type"] == "HOST" else RoleGroup.ADVERTISER
        
        role = Role(
            name=f"{application['company_type'].title()} Administrator",
            role_group=role_group,
            company_id=company_id,
            is_default=True,
            status="active"
        )
        
        saved_role = await repo.save_role(role)
        role_id = saved_role["id"]
        
        # Assign role to user
        user_role = UserRole(
            user_id=user_id,
            company_id=company_id,
            role_id=role_id,
            is_default=True,
            status="active"
        )
        
        await repo.save_user_role(user_role)
        
        # Update application with created entities
        await repo.update_company_application(
            application_id=application["id"],
            updates={
                "created_company_id": company_id,
                "created_user_id": user_id
            }
        )
        
        # TODO: Send email with login credentials
        print(f"Company created: {company_id}")
        print(f"Admin user created: {user_id} with temporary password: {temp_password}")
        
    except Exception as e:
        print(f"Error creating company and user: {e}")
        # TODO: Implement rollback mechanism
        raise


@router.get("/stats/summary", response_model=Dict)
async def get_application_stats(current_user: dict = Depends(get_current_user)):
    """Get application statistics (Admin only)"""
    try:
        # Check if user has SUPER_USER access (new authentication system)
        user_type = current_user.get("user_type", "")
        is_admin = user_type == "SUPER_USER"
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view application statistics"
            )
        
        all_applications = await repo.list_company_applications()
        
        stats = {
            "total": len(all_applications),
            "pending": len([app for app in all_applications if app.get("status") == "pending"]),
            "under_review": len([app for app in all_applications if app.get("status") == "under_review"]),
            "approved": len([app for app in all_applications if app.get("status") == "approved"]),
            "rejected": len([app for app in all_applications if app.get("status") == "rejected"]),
            "host_applications": len([app for app in all_applications if app.get("company_type") == "HOST"]),
            "advertiser_applications": len([app for app in all_applications if app.get("company_type") == "ADVERTISER"])
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch application statistics: {str(e)}"
        )