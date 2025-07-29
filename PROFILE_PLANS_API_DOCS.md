# API Documentation - Profile & Plans Endpoints

This document provides comprehensive information about the Profile and Plans API endpoints in the Review Collection System (RCS).

## 🔗 Quick Links

- **Swagger UI**: http://localhost:8000/api/schema/swagger/
- **Redoc UI**: http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## 📋 Profile Management APIs

### 1. User Profile Management
**Endpoint**: `GET|PUT|PATCH /api/auth/profile/`  
**Authentication**: Required (Bearer Token)

#### Features
- **GET**: Retrieve comprehensive profile information
- **PUT**: Complete profile update
- **PATCH**: Partial profile update
- Update both user personal info and business details

#### Profile Data Includes
- ✅ Personal information (name, email, phone, avatar, etc.)
- ✅ Business details (company name, website, address, ratings)
- ✅ Current subscription plan with features and limitations
- ✅ Badge information and achievements
- ✅ Business statistics (average rating, total reviews, recommendation %)

#### Example Response
```json
{
  "id": 2,
  "username": "admin@test.com",
  "email": "admin@test.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "business_name": "Test Company",
  "business_website": "https://testcompany.com",
  "business_email": "contact@testcompany.com",
  "business_average_rating": 4.5,
  "business_total_reviews": 15,
  "plan_type": "standard",
  "plan_display_name": "Standard",
  "review_limit": 200,
  "plan_features": {
    "name": "Standard Plan",
    "price": 29,
    "currency": "USD",
    "features": [
      "Up to 200 reviews per month",
      "Custom email templates",
      "Advanced analytics"
    ]
  }
}
```

#### Update Examples
```json
// Update user information
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}

// Update business information (prefix with business_)
{
  "business_name": "Updated Company Name",
  "business_website": "https://newwebsite.com",
  "business_email": "contact@newcompany.com"
}

// Update both
{
  "first_name": "John",
  "business_name": "My Company",
  "business_website": "https://mycompany.com"
}
```

### 2. Simple Profile View
**Endpoint**: `GET /api/auth/profile/simple/`  
**Authentication**: Required

Read-only endpoint that returns the same comprehensive profile data as the main profile endpoint.

## 📊 Subscription Plans APIs

### 1. Get All Plans
**Endpoint**: `GET /api/auth/plans/`  
**Authentication**: Not required (public endpoint)

#### Features
- Returns all available subscription plans
- Detailed pricing and feature information
- Plan limitations and restrictions
- No authentication required

#### Available Plans
| Plan | Price | Reviews/Month | Key Features |
|------|-------|---------------|--------------|
| **Basic** | Free | 50 | Basic templates, Standard widget, Community support |
| **Standard** | $29/month | 200 | Custom templates, Advanced analytics, Email support |
| **Premium** | $99/month | Unlimited | White-label, Full API, Priority support |

#### Example Response
```json
{
  "basic": {
    "name": "Basic Plan",
    "price": 0,
    "currency": "USD",
    "billing_period": "month",
    "review_limit": 50,
    "features": [
      "Up to 50 reviews per month",
      "Basic email templates",
      "Standard widget",
      "Email notifications",
      "Basic analytics",
      "Community support"
    ],
    "limitations": [
      "Limited customization",
      "Basic reporting only",
      "No API access"
    ]
  }
  // ... standard and premium plans
}
```

### 2. Plan Comparison
**Endpoint**: `GET /api/auth/plans/?comparison=true`  
**Authentication**: Not required

#### Features
- Side-by-side feature comparison matrix
- Easy to understand plan differences
- Includes both feature matrix and full plan details

#### Example Response
```json
{
  "features": [
    {
      "name": "Monthly Reviews",
      "basic": "50",
      "standard": "200",
      "premium": "Unlimited"
    },
    {
      "name": "Email Templates",
      "basic": "Basic",
      "standard": "Custom",
      "premium": "Full Customization"
    },
    {
      "name": "API Access",
      "basic": "❌",
      "standard": "Limited",
      "premium": "Full"
    }
  ],
  "plans": {
    // Full plan details as above
  }
}
```

## 🔐 Authentication

All profile endpoints require JWT Bearer token authentication:

