# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Campaign and Business Models

This module contains models related to advertising campaigns,
digital twins, templates, and company applications.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

from .shared_models import (
    DigitalTwinStatus,
    CompanyApplicationStatus,
    CompanyType
)


class AdvertiserCampaign(BaseModel):
    """Advertising campaign model"""
    id: Optional[str] = None
    name: str
    advertiser_company_id: str
    content_ids: List[str] = []
    target_categories: List[str] = []
    total_budget: float = 0.0
    daily_budget: float = 0.0
    campaign_start: datetime
    campaign_end: datetime
    total_impressions: int = 0
    total_spend: float = 0.0
    status: str = "draft"  # draft, active, paused, completed
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AdvertiserCampaignCreate(BaseModel):
    """Model for creating advertiser campaigns"""
    name: str
    advertiser_company_id: str
    content_ids: List[str]
    total_budget: float
    daily_budget: float
    campaign_start: datetime
    campaign_end: datetime


class AdCategoryPreference(BaseModel):
    """Host ad category preferences"""
    id: Optional[str] = None
    host_company_id: str
    layout_id: str
    zone_id: str
    preferred_categories: List[str] = []
    blocked_categories: List[str] = []
    max_duration_seconds: Optional[int] = None
    min_cpm_rate: Optional[float] = None
    revenue_share_percentage: float = 70.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DigitalTwin(BaseModel):
    """Digital twin for screen testing"""
    id: Optional[str] = None
    name: str
    screen_id: str
    company_id: str
    description: Optional[str] = None
    is_live_mirror: bool = False
    test_content_ids: List[str] = []
    status: DigitalTwinStatus = DigitalTwinStatus.STOPPED
    created_by: str
    last_accessed: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DigitalTwinCreate(BaseModel):
    """Model for creating digital twins"""
    name: str
    screen_id: str
    company_id: str
    description: Optional[str] = None
    is_live_mirror: bool = False


class DigitalTwinUpdate(BaseModel):
    """Model for updating digital twins"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_live_mirror: Optional[bool] = None
    test_content_ids: Optional[List[str]] = None
    status: Optional[DigitalTwinStatus] = None


class LayoutTemplate(BaseModel):
    """Screen layout templates"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    company_id: str
    template_data: Dict
    is_public: bool = False
    usage_count: int = 0
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LayoutTemplateCreate(BaseModel):
    """Model for creating layout templates"""
    name: str
    description: Optional[str] = None
    company_id: str
    template_data: Dict
    is_public: bool = False


class LayoutTemplateUpdate(BaseModel):
    """Model for updating layout templates"""
    name: Optional[str] = None
    description: Optional[str] = None
    template_data: Optional[Dict] = None
    is_public: Optional[bool] = None


class CompanyApplication(BaseModel):
    """Company registration application"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    company_type: CompanyType
    business_license: str
    address: str
    city: str
    country: str
    website: Optional[str] = None
    description: str
    applicant_name: str
    applicant_email: str
    applicant_phone: str
    status: CompanyApplicationStatus = CompanyApplicationStatus.PENDING
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    documents: Dict[str, str] = Field(default_factory=dict)
    created_company_id: Optional[str] = None
    created_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CompanyApplicationCreate(BaseModel):
    """Model for creating company applications"""
    company_name: str
    company_type: CompanyType
    business_license: str
    address: str
    city: str
    country: str
    website: Optional[str] = None
    description: str
    applicant_name: str
    applicant_email: str
    applicant_phone: str
    documents: Dict[str, str] = Field(default_factory=dict)


class CompanyApplicationReview(BaseModel):
    """Model for reviewing company applications"""
    decision: str = Field(..., pattern="^(approved|rejected)$")
    notes: Optional[str] = None


class CompanyApplicationUpdate(BaseModel):
    """Model for updating company applications"""
    status: Optional[CompanyApplicationStatus] = None
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    created_company_id: Optional[str] = None
    created_user_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)