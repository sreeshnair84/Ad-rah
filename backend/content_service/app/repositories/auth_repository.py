# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Authentication Repository

This module handles all database operations related to users, companies,
roles, and authentication in the Adara Digital Signage Platform.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from .base_repository import BaseRepository
from ..models.auth_models import User, UserProfile, Company
from ..models.shared_models import UserType, CompanyType, CompanyRole
from ..rbac_service import get_permissions_for_role


class UserRepository(BaseRepository):
    """Repository for user operations"""

    @property
    def collection_name(self) -> str:
        return "users"

    async def create_user(self, user_data: Dict) -> User:
        """Create a new user with email uniqueness validation"""
        try:
            # Check if user already exists
            existing_user = await self.get_by_field("email", user_data["email"])
            if existing_user:
                raise ValueError(f"User with email {user_data['email']} already exists")

            user_doc = await self.create(user_data)
            return User(**user_doc)

        except DuplicateKeyError:
            raise ValueError(f"User with email {user_data['email']} already exists")

    async def get_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return await self.get_by_field("email", email)

    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get comprehensive user profile with permissions and company info"""
        try:
            # Get user document
            user = await self.get_by_id(user_id)
            if not user:
                return None

            # Get company data if user belongs to a company
            company = None
            if user.get("company_id"):
                company_repo = CompanyRepository(self.db_service)
                company_doc = await company_repo.get_by_id(user["company_id"])
                if company_doc:
                    company = Company(**company_doc)

            # Compute permissions based on user type and role
            user_type = UserType(user["user_type"])
            company_type = CompanyType(company.company_type) if company else None
            company_role = CompanyRole(user["company_role"]) if user.get("company_role") else None

            permissions = get_permissions_for_role(user_type, company_type, company_role)
            permission_strings = [p.value for p in permissions]

            # Build accessible navigation based on permissions
            accessible_navigation = self._build_navigation_access(
                user_type, company_type, company_role, permission_strings
            )

            # Create profile data
            profile_data = {
                **user,
                "permissions": permission_strings,
                "company": company.model_dump() if company else None,
                "accessible_navigation": accessible_navigation,
                "display_name": self._get_display_name(user),
                "role_display": self._get_role_display(user_type, company_role)
            }

            return UserProfile(**profile_data)

        except Exception as e:
            self.logger.error(f"Failed to get user profile for {user_id}: {e}")
            return None

    def _build_navigation_access(self, user_type: UserType, company_type: Optional[CompanyType],
                               company_role: Optional[CompanyRole], permissions: List[str]) -> List[str]:
        """Build accessible navigation items based on permissions"""
        if user_type == UserType.SUPER_USER:
            return [
                "dashboard", "users", "companies", "content", "devices",
                "analytics", "settings", "billing"
            ]

        nav = ["dashboard"]

        # Add navigation based on permissions
        if "user_read" in permissions:
            nav.append("users")
        if "content_read" in permissions:
            nav.extend(["content", "upload"])
        if "device_read" in permissions:
            nav.append("devices")
        if "analytics_read" in permissions:
            nav.append("analytics")

        # Company type specific navigation
        if company_type == CompanyType.HOST and "device_manage" in permissions:
            nav.extend(["device-keys", "digital-twin"])
        elif company_type == CompanyType.ADVERTISER and "content_create" in permissions:
            nav.append("campaigns")

        return list(set(nav))  # Remove duplicates

    def _get_display_name(self, user: Dict) -> str:
        """Get user display name"""
        name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        return name if name else user.get('email', 'Unknown User')

    def _get_role_display(self, user_type: UserType, company_role: Optional[CompanyRole]) -> str:
        """Get user role display text"""
        if user_type == UserType.SUPER_USER:
            return "Super User"
        return company_role.value.title() if company_role else "User"

    async def update_login_timestamp(self, user_id: str):
        """Update user last login timestamp"""
        await self.update_by_id(user_id, {"last_login": datetime.utcnow()})

    async def list_by_company(self, company_id: str) -> List[UserProfile]:
        """Get all users in a company as profiles"""
        try:
            users = await super().list_by_company(company_id, {"is_active": True})
            profiles = []

            for user_data in users:
                profile = await self.get_user_profile(user_data["id"])
                if profile:
                    profiles.append(profile)

            return profiles

        except Exception as e:
            self.logger.error(f"Failed to list users by company {company_id}: {e}")
            return []


class CompanyRepository(BaseRepository):
    """Repository for company operations"""

    @property
    def collection_name(self) -> str:
        return "companies"

    async def create_company(self, company_data: Dict) -> Company:
        """Create a new company with generated codes"""
        from ..auth_service import generate_organization_code, generate_registration_key

        # Generate organization code and registration key
        company_data.update({
            "organization_code": company_data.get("organization_code") or generate_organization_code(),
            "registration_key": generate_registration_key(),
            "status": "active"
        })

        company_doc = await self.create(company_data)
        return Company(**company_doc)

    async def list_active(self) -> List[Company]:
        """List all active companies"""
        try:
            companies_data = await self.list_all({"status": "active"})
            return [Company(**company_data) for company_data in companies_data]

        except Exception as e:
            self.logger.error(f"Failed to list active companies: {e}")
            return []


class RoleRepository(BaseRepository):
    """Repository for role operations"""

    @property
    def collection_name(self) -> str:
        return "roles"

    async def list_by_company(self, company_id: str) -> List[Dict]:
        """Get all roles for a company"""
        return await super().list_by_company(company_id, {"status": "active"})


class UserRoleRepository(BaseRepository):
    """Repository for user-role assignments"""

    @property
    def collection_name(self) -> str:
        return "user_roles"

    async def assign_role(self, user_id: str, company_id: str, role_id: str, is_default: bool = False) -> Dict:
        """Assign a role to a user"""
        role_data = {
            "user_id": user_id,
            "company_id": company_id,
            "role_id": role_id,
            "is_default": is_default,
            "status": "active"
        }

        return await self.create(role_data)

    async def get_user_roles(self, user_id: str) -> List[Dict]:
        """Get all roles for a user"""
        return await self.find_by_query({"user_id": user_id, "status": "active"})

    async def revoke_role(self, user_id: str, role_id: str) -> bool:
        """Revoke a role from a user"""
        roles = await self.find_by_query({
            "user_id": user_id,
            "role_id": role_id,
            "status": "active"
        })

        for role in roles:
            await self.update_by_id(role["id"], {"status": "inactive"})

        return len(roles) > 0