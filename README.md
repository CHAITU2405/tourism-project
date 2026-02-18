# TourismHub - Hotel Booking System

A comprehensive Flask-based tourism website with a hotel booking system featuring multi-role authentication, hotel management, and booking functionality.

## Features

### 🏨 **Multi-Role System**
- **Users**: Browse and book hotels
- **Hotel Owners**: Register and manage their properties
- **Admins**: Manage bookings and hotels
- **Super Admin**: Approve hotels and manage admins

### 🔐 **Authentication & Authorization**
- Secure user registration and login
- Role-based access control
- Password hashing with Werkzeug
- Session management with Flask-Login

### 🏨 **Hotel Management**
- Hotel registration with detailed information
- Admin approval system for hotels
- Hotel search and filtering
- Amenities and pricing management

### 📅 **Booking System**
- **Real-time availability checking** - Room availability based on selected dates
- **Dynamic room selection** - Available rooms update when dates change
- **Overlapping booking detection** - Prevents double bookings
- **Booking confirmation and management**
- **Booking cancellation**
- **Price calculation with taxes**

### 📊 **Dashboard Analytics**
- User booking history
- Hotel performance metrics
- Revenue tracking
- Booking status management

### 🎨 **Modern UI/UX**
- Responsive Bootstrap 5 design
- Interactive JavaScript features
- Real-time form validation
- Mobile-friendly interface

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the project**
   ```bash
   cd tourism
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the database**
   ```bash
   python init_db.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and go to: `http://localhost:5000`

## Default Accounts

### Super Admin
- **Username**: `superadmin`
- **Password**: `admin123`
- **Access**: Full system control, hotel approval, admin management

## Usage Guide

### For Regular Users
1. **Register** as a "Traveler" account type
2. **Browse hotels** using search and filters
3. **Book hotels** by selecting dates and rooms
4. **Manage bookings** in your dashboard

### For Hotel Owners
1. **Register** as a "Hotel Owner" account type
2. **Register your hotel** with complete details
3. **Wait for approval** from super admin
4. **Manage bookings** and view analytics

### For Super Admin
1. **Login** with super admin credentials
2. **Review pending hotels** and approve/reject them
3. **Add new admins** from existing users
4. **Monitor system** performance and data

## Database Schema

### Users Table
- User authentication and profile information
- Role-based access (user, hotel, admin, superadmin)

### Hotels Table
- Hotel information and amenities
- Approval status and availability
- Owner relationship

### Bookings Table
- Booking details and status
- User and hotel relationships
- Pricing and dates

### Admins Table
- Admin permissions and management
- Created by super admin tracking

## API Endpoints

### Authentication
- `GET /register` - User registration form
- `POST /register` - Process registration
- `GET /login` - Login form
- `POST /login` - Process login
- `GET /logout` - User logout

### Hotels
- `GET /hotels` - Browse all approved hotels
- `GET /hotel/<id>` - Hotel details
- `GET /hotel/register` - Hotel registration form
- `POST /hotel/register` - Process hotel registration

### Bookings
- `GET /book/<hotel_id>` - Booking form
- `POST /book/<hotel_id>` - Process booking
- `GET /cancel_booking/<booking_id>` - Cancel booking

### API Endpoints
- `GET /api/room-availability/<hotel_id>` - Check room availability for specific dates

### VAPI webhook (voice / watch bookings)
Bookings can be made **manually** on the website or **via voice** through a watch (ESP32 → VAPI → this app).  
User details (name, email, phone) are taken from the **database** using `username`; VAPI sends only `username` and `booking_type` plus booking details.

- **Endpoint**: `POST /api/vapi/webhook`
- **Auth** (optional): Set env `VAPI_WEBHOOK_SECRET`; then send header `X-VAPI-Secret` or `Authorization: Bearer <secret>`.
- **Body**: JSON with `action`, `username` (for create actions), and action-specific fields. Response: `{ "success", "message" (for TTS), "data" }`.

