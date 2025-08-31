from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app.models import ContentMetadata, UploadResponse, ModerationResult, ContentMeta
import asyncio
try:
    import aiofiles
    _AIOFILES_AVAILABLE = True
except Exception:
    aiofiles = None
    _AIOFILES_AVAILABLE = False
import uuid
from app.repo import repo
import os
import random
from typing import List, Optional
from app.websocket_manager import websocket_manager
from app.default_content_manager import default_content_manager
from app.utils.serialization import safe_json_response, ensure_string_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


@router.post("/upload-file", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), owner_id: str = Form(...)):
    """Accept a file upload and simulate quarantine + AI moderation trigger."""
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    filepath = os.path.join(STORAGE_DIR, filename)

        # save file to local storage (placeholder for Azure Blob upload)
    try:
        if _AIOFILES_AVAILABLE and aiofiles:
            async with aiofiles.open(filepath, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)
        else:
            # fallback: read bytes asynchronously then write on thread executor
            content = await file.read()
            loop = asyncio.get_event_loop()

            def _write_bytes(path, b):
                with open(path, "wb") as fh:
                    fh.write(b)

            await loop.run_in_executor(None, _write_bytes, filepath, content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to save file: {e}")

    # Simulated virus scan -- here just a random pass
    virus_ok = random.random() > 0.01
    if not virus_ok:
        return UploadResponse(filename=filename, status="rejected", message="Virus detected")

    # Create ContentMeta entry with quarantine status
    content_meta = ContentMeta(
        id=file_id,
        owner_id=owner_id,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        size=len(content) if 'content' in locals() else 0,
        status="quarantine"  # Start in quarantine until moderation
    )
    await repo.save_content_meta(content_meta)

    # Auto-submit for moderation
    await submit_for_review_internal(content_id=file_id, owner_id=owner_id)

    # Simulated AI moderation enqueue (we'll return quarantined until moderation runs)
    return UploadResponse(filename=filename, status="quarantine", message="File saved and queued for moderation")


@router.post("/metadata", response_model=ContentMetadata)
async def post_metadata(metadata: ContentMetadata):
    # persist metadata
    metadata.id = metadata.id or str(uuid.uuid4())
    saved = await repo.save(metadata)
    return saved



@router.get("/{content_id}")
async def get_metadata(content_id: str):
    item = await repo.get(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="not found")
    return item


@router.get("/")
async def list_metadata():
    # Get both regular metadata and content meta
    try:
        regular_content = await repo.list()
    except Exception:
        regular_content = []
    
    try:
        uploaded_content = await repo.list_content_meta()
    except Exception:
        uploaded_content = []

    # Convert uploaded content to match the expected format and handle ObjectId
    formatted_uploaded_content = []
    for content in uploaded_content:
        # Convert ObjectId to string if present
        content_id = str(content.get("_id", content.get("id", ""))) if content.get("_id") else content.get("id", "")
        
        # Create a formatted version that matches ContentMetadata structure
        formatted_content = {
            "id": content_id,
            "title": content.get("title", content.get("filename", "Untitled")),  # Use title if available, otherwise filename
            "description": content.get("description", f"File: {content.get('filename', '')}"),
            "owner_id": content.get("owner_id", ""),
            "categories": content.get("categories", ["uploaded"]),  # Use existing categories or default
            "tags": content.get("tags", []),
            "status": content.get("status", "unknown"),
            "created_at": content.get("created_at"),
            "updated_at": content.get("updated_at"),
            "filename": content.get("filename"),
            "content_type": content.get("content_type"),
            "size": content.get("size")
        }
        formatted_uploaded_content.append(formatted_content)

    # Handle regular content ObjectId conversion too
    formatted_regular_content = []
    for content in regular_content:
        if isinstance(content, dict):
            content_id = str(content.get("_id", content.get("id", ""))) if content.get("_id") else content.get("id", "")
            formatted_content = dict(content)
            formatted_content["id"] = content_id
            if "_id" in formatted_content:
                del formatted_content["_id"]
            formatted_regular_content.append(formatted_content)
        else:
            formatted_regular_content.append(content)

    # Combine both lists
    all_content = formatted_regular_content + formatted_uploaded_content
    return safe_json_response(all_content)


@router.post("/moderation/simulate", response_model=ModerationResult)
async def simulate_moderation(content_id: str = Form(...)):
    # Simulate an AI moderation decision
    confidence = round(random.uniform(0.4, 0.99), 3)
    if confidence > 0.95:
        action = "approved"
    elif confidence >= 0.70:
        action = "needs_review"
    else:
        action = "rejected"

    reason = None
    if action != "approved":
        reason = "simulated policy flag"

    return ModerationResult(content_id=content_id, ai_confidence=confidence, action=action, reason=reason)


@router.put("/{content_id}/status")
async def update_content_status(content_id: str, status: str = Form(...)):
    # Update content status (for Host approval workflow)
    try:
        # Try to get from content meta first
        item = await repo.get_content_meta(content_id)
        use_content_meta = True
        
        # If not found in content meta, try main collection
        if not item:
            item = await repo.get(content_id)
            use_content_meta = False
            
        if not item:
            raise HTTPException(status_code=404, detail="content not found")

        # Update status
        item["status"] = status
        
        # Clean the item for safe model creation
        clean_item = ensure_string_id(item)
        
        # Save back to the appropriate collection
        if use_content_meta:
            # Convert dict to ContentMeta for type safety
            from app.models import ContentMeta
            # Remove any fields that can't be handled by the model
            model_fields = ContentMeta.model_fields.keys()
            filtered_item = {k: v for k, v in clean_item.items() if k in model_fields}
            
            metadata = ContentMeta(**filtered_item)
            saved = await repo.save_content_meta(metadata)
        else:
            # Save to main collection (this might be ContentMetadata format)
            # Try to determine the right model based on available fields
            if "filename" in clean_item and "content_type" in clean_item:
                # This looks like ContentMeta structure
                from app.models import ContentMeta
                model_fields = ContentMeta.model_fields.keys()
                filtered_item = {k: v for k, v in clean_item.items() if k in model_fields}
                metadata = ContentMeta(**filtered_item)
                saved = await repo.save_content_meta(metadata)
            else:
                # This looks like ContentMetadata structure
                from app.models import ContentMetadata
                model_fields = ContentMetadata.model_fields.keys()
                filtered_item = {k: v for k, v in clean_item.items() if k in model_fields}
                metadata = ContentMetadata(**filtered_item)
                saved = await repo.save(metadata)
        
        return safe_json_response(saved)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to update status: {e}")


@router.post("/submit-for-review")
async def submit_for_review(content_id: str = Form(...), owner_id: str = Form(...)):
    """Submit content for Host review (Advertiser workflow)"""
    return await submit_for_review_internal(content_id, owner_id)


async def submit_for_review_internal(content_id: str, owner_id: str):
    """Internal function to submit content for review"""
    try:
        # Get content metadata
        item = await repo.get_content_meta(content_id)
        if not item:
            raise HTTPException(status_code=404, detail="content not found")

        # Update status to pending review
        item["status"] = "pending"
        # Convert dict to ContentMeta for type safety
        from app.models import ContentMeta
        metadata = ContentMeta(**item)
        await repo.save_content_meta(metadata)

        # Create review record
        review = {
            "content_id": content_id,
            "action": "needs_review",
            "ai_confidence": None,  # Will be set by AI moderation
            "reviewer_id": None,
            "notes": "Submitted for Host review"
        }
        await repo.save_review(review)

        return {"status": "submitted", "message": "Content submitted for review"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to submit for review: {e}")


@router.post("/admin/approve/{content_id}")
async def admin_approve_content(content_id: str, reviewer_id: str = Form(...), notes: str = Form(None)):
    """Admin endpoint to approve content and push to devices"""
    try:
        # Get content metadata
        content = await repo.get_content_meta(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Update content status to approved
        content["status"] = "approved"
        content["updated_at"] = str(asyncio.get_event_loop().time())

        # Save updated content
        from app.models import ContentMeta
        content_meta = ContentMeta(**content)
        await repo.save_content_meta(content_meta)

        # Update review record
        reviews = await repo.list_reviews()
        review = next((r for r in reviews if r.get("content_id") == content_id), None)
        if review:
            review["action"] = "manual_approve"
            review["reviewer_id"] = reviewer_id
            review["notes"] = notes or "Approved by admin"
            await repo.save_review(review)

        # TODO: Trigger content distribution to devices
        # This would involve:
        # 1. Finding all devices that should receive this content
        # 2. Sending push notifications or updating device content lists
        # 3. Updating device heartbeat data

        return {
            "status": "approved",
            "content_id": content_id,
            "message": "Content approved and queued for distribution to devices"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve content: {str(e)}")


@router.post("/admin/reject/{content_id}")
async def admin_reject_content(content_id: str, reviewer_id: str = Form(...), notes: str = Form(...)):
    """Admin endpoint to reject content"""
    try:
        # Get content metadata
        content = await repo.get_content_meta(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Update content status to rejected
        content["status"] = "rejected"
        content["updated_at"] = str(asyncio.get_event_loop().time())

        # Save updated content
        from app.models import ContentMeta
        content_meta = ContentMeta(**content)
        await repo.save_content_meta(content_meta)

        # Update review record
        reviews = await repo.list_reviews()
        review = next((r for r in reviews if r.get("content_id") == content_id), None)
        if review:
            review["action"] = "manual_reject"
            review["reviewer_id"] = reviewer_id
            review["notes"] = notes
            await repo.save_review(review)

        return {
            "status": "rejected",
            "content_id": content_id,
            "message": "Content rejected"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject content: {str(e)}")


@router.get("/admin/pending")
async def get_pending_content():
    """Get all content pending admin approval"""
    try:
        # Get all content meta
        all_content = await repo.list_content_meta()

        # Filter for pending/quarantine content
        pending_content = []
        for content in all_content:
            if content.get("status") in ["quarantine", "pending"]:
                # Get associated review if exists
                reviews = await repo.list_reviews()
                review = next((r for r in reviews if r.get("content_id") == content.get("id")), None)

                content_with_review = {
                    **content,
                    "review": review
                }
                pending_content.append(content_with_review)

        return {
            "pending_content": pending_content,
            "total": len(pending_content)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending content: {str(e)}")


@router.post("/distribute/{content_id}")
async def distribute_content(content_id: str, target_devices: List[str] = Form(None)):
    """Distribute approved content to specified devices or all devices"""
    try:
        # Get content metadata
        content = await repo.get_content_meta(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        if content.get("status") != "approved":
            raise HTTPException(status_code=400, detail="Content must be approved before distribution")

        # Get target devices
        if not target_devices:
            # If no specific devices, get all active devices
            all_devices = await repo.list_digital_screens()
            target_devices = [d["id"] for d in all_devices if d.get("id") and d.get("status") == "active"]

        if not target_devices:
            raise HTTPException(status_code=400, detail="No target devices found")

        # Create content distribution records with enhanced metadata
        distribution_records = []
        for device_id in target_devices:
            record = {
                "id": str(uuid.uuid4()),
                "content_id": content_id,
                "device_id": device_id,
                "status": "queued",  # queued -> downloading -> downloaded -> displayed
                "priority": 1,  # Default priority
                "scheduled_at": None,  # Immediate distribution
                "expires_at": None,  # No expiration
                "retry_count": 0,
                "last_attempt": None,
                "error_message": None,
                "created_at": str(asyncio.get_event_loop().time()),
                "updated_at": str(asyncio.get_event_loop().time())
            }
            distribution_records.append(record)

        # Save distribution records using repo
        saved_distributions = []
        for record in distribution_records:
            saved = await repo.save_content_distribution(record)
            saved_distributions.append(saved)

        # Notify devices via WebSocket with enhanced message
        successful_notifications = 0
        for record in distribution_records:
            device_id = record.get("device_id")
            if device_id:
                success = await websocket_manager.notify_content_distribution(
                    device_id, content_id, record.get("id")
                )
                if success:
                    successful_notifications += 1

        # Log distribution summary
        logger.info(f"Content {content_id} distributed to {len(target_devices)} devices, {successful_notifications} notified immediately")

        return {
            "status": "distributed",
            "content_id": content_id,
            "target_devices": len(target_devices),
            "successful_notifications": successful_notifications,
            "distribution_ids": [r["id"] for r in saved_distributions],
            "message": f"Content queued for distribution to {len(target_devices)} devices ({successful_notifications} notified immediately)"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to distribute content {content_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to distribute content: {str(e)}")


@router.get("/distribution/status/{content_id}")
async def get_distribution_status(content_id: str):
    """Get distribution status for a specific content item"""
    try:
        # Get all distributions for this content using repo method
        distributions = await repo.list_content_distributions(content_id=content_id)

        # Enhance with device information
        enhanced_distributions = []
        for dist in distributions:
            device_id = dist.get("device_id")
            device = await repo.get_digital_screen(device_id) if device_id else None

            enhanced_dist = {
                **dist,
                "device_name": device.get("name") if device else "Unknown Device",
                "device_location": device.get("location") if device else "Unknown Location"
            }
            enhanced_distributions.append(enhanced_dist)

        return {
            "content_id": content_id,
            "distributions": enhanced_distributions,
            "total": len(enhanced_distributions),
            "queued": len([d for d in enhanced_distributions if d.get("status") == "queued"]),
            "downloading": len([d for d in enhanced_distributions if d.get("status") == "downloading"]),
            "downloaded": len([d for d in enhanced_distributions if d.get("status") == "downloaded"]),
            "displayed": len([d for d in enhanced_distributions if d.get("status") == "displayed"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get distribution status: {str(e)}")


@router.get("/device/{device_id}/content")
async def get_device_content(device_id: str):
    """Get all approved content assigned to a specific device"""
    try:
        # Try to verify device exists
        device = await repo.get_digital_screen(device_id)
        
        # Get all approved content
        all_content = await repo.list_content_meta()
        approved_content = [c for c in all_content if c.get("status") == "approved"]

        if device:
            # Device exists - get distributed content
            device_distributions = await repo.list_content_distributions(device_id=device_id)
            distributed_content_ids = {
                d.get("content_id") for d in device_distributions
                if d.get("status") in ["downloaded", "displayed"]
            }

            # Filter content that's been distributed to this device
            device_content = [
                c for c in approved_content
                if c.get("id") in distributed_content_ids
            ]

            # Check if we should show default content
            if await default_content_manager.should_show_default_content(device_id, device_content):
                company_id = device.get("company_id")
                device_content = await default_content_manager.get_default_content(device_id, company_id)
                logger.info(f"Using default content for registered device {device_id}")

            return {
                "device_id": device_id,
                "device_name": device.get("name"),
                "content": device_content,
                "total": len(device_content),
                "is_default_content": await default_content_manager.should_show_default_content(device_id, 
                    [c for c in approved_content if c.get("id") in distributed_content_ids])
            }
        else:
            # Device doesn't exist - return demo content
            logger.info(f"Device {device_id} not found, returning demo content")
            
            demo_content = await default_content_manager.get_demo_content(device_id)
            
            return {
                "device_id": device_id,
                "device_name": f"Demo Device ({device_id[:8]}...)",
                "content": demo_content,
                "total": len(demo_content),
                "is_demo": True,
                "note": "Demo mode - device not registered"
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get device content: {str(e)}")


@router.get("/device/{device_id}")
async def get_device_info(device_id: str):
    """Get device information and current content"""
    try:
        # Get device information
        device = await repo.get_digital_screen(device_id)
        
        if not device:
            # Return demo device info for unregistered devices
            logger.info(f"Device {device_id} not found, returning demo device info")
            
            # Get demo content
            demo_content = await default_content_manager.get_demo_content(device_id)
            
            return {
                "id": device_id,
                "name": f"Demo Device ({device_id[:8]}...)",
                "status": "demo",
                "location": "Demo Location",
                "company_id": "demo-company",
                "resolution_width": 1920,
                "resolution_height": 1080,
                "orientation": "landscape",
                "aspect_ratio": "16:9",
                "last_seen": str(asyncio.get_event_loop().time()),
                "is_demo": True,
                "current_content": demo_content,
                "total_content": len(demo_content)
            }
        
        # Get device's current content
        device_distributions = await repo.list_content_distributions(device_id=device_id)
        distributed_content_ids = {
            d.get("content_id") for d in device_distributions
            if d.get("status") in ["downloaded", "displayed"]
        }
        
        # Get content details
        current_content = []
        if distributed_content_ids:
            all_content = await repo.list_content_meta()
            current_content = [
                c for c in all_content
                if c.get("id") in distributed_content_ids and c.get("status") == "approved"
            ]
        
        # Check if we should show default content
        if await default_content_manager.should_show_default_content(device_id, current_content):
            company_id = device.get("company_id")
            current_content = await default_content_manager.get_default_content(device_id, company_id)
            logger.info(f"Using default content for device info {device_id}")
        
        return {
            "id": device.get("id"),
            "name": device.get("name"),
            "status": device.get("status", "unknown"),
            "location": device.get("location", "Unknown Location"),
            "company_id": device.get("company_id"),
            "resolution_width": device.get("resolution_width"),
            "resolution_height": device.get("resolution_height"),
            "orientation": device.get("orientation", "landscape"),
            "aspect_ratio": device.get("aspect_ratio", "16:9"),
            "last_seen": device.get("last_seen"),
            "is_demo": False,
            "current_content": current_content,
            "total_content": len(current_content)
        }

    except Exception as e:
        logger.error(f"Failed to get device info for {device_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get device info: {str(e)}")


@router.get("/download/{content_id}")
async def download_content(content_id: str, device_id: Optional[str] = None):
    """Download content file for authorized devices"""
    try:
        # Get content metadata
        content = await repo.get_content_meta(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        if content.get("status") != "approved":
            raise HTTPException(status_code=403, detail="Content is not approved for download")

        # If device_id is provided, verify the device has access to this content
        if device_id:
            device_distributions = await repo.list_content_distributions(device_id=device_id)
            has_access = any(
                dist.get("content_id") == content_id and dist.get("status") in ["downloading", "downloaded", "displayed"]
                for dist in device_distributions
            )
            
            if not has_access:
                raise HTTPException(status_code=403, detail="Device does not have access to this content")

        # Get file path
        filename = content.get("filename")
        if not filename:
            raise HTTPException(status_code=404, detail="Content file not found")

        filepath = os.path.join(STORAGE_DIR, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Content file not found on disk")

        # Return file
        from fastapi.responses import FileResponse
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type=content.get("content_type", "application/octet-stream")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download content: {str(e)}")


@router.post("/device/{device_id}/content/{content_id}/status")
async def update_content_display_status(device_id: str, content_id: str, status: str = Form(...)):
    """Update content display status for a device"""
    try:
        # Verify device exists
        device = await repo.get_digital_screen(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        # Verify content exists and is approved
        content = await repo.get_content_meta(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        if content.get("status") != "approved":
            raise HTTPException(status_code=400, detail="Content is not approved")

        # Find and update distribution record
        distributions = await repo.list_content_distributions(content_id=content_id, device_id=device_id)
        if not distributions:
            raise HTTPException(status_code=404, detail="No distribution record found for this device and content")

        distribution = distributions[0]  # Should only be one
        
        # Update status
        valid_statuses = ["queued", "downloading", "downloaded", "displayed"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        distribution_id = distribution.get("id")
        if not distribution_id:
            raise HTTPException(status_code=500, detail="Invalid distribution record")

        await repo.update_content_distribution_status(distribution_id, status)

        # Broadcast status update to admins
        await websocket_manager._broadcast_to_admins({
            "type": "content_status_update",
            "device_id": device_id,
            "content_id": content_id,
            "status": status,
            "timestamp": str(asyncio.get_event_loop().time())
        })

        return {
            "status": "updated",
            "device_id": device_id,
            "content_id": content_id,
            "new_status": status,
            "message": f"Content status updated to {status}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update content status: {str(e)}")


@router.post("/bulk-distribute")
async def bulk_distribute_content(
    content_ids: List[str] = Form(...),
    device_ids: List[str] = Form(...),
    priority: int = Form(1),
    scheduled_at: Optional[str] = Form(None)
):
    """Distribute multiple content items to multiple devices with priority and scheduling"""
    try:
        if not content_ids or not device_ids:
            raise HTTPException(status_code=400, detail="Content IDs and device IDs are required")

        # Validate content items exist and are approved
        valid_content_ids = []
        for content_id in content_ids:
            content = await repo.get_content_meta(content_id)
            if not content:
                raise HTTPException(status_code=404, detail=f"Content {content_id} not found")
            if content.get("status") != "approved":
                raise HTTPException(status_code=400, detail=f"Content {content_id} is not approved")
            valid_content_ids.append(content_id)

        # Validate devices exist and are active
        valid_device_ids = []
        for device_id in device_ids:
            device = await repo.get_digital_screen(device_id)
            if not device:
                raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
            if device.get("status") != "active":
                logger.warning(f"Device {device_id} is not active (status: {device.get('status')})")
                continue  # Skip inactive devices but don't fail
            valid_device_ids.append(device_id)

        if not valid_device_ids:
            raise HTTPException(status_code=400, detail="No valid active devices found")

        # Create distribution records for each content-device combination
        distribution_records = []
        for content_id in valid_content_ids:
            for device_id in valid_device_ids:
                record = {
                    "id": str(uuid.uuid4()),
                    "content_id": content_id,
                    "device_id": device_id,
                    "status": "queued",
                    "priority": priority,
                    "scheduled_at": scheduled_at,
                    "expires_at": None,
                    "retry_count": 0,
                    "last_attempt": None,
                    "error_message": None,
                    "created_at": str(asyncio.get_event_loop().time()),
                    "updated_at": str(asyncio.get_event_loop().time())
                }
                distribution_records.append(record)

        # Save all distribution records
        saved_distributions = []
        for record in distribution_records:
            saved = await repo.save_content_distribution(record)
            saved_distributions.append(saved)

        # Notify devices immediately if not scheduled
        successful_notifications = 0
        if not scheduled_at:
            for record in distribution_records:
                device_id = record.get("device_id")
                content_id = record.get("content_id")
                if device_id and content_id:
                    success = await websocket_manager.notify_content_distribution(
                        device_id, content_id, record.get("id")
                    )
                    if success:
                        successful_notifications += 1

        logger.info(f"Bulk distribution: {len(valid_content_ids)} contents to {len(valid_device_ids)} devices, {len(saved_distributions)} records created")

        return {
            "status": "bulk_distributed",
            "content_count": len(valid_content_ids),
            "device_count": len(valid_device_ids),
            "total_distributions": len(saved_distributions),
            "successful_notifications": successful_notifications,
            "scheduled": scheduled_at is not None,
            "priority": priority,
            "message": f"Content distributed to {len(valid_device_ids)} devices ({successful_notifications} notified immediately)"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed bulk distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to distribute content: {str(e)}")


@router.get("/distribution/stats")
async def get_distribution_stats():
    """Get overall distribution statistics and device status overview"""
    try:
        # Get all content distributions
        all_distributions = await repo.list_content_distributions()

        # Get all devices
        all_devices = await repo.list_digital_screens()

        # Get all approved content
        all_content = await repo.list_content_meta()
        approved_content = [c for c in all_content if c.get("status") == "approved"]

        # Calculate statistics
        stats = {
            "total_distributions": len(all_distributions),
            "total_devices": len(all_devices),
            "total_approved_content": len(approved_content),
            "active_devices": len([d for d in all_devices if d.get("status") == "active"]),
            "inactive_devices": len([d for d in all_devices if d.get("status") != "active"]),
            "distribution_status": {
                "queued": len([d for d in all_distributions if d.get("status") == "queued"]),
                "downloading": len([d for d in all_distributions if d.get("status") == "downloading"]),
                "downloaded": len([d for d in all_distributions if d.get("status") == "downloaded"]),
                "displayed": len([d for d in all_distributions if d.get("status") == "displayed"]),
                "failed": len([d for d in all_distributions if d.get("status") == "failed"])
            },
            "device_status": {
                "online": len([d for d in all_devices if d.get("status") == "active" and d.get("last_heartbeat")]),
                "offline": len([d for d in all_devices if d.get("status") == "active" and not d.get("last_heartbeat")]),
                "inactive": len([d for d in all_devices if d.get("status") != "active"])
            }
        }

        # Get recent distributions (last 24 hours)
        current_time = asyncio.get_event_loop().time()
        recent_distributions = [
            d for d in all_distributions
            if d.get("created_at") and float(d.get("created_at", 0)) > (current_time - 86400)  # 24 hours ago
        ]

        stats["recent_distributions"] = len(recent_distributions)

        # Get distribution success rate
        completed_distributions = [d for d in all_distributions if d.get("status") in ["downloaded", "displayed"]]
        failed_distributions = [d for d in all_distributions if d.get("status") == "failed"]

        total_completed = len(completed_distributions)
        total_failed = len(failed_distributions)

        if total_completed + total_failed > 0:
            stats["success_rate"] = round((total_completed / (total_completed + total_failed)) * 100, 2)
        else:
            stats["success_rate"] = 0.0

        return stats

    except Exception as e:
        logger.error(f"Failed to get distribution stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get distribution stats: {str(e)}")
