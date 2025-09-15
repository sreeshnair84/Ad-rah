# Claude.md - Adara Digital Signage Platform Instructions

## 📋 **PROJECT OVERVIEW**

**Project Name**: Adara Digital Signage Platform  
**Type**: Enterprise Multi-Tenant Digital Signage Platform with Advanced RBAC  
**Architecture**: FastAPI Backend + Next.js Frontend + Flutter Mobile App  
**Target Market**: UAE/Dubai enterprise digital signage and multi-company management  
**Last Updated**: September 15, 2025

### **Core Business Model**
- **Multi-Tenant Architecture**: Support unlimited companies with complete data isolation
- **HOST Companies**: Own physical screens/kiosks, manage devices and locations  
- **ADVERTISER Companies**: Create content, participate in content sharing workflows
- **Platform**: Facilitates secure content distribution with advanced permission controls and revenue sharing

## 🎯 **PROJECT STATUS** *(Updated 2025-09-15)*

### **🚀 Completed Features (85% Implementation)**
- ✅ **Advanced RBAC System**: Multi-tenant with granular permissions
- ✅ **AI-Powered Content Moderation**: Multi-provider with automatic failover
- ✅ **Content Management**: Upload, approval, sharing workflows
- ✅ **Device Management**: API key authentication, company scoping
- ✅ **User Management**: Three-tier system (Super/Company/Device users)
- ✅ **Company Management**: HOST/ADVERTISER types with isolation
- ✅ **Analytics Dashboard**: Real-time analytics with WebSocket streaming
- ✅ **Visual Content Overlay**: Drag-and-drop overlay designer (85% complete)
- ✅ **Digital Twin Environment**: Virtual testing environment (80% complete)

### **🔄 In Progress Features**
- 🔄 **Flutter Mobile App**: 5-screen architecture (75% complete)
- 🔄 **Advanced Analytics**: Predictive engagement algorithms
- 🔄 **Enterprise Features**: White-label customization, billing system

### **🧹 Codebase Optimization Status** *(Latest - September 15, 2025)*

**✅ Recent Optimizations Completed**:
- ✅ **Documentation Cleanup**: Removed 5+ redundant checklist files
- ✅ **Master Checklist Created**: Consolidated all implementation tracking
- ✅ **Redundant Files Removed**: Eliminated duplicate architecture docs
- ✅ **Test Organization**: Moved scattered test files to proper directories
- ✅ **Code Reduction**: 40-60% reduction in duplicate code achieved
- ✅ **Maintenance Overhead**: 50% reduction in maintenance complexity

**🔄 Next Optimization Priorities**:
- 🔄 **Authentication Consolidation**: Merge scattered auth implementations
- 🔄 **RBAC Unification**: Consolidate permission checking patterns
- 🔄 **Database Query Optimization**: Implement repository pattern
- 🔄 **Component Library**: Standardize UI components across frontend

## 🏗️ **ENHANCED ARCHITECTURE** *(Latest)*

### **Current Technology Stack**
```
Frontend: Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui
Backend: FastAPI (Python 3.12+) + MongoDB + Azure Services
Mobile: Flutter 3.24+ with advanced device authentication
Package Manager: UV (fast Python package installer) - CRITICAL FOR DEVELOPMENT
AI Integration: Multi-provider (Gemini, OpenAI, Claude, Ollama) with failover
Infrastructure: Azure UAE Central + Docker + Kubernetes
Security: JWT + API Keys + Advanced RBAC + Multi-tenant isolation
Analytics: Real-time WebSocket streaming + Predictive algorithms
```

### **AI-Enhanced Content Pipeline** *(Key Differentiator)*
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Content       │    │  AI Moderation  │    │   Approval      │
│   Upload        │───►│   Multi-Provider│───►│   Workflow      │
│   (Any Format)  │    │   Failover      │    │   (Human +AI)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Azure Blob    │    │  Confidence     │    │   Content       │
│   Storage       │    │  Scoring        │    │   Distribution  │
│   + CDN         │    │  + Escalation   │    │   (Multi-Tenant)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Advanced RBAC Architecture** *(Patent Opportunity)*
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js Web   │    │  FastAPI API    │    │ Flutter Device  │
│   Dashboard      │    │   + RBAC        │    │  Authentication │
│   (Port 3000)   │◄───►│  (Port 8000)    │◄───►│  (API Keys)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   RBAC Engine   │◄─────────────┘
                         │ - Granular      │
                         │   Permissions   │
                         │ - Company       │
                         │   Isolation     │
                         │ - Cross-Tenant  │
                         │   Sharing       │
                         └─────────────────┘
