# Onboarding Step Components

## Overview

The DailyBrief onboarding flow consists of six distinct step components, each responsible for collecting a specific aspect of user preferences. Each component is designed to be modular, reusable, and focused on a single responsibility.

## Component Hierarchy

```
OnboardingPage (Container)
├── WelcomeStep
├── TopicsStep
├── RegionsStep
├── LanguagesStep
├── PublicationsStep
└── FinishStep
```

## Common Props Pattern

All step components follow a consistent props pattern:

```typescript
interface StepProps {
  // Data from API
  [items]: ItemType[];
  
  // Currently selected values
  selected[Items]: IdType[];
  
  // Callback for changes
  onChange: (selected: IdType[]) => void;
  
  // Optional error message
  error?: string | null;
}
```

## Step Components

### 1. WelcomeStep

**Purpose:** Introduce users to the onboarding process and set expectations.

**Features:**
- Brand introduction
- Value proposition explanation
- No user input required
- Single action to proceed

**Implementation:**
- Static content with minimal interactivity
- Focus on clear communication and motivation

### 2. TopicsStep

**Purpose:** Allow users to select news topics they're interested in.

**Features:**
- Grid layout of selectable topic cards
- Visual topic icons from `topic-icons.tsx`
- Toggle selection with visual feedback
- Required selection (at least one topic)

**Implementation:**
- Controlled component with selected state
- Selection updates parent state via `onChange`
- Default selection of "General" topic

### 3. RegionsStep

**Purpose:** Collect geographic preferences for news content.

**Features:**
- List of regions with country flags
- Multi-select capability
- Search/filter functionality for large region lists
- Required selection (at least one region)

**Implementation:**
- Optimized rendering for potentially large lists
- Visual grouping by continents/regions
- Default selection based on user locale

### 4. LanguagesStep

**Purpose:** Determine language preferences for content.

**Features:**
- Language selection cards with native names
- Multi-select capability
- Common languages prominently featured
- Required selection (at least one language)

**Implementation:**
- Intelligent defaults based on browser language
- Primary/secondary language distinction
- ISO language code mapping

### 5. PublicationsStep

**Purpose:** Fine-tune publication sources based on previous selections.

**Features:**
- Two tabs: "Recommended" and "Other"
- Automatic selection of recommended publications
- Search and filtering capabilities
- Infinite scroll for browsing publications
- Visual indicators for topic and region tags
- Publication logos and favicons

**Implementation:**
- Complex state management for pagination
- Auto-selection logic based on authority ranking
- Optimized rendering for potentially hundreds of items
- Error handling for image loading
- Client-side and server-side filtering

**Key Functions:**
- `loadPublications`: Fetches paginated publications with filters
- `togglePublication`: Handles selection/deselection
- `handleTabChange`: Manages tab interface
- `renderPublicationItem`: Renders individual publication cards

### 6. FinishStep

**Purpose:** Confirm selections, complete the onboarding process, and initiate personalized content creation.

**Features:**
- Summary of selections with counts
- Visual confirmation of completion
- Call-to-action to enter personalized feed
- Engaging confirmation messaging
- **Seamless transition to automatic digest generation**

**Implementation:**
- Display of preference counts by category
- Final action button to complete process
- Clean, celebratory design
- **Integration with digest auto-generation pipeline**
- **Sets up user for immediate value delivery on home page**

**Post-Completion Flow:**
- Redirects user to home page (`/home`)
- Home page detects new user and auto-generates first digest
- User experiences real-time digest creation with visual feedback
- Smooth transition from onboarding to personalized content consumption

## Navigation Component

A shared `StepNavigation` component handles navigation between steps:

**Features:**
- Back/Continue buttons
- Custom state for welcome and finish steps
- Loading indicators during submission
- Validation-based button disabling
- Selection count display

**Implementation:**
- Conditionally renders different UI based on step
- Handles validation and navigation logic
- Consistent placement at bottom of screen

## Common UI Patterns

Across all step components:

1. **Selection Pattern:**
   - Consistent visual feedback for selected items
   - Clear toggle mechanism
   - Responsive grid or list layouts

2. **Error Handling:**
   - Inline validation messages
   - Graceful recovery from API failures
   - Fallback UI for missing data

3. **Loading States:**
   - Clear loading indicators
   - Skeleton UI when appropriate
   - Optimistic UI updates

4. **Accessibility:**
   - Semantic HTML elements
   - Keyboard navigation support
   - Screen reader considerations

## Component Lifecycle

1. Component mounts with default or previously selected values
2. User interacts with selection UI
3. Component calls `onChange` with updated selections
4. Parent updates state and passes new props
5. Component rerenders with new selection state

## Code Structure

Each component follows a consistent internal structure:

1. Props interface definition
2. State declarations
3. Event handlers and effects
4. Rendering logic with clear sections
5. Helper functions for complex UI elements

This modularity allows for easy testing, maintenance, and enhancement of individual steps without affecting the overall flow. 