# GitHub Repository Secrets Configuration

This document outlines all the required secrets and variables that need to be configured in your GitHub repository for the CI/CD pipeline to work properly.

## 📝 **How to Add Secrets**

1. Go to your GitHub repository
2. Navigate to `Settings` > `Secrets and variables` > `Actions`
3. Click `New repository secret`
4. Add each secret listed below

## 🔐 **Required Secrets**

### **Azure Authentication**

#### `AZURE_CREDENTIALS`
**Description**: JSON object containing Azure service principal credentials
**Source**: Output from `az ad sp create-for-rbac` command
**Format**:
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "your-client-secret",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

#### `AZURE_SUBSCRIPTION_ID`
**Description**: Your Azure subscription ID
**Source**: Azure portal or `az account show --query id --output tsv`
**Example**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

#### `AZURE_TENANT_ID`
**Description**: Your Azure tenant ID
**Source**: Azure portal or `az account show --query tenantId --output tsv`
**Example**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

#### `AZURE_CLIENT_ID`
**Description**: Service principal client ID
**Source**: From the AZURE_CREDENTIALS JSON or Azure portal
**Example**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

#### `AZURE_CLIENT_SECRET`
**Description**: Service principal client secret
**Source**: From the AZURE_CREDENTIALS JSON or Azure portal
**Example**: `your-client-secret-value`

### **Terraform Backend**

#### `TERRAFORM_STORAGE_ACCOUNT`
**Description**: Azure Storage Account name for Terraform state
**Source**: Created during setup (from setup-azure.sh script)
**Example**: `terraformstateabc123`

#### `TERRAFORM_CONTAINER_NAME`
**Description**: Storage container name for Terraform state
**Source**: Always `tfstate`
**Value**: `tfstate`

#### `TERRAFORM_STATE_KEY`
**Description**: Terraform state file name
**Source**: Project-specific
**Value**: `adara-signage.tfstate`

#### `TERRAFORM_RESOURCE_GROUP`
**Description**: Resource group containing Terraform storage
**Source**: Created during setup
**Value**: `rg-terraform-state`

### **Application Configuration**

#### `RESOURCE_GROUP_NAME`
**Description**: Main resource group for application resources
**Source**: From terraform.tfvars
**Example**: `rg-adara-signage-prod`

#### `AZURE_LOCATION`
**Description**: Azure region for deployments
**Source**: From terraform.tfvars
**Example**: `UAE Central`

#### `PROJECT_NAME`
**Description**: Project name prefix for resources
**Source**: From terraform.tfvars
**Example**: `adara-signage`

### **Container Registry**

#### `CONTAINER_REGISTRY_NAME`
**Description**: Azure Container Registry name (without .azurecr.io)
**Source**: Terraform output after first deployment
**Example**: `adarasignageacrabc123`

### **Container Apps**

#### `BACKEND_CONTAINER_APP_NAME`
**Description**: Backend Container App name
**Source**: Terraform output after first deployment
**Example**: `adara-signage-backend`

### **Frontend Configuration**

#### `NEXT_PUBLIC_API_URL`
**Description**: Backend API URL for frontend
**Source**: Terraform output after first deployment
**Example**: `https://adara-signage-backend.kindtree-12345678.uaecentral.azurecontainerapps.io`

#### `AZURE_STATIC_WEB_APPS_API_TOKEN`
**Description**: Deployment token for Azure Static Web Apps
**Source**: Terraform output or Azure portal
**Example**: `long-api-token-string`

#### `FRONTEND_APP_URL`
**Description**: Frontend application URL (for health checks)
**Source**: Terraform output after first deployment
**Example**: `https://wonderful-meadow-12345678.azurestaticapps.net`

## 🔄 **Post-Deployment Secrets Update**

After the initial Terraform deployment, you'll need to update these secrets with the actual values:

1. Run Terraform deployment first
2. Get outputs: `terraform output -json`
3. Update the following secrets with the actual values:
   - `CONTAINER_REGISTRY_NAME`
   - `BACKEND_CONTAINER_APP_NAME`
   - `NEXT_PUBLIC_API_URL`
   - `AZURE_STATIC_WEB_APPS_API_TOKEN`
   - `FRONTEND_APP_URL`

## 📋 **Setup Checklist**

### Initial Setup (Before first deployment):
- [ ] `AZURE_CREDENTIALS`
- [ ] `AZURE_SUBSCRIPTION_ID`
- [ ] `AZURE_TENANT_ID`
- [ ] `AZURE_CLIENT_ID`
- [ ] `AZURE_CLIENT_SECRET`
- [ ] `TERRAFORM_STORAGE_ACCOUNT`
- [ ] `TERRAFORM_CONTAINER_NAME`
- [ ] `TERRAFORM_STATE_KEY`
- [ ] `TERRAFORM_RESOURCE_GROUP`
- [ ] `RESOURCE_GROUP_NAME`
- [ ] `AZURE_LOCATION`
- [ ] `PROJECT_NAME`

### Post-Deployment Update:
- [ ] `CONTAINER_REGISTRY_NAME`
- [ ] `BACKEND_CONTAINER_APP_NAME`
- [ ] `NEXT_PUBLIC_API_URL`
- [ ] `AZURE_STATIC_WEB_APPS_API_TOKEN`
- [ ] `FRONTEND_APP_URL`

## 🔧 **Optional Secrets**

### **Notifications**
#### `SLACK_WEBHOOK_URL`
**Description**: Slack webhook for deployment notifications
**Source**: Slack app configuration
**Example**: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`

#### `TEAMS_WEBHOOK_URL`
**Description**: Microsoft Teams webhook for deployment notifications
**Source**: Teams connector configuration
**Example**: `https://outlook.office.com/webhook/...`

### **External Services**
#### `GEMINI_API_KEY`
**Description**: Google Gemini API key for AI content moderation
**Source**: Google AI Studio
**Example**: `AIza...`

#### `OPENAI_API_KEY`
**Description**: OpenAI API key for AI content moderation
**Source**: OpenAI platform
**Example**: `sk-...`

## 🚨 **Security Best Practices**

1. **Least Privilege**: Ensure service principals have minimum required permissions
2. **Rotation**: Regularly rotate client secrets and API keys
3. **Monitoring**: Monitor secret usage and set up alerts for unauthorized access
4. **Backup**: Keep encrypted backups of critical secrets in a secure location
5. **Environment Separation**: Use different secrets for different environments

## 🔍 **Troubleshooting**

### Common Issues:

#### Authentication Errors:
- Verify `AZURE_CREDENTIALS` JSON format
- Check service principal permissions
- Ensure subscription ID is correct

#### Terraform Backend Errors:
- Verify storage account name and access
- Check resource group exists
- Ensure proper permissions on storage account

#### Deployment Failures:
- Check resource naming conflicts
- Verify location availability
- Check quotas and limits

#### Container Registry Issues:
- Verify registry name format (no special characters)
- Check push/pull permissions
- Ensure managed identity has correct roles

## 📞 **Getting Help**

If you encounter issues with secret configuration:

1. Check the GitHub Actions logs for specific error messages
2. Verify all secrets are correctly named and formatted
3. Test Azure CLI access locally with the same credentials
4. Consult the Azure documentation for service-specific requirements

Remember to never commit secrets to your repository or share them publicly!