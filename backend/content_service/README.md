# Adārah<sup>from Hebron™</sup> - Content Service

FastAPI content microservice with event-driven architecture and Docker support.

## Local Development

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (optional, for full stack)

### Setup

1. Create virtual environment:
```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Create `.env` file from `.env.example`:
```pwsh
cp .env.example .env
```

3. Run locally:
```pwsh
uvicorn app.main:app --reload --port 8001
```

## Docker Development

### Using Docker Compose (Recommended)

```pwsh
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

This will start:
- Content Service (FastAPI) on port 8000
- MongoDB on port 27017
- Azurite (Azure Storage emulator) on ports 10000-10002
- Event Processor (background service)

### Using Docker alone

```pwsh
# Build image
docker build -t content-service .

# Run container
docker run -p 8000:8000 --env-file .env content-service
```

## Configuration

Environment variables (see `.env.example`):

### Required
- `SECRET_KEY`: JWT signing key (change in production)

### Optional
- `MONGO_URI`: MongoDB connection string
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Blob Storage connection
- `SERVICE_BUS_CONNECTION_STRING`: Azure Service Bus connection
- `AZURE_AI_ENDPOINT`: Azure AI Foundry endpoint
- `AZURE_AI_KEY`: Azure AI Foundry key

## Event-Driven Architecture

The service uses Azure Service Bus for event processing:

### Events
- `content_uploaded`: Triggered when content is uploaded
- `moderation_requested`: Triggers AI moderation workflow
- `moderation_completed`: Fired when AI moderation finishes
- `content_approved`: Triggers publishing workflow
- `publishing_requested`: Initiates content publishing

### Event Processor
Runs as a background service that:
1. Listens to Service Bus messages
2. Processes moderation requests using Azure AI
3. Updates content status
4. Triggers downstream workflows

## API Endpoints

### Authentication
- `POST /api/auth/token` - OAuth2 password flow
- `GET /api/auth/me` - Current user info
- `GET /api/auth/me/with-roles` - User with roles and companies
- `POST /api/auth/switch-role` - Switch active role

### Content Management
- `POST /api/uploads/media` - Upload media files
- `POST /api/content/metadata` - Save content metadata
- `GET /api/content/{id}` - Get content by ID
- `GET /api/content/` - List all content
- `POST /api/content/moderation/simulate` - Simulate moderation

### Companies & Users
- `GET /api/companies/` - List companies
- `POST /api/companies/` - Create company (admin only)
- `GET /api/companies/{id}` - Get company
- `PUT /api/companies/{id}` - Update company
- `DELETE /api/companies/{id}` - Delete company

### Events (Testing)
- `POST /api/events/trigger/{event_type}` - Trigger custom event
- `POST /api/events/content-uploaded/{content_id}` - Trigger content uploaded event
- `POST /api/events/moderation-requested/{content_id}` - Trigger moderation event

### Health
- `GET /health` - Service health check

## Demo Users

Default users created on startup:
- `admin@openkiosk.com` / `adminpass` (ADMIN role)
- `host@openkiosk.com` / `hostpass` (HOST role)
- `advertiser@openkiosk.com` / `advertiserpass` (ADVERTISER role)

## Development Workflow

1. Start services with Docker Compose
2. Upload content via `/api/uploads/media`
3. Trigger moderation via events API or automatic workflow
4. Check moderation results in database
5. View logs: `docker-compose logs -f event-processor`

## Production Deployment

For production:
1. Use Azure Container Registry (ACR) for images
2. Deploy to Azure Kubernetes Service (AKS)
3. Use Azure Key Vault for secrets
4. Configure Azure Front Door for CDN
5. Set up Azure Monitor for logging

## Architecture

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
