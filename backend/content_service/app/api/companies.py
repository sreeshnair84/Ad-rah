from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.models import Company
from app.repo import repo
from app.api.auth import get_current_user
from app.rbac_models import UserProfile, UserType

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=List[Company])
@router.get("", response_model=List[Company])  # Add route without trailing slash
async def list_companies(current_user: UserProfile = Depends(get_current_user)):
    """List companies accessible to the current user"""
    
    try:
        print(f"[COMPANIES] INFO: User {current_user.email} requesting companies list")
        print(f"[COMPANIES] DEBUG: User type: {current_user.user_type}, Company ID: {current_user.company_id}")
        
        # For SUPER_USER, return all companies
        if current_user.user_type == UserType.SUPER_USER:
            print(f"[COMPANIES] DEBUG: Super user, fetching all companies")
            companies = await repo.list_companies()
        else:
            # For regular users, return only their company
            user_company_id = current_user.company_id
            print(f"[COMPANIES] DEBUG: Regular user, fetching company: {user_company_id}")
            if user_company_id:
                try:
                    print(f"[COMPANIES] DEBUG: About to call repo.get_company({user_company_id})")
                    company = await repo.get_company(user_company_id)
                    print(f"[COMPANIES] DEBUG: repo.get_company returned: {company}")
                    if company:
                        print(f"[COMPANIES] DEBUG: Successfully fetched company: {company.get('name', 'Unknown')}")
                        companies = [company]
                    else:
                        print(f"[COMPANIES] WARNING: Company with ID {user_company_id} not found in database")
                        companies = []
                except Exception as e:
                    print(f"[COMPANIES] ERROR: Failed to fetch company {user_company_id}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    companies = []
            else:
                print(f"[COMPANIES] WARNING: User has no company_id assigned")
                companies = []
        
        print(f"[COMPANIES] INFO: Found {len(companies)} companies for user {current_user.email}")
        
        # Convert ObjectId to string and ensure proper serialization
        for company in companies:
            if "_id" in company:
                company["id"] = str(company["_id"])
                del company["_id"]
            # Handle field name mapping - database uses company_type, model uses type
            if "company_type" in company:
                company["type"] = company["company_type"]
                del company["company_type"]
            # Ensure datetime fields are properly serialized
            if "created_at" in company and hasattr(company["created_at"], 'isoformat'):
                company["created_at"] = company["created_at"].isoformat()
            if "updated_at" in company and hasattr(company["updated_at"], 'isoformat'):
                company["updated_at"] = company["updated_at"].isoformat()
        
        # Create Company objects to ensure proper validation and serialization
        return [Company(**company) for company in companies]
        
    except Exception as e:
        print(f"[COMPANIES] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")


@router.get("/{company_id}", response_model=Company)
async def get_company(company_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get a specific company by ID"""
    
    try:
        company = await repo.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Check access permissions
        if current_user.user_type != UserType.SUPER_USER:
            user_company_id = current_user.company_id
            if user_company_id != company_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert ObjectId to string and handle field mapping
        if "_id" in company:
            company["id"] = str(company["_id"])
            del company["_id"]
        # Handle field name mapping - database uses company_type, model uses type
        if "company_type" in company:
            company["type"] = company["company_type"]
            del company["company_type"]
        
        return Company(**company)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")
