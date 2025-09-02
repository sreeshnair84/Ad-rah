"""
Content Distribution Service
Manages efficient content distribution to devices with optimization for bandwidth,
device capabilities, and network conditions. Ensures reliable content delivery
with fallback mechanisms and retry logic.
"""

import logging
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class DeliveryStatus(Enum):
    """Content delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class DeliveryMethod(Enum):
    """Content delivery methods"""
    PUSH = "push"           # Push to device immediately
    PULL = "pull"           # Device pulls on schedule
    SYNC = "sync"           # Synchronized delivery
    STREAM = "stream"       # Real-time streaming
    HYBRID = "hybrid"       # Combination based on conditions

class CompressionLevel(Enum):
    """Content compression levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ADAPTIVE = "adaptive"   # Based on network conditions

@dataclass
class ContentPackage:
    """Complete content package for delivery"""
    id: str = field(default_factory=lambda: "")
    content_id: str = ""
    schedule_id: str = ""
    device_id: str = ""

    # Content details
    original_url: str = ""
    optimized_url: Optional[str] = None
    content_type: str = ""
    content_size: int = 0
    content_hash: str = ""
    duration: Optional[float] = None

    # Delivery configuration
    delivery_method: DeliveryMethod = DeliveryMethod.PUSH
    compression_level: CompressionLevel = CompressionLevel.MEDIUM
    quality_level: str = "standard"
    target_bandwidth: Optional[int] = None

    # Timing and priority
    delivery_deadline: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
    priority: int = 5
    device_requirements: Dict[str, Any] = field(default_factory=dict)
    status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Optional fields with defaults
    retry_count: int = 0
    max_retries: int = 3
    fallback_content: Optional[str] = None
    delivered_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Network optimization with defaults
    chunk_size: int = 1024 * 1024  # 1MB chunks
    parallel_downloads: int = 3
    bandwidth_limit: Optional[int] = None

    # Verification
    delivery_verification: Dict[str, Any] = field(default_factory=dict)
    integrity_verified: bool = False

@dataclass
class DeliveryMetrics:
    """Metrics for content delivery performance"""
    total_packages: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    average_delivery_time: float = 0.0
    total_bytes_delivered: int = 0
    bandwidth_utilization: float = 0.0
    compression_ratio: float = 0.0
    retry_rate: float = 0.0

