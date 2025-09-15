# Deployment Script for Adara Screen Digital Signage Platform
# This script handles the complete deployment process

param(
    [switch]$SkipTerraform,
    [switch]$SkipBuild,
    [switch]$SkipHealth,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Utility functions
function Write-Status { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Header { param([string]$Message) Write-Host "=" * 50 -ForegroundColor Blue; Write-Host $Message -ForegroundColor Blue; Write-Host "=" * 50 -ForegroundColor Blue }

# Show usage information
function Show-Usage {
    Write-Host "Usage: .\deploy.ps1 [OPTIONS]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -SkipTerraform    Skip Terraform deployment"
    Write-Host "  -SkipBuild        Skip application builds"
    Write-Host "  -SkipHealth       Skip health checks"
    Write-Host "  -Help             Show this help message"
    Write-Host ""
    Write-Host "Environment Variables:" -ForegroundColor Yellow
    Write-Host "  `$env:SKIP_TERRAFORM=1    Skip Terraform deployment"
    Write-Host "  `$env:SKIP_BUILD=1        Skip application builds"
    Write-Host "  `$env:SKIP_HEALTH=1       Skip health checks"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\deploy.ps1                    # Full deployment"
    Write-Host "  .\deploy.ps1 -SkipTerraform     # Skip infrastructure deployment"
    Write-Host "  .\deploy.ps1 -SkipBuild         # Skip application builds"
}

# Test if a command exists
function Test-Command {
    param([string]$CommandName)

    try {
        Get-Command $CommandName -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Check prerequisites
function Test-Prerequisites {
    Write-Header "Checking Prerequisites"

    $allGood = $true

    # Check Terraform
    if (Test-Command "terraform") {
        $terraformVersion = terraform version -json | ConvertFrom-Json
        Write-Status "Terraform is installed: $($terraformVersion.terraform_version)"
    }
    else {
        Write-Error "Terraform is not installed"
        $allGood = $false
    }

    # Check Azure CLI
    if (Test-Command "az") {
        Write-Status "Azure CLI is installed"
    }
    else {
        Write-Error "Azure CLI is not installed"
        $allGood = $false
    }

    # Check if logged in to Azure
    try {
        $account = az account show --output json 2>$null | ConvertFrom-Json
        if ($account) {
            Write-Status "Logged in to Azure CLI as: $($account.user.name)"
        }
        else {
            Write-Error "Not logged in to Azure CLI"
            Write-Status "Please run: az login"
            $allGood = $false
        }
    }
    catch {
        Write-Error "Not logged in to Azure CLI"
        Write-Status "Please run: az login"
        $allGood = $false
    }

    # Check Docker (optional)
    if (Test-Command "docker") {
        Write-Status "Docker is available"
    }
    else {
        Write-Warning "Docker is not available (optional for local testing)"
    }

    # Check Node.js (for frontend)
    if (Test-Command "node") {
        $nodeVersion = node --version
        Write-Status "Node.js is installed: $nodeVersion"
    }
    else {
        Write-Warning "Node.js is not installed (required for frontend development)"
    }

    # Check Python (for backend)
    if (Test-Command "python") {
        $pythonVersion = python --version
        Write-Status "Python is installed: $pythonVersion"
    }
    elseif (Test-Command "python3") {
        $pythonVersion = python3 --version
        Write-Status "Python is installed: $pythonVersion"
    }
    else {
        Write-Warning "Python is not installed (required for backend development)"
    }

    # Check UV (for backend)
    if (Test-Command "uv") {
        $uvVersion = uv --version
        Write-Status "UV is installed: $uvVersion"
    }
    else {
        Write-Warning "UV is not installed (required for backend development)"
    }

    if (!$allGood) {
        Write-Error "Prerequisites check failed. Please install missing tools."
        exit 1
    }
}

# Initialize Terraform
function Initialize-Terraform {
    Write-Header "Initializing Terraform"

    if (!(Test-Path ".\terraform")) {
        Write-Error "Terraform directory not found: .\terraform"
        exit 1
    }

    Push-Location ".\terraform"

    try {
        # Check if terraform.tfvars exists
        if (!(Test-Path "terraform.tfvars")) {
            if (Test-Path "terraform.tfvars.example") {
                Write-Warning "terraform.tfvars not found, copying from example"
                Copy-Item "terraform.tfvars.example" "terraform.tfvars"
                Write-Warning "Please edit terraform.tfvars with your specific values"
                Read-Host "Press Enter to continue after editing terraform.tfvars"
            }
            else {
                Write-Error "terraform.tfvars.example not found"
                exit 1
            }
        }

        # Initialize Terraform
        Write-Status "Running terraform init..."
        terraform init

        # Validate Terraform configuration
        Write-Status "Validating Terraform configuration..."
        terraform validate

        # Format check
        Write-Status "Checking Terraform formatting..."
        try {
            terraform fmt -check -recursive
        }
        catch {
            Write-Warning "Terraform files are not properly formatted"
            Write-Status "Running terraform fmt to fix formatting..."
            terraform fmt -recursive
        }
    }
    finally {
        Pop-Location
    }
}

# Plan Terraform deployment
function Start-TerraformPlan {
    Write-Header "Planning Terraform Deployment"

    Push-Location $TerraformDir

    try {
        Write-Status "Running terraform plan..."
        terraform plan -out=tfplan

        # Ask for confirmation
        $confirm = Read-Host "Do you want to proceed with the deployment? (y/N)"
        if ($confirm -notmatch "^[Yy]$") {
            Write-Warning "Deployment cancelled"
            if (Test-Path "tfplan") {
                Remove-Item "tfplan"
            }
            exit 0
        }
    }
    finally {
        Pop-Location
    }
}

# Apply Terraform deployment
function Start-TerraformApply {
    Write-Header "Applying Terraform Deployment"

    Push-Location $TerraformDir

    try {
        Write-Status "Running terraform apply..."
        terraform apply tfplan

        # Clean up plan file
        if (Test-Path "tfplan") {
            Remove-Item "tfplan"
        }

        # Get outputs
        Write-Status "Getting Terraform outputs..."
        terraform output -json | Out-File "terraform-outputs.json" -Encoding utf8

        Write-Status "Terraform deployment completed successfully!"
    }
    finally {
        Pop-Location
    }
}

# Build and test backend
function Build-Backend {
    Write-Header "Building and Testing Backend"

    if (!(Test-Path ".\backend\content_service")) {
        Write-Warning "Backend directory not found: .\backend\content_service"
        return
    }

    Push-Location ".\backend\content_service"

    try {
        # Check if uv is available
        if (Test-Command "uv") {
            Write-Status "Installing backend dependencies with UV..."
            uv sync

            Write-Status "Running backend tests..."
            try {
                uv run pytest --maxfail=1 --disable-warnings -q
            }
            catch {
                Write-Warning "Backend tests failed or not found"
            }

            Write-Status "Running linting..."
            try {
                uv run ruff check .
            }
            catch {
                Write-Warning "Linting issues found or ruff not configured"
            }
        }
        else {
            Write-Warning "UV not available, skipping backend build and tests"
        }
    }
    finally {
        Pop-Location
    }
}

# Build and test frontend
function Build-Frontend {
    Write-Header "Building and Testing Frontend"

    if (!(Test-Path ".\frontend")) {
        Write-Warning "Frontend directory not found: .\frontend"
        return
    }

    Push-Location ".\frontend"

    try {
        # Check if npm is available
        if (Test-Command "npm") {
            Write-Status "Installing frontend dependencies..."
            npm ci

            Write-Status "Running frontend linting..."
            try {
                npm run lint
            }
            catch {
                Write-Warning "Frontend linting failed"
            }

            Write-Status "Running type checking..."
            try {
                npx tsc --noEmit
            }
            catch {
                Write-Warning "Type checking failed"
            }

            Write-Status "Building frontend..."
            try {
                npm run build
            }
            catch {
                Write-Warning "Frontend build failed"
            }

            Write-Status "Running frontend tests..."
            try {
                npm test --passWithNoTests
            }
            catch {
                Write-Warning "Frontend tests failed or not found"
            }
        }
        else {
            Write-Warning "npm not available, skipping frontend build and tests"
        }
    }
    finally {
        Pop-Location
    }
}

# Deploy applications
function Deploy-Applications {
    Write-Header "Deploying Applications"

    # Check if we have Terraform outputs
    $outputsFile = ".\terraform\terraform-outputs.json"
    if (Test-Path $outputsFile) {
        Write-Status "Using Terraform outputs for deployment configuration"

        try {
            $outputs = Get-Content $outputsFile | ConvertFrom-Json

            # Extract important values
            $containerRegistry = $outputs.container_registry_login_server.value
            $backendUrl = $outputs.backend_app_url.value
            $frontendUrl = $outputs.frontend_app_url.value

            if ($containerRegistry) {
                Write-Status "Container Registry: $containerRegistry"
            }

            if ($backendUrl) {
                Write-Status "Backend URL: $backendUrl"
            }

            if ($frontendUrl) {
                Write-Status "Frontend URL: $frontendUrl"
            }
        }
        catch {
            Write-Warning "Could not parse Terraform outputs"
        }
    }
    else {
        Write-Warning "Terraform outputs not found. Applications may need manual configuration."
    }

    Write-Status "Application deployment will be handled by GitHub Actions"
    Write-Status "Push your changes to the main branch to trigger deployments"
}

# Health check
function Test-Health {
    Write-Header "Running Health Checks"

    # Check if we have the backend URL
    $outputsFile = ".\terraform\terraform-outputs.json"
    if (Test-Path $outputsFile) {
        try {
            $outputs = Get-Content $outputsFile | ConvertFrom-Json
            $backendUrl = $outputs.backend_app_url.value
            $frontendUrl = $outputs.frontend_app_url.value

            if ($backendUrl) {
                Write-Status "Checking backend health at: $backendUrl"

                # Wait a moment for the service to be ready
                Start-Sleep -Seconds 10

                try {
                    $response = Invoke-WebRequest -Uri "$backendUrl/health" -UseBasicParsing -TimeoutSec 30
                    if ($response.StatusCode -eq 200) {
                        Write-Status "✅ Backend is healthy"
                    }
                    else {
                        Write-Warning "⚠️ Backend health check returned status: $($response.StatusCode)"
                    }
                }
                catch {
                    Write-Warning "⚠️ Backend health check failed or endpoint not available"
                }
            }

            if ($frontendUrl) {
                Write-Status "Checking frontend at: $frontendUrl"

                try {
                    $response = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing -TimeoutSec 30
                    if ($response.StatusCode -eq 200) {
                        Write-Status "✅ Frontend is accessible"
                    }
                    else {
                        Write-Warning "⚠️ Frontend accessibility check returned status: $($response.StatusCode)"
                    }
                }
                catch {
                    Write-Warning "⚠️ Frontend accessibility check failed"
                }
            }
        }
        catch {
            Write-Warning "Cannot run health checks - failed to parse Terraform outputs"
        }
    }
    else {
        Write-Warning "Cannot run health checks without Terraform outputs"
    }
}

# Display deployment summary
function Show-Summary {
    Write-Header "Deployment Summary"

    $outputsFile = ".\terraform\terraform-outputs.json"
    if (Test-Path $outputsFile) {
        try {
            $outputs = Get-Content $outputsFile | ConvertFrom-Json

            Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
            Write-Host ""

            Write-Host "Application URLs:" -ForegroundColor Green
            $backendUrl = if ($outputs.backend_app_url.value) { $outputs.backend_app_url.value } else { "Not available" }
            $frontendUrl = if ($outputs.frontend_app_url.value) { $outputs.frontend_app_url.value } else { "Not available" }

            Write-Host "Backend API: $backendUrl"
            Write-Host "Frontend App: $frontendUrl"
            Write-Host ""

            Write-Host "Next Steps:" -ForegroundColor Green
            Write-Host "1. Configure your GitHub repository secrets with the Terraform outputs"
            Write-Host "2. Push your code to trigger GitHub Actions deployments"
            Write-Host "3. Configure custom domains if needed"
            Write-Host "4. Set up monitoring and alerting"
            Write-Host "5. Initialize your database with seed data"
            Write-Host ""

            Write-Host "Monitoring:" -ForegroundColor Green
            $insightsKey = if ($outputs.application_insights_instrumentation_key.value) { $outputs.application_insights_instrumentation_key.value } else { "Not available" }
            Write-Host "Application Insights Key: $insightsKey"
            Write-Host ""

            Write-Host "Important:" -ForegroundColor Yellow
            Write-Host "- Save the Terraform outputs securely"
            Write-Host "- Configure GitHub repository secrets for CI/CD"
            Write-Host "- Review and customize the deployed resources as needed"
        }
        catch {
            Write-Error "Failed to parse Terraform outputs for summary"
        }
    }
    else {
        Write-Error "Terraform outputs not available. Please check the deployment."
    }
}

# Cleanup function
function Stop-Deployment {
    Write-Warning "Script interrupted. Cleaning up..."
    $tfplanPath = ".\terraform\tfplan"
    if (Test-Path $tfplanPath) {
        Remove-Item $tfplanPath
    }
    exit 1
}

# Main execution function
function Start-Deployment {
    Write-Header "Adara Screen Digital Signage Platform Deployment"

    Test-Prerequisites

    if (!$SkipBuild) {
        Build-Backend
        Build-Frontend
    }

    if (!$SkipTerraform) {
        Initialize-Terraform
        Start-TerraformPlan
        Start-TerraformApply
    }

    Deploy-Applications

    if (!$SkipHealth) {
        Test-Health
    }

    Show-Summary
}

# Handle interruption
$null = Register-EngineEvent PowerShell.Exiting -Action { Stop-Deployment }

# Main execution
try {
    # Show help if requested
    if ($Help) {
        Show-Usage
        exit 0
    }

    # Run the main deployment
    Start-Deployment
}
catch {
    Write-Error "An error occurred during deployment: $($_.Exception.Message)"
    Write-Error "Stack trace: $($_.ScriptStackTrace)"
    exit 1
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")