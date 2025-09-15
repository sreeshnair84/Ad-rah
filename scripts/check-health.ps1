# Health Check Script for Adara Screen Digital Signage Platform
# This script performs comprehensive health checks on deployed services

param(
    [string]$ConfigFile = ".\terraform\terraform-outputs.json",
    [switch]$Verbose,
    [switch]$ExportReport,
    [string]$ReportPath = ".\health-report.html"
)

$ErrorActionPreference = "Continue"

# Utility functions
function Write-Status { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Header { param([string]$Message) Write-Host "=" * 50 -ForegroundColor Blue; Write-Host $Message -ForegroundColor Blue; Write-Host "=" * 50 -ForegroundColor Blue }
function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Failed { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }

# Health check results
$global:HealthResults = @{
    Timestamp = Get-Date
    OverallStatus = "Unknown"
    Services = @{}
    Summary = @{
        Total = 0
        Healthy = 0
        Unhealthy = 0
        Warning = 0
    }
}

# Test service health
function Test-ServiceHealth {
    param(
        [string]$ServiceName,
        [string]$Url,
        [string]$HealthEndpoint = "/health",
        [int]$TimeoutSeconds = 30
    )

    Write-Status "Testing $ServiceName health..."

    $result = @{
        ServiceName = $ServiceName
        Url = $Url
        Status = "Unknown"
        ResponseTime = 0
        StatusCode = 0
        Error = ""
        Details = @{}
    }

    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $fullUrl = "$Url$HealthEndpoint"

        $response = Invoke-WebRequest -Uri $fullUrl -UseBasicParsing -TimeoutSec $TimeoutSeconds
        $stopwatch.Stop()

        $result.Status = "Healthy"
        $result.ResponseTime = $stopwatch.ElapsedMilliseconds
        $result.StatusCode = $response.StatusCode

        # Try to parse response for additional details
        try {
            $healthData = $response.Content | ConvertFrom-Json
            $result.Details = $healthData
        }
        catch {
            $result.Details = @{ RawResponse = $response.Content }
        }

        Write-Success "$ServiceName is healthy (${$result.ResponseTime}ms)"
    }
    catch {
        $result.Status = "Unhealthy"
        $result.Error = $_.Exception.Message
        Write-Failed "$ServiceName is unhealthy: $($_.Exception.Message)"
    }

    return $result
}

# Test database connectivity
function Test-DatabaseHealth {
    param([string]$ConnectionString)

    Write-Status "Testing database connectivity..."

    # This is a simplified test - in practice, you'd use actual database connection testing
    $result = @{
        ServiceName = "Database"
        Status = "Unknown"
        Error = ""
        Details = @{}
    }

    try {
        # For Cosmos DB, we can test the endpoint
        if ($ConnectionString -match "AccountEndpoint=([^;]+)") {
            $endpoint = $Matches[1]
            $response = Invoke-WebRequest -Uri $endpoint -UseBasicParsing -TimeoutSec 10
            $result.Status = "Healthy"
            $result.Details = @{ Endpoint = $endpoint }
            Write-Success "Database endpoint is accessible"
        }
        else {
            $result.Status = "Warning"
            $result.Error = "Cannot test database connection without proper endpoint"
            Write-Warning "Database connection string format not recognized"
        }
    }
    catch {
        $result.Status = "Unhealthy"
        $result.Error = $_.Exception.Message
        Write-Failed "Database connectivity test failed: $($_.Exception.Message)"
    }

    return $result
}

# Test Azure services
function Test-AzureServices {
    param([hashtable]$TerraformOutputs)

    $results = @{}

    # Test Container Registry
    if ($TerraformOutputs.container_registry_login_server) {
        Write-Status "Testing Container Registry..."
        try {
            $registryUrl = "https://$($TerraformOutputs.container_registry_login_server)/v2/"
            $response = Invoke-WebRequest -Uri $registryUrl -UseBasicParsing -TimeoutSec 10
            $results["ContainerRegistry"] = @{
                ServiceName = "Container Registry"
                Status = "Healthy"
                Url = $registryUrl
                StatusCode = $response.StatusCode
            }
            Write-Success "Container Registry is accessible"
        }
        catch {
            $results["ContainerRegistry"] = @{
                ServiceName = "Container Registry"
                Status = "Unhealthy"
                Error = $_.Exception.Message
            }
            Write-Failed "Container Registry test failed: $($_.Exception.Message)"
        }
    }

    # Test Storage Account
    if ($TerraformOutputs.storage_account_primary_endpoint) {
        Write-Status "Testing Blob Storage..."
        try {
            $response = Invoke-WebRequest -Uri $TerraformOutputs.storage_account_primary_endpoint -UseBasicParsing -TimeoutSec 10
            $results["BlobStorage"] = @{
                ServiceName = "Blob Storage"
                Status = "Healthy"
                Url = $TerraformOutputs.storage_account_primary_endpoint
                StatusCode = $response.StatusCode
            }
            Write-Success "Blob Storage is accessible"
        }
        catch {
            $results["BlobStorage"] = @{
                ServiceName = "Blob Storage"
                Status = "Unhealthy"
                Error = $_.Exception.Message
            }
            Write-Failed "Blob Storage test failed: $($_.Exception.Message)"
        }
    }

    # Test CDN
    if ($TerraformOutputs.cdn_endpoint_url) {
        Write-Status "Testing CDN..."
        try {
            $response = Invoke-WebRequest -Uri $TerraformOutputs.cdn_endpoint_url -UseBasicParsing -TimeoutSec 10
            $results["CDN"] = @{
                ServiceName = "CDN"
                Status = "Healthy"
                Url = $TerraformOutputs.cdn_endpoint_url
                StatusCode = $response.StatusCode
            }
            Write-Success "CDN is accessible"
        }
        catch {
            $results["CDN"] = @{
                ServiceName = "CDN"
                Status = "Unhealthy"
                Error = $_.Exception.Message
            }
            Write-Failed "CDN test failed: $($_.Exception.Message)"
        }
    }

    return $results
}

