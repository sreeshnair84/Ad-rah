# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Device and Hardware Models

This module contains all models related to device management,
registration, monitoring, and analytics.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

from .shared_models import (
    ScreenStatus,
    ScreenOrientation,
    DeviceType,
    DeviceHistoryEventType
)


class DigitalScreen(BaseModel):
    """Digital screen/device model"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    company_id: str
    location: str
    resolution_width: int = 1920
    resolution_height: int = 1080
    orientation: ScreenOrientation = ScreenOrientation.LANDSCAPE
    registration_key: Optional[str] = None
    status: ScreenStatus = ScreenStatus.ACTIVE
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScreenCreate(BaseModel):
    """Model for creating digital screens"""
    name: str
    description: Optional[str] = None
    company_id: str
    location: str
    resolution_width: int = 1920
    resolution_height: int = 1080
    orientation: ScreenOrientation = ScreenOrientation.LANDSCAPE
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None


class ScreenUpdate(BaseModel):
    """Model for updating digital screens"""
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    orientation: Optional[ScreenOrientation] = None
    status: Optional[ScreenStatus] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None


class DeviceCapabilities(BaseModel):
    """Device hardware capabilities"""
    max_resolution_width: int = 1920
    max_resolution_height: int = 1080
    supports_video: bool = True
    supports_images: bool = True
    supported_formats: List[str] = ["mp4", "jpg", "png", "webp"]
    has_touch: bool = False
    has_audio: bool = True
    storage_capacity_gb: Optional[int] = None
    ram_gb: Optional[int] = None
    os_version: Optional[str] = None


class DeviceFingerprint(BaseModel):
    """Device identification"""
    hardware_id: str
    mac_addresses: List[str] = []
    platform: Optional[str] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    timezone: Optional[str] = None


class DeviceCredentials(BaseModel):
    """Device authentication credentials"""
    id: Optional[str] = None
    device_id: str
    jwt_token: Optional[str] = None
    jwt_expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_refreshed: Optional[datetime] = None
    revoked: bool = False


class DeviceHeartbeat(BaseModel):
    """Device status heartbeat"""
    id: Optional[str] = None
    device_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: ScreenStatus
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    storage_usage: Optional[float] = None
    current_content_id: Optional[str] = None
    content_errors: int = 0


class DeviceRegistrationCreate(BaseModel):
    """Device registration model"""
    device_name: str = Field(..., min_length=1, max_length=100)
    organization_code: str = Field(..., min_length=1, max_length=50)
    registration_key: str = Field(..., min_length=1, max_length=100)
    device_type: Optional[str] = None
    capabilities: Optional[DeviceCapabilities] = None
    fingerprint: Optional[DeviceFingerprint] = None
    location_description: Optional[str] = None


class DeviceRegistrationKey(BaseModel):
    """Device registration key"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    company_id: str
    created_by: str
    expires_at: datetime
    used: bool = False
    used_at: Optional[datetime] = None
    used_by_device: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DeviceRegistrationKeyCreate(BaseModel):
    """Model for creating device registration keys"""
    company_id: str
    expires_at: Optional[datetime] = None


class DeviceAnalytics(BaseModel):
    """Device analytics data"""
    device_id: str
    content_id: Optional[str] = None
    event_type: str  # impression, interaction, completion, error
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None
    estimated_revenue: float = 0.0
    user_interactions: int = 0
    location_data: Optional[Dict] = None


class ProximityDetection(BaseModel):
    """Privacy-compliant proximity detection"""
    id: Optional[str] = None
    device_id: str
    detection_method: str  # wifi, bluetooth, camera_count
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    detected_count: int = 0
    avg_dwell_time_seconds: Optional[float] = None
    interaction_rate: float = 0.0
    data_anonymized: bool = True


class DeviceHistory(BaseModel):
    """Device activity history"""
    id: Optional[str] = None
    device_id: str
    event_type: DeviceHistoryEventType
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)
    content_id: Optional[str] = None
    company_id: str
    device_status: Optional[str] = None
    event_data: Dict = Field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)