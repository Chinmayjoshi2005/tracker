#!/usr/bin/env python3
"""
Database Migration Script
Adds new fields for schedule quality scoring and user feedback
"""

from app import app, db
from models import Schedule, ScheduleFeedback
from sqlalchemy import inspect

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_database():
    """Add new columns to existing tables"""
    with app.app_context():
        print("🔄 Starting database migration...")
        
        # Create all tables (will create ScheduleFeedback if it doesn't exist)
        db.create_all()
        print("✅ Created new tables (if any)")
        
        # Check if Schedule table needs new columns
        needs_update = False
        
        if not check_column_exists('schedule', 'quality_score'):
            print("➕ Adding quality_score column to Schedule table")
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE schedule ADD COLUMN quality_score INTEGER'))
                conn.commit()
            needs_update = True
        
        if not check_column_exists('schedule', 'user_rating'):
            print("➕ Adding user_rating column to Schedule table")
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE schedule ADD COLUMN user_rating INTEGER'))
                conn.commit()
            needs_update = True
        
        if not check_column_exists('schedule', 'user_feedback'):
            print("➕ Adding user_feedback column to Schedule table")
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE schedule ADD COLUMN user_feedback TEXT'))
                conn.commit()
            needs_update = True
        
        if needs_update:
            print("✅ Schedule table updated successfully")
        else:
            print("✅ Schedule table already up to date")
        
        # Verify ScheduleFeedback table exists
        if db.engine.dialect.has_table(db.engine.connect(), 'schedule_feedback'):
            print("✅ ScheduleFeedback table exists")
        else:
            print("⚠️  ScheduleFeedback table not found - running db.create_all()")
            db.create_all()
            print("✅ ScheduleFeedback table created")
        
        print("\n🎉 Database migration completed successfully!")
        print("\nNew features available:")
        print("  - Schedule quality scoring")
        print("  - User feedback and ratings")
        print("  - Enhanced AI optimization metrics")

if __name__ == '__main__':
    migrate_database()
