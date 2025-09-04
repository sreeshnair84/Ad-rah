# GitHub Copilot System Instructions for Adara Digital Signage Platform

## 🎯 **PROJECT OVERVIEW**

You are working on **Adara from Hebron™**, a comprehensive **multi-tenant digital signage and content management platform** designed for the UAE/Dubai market. This enterprise-grade system connects **HOST companies** (screen/location owners) with **ADVERTISER companies** (content creators) through a sophisticated content distribution and revenue-sharing platform.

### **Business Model**
- **HOST Companies**: Own physical screens/kiosks (restaurants, malls, hotels, etc.)
- **ADVERTISER Companies**: Create and pay for content placement on host screens
- **Platform**: Facilitates secure content distribution, AI-powered moderation, and automated revenue sharing

### **Core Value Proposition**
- Multi-tenant SaaS platform with company isolation
- AI-powered content moderation with human oversight
- Real-time content distribution to thousands of devices
- Advanced analytics and proof-of-play tracking
- Enterprise-grade security and compliance

## 🏗️ **TECHNOLOGY STACK & ARCHITECTURE**

### **Frontend - Next.js Web Dashboard**
```typescript
// Technology: Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui
// Location: frontend/
// Purpose: Web-based management dashboard for all user roles

Key Libraries:
- @radix-ui/* - UI components (dialog, dropdown, etc.)
- @hookform/resolvers + zod - Form validation
- lucide-react - Icons
- recharts - Analytics charts
- next-themes - Dark/light mode
```

### **Backend - FastAPI Microservice**
```python
# Technology: FastAPI + Python 3.12 + MongoDB + Azure Blob Storage
# Location: backend/content_service/
# Purpose: Content management, authentication, and business logic

Key Dependencies:
- FastAPI - REST API framework
- Motor - Async MongoDB driver  
- Azure SDK - Blob storage integration
- JWT - Authentication tokens
- Bcrypt - Password hashing
- Pydantic - Data validation
```

### **Mobile - Flutter Digital Signage App**
```dart
// Technology: Flutter 3.24+ + Dart + Android SDK
// Location: flutter/adarah_digital_signage/
// Purpose: Kiosk/screen application for content display

Architecture: Five-screen system
1. Setup & Registration (QR code scanning)
2. Main Display (full-screen content)
3. Interactive (NFC/Bluetooth engagement)
4. Status & Diagnostics (monitoring)
5. Error & Offline Mode (graceful degradation)
```

### **Infrastructure - Azure Cloud (UAE Central)**
```bicep
# Technology: Azure Bicep + Docker + Kubernetes
# Location: infra/main.bicep
# Purpose: Production cloud infrastructure

Resources:
- Azure Blob Storage (media files)
- Azure Service Bus (event processing)
- Azure Key Vault (secrets management)
- Azure Container Registry (Docker images)
- MongoDB Atlas (database)
- Azure AI Content Safety (moderation)
```

## 🔐 **AUTHENTICATION & AUTHORIZATION SYSTEM**

### **Multi-Tenant Security Model**
```typescript
// Every user belongs to one or more companies with specific roles
interface User {
  id: string;
  email: string;
  roles: UserRole[];  // Can have multiple roles across companies
}

interface UserRole {
  user_id: string;
  company_id: string;     // Company context
  role_id: string;        // References Role table
  is_default: boolean;    // Default role for login
}

interface Company {
  id: string;
  organization_code: string;  // ORG-XXXXXXX format for device registration
  type: "HOST" | "ADVERTISER";
  registration_key: string;   // 16-character secure key for devices
}
```

### **Role-Based Access Control (RBAC)**
```typescript
enum RoleGroup {
  ADMIN = "ADMIN",           // Platform administrators - global access
  HOST = "HOST",             // Screen/location managers - company-scoped  
  ADVERTISER = "ADVERTISER"  // Content creators - campaign-scoped
}

enum Permission {
  VIEW = "view",      // Read access
  EDIT = "edit",      // Modify access
  DELETE = "delete",  // Remove access
  ACCESS = "access"   // Feature access
}

enum Screen {
  DASHBOARD = "dashboard",     // Main dashboard
  USERS = "users",            // User management
  COMPANIES = "companies",    // Company management
  CONTENT = "content",        // Content upload/management
  MODERATION = "moderation",  // Content approval
  ANALYTICS = "analytics",    // Performance tracking
  SETTINGS = "settings",      // System configuration
  BILLING = "billing"         // Payment management
}
```

