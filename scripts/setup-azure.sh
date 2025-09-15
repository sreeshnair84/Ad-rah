#!/bin/bash

# Azure Setup Script for Adara Screen Digital Signage Platform
# This script sets up the necessary Azure resources for Terraform backend

set -e  # Exit on any error

# Configuration
SUBSCRIPTION_ID=""
RESOURCE_GROUP_NAME="rg-terraform-state"
LOCATION="UAE Central"
STORAGE_ACCOUNT_PREFIX="terraformstate"
CONTAINER_NAME="tfstate"
SP_NAME="adara-signage-github-actions"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

# Check if Azure CLI is installed
check_azure_cli() {
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        print_error "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    print_status "Azure CLI is installed"
}

# Check if user is logged in
check_azure_login() {
    if ! az account show &> /dev/null; then
        print_error "You are not logged in to Azure CLI"
        print_status "Running: az login"
        az login
    fi
    print_status "Logged in to Azure CLI"
}

# Get subscription ID if not provided
get_subscription_id() {
    if [ -z "$SUBSCRIPTION_ID" ]; then
        print_status "Getting current subscription ID..."
        SUBSCRIPTION_ID=$(az account show --query id --output tsv)
    fi

    print_status "Using subscription: $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
}

# Generate unique storage account name
generate_storage_name() {
    RANDOM_SUFFIX=$(openssl rand -hex 3)
    STORAGE_ACCOUNT_NAME="${STORAGE_ACCOUNT_PREFIX}${RANDOM_SUFFIX}"
    print_status "Generated storage account name: $STORAGE_ACCOUNT_NAME"
}

# Create resource group for Terraform state
create_resource_group() {
    print_header "Creating Resource Group"

    if az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
        print_warning "Resource group '$RESOURCE_GROUP_NAME' already exists"
    else
        print_status "Creating resource group: $RESOURCE_GROUP_NAME"
        az group create \
            --name "$RESOURCE_GROUP_NAME" \
            --location "$LOCATION" \
            --output table
        print_status "Resource group created successfully"
    fi
}

# Create storage account for Terraform state
create_storage_account() {
    print_header "Creating Storage Account"

    if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" &> /dev/null; then
        print_warning "Storage account '$STORAGE_ACCOUNT_NAME' already exists"
    else
        print_status "Creating storage account: $STORAGE_ACCOUNT_NAME"
        az storage account create \
            --name "$STORAGE_ACCOUNT_NAME" \
            --resource-group "$RESOURCE_GROUP_NAME" \
            --location "$LOCATION" \
            --sku Standard_LRS \
            --allow-blob-public-access false \
            --min-tls-version TLS1_2 \
            --output table
        print_status "Storage account created successfully"
    fi

    # Get storage account key
    STORAGE_KEY=$(az storage account keys list \
        --account-name "$STORAGE_ACCOUNT_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --query '[0].value' \
        --output tsv)
}

# Create storage container
create_storage_container() {
    print_header "Creating Storage Container"

    if az storage container exists \
        --name "$CONTAINER_NAME" \
        --account-name "$STORAGE_ACCOUNT_NAME" \
        --account-key "$STORAGE_KEY" \
        --query exists --output tsv | grep -q true; then
        print_warning "Storage container '$CONTAINER_NAME' already exists"
    else
        print_status "Creating storage container: $CONTAINER_NAME"
        az storage container create \
            --name "$CONTAINER_NAME" \
            --account-name "$STORAGE_ACCOUNT_NAME" \
            --account-key "$STORAGE_KEY" \
            --public-access off \
            --output table
        print_status "Storage container created successfully"
    fi
}

# Create service principal for GitHub Actions
create_service_principal() {
    print_header "Creating Service Principal"

    print_status "Creating service principal: $SP_NAME"
    SP_JSON=$(az ad sp create-for-rbac \
        --name "$SP_NAME" \
        --role contributor \
        --scopes "/subscriptions/$SUBSCRIPTION_ID" \
        --sdk-auth)

    print_status "Service principal created successfully"

    # Extract values for display
    CLIENT_ID=$(echo "$SP_JSON" | jq -r '.clientId')
    TENANT_ID=$(echo "$SP_JSON" | jq -r '.tenantId')

    print_status "Client ID: $CLIENT_ID"
    print_status "Tenant ID: $TENANT_ID"
}

# Display final configuration
display_configuration() {
    print_header "Azure Setup Complete!"

    echo -e "${GREEN}Terraform Backend Configuration:${NC}"
    echo "Storage Account: $STORAGE_ACCOUNT_NAME"
    echo "Resource Group: $RESOURCE_GROUP_NAME"
    echo "Container: $CONTAINER_NAME"
    echo "Location: $LOCATION"
    echo ""

    echo -e "${GREEN}Add these secrets to your GitHub repository:${NC}"
    echo ""
    echo -e "${YELLOW}AZURE_CREDENTIALS:${NC}"
    echo "$SP_JSON"
    echo ""
    echo -e "${YELLOW}TERRAFORM_STORAGE_ACCOUNT:${NC} $STORAGE_ACCOUNT_NAME"
    echo -e "${YELLOW}TERRAFORM_CONTAINER_NAME:${NC} $CONTAINER_NAME"
    echo -e "${YELLOW}TERRAFORM_STATE_KEY:${NC} adara-signage.tfstate"
    echo -e "${YELLOW}TERRAFORM_RESOURCE_GROUP:${NC} $RESOURCE_GROUP_NAME"
    echo -e "${YELLOW}AZURE_SUBSCRIPTION_ID:${NC} $SUBSCRIPTION_ID"
    echo ""

    echo -e "${GREEN}Terraform Backend Configuration (add to your backend config):${NC}"
    echo "terraform {"
    echo "  backend \"azurerm\" {"
    echo "    storage_account_name = \"$STORAGE_ACCOUNT_NAME\""
    echo "    container_name       = \"$CONTAINER_NAME\""
    echo "    key                 = \"adara-signage.tfstate\""
    echo "    resource_group_name = \"$RESOURCE_GROUP_NAME\""
    echo "  }"
    echo "}"
    echo ""

    print_status "Setup completed successfully!"
    print_warning "Make sure to save the service principal credentials securely"
    print_warning "Add all the displayed secrets to your GitHub repository"
}

# Cleanup function
cleanup() {
    print_warning "Script interrupted. Cleaning up..."
    exit 1
}

# Trap interrupt signals
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    print_header "Azure Setup for Adara Screen Digital Signage Platform"

    # Prompt for subscription ID if not set
    if [ -z "$SUBSCRIPTION_ID" ]; then
        read -p "Enter your Azure Subscription ID (or press Enter to use current): " input_subscription
        if [ -n "$input_subscription" ]; then
            SUBSCRIPTION_ID="$input_subscription"
        fi
    fi

    check_azure_cli
    check_azure_login
    get_subscription_id
    generate_storage_name
    create_resource_group
    create_storage_account
    create_storage_container
    create_service_principal
    display_configuration
}

# Run main function
main "$@"