#!/usr/bin/env python3
"""
Digital Signage Ad Slot Management System - Database Models
Complete data models for multi-tenant ad slot management system
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Union, Literal
from datetime import datetime, time
from enum import Enum
import uuid
from decimal import Decimal


# ==============================
# ENUMS AND TYPES
# ==============================

class UserRole(str, Enum):
    """System-wide user roles"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HOST = "host"
    ADVERTISER = "advertiser"
    REVIEWER = "reviewer"

class AdSlotStatus(str, Enum):
    """Ad slot availability status"""
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"
    MAINTENANCE = "maintenance"

class BookingStatus(str, Enum):
    """Booking workflow status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ContentStatus(str, Enum):
    """Content moderation status"""
    SUBMITTED = "submitted"
    AI_REVIEW = "ai_review"
    HUMAN_REVIEW = "human_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"

class PaymentStatus(str, Enum):
    """Payment processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class InvoiceStatus(str, Enum):
    """Invoice status"""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


# ==============================
# USER MANAGEMENT MODELS
# ==============================

class User(BaseModel):
    """Enhanced user model for multi-tenant system"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str = Field(..., unique=True)
    username: str = Field(..., unique=True)
    full_name: str
    role: UserRole
    is_active: bool = True
    is_verified: bool = False
    
    # Profile information
    phone: Optional[str] = None
    company_id: Optional[str] = None
    profile_image: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    
    # Security
    password_hash: str
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


class Company(BaseModel):
    """Company/Organization model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    company_type: Literal["host", "advertiser", "both"]
    
    # Contact information
    contact_email: str
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    
    # Address
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    country: str
    postal_code: str
    
    # Business information
    tax_id: Optional[str] = None
    business_license: Optional[str] = None
    industry: Optional[str] = None
    
    # Platform settings
    is_active: bool = True
    subscription_tier: str = "basic"  # basic, premium, enterprise
    billing_contact: Optional[str] = None
    
    # KYC verification
    verification_status: str = "pending"  # pending, verified, rejected
    verification_documents: List[str] = []
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================
# LOCATION AND DEVICE MODELS
# ==============================

class Location(BaseModel):
    """Host location model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    host_company_id: str
    name: str
    description: Optional[str] = None
    
    # Geographic information
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    country: str
    postal_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Location characteristics
    venue_type: str  # mall, gym, restaurant, transit, office, outdoor
    foot_traffic_level: str = "medium"  # low, medium, high
    target_demographics: Dict = {}  # age_groups, income_levels, interests
    operating_hours: Dict = {}  # daily operating hours
    
    # Tags for discovery
    tags: List[str] = []
    category: str  # retail, healthcare, transportation, entertainment
    
    # Settings
    is_active: bool = True
    accepts_advertising: bool = True
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Device(BaseModel):
    """Digital signage device model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    location_id: str
    device_name: str
    device_type: str = "display"  # display, kiosk, interactive
    
    # Technical specifications
    screen_width: int = 1920
    screen_height: int = 1080
    screen_size_inches: Optional[float] = None
    supports_touch: bool = False
    supports_audio: bool = True
    
    # Network and authentication
    device_key: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    
    # Status and health
    is_online: bool = False
    last_heartbeat: Optional[datetime] = None
    software_version: Optional[str] = None
    battery_level: Optional[float] = None
    
    # Settings
    is_active: bool = True
    auto_update_enabled: bool = True
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================
# AD SLOT MODELS
# ==============================

class AdSlot(BaseModel):
    """Core ad slot model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    location_id: str
    device_id: str
    name: str
    description: Optional[str] = None
    
    # Slot configuration
    slot_duration_seconds: int = 30
    position_in_sequence: int = 1
    max_ads_per_hour: int = 10
    
    # Pricing
    base_price_per_slot: Decimal = Decimal("10.00")
    peak_hour_multiplier: Decimal = Decimal("1.5")
    weekend_multiplier: Decimal = Decimal("1.2")
    
    # Time restrictions
    available_days: List[int] = [0, 1, 2, 3, 4, 5, 6]  # Monday=0 to Sunday=6
    available_hours_start: time = time(6, 0)  # 6 AM
    available_hours_end: time = time(22, 0)  # 10 PM
    blackout_periods: List[Dict] = []  # Maintenance, special events
    
    # Content restrictions
    allowed_content_types: List[str] = ["video", "image", "html5"]
    content_categories: List[str] = []  # retail, food, automotive, etc.
    blocked_categories: List[str] = []
    content_rating_limit: str = "PG"
    
    # Settings
    status: AdSlotStatus = AdSlotStatus.AVAILABLE
    requires_approval: bool = True
    auto_approve_trusted_advertisers: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str


class RecurringSlotRule(BaseModel):
    """Rules for recurring ad slot bookings"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    recurrence_type: str  # daily, weekly, monthly
    recurrence_interval: int = 1  # Every X days/weeks/months
    days_of_week: List[int] = []  # For weekly recurrence
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    
    # Generated occurrences tracking
    generated_bookings: List[str] = []  # Booking IDs
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================
# BOOKING MODELS
# ==============================

