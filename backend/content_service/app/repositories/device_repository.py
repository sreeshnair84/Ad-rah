# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Device Repository

This module handles all database operations related to devices,
screens, device registration, and monitoring.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .base_repository import BaseRepository
from ..models.device_models import DigitalScreen, DeviceHeartbeat


class DeviceRepository(BaseRepository):
    """Repository for device operations"""

    @property
    def collection_name(self) -> str:
        return "devices"

    async def create_device(self, device_data: Dict) -> DigitalScreen:
        """Create new device/screen"""
        device_data.update({
            "status": "active",
            "last_seen": datetime.utcnow()
        })

        device_doc = await self.create(device_data)
        return DigitalScreen(**device_doc)

    async def register_device(self, registration_data: Dict) -> Optional[Dict]:
        """Register a new device with validation"""
        try:
            # Verify organization code and registration key
            company_repo = CompanyRepository(self.db_service)
            company = await company_repo.get_by_field("organization_code", registration_data["organization_code"])

            if not company:
                raise ValueError("Invalid organization code")

            # Verify registration key
            key_repo = DeviceRegistrationKeyRepository(self.db_service)
            valid_key = await key_repo.validate_key(
                registration_data["registration_key"],
                company["id"]
            )

            if not valid_key:
                raise ValueError("Invalid or expired registration key")

            # Create device
            device_data = {
                "name": registration_data["device_name"],
                "company_id": company["id"],
                "location": registration_data.get("location_description", ""),
                "device_type": registration_data.get("device_type", "kiosk"),
                "registration_key": registration_data["registration_key"]
            }

            # Add capabilities and fingerprint if provided
            if registration_data.get("capabilities"):
                device_data["capabilities"] = registration_data["capabilities"]
            if registration_data.get("fingerprint"):
                device_data["fingerprint"] = registration_data["fingerprint"]

            device = await self.create_device(device_data)

            # Mark registration key as used
            await key_repo.mark_key_used(registration_data["registration_key"], device.id)

            self.logger.info(f"Device registered successfully: {device.id} for company {company['id']}")
            return device.model_dump()

        except Exception as e:
            self.logger.error(f"Failed to register device: {e}")
            raise

    async def update_last_seen(self, device_id: str) -> bool:
        """Update device last seen timestamp"""
        return await self.update_by_id(device_id, {
            "last_seen": datetime.utcnow(),
            "status": "active"
        })

    async def list_offline_devices(self, offline_threshold_minutes: int = 30) -> List[Dict]:
        """Get devices that haven't been seen recently"""
        threshold = datetime.utcnow() - timedelta(minutes=offline_threshold_minutes)
        return await self.find_by_query({
            "$or": [
                {"last_seen": {"$lt": threshold}},
                {"last_seen": None}
            ]
        })

    async def get_device_stats(self, company_id: str) -> Dict[str, int]:
        """Get device statistics for a company"""
        try:
            devices = await self.list_by_company(company_id)

            stats = {
                "total": len(devices),
                "active": 0,
                "offline": 0,
                "maintenance": 0
            }

            threshold = datetime.utcnow() - timedelta(minutes=30)

            for device in devices:
                if device.get("status") == "maintenance":
                    stats["maintenance"] += 1
                elif not device.get("last_seen") or device["last_seen"] < threshold:
                    stats["offline"] += 1
                else:
                    stats["active"] += 1

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get device stats for company {company_id}: {e}")
            return {"total": 0, "active": 0, "offline": 0, "maintenance": 0}


