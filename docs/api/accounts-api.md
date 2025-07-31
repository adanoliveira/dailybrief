# DailyBrief Accounts API

This document describes the accounts API endpoints for the DailyBrief application.

## Authentication Architecture

The accounts API uses the **enhanced API standard approach**:
- **Enhanced `@api_view` decorator** with comprehensive features
- **Consolidated JWT authentication** via `apps.core.api_utils`
- **Consistent CORS handling** with automatic headers
- **Docker environment support** with automatic URL detection

## Base URLs

- **Docker Environment**: `http://backend:8000/api/`
- **Local Development**: `http://localhost:8000/api/`

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer <jwt-token>
```

The JWT token is obtained during the user sync process and stored in the NextAuth session.

## Endpoints

### 1. User Sync and Status

**Endpoint**: `/api/accounts/sync/`

This unified endpoint handles both user synchronization from NextAuth and retrieving user status.

#### POST Request (User Sync)

**Purpose**: Sync user from NextAuth to Django (called by NextAuth JWT callback)
**Authentication**: Not required (used during authentication flow)

**Request Body**:
```json
{
  "email": "user@example.com",
  "name": "User Name",
  "provider": "google",
  "nextauth_id": "nextauth-id",
  "image": "https://example.com/image.jpg"
}
```

**Response**:
```json
{
  "id": 123,
  "public_id": "uuid-string",
  "email": "user@example.com",
  "name": "User Name",
  "django_token": "jwt-token-for-api-authentication",
  "has_completed_onboarding": true
}
```

**CORS Headers**: Automatically included for cross-origin requests

#### GET Request (User Status)

**Purpose**: Retrieve current user status and preferences
**Authentication**: Required (JWT token in Authorization header)

**Response**:
```json
{
  "id": 123,
  "public_id": "uuid-string",
  "email": "user@example.com",
  "name": "User Name",
  "django_token": "refreshed-jwt-token",
  "has_completed_onboarding": true,
  "topics": [1, 2, 3],
  "topics_details": [
    {"id": 1, "name": "Technology", "slug": "technology"},
    {"id": 2, "name": "Business", "slug": "business"}
  ]
}
```

### 2. User Preferences

**Endpoint**: `/api/accounts/preferences/`

This endpoint handles retrieving and saving user preferences.

#### GET Request

**Purpose**: Retrieve user preferences
**Authentication**: Required (JWT token in Authorization header)

**Response**:
```json
{
  "topics": [1, 2, 3],
  "topics_details": [
    {"id": 1, "name": "Technology", "slug": "technology"},
    {"id": 2, "name": "Business", "slug": "business"}
  ],
  "regions": ["us", "eu"],
  "languages": ["en", "es"],
  "publications": [1, 2],
  "has_completed_onboarding": true,
  "user_id": 123,
  "public_id": "uuid-string",
  "email": "user@example.com",
  "name": "User Name"
}
```

#### POST Request

**Purpose**: Save user preferences and mark onboarding as completed
**Authentication**: Required (JWT token in Authorization header)

**Request Body**:
```json
{
  "topics": [1, 2, 3],
  "regions": ["us", "eu"],
  "languages": ["en", "es"],
  "publications": [1, 2]
}
```

**Response**:
```json
{
  "has_completed_onboarding": true,
  "success": true,
  "message": "Preferences saved successfully"
}
```

## Implementation Details

### Enhanced View Pattern

All API views follow the **consolidated API standard**:

```python
from apps.core.api_utils import (
    api_view, create_response, create_error_response, 
    create_success_response, parse_request_body, create_jwt_token,
    authenticate_request, get_auth_response
)

@api_view(['GET', 'POST'], authenticate=False)  # Custom auth handling
def user_sync_and_status(request):
    """
    Unified endpoint with enhanced features.
    """
    if request.method == 'GET':
        # Manual authentication for GET requests
        authenticated, user, error = authenticate_request(request)
        if not authenticated:
            return get_auth_response(error)
    
        # Business logic...
        return create_response(data)
    
    elif request.method == 'POST':
        # No auth required for sync
        data, error = parse_request_body(request)
        if error:
            return error
        
        # Create JWT token
        token = create_jwt_token(user)
        return create_response({'django_token': token})
```

### Consolidated Authentication

All authentication functions are now in one place:

```python
# Everything imported from one module
from apps.core.api_utils import (
    create_jwt_token,           # Generate JWT tokens
    authenticate_request,       # Validate JWT tokens
    get_auth_response,         # Create auth error responses
    api_view,                  # Enhanced view decorator
    create_response,           # Success responses
    create_error_response,     # Error responses
    create_success_response,   # Success with message
    parse_request_body         # JSON parsing
)
```

**⚠️ Deprecated modules removed:**
- ~~`apps.accounts.auth_helpers`~~ → Consolidated into `apps.core.api_utils`
- ~~`utils.http`~~ → Consolidated into `apps.core.api_utils`
- ~~`apps.accounts.utils`~~ → Removed (was just re-export with deprecation warning)

### CORS Handling

All endpoints automatically include proper CORS headers:

```python
# No manual CORS configuration needed
@api_view(['GET', 'POST'])
def my_endpoint(request):
    # CORS headers added automatically
    return create_response(data)
