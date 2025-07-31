# DailyBrief Authentication Architecture

This document provides a comprehensive overview of the authentication architecture in DailyBrief, detailing how NextAuth.js in the frontend integrates with our Django backend.

## Architecture Overview

DailyBrief uses a hybrid authentication system:
- **Frontend**: NextAuth.js handles the initial user authentication
- **Backend**: Django manages user data and authorization for API requests using plain Django views

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│   NextAuth  │────▶│  Django     │────▶│  Database   │
│  (Frontend) │     │  (Backend)  │     │             │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Authentication Providers

DailyBrief supports multiple authentication methods:

1. **Email Magic Links** (Passwordless)
   - Users receive a one-time link via email
   - 5-minute expiration for security
   - Rate limiting to prevent abuse

2. **Google OAuth**
   - Single sign-on with Google accounts
   - Retrieves user profile and email information

3. **Apple Sign-in** (Coming Soon)
   - Implementation documented but currently disabled
   - Will provide similar functionality to Google OAuth

## Authentication Flow

### 1. Initial Authentication

```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  User    │───▶│  NextAuth │───▶│ OAuth/Email│───▶│  NextAuth │
│  Login   │    │  Request  │    │  Provider  │    │  Callback │
└──────────┘    └───────────┘    └───────────┘    └───────────┘
                                                        │
                                                        ▼
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  User    │◀───│  Frontend │◀───│  Django   │◀───│  NextAuth │
│ Redirect │    │  Redirect │    │  Sync     │    │  Session  │
└──────────┘    └───────────┘    └───────────┘    └───────────┘
```

1. User initiates login with email or OAuth provider
2. NextAuth handles authentication with the respective provider
3. Upon successful authentication, NextAuth creates a user session
4. NextAuth JWT callback syncs user with Django backend
5. Backend returns a Django JWT token for API authorization
6. User redirected based on onboarding status

### 2. API Request Authorization

```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  Client  │───▶│  Request  │───▶│  Django   │───▶│  Django   │
│  Request │    │  + JWT    │    │  Auth     │    │   View    │
└──────────┘    └───────────┘    └───────────┘    └───────────┘
                                                        │
                                                        ▼
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  Client  │◀───│  Response │◀───│  Process  │◀───│  DB Query │
│          │    │           │    │  Request  │    │           │
└──────────┘    └───────────┘    └───────────┘    └───────────┘
```

1. Client makes API request with JWT token in Authorization header
2. Django view calls `authenticate_request()` helper function
3. Helper validates JWT token and returns user
4. API view processes the authenticated request
5. Response is returned with CORS headers via `create_cors_response()`

## Frontend Components (NextAuth)

### Configuration

NextAuth is configured in `frontend/app/api/auth/[...nextauth]/route.ts`:

- **JWT Strategy**: Uses JWT for session management
- **Providers**: Email, Google, Apple (disabled)
- **Callbacks**: Custom JWT and session handling with Django sync
- **Custom Pages**: Login, error, verification screens
- **Docker Support**: Handles container networking with proper URL construction

### JWT Token Contents

```json
{
  "name": "User's Name",
  "email": "user@example.com",
  "picture": "https://...", 
  "sub": "nextauth-user-id",
  "django_user_id": 123,
  "django_token": "jwt-for-django-auth",
  "has_completed_onboarding": true,
  "iat": 1625097600,
  "exp": 1625184000
}
```

### Backend Synchronization

The user synchronization process:

1. NextAuth `jwt` callback triggers after successful authentication
2. The callback makes a request to `/api/accounts/sync/` with POST method
3. **Docker Environment**: Uses `http://backend:8000/api/accounts/sync/`
4. **Local Environment**: Uses `http://localhost:8000/api/accounts/sync/`
5. Backend creates/updates the user record and returns Django JWT token
6. Token is stored in the NextAuth session for subsequent API calls

### Docker URL Handling

The NextAuth sync functions automatically detect the environment:

```javascript
// Smart URL construction for Docker vs Local
let apiUrl: string;
if (baseUrl.includes('/api')) {
  // Docker: http://backend:8000/api → http://backend:8000/api/accounts/sync/
  apiUrl = `${baseUrl}/accounts/sync/`;
} else {
  // Local: http://localhost:8000 → http://localhost:8000/api/accounts/sync/
  apiUrl = `${cleanBaseUrl}/api/accounts/sync/`;
}
```

## Backend Components (Django)

### Simplified Authentication Architecture

**Previous Issues (Fixed):**
- ❌ Django REST Framework authentication conflicts
- ❌ Custom JWT middleware causing recursion errors
- ❌ Multiple authentication systems competing

**Current Solution:**
- ✅ Plain Django views with `@csrf_exempt` decorator
- ✅ Single authentication helper: `authenticate_request()`
- ✅ Consistent CORS handling with `create_cors_response()`
- ✅ No DRF authentication dependencies

### View Pattern

All authenticated views follow this consistent pattern:

