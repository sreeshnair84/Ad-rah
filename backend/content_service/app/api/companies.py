from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.rbac_models import Company
from app.repo import repo
from app.database_service import db_service
from app.api.auth import get_current_user
from app.rbac_models import UserProfile, UserType

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/")
@router.get("")  # Add route without trailing slash
async def list_companies(current_user: UserProfile = Depends(get_current_user)):
    """List companies accessible to the current user"""
    
    try:
        print(f"[COMPANIES] INFO: User {current_user.email} requesting companies list")
        print(f"[COMPANIES] DEBUG: User type: {current_user.user_type}, Company ID: {current_user.company_id}")
        
        # For SUPER_USER, return all companies
        if current_user.user_type == UserType.SUPER_USER:
            print(f"[COMPANIES] DEBUG: Super user, fetching all companies")
            companies = await db_service.list_companies()
        else:
            # For regular users, return only their company
            user_company_id = current_user.company_id
            print(f"[COMPANIES] DEBUG: Regular user, fetching company: {user_company_id}")
            if user_company_id:
                try:
                    print(f"[COMPANIES] DEBUG: About to call db_service.get_company({user_company_id})")
                    company = await db_service.get_company(user_company_id)
                    print(f"[COMPANIES] DEBUG: db_service.get_company returned: {company}")
                    if company:
                        print(f"[COMPANIES] DEBUG: Successfully fetched company: {company.name}")
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
        
        # Database service already returns proper Company objects, no need for re-instantiation
        return companies
        
    except Exception as e:
        print(f"[COMPANIES] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")


