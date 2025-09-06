#!/usr/bin/env python3

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum
import uuid


class ContentLayoutType(str, Enum):
    SINGLE_ZONE = "single_zone"
    MULTI_ZONE = "multi_zone"
    DYNAMIC_OVERLAY = "dynamic_overlay"
    INTERACTIVE = "interactive"


class LayoutZone(BaseModel):
    """Individual zones within a layout"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "Main Content", "Side Banner", "Bottom Ticker"
    zone_type: str  # content, advertisement, text, logo
    position_x: int
    position_y: int
    width: int
    height: int
    z_index: int = 1
    is_interactive: bool = False
    allowed_content_types: List[str] = ["image", "video", "html"]
    max_duration_seconds: Optional[int] = None
    priority: int = 1  # For content selection when multiple items available
    rotation_enabled: bool = False  # Can content rotate in this zone
    rotation_interval_seconds: int = 30


class ContentLayout(BaseModel):
    """Multi-zone content layouts for screens"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    company_id: str
    layout_type: ContentLayoutType
    screen_resolution_width: int = 1920
    screen_resolution_height: int = 1080
    zones: List[LayoutZone] = []
    is_template: bool = False  # Can be used by other companies
    category_preferences: Dict[str, Dict] = {}  # Zone-specific category preferences
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentScheduleRule(BaseModel):
    """Advanced scheduling rules for content"""
    id: Optional[str] = None
    content_id: str
    layout_id: str
    zone_id: str
    # Time-based rules
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    days_of_week: List[int] = []  # 0=Monday, 6=Sunday
    time_slots: List[Dict] = []  # [{"start": "09:00", "end": "17:00"}]
    # Frequency rules
    max_plays_per_day: Optional[int] = None
    min_interval_seconds: int = 300  # Minimum time between plays
    priority: int = 1
    # Conditions
    weather_conditions: List[str] = []  # sunny, rainy, etc.
    audience_type: List[str] = []  # families, professionals, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AdCategoryPreference(BaseModel):
    """Host preferences for ad categories in specific zones"""
    id: Optional[str] = None
    host_company_id: str
    layout_id: str
    zone_id: str
    # Category filtering
    preferred_categories: List[str] = []  # Category IDs
    blocked_categories: List[str] = []
    # Content filtering
    max_duration_seconds: Optional[int] = None
    content_rating_limit: str = "PG"  # G, PG, PG-13, R
    # Revenue settings
    min_cpm_rate: Optional[float] = None  # Minimum cost per mille
    revenue_share_percentage: float = 70.0  # Host's share of ad revenue
    # Time restrictions
    restricted_time_slots: List[Dict] = []  # Times when certain categories blocked
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AdvertiserCampaign(BaseModel):
    """Advertiser campaign management"""
    id: Optional[str] = None
    name: str
    advertiser_company_id: str
    content_ids: List[str] = []
    # Targeting
    target_categories: List[str] = []  # Where ads should appear
    target_zones: List[str] = []  # Specific zones if known
    target_demographics: Dict = {}  # Age, gender, location preferences
    # Budget and bidding
    total_budget: float = 0.0
    daily_budget: float = 0.0
    cpm_bid: float = 0.0  # Cost per mille bid
    max_spend_per_day: float = 0.0
    # Campaign schedule
    campaign_start: datetime
    campaign_end: datetime
    # Performance tracking
    total_impressions: int = 0
    total_clicks: int = 0
    total_spend: float = 0.0
    status: str = "draft"  # draft, active, paused, completed
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentDeployment(BaseModel):
    """Content deployment to specific devices"""
    id: Optional[str] = None
    content_id: str
    layout_id: str
    device_ids: List[str] = []  # Target devices
    deployment_type: str = "immediate"  # immediate, scheduled
    scheduled_time: Optional[datetime] = None
    # Deployment status
    status: str = "pending"  # pending, deploying, deployed, failed
    deployment_progress: Dict = {}  # Device-specific progress
    error_logs: List[Dict] = []
    # Metadata
    deployed_by: str
    deployed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DeviceAnalytics(BaseModel):
    """Device-level analytics and statistics"""
    id: Optional[str] = None
    device_id: str
    content_id: str
    layout_id: str
    zone_id: Optional[str] = None
    # Event data
    event_type: str  # impression, interaction, completion, error
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None
    # Audience data (privacy-compliant)
    estimated_audience_count: int = 0
    detected_devices_nearby: int = 0  # Anonymized count
    audience_demographics: Dict = {}  # Aggregated, anonymized data
    # Technical metrics
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    network_quality: Optional[str] = None  # excellent, good, fair, poor
    # Revenue tracking
    estimated_revenue: float = 0.0
    cpm_rate: Optional[float] = None
    # Location context
    ambient_light: Optional[float] = None
    temperature: Optional[float] = None
    noise_level: Optional[float] = None


