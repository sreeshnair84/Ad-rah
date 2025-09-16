# 🚀 Quick Start Guide - Adara Screen Digital Signage Platform

**✅ FULLY IMPLEMENTED & PRODUCTION READY** - This guide gets you up and running with your **complete digital signage platform** in under 15 minutes.

## 📋 **What You'll Get** ✅ **ALL IMPLEMENTED**

- **✅ Backend API** on Azure Container Apps (auto-scaling, serverless) - **READY**
- **✅ Frontend Web App** on Azure Static Web Apps (free tier, global CDN) - **READY**
- **✅ Database** on Azure Cosmos DB (MongoDB-compatible) - **READY**
- **✅ File Storage** on Azure Blob Storage with CDN - **READY**
- **✅ Complete CI/CD** via GitHub Actions - **READY**
- **✅ RBAC System** with three-tier user management - **READY**
- **✅ Flutter Kiosk App** for Android devices - **READY**
- **✅ AI Content Moderation** with multi-provider support - **READY**
- **Estimated Cost**: $65-116/month (optimizable to $15-25/month for dev)

## ⚡ **Prerequisites** ✅ **STANDARD TOOLS**

### **Required Tools**
- **Azure CLI** - [Download](https://aka.ms/installazurecliwindows)
- **Terraform** - [Download](https://www.terraform.io/downloads.html)
- **PowerShell** (Windows) or **Bash** (Linux/Mac)
- **Git** - [Download](https://git-scm.com/downloads)
- **UV Package Manager** - `curl -LsSf https://astral.sh/uv/install.sh | sh`

### **Azure Requirements**
- Azure subscription with Contributor role
- Ability to create service principals

## 🎯 **10-Minute Setup** ✅ **STREAMLINED**

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

## 🎉 **You're Done!** ✅ **FULLY OPERATIONAL**

Your **complete digital signage platform** is now running on:
- **Frontend**: `https://your-app.azurestaticapps.net`
- **Backend API**: `https://your-backend.azurecontainerapps.io`
- **API Documentation**: `https://your-backend.azurecontainerapps.io/docs`
- **Health Report**: `./health-report.html`

## 📊 **Daily Operations** ✅ **ALL TOOLS READY**

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

## 🔧 **Local Development** ✅ **FULLY SUPPORTED**

### **Quick Local Setup**
```bash
# 1. Start services
cd backend/content_service
docker-compose up -d

# 2. Install dependencies
uv sync

# 3. Seed demo data
uv run python seed_data.py

# 4. Start backend
uv run uvicorn app.main:app --reload --port 8000

# 5. Start frontend (new terminal)
cd ../../frontend
npm install
npm run dev

# 6. Access applications
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### **Demo Accounts**
- **Super Admin**: `admin@adara.com` / `adminpass`
- **Host Company**: `host@techcorpsolutions.com` / `hostpass`
- **Advertiser**: `director@creativeadsinc.com` / `advertiserpass`

## 📁 **Project Structure** ✅ **COMPLETE IMPLEMENTATION**

```
adara-signage/
├── scripts/                 # Deployment scripts ✅
│   ├── setup-azure.ps1     # Azure setup (Windows) ✅
│   ├── setup-azure.sh      # Azure setup (Linux/Mac) ✅
│   ├── deploy.ps1          # Full deployment (Windows) ✅
│   ├── deploy.sh           # Full deployment (Linux/Mac) ✅
│   └── README.md           # Script documentation ✅
├── terraform/              # Infrastructure as Code ✅
│   ├── main.tf             # Core configuration ✅
│   ├── variables.tf        # Customizable parameters ✅
│   └── outputs.tf          # Deployment information ✅
├── backend/                # FastAPI application ✅
│   └── content_service/    # Complete API implementation ✅
├── frontend/               # Next.js application ✅
│   ├── src/app/            # Complete dashboard ✅
│   └── components/         # RBAC-aware UI components ✅
├── flutter/                # Flutter kiosk app ✅
│   └── adarah_digital_signage/ # 5-screen architecture ✅
├── .github/workflows/      # CI/CD pipelines ✅
└── docs/                   # Complete documentation ✅
```

## 💰 **Cost Management** ✅ **OPTIMIZED**

### **Development Environment**
- Use `cosmos_db_offer_type = "Serverless"`
- Set `container_apps_cpu = 0.25`
- **Est. Cost**: $15-25/month

### **Production Environment**
- Enable auto-scaling: `min_replicas = 0`
- Use lifecycle policies for storage
- Monitor with cost alerts
- **Est. Cost**: $65-116/month

## 🔒 **Security Features** ✅ **ENTERPRISE GRADE**

- **Azure Key Vault** for secrets management ✅
- **Managed Identity** for service authentication ✅
- **HTTPS** everywhere with auto-certificates ✅
- **RBAC** for fine-grained access control ✅
- **JWT Authentication** with refresh tokens ✅
- **Company Isolation** for multi-tenant security ✅
- **AI Content Moderation** with safety scoring ✅
- **Network isolation** options available ✅

## 📈 **Scaling** ✅ **AUTO-SCALING READY**

- **Horizontal**: Container Apps auto-scale 0-10 instances ✅
- **Database**: Cosmos DB scales RU/s on demand ✅
- **Storage**: Blob storage scales automatically ✅
- **Global**: CDN for worldwide content delivery ✅
- **Analytics**: Real-time performance monitoring ✅

## 🚀 **Next Steps** ✅ **READY TO SCALE**

1. **Customize**: Edit `terraform/terraform.tfvars` for your needs ✅
2. **Monitor**: Set up Azure Monitor alerts ✅
3. **Optimize**: Review cost optimization guide ✅
4. **Secure**: Configure custom domains and SSL ✅
5. **Scale**: Add more regions as needed ✅
6. **Deploy Devices**: Use Flutter app for kiosk deployment ✅
7. **Manage Content**: Use web dashboard for content management ✅

## 📞 **Support** ✅ **COMPLETE RESOURCES**

- **Documentation**: See `/docs` folder for detailed guides ✅
- **API Documentation**: Interactive Swagger docs at `/docs` ✅
- **Issues**: Report in GitHub repository ✅
- **Implementation Status**: All features fully implemented ✅

---

**🎯 Total Setup Time**: ~10-15 minutes
**💰 Monthly Cost**: $15-116 (depending on usage)
**🌍 Global Scale**: Ready for worldwide deployment
**🔒 Enterprise Security**: Built-in from day one
**✅ Implementation Status**: FULLY IMPLEMENTED & PRODUCTION READY