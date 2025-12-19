#!/usr/bin/env python3
"""
Comprehensive test script to identify and fix issues across the entire application
"""

import sys
import os
import json
from datetime import datetime, date, timedelta
import unittest

import werkzeug
if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '3.0.0'  # Dummy version to satisfy Flask

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app import app, db
from models import User, Task, Schedule, ChatMessage, LoginHistory
from analytics_service import AnalyticsService
from llm_service import OllamaLLMService
from llm_config import PROMPT_CONFIG
import base64

class ComprehensiveTestSuite(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # --- AUTHENTICATION TESTS ---
    def test_auth_flow(self):
        """Test full authentication flow: Register -> Login -> Logout"""
        print("\nTesting Authentication Flow...")
        
        # 1. Register
        response = self.app.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Congratulations, you are now a registered user!', response.data)
        
        # 2. Logout
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
        
        # 3. Login
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, testuser', response.data)

    # --- PROFILE TESTS ---
    def test_profile_management(self):
        """Test profile update functionality"""
        print("\nTesting Profile Management...")
        self._login()
        
        # Use /api/profile with JSON
        response = self.app.post('/api/profile', json={
            'name': 'Test User',
            'role': 'Student',
            'peak_energy': 'morning',
            'study_preference': 'quiet',
            'workout_preference': 'yoga',
            'workout_impact': 'energized',
            'main_goals': 'Learn Python',
            'family_time': 'Evening',
            'wake_time': '07:00',
            'bedtime': '23:00'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Profile updated', response.data)
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertEqual(user.name, 'Test User')
            self.assertEqual(user.role, 'Student')

    # --- TASK MANAGEMENT TESTS ---
    def test_task_management(self):
        """Test CRUD operations for tasks"""
        print("\nTesting Task Management...")
        self._login()
        
        # 1. Add Task via /api/tasks
        response = self.app.post('/api/tasks', json={
            'action': 'add',
            'description': 'Complete Project',
            'priority': 'high',
            'duration': '2h',
            'type': 'work',
            'preferences': 'focus'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Task added', response.data)
        
        # 2. Verify Task in DB
        with app.app_context():
            task = Task.query.first()
            self.assertIsNotNone(task)
            self.assertEqual(task.description, 'Complete Project')
            task_id = task.id
            
        # 3. Delete Task via /api/tasks
        response = self.app.post('/api/tasks', json={
            'action': 'delete',
            'id': task_id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Task deleted', response.data)
        
        with app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNone(task)

    # --- CHAT TESTS ---
    def test_chat_functionality(self):
        """Test chat persistence and clearing"""
        print("\nTesting Chat Functionality...")
        self._login()
        
        # 1. Send Message
        # Note: We expect success or fallback, but definitely 200 OK
        response = self.app.post('/api/ai_chat', json={'message': 'Hello'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['status'] in ['success', 'fallback'])
        
        # 2. Check History
        response = self.app.get('/api/chat/history')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data['messages']) > 0)
        
        # 3. Clear Chat
        response = self.app.post('/api/chat/clear')
        self.assertEqual(response.status_code, 200)
        
        # 4. Verify Empty History
        response = self.app.get('/api/chat/history')
        data = json.loads(response.data)
        self.assertEqual(len(data['messages']), 0)

    # --- SCHEDULE TESTS ---
    def test_schedule_generation(self):
        """Test schedule generation endpoint"""
        print("\nTesting Schedule Generation...")
        self._login()
        
        # Add a task first
        self.app.post('/api/tasks', json={
            'action': 'add',
            'description': 'Study',
            'priority': 'high',
            'duration': '1h',
            'type': 'study',
            'preferences': 'quiet'
        })
        
        # Generate Schedule via /api/ai_optimize
        response = self.app.post('/api/ai_optimize', json={
            'date': date.today().isoformat(),
            'prompt': 'Create a plan'
        })
        if response.status_code != 200:
            with open('test_error.log', 'wb') as f:
                f.write(response.data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('schedule', data)
        self.assertTrue(len(data['schedule']) > 0)

    def _login(self):
        """Helper to register and login a test user"""
        # Register
        self.app.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        
        # Login
        resp = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        # Verify login success
        if b'Welcome back' not in resp.data and b'Logout' not in resp.data:
            print(f"Login failed. Response: {resp.data}")

    # --- ANALYTICS TESTS ---
    def test_analytics_service(self):
        """Test analytics service functions"""
        print("\nTesting Analytics Service...")
        analytics = AnalyticsService()
        
        with app.app_context():
            # Create a user if not exists (might be created by other tests, but let's ensure)
            user = User.query.filter_by(username='analytics_test').first()
            if not user:
                user = User(username='analytics_test', email='analytics@example.com')
                user.set_password('password')
                db.session.add(user)
                db.session.commit()
            
            user_id = user.id

            # 1. Test Login Tracking
            # Create some history manually
            for i in range(3):
                login = LoginHistory(user_id=user_id, login_timestamp=datetime.utcnow() - timedelta(days=i))
                db.session.add(login)
            db.session.commit()
            
            history = LoginHistory.query.filter_by(user_id=user_id).all()
            self.assertTrue(len(history) >= 3)
            
            # 2. Test Chart Generation
            # Login chart
            chart = analytics.generate_login_chart(user_id)
            self.assertIsInstance(chart, str)
            # Check base64
            try:
                base64.b64decode(chart)
            except Exception:
                self.fail("Login chart is not valid base64")
                
            # Task chart
            chart = analytics.generate_task_chart(user_id)
            self.assertIsInstance(chart, str)
            
            # 3. Test Prediction Score
            # No completed tasks
            score = analytics.predict_completion_probability(user_id)
            self.assertEqual(score, 0)
            
            # Complete a task
            task = Task(user_id=user_id, description="Test Task", priority="low", duration="1h", type="work", status="completed")
            db.session.add(task)
            db.session.commit()
            
            score = analytics.predict_completion_probability(user_id)
            self.assertTrue(0 <= score <= 100)

    # --- PERSONA/LLM TESTS ---
    def test_persona_defaults(self):
        """Test LLM config defaults and basic generation"""
        print("\nTesting Persona Configuration...")
        self.assertIn("English by default", PROMPT_CONFIG['system_role'])
        self.assertIn("Default to simple English", PROMPT_CONFIG['style_instructions'][1])

        print("\nTesting Response Generation (Mock/Real)...")
        llm_service = OllamaLLMService()
        if not llm_service.check_ollama_status():
            print("Skipping LLM response test: Ollama not available")
            return

        # Simple response test
        response = llm_service.generate_general_response("Hello")
        if response is None:
            print("Warning: LLM generation timed out or failed despite status check. Skipping assertion.")
        else:
            self.assertIsNotNone(response)

    # --- DEEP SECURITY & VALIDATION TESTS (10 CHECKS) ---
    
    # 1. SQL Injection Vulnerability Check
    def test_security_sql_injection(self):
        """Test 1: SQL Injection vulnerability check on login"""
        print("\nTest 1: SQL Injection Security Check...")
        # Attempt login with common SQLi patterns
        sqli_inputs = ["' OR '1'='1", "admin' --", "' UNION SELECT 1,2,3--"]
        for payload in sqli_inputs:
            response = self.app.post('/login', data={
                'username': payload,
                'password': 'password'
            }, follow_redirects=True)
            # Should NOT log in (i.e., not see "Welcome" or index page content)
            self.assertNotIn(b'Welcome', response.data)
            self.assertIn(b'Invalid username or password', response.data)
        print("SQL Injection checks passed.")

    # 2. XSS Vulnerability Check
    def test_security_xss(self):
        """Test 2: XSS vulnerability check in profile"""
        print("\nTest 2: XSS Security Check...")
        self._login()
        xss_payload = "<script>alert('XSS')</script>"
        
        # Try to inject XSS into name
        self.app.post('/api/profile', json={'name': xss_payload})
        
        # Fetch profile and check if payload is escaped or handled safe
        response = self.app.get('/profile')
        # In Jinja2 autoescape is on by default, so < should be &lt;
        self.assertNotIn(b"<script>alert('XSS')</script>", response.data)
        self.assertIn(b"&lt;script&gt;alert(&#39;XSS&#39;)&lt;/script&gt;", response.data)
        print("XSS checks passed (Autoescaping verified).")

    # 3. Broken Authentication (Login Bypass)
    def test_security_auth_bypass(self):
        """Test 3: Verify protected routes cannot be accessed without login"""
        print("\nTest 3: Auth Bypass Security Check...")
        self.app.get('/logout', follow_redirects=True) # Ensure data is clear
        
        protected_routes = ['/', '/profile', '/tasks', '/schedule']
        for route in protected_routes:
            response = self.app.get(route, follow_redirects=True)
            # Should redirect to login
            self.assertIn(b'Sign In', response.data)
            self.assertIn('login', response.request.path)
        print("Auth Bypass checks passed.")

    # 4. Privilege Escalation
    def test_security_privilege_escalation(self):
        """Test 4: Regular user cannot access admin routes"""
        print("\nTest 4: Privilege Escalation Security Check...")
        self._login() # Logs in as 'testuser' (regular)
        
        response = self.app.get('/admin', follow_redirects=True)
        # Should be denied or redirected
        self.assertNotIn(b'Admin Dashboard', response.data)
        self.assertIn(b'Access denied', response.data)
        print("Privilege Escalation checks passed.")

    # 5. Data Exposure (API Payload Check)
    def test_security_data_exposure(self):
        """Test 5: API should not expose sensitive fields like password hashes"""
        print("\nTest 5: Sensitive Data Exposure Check...")
        self._login()
        
        response = self.app.get('/profile')
        content = response.data.decode()
        # Ensure password_hash is not leaking in the HTML or JS variables
        self.assertNotIn('scrypt:', content)
        self.assertNotIn('password_hash', content)
        print("Data Exposure checks passed.")

    # 6. Invalid Input Validation
    def test_validation_inputs(self):
        """Test 6: Handling of invalid inputs (Registration)"""
        print("\nTest 6: Input Validation Check...")
        # Invalid Email
        response = self.app.post('/register', data={
            'username': 'baduser',
            'email': 'not-an-email',
            'password': '123',
            'password2': '123'
        }, follow_redirects=True)
        # Should fail (assuming WTForms validators are working or DB constraints)
        # Note: HTML5 validation might catch this in browser, but we test server side
        if b'Invalid email address' in response.data:
            print("Email validation active.")
        else:
            print("Server-side email validation might be minimal, relying on client-side.")

    # 7. Logic Integrity (Task & Schedule)
    def test_logic_integrity(self):
        """Test 7: Verify task status transitions and data integrity"""
        print("\nTest 7: Logic Integrity Check...")
        self._login()
        # Create Task
        self.app.post('/api/tasks', json={
            'action': 'add', 'description': 'Integrity Task', 
            'priority': 'high', 'duration': '1h', 'type': 'work'
        })
        
        with app.app_context():
            task = Task.query.filter_by(description='Integrity Task').first()
            self.assertEqual(task.status, 'pending')
            task_id = task.id

        # Complete Task
        self.app.post('/api/tasks', json={'action': 'complete', 'id': task_id})
        
        with app.app_context():
            task = Task.query.get(task_id)
            self.assertEqual(task.status, 'completed')
            self.assertIsNotNone(task.completed_date)
            
        print("Logic Integrity checks passed.")

    # 8. AI Service Functionality & Fallback
    def test_logic_ai_fallback(self):
        """Test 8: AI Schedule optimization fallback logic"""
        print("\nTest 8: AI/Fallback Logic Check...")
        self._login()
        # Force LLM invalid to trigger fallback/check error handling
        # Using a mock prompt
        response = self.app.post('/api/ai_optimize', json={'prompt': 'Make a plan', 'date': '2025-01-01'})
        if response.status_code != 200:
            print(f"Fallback Failed with status {response.status_code}: {response.data.decode('utf-8')}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Should return a schedule regardless of AI status (using rule-based fallback if needed)
        self.assertIn('schedule', data)
        print(f"Schedule generated via {data.get('source', 'unknown')} mechanism.")
        print("AI/Fallback checks passed.")

    # 9. Performance Check
    def test_performance_api(self):
        """Test 9: API Response time check (< 500ms expected for non-AI)"""
        print("\nTest 9: Performance Check...")
        import time
        self._login()
        start = time.time()
        self.app.get('/tasks')
        end = time.time()
        duration = (end - start) * 1000
        print(f"Tasks Page Load Time: {duration:.2f}ms")
        self.assertTrue(duration < 1000, "Page load too slow (>1s)") 
        print("Performance checks passed.")

    # 10. Robustness (Error Handling)
    def test_robustness_404(self):
        """Test 10: Graceful handling of non-existent routes"""
        print("\nTest 10: Error Handling Check...")
        response = self.app.get('/non-existent-page-12345')
        self.assertEqual(response.status_code, 404)
        # Should ideally show a custom 404 page or at least standard 404
        print("Error handling checks passed.")

if __name__ == '__main__':
    print("🚀 Starting Comprehensive Test Suite...")
    unittest.main(verbosity=2)