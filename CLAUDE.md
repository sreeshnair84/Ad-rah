# Claude.md - Comprehensive Application Understanding

## 📋 **PROJECT OVERVIEW**

**Project Name**: Adārah Digital Signage Platform  
**Type**: Enterprise Multi-Tenant Digital Signage Platform with Advanced RBAC  
**Architecture**: FastAPI Backend + Next.js Frontend + Flutter Mobile App  
**Target Market**: UAE/Dubai enterprise digital signage and multi-company management  

### **Core Business Model**
- **Multi-Tenant Architecture**: Support unlimited companies with complete data isolation
- **HOST Companies**: Own physical screens/kiosks, manage devices and locations  
- **ADVERTISER Companies**: Create content, participate in content sharing workflows
- **Platform**: Facilitates secure content distribution with advanced permission controls and revenue sharing

## 🏗️ **ARCHITECTURE OVERVIEW**

### **Technology Stack**
```
Frontend: Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui
Backend: FastAPI (Python) + MongoDB + Azure Blob Storage + Advanced RBAC
Mobile: Flutter 3.24+ with RBAC device authentication
Infrastructure: Azure (UAE Central) + Docker + Kubernetes
AI: Multi-provider content moderation with automatic failover (Gemini, OpenAI, Claude, Ollama)
Security: JWT + API Keys + Permission-based access control
Package Management: UV (fast Python package installer and resolver)
```

### **Enhanced RBAC Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js Web   │    │  FastAPI API    │    │ Flutter Device  │
│   Dashboard      │    │   + RBAC        │    │  Authentication │
│   (Port 3000)   │◄───►│  (Port 8000)    │◄───►│  (API Keys)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   RBAC Engine   │◄─────────────┘
                         │ - Permissions   │
                         │ - Company       │
                         │   Isolation     │
                         │ - Content       │
                         │   Sharing       │
                         │ - Device Auth   │
                         └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Azure Cloud   │
                    │ - Blob Storage  │
                    │ - Service Bus   │
                    │ - AI Content    │
                    │   Safety        │
                    │ - MongoDB Atlas │
                    └─────────────────┘
```

## 🔐 **ADVANCED RBAC & AUTHENTICATION**

### **Three-Tier User System**
```typescript
enum UserType {
  SUPER_USER = "SUPER_USER",        // Platform administrators
  COMPANY_USER = "COMPANY_USER",    // Company-specific users  
  DEVICE_USER = "DEVICE_USER"       // Device authentication
}

enum CompanyRole {
  ADMIN = "ADMIN",                  // Company administrators
  REVIEWER = "REVIEWER",            // Content reviewers
  EDITOR = "EDITOR",                // Content creators/editors
  VIEWER = "VIEWER"                 // View-only access
}

interface User {
  id: string;
  email: string;
  user_type: UserType;
  company_id?: string;              // null for SUPER_USER
  company_role?: CompanyRole;       // Company-specific role
  permissions: string[];            // Resource-based permissions
  is_active: boolean;
  company?: Company;                // Populated company data
}
```

### **Granular Permission System**
```typescript
// Resource-based permissions format: {resource}_{action}
type Permission = 
  | "company_create" | "company_read" | "company_update" | "company_delete"
  | "user_create" | "user_read" | "user_update" | "user_delete" 
  | "content_create" | "content_read" | "content_update" | "content_delete"
  | "content_approve" | "content_reject" | "content_share"
  | "device_create" | "device_read" | "device_update" | "device_delete"
  | "device_manage" | "analytics_read" | "settings_manage";

// Permission checking
function hasPermission(user: User, resource: string, action: string): boolean {
  if (user.user_type === "SUPER_USER") return true;
  return user.permissions.includes(`${resource}_${action}`);
}
```

### **Company & Content Sharing System**
```typescript
interface Company {
  id: string;
  name: string;
  organization_code: string;        // ORG-XXXXXXX format for device registration
  company_type: "HOST" | "ADVERTISER";
  registration_key: string;         // 16-character secure key
  sharing_settings: {
    allow_content_sharing: boolean;
    max_shared_companies: number;
    require_approval_for_sharing: boolean;
  };
  limits: {
    max_users: number;
    max_devices: number;
    max_content_size_mb: number;
  };
}