```

Response includes:
```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With
Access-Control-Max-Age: 86400
```

## Error Handling

All endpoints return **standardized error responses** with appropriate HTTP status codes:

### Authentication Errors (401)
```json
{
  "error": "Authentication failed",
  "detail": "No Authorization header",
  "success": false
}
```

### Bad Request (400)
```json
{
  "error": "Invalid JSON in request body",
  "success": false,
  "error_code": "INVALID_JSON",
  "details": {
    "json_error": "Expecting value: line 1 column 1 (char 0)"
  }
}
```

### Validation Error (400)
```json
{
  "error": "Missing required field: topics",
  "success": false,
  "error_code": "MISSING_REQUIRED_FIELD",
  "details": {
    "field": "topics",
    "required_fields": ["topics"],
    "optional_fields": ["regions", "languages", "publications"]
  }
}
```

### Method Not Allowed (405)
```json
{
  "error": "Method DELETE not allowed",
  "success": false,
  "details": {
    "allowed_methods": ["GET", "POST"],
    "received_method": "DELETE"
  }
}
```

### Internal Server Error (500)
```json
{
  "error": "An internal error occurred. Please try again.",
  "success": false,
  "error_code": "INTERNAL_ERROR"
}
```

## Environment Configuration

### Docker Environment

```yaml
# docker-compose.yml
backend:
  environment:
    - SECRET_KEY=django-secret-key-for-jwt-signing
    - CORS_ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000

frontend:
  environment:
    - NEXT_PUBLIC_API_URL=http://backend:8000/api
    - NEXTAUTH_SECRET=secure-nextauth-secret
```

### Local Development

```bash
# Backend environment
SECRET_KEY=django-secret-key-for-jwt-signing
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Frontend environment
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=secure-nextauth-secret
```

## Testing

### Manual Testing

```bash
# Test user sync (no auth required)
curl -X POST http://localhost:8000/api/accounts/sync/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "provider": "email",
    "nextauth_id": "test123"
  }'

# Test user status (auth required)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/accounts/sync/

# Test preferences (auth required)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/accounts/preferences/
```

### CORS Testing

```bash
# Test CORS preflight (automatic handling)
curl -X OPTIONS http://localhost:8000/api/accounts/sync/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -v
```

## NextAuth Integration

### JWT Callback Sync

The NextAuth JWT callback automatically syncs users with Django:

```javascript
// In NextAuth JWT callback
const backendUser = await syncUserWithBackend({
  ...user,
  provider: account.provider
});

// Store Django JWT token in NextAuth session
token.django_token = backendUser.django_token;
```

### Frontend API Client

The frontend API client automatically includes the JWT token:

```javascript
// Get auth headers
const authHeaders = await getAuthHeaders();

// Make authenticated request
const response = await fetch('/api/accounts/sync/', {
  headers: {
    'Content-Type': 'application/json',
    ...authHeaders, // Includes: Authorization: Bearer <token>
  }
});
```

## Common Issues and Solutions

### 1. Token Format Issues

**Problem**: "Invalid token format detected"
**Solution**: 
- Verify backend sync is successful
- Check NEXT_PUBLIC_API_URL configuration
- Clear browser localStorage and cookies

### 2. CORS Errors

**Problem**: Cross-origin request blocked
**Solution**:
- CORS is now handled automatically by `@api_view`
- Verify endpoints use the enhanced API pattern
- Check that Authorization header is allowed (automatic)

### 3. Docker Networking

**Problem**: Backend sync fails in Docker
**Solution**:
- Use `http://backend:8000/api` for NEXT_PUBLIC_API_URL in Docker
- Ensure services are in the same Docker network
- Check service dependencies in docker-compose.yml

### 4. Authentication Failures

**Problem**: "No Authorization header found"
**Solution**:
- Verify JWT token is being generated during sync
- Check that token is stored in NextAuth session
- Ensure API client is sending Authorization header

## Security Considerations

1. **JWT Tokens**: Signed with Django SECRET_KEY, 30-day expiration
2. **CORS**: Automatic handling with proper preflight support
3. **Rate Limiting**: Built into email verification process
4. **Token Validation**: Format and signature verification via consolidated utilities
5. **Error Messages**: Standardized responses without sensitive data exposure 
6. **Consolidated Security**: Single source of truth for all auth functions

## Migration Notes

**✅ Completed Migrations:**
- Consolidated authentication functions into `apps.core.api_utils`
- Removed deprecated `auth_helpers.py`, `utils/http.py`, and `accounts/utils.py`
- Updated all imports to use consolidated utilities
- Enhanced error responses with standardized format
- Automatic CORS handling without manual configuration

**Benefits of Consolidation:**
- Single source of truth for authentication
- Consistent error handling across all endpoints
- Reduced maintenance overhead
- Improved developer experience
- Future-proof architecture for easy enhancements 