### **Authentication Flow**
```typescript
// Three-step authentication process
1. Email/Password Validation → JWT token generation
2. Role Selection (if user has multiple company roles)
3. Company Context Establishment → Dashboard redirect

// JWT Token Management
- Access Token: 30 minutes expiration
- Refresh Token: 7 days expiration  
- Automatic token refresh on API calls
- Secure storage in httpOnly cookies
```

## 📊 **DATABASE DESIGN & DATA MODELS**

### **Primary Database: MongoDB (Production) + In-Memory (Development)**
```javascript
// Companies Collection - Multi-tenant isolation
{
  _id: ObjectId,
  name: String,
  type: "HOST" | "ADVERTISER", 
  organization_code: String,     // ORG-XXXXXXX format
  registration_key: String,      // 16-character secure key
  address: String,
  city: String,
  country: String,
  status: "active" | "inactive",
  created_at: Date,
  updated_at: Date
}

// Users Collection - Authentication
{
  _id: ObjectId,
  name: String,
  email: String,               // Unique login identifier
  phone: String,
  hashed_password: String,     // Bcrypt hashed
  status: "active" | "inactive",
  email_verified: Boolean,
  last_login: Date,
  created_at: Date,
  updated_at: Date
}

// UserRoles Collection - Company-scoped permissions
{
  _id: ObjectId,
  user_id: String,            // References Users
  company_id: String,         // References Companies
  role_id: String,            // References Roles
  is_default: Boolean,        // Default role for login
  status: "active" | "inactive",
  created_at: Date,
  updated_at: Date
}

// ContentMeta Collection - Content management
{
  _id: ObjectId,
  owner_id: String,           // Content creator
  filename: String,
  content_type: String,       // MIME type
  size: Number,
  status: "quarantine" | "pending" | "approved" | "rejected",
  title: String,
  description: String,
  categories: [String],       // Content categorization
  tags: [String],            // Content tags
  start_time: Date,          // Scheduling
  end_time: Date,
  uploaded_at: Date,
  updated_at: Date
}

// DigitalScreens Collection - Device management
{
  _id: ObjectId,
  name: String,
  company_id: String,         // Owner company
  location: String,           // Physical location
  resolution_width: Number,   // Screen resolution
  resolution_height: Number,
  orientation: "landscape" | "portrait",
  status: "active" | "inactive" | "maintenance" | "offline",
  registration_key: String,   // Device registration
  ip_address: String,
  mac_address: String,
  last_seen: Date,
  created_at: Date,
  updated_at: Date
}
```

### **Repository Pattern Implementation**
```python
# backend/content_service/app/repo.py
class Repository:
    """Dual storage: MongoDB (prod) + In-memory (dev)"""
    
    async def create_company(self, company: CompanyCreate) -> Company
    async def list_companies(self) -> List[Company]
    async def get_company_by_organization_code(self, code: str) -> Company
    
    async def create_user(self, user: UserCreate) -> User
    async def assign_user_role(self, user_id: str, company_id: str, role_id: str)
    async def check_permission(self, user_id: str, company_id: str, screen: Screen, permission: Permission) -> bool
    
    async def create_content_meta(self, content: ContentMeta) -> ContentMeta
    async def list_content_by_owner(self, owner_id: str) -> List[ContentMeta]
    async def update_content_status(self, content_id: str, status: str)
```

## 🚀 **API ARCHITECTURE & ENDPOINTS**

