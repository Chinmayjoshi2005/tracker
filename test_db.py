#!/usr/bin/env python3
"""
Test script to check database connectivity and table structure
"""

from app import app, db
from models import User, Task, Schedule, ScheduleFeedback

def test_database():
    """Test database connectivity and table creation"""
    with app.app_context():
        try:
            # Create all tables
            print("Creating tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Existing tables: {tables}")
            
            # Check specific table structures
            for table_name in ['user', 'task', 'schedule', 'schedule_feedback']:
                if table_name in tables:
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    print(f"📄 {table_name.capitalize()} table columns: {columns}")
                else:
                    print(f"❌ Table {table_name} not found")
            
            # Test user creation
            print("\nTesting user creation...")
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(username='testuser', email='test@example.com')
                test_user.set_password('testpass123')
                db.session.add(test_user)
                db.session.commit()
                print("✅ Test user created successfully")
            else:
                print("ℹ️  Test user already exists")
                
            # Verify user
            user = User.query.filter_by(username='testuser').first()
            if user and user.check_password('testpass123'):
                print("✅ User authentication working")
            else:
                print("❌ User authentication failed")
                
            print("\n🎉 Database test completed successfully!")
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_database()