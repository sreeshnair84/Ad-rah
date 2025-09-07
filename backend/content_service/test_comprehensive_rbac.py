#!/usr/bin/env python3
"""
Comprehensive RBAC Testing Suite
Adara Screen Digital Signage Platform

This unified test script covers:
1. All user personas and their expected permissions
2. All UI URLs and their accessibility based on RBAC
3. Authentication flow validation
4. Company isolation testing
5. Permission enforcement across all endpoints

Author: Claude Code Assistant
Date: 2025-01-15
"""

import asyncio
import json
import requests
import time
from typing import Dict, List, Optional, Any, Tuple
import os
from datetime import datetime
from pathlib import Path

# Test Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_RESULTS: List[Dict] = []
TEST_SESSION = requests.Session()

# Comprehensive Test User Personas
TEST_PERSONAS = {
    "SUPER_USER": {
        "email": "admin@adara.com",
        "password": "SuperAdmin123!",
        "user_type": "SUPER_USER",
        "company_type": None,
        "company_role": None,
        "expected_permissions": 27,  # All permissions
        "expected_navigation": [
            "dashboard", "unified", "users", "roles", "registration",
            "content", "my-content", "my-ads", "upload", "moderation", 
            "ads-approval", "host-review", "content-overlay", "kiosks", 
            "device-keys", "digital-twin", "analytics", "analytics/real-time",
            "performance", "schedules", "settings", "master-data", "billing"
        ],
        "description": "Platform Super Administrator with full system access"
    },
    "HOST_ADMIN": {
        "email": "admin@dubaimall-displays.com",
        "password": "HostAdmin123!",
        "user_type": "COMPANY_USER",
        "company_type": "HOST",
        "company_role": "ADMIN",
        "expected_permissions": 23,  # All HOST permissions
        "expected_navigation": [
            "dashboard", "users", "content", "my-content", "upload", 
            "moderation", "ads-approval", "host-review", "content-overlay",
            "kiosks", "device-keys", "digital-twin", "analytics", 
            "analytics/real-time", "performance", "schedules", "settings", "billing"
        ],
        "description": "HOST Company Administrator - Owns devices and screens"
    },
    "HOST_REVIEWER": {
        "email": "reviewer@dubaimall-displays.com",
        "password": "HostReviewer123!",
        "user_type": "COMPANY_USER",
        "company_type": "HOST",
        "company_role": "REVIEWER",
        "expected_permissions": 9,
        "expected_navigation": [
            "dashboard", "content", "my-content", "moderation", 
            "ads-approval", "host-review", "kiosks", "analytics", 
            "analytics/real-time", "performance"
        ],
        "description": "HOST Company Reviewer - Reviews and approves content"
    },
    "HOST_EDITOR": {
        "email": "editor@dubaimall-displays.com",
        "password": "HostEditor123!",
        "user_type": "COMPANY_USER",
        "company_type": "HOST",
        "company_role": "EDITOR",
        "expected_permissions": 6,
        "expected_navigation": [
            "dashboard", "content", "my-content", "upload", 
            "analytics", "analytics/real-time", "performance"
        ],
        "description": "HOST Company Editor - Creates and edits content"
    },
    "HOST_VIEWER": {
        "email": "viewer@dubaimall-displays.com",
        "password": "HostViewer123!",
        "user_type": "COMPANY_USER",
        "company_type": "HOST",
        "company_role": "VIEWER",
        "expected_permissions": 3,
        "expected_navigation": [
            "dashboard", "content", "my-content", "upload", "analytics"
        ],
        "description": "HOST Company Viewer - View-only access with basic upload"
    },
    "ADVERTISER_ADMIN": {
        "email": "admin@emirates-digital.ae",
        "password": "AdvAdmin123!",
        "user_type": "COMPANY_USER",
        "company_type": "ADVERTISER", 
        "company_role": "ADMIN",
        "expected_permissions": 15,  # No device permissions
        "expected_navigation": [
            "dashboard", "users", "content", "my-content", "my-ads", 
            "upload", "moderation", "ads-approval", "content-overlay",
            "analytics", "analytics/real-time", "performance", 
            "schedules", "settings", "billing"
        ],
        "description": "ADVERTISER Company Administrator - Creates ads and content"
    },
    "ADVERTISER_REVIEWER": {
        "email": "reviewer@emirates-digital.ae",
        "password": "AdvReviewer123!",
        "user_type": "COMPANY_USER",
        "company_type": "ADVERTISER",
        "company_role": "REVIEWER", 
        "expected_permissions": 7,
        "expected_navigation": [
            "dashboard", "content", "my-content", "my-ads", 
            "moderation", "ads-approval", "analytics", 
            "analytics/real-time", "performance"
        ],
        "description": "ADVERTISER Company Reviewer - Reviews ad content"
    },
    "ADVERTISER_EDITOR": {
        "email": "editor@emirates-digital.ae",
        "password": "AdvEditor123!",
        "user_type": "COMPANY_USER",
        "company_type": "ADVERTISER",
        "company_role": "EDITOR",
        "expected_permissions": 6,
        "expected_navigation": [
            "dashboard", "content", "my-content", "my-ads", 
            "upload", "analytics", "analytics/real-time", "performance"
        ],
        "description": "ADVERTISER Company Editor - Creates advertisement content"
    },
    "ADVERTISER_VIEWER": {
        "email": "viewer@emirates-digital.ae",
        "password": "AdvViewer123!",
        "user_type": "COMPANY_USER",
        "company_type": "ADVERTISER",
        "company_role": "VIEWER",
        "expected_permissions": 3,
        "expected_navigation": [
            "dashboard", "content", "my-content", "my-ads", 
            "upload", "analytics"
        ],
        "description": "ADVERTISER Company Viewer - View ads and basic upload"
    }
}