# Generate HTML health report
function New-HealthReport {
    param(
        [hashtable]$HealthResults,
        [string]$OutputPath
    )

    $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adara Screen Health Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1, h2 { color: #333; }
        .header { text-align: center; margin-bottom: 30px; }
        .status-healthy { color: #28a745; }
        .status-unhealthy { color: #dc3545; }
        .status-warning { color: #ffc107; }
        .summary { display: flex; justify-content: space-around; margin: 20px 0; }
        .summary-item { text-align: center; padding: 10px; border-radius: 5px; background: #f8f9fa; }
        .service { margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .service-healthy { border-left: 5px solid #28a745; }
        .service-unhealthy { border-left: 5px solid #dc3545; }
        .service-warning { border-left: 5px solid #ffc107; }
        .details { background: #f8f9fa; padding: 10px; border-radius: 3px; margin-top: 10px; font-family: monospace; font-size: 12px; }
        .timestamp { color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Adara Screen Health Report</h1>
            <p class="timestamp">Generated: $($HealthResults.Timestamp.ToString("yyyy-MM-dd HH:mm:ss"))</p>
            <h2 class="status-$($HealthResults.OverallStatus.ToLower())">Overall Status: $($HealthResults.OverallStatus.ToUpper())</h2>
        </div>

        <div class="summary">
            <div class="summary-item">
                <h3>Total Services</h3>
                <p><strong>$($HealthResults.Summary.Total)</strong></p>
            </div>
            <div class="summary-item">
                <h3>Healthy</h3>
                <p><strong class="status-healthy">$($HealthResults.Summary.Healthy)</strong></p>
            </div>
            <div class="summary-item">
                <h3>Unhealthy</h3>
                <p><strong class="status-unhealthy">$($HealthResults.Summary.Unhealthy)</strong></p>
            </div>
            <div class="summary-item">
                <h3>Warnings</h3>
                <p><strong class="status-warning">$($HealthResults.Summary.Warning)</strong></p>
            </div>
        </div>

        <h2>Service Details</h2>
"@

    foreach ($service in $HealthResults.Services.GetEnumerator()) {
        $statusClass = $service.Value.Status.ToLower()
        $serviceClass = "service-$statusClass"

        $html += @"
        <div class="service $serviceClass">
            <h3>$($service.Value.ServiceName) <span class="status-$statusClass">[$($service.Value.Status)]</span></h3>
"@

        if ($service.Value.Url) {
            $html += "<p><strong>URL:</strong> $($service.Value.Url)</p>"
        }

        if ($service.Value.ResponseTime) {
            $html += "<p><strong>Response Time:</strong> $($service.Value.ResponseTime)ms</p>"
        }

        if ($service.Value.StatusCode) {
            $html += "<p><strong>Status Code:</strong> $($service.Value.StatusCode)</p>"
        }

        if ($service.Value.Error) {
            $html += "<p><strong>Error:</strong> <span class='status-unhealthy'>$($service.Value.Error)</span></p>"
        }

        if ($service.Value.Details -and $service.Value.Details.Count -gt 0) {
            $detailsJson = $service.Value.Details | ConvertTo-Json -Depth 3
            $html += "<div class='details'><strong>Details:</strong><br><pre>$detailsJson</pre></div>"
        }

        $html += "</div>"
    }

    $html += @"
    </div>
</body>
</html>
"@

    try {
        $html | Out-File $OutputPath -Encoding utf8
        Write-Success "Health report saved to: $OutputPath"
        return $true
    }
    catch {
        Write-Error "Failed to save health report: $($_.Exception.Message)"
        return $false
    }
}

# Main health check function
function Start-HealthCheck {
    Write-Header "Adara Screen Digital Signage Platform - Health Check"

    # Load configuration
    if (!(Test-Path $ConfigFile)) {
        Write-Error "Configuration file not found: $ConfigFile"
        Write-Status "Please run Terraform deployment first to generate outputs"
        return
    }

    try {
        $outputs = Get-Content $ConfigFile | ConvertFrom-Json -AsHashtable
        $terraformOutputs = @{}

        # Convert Terraform outputs format
        foreach ($key in $outputs.Keys) {
            if ($outputs[$key].value) {
                $terraformOutputs[$key] = $outputs[$key].value
            }
        }
    }
    catch {
        Write-Error "Failed to parse configuration file: $($_.Exception.Message)"
        return
    }

    # Test main application services
    if ($terraformOutputs.backend_app_url) {
        $backendResult = Test-ServiceHealth -ServiceName "Backend API" -Url $terraformOutputs.backend_app_url
        $global:HealthResults.Services["Backend"] = $backendResult
    }

    if ($terraformOutputs.frontend_app_url) {
        $frontendResult = Test-ServiceHealth -ServiceName "Frontend Web App" -Url $terraformOutputs.frontend_app_url -HealthEndpoint ""
        $global:HealthResults.Services["Frontend"] = $frontendResult
    }

    # Test database
    if ($terraformOutputs.cosmos_db_endpoint) {
        $dbResult = Test-DatabaseHealth -ConnectionString $terraformOutputs.cosmos_db_endpoint
        $global:HealthResults.Services["Database"] = $dbResult
    }

    # Test Azure services
    $azureResults = Test-AzureServices -TerraformOutputs $terraformOutputs
    foreach ($service in $azureResults.GetEnumerator()) {
        $global:HealthResults.Services[$service.Key] = $service.Value
    }

    # Calculate summary
    $global:HealthResults.Summary.Total = $global:HealthResults.Services.Count
    $global:HealthResults.Summary.Healthy = ($global:HealthResults.Services.Values | Where-Object { $_.Status -eq "Healthy" }).Count
    $global:HealthResults.Summary.Unhealthy = ($global:HealthResults.Services.Values | Where-Object { $_.Status -eq "Unhealthy" }).Count
    $global:HealthResults.Summary.Warning = ($global:HealthResults.Services.Values | Where-Object { $_.Status -eq "Warning" }).Count

    # Determine overall status
    if ($global:HealthResults.Summary.Unhealthy -gt 0) {
        $global:HealthResults.OverallStatus = "Unhealthy"
    }
    elseif ($global:HealthResults.Summary.Warning -gt 0) {
        $global:HealthResults.OverallStatus = "Warning"
    }
    elseif ($global:HealthResults.Summary.Healthy -gt 0) {
        $global:HealthResults.OverallStatus = "Healthy"
    }
    else {
        $global:HealthResults.OverallStatus = "Unknown"
    }

    # Display summary
    Write-Header "Health Check Summary"
    Write-Host "Overall Status: " -NoNewline
    switch ($global:HealthResults.OverallStatus) {
        "Healthy" { Write-Host $global:HealthResults.OverallStatus -ForegroundColor Green }
        "Warning" { Write-Host $global:HealthResults.OverallStatus -ForegroundColor Yellow }
        "Unhealthy" { Write-Host $global:HealthResults.OverallStatus -ForegroundColor Red }
        default { Write-Host $global:HealthResults.OverallStatus -ForegroundColor Gray }
    }

    Write-Host ""
    Write-Host "Services Summary:" -ForegroundColor Cyan
    Write-Host "  Total: $($global:HealthResults.Summary.Total)"
    Write-Host "  Healthy: " -NoNewline; Write-Host $global:HealthResults.Summary.Healthy -ForegroundColor Green
    Write-Host "  Warnings: " -NoNewline; Write-Host $global:HealthResults.Summary.Warning -ForegroundColor Yellow
    Write-Host "  Unhealthy: " -NoNewline; Write-Host $global:HealthResults.Summary.Unhealthy -ForegroundColor Red

    # Verbose output
    if ($Verbose) {
        Write-Host ""
        Write-Header "Detailed Results"
        foreach ($service in $global:HealthResults.Services.GetEnumerator()) {
            Write-Host "Service: $($service.Value.ServiceName)" -ForegroundColor Cyan
            Write-Host "  Status: " -NoNewline
            switch ($service.Value.Status) {
                "Healthy" { Write-Host $service.Value.Status -ForegroundColor Green }
                "Warning" { Write-Host $service.Value.Status -ForegroundColor Yellow }
                "Unhealthy" { Write-Host $service.Value.Status -ForegroundColor Red }
                default { Write-Host $service.Value.Status -ForegroundColor Gray }
            }

            if ($service.Value.Url) {
                Write-Host "  URL: $($service.Value.Url)"
            }

            if ($service.Value.ResponseTime) {
                Write-Host "  Response Time: $($service.Value.ResponseTime)ms"
            }

            if ($service.Value.Error) {
                Write-Host "  Error: $($service.Value.Error)" -ForegroundColor Red
            }

            Write-Host ""
        }
    }

    # Export report
    if ($ExportReport) {
        New-HealthReport -HealthResults $global:HealthResults -OutputPath $ReportPath
    }

    # Exit with appropriate code
    if ($global:HealthResults.OverallStatus -eq "Unhealthy") {
        exit 1
    }
    elseif ($global:HealthResults.OverallStatus -eq "Warning") {
        exit 2
    }
    else {
        exit 0
    }
}

# Run health check
try {
    Start-HealthCheck
}
catch {
    Write-Error "Health check failed: $($_.Exception.Message)"
    exit 1
}