class ProximityDetection(BaseModel):
    """Privacy-compliant proximity detection"""
    id: Optional[str] = None
    device_id: str
    detection_method: str  # wifi, bluetooth, camera_count
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Anonymized data only
    detected_count: int = 0
    avg_dwell_time_seconds: Optional[float] = None
    device_types: Dict[str, int] = {}  # {"mobile": 5, "tablet": 2}
    estimated_demographics: Dict = {}  # Aggregated estimates only
    # Engagement metrics
    interaction_rate: float = 0.0
    attention_duration_seconds: float = 0.0
    # Privacy compliance
    data_anonymized: bool = True
    retention_period_days: int = 7  # How long this data is kept


class MonetizationMetrics(BaseModel):
    """Revenue and monetization tracking"""
    id: Optional[str] = None
    device_id: str
    content_id: str
    advertiser_company_id: str
    host_company_id: str
    # Time period
    date: datetime
    hour: int  # 0-23 for hourly tracking
    # Metrics
    impressions: int = 0
    clicks: int = 0
    completions: int = 0  # Full ad views
    unique_viewers: int = 0  # Estimated unique audience
    total_view_time_seconds: float = 0.0
    # Revenue
    revenue_generated: float = 0.0
    host_revenue_share: float = 0.0
    platform_revenue_share: float = 0.0
    cpm_rate: float = 0.0
    # Quality metrics
    attention_score: float = 0.0  # 0-1 score of audience engagement
    completion_rate: float = 0.0  # Percentage who watched full ad
    interaction_rate: float = 0.0  # Percentage who interacted


# API Request/Response Models
class ContentLayoutCreate(BaseModel):
    name: str
    description: Optional[str] = None
    company_id: str
    layout_type: ContentLayoutType
    screen_resolution_width: int = 1920
    screen_resolution_height: int = 1080
    zones: List[Dict] = []  # Zone configurations
    is_template: bool = False


class ContentLayoutUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    layout_type: Optional[ContentLayoutType] = None
    zones: Optional[List[Dict]] = None
    category_preferences: Optional[Dict] = None


class AdvertiserCampaignCreate(BaseModel):
    name: str
    advertiser_company_id: str
    content_ids: List[str]
    target_categories: List[str] = []
    total_budget: float
    daily_budget: float
    cpm_bid: float
    campaign_start: datetime
    campaign_end: datetime


class ContentDeploymentCreate(BaseModel):
    content_id: str
    layout_id: str
    device_ids: List[str]
    deployment_type: str = "immediate"
    scheduled_time: Optional[datetime] = None


class AnalyticsQuery(BaseModel):
    device_ids: Optional[List[str]] = None
    content_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[str]] = None
    group_by: str = "hour"  # hour, day, week, month
    metrics: List[str] = ["impressions", "revenue", "engagement"]


class AnalyticsSummary(BaseModel):
    total_impressions: int = 0
    total_revenue: float = 0.0
    total_interactions: int = 0
    unique_devices: int = 0
    avg_engagement_time: float = 0.0
    top_performing_content: List[Dict] = []
    revenue_by_category: Dict[str, float] = {}
    hourly_breakdown: List[Dict] = []
