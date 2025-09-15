# 🚀 Quick Start Guide - Adara Screen Digital Signage Platform

This guide gets you up and running with your digital signage platform on Azure in under 30 minutes.

## 📋 **What You'll Get**

- **Backend API** on Azure Container Apps (auto-scaling, serverless)
- **Frontend Web App** on Azure Static Web Apps (free tier, global CDN)
- **Database** on Azure Cosmos DB (MongoDB-compatible)
- **File Storage** on Azure Blob Storage with CDN
- **Complete CI/CD** via GitHub Actions
- **Estimated Cost**: $65-116/month (optimizable to $15-25/month for dev)

## ⚡ **Prerequisites**

### **Required Tools**
- **Azure CLI** - [Download](https://aka.ms/installazurecliwindows)
- **Terraform** - [Download](https://www.terraform.io/downloads.html)
- **PowerShell** (Windows) or **Bash** (Linux/Mac)
- **Git** - [Download](https://git-scm.com/downloads)

### **Azure Requirements**
- Azure subscription with Contributor role
- Ability to create service principals

## 🎯 **5-Minute Setup**

### **Step 1: Clone Repository**
```bash
git clone https://github.com/yourusername/adara-signage.git
cd adara-signage
```

### **Step 2: Azure Setup (Windows)**
```powershell
# Open PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run setup
.\scripts\setup-azure.ps1
```

### **Step 2: Azure Setup (Linux/Mac)**
```bash
# Make executable and run
chmod +x scripts/setup-azure.sh
./scripts/setup-azure.sh
```

### **Step 3: GitHub Secrets**
Add the displayed secrets to your GitHub repository:
1. Go to `Settings` > `Secrets and variables` > `Actions`
2. Add each secret shown by the setup script

### **Step 4: Deploy Application (Windows)**
```powershell
.\scripts\deploy.ps1
```

### **Step 4: Deploy Application (Linux/Mac)**
```bash
./scripts/deploy.sh
```

### **Step 5: Verify Deployment**
```powershell
# Windows
.\scripts\check-health.ps1 -Verbose -ExportReport

# Linux/Mac
./scripts/check-health.sh
```

## 🎉 **You're Done!**

Your application is now running on:
- **Frontend**: `https://your-app.azurestaticapps.net`
- **Backend API**: `https://your-backend.azurecontainerapps.io`
- **Health Report**: `./health-report.html`

## 📊 **Daily Operations**

### **Check Status**
```powershell
# Windows
.\scripts\manage-azure.ps1 -Action status

# Linux/Mac
./scripts/manage.sh status
```

### **View Logs**
```powershell
# Windows
.\scripts\manage-azure.ps1 -Action logs

# Linux/Mac
./scripts/manage.sh logs
```

### **Scale Services**
```powershell
# Windows
.\scripts\manage-azure.ps1 -Action scale -ScaleReplicas 3

# Linux/Mac
./scripts/manage.sh scale 3
```

## 🔧 **Troubleshooting**

### **Common Issues**

| Issue | Solution |
|-------|----------|
| Authentication failed | `az logout && az login` |
| Permission denied | Run as Administrator/sudo |
| Terraform not found | Install from terraform.io |
| Storage account exists | Use different name suffix |

### **Getting Help**
```powershell
# Show help
.\scripts\deploy.ps1 -Help
.\scripts\manage-azure.ps1 -Action help
```

## 📁 **Project Structure**

```
adara-signage/
├── scripts/                 # Deployment scripts
│   ├── setup-azure.ps1     # Azure setup (Windows)
│   ├── setup-azure.sh      # Azure setup (Linux/Mac)
│   ├── deploy.ps1          # Full deployment (Windows)
│   ├── deploy.sh           # Full deployment (Linux/Mac)
│   └── README.md           # Script documentation
├── terraform/              # Infrastructure as Code
│   ├── main.tf             # Core configuration
│   ├── variables.tf        # Customizable parameters
│   └── outputs.tf          # Deployment information
├── backend/                # FastAPI application
├── frontend/               # Next.js application
├── .github/workflows/      # CI/CD pipelines
└── docs/                   # Documentation
```

## 💰 **Cost Management**

### **Development Environment**
- Use `cosmos_db_offer_type = "Serverless"`
- Set `container_apps_cpu = 0.25`
- **Est. Cost**: $15-25/month

### **Production Environment**
- Enable auto-scaling: `min_replicas = 0`
- Use lifecycle policies for storage
- Monitor with cost alerts
- **Est. Cost**: $65-116/month

## 🔒 **Security Features**

- **Azure Key Vault** for secrets management
- **Managed Identity** for service authentication
- **HTTPS** everywhere with auto-certificates
- **RBAC** for fine-grained access control
- **Network isolation** options available

## 📈 **Scaling**

- **Horizontal**: Container Apps auto-scale 0-10 instances
- **Database**: Cosmos DB scales RU/s on demand
- **Storage**: Blob storage scales automatically
- **Global**: CDN for worldwide content delivery

## 🚀 **Next Steps**

1. **Customize**: Edit `terraform/terraform.tfvars` for your needs
2. **Monitor**: Set up Azure Monitor alerts
3. **Optimize**: Review cost optimization guide
4. **Secure**: Configure custom domains and SSL
5. **Scale**: Add more regions as needed

## 📞 **Support**

- **Documentation**: See `/docs` folder for detailed guides
- **Issues**: Report in GitHub repository
- **Community**: Join our Discord/Slack (if available)

---

**🎯 Total Setup Time**: ~15-30 minutes
**💰 Monthly Cost**: $15-116 (depending on usage)
**🌍 Global Scale**: Ready for worldwide deployment
**🔒 Enterprise Security**: Built-in from day one