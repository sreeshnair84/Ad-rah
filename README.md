# Adara Screen Digital Signage Platform

A comprehensive, enterprise-grade digital signage platform with advanced Role-Based Access Control (RBAC), multi-tenant architecture, and AI-powered content moderation.

## 🌟 Key Features

### 🔐 **Advanced RBAC & Multi-Tenant Security**
- **Three-Tier User System**: Super Users, Company Users, and Device Users
- **Granular Permissions**: Resource-based permissions (content_create, content_approve, device_manage, etc.)
- **Company Isolation**: Complete data separation between companies with secure content sharing
- **Device Authentication**: API key-based authentication for secure device access
- **Role Hierarchy**: Admin, Reviewer, Editor, and Viewer roles with appropriate permissions

### 🏢 **Enterprise Multi-Tenancy**
- **Company Management**: HOST and ADVERTISER company types with customizable settings
- **Content Sharing**: Controlled content sharing between companies with approval workflows
- **Company Limits**: Configurable limits for users, devices, and content per company
- **Branding & Customization**: Company-specific settings and configurations

### 📊 **Advanced Content Management**
- **AI-Powered Moderation**: Azure AI Content Safety integration with content scoring
- **Approval Workflows**: Multi-stage content approval with reviewer assignments
- **Content Versioning**: Track content changes and approval history
- **Multi-Format Support**: Images, videos, HTML5, and text content
- **Visibility Controls**: Private, shared, and public content visibility levels

### 🖥️ **Smart Device Management**
- **Secure Device Registration**: Automatic device registration with unique API keys
- **Company-Based Access**: Devices access only authorized company content
- **Real-time Monitoring**: Device status tracking and health monitoring
- **Content Synchronization**: Intelligent content delivery to appropriate devices
- **Offline Capabilities**: Cached content for offline operation

### 👥 **Comprehensive User Management**
- **Super User Dashboard**: Platform-wide administration and monitoring
- **Company User Roles**: Role-based access within companies
- **Permission-Based UI**: Dynamic interface based on user permissions
- **User Activity Tracking**: Audit trails and activity monitoring

## 🔧 Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework with automatic API documentation
- **MongoDB**: Document database with advanced indexing and aggregation
- **JWT Authentication**: Secure token-based authentication
- **Azure AI Content Safety**: AI-powered content moderation and scoring
- **Azure Service Bus**: Reliable message queue for event processing
- **Azure Blob Storage**: Scalable file storage with CDN integration
- **UV**: Fast Python package installer and resolver for efficient dependency management

### Frontend
- **Next.js 15**: React framework with Turbopack for fast development
- **TypeScript**: Type-safe development with enhanced developer experience
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **React Hook Form**: Performant forms with easy validation
- **Zustand**: Lightweight state management

### Mobile/Display
- **Flutter**: Cross-platform framework for device applications
- **Provider**: State management for device authentication and content
- **HTTP Client**: Secure API communication with automatic retry

### Infrastructure
- **Docker**: Containerized deployment for consistency
- **Azure Bicep**: Infrastructure as Code for Azure resources
- **GitHub Actions**: CI/CD pipeline for automated deployment
- **Azurite**: Local Azure Storage emulator for development

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have the following installed:

- **Python 3.12+** with UV package manager
- **Node.js 18+** with npm
- **Docker & Docker Compose**
- **Git**
- **UV**: Fast Python package installer

### Installing UV

```bash
# Windows (PowerShell)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or install via pip as fallback
pip install uv
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd Open_kiosk

# Start backend services with Docker
cd backend/content_service
docker-compose up -d

# Install and start frontend
cd ../../frontend
npm install
npm run dev

# Frontend will be available at http://localhost:3000
# Backend API at http://localhost:8000
# API Documentation at http://localhost:8000/docs
```

### 3. Initialize with Sample Data

```bash
# Navigate to backend service
cd backend/content_service

# Run the comprehensive seeding script using UV
uv run python seed_data.py
```

### 4. Login with Sample Accounts

**Super User (Platform Administrator):**
- Email: `admin@adara.com`
- Password: `adminpass`
- Access: Full platform administration

