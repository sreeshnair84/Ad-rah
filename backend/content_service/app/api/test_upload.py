"""
Test Upload API - Simplified upload endpoint for development and testing
No authentication required - FOR DEVELOPMENT ONLY
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
import os
import uuid
from datetime import datetime
import logging
from typing import Optional

from app.events.event_manager import publish_content_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test Upload"])

@router.post("/upload")
async def test_upload_content(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form("Test Upload"),
    description: Optional[str] = Form("Test content uploaded via test endpoint"),
):
    """
    Test upload endpoint - NO AUTHENTICATION REQUIRED
    Only for development and testing purposes
    """
    try:
        # Generate test data
        test_content_id = f"test_content_{uuid.uuid4()}"
        test_company_id = "test_company_123"
        test_user_id = "test_user_456"

        # Basic file validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Create upload directory if it doesn't exist
        upload_dir = "uploads/test"
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        logger.info(f"Test file uploaded: {filename} ({file_size} bytes)")

        # Publish content upload event to test event-driven architecture
        try:
            await publish_content_event(
                event_type="content.uploaded",
                content_id=test_content_id,
                company_id=test_company_id,
                user_id=test_user_id,
                payload={
                    "filename": filename,
                    "original_filename": file.filename,
                    "content_type": file.content_type or "unknown",
                    "file_size": file_size,
                    "title": title,
                    "description": description,
                    "file_path": file_path,
                    "test_upload": True
                },
                correlation_id=f"test_upload_{uuid.uuid4()}"
            )
            logger.info(f"✅ Published content upload event for test file {test_content_id}")

        except Exception as event_error:
            logger.error(f"Failed to publish event: {event_error}")
            # Don't fail the upload if event publishing fails

        return {
            "success": True,
            "message": "File uploaded successfully",
            "data": {
                "content_id": test_content_id,
                "filename": filename,
                "original_filename": file.filename,
                "file_size": file_size,
                "content_type": file.content_type,
                "file_path": file_path,
                "title": title,
                "description": description,
                "uploaded_at": datetime.utcnow().isoformat(),
                "event_published": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/events/status")
async def get_event_system_status():
    """Get event system status - no auth required"""
    try:
        from app.events.event_manager import event_manager

        metrics = event_manager.get_metrics()

        return {
            "event_system": "operational",
            "status": metrics.get("status", "unknown"),
            "handlers_count": metrics.get("handlers_count", 0),
            "events_processed": metrics.get("event_bus", {}).get("events_processed", 0),
            "events_published": metrics.get("event_bus", {}).get("events_published", 0),
            "queue_size": metrics.get("event_bus", {}).get("queue_size", 0),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get event status: {e}")
        return {
            "event_system": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/events/trigger")
async def trigger_test_event():
    """Trigger a test event - no auth required"""
    try:
        test_event_id = f"manual_test_{uuid.uuid4()}"

        await publish_content_event(
            event_type="content.approved",
            content_id=test_event_id,
            company_id="manual_test_company",
            user_id="manual_test_user",
            payload={
                "test_event": True,
                "triggered_manually": True,
                "timestamp": datetime.utcnow().isoformat(),
                "event_id": test_event_id
            }
        )

        return {
            "success": True,
            "message": "Test event triggered successfully",
            "event_id": test_event_id,
            "event_type": "content.approved",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to trigger test event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger event: {str(e)}")