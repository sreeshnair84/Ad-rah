# Company Registration Management Requirements

## Overview
This document defines the standardized process for Host Company and Advertiser Company registration approval within the OpenKiosk platform. This addresses the current confusion between user invitations and company applications.

## Current Issues Identified

### 1. Conflicting Registration Terminology
- **User Registration**: Individual users joining existing companies (implemented)
- **Company Registration**: HOST/ADVERTISER companies applying to join platform (missing)
- **Issue**: Both use "registration" causing confusion

### 2. Missing Company Application Backend
- Frontend UI exists with mock data (`registration/page.tsx`)
- No backend API implementation for company applications
- No database schema for company applications
- No approval workflow persistence

### 3. Roles Screen Access Issues
- Fixed: Backend permission check was disabled for debugging
- Admin users can now properly access roles management screen

## Standardized Company Registration Process

### Business Process Flow

```
1. Company Application Submission (Public)
   ↓
2. Admin Review & Document Verification (Admin Only)
   ↓
3. Approval Decision with Approver Tracking (Admin Only)
   ↓
4. Post-Approval Automation (System)
   - Create company record
   - Create default admin user
   - Send credentials to applicant
   - Assign default role
```

### Technical Implementation Requirements

#### Database Schema

```python
class CompanyApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Company Information
    company_name: str
    company_type: Literal["HOST", "ADVERTISER"]
    business_license: str
    address: str
    city: str
    country: str
    website: Optional[str] = None
    description: str
    
    # Applicant Information  
    applicant_name: str
    applicant_email: str
    applicant_phone: str
    
    # Process Tracking
    status: Literal["pending", "under_review", "approved", "rejected"] = "pending"
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None  # Critical: Track approving admin
    reviewer_notes: Optional[str] = None
    
    # Document Management
    documents: Dict[str, str] = {}  # document_type -> file_url/path
    
    # Post-Approval Linking
    created_company_id: Optional[str] = None
    created_user_id: Optional[str] = None
    
    # Audit Fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Required API Endpoints

##### Public Endpoints
```python
POST /api/company-applications
# Submit company application (public)
# Body: CompanyApplicationRequest
# Response: {"message": "Application submitted", "application_id": str}
```

##### Admin-Only Endpoints
```python
GET /api/company-applications
# List all applications with filtering
# Query params: status?, company_type?, page?, limit?
# Response: List[CompanyApplication]

GET /api/company-applications/{application_id}
# Get detailed application info
# Response: CompanyApplication with full details

PUT /api/company-applications/{application_id}/review
# Approve or reject application
# Body: {"decision": "approved|rejected", "notes": str}
# Action: Records reviewer_id automatically from current_user

GET /api/company-applications/{application_id}/documents/{document_type}
# Download/view submitted documents
# Response: File stream or signed URL

POST /api/company-applications/{application_id}/approve
# Execute approval workflow
# Action: Creates company + admin user + role assignment
```

#### Frontend Integration

Update `frontend/src/app/dashboard/registration/page.tsx`:

1. **Replace mock data** with actual API calls
2. **Add approver user ID tracking** in review workflow
3. **Implement document viewing/downloading**
4. **Add proper error handling and loading states**

Key changes needed:
```typescript
// Replace mock data with API calls
const fetchApplications = async () => {
  const response = await fetch('/api/company-applications', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};

// Add approver tracking in review submission
const handleReviewSubmit = async () => {
  const reviewData = {
    decision: reviewDecision,
    notes: reviewNotes
    // reviewer_id will be automatically set from current_user in backend
  };
  // ... API call to submit review
};
```

#### Repository Methods

```python
# Add to repo.py
async def save_company_application(self, application: CompanyApplication) -> dict
async def get_company_application(self, application_id: str) -> Optional[dict] 
async def list_company_applications(self, status: Optional[str] = None, company_type: Optional[str] = None) -> List[dict]
async def update_company_application_status(self, application_id: str, status: str, reviewer_id: str, notes: str) -> bool
async def get_company_applications_by_status(self, status: str) -> List[dict]
```

### Security & Compliance Requirements

1. **Approver Audit Trail**
   - Every approval/rejection MUST record reviewer_id
   - Reviewer notes are mandatory for rejections
   - Audit log of all status changes

2. **Document Security**
   - Secure file upload with validation
   - Document access restricted to admin users
   - File type restrictions (PDF, images only)
   - Maximum file size limits

3. **Data Protection**
   - PII encryption for applicant information
   - Secure deletion of rejected applications after retention period
   - GDPR compliance for data handling

### Implementation Priority

#### Phase 1: Core Functionality (Week 1)
- [ ] Create CompanyApplication model
- [ ] Implement backend API endpoints
- [ ] Add repository methods
- [ ] Update frontend to use real API

#### Phase 2: Document Management (Week 2)
- [ ] Implement file upload/storage
- [ ] Add document viewing capabilities
- [ ] Secure document access controls

#### Phase 3: Workflow Automation (Week 3)
- [ ] Post-approval company creation
- [ ] Automatic user account creation
- [ ] Email notifications
- [ ] Role assignment automation

#### Phase 4: Advanced Features (Week 4)
- [ ] Bulk application actions
- [ ] Advanced filtering and search
- [ ] Application analytics dashboard
- [ ] Audit trail reporting

### Testing Requirements

1. **Unit Tests**
   - All repository methods
   - API endpoint functionality
   - Business logic validation

2. **Integration Tests**
   - End-to-end application workflow
   - File upload/download
   - Email notification delivery

3. **Security Tests**
   - Authentication/authorization
   - File upload security
   - Data access controls

### Migration Plan

1. **Database Migration**
   ```sql
   CREATE TABLE company_applications (
     id VARCHAR(36) PRIMARY KEY,
     company_name VARCHAR(255) NOT NULL,
     company_type ENUM('HOST', 'ADVERTISER') NOT NULL,
     -- ... other fields
     reviewer_id VARCHAR(36),
     INDEX idx_status (status),
     INDEX idx_reviewer (reviewer_id),
     FOREIGN KEY (reviewer_id) REFERENCES users(id)
   );
   ```

2. **API Versioning**
   - New endpoints under `/api/v1/company-applications`
   - Maintain backward compatibility
   - Gradual migration of frontend components

3. **Data Migration**
   - No existing data to migrate (new feature)
   - Seed test data for development

---

## Summary

The standardized company registration process will:

1. **Separate concerns** between user invitations and company applications
2. **Provide full audit trail** with approver user ID tracking  
3. **Enable admin control** over company onboarding
4. **Automate post-approval** company and user creation
5. **Ensure compliance** with data protection requirements

This implementation addresses all identified issues and provides a scalable foundation for company onboarding management.

---
**Document Version**: 1.0  
**Last Updated**: 2025-08-30  
**Author**: Claude Code Analysis  
**Status**: Requirements Finalized - Ready for Implementation