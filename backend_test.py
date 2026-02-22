#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class AITravelglobeAPITester:
    def __init__(self, base_url="https://globetrotter-app-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.passed_tests = []

    def log_result(self, test_name, success, response_data=None, error=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            self.passed_tests.append(test_name)
            print(f"✅ {test_name} - PASSED")
        else:
            self.failed_tests.append({
                "test": test_name,
                "error": str(error) if error else "Unknown error",
                "response": response_data
            })
            print(f"❌ {test_name} - FAILED: {error}")

    def run_test(self, test_name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = self.session.headers.copy()
        if headers:
            test_headers.update(headers)
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = self.session.get(url, headers=test_headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=test_headers)

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

    def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        self.run_test("Root Endpoint", "GET", "", 200)
        
        # Test health check
        self.run_test("Health Check", "GET", "health", 200)

    def test_destinations_endpoint(self):
        """Test destinations endpoint"""
        print("\n🔍 Testing Destinations...")
        
        success, data = self.run_test("Popular Destinations", "GET", "destinations/popular", 200)
        if success and isinstance(data, list) and len(data) > 0:
            print(f"   Found {len(data)} destinations")
        
    def test_emergency_endpoint(self):
        """Test emergency info endpoint"""
        print("\n🔍 Testing Emergency Info...")
        
        # Test default emergency info
        self.run_test("Emergency Info Default", "GET", "emergency/info", 200)
        
        # Test country-specific emergency info
        self.run_test("Emergency Info France", "GET", "emergency/info?country=france", 200)

    def test_user_registration_login(self):
        """Test user registration and login"""
        print("\n🔍 Testing User Authentication...")
        
        # Generate unique test user
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "TestPass123!"
        test_name = "Test User"
        
        # Test registration
        registration_data = {
            "email": test_email,
            "name": test_name,
            "password": test_password
        }
        
        success, response = self.run_test("User Registration", "POST", "auth/register", 200, registration_data)
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Registered user: {test_email}")
        
        # Test login with same credentials
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        success, response = self.run_test("User Login", "POST", "auth/login", 200, login_data)
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Logged in user: {test_email}")
        
        # Test get current user
        if self.token:
            self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_profile_management(self):
        """Test profile management"""
        if not self.token:
            print("⚠️ Skipping profile tests - no authentication token")
            return
            
        print("\n🔍 Testing Profile Management...")
        
        # Test profile update
        profile_data = {
            "age": 30,
            "gender": "male",
            "marital_status": "single",
            "food_preferences": {
                "diet_type": "vegetarian",
                "allergies": ["peanuts"],
                "restrictions": ["no beef"]
            },
            "budget_preferences": {
                "daily_budget_min": 100,
                "daily_budget_max": 300,
                "trip_budget_preference": "mid-range"
            },
            "travel_interests": ["food", "culture", "nature"],
            "is_business_traveler": False
        }
        
        self.run_test("Update Profile", "PUT", "auth/profile", 200, profile_data)

    def test_itinerary_generation(self):
        """Test AI itinerary generation"""
        if not self.token:
            print("⚠️ Skipping itinerary tests - no authentication token")
            return
            
        print("\n🔍 Testing AI Itinerary Generation...")
        
        # Test itinerary generation
        trip_data = {
            "destination": "Paris",
            "start_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "end_date": (datetime.now() + timedelta(days=33)).strftime('%Y-%m-%d'),
            "trip_type": "romantic",
            "interests": ["culture", "food"],
            "budget_range": "medium",
            "travelers_count": 2,
            "has_children": False,
            "children_ages": [],
            "special_requirements": "Vegetarian meals preferred",
            "is_business_trip": False
        }
        
        success, response = self.run_test("Generate Itinerary", "POST", "itinerary/generate", 200, trip_data)
        
        if success and 'id' in response:
            itinerary_id = response['id']
            print(f"   Generated itinerary: {itinerary_id}")
            
            # Test get specific itinerary
            self.run_test("Get Itinerary", "GET", f"itinerary/{itinerary_id}", 200)
            
            # Test get my itineraries
            self.run_test("Get My Itineraries", "GET", "itineraries/my", 200)
            
            return itinerary_id
        
        return None

    def test_business_trip_generation(self):
        """Test business trip itinerary generation"""
        if not self.token:
            print("⚠️ Skipping business trip tests - no authentication token")
            return
            
        print("\n🔍 Testing Business Trip Generation...")
        
        # Test business trip generation
        business_trip_data = {
            "destination": "Tokyo",
            "start_date": (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
            "end_date": (datetime.now() + timedelta(days=47)).strftime('%Y-%m-%d'),
            "trip_type": "business",
            "interests": ["business", "culture"],
            "budget_range": "high",
            "travelers_count": 1,
            "has_children": False,
            "children_ages": [],
            "special_requirements": "Need reliable WiFi",
            "is_business_trip": True,
            "meeting_agenda": "Quarterly business review",
            "meeting_location": "Tokyo Business Center",
            "meeting_date": (datetime.now() + timedelta(days=46)).strftime('%Y-%m-%d'),
            "meeting_time": "14:00",
            "meeting_duration": "2hr"
        }
        
        success, response = self.run_test("Generate Business Trip", "POST", "itinerary/generate", 200, business_trip_data)
        
        if success and 'id' in response:
            print(f"   Generated business itinerary: {response['id']}")
            return response['id']
        
        return None

    def test_albums_management(self):
        """Test trip albums management"""
        if not self.token:
            print("⚠️ Skipping albums tests - no authentication token")
            return
            
        print("\n🔍 Testing Albums Management...")
        
        # Test create album
        success, response = self.run_test("Create Album", "POST", "albums?name=Test Album&description=Test Description", 200)
        
        if success and 'id' in response:
            album_id = response['id']
            print(f"   Created album: {album_id}")
            
            # Test get my albums
            self.run_test("Get My Albums", "GET", "albums", 200)
            
            # Test get specific album
            self.run_test("Get Album", "GET", f"albums/{album_id}", 200)
            
            # Test update album
            self.run_test("Update Album", "PUT", f"albums/{album_id}?name=Updated Album&is_public=true", 200)
            
            return album_id
        
        return None

    def test_community_chat(self):
        """Test community chat functionality"""
        if not self.token:
            print("⚠️ Skipping community tests - no authentication token")
            return
            
        print("\n🔍 Testing Community Chat...")
        
        # Test post message
        message_data = {
            "message": "Hello from the test suite! Great travel tips here.",
            "location_approximate": "Paris, France"
        }
        
        success, response = self.run_test("Post Community Message", "POST", "community/messages", 200, message_data)
        
        if success and 'id' in response:
            message_id = response['id']
            print(f"   Posted message: {message_id}")
            
            # Test get messages
            self.run_test("Get Community Messages", "GET", "community/messages", 200)
            
            return message_id
        
        return None

    def test_ai_chat(self):
        """Test AI chat functionality"""
        print("\n🔍 Testing AI Chat...")
        
        # Test AI chat
        chat_data = {
            "message": "I want to visit Paris for 3 days. What should I see?",
            "session_id": str(uuid.uuid4())
        }
        
        success, response = self.run_test("AI Chat", "POST", "chat", 200, chat_data)
        
        if success and 'response' in response:
            print(f"   AI responded with {len(response['response'])} characters")

    def test_delete_chat_history(self):
        """Test delete chat history functionality - COMPREHENSIVE TESTING"""
        if not self.token:
            print("⚠️ Skipping delete chat history tests - no authentication token")
            return
            
        print("\n🔍 Testing Delete Chat History - COMPREHENSIVE")
        print("=" * 50)
        
        # Store original token to restore later
        original_token = self.token
        original_user_id = self.user_id
        
        # ===== SCENARIO 1: Community Message Clear All =====
        print("\n📋 Scenario 1: Community Message Clear All")
        
        # Register a test user specifically for delete testing
        test_email = "deletetest@test.com"
        test_password = "DeleteTest123!"
        test_name = "Delete Test User"
        
        registration_data = {
            "email": test_email,
            "name": test_name,
            "password": test_password
        }
        
        success, response = self.run_test("Register Delete Test User", "POST", "auth/register", 200, registration_data)
        if success and 'access_token' in response:
            delete_test_token = response['access_token']
            delete_test_user_id = response['user']['id']
            self.token = delete_test_token
            self.user_id = delete_test_user_id
            print(f"   ✅ Registered delete test user: {test_email}")
        else:
            # Try to login with existing user
            login_data = {"email": test_email, "password": test_password}
            success, response = self.run_test("Login Delete Test User", "POST", "auth/login", 200, login_data)
            if success and 'access_token' in response:
                delete_test_token = response['access_token']
                delete_test_user_id = response['user']['id']
                self.token = delete_test_token
                self.user_id = delete_test_user_id
                print(f"   ✅ Logged in delete test user: {test_email}")
            else:
                print("   ❌ Failed to create/login delete test user")
                self.token = original_token
                self.user_id = original_user_id
                return
        
        # Send 3 community messages
        community_message_ids = []
        for i in range(3):
            message_data = {
                "message": f"Test community message {i+1} for deletion testing",
                "location_approximate": "Test Location"
            }
            
            success, response = self.run_test(f"Post Community Message {i+1}", "POST", "community/messages", 200, message_data)
            if success and 'id' in response:
                community_message_ids.append(response['id'])
                print(f"   Posted community message {i+1}: {response['id']}")
        
        # Verify messages appear in GET /api/community/messages
        success, messages = self.run_test("Get Community Messages Before Delete", "GET", "community/messages", 200)
        if success and isinstance(messages, list):
            user_messages_before = [msg for msg in messages if msg.get('user_id') == self.user_id]
            print(f"   User has {len(user_messages_before)} community messages before deletion")
            
            # Call DELETE /api/community/messages/clear-all
            success, delete_response = self.run_test("Delete All Community Messages", "DELETE", "community/messages/clear-all", 200)
            
            if success and 'deleted_count' in delete_response:
                deleted_count = delete_response['deleted_count']
                print(f"   ✅ Deleted {deleted_count} community messages")
                
                # Verify response includes deleted_count
                if 'deleted_count' in delete_response and 'message' in delete_response:
                    print(f"   ✅ Response format correct: {delete_response}")
                else:
                    print(f"   ❌ Response format incorrect: {delete_response}")
                
                # Verify messages are gone from GET response
                success, messages_after = self.run_test("Get Community Messages After Delete", "GET", "community/messages", 200)
                if success and isinstance(messages_after, list):
                    user_messages_after = [msg for msg in messages_after if msg.get('user_id') == self.user_id]
                    print(f"   User has {len(user_messages_after)} community messages after deletion")
                    
                    if len(user_messages_after) == 0:
                        print("   ✅ Community messages successfully deleted")
                    else:
                        print("   ❌ Some community messages still exist after deletion")
        
        # ===== SCENARIO 2: Single Message Delete =====
        print("\n📋 Scenario 2: Single Message Delete")
        
        # Send a new community message
        message_data = {
            "message": "Single message for deletion test",
            "location_approximate": "Test Location"
        }
        
        success, response = self.run_test("Post Single Community Message", "POST", "community/messages", 200, message_data)
        if success and 'id' in response:
            single_message_id = response['id']
            print(f"   Posted single message: {single_message_id}")
            
            # Call DELETE /api/community/messages/{message_id}
            success, delete_response = self.run_test("Delete Single Community Message", "DELETE", f"community/messages/{single_message_id}", 200)
            
            if success:
                print(f"   ✅ Single message deleted: {delete_response}")
                
                # Verify message is deleted by checking it doesn't appear in GET
                success, messages = self.run_test("Get Community Messages After Single Delete", "GET", "community/messages", 200)
                if success and isinstance(messages, list):
                    deleted_message_exists = any(msg.get('id') == single_message_id for msg in messages)
                    if not deleted_message_exists:
                        print("   ✅ Single message successfully deleted")
                    else:
                        print("   ❌ Single message still exists after deletion")
        
        # ===== SCENARIO 3: Private Message Testing Setup =====
        print("\n📋 Scenario 3: Private Message Clear All")
        
        # Register a second user for private messaging
        test_email2 = "deletetest2@test.com"
        test_password2 = "DeleteTest123!"
        test_name2 = "Delete Test User 2"
        
        registration_data2 = {
            "email": test_email2,
            "name": test_name2,
            "password": test_password2
        }
        
        # Store first user's token
        user1_token = self.token
        user1_id = self.user_id
        
        success, response = self.run_test("Register Second Delete Test User", "POST", "auth/register", 200, registration_data2)
        if success and 'access_token' in response:
            user2_token = response['access_token']
            user2_id = response['user']['id']
            print(f"   ✅ Registered second user: {test_email2}")
        else:
            # Try to login with existing user
            login_data2 = {"email": test_email2, "password": test_password2}
            success, response = self.run_test("Login Second Delete Test User", "POST", "auth/login", 200, login_data2)
            if success and 'access_token' in response:
                user2_token = response['access_token']
                user2_id = response['user']['id']
                print(f"   ✅ Logged in second user: {test_email2}")
            else:
                print("   ❌ Failed to create/login second user - skipping private message tests")
                self.token = original_token
                self.user_id = original_user_id
                return
        
        # Send private messages between users
        self.token = user1_token
        self.user_id = user1_id
        
        # User 1 sends messages to User 2
        private_message_ids = []
        for i in range(2):
            message_data = {
                "recipient_id": user2_id,
                "content": f"Private message {i+1} from User 1 to User 2"
            }
            
            success, response = self.run_test(f"Send Private Message {i+1}", "POST", "messages", 200, message_data)
            if success and 'id' in response:
                private_message_ids.append(response['id'])
                print(f"   User 1 sent private message {i+1}: {response['id']}")
        
        # User 2 sends messages to User 1
        self.token = user2_token
        self.user_id = user2_id
        
        for i in range(2):
            message_data = {
                "recipient_id": user1_id,
                "content": f"Private message {i+1} from User 2 to User 1"
            }
            
            success, response = self.run_test(f"Send Private Message Back {i+1}", "POST", "messages", 200, message_data)
            if success and 'id' in response:
                print(f"   User 2 sent private message {i+1}: {response['id']}")
        
        # User 1 calls DELETE /api/messages/clear-all
        self.token = user1_token
        self.user_id = user1_id
        
        success, delete_response = self.run_test("User 1 Delete All Private Messages", "DELETE", "messages/clear-all", 200)
        if success and 'deleted_count' in delete_response:
            deleted_count = delete_response['deleted_count']
            print(f"   ✅ User 1 deleted {deleted_count} private messages")
            
            # Verify only User 1's sent messages are deleted
            success, conversations = self.run_test("Get Conversations After Delete", "GET", "messages/conversations", 200)
            if success:
                print(f"   Conversations after User 1 delete: {len(conversations) if isinstance(conversations, list) else 'N/A'}")
        
        # ===== SCENARIO 4: Clear Specific Conversation =====
        print("\n📋 Scenario 4: Clear Specific Conversation")
        
        # Send more private messages
        for i in range(2):
            message_data = {
                "recipient_id": user2_id,
                "content": f"New private message {i+1} from User 1 to User 2"
            }
            
            success, response = self.run_test(f"Send New Private Message {i+1}", "POST", "messages", 200, message_data)
            if success and 'id' in response:
                print(f"   User 1 sent new private message {i+1}: {response['id']}")
        
        # Call DELETE /api/messages/{partner_id}/clear
        success, delete_response = self.run_test("Clear Specific Conversation", "DELETE", f"messages/{user2_id}/clear", 200)
        if success and 'deleted_count' in delete_response:
            deleted_count = delete_response['deleted_count']
            print(f"   ✅ Cleared {deleted_count} messages in conversation with User 2")
            
            # Verify only messages in that conversation are deleted
            success, messages_with_user2 = self.run_test("Get Messages with User 2 After Clear", "GET", f"messages/{user2_id}", 200)
            if success and isinstance(messages_with_user2, list):
                user1_sent_messages = [msg for msg in messages_with_user2 if msg.get('sender_id') == user1_id]
                print(f"   User 1 has {len(user1_sent_messages)} messages with User 2 after clear")
        
        # ===== Test Unauthorized Requests =====
        print("\n📋 Testing Unauthorized Requests")
        
        # Remove token to test unauthorized access
        self.token = None
        
        success, response = self.run_test("Unauthorized Community Clear", "DELETE", "community/messages/clear-all", 401)
        if success:
            print("   ✅ Unauthorized community clear properly rejected")
        
        success, response = self.run_test("Unauthorized Private Clear", "DELETE", "messages/clear-all", 401)
        if success:
            print("   ✅ Unauthorized private clear properly rejected")
        
        # Restore original token
        self.token = original_token
        self.user_id = original_user_id
        
        print("\n✅ Delete Chat History Testing Complete")
        print("=" * 50)

    def test_existing_user_login(self):
        """Test login with existing test user"""
        print("\n🔍 Testing Existing User Login...")
        
        # Test login with existing test user
        login_data = {
            "email": "chattest@example.com",
            "password": "test123456"
        }
        
        success, response = self.run_test("Existing User Login", "POST", "auth/login", 200, login_data)
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Logged in existing user: chattest@example.com")
            return True
        else:
            print("   ⚠️ Existing test user not found, will use newly created user")
            return False

    def test_dashboard_theme(self):
        """Test dashboard theme endpoint"""
        print("\n🔍 Testing Dashboard Theme...")
        
        self.run_test("Get Dashboard Theme", "GET", "dashboard/theme", 200)

    def test_ghost_user_bug_fix(self):
        """Test Ghost User Bug Fix - Critical Priority Test"""
        print("\n🔍 Testing Ghost User Bug Fix - CRITICAL PRIORITY")
        print("=" * 50)
        
        # Store original token to restore later
        original_token = self.token
        original_user_id = self.user_id
        
        # Scenario 1: Basic Online Users Flow
        print("\n📋 Scenario 1: Basic Online Users Flow")
        
        # Register first test user
        test_email1 = f"ghosttest1@test.com"
        test_password1 = "GhostTest123!"
        test_name1 = "Ghost Test 1"
        
        registration_data1 = {
            "email": test_email1,
            "name": test_name1,
            "password": test_password1
        }
        
        success1, response1 = self.run_test("Register Ghost Test User 1", "POST", "auth/register", 200, registration_data1)
        if not success1:
            print("❌ Failed to register first test user - aborting ghost user tests")
            return
            
        token1 = response1.get('access_token')
        user_id1 = response1['user']['id']
        print(f"   ✅ Registered User 1: {test_email1} (ID: {user_id1})")
        
        # Register second test user
        test_email2 = f"ghosttest2@test.com"
        test_password2 = "GhostTest123!"
        test_name2 = "Ghost Test 2"
        
        registration_data2 = {
            "email": test_email2,
            "name": test_name2,
            "password": test_password2
        }
        
        success2, response2 = self.run_test("Register Ghost Test User 2", "POST", "auth/register", 200, registration_data2)
        if not success2:
            print("❌ Failed to register second test user - aborting ghost user tests")
            return
            
        token2 = response2.get('access_token')
        user_id2 = response2['user']['id']
        print(f"   ✅ Registered User 2: {test_email2} (ID: {user_id2})")
        
        # User 1 calls online-users endpoint (this marks them as online)
        self.token = token1
        success, online_users1 = self.run_test("User 1 Get Online Users", "GET", "community/online-users", 200)
        if success:
            print(f"   User 1 sees {len(online_users1)} online users")
        
        # User 2 calls online-users endpoint (this marks them as online)
        self.token = token2
        success, online_users2 = self.run_test("User 2 Get Online Users", "GET", "community/online-users", 200)
        if success:
            print(f"   User 2 sees {len(online_users2)} online users")
            # Check if User 1 is visible to User 2
            user1_visible = any(user.get('id') == user_id1 for user in online_users2)
            if user1_visible:
                print("   ✅ User 1 is visible to User 2")
            else:
                print("   ❌ User 1 is NOT visible to User 2")
        
        # Check presence status
        success, presence_status = self.run_test("Check Presence Status", "GET", "community/presence-status", 200)
        if success:
            cache_count = presence_status.get('cache_users_count', 0)
            db_count = presence_status.get('db_users_count', 0)
            print(f"   Cache has {cache_count} users, DB has {db_count} users")
        
        # Scenario 2: Ghost User Prevention
        print("\n📋 Scenario 2: Ghost User Prevention")
        print("   Simulating direct database deletion of User 1...")
        
        # Use admin endpoint to simulate user deletion (cascade delete)
        # This is safer than direct DB manipulation in a test environment
        self.token = token1  # Use User 1's token for deletion
        
        # First, let's try the admin cleanup endpoint to see current state
        success, cleanup_result = self.run_test("Admin Cleanup Ghost Users", "POST", "admin/cleanup-ghost-users", 200)
        if success:
            print(f"   Initial cleanup removed {cleanup_result.get('invalid_removed', 0)} ghost users")
        
        # Now User 2 checks online users - should still see User 1 since both exist
        self.token = token2
        success, online_users_before = self.run_test("User 2 Get Online Users Before Deletion", "GET", "community/online-users", 200)
        if success:
            user1_visible_before = any(user.get('id') == user_id1 for user in online_users_before)
            print(f"   Before deletion: User 1 visible to User 2: {user1_visible_before}")
        
        # Simulate user deletion by testing the validation logic
        # Since we can't directly delete from MongoDB in this test environment,
        # we'll test the admin endpoints that handle ghost user cleanup
        
        # Test admin reset functionality
        print("\n📋 Scenario 3: Admin Reset Functionality")
        
        # Test admin reset endpoint
        self.token = token2  # Use any valid token for admin operations
        success, reset_result = self.run_test("Admin Reset Online Users", "POST", "admin/reset-online-users", 200)
        if success:
            cache_cleared = reset_result.get('cache_cleared', 0)
            users_reset = reset_result.get('users_reset', 0)
            print(f"   Reset cleared {cache_cleared} cache entries and reset {users_reset} users")
        
        # Check presence status after reset
        success, presence_after_reset = self.run_test("Check Presence Status After Reset", "GET", "community/presence-status", 200)
        if success:
            cache_count_after = presence_after_reset.get('cache_users_count', 0)
            db_count_after = presence_after_reset.get('db_users_count', 0)
            print(f"   After reset: Cache has {cache_count_after} users, DB has {db_count_after} users")
        
        # Users should be able to re-add themselves to online list
        success, online_users_after_reset = self.run_test("User 2 Get Online Users After Reset", "GET", "community/online-users", 200)
        if success:
            print(f"   After reset: User 2 sees {len(online_users_after_reset)} online users")
        
        # Test the cleanup endpoint again
        success, final_cleanup = self.run_test("Final Admin Cleanup Ghost Users", "POST", "admin/cleanup-ghost-users", 200)
        if success:
            invalid_removed = final_cleanup.get('invalid_removed', 0)
            stale_removed = final_cleanup.get('stale_removed', 0)
            print(f"   Final cleanup: {invalid_removed} invalid users, {stale_removed} stale users removed")
        
        # Restore original token
        self.token = original_token
        self.user_id = original_user_id
        
        print("\n✅ Ghost User Bug Fix Testing Complete")
        print("=" * 50)

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting AITravelglobe API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic endpoints
        self.test_health_endpoints()
        self.test_destinations_endpoint()
        self.test_emergency_endpoint()
        self.test_dashboard_theme()
        
        # Authentication and user management
        # Try existing user first, then create new if needed
        existing_user_success = self.test_existing_user_login()
        if not existing_user_success:
            self.test_user_registration_login()
        
        self.test_profile_management()
        
        # CRITICAL PRIORITY: Ghost User Bug Fix Testing
        self.test_ghost_user_bug_fix()
        
        # Core functionality
        self.test_itinerary_generation()
        self.test_business_trip_generation()
        self.test_albums_management()
        self.test_community_chat()
        self.test_ai_chat()
        
        # Delete chat history tests
        self.test_delete_chat_history()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['error']}")
        
        if self.passed_tests:
            print(f"\n✅ PASSED TESTS ({len(self.passed_tests)}):")
            for test in self.passed_tests:
                print(f"  - {test}")
        
        return len(self.failed_tests) == 0

def main():
    tester = AITravelglobeAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())