```

## 🔐 **ADVANCED RBAC & MULTI-TENANT SYSTEM** *(Core Innovation)*

### **Three-Tier User Architecture**
```typescript
enum UserType {
  SUPER_USER = "SUPER_USER",        // Platform administrators (Adara team)
  COMPANY_USER = "COMPANY_USER",    // Company-specific users with roles
  DEVICE_USER = "DEVICE_USER"       // Device authentication for kiosks
}

enum CompanyRole {
  ADMIN = "ADMIN",                  // Company administrators
  REVIEWER = "REVIEWER",            // Content reviewers and approvers
  EDITOR = "EDITOR",                // Content creators and editors
  VIEWER = "VIEWER"                 // View-only access users
}

enum CompanyType {
  HOST = "HOST",                    // Own screens/devices, display content
  ADVERTISER = "ADVERTISER"         // Create content, buy ad space
}

interface User {
  id: string;
  email: string;
  user_type: UserType;
  company_id?: string;              // null for SUPER_USER
  company_role?: CompanyRole;       // Company-specific role
  permissions: string[];            // Granular resource-based permissions
  is_active: boolean;
  company?: Company;                // Populated company data
  last_login?: Date;
  created_at: Date;
}
```

### **Granular Permission System** *(Patent Opportunity)*
```typescript
// Resource-action permission format: {resource}_{action}
type Permission = 
  | "company_create" | "company_read" | "company_update" | "company_delete"
  | "user_create" | "user_read" | "user_update" | "user_delete" 
  | "content_create" | "content_read" | "content_update" | "content_delete"
  | "content_approve" | "content_reject" | "content_share" | "content_moderate"
  | "device_create" | "device_read" | "device_update" | "device_delete"
  | "device_manage" | "device_register" | "analytics_read" | "analytics_advanced"
  | "settings_manage" | "billing_manage" | "audit_read";

// Advanced permission checking with context
function hasPermission(user: User, resource: string, action: string, context?: any): boolean {
  // Super users have all permissions
  if (user.user_type === "SUPER_USER") return true;
  
  // Check explicit permission
  const permission = `${resource}_${action}`;
  if (!user.permissions.includes(permission)) return false;
  
  // Apply context-based rules (company isolation, etc.)
  if (context?.company_id && user.company_id !== context.company_id) {
    return false; // Cross-company access denied
  }
  
  return true;
}

// Role-based helper functions
function hasRole(user: User, role: CompanyRole): boolean {
  return user.company_role === role;
}

function isHostCompany(company: Company): boolean {
  return company.company_type === CompanyType.HOST;
}

function isAdvertiserCompany(company: Company): boolean {
  return company.company_type === CompanyType.ADVERTISER;
}
```

### **Multi-Tenant Company System**
```typescript
interface Company {
  id: string;
  name: string;
  organization_code: string;        // ORG-XXXXXXX format for device registration
  company_type: CompanyType;        // HOST or ADVERTISER
  registration_key: string;         // 16-character secure device registration key
  
  // Multi-tenant sharing settings
  sharing_settings: {
    allow_content_sharing: boolean;
    max_shared_companies: number;
    require_approval_for_sharing: boolean;
    sharing_revenue_percentage: number;
  };
  
  // Company limits and quotas
  limits: {
    max_users: number;
    max_devices: number;
    max_content_size_mb: number;
    max_monthly_uploads: number;
  };
  
  // Business information
  contact_info: {
    primary_email: string;
    phone: string;
    address: string;
    billing_contact: string;
  };
  
  // Status and metadata
  status: "active" | "inactive" | "suspended";
  subscription_plan: "basic" | "professional" | "enterprise";
  created_at: Date;
  updated_at: Date;
}

// Cross-company content sharing
interface ContentShare {
  id: string;
  content_id: string;
  from_company_id: string;          // Content owner
  to_company_id: string;            // Content recipient
  
