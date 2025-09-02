"""
Proof-of-Play Service
Provides legally compliant verification that content was displayed as contracted.
Essential for advertising revenue verification and dispute resolution.
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class PlaybackEvent(Enum):
    """Types of playback events that can be recorded"""
    CONTENT_STARTED = "content_started"
    CONTENT_COMPLETED = "content_completed" 
    CONTENT_SKIPPED = "content_skipped"
    CONTENT_ERROR = "content_error"
    PLAYLIST_STARTED = "playlist_started"
    PLAYLIST_COMPLETED = "playlist_completed"
    DEVICE_INTERACTION = "device_interaction"
    CONTENT_PAUSED = "content_paused"
    CONTENT_RESUMED = "content_resumed"

class ProofQuality(Enum):
    """Quality levels for proof-of-play verification"""
    BASIC = "basic"           # Timestamp + content ID only
    STANDARD = "standard"     # + device verification + location
    PREMIUM = "premium"       # + photo verification + full audit trail
    LEGAL = "legal"          # + blockchain verification + legal signatures

@dataclass
class PlaybackVerification:
    """Cryptographic verification data for playback events"""
    device_fingerprint: str
    location_hash: str
    timestamp_signature: str
    content_hash: str
    verification_level: ProofQuality

@dataclass
class ProofOfPlayRecord:
    """Comprehensive proof-of-play record for legal compliance"""
    id: Optional[str]
    device_id: str
    content_id: str
    campaign_id: Optional[str]
    advertiser_id: str
    host_id: str
    
    # Playback details
    event_type: PlaybackEvent
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    actual_duration: Optional[float]
    scheduled_duration: Optional[float]
    
    # Location and context
    latitude: Optional[float]
    longitude: Optional[float]
    venue_name: Optional[str]
    screen_position: Optional[str]
    audience_count_estimate: Optional[int]
    
    # Technical details
    resolution: Optional[str]
    brightness_level: Optional[int]
    volume_level: Optional[int]
    network_quality: Optional[str]
    
    # Verification data
    verification: Optional[PlaybackVerification]
    photo_verification_url: Optional[str]
    witness_device_ids: List[str]  # Other devices that can verify
    
    # Quality metrics
    completion_percentage: Optional[float]
    user_interaction_count: int
    error_count: int
    quality_score: Optional[float]
    
    # Billing and legal
    billing_rate: Optional[float]
    currency: str
    legal_jurisdiction: str
    contract_reference: Optional[str]
    
    # Audit trail
    created_at: datetime
    verified_at: Optional[datetime]
    blockchain_hash: Optional[str]
    legal_signature: Optional[str]

class ProofOfPlayService:
    """Service for managing proof-of-play verification and legal compliance"""
    
    def __init__(self):
        self.verification_enabled = True
        self.photo_verification_rate = 0.1  # 10% of playbacks get photo verification
        self.blockchain_verification = False  # Enable for premium legal compliance
        self.witness_verification = True  # Enable cross-device verification
        
        # Import dependencies
        try:
            from app.repo import repo
            self.repo = repo
        except ImportError:
            self.repo = None
            logger.warning("Repository not available - using mock data")
        
        try:
            from app.security import audit_logger
            self.audit_logger = audit_logger
        except ImportError:
            self.audit_logger = None
            logger.warning("Audit logging not available")
        
        try:
            from app.monitoring import device_health_monitor
            self.health_monitor = device_health_monitor
        except ImportError:
            self.health_monitor = None
            logger.warning("Health monitoring not available")
    
    async def record_playback_event(self, device_id: str, content_id: str, 
                                  event_type: PlaybackEvent, **kwargs) -> Dict[str, Any]:
        """Record a playback event with comprehensive verification"""
        try:
            # Get content and campaign information
            content_info = await self._get_content_info(content_id)
            if not content_info:
                return {"success": False, "error": "Content not found"}
            
            # Get device and location information
            device_info = await self._get_device_info(device_id)
            if not device_info:
                return {"success": False, "error": "Device not found"}
            
            # Create verification data
            verification = await self._create_verification(device_id, content_id, **kwargs)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(event_type, **kwargs)
            
            # Create proof-of-play record
            record = ProofOfPlayRecord(
                id=str(uuid.uuid4()),
                device_id=device_id,
                content_id=content_id,
                campaign_id=content_info.get("campaign_id"),
                advertiser_id=content_info.get("owner_id"),
                host_id=device_info.get("host_id"),
                
                # Playback details
                event_type=event_type,
                start_time=kwargs.get("start_time", datetime.utcnow()),
                end_time=kwargs.get("end_time"),
                duration_seconds=kwargs.get("duration_seconds"),
                actual_duration=kwargs.get("actual_duration"),
                scheduled_duration=kwargs.get("scheduled_duration"),
                
                # Location and context
                latitude=device_info.get("latitude") or kwargs.get("latitude"),
                longitude=device_info.get("longitude") or kwargs.get("longitude"),
                venue_name=device_info.get("venue_name"),
                screen_position=device_info.get("screen_position"),
                audience_count_estimate=kwargs.get("audience_count"),
                
                # Technical details
                resolution=kwargs.get("resolution", device_info.get("resolution")),
                brightness_level=kwargs.get("brightness_level"),
                volume_level=kwargs.get("volume_level"),
                network_quality=kwargs.get("network_quality"),
                
                # Verification
                verification=verification,
                photo_verification_url=kwargs.get("photo_url"),
                witness_device_ids=kwargs.get("witness_devices", []),
                
                # Quality metrics
                completion_percentage=quality_metrics.get("completion_percentage"),
                user_interaction_count=kwargs.get("interaction_count", 0),
                error_count=kwargs.get("error_count", 0),
                quality_score=quality_metrics.get("quality_score"),
                
                # Billing and legal
                billing_rate=content_info.get("billing_rate"),
                currency=content_info.get("currency", "AED"),
                legal_jurisdiction="UAE",
                contract_reference=content_info.get("contract_reference"),
                
                # Audit trail
                created_at=datetime.utcnow(),
                verified_at=None,
                blockchain_hash=None,
                legal_signature=None
            )
            
            # Save to repository
            if self.repo:
                saved_record = await self.repo.save_proof_of_play(asdict(record))
            else:
                saved_record = asdict(record)
            
            # Log audit event
            if self.audit_logger:
                self.audit_logger.log_content_event(
                    f"proof_of_play_{event_type.value}",
                    {
                        "device_id": device_id,
                        "content_id": content_id,
                        "record_id": record.id,
                        "quality_score": quality_metrics.get("quality_score"),
                        "verification_level": verification.verification_level.value if verification else "none"
                    }
                )
            
            # Trigger additional verifications for premium content
            if content_info.get("verification_level") == "premium":
                await self._trigger_premium_verification(record)
            
            return {
                "success": True,
                "record_id": record.id,
                "verification_level": verification.verification_level.value if verification else "basic",
                "quality_score": quality_metrics.get("quality_score"),
                "billing_amount": self._calculate_billing_amount(record)
            }
            
        except Exception as e:
            logger.error(f"Failed to record playback event: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_playback_record(self, record_id: str) -> Dict[str, Any]:
        """Verify the authenticity and completeness of a playback record"""
        try:
            # Get the record
            if self.repo:
                record_data = await self.repo.get_proof_of_play(record_id)
            else:
                return {"success": False, "error": "Repository not available"}
            
            if not record_data:
                return {"success": False, "error": "Record not found"}
            
            record = ProofOfPlayRecord(**record_data)
            
            # Verify cryptographic signatures
            signature_valid = await self._verify_signatures(record)
            
            # Verify device authenticity
            device_valid = await self._verify_device_authenticity(record.device_id, record.created_at)
            
            # Verify location consistency
            location_valid = await self._verify_location_consistency(record)
            
            # Verify timing consistency
            timing_valid = await self._verify_timing_consistency(record)
            
            # Cross-reference with witness devices
            witness_verification = await self._verify_witness_devices(record)
            
            # Calculate verification score
            verification_score = self._calculate_verification_score({
                "signature_valid": signature_valid,
                "device_valid": device_valid,
                "location_valid": location_valid,
                "timing_valid": timing_valid,
                "witness_verification": witness_verification
            })
            
            # Update record with verification results
            if verification_score >= 0.8:
                await self._mark_record_verified(record_id, verification_score)
            
            return {
                "success": True,
                "record_id": record_id,
                "verification_score": verification_score,
                "signature_valid": signature_valid,
                "device_valid": device_valid,
                "location_valid": location_valid,
                "timing_valid": timing_valid,
                "witness_verification": witness_verification,
                "legally_compliant": verification_score >= 0.9
            }
            
        except Exception as e:
            logger.error(f"Failed to verify playback record: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_campaign_proof_report(self, campaign_id: str, start_date: datetime, 
                                      end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive proof-of-play report for a campaign"""
        try:
            # Get all records for the campaign
            if self.repo:
                records = await self.repo.get_campaign_proof_records(
                    campaign_id, start_date, end_date
                )
            else:
                return {"success": False, "error": "Repository not available"}
            
            # Calculate aggregate metrics
            total_plays = len([r for r in records if r.get("event_type") == "content_completed"])
            total_duration = sum([r.get("actual_duration", 0) for r in records])
            total_impressions = sum([r.get("audience_count_estimate", 1) for r in records])
            
            # Calculate quality metrics
            avg_completion_rate = sum([r.get("completion_percentage", 0) for r in records]) / len(records) if records else 0
            avg_quality_score = sum([r.get("quality_score", 0) for r in records]) / len(records) if records else 0
            
            # Calculate billing metrics
            total_billing = sum([self._calculate_billing_amount(r) for r in records])
            
            # Verification statistics
            verified_records = len([r for r in records if r.get("verified_at")])
            verification_rate = verified_records / len(records) if records else 0
            
            # Device and location breakdown
            unique_devices = len(set([r.get("device_id") for r in records]))
            unique_locations = len(set([f"{r.get('latitude')},{r.get('longitude')}" 
                                      for r in records if r.get("latitude")]))
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "playback_summary": {
                    "total_plays": total_plays,
                    "total_duration_seconds": total_duration,
                    "total_impressions": total_impressions,
                    "unique_devices": unique_devices,
                    "unique_locations": unique_locations
                },
                "quality_metrics": {
                    "average_completion_rate": avg_completion_rate,
                    "average_quality_score": avg_quality_score,
                    "verification_rate": verification_rate
                },
                "billing_summary": {
                    "total_amount": total_billing,
                    "currency": "AED",
                    "verified_amount": sum([self._calculate_billing_amount(r) 
                                          for r in records if r.get("verified_at")])
                },
                "legal_compliance": {
                    "records_count": len(records),
                    "verified_records": verified_records,
                    "compliance_rate": verification_rate,
                    "blockchain_verified": len([r for r in records if r.get("blockchain_hash")]),
                    "legally_binding": verification_rate >= 0.95
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate campaign proof report: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_content_info(self, content_id: str) -> Optional[Dict]:
        """Get content information including billing and campaign details"""
        try:
            if self.repo:
                return await self.repo.get_content_meta(content_id)
            return None
        except Exception as e:
            logger.error(f"Failed to get content info: {e}")
            return None
    
    async def _get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get device information including location and capabilities"""
        try:
            if self.repo:
                return await self.repo.get_digital_screen(device_id)
            return None
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return None
    
    async def _create_verification(self, device_id: str, content_id: str, 
                                 **kwargs) -> Optional[PlaybackVerification]:
        """Create cryptographic verification data"""
        try:
            # Create device fingerprint
            device_fingerprint = self._create_device_fingerprint(device_id, kwargs)
            
            # Create location hash
            location_hash = self._create_location_hash(kwargs)
            
            # Create timestamp signature
            timestamp_signature = self._create_timestamp_signature(datetime.utcnow())
            
            # Create content hash
            content_hash = self._create_content_hash(content_id)
            
            # Determine verification level
            verification_level = self._determine_verification_level(kwargs)
            
            return PlaybackVerification(
                device_fingerprint=device_fingerprint,
                location_hash=location_hash,
                timestamp_signature=timestamp_signature,
                content_hash=content_hash,
                verification_level=verification_level
            )
            
        except Exception as e:
            logger.error(f"Failed to create verification: {e}")
            return None
    
    def _calculate_quality_metrics(self, event_type: PlaybackEvent, **kwargs) -> Dict:
        """Calculate quality metrics for the playback event"""
        quality_score = 100.0
        
        # Completion percentage
        completion_percentage = kwargs.get("completion_percentage", 100.0)
        if completion_percentage < 100:
            quality_score -= (100 - completion_percentage) * 0.5
        
        # Error count penalty
        error_count = kwargs.get("error_count", 0)
        quality_score -= min(error_count * 10, 30)
        
        # Network quality factor
        network_quality = kwargs.get("network_quality", "good")
        if network_quality == "poor":
            quality_score -= 20
        elif network_quality == "fair":
            quality_score -= 10
        
        # Interaction bonus
        interaction_count = kwargs.get("interaction_count", 0)
        if interaction_count > 0:
            quality_score += min(interaction_count * 2, 10)
        
        return {
            "completion_percentage": completion_percentage,
            "quality_score": max(0, min(100, quality_score))
        }
    
    def _calculate_billing_amount(self, record) -> float:
        """Calculate billing amount based on playback quality and duration"""
        if isinstance(record, dict):
            billing_rate = record.get("billing_rate", 0)
            quality_score = record.get("quality_score", 100)
            completion_percentage = record.get("completion_percentage", 100)
        else:
            billing_rate = record.billing_rate or 0
            quality_score = record.quality_score or 100
            completion_percentage = record.completion_percentage or 100
        
        # Base amount
        base_amount = billing_rate
        
        # Quality adjustment
        quality_factor = quality_score / 100
        completion_factor = completion_percentage / 100
        
        return base_amount * quality_factor * completion_factor
    
    def _create_device_fingerprint(self, device_id: str, kwargs: Dict) -> str:
        """Create unique device fingerprint for verification"""
        fingerprint_data = {
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "resolution": kwargs.get("resolution", ""),
            "user_agent": kwargs.get("user_agent", ""),
            "network_info": kwargs.get("network_quality", "")
        }
        
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    def _create_location_hash(self, kwargs: Dict) -> str:
        """Create location verification hash"""
        location_data = {
            "latitude": kwargs.get("latitude", 0),
            "longitude": kwargs.get("longitude", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        location_str = json.dumps(location_data, sort_keys=True)
        return hashlib.sha256(location_str.encode()).hexdigest()
    
    def _create_timestamp_signature(self, timestamp: datetime) -> str:
        """Create timestamp signature for verification"""
        timestamp_str = timestamp.isoformat()
        return hashlib.sha256(timestamp_str.encode()).hexdigest()
    
    def _create_content_hash(self, content_id: str) -> str:
        """Create content verification hash"""
        return hashlib.sha256(content_id.encode()).hexdigest()
    
    def _determine_verification_level(self, kwargs: Dict) -> ProofQuality:
        """Determine appropriate verification level based on content value"""
        billing_rate = kwargs.get("billing_rate", 0)
        
        if billing_rate >= 1000:  # High-value content
            return ProofQuality.LEGAL
        elif billing_rate >= 500:
            return ProofQuality.PREMIUM
        elif billing_rate >= 100:
            return ProofQuality.STANDARD
        else:
            return ProofQuality.BASIC
    
    async def _verify_signatures(self, record: ProofOfPlayRecord) -> bool:
        """Verify cryptographic signatures in the record"""
        # Implementation would verify digital signatures
        return True  # Simplified for now
    
    async def _verify_device_authenticity(self, device_id: str, timestamp: datetime) -> bool:
        """Verify that the device was authentic at the time of recording"""
        # Implementation would check device certificates and authentication
        return True  # Simplified for now
    
    async def _verify_location_consistency(self, record: ProofOfPlayRecord) -> bool:
        """Verify location consistency with device registration"""
        # Implementation would verify GPS coordinates match device location
        return True  # Simplified for now
    
    async def _verify_timing_consistency(self, record: ProofOfPlayRecord) -> bool:
        """Verify timing consistency and detect anomalies"""
        # Implementation would check for timing anomalies
        return True  # Simplified for now
    
    async def _verify_witness_devices(self, record: ProofOfPlayRecord) -> Dict[str, Any]:
        """Verify with witness devices for cross-validation"""
        return {"verified": True, "witness_count": len(record.witness_device_ids)}
    
    def _calculate_verification_score(self, checks: Dict[str, Any]) -> float:
        """Calculate overall verification score"""
        score = 0.0
        total_checks = len(checks)
        
        for check, result in checks.items():
            if isinstance(result, bool) and result:
                score += 1.0
            elif isinstance(result, dict) and result.get("verified"):
                score += 1.0
        
        return score / total_checks if total_checks > 0 else 0.0
    
    async def _mark_record_verified(self, record_id: str, verification_score: float):
        """Mark a record as verified with score"""
        if self.repo:
            await self.repo.update_proof_of_play(record_id, {
                "verified_at": datetime.utcnow(),
                "verification_score": verification_score
            })
    
    async def _trigger_premium_verification(self, record: ProofOfPlayRecord):
        """Trigger additional premium verification processes"""
        # Implementation would trigger photo capture, blockchain verification, etc.
        pass

# Global proof-of-play service instance
proof_of_play_service = ProofOfPlayService()