class Booking(BaseModel):
    """Ad slot booking model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    ad_slot_id: str
    advertiser_company_id: str
    campaign_id: Optional[str] = None
    
    # Booking details
    booking_date: datetime
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    
    # Pricing
    base_price: Decimal
    final_price: Decimal  # After multipliers and discounts
    currency: str = "USD"
    
    # Booking workflow
    status: BookingStatus = BookingStatus.PENDING
    host_approval_required: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Content association
    content_id: Optional[str] = None
    content_approved: bool = False
    
    # Recurring booking
    is_recurring: bool = False
    recurring_rule_id: Optional[str] = None
    parent_booking_id: Optional[str] = None
    
    # Payment
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_intent_id: Optional[str] = None  # Stripe/payment gateway ID
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str


class Campaign(BaseModel):
    """Advertiser campaign model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    advertiser_company_id: str
    name: str
    description: Optional[str] = None
    
    # Campaign objectives
    objective: str = "awareness"  # awareness, traffic, conversions
    target_audience: Dict = {}
    
    # Budget and dates
    total_budget: Decimal
    daily_budget: Optional[Decimal] = None
    start_date: datetime
    end_date: datetime
    
    # Targeting
    target_locations: List[str] = []  # Location IDs
    target_categories: List[str] = []
    target_demographics: Dict = {}
    geographic_radius_km: Optional[float] = None
    
    # Performance tracking
    total_spent: Decimal = Decimal("0.00")
    total_impressions: int = 0
    total_clicks: int = 0
    
    # Status
    status: str = "draft"  # draft, active, paused, completed
    is_active: bool = True
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str


# ==============================
# CONTENT MODELS
# ==============================

class Content(BaseModel):
    """Enhanced content model for ads"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    advertiser_company_id: str
    campaign_id: Optional[str] = None
    
    # Content details
    title: str
    description: Optional[str] = None
    content_type: str  # video/mp4, image/png, text/html
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    duration_seconds: Optional[int] = None
    
    # Content metadata
    categories: List[str] = []
    tags: List[str] = []
    content_rating: str = "G"  # G, PG, PG-13, R
    call_to_action: Optional[str] = None
    landing_url: Optional[str] = None
    
    # Moderation
    status: ContentStatus = ContentStatus.SUBMITTED
    ai_moderation_score: Optional[float] = None
    ai_moderation_flags: List[str] = []
    human_review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    # Usage tracking
    total_plays: int = 0
    total_impressions: int = 0
    
    # Settings
    is_active: bool = True
    expires_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str


class ModerationLog(BaseModel):
    """Content moderation audit trail"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str
    
    # Moderation details
    moderation_type: str  # ai, human
    previous_status: ContentStatus
    new_status: ContentStatus
    
    # AI moderation
    ai_confidence_score: Optional[float] = None
    ai_flags: List[str] = []
    ai_model_version: Optional[str] = None
    
    # Human moderation
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    decision_reason: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================
# PLAYBACK AND ANALYTICS MODELS
# ==============================

class PlaybackEvent(BaseModel):
    """Proof-of-play event logging"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Core identifiers
    device_id: str
    location_id: str
    ad_slot_id: str
    booking_id: str
    content_id: str
    
    # Event details
    event_type: str  # start, complete, skip, error
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_played: Optional[int] = None  # Seconds
    
    # Technical context
    playback_quality: Optional[str] = None  # HD, SD, etc.
    network_quality: Optional[str] = None
    device_status: Dict = {}  # CPU, memory, battery
    
    # Audience metrics (anonymous)
    estimated_viewers: int = 0
    interaction_count: int = 0
    
    # Error handling
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sync_status: str = "pending"  # pending, synced, failed


class AnalyticsAggregation(BaseModel):
    """Aggregated analytics for reporting"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Time period
    date: datetime
    hour: Optional[int] = None  # For hourly aggregation
    aggregation_level: str  # hourly, daily, weekly, monthly
    
    # Identifiers
    device_id: Optional[str] = None
    location_id: Optional[str] = None
    advertiser_company_id: Optional[str] = None
    host_company_id: Optional[str] = None
    content_id: Optional[str] = None
    
    # Metrics
    total_impressions: int = 0
    total_plays: int = 0
    total_completions: int = 0
    total_duration_seconds: int = 0
    unique_viewers: int = 0
    
    # Revenue
    revenue_generated: Decimal = Decimal("0.00")
    host_revenue_share: Decimal = Decimal("0.00")
    platform_revenue_share: Decimal = Decimal("0.00")
    
    # Performance
    completion_rate: float = 0.0  # Percentage
    engagement_score: float = 0.0  # 0-1 scale
    
    # Quality metrics
    error_rate: float = 0.0
    avg_load_time_seconds: float = 0.0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================