### **FastAPI Application Structure**
```python
# backend/content_service/app/main.py - Application entry point
# backend/content_service/app/api/ - All API routes

✅ IMPLEMENTED ENDPOINTS:

# Authentication & Authorization
POST   /api/auth/login                    # User authentication
POST   /api/auth/logout                   # Session termination
POST   /api/auth/refresh                  # Token refresh
GET    /api/auth/me                       # Current user profile

# User & Role Management
GET    /api/users                         # List users (company-scoped)
POST   /api/users                         # Create user
PUT    /api/users/{id}                    # Update user
DELETE /api/users/{id}                    # Delete user
POST   /api/users/{id}/roles              # Assign role

GET    /api/roles                         # List roles (company-scoped)
POST   /api/roles                         # Create role
PUT    /api/roles/{id}                    # Update role
GET    /api/roles/{id}/permissions        # Get permissions
POST   /api/roles/{id}/permissions        # Set permissions

# Company Management
GET    /api/companies                     # List companies
POST   /api/companies                     # Create company  
PUT    /api/companies/{id}                # Update company
DELETE /api/companies/{id}                # Delete company

# Content Management
POST   /api/uploads/media                 # File upload (Azure Blob)
GET    /api/content                       # List content (owner-scoped)
POST   /api/content                       # Create content metadata
PUT    /api/content/{id}                  # Update content
DELETE /api/content/{id}                  # Delete content

# Screen & Device Management
GET    /api/screens                       # List screens (company-scoped)
POST   /api/screens                       # Create screen
PUT    /api/screens/{id}                  # Update screen
GET    /api/screens/{id}/overlays         # Get content overlays
POST   /api/screens/{id}/overlays         # Create overlay
PUT    /api/screens/{id}/overlays/{oid}   # Update overlay positioning

# Device Registration & Authentication
POST   /api/device/register               # Device registration with org code
GET    /api/device/status                 # Device health status
POST   /api/device/heartbeat              # Device heartbeat

# Digital Twin & Real-time Monitoring  
GET    /api/digital-twins                 # List virtual devices
POST   /api/digital-twins                 # Create digital twin
PUT    /api/digital-twins/{id}            # Update twin configuration
WebSocket /api/ws/device/{id}             # Real-time device control

# Analytics & Events
POST   /api/events                        # Event ingestion (proof-of-play)
GET    /api/analytics/performance         # Performance metrics
GET    /api/analytics/content             # Content analytics
GET    /api/analytics/devices             # Device analytics

# Company Registration Workflow
GET    /api/company-applications          # List applications
POST   /api/company-applications          # Submit application
PUT    /api/company-applications/{id}     # Review application (approve/reject)

# Content Moderation
GET    /api/moderation/queue              # Content review queue
POST   /api/moderation/{id}/decision      # Approve/reject content
GET    /api/moderation/history            # Moderation history

🔄 PARTIALLY IMPLEMENTED:
- Content Scheduling APIs (backend logic exists, frontend integration needed)
- Advanced Analytics APIs (basic metrics available, BI features limited)
- Bulk Operations APIs (individual CRUD complete, batch operations limited)

❌ NOT YET IMPLEMENTED:
- Payment & Billing APIs
- Revenue Sharing APIs
- Advanced Reporting APIs
- Yodeck/Xibo Integration APIs
```

## 🎨 **FRONTEND ARCHITECTURE & PAGES**

