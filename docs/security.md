# Security Architecture - Adārah from Hebron™

## Current Security Status

### CRITICAL VULNERABILITIES (IMMEDIATE ACTION REQUIRED)

1. **JWT Secret Management** 🔴
   - **Issue**: Hardcoded secret key in source code
   - **Risk**: Complete authentication bypass possible
   - **Fix**: Move to environment variables immediately, migrate to Azure Key Vault

2. **PII Data Exposure** 🔴
   - **Issue**: No encryption for personally identifiable information
   - **Risk**: GDPR/UAE data protection violations
   - **Fix**: Implement field-level encryption for PII fields

3. **Authentication State Management** 🟡
   - **Issue**: Login redirect loops, inconsistent token validation
   - **Status**: ✅ FIXED - Improved token validation and state management

### Identity & Authentication

#### Current Implementation
- **Authentication**: JWT tokens with configurable expiration (default 60 minutes)
- **Storage**: localStorage in frontend (development mode)
- **Validation**: Enhanced token expiration checking and error handling
- **Fallback**: SHA256 hashing when bcrypt unavailable

#### Production Requirements
- **Identity Provider**: Entra ID OIDC integration
- **Token Strategy**: Short-lived access tokens (15 min) + rotating refresh tokens
- **Device Security**: Device-bound tokens for kiosk endpoints
- **Secret Management**: Azure Key Vault with Managed Identity

### Authorization Model

#### Current Implementation
- **RBAC**: Role-based access control with company-scoped permissions
- **Roles**: ADMIN, HOST, ADVERTISER with hierarchical permissions
- **Checks**: Handler-level authorization with role validation

#### Role Hierarchy
```
ADMIN (Global)
├── Full platform access
├── User management across all companies
└── System configuration

HOST (Company-scoped)  
├── Kiosk management
├── Content approval
├── Revenue analytics
└── Advertiser management

ADVERTISER (Company-scoped)
├── Content upload
├── Campaign management
├── Performance analytics
└── Billing access
```

### Data Protection

#### PII Classification
**Highly Sensitive**
- User passwords (hashed)
- Payment information
- Personal contact details

**Sensitive**  
- User behavior analytics
- QR code interaction data
- Company financial data

**Internal**
- Content metadata
- System logs
- Performance metrics

#### Current Data Handling
- **Encryption at Rest**: MongoDB encryption (if enabled)
- **Encryption in Transit**: TLS 1.3 for all connections
- **PII Protection**: ⚠️ NO FIELD-LEVEL ENCRYPTION (Critical Gap)

#### Required Data Protection Measures
1. **Field-Level Encryption**: Encrypt PII fields with separate keys
2. **Audit Logging**: Log all access to sensitive data
3. **Data Retention**: Automated cleanup based on retention policies
4. **Access Controls**: Principle of least privilege enforcement

### Content Security

#### Upload Security
- **Current**: Direct multipart upload to Azure Blob Storage
- **Validation**: Basic file type and size checks
- **Scanning**: ⚠️ NO VIRUS SCANNING (Critical Gap)

#### Required Content Protection
- **Upload Flow**: Presigned SAS URLs only
- **File Validation**: Strict allowlist for file types and sizes
- **Security Scanning**: Mandatory virus/malware detection
- **Content Sanitization**: Server-side HTML/script sanitization

### Network Security

#### Current Configuration
```javascript
// CORS Settings
allow_origins: [
  "http://localhost:3000",
  "http://127.0.0.1:3000", 
  "http://localhost:8000",
  "http://127.0.0.1:8000"
]
```

#### Production Security Headers
```http
Content-Security-Policy: default-src 'self'; script-src 'none' (for previews)
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Event & Message Security

#### Architecture
- **Message Bus**: Azure Service Bus for event processing
- **Authentication**: Managed Identity for service-to-service
- **Encryption**: Encrypted message payloads
- **Audit**: Complete event audit trail

### Compliance Framework

#### UAE Data Protection Requirements
- **Residency**: All data stored within UAE borders
- **Encryption**: AES-256 encryption for data at rest
- **Access Logs**: Complete audit trail for data access
- **Retention**: Configurable retention policies

#### GDPR Compliance (for EU users)
- **Right to be Forgotten**: Automated data deletion
- **Data Portability**: Export functionality for user data
- **Consent Management**: Granular permission tracking
- **Breach Notification**: 72-hour notification procedures

### Security Monitoring

#### Current Logging
- **Level**: Basic application logs
- **Format**: Unstructured text
- **Storage**: Local files/console

#### Required Security Monitoring
- **SIEM Integration**: Azure Sentinel for security events
- **Structured Logging**: JSON format with correlation IDs  
- **Alert Policies**: Real-time alerting for security events
- **Compliance Reporting**: Automated compliance dashboards

### Incident Response

#### Security Incident Categories
1. **P0 - Critical**: Data breach, system compromise
2. **P1 - High**: Authentication bypass, privilege escalation
3. **P2 - Medium**: Suspicious activity, policy violations
4. **P3 - Low**: Configuration issues, minor policy gaps

#### Response Procedures
1. **Detection**: Automated alerting + manual monitoring
2. **Containment**: Immediate isolation of affected systems
3. **Investigation**: Forensic analysis and impact assessment
4. **Recovery**: Secure system restoration and hardening
5. **Documentation**: Comprehensive incident reporting

### Immediate Action Items

#### Week 1 - Critical Fixes
- [ ] Move JWT secret to environment variables
- [ ] Implement PII field-level encryption
- [ ] Add comprehensive input validation
- [ ] Enable security headers in production

#### Week 2 - Enhanced Security
- [ ] Implement refresh token mechanism  
- [ ] Add rate limiting for authentication
- [ ] Deploy Azure Key Vault integration
- [ ] Configure security monitoring

#### Week 3-4 - Compliance & Hardening
- [ ] Complete GDPR compliance implementation
- [ ] Deploy virus scanning for uploads
- [ ] Implement automated security testing
- [ ] Create incident response procedures

---
**Classification**: Internal Use Only
**Last Updated**: 2025-08-28  
**Next Review**: 2025-09-28
**Owner**: Security Engineering Team