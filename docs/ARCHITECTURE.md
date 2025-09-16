# Adara Digital Signage Platform - System Architecture

**Last Updated:** 2025-09-16  
**Version:** 2.0.0

## 🎯 Executive Summary

The Adara Digital Signage Platform is a comprehensive, enterprise-grade multi-tenant digital signage solution with advanced Role-Based Access Control (RBAC), AI-powered content moderation, and complete device management capabilities.

## 🏗️ System Architecture Overview

### **Core Components**

#### **1. Backend Services (FastAPI/Python)**
- **Technology Stack**: FastAPI 0.116+, Python 3.12+, MongoDB, Azure Services
- **Location**: `backend/content_service/`
- **Purpose**: Enterprise-grade API with RBAC, content management, and AI moderation
- **Package Manager**: UV (10-100x faster than pip)

#### **2. Frontend Dashboard (Next.js/TypeScript)**
- **Technology Stack**: Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Location**: `frontend/`
- **Purpose**: Permission-based web dashboard with dynamic UI controls
- **Features**: Role-based navigation, content management, device monitoring

#### **3. Flutter Kiosk Application**
- **Technology Stack**: Flutter 3.24+, Android TV/tablet support
- **Location**: `flutter/adarah_digital_signage/`
- **Purpose**: Cross-platform digital signage display application
- **Architecture**: Complete 5-screen system with device registration

#### **4. Infrastructure & Deployment**
- **IaC**: Azure Bicep + Terraform
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Azure Container Apps
- **Database**: MongoDB Atlas (UAE region)
- **Storage**: Azure Blob Storage + Azurite (development)

## 🔐 Security & Authentication Architecture

### **Multi-Tier User System**
```typescript
enum UserType {
  SUPER_USER = "SUPER_USER",        // Platform administrators
  COMPANY_USER = "COMPANY_USER",    // Company-specific users
  DEVICE_USER = "DEVICE_USER"       // Device authentication
}
```

### **RBAC Implementation**
- **Permission-Based Access**: Granular permissions (content_create, device_manage, etc.)
- **Company Isolation**: Complete data separation between tenants
- **JWT Authentication**: Secure token-based auth with refresh tokens
- **Device Authentication**: API key-based secure device access

### **Security Features**
- **Azure Key Vault**: Secrets management and encryption keys
- **Field-Level Encryption**: PII data protection
- **Rate Limiting**: DDoS protection and abuse prevention
- **Security Headers**: OWASP-compliant HTTP headers
- **Audit Logging**: Comprehensive activity and security event tracking

## 📊 Data Architecture

### **Database Design**
- **Primary Database**: MongoDB with advanced indexing and aggregation
- **Schema Management**: Automatic schema validation and migration
- **Repository Pattern**: Clean data access layer with error handling
- **Connection Pooling**: Optimized database connections

### **Storage Architecture**
- **Media Files**: Azure Blob Storage with CDN integration
- **Development**: Azurite local Azure Storage emulator
- **Backup Strategy**: Automated backups with point-in-time recovery

### **Data Flow**
```
Content Upload → AI Moderation → Approval Workflow → Distribution → Device Display
```

## 🤖 AI & Content Moderation

### **Multi-Provider AI Framework**
- **Providers**: Gemini, OpenAI GPT-4, Claude, Ollama (local)
- **Automatic Failover**: Seamless switching between providers
- **Content Safety**: Azure AI Content Safety integration
- **Moderation Workflow**: Upload → Pre-scan → AI scoring → Manual review (if needed)

### **Content Processing Pipeline**
1. **Virus Scanning**: Pre-upload security check
2. **AI Moderation**: Multi-provider content analysis
3. **Confidence Scoring**: Automated approval/rejection
4. **Manual Review**: Human oversight for borderline content
5. **Distribution**: Secure content delivery to authorized devices

## 📱 Device Management Architecture

### **Flutter Application Structure**
```
5-Screen Architecture:
├── Setup/Registration Screen    # Device onboarding
├── Main Display Screen         # Content playback
├── Interactive Screen          # User interaction
├── Status/Diagnostics Screen   # Health monitoring
└── Error/Offline Screen        # Fallback handling
```

### **Device Features**
- **QR Code Registration**: Secure device association with companies
- **Offline Capability**: Cached content for network interruptions
- **Real-time Sync**: 5-minute content synchronization intervals
- **Heartbeat Monitoring**: Device health and status reporting
- **Remote Management**: Over-the-air updates and configuration

### **Digital Twin System**
- **Virtual Representation**: Cloud-based device mirroring
- **Predictive Maintenance**: AI-powered failure prediction
- **Remote Control**: Secure device management and updates
- **Performance Analytics**: Device usage and performance metrics

## 🔄 Event-Driven Architecture

### **Event Processing**
- **Azure Service Bus**: Reliable message queuing
- **Event Manager**: Centralized event processing and routing
- **WebSocket Support**: Real-time communication with devices
- **Background Processing**: Asynchronous task execution

### **Key Events**
- **Content Events**: Upload, approval, distribution notifications
- **Device Events**: Registration, heartbeat, status updates
- **Security Events**: Authentication, authorization, audit logs
- **Analytics Events**: Usage tracking and performance metrics

## 🚀 API Architecture

### **RESTful API Design**
- **Base URL**: `/api/v1/`
- **Authentication**: JWT Bearer tokens
- **Response Format**: JSON with consistent error handling
- **Rate Limiting**: Configurable request limits per endpoint