### **Next.js Application Structure**
```typescript
// frontend/src/app/ - App Router (Next.js 15)

✅ FULLY IMPLEMENTED PAGES:

/login                                    # Multi-step authentication
  - Step 1: Email/password validation
  - Step 2: Role selection (if multiple)
  - Step 3: Success animation + redirect

/dashboard                                # Main dashboard home
  - Overview cards with key metrics
  - Recent activity feed
  - Quick actions menu

/dashboard/users                          # User management
  - User CRUD operations
  - Role assignment interface
  - Company context switching
  - Bulk user operations

/dashboard/roles                          # Role & permission management
  - Role CRUD operations
  - Permission matrix editor (visual grid)
  - Role hierarchy management
  - Template-based role creation

/dashboard/registration                   # Company application review
  - Application dashboard with statistics
  - Document review interface
  - Approval/rejection workflow
  - Applicant communication

/dashboard/master-data                    # Company management
  - Company CRUD operations
  - Organization code generation
  - Registration key management
  - Company type configuration

/dashboard/my-ads                         # Content upload & management
  - File upload with drag-and-drop
  - Content metadata editor
  - Status tracking (quarantine → pending → approved)
  - Content categorization and tagging

/dashboard/kiosks                         # Screen/device management
  - Screen CRUD operations
  - Device registration monitoring
  - Screen status and health tracking
  - Resolution and orientation settings

/dashboard/content-overlay                # Content positioning & layout
  - Drag-and-drop layout designer
  - Multi-layer content management
  - Position and size controls
  - Preview and testing interface

/dashboard/digital-twin                   # Virtual device testing
  - Digital twin CRUD operations
  - Live device mirroring
  - Test content deployment
  - Performance simulation

/dashboard/performance                    # Analytics & reporting
  - Real-time device telemetry
  - Content performance metrics
  - Device health monitoring
  - Custom dashboard creation

🔄 PARTIALLY IMPLEMENTED:

/dashboard/moderation                     # Content approval workflow
  - Basic approval/rejection interface
  - Missing: Bulk operations, advanced filters
  - Missing: AI confidence visualization

/dashboard/settings                       # User preferences & configuration
  - Basic user profile management
  - Missing: Advanced customization options
  - Missing: Role-based UI configuration

❌ NOT YET IMPLEMENTED:

/dashboard/billing                        # Payment & revenue management
/dashboard/reports                        # Advanced business intelligence
/dashboard/integrations                   # Third-party API management
/dashboard/compliance                     # Regulatory compliance tools
```

### **Component Architecture**
```typescript
// frontend/src/components/ - Reusable UI components

✅ IMPLEMENTED COMPONENTS:

ui/ - shadcn/ui component library
  - Button, Input, Dialog, Alert, Progress, etc.
  - Custom themed components
  - Dark/light mode support

DeviceMonitor.tsx - Real-time device monitoring
  - WebSocket connection management
  - Live telemetry display
  - Device control interface

Navigation/ - Dashboard navigation
  - Sidebar with role-based menu items
  - Breadcrumb navigation
  - User profile dropdown

Forms/ - Form components
  - User creation/editing forms
  - Role assignment forms
  - Content upload forms

Charts/ - Analytics visualization
  - Performance charts with Recharts
  - Real-time data display
  - Custom dashboard widgets
```

## 🤖 **AI CONTENT MODERATION FRAMEWORK**

### **Multi-Provider Architecture**
```python
# backend/content_service/ai_manager.py - AI provider management

class AIManager:
    """Multi-provider AI with automatic failover"""
    
    providers = {
        "gemini": GeminiProvider(),      # Google Gemini (primary)
        "openai": OpenAIProvider(),      # OpenAI GPT (secondary)
        "claude": ClaudeProvider(),      # Anthropic Claude (tertiary)
        "ollama": OllamaProvider()       # Local AI (free fallback)
    }
    
    async def moderate_content(self, content_data: bytes) -> ModerationResult:
        # Automatic provider failover
        # Cost optimization (prefer cheaper providers)
        # Confidence scoring and human review integration
        
    async def switch_provider(self, provider_name: str):
        # Runtime provider switching
        # Configuration persistence
        # Performance monitoring
```

### **Moderation Workflow**
```
Content Upload → Virus Scan → AI Analysis → Confidence Score
                                              │
                                    ┌─────────┼─────────┐
                                    │         │         │
                               >95% Auto    70-95%    <70%
                              Approve    Human Review  Auto Reject
                                    │         │         │
                                    └─────────┼─────────┘
                                              │
                                         Approve/Reject
                                              │
                                         Content Live
```

### **Provider Management Commands**
```bash
# Switch AI providers dynamically
python ai_manager.py switch gemini      # Use Google Gemini
python ai_manager.py switch ollama      # Use local free AI
python ai_manager.py switch openai      # Use OpenAI
python ai_manager.py status             # Check all providers
```

## 📱 **FLUTTER DIGITAL SIGNAGE APPLICATION**

