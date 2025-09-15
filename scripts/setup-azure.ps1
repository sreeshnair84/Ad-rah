# Azure Setup Script for Adara Screen Digital Signage Platform
# This script sets up the necessary Azure resources for Terraform backend

param(
    [string]$SubscriptionId = "",
    [string]$ResourceGroupName = "rg-terraform-state",
    [string]$Location = "UAE Central",
    [string]$StorageAccountPrefix = "terraformstate",
    [string]$ContainerName = "tfstate",
    [string]$ServicePrincipalName = "adara-signage-github-actions"
)

$ErrorActionPreference = "Continue"

# Utility functions
function Write-Status { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Header { param([string]$Message) Write-Host "=" * 50 -ForegroundColor Blue; Write-Host $Message -ForegroundColor Blue; Write-Host "=" * 50 -ForegroundColor Blue }

# Check Azure CLI and authentication
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."

    if (!(Get-Command az -ErrorAction SilentlyContinue)) {
        Write-Error "Azure CLI not found. Please install from: https://aka.ms/installazurecliwindows"
        return $false
    }

    try {
        $account = az account show --output json 2>$null | ConvertFrom-Json
        if (!$account) {
            Write-Status "Please authenticate to Azure..."
            az login
            $account = az account show --output json | ConvertFrom-Json
        }
        Write-Status "Logged in as: $($account.user.name)"
        return $true
    }
    catch {
        Write-Error "Azure authentication failed"
        return $false
    }
}

# Generate unique storage account name
function New-StorageAccountName {
    $suffix = -join ((1..6) | ForEach { [char]((97..122) + (48..57) | Get-Random) })
    return $StorageAccountPrefix + $suffix
}

# Create resource group
function New-ResourceGroup {
    param([string]$Name, [string]$Location)

    Write-Status "Creating resource group: $Name"
    try {
        $existing = az group show --name $Name --output json 2>$null
        if ($existing) {
            Write-Warning "Resource group already exists"
            return $true
        }

        az group create --name $Name --location $Location --output none
        Write-Status "Resource group created successfully"
        return $true
    }
    catch {
        Write-Error "Failed to create resource group: $($_.Exception.Message)"
        return $false
    }
}

# Create storage account
function New-StorageAccount {
    param([string]$Name, [string]$ResourceGroup, [string]$Location)

    Write-Status "Creating storage account: $Name"
    try {
        $existing = az storage account show --name $Name --resource-group $ResourceGroup --output json 2>$null
        if ($existing) {
            Write-Warning "Storage account already exists"
        }
        else {
            az storage account create --name $Name --resource-group $ResourceGroup --location $Location --sku Standard_LRS --allow-blob-public-access false --output none
            Write-Status "Storage account created successfully"
        }

        $key = az storage account keys list --account-name $Name --resource-group $ResourceGroup --query '[0].value' --output tsv
        return $key
    }
    catch {
        Write-Error "Failed to create storage account: $($_.Exception.Message)"
        return $null
    }
}

# Create storage container
function New-StorageContainer {
    param([string]$ContainerName, [string]$StorageAccount, [string]$StorageKey)

    Write-Status "Creating storage container: $ContainerName"
    try {
        $exists = az storage container exists --name $ContainerName --account-name $StorageAccount --account-key $StorageKey --query exists --output tsv
        if ($exists -eq "true") {
            Write-Warning "Container already exists"
            return $true
        }

        az storage container create --name $ContainerName --account-name $StorageAccount --account-key $StorageKey --public-access off --output none
        Write-Status "Storage container created successfully"
        return $true
    }
    catch {
        Write-Error "Failed to create storage container: $($_.Exception.Message)"
        return $false
    }
}

# Create service principal
function New-ServicePrincipal {
    param([string]$Name, [string]$SubscriptionId)

    Write-Status "Creating service principal: $Name"
    try {
        # Check if exists
        $existing = az ad sp list --display-name $Name --output json 2>$null | ConvertFrom-Json
        if ($existing -and $existing.Count -gt 0) {
            Write-Warning "Service principal already exists. Resetting credentials..."
            $reset = az ad sp credential reset --id $existing[0].appId --output json | ConvertFrom-Json
            return @{
                clientId = $existing[0].appId
                clientSecret = $reset.password
                subscriptionId = $SubscriptionId
                tenantId = $reset.tenant
            } | ConvertTo-Json
        }

        # Create new
        $sp = az ad sp create-for-rbac --name $Name --role contributor --scopes "/subscriptions/$SubscriptionId" --output json | ConvertFrom-Json
        return @{
            clientId = $sp.appId
            clientSecret = $sp.password
            subscriptionId = $SubscriptionId
            tenantId = $sp.tenant
        } | ConvertTo-Json
    }
    catch {
        Write-Error "Failed to create service principal: $($_.Exception.Message)"
        return $null
    }
}

# Main execution
function Start-Setup {
    Write-Header "Azure Setup for Adara Screen Digital Signage Platform"

    if (!(Test-Prerequisites)) { exit 1 }

    # Get subscription
    if (!$SubscriptionId) {
        $SubscriptionId = Read-Host "Enter Azure Subscription ID (or press Enter for current)"
        if (!$SubscriptionId) {
            $SubscriptionId = az account show --query id --output tsv
        }
    }

    az account set --subscription $SubscriptionId
    Write-Status "Using subscription: $SubscriptionId"

    # Generate names
    $storageAccountName = New-StorageAccountName
    Write-Status "Generated storage account name: $storageAccountName"

    # Create resources
    if (!(New-ResourceGroup -Name $ResourceGroupName -Location $Location)) { exit 1 }

    $storageKey = New-StorageAccount -Name $storageAccountName -ResourceGroup $ResourceGroupName -Location $Location
    if (!$storageKey) { exit 1 }

    if (!(New-StorageContainer -ContainerName $ContainerName -StorageAccount $storageAccountName -StorageKey $storageKey)) { exit 1 }

    $spJson = New-ServicePrincipal -Name $ServicePrincipalName -SubscriptionId $SubscriptionId

    # Display results
    Write-Header "Setup Complete!"
    Write-Host ""
    Write-Host "GitHub Repository Secrets:" -ForegroundColor Green
    Write-Host "AZURE_CREDENTIALS:"
    Write-Host $spJson
    Write-Host ""
    Write-Host "TERRAFORM_STORAGE_ACCOUNT: $storageAccountName"
    Write-Host "TERRAFORM_CONTAINER_NAME: $ContainerName"
    Write-Host "TERRAFORM_STATE_KEY: adara-signage.tfstate"
    Write-Host "TERRAFORM_RESOURCE_GROUP: $ResourceGroupName"
    Write-Host "AZURE_SUBSCRIPTION_ID: $SubscriptionId"
    Write-Host ""
    Write-Host "Terraform Backend Config:" -ForegroundColor Green
    Write-Host "terraform {"
    Write-Host "  backend `"azurerm`" {"
    Write-Host "    storage_account_name = `"$storageAccountName`""
    Write-Host "    container_name       = `"$ContainerName`""
    Write-Host "    key                 = `"adara-signage.tfstate`""
    Write-Host "    resource_group_name = `"$ResourceGroupName`""
    Write-Host "  }"
    Write-Host "}"
    Write-Host ""
    Write-Host "Next: Add the above secrets to your GitHub repository" -ForegroundColor Yellow
}

try {
    Start-Setup
}
catch {
    Write-Error "Setup failed: $($_.Exception.Message)"
    exit 1
}

Read-Host "Press Enter to exit"