# BILLING AND PAYMENT MODELS
# ==============================

class Invoice(BaseModel):
    """Invoice model for billing"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    
    # Parties
    advertiser_company_id: str
    host_company_id: str
    
    # Invoice period
    billing_period_start: datetime
    billing_period_end: datetime
    
    # Line items (calculated from playback events)
    bookings: List[str] = []  # Booking IDs included
    total_impressions: int = 0
    total_duration_seconds: int = 0
    
    # Amounts
    subtotal: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    
    # Revenue sharing
    host_share_amount: Decimal = Decimal("0.00")
    platform_share_amount: Decimal = Decimal("0.00")
    host_share_percentage: Decimal = Decimal("70.00")
    
    # Status and dates
    status: InvoiceStatus = InvoiceStatus.DRAFT
    issued_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    
    # Payment processing
    payment_intent_id: Optional[str] = None
    payment_method: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str


class PaymentTransaction(BaseModel):
    """Payment transaction record"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str
    
    # Transaction details
    amount: Decimal
    currency: str = "USD"
    payment_method: str  # card, bank_transfer, etc.
    
    # Gateway integration
    gateway_provider: str  # stripe, paypal, etc.
    gateway_transaction_id: str
    gateway_fee: Optional[Decimal] = None
    
    # Status
    status: PaymentStatus = PaymentStatus.PENDING
    processed_at: Optional[datetime] = None
    
    # Failure handling
    failure_reason: Optional[str] = None
    retry_count: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RevenueShare(BaseModel):
    """Revenue sharing record for hosts"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    host_company_id: str
    invoice_id: str
    
    # Revenue details
    total_revenue: Decimal
    host_share_percentage: Decimal
    host_share_amount: Decimal
    platform_share_amount: Decimal
    
    # Period
    period_start: datetime
    period_end: datetime
    
    # Payout status
    payout_status: str = "pending"  # pending, processed, paid
    payout_date: Optional[datetime] = None
    payout_transaction_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================
# API REQUEST/RESPONSE MODELS
# ==============================

class SlotSearchQuery(BaseModel):
    """Search query for ad slot discovery"""
    # Location filters
    city: Optional[str] = None
    state: Optional[str] = None
    venue_types: List[str] = []
    categories: List[str] = []
    
    # Time filters
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    days_of_week: List[int] = []
    hours_start: Optional[time] = None
    hours_end: Optional[time] = None
    
    # Price filters
    max_price_per_slot: Optional[Decimal] = None
    min_foot_traffic: Optional[str] = None
    
    # Demographics
    target_demographics: Optional[Dict] = None
    
    # Pagination
    page: int = 1
    limit: int = 20


class BookingRequest(BaseModel):
    """Request to book an ad slot"""
    ad_slot_id: str
    campaign_id: Optional[str] = None
    
    # Time details
    start_time: datetime
    end_time: datetime
    
    # Recurring options
    is_recurring: bool = False
    recurrence_type: Optional[str] = None  # daily, weekly, monthly
    recurrence_interval: Optional[int] = None
    end_recurrence_date: Optional[datetime] = None
    
    # Content
    content_id: Optional[str] = None
    
    # Special requests
    special_instructions: Optional[str] = None


class ContentUploadRequest(BaseModel):
    """Request to upload new content"""
    title: str
    description: Optional[str] = None
    campaign_id: Optional[str] = None
    categories: List[str] = []
    tags: List[str] = []
    content_rating: str = "G"
    call_to_action: Optional[str] = None
    landing_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class AnalyticsRequest(BaseModel):
    """Request for analytics data"""
    # Time period
    start_date: datetime
    end_date: datetime
    aggregation: str = "daily"  # hourly, daily, weekly, monthly
    
    # Filters
    location_ids: List[str] = []
    device_ids: List[str] = []
    content_ids: List[str] = []
    campaign_ids: List[str] = []
    
    # Metrics to include
    metrics: List[str] = ["impressions", "revenue", "engagement"]


# ==============================
# RESPONSE MODELS
# ==============================

class SlotAvailability(BaseModel):
    """Ad slot availability response"""
    ad_slot: AdSlot
    available_times: List[Dict]  # Available time slots
    pricing: Dict  # Dynamic pricing info
    restrictions: Dict  # Content/category restrictions


class BookingConfirmation(BaseModel):
    """Booking confirmation response"""
    booking: Booking
    payment_required: bool
    payment_amount: Decimal
    payment_deadline: Optional[datetime] = None
    next_steps: List[str] = []


class AnalyticsResponse(BaseModel):
    """Analytics response model"""
    summary: Dict  # Overall metrics
    time_series: List[Dict]  # Time-based data
    breakdowns: Dict  # Category/location breakdowns
    comparisons: Optional[Dict] = None  # Period comparisons