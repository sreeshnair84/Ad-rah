# Adārah Platform

A comprehensive content management and digital signage platform built with modern technologies.

## Overview

The Adārah platform provides a complete solution for managing digital content across multiple locations, featuring AI-powered content moderation, multi-tenant architecture, and seamless integration with popular digital signage systems.

## Tech Stack

- **Backend**: Python 3.12+ with FastAPI
- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Database**: MongoDB
- **Storage**: Azure Blob Storage (with Azurite emulator for local development)
- **Message Queue**: Azure Service Bus
- **AI Services**: Azure AI Content Safety
- **Infrastructure**: Azure Bicep templates
- **Containerization**: Docker & Docker Compose

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** - [Download from python.org](https://python.org)
- **Node.js 18+** - [Download from nodejs.org](https://nodejs.org)
- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Git** - [Download from git-scm.com](https://git-scm.com)

## Quick Start (Recommended)

The fastest way to get started is using Docker Compose, which sets up the entire development environment:

### 1. Clone the Repository

```bash
git clone <repository-url>
cd open_kiosk
```

### 2. Start Backend Services

```bash
# Navigate to the backend service
cd backend/content_service

# Start all services (backend, database, storage emulator)
docker-compose up -d

# View logs to see startup progress
docker-compose logs -f
```

This will start:
- **Content Service** (FastAPI) on `http://localhost:8000`
- **MongoDB** on port `27017`
- **Azurite** (Azure Storage emulator) on ports `10000-10002`
- **Event Processor** (background service for AI moderation)

### 3. Start Frontend

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000` and automatically connects to the backend API.

## Manual Setup (Alternative)

If you prefer to run services individually without Docker:

### Backend Setup

```bash
# Navigate to backend service
cd backend/content_service

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn app.main:app --reload --port 8000
```

### Database Setup

For local development without Docker, you'll need:

1. **MongoDB**: Install MongoDB Community Server or use MongoDB Atlas
2. **Azurite**: Install Azure Storage Emulator

```bash
# Install Azurite globally
npm install -g azurite

# Start Azurite
azurite
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Environment Configuration

Create environment files as needed:

### Backend (.env)

```bash
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=content_service

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
AZURE_STORAGE_CONTAINER=content

# Azure Service Bus
SERVICE_BUS_CONNECTION_STRING=<your-service-bus-connection-string>

# Azure AI Content Safety
CONTENT_SAFETY_ENDPOINT=<your-content-safety-endpoint>
CONTENT_SAFETY_KEY=<your-content-safety-key>

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<your-email>
SMTP_PASSWORD=<your-app-password>
```

### Frontend (.env.local)

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Other environment variables as needed
```

## Default Test Data

When you start the backend for the first time, it automatically creates mock data:

### Default Companies
- **OpenKiosk Admin** (HOST)
- **Dubai Mall Management** (HOST)
- **Brand Solutions UAE** (ADVERTISER)

### Default Users
- `admin@openkiosk.com` / `adminpass` (System Administrator)
- `host@openkiosk.com` / `hostpass` (Host Manager)
- `advertiser@openkiosk.com` / `advertiserpass` (Advertiser Manager)

### Sample Content
- Dubai Mall promotional video advertisement
- Brand Solutions UAE banner advertisement
- Associated metadata and AI moderation reviews

## Running Tests

### Backend Tests

```bash
# Navigate to backend service
cd backend/content_service

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run tests
python -m pytest tests -q
```

### Frontend Tests

```bash
# Navigate to frontend directory
cd frontend

# Run tests (if configured)
npm test
```

## Building for Production

### Backend

```bash
# Build Docker image
docker build -t content-service .

# Or build with uv (if using uv)
uv build
```

### Frontend

```bash
# Build for production
npm run build

# Start production server
npm start
```

## API Documentation

Once the backend is running, you can access:

- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc`

## Project Structure

```
├── backend/
│   └── content_service/          # FastAPI microservice
│       ├── app/                  # Application code
│       ├── tests/                # Unit tests
│       ├── data/                 # Local data storage
│       └── Dockerfile            # Docker configuration
├── frontend/                     # Next.js application
│   ├── src/
│   │   ├── app/                  # Next.js app router
│   │   ├── components/           # React components
│   │   └── lib/                  # Utility libraries
│   └── public/                   # Static assets
├── infra/                        # Infrastructure as Code
│   └── main.bicep               # Azure Bicep templates
├── docs/                        # Documentation
└── images/                      # Project images
```

## Development Workflow

1. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
2. **Make Changes**: Implement your feature
3. **Run Tests**: Ensure all tests pass
4. **Commit Changes**: `git commit -m "Add your feature"`
5. **Push Branch**: `git push origin feature/your-feature-name`
6. **Create Pull Request**: Submit for review

## Contributing

Please read our [Contributing Guidelines](docs/CONTRIBUTING.md) before making contributions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Check the [Documentation](docs/)
- Create an [Issue](https://github.com/your-repo/issues)
- Contact the development team

---

**Note**: This platform is designed to work with popular digital signage systems like Yodeck and Xibo. Integration details are available in the [API Documentation](docs/api.md).
# Ad-rah
