# Company Service Layer
# Enterprise-grade company management with multi-tenancy

import logging
import secrets
import string
from typing import Optional, List, Dict, Any

from app.database import get_db_service, QueryFilter, FilterOperation, QueryOptions, DatabaseResult
from app.models import Company, CompanyCreate, CompanyUpdate

logger = logging.getLogger(__name__)

class CompanyService:
    """Company management service with multi-tenant isolation"""
    
    def __init__(self):
        self._db = None
    
    @property
    def db(self):
        """Lazy initialization of database service"""
        if self._db is None:
            self._db = get_db_service()
        return self._db
    
    async def create_company(
        self,
        company_data: CompanyCreate,
        created_by: Optional[str] = None
    ) -> DatabaseResult:
        """Create a new company with unique organization code"""
        try:
            # Generate unique organization code
            organization_code = await self._generate_organization_code()
            
            # Prepare company record
            company_record = {
                "name": company_data.name,
                "company_type": company_data.type,
                "organization_code": organization_code,
                "business_license": company_data.business_license if hasattr(company_data, 'business_license') else None,
                "email": company_data.email,
                "phone": company_data.phone,
                "address": company_data.address,
                "city": company_data.city,
                "country": company_data.country,
                "website": company_data.website,
                "description": getattr(company_data, 'description', None),
                "status": "active",
                "settings": {
                    "allow_content_sharing": True,
                    "max_shared_companies": 10,
                    "require_approval_for_sharing": True
                },
                "limits": {
                    "max_users": 50,
                    "max_devices": 100,
                    "max_content_size_mb": 1024
                },
                "created_by": created_by
            }
            
            return await self.db.create_record("companies", company_record)
            
        except Exception as e:
            logger.error(f"Error creating company: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def get_company(self, company_id: str) -> DatabaseResult:
        """Get company by ID"""
        try:
            return await self.db.get_record("companies", company_id)
            
        except Exception as e:
            logger.error(f"Error getting company: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def get_company_by_organization_code(self, organization_code: str) -> DatabaseResult:
        """Get company by organization code"""
        try:
            filters = [
                QueryFilter("organization_code", FilterOperation.EQUALS, organization_code),
                QueryFilter("is_deleted", FilterOperation.EQUALS, False)
            ]
            
            return await self.db.find_one_record("companies", filters)
            
        except Exception as e:
            logger.error(f"Error getting company by organization code: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def update_company(
        self,
        company_id: str,
        update_data: CompanyUpdate,
        updated_by: Optional[str] = None
    ) -> DatabaseResult:
        """Update company information"""
        try:
            # Prepare update data
            update_record = {}
            
            if update_data.name is not None:
                update_record["name"] = update_data.name
            
            if update_data.type is not None:
                update_record["company_type"] = update_data.type
            
            if update_data.email is not None:
                update_record["email"] = update_data.email
            
            if update_data.phone is not None:
                update_record["phone"] = update_data.phone
            
            if update_data.address is not None:
                update_record["address"] = update_data.address
            
            if update_data.city is not None:
                update_record["city"] = update_data.city
            
            if update_data.country is not None:
                update_record["country"] = update_data.country
            
            if update_data.website is not None:
                update_record["website"] = update_data.website
            
            if update_data.status is not None:
                update_record["status"] = update_data.status
            
            if updated_by:
                update_record["updated_by"] = updated_by
            
            return await self.db.update_record("companies", company_id, update_record)
            
        except Exception as e:
            logger.error(f"Error updating company: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def delete_company(
        self,
        company_id: str,
        deleted_by: Optional[str] = None
    ) -> DatabaseResult:
        """Soft delete company and associated data"""
        try:
            # Check if company has active users
            user_filters = [
                QueryFilter("company_id", FilterOperation.EQUALS, company_id),
                QueryFilter("status", FilterOperation.EQUALS, "active")
            ]
            
            users_result = await self.db.find_records("user_company_roles", user_filters)
            if users_result.success and users_result.data:
                return DatabaseResult(
                    success=False, 
                    error="Cannot delete company with active users. Please remove all users first."
                )
            
            # Check if company has active devices
            device_filters = [
                QueryFilter("company_id", FilterOperation.EQUALS, company_id),
                QueryFilter("status", FilterOperation.EQUALS, "active")
            ]
            
            devices_result = await self.db.find_records("devices", device_filters)
            if devices_result.success and devices_result.data:
                return DatabaseResult(
                    success=False,
                    error="Cannot delete company with active devices. Please remove all devices first."
                )
            
            # Soft delete company
            update_data = {
                "is_deleted": True,
                "deleted_at": self.db.current_timestamp(),
                "deleted_by": deleted_by,
                "status": "inactive"
            }
            
            return await self.db.update_record("companies", company_id, update_data)
            
        except Exception as e:
            logger.error(f"Error deleting company: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def list_companies(
        self,
        company_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        search: Optional[str] = None
    ) -> DatabaseResult:
        """List companies with filtering and pagination"""
        try:
            filters = []
            
            # Exclude soft-deleted companies
            filters.append(QueryFilter("is_deleted", FilterOperation.EQUALS, False))
            
            if company_type:
                filters.append(QueryFilter("company_type", FilterOperation.EQUALS, company_type))
            
            if status:
                filters.append(QueryFilter("status", FilterOperation.EQUALS, status))
            
            if search:
                # Search in name, email, or organization code
                search_filters = [
                    QueryFilter("name", FilterOperation.CONTAINS, search),
                    QueryFilter("email", FilterOperation.CONTAINS, search),
                    QueryFilter("organization_code", FilterOperation.CONTAINS, search)
                ]
                # Note: This would need OR logic which isn't directly supported
                # For now, search only in name
                filters.append(QueryFilter("name", FilterOperation.CONTAINS, search))
            
            options = QueryOptions(
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by="created_at",
                sort_desc=True
            )
            
            return await self.db.list_records("companies", options)
            
        except Exception as e:
            logger.error(f"Error listing companies: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def get_company_statistics(self, company_id: str) -> DatabaseResult:
        """Get company usage statistics"""
        try:
            # Get user count
            user_filters = [QueryFilter("company_id", FilterOperation.EQUALS, company_id)]
            users_result = await self.db.count_records("user_company_roles", user_filters)
            user_count = users_result.data if users_result.success else 0
            
            # Get device count
            device_filters = [
                QueryFilter("company_id", FilterOperation.EQUALS, company_id),
                QueryFilter("is_deleted", FilterOperation.EQUALS, False)
            ]
            devices_result = await self.db.count_records("devices", device_filters)
            device_count = devices_result.data if devices_result.success else 0
            
            # Get content count
            content_filters = [
                QueryFilter("company_id", FilterOperation.EQUALS, company_id),
                QueryFilter("is_deleted", FilterOperation.EQUALS, False)
            ]
            content_result = await self.db.count_records("content", content_filters)
            content_count = content_result.data if content_result.success else 0
            
            # Get active schedules count
            schedule_filters = [
                QueryFilter("company_id", FilterOperation.EQUALS, company_id),
                QueryFilter("status", FilterOperation.EQUALS, "active")
            ]
            schedules_result = await self.db.count_records("content_schedule", schedule_filters)
            schedule_count = schedules_result.data if schedules_result.success else 0
            
            statistics = {
                "users": user_count,
                "devices": device_count,
                "content": content_count,
                "active_schedules": schedule_count,
                "last_updated": self.db.current_timestamp().isoformat()
            }
            
            return DatabaseResult(success=True, data=statistics)
            
        except Exception as e:
            logger.error(f"Error getting company statistics: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def update_company_settings(
        self,
        company_id: str,
        settings: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> DatabaseResult:
        """Update company-specific settings"""
        try:
            # Get current company
            company_result = await self.get_company(company_id)
            if not company_result.success:
                return company_result
            
            company_data = company_result.data
            current_settings = company_data.get("settings", {})
            
            # Merge settings
            updated_settings = {**current_settings, **settings}
            
            # Update company
            return await self.db.update_record("companies", company_id, {
                "settings": updated_settings,
                "updated_by": updated_by
            })
            
        except Exception as e:
            logger.error(f"Error updating company settings: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def update_company_limits(
        self,
        company_id: str,
        limits: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> DatabaseResult:
        """Update company resource limits"""
        try:
            # Get current company
            company_result = await self.get_company(company_id)
            if not company_result.success:
                return company_result
            
            company_data = company_result.data
            current_limits = company_data.get("limits", {})
            
            # Merge limits
            updated_limits = {**current_limits, **limits}
            
            # Update company
            return await self.db.update_record("companies", company_id, {
                "limits": updated_limits,
                "updated_by": updated_by
            })
            
        except Exception as e:
            logger.error(f"Error updating company limits: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def check_company_limits(self, company_id: str) -> DatabaseResult:
        """Check if company is within its resource limits"""
        try:
            # Get company limits
            company_result = await self.get_company(company_id)
            if not company_result.success:
                return company_result
            
            limits = company_result.data.get("limits", {})
            
            # Get current usage
            stats_result = await self.get_company_statistics(company_id)
            if not stats_result.success:
                return stats_result
            
            stats = stats_result.data
            
            # Check limits
            limit_checks = {
                "users": {
                    "current": stats["users"],
                    "limit": limits.get("max_users", 50),
                    "within_limit": stats["users"] <= limits.get("max_users", 50)
                },
                "devices": {
                    "current": stats["devices"],
                    "limit": limits.get("max_devices", 100),
                    "within_limit": stats["devices"] <= limits.get("max_devices", 100)
                },
                "content": {
                    "current": stats["content"],
                    "limit": limits.get("max_content", 1000),
                    "within_limit": stats["content"] <= limits.get("max_content", 1000)
                }
            }
            
            # Overall status
            all_within_limits = all(check["within_limit"] for check in limit_checks.values())
            
            return DatabaseResult(success=True, data={
                "within_limits": all_within_limits,
                "checks": limit_checks
            })
            
        except Exception as e:
            logger.error(f"Error checking company limits: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    # Private helper methods
    
    async def _generate_organization_code(self) -> str:
        """Generate unique organization code"""
        max_attempts = 10
        
        for _ in range(max_attempts):
            # Generate code in format ORG-XXXXXX
            code_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            organization_code = f"ORG-{code_suffix}"
            
            # Check if code already exists
            existing_result = await self.get_company_by_organization_code(organization_code)
            if not existing_result.success:
                return organization_code
        
        raise Exception("Failed to generate unique organization code after multiple attempts")
    
    async def _generate_registration_key(self, company_id: str) -> str:
        """Generate secure registration key for devices"""
        # Generate 32-character registration key
        key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        return f"{company_id[:8]}-{key}"