@router.get("/{company_id}")
async def get_company(company_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get a specific company by ID"""

    try:
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Check access permissions
        if current_user.user_type != UserType.SUPER_USER:
            user_company_id = current_user.company_id
            if user_company_id != company_id:
                raise HTTPException(status_code=403, detail="Access denied")

        # Database service already returns proper Company object
        return company
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")


@router.post("/", response_model=Company)
async def create_company(company_data: dict, current_user: UserProfile = Depends(get_current_user)):
    """Create a new company"""
    
    try:
        print(f"[COMPANIES] INFO: User {current_user.email} creating company")
        print(f"[COMPANIES] DEBUG: Input data: {company_data}")
        
        # Check permissions - only SUPER_USER can create companies
        if current_user.user_type != UserType.SUPER_USER:
            raise HTTPException(status_code=403, detail="Only administrators can create companies")
        
        # Handle field mapping from API input to model
        mapped_data = {
            "name": company_data.get("name"),
            "company_type": company_data.get("type") or company_data.get("company_type"),  # Handle both field names
            "address": company_data.get("address") or company_data.get("address_line1"),
            "city": company_data.get("city") or company_data.get("state"),
            "country": company_data.get("country") or company_data.get("postal_code"),
            "phone": company_data.get("phone"),
            "email": company_data.get("email") or company_data.get("contact_email"),
            "website": company_data.get("website"),
            "organization_code": company_data.get("organization_code"),
            "status": company_data.get("status", "active")
        }
        
        # Remove None values to avoid validation errors
        mapped_data = {k: v for k, v in mapped_data.items() if v is not None}
        
        print(f"[COMPANIES] DEBUG: Mapped data: {mapped_data}")
        
        # Validate required fields
        required_fields = ["name", "company_type", "address", "city", "country"]
        missing_fields = [field for field in required_fields if not mapped_data.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=422, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Validate company_type
        if mapped_data["company_type"] not in ["HOST", "ADVERTISER"]:
            raise HTTPException(
                status_code=422, 
                detail="company_type must be either 'HOST' or 'ADVERTISER'"
            )
        
        # Create Company object
        company = Company(**mapped_data)
        
        # Save to database
        saved_company = await repo.save_company(company)
        
        print(f"[COMPANIES] INFO: Successfully created company: {saved_company.get('name')}")
        
        # Convert ObjectId to string and handle field mapping for response
        if "_id" in saved_company:
            saved_company["id"] = str(saved_company["_id"])
            del saved_company["_id"]
        
        # Handle field name mapping for response - database uses different field names
        if "type" in saved_company:
            saved_company["company_type"] = saved_company["type"]
            del saved_company["type"]
        if "contact_email" in saved_company:
            saved_company["email"] = saved_company["contact_email"]
            del saved_company["contact_email"]
        if "address_line1" in saved_company:
            saved_company["address"] = saved_company["address_line1"]
            del saved_company["address_line1"]
        if "state" in saved_company:
            saved_company["city"] = saved_company["state"]
            del saved_company["state"]
        if "postal_code" in saved_company:
            saved_company["country"] = saved_company["postal_code"]
            del saved_company["postal_code"]
        
        return Company(**saved_company)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[COMPANIES] ERROR: Failed to create company: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")


@router.put("/{company_id}", response_model=Company)
async def update_company(
    company_id: str, 
    company_data: dict, 
    current_user: UserProfile = Depends(get_current_user)
):
    """Update an existing company"""
    
    try:
        print(f"[COMPANIES] INFO: User {current_user.email} updating company {company_id}")
        print(f"[COMPANIES] DEBUG: Input data: {company_data}")
        
        # Check permissions - only SUPER_USER can update companies
        if current_user.user_type != UserType.SUPER_USER:
            raise HTTPException(status_code=403, detail="Only administrators can update companies")
        
        # Check if company exists
        existing_company = await repo.get_company(company_id)
        if not existing_company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Handle field mapping from API input to model
        mapped_data = {}
        if "name" in company_data:
            mapped_data["name"] = company_data["name"]
        if "type" in company_data or "company_type" in company_data:
            mapped_data["company_type"] = company_data.get("type") or company_data.get("company_type")
        if "address" in company_data or "address_line1" in company_data:
            mapped_data["address"] = company_data.get("address") or company_data.get("address_line1")
        if "city" in company_data or "state" in company_data:
            mapped_data["city"] = company_data.get("city") or company_data.get("state")
        if "country" in company_data or "postal_code" in company_data:
            mapped_data["country"] = company_data.get("country") or company_data.get("postal_code")
        if "phone" in company_data:
            mapped_data["phone"] = company_data["phone"]
        if "email" in company_data or "contact_email" in company_data:
            mapped_data["email"] = company_data.get("email") or company_data.get("contact_email")
        if "website" in company_data:
            mapped_data["website"] = company_data["website"]
        if "organization_code" in company_data:
            mapped_data["organization_code"] = company_data["organization_code"]
        if "status" in company_data:
            mapped_data["status"] = company_data["status"]
        
        # Remove None values
        mapped_data = {k: v for k, v in mapped_data.items() if v is not None}
        
        print(f"[COMPANIES] DEBUG: Mapped data: {mapped_data}")
        
        # Validate company_type if provided
        if "company_type" in mapped_data and mapped_data["company_type"] not in ["HOST", "ADVERTISER"]:
            raise HTTPException(
                status_code=422, 
                detail="company_type must be either 'HOST' or 'ADVERTISER'"
            )
        
        # Update the company data
        updated_data = {**existing_company, **mapped_data}
        
        # Create Company object for validation
        company = Company(**updated_data)
        
        # Save to database
        saved_company = await repo.save_company(company)
        
        print(f"[COMPANIES] INFO: Successfully updated company: {saved_company.get('name')}")
        
        # Convert ObjectId to string and handle field mapping for response
        if "_id" in saved_company:
            saved_company["id"] = str(saved_company["_id"])
            del saved_company["_id"]
        
        # Handle field name mapping for response
        if "type" in saved_company:
            saved_company["company_type"] = saved_company["type"]
            del saved_company["type"]
        if "contact_email" in saved_company:
            saved_company["email"] = saved_company["contact_email"]
            del saved_company["contact_email"]
        if "address_line1" in saved_company:
            saved_company["address"] = saved_company["address_line1"]
            del saved_company["address_line1"]
        if "state" in saved_company:
            saved_company["city"] = saved_company["state"]
            del saved_company["state"]
        if "postal_code" in saved_company:
            saved_company["country"] = saved_company["postal_code"]
            del saved_company["postal_code"]
        
        return Company(**saved_company)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[COMPANIES] ERROR: Failed to update company: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")