| action | purpose | body fields (from VAPI) |
|--------|---------|-------------------------|
| `list_hotels` | List approved hotels | optional: `city` |
| `list_vehicles` | List available vehicles | optional: `city`, `vehicle_type` |
| `create_hotel_booking` | Create hotel booking | **`username`**, **`booking_type`** (`"hotel"`), `hotel_id`, `check_in`, `check_out` (YYYY-MM-DD), `rooms`, `guests` — user details from DB |
| `create_vehicle_booking` | Create vehicle booking | **`username`**, **`booking_type`** (`"vehicle"`), `vehicle_id`, `rental_company_id`, `pickup_date`, `return_date` (YYYY-MM-DD) — user details from DB |
| `get_booking_status` | Get status by reference | `booking_reference`, optional: `type` (`hotel` or `vehicle`) |

### Admin Functions
- `GET /superadmin/dashboard` - Super admin dashboard
- `GET /approve_hotel/<hotel_id>` - Approve hotel
- `GET /reject_hotel/<hotel_id>` - Reject hotel
- `POST /add_admin` - Add new admin

## File Structure

```
tourism/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── init_db.py             # Database initialization script
├── test_app.py            # Test script with sample data
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── QUICK_START.md        # Quick start guide
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── register.html     # User registration
│   ├── login.html        # User login
│   ├── hotels.html       # Hotel listing
│   ├── hotel_detail.html # Hotel details
│   ├── book_hotel.html   # Booking form
│   ├── user_dashboard.html      # User dashboard
│   ├── hotel_register.html      # Hotel registration
│   ├── hotel_dashboard.html     # Hotel owner dashboard
│   ├── admin_dashboard.html     # Admin dashboard
│   └── superadmin_dashboard.html # Super admin dashboard
└── static/               # Static files
    ├── css/
    │   └── style.css     # Custom styles
    └── js/
        └── main.js       # JavaScript functionality
```

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Icons**: Font Awesome
- **Security**: Werkzeug password hashing
- **Templates**: Jinja2 with custom filters

## Features in Detail

### Hotel Registration
- Complete hotel information form
- Amenities selection
- Image upload support (placeholder)
- Automatic approval workflow

### Booking System
- Date validation and availability checking
- Real-time price calculation
- Room and guest selection
- Special requests handling

### Admin Dashboard
- Hotel approval interface
- User management
- Booking analytics
- Revenue tracking

### Responsive Design
- Mobile-first approach
- Bootstrap 5 components
- Custom CSS animations
- Interactive JavaScript features

## Security Features

- Password hashing with Werkzeug
- CSRF protection with Flask-WTF
- Role-based access control
- Input validation and sanitization
- Secure session management

## Custom Jinja2 Filters and Functions

The application includes custom Jinja2 filters and functions for enhanced template functionality:

### **Custom Filters:**
- **`from_json`** - Converts JSON strings to Python objects (used for amenities)
- **`to_json`** - Converts Python objects to JSON strings
- **`format_currency`** - Formats numbers as currency with proper decimal places

### **Global Functions:**
- **`min`** - Returns the minimum of two values
- **`max`** - Returns the maximum of two values
- **`len`** - Returns the length of a sequence
- **`range`** - Generates a sequence of numbers

## Future Enhancements

- Payment gateway integration
- Email notifications
- Advanced search filters
- Hotel image uploads
- Review and rating system
- Mobile app development
- API for third-party integrations

## Troubleshooting

### Common Issues

1. **Database not found**
   - The SQLite database is created automatically on first run
   - Ensure the application has write permissions

2. **Port already in use**
   - Change the port in `app.py` or kill the process using port 5000

3. **Dependencies not installed**
   - Make sure virtual environment is activated
   - Run `pip install -r requirements.txt`

4. **Permission errors**
   - Ensure proper file permissions
   - Run with appropriate user privileges

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Ensure all dependencies are installed
4. Verify Python version compatibility

## License

This project is created for educational and demonstration purposes. Feel free to use and modify as needed.

---

**TourismHub** - Your gateway to amazing travel experiences! 🌟