interface ContentShare {
  id: string;
  content_id: string;
  from_company_id: string;
  to_company_id: string;
  permissions: {
    can_edit: boolean;
    can_reshare: boolean;
    can_download: boolean;
  };
  expires_at?: Date;
  status: "active" | "expired" | "revoked";
}
```

### **Device Authentication System**
```typescript
interface Device {
  id: string;
  name: string;
  company_id: string;
  api_key: string;              // Unique API key for authentication
  device_type: string;
  location?: string;
  status: "active" | "inactive" | "maintenance";
  last_seen?: Date;
  metadata?: Record<string, any>;
}

// Device authentication headers
const deviceHeaders = {
  "X-Device-ID": device.id,
  "X-API-Key": device.api_key
};
```

## 🎯 **COMPREHENSIVE ROLE-BASED ACCESS CONTROL SYSTEM**

### **User Types and Company Roles Matrix**

The platform implements a sophisticated RBAC system with three user types and four company roles:

#### **User Types:**
1. **SUPER_USER** - Platform administrators with global access
2. **COMPANY_USER** - Users belonging to specific companies
3. **DEVICE_USER** - Devices for content pulling and reporting

#### **Company Types:**
1. **HOST** - Companies that own physical screens/kiosks and display content
2. **ADVERTISER** - Companies that create content for distribution

#### **Company Roles (for COMPANY_USER):**
1. **ADMIN** - Full company management access
2. **REVIEWER** - Content approval and device monitoring
3. **EDITOR** - Content creation and editing
4. **VIEWER** - View access with upload capability

### **Role-Based Navigation Access**

```typescript
// Navigation Access Matrix
const navigationAccess = {
  "SUPER_USER": {
    access: "ALL_PAGES",
    description: "Complete platform access"
  },
  "COMPANY_USER": {
    "HOST": {
      "ADMIN": [
        "dashboard", "users", "content", "upload", "content-share", 
        "moderation", "content-approval", "content-overlay", "devices", 
        "device-control", "device-keys", "analytics/*", "settings"
      ],
      "REVIEWER": [
        "dashboard", "users", "content", "moderation", "content-approval", 
        "device-control", "analytics/real-time", "analytics/reports"
      ],
      "EDITOR": [
        "dashboard", "content", "upload", "analytics/real-time", "analytics/reports"
      ],
      "VIEWER": [
        "dashboard", "content", "upload", "analytics/real-time", "analytics/reports"
      ]
    },
    "ADVERTISER": {
      "ADMIN": [
        "dashboard", "users", "content", "upload", "moderation", 
        "content-approval", "analytics/*", "settings"
      ],
      "REVIEWER": [
        "dashboard", "users", "content", "moderation", "content-approval", 
        "analytics/real-time", "analytics/reports"
      ],
      "EDITOR": [
        "dashboard", "content", "upload", "analytics/real-time", "analytics/reports"
      ],
      "VIEWER": [
        "dashboard", "content", "upload", "analytics/real-time", "analytics/reports"
      ]
    }
  }
};
```

### **Company Type Restrictions**

#### **HOST Company Capabilities:**
- ✅ Manage physical devices (screens/kiosks)
- ✅ Create and manage their own content
- ✅ Share content with ADVERTISER companies
- ✅ View shared content from approved ADVERTISER companies
- ✅ Control device playback and scheduling
- ✅ Generate device registration QR codes
- ✅ Monitor device health and performance
- ✅ Access full analytics for their devices

#### **ADVERTISER Company Capabilities:**
- ✅ Create and manage advertising content
- ✅ Submit content for approval/review
- ✅ View performance analytics for their content
- ✅ Manage company users and roles
- ❌ Cannot manage devices
- ❌ Cannot share content with other companies
- ❌ Cannot control device playback
- ❌ No device registration capabilities

### **Permission-Based Feature Access**

```typescript
// Permission Requirements for Key Features
const featurePermissions = {
  "User Management": {
    permission: { resource: "user", action: "view" },
    requiredRoles: ["ADMIN", "REVIEWER"],
    description: "Manage company users"
  },
  "Device Registration": {
    permission: { resource: "device", action: "create" },
    companyTypes: ["HOST"],
    requiredRoles: ["ADMIN"],
    description: "HOST admins only"
  },
  "Content Sharing": {
    permission: { resource: "content", action: "share" },
    companyTypes: ["HOST"],
    requiredRoles: ["ADMIN"],
    description: "HOST admins can share with ADVERTISER companies"
  },
  "Content Review": {
    permission: { resource: "content", action: "approve" },
    requiredRoles: ["ADMIN", "REVIEWER"],
    description: "Review and approve content"
  },
  "Device Control": {
    permission: { resource: "device", action: "control" },
    companyTypes: ["HOST"],
    requiredRoles: ["ADMIN", "REVIEWER"],
    description: "Control device playback"
  },
  "Analytics Export": {
    permission: { resource: "analytics", action: "export" },
    requiredRoles: ["ADMIN"],
    description: "Export analytics data"
  }
};
```

### **Device Authentication and Content Access**

#### **Device Role Capabilities:**
- ✅ Pull approved content based on company type and sharing rules
- ✅ Report device health and status via heartbeat
- ✅ Send analytics data for content performance
- ✅ Receive commands and notifications from company admins
- ❌ Cannot access user management functions
- ❌ Cannot modify content or approve submissions

#### **Content Access Rules for Devices:**
```typescript
const deviceContentAccess = {
  "HOST_DEVICE": [
    "own_approved_content",           // Company's own approved content
    "shared_content_from_advertisers" // Content shared by ADVERTISER companies
  ],
  "ADVERTISER_DEVICE": [
    "own_approved_content"            // Only company's own approved content
  ]
};
```

### **API Endpoints for Device Management**

```bash
# Device Authentication & Content
GET /api/device/content/pull/{device_id}     # Pull content for device
POST /api/device/heartbeat/{device_id}       # Device health reporting  
POST /api/device/analytics/{device_id}       # Analytics reporting