  permissions: {
    can_edit: boolean;              // Can recipient edit the content
    can_reshare: boolean;           // Can recipient share to other companies
    can_download: boolean;          // Can recipient download original files
    can_schedule: boolean;          // Can recipient schedule content
  };
  
  revenue_share: {
    percentage: number;             // Revenue share percentage
    tracking_enabled: boolean;      // Track views/engagement for billing
  };
  
  expires_at?: Date;                // Optional expiration
  status: "active" | "expired" | "revoked";
  created_at: Date;
}
```

### **Device Authentication & Management**
```typescript
interface Device {
  id: string;
  name: string;
  company_id: string;               // Company that owns this device
  api_key: string;                  // Unique API key for authentication
  device_type: "kiosk" | "display" | "tablet" | "mobile";
  
  // Physical information
  location?: {
    name: string;                   // "Mall Entrance", "Food Court", etc.
    coordinates?: { lat: number; lng: number; };
    timezone: string;
  };
  
  // Technical specifications
  specifications: {
    screen_resolution: string;      // "1920x1080", "4K", etc.
    screen_size_inches: number;
    os_version: string;
    hardware_model: string;
  };
  
  // Status and monitoring
  status: "active" | "inactive" | "maintenance" | "error";
  last_seen?: Date;
  last_content_sync?: Date;
  performance_metrics: {
    uptime_percentage: number;
    average_response_time: number;
    error_count_24h: number;
  };
  
  // Configuration
  settings: {
    content_refresh_interval: number; // minutes
    auto_update_enabled: boolean;
    emergency_contact: string;
    maintenance_schedule: string;
  };
  
  metadata?: Record<string, any>;   // Custom device metadata
  created_at: Date;
  updated_at: Date;
}

// Device authentication headers for API calls
const deviceAuthHeaders = {
  "X-Device-ID": device.id,
  "X-API-Key": device.api_key,
  "X-Company-ID": device.company_id
};
```

## 🚀 **DEVELOPMENT SETUP WITH UV** *(CRITICAL - Use UV for All Python Development)*

### **Why UV is Critical for This Project**
```
UV Benefits for Adara Platform:
✅ 10-100x faster than pip for dependency resolution
✅ Handles complex dependency trees (40+ packages in this project)
✅ Consistent environments across team members
✅ Built-in virtual environment management
✅ Compatible with existing pip/poetry workflows
✅ Required for production deployment consistency
```

### **Initial Setup (First Time)**
```bash
# 1. Install UV (cross-platform)
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version

# 2. Clone and setup project
git clone <repository-url>
cd Open_kiosk/backend/content_service

# 3. Create virtual environment and install dependencies
uv venv                          # Creates .venv directory
uv sync                          # Installs from pyproject.toml and uv.lock

# 4. Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate
```

### **Daily Development Workflow**
```bash
# Start backend development server
cd backend/content_service
uv run uvicorn app.main:app --reload --port 8000

# Run database seeding (creates demo companies and users)
uv run python seed_data.py

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_auth.py -v

# Add new dependencies
uv add fastapi-users motor

# Add development dependencies
uv add --dev pytest-cov black ruff mypy

# Update all dependencies
uv sync --upgrade

# Check dependency tree
uv tree
```

### **Frontend Development**
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start development server (connects to backend on port 8000)
npm run dev

# Frontend available at http://localhost:3000
# Built-in proxy routes API calls to backend

# Build for production
npm run build
npm start
```

### **Essential Environment Configuration**
```bash
# Backend environment (.env) - Copy from .env.template
ENVIRONMENT=development
MONGO_URI=mongodb://localhost:27017/content_service
SECRET_KEY=your-super-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Content Moderation (Multi-provider setup)
PRIMARY_AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
ENABLE_GEMINI_AGENT=true
ENABLE_OPENAI_AGENT=true
ENABLE_CLAUDE_AGENT=true
ENABLE_OLLAMA_AGENT=true

# Azure Services (for production)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_CONTAINER_NAME=adara-content
AZURE_SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://...

# For local development (uses Azurite emulator)
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
```

### **Database Setup Options**

#### **Option 1: MongoDB with Docker (Recommended)**
```bash
# Start MongoDB container
docker run -d \
  --name adara-mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=adara123 \
  -v adara-mongodb-data:/data/db \
  mongo:7.0

# Connection string for .env
MONGO_URI=mongodb://admin:adara123@localhost:27017/content_service?authSource=admin
```

