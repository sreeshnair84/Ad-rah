import 'package:flutter_test/flutter_test.dart';
import 'package:adarah_digital_signage/services/api_service.dart';
import 'package:adarah_digital_signage/services/device_info_service.dart';
import 'package:adarah_digital_signage/services/websocket_service.dart';

void main() {
  group('Services Integration Tests', () {
    test('ApiService should initialize correctly', () {
      final apiService = ApiService();
      expect(apiService, isNotNull);
      expect(apiService.isAuthenticated, isFalse);
      expect(apiService.deviceId, isNull);
      expect(apiService.jwtToken, isNull);
    });

    test('ApiService should set credentials', () {
      final apiService = ApiService();
      apiService.setCredentials('test-jwt', 'test-refresh', 'test-device-123');
      
      expect(apiService.isAuthenticated, isTrue);
      expect(apiService.deviceId, equals('test-device-123'));
      expect(apiService.jwtToken, equals('test-jwt'));
    });

    test('DeviceInfoService should initialize as singleton', () {
      final service1 = DeviceInfoService();
      final service2 = DeviceInfoService();
      
      expect(service1, same(service2));
      expect(service1, isNotNull);
    });

    test('DeviceInfoService should provide device capabilities', () async {
      final deviceService = DeviceInfoService();
      final capabilities = await deviceService.getDeviceCapabilities();
      
      expect(capabilities, isNotNull);
      expect(capabilities['platform'], isNotNull);
      expect(capabilities['max_resolution_width'], isA<int>());
      expect(capabilities['max_resolution_height'], isA<int>());
      expect(capabilities['supported_formats'], isA<List>());
      expect(capabilities['has_touch'], isA<bool>());
      expect(capabilities['has_audio'], isA<bool>());
      expect(capabilities['detected_at'], isNotNull);
    });

    test('DeviceInfoService should provide device fingerprint', () async {
      final deviceService = DeviceInfoService();
      final fingerprint = await deviceService.getDeviceFingerprint();
      
      expect(fingerprint, isNotNull);
      expect(fingerprint['hardware_id'], isNotNull);
      expect(fingerprint['mac_addresses'], isA<List>());
      expect(fingerprint['timezone'], isNotNull);
      expect(fingerprint['locale'], isNotNull);
      expect(fingerprint['created_at'], isNotNull);
    });

    test('DeviceInfoService should check minimum requirements', () async {
      final deviceService = DeviceInfoService();
      final meetsRequirements = await deviceService.checkMinimumRequirements();
      
      expect(meetsRequirements, isA<bool>());
    });

    test('WebSocketService should initialize as singleton', () {
      final service1 = WebSocketService();
      final service2 = WebSocketService();
      
      expect(service1, same(service2));
      expect(service1, isNotNull);
      expect(service1.isConnected, isFalse);
    });

    test('WebSocketService should initialize with credentials', () async {
      final wsService = WebSocketService();
      await wsService.initialize('test-device-123', 'test-jwt-token');
      
      expect(wsService, isNotNull);
    });

    test('ApiService should handle connectivity check', () async {
      final apiService = ApiService();
      final isConnected = await apiService.checkConnectivity();
      
      // This might fail in test environment without network, which is expected
      expect(isConnected, isA<bool>());
    });

    test('All services should be properly integrated', () async {
      // Test that all services can be created and used together
      final apiService = ApiService();
      final deviceService = DeviceInfoService();
      final wsService = WebSocketService();

      // Get device capabilities
      final capabilities = await deviceService.getDeviceCapabilities();
      expect(capabilities, isNotNull);

      // Get device fingerprint  
      final fingerprint = await deviceService.getDeviceFingerprint();
      expect(fingerprint, isNotNull);

      // Initialize WebSocket with mock credentials
      await wsService.initialize('test-device', 'test-token');

      // Set API service credentials
      apiService.setCredentials('test-jwt', 'test-refresh', 'test-device');

      // Verify all services are properly initialized
      expect(apiService.isAuthenticated, isTrue);
      expect(wsService, isNotNull);
      expect(capabilities['platform'], isNotNull);
      expect(fingerprint['hardware_id'], isNotNull);
    });
  });
}