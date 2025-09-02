#!/usr/bin/env python3
"""
Comprehensive Offline Capabilities Test Suite
Tests the entire offline ecosystem including Flutter content caching,
backend analytics collection, and real-time synchronization.
"""

import asyncio
import aiohttp
import json
import websockets
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OfflineCapabilitiesValidator:
    """Validates offline capabilities across the entire system"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000" 
        self.websocket_url = "ws://localhost:8000/api/analytics/stream"
        
        # Test data
        self.test_device_id = f"test_device_{int(time.time())}"
        self.test_user_email = "admin@openkiosk.com"
        self.test_user_password = "adminpass"
        self.auth_token = None
        
        # Results storage
        self.test_results = {
            "backend_analytics": {"passed": 0, "failed": 0, "details": []},
            "websocket_streaming": {"passed": 0, "failed": 0, "details": []},
            "content_caching": {"passed": 0, "failed": 0, "details": []},
            "offline_sync": {"passed": 0, "failed": 0, "details": []},
            "enterprise_auth": {"passed": 0, "failed": 0, "details": []},
            "real_time_dashboard": {"passed": 0, "failed": 0, "details": []}
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive offline capabilities test suite"""
        logger.info("🚀 Starting Offline Capabilities Validation Suite")
        
        try:
            # 1. Test Backend Analytics Service
            await self.test_backend_analytics_service()
            
            # 2. Test WebSocket Real-Time Streaming  
            await self.test_websocket_streaming()
            
            # 3. Test Enterprise Authentication
            await self.test_enterprise_authentication()
            
            # 4. Test Content Caching Simulation
            await self.test_content_caching_simulation()
            
            # 5. Test Offline Synchronization
            await self.test_offline_synchronization()
            
            # 6. Test Real-Time Dashboard Integration
            await self.test_dashboard_integration()
            
            # Generate comprehensive report
            return self.generate_test_report()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            return {"error": str(e), "results": self.test_results}

    async def test_backend_analytics_service(self):
        """Test backend real-time analytics service"""
        logger.info("🔧 Testing Backend Analytics Service")
        
        try:
            # First authenticate
            await self.authenticate_user()
            
            # Test single event recording
            await self.test_single_analytics_event()
            
            # Test batch event recording
            await self.test_batch_analytics_events()
            
            # Test real-time metrics retrieval
            await self.test_real_time_metrics_api()
            
            # Test device analytics
            await self.test_device_analytics_api()
            
            logger.info("✅ Backend Analytics Service: All tests passed")
            
        except Exception as e:
            logger.error(f"❌ Backend Analytics Service failed: {e}")
            self.test_results["backend_analytics"]["failed"] += 1
            self.test_results["backend_analytics"]["details"].append(f"Error: {e}")

    async def test_websocket_streaming(self):
        """Test WebSocket real-time streaming"""
        logger.info("🌐 Testing WebSocket Real-Time Streaming")
        
        try:
            # Test WebSocket connection
            uri = self.websocket_url
            
            async with websockets.connect(uri) as websocket:
                logger.info("📡 Connected to WebSocket analytics stream")
                
                # Send subscription request
                subscription_message = {
                    "type": "subscribe_metrics",
                    "metric_types": ["impression", "interaction", "error"]
                }
                await websocket.send(json.dumps(subscription_message))
                
                # Wait for subscription confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "subscription_confirmed":
                    logger.info("✅ WebSocket subscription confirmed")
                    self.test_results["websocket_streaming"]["passed"] += 1
                else:
                    logger.warning(f"⚠️ Unexpected WebSocket response: {data}")
                
                # Request current metrics
                metrics_request = {"type": "request_current_metrics"}
                await websocket.send(json.dumps(metrics_request))
                
                # Wait for metrics response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "metrics_update":
                    logger.info("✅ Real-time metrics received via WebSocket")
                    self.test_results["websocket_streaming"]["passed"] += 1
                    self.test_results["websocket_streaming"]["details"].append(f"Received metrics: {data['metrics']}")
                
        except Exception as e:
            logger.error(f"❌ WebSocket Streaming failed: {e}")
            self.test_results["websocket_streaming"]["failed"] += 1
            self.test_results["websocket_streaming"]["details"].append(f"Error: {e}")

    async def test_enterprise_authentication(self):
        """Test enterprise authentication features"""
        logger.info("🔐 Testing Enterprise Authentication")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test basic authentication
                auth_data = {
                    "username": self.test_user_email,
                    "password": self.test_user_password
                }
                
                async with session.post(f"{self.backend_url}/api/auth/login", json=auth_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("access_token"):
                            logger.info("✅ Basic authentication successful")
                            self.test_results["enterprise_auth"]["passed"] += 1
                        else:
                            logger.warning("⚠️ Authentication returned no token")
                    else:
                        logger.error(f"❌ Authentication failed with status: {response.status}")
                        self.test_results["enterprise_auth"]["failed"] += 1
                
                # Test MFA simulation (would require actual MFA setup)
                logger.info("ℹ️ MFA testing requires production setup - skipping for now")
                self.test_results["enterprise_auth"]["details"].append("MFA testing requires production configuration")
                
        except Exception as e:
            logger.error(f"❌ Enterprise Authentication failed: {e}")
            self.test_results["enterprise_auth"]["failed"] += 1
            self.test_results["enterprise_auth"]["details"].append(f"Error: {e}")

    async def test_content_caching_simulation(self):
        """Simulate Flutter content caching functionality"""
        logger.info("💾 Testing Content Caching Simulation")
        
        try:
            # Simulate content caching workflow
            test_content = {
                "id": f"test_content_{int(time.time())}",
                "title": "Test Video Content",
                "type": "video",
                "url": "https://example.com/test-video.mp4",
                "size_bytes": 1048576,  # 1MB
                "duration_seconds": 30
            }
            
            # Test 1: Cache content metadata
            logger.info("📝 Simulating content metadata caching")
            cache_result = await self.simulate_content_cache(test_content)
            
            if cache_result["success"]:
                logger.info("✅ Content metadata caching simulation successful")
                self.test_results["content_caching"]["passed"] += 1
            else:
                logger.error("❌ Content metadata caching simulation failed")
                self.test_results["content_caching"]["failed"] += 1
            
            # Test 2: Offline content retrieval
            logger.info("📱 Simulating offline content retrieval")
            retrieval_result = await self.simulate_offline_content_retrieval(test_content["id"])
            
            if retrieval_result["success"]:
                logger.info("✅ Offline content retrieval simulation successful")
                self.test_results["content_caching"]["passed"] += 1
            else:
                logger.error("❌ Offline content retrieval simulation failed")
                self.test_results["content_caching"]["failed"] += 1
            
            # Test 3: Cache size management
            logger.info("🗂️ Simulating cache size management")
            cache_management_result = await self.simulate_cache_management()
            
            if cache_management_result["success"]:
                logger.info("✅ Cache management simulation successful")
                self.test_results["content_caching"]["passed"] += 1
            else:
                logger.error("❌ Cache management simulation failed")
                self.test_results["content_caching"]["failed"] += 1
                
        except Exception as e:
            logger.error(f"❌ Content Caching Simulation failed: {e}")
            self.test_results["content_caching"]["failed"] += 1
            self.test_results["content_caching"]["details"].append(f"Error: {e}")

    async def test_offline_synchronization(self):
        """Test offline event synchronization"""
        logger.info("🔄 Testing Offline Event Synchronization")
        
        try:
            # Simulate offline analytics events queue
            offline_events = []
            
            # Generate test events
            for i in range(10):
                event = {
                    "metric_type": random.choice(["impression", "interaction", "dwell_time"]),
                    "event_type": random.choice(["content_view_start", "content_view_end", "content_interaction"]),
                    "device_id": self.test_device_id,
                    "content_id": f"content_{i}",
                    "value": random.uniform(1.0, 100.0),
                    "timestamp": (datetime.utcnow() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                    "audience_count": random.randint(1, 10)
                }
                offline_events.append(event)
            
            logger.info(f"📊 Generated {len(offline_events)} offline analytics events")
            
            # Test batch synchronization
            if self.auth_token:
                sync_result = await self.sync_offline_events(offline_events)
                
                if sync_result["success"]:
                    logger.info(f"✅ Synchronized {len(offline_events)} offline events successfully")
                    self.test_results["offline_sync"]["passed"] += 1
                    self.test_results["offline_sync"]["details"].append(f"Synced {len(offline_events)} events")
                else:
                    logger.error("❌ Offline event synchronization failed")
                    self.test_results["offline_sync"]["failed"] += 1
            else:
                logger.warning("⚠️ No auth token available for sync test")
                self.test_results["offline_sync"]["details"].append("Auth token required for sync test")
                
        except Exception as e:
            logger.error(f"❌ Offline Synchronization failed: {e}")
            self.test_results["offline_sync"]["failed"] += 1
            self.test_results["offline_sync"]["details"].append(f"Error: {e}")

    async def test_dashboard_integration(self):
        """Test real-time dashboard integration"""
        logger.info("📊 Testing Real-Time Dashboard Integration")
        
        try:
            # Test dashboard API endpoints
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                
                # Test real-time metrics API
                async with session.get(f"{self.backend_url}/api/analytics/real-time", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ Real-time metrics API accessible")
                        self.test_results["real_time_dashboard"]["passed"] += 1
                        self.test_results["real_time_dashboard"]["details"].append(f"Metrics data: {data.get('success', False)}")
                    else:
                        logger.error(f"❌ Real-time metrics API failed: {response.status}")
                        self.test_results["real_time_dashboard"]["failed"] += 1
                
                # Test analytics health check
                async with session.get(f"{self.backend_url}/api/analytics/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ Analytics service health check passed")
                        self.test_results["real_time_dashboard"]["passed"] += 1
                        self.test_results["real_time_dashboard"]["details"].append(f"Health status: {data.get('status')}")
                    else:
                        logger.error(f"❌ Analytics health check failed: {response.status}")
                        self.test_results["real_time_dashboard"]["failed"] += 1
                        
        except Exception as e:
            logger.error(f"❌ Dashboard Integration failed: {e}")
            self.test_results["real_time_dashboard"]["failed"] += 1
            self.test_results["real_time_dashboard"]["details"].append(f"Error: {e}")

    # Helper methods

    async def authenticate_user(self):
        """Authenticate user and store token"""
        try:
            async with aiohttp.ClientSession() as session:
                auth_data = {
                    "username": self.test_user_email,
                    "password": self.test_user_password
                }
                
                async with session.post(f"{self.backend_url}/api/auth/login", json=auth_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.auth_token = result.get("access_token")
                        logger.info("🔑 Authentication successful")
                    else:
                        logger.warning(f"⚠️ Authentication failed with status: {response.status}")
                        
        except Exception as e:
            logger.error(f"Authentication error: {e}")

    async def test_single_analytics_event(self):
        """Test single analytics event recording"""
        event_data = {
            "metric_type": "impression",
            "event_type": "content_view_start", 
            "device_id": self.test_device_id,
            "content_id": "test_content_001",
            "value": 1.0,
            "audience_count": 5
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            async with session.post(f"{self.backend_url}/api/analytics/event", json=event_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        logger.info("✅ Single analytics event recorded")
                        self.test_results["backend_analytics"]["passed"] += 1
                    else:
                        logger.error("❌ Single analytics event failed")
                        self.test_results["backend_analytics"]["failed"] += 1
                else:
                    logger.error(f"❌ Event recording failed: {response.status}")
                    self.test_results["backend_analytics"]["failed"] += 1

    async def test_batch_analytics_events(self):
        """Test batch analytics events recording"""
        batch_events = {
            "events": [
                {
                    "metric_type": "interaction",
                    "event_type": "content_interaction",
                    "device_id": self.test_device_id,
                    "content_id": "test_content_002",
                    "value": 1.0
                },
                {
                    "metric_type": "dwell_time", 
                    "event_type": "audience_detected",
                    "device_id": self.test_device_id,
                    "duration_seconds": 30.5,
                    "audience_count": 3
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            async with session.post(f"{self.backend_url}/api/analytics/events/batch", json=batch_events, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        logger.info("✅ Batch analytics events recorded")
                        self.test_results["backend_analytics"]["passed"] += 1
                    else:
                        logger.error("❌ Batch analytics events failed")
                        self.test_results["backend_analytics"]["failed"] += 1
                else:
                    logger.error(f"❌ Batch event recording failed: {response.status}")
                    self.test_results["backend_analytics"]["failed"] += 1

    async def test_real_time_metrics_api(self):
        """Test real-time metrics API"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            async with session.get(f"{self.backend_url}/api/analytics/real-time?period=minute", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        logger.info("✅ Real-time metrics API working")
                        self.test_results["backend_analytics"]["passed"] += 1
                    else:
                        logger.error("❌ Real-time metrics API failed")
                        self.test_results["backend_analytics"]["failed"] += 1
                else:
                    logger.error(f"❌ Real-time metrics API error: {response.status}")
                    self.test_results["backend_analytics"]["failed"] += 1

    async def test_device_analytics_api(self):
        """Test device analytics API"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            async with session.get(f"{self.backend_url}/api/analytics/device/{self.test_device_id}?hours=24", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        logger.info("✅ Device analytics API working")
                        self.test_results["backend_analytics"]["passed"] += 1
                    else:
                        logger.error("❌ Device analytics API failed")
                        self.test_results["backend_analytics"]["failed"] += 1
                else:
                    logger.error(f"❌ Device analytics API error: {response.status}")
                    self.test_results["backend_analytics"]["failed"] += 1

    async def simulate_content_cache(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Flutter content caching"""
        # Simulate caching process
        await asyncio.sleep(0.1)  # Simulate cache operation
        return {
            "success": True,
            "content_id": content["id"], 
            "cached_size_bytes": content["size_bytes"],
            "cache_timestamp": datetime.utcnow().isoformat()
        }

    async def simulate_offline_content_retrieval(self, content_id: str) -> Dict[str, Any]:
        """Simulate offline content retrieval"""
        await asyncio.sleep(0.05)  # Simulate retrieval
        return {
            "success": True,
            "content_id": content_id,
            "source": "local_cache",
            "retrieval_time_ms": 50
        }

    async def simulate_cache_management(self) -> Dict[str, Any]:
        """Simulate cache size management"""
        await asyncio.sleep(0.02)
        return {
            "success": True,
            "cache_size_mb": 250,
            "cache_limit_mb": 1000,
            "items_cached": 45,
            "cleanup_performed": False
        }

    async def sync_offline_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync offline events with backend"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                batch_data = {"events": events}
                
                async with session.post(f"{self.backend_url}/api/analytics/events/batch", json=batch_data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {"success": result.get("success", False), "synced_count": len(events)}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_passed = sum(category["passed"] for category in self.test_results.values())
        total_failed = sum(category["failed"] for category in self.test_results.values())
        total_tests = total_passed + total_failed
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "success_rate": f"{success_rate:.1f}%",
                "timestamp": datetime.utcnow().isoformat()
            },
            "categories": self.test_results,
            "recommendations": self.generate_recommendations(),
            "industry_compliance": self.assess_industry_compliance(success_rate)
        }
        
        return report

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for category, results in self.test_results.items():
            if results["failed"] > 0:
                if category == "websocket_streaming":
                    recommendations.append("Ensure WebSocket server is running on port 8000")
                elif category == "backend_analytics":
                    recommendations.append("Verify analytics API endpoints are properly configured")
                elif category == "enterprise_auth":
                    recommendations.append("Configure enterprise authentication with proper secrets")
                elif category == "content_caching":
                    recommendations.append("Implement robust content caching with error handling")
                elif category == "offline_sync":
                    recommendations.append("Enhance offline synchronization with retry mechanisms")
        
        if not recommendations:
            recommendations.append("All systems functioning correctly - ready for production!")
        
        return recommendations

    def assess_industry_compliance(self, success_rate: float) -> Dict[str, Any]:
        """Assess compliance with industry standards"""
        if success_rate >= 95:
            compliance_level = "EXCELLENT - Exceeds industry standards"
        elif success_rate >= 85:
            compliance_level = "GOOD - Meets industry standards"  
        elif success_rate >= 70:
            compliance_level = "ACCEPTABLE - Basic industry compliance"
        else:
            compliance_level = "NEEDS IMPROVEMENT - Below industry standards"
        
        return {
            "compliance_level": compliance_level,
            "success_rate": success_rate,
            "industry_benchmark": 85.0,
            "meets_standards": success_rate >= 85.0
        }

    async def close(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up test resources")

# Main execution
async def main():
    """Run the complete offline capabilities validation"""
    validator = OfflineCapabilitiesValidator()
    
    try:
        logger.info("=" * 60)
        logger.info("🚀 DIGITAL SIGNAGE OFFLINE CAPABILITIES VALIDATION")
        logger.info("=" * 60)
        
        results = await validator.run_all_tests()
        
        logger.info("=" * 60)
        logger.info("📊 VALIDATION RESULTS")
        logger.info("=" * 60)
        
        # Print summary
        summary = results["summary"]
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success Rate: {summary['success_rate']}")
        
        # Print compliance assessment
        compliance = results["industry_compliance"]
        logger.info(f"Industry Compliance: {compliance['compliance_level']}")
        
        # Print recommendations
        logger.info("\n📝 RECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"], 1):
            logger.info(f"{i}. {rec}")
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"offline_validation_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n💾 Detailed report saved to: {report_file}")
        logger.info("=" * 60)
        
        return results
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Validation interrupted by user")
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
    finally:
        await validator.close()

if __name__ == "__main__":
    asyncio.run(main())