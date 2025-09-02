Purpose: Technical design.

Contents:

Frontend: Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui.

Backend: FastAPI (Python) microservice for content management and moderation pipeline.

Flutter Client: Cross-platform digital signage app with Android TV/tablet/kiosk support.

Database: MongoDB Atlas (UAE region) for metadata + Azure Blob Storage for media files.

AI moderation:

Current: Simulation-based scoring (development mode).

Planned: Azure AI Foundry integration for multimodal validation (video/image).

Workflow: Upload → Pre-scan (virus check) → AI moderation → Confidence score → Manual queue if <95%. Event-driven processing with Docker containers.

Flutter Architecture:

Five-screen system: Setup/Registration → Main Display → Interactive → Status/Diagnostics → Error/Offline.

Background services: Content sync (5min intervals), analytics collection, NFC/Bluetooth integration.

Digital twin: Virtual device representation for remote management and predictive maintenance.

Signage API integration:

Current: Not implemented.

Planned: Yodeck API for push (primary), fallback to Xibo API with adapter microservice.

Scheduler: Cloud-native (Azure Scheduler / GCP Cloud Scheduler).

Event Framework: Docker-managed event processing with Azure Service Bus for message queuing.

Deployment: Docker containers orchestrated with Kubernetes on Azure AKS.

Implemented in repository (code references):

- Screen & overlay management APIs: implemented in `backend/content_service/app/api/screens.py` with models in `backend/content_service/app/models.py` and frontend pages under `frontend/src/app/dashboard/kiosks` and `frontend/src/app/dashboard/content-overlay`.
- Digital twin / virtual device endpoints and UI: frontend at `frontend/src/app/dashboard/digital-twin/page.tsx`, backend support in `backend/content_service/app/api/screens.py` (DigitalTwin models) and `backend/content_service/app/websocket_manager.py` for mirroring/control.
- Real-time device telemetry & control (WebSocket): backend `backend/content_service/app/api/websocket.py`, frontend `frontend/src/components/DeviceMonitor.tsx`.
- Content scheduler / distributor / proof-of-play: backend modules `backend/content_service/app/content_delivery/content_scheduler.py`, `content_distributor.py`, and `proof_of_play.py` provide scheduling and delivery logic.
- Analytics ingestion & real-time analytics components: backend `backend/content_service/app/analytics/real_time_analytics.py` and frontend analytics pages under `frontend/src/app/dashboard/performance`.

Note: The above items are implemented in code and have corresponding frontend pages and tests; docs in this repository should be considered updated-to-date for these features. Where behaviour is still labelled "planned" in other sections, treat the code as authoritative and reconcile with the design roadmap.