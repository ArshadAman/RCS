# Review Collection System - Backend

A comprehensive multi-tenant SaaS feedback collection system built with Django REST Framework. This system allows businesses to collect, manage, and display customer reviews with automated email requests, customizable review criteria, and public widgets.

## Features

### 🏢 Multi-Tenant Architecture
- **Company Management**: Each company has its own isolated data
- **Business Management**: Companies can manage multiple businesses
- **User Permissions**: Role-based access control with company ownership

### 📝 Review Management
- **Customizable Criteria**: Companies can define their own review criteria
- **Automated Emails**: Personalized review request emails with templates
- **Public Submission**: Token-based public review submission
- **Approval Workflow**: Review moderation with approve/reject functionality
- **Business Responses**: Companies can respond to reviews

### 📧 Email System
- **Automated Requests**: Send review requests based on orders
- **Custom Templates**: Personalized email templates per company
- **Reminder System**: Follow-up emails for pending reviews
- **Token-based Links**: Secure review submission links

### 🎨 Public Widget
- **Embeddable Widget**: Display reviews on company websites
- **Customizable Display**: Configure appearance and review count
- **Real-time Updates**: Dynamic content updates
- **Responsive Design**: Mobile-friendly widget

### 📱 QR Code Feedback
- **Branch-specific QR Codes**: Generate QR codes for physical locations
- **Quick Feedback**: Instant feedback collection
- **Analytics**: Track feedback by location

### 📊 Analytics & Reporting
- **Dashboard Statistics**: Company-wide review analytics
- **Export Functionality**: CSV export of reviews
- **Rating Distribution**: Visual representation of ratings
- **Recommendation Tracking**: Track recommendation percentages

## Technology Stack

- **Framework**: Django 5.2.4
- **API**: Django REST Framework 3.15.2
- **Authentication**: JWT with django-rest-framework-simplejwt
- **Database**: SQLite (development), PostgreSQL (production)
- **Email**: Django Email Backend with SMTP support
- **File Storage**: Django File Storage (configurable)
- **Caching**: Redis for session and rate limiting
- **Task Queue**: Celery for background tasks

## Project Structure

