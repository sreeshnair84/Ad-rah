# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Authentication and Authorization Models

This module contains all models related to users, companies, roles,
permissions, and authentication in the Adara Digital Signage Platform.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

from .shared_models import (
    Permission,
    RoleGroup,
    CompanyRoleType,
    Screen,
    CompanyType,
    UserType
)


class Company(BaseModel):
    """Company entity in the multi-tenant system"""
    id: Optional[str] = None
    name: str
    company_type: str = Field(..., pattern="^(HOST|ADVERTISER)$")
    organization_code: Optional[str] = None
    registration_key: Optional[str] = None

    # Contact Information
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    # Multi-tenant sharing settings
    sharing_settings: Optional[Dict] = Field(default_factory=dict)

    # Business limits and quotas
    limits: Optional[Dict] = Field(default_factory=dict)

    # Status and metadata
    status: str = "active"
    subscription_plan: str = "basic"
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class CompanyCreate(BaseModel):
    """Model for creating new companies"""
    name: str
    company_type: str = Field(..., pattern="^(HOST|ADVERTISER)$")
    address: str
    city: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    organization_code: Optional[str] = None
    status: str = "active"


class CompanyUpdate(BaseModel):
    """Model for updating company information"""
    name: Optional[str] = None
    company_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None


class Role(BaseModel):
    """Role entity for RBAC system"""
    id: Optional[str] = None
    name: str
    role_group: RoleGroup
    company_role_type: Optional[CompanyRoleType] = None
    company_id: str
    is_default: bool = False
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RoleCreate(BaseModel):
    """Model for creating new roles"""
    name: str
    role_group: RoleGroup
    company_role_type: Optional[CompanyRoleType] = None
    company_id: str
    permissions: List[Dict] = []
    is_default: bool = False


class RoleUpdate(BaseModel):
    """Model for updating roles"""
    name: Optional[str] = None
    company_role_type: Optional[CompanyRoleType] = None
    permissions: Optional[List[Dict]] = None
    is_default: Optional[bool] = None
    status: Optional[str] = None


class RolePermission(BaseModel):
    """Permission assignments to roles"""
    id: Optional[str] = None
    role_id: str
    screen: Screen
    permissions: List[Permission] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserRole(BaseModel):
    """User-role assignments"""
    id: Optional[str] = None
    user_id: str
    company_id: str
    role_id: str
    is_default: bool = False
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    """User entity in the system"""
    id: Optional[str] = None
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    status: str = "active"
    hashed_password: Optional[str] = None
    user_type: Optional[str] = "COMPANY_USER"
    company_id: Optional[str] = None
    roles: List[UserRole] = []

    # OAuth support
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None

    # User status flags
    is_active: bool = True
    is_deleted: bool = False
    email_verified: bool = False

    # Timestamps
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(BaseModel):
    """Model for creating new users"""
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    password: str
    roles: List[dict] = []
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for updating user information"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    roles: Optional[List[dict]] = None


class UserProfile(BaseModel):
    """Comprehensive user profile with permissions and company info"""
    model_config = {"from_attributes": True}

    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    user_type: str = "COMPANY_USER"
    company_id: Optional[str] = None
    company_role: Optional[str] = None
    permissions: List[str] = []
    is_active: bool = True
    status: str = "active"
    roles: List[Dict] = []
    companies: List[Dict] = []
    company: Optional[Dict] = None
    active_company: Optional[str] = None
    active_role: Optional[str] = None
    email_verified: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: Optional[int] = 0
    locked_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None


class UserLogin(BaseModel):
    """User login credentials"""
    username: str  # This will be the email
    password: str


class UserRegistration(BaseModel):
    """User registration model"""
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    password: str


class UserInvitation(BaseModel):
    """User invitation model"""
    id: Optional[str] = None
    email: str
    invited_by: str
    company_id: str
    role_id: str
    invitation_token: str
    expires_at: datetime
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PermissionCheck(BaseModel):
    """Model for checking user permissions"""
    user_id: str
    company_id: str
    screen: Screen
    permission: Permission


class OAuthLogin(BaseModel):
    """OAuth login model"""
    provider: str  # google, microsoft, etc.
    code: str
    redirect_uri: str


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: str


class PasswordReset(BaseModel):
    """Password reset model"""
    token: str
    new_password: str


class PasswordResetToken(BaseModel):
    """Password reset token storage"""
    id: Optional[str] = None
    user_id: str
    reset_token: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)