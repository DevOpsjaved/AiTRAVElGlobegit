#!/usr/bin/env python3

import requests
import json
import uuid

class ComprehensiveDeleteChatTester:
    def __init__(self, base_url="https://globetrotter-app-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.token = None
        self.user_id = None
        self.second_user_id = None
        self.second_token = None

    def create_test_user(self):
        """Create a second test user for private messaging"""
        print("👤 Creating second test user...")
        
        test_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": test_email,
            "name": "Test User 2",
            "password": "TestPass123!"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/register", json=user_data)
            if response.status_code == 200:
                data = response.json()
                self.second_user_id = data['user']['id']
                self.second_token = data['access_token']
                print(f"✅ Created second user: {test_email} (ID: {self.second_user_id})")
                return True
            else:
                print(f"❌ Failed to create second user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating second user: {e}")
            return False

    def login_test_user(self):
        """Login with existing test user"""
        print("🔐 Logging in with main test user...")
        
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
                print(f"✅ Logged in successfully as {login_data['email']} (ID: {self.user_id})")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def send_private_message(self, recipient_id, content):
        """Send a private message"""
        message_data = {
            "recipient_id": recipient_id,
            "content": content
        }
        
        try:
            response = self.session.post(f"{self.base_url}/messages", json=message_data)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to send private message: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error sending private message: {e}")
            return None

    def test_comprehensive_delete_flow(self):
        """Test comprehensive delete chat history flow"""
        print("\n🔍 Testing Comprehensive Delete Chat History Flow...")
        
        # 1. Send multiple private messages to the second user
        print("📤 Sending private messages...")
        messages_sent = []
        for i in range(3):
            content = f"Test private message {i+1} for deletion testing"
            message = self.send_private_message(self.second_user_id, content)
            if message:
                messages_sent.append(message['id'])
                print(f"✅ Sent private message {i+1}: {message['id']}")
        
        if not messages_sent:
            print("❌ No private messages sent, cannot test deletion")
            return False
        
        # 2. Post community messages
        print("\n📤 Posting community messages...")
        community_messages = []
        for i in range(2):
            message_data = {
                "message": f"Test community message {i+1} for deletion testing",
                "location_approximate": f"Test Location {i+1}"
            }
            
            try:
                response = self.session.post(f"{self.base_url}/community/messages", json=message_data)
                if response.status_code == 200:
                    msg_id = response.json()['id']
                    community_messages.append(msg_id)
                    print(f"✅ Posted community message {i+1}: {msg_id}")
            except Exception as e:
                print(f"❌ Error posting community message: {e}")
        
        # 3. Verify messages exist before deletion
        print("\n📊 Verifying messages before deletion...")
        
        # Check private messages
        try:
            response = self.session.get(f"{self.base_url}/messages/{self.second_user_id}")
            if response.status_code == 200:
                private_msgs = response.json()
                user_private_msgs = [msg for msg in private_msgs if msg.get('sender_id') == self.user_id]
                print(f"📊 Found {len(user_private_msgs)} private messages with second user")
            else:
                print(f"❌ Failed to get private messages: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting private messages: {e}")
        
        # Check community messages
        try:
            response = self.session.get(f"{self.base_url}/community/messages")
            if response.status_code == 200:
                all_community_msgs = response.json()
                user_community_msgs = [msg for msg in all_community_msgs if msg.get('user_id') == self.user_id]
                print(f"📊 Found {len(user_community_msgs)} community messages from user")
            else:
                print(f"❌ Failed to get community messages: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting community messages: {e}")
        
        # 4. Test specific conversation deletion
        print("\n🗑️ Testing specific conversation deletion...")
        try:
            response = self.session.delete(f"{self.base_url}/messages/{self.second_user_id}/clear")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ DELETE /api/messages/{{partner_id}}/clear - Deleted {result['deleted_count']} messages")
                print(f"   Response: {result['message']}")
                
                # Verify specific conversation is cleared
                response = self.session.get(f"{self.base_url}/messages/{self.second_user_id}")
                if response.status_code == 200:
                    remaining_msgs = response.json()
                    user_msgs_after = [msg for msg in remaining_msgs if msg.get('sender_id') == self.user_id]
                    print(f"📊 {len(user_msgs_after)} messages remaining in conversation after deletion")
                    
                    if len(user_msgs_after) == 0:
                        print("✅ Specific conversation deletion verified")
                    else:
                        print("❌ Some messages still exist in conversation")
            else:
                print(f"❌ Specific conversation deletion failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error in specific conversation deletion: {e}")
            return False
        
        # 5. Send more messages and test clear all private messages
        print("\n📤 Sending more private messages for clear-all test...")
        for i in range(2):
            content = f"Additional test message {i+1} for clear-all testing"
            message = self.send_private_message(self.second_user_id, content)
            if message:
                print(f"✅ Sent additional message {i+1}: {message['id']}")
        
        # 6. Test clear all private messages
        print("\n🗑️ Testing clear all private messages...")
        try:
            response = self.session.delete(f"{self.base_url}/messages/clear-all")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ DELETE /api/messages/clear-all - Deleted {result['deleted_count']} messages")
                print(f"   Response: {result['message']}")
            else:
                print(f"❌ Clear all private messages failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error in clear all private messages: {e}")
            return False
        
        # 7. Test clear all community messages
        print("\n🗑️ Testing clear all community messages...")
        try:
            response = self.session.delete(f"{self.base_url}/community/messages/clear-all")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ DELETE /api/community/messages/clear-all - Deleted {result['deleted_count']} messages")
                print(f"   Response: {result['message']}")
            else:
                print(f"❌ Clear all community messages failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error in clear all community messages: {e}")
            return False
        
        # 8. Final verification - all user messages should be gone
        print("\n📊 Final verification...")
        
        # Check private messages
        try:
            response = self.session.get(f"{self.base_url}/messages/{self.second_user_id}")
            if response.status_code == 200:
                final_private_msgs = response.json()
                user_final_private = [msg for msg in final_private_msgs if msg.get('sender_id') == self.user_id]
                print(f"📊 Final private messages count: {len(user_final_private)}")
                
                if len(user_final_private) == 0:
                    print("✅ All private messages successfully deleted")
                else:
                    print("❌ Some private messages still exist")
                    return False
        except Exception as e:
            print(f"❌ Error in final private message check: {e}")
        
        # Check community messages
        try:
            response = self.session.get(f"{self.base_url}/community/messages")
            if response.status_code == 200:
                final_community_msgs = response.json()
                user_final_community = [msg for msg in final_community_msgs if msg.get('user_id') == self.user_id]
                print(f"📊 Final community messages count: {len(user_final_community)}")
                
                if len(user_final_community) == 0:
                    print("✅ All community messages successfully deleted")
                    return True
                else:
                    print("❌ Some community messages still exist")
                    return False
        except Exception as e:
            print(f"❌ Error in final community message check: {e}")
            return False

    def run_tests(self):
        """Run comprehensive delete chat history tests"""
        print("🚀 Starting Comprehensive Delete Chat History Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 70)
        
        # Setup
        if not self.login_test_user():
            print("❌ Cannot proceed without main user authentication")
            return False
        
        if not self.create_test_user():
            print("❌ Cannot proceed without second user")
            return False
        
        # Run comprehensive test
        success = self.test_comprehensive_delete_flow()
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE DELETE CHAT HISTORY TEST SUMMARY")
        print("=" * 70)
        
        if success:
            print("✅ ALL COMPREHENSIVE DELETE TESTS PASSED")
            print("✅ Private message creation and deletion - Working")
            print("✅ Community message creation and deletion - Working")
            print("✅ DELETE /api/messages/{partner_id}/clear - Working")
            print("✅ DELETE /api/messages/clear-all - Working")
            print("✅ DELETE /api/community/messages/clear-all - Working")
            print("✅ End-to-end delete chat history flow - Working")
            return True
        else:
            print("❌ COMPREHENSIVE DELETE TESTS FAILED")
            return False

def main():
    tester = ComprehensiveDeleteChatTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())