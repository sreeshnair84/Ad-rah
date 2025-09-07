#!/usr/bin/env python3
"""
Comprehensive End-to-End RBAC Testing Script
Adara Screen Digital Signage Platform - Enhanced RBAC System

This script tests all persona-based access scenarios and API functionality
"""

import asyncio
import json
import requests
import time
from typing import Dict, List, Optional, Any
import os
from datetime import datetime

# Test Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_RESULTS: List[Dict] = []

# Test Users (from seed data)
TEST_PERSONAS = {
    "SUPER_USER": {
        "email": "admin@adara.com",
        "password": "SuperAdmin123!",
        "expected_permissions": 27,  # All permissions
        "expected_navigation": ["dashboard", "users", "content", "upload", "analytics", "settings"],
        "description": "Platform Administrator with full access"
    },
    "HOST_ADMIN": {
        "email": "admin@dubaimall-displays.com", 
        "password": "HostAdmin123!",
        "expected_permissions": 23,  # HOST company admin permissions (no device sharing)
        "expected_navigation": ["dashboard", "users", "content", "upload", "analytics", "settings"],
        "description": "HOST Company Administrator"
    },
    "HOST_REVIEWER": {
        "email": "reviewer@dubaimall-displays.com",
        "password": "HostReviewer123!",
        "expected_permissions": 9,   # HOST reviewer permissions
        "expected_navigation": ["dashboard", "users", "content", "analytics"],
        "description": "HOST Company Reviewer (Limited Access)"
    },
    "HOST_EDITOR": {
        "email": "editor@dubaimall-displays.com",
        "password": "HostEditor123!",
        "expected_permissions": 6,   # HOST editor permissions
        "expected_navigation": ["dashboard", "content", "upload", "analytics"],
        "description": "HOST Company Editor"
    },
    "HOST_VIEWER": {
        "email": "viewer@dubaimall-displays.com", 
        "password": "HostViewer123!",
        "expected_permissions": 3,   # HOST viewer permissions
        "expected_navigation": ["dashboard", "content", "upload", "analytics"],
        "description": "HOST Company Viewer (Read-only)"
    },
    "ADVERTISER_ADMIN": {
        "email": "admin@emirates-digital.ae",
        "password": "AdvAdmin123!",
        "expected_permissions": 15,  # ADVERTISER admin permissions (no device management)
        "expected_navigation": ["dashboard", "users", "content", "upload", "analytics", "settings"],
        "description": "ADVERTISER Company Administrator"
    },
    "ADVERTISER_REVIEWER": {
        "email": "reviewer@emirates-digital.ae",
        "password": "AdvReviewer123!",
        "expected_permissions": 7,   # ADVERTISER reviewer permissions
        "expected_navigation": ["dashboard", "users", "content", "analytics"],
        "description": "ADVERTISER Company Reviewer"
    }
}

class RBACTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.current_token = None
        self.current_user = None
        
    def log_result(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test results"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        TEST_RESULTS.append(result)
        
        # Color coding for console output
        colors = {"PASS": "\033[92m", "FAIL": "\033[91m", "INFO": "\033[94m", "END": "\033[0m"}
        color = colors.get(status, colors["INFO"])
        
        print(f"{color}[{status}] {test_name}: {message}{colors['END']}")
        if details and status == "FAIL":
            print(f"  Details: {json.dumps(details, indent=2)}")
    
    def login_user(self, persona_key: str) -> bool:
        """Login as a specific test persona"""
        persona = TEST_PERSONAS[persona_key]
        
        try:
            response = self.session.post(
                f"{FRONTEND_URL}/api/auth/login",
                json={"email": persona["email"], "password": persona["password"]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_token = data["access_token"]
                self.current_user = data["user"]
                
                # Verify expected permissions count
                actual_permissions = len(self.current_user["permissions"])
                expected_permissions = persona["expected_permissions"]
                
                if actual_permissions != expected_permissions:
                    self.log_result(
                        f"Login {persona_key}",
                        "FAIL",
                        f"Permission count mismatch: expected {expected_permissions}, got {actual_permissions}",
                        {"expected": expected_permissions, "actual": actual_permissions, "permissions": self.current_user["permissions"]}
                    )
                    return False
                
                self.log_result(f"Login {persona_key}", "PASS", f"Authenticated successfully with {actual_permissions} permissions")
                return True
            else:
                self.log_result(f"Login {persona_key}", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result(f"Login {persona_key}", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_endpoint(self, endpoint: str, method: str = "GET", data: Dict = None, expected_status: int = 200) -> Dict:
        """Test a specific API endpoint"""
        headers = {"Content-Type": "application/json"}
        if self.current_token:
            headers["Authorization"] = f"Bearer {self.current_token}"
        
        try:
            if method == "GET":
                response = self.session.get(f"{FRONTEND_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = self.session.post(f"{FRONTEND_URL}{endpoint}", json=data, headers=headers)
            elif method == "PUT":
                response = self.session.put(f"{FRONTEND_URL}{endpoint}", json=data, headers=headers)
            elif method == "DELETE":
                response = self.session.delete(f"{FRONTEND_URL}{endpoint}", headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return {
                "status_code": response.status_code,
                "success": response.status_code == expected_status,
                "response": response.text[:500] if response.text else "",
                "headers": dict(response.headers)
            }
            
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "error": str(e),
                "response": "",
                "headers": {}
            }
    
    def test_persona_endpoints(self, persona_key: str):
        """Test all relevant endpoints for a specific persona"""
        persona = TEST_PERSONAS[persona_key]
        user_type = self.current_user.get("user_type")
        company_type = self.current_user.get("company", {}).get("company_type")
        company_role = self.current_user.get("company_role")
        
        print(f"\n{'='*60}")
        print(f"Testing {persona_key}: {persona['description']}")
        print(f"User Type: {user_type}, Company Type: {company_type}, Role: {company_role}")
        print(f"{'='*60}")
        
        # Test basic endpoints that all authenticated users should access
        basic_endpoints = [
            ("/api/auth/me", "GET", 200),
            ("/api/auth/companies", "GET", 200),
            ("/api/auth/navigation", "GET", 200)
        ]
        
        for endpoint, method, expected_status in basic_endpoints:
            result = self.test_endpoint(endpoint, method, expected_status=expected_status)
            status = "PASS" if result["success"] else "FAIL"
            self.log_result(
                f"{persona_key} - {endpoint}",
                status,
                f"{method} {endpoint} -> {result['status_code']}",
                result if not result["success"] else None
            )
        
        # Test permission-based endpoints
        permission_tests = [
            # User management (requires user_read permission)
            ("/api/auth/users", "GET", user_type == "SUPER_USER" or company_role in ["ADMIN", "REVIEWER"]),
            
            # User creation (requires user_create permission) 
            ("/api/auth/users", "POST", user_type == "SUPER_USER" or company_role == "ADMIN", {
                "first_name": f"Test{int(time.time())}",
                "last_name": "User", 
                "email": f"test{int(time.time())}@example.com",
                "password": "Test123!",
                "user_type": "COMPANY_USER",
                "company_id": self.current_user.get("company_id", "company_host_dubai_mall"),
                "company_role": "VIEWER"
            }),
            
            # Settings (requires settings_read permission)
            # Note: This would need actual settings endpoint
        ]
        
        for endpoint, method, should_succeed, *args in permission_tests:
            data = args[0] if args else None
            expected_status = 200 if should_succeed else 403
            
            result = self.test_endpoint(endpoint, method, data, expected_status)
            
            if should_succeed:
                status = "PASS" if result["success"] else "FAIL"
                message = f"Authorized access granted ({result['status_code']})"
            else:
                status = "PASS" if result["status_code"] == 403 else "FAIL"
                message = f"Access properly denied ({result['status_code']})"
                
            self.log_result(
                f"{persona_key} - {method} {endpoint}",
                status,
                message,
                result if status == "FAIL" else None
            )
    
    def test_navigation_access(self, persona_key: str):
        """Test navigation access based on user permissions"""
        persona = TEST_PERSONAS[persona_key]
        expected_navigation = set(persona["expected_navigation"])
        actual_navigation = set(self.current_user.get("accessible_navigation", []))
        
        # Check if user has expected navigation items
        missing_nav = expected_navigation - actual_navigation
        extra_nav = actual_navigation - expected_navigation
        
        if missing_nav or extra_nav:
            self.log_result(
                f"{persona_key} Navigation",
                "FAIL",
                f"Navigation mismatch - Missing: {list(missing_nav)}, Extra: {list(extra_nav)}",
                {"expected": list(expected_navigation), "actual": list(actual_navigation)}
            )
        else:
            self.log_result(
                f"{persona_key} Navigation",
                "PASS",
                f"Navigation access correct ({len(actual_navigation)} items)"
            )
    
    def test_company_isolation(self):
        """Test that company users only see their company's data"""
        # This would require testing with multiple companies and ensuring data isolation
        pass
    
    def run_comprehensive_test(self):
        """Run the complete RBAC test suite"""
        print(f"""
{'='*80}
🚀 Adara Screen DIGITAL SIGNAGE PLATFORM - COMPREHENSIVE RBAC TEST SUITE
{'='*80}
Testing {len(TEST_PERSONAS)} personas with enhanced RBAC system
Base URL: {BASE_URL}
Frontend URL: {FRONTEND_URL}
Started: {datetime.now().isoformat()}
{'='*80}
""")
        
        # Test each persona
        for persona_key in TEST_PERSONAS.keys():
            if self.login_user(persona_key):
                self.test_navigation_access(persona_key)
                self.test_persona_endpoints(persona_key)
            print()  # Add spacing between personas
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate a comprehensive test summary report"""
        total_tests = len(TEST_RESULTS)
        passed_tests = len([r for r in TEST_RESULTS if r["status"] == "PASS"])
        failed_tests = len([r for r in TEST_RESULTS if r["status"] == "FAIL"])
        
        print(f"""
{'='*80}
🏁 TEST SUMMARY REPORT
{'='*80}
Total Tests: {total_tests}
✅ Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)
❌ Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)

RBAC System Status: {'✅ HEALTHY' if failed_tests == 0 else '⚠️ ISSUES DETECTED'}
{'='*80}
""")
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in TEST_RESULTS:
                if result["status"] == "FAIL":
                    print(f"  • {result['test']}: {result['message']}")
        
        print(f"""
🔍 PERSONA VERIFICATION SUMMARY:
""")
        
        for persona_key, persona in TEST_PERSONAS.items():
            persona_results = [r for r in TEST_RESULTS if persona_key in r["test"]]
            persona_passed = len([r for r in persona_results if r["status"] == "PASS"])
            persona_total = len(persona_results)
            status_icon = "✅" if persona_passed == persona_total else "⚠️"
            
            print(f"  {status_icon} {persona_key}: {persona_passed}/{persona_total} tests passed")
            print(f"     {persona['description']}")
        
        # Save detailed results to file
        with open("rbac_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "personas": TEST_PERSONAS,
                "detailed_results": TEST_RESULTS
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: rbac_test_results.json")
        print(f"🌐 API Documentation: {BASE_URL}/api/docs")

def main():
    """Main test execution"""
    print("🔧 Initializing RBAC Test Suite...")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/auth/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Backend not healthy: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Check if frontend is running  
    try:
        response = requests.get(f"{FRONTEND_URL}/api/auth/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Frontend proxy not working: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to frontend: {e}")
        return
    
    # Run the comprehensive test
    tester = RBACTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()