**Company Admin (TechCorp Solutions):**
- Email: `admin@techcorpsolutions.com`
- Password: `adminpass`
- Access: Company management and device oversight

**Content Reviewer (Creative Ads Inc):**
- Email: `reviewer@creativeadsinc.com`
- Password: `reviewerpass`
- Access: Content approval and moderation

**Content Editor (Digital Displays LLC):**
- Email: `editor@digitaldisplays.com`
- Password: `editorpass`
- Access: Content creation and editing

### 5. Test Device Registration

Use the Flutter app or test with API calls:

```bash
# Test device registration (replace with actual company info)
curl -X POST "http://localhost:8000/api/auth/device/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "Lobby Display", 
    "device_type": "display", 
    "location": "Main Lobby"
  }'
```

## 📱 Application Components

### Web Management Interface (`/frontend`)
- **Super User Dashboard**: Platform overview, company management, system monitoring
- **Company Dashboard**: Company-specific content and device management
- **Content Management**: Upload, review, and approve content with AI moderation
- **Device Management**: Monitor and configure display devices
- **User Management**: Manage company users and permissions
- **Analytics & Reporting**: Usage statistics and performance metrics

### Flutter Display Application (`/flutter`)
- **Device Registration**: Automatic setup and company association
- **Content Playback**: Secure content display with company isolation
- **Offline Mode**: Cached content for network interruptions
- **Status Reporting**: Real-time device health and content status
- **Remote Management**: Over-the-air updates and configuration

### Backend API (`/backend/content_service`)
- **RBAC Service**: Advanced permission and role management
- **Content Pipeline**: Upload, moderation, and approval workflows
- **Device Authentication**: Secure API key-based device access
- **Company Isolation**: Multi-tenant data separation
- **AI Integration**: Content safety and automated moderation
- **Audit Logging**: Comprehensive activity and security logging

## Data Seeding & Development Setup

### Automated Data Seeding

The platform includes a comprehensive seeding system for development and testing:

```bash
# After starting the backend services
cd backend/content_service

# Run the seeding script using UV
uv run python seed_data.py
```

**What gets created:**
- ✅ 4 sample companies with unique organization codes
- ✅ 9 users with proper role assignments
- ✅ Secure registration keys for device registration
- ✅ Complete RBAC permissions setup
- ✅ Sample content and metadata

### Development Workflow

1. **Start Services**: `docker-compose up -d` (from backend/content_service)
2. **Seed Data**: `uv run python seed_data.py`
3. **Start Frontend**: `npm run dev` (from frontend directory)
4. **Access Application**: 
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Testing the Platform

**Login Credentials:**
- **Admin**: admin@adara.com / adminpass
- **Host**: host@techcorpsolutions.com / hostpass
- **Advertiser**: director@creativeadsinc.com / advertiserpass

**Device Registration:**
- Use organization codes (ORG-XXXXXXX) and registration keys from seeding output
- Test multi-tenant isolation and role-based permissions
- Verify content upload and AI moderation workflows

## Manual Setup (Alternative)

If you prefer to run services individually without Docker:

### Backend Setup

```bash
# Navigate to backend service
cd backend/content_service

# Create virtual environment using UV
uv venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Install dependencies using UV
uv sync

# Start the development server
uv run uvicorn app.main:app --reload --port 8000
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

The application includes a comprehensive data seeding system that creates production-ready test data:

### Data Seeding

Run the seeding script to populate the database with test data:

```bash
# Navigate to backend service
cd backend/content_service

