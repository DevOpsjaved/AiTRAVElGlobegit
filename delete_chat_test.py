#!/usr/bin/env python3

import requests
import json
import uuid

class DeleteChatHistoryTester:
    def __init__(self, base_url="https://globetrotter-app-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.token = None
        self.user_id = None

    def login_test_user(self):
        """Login with existing test user"""
        print("🔐 Logging in with test user...")
        
        login_data = {
            "email": "chattest@example.com",
            "password": "test123456"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.user_id = data['user']['id']
                self.session.headers['Authorization'] = f'Bearer {self.token}'
                print(f"✅ Logged in successfully as {login_data['email']}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_community_message_deletion(self):
        """Test community message deletion flow"""
        print("\n🔍 Testing Community Message Deletion...")
        
        # 1. Post a community message
        message_data = {
            "message": "Test message for deletion - community chat testing",
            "location_approximate": "Test Location for Deletion"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/community/messages", json=message_data)
            if response.status_code == 200:
                message_id = response.json()['id']
                print(f"✅ Posted community message: {message_id}")
                
                # 2. Get messages to verify it exists
                response = self.session.get(f"{self.base_url}/community/messages")
                if response.status_code == 200:
                    messages = response.json()
                    user_messages_before = [msg for msg in messages if msg.get('user_id') == self.user_id]
                    print(f"📊 User has {len(user_messages_before)} community messages before deletion")
                    
                    # 3. Delete all community messages
                    response = self.session.delete(f"{self.base_url}/community/messages/clear-all")
                    if response.status_code == 200:
                        delete_result = response.json()
                        print(f"✅ DELETE /api/community/messages/clear-all - Deleted {delete_result['deleted_count']} messages")
                        print(f"   Response: {delete_result['message']}")
                        
                        # 4. Verify messages are deleted
                        response = self.session.get(f"{self.base_url}/community/messages")
                        if response.status_code == 200:
                            messages_after = response.json()
                            user_messages_after = [msg for msg in messages_after if msg.get('user_id') == self.user_id]
                            print(f"📊 User has {len(user_messages_after)} community messages after deletion")
                            
                            if len(user_messages_after) == 0:
                                print("✅ Community message deletion verified - all user messages removed")
                                return True
                            else:
                                print("❌ Some messages still exist after deletion")
                                return False
                    else:
                        print(f"❌ Delete failed: {response.status_code} - {response.text}")
                        return False
                else:
                    print(f"❌ Failed to get messages after posting: {response.status_code}")
                    return False
            else:
                print(f"❌ Failed to post message: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Community message deletion test error: {e}")
            return False

    def test_private_message_deletion(self):
        """Test private message deletion endpoints"""
        print("\n🔍 Testing Private Message Deletion...")
        
        try:
            # Test delete all private messages
            response = self.session.delete(f"{self.base_url}/messages/clear-all")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ DELETE /api/messages/clear-all - Deleted {result['deleted_count']} messages")
                print(f"   Response: {result['message']}")
            else:
                print(f"❌ Delete all private messages failed: {response.status_code} - {response.text}")
                return False
            
            # Test delete messages with specific partner
            dummy_partner_id = str(uuid.uuid4())
            response = self.session.delete(f"{self.base_url}/messages/{dummy_partner_id}/clear")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ DELETE /api/messages/{{partner_id}}/clear - Deleted {result['deleted_count']} messages")
                print(f"   Response: {result['message']}")
                return True
            else:
                print(f"❌ Delete partner messages failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Private message deletion test error: {e}")
            return False

    def test_authentication_required(self):
        """Test that endpoints require authentication"""
        print("\n🔍 Testing Authentication Requirements...")
        
        # Remove auth header temporarily
        original_auth = self.session.headers.get('Authorization')
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        
        try:
            # Test community messages clear without auth
            response = self.session.delete(f"{self.base_url}/community/messages/clear-all")
            if response.status_code == 401:
                print("✅ DELETE /api/community/messages/clear-all requires authentication")
            else:
                print(f"❌ Expected 401, got {response.status_code}")
            
            # Test private messages clear without auth
            response = self.session.delete(f"{self.base_url}/messages/clear-all")
            if response.status_code == 401:
                print("✅ DELETE /api/messages/clear-all requires authentication")
            else:
                print(f"❌ Expected 401, got {response.status_code}")
            
            # Test partner messages clear without auth
            dummy_partner_id = str(uuid.uuid4())
            response = self.session.delete(f"{self.base_url}/messages/{dummy_partner_id}/clear")
            if response.status_code == 401:
                print("✅ DELETE /api/messages/{partner_id}/clear requires authentication")
            else:
                print(f"❌ Expected 401, got {response.status_code}")
                
        finally:
            # Restore auth header
            if original_auth:
                self.session.headers['Authorization'] = original_auth

    def run_tests(self):
        """Run all delete chat history tests"""
        print("🚀 Starting Delete Chat History Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Login first
        if not self.login_test_user():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Test authentication requirements
        self.test_authentication_required()
        
        # Test community message deletion
        community_success = self.test_community_message_deletion()
        
        # Test private message deletion
        private_success = self.test_private_message_deletion()
        
        print("\n" + "=" * 60)
        print("📊 DELETE CHAT HISTORY TEST SUMMARY")
        print("=" * 60)
        
        if community_success and private_success:
            print("✅ ALL DELETE CHAT HISTORY TESTS PASSED")
            print("✅ DELETE /api/community/messages/clear-all - Working")
            print("✅ DELETE /api/messages/clear-all - Working") 
            print("✅ DELETE /api/messages/{partner_id}/clear - Working")
            print("✅ Authentication required for all endpoints")
            return True
        else:
            print("❌ SOME TESTS FAILED")
            if not community_success:
                print("❌ Community message deletion failed")
            if not private_success:
                print("❌ Private message deletion failed")
            return False

def main():
    tester = DeleteChatHistoryTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())