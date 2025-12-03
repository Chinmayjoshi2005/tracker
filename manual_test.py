#!/usr/bin/env python3
"""
Simple manual test for registration functionality
"""

import os
import sys
sys.path.insert(0, '/Users/chinmayjoshi/Desktop/projects/tracker')

from app import app, db
from models import User

def test_registration_manually():
    """Manually test registration functionality"""
    print("🔧 Manual Registration Test")
    print("=" * 40)
    
    with app.app_context():
        try:
            # Test 1: Check if database tables exist
            print("1. Checking database tables...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            required_tables = ['user', 'task', 'schedule', 'schedule_feedback']
            
            for table in required_tables:
                if table in tables:
                    print(f"   ✅ {table} table exists")
                else:
                    print(f"   ❌ {table} table missing")
            
            # Test 2: Try to create a user manually
            print("\n2. Testing user creation...")
            
            # Clean up any existing test user
            test_user = User.query.filter_by(username='manualtest').first()
            if test_user:
                print("   🗑️  Removing existing test user")
                db.session.delete(test_user)
                db.session.commit()
            
            # Create new user
            new_user = User(username='manualtest', email='manual@test.com')
            new_user.set_password('testpass123')
            
            db.session.add(new_user)
            db.session.commit()
            print("   ✅ User created successfully")
            
            # Test 3: Verify user authentication
            print("\n3. Testing user authentication...")
            user = User.query.filter_by(username='manualtest').first()
            if user and user.check_password('testpass123'):
                print("   ✅ User authentication working")
                print(f"   👤 User ID: {user.id}")
                print(f"   📧 Email: {user.email}")
            else:
                print("   ❌ User authentication failed")
            
            # Test 4: Test duplicate username handling
            print("\n4. Testing duplicate username protection...")
            try:
                duplicate_user = User(username='manualtest', email='another@test.com')
                duplicate_user.set_password('testpass123')
                db.session.add(duplicate_user)
                db.session.commit()
                print("   ❌ Duplicate username allowed (should not happen)")
                db.session.rollback()
            except Exception as e:
                db.session.rollback()
                print("   ✅ Duplicate username correctly rejected")
            
            # Test 5: Test duplicate email handling
            print("\n5. Testing duplicate email protection...")
            try:
                duplicate_email_user = User(username='differentuser', email='manual@test.com')
                duplicate_email_user.set_password('testpass123')
                db.session.add(duplicate_email_user)
                db.session.commit()
                print("   ❌ Duplicate email allowed (should not happen)")
                db.session.rollback()
            except Exception as e:
                db.session.rollback()
                print("   ✅ Duplicate email correctly rejected")
            
            # Clean up
            print("\n6. Cleaning up test data...")
            test_user = User.query.filter_by(username='manualtest').first()
            if test_user:
                db.session.delete(test_user)
                db.session.commit()
                print("   ✅ Test user cleaned up")
            
            print("\n🎉 Manual registration test completed successfully!")
            print("\n💡 If you're experiencing registration issues in the web interface,")
            print("   it might be due to:")
            print("   - CSRF token issues")
            print("   - JavaScript errors")
            print("   - Network connectivity problems")
            print("   - Browser cache issues")
            
        except Exception as e:
            print(f"❌ Manual test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_registration_manually()