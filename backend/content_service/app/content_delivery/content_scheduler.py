"""
Content Scheduler Service
Manages content scheduling, playlist generation, and content distribution timing.
Ensures optimal content delivery based on audience analytics and device capabilities.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class DeliveryMode(Enum):
    """Content delivery modes"""
    IMMEDIATE = "immediate"       # Deliver immediately
    SCHEDULED = "scheduled"       # Deliver at specific time
    OPTIMIZED = "optimized"       # Deliver at optimal time based on analytics
    EMERGENCY = "emergency"       # Emergency override delivery
    MAINTENANCE = "maintenance"   # Maintenance window delivery

class SchedulePriority(Enum):
    """Schedule priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5

class ContentType(Enum):
    """Content types for scheduling"""
    IMAGE = "image"
    VIDEO = "video"
    HTML = "html"
    PLAYLIST = "playlist"
    EMERGENCY_ALERT = "emergency_alert"
    MAINTENANCE_MESSAGE = "maintenance_message"

@dataclass
class TimeSlot:
    """Represents a time slot for content scheduling"""
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    audience_estimate: Optional[int] = None
    peak_hours: bool = False
    special_event: Optional[str] = None

@dataclass  
class ContentSchedule:
    """Comprehensive content schedule with targeting and optimization"""
    id: Optional[str]
    content_id: str
    campaign_id: Optional[str]
    device_ids: List[str]
    
    # Scheduling details
    start_date: datetime
    end_date: datetime
    time_slots: List[TimeSlot]
    delivery_mode: DeliveryMode
    priority: SchedulePriority
    
    # Targeting and optimization
    target_audience: Dict[str, Any]  # Demographics, interests, etc.
    location_targeting: Dict[str, Any]  # Geographic constraints
    device_requirements: Dict[str, Any]  # Technical requirements
    weather_conditions: Optional[Dict[str, Any]]  # Weather-based targeting
    
    # Frequency and rotation
    frequency_cap: Optional[int]  # Max plays per day/hour
    rotation_weight: float  # Weight in rotation algorithm
    minimum_gap_minutes: int  # Minimum gap between plays
    
    # Performance optimization
    optimal_times: List[str]  # Preferred time slots
    audience_multiplier: float  # Audience size factor
    engagement_target: float  # Target engagement score
    
    # Business rules
    exclusion_rules: List[Dict[str, Any]]  # Content exclusion rules
    competitive_separation: bool  # Separate competing brands
    brand_safety_level: str  # Brand safety requirements
    
    # Status and metadata
    status: str
    created_by: str
    approved_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Analytics and reporting
    total_impressions: int = 0
    total_plays: int = 0
    average_engagement: float = 0.0
    revenue_generated: float = 0.0

