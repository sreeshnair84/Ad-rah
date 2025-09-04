# Flutter Digital Signage App - Technical Requirements

## Overview
This document outlines the technical requirements and implementation specifications for the Flutter-based digital signage application that will run on Android devices (TVs, tablets, kiosks) to display CSM content.

## Architecture Overview

### Five-Screen System Architecture
The Flutter app implements a five-screen architecture optimized for minimal user interaction and maximum content delivery:

1. **Setup & Registration Screen** - Device onboarding and authentication
2. **Main Display Screen** - Primary content rendering with multi-zone support
3. **Interactive & Game Screen** - NFC/Bluetooth engagement and gamification
4. **Status & Diagnostics Screen** - Administrative monitoring and controls
5. **Error & Offline Mode Screen** - Graceful degradation and recovery

### Background Services
- **Content Synchronization Service** - 5-minute interval sync with differential updates
- **Analytics Collection Service** - Privacy-compliant data gathering and batch upload
- **Digital Twin Service** - Device mirroring and remote management
- **Network Monitoring Service** - Connectivity awareness and optimization
- **Battery Optimization Service** - Power management for extended operation

## Technical Specifications

### Flutter Framework Requirements
```yaml
# pubspec.yaml
environment:
  sdk: '>=3.0.0 <4.0.0'
  flutter: '>=3.24.0'

dependencies:
  flutter:
    sdk: flutter

  # Core Dependencies
  dio: ^5.4.0                    # HTTP client with interceptors
  flutter_riverpod: ^2.4.9       # State management
  flutter_secure_storage: ^9.0.0 # Encrypted storage
  shared_preferences: ^2.2.2     # Local preferences

  # Media & Content
  video_player: ^2.8.2           # Video playback
  cached_network_image: ^3.3.0   # Image caching
  just_audio: ^0.9.36            # Audio playback

  # Hardware Integration
  nfc_manager: ^3.4.0            # NFC support
  flutter_blue_plus: ^1.32.0     # Bluetooth LE
  qr_code_scanner: ^1.0.1        # QR scanning
  qr_flutter: ^4.1.0             # QR generation

  # Utilities
  intl: ^0.19.0                  # Internationalization
  path_provider: ^2.1.3          # File system access
  connectivity_plus: ^5.0.2      # Network monitoring
  package_info_plus: ^5.0.0      # App information
  device_info_plus: ^9.0.3       # Device information
  permission_handler: ^11.3.0    # Permission management

  # UI & UX
  flutter_localizations:
    sdk: flutter
  auto_size_text: ^3.0.0          # Responsive text
  flutter_staggered_animations: ^1.1.1 # Animations

dev_dependencies:
  flutter_test:
    sdk: flutter
  integration_test:
    sdk: flutter
  flutter_lints: ^3.0.0
```

### Android Configuration
```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- Device permissions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />

    <!-- NFC permissions -->
    <uses-permission android:name="android.permission.NFC" />
    <uses-feature android:name="android.hardware.nfc" android:required="false" />

    <!-- Bluetooth permissions -->
    <uses-permission android:name="android.permission.BLUETOOTH" />
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
    <uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
    <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />

    <!-- Camera permissions for QR scanning -->
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-feature android:name="android.hardware.camera" android:required="false" />

    <!-- Storage permissions -->
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <application
        android:label="Adara Digital Signage"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher">

        <!-- Main Activity -->
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">

            <meta-data
                android:name="io.flutter.embedding.android.NormalTheme"
                android:resource="@style/NormalTheme" />

            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>

        <!-- Kiosk Mode Service -->
        <service
            android:name=".KioskModeService"
            android:enabled="true"
            android:exported="false" />

    </application>
</manifest>
```

## Screen Specifications

### 1. Setup & Registration Screen

#### Features
- QR code scanning with real-time feedback
- Manual device registration form
- Network connectivity monitoring
- Secure credential storage
- Bilingual UI (Arabic/English)