class ContentDistributorService:
    """Service for efficient content distribution to digital signage devices"""
    
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
            from app.monitoring import device_health_monitor
            self.health_monitor = device_health_monitor
        except ImportError:
            self.health_monitor = None
            logger.warning("Health monitoring not available")
        
        # Distribution configuration
        self.max_concurrent_deliveries = 10
        self.default_chunk_size = 1024 * 1024  # 1MB
        self.bandwidth_monitoring = True
        self.adaptive_quality = True
        self.compression_enabled = True
        
        # Network optimization
        self.network_conditions_cache = {}
        self.device_capabilities_cache = {}
        self.delivery_queue = []
        self.active_deliveries = {}
        
        # Retry and fallback settings
        self.default_max_retries = 3
        self.retry_delay_multiplier = 2.0
        self.fallback_quality_enabled = True
        
        # Performance tracking
        self.delivery_metrics = DeliveryMetrics()
        self.performance_history = []
        
    async def prepare_content_package(self, content_id: str, schedule_id: str, 
                                    device_id: str, **kwargs) -> Dict[str, Any]:
        """Prepare optimized content package for delivery"""
        try:
            # Get content information
            content_info = await self._get_content_info(content_id)
            if not content_info:
                return {"success": False, "error": "Content not found"}
            
            # Get device information and capabilities
            device_info = await self._get_device_info(device_id)
            if not device_info:
                return {"success": False, "error": "Device not found"}
            
            # Get current network conditions
            network_conditions = await self._get_network_conditions(device_id)
            
            # Determine optimal delivery method
            delivery_method = await self._determine_delivery_method(
                content_info, device_info, network_conditions
            )
            
            # Optimize content for device and network
            optimization_result = await self._optimize_content(
                content_info, device_info, network_conditions
            )
            
            # Create content package
            package = ContentPackage(
                id=str(uuid.uuid4()),
                content_id=content_id,
                schedule_id=schedule_id,
                device_id=device_id,
                
                original_url=content_info["url"],
                optimized_url=optimization_result.get("optimized_url"),
                content_type=content_info["content_type"],
                content_size=optimization_result.get("size", content_info.get("size", 0)),
                content_hash=optimization_result.get("hash", content_info.get("hash", "")),
                duration=content_info.get("duration"),
                
                delivery_method=delivery_method,
                compression_level=CompressionLevel(optimization_result.get("compression", "medium")),
                quality_level=optimization_result.get("quality", "standard"),
                target_bandwidth=network_conditions.get("available_bandwidth"),
                
                delivery_deadline=kwargs.get("deadline", datetime.utcnow() + timedelta(hours=1)),
                priority=kwargs.get("priority", 5),
                
                device_requirements=device_info.get("capabilities", {}),
                fallback_content=await self._find_fallback_content(content_info, device_info),
                
                status=DeliveryStatus.PENDING,
                created_at=datetime.utcnow(),
                delivered_at=None,
                last_attempt_at=None,
                error_message=None,
                
                chunk_size=self._calculate_optimal_chunk_size(network_conditions),
                parallel_downloads=self._calculate_parallel_downloads(network_conditions),
                bandwidth_limit=network_conditions.get("bandwidth_limit"),
                
                delivery_verification={},
                integrity_verified=False
            )
            
            # Save package
            if self.repo:
                saved_package = await self.repo.save_content_package(asdict(package))
            else:
                saved_package = asdict(package)
            
            # Log package creation
            if self.audit_logger:
                self.audit_logger.log_content_event("package_prepared", {
                    "package_id": package.id,
                    "content_id": content_id,
                    "device_id": device_id,
                    "delivery_method": delivery_method.value,
                    "optimized_size": package.content_size,
                    "compression": package.compression_level.value
                })
            
            return {
                "success": True,
                "package_id": package.id,
                "delivery_method": delivery_method.value,
                "optimized_size": package.content_size,
                "estimated_delivery_time": self._estimate_delivery_time(package),
                "compression_applied": package.compression_level.value != "none"
            }
            
        except Exception as e:
            logger.error(f"Failed to prepare content package: {e}")
            return {"success": False, "error": str(e)}
    
    async def queue_delivery(self, package_id: str) -> Dict[str, Any]:
        """Queue content package for delivery"""
        try:
            # Get package
            if self.repo:
                package_data = await self.repo.get_content_package(package_id)
            else:
                return {"success": False, "error": "Repository not available"}
            
            if not package_data:
                return {"success": False, "error": "Package not found"}
            
            package = ContentPackage(**package_data)
            
            # Check if already queued or delivered
            if package.status in [DeliveryStatus.QUEUED, DeliveryStatus.DOWNLOADING, DeliveryStatus.DELIVERED]:
                return {"success": True, "status": package.status.value, "message": f"Package already {package.status.value}"}
            
            # Update status to queued
            package.status = DeliveryStatus.QUEUED
            
            if self.repo:
                await self.repo.update_content_package(package_id, {"status": package.status.value})
            
            # Add to delivery queue
            self.delivery_queue.append(package)
            
            # Sort queue by priority and deadline
            self.delivery_queue.sort(key=lambda p: (p.priority, p.delivery_deadline))
            
            # Start delivery processing if not already running
            asyncio.create_task(self._process_delivery_queue())
            
            return {
                "success": True,
                "package_id": package_id,
                "status": "queued",
                "queue_position": len(self.delivery_queue),
                "estimated_start": self._estimate_queue_processing_time()
            }
            
        except Exception as e:
            logger.error(f"Failed to queue delivery: {e}")
            return {"success": False, "error": str(e)}
    
    async def deliver_content(self, package_id: str) -> Dict[str, Any]:
        """Execute content delivery to device"""
        try:
            # Get package
            if self.repo:
                package_data = await self.repo.get_content_package(package_id)
            else:
                return {"success": False, "error": "Repository not available"}
            
            if not package_data:
                return {"success": False, "error": "Package not found"}
            
            package = ContentPackage(**package_data)
            
            # Check if delivery is still valid
            if datetime.utcnow() > package.delivery_deadline:
                package.status = DeliveryStatus.EXPIRED
                if self.repo:
                    await self.repo.update_content_package(package_id, {"status": package.status.value})
                return {"success": False, "error": "Delivery deadline expired"}
            
            # Update status to downloading
            package.status = DeliveryStatus.DOWNLOADING
            package.last_attempt_at = datetime.utcnow()
            
            if self.repo:
                await self.repo.update_content_package(package_id, {
                    "status": package.status.value,
                    "last_attempt_at": package.last_attempt_at
                })
            
            # Add to active deliveries
            self.active_deliveries[package_id] = package
            
            try:
                # Execute delivery based on method
                delivery_result = await self._execute_delivery(package)
                
                if delivery_result["success"]:
                    # Verify delivery integrity
                    verification_result = await self._verify_delivery_integrity(package, delivery_result)
                    
                    if verification_result["verified"]:
                        package.status = DeliveryStatus.DELIVERED
                        package.delivered_at = datetime.utcnow()
                        package.integrity_verified = True
                        package.delivery_verification = verification_result
                        
                        # Update metrics
                        self.delivery_metrics.successful_deliveries += 1
                        self.delivery_metrics.total_bytes_delivered += package.content_size
                        
                    else:
                        raise Exception("Delivery integrity verification failed")
                else:
                    raise Exception(delivery_result.get("error", "Delivery failed"))
                    
            except Exception as delivery_error:
                package.error_message = str(delivery_error)
                package.retry_count += 1
                
                if package.retry_count <= package.max_retries:
                    # Schedule retry
                    retry_delay = self.retry_delay_multiplier ** package.retry_count
                    await asyncio.sleep(retry_delay)
                    
                    package.status = DeliveryStatus.QUEUED
                    self.delivery_queue.append(package)
                    
                    self.delivery_metrics.retry_rate = (
                        self.delivery_metrics.retry_rate * 0.9 + 0.1
                    )
                else:
                    package.status = DeliveryStatus.FAILED
                    self.delivery_metrics.failed_deliveries += 1
                    
                    # Try fallback content if available
                    if package.fallback_content:
                        fallback_result = await self._deliver_fallback_content(package)
                        if fallback_result["success"]:
                            package.status = DeliveryStatus.DELIVERED
                            package.delivered_at = datetime.utcnow()
            
            finally:
                # Update package status
                if self.repo:
                    await self.repo.update_content_package(package_id, {
                        "status": package.status.value,
                        "delivered_at": package.delivered_at,
                        "retry_count": package.retry_count,
                        "error_message": package.error_message,
                        "integrity_verified": package.integrity_verified,
                        "delivery_verification": package.delivery_verification
                    })
                
                # Remove from active deliveries
                self.active_deliveries.pop(package_id, None)
                
                # Update total metrics
                self.delivery_metrics.total_packages += 1
            
            # Log delivery result
            if self.audit_logger:
                self.audit_logger.log_content_event("content_delivery_completed", {
                    "package_id": package_id,
                    "device_id": package.device_id,
                    "status": package.status.value,
                    "retry_count": package.retry_count,
                    "delivery_time": (datetime.utcnow() - package.created_at).total_seconds(),
                    "bytes_delivered": package.content_size
                })
            
            return {
                "success": package.status == DeliveryStatus.DELIVERED,
                "package_id": package_id,
                "status": package.status.value,
                "delivered_at": package.delivered_at.isoformat() if package.delivered_at else None,
                "retry_count": package.retry_count,
                "integrity_verified": package.integrity_verified,
                "delivery_time_seconds": (datetime.utcnow() - package.created_at).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Failed to deliver content: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_delivery_status(self, package_id: str) -> Dict[str, Any]:
        """Get current delivery status and progress"""
        try:
            # Check active deliveries first
            if package_id in self.active_deliveries:
                package = self.active_deliveries[package_id]
                
                # Get real-time progress if downloading
                progress = await self._get_delivery_progress(package_id)
                
                return {
                    "success": True,
                    "package_id": package_id,
                    "status": package.status.value,
                    "progress": progress,
                    "current_retry": package.retry_count,
                    "max_retries": package.max_retries,
                    "error_message": package.error_message
                }
            
            # Get from repository
            if self.repo:
                package_data = await self.repo.get_content_package(package_id)
            else:
                return {"success": False, "error": "Repository not available"}
            
            if not package_data:
                return {"success": False, "error": "Package not found"}
            
            return {
                "success": True,
                "package_id": package_id,
                "status": package_data.get("status"),
                "delivered_at": package_data.get("delivered_at"),
                "retry_count": package_data.get("retry_count", 0),
                "integrity_verified": package_data.get("integrity_verified", False),
                "error_message": package_data.get("error_message")
            }
            
        except Exception as e:
            logger.error(f"Failed to get delivery status: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_delivery_metrics(self) -> Dict[str, Any]:
        """Get comprehensive delivery performance metrics"""
        try:
            # Calculate current rates
            if self.delivery_metrics.total_packages > 0:
                success_rate = self.delivery_metrics.successful_deliveries / self.delivery_metrics.total_packages
                failure_rate = self.delivery_metrics.failed_deliveries / self.delivery_metrics.total_packages
            else:
                success_rate = 0.0
                failure_rate = 0.0
            
            # Get current queue status
            queue_length = len(self.delivery_queue)
            active_deliveries = len(self.active_deliveries)
            
            # Calculate bandwidth utilization
            if self.bandwidth_monitoring:
                current_bandwidth = await self._get_current_bandwidth_usage()
            else:
                current_bandwidth = 0.0
            
            return {
                "success": True,
                "delivery_performance": {
                    "total_packages": self.delivery_metrics.total_packages,
                    "successful_deliveries": self.delivery_metrics.successful_deliveries,
                    "failed_deliveries": self.delivery_metrics.failed_deliveries,
                    "success_rate": success_rate,
                    "failure_rate": failure_rate,
                    "retry_rate": self.delivery_metrics.retry_rate,
                    "average_delivery_time": self.delivery_metrics.average_delivery_time
                },
                "current_status": {
                    "queue_length": queue_length,
                    "active_deliveries": active_deliveries,
                    "max_concurrent": self.max_concurrent_deliveries
                },
                "bandwidth_metrics": {
                    "current_usage_mbps": current_bandwidth,
                    "total_bytes_delivered": self.delivery_metrics.total_bytes_delivered,
                    "utilization_percentage": self.delivery_metrics.bandwidth_utilization,
                    "compression_ratio": self.delivery_metrics.compression_ratio
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get delivery metrics: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_delivery_queue(self):
        """Process the delivery queue with concurrency control"""
        while self.delivery_queue and len(self.active_deliveries) < self.max_concurrent_deliveries:
            try:
                # Get next package from queue
                package = self.delivery_queue.pop(0)
                
                # Start delivery task
                asyncio.create_task(self.deliver_content(package.id))
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing delivery queue: {e}")
                break
    
    async def _get_content_info(self, content_id: str) -> Optional[Dict]:
        """Get content information"""
        if self.repo:
            return await self.repo.get_content_meta(content_id)
        return None
    
    async def _get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get device information and capabilities"""
        if self.repo:
            return await self.repo.get_digital_screen(device_id)
        return None
    
    async def _get_network_conditions(self, device_id: str) -> Dict[str, Any]:
        """Get current network conditions for device"""
        # Check cache first
        if device_id in self.network_conditions_cache:
            cached = self.network_conditions_cache[device_id]
            if datetime.utcnow() - cached["timestamp"] < timedelta(minutes=5):
                return cached["conditions"]
        
        # Get from health monitor if available
        if self.health_monitor:
            health_data = await self.health_monitor.get_device_metrics(device_id)
            network_conditions = {
                "available_bandwidth": health_data.get("bandwidth_mbps", 10),
                "latency": health_data.get("latency_ms", 50),
                "signal_strength": health_data.get("network_strength", 70),
                "connection_type": health_data.get("connection_type", "wifi")
            }
        else:
            # Default conditions
            network_conditions = {
                "available_bandwidth": 10,
                "latency": 50,
                "signal_strength": 70,
                "connection_type": "wifi"
            }
        
        # Cache conditions
        self.network_conditions_cache[device_id] = {
            "conditions": network_conditions,
            "timestamp": datetime.utcnow()
        }
        
        return network_conditions
    
    async def _determine_delivery_method(self, content_info: Dict, 
                                       device_info: Dict, network_conditions: Dict) -> DeliveryMethod:
        """Determine optimal delivery method"""
        # Consider content size, network conditions, and device capabilities
        content_size = content_info.get("size", 0)
        bandwidth = network_conditions.get("available_bandwidth", 10)
        
        if content_size < 1024 * 1024:  # < 1MB
            return DeliveryMethod.PUSH
        elif bandwidth > 50:  # High bandwidth
            return DeliveryMethod.PUSH
        elif bandwidth > 10:  # Medium bandwidth
            return DeliveryMethod.SYNC
        else:  # Low bandwidth
            return DeliveryMethod.PULL
    
    async def _optimize_content(self, content_info: Dict, device_info: Dict, 
                              network_conditions: Dict) -> Dict[str, Any]:
        """Optimize content for device and network conditions"""
        optimized = {
            "optimized_url": content_info.get("url"),
            "size": content_info.get("size", 0),
            "hash": content_info.get("hash", ""),
            "quality": "standard",
            "compression": "medium"
        }
        
        # Adapt based on network conditions
        bandwidth = network_conditions.get("available_bandwidth", 10)
        
        if bandwidth < 5:  # Low bandwidth
            optimized.update({
                "quality": "low",
                "compression": "high"
            })
            # Reduce size by estimated 60%
            optimized["size"] = int(optimized["size"] * 0.4)
        elif bandwidth < 20:  # Medium bandwidth
            optimized.update({
                "quality": "medium",
                "compression": "medium"
            })
            # Reduce size by estimated 30%
            optimized["size"] = int(optimized["size"] * 0.7)
        
        return optimized
    
    async def _find_fallback_content(self, content_info: Dict, device_info: Dict) -> Optional[str]:
        """Find suitable fallback content"""
        # Implementation would find similar content with lower requirements
        return None
    
    def _calculate_optimal_chunk_size(self, network_conditions: Dict) -> int:
        """Calculate optimal chunk size based on network conditions"""
        bandwidth = network_conditions.get("available_bandwidth", 10)
        latency = network_conditions.get("latency", 50)
        
        if bandwidth > 50:  # High bandwidth
            return 2 * 1024 * 1024  # 2MB chunks
        elif bandwidth > 10:  # Medium bandwidth
            return 1 * 1024 * 1024  # 1MB chunks
        else:  # Low bandwidth
            return 512 * 1024  # 512KB chunks
    
    def _calculate_parallel_downloads(self, network_conditions: Dict) -> int:
        """Calculate optimal number of parallel download streams"""
        bandwidth = network_conditions.get("available_bandwidth", 10)
        
        if bandwidth > 100:
            return 8
        elif bandwidth > 50:
            return 4
        elif bandwidth > 20:
            return 3
        elif bandwidth > 10:
            return 2
        else:
            return 1
    
    def _estimate_delivery_time(self, package: ContentPackage) -> float:
        """Estimate delivery time in seconds"""
        # Basic estimation based on size and bandwidth
        if package.target_bandwidth and package.target_bandwidth > 0:
            # Convert bandwidth from Mbps to bytes per second
            bandwidth_bps = package.target_bandwidth * 1024 * 1024 / 8
            estimated_time = package.content_size / bandwidth_bps
            
            # Add overhead for chunking and verification
            return estimated_time * 1.3
        
        return 60.0  # Default 60 seconds
    
    def _estimate_queue_processing_time(self) -> str:
        """Estimate when queue processing will start"""
        # Simple estimation based on queue length and average delivery time
        avg_time = self.delivery_metrics.average_delivery_time or 30.0
        queue_time = len(self.delivery_queue) * avg_time / self.max_concurrent_deliveries
        
        start_time = datetime.utcnow() + timedelta(seconds=queue_time)
        return start_time.isoformat()
    
    async def _execute_delivery(self, package: ContentPackage) -> Dict[str, Any]:
        """Execute the actual content delivery"""
        try:
            # Simulate content delivery process
            # In production, this would implement actual file transfer
            
            delivery_time = self._estimate_delivery_time(package)
            await asyncio.sleep(min(delivery_time, 5.0))  # Simulate with max 5s for demo
            
            # Simulate some failures for testing
            if package.retry_count == 0 and package.content_id.endswith("_fail"):
                return {"success": False, "error": "Simulated delivery failure"}
            
            return {
                "success": True,
                "bytes_transferred": package.content_size,
                "transfer_time": delivery_time,
                "checksum": package.content_hash
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _verify_delivery_integrity(self, package: ContentPackage, 
                                       delivery_result: Dict) -> Dict[str, Any]:
        """Verify delivery integrity and completeness"""
        try:
            # Verify checksum
            expected_checksum = package.content_hash
            actual_checksum = delivery_result.get("checksum", "")
            
            checksum_verified = expected_checksum == actual_checksum
            
            # Verify size
            expected_size = package.content_size
            actual_size = delivery_result.get("bytes_transferred", 0)
            
            size_verified = expected_size == actual_size
            
            verified = checksum_verified and size_verified
            
            return {
                "verified": verified,
                "checksum_verified": checksum_verified,
                "size_verified": size_verified,
                "expected_checksum": expected_checksum,
                "actual_checksum": actual_checksum,
                "expected_size": expected_size,
                "actual_size": actual_size,
                "verification_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return {"verified": False, "error": str(e)}
    
    async def _deliver_fallback_content(self, package: ContentPackage) -> Dict[str, Any]:
        """Deliver fallback content when primary delivery fails"""
        # Implementation would deliver lower-quality or default content
        return {"success": True, "fallback_used": True}
    
    async def _get_delivery_progress(self, package_id: str) -> Dict[str, Any]:
        """Get real-time delivery progress"""
        # Implementation would track actual transfer progress
        return {
            "percentage": 75.0,
            "bytes_transferred": 3 * 1024 * 1024,
            "transfer_rate_mbps": 15.5,
            "eta_seconds": 30
        }
    
    async def _get_current_bandwidth_usage(self) -> float:
        """Get current bandwidth usage across all deliveries"""
        # Implementation would monitor actual bandwidth usage
        return 45.2  # Simulated 45.2 Mbps

# Global content distributor service instance
content_distributor = ContentDistributorService()