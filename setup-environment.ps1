# Environment Setup Helper Script
# Run this script to quickly set up your development environment

Write-Host "🔧 Setting up Open Kiosk Development Environment..." -ForegroundColor Green

# Check prerequisites
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Yellow

$prerequisites = @()

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.1[2-9]") {
        Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Python 3.12+ required, found: $pythonVersion" -ForegroundColor Red
        $prerequisites += "Python 3.12+"
    }
} catch {
    Write-Host "❌ Python not found" -ForegroundColor Red
    $prerequisites += "Python 3.12+"
}

# Check UV
try {
    $uvVersion = uv --version 2>&1
    Write-Host "✅ UV: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ UV not found" -ForegroundColor Red
    $prerequisites += "UV package manager"
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -match "v1[8-9]" -or $nodeVersion -match "v[2-9][0-9]") {
        Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Node.js 18+ required, found: $nodeVersion" -ForegroundColor Red
        $prerequisites += "Node.js 18+"
    }
} catch {
    Write-Host "❌ Node.js not found" -ForegroundColor Red
    $prerequisites += "Node.js 18+"
}

# Check Docker
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found" -ForegroundColor Red
    $prerequisites += "Docker"
}

if ($prerequisites.Count -gt 0) {
    Write-Host "`n❌ Missing prerequisites:" -ForegroundColor Red
    foreach ($prereq in $prerequisites) {
        Write-Host "   - $prereq" -ForegroundColor Red
    }
    Write-Host "`nPlease install missing prerequisites and run this script again." -ForegroundColor Yellow
    exit 1
}

# Setup environment files
Write-Host "`n📝 Setting up environment files..." -ForegroundColor Yellow

# Backend environment
$backendEnvPath = "backend\content_service\.env"
$backendTemplatePath = "backend\content_service\.env.template"

if (Test-Path $backendTemplatePath) {
    if (-not (Test-Path $backendEnvPath)) {
        Copy-Item $backendTemplatePath $backendEnvPath
        Write-Host "✅ Created backend .env file from template" -ForegroundColor Green
        Write-Host "⚠️  Please edit $backendEnvPath with your actual values" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Backend .env file already exists" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Backend .env template not found" -ForegroundColor Red
}

# Frontend environment
$frontendEnvPath = "frontend\.env.local"
if (-not (Test-Path $frontendEnvPath)) {
    "NEXT_PUBLIC_API_URL=http://localhost:8000" | Out-File -FilePath $frontendEnvPath -Encoding UTF8
    Write-Host "✅ Created frontend .env.local file" -ForegroundColor Green
} else {
    Write-Host "✅ Frontend .env.local file already exists" -ForegroundColor Green
}

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow

# Backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Gray
Set-Location "backend\content_service"
try {
    uv sync
    Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install backend dependencies" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}
Set-Location "..\..\"

# Frontend dependencies
Write-Host "Installing frontend dependencies..." -ForegroundColor Gray
Set-Location "frontend"
try {
    npm install
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}
Set-Location ".."

# Docker services
Write-Host "`n🐳 Starting Docker services..." -ForegroundColor Yellow
Set-Location "backend\content_service"
try {
    docker-compose up -d
    Write-Host "✅ Docker services started" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to start Docker services" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}
Set-Location "..\..\"

# Wait for services to be ready
Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Seed test data
Write-Host "`n🌱 Seeding test data..." -ForegroundColor Yellow
Set-Location "backend\content_service"
try {
    uv run python seed_data.py
    Write-Host "✅ Test data seeded successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to seed test data" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}
Set-Location "..\..\"

# Final instructions
Write-Host "`n🎉 Setup Complete!" -ForegroundColor Green
Write-Host "`nTo start development:" -ForegroundColor Cyan
Write-Host "1. Backend API: Already running at http://localhost:8000" -ForegroundColor White
Write-Host "2. API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "3. Start frontend: cd frontend && npm run dev" -ForegroundColor White
Write-Host "4. Frontend: http://localhost:3000" -ForegroundColor White

Write-Host "`nTest Accounts:" -ForegroundColor Cyan
Write-Host "• Super User: admin@adara.com / adminpass" -ForegroundColor White
Write-Host "• Company Admin: admin@techcorpsolutions.com / adminpass" -ForegroundColor White
Write-Host "• Content Editor: editor@techcorpsolutions.com / adminpass" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "• Review .env files and update with your actual values" -ForegroundColor White
Write-Host "• Check the KEYS_REFERENCE.md for GitHub Actions setup" -ForegroundColor White
Write-Host "• Read the README.md for detailed documentation" -ForegroundColor White

Write-Host "`nHappy coding! 🚀" -ForegroundColor Green