#### Implementation
```dart
class SetupRegistrationScreen extends StatefulWidget {
  @override
  _SetupRegistrationScreenState createState() => _SetupRegistrationScreenState();
}

class _SetupRegistrationScreenState extends State<SetupRegistrationScreen> {
  final TextEditingController _deviceNameController = TextEditingController();
  final TextEditingController _organizationCodeController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Device Setup')),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16.0),
        child: Column(
          children: [
            // QR Scanner Widget
            Container(
              height: 300,
              child: QRScannerWidget(
                onQRCodeScanned: _handleQRCodeScanned,
              ),
            ),

            // Manual Input Form
            TextField(
              controller: _deviceNameController,
              decoration: InputDecoration(
                labelText: 'Device Name',
                border: OutlineInputBorder(),
              ),
            ),

            SizedBox(height: 16),

            TextField(
              controller: _organizationCodeController,
              decoration: InputDecoration(
                labelText: 'Organization Code',
                border: OutlineInputBorder(),
              ),
            ),

            SizedBox(height: 24),

            ElevatedButton(
              onPressed: _registerDevice,
              child: Text('Register Device'),
              style: ElevatedButton.styleFrom(
                minimumSize: Size(double.infinity, 50),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

### 2. Main Display Screen

#### Features
- Full-screen content rendering
- Multi-zone layout support
- Hardware-accelerated video playback
- Dynamic content scheduling
- Smooth transitions and animations

#### Implementation
```dart
class MainDisplayScreen extends StatefulWidget {
  @override
  _MainDisplayScreenState createState() => _MainDisplayScreenState();
}

class _MainDisplayScreenState extends State<MainDisplayScreen> {
  List<ContentItem> _currentContent = [];
  Timer? _contentTimer;

  @override
  void initState() {
    super.initState();
    _loadContent();
    _startContentRotation();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: _currentContent.map((content) {
          return Positioned(
            left: content.position.x,
            top: content.position.y,
            width: content.size.width,
            height: content.size.height,
            child: ContentWidget(content: content),
          );
        }).toList(),
      ),
    );
  }
}
```

### 3. Interactive & Game Screen

#### Features
- NFC proximity detection
- Bluetooth LE beacon scanning
- Gamified user engagement
- Touch-optimized controls
- Privacy-compliant data collection

#### Implementation
```dart
class InteractiveScreen extends StatefulWidget {
  @override
  _InteractiveScreenState createState() => _InteractiveScreenState();
}

class _InteractiveScreenState extends State<InteractiveScreen> {
  StreamSubscription<NfcData>? _nfcSubscription;
  FlutterBluePlus? _bluetooth;

  @override
  void initState() {
    super.initState();
    _initializeNFC();
    _initializeBluetooth();
  }

  Future<void> _initializeNFC() async {
    bool isAvailable = await NfcManager.instance.isAvailable();
    if (isAvailable) {
      _nfcSubscription = NfcManager.instance.startSession(
        onDiscovered: (NfcTag tag) async {
          // Handle NFC tag discovery
          _handleNFCTag(tag);
        },
      );
    }
  }
}
```

### 4. Status & Diagnostics Screen

#### Features
- Real-time system monitoring
- Network diagnostics
- Content synchronization status
- Administrative controls
- Performance metrics

#### Implementation
```dart
class StatusDiagnosticsScreen extends StatefulWidget {
  @override
  _StatusDiagnosticsScreenState createState() => _StatusDiagnosticsScreenState();
}

class _StatusDiagnosticsScreenState extends State<StatusDiagnosticsScreen> {
  SystemMetrics _metrics = SystemMetrics.empty();

  @override
  void initState() {
    super.initState();
    _startMonitoring();
  }

  void _startMonitoring() {
    Timer.periodic(Duration(seconds: 5), (timer) async {
      final metrics = await _collectSystemMetrics();
      setState(() => _metrics = metrics);
    });
  }
}
```

### 5. Error & Offline Mode Screen

#### Features
- Offline content playback
- Network reconnection monitoring
- Error classification and reporting
- Recovery action suggestions
- Emergency contact information

#### Implementation
```dart
class ErrorOfflineScreen extends StatefulWidget {
  final String errorType;
  final String errorMessage;

  const ErrorOfflineScreen({
    required this.errorType,
    required this.errorMessage,
  });

