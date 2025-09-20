from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Storing plaintext per request (field name kept for compatibility)
    password_hash = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='user')  # user, hotel, vehicle_rental, admin, superadmin
    profile_completed = db.Column(db.Boolean, default=False)  # Track if profile is completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    hotels = db.relationship('Hotel', backref='owner', lazy=True)
    admin_profile = db.relationship('Admin', foreign_keys='Admin.user_id', backref='user')
    vehicle_bookings = db.relationship('VehicleBooking', backref='user', lazy=True)
    vehicle_rentals = db.relationship('VehicleRental', backref='owner', lazy=True)

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), default='Standard')  # Budget, Standard, Deluxe, Luxury, Resort, Boutique
    rating = db.Column(db.Float, default=0.0)  # User-generated rating (0-5)
    total_reviews = db.Column(db.Integer, default=0)  # Number of user reviews
    amenities = db.Column(db.Text, nullable=True)  # JSON string
    images = db.Column(db.Text, nullable=True)  # JSON string of image URLs
    price_per_night = db.Column(db.Float, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    available_rooms = db.Column(db.Integer, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='hotel', lazy=True)
    room_types = db.relationship('RoomType', backref='hotel', lazy=True, cascade='all, delete-orphan')

class RoomType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Deluxe Room", "Suite"
    description = db.Column(db.Text, nullable=True)
    max_occupancy = db.Column(db.Integer, nullable=False, default=2)
    price_per_night = db.Column(db.Float, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.Text, nullable=True)  # JSON string of room amenities
    images = db.Column(db.Text, nullable=True)  # JSON string of room images
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='room_type', lazy=True)
    availability = db.relationship('RoomAvailability', backref='room_type', lazy=True, cascade='all, delete-orphan')

class RoomAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    available_rooms = db.Column(db.Integer, nullable=False)
    booked_rooms = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate entries for same room type and date
    __table_args__ = (db.UniqueConstraint('room_type_id', 'date', name='unique_room_date'),)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.id'), nullable=True)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    rooms = db.Column(db.Integer, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, refunded
    special_requests = db.Column(db.Text, nullable=True)
    booking_reference = db.Column(db.String(20), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='reviews')
    hotel = db.relationship('Hotel', backref='reviews')
    booking = db.relationship('Booking', backref='review')

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='wishlist_items')
    hotel = db.relationship('Hotel', backref='wishlist_items')
    
    # Ensure unique user-hotel combination
    __table_args__ = (db.UniqueConstraint('user_id', 'hotel_id', name='unique_user_hotel_wishlist'),)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permissions = db.Column(db.Text, nullable=True)  # JSON string
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])

class VehicleRental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200), nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True)  # Company profile picture
    rating = db.Column(db.Float, default=0.0)  # User-generated rating (0-5)
    total_reviews = db.Column(db.Integer, default=0)  # Number of user reviews
    amenities = db.Column(db.Text, nullable=True)  # JSON string
    images = db.Column(db.Text, nullable=True)  # JSON string of image URLs
    is_approved = db.Column(db.Boolean, default=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='rental_company', lazy=True)
    bookings = db.relationship('VehicleBooking', backref='rental_company', lazy=True)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rental_company_id = db.Column(db.Integer, db.ForeignKey('vehicle_rental.id'), nullable=False)
    make = db.Column(db.String(50), nullable=False)  # e.g., "Toyota", "Honda"
    model = db.Column(db.String(50), nullable=False)  # e.g., "Camry", "Civic"
    year = db.Column(db.Integer, nullable=False)
    vehicle_type = db.Column(db.String(30), nullable=False)  # sedan, suv, hatchback, luxury, etc.
    transmission = db.Column(db.String(20), nullable=False)  # manual, automatic
    fuel_type = db.Column(db.String(20), nullable=False)  # petrol, diesel, electric, hybrid
    seating_capacity = db.Column(db.Integer, nullable=False)
    luggage_capacity = db.Column(db.String(50), nullable=True)  # e.g., "2 large bags"
    mileage = db.Column(db.String(20), nullable=True)  # e.g., "15 km/l"
    features = db.Column(db.Text, nullable=True)  # JSON string
    images = db.Column(db.Text, nullable=True)  # JSON string of image URLs
    price_per_day = db.Column(db.Float, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=True)
    total_vehicles = db.Column(db.Integer, nullable=False)
    available_vehicles = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('VehicleBooking', backref='vehicle', lazy=True)

class VehicleBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rental_company_id = db.Column(db.Integer, db.ForeignKey('vehicle_rental.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    pickup_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    pickup_time = db.Column(db.Time, nullable=False)
    return_time = db.Column(db.Time, nullable=False)
    pickup_location = db.Column(db.String(200), nullable=False)
    return_location = db.Column(db.String(200), nullable=False)
    drivers_license = db.Column(db.String(50), nullable=False)
    drivers_license_expiry = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, refunded
    special_requests = db.Column(db.Text, nullable=True)
    booking_reference = db.Column(db.String(20), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VehicleReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rental_company_id = db.Column(db.Integer, db.ForeignKey('vehicle_rental.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('vehicle_booking.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='vehicle_reviews')
    rental_company = db.relationship('VehicleRental', backref='reviews')
    vehicle = db.relationship('Vehicle', backref='reviews')
    booking = db.relationship('VehicleBooking', backref='review')

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    complaint_type = db.Column(db.String(50), nullable=False)  # transportation, accommodation, safety, etc.
    location = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    suggestions = db.Column(db.Text, nullable=True)
    public_visibility = db.Column(db.Boolean, default=True)  # Whether visible to other tourists
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved, closed
    admin_notes = db.Column(db.Text, nullable=True)  # Notes from superadmin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # No user_id - completely anonymous

