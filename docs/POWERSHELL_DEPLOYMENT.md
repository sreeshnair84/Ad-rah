# PowerShell Deployment Guide - Adara Screen Digital Signage Platform

This guide provides Windows users with PowerShell scripts for deploying and managing the Adara Screen Digital Signage Platform on Azure.

## 📋 **Prerequisites**

### **Required Software**
- **Windows PowerShell 5.1** or **PowerShell Core 7+**
- **Azure CLI** - [Download and Install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows)
- **Terraform** - [Download and Install](https://www.terraform.io/downloads.html)
- **Git** - [Download and Install](https://git-scm.com/download/win)

### **Optional Software**
- **Docker Desktop** - For local testing
- **Node.js** - For frontend development
- **Python** - For backend development
- **UV** - Python package manager

## 🚀 **PowerShell Scripts Overview**

### **Core Scripts**

| Script | Description | Usage |
|--------|-------------|-------|
| `setup-azure.ps1` | Azure initial setup and service principal creation | One-time setup |
| `deploy.ps1` | Complete deployment automation | Full deployment |
| `check-health.ps1` | Health monitoring and reporting | Ongoing monitoring |
| `manage-azure.ps1` | Resource management operations | Day-to-day operations |

## 📝 **Step-by-Step Deployment**

### **Step 1: Initial Azure Setup**

1. **Open PowerShell as Administrator**
2. **Navigate to your project directory:**
   ```powershell
   cd C:\path\to\your\project
   ```

3. **Run the Azure setup script:**
   ```powershell
   # Allow script execution (if needed)
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

   # Run setup
   .\scripts\setup-azure.ps1
   ```

4. **Follow the prompts:**
   - Enter your Azure Subscription ID (or press Enter for current)
   - The script will create:
     - Resource group for Terraform state
     - Storage account for Terraform backend
     - Service principal for GitHub Actions

5. **Save the output:**
   - Copy the `AZURE_CREDENTIALS` JSON
   - Save all GitHub secrets displayed

### **Step 2: Configure GitHub Repository**

Add all secrets from Step 1 to your GitHub repository:
1. Go to your GitHub repository
2. Navigate to `Settings` > `Secrets and variables` > `Actions`
3. Add all the secrets displayed by the setup script

### **Step 3: Deploy Infrastructure**

1. **Run the deployment script:**
   ```powershell
   .\scripts\deploy.ps1
   ```

2. **The script will:**
   - Check prerequisites
   - Build and test applications
   - Initialize Terraform
   - Plan the deployment
   - Apply the infrastructure

3. **Review and approve the Terraform plan when prompted**

### **Step 4: Update GitHub Secrets**

After deployment, update these secrets with actual values:
```powershell
# Get the outputs
$outputs = Get-Content .\terraform\terraform-outputs.json | ConvertFrom-Json

# Update these GitHub secrets:
# CONTAINER_REGISTRY_NAME
# BACKEND_CONTAINER_APP_NAME
# NEXT_PUBLIC_API_URL
# AZURE_STATIC_WEB_APPS_API_TOKEN
# FRONTEND_APP_URL
```

## 🔧 **Script Usage Examples**

### **setup-azure.ps1**

```powershell
# Basic setup
.\scripts\setup-azure.ps1

# Specify subscription ID
.\scripts\setup-azure.ps1 -SubscriptionId "your-subscription-id"

# Custom resource group name
.\scripts\setup-azure.ps1 -ResourceGroupName "my-terraform-state"

# Custom location
.\scripts\setup-azure.ps1 -Location "UAE North"
```

### **deploy.ps1**

```powershell
# Full deployment
.\scripts\deploy.ps1

# Skip Terraform (if already deployed)
.\scripts\deploy.ps1 -SkipTerraform

# Skip application builds
.\scripts\deploy.ps1 -SkipBuild

# Skip health checks
.\scripts\deploy.ps1 -SkipHealth

# Get help
.\scripts\deploy.ps1 -Help
```

### **check-health.ps1**

```powershell
# Basic health check
.\scripts\check-health.ps1

# Verbose output
.\scripts\check-health.ps1 -Verbose

# Export HTML report
.\scripts\check-health.ps1 -ExportReport

# Custom report path
.\scripts\check-health.ps1 -ExportReport -ReportPath "C:\reports\health.html"

# Custom config file
.\scripts\check-health.ps1 -ConfigFile ".\custom-outputs.json"
```

### **manage-azure.ps1**

```powershell
# Check service status
.\scripts\manage-azure.ps1 -Action status

# Restart services
.\scripts\manage-azure.ps1 -Action restart

# Scale services
.\scripts\manage-azure.ps1 -Action scale -ScaleReplicas 3

# View logs (last 50 lines)
.\scripts\manage-azure.ps1 -Action logs -LogLines 50

# Cost analysis
.\scripts\manage-azure.ps1 -Action cost

# Cleanup old resources
.\scripts\manage-azure.ps1 -Action cleanup -Force

# Backup configuration
.\scripts\manage-azure.ps1 -Action backup

# Get help
.\scripts\manage-azure.ps1 -Action help
```

## 🛠️ **PowerShell Utility Functions**

### **Import Utils Module**
```powershell
# Import utility functions
. .\scripts\utils.ps1

# Use utility functions
Write-Status "This is an info message"
Write-Warning "This is a warning message"
Write-Error "This is an error message"
Write-Header "Section Header"
```

### **Common Utility Functions**

```powershell
# Test if command exists
Test-Command "terraform"

# Test Azure authentication
$auth = Test-AzureAuth
if ($auth.Authenticated) {
    Write-Host "Logged in as: $($auth.Account)"
}

# Test internet connection
if (Test-InternetConnection) {
    Write-Host "Internet connection is available"
}

# Generate random string
$randomString = New-RandomString -Length 10 -IncludeNumbers

# Wait for service to be ready
Wait-ForService -Url "https://myapp.com" -MaxRetries 30

# Get Terraform outputs
$outputs = Get-TerraformOutputs -TerraformDir ".\terraform"

# Show system information
Show-SystemInfo
```

## 🐛 **Troubleshooting**

### **Common Issues and Solutions**

#### **Execution Policy Error**
```powershell
# Error: execution of scripts is disabled
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### **Azure CLI Not Found**
```powershell
# Install Azure CLI using winget
winget install Microsoft.AzureCLI

# Or download from: https://aka.ms/installazurecliwindows
```

#### **Terraform Not Found**
```powershell
# Install Terraform using Chocolatey
choco install terraform

# Or download from: https://www.terraform.io/downloads.html
```

#### **Authentication Issues**
```powershell
# Re-authenticate to Azure
az logout
az login

# Check current account
az account show
```

#### **Script Permissions**
```powershell
# If scripts won't run, check execution policy
Get-ExecutionPolicy

# Allow signed scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Debug Mode**
```powershell
# Run scripts with verbose output
.\scripts\deploy.ps1 -Verbose

# Or enable debug output
$VerbosePreference = "Continue"
.\scripts\deploy.ps1
```

## 📊 **Monitoring and Maintenance**

### **Daily Operations**
```powershell
# Check health status
.\scripts\check-health.ps1 -Verbose

# View recent logs
.\scripts\manage-azure.ps1 -Action logs -LogLines 100

# Check costs
.\scripts\manage-azure.ps1 -Action cost
```

### **Weekly Operations**
```powershell
# Clean up old resources
.\scripts\manage-azure.ps1 -Action cleanup

# Backup configuration
.\scripts\manage-azure.ps1 -Action backup

# Generate health report
.\scripts\check-health.ps1 -ExportReport -ReportPath ".\reports\weekly-health.html"
```

### **Monthly Operations**
```powershell
# Review cost analysis
.\scripts\manage-azure.ps1 -Action cost

# Update services (if needed)
.\scripts\manage-azure.ps1 -Action update
```

## 🔒 **Security Best Practices**

### **Script Security**
- Always verify script sources before execution
- Use signed execution policy: `Set-ExecutionPolicy RemoteSigned`
- Regularly update Azure CLI and PowerShell

### **Credential Management**
- Never hardcode credentials in scripts
- Use Azure Key Vault for sensitive data
- Rotate service principal credentials regularly

### **Access Control**
- Use least-privilege principle for service principals
- Regularly audit access permissions
- Enable multi-factor authentication

## 📁 **File Structure**

```
scripts/
├── setup-azure.ps1      # Initial Azure setup
├── deploy.ps1          # Complete deployment
├── utils.ps1           # Utility functions
├── check-health.ps1    # Health monitoring
└── manage-azure.ps1    # Resource management

docs/
├── POWERSHELL_DEPLOYMENT.md  # This file
├── DEPLOYMENT_GUIDE.md       # General deployment guide
├── GITHUB_SECRETS.md          # GitHub secrets configuration
└── COST_OPTIMIZATION.md      # Cost optimization guide
```

## 🚀 **Quick Start Commands**

### **Complete Setup (New Installation)**
```powershell
# 1. Clone repository
git clone https://github.com/yourusername/adara-signage.git
cd adara-signage

# 2. Initial Azure setup
.\scripts\setup-azure.ps1

# 3. Configure GitHub secrets (manual step)
# Add all displayed secrets to GitHub repository

# 4. Deploy infrastructure
.\scripts\deploy.ps1

# 5. Check health
.\scripts\check-health.ps1 -Verbose -ExportReport
```

### **Daily Monitoring**
```powershell
# Check status
.\scripts\manage-azure.ps1 -Action status

# View logs if issues
.\scripts\manage-azure.ps1 -Action logs

# Generate health report
.\scripts\check-health.ps1 -ExportReport
```

### **Emergency Operations**
```powershell
# Restart services
.\scripts\manage-azure.ps1 -Action restart -Force

# Scale up for high load
.\scripts\manage-azure.ps1 -Action scale -ScaleReplicas 5

# Check costs if unexpected charges
.\scripts\manage-azure.ps1 -Action cost
```

## 📞 **Support and Resources**

- **GitHub Issues**: Report issues in the project repository
- **Azure Documentation**: [Azure PowerShell Documentation](https://docs.microsoft.com/en-us/powershell/azure/)
- **Terraform Documentation**: [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)

For additional help, ensure you have the latest versions of all tools and check the troubleshooting section above.