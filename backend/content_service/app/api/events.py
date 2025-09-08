from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.auth_service import get_current_user
from app.event_processor import event_processor

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/trigger/{event_type}")
async def trigger_event(
    event_type: str,
    payload: Dict[str, Any],
    current_user=Depends(get_current_user)
):
    """Trigger an event manually (for testing purposes)"""
    try:
        await event_processor._send_event(event_type, payload)
        return {"message": f"Event {event_type} triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger event: {e}")


@router.post("/content-uploaded/{content_id}")
async def trigger_content_uploaded(
    content_id: str,
    current_user=Depends(get_current_user)
):
    """Trigger content uploaded event"""
    # Get content metadata
    from app.repo import repo
    content = await repo.get(content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    await event_processor._send_event("content_uploaded", {
        "content_id": content_id,
        "owner_id": content.get("owner_id"),
        "filename": content.get("filename")
    })

    return {"message": "Content uploaded event triggered"}


@router.post("/moderation-requested/{content_id}")
async def trigger_moderation_requested(
    content_id: str,
    current_user=Depends(get_current_user)
):
    """Trigger moderation requested event"""
    await event_processor._send_event("moderation_requested", {
        "content_id": content_id
    })

    return {"message": "Moderation requested event triggered"}
