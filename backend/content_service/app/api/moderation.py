from fastapi import APIRouter, HTTPException, Depends, Form
from app.models import ModerationResult, Review
from app.repo import repo
import uuid
from app.moderation_worker import worker
from app.utils.serialization import safe_json_response

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.post("/enqueue", response_model=Review)
async def enqueue_for_moderation(content_id: str = Form(...)):
    # Simulate AI scoring and create a review record in queue
    import random

    confidence = round(random.uniform(0.4, 0.99), 3)
    if confidence > 0.95:
        action = "approved"
    elif confidence >= 0.70:
        action = "needs_review"
    else:
        action = "rejected"

    review = Review(id=str(uuid.uuid4()), content_id=content_id, ai_confidence=confidence, action=action)
    saved = await repo.save_review(review.model_dump())
    return saved


@router.get("/queue")
async def list_queue():
    reviews = await repo.list_reviews()
    return safe_json_response(reviews)


@router.post("/job/enqueue")
async def enqueue_job(content_id: str = Form(...)):
    job_id = await worker.enqueue(content_id)
    return {"job_id": job_id}


@router.get("/job/{job_id}")
async def job_status(job_id: str):
    status = await worker.get_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="job not found")
    return status


@router.post("/job/{job_id}/wait")
async def job_wait(job_id: str, timeout: float = 5.0):
    try:
        job = await worker.wait_for_job(job_id, timeout=timeout)
        return job
    except KeyError:
        raise HTTPException(status_code=404, detail="job not found")
    except TimeoutError:
        raise HTTPException(status_code=504, detail="job did not complete in time")


@router.post("/{review_id}/decision")
async def post_decision(review_id: str, decision: str = Form(...), reviewer_id: str = Form(None), notes: str = Form(None)):
    reviews = await repo.list_reviews()
    item = next((r for r in reviews if r.get("id") == review_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="review not found")
    item["action"] = "manual_approve" if decision == "approve" else "manual_reject"
    item["reviewer_id"] = reviewer_id
    item["notes"] = notes
    saved = await repo.save_review(item)
    return saved


@router.post("/content/{content_id}/decision")
async def post_decision_by_content_id(content_id: str, decision: str = Form(...), reviewer_id: str = Form(None), notes: str = Form(None)):
    """Post moderation decision using content_id instead of review_id"""
    try:
        print(f"[MODERATION] Processing decision for content_id: {content_id}, decision: {decision}")
        
        # Find the review record for this content
        reviews = await repo.list_reviews()
        print(f"[MODERATION] Found {len(reviews)} total reviews")
        
        item = next((r for r in reviews if r.get("content_id") == content_id), None)
        print(f"[MODERATION] Found existing review: {item is not None}")
        
        if not item:
            # If no review exists, create one
            import uuid
            item = {
                "id": str(uuid.uuid4()),
                "content_id": content_id,
                "action": "needs_review",
                "ai_confidence": None,
                "reviewer_id": None,
                "notes": None
            }
            print(f"[MODERATION] Created new review with id: {item['id']}")
        
        # Update the review with the decision
        item["action"] = "manual_approve" if decision == "approve" else "manual_reject"
        item["reviewer_id"] = reviewer_id
        item["notes"] = notes
        print(f"[MODERATION] Updated review action to: {item['action']}")
        
        # Save the review
        saved = await repo.save_review(item)
        print(f"[MODERATION] Successfully saved review")
        return saved
        
    except Exception as e:
        print(f"[MODERATION] ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing decision: {e}")


@router.get("/pending")
async def get_pending_reviews():
    """Get reviews that need manual attention (for Host dashboard)"""
    try:
        reviews = await repo.list_reviews()
        # Filter for reviews that need manual review
        pending_reviews = [r for r in reviews if r.get("action") == "needs_review"]
        return pending_reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to get pending reviews: {e}")
