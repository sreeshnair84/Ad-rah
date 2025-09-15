# Azure Management Script for Adara Screen Digital Signage Platform
# This script provides management operations for deployed Azure resources

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("status", "restart", "scale", "logs", "cost", "cleanup", "backup", "update")]
    [string]$Action,

    [string]$ResourceGroup = "",
    [string]$ServiceName = "",
    [int]$ScaleReplicas = 1,
    [int]$LogLines = 100,
    [string]$ConfigFile = ".\terraform\terraform-outputs.json",
    [switch]$Force,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Utility functions
function Write-Status { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Header { param([string]$Message) Write-Host "=" * 50 -ForegroundColor Blue; Write-Host $Message -ForegroundColor Blue; Write-Host "=" * 50 -ForegroundColor Blue }
function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Failed { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }

# Get Azure resources from Terraform outputs
function Get-AzureResources {
    if (!(Test-Path $ConfigFile)) {
        Write-Error "Configuration file not found: $ConfigFile"
        return $null
    }

    try {
        $outputs = Get-Content $ConfigFile | ConvertFrom-Json
        return @{
            ResourceGroup = $outputs.resource_group_name.value
            ContainerAppName = ($outputs.PSObject.Properties | Where-Object { $_.Name -like "*backend*" -and $_.Name -like "*name*" } | Select-Object -First 1).Value
            FrontendName = ($outputs.PSObject.Properties | Where-Object { $_.Name -like "*frontend*" -and $_.Name -like "*name*" } | Select-Object -First 1).Value
            StorageAccount = $outputs.storage_account_name.value
            ContainerRegistry = $outputs.container_registry_login_server.value
            CosmosDb = ($outputs.PSObject.Properties | Where-Object { $_.Name -like "*cosmos*" -and $_.Name -like "*name*" } | Select-Object -First 1).Value
        }
    }
    catch {
        Write-Error "Failed to parse configuration: $($_.Exception.Message)"
        return $null
    }
}

# Get service status
function Get-ServiceStatus {
    param([hashtable]$Resources)

    Write-Header "Service Status"

    # Container App status
    if ($Resources.ContainerAppName) {
        Write-Status "Checking Container App status..."
        try {
            $containerApp = az containerapp show --name $Resources.ContainerAppName --resource-group $Resources.ResourceGroup --output json | ConvertFrom-Json

            Write-Host "Container App: $($Resources.ContainerAppName)" -ForegroundColor Cyan
            Write-Host "  Status: $($containerApp.properties.runningStatus)" -ForegroundColor Green
            Write-Host "  Replicas: $($containerApp.properties.template.scale.minReplicas) - $($containerApp.properties.template.scale.maxReplicas)"
            Write-Host "  CPU: $($containerApp.properties.template.containers[0].resources.cpu)"
            Write-Host "  Memory: $($containerApp.properties.template.containers[0].resources.memory)"
            Write-Host "  URL: https://$($containerApp.properties.configuration.ingress.fqdn)"
            Write-Host ""
        }
        catch {
            Write-Warning "Failed to get Container App status: $($_.Exception.Message)"
        }
    }

    # Static Web App status (if applicable)
    if ($Resources.FrontendName) {
        Write-Status "Checking Static Web App status..."
        try {
            $staticApp = az staticwebapp show --name $Resources.FrontendName --resource-group $Resources.ResourceGroup --output json | ConvertFrom-Json

            Write-Host "Static Web App: $($Resources.FrontendName)" -ForegroundColor Cyan
            Write-Host "  Status: $($staticApp.repositoryUrl ? 'Connected' : 'Not Connected')"
            Write-Host "  URL: https://$($staticApp.defaultHostname)"
            Write-Host ""
        }
        catch {
            Write-Warning "Failed to get Static Web App status: $($_.Exception.Message)"
        }
    }

    # Storage Account status
    if ($Resources.StorageAccount) {
        Write-Status "Checking Storage Account status..."
        try {
            $storage = az storage account show --name $Resources.StorageAccount --resource-group $Resources.ResourceGroup --output json | ConvertFrom-Json

            Write-Host "Storage Account: $($Resources.StorageAccount)" -ForegroundColor Cyan
            Write-Host "  Status: $($storage.statusOfPrimary)"
            Write-Host "  Tier: $($storage.accountKind)"
            Write-Host "  Replication: $($storage.replication.type)"
            Write-Host ""
        }
        catch {
            Write-Warning "Failed to get Storage Account status: $($_.Exception.Message)"
        }
    }

    # Cosmos DB status
    if ($Resources.CosmosDb) {
        Write-Status "Checking Cosmos DB status..."
        try {
            $cosmos = az cosmosdb show --name $Resources.CosmosDb --resource-group $Resources.ResourceGroup --output json | ConvertFrom-Json

            Write-Host "Cosmos DB: $($Resources.CosmosDb)" -ForegroundColor Cyan
            Write-Host "  Status: $($cosmos.provisioningState)"
            Write-Host "  Locations: $($cosmos.locations.Count)"
            Write-Host "  Backup Policy: $($cosmos.backupPolicy.type)"
            Write-Host ""
        }
        catch {
            Write-Warning "Failed to get Cosmos DB status: $($_.Exception.Message)"
        }
    }
}

# Restart services
function Restart-Services {
    param([hashtable]$Resources)

    Write-Header "Restarting Services"

    if (!$Force) {
        $confirm = Read-Host "Are you sure you want to restart services? This will cause downtime. (y/N)"
        if ($confirm -notmatch "^[Yy]$") {
            Write-Status "Operation cancelled"
            return
        }
    }

    # Restart Container App
    if ($Resources.ContainerAppName) {
        Write-Status "Restarting Container App: $($Resources.ContainerAppName)..."
        try {
            az containerapp revision restart --name $Resources.ContainerAppName --resource-group $Resources.ResourceGroup
            Write-Success "Container App restarted successfully"
        }
        catch {
            Write-Error "Failed to restart Container App: $($_.Exception.Message)"
        }
    }

    Write-Status "Services restart completed"
}

# Scale services
function Set-ServiceScale {
    param(
        [hashtable]$Resources,
        [int]$Replicas
    )

    Write-Header "Scaling Services"

    if ($Resources.ContainerAppName) {
        Write-Status "Scaling Container App to $Replicas replicas..."
        try {
            az containerapp update --name $Resources.ContainerAppName --resource-group $Resources.ResourceGroup --min-replicas $Replicas --max-replicas ([math]::Max($Replicas * 2, 10))
            Write-Success "Container App scaled successfully"
        }
        catch {
            Write-Error "Failed to scale Container App: $($_.Exception.Message)"
        }
    }
}

# Get service logs
function Get-ServiceLogs {
    param(
        [hashtable]$Resources,
        [int]$Lines
    )

    Write-Header "Service Logs"

    if ($Resources.ContainerAppName) {
        Write-Status "Fetching Container App logs (last $Lines lines)..."
        try {
            $logs = az containerapp logs show --name $Resources.ContainerAppName --resource-group $Resources.ResourceGroup --tail $Lines --output table
            Write-Host $logs
        }
        catch {
            Write-Error "Failed to get Container App logs: $($_.Exception.Message)"
        }
    }
}

# Get cost information
function Get-CostAnalysis {
    param([hashtable]$Resources)

    Write-Header "Cost Analysis"

    try {
        Write-Status "Fetching cost information for resource group: $($Resources.ResourceGroup)..."

        # Get current month costs
        $startDate = (Get-Date -Day 1).ToString("yyyy-MM-dd")
        $endDate = (Get-Date).ToString("yyyy-MM-dd")

        $costs = az consumption usage list --start-date $startDate --end-date $endDate --output json | ConvertFrom-Json

        if ($costs) {
            $totalCost = ($costs | Measure-Object -Property pretaxCost -Sum).Sum
            $avgDailyCost = $totalCost / (Get-Date).Day

            Write-Host "Cost Summary (Current Month):" -ForegroundColor Cyan
            Write-Host "  Total Cost: `$$([math]::Round($totalCost, 2))"
            Write-Host "  Average Daily Cost: `$$([math]::Round($avgDailyCost, 2))"
            Write-Host "  Projected Monthly Cost: `$$([math]::Round($avgDailyCost * 30, 2))"
            Write-Host ""

            # Top services by cost
            $topServices = $costs | Group-Object -Property meterName | Sort-Object { ($_.Group | Measure-Object -Property pretaxCost -Sum).Sum } -Descending | Select-Object -First 5

            Write-Host "Top 5 Services by Cost:" -ForegroundColor Cyan
            foreach ($service in $topServices) {
                $serviceCost = ($service.Group | Measure-Object -Property pretaxCost -Sum).Sum
                Write-Host "  $($service.Name): `$$([math]::Round($serviceCost, 2))"
            }
        }
        else {
            Write-Warning "No cost data available for the specified period"
        }
    }
    catch {
        Write-Warning "Failed to get cost information: $($_.Exception.Message)"
        Write-Status "Make sure you have proper permissions to access billing information"
    }
}

# Cleanup old resources
function Start-Cleanup {
    param([hashtable]$Resources)

    Write-Header "Resource Cleanup"

    if (!$Force) {
        $confirm = Read-Host "This will clean up old resources. Continue? (y/N)"
        if ($confirm -notmatch "^[Yy]$") {
            Write-Status "Cleanup cancelled"
            return
        }
    }

    # Clean up old container images
    if ($Resources.ContainerRegistry) {
        Write-Status "Cleaning up old container images..."
        try {
            $repositories = az acr repository list --name ($Resources.ContainerRegistry -replace ".azurecr.io", "") --output json | ConvertFrom-Json

            foreach ($repo in $repositories) {
                # Keep only the last 5 images
                $tags = az acr repository show-tags --name ($Resources.ContainerRegistry -replace ".azurecr.io", "") --repository $repo --orderby time_desc --output json | ConvertFrom-Json

                if ($tags.Count -gt 5) {
                    $tagsToDelete = $tags | Select-Object -Skip 5
                    foreach ($tag in $tagsToDelete) {
                        Write-Status "Deleting old image: $repo`:$($tag.name)"
                        az acr repository delete --name ($Resources.ContainerRegistry -replace ".azurecr.io", "") --image "$repo`:$($tag.name)" --yes
                    }
                }
            }
        }
        catch {
            Write-Warning "Failed to cleanup container images: $($_.Exception.Message)"
        }
    }

    # Clean up old storage blobs (optional)
    if ($Resources.StorageAccount) {
        Write-Status "Cleaning up old storage blobs..."
        # This would require more specific logic based on your storage structure
        Write-Warning "Storage cleanup not implemented - please configure lifecycle management policies"
    }

    Write-Success "Cleanup completed"
}

# Backup configuration
function Start-Backup {
    param([hashtable]$Resources)

    Write-Header "Configuration Backup"

    $backupDir = ".\backups\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-DirectoryIfNotExists -Path $backupDir

    # Backup Terraform outputs
    if (Test-Path $ConfigFile) {
        Copy-Item $ConfigFile (Join-Path $backupDir "terraform-outputs.json")
        Write-Status "Terraform outputs backed up"
    }

    # Backup Cosmos DB (create a restore point)
    if ($Resources.CosmosDb) {
        Write-Status "Creating Cosmos DB backup reference..."
        try {
            $cosmos = az cosmosdb show --name $Resources.CosmosDb --resource-group $Resources.ResourceGroup --output json | ConvertFrom-Json
            $backupInfo = @{
                DatabaseName = $Resources.CosmosDb
                BackupTime = Get-Date -Format "o"
                BackupPolicy = $cosmos.backupPolicy
            }
            $backupInfo | ConvertTo-Json | Out-File (Join-Path $backupDir "cosmos-backup-info.json")
        }
        catch {
            Write-Warning "Failed to create Cosmos DB backup reference: $($_.Exception.Message)"
        }
    }

    Write-Success "Backup completed to: $backupDir"
}

# Update services
function Update-Services {
    param([hashtable]$Resources)

    Write-Header "Updating Services"

    Write-Status "Service updates should be handled through GitHub Actions"
    Write-Status "To update services:"
    Write-Host "  1. Push changes to your Git repository" -ForegroundColor Yellow
    Write-Host "  2. GitHub Actions will automatically deploy updates" -ForegroundColor Yellow
    Write-Host "  3. Use 'status' action to verify updates" -ForegroundColor Yellow
    Write-Host ""
    Write-Status "For manual updates, use Azure CLI or Azure Portal"
}

# Main execution
function Start-Management {
    Write-Header "Azure Resource Management - $($Action.ToUpper())"

    # Test Azure authentication
    $auth = Test-AzureAuth
    if (!$auth.Authenticated) {
        Write-Error "Not authenticated to Azure. Please run: az login"
        return
    }

    Write-Status "Authenticated as: $($auth.Account)"

    # Get Azure resources
    $resources = Get-AzureResources
    if (!$resources) {
        return
    }

    # Override resource group if specified
    if ($ResourceGroup) {
        $resources.ResourceGroup = $ResourceGroup
    }

    Write-Status "Using Resource Group: $($resources.ResourceGroup)"

    # Execute action
    switch ($Action) {
        "status" {
            Get-ServiceStatus -Resources $resources
        }
        "restart" {
            Restart-Services -Resources $resources
        }
        "scale" {
            Set-ServiceScale -Resources $resources -Replicas $ScaleReplicas
        }
        "logs" {
            Get-ServiceLogs -Resources $resources -Lines $LogLines
        }
        "cost" {
            Get-CostAnalysis -Resources $resources
        }
        "cleanup" {
            Start-Cleanup -Resources $resources
        }
        "backup" {
            Start-Backup -Resources $resources
        }
        "update" {
            Update-Services -Resources $resources
        }
    }
}

# Show help
function Show-Help {
    Write-Host "Azure Management Script for Adara Screen Digital Signage Platform" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Usage: .\manage-azure.ps1 -Action <action> [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Yellow
    Write-Host "  status    - Show status of all services"
    Write-Host "  restart   - Restart services (causes downtime)"
    Write-Host "  scale     - Scale services up/down"
    Write-Host "  logs      - View service logs"
    Write-Host "  cost      - Show cost analysis"
    Write-Host "  cleanup   - Clean up old resources"
    Write-Host "  backup    - Backup configuration"
    Write-Host "  update    - Update services (via GitHub Actions)"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -ResourceGroup  <name>     Override resource group"
    Write-Host "  -ServiceName    <name>     Target specific service"
    Write-Host "  -ScaleReplicas  <number>   Number of replicas for scaling (default: 1)"
    Write-Host "  -LogLines       <number>   Number of log lines to show (default: 100)"
    Write-Host "  -ConfigFile     <path>     Terraform outputs file (default: .\terraform\terraform-outputs.json)"
    Write-Host "  -Force                     Skip confirmation prompts"
    Write-Host "  -Verbose                   Show detailed output"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\manage-azure.ps1 -Action status"
    Write-Host "  .\manage-azure.ps1 -Action scale -ScaleReplicas 3"
    Write-Host "  .\manage-azure.ps1 -Action restart -Force"
    Write-Host "  .\manage-azure.ps1 -Action logs -LogLines 50"
}

# Main execution
try {
    if (!$Action -or $Action -eq "help") {
        Show-Help
    }
    else {
        Start-Management
    }
}
catch {
    Write-Error "Management operation failed: $($_.Exception.Message)"
    if ($Verbose) {
        Write-Error "Stack trace: $($_.ScriptStackTrace)"
    }
    exit 1
}