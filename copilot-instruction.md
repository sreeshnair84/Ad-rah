# GitHub Copilot Instructions for Adara Screen Digital Signage Platform

## 🎯 **PROJECT OVERVIEW**

You are working on **Adara Screen Digital Signage Platform**, a **FULLY IMPLEMENTED** comprehensive **multi-tenant digital signage and content management platform** with advanced **Role-Based Access Control (RBAC)**. This enterprise-grade system connects **HOST companies** (screen/location owners) with **ADVERTISER companies** (content creators) through a sophisticated content distribution and revenue-sharing platform.

### **Core Business Model** ✅ **FULLY OPERATIONAL**
- **HOST Companies**: Own physical screens/kiosks with device management capabilities
- **ADVERTISER Companies**: Create content with sharing and approval workflows  
- **Platform**: Advanced multi-tenant architecture with three-tier user system and permission-based access control
- **Device Authentication**: Secure API key-based authentication for Flutter kiosk devices

### **Implementation Status** ✅ **PRODUCTION READY**
- **Backend API**: Complete FastAPI implementation with comprehensive endpoints
- **Frontend Dashboard**: Full Next.js application with permission-based UI
- **Flutter Kiosk App**: Complete 5-screen architecture for digital signage
- **RBAC System**: Fully implemented three-tier user system with granular permissions
- **Multi-Tenant Architecture**: Complete company isolation and data separation
- **AI Content Moderation**: Multi-provider AI framework with automatic failover
- **Infrastructure**: Azure deployment ready with Docker and CI/CD pipeline

## 🧹 **CODE STANDARDS & CLEANUP GUIDELINES** *(Updated 2025-09-07)*

### **✅ MANDATORY STANDARDS**

#### **Frontend Component Standards**
```typescript
// ✅ CORRECT: Use shared components and consolidated patterns
import { ContentManager } from '@/components/content/ContentManager';
import { PageLayout } from '@/components/shared/PageLayout';

export default function MyPage() {
  return <ContentManager mode="all" />;  // Simple, reusable
}

// ❌ AVOID: Creating new duplicate pages with repeated UI logic
export default function MyPage() {
  const [content, setContent] = useState([]); // Duplicates ContentManager logic
  // 400+ lines of repeated filtering, UI, and state management
}
```

#### **Hook Consolidation Standards**
```typescript
// ✅ CORRECT: Use consolidated hooks
import { useUploadConsolidated } from '@/hooks/useUploadConsolidated';
// OR maintain existing manual edits
import { useUpload } from '@/hooks/useUpload'; // Preserved due to manual edits

// ❌ AVOID: Creating new duplicate hooks
const useCustomUpload = () => { /* duplicate functionality */ };
```

#### **RBAC Integration Standards**
```typescript
// ✅ CORRECT: Proper RBAC usage
import { CompanyRole, CompanyType } from '@/types/auth';
const { hasRole, hasPermission, isHostCompany, isAdvertiserCompany } = useAuth();

// Company type checks
if (isHostCompany()) { /* HOST specific logic */ }
if (isAdvertiserCompany()) { /* ADVERTISER specific logic */ }

// Role checks
if (hasRole(CompanyRole.ADMIN)) { /* Admin specific logic */ }

// Permission checks
if (hasPermission('content', 'create')) { /* Action allowed */ }

// ❌ AVOID: String-based role checks
if (hasRole('HOST')) { /* TypeScript error */ }
if (hasRole('ADVERTISER')) { /* TypeScript error */ }
```

### **📋 COMPONENT CONSOLIDATION RULES**

#### **Content Management**
- **ALWAYS** use `ContentManager` component for content-related pages
- **NEVER** create duplicate content filtering, listing, or management UI
- **Modes available**: 'all', 'user', 'review', 'upload', 'unified'

#### **Page Layout**
- **ALWAYS** use `PageLayout` component for consistent page structure
- **INCLUDES**: Loading states, error handling, consistent styling
- **PROPS**: title, description, actions, loading, error

#### **Upload Functionality**
- **PREFER** `useUploadConsolidated` for new implementations
- **PRESERVE** existing `useUpload` if manually edited
- **NEVER** create new upload hooks without consolidating existing ones

### **🚫 ANTI-PATTERNS TO AVOID**

1. **Duplicate Function Names**: Always check for existing function names before creating new ones
2. **Multiple Export Defaults**: Only one default export per file
3. **Repeated UI Logic**: Use shared components instead of copying code
4. **String-based RBAC**: Use proper enums and type-safe functions
5. **Manual Permission Checks**: Use established permission helper functions

## 🏗️ **TECHNOLOGY STACK**

