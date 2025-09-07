# Claude.md - Comprehensive Application Understanding & Cleanup Guide

## 📋 **PROJECT OVERVIEW**

**Project Name**: Adara Screen Digital Signage Platform  
**Type**: Enterprise Multi-Tenant Digital Signage Platform with Advanced RBAC  
**Architecture**: FastAPI Backend + Next.js Frontend + Flutter Mobile App  
**Target Market**: UAE/Dubai enterprise digital signage and multi-company management  

### **Core Business Model**
- **Multi-Tenant Architecture**: Support unlimited companies with complete data isolation
- **HOST Companies**: Own physical screens/kiosks, manage devices and locations  
- **ADVERTISER Companies**: Create content, participate in content sharing workflows
- **Platform**: Facilitates secure content distribution with advanced permission controls and revenue sharing

## 🧹 **CODE CLEANUP STATUS & STANDARDS** *(Updated 2025-09-07)*

### **✅ COMPLETED CLEANUPS**

#### **Frontend Consolidation**
- **✅ Content Management Pages**: Eliminated 4 duplicate content pages
  - `/dashboard/content/page.tsx` - Consolidated to use ContentManager (585 lines → 5 lines)
  - `/dashboard/my-ads/page.tsx` - Consolidated to use ContentManager (103 lines → 5 lines)
  - Created unified `ContentManager` component for all content operations
  - **Before**: Separate duplicate pages with repeated UI, filters, and logic
  - **After**: Single reusable ContentManager with mode-based rendering

- **✅ Shared Components Created**:
  - `PageLayout.tsx` - Standardized page wrapper with loading states and error handling
  - `ContentManager.tsx` - Unified content management with RBAC integration
  - Uses consistent shadcn/ui components and styling patterns

- **✅ Upload Hook Consolidation**:
  - Created `useUploadConsolidated.ts` merging functionality from duplicate hooks
  - **Note**: Original `useUpload.ts` preserved due to manual edits, both coexist for now

- **✅ Unified Dashboard Integration**:
  - Added ContentManager to unified dashboard as new "Content" tab
  - Fixed TypeScript errors related to company role checks
  - Replaced string-based role checks with proper enum usage (`CompanyRole.ADMIN`)
  - Used `isHostCompany()` and `isAdvertiserCompany()` for company type checks

#### **Standards Established**
- **Component Structure**: All new components use shadcn/ui with consistent props pattern
- **RBAC Integration**: Proper use of `hasRole()`, `hasPermission()`, `isHostCompany()`, `isAdvertiserCompany()`
- **TypeScript**: Strict typing with proper enum usage (`CompanyRole`, `CompanyType`, `UserType`)
- **Error Handling**: Consistent error states and loading patterns across components

### **🔄 IN PROGRESS**

#### **Backend Auth Consolidation** *(Next Priority)*
- **Issues Identified**:
  - `/app/auth.py` (645 lines) - Large auth file with JWT and password handling
  - `/app/auth_service.py` (206 lines) - Clean authentication service
  - `/app/api/auth.py` (108 lines) - Authentication API endpoints
  - Mixed imports across codebase using both auth systems

- **Cleanup Strategy**:
  - Keep `auth_service.py` as core service (cleaner, more focused)
  - Migrate missing functionality from `auth.py` to `auth_service.py`
  - Keep `/api/auth.py` for API endpoints
  - Remove duplicate `auth.py`
  - Update all imports to use consolidated system

#### **API Structure Consolidation**
- **Issues Identified**:
  - `/app/api/` directory with most endpoints (20+ files)
  - `/app/routes/` directory with only `content.py` and `overlay.py`
  - Inconsistent import patterns

- **Cleanup Strategy**:
  - Move `content.py` and `overlay.py` from `/routes/` to `/api/`
  - Remove `/routes/` directory
  - Update all imports and main.py route registration
  - Standardize API organization under single `/api/` structure

### **📋 PENDING CLEANUP TASKS**

1. **Flutter Architecture Cleanup**:
   - Resolve `/screens/` vs `/pages/` directory confusion
   - Implement consistent naming conventions
   - Consolidate duplicate navigation patterns

2. **Upload System Unification**:
   - Fully replace `useUpload.ts` with `useUploadConsolidated.ts`
   - Update all components to use consolidated hook
   - Remove legacy upload implementations

3. **ContentManager Enhancement**:
   - Add remaining modes ('review', 'upload') to ContentManager
   - Replace more duplicate content-related pages
   - Implement consistent action handlers across all modes

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

This comprehensive documentation provides everything needed to understand, develop, and deploy the Adara Screen Digital Signage Platform using modern tools like UV for Python package management.