  @override
  _ErrorOfflineScreenState createState() => _ErrorOfflineScreenState();
}

class _ErrorOfflineScreenState extends State<ErrorOfflineScreen> {
  ConnectivityResult _connectivity = ConnectivityResult.none;

  @override
  void initState() {
    super.initState();
    _monitorConnectivity();
  }

  void _monitorConnectivity() {
    Connectivity().onConnectivityChanged.listen((result) {
      setState(() => _connectivity = result);
      if (result != ConnectivityResult.none) {
        _attemptRecovery();
      }
    });
  }
}
```

## API Integration

### Device Management APIs
```dart
class ApiService {
  final Dio _dio;

  ApiService() : _dio = Dio(BaseOptions(
    baseUrl: 'https://api.adara.com/api/v1',
    connectTimeout: Duration(seconds: 10),
    receiveTimeout: Duration(seconds: 30),
  )) {
    _setupInterceptors();
  }

  void _setupInterceptors() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // Add authentication headers
        final token = await _getAuthToken();
        options.headers['Authorization'] = 'Bearer $token';
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          // Handle token refresh
          await _refreshToken();
          // Retry the request
          final response = await _dio.request(
            error.requestOptions.path,
            options: Options(
              method: error.requestOptions.method,
              headers: error.requestOptions.headers,
            ),
            data: error.requestOptions.data,
          );
          handler.resolve(response);
        } else {
          handler.next(error);
        }
      },
    ));
  }

  Future<DeviceRegistrationResponse> registerDevice(DeviceInfo deviceInfo) async {
    final response = await _dio.post('/device/register', data: deviceInfo.toJson());
    return DeviceRegistrationResponse.fromJson(response.data);
  }

  Future<ContentSyncResponse> syncContent(DateTime lastSync) async {
    final response = await _dio.get('/content/sync', queryParameters: {
      'last_sync': lastSync.toIso8601String(),
    });
    return ContentSyncResponse.fromJson(response.data);
  }

  Future<void> uploadAnalytics(List<AnalyticsEvent> events) async {
    await _dio.post('/analytics/events', data: {
      'events': events.map((e) => e.toJson()).toList(),
    });
  }
}
```

## Data Models

### Core Data Models
```dart
class DeviceInfo {
  final String deviceId;
  final String deviceName;
  final String organizationCode;
  final LocationData location;
  final DeviceCapabilities capabilities;
  final NetworkConfig networkConfig;

  DeviceInfo({
    required this.deviceId,
    required this.deviceName,
    required this.organizationCode,
    required this.location,
    required this.capabilities,
    required this.networkConfig,
  });

  Map<String, dynamic> toJson() => {
    'deviceId': deviceId,
    'deviceName': deviceName,
    'organizationCode': organizationCode,
    'location': location.toJson(),
    'capabilities': capabilities.toJson(),
    'networkConfig': networkConfig.toJson(),
  };
}

class ContentItem {
  final String contentId;
  final ContentType contentType;
  final Duration playbackDuration;
  final ContentPosition position;
  final ContentSize size;
  final int priority;
  final Map<String, dynamic> schedulingRules;

  ContentItem({
    required this.contentId,
    required this.contentType,
    required this.playbackDuration,
    required this.position,
    required this.size,
    required this.priority,
    required this.schedulingRules,
  });
}

class AnalyticsEvent {
  final String eventType;
  final DateTime timestamp;
  final Map<String, dynamic> data;
  final String sessionId;

  AnalyticsEvent({
    required this.eventType,
    required this.timestamp,
    required this.data,
    required this.sessionId,
  });
}
```

## Background Services

### Content Synchronization Service
```dart
class ContentSyncService {
  static const Duration SYNC_INTERVAL = Duration(minutes: 5);

  Timer? _syncTimer;
  final ApiService _apiService;

  ContentSyncService(this._apiService);

  void startSync() {
    _syncTimer = Timer.periodic(SYNC_INTERVAL, (timer) => _performSync());
  }

