# New Authentication Flow Diagram

```
┌───────────────┐
│ User Visits   │
│ Application   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Check Auth    │◄────────────────────────────┐
│ Status        │                             │
└───────┬───────┘                             │
        │                                     │
        ▼                                     │
┌───────────────┐     No     ┌──────────────┐ │
│ Is User       ├────────────► Go to Auth   │ │
│ Authenticated?│            │ Page         │ │
└───────┬───────┘            └──────┬───────┘ │
        │ Yes                       │         │
        ▼                           ▼         │
┌────────────────┐         ┌──────────────┐   │
│ Load User Data │         │ User         │   │
│ from Context   │         │ Authenticates│   │
└────────┬───────┘         └──────┬───────┘   │
        │                         │           │
        │                         ▼           │
        │                 ┌──────────────┐    │
        │                 │ Single API   │    │
        │                 │ Call to Sync │    │
        │                 └──────┬───────┘    │
        │                        │            │
        │                        ▼            │
        │                 ┌──────────────┐    │
        │                 │ Update User  │    │
        │                 │ Context      ├────┘
        │                 └──────────────┘
        │
        ▼
┌────────────────┐     No      ┌──────────────┐
│ Has Completed  ├─────────────► Go to        │
│ Onboarding?    │             │ Onboarding   │
└────────┬───────┘             └──────┬───────┘
        │ Yes                         │
        ▼                             ▼
┌────────────────┐           ┌──────────────┐
│ Go to Homepage │           │ Complete     │
│                │◄──────────┤ Onboarding   │
└────────────────┘           └──────────────┘
```

## Key Principles

1. **Single Source of Truth**
   - User state managed only in UserContext
   - All components read from this context

2. **Minimal API Calls**
   - One call to sync after authentication
   - One call to save preferences after onboarding

3. **Clear Decision Points**
   - Auth status determines protected routes access
   - Onboarding status determines post-auth routing

4. **User Experience**
   - Proper loading states shown during transitions
   - Intuitive flow without unnecessary redirects

## Implementation Notes

- The middleware will only check if routes are protected, not handle onboarding status
- Client-side code will handle the onboarding vs. home navigation decision
- Loading states will be managed through the UserContext provider 