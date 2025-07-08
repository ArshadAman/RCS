# Review Collection System - Django Backend

A comprehensive Review Collection System built with Django REST Framework that allows businesses to collect, manage, and display customer reviews.

## Features

### User Management
- Custom user model with profile information
- JWT-based authentication
- User registration and login
- Profile management
- Password change functionality

### Business Management
- Business registration and management
- Category-based organization
- Business profile with contact information
- Owner-based access control

### Review System
- Customer review submission
- Rating system (1-5 stars)
- Review approval workflow
- Business response to reviews
- Review images support
- Like/helpful voting system
- Anonymous review option

### Admin Features
- Django admin interface
- Review moderation
- Business management
- User management
- Statistics and analytics

## Technology Stack

- **Backend Framework**: Django 5.2.4
- **API Framework**: Django REST Framework 3.15.2
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: SQLite (development) / PostgreSQL (production)
- **File Storage**: Local file system (development)
- **CORS**: django-cors-headers
- **Environment Variables**: python-decouple

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone or navigate to the project directory**
   ```bash
   cd /Users/arshadaman/Desktop/RCS
   ```

2. **Virtual environment is already set up and activated**
   The project uses a virtual environment located at `.venv/`

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   The project uses a `.env` file for configuration. Default values are already set for development.

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Sample Data**
   ```bash
   python manage.py create_sample_data
   ```

7. **Run the Development Server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET/PUT /api/auth/profile/` - User profile
- `POST /api/auth/password/change/` - Change password
- `POST /api/auth/token/refresh/` - Refresh JWT token

### Categories
- `GET /api/categories/` - List all categories

### Businesses
- `GET /api/businesses/` - List businesses
- `POST /api/businesses/` - Create business (authenticated)
- `GET /api/businesses/{id}/` - Get business details
- `PUT/PATCH /api/businesses/{id}/` - Update business (owner only)
- `DELETE /api/businesses/{id}/` - Delete business (owner only)
- `GET /api/businesses/{id}/reviews/` - Get business reviews
- `GET /api/businesses/{id}/stats/` - Get business statistics

### Reviews
- `GET /api/reviews/` - List reviews
- `POST /api/reviews/` - Create review (authenticated)
- `GET /api/reviews/{id}/` - Get review details
- `PUT/PATCH /api/reviews/{id}/` - Update review (author only)
- `DELETE /api/reviews/{id}/` - Delete review (author only)
- `PUT /api/reviews/{id}/response/` - Business response (business owner)
- `POST /api/reviews/{id}/like/` - Toggle review like
- `POST /api/reviews/{id}/approve/` - Approve review (admin/owner)

## Sample Data

The system comes with pre-created sample data:

### Users
- **Admin**: admin@example.com / admin123
- **Regular Users**: 
  - john@example.com / user123
  - jane@example.com / user123
- **Business Owner**: owner@example.com / user123

### Categories
- Restaurant, Hotel, Retail, Healthcare, Education, Technology

### Sample Businesses
- The Great Restaurant
- Grand Hotel  
- Tech Solutions Inc

### Sample Reviews
- Multiple reviews for each business with different ratings

## Admin Interface

Access the Django admin interface at `http://localhost:8000/admin/`

Login with: admin@example.com / admin123

Features:
- User management
- Business management
- Review moderation
- Category management
- Bulk actions for reviews

## Project Structure

```
review_collection_system/
├── authentication/          # User authentication app
│   ├── models.py           # Custom User model
│   ├── serializers.py      # API serializers
│   ├── views.py            # API views
│   ├── urls.py             # URL patterns
│   └── admin.py            # Admin configuration
├── reviews/                # Review management app
│   ├── models.py           # Business, Review, Category models
│   ├── serializers.py      # API serializers
│   ├── views.py            # API views
│   ├── urls.py             # URL patterns
│   ├── admin.py            # Admin configuration
│   └── management/         # Management commands
├── review_collection_system/ # Project settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration
├── media/                  # User uploaded files
├── static/                 # Static files
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── manage.py               # Django management script
```

## Configuration

### Environment Variables (.env)
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### CORS Configuration
The system is configured to allow requests from:
- http://localhost:3000 (React default)
- http://localhost:5173 (Vite default)

## Security Features

- JWT-based authentication
- Password validation
- CORS protection
- User permission checks
- Input validation and sanitization
- SQL injection protection (Django ORM)

## Development

### Adding New Features
1. Create new models in appropriate app
2. Create and run migrations
3. Add serializers for API endpoints
4. Create views with proper permissions
5. Add URL patterns
6. Update admin interface if needed

### Testing
The system includes comprehensive model relationships and validation. Test using:
- Django admin interface
- API endpoints with tools like Postman
- Python shell for model testing

## Production Deployment

For production deployment:
1. Set `DEBUG=False` in environment
2. Configure proper database (PostgreSQL recommended)
3. Set up proper static file serving
4. Configure email backend for notifications
5. Set up proper media file storage
6. Use environment variables for sensitive data

## API Usage Examples

### Register a new user
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "first_name": "New",
    "last_name": "User"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "user123"
  }'
```

### Create a review
```bash
curl -X POST http://localhost:8000/api/reviews/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "business_id": 1,
    "rating": 5,
    "title": "Excellent service!",
    "content": "Great experience with professional staff.",
    "reviewer_name": "Happy Customer"
  }'
```

## Support

For questions or issues:
1. Check the Django admin interface for data management
2. Review API endpoint documentation
3. Check server logs for error details
4. Verify authentication tokens for protected endpoints

## License

This project is developed for educational and demonstration purposes.
