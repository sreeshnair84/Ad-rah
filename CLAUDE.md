# Adārah from Hebron™ - Digital Kiosk Content Management Platform

## Overview
A Next.js 15 + React 19 frontend with FastAPI backend for managing digital advertising content on kiosks across UAE. Supports multi-tenant operations for Host Companies (venue owners) and Advertiser Companies with AI-powered content moderation.

## Architecture Summary

### Frontend Stack
- **Framework**: Next.js 15 with React 19
- **Language**: TypeScript 
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: React hooks + localStorage for auth tokens
- **API Communication**: Fetch API with proxy to backend

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: MongoDB Atlas (UAE region) for metadata
- **Storage**: Azure Blob Storage for media files
- **Authentication**: JWT with hardcoded secret (development mode)
- **AI Moderation**: Simulation-based (development), planned Azure AI Foundry

### Infrastructure
- **Cloud**: Microsoft Azure UAE Central
- **Containers**: Docker with planned Kubernetes (AKS)
- **Message Queue**: Azure Service Bus (planned)
- **Monitoring**: Basic logging (needs enhancement)

## Current Critical Issues

### 1. Authentication & Security
- **CRITICAL**: Hardcoded JWT secret key in code
- **CRITICAL**: PII data handling not properly secured
- **ISSUE**: Login redirect loop due to missing authentication state persistence
- **ISSUE**: No refresh token mechanism
- **ISSUE**: Weak password hashing fallback (SHA256 instead of bcrypt)

### 2. Data Architecture Issues
- **ISSUE**: Mixed storage backends (in-memory for development, MongoDB for production)
- **ISSUE**: Inconsistent data serialization (ObjectId handling)
- **ISSUE**: No data validation at API boundaries
- **ISSUE**: Missing audit trails for PII access

### 3. Enterprise Standards Gaps
- **ISSUE**: No centralized configuration management
- **ISSUE**: Missing health checks and observability
- **ISSUE**: No API versioning strategy
- **ISSUE**: Inconsistent error handling patterns

## Enterprise Standardization Plan

### Phase 1: Security & Compliance (IMMEDIATE)
1. **Secure Secret Management**
   - Move all secrets to Azure Key Vault
   - Implement managed identities for service authentication
   - Rotate JWT secrets quarterly

2. **Authentication Hardening**
   - Implement proper refresh token flow
   - Add device-bound tokens for kiosks
   - Enable Entra ID OIDC integration

3. **PII Protection**
   - Implement data classification and handling policies
   - Add audit logging for all PII access
   - Ensure GDPR/UAE data protection compliance
   - Encrypt PII data at rest with separate keys

### Phase 2: Data Architecture (WEEK 2-3)
1. **Database Standardization**
   - Consolidate on MongoDB Atlas for all environments
   - Implement proper connection pooling
   - Add database migration framework

2. **API Standards**
   - Implement OpenAPI 3.0 specifications
   - Add API versioning (v1, v2, etc.)
   - Standardize error response formats
   - Add request/response validation middleware

3. **Data Governance**
   - Implement audit trails for all operations
   - Add data retention policies
   - Create backup and recovery procedures

### Phase 3: Observability & Monitoring (WEEK 3-4)
1. **Logging Standards**
   - Implement structured logging (JSON format)
   - Add correlation IDs across services
   - Set up Azure Monitor integration

2. **Health & Metrics**
   - Add comprehensive health checks
   - Implement application metrics
   - Set up alerting for critical issues

### Phase 4: Infrastructure & Deployment (WEEK 4-6)
1. **Containerization**
   - Standardize Docker configurations
   - Implement multi-stage builds
   - Add container security scanning

2. **CI/CD Pipeline**
   - Implement automated testing
   - Add security scanning in pipeline
   - Set up automated deployments

## Immediate Fixes Required

### Login Redirect Issue
**Root Cause**: Authentication state not properly managed between frontend and backend
**Impact**: Users cannot access dashboard after login
**Priority**: CRITICAL

**Solution Components**:
1. Fix token persistence in localStorage
2. Add proper authentication state management
3. Implement token refresh mechanism
4. Add authentication guard for protected routes

### PII Handling Issues
**Root Cause**: No data classification or protection mechanisms
**Impact**: Potential compliance violations
**Priority**: HIGH

**Solution Components**:
1. Identify and classify PII fields
2. Implement encryption for PII at rest
3. Add audit logging for PII access
4. Create data retention policies

## Development Guidelines

### Code Standards
- Use TypeScript strict mode
- Implement proper error boundaries in React
- Follow REST API conventions
- Add comprehensive input validation
- Use environment variables for all configuration

### Security Practices
- Never commit secrets to repository
- Validate all user inputs
- Implement proper authorization checks
- Use HTTPS only in production
- Regular security scanning

### Testing Requirements
- Unit tests for all business logic
- Integration tests for API endpoints
- End-to-end tests for critical user flows
- Security testing for authentication flows

## Command Reference

### Frontend Development
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production  
npm run lint         # Run ESLint
npm test            # Run tests
```

### Backend Development
```bash
cd backend/content_service
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest              # Run tests
```

### Default Test Accounts
- **Admin**: admin@openkiosk.com / adminpass
- **Host**: host@openkiosk.com / hostpass  
- **Advertiser**: advertiser@openkiosk.com / advertiserpass

## Environment Configuration

### Required Environment Variables
```bash
# Backend
MONGO_URI=mongodb://localhost:27017/openkiosk
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection
AZURE_CONTAINER_NAME=openkiosk-media
SECRET_KEY=your_secure_secret_key
AZURE_AI_ENDPOINT=your_ai_endpoint
AZURE_AI_KEY=your_ai_key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Next Steps
1. ✅ Architecture analysis completed
2. ✅ Critical issues identified  
3. 🔄 Fix authentication/login issues
4. 📝 Update security documentation
5. 🔐 Implement PII protection measures
6. 📊 Add monitoring and observability
7. 🚀 Prepare for production deployment

## New API Endpoints

### Categories & Tags Management
```bash
# Categories
GET    /api/categories/              # List all categories
POST   /api/categories/              # Create category (Admin)
GET    /api/categories/{id}          # Get specific category
PUT    /api/categories/{id}          # Update category (Admin)
DELETE /api/categories/{id}          # Delete category (Admin)

# Tags
GET    /api/categories/tags         # List all tags
POST   /api/categories/tags         # Create tag (Admin/Advertiser)
GET    /api/categories/tags/{id}    # Get specific tag
PUT    /api/categories/tags/{id}    # Update tag (Admin/Advertiser)
DELETE /api/categories/tags/{id}    # Delete tag (Admin/Advertiser)

# Host Preferences
POST   /api/categories/preferences                    # Create host preferences
GET    /api/categories/preferences/{company_id}      # Get host preferences
PUT    /api/categories/preferences/{preference_id}   # Update preferences
DELETE /api/categories/preferences/{preference_id}   # Delete preferences
```

### Authentication Flow
```bash
POST   /api/auth/token           # Login
GET    /api/auth/me              # Get current user
GET    /api/auth/me/with-roles   # Get user with roles and companies
POST   /api/auth/switch-role     # Switch active role/company
```

---
**Last Updated**: 2025-08-31
**Status**: ✅ Security Issues Resolved - Ready for Production Testing
**Next Phase**: Deployment and Monitoring Setup