# DailyBrief - Onboarding Flow Plan

## Current State Analysis

The current onboarding flow:
- Uses a single-page form with all preference options at once
- Has hardcoded preference options (topics, sources, languages)
- Lacks proper mobile-first UX
- Doesn't properly connect with backend APIs to fetch available options
- Has outdated integration with the authentication flow

## Requirements

1. Create a multi-step onboarding flow
2. Pull available preferences from the backend:
   - Topics
   - Regions
   - Publishers/Sources
   - Languages
3. Set smart defaults
4. Mobile-first UX/UI
5. Proper integration with auth flow
6. Save preferences to backend when complete
7. Mark onboarding as complete in both frontend and backend

## Backend API Endpoints

From analysis, we have these endpoints available:
- `/api/feeds/topics/` - Get all topics
- `/api/feeds/regions/` - Get all regions
- `/api/feeds/languages/` - Get all languages
- `/api/feeds/publications/` - Get all publications (with optional filters)
- `/api/accounts/preferences/` - GET current preferences or POST new preferences

## Frontend Implementation Plan

### 1. Create New Onboarding Service

Create a new service to handle fetching preference data and submitting onboarding results:

```typescript
// frontend/lib/onboarding-service.ts
import apiClient from '@/lib/api-client';

export interface Topic {
  id: number;
  name: string;
  slug: string;
}

export interface Region {
  code: string;
  name: string;
}

export interface Language {
  iso_code: string;
  name: string;
}

export interface Publication {
  id: number;
  name: string;
  website_url: string;
  logo_url: string | null;
  description: string;
  authority: number;
}

export interface OnboardingOptions {
  topics: Topic[];
  regions: Region[];
  languages: Language[];
  publications: Publication[];
}

export interface UserPreferences {
  topics: number[];
  regions: string[];
  languages: string[];
  publications: number[];
}

// Fetch all options for onboarding
export async function fetchOnboardingOptions(): Promise<OnboardingOptions> {
  try {
    const [topics, regions, languages, publications] = await Promise.all([
      apiClient.get<Topic[]>('/api/feeds/topics/'),
      apiClient.get<Region[]>('/api/feeds/regions/'),
      apiClient.get<Language[]>('/api/feeds/languages/'),
      apiClient.get<Publication[]>('/api/feeds/publications/')
    ]);
    
    return {
      topics,
      regions,
      languages,
      publications
    };
  } catch (error) {
    console.error('Error fetching onboarding options:', error);
    throw new Error('Failed to load onboarding options');
  }
}

// Submit user preferences
export async function saveUserPreferences(preferences: UserPreferences): Promise<{ success: boolean }> {
  try {
    await apiClient.post('/api/accounts/preferences/', preferences);
    return { success: true };
  } catch (error) {
    console.error('Error saving preferences:', error);
    throw new Error('Failed to save preferences');
  }
}
```

### 2. Create Multi-Step Onboarding Components

