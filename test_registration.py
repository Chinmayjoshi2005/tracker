#!/usr/bin/env python3
"""
Test script to simulate user registration
"""

from app import app, db
from models import User

def test_registration():
    """Test user registration process"""
    with app.app_context():
        try:
            print("Testing user registration...")
            
            # Check if test user already exists
            existing_user = User.query.filter_by(username='newuser').first()
            if existing_user:
                print("🗑️  Removing existing test user")
                db.session.delete(existing_user)
                db.session.commit()
            
            # Create new user
            new_user = User(username='newuser', email='newuser@example.com')
            new_user.set_password('password123')
            
            db.session.add(new_user)
            db.session.commit()
            
            print("✅ User registered successfully")
            
            # Verify user
            user = User.query.filter_by(username='newuser').first()
            if user and user.check_password('password123'):
                print("✅ User authentication verified")
                print(f"👤 User ID: {user.id}")
                print(f"📧 Email: {user.email}")
                print(f"📅 Created: {user.created_at}")
            else:
                print("❌ User verification failed")
                
            # Test duplicate username
            print("\nTesting duplicate username protection...")
            duplicate_user = User(username='newuser', email='another@example.com')
            duplicate_user.set_password('password123')
            db.session.add(duplicate_user)
            
            try:
                db.session.commit()
                print("❌ Duplicate username allowed (should not happen)")
            except Exception as e:
                db.session.rollback()
                print("✅ Duplicate username correctly rejected")
                
            # Test duplicate email
            print("\nTesting duplicate email protection...")
            duplicate_email_user = User(username='differentuser', email='newuser@example.com')
            duplicate_email_user.set_password('password123')
            db.session.add(duplicate_email_user)
            
            try:
                db.session.commit()
                print("❌ Duplicate email allowed (should not happen)")
            except Exception as e:
                db.session.rollback()
                print("✅ Duplicate email correctly rejected")
                
            print("\n🎉 Registration test completed successfully!")
            
        except Exception as e:
            print(f"❌ Registration test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_registration()