```
review_collection_system/
├── authentication/          # User authentication app
│   ├── models.py           # Custom user model
│   ├── serializers.py      # User serializers
│   ├── views.py            # Auth views
│   └── urls.py             # Auth URLs
├── reviews/                # Main review system app
│   ├── models.py           # Core models (Company, Business, Review, etc.)
│   ├── serializers.py      # API serializers
│   ├── views.py            # API views and ViewSets
│   ├── urls.py             # API URLs
│   ├── permissions.py      # Custom permissions
│   ├── filters.py          # Django filters
│   └── management/         # Management commands
│       └── commands/
│           └── populate_sample_data.py
├── review_collection_system/
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## API Endpoints

### Authentication
- `POST /auth/register/` - User registration
- `POST /auth/login/` - User login
- `POST /auth/logout/` - User logout
- `POST /auth/refresh/` - Token refresh

### Companies
- `GET /api/companies/` - List user's companies
- `POST /api/companies/` - Create new company
- `GET /api/companies/{id}/` - Get company details
- `PUT /api/companies/{id}/` - Update company
- `DELETE /api/companies/{id}/` - Delete company
- `GET /api/companies/{id}/dashboard/` - Company dashboard stats

### Businesses
- `GET /api/businesses/` - List businesses
- `POST /api/businesses/` - Create new business
- `GET /api/businesses/{id}/` - Get business details
- `PUT /api/businesses/{id}/` - Update business
- `DELETE /api/businesses/{id}/` - Delete business
- `GET /api/businesses/{id}/reviews/` - Get business reviews
- `GET /api/businesses/{id}/public-reviews/` - Get public reviews

### Orders
- `GET /api/orders/` - List orders
- `POST /api/orders/` - Create new order
- `GET /api/orders/{id}/` - Get order details
- `PUT /api/orders/{id}/` - Update order
- `DELETE /api/orders/{id}/` - Delete order
- `POST /api/orders/{id}/send-review-request/` - Send review request email

### Reviews
- `GET /api/reviews/` - List reviews
- `POST /api/reviews/` - Create new review
- `GET /api/reviews/{id}/` - Get review details
- `PUT /api/reviews/{id}/` - Update review
- `DELETE /api/reviews/{id}/` - Delete review
- `POST /api/reviews/{id}/approve/` - Approve review
- `POST /api/reviews/{id}/reject/` - Reject review
- `POST /api/reviews/{id}/respond/` - Add business response

### Review Criteria
- `GET /api/review-criteria/` - List review criteria
- `POST /api/review-criteria/` - Create new criteria
- `GET /api/review-criteria/{id}/` - Get criteria details
- `PUT /api/review-criteria/{id}/` - Update criteria
- `DELETE /api/review-criteria/{id}/` - Delete criteria

### Email Templates
- `GET /api/email-templates/` - List email templates
- `POST /api/email-templates/` - Create new template
- `GET /api/email-templates/{id}/` - Get template details
- `PUT /api/email-templates/{id}/` - Update template
- `DELETE /api/email-templates/{id}/` - Delete template

### Widget Settings
- `GET /api/widget-settings/` - List widget settings
- `POST /api/widget-settings/` - Create new settings
- `GET /api/widget-settings/{id}/` - Get settings details
- `PUT /api/widget-settings/{id}/` - Update settings
- `DELETE /api/widget-settings/{id}/` - Delete settings

### Public APIs (No Authentication Required)
- `GET /api/public/review-form/{token}/` - Get review form data
- `POST /api/public/submit-review/{token}/` - Submit public review
- `GET /api/public/widget/{company_id}/` - Get widget data
- `GET /api/public/qr-code/{company_id}/{branch_id}/` - Generate QR code
- `POST /api/public/qr-feedback/{company_id}/{branch_id}/` - Submit QR feedback

### Additional Endpoints
- `GET /api/export/{company_id}/` - Export reviews
- `POST /api/bulk-approve/` - Bulk approve reviews
- `POST /api/bulk-reject/` - Bulk reject reviews

## Installation & Setup

### Prerequisites
- Python 3.9+
- pip
- virtualenv (recommended)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RCS
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   FRONTEND_URL=http://localhost:3000
   DEFAULT_FROM_EMAIL=noreply@yourcompany.com
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Load sample data (optional)**
   ```bash
   python manage.py populate_sample_data
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/api/`

## Configuration

### Email Settings
Configure email settings in your `.env` file:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Configuration
For production, configure PostgreSQL:
```env
DATABASE_URL=postgres://username:password@localhost:5432/database_name
```

### File Storage
Configure file storage for production:
```env
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

## Business Logic

### Review Validation
- Comments are required for ratings of 3 or below
- Default rating is set to 3 if not provided
- Overall rating is calculated from criteria ratings

### Multi-Tenancy
- All data is isolated by company
- Users can only access their own companies' data
- API endpoints enforce company ownership

### Email Workflow
1. Order is created in the system
2. Review request email is sent to customer
3. Customer clicks link to submit review
4. Review is submitted and awaits approval
5. Business owner approves/rejects review
6. Approved reviews appear in public widget

### Security
- JWT-based authentication
- Rate limiting on API endpoints
- CSRF protection
- XSS protection
- SQL injection protection

## Testing

Run tests with:
```bash
python manage.py test
```

Run with coverage:
```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Deployment

### Production Checklist
1. Set `DEBUG=False`
2. Configure PostgreSQL database
3. Set up Redis for caching
4. Configure email backend
5. Set up static file serving
6. Configure HTTPS
7. Set up monitoring and logging

### Environment Variables
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://username:password@localhost:5432/database_name
REDIS_URL=redis://localhost:6379/0
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yourdomain.com
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password
```

## API Documentation

The API documentation is available at `/api/schema/swagger-ui/` when running the development server.

## Management Commands

### Create Sample Data
```bash
python manage.py populate_sample_data --users 10 --companies 5 --businesses 15 --orders 100 --reviews 200
```

### Custom Management Commands
- `populate_sample_data`: Create sample data for testing
- `send_review_requests`: Send pending review requests (can be scheduled)
- `cleanup_expired_tokens`: Remove expired review tokens

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.
