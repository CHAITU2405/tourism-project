#!/usr/bin/env python3
"""
Migration script to add profile_completed field to User model
and update existing vehicle rental owners
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, VehicleRental

def migrate_vehicle_rental_profile():
    """Add profile_completed field and update existing users"""
    with app.app_context():
        try:
            print("🔄 Starting vehicle rental profile migration...")
            
            # Check if profile_completed column exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('user')]
            
            if 'profile_completed' not in columns:
                print("📝 Adding profile_completed column to User table...")
                db.engine.execute('ALTER TABLE user ADD COLUMN profile_completed BOOLEAN DEFAULT FALSE')
                print("✅ profile_completed column added successfully")
            else:
                print("✅ profile_completed column already exists")
            
            # Update existing vehicle rental owners who have rental companies
            vehicle_rental_users = User.query.filter_by(role='vehicle_rental').all()
            print(f"📊 Found {len(vehicle_rental_users)} vehicle rental users")
            
            updated_count = 0
            for user in vehicle_rental_users:
                # Check if user has any rental companies
                has_rentals = VehicleRental.query.filter_by(owner_id=user.id).count() > 0
                
                if has_rentals and not user.profile_completed:
                    user.profile_completed = True
                    updated_count += 1
                    print(f"✅ Updated profile for user: {user.username}")
            
            if updated_count > 0:
                db.session.commit()
                print(f"🎉 Updated {updated_count} existing vehicle rental owners")
            else:
                print("ℹ️  No existing users needed profile updates")
            
            # Create demo vehicle rental owner if none exist
            if len(vehicle_rental_users) == 0:
                from werkzeug.security import generate_password_hash
                
                demo_owner = User(
                    username='demo_vehicle_owner',
                    email='demo@vehiclerental.com',
                    password_hash=generate_password_hash('demo123'),
                    first_name='Demo',
                    last_name='Vehicle Owner',
                    phone='+91 9876543210',
                    role='vehicle_rental',
                    profile_completed=False  # Will need to complete profile
                )
                
                db.session.add(demo_owner)
                db.session.commit()
                print("🎯 Demo vehicle rental owner created:")
                print("   Username: demo_vehicle_owner")
                print("   Password: demo123")
                print("   Email: demo@vehiclerental.com")
                print("   Role: vehicle_rental")
                print("   Profile Status: Needs completion")
            
            print("🎉 Vehicle rental profile migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    success = migrate_vehicle_rental_profile()
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Vehicle rental owners will now be prompted to complete their profile on first login")
        print("2. Profile completion creates their rental company")
        print("3. They can then add vehicles to their fleet")
        print("4. All vehicles are clearly marked as rental vehicles (not cabs)")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
