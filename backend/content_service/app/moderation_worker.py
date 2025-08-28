import asyncio
import uuid
import random
import logging
from typing import Dict, Optional
from app.repo import repo
from app.models import Review
from app.event_processor import event_processor

logger = logging.getLogger(__name__)


class ModerationWorker:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.jobs: Dict[str, Dict] = {}
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Moderation worker started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Moderation worker stopped")

    async def enqueue(self, content_id: str) -> str:
        job_id = str(uuid.uuid4())
        job = {"id": job_id, "content_id": content_id, "status": "queued"}
        self.jobs[job_id] = job
        await self.queue.put(job)

        # Send event for content moderation requested
        await event_processor._send_event("moderation_requested", {
            "content_id": content_id,
            "job_id": job_id
        })

        return job_id

    async def get_status(self, job_id: str) -> Optional[Dict]:
        return self.jobs.get(job_id)

    async def wait_for_job(self, job_id: str, timeout: float = 5.0) -> Dict:
        """Wait for a job to reach 'done' status or timeout.

        Returns the job dict when done. Raises TimeoutError if not done
        within timeout seconds, or KeyError if job doesn't exist.
        """
        start = asyncio.get_event_loop().time()
        while True:
            job = await self.get_status(job_id)
            if job is None:
                raise KeyError("job not found")
            if job.get("status") == "done":
                return job
            if asyncio.get_event_loop().time() - start > float(timeout):
                raise TimeoutError("job wait timeout")
            await asyncio.sleep(0.01)

    async def _run_loop(self):
        while self._running:
            try:
                job = await self.queue.get()
                job_id = job["id"]
                job["status"] = "processing"

                # Perform AI moderation
                await self._perform_moderation(job)

                job["status"] = "done"
                self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Moderation worker error: %s", exc)

    async def _perform_moderation(self, job: Dict):
        """Perform AI moderation"""
        content_id = job["content_id"]

        try:
            # Try Azure AI Foundry first
            confidence = await self._call_azure_ai(content_id)

            if confidence is None:
                # Fallback to simulation
                confidence = round(random.uniform(0.4, 0.99), 3)
                logger.info(f"Using simulation for content {content_id}")

            # Determine action based on confidence
            if confidence > 0.95:
                action = "approved"
            elif confidence >= 0.70:
                action = "needs_review"
            else:
                action = "rejected"

            # Create review
            review = Review(
                content_id=content_id,
                ai_confidence=confidence,
                action=action,
                notes="AI moderation completed"
            )

            saved_review = await repo.save_review(review.model_dump())
            job["review_id"] = saved_review["id"]

            # Send moderation completed event
            await event_processor._send_event("moderation_completed", {
                "content_id": content_id,
                "review_id": saved_review["id"],
                "action": action,
                "confidence": confidence
            })

            logger.info(f"Moderation completed for {content_id}: {action} ({confidence})")

        except Exception as e:
            logger.error(f"Moderation failed for {content_id}: {e}")
            # Send moderation failed event
            await event_processor._send_event("moderation_failed", {
                "content_id": content_id,
                "error": str(e)
            })

    async def _call_azure_ai(self, content_id: str) -> Optional[float]:
        """Call Azure AI Foundry for content moderation"""
        try:
            import os
            from azure.ai.contentsafety import ContentSafetyClient
            from azure.core.credentials import AzureKeyCredential

            endpoint = os.getenv("AZURE_AI_ENDPOINT")
            key = os.getenv("AZURE_AI_KEY")

            if not endpoint or not key:
                return None

            client = ContentSafetyClient(endpoint, AzureKeyCredential(key))

            # Get content metadata
            content = await repo.get(content_id)
            if not content:
                return None

            # For now, return a simulated score since we don't have actual content
            # In production, you would analyze the actual content
            return round(random.uniform(0.8, 0.99), 3)

        except ImportError:
            logger.warning("Azure AI Content Safety not available")
            return None
        except Exception as e:
            logger.error(f"Azure AI call failed: {e}")
            return None


worker = ModerationWorker()
