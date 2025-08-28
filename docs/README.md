# Purpose: High-level introduction to the project for developers, partners, and stakeholders.

## Contents:

Project overview & mission statement.

## Core features.

This repo contains a multi-service scaffold for the **Adārah**<sup>from Hebron™</sup> platform. A runnable `content-service` FastAPI microservice exists under `backend/content_service` which demonstrates the upload, metadata, simple auth, and moderation-simulation flow.

## Quick Start with Docker Compose (Recommended)

The easiest way to get started is using Docker Compose, which sets up the entire stack:

```pwsh
# Navigate to the backend service
cd backend/content_service

# Start all services (backend, database, storage emulator)
docker-compose up -d

# View logs to see startup progress
docker-compose logs -f

# The backend will be available at http://localhost:8000
# Frontend can be started separately (see Frontend Setup below)
```

This will start:
- **Content Service** (FastAPI) on port 8000
- **MongoDB** on port 27017
- **Azurite** (Azure Storage emulator) on ports 10000-10002
- **Event Processor** (background service for AI moderation)

### Mock Data

When you start the backend for the first time, it automatically creates mock data for development:

**Default Companies:**
- OpenKiosk Admin (HOST)
- Dubai Mall Management (HOST)
- Brand Solutions UAE (ADVERTISER)

**Default Users for Testing:**
- `admin@openkiosk.com` / `adminpass` (System Administrator)
- `host@openkiosk.com` / `hostpass` (Host Manager)
- `advertiser@openkiosk.com` / `advertiserpass` (Advertiser Manager)

**Sample Content:**
- Dubai Mall promotional video advertisement
- Brand Solutions UAE banner advertisement
- Associated metadata and AI moderation reviews

## Frontend Setup

```pwsh
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
```

The frontend is automatically configured to connect to the backend API running on `localhost:8000` through Next.js rewrites.

## Manual Setup (Alternative)

Quick start (content-service):

```pwsh
cd backend\content_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Run tests:

```pwsh
.\.venv\Scripts\python.exe -m pytest backend/content_service/tests -q
```

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Content Service │    │  Event Processor│
│  (Next.js)      │◄──►│   (FastAPI)      │◄──►│   (Background)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Azure Service │    │    MongoDB       │    │  Azure AI       │
│     Bus         │    │                  │    │  Foundry        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

Supported integrations (Yodeck, Xibo fallback) are in design and TODO; see `docs/api.md` and `docs/ARCHITECTURE.md` for integration notes.

Contribution & licensing.