# Run the seeding script
python seed_data.py
```

This creates:
- **4 Sample Companies** with unique organization codes (ORG-XXXXXXX format)
- **9 Users** with proper role assignments across companies
- **Secure Registration Keys** for device registration (16-character keys)
- **Complete RBAC Setup** with permissions and role assignments

### Default Companies
- **TechCorp Solutions** (HOST) - ORG-XXXXXXX
- **Creative Ads Inc** (ADVERTISER) - ORG-XXXXXXX
- **Digital Displays LLC** (HOST) - ORG-XXXXXXX
- **AdVantage Media** (ADVERTISER) - ORG-XXXXXXX

### Default Users
- `admin@adara.com` / `adminpass` (System Administrator)
- `host@techcorpsolutions.com` / `hostpass` (Host Manager)
- `operator@techcorpsolutions.com` / `hostpass` (Screen Operator)
- `director@creativeadsinc.com` / `advertiserpass` (Advertiser Director)
- `creator@creativeadsinc.com` / `advertiserpass` (Content Creator)

### Registration Keys
Each company gets a unique 16-character registration key for device registration:
- TechCorp Solutions: [Generated key]
- Creative Ads Inc: [Generated key]
- Digital Displays LLC: [Generated key]
- AdVantage Media: [Generated key]

### Organization Codes
Each company has a unique organization code used for device registration:
- TechCorp Solutions: ORG-XXXXXXX
- Creative Ads Inc: ORG-XXXXXXX
- Digital Displays LLC: ORG-XXXXXXX
- AdVantage Media: ORG-XXXXXXX

## Running Tests

### Backend Tests

```bash
# Navigate to backend service
cd backend/content_service

# Activate virtual environment (if not already active)
.\.venv\Scripts\Activate.ps1

# Run tests using UV
uv run pytest tests -q
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
│       │   ├── api/              # API routes and endpoints
│       │   ├── auth.py           # Authentication & authorization
│       │   ├── models.py         # Pydantic data models
│       │   ├── repo.py           # Data repository layer
│       │   └── routes/           # Additional route handlers
│       ├── seed_data.py          # Database seeding script
│       ├── tests/                # Unit and integration tests
│       ├── data/                 # Local data storage
│       ├── pyproject.toml        # UV configuration and dependencies
│       ├── uv.lock               # UV dependency lock file
│       ├── Dockerfile            # Docker configuration
│       └── docker-compose.yml    # Multi-service orchestration
├── frontend/                     # Next.js application
│   ├── src/
│   │   ├── app/                  # Next.js app router pages
│   │   ├── components/           # React components
│   │   ├── hooks/                # Custom React hooks
│   │   └── lib/                  # Utility libraries
│   ├── package.json              # Node.js dependencies
│   └── next.config.ts            # Next.js configuration
├── flutter/                      # Flutter mobile app
│   └── adarah_digital_signage/   # Digital signage kiosk app
├── infra/                        # Infrastructure as Code
│   └── main.bicep               # Azure Bicep templates
├── docs/                        # Documentation
│   ├── api.md                   # API documentation
│   ├── ARCHITECTURE.md          # System architecture
│   └── *.md                     # Additional docs
└── README.md                    # This file
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

 ✓ Created SUPER_USER user: admin@adara.com (Role: None)
  ✓ Created COMPANY_USER user: admin@techcorpsolutions.com (Role: ADMIN)
  ✓ Created COMPANY_USER user: reviewer@techcorpsolutions.com (Role: REVIEWER)        
  ✓ Created COMPANY_USER user: editor@techcorpsolutions.com (Role: EDITOR)
  ✓ Created COMPANY_USER user: viewer@techcorpsolutions.com (Role: VIEWER)
  ✓ Created COMPANY_USER user: admin@digitaldisplaysllc.com (Role: ADMIN)
  ✓ Created COMPANY_USER user: reviewer@digitaldisplaysllc.com (Role: REVIEWER)       
  ✓ Created COMPANY_USER user: editor@digitaldisplaysllc.com (Role: EDITOR)
  ✓ Created COMPANY_USER user: viewer@digitaldisplaysllc.com (Role: VIEWER)
  ✓ Created COMPANY_USER user: director@creativeadsinc.com (Role: ADMIN)
  ✓ Created COMPANY_USER user: approver@creativeadsinc.com (Role: REVIEWER)
  ✓ Created COMPANY_USER user: creator@creativeadsinc.com (Role: EDITOR)
  ✓ Created COMPANY_USER user: analytics@creativeadsinc.com (Role: VIEWER)
  ✓ Created COMPANY_USER user: director@advantagemedia.com (Role: ADMIN)
  ✓ Created COMPANY_USER user: approver@advantagemedia.com (Role: REVIEWER)
  ✓ Created COMPANY_USER user: creator@advantagemedia.com (Role: EDITOR)
  ✓ Created COMPANY_USER user: analytics@advantagemedia.com (Role: VIEWER)
