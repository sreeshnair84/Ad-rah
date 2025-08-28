Purpose: Define the AI moderation pipeline and the human-in-the-loop rules used by the content-service.

Current implementation: the `content-service` contains a dev-only endpoint `/api/content/moderation/simulate` which returns a simulated AI decision. The production pipeline should implement the steps below.

Pipeline (production):

1) Preprocessing
  - Validate file type, declared MIME, max size limits.
  - Strip/extract metadata (EXIF) and sanitize filenames.
  - Compute checksums (SHA256) for deduplication.

2) Malware scanning
  - Run ClamAV or provider-managed virus scanning.
  - Quarantine immediately on detection; notify partner.

3) Multimodal AI moderation (Gemini + DK cross-check)
  - Image / video: detect violence, NSFW, drug content, hate symbols, logos/trademarks.
  - OCR / text overlay: extract and analyze for hate speech, claims, PII, fraud.
  - Video: sample frames + audio transcript analysis.

4) Decision scoring & thresholds (configurable per-tenant)
  - confidence >= 0.95 -> auto-approve
  - 0.70 <= confidence < 0.95 -> enqueue for human review (Supervisor)
  - confidence < 0.70 -> auto-reject and notify partner

5) Human review
  - Supervisor UI shows AI score, explanation, key flagged regions (image crops / timestamps).
  - Supervisor decision (approve/reject) is recorded in `Review` with audit metadata.

6) Feedback loop
  - Supervisor decisions are stored and periodically used to re-train/tune the AI scoring thresholds.

Interface (contract):

 - Input: asset id, pre-signed storage URL, extracted OCR text, sample thumbnails, content metadata
 - Output: { asset_id, ai_confidence: float, action: approved|needs_review|rejected, explanation: string, flags: [ {type, region, severity} ] }

Operational TODOs:

 - Implement an async moderation worker (Azure Functions or a container worker) that pulls queued assets, calls Gemini + DK, writes `Review` records.
 - Add storage of thumbnails and flagged regions to enable reviewer UI.
 - Expose a `moderation.queue` API to list pending items and a `moderation/{id}/decision` endpoint to capture supervisor actions.
 - Add tenant-level configuration for thresholds and SLAs.