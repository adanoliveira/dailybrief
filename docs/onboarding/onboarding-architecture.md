# Onboarding Architecture

## Overview

DailyBrief implements a multi-step onboarding flow that collects user preferences to personalize the news feed experience. The architecture follows a modular approach, with separate React components for each step and a centralized state management system.

## Architecture Components

### Frontend

```
frontend/
├── app/
│   └── onboarding/
│       └── page.tsx          # Main onboarding container and controller
├── components/
│   └── onboarding/
│       ├── welcome-step.tsx  # Introduction step
│       ├── topics-step.tsx   # Topic selection
│       ├── regions-step.tsx  # Region selection
│       ├── languages-step.tsx# Language selection
│       ├── publications-step.tsx # Publication selection
│       └── finish-step.tsx   # Confirmation step
└── lib/
    ├── onboarding-service.ts # API interactions and data processing
    ├── topic-icons.tsx       # Icons mapping for topics
    ├── region-flags.tsx      # Country/region flag emoji utilities
    ├── language-autonyms.tsx # Language names in native scripts
    └── user-context.tsx      # User state management
```

### Backend

```
backend/
├── accounts/
│   ├── models.py             # User and preference models
│   ├── serializers.py        # Preference serialization
│   └── views.py              # Preference API endpoints
└── feeds/
    ├── models.py             # Topic, Region, Language, Publication models
    ├── serializers.py        # Data serialization
    └── views.py              # API endpoints for onboarding options
```

## Data Flow

1. **Initialization**:
   - User navigates to `/onboarding`
   - Authentication is verified via NextAuth session
   - Onboarding options are fetched from `/api/feeds/basic-data`
   - Default preferences are set based on available options

2. **Step Navigation**:
   - User progresses through steps using Next/Back buttons
   - Current step is tracked in React state
   - Step changes trigger validation of current selections
   - Progress is visually indicated via progress bar

3. **Preference Collection**:
   - Each step updates the centralized preference state
   - Client-side validation ensures required selections
   - No API calls until final submission

4. **Publication Recommendation**:
   - Selected topics, regions, and languages are used to fetch recommended publications
   - Publications are automatically selected based on authority ranking
   - User can refine selections manually

5. **Preference Submission**:
   - Final preferences are submitted to `/api/accounts/preferences/`
   - User's `has_completed_onboarding` flag is updated
   - Session state is refreshed to reflect completion status

6. **Completion**:
   - User sees confirmation screen with preference summary
   - Session redirects to personalized news feed
   - **System automatically triggers first digest generation**
   - **User sees real-time generation progress on home page**

## Post-Onboarding Integration

### Automatic Digest Generation

After successful onboarding completion, the system seamlessly integrates with the digest generation pipeline:

1. **Trigger**: Digest auto-generation is initiated when user reaches home page
2. **Processing**: Celery task processes articles based on user's selected preferences
3. **Real-time Updates**: Frontend polls digest status and shows visual progress
4. **Completion**: User receives their first personalized digest without manual intervention

### Home Page Experience

The home page (`/home`) provides immediate value after onboarding:

- **Generating State**: Shows animated loading with "Creating your digest..." message
- **Progress Feedback**: Real-time status updates during generation process  
- **Success State**: Seamless transition to completed digest display
- **Error Handling**: Graceful fallback with retry options if generation fails

This ensures users get immediate value from their personalization choices without needing to understand or manually trigger digest creation.

## State Management

The onboarding process uses React's `useState` hooks to manage:

- Current step navigation
- User preferences for each category
- Loading/error states
- Validation status

```typescript
// Key state elements in page.tsx
const [currentStep, setCurrentStep] = useState<Step>("welcome")
const [stepIndex, setStepIndex] = useState(0)
const [preferences, setPreferences] = useState<UserPreferences>({...})
const [options, setOptions] = useState<OnboardingOptions | null>(null)
```

## Data Models

### UserPreferences

```typescript
export interface UserPreferences {
  topics: number[];       // Topic IDs
  regions: string[];      // Region codes
  languages: string[];    // Language ISO codes
  publications: number[]; // Publication IDs
}
```

### OnboardingOptions

```typescript
export interface OnboardingOptions {
  topics: Topic[];
  regions: Region[];
  languages: Language[];
  publications: Publication[];
}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/feeds/basic-data` | GET | Fetches all topics, regions, languages, and featured publications |
| `/api/feeds/publications` | GET | Fetches publications with filtering and pagination |
| `/api/accounts/preferences` | POST | Saves user preferences |
| `/api/accounts/sync` | GET | Gets current user status including onboarding flag |

## Security Considerations

- Onboarding route is protected for authenticated users only
- Users who have completed onboarding are redirected to home
- Preferences are only saved for the authenticated user
- Validation ensures data integrity

## Performance Optimizations

- Publication data is loaded with pagination and infinite scroll
- Cached API responses prevent redundant data fetching
- Debounced search for publication filtering
- Optimistic UI updates for selections
- Lazy loading of images

## Error Handling

- Network errors display user-friendly messages
- Validation errors display specific guidance
- Failed API calls gracefully degrade
- Session issues redirect to authentication

## Cross-Cutting Concerns

- Mobile-first responsive design
- Accessibility considerations with proper ARIA attributes
- Browser compatibility with modern standards 