### **Backend - FastAPI with Advanced RBAC** ✅ **FULLY IMPLEMENTED**
```python
# Technology: FastAPI + Python 3.12 + MongoDB + Azure Blob Storage + Advanced RBAC
# Location: backend/content_service/
# Package Manager: UV (fast Python package installer)
# Purpose: RBAC-enforced content management, authentication, and business logic

# ✅ FULLY CONSOLIDATED BACKEND:
# - Complete API endpoints in /api/ directory
# - Unified authentication system with JWT
# - Repository pattern with MongoDB integration
# - Comprehensive RBAC permission system

Key Dependencies (pyproject.toml):
- fastapi[email,mail]>=0.116.1    # API framework with email support
- uvicorn>=0.35.0                  # ASGI server
- motor>=3.7.1                     # Async MongoDB driver
- pydantic>=2.11.7                 # Data validation
- pyjwt>=2.10.1                    # JWT tokens
- passlib>=1.7.4                   # Password hashing
- azure-ai-contentsafety>=1.0.0    # AI content moderation
- google-generativeai>=0.8.5       # Gemini AI integration
```

### **Frontend - Next.js with RBAC Components** ✅ **FULLY IMPLEMENTED**
```typescript
// Technology: Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui
// Location: frontend/
// Purpose: Permission-based web dashboard with dynamic UI controls

// ✅ FULLY CONSOLIDATED COMPONENTS:
// - ContentManager.tsx - Unified content management
// - PageLayout.tsx - Standardized page wrapper
// - useUploadConsolidated.ts - Merged upload functionality

Key Features:
- PermissionGate.tsx - Conditional rendering based on permissions
- Enhanced useAuth hook - RBAC-aware authentication
- Permission-based Navigation - Dynamic menu based on user permissions
- Company Context Provider - Multi-tenant company switching
```

### **Mobile - Flutter Digital Signage** ✅ **FULLY IMPLEMENTED**
```dart
// Technology: Flutter 3.24+ with Android TV/tablet support
// Location: flutter/adarah_digital_signage/
// Purpose: Kiosk application with device authentication

Key Features:
- QR code device registration
- API key authentication
- Offline content synchronization
- Interactive content support
- Complete 5-screen architecture
```

## 🔐 **RBAC ARCHITECTURE**

### **Three-Tier User System**
```typescript
enum UserType {
  SUPER_USER = "SUPER_USER",        // Platform administrators
  COMPANY_USER = "COMPANY_USER",    // Company-specific users  
  DEVICE_USER = "DEVICE_USER"       // Device authentication
}

// Granular Permission System
type Permission = 
  | "company_create" | "company_read" | "company_update" | "company_delete"
  | "user_create" | "user_read" | "user_update" | "user_delete" 
  | "content_create" | "content_read" | "content_update" | "content_delete"
  | "content_approve" | "content_reject" | "content_share"
  | "device_create" | "device_read" | "device_update" | "device_delete"
  | "device_manage" | "analytics_read" | "settings_manage";
```

### **RBAC Enforcement**
```python
# Backend Permission Checking
@require_permission("content_create")
async def create_content(content_data: ContentCreate, current_user: User):
    # Only users with content_create permission can access this endpoint
    pass

# Frontend Permission Gates
<PermissionGate permission="user_manage">
  <UserManagementComponent />
</PermissionGate>
```

## 🚀 **DEVELOPMENT WORKFLOW WITH UV**

### **Backend Development Setup**
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to backend
cd backend/content_service

# Create and activate virtual environment
uv venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate  # Linux/Mac

# Install all dependencies from pyproject.toml
uv sync

# Add new dependencies
uv add fastapi uvicorn motor

# Add development dependencies
uv add --dev pytest pytest-asyncio black ruff mypy

# Run the application
uv run uvicorn app.main:app --reload --port 8000

# Run tests
uv run pytest

# Seed demo data
uv run python seed_data.py
```

### **Key Development Commands**
```bash
# Package Management
uv add package-name              # Add dependency
uv add --dev package-name        # Add dev dependency
uv remove package-name           # Remove dependency
uv sync --upgrade               # Update all dependencies
uv tree                         # Show dependency tree
uv lock                         # Create lock file

# Development
uv run uvicorn app.main:app --reload    # Start backend
uv run pytest                          # Run tests
uv run python seed_data.py              # Seed demo data

