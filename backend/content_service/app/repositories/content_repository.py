# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Content Repository

This module handles all database operations related to content management,
including uploads, reviews, overlays, and deployments.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_repository import BaseRepository
from ..models.content_models import ContentMeta, ContentOverlay


class ContentRepository(BaseRepository):
    """Repository for content operations"""

    @property
    def collection_name(self) -> str:
        return "content"

    async def create_content(self, content_data: Dict) -> ContentMeta:
        """Create new content with initial status"""
        content_data.update({
            "status": "pending",
            "view_count": 0,
            "uploaded_at": datetime.utcnow()
        })

        content_doc = await self.create(content_data)
        return ContentMeta(**content_doc)

    async def list_by_status(self, company_id: str, status: str) -> List[Dict]:
        """Get content by status for a company"""
        return await self.list_by_company(company_id, {"status": status})

    async def update_status(self, content_id: str, status: str, reviewer_id: Optional[str] = None,
                           notes: Optional[str] = None) -> bool:
        """Update content status with reviewer information"""
        update_data = {
            "status": status,
            "reviewed_at": datetime.utcnow()
        }

        if reviewer_id:
            update_data["reviewer_id"] = reviewer_id
        if notes:
            update_data["reviewer_notes"] = notes

        return await self.update_by_id(content_id, update_data)

    async def update_ai_moderation(self, content_id: str, ai_result: Dict) -> bool:
        """Update content with AI moderation results"""
        update_data = {
            "ai_moderation_status": ai_result.get("action"),
            "ai_confidence_score": ai_result.get("ai_confidence"),
            "ai_analysis": ai_result.get("analysis", {}),
            "ai_processed_at": datetime.utcnow()
        }

        return await self.update_by_id(content_id, update_data)

    async def increment_view_count(self, content_id: str) -> bool:
        """Increment content view count"""
        try:
            result = await self.collection.update_one(
                {"id": content_id},
                {"$inc": {"view_count": 1}}
            )
            return result.modified_count > 0

        except Exception as e:
            self.logger.error(f"Failed to increment view count for {content_id}: {e}")
            return False

    async def get_content_stats(self, company_id: str) -> Dict[str, int]:
        """Get content statistics for a company"""
        try:
            pipeline = [
                {"$match": {"company_id": company_id}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]

            stats_data = await self.aggregate(pipeline)
            stats = {item["_id"]: item["count"] for item in stats_data}

            # Ensure all statuses are present
            for status in ["pending", "approved", "rejected"]:
                if status not in stats:
                    stats[status] = 0

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get content stats for company {company_id}: {e}")
            return {"pending": 0, "approved": 0, "rejected": 0}


class ContentOverlayRepository(BaseRepository):
    """Repository for content overlay operations"""

    @property
    def collection_name(self) -> str:
        return "content_overlays"

    async def create_overlay(self, overlay_data: Dict) -> ContentOverlay:
        """Create new content overlay"""
        overlay_doc = await self.create(overlay_data)
        return ContentOverlay(**overlay_doc)

    async def list_by_screen(self, screen_id: str, active_only: bool = True) -> List[Dict]:
        """Get overlays for a specific screen"""
        filters = {"screen_id": screen_id}
        if active_only:
            filters["status"] = "active"

        return await self.find_by_query(filters)

    async def list_by_content(self, content_id: str) -> List[Dict]:
        """Get overlays using specific content"""
        return await self.find_by_query({"content_id": content_id})

    async def activate_overlay(self, overlay_id: str) -> bool:
        """Activate an overlay"""
        return await self.update_by_id(overlay_id, {
            "status": "active",
            "start_time": datetime.utcnow()
        })

    async def deactivate_overlay(self, overlay_id: str) -> bool:
        """Deactivate an overlay"""
        return await self.update_by_id(overlay_id, {
            "status": "paused",
            "end_time": datetime.utcnow()
        })


class ContentLayoutRepository(BaseRepository):
    """Repository for content layout operations"""

    @property
    def collection_name(self) -> str:
        return "content_layouts"

    async def list_templates(self, company_id: Optional[str] = None) -> List[Dict]:
        """Get layout templates (public or company-specific)"""
        if company_id:
            # Get company templates and public templates
            return await self.find_by_query({
                "$or": [
                    {"company_id": company_id, "is_template": True},
                    {"is_public": True, "is_template": True}
                ]
            })
        else:
            # Get only public templates
            return await self.find_by_query({"is_public": True, "is_template": True})

    async def increment_usage_count(self, layout_id: str) -> bool:
        """Increment template usage count"""
        try:
            result = await self.collection.update_one(
                {"id": layout_id},
                {"$inc": {"usage_count": 1}}
            )
            return result.modified_count > 0

        except Exception as e:
            self.logger.error(f"Failed to increment usage count for layout {layout_id}: {e}")
            return False


class ContentDeploymentRepository(BaseRepository):
    """Repository for content deployment operations"""

    @property
    def collection_name(self) -> str:
        return "content_deployments"

    async def create_deployment(self, deployment_data: Dict) -> Dict:
        """Create new content deployment"""
        deployment_data.update({
            "status": "pending",
            "deployed_at": None
        })

        return await self.create(deployment_data)

    async def list_pending_deployments(self) -> List[Dict]:
        """Get all pending deployments"""
        return await self.find_by_query({"status": "pending"})

    async def update_deployment_status(self, deployment_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update deployment status"""
        update_data = {"status": status}

        if status == "deployed":
            update_data["deployed_at"] = datetime.utcnow()
        elif status == "failed" and error_message:
            update_data["error_message"] = error_message

        return await self.update_by_id(deployment_id, update_data)

    async def get_deployment_stats(self, company_id: str) -> Dict[str, int]:
        """Get deployment statistics for a company"""
        try:
            # Get deployments for content owned by the company
            pipeline = [
                {"$lookup": {
                    "from": "content",
                    "localField": "content_id",
                    "foreignField": "id",
                    "as": "content"
                }},
                {"$match": {"content.company_id": company_id}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]

            stats_data = await self.aggregate(pipeline)
            stats = {item["_id"]: item["count"] for item in stats_data}

            return {
                "pending": stats.get("pending", 0),
                "deployed": stats.get("deployed", 0),
                "failed": stats.get("failed", 0)
            }

        except Exception as e:
            self.logger.error(f"Failed to get deployment stats for company {company_id}: {e}")
            return {"pending": 0, "deployed": 0, "failed": 0}