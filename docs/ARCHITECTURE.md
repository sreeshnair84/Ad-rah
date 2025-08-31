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