# Device Registration (HOST companies only)
POST /api/device/register                    # Register new device
GET /api/device/generate-qr/{company_id}     # Generate registration QR
GET /api/device/keys                         # List registration keys
```

### **Security Implementation**

#### **Authentication Flow:**
1. **Web Users:** JWT tokens with role-based permissions
2. **Devices:** API key authentication with company association
3. **SUPER_USER:** Bypass mechanism for platform administration

#### **Permission Checking:**
```typescript
// Frontend permission checking
const hasAccess = (item) => {
  if (isSuperUser()) return true;
  
  // Check permission requirements
  if (item.permission && !hasPermission(item.permission.resource, item.permission.action)) {
    return false;
  }
  
  // Check company type restrictions
  if (item.companyTypes && !item.companyTypes.includes(user.company?.company_type)) {
    return false;
  }
  
  // Check role requirements
  if (item.requiredRoles && !item.requiredRoles.includes(user.company_role)) {
    return false;
  }
  
  return true;
};
```

#### **Backend Authorization:**
```python
# Backend permission verification
async def check_permission(user_id: str, company_id: str, resource: str, action: str):
    user = await get_user_profile(user_id)
    
    # Super users have all permissions
    if user.user_type == "SUPER_USER":
        return True
    
    # Check user's role permissions
    permissions = await get_user_permissions(user_id, company_id)
    required_permission = f"{resource}_{action}"
    
    return required_permission in permissions