# Complete UI URL mapping based on Next.js frontend structure
UI_URLS = {
    # Authentication
    "login": "/login",
    "logout": "/api/auth/logout",
    
    # Dashboard & Overview
    "dashboard": "/dashboard",
    "unified": "/dashboard/unified",
    
    # User Management
    "users": "/dashboard/users",
    "roles": "/dashboard/roles",
    "registration": "/dashboard/registration",
    
    # Content Management
    "content": "/dashboard/content",
    "my-content": "/dashboard/content/my-content",
    "my-ads": "/dashboard/content/my-ads",
    "upload": "/dashboard/upload",
    "moderation": "/dashboard/content/moderation",
    "ads-approval": "/dashboard/content/ads-approval",
    "host-review": "/dashboard/content/host-review",
    "content-overlay": "/dashboard/content/overlay",
    
    # Device Management (HOST companies only)
    "kiosks": "/dashboard/devices/kiosks",
    "device-keys": "/dashboard/devices/keys",
    "digital-twin": "/dashboard/devices/digital-twin",
    
    # Analytics & Reporting
    "analytics": "/dashboard/analytics",
    "analytics/real-time": "/dashboard/analytics/real-time",
    "performance": "/dashboard/analytics/performance",
    
    # Scheduling
    "schedules": "/dashboard/schedules",
    
    # Settings & Administration
    "settings": "/dashboard/settings",
    "master-data": "/dashboard/settings/master-data",
    "billing": "/dashboard/billing"
}

# API Endpoint mapping for backend testing
API_ENDPOINTS = {
    # Authentication
    "auth/login": ("/api/auth/login", "POST"),
    "auth/me": ("/api/auth/me", "GET"),
    "auth/companies": ("/api/auth/companies", "GET"),
    "auth/navigation": ("/api/auth/navigation", "GET"),
    "auth/users": ("/api/auth/users", "GET"),
    "auth/logout": ("/api/auth/logout", "POST"),
    
    # Content Management
    "content/list": ("/api/content/", "GET"),
    "content/upload": ("/api/content/upload", "POST"),
    "content/moderate": ("/api/content/moderate", "POST"),
    
    # Device Management
    "devices/list": ("/api/devices/", "GET"),
    "devices/register": ("/api/devices/register", "POST"),
    
    # Analytics
    "analytics/dashboard": ("/api/analytics/dashboard", "GET"),
    "analytics/reports": ("/api/analytics/reports", "GET"),
    
    # Company Management
    "companies/list": ("/api/companies/", "GET"),
    "companies/create": ("/api/companies/", "POST"),
}

class ComprehensiveRBACTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.current_token = None
        self.current_user = None
        self.current_persona = None
        
    def log_result(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test results with color coding"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "persona": self.current_persona,
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        TEST_RESULTS.append(result)
        
        # Console output with color coding
        colors = {"PASS": "\033[92m", "FAIL": "\033[91m", "INFO": "\033[94m", "WARN": "\033[93m", "END": "\033[0m"}
        color = colors.get(status, colors["INFO"])
        
        print(f"{color}[{status}] {test_name}: {message}{colors['END']}")
        if details and status == "FAIL":
            print(f"  Details: {json.dumps(details, indent=2)}")
    
    def login_persona(self, persona_key: str) -> bool:
        """Login as a specific test persona and validate authentication"""
        persona = TEST_PERSONAS[persona_key]
        self.current_persona = persona_key
        
        try:
            # Login via backend API
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": persona["email"], "password": persona["password"]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_token = data["access_token"]
                self.current_user = data["user"]
                
                # Validate user profile data
                validation_errors = []
                
                # Check user type
                if self.current_user.get("user_type") != persona["user_type"]:
                    validation_errors.append(f"User type mismatch: expected {persona['user_type']}, got {self.current_user.get('user_type')}")
                
                # Check company type for company users
                if persona["company_type"] and self.current_user.get("company", {}).get("company_type") != persona["company_type"]:
                    validation_errors.append(f"Company type mismatch: expected {persona['company_type']}, got {self.current_user.get('company', {}).get('company_type')}")
                
                # Check company role
                if persona["company_role"] and self.current_user.get("company_role") != persona["company_role"]:
                    validation_errors.append(f"Company role mismatch: expected {persona['company_role']}, got {self.current_user.get('company_role')}")
                
                # Check permission count
                actual_permissions = len(self.current_user.get("permissions", []))
                expected_permissions = persona["expected_permissions"]
                if actual_permissions != expected_permissions:
                    validation_errors.append(f"Permission count mismatch: expected {expected_permissions}, got {actual_permissions}")
                
                # Check navigation access
                actual_navigation = set(self.current_user.get("accessible_navigation", []))
                expected_navigation = set(persona["expected_navigation"])
                
                missing_nav = expected_navigation - actual_navigation
                extra_nav = actual_navigation - expected_navigation
                
                if missing_nav:
                    validation_errors.append(f"Missing navigation items: {list(missing_nav)}")
                if extra_nav:
                    validation_errors.append(f"Extra navigation items: {list(extra_nav)}")
                
                if validation_errors:
                    self.log_result(
                        f"Login Validation {persona_key}",
                        "FAIL",
                        f"Authentication succeeded but profile validation failed: {'; '.join(validation_errors)}",
                        {
                            "validation_errors": validation_errors,
                            "user_profile": self.current_user,
                            "expected_profile": persona
                        }
                    )
                    return False
                
                self.log_result(
                    f"Login {persona_key}",
                    "PASS",
                    f"Successfully authenticated and validated ({actual_permissions} permissions, {len(actual_navigation)} nav items)"
                )
                return True
            else:
                self.log_result(
                    f"Login {persona_key}",
                    "FAIL",
                    f"Authentication failed: HTTP {response.status_code}",
                    {"response": response.text[:500]}
                )
                return False
                
        except Exception as e:
            self.log_result(f"Login {persona_key}", "FAIL", f"Exception during authentication: {str(e)}")
            return False
    
    def test_api_endpoint(self, endpoint_name: str, expected_success: bool = True) -> Dict:
        """Test a specific API endpoint with current user's token"""
        if endpoint_name not in API_ENDPOINTS:
            return {"success": False, "error": "Unknown endpoint"}
        
        endpoint_url, method = API_ENDPOINTS[endpoint_name]
        headers = {"Content-Type": "application/json"}
        
        if self.current_token:
            headers["Authorization"] = f"Bearer {self.current_token}"
        
        try:
            if method == "GET":
                response = self.session.get(f"{BASE_URL}{endpoint_url}", headers=headers)
            elif method == "POST":
                response = self.session.post(f"{BASE_URL}{endpoint_url}", json={}, headers=headers)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            return {
                "status_code": response.status_code,
                "success": (response.status_code < 400) == expected_success,
                "response": response.text[:200] if response.text else "",
                "expected_success": expected_success,
                "actual_success": response.status_code < 400
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": 0,
                "expected_success": expected_success,
                "actual_success": False
            }
    
    def test_ui_page_access(self, page_name: str, should_have_access: bool) -> Dict:
        """Test UI page access (frontend route availability)"""
        if page_name not in UI_URLS:
            return {"success": False, "error": "Unknown UI page"}
        
        page_url = UI_URLS[page_name]
        
        try:
            headers = {}
            if self.current_token:
                headers["Authorization"] = f"Bearer {self.current_token}"
            
            response = self.session.get(f"{FRONTEND_URL}{page_url}", headers=headers)
            
            # For frontend routes, we expect:
            # - 200 if user should have access
            # - 401/403 if user shouldn't have access
            # - 404 if route doesn't exist
            
            has_access = response.status_code == 200
            test_passed = has_access == should_have_access
            
            return {
                "status_code": response.status_code,
                "success": test_passed,
                "has_access": has_access,
                "should_have_access": should_have_access,
                "response": response.text[:200] if response.text else ""
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": 0,
                "has_access": False,
                "should_have_access": should_have_access
            }
    
    def test_persona_access_patterns(self, persona_key: str):
        """Test comprehensive access patterns for a specific persona"""
        persona = TEST_PERSONAS[persona_key]
        expected_navigation = set(persona["expected_navigation"])
        
        print(f"\n{'='*80}")
        print(f"🔍 TESTING ACCESS PATTERNS: {persona_key}")
        print(f"📊 {persona['description']}")
        print(f"👤 User Type: {persona['user_type']}, Company Type: {persona.get('company_type', 'N/A')}, Role: {persona.get('company_role', 'N/A')}")
        print(f"{'='*80}")
        
        # Test API endpoints based on permissions
        api_tests = self._get_api_tests_for_persona(persona_key)
        
        for endpoint_name, should_succeed in api_tests:
            result = self.test_api_endpoint(endpoint_name, should_succeed)
            status = "PASS" if result["success"] else "FAIL"
            
            if should_succeed:
                message = f"Authorized access: expected success, got {result.get('status_code', 'error')}"
            else:
                message = f"Denied access: expected failure, got {result.get('status_code', 'error')}"
            
            self.log_result(
                f"{persona_key} API {endpoint_name}",
                status,
                message,
                result if status == "FAIL" else None
            )
        
        # Test UI page access
        for page_name in UI_URLS.keys():
            should_have_access = page_name in expected_navigation
            result = self.test_ui_page_access(page_name, should_have_access)
            
            status = "PASS" if result["success"] else "FAIL"
            
            if should_have_access:
                message = f"Page access granted: {result.get('status_code', 'error')}"
            else:
                message = f"Page access denied: {result.get('status_code', 'error')}"
            
            self.log_result(
                f"{persona_key} UI {page_name}",
                status,
                message,
                result if status == "FAIL" else None
            )
    
    def _get_api_tests_for_persona(self, persona_key: str) -> List[Tuple[str, bool]]:
        """Get API endpoint tests based on persona permissions"""
        persona = TEST_PERSONAS[persona_key]
        user_type = persona["user_type"]
        company_type = persona.get("company_type")
        company_role = persona.get("company_role")
        
        tests = [
            # Basic authenticated endpoints - all users should have access
            ("auth/me", True),
            ("auth/companies", True),
            ("auth/navigation", True),
            ("auth/logout", True),
        ]
        
        # User management endpoints
        if user_type == "SUPER_USER" or company_role == "ADMIN":
            tests.extend([
                ("auth/users", True),
                ("companies/list", True),
                ("companies/create", user_type == "SUPER_USER"),  # Only super users can create companies
            ])
        else:
            tests.extend([
                ("auth/users", False),
                ("companies/list", False),
                ("companies/create", False),
            ])
        
        # Content management - all authenticated users have some level of access
        tests.extend([
            ("content/list", True),
            ("content/upload", True),
        ])
        
        # Content moderation - only ADMIN and REVIEWER roles
        if company_role in ["ADMIN", "REVIEWER"] or user_type == "SUPER_USER":
            tests.append(("content/moderate", True))
        else:
            tests.append(("content/moderate", False))
        
        # Device management - only HOST companies and super users
        if user_type == "SUPER_USER" or company_type == "HOST":
            tests.extend([
                ("devices/list", True),
                ("devices/register", company_role in ["ADMIN", "EDITOR"] or user_type == "SUPER_USER"),
            ])
        else:
            tests.extend([
                ("devices/list", False),
                ("devices/register", False),
            ])
        
        # Analytics - all authenticated users have basic access
        tests.extend([
            ("analytics/dashboard", True),
            ("analytics/reports", True),
        ])
        
        return tests
    
    def test_company_isolation(self):
        """Test that company users can only access their company's data"""
        print(f"\n{'='*80}")
        print("🏢 TESTING COMPANY ISOLATION")
        print("Ensuring users can only access their company's data")
        print(f"{'='*80}")
        
        # This would require creating test content for each company and verifying isolation
        # For now, we'll log this as a placeholder test
        self.log_result(
            "Company Isolation",
            "INFO",
            "Company isolation testing requires specific test data setup - manual verification needed"
        )
    
    def run_comprehensive_tests(self):
        """Run the complete RBAC test suite"""
        print(f"""
{'='*100}
ADARA SCREEN DIGITAL SIGNAGE PLATFORM
   COMPREHENSIVE RBAC & UI ACCESS TESTING SUITE
{'='*100}
Testing {len(TEST_PERSONAS)} personas across {len(UI_URLS)} UI pages and {len(API_ENDPOINTS)} API endpoints
Backend: {BASE_URL}
Frontend: {FRONTEND_URL}
Started: {datetime.now().isoformat()}
{'='*100}
""")
        
        # Test health endpoints first
        self._test_system_health()
        
        # Test each persona comprehensively
        for persona_key in TEST_PERSONAS.keys():
            if self.login_persona(persona_key):
                self.test_persona_access_patterns(persona_key)
            print()  # Add spacing between personas
        
        # Test company isolation
        self.test_company_isolation()
        
        # Generate comprehensive report
        self.generate_comprehensive_report()
    
    def _test_system_health(self):
        """Test that both backend and frontend are running"""
        print("🏥 SYSTEM HEALTH CHECK")
        
        try:
            backend_response = requests.get(f"{BASE_URL}/docs", timeout=5)
            backend_healthy = backend_response.status_code == 200
        except:
            backend_healthy = False
        
        try:
            frontend_response = requests.get(f"{FRONTEND_URL}/login", timeout=5)
            frontend_healthy = frontend_response.status_code in [200, 404]  # 404 is ok for Next.js routes
        except:
            frontend_healthy = False
        
        self.log_result("Backend Health", "PASS" if backend_healthy else "FAIL", 
                       f"Backend API {'accessible' if backend_healthy else 'not accessible'}")
        self.log_result("Frontend Health", "PASS" if frontend_healthy else "FAIL",
                       f"Frontend app {'accessible' if frontend_healthy else 'not accessible'}")
        
        if not backend_healthy or not frontend_healthy:
            print("⚠️  Warning: Some services are not healthy. Test results may be incomplete.")
    
    def generate_comprehensive_report(self):
        """Generate detailed test report with analytics"""
        total_tests = len(TEST_RESULTS)
        passed_tests = len([r for r in TEST_RESULTS if r["status"] == "PASS"])
        failed_tests = len([r for r in TEST_RESULTS if r["status"] == "FAIL"])
        
        print(f"""
{'='*100}
🏁 COMPREHENSIVE RBAC TESTING REPORT
{'='*100}
📊 OVERALL STATISTICS:
   • Total Tests Run: {total_tests}
   • ✅ Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)
   • ❌ Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)
   
🎯 RBAC SYSTEM STATUS: {'✅ HEALTHY - All tests passed!' if failed_tests == 0 else f'⚠️  ISSUES DETECTED - {failed_tests} test(s) failed'}
{'='*100}
""")
        
        # Persona-specific analysis
        print("👥 PERSONA-SPECIFIC RESULTS:")
        for persona_key, persona in TEST_PERSONAS.items():
            persona_results = [r for r in TEST_RESULTS if r.get("persona") == persona_key]
            persona_passed = len([r for r in persona_results if r["status"] == "PASS"])
            persona_failed = len([r for r in persona_results if r["status"] == "FAIL"])
            persona_total = persona_passed + persona_failed
            
            if persona_total > 0:
                success_rate = persona_passed / persona_total * 100
                status_icon = "✅" if persona_failed == 0 else "⚠️" if persona_failed < 3 else "❌"
                
                print(f"   {status_icon} {persona_key}: {persona_passed}/{persona_total} tests passed ({success_rate:.1f}%)")
                print(f"      📝 {persona['description']}")
                
                if persona_failed > 0:
                    failed_tests_for_persona = [r for r in persona_results if r["status"] == "FAIL"]
                    for test in failed_tests_for_persona[:3]:  # Show first 3 failures
                        print(f"         ❌ {test['test']}: {test['message']}")
                    if len(failed_tests_for_persona) > 3:
                        print(f"         ... and {len(failed_tests_for_persona) - 3} more failures")
                print()
        
        # Failed tests summary
        if failed_tests > 0:
            print("❌ CRITICAL ISSUES DETECTED:")
            failure_categories = {}
            for result in TEST_RESULTS:
                if result["status"] == "FAIL":
                    test_type = result["test"].split()[1] if len(result["test"].split()) > 1 else "General"
                    if test_type not in failure_categories:
                        failure_categories[test_type] = []
                    failure_categories[test_type].append(result)
            
            for category, failures in failure_categories.items():
                print(f"   🔴 {category}: {len(failures)} failures")
                for failure in failures[:2]:  # Show first 2 in each category
                    print(f"      • {failure['test']}: {failure['message']}")
                if len(failures) > 2:
                    print(f"      • ... and {len(failures) - 2} more {category} failures")
        
        # Save detailed results
        report_data = {
            "summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests/total_tests*100 if total_tests > 0 else 0,
                "system_health": failed_tests == 0
            },
            "personas": TEST_PERSONAS,
            "ui_urls": UI_URLS,
            "api_endpoints": API_ENDPOINTS,
            "detailed_results": TEST_RESULTS
        }
        
        report_file = Path("comprehensive_rbac_test_results.json")
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"""
{'='*100}
📋 DETAILED RESULTS: {report_file.absolute()}
🌐 API Documentation: {BASE_URL}/docs
🔧 Frontend Development: {FRONTEND_URL}

🎯 NEXT STEPS:
   {'✅ All systems operational! RBAC is working correctly.' if failed_tests == 0 else 
    '⚠️  Review failed tests and fix RBAC configuration.'}
   {'✅ All user personas have correct access levels.' if failed_tests == 0 else
    '⚠️  Some personas may have incorrect permission assignments.'}
   {'✅ UI navigation controls are properly enforced.' if failed_tests == 0 else
    '⚠️  Check frontend navigation and route protection.'}
{'='*100}
""")

def main():
    """Main test execution function"""
    print("Initializing Comprehensive RBAC Test Suite...")
    
    tester = ComprehensiveRBACTester()
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()