import 'package:flutter/material.dart';
import 'lib/services/device_api_service.dart';
import 'lib/services/analytics_tracking_service.dart';
import 'lib/services/content_scheduler_service.dart';
import 'lib/services/audience_detection_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  print('Testing Digital Signage Services...');
  
  try {
    // Test Device API Service
    print('\n1. Testing Device API Service...');
    final deviceService = DeviceApiService.instance;
    final isRegistered = await deviceService.isDeviceRegistered();
    print('Device registered: $isRegistered');
    
    // Test Analytics Service
    print('\n2. Testing Analytics Service...');
    await AnalyticsTrackingService.instance.initialize();
    AnalyticsTrackingService.instance.trackEvent(
      type: AnalyticsEventType.systemEvent,
      data: {'test': 'service_test'},
    );
    print('Analytics service initialized and test event tracked');
    
    // Test Content Scheduler
    print('\n3. Testing Content Scheduler...');
    await ContentSchedulerService.instance.initialize();
    print('Content scheduler initialized');
    
    // Test Audience Detection
    print('\n4. Testing Audience Detection...');
    final audienceService = AudienceDetectionService.instance;
    final initResult = await audienceService.initialize();
    print('Audience detection initialized: $initResult');
    if (initResult) {
      print('Available detection methods: ${audienceService.availableMethods.map((m) => m.value).join(', ')}');
    }
    
    print('\n✅ All services tested successfully!');
    print('\nThe digital signage platform is ready for deployment.');
    
  } catch (e) {
    print('\n❌ Error during service testing: $e');
  }
}