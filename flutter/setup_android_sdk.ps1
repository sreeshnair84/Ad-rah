# Android SDK Setup Script for Windows
# Run this script with administrator privileges

Write-Host "Setting up Android SDK for Flutter development..." -ForegroundColor Green

# Define paths
$ANDROID_HOME = "$env:USERPROFILE\Android\Sdk"
$ANDROID_SDK_ROOT = $ANDROID_HOME
$CMD_TOOLS_PATH = "$ANDROID_HOME\cmdline-tools\latest"

# Create Android SDK directory
if (!(Test-Path $ANDROID_HOME)) {
    New-Item -ItemType Directory -Path $ANDROID_HOME -Force
    Write-Host "Created Android SDK directory: $ANDROID_HOME" -ForegroundColor Yellow
}

# Download Android SDK Command Line Tools
$CMD_TOOLS_URL = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
$CMD_TOOLS_ZIP = "$env:TEMP\cmdline-tools.zip"

Write-Host "Downloading Android SDK Command Line Tools..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $CMD_TOOLS_URL -OutFile $CMD_TOOLS_ZIP

# Extract to temporary location first
$EXTRACT_TEMP = "$env:TEMP\cmdline-tools-temp"
if (Test-Path $EXTRACT_TEMP) { Remove-Item $EXTRACT_TEMP -Recurse -Force }
New-Item -ItemType Directory -Path $EXTRACT_TEMP -Force

Write-Host "Extracting Android SDK Command Line Tools..." -ForegroundColor Yellow
Expand-Archive -Path $CMD_TOOLS_ZIP -DestinationPath $EXTRACT_TEMP

# Move to correct location
if (!(Test-Path $CMD_TOOLS_PATH)) {
    New-Item -ItemType Directory -Path $CMD_TOOLS_PATH -Force
}
Copy-Item "$EXTRACT_TEMP\cmdline-tools\*" $CMD_TOOLS_PATH -Recurse -Force

# Clean up
Remove-Item $CMD_TOOLS_ZIP -Force
Remove-Item $EXTRACT_TEMP -Recurse -Force

# Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Yellow

# Check if ANDROID_HOME is already in PATH
$pathArray = $env:PATH -split ';'
$androidInPath = $pathArray -contains "$CMD_TOOLS_PATH\bin"

if (!$androidInPath) {
    # Add to PATH
    $newPath = "$CMD_TOOLS_PATH\bin;$env:PATH"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    Write-Host "Added Android SDK to PATH" -ForegroundColor Green
}

# Set ANDROID_HOME and ANDROID_SDK_ROOT
[Environment]::SetEnvironmentVariable("ANDROID_HOME", $ANDROID_HOME, "User")
[Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", $ANDROID_SDK_ROOT, "User")

Write-Host "Environment variables set:" -ForegroundColor Green
Write-Host "ANDROID_HOME: $ANDROID_HOME" -ForegroundColor White
Write-Host "ANDROID_SDK_ROOT: $ANDROID_SDK_ROOT" -ForegroundColor White

# Accept Android SDK licenses
Write-Host "Accepting Android SDK licenses..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c yes | $CMD_TOOLS_PATH\bin\sdkmanager.bat --licenses" -Wait -NoNewWindow

# Install required SDK components
Write-Host "Installing required Android SDK components..." -ForegroundColor Yellow

$sdkComponents = @(
    "platform-tools",
    "platforms;android-34",
    "build-tools;34.0.0",
    "emulator",
    "system-images;android-34;google_apis;x86_64"
)

foreach ($component in $sdkComponents) {
    Write-Host "Installing $component..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c $CMD_TOOLS_PATH\bin\sdkmanager.bat `"$component`"" -Wait -NoNewWindow
}

Write-Host "Android SDK setup completed!" -ForegroundColor Green
Write-Host "Please restart your terminal/command prompt for changes to take effect." -ForegroundColor Yellow
Write-Host "Then run: flutter doctor --android-licenses" -ForegroundColor Yellow
Write-Host "And: flutter doctor" -ForegroundColor Yellow

# Create Android Virtual Devices
Write-Host "Creating Android Virtual Devices..." -ForegroundColor Yellow

# Create AVD directory if it doesn't exist
$AVD_HOME = "$env:USERPROFILE\.android\avd"
if (!(Test-Path $AVD_HOME)) {
    New-Item -ItemType Directory -Path $AVD_HOME -Force
}

# Create tablet AVD
Write-Host "Creating Tablet AVD for kiosk testing..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c echo Creating Tablet AVD... && $CMD_TOOLS_PATH\bin\avdmanager.bat create avd -n Tablet_Kiosk -k `"system-images;android-34;google_apis;x86_64`" -d pixel_tablet" -Wait -NoNewWindow

# Create phone AVD
Write-Host "Creating Phone AVD for mobile testing..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c $CMD_TOOLS_PATH\bin\avdmanager.bat create avd -n Phone_Test -k `"system-images;android-34;google_apis;x86_64`" -d pixel" -Wait -NoNewWindow

# Create TV AVD
Write-Host "Creating Android TV AVD for TV testing..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c $CMD_TOOLS_PATH\bin\avdmanager.bat create avd -n Android_TV -k `"system-images;android-34;google_apis;x86_64`" -d tv_1080p" -Wait -NoNewWindow

Write-Host "Android Virtual Devices created!" -ForegroundColor Green
Write-Host "Available emulators:" -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c $CMD_TOOLS_PATH\bin\emulator.exe -list-avds" -Wait -NoNewWindow

Write-Host "`nSetup complete! You can now run:" -ForegroundColor Green
Write-Host "flutter emulators --launch Tablet_Kiosk" -ForegroundColor White
Write-Host "flutter emulators --launch Phone_Test" -ForegroundColor White
Write-Host "flutter emulators --launch Android_TV" -ForegroundColor White

Read-Host "Press Enter to exit"
