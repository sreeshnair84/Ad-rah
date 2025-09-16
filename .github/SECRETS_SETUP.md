# GitHub Secrets Configuration

This document outlines all the GitHub repository secrets required for the CI/CD pipelines to work correctly.

## Repository Secrets

### Required for All Workflows

#### Azure Authentication
- `AZURE_CREDENTIALS` - Azure service principal credentials in JSON format:
  ```json
  {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "subscriptionId": "your-subscription-id",
    "tenantId": "your-tenant-id"
  }
  ```

#### Azure Infrastructure
- `RESOURCE_GROUP_NAME` - Azure resource group name
- `AZURE_LOCATION` - Azure region (e.g., "eastus", "westus2")
- `PROJECT_NAME` - Project name used for resource naming

### Backend Deployment Secrets

#### Container Registry
- `CONTAINER_REGISTRY_NAME` - Azure Container Registry name (without .azurecr.io)
- `BACKEND_CONTAINER_APP_NAME` - Azure Container App name for backend

### Frontend Deployment Secrets

#### Static Web App
- `AZURE_STATIC_WEB_APPS_API_TOKEN` - Azure Static Web Apps deployment token
- `NEXT_PUBLIC_API_URL` - Backend API URL for frontend (e.g., "https://your-backend.azurecontainerapps.io")
- `FRONTEND_APP_URL` - Frontend URL for health checks (optional)

### Infrastructure Deployment Secrets

#### Terraform Backend
- `TERRAFORM_STORAGE_ACCOUNT` - Storage account name for Terraform state
- `TERRAFORM_CONTAINER_NAME` - Blob container name for state (usually "tfstate")
- `TERRAFORM_STATE_KEY` - State file name (e.g., "terraform.tfstate")
- `TERRAFORM_RESOURCE_GROUP` - Resource group containing the storage account

## Environment Variables

### Production Environment
Create a production environment in your repository settings with these secrets configured.

### Development/Test Environment Variables
The following are set automatically in CI:
- `MONGO_URI` - MongoDB connection string (set in workflows)
- `SECRET_KEY` - Application secret key (set in workflows)
- `JWT_SECRET_KEY` - JWT signing key (set in workflows)
- `ENVIRONMENT` - Environment name (set to "test" in CI)
- `NODE_ENV` - Node.js environment (set to "production" for builds)

## Setup Instructions

### 1. Azure Service Principal Setup
```bash
# Create service principal
az ad sp create-for-rbac --name "github-actions-sp" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth

# Copy the output JSON to AZURE_CREDENTIALS secret
```

### 2. Azure Static Web Apps Token
```bash
# Get deployment token from Azure Portal
# Navigate to: Static Web Apps → your-app → Manage deployment token
# Copy token to AZURE_STATIC_WEB_APPS_API_TOKEN secret
```

### 3. Container Registry Setup
```bash
# Get registry name
az acr list --query "[].name" -o table

# Ensure service principal has AcrPush role
az role assignment create \
  --assignee {service-principal-id} \
  --role AcrPush \
  --scope /subscriptions/{subscription-id}/resourceGroups/{rg-name}/providers/Microsoft.ContainerRegistry/registries/{acr-name}
```

### 4. Terraform Backend Setup
```bash
# Create storage account for state
az storage account create \
  --name {storage-account-name} \
  --resource-group {resource-group} \
  --location {location} \
  --sku Standard_LRS

# Create container
az storage container create \
  --name tfstate \
  --account-name {storage-account-name}
```

## Troubleshooting

### Common Issues

1. **AZURE_CREDENTIALS format** - Must be valid JSON with all required fields
2. **Missing permissions** - Service principal needs Contributor role on subscription/resource group
3. **Token expiry** - Static Web Apps tokens expire and need renewal
4. **Container registry access** - Ensure ACR allows access from service principal

### Validation Commands

```bash
# Test Azure credentials
az login --service-principal -u $clientId -p $clientSecret --tenant $tenantId

# Test container registry access
az acr login --name {registry-name}

# Test Static Web Apps token
# (Token validation is done during deployment)
```

## Security Best Practices

1. **Rotate secrets regularly** - Especially service principal secrets
2. **Use least privilege** - Grant minimal required permissions
3. **Monitor access** - Review Azure Activity Logs for unauthorized access
4. **Environment separation** - Use different secrets for prod/staging/dev
5. **Secret expiry** - Set expiration dates where possible

## Support

If you encounter issues with secrets configuration:
1. Check Azure Activity Logs for authentication failures
2. Verify secret format and content
3. Ensure all required permissions are granted
4. Review GitHub Actions logs for specific error messages