# Authentication Workflow Refactoring Plan

## Current Issues

1. **Multiple Redundant Backend Calls**
   - The frontend makes multiple calls to check user status and preferences
   - Three parallel checks: session data, localStorage, and API calls
   - This results in performance issues and potential race conditions

2. **Complex State Management**
   - User state is managed in multiple places: NextAuth session, localStorage, and UserContext
   - The loading-check component makes duplicate API calls and has its own state logic
   - This creates potential inconsistencies in user state

3. **Multiple Redirect Mechanisms**
   - Middleware redirects based on NextAuth session
   - Loading-check page makes its own redirection decisions
   - UserContext impacts routing decisions
   - This causes unpredictable navigation behavior

4. **Inefficient Code Flow**
   - App loads `/loading-check` which then decides where to go next
   - Multiple checks for the same information (onboarding status)
   - Every page load triggers new API calls to verify authentication

## Target Workflow

1. **Authentication Step**
   - User authenticates via email, Google, or Apple
   - On successful auth, make a single call to `/api/accounts/sync/`
   - Store complete user data including onboarding status

2. **State Storage Step**
   - Store user data in UserContext as the single source of truth
   - Cache minimal necessary data in localStorage for offline/startup

3. **Route Decision Step**
   - Based on `has_completed_onboarding` flag, direct user:
     - If true: go to `/home`
     - If false: go to `/onboarding`

4. **Onboarding Step (if needed)**
   - Complete onboarding and save preferences
   - Update user state and redirect to `/home`

## Implementation Plan

### Phase 1: Refactor User Context (Single Source of Truth)

1. Update `UserContext` to:
   - Load user data only once after authentication
   - Provide proper loading states
   - Cache user data efficiently
   - Eliminate redundant API calls

2. Modifications needed:
   - Simplify the context initialization
   - Add clear state update methods
   - Improve error handling
   - Optimize caching strategy

### Phase 2: Streamline Auth Flow

1. Update auth components to:
   - Directly check onboarding status after login
   - Simplify post-auth navigation
   - Avoid unnecessary redirections

2. Eliminate loading-check page:
   - Replace with in-page loading states
   - Handle auth-to-page transitions elegantly

### Phase 3: Update Middleware and Routes

1. Simplify middleware to:
   - Focus on auth status only (not onboarding)
   - Protect appropriate routes
   - Allow public routes

2. Adjust routes to:
   - Match new workflow
   - Handle auth state transitions cleanly

### Phase 4: Clean Up Redundant Code

1. Remove unused functions:
   - Duplicate API calls
   - Redundant state checks
   - Unnecessary localStorage operations

2. Ensure consistent behavior:
   - Across different auth methods
   - During offline/online transitions
   - While handling errors

## Files to Modify

1. `frontend/lib/user-context.tsx` - Primary state management
2. `frontend/middleware.ts` - Route protection
3. `frontend/app/auth/page.tsx` - Authentication implementation
4. `frontend/lib/accounts-service.ts` - API interactions
5. `frontend/lib/api-client.ts` - API fetching logic
6. `frontend/app/(authenticated)/loading-check/page.tsx` - To be removed
7. `frontend/app/onboarding/page.tsx` - Onboarding flow integration 