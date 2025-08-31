# 🚀 Quick Start Guide - Adara Digital Signage Flutter App

## Prerequisites Checklist
- [ ] Flutter SDK 3.35.2 installed (`flutter --version`)
- [ ] **Java JDK 17+ installed** (Critical!)
- [ ] Android Studio installed with Android SDK
- [ ] Android SDK Command Line Tools installed
- [ ] Android Virtual Devices created

## ❌ Current Issues & Solutions

### Issue 1: JAVA_HOME Not Set (Most Critical)
**Symptoms:** `ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH`

**Solution:**
1. Download JDK 17+ from: https://adoptium.net/temurin/releases/
2. Install JDK (choose Windows x64 MSI)
3. Set environment variables:
   ```bash
   setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-17.x.x.x-hotspot" /M
   setx PATH "%PATH%;%JAVA_HOME%\bin" /M
   ```
4. Restart terminal/command prompt
5. Verify: `java -version`

### Issue 2: Android SDK Command Line Tools Missing
**Symptoms:** `cmdline-tools component is missing`

**Solution:**
1. Download from: https://developer.android.com/studio#command-line-tools-only
2. Extract to: `C:\Users\%USERNAME%\Android\Sdk\cmdline-tools\latest`
3. Set environment variables:
   ```bash
   setx ANDROID_HOME "C:\Users\%USERNAME%\Android\Sdk" /M
   setx ANDROID_SDK_ROOT "C:\Users\%USERNAME%\Android\Sdk" /M
   setx PATH "%PATH%;%ANDROID_HOME%\cmdline-tools\latest\bin" /M
   ```
4. Restart terminal
5. Accept licenses: `flutter doctor --android-licenses`

### Issue 3: Deprecated withOpacity Usage (Fixed ✅)
**Status:** Already resolved in the codebase
- Replaced all `withOpacity()` calls with `withValues(alpha:)`
- Fixed test file to use correct class name

## Step 1: Install Java JDK (CRITICAL FIRST STEP)
```bash
# Download and install JDK 17+ from:
# https://adoptium.net/temurin/releases/

# After installation, set environment variables:
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-17.x.x.x-hotspot" /M
setx PATH "%PATH%;%JAVA_HOME%\bin" /M

# Restart terminal and verify:
java -version
```

## Step 2: Android SDK Setup
```bash
# Download Android SDK Command Line Tools:
# https://developer.android.com/studio#command-line-tools-only

# Extract to:
# C:\Users\%USERNAME%\Android\Sdk\cmdline-tools\latest

# Set environment variables:
setx ANDROID_HOME "C:\Users\%USERNAME%\Android\Sdk" /M
setx ANDROID_SDK_ROOT "C:\Users\%USERNAME%\Android\Sdk" /M
setx PATH "%PATH%;%ANDROID_HOME%\cmdline-tools\latest\bin" /M

# Restart terminal
```

## Step 3: Install Android SDK Components
```bash
# Accept licenses first:
flutter doctor --android-licenses

# Install required components:
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0" "emulator" "system-images;android-34;google_apis;x86_64"
```

## Step 4: Create Android Virtual Devices
```bash
# Create tablet emulator for kiosk:
flutter emulators --create --name "Tablet_Kiosk"

# Create phone emulator for mobile:
flutter emulators --create --name "Phone_Test"

# Create TV emulator:
flutter emulators --create --name "Android_TV"
```

## Step 5: Verify Setup
```bash
# Run the test script:
.\test_setup.ps1

# OR manual verification:
flutter doctor
flutter devices
flutter emulators
```

## Step 6: Run the App

### Start an Emulator
```bash
# List available emulators
flutter emulators

# Start tablet emulator (recommended for kiosk)
flutter emulators --launch Tablet_Kiosk

# OR start phone emulator
flutter emulators --launch Phone_Test

# OR start TV emulator
flutter emulators --launch Android_TV
```

### Run the Application
```bash
cd adarah_digital_signage
flutter run
```

## Step 7: Test Different Screen Sizes
```bash
# Run on different emulators
flutter run -d Tablet_Kiosk
flutter run -d Phone_Test
flutter run -d Android_TV
```

## Troubleshooting

### If Java is still not found:
```bash
# Check Java installation:
where java
java -version

# If not found, reinstall JDK and ensure PATH is set correctly
```

### If Android SDK still not working:
```bash
# Check environment variables:
echo %ANDROID_HOME%
echo %JAVA_HOME%

# Verify SDK location exists:
dir "C:\Users\%USERNAME%\Android\Sdk"
```

### If emulator won't start:
```bash
# Kill existing processes
adb kill-server
adb start-server

# Cold boot emulator
flutter emulators --launch Tablet_Kiosk --cold
```

### If build fails:
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter run
```

## Development Commands

```bash
# Hot reload (during development)
r

# Hot restart
R

# Build debug APK
flutter build apk

# Build release APK
flutter build apk --release

# Run tests
flutter test
```

## App Features Overview

The app includes 5 main screens:
1. **Setup Screen** (`/setup`) - Device registration with QR scanning
2. **Main Display** (`/main`) - Full-screen content rotation
3. **Interactive Screen** (`/interactive`) - NFC/Bluetooth engagement
4. **Status Screen** (`/status`) - Administrative monitoring
5. **Error Screen** (`/error`) - Offline mode handling

## Next Steps

1. ✅ Complete Java JDK installation
2. ⏳ Complete Android SDK setup
3. ⏳ Test app on emulators
4. ⏳ Add backend integration
5. ⏳ Implement NFC/Bluetooth features

---

**Need Help?** Check the full README.md for detailed documentation.

**Priority:** Install Java JDK first, then Android SDK setup.

**Happy Coding! 🎉**
