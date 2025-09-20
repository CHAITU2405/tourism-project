#!/usr/bin/env python3
"""
Database initialization script for TourismHub
"""

from app import app
from models import db, User
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize database with tables and superadmin user"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Create superadmin if not exists
        superadmin = User.query.filter_by(username='superadmin').first()
        if not superadmin:
            superadmin = User(
                username='superadmin',
                email='admin@tourism.com',
                password_hash=generate_password_hash('admin123'),
                first_name='Super',
                last_name='Admin',
                role='superadmin'
            )
            db.session.add(superadmin)
            db.session.commit()
            print("✅ Superadmin created: username='superadmin', password='admin123'")
        else:
            print("✅ Superadmin already exists")
        
        print("🎉 Database initialization completed!")

if __name__ == '__main__':
    init_database()