class ContentSchedulerService:
    """Service for managing content scheduling and optimization"""
    
    def __init__(self):
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
            from app.content_delivery.proof_of_play import proof_of_play_service
            self.proof_service = proof_of_play_service
        except ImportError:
            self.proof_service = None
            logger.warning("Proof-of-play service not available")
        
        # Scheduling configuration
        self.default_schedule_window_days = 30
        self.max_schedules_per_device = 100
        self.optimization_enabled = True
        self.emergency_override_enabled = True
        
        # Content rotation settings
        self.default_rotation_algorithm = "weighted_round_robin"
        self.audience_optimization = True
        self.weather_integration = False  # Future enhancement
        
    async def create_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new content schedule with optimization"""
        try:
            # Validate schedule data
            validation_result = await self._validate_schedule_data(schedule_data)
            if not validation_result["valid"]:
                return {"success": False, "errors": validation_result["errors"]}
            
            # Create time slots if not provided
            if not schedule_data.get("time_slots"):
                time_slots = await self._generate_optimal_time_slots(
                    schedule_data.get("start_date"),
                    schedule_data.get("end_date"),
                    schedule_data.get("device_ids", []),
                    schedule_data.get("target_audience", {})
                )
                schedule_data["time_slots"] = time_slots
            
            # Create schedule object
            schedule = ContentSchedule(
                id=str(uuid.uuid4()),
                content_id=schedule_data["content_id"],
                campaign_id=schedule_data.get("campaign_id"),
                device_ids=schedule_data["device_ids"],
                
                start_date=datetime.fromisoformat(schedule_data["start_date"]),
                end_date=datetime.fromisoformat(schedule_data["end_date"]),
                time_slots=[TimeSlot(**slot) for slot in schedule_data["time_slots"]],
                delivery_mode=DeliveryMode(schedule_data.get("delivery_mode", "scheduled")),
                priority=SchedulePriority(schedule_data.get("priority", 2)),
                
                target_audience=schedule_data.get("target_audience", {}),
                location_targeting=schedule_data.get("location_targeting", {}),
                device_requirements=schedule_data.get("device_requirements", {}),
                weather_conditions=schedule_data.get("weather_conditions"),
                
                frequency_cap=schedule_data.get("frequency_cap"),
                rotation_weight=schedule_data.get("rotation_weight", 1.0),
                minimum_gap_minutes=schedule_data.get("minimum_gap_minutes", 30),
                
                optimal_times=schedule_data.get("optimal_times", []),
                audience_multiplier=schedule_data.get("audience_multiplier", 1.0),
                engagement_target=schedule_data.get("engagement_target", 0.5),
                
                exclusion_rules=schedule_data.get("exclusion_rules", []),
                competitive_separation=schedule_data.get("competitive_separation", True),
                brand_safety_level=schedule_data.get("brand_safety_level", "standard"),
                
                status="pending_approval",
                created_by=schedule_data["created_by"],
                approved_by=None,
                created_at=datetime.utcnow(),
                updated_at=None
            )
            
            # Check for conflicts
            conflicts = await self._check_schedule_conflicts(schedule)
            if conflicts:
                return {
                    "success": False, 
                    "error": "Schedule conflicts detected",
                    "conflicts": conflicts
                }
            
            # Save schedule
            if self.repo:
                saved_schedule = await self.repo.save_content_schedule(asdict(schedule))
            else:
                saved_schedule = asdict(schedule)
            
            # Log audit event
            if self.audit_logger:
                self.audit_logger.log_content_event("schedule_created", {
                    "schedule_id": schedule.id,
                    "content_id": schedule.content_id,
                    "device_count": len(schedule.device_ids),
                    "priority": schedule.priority.name,
                    "delivery_mode": schedule.delivery_mode.value
                })
            
            # If immediate delivery, trigger deployment
            if schedule.delivery_mode == DeliveryMode.IMMEDIATE:
                await self._trigger_immediate_deployment(schedule)
            
            return {
                "success": True,
                "schedule_id": schedule.id,
                "status": schedule.status,
                "conflicts_resolved": len(conflicts) == 0,
                "estimated_impressions": self._calculate_estimated_impressions(schedule)
            }
            
        except Exception as e:
            logger.error(f"Failed to create schedule: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_device_playlist(self, device_id: str, target_time: datetime = None) -> Dict[str, Any]:
        """Generate optimized playlist for a specific device at a given time"""
        try:
            if not target_time:
                target_time = datetime.utcnow()
            
            # Get active schedules for this device
            schedules = await self._get_active_schedules(device_id, target_time)
            
            if not schedules:
                return {
                    "success": True,
                    "device_id": device_id,
                    "playlist": [],
                    "message": "No active schedules"
                }
            
            # Get device capabilities and status
            device_info = await self._get_device_info(device_id)
            if not device_info:
                return {"success": False, "error": "Device not found"}
            
            # Apply content filters and business rules
            filtered_schedules = await self._apply_content_filters(schedules, device_info)
            
            # Optimize playlist order
            optimized_playlist = await self._optimize_playlist_order(
                filtered_schedules, device_info, target_time
            )
            
            # Generate playlist with timing
            playlist = await self._generate_playlist_with_timing(optimized_playlist, target_time)
            
            # Track playlist generation
            if self.audit_logger:
                self.audit_logger.log_content_event("playlist_generated", {
                    "device_id": device_id,
                    "content_count": len(playlist),
                    "total_duration": sum([item.get("duration", 0) for item in playlist]),
                    "optimization_applied": self.optimization_enabled
                })
            
            return {
                "success": True,
                "device_id": device_id,
                "generated_at": target_time.isoformat(),
                "playlist": playlist,
                "next_update": self._calculate_next_playlist_update(target_time),
                "optimization_score": self._calculate_optimization_score(playlist)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate playlist for device {device_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_schedule_performance(self, schedule_id: str, performance_data: Dict) -> Dict[str, Any]:
        """Update schedule with performance data from proof-of-play"""
        try:
            # Get current schedule
            if self.repo:
                schedule_data = await self.repo.get_content_schedule(schedule_id)
            else:
                return {"success": False, "error": "Repository not available"}
            
            if not schedule_data:
                return {"success": False, "error": "Schedule not found"}
            
            # Update performance metrics
            updates = {
                "total_impressions": schedule_data.get("total_impressions", 0) + performance_data.get("impressions", 0),
                "total_plays": schedule_data.get("total_plays", 0) + performance_data.get("plays", 0),
                "revenue_generated": schedule_data.get("revenue_generated", 0) + performance_data.get("revenue", 0),
                "updated_at": datetime.utcnow()
            }
            
            # Calculate new average engagement
            current_plays = schedule_data.get("total_plays", 0)
            new_plays = performance_data.get("plays", 0)
            if current_plays + new_plays > 0:
                current_engagement = schedule_data.get("average_engagement", 0)
                new_engagement = performance_data.get("engagement", 0)
                
                updates["average_engagement"] = (
                    (current_engagement * current_plays) + (new_engagement * new_plays)
                ) / (current_plays + new_plays)
            
            # Update schedule
            if self.repo:
                success = await self.repo.update_content_schedule(schedule_id, updates)
            else:
                success = False
            
            return {
                "success": success,
                "schedule_id": schedule_id,
                "updated_metrics": updates
            }
            
        except Exception as e:
            logger.error(f"Failed to update schedule performance: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_emergency_override(self, device_ids: List[str], 
                                      emergency_content_id: str, 
                                      duration_minutes: int,
                                      authorized_by: str) -> Dict[str, Any]:
        """Handle emergency content override"""
        try:
            if not self.emergency_override_enabled:
                return {"success": False, "error": "Emergency override not enabled"}
            
            # Create emergency schedule
            emergency_schedule = ContentSchedule(
                id=str(uuid.uuid4()),
                content_id=emergency_content_id,
                campaign_id=f"EMERGENCY_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                device_ids=device_ids,
                
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(minutes=duration_minutes),
                time_slots=[TimeSlot(
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow() + timedelta(minutes=duration_minutes),
                    duration_minutes=duration_minutes,
                    peak_hours=True,
                    special_event="emergency_override"
                )],
                delivery_mode=DeliveryMode.EMERGENCY,
                priority=SchedulePriority.EMERGENCY,
                
                target_audience={},
                location_targeting={},
                device_requirements={},
                
                frequency_cap=None,  # No frequency limits for emergency
                rotation_weight=1000.0,  # Highest weight
                minimum_gap_minutes=0,
                
                optimal_times=[],
                audience_multiplier=1.0,
                engagement_target=1.0,
                
                exclusion_rules=[],
                competitive_separation=False,
                brand_safety_level="emergency",
                
                status="approved",  # Auto-approved
                created_by=authorized_by,
                approved_by=authorized_by,
                created_at=datetime.utcnow()
            )
            
            # Save emergency schedule
            if self.repo:
                await self.repo.save_content_schedule(asdict(emergency_schedule))
            
            # Immediately deploy to devices
            deployment_result = await self._trigger_immediate_deployment(emergency_schedule)
            
            # Log emergency event
            if self.audit_logger:
                self.audit_logger.log_security_event("emergency_override", {
                    "schedule_id": emergency_schedule.id,
                    "content_id": emergency_content_id,
                    "device_count": len(device_ids),
                    "duration_minutes": duration_minutes,
                    "authorized_by": authorized_by
                }, severity="HIGH")
            
            return {
                "success": True,
                "emergency_schedule_id": emergency_schedule.id,
                "deployment_status": deployment_result,
                "active_until": emergency_schedule.end_date.isoformat(),
                "affected_devices": len(device_ids)
            }
            
        except Exception as e:
            logger.error(f"Failed to handle emergency override: {e}")
            return {"success": False, "error": str(e)}
    
    async def _validate_schedule_data(self, schedule_data: Dict) -> Dict[str, Any]:
        """Validate schedule data for consistency and requirements"""
        errors = []
        
        # Required fields
        required_fields = ["content_id", "device_ids", "start_date", "end_date", "created_by"]
        for field in required_fields:
            if not schedule_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Date validation
        if schedule_data.get("start_date") and schedule_data.get("end_date"):
            try:
                start_date = datetime.fromisoformat(schedule_data["start_date"])
                end_date = datetime.fromisoformat(schedule_data["end_date"])
                
                if end_date <= start_date:
                    errors.append("End date must be after start date")
                
                if start_date < datetime.utcnow() - timedelta(minutes=5):
                    errors.append("Start date cannot be in the past")
                    
            except ValueError as e:
                errors.append(f"Invalid date format: {e}")
        
        # Device validation
        if schedule_data.get("device_ids"):
            if not isinstance(schedule_data["device_ids"], list):
                errors.append("device_ids must be a list")
            elif len(schedule_data["device_ids"]) == 0:
                errors.append("At least one device ID is required")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def _generate_optimal_time_slots(self, start_date: str, end_date: str, 
                                         device_ids: List[str], target_audience: Dict) -> List[Dict]:
        """Generate optimal time slots based on audience analytics"""
        # Simplified implementation - would use ML/analytics in production
        time_slots = []
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        # Generate daily time slots during peak hours
        current_date = start.date()
        while current_date <= end.date():
            # Morning peak: 8-10 AM
            morning_start = datetime.combine(current_date, datetime.min.time().replace(hour=8))
            morning_end = datetime.combine(current_date, datetime.min.time().replace(hour=10))
            
            time_slots.append({
                "start_time": morning_start.isoformat(),
                "end_time": morning_end.isoformat(),
                "duration_minutes": 120,
                "audience_estimate": 150,
                "peak_hours": True
            })
            
            # Evening peak: 6-9 PM
            evening_start = datetime.combine(current_date, datetime.min.time().replace(hour=18))
            evening_end = datetime.combine(current_date, datetime.min.time().replace(hour=21))
            
            time_slots.append({
                "start_time": evening_start.isoformat(),
                "end_time": evening_end.isoformat(),
                "duration_minutes": 180,
                "audience_estimate": 200,
                "peak_hours": True
            })
            
            current_date += timedelta(days=1)
        
        return time_slots
    
    async def _check_schedule_conflicts(self, schedule: ContentSchedule) -> List[Dict]:
        """Check for scheduling conflicts"""
        # Simplified implementation
        return []  # No conflicts for now
    
    async def _get_active_schedules(self, device_id: str, target_time: datetime) -> List[Dict]:
        """Get active schedules for a device at a specific time"""
        if self.repo:
            return await self.repo.get_active_schedules(device_id, target_time)
        return []
    
    async def _get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get device information and capabilities"""
        if self.repo:
            return await self.repo.get_digital_screen(device_id)
        return None
    
    async def _apply_content_filters(self, schedules: List[Dict], device_info: Dict) -> List[Dict]:
        """Apply content filters based on device capabilities and business rules"""
        filtered = []
        
        for schedule in schedules:
            # Check device compatibility
            device_reqs = schedule.get("device_requirements", {})
            if device_reqs and not self._check_device_compatibility(device_info, device_reqs):
                continue
            
            # Check brand safety
            if not self._check_brand_safety(schedule, device_info):
                continue
            
            # Check frequency caps
            if not await self._check_frequency_cap(schedule, device_info):
                continue
            
            filtered.append(schedule)
        
        return filtered
    
    async def _optimize_playlist_order(self, schedules: List[Dict], 
                                     device_info: Dict, target_time: datetime) -> List[Dict]:
        """Optimize playlist order based on priority, audience, and engagement"""
        # Sort by priority, then by rotation weight
        return sorted(schedules, key=lambda x: (
            -x.get("priority", 2),  # Higher priority first
            -x.get("rotation_weight", 1.0),  # Higher weight first
            x.get("created_at", "")  # Then by creation time
        ))
    
    async def _generate_playlist_with_timing(self, schedules: List[Dict], 
                                           target_time: datetime) -> List[Dict]:
        """Generate playlist with specific timing and transitions"""
        playlist = []
        current_time = target_time
        
        for schedule in schedules:
            # Get content information
            content_info = await self._get_content_info(schedule["content_id"])
            if not content_info:
                continue
            
            duration = content_info.get("duration", 30)  # Default 30 seconds
            
            playlist_item = {
                "schedule_id": schedule["id"],
                "content_id": schedule["content_id"],
                "start_time": current_time.isoformat(),
                "duration": duration,
                "priority": schedule.get("priority", 2),
                "content_type": content_info.get("content_type", "image"),
                "metadata": content_info.get("metadata", {}),
                "transitions": {
                    "fade_in": 1.0,
                    "fade_out": 1.0
                }
            }
            
            playlist.append(playlist_item)
            current_time += timedelta(seconds=duration + 2)  # Add 2s for transitions
        
        return playlist
    
    def _calculate_estimated_impressions(self, schedule: ContentSchedule) -> int:
        """Calculate estimated impressions for a schedule"""
        total_impressions = 0
        
        for time_slot in schedule.time_slots:
            slot_impressions = time_slot.audience_estimate or 100
            slot_impressions *= schedule.audience_multiplier
            
            if time_slot.peak_hours:
                slot_impressions *= 1.5
            
            total_impressions += int(slot_impressions)
        
        return int(total_impressions * len(schedule.device_ids))
    
    def _calculate_next_playlist_update(self, current_time: datetime) -> str:
        """Calculate when the next playlist update should occur"""
        # Update every hour
        next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return next_hour.isoformat()
    
    def _calculate_optimization_score(self, playlist: List[Dict]) -> float:
        """Calculate optimization score for the playlist"""
        if not playlist:
            return 0.0
        
        score = 100.0
        
        # Penalty for low-priority content in prime positions
        for i, item in enumerate(playlist[:3]):  # Check top 3 positions
            if item.get("priority", 2) < 3:  # Less than HIGH priority
                score -= 10
        
        # Bonus for good content mix
        content_types = set([item.get("content_type") for item in playlist])
        if len(content_types) > 1:
            score += 5
        
        return min(100.0, max(0.0, score))
    
    def _check_device_compatibility(self, device_info: Dict, requirements: Dict) -> bool:
        """Check if device meets content requirements"""
        # Simplified compatibility check
        return True
    
    def _check_brand_safety(self, schedule: Dict, device_info: Dict) -> bool:
        """Check brand safety compliance"""
        # Simplified brand safety check
        return True
    
    async def _check_frequency_cap(self, schedule: Dict, device_info: Dict) -> bool:
        """Check frequency cap compliance"""
        # Simplified frequency cap check
        return True
    
    async def _get_content_info(self, content_id: str) -> Optional[Dict]:
        """Get content information"""
        if self.repo:
            return await self.repo.get_content_meta(content_id)
        return None
    
    async def _trigger_immediate_deployment(self, schedule: ContentSchedule) -> Dict[str, Any]:
        """Trigger immediate deployment of schedule to devices"""
        # Implementation would send deployment commands to devices
        return {"status": "deployed", "device_count": len(schedule.device_ids)}

# Global content scheduler service instance
content_scheduler = ContentSchedulerService()