```bash
# Get token via login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Use token in subsequent requests
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📝 Usage Examples

### JavaScript/Frontend
```javascript
// Get user profile
const getProfile = async () => {
  const response = await fetch('/api/auth/profile/', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.json();
};

// Update profile
const updateProfile = async (updates) => {
  const response = await fetch('/api/auth/profile/', {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  });
  return response.json();
};

// Get plans
const getPlans = async () => {
  const response = await fetch('/api/auth/plans/');
  return response.json();
};

// Get plan comparison
const getPlanComparison = async () => {
  const response = await fetch('/api/auth/plans/?comparison=true');
  return response.json();
};
```

### Python
```python
import requests

# Login and get token
login_response = requests.post('http://localhost:8000/api/auth/login/', json={
    'email': 'user@example.com',
    'password': 'password123'
})
token = login_response.json()['tokens']['access']

# Get profile
headers = {'Authorization': f'Bearer {token}'}
profile = requests.get('http://localhost:8000/api/auth/profile/', headers=headers).json()

# Update business info
update_data = {
    'business_name': 'New Company Name',
    'business_website': 'https://newsite.com'
}
updated_profile = requests.patch('http://localhost:8000/api/auth/profile/', 
                                json=update_data, headers=headers).json()

# Get plans
plans = requests.get('http://localhost:8000/api/auth/plans/').json()
```

### cURL Examples
```bash
# Get profile
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update profile
curl -X PATCH http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","business_name":"My Company"}'

# Get plans
curl -X GET http://localhost:8000/api/auth/plans/

# Get plan comparison
curl -X GET "http://localhost:8000/api/auth/plans/?comparison=true"
```

## ⚠️ Error Handling

### Common HTTP Status Codes
- **200**: Success
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (missing/invalid token)
- **403**: Forbidden
- **404**: Not Found
- **500**: Internal Server Error

### Error Response Format
```json
{
  "detail": "Authentication credentials were not provided."
}

// Validation errors
{
  "business_email": ["Enter a valid email address."],
  "date_of_birth": ["Date has wrong format. Use YYYY-MM-DD."]
}
```

## 🚀 Best Practices

1. **Use PATCH for updates**: Prefer PATCH over PUT for partial updates
2. **Cache plan data**: Plans don't change frequently, cache the response
3. **Handle token expiration**: Implement token refresh logic
4. **Validate input**: Check required fields before making requests
5. **Secure token storage**: Use secure storage for access tokens

## 📊 Response Fields Reference

### User Profile Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | User's unique identifier |
| `username` | String | User's username |
| `email` | String | User's email address |
| `first_name` | String | User's first name |
| `last_name` | String | User's last name |
| `full_name` | String | Computed full name |
| `avatar` | String/null | Avatar image URL |
| `phone_number` | String | Phone number |
| `date_of_birth` | Date/null | Date of birth |
| `is_verified` | Boolean | Email verification status |

### Business Fields
| Field | Type | Description |
|-------|------|-------------|
| `business_name` | String | Company/business name |
| `business_website` | String | Business website URL |
| `business_email` | String | Business contact email |
| `business_phone` | String | Business phone number |
| `business_address` | String | Business address |
| `business_category` | String | Business category |
| `business_logo` | String/null | Business logo URL |
| `business_description` | String | Business description |
| `business_average_rating` | Float | Average rating from reviews |
| `business_total_reviews` | Integer | Total published reviews |
| `business_recommendation_percentage` | Float | % of positive recommendations |

### Plan Fields
| Field | Type | Description |
|-------|------|-------------|
| `plan_type` | String | Plan type (basic/standard/premium) |
| `plan_display_name` | String | Human-readable plan name |
| `review_limit` | Integer | Monthly review limit |
| `plan_created_at` | DateTime | Plan creation date |
| `plan_features` | Object | Detailed plan information |

### Plan Features Object
| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Plan name |
| `price` | Number | Monthly price |
| `currency` | String | Currency code |
| `billing_period` | String | Billing frequency |
| `review_limit` | Integer | Monthly review limit (-1 = unlimited) |
| `features` | Array | List of plan features |
| `limitations` | Array | List of plan limitations |

## 🔍 Interactive Documentation

For the most up-to-date and interactive documentation:

- **Swagger UI**: http://localhost:8000/api/schema/swagger/
  - Interactive API explorer
  - Try out requests directly
  - View request/response examples

- **Redoc**: http://localhost:8000/api/schema/redoc/
  - Clean, readable documentation
  - Better for documentation reading
  - Comprehensive endpoint details

Both interfaces are automatically updated when the API changes and provide the most accurate, current information about all endpoints.