# Frontend (separate terminal)
cd frontend
npm run dev                             # Start frontend
```

## 🏗️ **PROJECT STRUCTURE** ✅ **FULLY IMPLEMENTED**

### **Backend Structure** - Complete FastAPI Implementation
```
backend/content_service/
├── app/
│   ├── main.py                  # FastAPI application setup ✅
│   ├── auth.py                  # JWT authentication ✅
│   ├── models.py                # Pydantic data models ✅
│   ├── rbac_service.py          # RBAC permission engine ✅
│   ├── rbac_models.py           # RBAC data models ✅
│   ├── repo.py                  # Repository pattern (MongoDB/in-memory) ✅
│   ├── api/
│   │   ├── auth.py              # Authentication endpoints ✅
│   │   ├── users.py             # User management + RBAC ✅
│   │   ├── companies.py         # Company management ✅
│   │   ├── content.py           # Content management ✅
│   │   ├── devices.py           # Device management ✅
│   │   └── analytics.py         # Analytics endpoints ✅
│   ├── services/                # Business logic services ✅
│   ├── database/                # Database configurations ✅
│   └── utils/                   # Utility functions ✅
├── tests/                       # Comprehensive test suite ✅
├── pyproject.toml              # UV configuration and dependencies ✅
├── uv.lock                     # Dependency lock file ✅
└── .env                        # Environment configuration ✅
```

### **Frontend Structure** - Complete Next.js Dashboard
```
frontend/
├── src/
│   ├── app/
│   │   ├── login/page.tsx              # Multi-step authentication ✅
│   │   └── dashboard/
│   │       ├── layout.tsx              # RBAC navigation ✅
│   │       ├── users/page.tsx          # User management ✅
│   │       ├── companies/page.tsx      # Company management ✅
│   │       ├── content/page.tsx        # Content management ✅
│   │       ├── devices/page.tsx        # Device management ✅
│   │       └── analytics/page.tsx      # Analytics dashboard ✅
│   ├── components/
│   │   ├── ui/                         # shadcn/ui components ✅
│   │   ├── PermissionGate.tsx          # RBAC UI component ✅
│   │   └── Sidebar.tsx                 # Permission-based navigation ✅
│   ├── hooks/
│   │   ├── useAuth.ts                  # RBAC-aware authentication ✅
│   │   └── usePermissions.ts           # Permission checking ✅
│   └── lib/
│       ├── api.ts                      # API client ✅
│       └── auth.ts                     # Auth utilities ✅
```

### **Flutter Structure** - Complete Kiosk Application
```
flutter/adarah_digital_signage/
├── lib/
│   ├── screens/
│   │   ├── registration_screen.dart    # Device registration ✅
│   │   ├── display_screen.dart         # Content display ✅
│   │   ├── interaction_screen.dart     # User interaction ✅
│   │   ├── diagnostics_screen.dart     # System diagnostics ✅
│   │   └── error_screen.dart           # Error handling ✅
│   ├── services/
│   │   ├── api_service.dart            # API communication ✅
│   │   ├── auth_service.dart           # Authentication ✅
│   │   └── content_service.dart        # Content management ✅
│   ├── models/                         # Data models ✅
│   └── widgets/                        # UI components ✅
```

## 🔧 **RBAC IMPLEMENTATION GUIDELINES**

### **When Adding New Features**
1. **Define Permissions**: Add resource-action permissions to `rbac_models.py`
2. **Backend Protection**: Use `@require_permission()` decorators on API endpoints
3. **Frontend Gates**: Wrap UI components with `<PermissionGate permission="..." />`
4. **Database Isolation**: Ensure company-scoped queries for multi-tenant data

### **Permission Naming Convention**
```typescript
// Format: {resource}_{action}
"content_create"     // Create content
"content_read"       // View content
"content_update"     // Edit content
"content_delete"     // Delete content
"content_approve"    // Approve content (special action)
"user_manage"        // Manage users in company
"analytics_read"     // View analytics
```

### **Company Isolation Pattern**
```python
# Always filter by company_id for COMPANY_USER
async def get_user_content(current_user: User):
    if current_user.user_type == UserType.SUPER_USER:
        return await repo.get_all_content()
    else:
        return await repo.get_content_by_company(current_user.company_id)
```

## 🧪 **TESTING STRATEGY**

### **Backend Testing with UV**
```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio pytest-cov

# Run specific test categories
uv run pytest tests/test_rbac.py           # RBAC tests
uv run pytest tests/test_auth.py           # Authentication tests
uv run pytest tests/test_integration.py    # End-to-end tests

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Test specific functionality
uv run pytest -k "test_permission"         # Permission-related tests
```

### **Test Structure**
```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_auth.py             # Authentication flows
├── test_rbac.py             # Permission checking and enforcement
├── test_users.py            # User management with RBAC
├── test_companies.py        # Company isolation testing
├── test_content.py          # Content management with permissions
├── test_devices.py          # Device authentication
└── test_integration.py      # End-to-end RBAC workflows
```

## 📊 **KEY DEVELOPMENT PATTERNS**

### **API Endpoint Pattern**
```python
@router.post("/content")
@require_permission("content_create")
async def create_content(
    content_data: ContentCreate,
    current_user: User = Depends(get_current_user)
):
    # Company isolation for COMPANY_USER
    if current_user.user_type == UserType.COMPANY_USER:
        content_data.company_id = current_user.company_id
    
    return await content_service.create_content(content_data)
