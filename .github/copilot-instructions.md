<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Review Collection System - Django Backend

This is a comprehensive Review Collection System built with Django REST Framework. The system allows businesses to collect, manage, and display customer reviews with a robust API backend.

## Project Context

- **Framework**: Django 5.2.4 with Django REST Framework
- **Authentication**: JWT-based authentication system
- **Database**: SQLite for development, PostgreSQL-ready for production
- **Architecture**: RESTful API with clear separation of concerns

## Key Components

### Models
- **User**: Custom user model with profile information
- **Business**: Business entities that can receive reviews
- **Review**: Customer reviews with ratings, content, and images
- **Category**: Business categorization system
- **ReviewLike**: User engagement tracking

### Apps Structure
- **authentication**: Handles user management, login, registration
- **reviews**: Manages businesses, reviews, categories, and interactions

## Development Guidelines

When suggesting code improvements or additions:

1. **Follow Django Best Practices**
   - Use Django's built-in features (models, forms, admin)
   - Implement proper model relationships
   - Use Django's permission system

2. **API Design**
   - Follow RESTful conventions
   - Use proper HTTP status codes
   - Implement pagination for list views
   - Add proper filtering and searching

3. **Security**
   - Always validate user permissions
   - Use Django's built-in security features
   - Implement proper authentication checks
   - Validate input data with serializers

4. **Code Organization**
   - Keep views focused and single-purpose
   - Use serializers for data validation
   - Implement proper error handling
   - Add comprehensive docstrings

## Common Patterns

- Use `get_or_create` for data that might already exist
- Implement proper `__str__` methods for models
- Use `select_related` and `prefetch_related` for query optimization
- Add proper `Meta` classes for model configuration
- Use Django's built-in validators where possible

## Testing Considerations

- Test API endpoints with different user permissions
- Verify proper error responses
- Test authentication flows
- Validate business logic in models
- Test admin interface functionality

## Current Features

The system already includes:
- Complete user authentication system
- Business management with owner permissions
- Review system with approval workflow
- Admin interface with bulk actions
- Sample data for testing
- Comprehensive API endpoints
- Image upload support
- Review like/dislike functionality
