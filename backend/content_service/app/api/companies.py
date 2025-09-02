from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.models import Company
from app.database import get_db_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=List[Company])
@router.get("", response_model=List[Company])  # Add route without trailing slash
async def list_companies(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List companies accessible to the current user"""
    
    try:
        db = get_db_service()
        
        # For SUPER_USER, return all companies
        if current_user.get("user_type") == "SUPER_USER":
            companies_result = await db.list_records("companies")
            companies = companies_result.data if companies_result.success else []
        else:
            # For regular users, return only their companies
            user_company_id = current_user.get("company_id")
            if user_company_id:
                company_result = await db.get_record("companies", user_company_id)
                companies = [company_result.data] if company_result.success else []
            else:
                companies = []
        
        # Convert ObjectId to string and ensure proper serialization
        for company in companies:
            if "_id" in company:
                company["id"] = str(company["_id"])
                del company["_id"]
            # Ensure datetime fields are properly serialized
            if "created_at" in company and hasattr(company["created_at"], 'isoformat'):
                company["created_at"] = company["created_at"].isoformat()
            if "updated_at" in company and hasattr(company["updated_at"], 'isoformat'):
                company["updated_at"] = company["updated_at"].isoformat()
        
        # Create Company objects to ensure proper validation and serialization
        return [Company(**company) for company in companies]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")


@router.get("/{company_id}", response_model=Company)
async def get_company(company_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get a specific company by ID"""
    
    try:
        db = get_db_service()
        company_result = await db.get_record("companies", company_id)
        
        if not company_result.success:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company = company_result.data
        
        # Check access permissions
        if current_user.get("user_type") != "SUPER_USER":
            user_company_id = current_user.get("company_id")
            if user_company_id != company_id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert ObjectId to string
        if "_id" in company:
            company["id"] = str(company["_id"])
            del company["_id"]
        
        return Company(**company)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")
