# Purpose: End-to-end architecture & platform-level description.

## Contents:

Cloud hosting choice (Dubai-friendly provider: Microsoft Azure UAE Central).

Integration with Yodeck API (scheduling push, failover to Xibo API).

Architecture diagram (frontend–backend–database–AI moderation–signage API).

Deployment model (Docker + Kubernetes on Azure AKS with event-driven processing).

Event Framework: Azure Service Bus for message queuing, Docker containers for event processing.

## Technology Stack:

Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui

Backend: FastAPI (Python), MongoDB, Azure Blob Storage

AI: Azure AI Foundry (planned), simulation-based moderation (current)

## Security model:

HTTPS only,

RBAC enforcement,

Audit logs,

At-rest encryption (AES-256) + in-transit TLS 1.3.