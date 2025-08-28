# Local Development Setup for OpenKiosk

This guide explains how to run the OpenKiosk application locally without requiring Azure services.

## Prerequisites

- Python 3.8+
- MongoDB (optional - will use in-memory storage if not available)
- Git

## Quick Start

1. **Clone and setup the project:**
   ```bash
   git clone <your-repo-url>
   cd open_kiosk/backend/content_service
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables for local development:**

   **Option A: Using .env file (Recommended)**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

   **Option B: Using environment variables**
   ```bash
   export USE_LOCAL_EVENT_PROCESSOR=true
   export SECRET_KEY=your-secret-key-here
   # Optional: MongoDB connection
   export MONGO_URI=mongodb://localhost:27017
   ```

4. **Run the application:**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Local Event Processor

The application automatically uses a local event processor when:
- `USE_LOCAL_EVENT_PROCESSOR=true` is set, OR
- No `SERVICE_BUS_CONNECTION_STRING` is provided

### How the Local Event Processor Works

- Uses in-memory `asyncio.Queue` for event processing
- Simulates AI moderation with random confidence scores
- Processes events asynchronously without external dependencies
- Logs all events for debugging

### Testing Event Processing

You can test the event processing by uploading content through the API. The local processor will:

1. Receive `content_uploaded` event
2. Trigger `moderation_requested` event
3. Simulate AI moderation (70% approval rate)
4. Send `moderation_completed` event

Check the application logs to see event processing in action.

## API Endpoints

### Authentication
- `POST /api/auth/token` - Login
- `POST /api/auth/register` - Register new user

### Users Management
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/users/{id}/profile` - Get user profile
- `POST /api/users/roles` - Create role
- `POST /api/users/check-permission` - Check permissions

### Content Management
- `POST /api/uploads/` - Upload content
- `GET /api/content/` - List content
- `GET /api/moderation/queue` - View moderation queue

## Default Test Accounts

The application creates these default accounts on startup:

- **Admin**: `admin@openkiosk.com` / `adminpass`
- **Host**: `host@openkiosk.com` / `hostpass`
- **Advertiser**: `advertiser@openkiosk.com` / `advertiserpass`

## Development Workflow

1. **Start the backend:**
   ```bash
   cd backend/content_service
   python -m uvicorn app.main:app --reload
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Test API endpoints:**
   ```bash
   # Get API documentation
   open http://localhost:8000/docs

   # Test authentication
   curl -X POST "http://localhost:8000/api/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@openkiosk.com&password=adminpass"
   ```

## Switching to Azure Services

When ready for production:

1. **Install Azure SDK:**
   ```bash
   pip install azure-servicebus azure-storage-blob azure-ai-contentsafety
   ```

2. **Set environment variables:**
   ```bash
   export USE_LOCAL_EVENT_PROCESSOR=false
   export SERVICE_BUS_CONNECTION_STRING="your-service-bus-connection-string"
   export AZURE_STORAGE_CONNECTION_STRING="your-storage-connection-string"
   export AZURE_AI_ENDPOINT="your-ai-endpoint"
   export AZURE_AI_KEY="your-ai-key"
   ```

3. **Update Azure resources:**
   - Create Service Bus namespace and topic
   - Create Storage Account and container
   - Configure AI services

## Troubleshooting

### Event Processor Not Starting
- Check that `USE_LOCAL_EVENT_PROCESSOR=true` is set
- Verify no Azure Service Bus connection string is set
- Check application logs for errors

### Permission Errors
- Ensure you're using the correct test account credentials
- Check user roles are properly assigned
- Verify API endpoints are called with correct authentication

### Database Connection Issues
- For local development, no MongoDB setup is required (uses in-memory storage)
- If using MongoDB, ensure it's running and connection string is correct

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │ Local Event     │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│ Processor       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Database       │    │ In-Memory Queue │
                       │   (MongoDB)      │    │                 │
                       └──────────────────┘    └─────────────────┘
```

The local event processor provides the same interface as Azure Service Bus but uses local queues, making development and testing much simpler.</content>
<parameter name="filePath">c:\Users\Srees\Workarea\Open_kiosk\backend\content_service\README_LOCAL_DEV.md
