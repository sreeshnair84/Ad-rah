#!/usr/bin/env python3
"""
Comprehensive RBAC Upload Test Suite
Tests all aspects of the content upload flow with different user roles
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import aiohttp
import aiofiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('rbac_upload_test.log')
    ]
)
logger = logging.getLogger(__name__)

class RBACUploadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.test_users = {
            "SUPER_ADMIN": {
                "email": "admin@adara.com",
                "password": "SuperAdmin123!",
                "expected_upload": True,
                "description": "Platform Super Administrator"
            },
            "HOST_ADMIN": {
                "email": "admin@dubaimall-displays.com",
                "password": "HostAdmin123!",
                "expected_upload": True,
                "description": "HOST Company Administrator"
            },
            "HOST_REVIEWER": {
                "email": "reviewer@dubaimall-displays.com",
                "password": "HostReviewer123!",
                "expected_upload": True,
                "description": "HOST Company Reviewer"
            },
            "HOST_EDITOR": {
                "email": "editor@dubaimall-displays.com",
                "password": "HostEditor123!",
                "expected_upload": True,
                "description": "HOST Company Editor"
            },
            "HOST_VIEWER": {
                "email": "viewer@dubaimall-displays.com",
                "password": "HostViewer123!",
                "expected_upload": True,  # VIEWER has CONTENT_UPLOAD permission according to rbac_models.py
                "description": "HOST Company Viewer"
            },
            "ADVERTISER_ADMIN": {
                "email": "admin@mcdonalds-uae.com",
                "password": "AdvAdmin123!",
                "expected_upload": True,
                "description": "ADVERTISER Company Administrator"
            },
            "ADVERTISER_EDITOR": {
                "email": "editor@mcdonalds-uae.com",
                "password": "AdvEditor123!",
                "expected_upload": True,
                "description": "ADVERTISER Company Editor"
            },
            "ADVERTISER_VIEWER": {
                "email": "viewer@mcdonalds-uae.com",
                "password": "AdvViewer123!",
                "expected_upload": True,
                "description": "ADVERTISER Company Viewer"
            }
        }
    
    async def setup(self):
        """Initialize the test session"""
        self.session = aiohttp.ClientSession()
        logger.info("Test session initialized")
    
    async def teardown(self):
        """Clean up the test session"""
        if self.session:
            await self.session.close()
        logger.info("Test session closed")
    
    async def login_user(self, user_type: str) -> Dict[str, Any]:
        """Login a user and return the response with token"""
        user_info = self.test_users[user_type]
        
        login_data = {
            "email": user_info["email"],
            "password": user_info["password"]
        }
        
        logger.info(f"Attempting login for {user_type}: {user_info['email']}")
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_text = await response.text()
                logger.info(f"Login response status: {response.status}")
                logger.info(f"Login response: {response_text}")
                
                if response.status == 200:
                    login_response = json.loads(response_text)
                    token = login_response.get("access_token")
                    user_data = login_response.get("user")
                    
                    if token and user_data:
                        logger.info(f"✅ Login successful for {user_type}")
                        logger.info(f"User data: {json.dumps(user_data, indent=2)}")
                        return {
                            "success": True,
                            "token": token,
                            "user": user_data,
                            "response": login_response
                        }
                    else:
                        logger.error(f"❌ Login failed - missing token or user data")
                        return {"success": False, "error": "Missing token or user data", "response": response_text}
                else:
                    logger.error(f"❌ Login failed with status {response.status}: {response_text}")
                    return {"success": False, "error": f"HTTP {response.status}", "response": response_text}
                    
        except Exception as e:
            logger.error(f"❌ Login exception for {user_type}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def check_user_permissions(self, token: str, user_type: str) -> Dict[str, Any]:
        """Check user's current permissions and context"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get user profile
            async with self.session.get(
                f"{self.base_url}/api/auth/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    logger.info(f"User profile for {user_type}: {json.dumps(user_data, indent=2)}")
                    
                    # Extract key information
                    permissions = user_data.get("permissions", [])
                    company_role = user_data.get("company_role")
                    user_type_value = user_data.get("user_type")
                    company = user_data.get("company", {})
                    
                    return {
                        "success": True,
                        "permissions": permissions,
                        "company_role": company_role,
                        "user_type": user_type_value,
                        "company": company,
                        "has_content_upload": "content_upload" in permissions,
                        "user_data": user_data
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get user profile: {error_text}")
                    return {"success": False, "error": error_text}
                    
        except Exception as e:
            logger.error(f"Exception checking user permissions: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_content_upload(self, token: str, user_type: str, user_id: str) -> Dict[str, Any]:
        """Test content upload for a specific user"""
        logger.info(f"\n🔄 Testing content upload for {user_type}")
        
        try:
            # Create a test file
            test_file_content = b"Test content for RBAC upload test"
            test_filename = f"test_upload_{user_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            data.add_field('owner_id', user_id)
            data.add_field('file', test_file_content, filename=test_filename, content_type='text/plain')
            
            headers = {"Authorization": f"Bearer {token}"}
            
            async with self.session.post(
                f"{self.base_url}/api/content/upload-file",
                data=data,
                headers=headers
            ) as response:
                response_text = await response.text()
                logger.info(f"Upload response status: {response.status}")
                logger.info(f"Upload response: {response_text}")
                
                if response.status == 200:
                    upload_response = json.loads(response_text)
                    logger.info(f"✅ Upload successful for {user_type}")
                    return {
                        "success": True,
                        "status_code": response.status,
                        "response": upload_response
                    }
                else:
                    logger.error(f"❌ Upload failed for {user_type} with status {response.status}")
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": response_text
                    }
                    
        except Exception as e:
            logger.error(f"❌ Upload exception for {user_type}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_content_listing(self, token: str, user_type: str) -> Dict[str, Any]:
        """Test content listing for a specific user"""
        logger.info(f"\n🔄 Testing content listing for {user_type}")
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            async with self.session.get(
                f"{self.base_url}/api/content/",
                headers=headers
            ) as response:
                response_text = await response.text()
                logger.info(f"Listing response status: {response.status}")
                
                if response.status == 200:
                    content_list = json.loads(response_text)
                    content_count = len(content_list) if isinstance(content_list, list) else 0
                    logger.info(f"✅ Listing successful for {user_type}: {content_count} items")
                    return {
                        "success": True,
                        "status_code": response.status,
                        "content_count": content_count,
                        "response": content_list
                    }
                else:
                    logger.error(f"❌ Listing failed for {user_type} with status {response.status}")
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": response_text
                    }
                    
        except Exception as e:
            logger.error(f"❌ Listing exception for {user_type}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_comprehensive_test_for_user(self, user_type: str) -> Dict[str, Any]:
        """Run complete test suite for a single user type"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 TESTING USER TYPE: {user_type}")
        logger.info(f"📝 Description: {self.test_users[user_type]['description']}")
        logger.info(f"✉️  Email: {self.test_users[user_type]['email']}")
        logger.info(f"🎯 Expected Upload: {self.test_users[user_type]['expected_upload']}")
        logger.info(f"{'='*60}")
        
        test_result = {
            "user_type": user_type,
            "description": self.test_users[user_type]["description"],
            "email": self.test_users[user_type]["email"],
            "expected_upload": self.test_users[user_type]["expected_upload"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Step 1: Login
        login_result = await self.login_user(user_type)
        test_result["login"] = login_result
        
        if not login_result["success"]:
            logger.error(f"❌ Login failed for {user_type}, skipping other tests")
            test_result["overall_result"] = "FAILED - Login"
            return test_result
        
        token = login_result["token"]
        user_data = login_result["user"]
        user_id = user_data.get("id")
        
        if not user_id:
            logger.error(f"❌ No user ID found for {user_type}")
            test_result["overall_result"] = "FAILED - No User ID"
            return test_result
        
        # Step 2: Check permissions
        permissions_result = await self.check_user_permissions(token, user_type)
        test_result["permissions"] = permissions_result
        
        # Step 3: Test content upload
        upload_result = await self.test_content_upload(token, user_type, user_id)
        test_result["upload"] = upload_result
        
        # Step 4: Test content listing
        listing_result = await self.test_content_listing(token, user_type)
        test_result["listing"] = listing_result
        
        # Determine overall result
        expected_upload = self.test_users[user_type]["expected_upload"]
        actual_upload_success = upload_result.get("success", False)
        
        if expected_upload == actual_upload_success:
            if login_result["success"] and listing_result.get("success", False):
                test_result["overall_result"] = "PASSED"
                logger.info(f"✅ ALL TESTS PASSED for {user_type}")
            else:
                test_result["overall_result"] = "PARTIAL - Upload correct, but other issues"
                logger.warning(f"⚠️  PARTIAL SUCCESS for {user_type}")
        else:
            test_result["overall_result"] = "FAILED - Upload permission mismatch"
            if expected_upload:
                logger.error(f"❌ UPLOAD SHOULD WORK but failed for {user_type}")
            else:
                logger.error(f"❌ UPLOAD SHOULD FAIL but succeeded for {user_type}")
        
        return test_result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run tests for all user types"""
        logger.info("\n🚀 STARTING COMPREHENSIVE RBAC UPLOAD TEST SUITE")
        logger.info(f"🎯 Target URL: {self.base_url}")
        logger.info(f"👥 Testing {len(self.test_users)} user types")
        
        await self.setup()
        
        try:
            all_results = []
            
            for user_type in self.test_users.keys():
                result = await self.run_comprehensive_test_for_user(user_type)
                all_results.append(result)
                
                # Add delay between tests to avoid overwhelming the server
                await asyncio.sleep(1)
            
            # Generate summary
            summary = self.generate_test_summary(all_results)
            
            # Save results to file
            await self.save_results_to_file(all_results, summary)
            
            return {
                "summary": summary,
                "detailed_results": all_results
            }
            
        finally:
            await self.teardown()
    
    def generate_test_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of all test results"""
        total_tests = len(results)
        passed_tests = len([r for r in results if r["overall_result"] == "PASSED"])
        failed_tests = len([r for r in results if "FAILED" in r["overall_result"]])
        partial_tests = len([r for r in results if "PARTIAL" in r["overall_result"]])
        
        # Analyze specific issues
        login_failures = [r for r in results if not r.get("login", {}).get("success", False)]
        upload_mismatches = [r for r in results if r["expected_upload"] != r.get("upload", {}).get("success", False)]
        permission_issues = [r for r in results if not r.get("permissions", {}).get("success", False)]
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "partial": partial_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "login_failures": len(login_failures),
            "upload_mismatches": len(upload_mismatches),
            "permission_issues": len(permission_issues),
            "detailed_issues": {
                "login_failures": [{"user_type": r["user_type"], "error": r["login"].get("error")} for r in login_failures],
                "upload_mismatches": [{"user_type": r["user_type"], "expected": r["expected_upload"], "actual": r.get("upload", {}).get("success")} for r in upload_mismatches],
                "permission_issues": [{"user_type": r["user_type"], "error": r["permissions"].get("error")} for r in permission_issues]
            }
        }
        
        return summary
    
    async def save_results_to_file(self, results: List[Dict[str, Any]], summary: Dict[str, Any]):
        """Save test results to a JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rbac_upload_test_results_{timestamp}.json"
        
        output = {
            "test_run_info": {
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "total_users_tested": len(self.test_users)
            },
            "summary": summary,
            "detailed_results": results
        }
        
        try:
            async with aiofiles.open(filename, 'w') as f:
                await f.write(json.dumps(output, indent=2))
            logger.info(f"📁 Test results saved to: {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save results to file: {str(e)}")
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print a formatted summary of test results"""
        logger.info("\n" + "="*80)
        logger.info("📊 TEST SUMMARY REPORT")
        logger.info("="*80)
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"✅ Passed: {summary['passed']}")
        logger.info(f"❌ Failed: {summary['failed']}")
        logger.info(f"⚠️  Partial: {summary['partial']}")
        logger.info(f"🎯 Success Rate: {summary['success_rate']}")
        logger.info("-" * 80)
        
        if summary['login_failures'] > 0:
            logger.error(f"🔐 Login Failures: {summary['login_failures']}")
            for failure in summary['detailed_issues']['login_failures']:
                logger.error(f"   - {failure['user_type']}: {failure['error']}")
        
        if summary['upload_mismatches'] > 0:
            logger.error(f"📤 Upload Permission Mismatches: {summary['upload_mismatches']}")
            for mismatch in summary['detailed_issues']['upload_mismatches']:
                logger.error(f"   - {mismatch['user_type']}: Expected {mismatch['expected']}, Got {mismatch['actual']}")
        
        if summary['permission_issues'] > 0:
            logger.error(f"🛡️  Permission Check Issues: {summary['permission_issues']}")
            for issue in summary['detailed_issues']['permission_issues']:
                logger.error(f"   - {issue['user_type']}: {issue['error']}")
        
        logger.info("="*80)

async def main():
    """Main test execution function"""
    # Check if server URL is provided
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    logger.info(f"🎯 Testing against server: {server_url}")
    
    # Initialize tester
    tester = RBACUploadTester(base_url=server_url)
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print summary
        tester.print_summary(results["summary"])
        
        # Return appropriate exit code
        if results["summary"]["failed"] == 0:
            logger.info("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            return 0
        else:
            logger.error("❌ SOME TESTS FAILED!")
            return 1
            
    except KeyboardInterrupt:
        logger.warning("⚠️  Test interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"💥 Test suite failed with exception: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
