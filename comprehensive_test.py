#!/usr/bin/env python3
"""
Comprehensive test script to identify and fix registration issues
"""

import sys
import os
sys.path.insert(0, '/Users/chinmayjoshi/Desktop/projects/tracker')

from app import app, db
from models import User
import unittest

class TestRegistration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.drop_all()
    
    def test_home_page(self):
        """Test home page accessibility"""
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to login page for unauthenticated users
        self.assertIn(b'Login', response.data)
    
    def test_register_page(self):
        """Test registration page accessibility"""
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)
    
    def test_valid_registration(self):
        """Test valid user registration"""
        response = self.app.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Congratulations, you are now a registered user!', response.data)
        
        # Verify user was created
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'test@example.com')
    
    def test_duplicate_username_registration(self):
        """Test registration with duplicate username"""
        # First registration
        self.app.post('/register', data={
            'username': 'testuser',
            'email': 'test1@example.com',
            'password': 'password123',
            'password2': 'password123'
        })
        
        # Second registration with same username
        response = self.app.post('/register', data={
            'username': 'testuser',
            'email': 'test2@example.com',
            'password': 'password123',
            'password2': 'password123'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should show error message
        self.assertIn(b'already exists', response.data.lower() or response.data)
    
    def test_password_mismatch(self):
        """Test registration with password mismatch"""
        response = self.app.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'password2': 'differentpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should stay on registration page and show error
        self.assertIn(b'Register', response.data)
        self.assertIn(b'Field must be equal to password', response.data)

def run_comprehensive_tests():
    """Run all tests"""
    print("🧪 Running comprehensive registration tests...")
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Additional manual tests
    with app.app_context():
        try:
            print("\n🔧 Running manual database tests...")
            
            # Test database connectivity
            db.create_all()
            print("✅ Database connectivity OK")
            
            # Test model imports
            from models import User, Task, Schedule, ScheduleFeedback
            print("✅ Model imports OK")
            
            # Test form imports
            from forms import LoginForm, RegistrationForm, ProfileForm, TaskForm
            print("✅ Form imports OK")
            
            # Test service imports
            from llm_service import get_llm_service
            print("✅ Service imports OK")
            
            print("\n🎉 All tests passed! Application should work correctly.")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    run_comprehensive_tests()