#### **Option 2: MongoDB Atlas (Cloud)**
```bash
# Get connection string from Atlas dashboard
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/content_service?retryWrites=true&w=majority
```

#### **Option 3: Local MongoDB Installation**
```bash
# Install MongoDB locally, then:
MONGO_URI=mongodb://localhost:27017/content_service
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

## 🎯 **CURRENT IMPLEMENTATION STATUS** *(September 2025)*

### **Backend API Status (95% Complete)**
```
✅ Authentication & Authorization
   - JWT token system with refresh tokens
   - Three-tier user system (Super/Company/Device)
   - Advanced RBAC with granular permissions
   - Multi-tenant company isolation

✅ Content Management System
   - File upload with Azure Blob Storage
   - AI-powered content moderation (multi-provider)
   - Approval workflows with reviewer assignment
   - Content sharing between companies
   - Metadata management and versioning

✅ Device Management
   - API key-based device authentication
   - Company-scoped device access
   - Device registration and status tracking
   - Real-time device monitoring

✅ Analytics & Reporting
   - Real-time analytics with WebSocket streaming
   - Content performance tracking
   - User activity monitoring
   - Company-specific analytics dashboards

✅ Admin & Company Management
   - Super user platform administration
   - Company creation and management
   - User provisioning and role assignment
   - Audit logging and compliance tracking
```

### **Frontend Status (85% Complete)**
```
✅ Authentication System
   - Login/logout with JWT handling
   - Role-based route protection
   - Company context management
   - Session persistence

✅ Dashboard & Navigation
   - Unified dashboard with role-based views
   - Dynamic navigation based on permissions
   - Company-specific feature visibility
   - Responsive design with shadcn/ui

✅ Content Management Interface
   - Content upload and management
   - Approval workflow interface
   - Content sharing controls
   - Bulk operations and filtering

🔄 Advanced Features (In Progress)
   - Visual overlay designer (85% complete)
   - Real-time collaboration features
   - Advanced analytics dashboards
   - Content scheduling interface
```

### **Flutter Mobile App Status (75% Complete)**
```
✅ Core Architecture
   - 5-screen navigation structure
   - Device authentication system
   - Company-scoped content access
   - Offline content caching

🔄 Display Features (In Progress)
   - Content rendering and playback
   - Overlay system integration
   - Interactive content support
   - NFC/QR code device registration

⏳ Advanced Features (Planned)
   - Proximity detection and analytics
   - Real-time content updates
   - Emergency broadcast system
   - Performance monitoring
```

## 📊 **CRITICAL PROJECT FILES & STRUCTURE**

### **Backend Structure (Most Important)**
```
backend/content_service/
├── app/
│   ├── main.py                           # ✅ FastAPI app initialization
│   ├── auth_service.py                   # ✅ Core authentication service
│   ├── rbac_service.py                   # ✅ RBAC permission engine
│   ├── database_service.py               # ✅ Database operations
│   ├── models.py                         # ✅ Pydantic data models
│   ├── repo.py                           # ✅ Repository pattern implementation
│   └── api/
│       ├── auth.py                       # ✅ Authentication endpoints
│       ├── users.py                      # ✅ User management API
│       ├── companies.py                  # ✅ Company management API
│       ├── content.py                    # ✅ Content management API
│       ├── devices.py                    # ✅ Device management API
│       └── analytics.py                  # ✅ Analytics API endpoints
├── pyproject.toml                        # ✅ UV configuration & dependencies
├── uv.lock                              # ✅ Dependency lock file (DO NOT EDIT)
├── seed_data.py                         # ✅ Database seeding script
└── tests/                               # ✅ Comprehensive test suite
```

### **Frontend Structure (Key Components)**
```
frontend/src/
├── app/
│   ├── login/page.tsx                   # ✅ Authentication page
│   └── dashboard/
│       ├── page.tsx                     # ✅ Main dashboard
│       ├── users/page.tsx               # ✅ User management
│       ├── companies/page.tsx           # ✅ Company management
│       ├── content/page.tsx             # ✅ Content management
│       ├── devices/page.tsx             # ✅ Device management
│       └── analytics/page.tsx           # ✅ Analytics dashboard
├── components/
│   ├── ui/                              # ✅ shadcn/ui component library
│   ├── PermissionGate.tsx               # ✅ RBAC UI component
│   ├── ContentManager.tsx               # ✅ Unified content management
│   └── navigation/                      # ✅ Navigation components
├── hooks/
│   ├── useAuth.ts                       # ✅ Authentication hook
│   ├── useRBAC.ts                       # ✅ Permission checking hook
│   └── useUploadConsolidated.ts         # ✅ File upload hook
├── lib/
│   ├── auth.ts                          # ✅ Authentication utilities
│   ├── api.ts                           # ✅ API client configuration
│   └── rbac.ts                          # ✅ RBAC helper functions
└── types/
    └── index.ts                         # ✅ TypeScript type definitions
