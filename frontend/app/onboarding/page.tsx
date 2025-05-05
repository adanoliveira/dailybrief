"use client"

import { useState, useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"
import { useSession } from "next-auth/react"
import { useUser } from "@/lib/user-context"
import { Progress } from "@/components/ui/progress"
import { LogoHorizontal } from "@/components/ui/logo"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { Button } from "@/components/ui/button"
import { 
  fetchOnboardingOptions, 
  saveUserPreferences,
  getDefaultPreferences,
  UserPreferences,
  OnboardingOptions
} from "@/lib/onboarding-service"

// Import step components
import { WelcomeStep } from "@/components/onboarding/welcome-step"
import { TopicsStep } from "@/components/onboarding/topics-step"
import { RegionsStep } from "@/components/onboarding/regions-step"
import { LanguagesStep } from "@/components/onboarding/languages-step"
import { PublicationsStep } from "@/components/onboarding/publications-step"
import { FinishStep } from "@/components/onboarding/finish-step"

// Onboarding steps
type Step = "welcome" | "topics" | "regions" | "languages" | "publications" | "finish"
const STEPS: Step[] = ["welcome", "topics", "regions", "languages", "publications", "finish"]

// Step names for display in nav
const STEP_NAMES: Record<Step, string> = {
  welcome: "Welcome",
  topics: "Topics",
  regions: "Regions",
  languages: "Languages",
  publications: "Sources",
  finish: "Done"
}

// Navigation component
function StepNavigation({ 
  currentStep, 
  onNext, 
  onBack, 
  isSubmitting = false,
  isFinalStep = false,
  isFirstStep = false,
  selectionCount = 0
}: { 
  currentStep: Step,
  onNext: () => void, 
  onBack: () => void,
  isSubmitting?: boolean,
  isFinalStep?: boolean,
  isFirstStep?: boolean,
  selectionCount?: number
}) {
  let leftButton = (
    <Button 
      onClick={onBack} 
      variant="outline"
      disabled={isFirstStep || isSubmitting}
    >
      Back
    </Button>
  )

  let rightButton = (
    <Button 
      onClick={onNext}
      disabled={isSubmitting}
    >
      {isSubmitting ? (
        <>
          <LoadingSpinner className="mr-2 h-4 w-4" />
          Saving...
        </>
      ) : isFinalStep ? "Finish" : "Continue"}
    </Button>
  )

  // Special case for welcome step
  if (currentStep === "welcome") {
    return (
      <div className="container max-w-md mx-auto">
        <Button 
          onClick={onNext} 
          className="w-full"
          size="lg"
        >
          Let's Get Started
        </Button>
      </div>
    )
  }

  // Special case for finish step
  if (currentStep === "finish") {
    return (
      <div className="container max-w-md mx-auto">
        <Button 
          onClick={onNext} 
          className="w-full"
          size="lg"
        >
          Go to My Feed
        </Button>
      </div>
    )
  }

  // Show selection count for steps that have selections
  const showSelectionCount = ["topics", "regions", "languages", "publications"].includes(currentStep);
  const itemType = currentStep === "topics" ? "topics" : 
                   currentStep === "regions" ? "regions" : 
                   currentStep === "languages" ? "languages" : "publications";

  return (
    <div className="container max-w-md mx-auto">
      <div className="flex justify-between">
        {leftButton}
        {rightButton}
      </div>
    </div>
  )
}

export default function OnboardingPage() {
  // Step and navigation state
  const [currentStep, setCurrentStep] = useState<Step>("welcome")
  const [stepIndex, setStepIndex] = useState(0)
  
  // Preferences state
  const [preferences, setPreferences] = useState<UserPreferences>({
    topics: [],
    regions: [],
    languages: [],
    publications: []
  })
  
  // Options from API
  const [options, setOptions] = useState<OnboardingOptions | null>(null)
  
  // Loading and error states
  const [isLoading, setIsLoading] = useState(true)
  const [isRedirecting, setIsRedirecting] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Validation error
  const [validationError, setValidationError] = useState<string | null>(null)
  
  // Auth and routing
  const { userStatus, isLoading: isUserLoading, setOnboardingComplete } = useUser()
  const { data: session, status: sessionStatus } = useSession()
  const router = useRouter()
  
  // Check auth state and fetch options
  useEffect(() => {
    // Skip if already redirecting
    if (isRedirecting) return
    
    // Handle redirects for already onboarded or unauthenticated users
    if (sessionStatus === "unauthenticated") {
      console.log("Onboarding page: User not authenticated, redirecting to auth")
      setIsRedirecting(true)
      router.replace("/auth")
      return
    }
    
    // Wait for user data to load
    if (sessionStatus === "loading" || isUserLoading) {
      console.log("Onboarding page: Still loading user data")
      return
    }
    
    // Check if user has already completed onboarding
    const hasCompletedOnboarding = userStatus?.has_completed_onboarding === true || session?.user?.has_completed_onboarding === true
    
    if (hasCompletedOnboarding) {
      console.log("Onboarding page: User has already completed onboarding, redirecting to home")
      setIsRedirecting(true)
      router.replace("/home")
      return
    }
    
    // Fetch options from API
    const loadOptions = async () => {
      try {
        console.log("Onboarding page: Fetching preference options")
        setIsLoading(true)
        const data = await fetchOnboardingOptions()
        setOptions(data)
        
        // Set smart defaults
        const defaultPrefs = getDefaultPreferences(data)
        setPreferences(defaultPrefs)
        
        console.log("Onboarding page: Options loaded, defaults set", defaultPrefs)
      } catch (err) {
        console.error("Onboarding page: Failed to load options", err)
        setError("Failed to load options. Please try again.")
      } finally {
        setIsLoading(false)
      }
    }
    
    loadOptions()
  }, [sessionStatus, userStatus, isUserLoading, session, router, isRedirecting])
  
  // Navigation handlers
  const goToNextStep = () => {
    // Clear any validation errors
    setValidationError(null)
    
    // Validate current step
    if (currentStep === "topics" && preferences.topics.length === 0) {
      setValidationError("Please select at least one topic")
      return
    }
    
    if (currentStep === "regions" && preferences.regions.length === 0) {
      setValidationError("Please select at least one region")
      return
    }
    
    if (currentStep === "languages" && preferences.languages.length === 0) {
      setValidationError("Please select at least one language")
      return
    }
    
    // Handle special case for the final step
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
  
  // Update preferences
  const updatePreferences = (key: keyof UserPreferences, value: any) => {
    setValidationError(null)
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }))
  }
  
  // Submit final preferences
  const submitPreferences = async () => {
    try {
      console.log("Onboarding page: Submitting preferences", preferences)
      setIsSubmitting(true)
      setError(null)
      
      await saveUserPreferences(preferences)
      
      // Update user context
      setOnboardingComplete(true)
      
      // Go to final step
      setCurrentStep("finish")
      setStepIndex(STEPS.indexOf("finish"))
      
      console.log("Onboarding page: Preferences saved successfully")
    } catch (err) {
      console.error("Onboarding page: Failed to save preferences", err)
      setError("Failed to save preferences. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }
  
  // Handle finish
  const finishOnboarding = () => {
    router.replace("/home")
  }
  
  // Loading state
  if (isLoading || !options || isRedirecting) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-4">
        <LogoHorizontal width={180} priority />
        <div className="mt-8 flex flex-col items-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-muted-foreground">
            {isRedirecting ? "Taking you to the right place..." : "Loading your personalization options..."}
          </p>
        </div>
      </div>
    )
  }
  
  // Progress percentage
  const progress = Math.max(
    5, 
    Math.min(100, ((stepIndex / (STEPS.length - 1)) * 100))
  )
  
  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header - now fixed */}
      <header className="fixed top-0 left-0 right-0 z-10 bg-background p-4 border-b shadow-sm">
        <div className="container max-w-md mx-auto">
          <div className="flex justify-center mb-4">
            <LogoHorizontal width={120} priority />
          </div>
          <div className="flex items-center gap-2">
            <Progress 
              value={progress} 
              className="h-1.5 bg-muted" 
            />
            <span className="text-xs text-muted-foreground w-12 text-right">
              {Math.round(progress)}%
            </span>
          </div>
        </div>
      </header>
      
      {/* Main content - add top padding to account for fixed header */}
      <main className="flex-1 container max-w-md mx-auto px-4 py-6 pb-24 pt-28">
        {error && (
          <div className="bg-destructive/10 text-destructive p-3 rounded-md mb-6">
            {error}
          </div>
        )}
        
        {validationError && (
          <div className="bg-destructive/10 text-destructive p-3 rounded-md mb-6">
            {validationError}
          </div>
        )}
        
        {/* Step content - use relative positioning to allow content to push container height */}
        <div className="relative">
          {currentStep === "welcome" && (
            <WelcomeStep />
          )}
          
          {currentStep === "topics" && options && (
            <TopicsStep 
              topics={options.topics}
              selectedTopics={preferences.topics}
              onChange={(selected) => updatePreferences('topics', selected)}
              error={validationError}
            />
          )}
          
          {currentStep === "regions" && options && (
            <RegionsStep
              regions={options.regions}
              selectedRegions={preferences.regions}
              onChange={(selected) => updatePreferences('regions', selected)}
              error={validationError}
            />
          )}
          
          {currentStep === "languages" && options && (
            <LanguagesStep
              languages={options.languages}
              selectedLanguages={preferences.languages}
              onChange={(selected) => updatePreferences('languages', selected)}
              error={validationError}
            />
          )}
          
          {currentStep === "publications" && options && (
            <PublicationsStep
              publications={options.publications}
              selectedPublications={preferences.publications}
              onChange={(selected) => updatePreferences('publications', selected)}
              error={validationError}
            />
          )}
          
          {currentStep === "finish" && (
            <FinishStep />
          )}
        </div>
      </main>
      
      {/* Fixed bottom navigation - now centralized here with reduced vertical padding */}
      <div className="fixed bottom-0 left-0 right-0 border-t bg-background py-3 px-4 shadow-sm">
        <StepNavigation
          currentStep={currentStep}
          onNext={goToNextStep}
          onBack={goToPrevStep}
          isSubmitting={isSubmitting}
          isFinalStep={currentStep === "publications"}
          isFirstStep={currentStep === "welcome"}
          selectionCount={
            currentStep === "topics" ? preferences.topics.length :
            currentStep === "regions" ? preferences.regions.length :
            currentStep === "languages" ? preferences.languages.length :
            currentStep === "publications" ? preferences.publications.length : 0
          }
        />
      </div>
    </div>
  )
}