  Future<void> _performSync() async {
    try {
      final lastSync = await _getLastSyncTime();
      final response = await _apiService.syncContent(lastSync);

      // Process differential updates
      await _processContentUpdates(response.updates);

      // Update last sync time
      await _updateLastSyncTime(DateTime.now());

    } catch (e) {
      // Handle sync errors
      await _handleSyncError(e);
    }
  }

  void stopSync() {
    _syncTimer?.cancel();
    _syncTimer = null;
  }
}
```

### Analytics Collection Service
```dart
class AnalyticsService {
  static const int BATCH_SIZE = 50;
  static const Duration UPLOAD_INTERVAL = Duration(minutes: 10);

  final List<AnalyticsEvent> _eventBuffer = [];
  Timer? _uploadTimer;
  final ApiService _apiService;

  AnalyticsService(this._apiService);

  void startCollection() {
    _uploadTimer = Timer.periodic(UPLOAD_INTERVAL, (timer) => _uploadBatch());
  }

  void trackEvent(String eventType, Map<String, dynamic> data) {
    final event = AnalyticsEvent(
      eventType: eventType,
      timestamp: DateTime.now(),
      data: data,
      sessionId: _getCurrentSessionId(),
    );

    _eventBuffer.add(event);

    // Upload immediately if batch size reached
    if (_eventBuffer.length >= BATCH_SIZE) {
      _uploadBatch();
    }
  }

  Future<void> _uploadBatch() async {
    if (_eventBuffer.isEmpty) return;

    final batch = List<AnalyticsEvent>.from(_eventBuffer);
    _eventBuffer.clear();

    try {
      await _apiService.uploadAnalytics(batch);
    } catch (e) {
      // Re-queue failed events
      _eventBuffer.insertAll(0, batch);
    }
  }
}
```

## Security Implementation

### Secure Storage
```dart
class SecureStorageService {
  static const String DEVICE_TOKEN_KEY = 'device_token';
  static const String REFRESH_TOKEN_KEY = 'refresh_token';
  static const String DEVICE_ID_KEY = 'device_id';

  final FlutterSecureStorage _storage = FlutterSecureStorage();

  Future<void> storeDeviceToken(String token) async {
    await _storage.write(key: DEVICE_TOKEN_KEY, value: token);
  }

  Future<String?> getDeviceToken() async {
    return await _storage.read(key: DEVICE_TOKEN_KEY);
  }

  Future<void> storeCredentials(DeviceCredentials credentials) async {
    final encrypted = await _encryptCredentials(credentials);
    await _storage.write(key: 'credentials', value: encrypted);
  }
}
```

### Certificate Pinning
```dart
class CertificatePinningInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    // Add certificate pinning logic
    options.validateCertificate = (certificate, host, port) {
      // Validate certificate against pinned certificates
      return _validateCertificate(certificate, host);
    };
    handler.next(options);
  }

  bool _validateCertificate(X509Certificate certificate, String host) {
    // Certificate validation logic
    final pinnedCertificates = _getPinnedCertificates(host);
    return pinnedCertificates.contains(certificate.sha256);
  }
}
```

## Performance Optimization

### Memory Management
```dart
class MemoryManager {
  static const int MAX_CACHE_SIZE = 100 * 1024 * 1024; // 100MB

  final Map<String, CachedContent> _cache = {};
  int _currentCacheSize = 0;

  Future<void> cacheContent(String key, CachedContent content) async {
    if (_currentCacheSize + content.size > MAX_CACHE_SIZE) {
      await _evictOldContent(content.size);
    }

    _cache[key] = content;
    _currentCacheSize += content.size;
  }

  Future<void> _evictOldContent(int requiredSize) async {
    final sortedEntries = _cache.entries.toList()
      ..sort((a, b) => a.value.lastAccessed.compareTo(b.value.lastAccessed));

    int freedSize = 0;
    for (final entry in sortedEntries) {
      if (freedSize >= requiredSize) break;

      await entry.value.dispose();
      _cache.remove(entry.key);
      freedSize += entry.value.size;
    }

    _currentCacheSize -= freedSize;
  }
}
```

### Battery Optimization
```dart
class BatteryOptimizationService {
  static const int LOW_BATTERY_THRESHOLD = 20;