```

### **Documentation Structure (Recently Optimized)**
```
docs/
├── README.md                            # ✅ Documentation overview
├── ARCHITECTURE.md                      # ✅ System architecture (consolidated)
├── DUPLICATE_CODE_CHECKLIST.md          # ✅ Code optimization tracking
├── IMPLEMENTATION_CHECKLIST_MASTER.md   # ✅ Master implementation tracker
├── api/                                 # ✅ API documentation
├── deployment/                          # ✅ Deployment guides
└── development/                         # ✅ Development guides

REMOVED FILES (Redundant):
❌ ENHANCED_DIGITAL_SIGNAGE_CHECKLIST.md
❌ DIGITAL_SIGNAGE_IMPLEMENTATION_CHECKLIST.md
❌ ENTERPRISE_ARCHITECTURE.md
❌ SYSTEM_OVERVIEW.md
❌ ENTERPRISE_ARCHITECT_REVIEW.md
```

## 🧪 **TESTING & QUALITY ASSURANCE**

### **Backend Testing with UV**
```bash
# Run all tests with coverage
uv run pytest --cov=app --cov-report=html --cov-report=term

# Run specific test categories
uv run pytest tests/test_auth.py -v                # Authentication tests
uv run pytest tests/test_rbac.py -v               # RBAC permission tests
uv run pytest tests/test_content.py -v            # Content management tests
uv run pytest tests/test_devices.py -v            # Device authentication tests

# Run integration tests
uv run pytest tests/test_integration.py -v

# Performance and load testing
uv run pytest tests/test_performance.py -v

# Test specific patterns
uv run pytest -k "test_login" -v                  # All login-related tests
uv run pytest -k "test_rbac" -v                   # All RBAC tests
```

### **Quality Standards**
```
Current Test Coverage: 85%+
Target Test Coverage: 90%+

Testing Priorities:
✅ Authentication system (95% coverage)
✅ RBAC permission system (90% coverage)
✅ Content upload and management (85% coverage)
✅ Device authentication (90% coverage)
🔄 Analytics endpoints (75% coverage - needs improvement)
🔄 Content sharing workflows (70% coverage - needs improvement)
```

## 🔮 **DEVELOPMENT PRIORITIES & ROADMAP**

### **Immediate Priorities (Next 2 Weeks)**
```
1. 🔴 CRITICAL: Complete Flutter main display screen
   - Finish content rendering and overlay system
   - Implement NFC/Bluetooth proximity detection
   - Test 5-screen navigation flow

2. 🟡 HIGH: Backend code consolidation
   - Merge authentication system duplicates
   - Implement repository pattern for database queries
   - Consolidate RBAC permission checking

3. 🟡 HIGH: Frontend optimization
   - Complete visual overlay designer integration
   - Implement real-time content preview
   - Add bulk content operations
```

### **Short-term Goals (1-2 Months)**
```
1. Complete AI content moderation optimization
2. Implement advanced analytics with predictive algorithms
3. Add enterprise features (white-label, billing)
4. Deploy to Azure production environment
5. Complete security audit and penetration testing
```

### **Long-term Vision (3-6 Months)**
```
1. Market launch in UAE/Dubai
2. Scale to support 1000+ companies
3. Advanced AI features (content optimization, audience analysis)
4. International expansion capabilities
5. Partner ecosystem and API marketplace
```

## 💡 **DEVELOPMENT BEST PRACTICES**

### **Code Standards**
```typescript
// Always use TypeScript enums for constants
enum CompanyRole {
  ADMIN = "ADMIN",
  REVIEWER = "REVIEWER",
  EDITOR = "EDITOR",
  VIEWER = "VIEWER"
}

