# Adara Platform Documentation

This directory contains the essential documentation for the Adara Digital Signage Platform. All duplicate and outdated documents have been removed to maintain clarity and reduce maintenance overhead.

**Copyright © 2024 Adara Screen by Hebron. All rights reserved.**  
**Owner: Sugesh M S**

This documentation is proprietary to Adara Screen by Hebron and contains confidential information. Unauthorized reproduction, distribution, or disclosure may result in legal action.

## 📚 **Core Documentation**

### **Architecture & Design**
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical system architecture and design decisions
- **[DATA_MODEL.md](DATA_MODEL.md)** - Database schema and data relationships
- **[UI_SPEC.md](UI_SPEC.md)** - User interface specifications and component library

### **Authentication & Security**
- **[ENHANCED_RBAC_SYSTEM.md](ENHANCED_RBAC_SYSTEM.md)** - Complete RBAC implementation guide
- **[security/](security/)** - Security policies and device registration guidelines

### **Development & Deployment**
- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup guide for development and production
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Comprehensive Azure deployment instructions
- **[api.md](api.md)** - API documentation and integration guides

### **Application Components**
- **[FLUTTER_APP_SPEC.md](FLUTTER_APP_SPEC.md)** - Flutter mobile/kiosk application specifications
- **[AI_CONTENT_MODERATION_FRAMEWORK.md](AI_CONTENT_MODERATION_FRAMEWORK.md)** - AI moderation system implementation

### **Project Management**
- **[IMPLEMENTATION_CHECKLIST_MASTER.md](IMPLEMENTATION_CHECKLIST_MASTER.md)** - Master implementation tracking
- **[CODEBASE_OPTIMIZATION_REPORT.md](CODEBASE_OPTIMIZATION_REPORT.md)** - Code quality and optimization report

## 🗑️ **Removed Documents**

The following documents have been removed due to duplication or being outdated:

### **Merged into Other Documents**
- RBAC_INTEGRATION_GUIDE.md → **ENHANCED_RBAC_SYSTEM.md**
- ROLES_AND_PERMISSIONS.md → **ENHANCED_RBAC_SYSTEM.md**
- COMPANY_REGISTRATION_REQUIREMENTS.md → **ENHANCED_RBAC_SYSTEM.md**
- AI_BEHAVIOR.md → **AI_CONTENT_MODERATION_FRAMEWORK.md**
- POWERSHELL_DEPLOYMENT.md → **DEPLOYMENT_GUIDE.md**
- GITHUB_SECRETS.md → **DEPLOYMENT_GUIDE.md**
- COST_OPTIMIZATION.md → **QUICKSTART.md**

### **Consolidated into Master Documents**
- FEATURE_IMPLEMENTATION_CHECKLIST.md → **IMPLEMENTATION_CHECKLIST_MASTER.md**
- TASK_CHECKLIST.md → **IMPLEMENTATION_CHECKLIST_MASTER.md**
- IMPLEMENTATION_SUMMARY.md → **IMPLEMENTATION_CHECKLIST_MASTER.md**
- DUPLICATE_CODE_CHECKLIST.md → **CODEBASE_OPTIMIZATION_REPORT.md**
- UNIFIED_CONTENT_OPTIMIZATION_SUMMARY.md → **CODEBASE_OPTIMIZATION_REPORT.md**

### **Outdated/Irrelevant**
- copilot-instruction.md (replaced by ../CLAUDE.md)
- Mobile_Wireframe.md (replaced by **FLUTTER_APP_SPEC.md**)
- pages.md (basic page list - covered in **UI_SPEC.md**)
- PERSONA.md (marketing content - not development docs)
- RISK_REGISTER.md (project management - not dev docs)
- sow.md (statement of work - not dev docs)
- ACCESSIBILITY_IMPROVEMENTS.md (outdated accessibility info)
- security.md (duplicate - **security/** folder has better content)

## 📋 **Documentation Standards**

### **File Naming Convention**
- Use **UPPERCASE.md** for major documents
- Use **lowercase.md** for specific technical docs (api.md)
- Group related docs in folders (security/)

### **Content Guidelines**
- Keep docs up-to-date with code implementation
- Cross-reference related documents
- Include practical examples and code snippets
- Maintain backward compatibility notes

### **Review Schedule**
- **Monthly**: Review for accuracy with codebase
- **Quarterly**: Update architecture and design docs
- **Before releases**: Validate all deployment guides

## 🔗 **External References**

- **Main Project Instructions**: ../CLAUDE.md
- **Quick Start Guide**: ../README.md
- **Optimization Report**: ./CODEBASE_OPTIMIZATION_REPORT.md

---

**Last Cleanup**: 2025-09-15  
**Documents Maintained**: 12 core files  
**Documents Removed**: 21 duplicate/outdated files  
**Space Saved**: ~60% reduction in documentation files
