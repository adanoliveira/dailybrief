# Authentication and Redirection Flow

This document explains how authentication and page redirections work in DailyBrief, specifically focusing on the post-authentication flow and how onboarding status affects navigation.

## Authentication Flow Overview

1. **Unauthenticated Users**:
   - Are redirected to `/auth` when they try to access protected routes
   - Can sign in via email magic link, Google, or Apple
   - After successful authentication, they're directed to either `/onboarding` or `/home` based on their onboarding status

2. **Authenticated Users**:
   - Are redirected based on their onboarding completion status
   - Users who haven't completed onboarding go to `/onboarding`
   - Users who have completed onboarding go to `/home`

## Architecture Approach

We've implemented a decentralized redirection approach with the following components:

### 1. SessionRedirect Component (Limited Scope)

The `SessionRedirect` component has a single responsibility:
- Redirect unauthenticated users away from protected routes to `/auth`
- It does NOT handle onboarding status or other specific redirections

```tsx
// Simplified example
if (sessionStatus === "unauthenticated" && !isPublicRoute) {
  router.replace("/auth");
}
```

### 2. Page-Level Redirection

Each page handles its own redirection logic:

- **Root Page (`/`)**: Redirects based on authentication and onboarding status
- **Auth Page (`/auth`)**: Redirects authenticated users based on onboarding status
- **Onboarding Page (`/onboarding`)**: Redirects users who have already completed onboarding

This approach provides clearer responsibility separation and prevents competing redirects.

## Implementation Details

### 1. Auth Page Redirection

```tsx
// In auth/page.tsx
useEffect(() => {
  // Skip if already redirecting
  if (isRedirecting) return;
  
  // Wait for data to load
  if (sessionStatus === "loading" || isUserLoading) return;
  
  // Handle authenticated users
  if (sessionStatus === "authenticated" && session?.user) {
    setIsRedirecting(true);
    
    // First check session token for onboarding status
    if (session.user.has_completed_onboarding === true) {
      router.replace("/home");
      return;
    }
    
    // Then check user context
    if (userStatus?.has_completed_onboarding === true) {
      router.replace("/home");
    } else {
      router.replace("/onboarding");
    }
  }
}, [sessionStatus, session, userStatus, isUserLoading, router, isRedirecting]);
```

### 2. Root Page Redirection

```tsx
// In page.tsx (root)
useEffect(() => {
  // Only proceed when data is loaded and not already redirecting
  if (isRedirecting || sessionStatus === "loading" || isUserLoading) return;
  
  // Unauthenticated users go to auth
  if (sessionStatus === "unauthenticated") {
    setIsRedirecting(true);
    router.replace("/auth");
    return;
  }
  
  // Authenticated users go to home or onboarding based on status
  if (sessionStatus === "authenticated") {
    setIsRedirecting(true);
    
    // Check onboarding status
    const hasCompletedOnboarding = 
      session?.user?.has_completed_onboarding === true || 
      userStatus?.has_completed_onboarding === true;
    
    router.replace(hasCompletedOnboarding ? "/home" : "/onboarding");
  }
}, [sessionStatus, session, userStatus, isUserLoading, router, isRedirecting]);
```

### 3. Onboarding Page Redirection

```tsx
// In onboarding/page.tsx
useEffect(() => {
  // Skip if already redirecting
  if (isRedirecting) return;
  
  // Check authentication first
  if (sessionStatus === "unauthenticated") {
    setIsRedirecting(true);
    router.replace("/auth");
    return;
  }
  
  // If onboarding is already complete, redirect to home
  const hasCompletedOnboarding = 
    session?.user?.has_completed_onboarding === true || 
    userStatus?.has_completed_onboarding === true;
  
  if (hasCompletedOnboarding) {
    setIsRedirecting(true);
    router.replace("/home");
  }
}, [session, sessionStatus, userStatus, isUserLoading, router, isRedirecting]);
```

## Preventing Redirect Loops

Several techniques are used to prevent redirect loops:

1. **Redirect Rate Limiting**: Using an `isRedirecting` state flag to prevent multiple redirects
2. **Loading States**: Showing loading states during redirection transitions
3. **Onboarding Status Checks**: Checking multiple sources (session and user context) to determine onboarding status
4. **Logged Navigation**: Extensive console logs to track navigation decisions

## Best Practices

1. **Single Responsibility**: Each component handles only what it needs to
2. **Clear Loading States**: Show loading UI while determining navigation
3. **Rate Limiting**: Prevent excessive redirects with flags and timeouts
4. **Thorough Logging**: Log redirection decisions for debugging
5. **Use `router.replace()` instead of `router.push()`**: Prevents building up history stack

## How to Add a New Protected Route

When adding a new protected route:

1. Determine if the route should be accessible to:
   - All authenticated users
   - Only users who have completed onboarding
   
2. Add appropriate redirection code to check authentication status:

```tsx
useEffect(() => {
  if (sessionStatus === "unauthenticated") {
    router.replace("/auth");
    return;
  }
  
  // If the route requires completed onboarding
  if (requiresOnboarding && !userStatus?.has_completed_onboarding) {
    router.replace("/onboarding");
  }
}, [sessionStatus, userStatus]);
``` 