```python
@csrf_exempt
def my_api_view(request):
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return handle_options_request("GET, POST, OPTIONS")
    
    # Authenticate if needed
    if request.method in ['GET', 'POST']:
        authenticated, user, error = authenticate_request(request)
        if not authenticated:
            return get_auth_response(error)
    
    # Process the request
    data = {...}
    return create_cors_response(data)
```

### User Sync API

The Django backend provides a unified `/api/accounts/sync/` endpoint:

1. **POST method**: Receives user data from NextAuth, creates/updates Django user records, and returns JWT token
2. **GET method**: Retrieves current authenticated user status and preferences
3. Returns consistent JSON responses with appropriate CORS headers

### User Preferences API

The `/api/accounts/preferences/` endpoint:

1. **GET method**: Retrieves user preferences
2. **POST method**: Updates user preferences and marks onboarding as complete

### Authentication Helper Functions

Core authentication utilities in `apps/accounts/auth_helpers.py`:

- **`authenticate_request(request)`**: Validates JWT tokens and returns user
- **`get_auth_response(message, status=401)`**: Creates standardized auth error responses
- **`create_jwt_token(user)`**: Generates Django JWT tokens with proper validation

### CORS Utilities

CORS handling utilities in `utils/http.py`:

- **`create_cors_response(data, status=200)`**: Standardized API responses with CORS headers
- **`handle_options_request(allowed_methods)`**: Handles CORS preflight requests
- **`add_cors_headers(response)`**: Adds CORS headers to existing responses

## Environment Configuration

### Docker Environment (Production/Development)

```yaml
# docker-compose.yml
environment:
  - NEXT_PUBLIC_API_URL=http://backend:8000/api
  - NEXTAUTH_URL=http://localhost:3000
  - NEXTAUTH_SECRET=dev-nextauth-secret
```

### Local Development

```bash
# Environment variables
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key
```

## Security Considerations

### Token Handling

- JWT tokens are signed with Django SECRET_KEY
- 30-day expiration for Django JWT tokens
- 5-minute expiration for magic link tokens
- Rate limiting for email verification requests
- Proper token format validation (3 segments separated by dots)

### CORS and API Security

- All API endpoints include proper CORS headers
- Authorization header explicitly allowed in CORS
- OPTIONS requests handled for preflight checks
- Standardized error responses with appropriate HTTP status codes

### Environment Variables

```bash
# Django Backend
SECRET_KEY=django-secret-key-for-jwt-signing
DEBUG=True/False
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# NextAuth Frontend
NEXTAUTH_SECRET=secure-key-for-nextauth-jwt
GOOGLE_CLIENT_ID=google-oauth-client-id
GOOGLE_CLIENT_SECRET=google-oauth-client-secret
NEXT_PUBLIC_API_URL=http://backend:8000/api (Docker) or http://localhost:8000 (Local)
```

## Docker Deployment

### Running with Docker

```bash
# Start all services
./docker.sh up

# View logs
./docker.sh logs

# Restart services
./docker.sh restart
```

### Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Database**: PostgreSQL on port 5432
- **Redis**: Redis on port 6379
- **Flower**: http://localhost:5555 (Celery monitoring)

## Troubleshooting

### Common Issues and Solutions

1. **"Invalid token format detected"**
   - Check that backend sync is successful
   - Verify NEXT_PUBLIC_API_URL is correctly set
   - Clear browser localStorage and cookies

2. **"No Authorization header found"**
   - Ensure JWT token is being generated by backend sync
   - Check network connectivity between frontend and backend containers

3. **CORS errors**
   - Verify CORS_ALLOWED_ORIGINS includes frontend URL
   - Check that OPTIONS requests are being handled

4. **Backend sync failures**
   - Check Docker container networking
   - Verify backend service is running and accessible
   - Review NextAuth server-side logs

### Debug Commands

```bash
# Check backend logs
./docker.sh django shell

# Test backend endpoint directly
curl -X POST http://localhost:8000/api/accounts/sync/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test"}'

# Check frontend logs
./docker.sh logs frontend
```

## Post-Authentication Flow

### Onboarding Status Check

After authentication, the system checks onboarding status:

1. Frontend checks `has_completed_onboarding` in JWT token
2. If necessary, makes API call to get latest status via GET to `/api/accounts/sync/`
3. Redirects to onboarding or home page based on status

### Redirection Logic

1. New users → onboarding flow
2. Existing users with incomplete onboarding → onboarding flow
3. Existing users with complete onboarding → home page

## Testing Authentication

### Manual Testing

1. **Clear browser data**: localStorage, cookies for localhost:3000
2. **Sign in**: Use email or Google OAuth
3. **Check console**: Look for NextAuth sync logs
4. **Verify token**: Should see valid JWT in API requests

### API Testing

```bash
# Test user sync
curl -X POST http://localhost:8000/api/accounts/sync/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User"}'

# Test authenticated endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/accounts/sync/
```

## Future Enhancements

1. Implement Apple Sign-in
2. Add refresh token rotation
3. Implement session management improvements
4. Add comprehensive authentication test suite
5. Enhanced security monitoring and logging 