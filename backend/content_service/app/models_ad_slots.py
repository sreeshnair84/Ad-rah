"""
Digital Signage Ad Slot Management System Models
===============================================

This module contains all models for the ad slot marketplace functionality:
- Ad slot inventory management
- Booking and scheduling
- Billing and invoicing
- Proof-of-play tracking
- Revenue sharing
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime, date, time
from enum import Enum
import uuid


# ==================== ENUMS ====================

class AdSlotStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"

class BookingStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PlaybackStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
    SKIPPED = "skipped"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class ContentRating(str, Enum):
    G = "G"           # General audiences
    PG = "PG"         # Parental guidance
    PG13 = "PG-13"    # Parents strongly cautioned
    R = "R"           # Restricted
    NC17 = "NC-17"    # Adults only

class TimeSlotType(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ==================== LOCATION & DEVICE MODELS ====================

class Location(BaseModel):
    """Physical location information for ad slots"""
    id: Optional[str] = None
    host_company_id: str
    name: str                          # "Dubai Mall - Main Entrance"
    description: Optional[str] = None
    address: str
    city: str
    country: str
    coordinates: Optional[Dict] = None  # {"lat": 25.1972, "lng": 55.2744}
    timezone: str = "Asia/Dubai"

    # Location categorization
    venue_type: str                    # "mall", "airport", "gym", "restaurant"
    foot_traffic_level: str = "medium" # "low", "medium", "high", "very_high"
    demographics: Dict = Field(default_factory=dict)  # Target audience info

    # Operational info
    operating_hours: Dict = Field(default_factory=dict)  # {"monday": {"open": "09:00", "close": "22:00"}}
    peak_hours: List[str] = Field(default_factory=list)  # ["09:00-11:00", "18:00-21:00"]

    status: str = "active"  # active, inactive, maintenance
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Device(BaseModel):
    """Digital signage device/screen"""
    id: Optional[str] = None
    host_company_id: str
    location_id: str
    name: str                          # "Mall Entrance Screen 1"
    description: Optional[str] = None

    # Device specifications
    screen_size_inches: float
    resolution_width: int = 1920
    resolution_height: int = 1080
    orientation: str = "landscape"     # landscape, portrait

    # Device capabilities
    supports_touch: bool = False
    supports_audio: bool = True
    supports_video: bool = True
    max_content_duration: int = 300    # seconds

    # API authentication
    api_key: str
    registration_key: str

    # Status and monitoring
    status: str = "active"             # active, inactive, maintenance, offline
    last_seen: Optional[datetime] = None
    last_content_sync: Optional[datetime] = None

    # Performance metrics
    uptime_percentage: float = 99.0
    average_response_time: int = 200   # milliseconds

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== AD SLOT MODELS ====================

class AdSlot(BaseModel):
    """Individual ad slot inventory"""
    id: Optional[str] = None
    host_company_id: str
    location_id: str
    device_id: str

    # Slot identification
    slot_name: str                     # "Morning Rush Hour - Main Screen"
    slot_code: str                     # "MALL-ENT-001-MRH" (unique identifier)

    # Time definition
    start_time: time                   # Daily start time (e.g., 09:00)
    end_time: time                     # Daily end time (e.g., 10:00)
    days_of_week: List[int]            # [1,2,3,4,5] (Monday=1, Sunday=7)
    duration_seconds: int              # Length of individual ad play
    slots_per_hour: int                # How many ad slots per hour

    # Pricing
    base_price_per_slot: float         # Base price per individual slot
    peak_multiplier: float = 1.0       # Multiplier for peak hours
    weekend_multiplier: float = 1.0    # Multiplier for weekends

    # Content restrictions
    max_content_duration: int = 30     # Maximum seconds per ad
    allowed_content_types: List[str] = ["video", "image"]
    content_rating_limit: ContentRating = ContentRating.PG
    blocked_categories: List[str] = Field(default_factory=list)

    # Availability
    status: AdSlotStatus = AdSlotStatus.AVAILABLE
    blocked_dates: List[date] = Field(default_factory=list)  # Specific dates unavailable

    # Performance data
    average_impressions_per_slot: int = 0
    average_engagement_rate: float = 0.0
    historical_ctr: float = 0.0        # Click-through rate

    # Revenue sharing
    host_revenue_percentage: float = 70.0  # Host gets 70%, platform gets 30%

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AdSlotAvailability(BaseModel):
    """Real-time availability for specific dates"""
    id: Optional[str] = None
    ad_slot_id: str
    date: date
    available_slots: int               # How many slots still available for this date
    booked_slots: int                  # How many already booked
    total_slots: int                   # Total slots for the day

    # Dynamic pricing
    current_price_per_slot: float      # Current price (may differ from base)
    demand_multiplier: float = 1.0     # Based on demand

    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ==================== BOOKING MODELS ====================

class AdBooking(BaseModel):
    """Advertiser booking for ad slots"""
    id: Optional[str] = None
    booking_number: str                # "BK-2025-001234"

    # Parties involved
    advertiser_company_id: str
    host_company_id: str
    ad_slot_id: str

    # Booking details
    content_id: str                    # Reference to uploaded content
    start_date: date
    end_date: date
    total_slots_booked: int

    # Pricing
    price_per_slot: float
    total_amount: float
    currency: str = "AED"

    # Status tracking
    status: BookingStatus = BookingStatus.DRAFT
    booking_date: datetime = Field(default_factory=datetime.utcnow)

    # Approval workflow
    requires_approval: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Campaign information
    campaign_name: str
    campaign_description: Optional[str] = None
    target_demographics: Dict = Field(default_factory=dict)

    # Performance tracking
    actual_slots_played: int = 0
    total_impressions: int = 0
    total_interactions: int = 0
    completion_rate: float = 0.0

    # Billing
    invoice_id: Optional[str] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING

    created_by: str                    # User who created the booking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BookingSlotDetail(BaseModel):
    """Individual slot booking detail within a booking"""
    id: Optional[str] = None
    booking_id: str
    ad_slot_id: str
    scheduled_date: date
    scheduled_time_slot: str           # "09:00-09:30"
    position_in_rotation: int = 1      # If multiple ads in same slot

    # Playback tracking
    status: str = "scheduled"          # scheduled, played, skipped, error
    actual_play_time: Optional[datetime] = None
    duration_played: int = 0           # Actual seconds played
    impressions_recorded: int = 0
    interactions_recorded: int = 0

    # Revenue calculation
    slot_rate: float                   # Rate for this specific slot
    revenue_generated: float = 0.0
    host_revenue: float = 0.0
    platform_revenue: float = 0.0

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== CONTENT MODERATION MODELS ====================

class ContentModerationQueue(BaseModel):
    """Content moderation queue for advertiser content"""
    id: Optional[str] = None
    content_id: str
    advertiser_company_id: str
    booking_id: Optional[str] = None

    # Content information
    content_title: str
    content_type: str                  # video, image, html5
    file_size_mb: float
    duration_seconds: Optional[int] = None

    # AI Moderation (future-ready)
    ai_moderation_status: str = "pending"  # pending, approved, flagged, error
    ai_confidence_score: Optional[float] = None
    ai_flags: List[str] = Field(default_factory=list)  # ["inappropriate_content", "logo_violation"]
    ai_processed_at: Optional[datetime] = None

    # Human Review (MVP implementation)
    review_status: str = "pending"     # pending, approved, rejected
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    # Review priority
    priority: str = "normal"           # low, normal, high, urgent
    review_deadline: Optional[datetime] = None

    # Escalation
    escalated: bool = False
    escalated_to: Optional[str] = None
    escalation_reason: Optional[str] = None

    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== PLAYBACK & PROOF-OF-PLAY MODELS ====================

class PlaybackLog(BaseModel):
    """Proof-of-play logging for each ad playback"""
    id: Optional[str] = None

    # Identifiers
    booking_slot_detail_id: str
    device_id: str
    content_id: str
    ad_slot_id: str

    # Playback details
    scheduled_start_time: datetime
    actual_start_time: datetime
    actual_end_time: Optional[datetime] = None
    duration_played_seconds: int
    total_content_duration_seconds: int

    # Status and quality
    playback_status: PlaybackStatus
    completion_percentage: float = 0.0  # 0-100

    # Technical information
    device_status: str = "online"      # online, offline, maintenance
    network_status: str = "connected"  # connected, disconnected, poor
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Audience analytics (privacy-compliant)
    estimated_impressions: int = 0     # Estimated viewers
    interaction_count: int = 0         # Touches, gestures, etc.
    audience_engagement_score: float = 0.0  # 0-10 scale

    # Environmental context
    ambient_light_level: Optional[str] = None  # bright, normal, dim
    noise_level: Optional[str] = None  # quiet, normal, loud
    temperature_celsius: Optional[float] = None

    # Revenue calculation
    billable_duration_seconds: int = 0  # Only count successful playback
    revenue_generated: float = 0.0

    # Verification
    proof_hash: Optional[str] = None   # Cryptographic proof for audit
    verification_status: str = "verified"  # verified, disputed, pending

    created_at: datetime = Field(default_factory=datetime.utcnow)


class PlaybackStatistics(BaseModel):
    """Aggregated playback statistics for reporting"""
    id: Optional[str] = None

    # Time period
    date: date
    hour: int                          # 0-23 for hourly aggregation

    # Identifiers
    device_id: str
    ad_slot_id: str
    advertiser_company_id: str
    host_company_id: str

    # Aggregated metrics
    total_scheduled_slots: int = 0
    total_played_slots: int = 0
    total_skipped_slots: int = 0
    total_error_slots: int = 0

    # Performance metrics
    success_rate: float = 0.0          # Percentage of successful plays
    average_completion_rate: float = 0.0
    total_impressions: int = 0
    total_interactions: int = 0

    # Revenue metrics
    total_revenue_generated: float = 0.0
    host_revenue_share: float = 0.0
    platform_revenue_share: float = 0.0

    # Quality metrics
    average_playback_quality: float = 0.0
    network_reliability: float = 0.0
    device_uptime: float = 0.0

    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ==================== BILLING & INVOICING MODELS ====================

class Invoice(BaseModel):
    """Invoice for ad slot bookings"""
    id: Optional[str] = None
    invoice_number: str                # "INV-2025-001234"

    # Parties
    advertiser_company_id: str
    host_company_id: str
    billing_period_start: date
    billing_period_end: date

    # Invoice details
    currency: str = "AED"
    subtotal: float = 0.0
    tax_rate: float = 5.0              # VAT percentage
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0

    # Line items (stored as JSON)
    line_items: List[Dict] = Field(default_factory=list)

    # Payment terms
    payment_due_date: date
    payment_terms_days: int = 30       # Net 30

    # Status tracking
    status: InvoiceStatus = InvoiceStatus.DRAFT
    issued_date: Optional[date] = None
    paid_date: Optional[date] = None

    # Proof-of-play summary
    total_slots_scheduled: int = 0
    total_slots_played: int = 0
    fulfillment_rate: float = 0.0      # Percentage of slots actually played

    # Adjustments
    adjustments: List[Dict] = Field(default_factory=list)  # Credits, penalties

    # Payment information
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_gateway_id: Optional[str] = None

    # Host revenue sharing
    host_payout_amount: float = 0.0
    host_payout_status: str = "pending"  # pending, processed, completed
    host_payout_date: Optional[date] = None

    # Audit trail
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class InvoiceLineItem(BaseModel):
    """Individual line item in an invoice"""
    id: Optional[str] = None
    invoice_id: str
    booking_id: str

    # Item details
    description: str                   # "Ad slots at Dubai Mall - Main Entrance"
    ad_slot_name: str
    date_range: str                    # "Jan 1-7, 2025"

    # Quantities
    scheduled_slots: int
    played_slots: int
    rate_per_slot: float

    # Calculations
    gross_amount: float
    adjustment_amount: float = 0.0     # Credits for missed slots
    net_amount: float

    # Proof verification
    proof_documents: List[str] = Field(default_factory=list)  # File references
    verification_status: str = "verified"

    created_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentTransaction(BaseModel):
    """Payment transaction record"""
    id: Optional[str] = None
    transaction_number: str            # "PAY-2025-001234"
    invoice_id: str

    # Payment details
    amount: float
    currency: str = "AED"
    payment_method: str                # stripe, paypal, bank_transfer
    payment_gateway: str
    gateway_transaction_id: str

    # Status
    status: PaymentStatus = PaymentStatus.PENDING

    # Timestamps
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Failure information
    failure_reason: Optional[str] = None
    failure_code: Optional[str] = None
    retry_count: int = 0

    # Gateway response
    gateway_response: Dict = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== REVENUE SHARING MODELS ====================

class HostPayout(BaseModel):
    """Payout to host companies"""
    id: Optional[str] = None
    payout_number: str                 # "PO-2025-001234"
    host_company_id: str

    # Payout period
    period_start: date
    period_end: date

    # Financial details
    gross_revenue: float               # Total revenue from host's slots
    platform_commission: float        # Platform's share
    net_payout: float                  # Amount to pay host
    currency: str = "AED"

    # Included invoices
    invoice_ids: List[str] = Field(default_factory=list)

    # Payout details
    payout_method: str = "bank_transfer"  # bank_transfer, paypal, check
    bank_account_id: Optional[str] = None

    # Status
    status: str = "pending"            # pending, processing, completed, failed
    processed_date: Optional[date] = None
    reference_number: Optional[str] = None

    # Verification
    verification_documents: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== ANALYTICS MODELS ====================

class PerformanceMetrics(BaseModel):
    """Performance analytics for slots, campaigns, etc."""
    id: Optional[str] = None

    # Scope
    metric_type: str                   # "slot", "campaign", "device", "location"
    entity_id: str                     # ID of the entity being measured

    # Time period
    date: date
    hour: Optional[int] = None         # For hourly granularity

    # Basic metrics
    impressions: int = 0
    clicks: int = 0
    interactions: int = 0
    completions: int = 0

    # Calculated metrics
    ctr: float = 0.0                   # Click-through rate
    completion_rate: float = 0.0
    engagement_rate: float = 0.0

    # Revenue metrics
    revenue: float = 0.0
    cost_per_impression: float = 0.0
    cost_per_click: float = 0.0

    # Quality metrics
    technical_success_rate: float = 0.0
    content_quality_score: float = 0.0
    audience_satisfaction: float = 0.0

    last_calculated: datetime = Field(default_factory=datetime.utcnow)


# ==================== REQUEST/RESPONSE MODELS ====================

class AdSlotSearchRequest(BaseModel):
    """Search for available ad slots"""
    # Location filters
    city: Optional[str] = None
    venue_types: Optional[List[str]] = None
    foot_traffic_levels: Optional[List[str]] = None

    # Time filters
    start_date: date
    end_date: date
    time_slots: Optional[List[str]] = None  # ["09:00-10:00", "18:00-19:00"]
    days_of_week: Optional[List[int]] = None

    # Budget filters
    max_price_per_slot: Optional[float] = None
    total_budget: Optional[float] = None

    # Content filters
    content_duration: Optional[int] = None
    content_rating: Optional[ContentRating] = None

    # Sorting
    sort_by: str = "price"             # price, impressions, engagement, location
    sort_order: str = "asc"            # asc, desc

    # Pagination
    page: int = 1
    page_size: int = 20


class AdSlotSearchResponse(BaseModel):
    """Search results for ad slots"""
    slots: List[Dict]                  # Detailed slot information
    total_count: int
    total_pages: int
    current_page: int

    # Summary statistics
    price_range: Dict[str, float]      # {"min": 50, "max": 500}
    total_impressions: int
    average_engagement_rate: float


class BookingCreateRequest(BaseModel):
    """Create new booking request"""
    ad_slot_id: str
    content_id: str
    start_date: date
    end_date: date
    time_slots: List[str]              # Specific time slots within the ad slot

    campaign_name: str
    campaign_description: Optional[str] = None

    # Budget confirmation
    max_total_budget: float
    acknowledged_terms: bool = True


class BookingUpdateRequest(BaseModel):
    """Update booking request"""
    campaign_name: Optional[str] = None
    campaign_description: Optional[str] = None
    time_slots: Optional[List[str]] = None

    # Only allowed before approval
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class BookingApprovalRequest(BaseModel):
    """Host approval/rejection of booking"""
    action: Literal["approve", "reject"]
    notes: Optional[str] = None

    # Approval with modifications
    modified_price: Optional[float] = None
    modified_time_slots: Optional[List[str]] = None
    conditions: Optional[str] = None


class ProofOfPlayRequest(BaseModel):
    """Request proof-of-play report"""
    booking_ids: Optional[List[str]] = None
    start_date: date
    end_date: date
    format: str = "pdf"                # pdf, csv, json
    include_technical_details: bool = False
    group_by: str = "booking"          # booking, slot, date


# ==================== CREATE/UPDATE MODELS ====================

class LocationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    city: str
    country: str
    venue_type: str
    foot_traffic_level: str = "medium"
    operating_hours: Dict = Field(default_factory=dict)
    peak_hours: List[str] = Field(default_factory=list)


class DeviceCreate(BaseModel):
    location_id: str
    name: str
    description: Optional[str] = None
    screen_size_inches: float
    resolution_width: int = 1920
    resolution_height: int = 1080
    orientation: str = "landscape"
    supports_touch: bool = False
    supports_audio: bool = True
    max_content_duration: int = 300


class AdSlotCreate(BaseModel):
    location_id: str
    device_id: str
    slot_name: str
    start_time: time
    end_time: time
    days_of_week: List[int]
    duration_seconds: int
    slots_per_hour: int
    base_price_per_slot: float
    max_content_duration: int = 30
    allowed_content_types: List[str] = ["video", "image"]
    content_rating_limit: ContentRating = ContentRating.PG
    host_revenue_percentage: float = 70.0


class AdSlotUpdate(BaseModel):
    slot_name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days_of_week: Optional[List[int]] = None
    base_price_per_slot: Optional[float] = None
    status: Optional[AdSlotStatus] = None
    blocked_dates: Optional[List[date]] = None
    host_revenue_percentage: Optional[float] = None