# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Content Management Models

This module contains all models related to content management,
including uploads, moderation, overlays, and content organization.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

from .shared_models import ContentLayoutType, ContentOverlayStatus


class ContentMeta(BaseModel):
    """Core content metadata model"""
    id: Optional[str] = None
    owner_id: str
    company_id: str
    filename: str
    content_type: str
    size: int
    title: Optional[str] = None
    description: Optional[str] = None

    # Status workflow
    status: str = "pending"  # pending -> approved -> rejected

    # AI Moderation
    ai_moderation_status: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    ai_analysis: Optional[Dict] = None

    # Review workflow
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    # File URLs
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Analytics
    view_count: int = 0

    # Timestamps
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentUploadRequest(BaseModel):
    """Content upload request model"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    duration_seconds: Optional[int] = Field(None, ge=0)


class UploadResponse(BaseModel):
    """Content upload response"""
    filename: str
    status: str
    message: Optional[str] = None
    content_id: Optional[str] = None
    ai_moderation_required: bool = False


class ModerationResult(BaseModel):
    """AI moderation result"""
    content_id: str
    ai_confidence: float = Field(..., ge=0.0, le=1.0)
    action: str  # approved / quarantine / reject
    reason: Optional[str] = None


class Review(BaseModel):
    """Content review model"""
    id: Optional[str] = None
    content_id: str
    ai_confidence: Optional[float] = None
    action: str  # approved | rejected | needs_review
    reviewer_id: Optional[str] = None
    notes: Optional[str] = None
    ai_analysis: Optional[Dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LayoutZone(BaseModel):
    """Layout zone definition for multi-zone content"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "Main Content", "Side Banner"
    position_x: int
    position_y: int
    width: int
    height: int
    z_index: int = 1


class ContentLayout(BaseModel):
    """Content layout for screens"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    company_id: str
    layout_type: ContentLayoutType
    screen_resolution_width: int = 1920
    screen_resolution_height: int = 1080
    zones: List[LayoutZone] = []
    is_template: bool = False
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentLayoutCreate(BaseModel):
    """Model for creating content layouts"""
    name: str
    description: Optional[str] = None
    company_id: str
    layout_type: ContentLayoutType = ContentLayoutType.SINGLE_ZONE
    zones: List[Dict] = []
    is_template: bool = False


class ContentLayoutUpdate(BaseModel):
    """Model for updating content layouts"""
    name: Optional[str] = None
    description: Optional[str] = None
    layout_type: Optional[ContentLayoutType] = None
    zones: Optional[List[Dict]] = None


class ContentOverlay(BaseModel):
    """Content overlay on screens"""
    id: Optional[str] = None
    content_id: str
    screen_id: str
    company_id: str
    name: str
    position_x: int = 0
    position_y: int = 0
    width: int = 100
    height: int = 100
    z_index: int = 1
    opacity: float = 1.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: ContentOverlayStatus = ContentOverlayStatus.DRAFT
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentOverlayCreate(BaseModel):
    """Model for creating content overlays"""
    content_id: str
    screen_id: str
    company_id: str
    name: str
    position_x: int = 0
    position_y: int = 0
    width: int = 100
    height: int = 100
    z_index: int = 1
    opacity: float = 1.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ContentOverlayUpdate(BaseModel):
    """Model for updating content overlays"""
    name: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    z_index: Optional[int] = None
    opacity: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[ContentOverlayStatus] = None


class ContentDeployment(BaseModel):
    """Content deployment to devices"""
    id: Optional[str] = None
    content_id: str
    device_ids: List[str] = []
    deployment_type: str = "immediate"  # immediate, scheduled
    scheduled_time: Optional[datetime] = None
    status: str = "pending"  # pending, deploying, deployed, failed
    deployed_by: str
    deployed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentDeploymentCreate(BaseModel):
    """Model for creating content deployments"""
    content_id: str
    device_ids: List[str]
    deployment_type: str = "immediate"
    scheduled_time: Optional[datetime] = None