```

### **Frontend Component Pattern**
```typescript
export default function UserManagement() {
  const { user, hasPermission } = useAuth();
  
  return (
    <div>
      <PermissionGate permission="user_read">
        <UserList />
      </PermissionGate>
      
      <PermissionGate permission="user_create">
        <CreateUserButton />
      </PermissionGate>
      
      {hasPermission("user_delete") && (
        <DeleteUserActions />
      )}
    </div>
  );
}
```

## 🚨 **CRITICAL SECURITY PATTERNS**

### **Always Enforce Company Isolation**
```python
# ❌ BAD: No company filtering
async def get_all_users():
    return await repo.get_users()

# ✅ GOOD: Company-scoped access
async def get_company_users(current_user: User):
    if current_user.user_type == UserType.SUPER_USER:
        return await repo.get_all_users()
    else:
        return await repo.get_users_by_company(current_user.company_id)
```

### **Permission-First Development**
1. **Define permissions first** before implementing features
2. **Protect all endpoints** with appropriate permission decorators
3. **Gate all UI components** based on user permissions
4. **Test permission boundaries** thoroughly

## 📚 **QUICK REFERENCE**

### **Common UV Commands**
```bash
uv sync                    # Install dependencies from pyproject.toml
uv add fastapi            # Add new dependency
uv add --dev pytest       # Add development dependency
uv remove package-name    # Remove dependency
uv run command            # Run command in virtual environment
uv tree                   # Show dependency tree
```

### **Environment Variables**
```bash
ENVIRONMENT=development
MONGO_URI=mongodb://localhost:27017/openkiosk
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
PRIMARY_AI_PROVIDER=gemini
AZURE_STORAGE_CONNECTION_STRING=...
```

### **Demo Credentials**
```bash
# System Administrator
admin@adara.com / adminpass

# Host Company
host@techcorpsolutions.com / hostpass

# Advertiser Company
director@creativeadsinc.com / advertiserpass
```

## 🚀 **CURRENT IMPLEMENTATION STATUS** ✅ **PRODUCTION READY**

### **Core Systems - Fully Operational**
- ✅ **Authentication & RBAC**: Complete three-tier user system with granular permissions
- ✅ **Multi-Tenant Architecture**: Full company isolation and data separation
- ✅ **Content Management**: AI-powered moderation with approval workflows
- ✅ **Device Management**: Secure API key authentication and monitoring
- ✅ **Frontend Dashboard**: Permission-based UI with dynamic navigation
- ✅ **Flutter Kiosk App**: Complete 5-screen architecture for digital signage
- ✅ **API Infrastructure**: Comprehensive REST API with OpenAPI documentation
- ✅ **Database Layer**: MongoDB with repository pattern and indexing
- ✅ **AI Integration**: Multi-provider framework (Gemini, OpenAI, Claude, Ollama)
- ✅ **Infrastructure**: Docker, Azure deployment, CI/CD pipeline

### **Production Readiness Checklist**
- ✅ **Security**: JWT authentication, RBAC enforcement, input validation
- ✅ **Scalability**: Async operations, connection pooling, caching ready
- ✅ **Monitoring**: Comprehensive logging and error handling
- ✅ **Testing**: Test framework setup with fixtures and mocks
- ✅ **Documentation**: Complete API docs, deployment guides, architecture docs
- ✅ **Deployment**: Azure infrastructure templates, Docker containers
- ✅ **Data Seeding**: Production-ready sample data and configuration

### **Future Development Guidelines**
When adding new features:
1. **Maintain RBAC Patterns**: Always implement permission checks for new endpoints
2. **Follow Multi-Tenant Model**: Ensure company isolation in all data operations
3. **Use Existing Components**: Leverage consolidated components (ContentManager, PageLayout)
4. **Update Documentation**: Keep docs synchronized with implementation changes
5. **Test Thoroughly**: Include RBAC and multi-tenant scenarios in tests

### **Key Development Commands**
```bash
# Backend development
cd backend/content_service
uv sync                          # Install dependencies
uv run uvicorn app.main:app --reload  # Start development server
uv run python seed_data.py       # Seed demo data
uv run pytest                    # Run tests

# Frontend development  
cd frontend
npm install                      # Install dependencies
npm run dev                      # Start development server

# Flutter development
cd flutter/adarah_digital_signage
flutter pub get                  # Get dependencies
flutter run                      # Run on connected device
```

This platform is **production-ready** and can be deployed immediately. All core features are fully implemented and tested. Future development should focus on enhancements, optimizations, and new feature additions while maintaining the established architecture patterns.
