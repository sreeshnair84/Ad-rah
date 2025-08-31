# Adārah Platform

A comprehensive content management and digital signage platform built with modern technologies.

## Key Features

### 🔐 **Secure Multi-Tenant Architecture**
- **Organization Codes**: Unique identifiers for each company (ORG-XXXXXXX format)
- **Registration Keys**: Secure 16-character keys for device registration
- **Role-Based Access Control**: Complete RBAC with granular permissions
- **Company Isolation**: Full data separation between tenants

### 📊 **Content Management**
- **AI-Powered Moderation**: Azure AI Content Safety integration
- **Multi-Format Support**: Images, videos, and documents
- **Automated Workflows**: Event-driven content processing
- **Real-time Status Updates**: Live content approval tracking

### 🖥️ **Digital Signage Integration**
- **Device Registration**: Secure device onboarding with org codes and keys
- **Multi-Device Support**: Manage thousands of screens across locations
- **Real-time Content Delivery**: Instant content updates to registered devices
- **Performance Monitoring**: Device health and uptime tracking

### 👥 **User Management**
- **Multi-Role Support**: Admin, Host Manager, Screen Operator, Advertiser roles
- **Company-Based Access**: Users belong to specific companies with appropriate permissions
- **Secure Authentication**: JWT-based auth with bcrypt password hashing
- **Role Switching**: Users can switch between their assigned roles

## Security & Architecture

### 🔒 **Security Features**
- **Secure Key Generation**: Cryptographically secure organization codes and registration keys
- **JWT Authentication**: Token-based authentication with configurable expiration
- **Password Hashing**: bcrypt-based password security
- **Role-Based Access Control**: Granular permissions system
- **Multi-Tenant Isolation**: Complete data separation between companies

### 🏗️ **Architecture Highlights**
- **Event-Driven Processing**: Azure Service Bus for reliable message processing
- **Microservices Design**: Modular backend services with clear separation of concerns
- **Scalable Storage**: Azure Blob Storage with local Azurite emulator
- **AI Integration**: Azure AI Content Safety for automated content moderation
- **Docker Containerization**: Consistent deployment across environments

### 📈 **Production Readiness**
- **Infrastructure as Code**: Azure Bicep templates for automated deployment
- **Monitoring & Logging**: Comprehensive logging and health checks
- **Database Optimization**: Efficient MongoDB queries and indexing
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation
- **Testing Framework**: Comprehensive test suite with pytest

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** - [Download from python.org](https://python.org)
- **Node.js 18+** - [Download from nodejs.org](https://nodejs.org)
- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Git** - [Download from git-scm.com](https://git-scm.com)

## Data Seeding & Development Setup

### Automated Data Seeding

The platform includes a comprehensive seeding system for development and testing:

```bash
# After starting the backend services
cd backend/content_service

# Run the seeding script
python seed_data.py
```

**What gets created:**
- ✅ 4 sample companies with unique organization codes
- ✅ 9 users with proper role assignments
- ✅ Secure registration keys for device registration
- ✅ Complete RBAC permissions setup
- ✅ Sample content and metadata

### Development Workflow

1. **Start Services**: `docker-compose up -d` (from backend/content_service)
2. **Seed Data**: `python seed_data.py`
3. **Start Frontend**: `npm run dev` (from frontend directory)
4. **Access Application**: 
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Testing the Platform

**Login Credentials:**
- **Admin**: admin@openkiosk.com / adminpass
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
- `admin@openkiosk.com` / `adminpass` (System Administrator)
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
│       │   ├── api/              # API routes and endpoints
│       │   ├── auth.py           # Authentication & authorization
│       │   ├── models.py         # Pydantic data models
│       │   ├── repo.py           # Data repository layer
│       │   └── routes/           # Additional route handlers
│       ├── seed_data.py          # Database seeding script
│       ├── tests/                # Unit and integration tests
│       ├── data/                 # Local data storage
│       ├── requirements.txt      # Python dependencies
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