### **API Endpoints Structure**
```
├── /auth/           # Authentication & authorization
├── /users/          # User management
├── /companies/      # Multi-tenant company management
├── /content/        # Content CRUD and management
├── /devices/        # Device registration and monitoring
├── /analytics/      # Reporting and analytics
├── /moderation/     # Content moderation workflow
└── /admin/          # Platform administration
```

### **API Features**
- **OpenAPI/Swagger**: Automatic API documentation
- **Request Validation**: Pydantic-based data validation
- **Error Handling**: Consistent error responses
- **Pagination**: Efficient large dataset handling
- **Filtering**: Advanced query capabilities

## 🎨 Frontend Architecture

### **Component Structure**
```
frontend/
├── app/                    # Next.js app router
│   ├── dashboard/         # Main dashboard pages
│   ├── admin/            # Admin-specific pages
│   ├── advertiser/       # Advertiser portal
│   └── host/             # Host company pages
├── components/            # Reusable UI components
│   ├── ui/               # shadcn/ui components
│   ├── PermissionGate.tsx # RBAC UI component
│   └── shared/           # Shared components
└── lib/                  # Utilities and configurations
```

### **State Management**
- **Zustand**: Lightweight global state management
- **React Context**: Company and user context providers
- **React Query**: Server state management and caching
- **Local Storage**: Persistent user preferences

### **UI/UX Features**
- **Responsive Design**: Mobile-first approach
- **Dark/Light Mode**: Theme switching capability
- **Accessibility**: WCAG 2.1 AA compliance
- **Internationalization**: Multi-language support preparation

## 🏭 Infrastructure Architecture

### **Development Environment**
- **Local Services**: Docker Compose with MongoDB and Azurite
- **Hot Reload**: FastAPI and Next.js development servers
- **Testing**: Comprehensive test suites with pytest and Jest
- **Code Quality**: Black, Ruff, ESLint, Prettier

### **Production Deployment**
- **Azure Container Apps**: Serverless container orchestration
- **Azure Front Door**: Global CDN and load balancing
- **Azure Key Vault**: Secrets and certificate management
- **Azure Monitor**: Application performance monitoring
- **Azure Backup**: Automated backup and disaster recovery

### **Scalability Features**
- **Horizontal Scaling**: Auto-scaling based on demand
- **Database Sharding**: Multi-region data distribution
- **Caching**: Redis for session and data caching
- **CDN**: Global content delivery optimization

## 📈 Analytics & Monitoring

### **Analytics Architecture**
- **Real-time Processing**: Event-driven analytics collection
- **Dashboard**: Comprehensive reporting and visualization
- **Predictive Analytics**: AI-powered insights and recommendations
- **Custom Reports**: Flexible reporting framework

### **Monitoring & Observability**
- **Application Insights**: Azure-native monitoring
- **Log Aggregation**: Centralized logging with Azure Log Analytics
- **Performance Metrics**: Response times, error rates, throughput
- **Alerting**: Proactive issue detection and notification

## 🔧 Development Workflow

### **Technology Stack**
- **Backend**: Python 3.12+ with FastAPI, UV package management
- **Frontend**: TypeScript with Next.js 15 and React 19
- **Mobile**: Flutter with Android TV support
- **Database**: MongoDB with Motor async driver
- **Infrastructure**: Azure Bicep and Terraform
- **CI/CD**: GitHub Actions with Azure deployment

### **Code Quality Standards**
- **Testing**: pytest for backend, Jest for frontend
- **Linting**: Ruff (Python), ESLint (TypeScript)
- **Formatting**: Black (Python), Prettier (TypeScript)
- **Type Safety**: Full TypeScript adoption, Python type hints

### **Development Commands**
```bash
# Backend development
cd backend/content_service
uv sync                    # Install dependencies
uv run uvicorn app.main:app --reload  # Start server

# Frontend development
cd frontend
npm run dev               # Start development server

# Flutter development
cd flutter/adarah_digital_signage
flutter run               # Run on connected device
```

## 🚀 Deployment Architecture

### **CI/CD Pipeline**
- **GitHub Actions**: Automated testing and deployment
- **Multi-Environment**: Development, staging, production
- **Blue-Green Deployment**: Zero-downtime updates
- **Rollback Capability**: Quick recovery from failed deployments

### **Environment Configuration**
- **Secrets Management**: Azure Key Vault integration
- **Environment Variables**: Secure configuration management
- **Feature Flags**: Runtime feature toggling
- **Configuration Validation**: Startup-time config verification

## 📚 Documentation Architecture

### **Documentation Structure**
```
docs/
├── ARCHITECTURE.md          # This file
├── IMPLEMENTATION_CHECKLIST_MASTER.md
├── ENHANCED_RBAC_SYSTEM.md
├── api.md                   # API documentation
├── FLUTTER_APP_SPEC.md      # Mobile app specs
├── AI_CONTENT_MODERATION_FRAMEWORK.md
├── DEPLOYMENT_GUIDE.md      # Production deployment
└── security/               # Security guidelines
```

### **Documentation Standards**
- **Markdown Format**: Consistent formatting and structure
- **Cross-References**: Linked related documentation
- **Code Examples**: Practical implementation examples
- **Regular Updates**: Documentation kept current with code

---

**Architecture Version:** 2.0.0  
**Last Reviewed:** 2025-09-16  
**Next Review:** Monthly  
**Owner:** Enterprise Architecture Team