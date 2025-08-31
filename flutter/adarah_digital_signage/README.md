# Adara Digital Signage - Flutter App

A Flutter-based digital signage application for Android devices (TVs, tablets, kiosks) that displays CSM content with interactive features and robust offline capabilities. This app implements a complete five-screen architecture with Material Design 3 theming and responsive layouts.

## Features

### Five-Screen Architecture ✅
1. **Setup & Registration Screen** - Device onboarding with QR code scanning
2. **Main Display Screen** - Full-screen content rendering with multi-zone support
3. **Interactive Screen** - NFC/Bluetooth engagement with gamification
4. **Status & Diagnostics Screen** - Administrative monitoring and controls
5. **Error & Offline Mode Screen** - Graceful degradation with offline content

### Key Capabilities
- **Content Synchronization** - 5-minute interval sync with differential updates
- **Analytics Collection** - Privacy-compliant data gathering and batch upload
- **Digital Twin Integration** - Device mirroring and remote management
- **NFC/Bluetooth Support** - Proximity detection and interactive engagement
- **Offline Operation** - Cached content playback during connectivity issues
- **Real-time Monitoring** - System health metrics and diagnostics

### Current Implementation Status
- ✅ **Core UI Framework** - All 5 screens implemented with Material Design 3
- ✅ **Navigation System** - Named routes with proper routing setup
- ✅ **Theme System** - Light/dark theme support with custom color scheme
- ✅ **Responsive Design** - Optimized for tablets, phones, and Android TV
- ⏳ **Backend Integration** - API services and data models (planned)
- ⏳ **NFC/Bluetooth** - Hardware integration (planned)
- ⏳ **Content Management** - Synchronization and caching (planned)

## Prerequisites

### Required Software
1. **Flutter SDK** (Latest stable version - currently 3.35.2)
   ```bash
   flutter --version
   ```

2. **Android Studio** with Android SDK
   - Download from: https://developer.android.com/studio
   - Install Android SDK Platform 34 (Android 14)
   - Install Android SDK Build-Tools 34.0.0
   - Install Android SDK Command-line Tools

