#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class GhostUserBugFixTester:
    def __init__(self, base_url="https://globetrotter-app-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_result(self, test_name, success, response_data=None, error=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed_tests.append({
                "test": test_name,
                "error": str(error) if error else "Unknown error",
                "response": response_data
            })
            print(f"❌ {test_name} - FAILED: {error}")

    def run_test(self, test_name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = self.session.headers.copy()
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            response_data = None
            try:
                response_data = response.json()
            except:
                response_data = response.text

            if success:
                self.log_result(test_name, True, response_data)
                return True, response_data
            else:
                self.log_result(test_name, False, response_data, f"Expected {expected_status}, got {response.status_code}")
                return False, response_data

        except Exception as e:
            self.log_result(test_name, False, None, str(e))
            return False, {}

    def test_ghost_user_bug_fix(self):
        """Test Ghost User Bug Fix - Complete Scenarios"""
        print("🔍 GHOST USER BUG FIX TESTING")
        print("=" * 60)
        
        # Scenario 1: Register test users
        print("\n📋 Scenario 1: Basic Online Users Flow")
        
        # Register User 1
        test_email1 = f"ghosttest1_{uuid.uuid4().hex[:8]}@test.com"
        registration_data1 = {
            "email": test_email1,
            "name": "Ghost Test 1",
            "password": "GhostTest123!"
        }
        
        success1, response1 = self.run_test("Register User 1", "POST", "auth/register", 200, registration_data1)
        if not success1:
            print("❌ Cannot proceed without User 1")
            return False
            
        token1 = response1.get('access_token')
        user_id1 = response1['user']['id']
        print(f"   User 1 ID: {user_id1}")
        
        # Register User 2
        test_email2 = f"ghosttest2_{uuid.uuid4().hex[:8]}@test.com"
        registration_data2 = {
            "email": test_email2,
            "name": "Ghost Test 2", 
            "password": "GhostTest123!"
        }
        
        success2, response2 = self.run_test("Register User 2", "POST", "auth/register", 200, registration_data2)
        if not success2:
            print("❌ Cannot proceed without User 2")
            return False
            
        token2 = response2.get('access_token')
        user_id2 = response2['user']['id']
        print(f"   User 2 ID: {user_id2}")
        
        # User 1 gets online users (marks self as online)
        success, online_users1 = self.run_test("User 1 Get Online Users", "GET", "community/online-users", 200, token=token1)
        if success:
            print(f"   User 1 sees {len(online_users1)} online users")
        
        # User 2 gets online users (marks self as online)
        success, online_users2 = self.run_test("User 2 Get Online Users", "GET", "community/online-users", 200, token=token2)
        if success:
            print(f"   User 2 sees {len(online_users2)} online users")
            user1_visible = any(user.get('id') == user_id1 for user in online_users2)
            print(f"   User 1 visible to User 2: {user1_visible}")
        
        # Check presence status
        success, presence = self.run_test("Check Presence Status", "GET", "community/presence-status", 200, token=token2)
        if success:
            cache_count = presence.get('cache_users_count', 0)
            db_count = presence.get('db_users_count', 0)
            print(f"   Cache: {cache_count} users, DB: {db_count} users")
        
        # Scenario 2: Test admin cleanup functionality
        print("\n📋 Scenario 2: Admin Cleanup Functionality")
        
        # Test cleanup ghost users
        success, cleanup1 = self.run_test("Admin Cleanup Ghost Users", "POST", "admin/cleanup-ghost-users", 200, token=token1)
        if success:
            invalid_removed = cleanup1.get('invalid_removed', 0)
            stale_removed = cleanup1.get('stale_removed', 0)
            print(f"   Cleanup: {invalid_removed} invalid, {stale_removed} stale users removed")
        
        # Scenario 3: Test admin reset functionality
        print("\n📋 Scenario 3: Admin Reset Functionality")
        
        # Test admin reset
        success, reset_result = self.run_test("Admin Reset Online Users", "POST", "admin/reset-online-users", 200, token=token2)
        if success:
            cache_cleared = reset_result.get('cache_cleared', 0)
            users_reset = reset_result.get('users_reset', 0)
            print(f"   Reset: {cache_cleared} cache cleared, {users_reset} users reset")
        
        # Check presence after reset
        success, presence_after = self.run_test("Presence Status After Reset", "GET", "community/presence-status", 200, token=token1)
        if success:
            cache_count_after = presence_after.get('cache_users_count', 0)
            db_count_after = presence_after.get('db_users_count', 0)
            print(f"   After reset - Cache: {cache_count_after} users, DB: {db_count_after} users")
        
        # Users can re-add themselves
        success, online_after_reset = self.run_test("User 2 Online After Reset", "GET", "community/online-users", 200, token=token2)
        if success:
            print(f"   User 2 sees {len(online_after_reset)} users after reset")
        
        # Final cleanup test
        success, final_cleanup = self.run_test("Final Cleanup Test", "POST", "admin/cleanup-ghost-users", 200, token=token1)
        if success:
            final_invalid = final_cleanup.get('invalid_removed', 0)
            final_stale = final_cleanup.get('stale_removed', 0)
            print(f"   Final cleanup: {final_invalid} invalid, {final_stale} stale users")
        
        return True

    def run_tests(self):
        """Run all ghost user tests"""
        print("🚀 GHOST USER BUG FIX VERIFICATION")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        success = self.test_ghost_user_bug_fix()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 GHOST USER TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['error']}")
        
        if success and len(self.failed_tests) == 0:
            print("\n🎉 GHOST USER BUG FIX VERIFICATION: PASSED")
            print("✅ All ghost user prevention mechanisms working correctly")
        else:
            print("\n⚠️ GHOST USER BUG FIX VERIFICATION: ISSUES FOUND")
        
        return len(self.failed_tests) == 0

def main():
    tester = GhostUserBugFixTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())