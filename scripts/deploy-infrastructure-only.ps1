# Deploy Infrastructure Only - Skips application builds
# This script runs only the Terraform deployment

$ErrorActionPreference = "Stop"

# Utility functions
function Write-Status { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Header { param([string]$Message) Write-Host "=" * 50 -ForegroundColor Blue; Write-Host $Message -ForegroundColor Blue; Write-Host "=" * 50 -ForegroundColor Blue }

Write-Header "Infrastructure-Only Deployment"

# Check if terraform.tfvars exists
if (!(Test-Path ".\terraform\terraform.tfvars")) {
    Write-Error "terraform.tfvars not found. Please run the full deploy script first."
    exit 1
}

# Check if we're in the right directory
if (!(Test-Path ".\terraform")) {
    Write-Error "Please run this script from the project root directory"
    exit 1
}

try {
    Push-Location ".\terraform"

    Write-Status "Initializing Terraform..."
    terraform init

    Write-Status "Validating Terraform configuration..."
    terraform validate

    Write-Status "Planning deployment..."
    terraform plan -out=tfplan

    Write-Host ""
    Write-Host "Terraform plan completed successfully!" -ForegroundColor Green
    Write-Host ""
    $confirm = Read-Host "Do you want to apply this plan? (y/N)"

    if ($confirm -match "^[Yy]$") {
        Write-Status "Applying Terraform plan..."
        terraform apply tfplan

        Write-Status "Getting outputs..."
        terraform output -json | Out-File "terraform-outputs.json" -Encoding utf8

        Write-Header "Deployment Complete!"
        Write-Host ""
        Write-Host "Infrastructure deployed successfully!" -ForegroundColor Green
        Write-Host "Outputs saved to: terraform-outputs.json" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Configure GitHub repository secrets with the Terraform outputs"
        Write-Host "2. Push your code to trigger GitHub Actions for application deployment"
        Write-Host "3. Run health checks: .\scripts\check-health.ps1"
    }
    else {
        Write-Status "Deployment cancelled"
        Remove-Item "tfplan" -ErrorAction SilentlyContinue
    }
}
catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    exit 1
}
finally {
    Pop-Location
    Remove-Item ".\terraform\tfplan" -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host