#### Main Onboarding Layout
```tsx
// frontend/app/onboarding/page.tsx
"use client"

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useUser } from "@/lib/user-context";
import { 
  fetchOnboardingOptions, 
  saveUserPreferences,
  UserPreferences,
  OnboardingOptions,
  Topic,
  Region,
  Language,
  Publication
} from "@/lib/onboarding-service";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { LogoHorizontal } from "@/components/ui/logo";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

// Step components
import { WelcomeStep } from "@/components/onboarding/welcome-step";
import { TopicsStep } from "@/components/onboarding/topics-step";
import { RegionsStep } from "@/components/onboarding/regions-step";
import { LanguagesStep } from "@/components/onboarding/languages-step";
import { PublicationsStep } from "@/components/onboarding/publications-step";
import { FinishStep } from "@/components/onboarding/finish-step";

// Onboarding steps
type Step = "welcome" | "topics" | "regions" | "languages" | "publications" | "finish";
const STEPS: Step[] = ["welcome", "topics", "regions", "languages", "publications", "finish"];

export default function OnboardingPage() {
  // Step and navigation state
  const [currentStep, setCurrentStep] = useState<Step>("welcome");
  const [stepIndex, setStepIndex] = useState(0);
  
  // Preferences state
  const [preferences, setPreferences] = useState<UserPreferences>({
    topics: [],
    regions: [],
    languages: [],
    publications: []
  });
  
  // Options from API
  const [options, setOptions] = useState<OnboardingOptions | null>(null);
  
  // Loading and error states
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Auth and routing
  const { userStatus, isLoading: isUserLoading, setOnboardingComplete } = useUser();
  const { data: session, status: sessionStatus } = useSession();
  const router = useRouter();
  
  // Check auth state and fetch options
  useEffect(() => {
    // Handle redirects for already onboarded or unauthenticated users
    if (sessionStatus === "unauthenticated") {
      router.replace("/auth");
      return;
    }
    
    if (
      !isUserLoading && 
      (userStatus?.has_completed_onboarding || session?.user?.has_completed_onboarding)
    ) {
      router.replace("/home");
      return;
    }
    
    // Fetch options from API
    const loadOptions = async () => {
      try {
        setIsLoading(true);
        const data = await fetchOnboardingOptions();
        setOptions(data);
        
        // Set smart defaults
        setPreferences({
          topics: data.topics.filter(t => 
            ["general", "technology", "world"].includes(t.slug)
          ).map(t => t.id).slice(0, 3),
          regions: data.regions.filter(r => 
            ["us", "gb", "ca"].includes(r.code)
          ).map(r => r.code).slice(0, 2),
          languages: ["en"],
          publications: data.publications
            .filter(p => p.authority >= 4.5)
            .slice(0, 5)
            .map(p => p.id)
        });
      } catch (err) {
        setError("Failed to load options. Please try again.");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadOptions();
  }, [sessionStatus, userStatus, isUserLoading, session, router]);
  
  // Navigation handlers
  const goToNextStep = () => {
    const nextIndex = stepIndex + 1;
    if (nextIndex < STEPS.length) {
      setStepIndex(nextIndex);
      setCurrentStep(STEPS[nextIndex]);
      window.scrollTo(0, 0);
    }
  };
  
  const goToPrevStep = () => {
    const prevIndex = stepIndex - 1;
    if (prevIndex >= 0) {
      setStepIndex(prevIndex);
      setCurrentStep(STEPS[prevIndex]);
      window.scrollTo(0, 0);
    }
  };
  
  // Update preferences
  const updatePreferences = (key: keyof UserPreferences, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };
  
  // Submit final preferences
  const submitPreferences = async () => {
    try {
      setIsSubmitting(true);
      setError(null);
      
      await saveUserPreferences(preferences);
      
      // Update user context
      setOnboardingComplete(true);
      
      // Go to final step
      setCurrentStep("finish");
      setStepIndex(STEPS.indexOf("finish"));
    } catch (err) {
      setError("Failed to save preferences. Please try again.");
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handle finish
  const finishOnboarding = () => {
    router.replace("/home");
  };
  
  // Loading state
  if (isLoading || !options) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-4">
        <LogoHorizontal width={180} priority />
        <div className="mt-8 flex flex-col items-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-muted-foreground">Loading your personalization options...</p>
        </div>
      </div>
    );
  }
  
  // Progress percentage
  const progress = Math.max(
    5, 
    Math.min(100, ((stepIndex / (STEPS.length - 1)) * 100))
  );
  
  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="p-4 border-b">
        <div className="container max-w-md mx-auto">
          <LogoHorizontal width={150} priority />
          <Progress value={progress} className="mt-4" />
        </div>
      </header>
      
      {/* Main content */}
      <main className="flex-1 container max-w-md mx-auto px-4 py-6">
        {error && (
          <div className="bg-destructive/10 text-destructive p-3 rounded-md mb-6">
            {error}
          </div>
        )}
        
        {/* Step content */}
        <div className="mb-8">
          {currentStep === "welcome" && (
            <WelcomeStep onNext={goToNextStep} />
          )}
          
          {currentStep === "topics" && options && (
            <TopicsStep 
              topics={options.topics}
              selectedTopics={preferences.topics}
              onChange={(selected) => updatePreferences('topics', selected)}
              onNext={goToNextStep}
              onBack={goToPrevStep}
            />
          )}
          
          {currentStep === "regions" && options && (
            <RegionsStep
              regions={options.regions}
              selectedRegions={preferences.regions}
              onChange={(selected) => updatePreferences('regions', selected)}
              onNext={goToNextStep}
              onBack={goToPrevStep}
            />
          )}
          
          {currentStep === "languages" && options && (
            <LanguagesStep
              languages={options.languages}
              selectedLanguages={preferences.languages}
              onChange={(selected) => updatePreferences('languages', selected)}
              onNext={goToNextStep}
              onBack={goToPrevStep}
            />
          )}
          
          {currentStep === "publications" && options && (
            <PublicationsStep
              publications={options.publications}
              selectedPublications={preferences.publications}
              onChange={(selected) => updatePreferences('publications', selected)}
              onNext={submitPreferences}
              onBack={goToPrevStep}
              isSubmitting={isSubmitting}
            />
          )}
          
          {currentStep === "finish" && (
            <FinishStep onFinish={finishOnboarding} />
          )}
        </div>
      </main>
    </div>
  );
}
```

### 3. Individual Step Components

Create the following step components:

1. `WelcomeStep`: Introduces the onboarding process
2. `TopicsStep`: Select news topics
3. `RegionsStep`: Select regions of interest
4. `LanguagesStep`: Select language preferences
5. `PublicationsStep`: Select preferred news sources
6. `FinishStep`: Confirmation and completion

Each step will be a separate component with a consistent UI pattern following mobile-first design principles.

## UI/UX Principles

1. **Mobile-first design**: All components optimized for touch and mobile screens
2. **Minimal UI**: Clean, simple interface with clear instructions
3. **Visual feedback**: Clear indicators of selection and progress
4. **Smart defaults**: Pre-select popular/relevant options
5. **Limited choices**: Avoid overwhelming users with too many options at once
6. **Clear CTAs**: Prominent action buttons
7. **Instant feedback**: Visual confirmation of selections

## Implementation Timeline

1. Create onboarding service (1 hour)
2. Build the base onboarding page with step framework (2 hours)
3. Implement individual step components (3 hours)
4. Add visual polish and animations (1 hour)
5. Connect to backend APIs and test (1 hour)
6. Final testing and bug fixes (1 hour)

Total estimated time: 9 hours 