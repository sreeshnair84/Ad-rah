# Install Terraform on Windows
# This script downloads and installs the latest Terraform

$ErrorActionPreference = "Stop"

# Utility functions
function Write-Status { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Header { param([string]$Message) Write-Host "=" * 50 -ForegroundColor Blue; Write-Host $Message -ForegroundColor Blue; Write-Host "=" * 50 -ForegroundColor Blue }

Write-Header "Installing Terraform for Windows"

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (!$isAdmin) {
    Write-Warning "This script should be run as Administrator for best results"
    Write-Status "You can also install to a user directory without admin rights"
}

# Method 1: Try Chocolatey first (if available)
if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Status "Found Chocolatey package manager. Installing Terraform..."
    try {
        choco install terraform -y
        Write-Status "Terraform installed successfully via Chocolatey"

        # Verify installation
        $terraformPath = Get-Command terraform -ErrorAction SilentlyContinue
        if ($terraformPath) {
            $version = terraform version
            Write-Status "Terraform is now available: $version"
            exit 0
        }
    }
    catch {
        Write-Warning "Chocolatey installation failed, trying manual installation..."
    }
}

# Method 2: Try winget (Windows Package Manager)
if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Status "Found winget package manager. Installing Terraform..."
    try {
        winget install Hashicorp.Terraform
        Write-Status "Terraform installed successfully via winget"

        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

        # Verify installation
        $terraformPath = Get-Command terraform -ErrorAction SilentlyContinue
        if ($terraformPath) {
            $version = terraform version
            Write-Status "Terraform is now available: $version"
            exit 0
        }
    }
    catch {
        Write-Warning "winget installation failed, trying manual installation..."
    }
}

# Method 3: Manual installation
Write-Status "Performing manual installation..."

try {
    # Get latest version
    Write-Status "Fetching latest Terraform version..."
    $apiUrl = "https://api.github.com/repos/hashicorp/terraform/releases/latest"
    $response = Invoke-RestMethod -Uri $apiUrl
    $latestVersion = $response.tag_name.TrimStart('v')

    Write-Status "Latest version: $latestVersion"

    # Determine architecture
    $arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "386" }

    # Download URL
    $downloadUrl = "https://releases.hashicorp.com/terraform/$latestVersion/terraform_${latestVersion}_windows_${arch}.zip"
    $zipFile = "$env:TEMP\terraform_${latestVersion}_windows_${arch}.zip"

    Write-Status "Downloading Terraform from: $downloadUrl"
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFile

    # Extract
    $extractPath = "$env:TEMP\terraform_extract"
    if (Test-Path $extractPath) {
        Remove-Item $extractPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $extractPath | Out-Null

    Write-Status "Extracting Terraform..."
    Expand-Archive -Path $zipFile -DestinationPath $extractPath

    # Determine installation path
    if ($isAdmin) {
        $installPath = "C:\Program Files\Terraform"
        $pathScope = "Machine"
    }
    else {
        $installPath = "$env:USERPROFILE\Tools\Terraform"
        $pathScope = "User"
    }

    # Create installation directory
    if (!(Test-Path $installPath)) {
        New-Item -ItemType Directory -Path $installPath -Force | Out-Null
    }

    # Copy terraform.exe
    Write-Status "Installing Terraform to: $installPath"
    Copy-Item "$extractPath\terraform.exe" $installPath -Force

    # Add to PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", $pathScope)
    if ($currentPath -notlike "*$installPath*") {
        Write-Status "Adding Terraform to PATH..."
        $newPath = "$currentPath;$installPath"
        [Environment]::SetEnvironmentVariable("PATH", $newPath, $pathScope)

        # Update current session PATH
        $env:PATH = "$env:PATH;$installPath"
    }

    # Cleanup
    Remove-Item $zipFile -Force
    Remove-Item $extractPath -Recurse -Force

    # Verify installation
    Write-Status "Verifying installation..."
    $terraformPath = Get-Command terraform -ErrorAction SilentlyContinue
    if ($terraformPath) {
        $version = terraform version
        Write-Status "✅ Terraform installed successfully!"
        Write-Status "Version: $version"
        Write-Status "Location: $($terraformPath.Source)"
    }
    else {
        Write-Error "Installation completed but terraform command not found"
        Write-Status "You may need to restart your PowerShell session"
        Write-Status "Or manually add $installPath to your PATH"
    }
}
catch {
    Write-Error "Manual installation failed: $($_.Exception.Message)"

    Write-Host ""
    Write-Host "Manual Installation Steps:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://www.terraform.io/downloads.html"
    Write-Host "2. Download the Windows version"
    Write-Host "3. Extract terraform.exe to a folder (e.g., C:\Tools\Terraform)"
    Write-Host "4. Add that folder to your system PATH"
    Write-Host "5. Restart PowerShell and run 'terraform version'"
}

Write-Host ""
Write-Host "Installation Options Summary:" -ForegroundColor Green
Write-Host "Option 1 - Chocolatey: choco install terraform"
Write-Host "Option 2 - winget: winget install Hashicorp.Terraform"
Write-Host "Option 3 - Manual: Download from terraform.io"
Write-Host ""
Write-Host "After installation, restart PowerShell and run: terraform version"

Read-Host "Press Enter to exit"