class DeviceHeartbeatRepository(BaseRepository):
    """Repository for device heartbeat operations"""

    @property
    def collection_name(self) -> str:
        return "device_heartbeats"

    async def record_heartbeat(self, heartbeat_data: Dict) -> DeviceHeartbeat:
        """Record device heartbeat"""
        heartbeat_doc = await self.create(heartbeat_data)

        # Update device last_seen timestamp
        device_repo = DeviceRepository(self.db_service)
        await device_repo.update_last_seen(heartbeat_data["device_id"])

        return DeviceHeartbeat(**heartbeat_doc)

    async def get_latest_heartbeat(self, device_id: str) -> Optional[Dict]:
        """Get the latest heartbeat for a device"""
        heartbeats = await self.find_by_query(
            {"device_id": device_id},
            limit=1,
            sort=[("timestamp", -1)]
        )
        return heartbeats[0] if heartbeats else None

    async def cleanup_old_heartbeats(self, days_to_keep: int = 30) -> int:
        """Clean up old heartbeat records"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            result = await self.collection.delete_many({"timestamp": {"$lt": cutoff_date}})

            deleted_count = result.deleted_count
            self.logger.info(f"Cleaned up {deleted_count} old heartbeat records")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old heartbeats: {e}")
            return 0


class DeviceAnalyticsRepository(BaseRepository):
    """Repository for device analytics operations"""

    @property
    def collection_name(self) -> str:
        return "device_analytics"

    async def record_analytics(self, analytics_data: Dict) -> Dict:
        """Record device analytics event"""
        return await self.create(analytics_data)

    async def get_device_analytics(self, device_id: str,
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> List[Dict]:
        """Get analytics for a specific device"""
        query = {"device_id": device_id}

        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["timestamp"] = date_filter

        return await self.find_by_query(query, sort=[("timestamp", -1)])

    async def get_analytics_summary(self, company_id: str,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> Dict:
        """Get analytics summary for a company"""
        try:
            # Build match stage for aggregation
            match_stage = {"company_id": company_id}
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                match_stage["timestamp"] = date_filter

            pipeline = [
                {"$match": match_stage},
                {"$group": {
                    "_id": None,
                    "total_impressions": {"$sum": {"$cond": [{"$eq": ["$event_type", "impression"]}, 1, 0]}},
                    "total_interactions": {"$sum": "$user_interactions"},
                    "total_revenue": {"$sum": "$estimated_revenue"},
                    "unique_devices": {"$addToSet": "$device_id"}
                }},
                {"$project": {
                    "_id": 0,
                    "total_impressions": 1,
                    "total_interactions": 1,
                    "total_revenue": 1,
                    "unique_devices": {"$size": "$unique_devices"}
                }}
            ]

            results = await self.aggregate(pipeline)

            return results[0] if results else {
                "total_impressions": 0,
                "total_interactions": 0,
                "total_revenue": 0.0,
                "unique_devices": 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get analytics summary for company {company_id}: {e}")
            return {"total_impressions": 0, "total_interactions": 0, "total_revenue": 0.0, "unique_devices": 0}


class DeviceRegistrationKeyRepository(BaseRepository):
    """Repository for device registration key operations"""

    @property
    def collection_name(self) -> str:
        return "device_registration_keys"

    async def create_registration_key(self, company_id: str, created_by: str, expires_hours: int = 24) -> Dict:
        """Create a new device registration key"""
        import secrets

        key_data = {
            "key": secrets.token_urlsafe(32),
            "company_id": company_id,
            "created_by": created_by,
            "expires_at": datetime.utcnow() + timedelta(hours=expires_hours),
            "used": False
        }

        return await self.create(key_data)

    async def validate_key(self, key: str, company_id: str) -> bool:
        """Validate a registration key"""
        try:
            key_doc = await self.get_by_field("key", key)

            if not key_doc:
                return False

            # Check if key belongs to the right company
            if key_doc["company_id"] != company_id:
                return False

            # Check if key is not used and not expired
            if key_doc["used"] or key_doc["expires_at"] < datetime.utcnow():
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate registration key: {e}")
            return False

    async def mark_key_used(self, key: str, device_id: str) -> bool:
        """Mark a registration key as used"""
        try:
            key_doc = await self.get_by_field("key", key)
            if not key_doc:
                return False

            return await self.update_by_id(key_doc["id"], {
                "used": True,
                "used_at": datetime.utcnow(),
                "used_by_device": device_id
            })

        except Exception as e:
            self.logger.error(f"Failed to mark key as used: {e}")
            return False

    async def list_company_keys(self, company_id: str, include_used: bool = False) -> List[Dict]:
        """List registration keys for a company"""
        query = {"company_id": company_id}
        if not include_used:
            query["used"] = False

        return await self.find_by_query(query, sort=[("created_at", -1)])


# Import here to avoid circular imports
from .auth_repository import CompanyRepository