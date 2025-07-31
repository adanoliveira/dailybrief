# Onboarding Navigation Flow

## Overview

The DailyBrief onboarding process implements a guided step-by-step navigation flow that walks users through preference selection in a logical sequence. This document details how navigation works between steps, the validation rules, and the user experience considerations.

## Step Sequence

The onboarding flow follows a fixed sequence:

1. **Welcome** → Introduction and overview
2. **Topics** → Topic selection
3. **Regions** → Geographic region selection
4. **Languages** → Language preference selection
5. **Publications** → Publication source selection
6. **Finish** → Confirmation and completion

## Navigation Management

The navigation is controlled by the `OnboardingPage` component in `frontend/app/onboarding/page.tsx`, which manages:

- Current step tracking
- Step index for progress calculation
- Validation rules for each step
- Special case handling for final steps

```typescript
// Step and navigation state
const [currentStep, setCurrentStep] = useState<Step>("welcome")
const [stepIndex, setStepIndex] = useState(0)
```

## Navigation Controls

The `StepNavigation` component renders appropriate navigation controls based on the current step:

- **Standard Steps**: Back + Continue buttons
- **Welcome Step**: Single "Let's Get Started" button
- **Finish Step**: Single "Go to My Feed" button
- **Final Step (Publications)**: Continue triggers preference submission

## Navigation Logic

### Forward Navigation (`goToNextStep`)

```typescript
const goToNextStep = () => {
  // Clear any validation errors
  setValidationError(null)
  
  // Validate current step
  if (currentStep === "topics" && preferences.topics.length === 0) {
    setValidationError("Please select at least one topic")
    return
  }
  
  // Similar validation for other steps...
  
  // Handle special case for the final step (publications)
  if (currentStep === "publications") {
    submitPreferences()
    return
  }
  
  // Handle special case for finish step
  if (currentStep === "finish") {
    finishOnboarding()
    return
  }
  
  // Regular navigation
  const nextIndex = stepIndex + 1
  if (nextIndex < STEPS.length) {
    setStepIndex(nextIndex)
    setCurrentStep(STEPS[nextIndex])
    window.scrollTo(0, 0)
  }
}
```

### Backward Navigation (`goToPrevStep`)

```typescript
const goToPrevStep = () => {
  // Clear any validation errors
  setValidationError(null)
  
  const prevIndex = stepIndex - 1
  if (prevIndex >= 0) {
    setStepIndex(prevIndex)
    setCurrentStep(STEPS[prevIndex])
    window.scrollTo(0, 0)
  }
}
```

## Validation Rules

Each step has specific validation rules:

1. **Welcome**: No validation (informational only)
2. **Topics**: At least one topic must be selected
3. **Regions**: At least one region must be selected
4. **Languages**: At least one language must be selected
5. **Publications**: At least one publication must be selected
6. **Finish**: No validation (confirmation only)

## Button State Management

The Continue button is disabled under these conditions:

- During submission (loading state)
- When validation fails
- When required selections are missing

```typescript
<Button 
  onClick={onNext}
  disabled={isSubmitting || !isValid}
>
  {isSubmitting ? (
    <>
      <LoadingSpinner className="mr-2 h-4 w-4" />
      Saving...
    </>
  ) : isFinalStep ? "Finish" : "Continue"}
</Button>
```

## Progress Tracking

User progress is visually indicated through:

1. **Progress Bar**: Shows percentage completion based on current step index
2. **Step Titles**: Current step is highlighted in the UI
3. **Visual Feedback**: Completed steps have check marks (in some UI variations)

```typescript
// Progress percentage calculation
const progress = Math.max(
  5, 
  Math.min(100, ((stepIndex / (STEPS.length - 1)) * 100))
)
```

## Special Navigation Cases

### Publication Step to Finish Step

When completing the publications step:

1. User preferences are submitted to the backend
2. The `has_completed_onboarding` flag is set to `true`
3. The session is updated with the new onboarding status
4. Only then is the user navigated to the finish step

```typescript
const submitPreferences = async () => {
  try {
    // Save preferences to backend
    const response = await saveUserPreferences(preferences)
    
    // Update user context and session
    setOnboardingComplete(true)
    await updateSession()
    
    // Navigate to finish step
    setCurrentStep("finish")
    setStepIndex(STEPS.indexOf("finish"))
  } catch (err) {
    // Error handling
  }
}
```

### Finish Step to Home Page

When the user completes the entire flow:

1. The `finishOnboarding` function is called
2. The user is redirected to the home page
3. A small delay ensures smooth transition
4. **The home page automatically triggers first digest generation**
5. **User sees real-time progress of digest creation**

```typescript
const finishOnboarding = () => {
  setIsRedirecting(true)
  
  // Small delay for smooth transition
  setTimeout(() => {
    router.replace("/home")
  }, 100)
}
```

## Post-Onboarding Flow

### Home Page Integration

After onboarding completion, the home page seamlessly continues the user journey:

1. **Auto-Detection**: Home page detects new user without existing digest
2. **Auto-Generation**: Automatically triggers digest generation with `force_regenerate: true`
3. **Real-time Feedback**: Shows generating state with progress indicators
4. **Status Polling**: Polls backend every 3 seconds for generation status
5. **Completion**: Smoothly transitions to display completed digest

### Digest Generation States

The digest card manages three distinct states post-onboarding:

```typescript
// Generating State
- Headline: "Creating your digest..."
- Visual: Skeleton loaders matching final layout
- Feedback: Subtle gradient and backdrop blur effects

// Success State  
- Transition: Smooth fade-in of digest content
- Visual: Clean, minimalistic design matching app theme

// Error State
- Headline: "😞 Couldn't load your digest"  
- Actions: Retry button and view archive option
- Recovery: Reset to generating state on retry
```

### User Experience Continuity

The post-onboarding flow ensures:

- **Immediate Value**: Users see personalized content creation in real-time
- **No Dead Ends**: No empty states or manual triggers required
- **Progressive Enhancement**: Graceful fallbacks for any failures
- **Consistent Design**: Unified visual language from onboarding to content

## Preventing Premature Exit

Several safeguards prevent users from exiting the flow prematurely:

1. **Session Checks**: Authentication is verified before showing onboarding
2. **Onboarding Status Checks**: Completed onboarding status is checked
3. **Error Recovery**: Failed API calls allow retries without losing progress
4. **Browser Navigation**: Page refreshes retain current state when possible

## Handling Completed Onboarding

Users who have already completed onboarding are automatically redirected:

```typescript
// Check if user has already completed onboarding
const hasCompletedOnboarding = userStatus?.has_completed_onboarding === true

// Only redirect if onboarding is complete AND not on finish step AND not submitting
if (hasCompletedOnboarding && currentStep !== "finish" && !isSubmitting) {
  router.replace("/home")
}
```

## User Experience Considerations

1. **Scroll Position**: Reset to top on step changes
2. **Loading Feedback**: Clear indicators during API operations
3. **Error Messages**: Specific validation guidance
4. **Fixed Navigation**: Bottom navigation bar stays accessible
5. **Progress Visibility**: Always visible progress indicator

## Implementation Best Practices

1. **State Isolation**: Each step manages its internal state
2. **Unidirectional Data Flow**: Child components report changes up
3. **Validation First**: Validate before navigation
4. **Consistent Patterns**: Similar navigation across all steps
5. **Graceful Degradation**: Fallbacks for network issues 