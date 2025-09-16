"""
Content Service - Clean Architecture Implementation
=================================================

Handles all content-related business logic including:
- Content upload and metadata management
- AI moderation workflow
- Approval and rejection processes
- Content sharing between companies
- Layout and deployment management
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from fastapi import UploadFile

from app.services.base_service import (
    BaseService, CRUDService, CompanyAwareService, AuditableService,
    ValidationError, NotFoundError, PermissionError, log_service_call
)
from app.models import (
    Content, ContentCreate, ContentUpdate, ContentStatus,
    ContentLayout, ContentLayoutCreate, ContentLayoutUpdate,
    ContentDeployment, ContentDeploymentCreate,
    ContentScheduleRule, DeviceAnalytics
)


class ContentService(CRUDService[Content], CompanyAwareService, AuditableService):
    """
    Content management service implementing clean architecture patterns
    """

    def get_model_name(self) -> str:
        return "Content"

    @log_service_call
    async def create(self, data: Dict, user_context: Dict) -> Content:
        """Create new content with validation and AI moderation"""

        # Validate required fields
        self.validate_required_fields(data, ["title", "file_type", "file_size"])

        # Validate permissions
        self.validate_permissions(user_context["permissions"], "content_create")

        # Prepare content data
        content_data = {
            **data,
            "company_id": user_context["company_id"],
            "created_by": user_context["user_id"],
            "status": ContentStatus.PENDING_REVIEW,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        try:
            # Create content record
            content = await self.repo.create_content(content_data)

            # Log audit event
            await self.log_audit_event(
                "CONTENT_CREATED",
                "content",
                content.id,
                user_context,
                {"title": content.title, "file_type": content.file_type}
            )

            # Trigger AI moderation asynchronously
            asyncio.create_task(self._trigger_ai_moderation(content.id, user_context))

            return content

        except Exception as e:
            raise self.handle_service_error(e, "content creation")

    @log_service_call
    async def upload_file(self, file: UploadFile, metadata: Dict, user_context: Dict) -> Content:
        """Upload file and create content with enhanced validation"""

        # Validate file
        await self._validate_upload_file(file, user_context)

        # Extract metadata from file
        file_metadata = await self._extract_file_metadata(file)

        # Combine metadata
        content_data = {
            **metadata,
            **file_metadata,
            "company_id": user_context["company_id"],
            "created_by": user_context["user_id"]
        }

        try:
            # Store file
            file_url = await self._store_file(file, user_context)
            content_data["file_url"] = file_url

            # Create content
            return await self.create(content_data, user_context)

        except Exception as e:
            # Clean up uploaded file if content creation fails
            if "file_url" in content_data:
                await self._cleanup_file(content_data["file_url"])
            raise self.handle_service_error(e, "file upload")

    @log_service_call
    async def get_by_id(self, content_id: str, user_context: Dict) -> Optional[Content]:
        """Get content by ID with company access validation"""

        content = await self.repo.get_content_by_id(content_id)
        if not content:
            return None

        # Validate company access
        self.validate_company_access(
            user_context["company_id"],
            content.company_id,
            user_context["user_type"]
        )

        return content

    @log_service_call
    async def update(self, content_id: str, data: Dict, user_context: Dict) -> Content:
        """Update content with validation and audit logging"""

        # Get existing content
        content = await self.get_by_id(content_id, user_context)
        if not content:
            raise NotFoundError(f"Content {content_id} not found")

        # Validate permissions
        self.validate_permissions(user_context["permissions"], "content_update")

        # Validate ownership or admin permissions
        if (content.created_by != user_context["user_id"] and
            "content_admin" not in user_context["permissions"]):
            raise PermissionError("Can only update own content or need admin permissions")

        try:
            # Update content
            update_data = {
                **data,
                "updated_at": datetime.utcnow(),
                "updated_by": user_context["user_id"]
            }

            updated_content = await self.repo.update_content(content_id, update_data)

            # Log audit event
            await self.log_audit_event(
                "CONTENT_UPDATED",
                "content",
                content_id,
                user_context,
                {"changes": data}
            )

            return updated_content

        except Exception as e:
            raise self.handle_service_error(e, "content update")

    @log_service_call
    async def delete(self, content_id: str, user_context: Dict) -> bool:
        """Delete content with proper validation"""

        # Get existing content
        content = await self.get_by_id(content_id, user_context)
        if not content:
            raise NotFoundError(f"Content {content_id} not found")

        # Validate permissions
        self.validate_permissions(user_context["permissions"], "content_delete")

        # Check if content is in use
        if await self._is_content_in_use(content_id):
            raise ValidationError("Cannot delete content that is currently deployed")

        try:
            # Delete content
            success = await self.repo.delete_content(content_id)

            if success:
                # Clean up associated file
                if content.file_url:
                    await self._cleanup_file(content.file_url)

                # Log audit event
                await self.log_audit_event(
                    "CONTENT_DELETED",
                    "content",
                    content_id,
                    user_context,
                    {"title": content.title}
                )

            return success

        except Exception as e:
            raise self.handle_service_error(e, "content deletion")

    @log_service_call
    async def list(self, filters: Dict, user_context: Dict) -> List[Content]:
        """List content with company filtering"""

        # Apply company filtering
        filters = self.filter_by_company(filters, user_context)

        try:
            return await self.repo.list_content(filters)
        except Exception as e:
            raise self.handle_service_error(e, "content listing")

    @log_service_call
    async def approve_content(self, content_id: str, user_context: Dict, notes: str = None) -> Content:
        """Approve content for publication"""

        # Validate permissions
        self.validate_permissions(user_context["permissions"], "content_approve")

        content = await self.get_by_id(content_id, user_context)
        if not content:
            raise NotFoundError(f"Content {content_id} not found")

        if content.status != ContentStatus.PENDING_REVIEW:
            raise ValidationError(f"Content is not in pending review status: {content.status}")

        try:
            # Update status
            update_data = {
                "status": ContentStatus.APPROVED,
                "approved_by": user_context["user_id"],
                "approved_at": datetime.utcnow(),
                "reviewer_notes": notes,
                "updated_at": datetime.utcnow()
            }

            updated_content = await self.repo.update_content(content_id, update_data)

            # Log audit event
            await self.log_audit_event(
                "CONTENT_APPROVED",
                "content",
                content_id,
                user_context,
                {"notes": notes}
            )

            return updated_content

        except Exception as e:
            raise self.handle_service_error(e, "content approval")

    @log_service_call
    async def reject_content(self, content_id: str, user_context: Dict, reason: str) -> Content:
        """Reject content with reason"""

        # Validate permissions
        self.validate_permissions(user_context["permissions"], "content_approve")

        content = await self.get_by_id(content_id, user_context)
        if not content:
            raise NotFoundError(f"Content {content_id} not found")

        if not reason or not reason.strip():
            raise ValidationError("Rejection reason is required")

        try:
            # Update status
            update_data = {
                "status": ContentStatus.REJECTED,
                "rejected_by": user_context["user_id"],
                "rejected_at": datetime.utcnow(),
                "rejection_reason": reason,
                "updated_at": datetime.utcnow()
            }

            updated_content = await self.repo.update_content(content_id, update_data)

            # Log audit event
            await self.log_audit_event(
                "CONTENT_REJECTED",
                "content",
                content_id,
                user_context,
                {"reason": reason}
            )

            return updated_content

        except Exception as e:
            raise self.handle_service_error(e, "content rejection")

    # Private helper methods

    async def _validate_upload_file(self, file: UploadFile, user_context: Dict):
        """Validate uploaded file"""
        # Check file size
        if file.size > 100 * 1024 * 1024:  # 100MB limit
            raise ValidationError("File size exceeds 100MB limit")

        # Check file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "video/mp4", "video/webm"]
        if file.content_type not in allowed_types:
            raise ValidationError(f"File type {file.content_type} not allowed")

        # Additional company-specific validations can be added here
        company_id = user_context["company_id"]
        # TODO: Check company-specific file policies

    async def _extract_file_metadata(self, file: UploadFile) -> Dict:
        """Extract metadata from uploaded file"""
        metadata = {
            "file_type": file.content_type,
            "file_size": file.size,
            "original_filename": file.filename
        }

        # TODO: Extract additional metadata like dimensions, duration for videos, etc.

        return metadata

    async def _store_file(self, file: UploadFile, user_context: Dict) -> str:
        """Store file and return URL"""
        # TODO: Implement actual file storage (Azure Blob, S3, etc.)
        # For now, return a placeholder URL
        return f"/content/{user_context['company_id']}/{file.filename}"

    async def _cleanup_file(self, file_url: str):
        """Clean up stored file"""
        # TODO: Implement actual file cleanup
        pass

    async def _is_content_in_use(self, content_id: str) -> bool:
        """Check if content is currently deployed or scheduled"""
        # TODO: Check deployments and schedules
        return False

    async def _trigger_ai_moderation(self, content_id: str, user_context: Dict):
        """Trigger AI moderation for content"""
        try:
            from app.ai_manager import ai_manager

            # Start AI moderation
            moderation_result = await ai_manager.moderate_content(content_id)

            # Update content with moderation results
            update_data = {
                "ai_moderation_status": "completed",
                "ai_confidence_score": moderation_result.get("confidence", 0.0),
                "ai_analysis": moderation_result,
                "updated_at": datetime.utcnow()
            }

            await self.repo.update_content(content_id, update_data)

            # Log audit event
            await self.log_audit_event(
                "AI_MODERATION_COMPLETED",
                "content",
                content_id,
                user_context,
                {"result": moderation_result}
            )

        except Exception as e:
            self.logger.error(f"AI moderation failed for content {content_id}: {e}")

            # Mark moderation as failed
            await self.repo.update_content(content_id, {
                "ai_moderation_status": "failed",
                "ai_error": str(e),
                "updated_at": datetime.utcnow()
            })


# Create service instance
content_service = ContentService()

# Register in service registry
from app.services.base_service import service_registry
service_registry.register("content", content_service)