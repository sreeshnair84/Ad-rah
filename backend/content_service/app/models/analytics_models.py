# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Analytics and Reporting Models

This module contains all models related to analytics, reporting,
audit trails, and system monitoring.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

from .shared_models import ContentHistoryEventType


class AnalyticsQuery(BaseModel):
    """Analytics query parameters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    device_ids: Optional[List[str]] = None
    content_ids: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    group_by: Optional[str] = None  # device, content, date, hour


class AnalyticsSummary(BaseModel):
    """Analytics summary response"""
    total_impressions: int = 0
    total_revenue: float = 0.0
    total_interactions: int = 0
    unique_devices: int = 0
    avg_engagement_time: float = 0.0
    top_performing_content: List[Dict] = []
    revenue_by_category: Dict[str, float] = {}
    hourly_breakdown: List[Dict] = []


class MonetizationMetrics(BaseModel):
    """Revenue tracking metrics"""
    id: Optional[str] = None
    device_id: str
    content_id: str
    advertiser_company_id: str
    host_company_id: str
    date: datetime
    hour: int  # 0-23
    impressions: int = 0
    revenue_generated: float = 0.0
    host_revenue_share: float = 0.0
    platform_revenue_share: float = 0.0
    completion_rate: float = 0.0


class ContentHistory(BaseModel):
    """Content lifecycle audit trail"""
    id: Optional[str] = None
    content_id: str
    event_type: ContentHistoryEventType
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)
    triggered_by_user_id: Optional[str] = None
    triggered_by_system: Optional[str] = None
    device_id: Optional[str] = None
    company_id: str
    event_details: Dict = Field(default_factory=dict)
    previous_state: Optional[Dict] = None
    new_state: Optional[Dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentHistoryQuery(BaseModel):
    """Content history query parameters"""
    content_ids: Optional[List[str]] = None
    event_types: Optional[List[ContentHistoryEventType]] = None
    user_ids: Optional[List[str]] = None
    device_ids: Optional[List[str]] = None
    company_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class HistoryEventCreate(BaseModel):
    """Model for creating history events"""
    content_id: str
    event_type: ContentHistoryEventType
    event_details: Dict = Field(default_factory=dict)
    previous_state: Optional[Dict] = None
    new_state: Optional[Dict] = None
    device_id: Optional[str] = None
    triggered_by_system: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class ContentTimelineView(BaseModel):
    """Content timeline for UI display"""
    content_id: str
    content_title: str
    timeline_events: List[Dict] = Field(default_factory=list)
    current_phase: str  # upload, moderation, review, approved, deployed
    next_expected_action: Optional[str] = None
    performance_score: Optional[float] = None


class ContentLifecycleSummary(BaseModel):
    """Content lifecycle summary"""
    content_id: str
    content_title: str
    current_status: str
    company_id: str
    company_name: str
    uploaded_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    first_deployed_at: Optional[datetime] = None
    total_deployments: int = 0
    total_displays: int = 0
    estimated_revenue: float = 0.0
    uploaded_by: Optional[str] = None
    reviewed_by: Optional[str] = None


class ContentAuditReport(BaseModel):
    """Comprehensive audit report"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    report_type: str  # daily, weekly, monthly, compliance
    start_date: datetime
    end_date: datetime
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str
    total_content_uploaded: int = 0
    total_content_approved: int = 0
    total_content_rejected: int = 0
    avg_approval_time_hours: Optional[float] = None
    success_rate_percentage: Optional[float] = None
    events_by_type: Dict[str, int] = Field(default_factory=dict)


class SystemAuditLog(BaseModel):
    """System-wide audit logging"""
    id: Optional[str] = None
    audit_type: str  # USER_ACTION, SYSTEM_EVENT, SECURITY_EVENT
    resource_type: str  # CONTENT, USER, COMPANY, DEVICE
    resource_id: str
    action_performed: str
    performed_by_user_id: Optional[str] = None
    performed_by_system: Optional[str] = None
    company_id: Optional[str] = None
    ip_address: Optional[str] = None
    success: bool = True
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)