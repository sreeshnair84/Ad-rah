#!/usr/bin/env python3
"""
API Testing Script for Device Registration and Management

This script tests the complete device lifecycle:
1. Device registration via API
2. Device listing via API  
3. Content management for devices
4. Screen/kiosk management

Usage:
    # Start the backend first:
    # uv run uvicorn app.main:app --reload --port 8000
    
    # Then run tests:
    # python api_test.py
"""

import asyncio
import httpx
import json
import os
from typing import Dict, Optional
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeviceAPITester:
    """Test device APIs end-to-end"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.auth_token = None
        self.device_id = None
        
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def authenticate_as_super_user(self) -> bool:
        """Authenticate as super user to get API access"""
        try:
            logger.info("🔐 Authenticating as super user...")
            
            # First, let's try to login
            login_data = {
                "email": "admin@adara.com", 
                "password": "SuperAdmin123!"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result.get("access_token")
                logger.info("✅ Authentication successful")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if not self.auth_token:
            return {}
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def test_device_registration(self) -> bool:
        """Test device registration via API"""
        try:
            logger.info("📱 Testing device registration via API...")
            
            registration_data = {
                "device_name": "API-Test-Device-001", 
                "organization_code": "ORG-TEST001",
                "registration_key": "rV7Xh1aWhgmUN1Su",  # Fresh key we created
                "location_description": "API Test Location",
                "aspect_ratio": "16:9",
                "device_type": "KIOSK"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/devices/register",
                json=registration_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.device_id = result.get("device_id")
                    logger.info(f"✅ Device registered via API: {self.device_id}")
                    logger.info(f"   Company: {result.get('company_name')}")
                    logger.info(f"   Organization: {result.get('organization_code')}")
                    logger.info(f"   JWT Token: {'Present' if result.get('jwt_token') else 'Missing'}")
                    return True
                else:
                    logger.error(f"❌ Registration failed: {result}")
                    return False
            else:
                logger.error(f"❌ API registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Device registration test failed: {e}")
            return False
    
    async def test_device_listing(self) -> bool:
        """Test device listing via API"""
        try:
            logger.info("📋 Testing device listing via API...")
            
            response = await self.client.get(
                f"{self.base_url}/api/devices/",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                devices = response.json()
                logger.info(f"✅ Device listing successful: {len(devices)} devices found")
                
                for device in devices:
                    logger.info(f"   Device: {device.get('name')} ({device.get('id')})")
                    logger.info(f"   Company: {device.get('company_id')}")
                    logger.info(f"   Status: {device.get('status')}")
                
                return True
            else:
                logger.error(f"❌ Device listing failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Device listing test failed: {e}")
            return False
    
    async def test_registration_keys_listing(self) -> bool:
        """Test registration keys listing via API"""
        try:
            logger.info("🔑 Testing registration keys listing...")
            
            response = await self.client.get(
                f"{self.base_url}/api/devices/keys",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                keys = response.json()
                logger.info(f"✅ Registration keys listing successful: {len(keys)} keys found")
                
                for key in keys:
                    logger.info(f"   Key: {key.get('key')} (Company: {key.get('company_name')})")
                    logger.info(f"   Used: {key.get('used')}, Expires: {key.get('expires_at')}")
                
                return True
            else:
                logger.error(f"❌ Registration keys listing failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Registration keys test failed: {e}")
            return False
    
    async def test_device_by_organization(self) -> bool:
        """Test getting devices by organization code"""
        try:
            logger.info("🏢 Testing devices by organization...")
            
            response = await self.client.get(
                f"{self.base_url}/api/devices/organization/ORG-TEST001",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Organization devices listing successful")
                logger.info(f"   Organization: {result.get('organization_code')}")
                logger.info(f"   Company: {result.get('company_name')}")
                logger.info(f"   Total devices: {result.get('total')}")
                logger.info(f"   Online: {result.get('online')}, Offline: {result.get('offline')}")
                
                return True
            else:
                logger.error(f"❌ Organization devices failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Organization devices test failed: {e}")
            return False
    
    async def test_frontend_device_api(self) -> bool:
        """Test frontend device API proxy"""
        try:
            logger.info("🌐 Testing frontend device API...")
            
            # Test the frontend proxy endpoint
            response = await self.client.get(
                "http://localhost:3000/api/device",  # Frontend proxy
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                devices = response.json()
                logger.info(f"✅ Frontend device API successful: {len(devices)} devices found")
                return True
            else:
                logger.warning(f"⚠️  Frontend API not available: {response.status_code}")
                logger.info("   This is OK if frontend is not running")
                return True  # Don't fail the test for this
                
        except Exception as e:
            logger.warning(f"⚠️  Frontend API test failed (expected if not running): {e}")
            return True  # Don't fail the test for this
    
    async def test_health_check(self) -> bool:
        """Test API health check"""
        try:
            logger.info("❤️  Testing API health check...")
            
            response = await self.client.get(f"{self.base_url}/api/auth/health")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Health check passed")
                logger.info(f"   Status: {result.get('status')}")
                logger.info(f"   Database: {result.get('database')}")
                logger.info(f"   Timestamp: {result.get('timestamp')}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all API tests"""
        logger.info("🚀 Starting comprehensive API tests...")
        
        # Test health check first
        if not await self.test_health_check():
            logger.error("❌ Backend not available or unhealthy")
            return False
        
        # Authenticate
        if not await self.authenticate_as_super_user():
            logger.error("❌ Authentication failed - cannot continue tests")
            return False
        
        # Run all tests
        tests = [
            ("Device Registration", self.test_device_registration),
            ("Device Listing", self.test_device_listing),
            ("Registration Keys", self.test_registration_keys_listing),
            ("Organization Devices", self.test_device_by_organization),
            ("Frontend API", self.test_frontend_device_api),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
                else:
                    failed += 1
                    logger.error(f"❌ {test_name} test failed")
            except Exception as e:
                failed += 1
                logger.error(f"❌ {test_name} test crashed: {e}")
        
        # Report results
        logger.info("")
        logger.info("📊 TEST RESULTS:")
        logger.info(f"   ✅ Passed: {passed}")
        logger.info(f"   ❌ Failed: {failed}")
        logger.info(f"   📊 Success Rate: {passed}/{passed+failed}")
        
        if failed == 0:
            logger.info("🎉 All API tests passed!")
            return True
        else:
            logger.error("💥 Some tests failed")
            return False

async def main():
    """Main test function"""
    tester = DeviceAPITester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            logger.info("")
            logger.info("✅ ALL TESTS PASSED!")
            logger.info("")
            logger.info("🔧 Your device registration system is working correctly:")
            logger.info("   • Backend APIs are functional")
            logger.info("   • Device registration works")
            logger.info("   • Device listing works")  
            logger.info("   • Registration key management works")
            logger.info("   • Organization-based device queries work")
            logger.info("")
            logger.info("📱 Flutter app can now register devices using:")
            logger.info("   • Registration Key: nZ2CB2bX472WhaOq")
            logger.info("   • Organization Code: ORG-TEST001")
            logger.info("   • API Endpoint: http://localhost:8000/api/devices/register")
            logger.info("")
        else:
            logger.error("❌ SOME TESTS FAILED!")
            logger.error("Check the logs above for details")
            exit(1)
            
    finally:
        await tester.close()

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())