```

This comprehensive RBAC system ensures:
- **Company Isolation:** Users only see data from their company
- **Role-Based Access:** Different roles have appropriate permissions
- **Company Type Restrictions:** HOST and ADVERTISER companies have different capabilities
- **Device Security:** Secure device authentication and content access
- **Scalable Permissions:** Easy to add new roles and permissions as needed
```

## 🚀 **DEVELOPMENT SETUP WITH UV**

### **Backend Setup**
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to backend directory
cd backend/content_service

# Create virtual environment with UV
uv venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Install dependencies from pyproject.toml
uv sync

# Install development dependencies
uv add --dev pytest pytest-asyncio pytest-cov black ruff mypy

# Run the application
uv run uvicorn app.main:app --reload --port 8000

# Alternative: Run directly with Python
uv run python app/main.py
```

### **Frontend Setup**
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### **Package Management with UV**
```bash
# Add new dependencies
uv add fastapi uvicorn motor pymongo

# Add development dependencies
uv add --dev pytest black ruff

# Remove dependencies
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Show dependency tree
uv tree

# Create lock file
uv lock

# Install from lock file (for production)
uv sync --frozen
```

### **Environment Configuration**
```bash
# Backend environment (.env)
ENVIRONMENT=development
MONGO_URI=mongodb://localhost:27017/openkiosk
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Content Moderation
PRIMARY_AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
ENABLE_GEMINI_AGENT=true
ENABLE_OLLAMA_AGENT=true

# Azure Services
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
AZURE_CONTAINER_NAME=openkiosk-media
```

## 🐳 **DOCKER DEPLOYMENT**

### **Backend Dockerfile**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy pyproject.toml and uv.lock
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Docker Compose**
```yaml
# docker-compose.yml
services:
  mongodb:
    image: mongo:7.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    ports: ["27017:27017"]
    
  content-service:
    build: .
    environment:
      MONGO_URI: mongodb://admin:password@mongodb:27017/content_service?authSource=admin
    ports: ["8000:8000"]
    depends_on: [mongodb]
    
  frontend:
    build: ../frontend
    ports: ["3000:3000"]
    depends_on: [content-service]
```

## 📊 **PROJECT STRUCTURE**

### **Backend Structure**
```
backend/content_service/
├── app/
│   ├── main.py                           # ✅ FastAPI application setup
│   ├── models.py                         # ✅ Pydantic data models
│   ├── auth.py                           # ✅ JWT authentication
│   ├── rbac_service.py                   # ✅ RBAC permission engine
│   ├── rbac_models.py                    # ✅ RBAC data models
│   ├── repo.py                           # ✅ Repository pattern
│   └── api/
│       ├── auth.py                       # ✅ Authentication endpoints
│       ├── users.py                      # ✅ User management
│       ├── companies.py                  # ✅ Company management
│       ├── content.py                    # ✅ Content management
│       ├── devices.py                    # ✅ Device management
│       └── analytics.py                  # ✅ Analytics endpoints
├── pyproject.toml                        # ✅ UV configuration
├── uv.lock                              # ✅ Dependency lock file
└── tests/                               # ✅ Test suite
```

### **Frontend Structure**
```
frontend/
├── src/
│   ├── app/
│   │   ├── login/page.tsx               # ✅ Authentication
│   │   └── dashboard/
│   │       ├── users/page.tsx           # ✅ User management
│   │       ├── companies/page.tsx       # ✅ Company management
│   │       ├── content/page.tsx         # ✅ Content management
│   │       └── analytics/page.tsx       # ✅ Analytics dashboard
│   ├── components/
│   │   ├── ui/                          # ✅ shadcn/ui components
│   │   └── PermissionGate.tsx           # ✅ RBAC UI component
│   └── hooks/
│       └── useAuth.ts                   # ✅ Authentication hook
├── package.json
└── next.config.js
```

## 🧪 **TESTING STRATEGY**

### **Backend Testing with UV**
```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio pytest-cov

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_auth.py