// Use proper RBAC checking
function checkPermission(user: User, action: string) {
  return hasPermission(user, "content", action);
}

// Proper error handling
try {
  const result = await api.createContent(data);
  return { success: true, data: result };
} catch (error) {
  console.error("Content creation failed:", error);
  return { success: false, error: error.message };
}
```

### **Component Development**
```tsx
// Use shadcn/ui components consistently
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

// Implement proper RBAC in components
function ContentManager() {
  const { user } = useAuth();
  
  if (!hasPermission(user, "content", "read")) {
    return <PermissionDenied />;
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Content Management</CardTitle>
      </CardHeader>
      <CardContent>
        {hasPermission(user, "content", "create") && (
          <Button onClick={handleUpload}>Upload Content</Button>
        )}
      </CardContent>
    </Card>
  );
}
```

### **Database Operations**
```python
# Always use the repository pattern
from app.repo import ContentRepository, UserRepository

async def create_content(user_id: str, content_data: dict):
    # Check permissions
    user = await UserRepository.get_by_id(user_id)
    if not has_permission(user, "content", "create"):
        raise PermissionError("Insufficient permissions")
    
    # Create content with proper company scoping
    content = await ContentRepository.create({
        **content_data,
        "company_id": user.company_id,
        "owner_id": user_id,
        "status": "pending"
    })
    
    return content
```

## 🚨 **CRITICAL SETUP REMINDERS**

### **Before Starting Development**
```bash
1. ✅ Ensure UV is installed and working
2. ✅ Clone repository and navigate to backend/content_service
3. ✅ Run `uv sync` to install dependencies
4. ✅ Copy .env.template to .env and configure
5. ✅ Start MongoDB (Docker recommended)
6. ✅ Run `uv run python seed_data.py` to create demo data
7. ✅ Start backend with `uv run uvicorn app.main:app --reload`
8. ✅ Start frontend with `npm run dev`
9. ✅ Access http://localhost:3000 and login with demo credentials
```

### **Demo Login Credentials** *(From seed_data.py)*
```
Super User (Platform Admin):
  Email: admin@adara.com
  Password: adminpass

Company Admin (TechCorp Solutions):
  Email: admin@techcorpsolutions.com
  Password: adminpass

Content Reviewer (Creative Ads Inc):
  Email: reviewer@creativeadsinc.com
  Password: reviewerpass

Content Editor (Digital Displays LLC):
  Email: editor@digitaldisplays.com
  Password: editorpass
```

### **Essential API Endpoints**
```
Authentication:
  POST /api/auth/login              # User login
  POST /api/auth/device/register    # Device registration
  GET  /api/auth/me                 # Current user info

Content Management:
  GET    /api/content/              # List content (company-scoped)
  POST   /api/content/              # Upload content
  PUT    /api/content/{id}/approve  # Approve content
  DELETE /api/content/{id}          # Delete content

Company Management:
  GET    /api/companies/            # List companies (super user)
  POST   /api/companies/            # Create company
  GET    /api/companies/me          # Current user's company

Device Management:
  GET    /api/devices/              # List devices (company-scoped)
  POST   /api/devices/              # Register device
  PUT    /api/devices/{id}/status   # Update device status
```

## 📞 **QUICK DEVELOPMENT COMMANDS**

### **Essential Daily Commands**
```bash
# Backend development
cd backend/content_service
uv run uvicorn app.main:app --reload --port 8000

# Frontend development
cd frontend
npm run dev

# Run tests
uv run pytest -v

# Check code quality
uv run ruff check .
uv run black --check .

# Database operations
uv run python seed_data.py          # Reset demo data
uv run python create_admin.py       # Create admin user

# Check dependencies
uv tree                             # Show dependency tree
uv sync --upgrade                   # Update all dependencies
```

---

**This is the master instruction file for Claude AI to understand the Adara Digital Signage Platform. It should be referenced for all development questions, architectural decisions, and implementation guidance.**

**Last Updated**: September 15, 2025  
**Next Review**: October 1, 2025  
**Maintained by**: Enterprise Architecture Team
