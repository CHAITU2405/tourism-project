#!/usr/bin/env python3
"""
Migration script to add profile_picture field to VehicleRental model
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_profile_picture():
    """Add profile_picture field to VehicleRental table"""
    with app.app_context():
        try:
            print("🔄 Starting profile picture migration...")
            
            # Check if profile_picture column exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('vehicle_rental')]
            
            if 'profile_picture' not in columns:
                print("📝 Adding profile_picture column to VehicleRental table...")
                db.engine.execute('ALTER TABLE vehicle_rental ADD COLUMN profile_picture VARCHAR(200)')
                print("✅ profile_picture column added successfully")
            else:
                print("✅ profile_picture column already exists")
            
            # Create uploads directory structure
            uploads_dir = os.path.join('static', 'uploads', 'companies')
            os.makedirs(uploads_dir, exist_ok=True)
            print(f"📁 Created uploads directory: {uploads_dir}")
            
            print("🎉 Profile picture migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    success = migrate_profile_picture()
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Vehicle rental owners can now upload profile pictures during profile completion")
        print("2. Profile pictures will be displayed in the dashboard")
        print("3. Upload directory structure is ready")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
