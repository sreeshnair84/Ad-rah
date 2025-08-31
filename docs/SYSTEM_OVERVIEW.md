# Purpose: End-to-end architecture & platform-level description.

## Contents:

Cloud hosting choice (Dubai-friendly provider: Microsoft Azure UAE Central).

Integration with Yodeck API (scheduling push, failover to Xibo API).

Architecture diagram (frontend–backend–Flutter client–database–AI moderation–signage API).

Deployment model (Docker + Kubernetes on Azure AKS with event-driven processing).

Event Framework: Azure Service Bus for message queuing, Docker containers for event processing.

## Technology Stack:

Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui

Backend: FastAPI (Python), MongoDB, Azure Blob Storage

Flutter Client: Flutter 3.24+, Dart, Android SDK, Material Design 3

AI: Azure AI Foundry (planned), simulation-based moderation (current)

## Mobile/Kiosk Architecture:

Flutter Digital Signage Platform with 5-screen architecture:

1. Setup & Registration Screen - QR code scanning, device onboarding

2. Main Display Screen - Full-screen content rendering with dynamic layouts

3. Interactive Screen - NFC/Bluetooth engagement with gamification

4. Status & Diagnostics Screen - Administrative interface with health monitoring

5. Error & Offline Mode Screen - Graceful degradation with cached content

Background Services: Content synchronization, analytics collection, digital twin integration

## Security model:

HTTPS only,

RBAC enforcement,

At-rest encryption (AES-256) + in-transit TLS 1.3.