  StreamSubscription<BatteryState>? _batterySubscription;

  void startMonitoring() {
    _batterySubscription = Battery().onBatteryStateChanged.listen(
      (BatteryState state) => _handleBatteryStateChange(state),
    );
  }

  void _handleBatteryStateChange(BatteryState state) async {
    final level = await Battery().batteryLevel;

    if (level <= LOW_BATTERY_THRESHOLD) {
      // Enable battery saving mode
      await _enableBatterySavingMode();
    } else {
      // Resume normal operation
      await _disableBatterySavingMode();
    }
  }

  Future<void> _enableBatterySavingMode() async {
    // Reduce sync frequency
    ContentSyncService.instance.setSyncInterval(Duration(minutes: 15));

    // Disable non-essential features
    AnalyticsService.instance.pauseCollection();

    // Reduce screen brightness if possible
    // Adjust content refresh rates
  }
}
```

## Testing Strategy

### Unit Testing
```dart
void main() {
  group('ApiService', () {
    late ApiService apiService;
    late MockDio mockDio;

    setUp(() {
      mockDio = MockDio();
      apiService = ApiService()..dio = mockDio;
    });

    test('registerDevice should return DeviceRegistrationResponse on success', () async {
      final deviceInfo = DeviceInfo(/* test data */);
      final expectedResponse = DeviceRegistrationResponse(/* test data */);

      when(mockDio.post('/device/register', data: deviceInfo.toJson()))
          .thenAnswer((_) async => Response(
                data: expectedResponse.toJson(),
                statusCode: 200,
                requestOptions: RequestOptions(path: '/device/register'),
              ));

      final result = await apiService.registerDevice(deviceInfo);
      expect(result.deviceId, expectedResponse.deviceId);
    });
  });
}
```

### Integration Testing
```dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('end-to-end test', () {
    testWidgets('complete device registration flow', (tester) async {
      await tester.pumpWidget(MyApp());

      // Navigate to setup screen
      expect(find.text('Device Setup'), findsOneWidget);

      // Enter device information
      await tester.enterText(find.byKey(Key('deviceName')), 'Test Device');
      await tester.enterText(find.byKey(Key('organizationCode')), 'TEST123');

      // Tap register button
      await tester.tap(find.text('Register Device'));
      await tester.pumpAndSettle();

      // Verify success
      expect(find.text('Registration Successful'), findsOneWidget);
    });
  });
}
```

## Deployment Strategy

### Build Configuration
```yaml
# flutter_build_config.yaml
targets:
  android-arm64:
    build_type: release
    signing_config: release
    abi_filters: [arm64-v8a]

  android-arm:
    build_type: release
    signing_config: release
    abi_filters: [armeabi-v7a]

  android-x86_64:
    build_type: release
    signing_config: release
    abi_filters: [x86_64]
```

### CI/CD Pipeline
```yaml
# .github/workflows/flutter-deploy.yml
name: Flutter Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Flutter
      uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.24.0'

    - name: Install dependencies
      run: flutter pub get

    - name: Run tests
      run: flutter test

    - name: Build APK
      run: flutter build apk --release

    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: apk-release
        path: build/app/outputs/flutter-apk/app-release.apk
```

## Success Metrics

### Technical KPIs
- **Performance**: 60 FPS animation performance
- **Reliability**: < 0.1% crash rate
- **Battery Life**: 8+ hours continuous operation
- **Sync Efficiency**: < 30 seconds content updates
- **Storage**: < 500MB app footprint

### User Experience KPIs
- **Setup Time**: < 5 minutes device registration
- **Content Loading**: < 2 seconds content transitions
- **Offline Resilience**: 24+ hours cached operation
- **Interactive Response**: < 100ms NFC/Bluetooth detection

### Business KPIs
- **Deployment Success**: 99% successful installations
- **Content Delivery**: 99.9% uptime for content display
- **Analytics Accuracy**: > 95% event capture rate
- **User Engagement**: Measurable interaction improvements

---

**Document Version**: 1.0
**Last Updated**: 2025-08-31
**Next Review**: 2025-09-15
**Owner**: Flutter Development Team