### **Five-Screen Architecture**
```dart
// flutter/adarah_digital_signage/lib/screens/

1. SetupRegistrationScreen
   - QR code scanning with real-time feedback
   - Manual device registration form
   - Organization code + registration key validation
   - Secure credential storage
   - Network connectivity monitoring

2. MainDisplayScreen  
   - Full-screen content rendering
   - Multi-zone layout support (overlays)
   - Hardware-accelerated video playback
   - Dynamic content scheduling
   - Smooth transitions and animations

3. InteractiveScreen
   - NFC proximity detection
   - Bluetooth LE beacon scanning  
   - Gamified user engagement
   - Touch-optimized controls
   - Privacy-compliant data collection

4. StatusDiagnosticsScreen
   - Real-time system monitoring
   - Network diagnostics and speed tests
   - Content synchronization status
   - Administrative controls
   - Performance metrics and alerts

5. ErrorOfflineScreen
   - Offline content playback from cache
   - Network reconnection monitoring
   - Error classification and reporting
   - Recovery action suggestions
   - Emergency contact information
```

### **Background Services**
```dart
// Background processing for always-on operation

ContentSyncService
  - 5-minute interval synchronization
  - Differential content updates
  - Bandwidth-aware downloading
  - Conflict resolution

AnalyticsService  
  - Privacy-compliant event collection
  - Batch upload optimization
  - Offline event queuing
  - Real-time performance tracking

DigitalTwinService
  - Device state mirroring
  - Remote control capabilities
  - Test content deployment
  - Performance simulation

NetworkMonitoringService
  - Connectivity awareness
  - Quality monitoring
  - Automatic recovery
  - Bandwidth optimization
```

## 🔄 **DEVELOPMENT WORKFLOW & COMMANDS**

### **Environment Setup**
```bash
# Backend Development (FastAPI + Python)
cd backend/content_service
docker-compose up -d              # Start MongoDB + Azurite
python -m venv .venv              # Create virtual environment
.\.venv\Scripts\Activate.ps1      # Activate (Windows)
pip install -r requirements.txt   # Install dependencies
python seed_data.py               # Create demo data
uvicorn app.main:app --reload     # Start development server

# Frontend Development (Next.js + React)
cd frontend
npm install                       # Install dependencies
npm run dev                       # Start development server

# Flutter Development (Digital Signage App)
cd flutter/adarah_digital_signage
flutter pub get                   # Install dependencies
flutter run -d chrome             # Run in browser for testing
flutter build apk --release       # Build Android APK
```

### **Demo Data & Testing**
```bash
# Initialize demo environment
python seed_data.py

# Demo Credentials:
admin@adara.com / adminpass           # System Administrator
host@techcorpsolutions.com / hostpass     # Host Manager
operator@techcorpsolutions.com / hostpass # Screen Operator
director@creativeadsinc.com / advertiserpass # Advertiser Director

# Demo Companies:
TechCorp Solutions (HOST) - ORG-TC12345
Creative Ads Inc (ADVERTISER) - ORG-CA67890
Digital Displays LLC (HOST) - ORG-DD11111
AdVantage Media (ADVERTISER) - ORG-AV22222
```

### **Testing Commands**
```bash
# Backend Tests
cd backend/content_service
pytest tests/ -v                 # Run all tests
pytest tests/test_auth.py -k "test_login" # Specific tests
pytest tests/ --cov=app --cov-report=html # Coverage report

# Frontend Tests (when configured)
cd frontend
npm test                         # Run Jest tests
npm run type-check              # TypeScript validation
npm run lint                    # ESLint checks

# Flutter Tests
cd flutter/adarah_digital_signage
flutter test                    # Unit tests
flutter test integration_test/  # Integration tests
flutter analyze                 # Static analysis
```

## 🚨 **COMMON DEVELOPMENT PATTERNS & BEST PRACTICES**

