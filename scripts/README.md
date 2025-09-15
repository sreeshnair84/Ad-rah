# PowerShell Scripts for Adara Screen Digital Signage Platform

This directory contains clean, production-ready PowerShell scripts for deploying and managing your application on Azure.

## 📁 **Scripts Overview**

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup-azure.ps1` | Initial Azure setup | First-time deployment only |
| `deploy.ps1` | Complete application deployment | After Azure setup is complete |
| `check-health.ps1` | Health monitoring and reporting | Regular monitoring |
| `manage-azure.ps1` | Resource management operations | Day-to-day operations |

## 🚀 **Quick Start**

### **1. First-Time Setup**
```powershell
# Run this ONCE to set up Azure resources
.\scripts\setup-azure.ps1
```

### **2. Deploy Application**
```powershell
# Run this to deploy your application
.\scripts\deploy.ps1
```

### **3. Monitor Health**
```powershell
# Check if everything is running
.\scripts\check-health.ps1 -Verbose
```

## 📋 **Prerequisites**

- **Windows PowerShell 5.1+** or **PowerShell Core 7+**
- **Azure CLI** - [Download Here](https://aka.ms/installazurecliwindows)
- **Terraform** - [Download Here](https://www.terraform.io/downloads.html)
- **Git** - [Download Here](https://git-scm.com/download/win)

## 🔧 **Script Details**

### **setup-azure.ps1**
Creates Azure infrastructure for Terraform backend:
- Resource group for Terraform state
- Storage account for state files
- Service principal for GitHub Actions

**Usage:**
```powershell
.\scripts\setup-azure.ps1
.\scripts\setup-azure.ps1 -SubscriptionId "your-sub-id"
.\scripts\setup-azure.ps1 -Location "UAE North"
```

### **deploy.ps1**
Deploys the complete application:
- Validates prerequisites
- Builds applications
- Runs Terraform
- Performs health checks

**Usage:**
```powershell
.\scripts\deploy.ps1
.\scripts\deploy.ps1 -SkipBuild        # Skip app builds
.\scripts\deploy.ps1 -SkipTerraform    # Skip infrastructure
.\scripts\deploy.ps1 -SkipHealth       # Skip health checks
```

### **check-health.ps1**
Monitors application health:
- Tests all services
- Generates HTML reports
- Checks response times

**Usage:**
```powershell
.\scripts\check-health.ps1
.\scripts\check-health.ps1 -Verbose
.\scripts\check-health.ps1 -ExportReport
.\scripts\check-health.ps1 -ReportPath "C:\reports\health.html"
```

### **manage-azure.ps1**
Manages Azure resources:
- View service status
- Restart services
- Scale applications
- View logs
- Cost analysis

**Usage:**
```powershell
.\scripts\manage-azure.ps1 -Action status
.\scripts\manage-azure.ps1 -Action restart
.\scripts\manage-azure.ps1 -Action scale -ScaleReplicas 3
.\scripts\manage-azure.ps1 -Action logs -LogLines 100
.\scripts\manage-azure.ps1 -Action cost
```

## 🛡️ **Security**

- Scripts use secure Azure authentication
- No hardcoded credentials
- Follows PowerShell security best practices
- Uses Azure Key Vault for secrets

## 🚨 **Troubleshooting**

### **Common Issues**

#### **"Execution Policy" Error**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### **"Azure CLI Not Found"**
Install Azure CLI: `winget install Microsoft.AzureCLI`

#### **"Not Authenticated"**
```powershell
az logout
az login
```

### **Getting Help**
```powershell
.\scripts\deploy.ps1 -Help
.\scripts\manage-azure.ps1 -Action help
```

## 📞 **Support**

- Check the main [deployment guide](../docs/POWERSHELL_DEPLOYMENT.md) for detailed instructions
- Report issues in the project's GitHub repository
- Ensure you have the latest Azure CLI and PowerShell versions