# Run tests matching pattern
uv run pytest -k "test_login"
```

### **Test Structure**
```
tests/
├── conftest.py                          # ✅ Test configuration
├── test_auth.py                         # ✅ Authentication tests
├── test_rbac.py                         # ✅ RBAC tests
├── test_users.py                        # ✅ User management tests
├── test_companies.py                    # ✅ Company management tests
└── test_integration.py                  # ✅ End-to-end tests
```

## 📈 **DATABASE DESIGN**

### **MongoDB Collections**
```javascript
// Companies Collection
{
  _id: ObjectId,
  name: String,
  organization_code: String,           // ORG-XXXXXXX format
  type: "HOST" | "ADVERTISER",
  registration_key: String,            // 16-character secure key
  status: "active" | "inactive",
  created_at: Date,
  updated_at: Date
}

// Users Collection
{
  _id: ObjectId,
  email: String,
  hashed_password: String,
  user_type: "SUPER_USER" | "COMPANY_USER" | "DEVICE_USER",
  company_id: String,                  // null for SUPER_USER
  permissions: [String],               // Resource-action permissions
  is_active: Boolean,
  created_at: Date,
  updated_at: Date
}

// Content Collection
{
  _id: ObjectId,
  owner_id: String,                    // Company ID
  filename: String,
  content_type: String,
  status: "pending" | "approved" | "rejected",
  ai_moderation_score: Number,
  metadata: Object,
  created_at: Date,
  updated_at: Date
}

// Devices Collection
{
  _id: ObjectId,
  name: String,
  company_id: String,
  api_key: String,                     // Unique authentication key
  device_type: String,
  location: String,
  status: "active" | "inactive" | "maintenance",
  last_seen: Date,
  created_at: Date,
  updated_at: Date
}
```

## 🔮 **DEVELOPMENT ROADMAP**

### **Phase 1: Core Platform (Completed)**
- ✅ Multi-tenant RBAC system
- ✅ User and company management
- ✅ Content upload and management
- ✅ Device authentication
- ✅ Basic analytics

### **Phase 2: Enhanced Features (In Progress)**
- 🔄 AI content moderation integration
- 🔄 Advanced analytics and reporting
- 🔄 Content scheduling and distribution
- 🔄 Payment and billing system

### **Phase 3: Mobile Application**
- ❌ Flutter digital signage app
- ❌ QR code device registration
- ❌ Offline content synchronization
- ❌ Interactive content support

### **Phase 4: Enterprise Features**
- ❌ Advanced security features
- ❌ Compliance reporting
- ❌ White-label customization
- ❌ API integrations

## 🚨 **PRODUCTION CHECKLIST**

### **Security**
- [ ] Change default secret keys
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Set up audit logging

### **Performance**
- [ ] Configure Redis caching
- [ ] Set up CDN for media files
- [ ] Optimize database queries
- [ ] Implement connection pooling

### **Monitoring**
- [ ] Set up application logs
- [ ] Configure error tracking
- [ ] Implement health checks
- [ ] Set up monitoring dashboards

### **Deployment**
- [ ] Configure Azure infrastructure
- [ ] Set up CI/CD pipelines
- [ ] Configure backup strategies
- [ ] Set up monitoring alerts

## 📞 **QUICK REFERENCE COMMANDS**

### **Development**
```bash
# Start backend
cd backend/content_service
uv run uvicorn app.main:app --reload

# Start frontend
cd frontend
npm run dev

# Run tests
uv run pytest

# Seed demo data
uv run python seed_data.py
```

### **Package Management**
```bash
# Add dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade

# Show installed packages
uv list
```

### **Database**
```bash
# Start MongoDB with Docker
docker run -d -p 27017:27017 mongo:7.0

# Connect to MongoDB
mongosh mongodb://localhost:27017/openkiosk
```

This comprehensive documentation provides everything needed to understand, develop, and deploy the Adārah Digital Signage Platform using modern tools like UV for Python package management.
