# 🔑 Required Keys Quick Reference

## ✅ GitHub Repository Secrets Checklist

### Required for All Deployments
- [ ] `AZURE_CREDENTIALS` - Service principal JSON
- [ ] `RESOURCE_GROUP_NAME` - Azure resource group
- [ ] `AZURE_LOCATION` - Azure region (e.g., eastus)
- [ ] `PROJECT_NAME` - Project identifier

### Backend Deployment
- [ ] `CONTAINER_REGISTRY_NAME` - ACR name (without .azurecr.io)
- [ ] `BACKEND_CONTAINER_APP_NAME` - Container app name

### Frontend Deployment
- [ ] `AZURE_STATIC_WEB_APPS_API_TOKEN` - SWA deployment token
- [ ] `NEXT_PUBLIC_API_URL` - Backend API URL

### Infrastructure (Terraform)
- [ ] `TERRAFORM_STORAGE_ACCOUNT` - State storage account
- [ ] `TERRAFORM_CONTAINER_NAME` - State container (usually "tfstate")
- [ ] `TERRAFORM_STATE_KEY` - State file name
- [ ] `TERRAFORM_RESOURCE_GROUP` - State resource group

## 🔧 Local Development Files

### Backend (.env)
```bash
MONGO_URI=mongodb://localhost:27017/openkiosk
SECRET_KEY=your-super-secure-secret-key-change-me
JWT_SECRET_KEY=your-jwt-secret-key-change-me
ENVIRONMENT=development
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🚀 Quick Setup Commands

```bash
# 1. Clone and setup
git clone <repo-url>
cd Open_kiosk

# 2. Copy environment template
cp backend/content_service/.env.template backend/content_service/.env

# 3. Create frontend env
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local

# 4. Start services
cd backend/content_service && docker-compose up -d
cd ../../frontend && npm install && npm run dev

# 5. Seed test data
cd backend/content_service && uv run python seed_data.py
```

## 🔐 Azure Service Principal Creation

```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac --name "github-actions-sp" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth
```

Copy the entire JSON output to `AZURE_CREDENTIALS` secret.

## 📱 Test Accounts (After Seeding)

- **Super User**: admin@adara.com / adminpass
- **Company Admin**: admin@techcorpsolutions.com / adminpass  
- **Content Reviewer**: reviewer@techcorpsolutions.com / adminpass
- **Content Editor**: editor@techcorpsolutions.com / adminpass

## 🚨 Security Warnings

- ⚠️ **Never commit secrets to git**
- ⚠️ **Change default passwords in production**
- ⚠️ **Use different secrets for dev/staging/prod**
- ⚠️ **Rotate secrets regularly**

## 📞 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| GitHub Actions failing | Check all secrets are configured |
| Backend won't start | Verify MongoDB is running and .env exists |
| Frontend can't connect | Check NEXT_PUBLIC_API_URL in .env.local |
| Azure deployment fails | Verify service principal permissions |
| Container registry access denied | Check ACR permissions for service principal |

## 📚 Documentation Links

- [Complete Setup Guide](.github/SECRETS_SETUP.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [GitHub Actions Validation](.github/validate-workflows.sh)