### **Authentication & Authorization Patterns**
```typescript
// Frontend: Always check authentication state
const { user, isInitialized } = useAuth();

if (!isInitialized) return <LoadingSpinner />;
if (!user) return <RedirectToLogin />;

// Backend: Protect endpoints with dependencies
from app.auth import get_current_user, check_permission

@router.get("/api/protected-endpoint")
async def protected_endpoint(
    current_user: User = Depends(get_current_user),
    authorized: bool = Depends(check_permission("content", "edit"))
):
    # Your endpoint logic here
```

### **Company Context Management**
```typescript
// Frontend: Always scope operations to selected company
const { selectedCompany } = useCompanyContext();

// Backend: Filter data by company ownership
async def list_content(company_id: str = Depends(get_current_company)):
    return await repo.list_content_by_company(company_id)
```

### **Error Handling Patterns**
```typescript
// Frontend: Consistent error display
try {
  await api.createUser(userData);
  toast.success("User created successfully");
} catch (error) {
  toast.error(error.message || "An error occurred");
}

// Backend: Structured error responses
from fastapi import HTTPException, status

if not user:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )
```

### **Real-time Data Patterns**
```typescript
// WebSocket connection management
const { socket, isConnected } = useWebSocket(`/api/ws/device/${deviceId}`);

useEffect(() => {
  if (socket) {
    socket.on('telemetry', handleTelemetryUpdate);
    socket.on('status_change', handleStatusChange);
  }
}, [socket]);
```

## 🎯 **KEY DEVELOPMENT PRIORITIES**

### **Current Implementation Status (60% Complete)**
✅ **Completed**: Authentication, RBAC, User Management, Content Upload, Screen Management
🔄 **In Progress**: AI Moderation Integration, Content Scheduling Interface
❌ **Pending**: Flutter App, Payment System, Advanced Analytics

### **Immediate Next Steps (Weeks 1-4)**
1. **AI Moderation Integration**: Connect framework with approval workflow
2. **Content Scheduling Interface**: Calendar-based scheduling UI
3. **Flutter App Foundation**: Initialize project and core screens
4. **Real-time Features Enhancement**: WebSocket optimization

### **Medium-term Goals (Weeks 5-12)**
1. **Flutter App Completion**: Five-screen architecture implementation
2. **Advanced Analytics**: Business intelligence dashboards
3. **Payment Integration**: Billing and revenue sharing
4. **Performance Optimization**: Caching and database optimization

### **Long-term Objectives (Weeks 13-24)**
1. **Enterprise Features**: White-labeling, advanced security
2. **API Integrations**: Yodeck, Xibo, and third-party systems
3. **Mobile Optimization**: Progressive Web App features
4. **International Expansion**: Multi-language and currency support

## 🔧 **TROUBLESHOOTING & DEBUGGING**

### **Common Issues & Solutions**
```bash
# MongoDB Connection Issues
# Check if MongoDB is running
docker ps | grep mongo
# Restart MongoDB container
docker-compose restart mongodb

# Authentication Redirect Loops
# Clear browser storage and check token expiration
localStorage.clear(); sessionStorage.clear();

# Flutter Build Issues
# Clean and rebuild
flutter clean && flutter pub get && flutter build apk

# API Permission Errors
# Verify user roles and company context
GET /api/auth/me
# Check role permissions
GET /api/roles/{role_id}/permissions
```

### **Development Environment Variables**
```bash
# Backend (.env)
MONGO_URI=mongodb://localhost:27017/content_service
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend (.env.local)  
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📚 **DOCUMENTATION REFERENCES**

- **Complete Architecture**: `docs/CLAUDE.md` - Comprehensive system understanding
- **API Documentation**: `docs/api.md` - Endpoint specifications
- **Flutter Specs**: `docs/FLUTTER_APP_SPEC.md` - Mobile app requirements
- **Data Models**: `docs/DATA_MODEL.md` - Database schema
- **Security**: `docs/security.md` - Security implementation
- **AI Framework**: `docs/AI_CONTENT_MODERATION_FRAMEWORK.md` - AI moderation details

Remember: This is a **multi-tenant, enterprise-grade platform** requiring careful attention to **company isolation**, **role-based permissions**, and **data security** in all implementations.  