3. **Android Virtual Device (AVD) Manager**
   - Create emulators for testing different screen sizes
   - Recommended configurations:
     - **Tablet (10.1", 1920x1200)** - For kiosk testing
     - **Phone (6.7", 1440x3120)** - For mobile testing
     - **Android TV (1080p)** - For TV interface testing

### Quick Setup (Recommended)
Use the automated setup scripts included in this project:

**For PowerShell users:**
```bash
# Run from the flutter directory
.\setup_android_sdk.ps1
```

**For Command Prompt users:**
```bash
# Run from the flutter directory
setup_android_sdk.bat
```

These scripts will automatically:
- Download and install Android SDK Command Line Tools
- Set up environment variables
- Accept Android SDK licenses
- Install required SDK components
- Create Android Virtual Devices

### Environment Setup

#### 1. Install Android SDK Command Line Tools
```bash
# Download and install Android SDK command-line tools
# Set ANDROID_HOME environment variable
# Add to PATH: %ANDROID_HOME%\cmdline-tools\latest\bin
```

#### 2. Accept Android SDK Licenses
```bash
flutter doctor --android-licenses
```

#### 3. Create Android Virtual Devices

**Option A: Using Android Studio**
1. Open Android Studio
2. Go to Tools → Device Manager
3. Create new devices with these specifications:

**Tablet Emulator (Recommended for Kiosk Testing):**
- Device: Pixel Tablet
- System Image: Android 14 (API 34)
- Orientation: Landscape
- Storage: 8GB
- RAM: 4GB

**Phone Emulator (Recommended for Mobile Testing):**
- Device: Pixel 8
- System Image: Android 14 (API 34)
- Storage: 4GB
- RAM: 2GB

**Android TV Emulator (Recommended for TV Testing):**
- Device: Android TV (1080p)
- System Image: Android TV 14 (API 34)
- Storage: 8GB
- RAM: 4GB

**Option B: Using Command Line**
```bash
# List available device types
flutter emulators

# Create tablet emulator
flutter emulators --create --name "Tablet_Kiosk"

# Create phone emulator
flutter emulators --create --name "Phone_Test"

# Create TV emulator
flutter emulators --create --name "Android_TV"
```

## Getting Started

### Quick Start (Recommended)
For the fastest setup experience, see our **[Quick Start Guide](../QUICK_START.md)** which provides step-by-step instructions.

### 1. Clone and Setup
```bash
cd flutter/adarah_digital_signage
flutter pub get
```

### 2. Verify Setup
Use the automated test script to verify your environment:

**PowerShell:**
```bash
# Run from the flutter directory
.\test_setup.ps1
```

**Command Prompt:**
```bash
# Run from the flutter directory
test_setup.bat
```

**Manual verification:**
```bash
flutter doctor
```

Expected output should show:
- ✅ Flutter (Channel stable, 3.35.2)
- ✅ Android toolchain
- ✅ Android Studio
- ✅ Connected device (or emulator)

### 3. Run the App

**Start an Emulator:**
```bash
# List available emulators
flutter emulators

# Start specific emulator
flutter emulators --launch Tablet_Kiosk
# OR
flutter emulators --launch Phone_Test
# OR
flutter emulators --launch Android_TV
```

**Run the Application:**
```bash
flutter run
```

**Run on Specific Device:**
```bash
# List connected devices
flutter devices

# Run on specific device
flutter run -d emulator-5554
```

## Development Workflow

### Hot Reload
- Press `r` in terminal for hot reload
- Press `R` for hot restart
- Changes to Dart code will be reflected immediately

### Testing Different Screen Sizes
```bash
# Run on different emulators
flutter run -d Tablet_Kiosk
flutter run -d Phone_Test
flutter run -d Android_TV
```

### Building APK
```bash
# Debug APK
flutter build apk

# Release APK
flutter build apk --release
```

## Device Registration

### Updated Registration System
The app now uses a secure registration key system instead of organization codes:

#### Registration Fields
- **Device Name**: Descriptive name for the device (e.g., "Lobby Display")
- **Organization Code**: Provided by your organization administrator
- **Registration Key**: Secure key generated by the system (keep this confidential)
- **Aspect Ratio**: Optional screen aspect ratio (e.g., "16:9", "4:3")

#### Registration Process
1. Obtain registration key from your organization administrator
2. Enter device information in the setup screen
3. Submit registration - device will be validated and registered
4. Upon success, device is ready to display content

#### API Integration
The registration uses the backend API endpoint:
```
POST /api/device/register
```

**Request Body:**
```json
{
  "device_name": "Lobby Display",
  "organization_code": "ORG123",
  "registration_key": "secure-key-here",
  "aspect_ratio": "16:9"
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "uuid-here",
  "message": "Device registered successfully",
  "organization_code": "ORG123",
  "company_name": "Your Company Name"
}
```

## Architecture Overview

### Project Structure
```
lib/
├── main.dart                          # App entry point with routing & theming
├── screens/                           # UI screens (✅ implemented)
│   ├── setup_registration_screen.dart # Device onboarding
│   ├── main_display_screen.dart       # Content display
│   ├── interactive_screen.dart        # NFC/Bluetooth engagement
│   ├── status_diagnostics_screen.dart # Admin monitoring
│   └── error_offline_screen.dart      # Offline handling
├── models/                            # Data models (⏳ planned)
├── services/                          # Business logic (⏳ planned)
├── widgets/                           # Reusable widgets (⏳ planned)
└── utils/                             # Utilities (⏳ planned)

flutter/                               # Development tools
├── QUICK_START.md                     # Quick setup guide
├── setup_android_sdk.ps1             # Automated Android setup (PowerShell)
├── setup_android_sdk.bat             # Automated Android setup (Batch)
├── test_setup.ps1                    # Environment verification (PowerShell)
└── test_setup.bat                    # Environment verification (Batch)
```

### Current Dependencies
```yaml
dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.8

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^6.0.0
```

### Theme Configuration
The app uses Material Design 3 with:
- **Primary Color**: Blue (#1E3A8A)
- **Font Family**: Roboto
- **Light/Dark Theme Support**: System-based theme switching
- **Custom Button Styles**: Rounded corners with consistent padding
- **Card Elevation**: 4dp with 12px border radius

## Testing

### Unit Tests
```bash
flutter test
```

### Integration Tests
```bash
flutter test integration_test/
```

### Widget Tests
```bash
flutter test test/widget_test.dart
```

## Deployment

### Android APK Generation
```bash
# Generate release APK
flutter build apk --release --target-platform android-arm64

# Install on device
flutter install
```

### App Bundle for Play Store
```bash
flutter build appbundle --release
```

## Troubleshooting

### Common Issues

**Android SDK Command Line Tools Missing:**
```bash
# Download manually from:
# https://developer.android.com/studio#command-line-tools-only

# Extract to:
# C:\Users\%USERNAME%\Android\Sdk\cmdline-tools\latest

# Set environment variables:
setx ANDROID_HOME "C:\Users\%USERNAME%\Android\Sdk" /M
setx ANDROID_SDK_ROOT "C:\Users\%USERNAME%\Android\Sdk" /M

# Add to PATH:
setx PATH "%PATH%;%ANDROID_HOME%\cmdline-tools\latest\bin" /M
```

**JAVA_HOME Not Set:**
```bash
# Download JDK 17+ from:
# https://adoptium.net/temurin/releases/

# Set environment variable:
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-17.x.x.x-hotspot" /M

# Add to PATH:
setx PATH "%PATH%;%JAVA_HOME%\bin" /M
```

**Emulator Creation Fails:**
```bash
# Install required SDK components first:
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0" "emulator" "system-images;android-34;google_apis;x86_64"

# Accept licenses:
flutter doctor --android-licenses

# Then create emulator:
flutter emulators --create --name "Tablet_Kiosk"
```

**Android Studio Not Installed:**
- Download from: https://developer.android.com/studio
- Install Android SDK Platform 34
- Install Android SDK Build-Tools 34.0.0
- Install Android SDK Command-line Tools

**Build failures:**
```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter run
```

**Android licenses:**
```bash
flutter doctor --android-licenses
```

**Device not detected:**
```bash
# Check connected devices
flutter devices

# Restart ADB
adb kill-server
adb start-server
```

### Performance Tips
- Use `const` constructors where possible
- Implement proper state management
- Optimize image loading with caching
- Use `ListView.builder` for large lists
- Profile with Flutter DevTools

## Development Roadmap

### Phase 1: Core UI (✅ Complete)
- [x] Five-screen architecture implementation
- [x] Material Design 3 theming
- [x] Responsive layouts for multiple screen sizes
- [x] Navigation system setup

### Phase 2: Backend Integration (⏳ Next)
- [ ] API service layer implementation
- [ ] Data models and serialization
- [ ] Content synchronization service
- [ ] Offline caching system

### Phase 3: Hardware Integration (⏳ Planned)
- [ ] NFC reader integration
- [ ] Bluetooth connectivity
- [ ] GPS location services
- [ ] Device sensors

### Phase 4: Advanced Features (⏳ Future)
- [ ] Real-time content updates
- [ ] Analytics and reporting
- [ ] Remote device management
- [ ] Multi-language support

### Phase 5: Production (⏳ Final)
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Security hardening
- [ ] Deployment automation

## Contributing

1. Follow Flutter best practices
2. Write tests for new features
3. Update documentation
4. Test on multiple screen sizes
5. Ensure Material Design 3 compliance

## Support

For issues and questions:
- Check Flutter documentation: https://docs.flutter.dev/
- Android Studio documentation: https://developer.android.com/studio
- Project documentation: `../../../docs/FLUTTER_APP_SPEC.md`
- Quick Start Guide: `../QUICK_START.md`

---

**Version**: 1.0.0
**Flutter Version**: 3.35.2
**Dart SDK**: ^3.9.0
**Android API Level**: 34
**Material Design**: Version 3
**Last Updated**: 2025-08-31
**Implementation Status**: Core UI Complete ✅
