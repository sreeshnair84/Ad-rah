# Flutter App Test Script
# Run this script to test your Flutter setup and app

Write-Host "Testing Flutter Digital Signage App Setup..." -ForegroundColor Green

# Change to Flutter project directory
$flutterPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Join-Path $flutterPath "adarah_digital_signage"

if (!(Test-Path $projectPath)) {
    Write-Host "Error: Flutter project not found at $projectPath" -ForegroundColor Red
    exit 1
}

Set-Location $projectPath

# Test 1: Flutter Doctor
Write-Host "`n1. Running Flutter Doctor..." -ForegroundColor Yellow
flutter doctor

# Test 2: Flutter Pub Get
Write-Host "`n2. Running Flutter Pub Get..." -ForegroundColor Yellow
flutter pub get

# Test 3: Flutter Analyze
Write-Host "`n3. Running Flutter Analyze..." -ForegroundColor Yellow
flutter analyze

# Test 4: Check for compilation errors
Write-Host "`n4. Testing App Compilation..." -ForegroundColor Yellow
$buildResult = flutter build apk --debug 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ App compiles successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Compilation failed:" -ForegroundColor Red
    Write-Host $buildResult -ForegroundColor Red
}

# Test 5: List available devices/emulators
Write-Host "`n5. Available Devices and Emulators:" -ForegroundColor Yellow
flutter devices

# Test 6: List available emulators
Write-Host "`n6. Available Emulators:" -ForegroundColor Yellow
flutter emulators

# Test 7: Check project structure
Write-Host "`n7. Project Structure Check:" -ForegroundColor Yellow
$requiredFiles = @(
    "lib\main.dart",
    "lib\screens\setup_registration_screen.dart",
    "lib\screens\main_display_screen.dart",
    "lib\screens\interactive_screen.dart",
    "lib\screens\status_diagnostics_screen.dart",
    "lib\screens\error_offline_screen.dart",
    "pubspec.yaml",
    "README.md"
)

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $projectPath $file
    if (Test-Path $filePath) {
        Write-Host "✅ $file - Found" -ForegroundColor Green
    } else {
        Write-Host "❌ $file - Missing" -ForegroundColor Red
    }
}

# Test 8: Check pubspec.yaml dependencies
Write-Host "`n8. Checking Dependencies:" -ForegroundColor Yellow
$pubspecPath = Join-Path $projectPath "pubspec.yaml"
if (Test-Path $pubspecPath) {
    $pubspecContent = Get-Content $pubspecPath -Raw
    if ($pubspecContent -match "flutter:") {
        Write-Host "✅ Flutter dependency found" -ForegroundColor Green
    } else {
        Write-Host "❌ Flutter dependency missing" -ForegroundColor Red
    }

    if ($pubspecContent -match "cupertino_icons:") {
        Write-Host "✅ Cupertino icons dependency found" -ForegroundColor Green
    } else {
        Write-Host "❌ Cupertino icons dependency missing" -ForegroundColor Red
    }
} else {
    Write-Host "❌ pubspec.yaml not found" -ForegroundColor Red
}

Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "Test Summary:" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan

if ($buildResult -and $LASTEXITCODE -eq 0) {
    Write-Host "🎉 Setup looks good! You can now run the app." -ForegroundColor Green
    Write-Host "Try: flutter run" -ForegroundColor White
    Write-Host "Or: flutter emulators --launch Tablet_Kiosk && flutter run" -ForegroundColor White
} else {
    Write-Host "⚠️  Some issues found. Please check the output above." -ForegroundColor Yellow
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "1. Run: flutter pub get" -ForegroundColor White
    Write-Host "2. Run: flutter clean && flutter pub get" -ForegroundColor White
    Write-Host "3. Check Android SDK setup" -ForegroundColor White
}

Write-Host "`nPress Enter to exit..." -ForegroundColor Gray
Read-Host
