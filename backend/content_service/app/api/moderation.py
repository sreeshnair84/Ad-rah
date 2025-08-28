from fastapi import APIRouter, HTTPException, Depends, Form
from app.models import ModerationResult, Review
from app.repo import repo
import uuid
from app.moderation_worker import worker
from fastapi import HTTPException

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
    return await repo.list_reviews()


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
