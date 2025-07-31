# Authentication Implementation Plan

This document serves as our roadmap and progress control for completing the authentication system in DailyBrief. As we advance on the implementation, we will update and complement this document.

## 1. Backend Integration

### 1.1. Django User Sync API
- [x] Create a user synchronization endpoint in the Django accounts app
- [x] Implement token verification using NextAuth's JWT secret
- [x] Add user creation/update logic that maps NextAuth data to Django user model

### 1.2. Django Auth Middleware
- [x] Create a middleware that validates JWT tokens from the frontend
- [x] Add request processing to extract user info from token
- [x] Create a function to map token user to Django user

### 1.3. Frontend Integration
- [x] Add Django user ID to NextAuth JWT payload
- [x] Update API client to include auth token in all requests
- [x] Create a callback in NextAuth to sync with Django after authentication

## 2. Auth Email Flow

### 2.1. Auth Link Redirects
- [x] Update NextAuth callback configuration to check onboarding status
- [x] Add API call to Django to check user preferences status
- [x] Create a loading-check page to manage redirects after authentication
  - [x] Show skeleton UI while checking status
  - [x] Check backend for onboarding completion status
  - [x] Redirect to appropriate page (onboarding or home)
- [x] Update NextAuth redirect callback to use loading-check for all redirects:
  - [x] New users → loading-check → onboarding
  - [x] Existing users with incomplete onboarding → loading-check → onboarding
  - [x] Existing users with complete onboarding → loading-check → home

### 2.2. Email Auth Security

- [x] Modify NextAuth EmailProvider configuration for shorter token lifetime (5 minutes)
- [x] Implement rate limiting for magic link requests:
  - [x] Add client-side cooldown (20s) with UI feedback
  - [x] Add server-side protection with request throttling
- [x] Add token invalidation when new tokens are requested:
  - [x] Track issued tokens in database with user ID + timestamp
  - [x] Mark previous tokens as invalid when new ones are generated
  - [x] Validate token status during verification

### 2.3. Error Feedback
- [x] Expand error handling in auth pages
- [x] Create reusable error components with clear messaging
- [x] Implement specific error states:
  - [x] Rate limiting ("Please wait before requesting another link")
  - [x] Invalid/expired tokens ("This link has expired")
  - [x] Account exists with different provider ("This email is already registered with Google")
  - [x] Authentication failed ("Unable to sign in")

## 3. Google Sign-in

- [x] Complete Google OAuth setup:
  - [x] Create configuration guide for Google Cloud Console setup
  - [x] Document required OAuth 2.0 credentials setup process
  - [x] Add steps for authorized JavaScript origins and redirect URIs
  - [x] Include consent screen configuration instructions
- [x] Update NextAuth configuration:
  - [x] Add proper configuration for GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
  - [x] Configure profile and email scopes
  - [x] Use custom authorization parameters (prompt: "select_account")
  - [x] Update .env.example with all required variables

## 4. Apple Sign-in

- [x] Complete Apple Developer account setup documentation:
  - [x] Create detailed guide for App ID with "Sign In with Apple" capability
  - [x] Document Services ID creation for web authentication
  - [x] Include instructions for domains and return URLs configuration
  - [x] Add steps for generating and downloading private key
- [x] Update NextAuth configuration:
  - [x] Add proper configuration for APPLE_ID, APPLE_TEAM_ID and APPLE_KEY_ID
  - [x] Configure the Apple secret with proper format
  - [x] Set up proper scope configuration
  - [x] Document local HTTPS setup for development testing
- [x] Implementation notes:
  - [x] Document HTTPS requirement with mkcert for local development
  - [x] Note 6-month refresh token expiration
  - [x] Include handling for potential null email scenario
- [ ] **Temporary status:** Provider is documented but disabled until credentials are set up

## 5. Onboarding Integration (NEEDS REFACTOR)

- [x] Create backend API for user preferences:
  - [x] POST endpoint to save topic/region/language preferences
  - [x] GET endpoint to check if onboarding is complete
- [x] Update frontend onboarding flow:
  - [x] Add onboarding completion API call at final step
  - [x] Set onboarding_completed cookie when finished
  - [x] Update middleware to check this new status
- [x] Implement dashboard redirect logic:
  - [x] After successful preferences save, mark onboarding complete
  - [x] Redirect to dashboard/home page

## 6. Documentation

- [x] Create comprehensive authentication architecture document:
  - [x] Detail the authentication flow between NextAuth and Django
  - [x] Document the JWT token structure and usage
  - [x] Explain security considerations and implementations
  - [x] Provide diagrams of the authentication process
- [x] Create setup guides for authentication providers:
  - [x] Google OAuth setup guide
  - [x] Apple Sign-in setup guide
  - [x] Post-authentication redirect flow documentation

## 7. Testing & Verification

- [ ] Create test suite for auth flows:
  - [ ] Email magic link generation and verification
  - [ ] Google OAuth authentication
  - [ ] Apple OAuth authentication (when implemented)
  - [ ] Backend user synchronization
- [ ] Test edge cases:
  - [ ] Token expiration and renewal
  - [ ] Account linking attempts
  - [ ] Different email formats
  - [ ] Network interruptions during auth

## Progress Tracking

| Section | Progress | Notes |
|---------|----------|-------|
| 1. Backend Integration | Completed | Backend token validation implemented |
| 2. Auth Email Flow | Completed | Security, error handling, and redirects all implemented |
| 3. Google Sign-in | Completed | Added NextAuth configuration and documentation |
| 4. Apple Sign-in | Partially Completed | Configuration documented but temporarily disabled in UI |
| 5. Onboarding Integration | Completed | Added user preferences model and API integration |
| 6. Documentation | Completed | Comprehensive architecture document created |
| 7. Testing & Verification | Not started | | 

## Next Steps

1. Test the Google authentication flow with real credentials
2. Implement comprehensive test cases for authentication
3. Add account linking if needed in future versions
4. Implement Apple Sign-in when ready

## Testing 

### Testing the Email Auth Flow

1. **Start the development servers**
   ```
   # Start Django backend
   cd backend
   python manage.py runserver
   
   # In another terminal, start Next.js frontend
   cd frontend
   npm run dev
   ```

2. **Test the basic authentication flow**
   - Visit `/auth` in your browser
   - Enter your email address and click "Continue with Email"
   - Verify that the cooldown timer appears (20s)
   - Check your console logs for the magic link URL (in development mode)

3. **Test rate limiting**
   - Try requesting multiple links within the 20-second cooldown
   - Verify the error message appears

4. **Test the magic link**
   - Use the magic link from your console logs or email
   - It should authenticate you and redirect to the loading-check page
   - Loading-check will determine where to redirect you:
     - If you have no topics selected → onboarding
     - If you have topics selected → home

5. **Test token expiration**
   - Wait more than 5 minutes before clicking a magic link
   - Verify you see the proper error page about expired tokens

6. **Test middleware redirects**
   - After authenticating, try visiting protected routes
   - Try visiting the `/auth` page while authenticated (should redirect to home)

7. **Test onboarding integration**
   - After authenticating for the first time, verify you're sent to onboarding
   - If you have test data, verify completed onboarding redirects to home
   - Complete the onboarding form and verify the preferences are saved to the database
   - Verify that the user is redirected to the home page after completing onboarding

The development environment will show magic links in the console, so you don't need to check your email during testing.
