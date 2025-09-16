"""
Moderation and Review Models for Digital Signage Ad Slot Management System
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class ModerationResult(BaseModel):
    content_id: str
    ai_confidence: float = Field(..., ge=0.0, le=1.0)
    action: str  # approved / quarantine / reject
    reason: Optional[str] = None


class Review(BaseModel):
    id: Optional[str] = None
    content_id: str
    ai_confidence: Optional[float] = None
    action: str  # approved | needs_review | rejected | manual_approve | manual_reject
    reviewer_id: Optional[str] = None
    notes: Optional[str] = None
    ai_analysis: Optional[Dict] = None  # AI analysis details
    created_at: datetime = Field(default_factory=datetime.utcnow)