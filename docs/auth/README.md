# DailyBrief Authentication System

This directory contains documentation for the DailyBrief authentication system.

## 🚀 Quick Start

### Docker Environment (Recommended)
```bash
# Start all services
./docker.sh up

# View logs
./docker.sh logs

# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Local Development
```bash
# Backend
cd backend && python manage.py runserver

# Frontend (in another terminal)
cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## 📁 Documentation Files

- **[authentication-architecture.md](authentication-architecture.md)** - Complete system overview
- **[implementation_plan__auth.md](implementation_plan__auth.md)** - Implementation details
- **[google-oauth-setup.md](google-oauth-setup.md)** - Google OAuth configuration
- **[apple-signin-setup.md](apple-signin-setup.md)** - Apple Sign-in setup (future)
- **[post-auth-redirect.md](post-auth-redirect.md)** - Redirect flow logic

## ✅ Current Status (Working)

### Authentication Flow
1. **NextAuth.js** handles initial user authentication (Google OAuth, Email magic links)
2. **Django sync** creates/updates user records and generates JWT tokens
3. **JWT tokens** are used for all subsequent API requests
4. **Plain Django views** handle authentication with custom helpers

### Key Components
- **Frontend**: NextAuth.js with Docker-aware URL handling
- **Backend**: Plain Django views with `@csrf_exempt` and custom JWT validation
- **CORS**: Proper headers for cross-origin requests
- **Docker**: Container networking with service name resolution

## 🔧 Recent Fixes (December 2024)

### Issues Resolved
- ❌ **DRF Authentication Conflicts**: Removed Django REST Framework authentication
- ❌ **Recursion Errors**: Eliminated competing authentication systems
- ❌ **Docker URL Issues**: Fixed NextAuth sync in container environment
- ❌ **Token Format Errors**: Improved JWT generation and validation

### Current Architecture
- ✅ **Simplified Views**: Plain Django views with `@csrf_exempt`
- ✅ **Single Auth Helper**: `authenticate_request()` function
- ✅ **Consistent CORS**: All responses include proper headers
- ✅ **Docker Support**: Automatic URL construction for container networking

## 🐳 Docker Configuration

```yaml
# docker-compose.yml
frontend:
  environment:
    - NEXT_PUBLIC_API_URL=http://backend:8000/api  # Important!
    - NEXTAUTH_URL=http://localhost:3000
    - NEXTAUTH_SECRET=dev-nextauth-secret

backend:
  environment:
    - SECRET_KEY=dev-secret-key
    - CORS_ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000
```

## 🧪 Testing Authentication

### Manual Test
1. Clear browser data (localStorage, cookies)
2. Go to http://localhost:3000
3. Sign in with Google or email
4. Check browser console for NextAuth logs
5. Verify successful onboarding flow

### API Test
```bash
# Test user sync (no auth required)
curl -X POST http://localhost:8000/api/accounts/sync/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User"}'

# Should return JWT token in response
```

## 🔍 Troubleshooting

### Common Issues

1. **"Invalid token format detected"**
   - Check NextAuth sync logs in browser console
   - Verify NEXT_PUBLIC_API_URL is set correctly
   - Clear browser localStorage and cookies

2. **Backend sync fails**
   - Check Docker container networking
   - Verify backend service is running
   - Review NextAuth server-side logs

3. **CORS errors**
   - Ensure CORS_ALLOWED_ORIGINS includes frontend URL
   - Check that Authorization header is allowed

### Debug Commands

```bash
# Check if backend is accessible from frontend container
./docker.sh exec frontend curl http://backend:8000/api/accounts/sync/

# View backend logs
./docker.sh logs backend

# View frontend logs
./docker.sh logs frontend
```

## 📊 Authentication Success Indicators

Look for these logs in the browser console:

```javascript
// Successful sync
"Server-side sync - using baseUrl: http://backend:8000/api"
"Backend sync response status: 200"
"Valid JWT token received from backend - length: 165"

// Failed sync (falling back to offline mode)
"Error syncing user with backend: ..."
"Falling back to offline_mode_token"
```

## 🔐 Security Features

- **JWT Tokens**: Signed with Django SECRET_KEY, 30-day expiration
- **Magic Links**: 5-minute expiration, rate limiting
- **CORS**: Explicit origin allowlist
- **Token Validation**: Format and signature verification
- **Error Handling**: Sanitized error messages

## 🚧 Future Enhancements

- [ ] Apple Sign-in implementation
- [ ] Refresh token rotation
- [ ] Enhanced session management
- [ ] Comprehensive test suite
- [ ] Security monitoring and logging

---

For detailed technical information, see [authentication-architecture.md](authentication-architecture.md). 