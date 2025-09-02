# Adārah Digital Signage Platform - Content Service

FastAPI content microservice with advanced RBAC, event-driven architecture, and Docker support.

## Local Development

### Prerequisites
- Python 3.12+
- UV (fast Python package manager)
- Docker & Docker Compose (optional, for full stack)

### Setup with UV

1. Install UV (if not already installed):
```pwsh
# Windows (PowerShell)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip as fallback
pip install uv
```

2. Create virtual environment and install dependencies:
```pwsh
# Create virtual environment
uv venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install all dependencies from pyproject.toml
uv sync
```

3. Create `.env` file from `.env.template`:
```pwsh
Copy-Item .env.template .env
```

4. Run locally:
```pwsh
# Using UV to run the application
uv run uvicorn app.main:app --reload --port 8000

# Or activate venv and run directly
uv run python app/main.py
```

## Package Management with UV

### Adding Dependencies
```pwsh
# Add runtime dependency
uv add fastapi uvicorn motor

# Add development dependency  
uv add --dev pytest pytest-asyncio black ruff mypy

# Add dependency with version constraint
uv add "fastapi>=0.104.0"

# Add dependency with extras
uv add "fastapi[email,mail]"
```

### Managing Dependencies
```pwsh
# Update all dependencies
uv sync --upgrade

# Remove dependency
uv remove package-name

# Show dependency tree
uv tree

# Generate lock file
uv lock

# Install from lock file (production)
uv sync --frozen
```

### Running Commands
```pwsh
# Run any command in the virtual environment
uv run command

# Examples:
uv run uvicorn app.main:app --reload
uv run pytest
uv run python seed_data.py
uv run black .
uv run ruff check .
```

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

## Data Seeding

The service includes a comprehensive data seeding system for development and testing:

### Running the Seed Script

```pwsh
# Run the seeding script to populate test data
uv run python seed_data.py
```

This creates:
- **4 Companies** with unique organization codes (ORG-XXXXXXX format)
- **9 Users** with proper role assignments
- **Secure Registration Keys** for device registration
- **Complete RBAC Setup** with permissions

### Default Users

After seeding, these accounts are available:
- `admin@openkiosk.com` / `adminpass` (System Administrator)
- `host@techcorpsolutions.com` / `hostpass` (Host Manager)
- `operator@techcorpsolutions.com` / `hostpass` (Screen Operator)
- `director@creativeadsinc.com` / `advertiserpass` (Advertiser Director)
- `creator@creativeadsinc.com` / `advertiserpass` (Content Creator)

### Organization Codes & Registration Keys

Each company gets:
- **Organization Code**: Unique identifier (ORG-XXXXXXX format)
- **Registration Key**: Secure 16-character key for device registration

Example:
```
Company: TechCorp Solutions
Org Code: ORG-03B62223
Reg Key: K6Z8fX7QfOnATpBv
```

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
