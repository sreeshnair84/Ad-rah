from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models import Company, CompanyCreate, CompanyUpdate
from app.repo import repo
from app.auth import require_roles

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=List[Company])
@router.get("", response_model=List[Company])  # Add route without trailing slash
async def list_companies():
    """List all companies"""
    companies = await repo.list_companies()
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
    try:
        return [Company(**company) for company in companies]
    except Exception as e:
        # If validation fails, return the raw data
        return companies


@router.get("/{company_id}", response_model=Company)
async def get_company(company_id: str):
    """Get a specific company by ID"""
    company = await repo.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # Convert ObjectId to string for JSON serialization
    if "_id" in company:
        company["id"] = str(company["_id"])
        del company["_id"]
    return Company(**company)


@router.post("/", response_model=Company)
async def create_company(company: CompanyCreate, user=Depends(require_roles("ADMIN"))):
    """Create a new company (Admin only)"""
    company_obj = Company(**company.model_dump())
    saved_company = await repo.save_company(company_obj)
    return Company(**saved_company)


@router.put("/{company_id}", response_model=Company)
async def update_company(
    company_id: str,
    company_update: CompanyUpdate,
    user=Depends(require_roles("ADMIN"))
):
    """Update a company (Admin only)"""
    existing_company = await repo.get_company(company_id)
    if not existing_company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Update fields
    update_data = company_update.model_dump(exclude_unset=True)
    updated_company = {**existing_company, **update_data}

    # Save updated company
    company_obj = Company(**updated_company)
    saved_company = await repo.save_company(company_obj)
    return Company(**saved_company)


@router.delete("/{company_id}")
async def delete_company(company_id: str, user=Depends(require_roles("ADMIN"))):
    """Delete a company (Admin only)"""
    success = await repo.delete_company(company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted successfully"}
