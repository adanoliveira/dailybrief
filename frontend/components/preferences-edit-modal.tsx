"use client"

import { useState, useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"
import { Progress } from "@/components/ui/progress"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { Button } from "@/components/ui/button"
import { X, AlertTriangle } from "lucide-react"
import { 
  fetchOnboardingOptions, 
  saveUserPreferences,
  getDefaultPreferences,
  UserPreferences,
  OnboardingOptions
} from "@/lib/onboarding-service"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

// Import step components
import { TopicsStep } from "@/components/onboarding/topics-step"
import { RegionsStep } from "@/components/onboarding/regions-step"
import { LanguagesStep } from "@/components/onboarding/languages-step"
import { PublicationsStep } from "@/components/onboarding/publications-step"

// Steps for preferences editing (excluding welcome and finish)
type Step = "topics" | "regions" | "languages" | "publications"
const STEPS: Step[] = ["topics", "regions", "languages", "publications"]

// Step names for display
const STEP_NAMES: Record<Step, string> = {
  topics: "Topics",
  regions: "Regions", 
  languages: "Languages",
  publications: "Sources"
}

interface PreferencesEditModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentPreferences: UserPreferences | null
  onPreferencesUpdated: (preferences: UserPreferences) => void
}

// Navigation component for the modal
function StepNavigation({ 
  currentStep, 
  onNext, 
  onBack, 
  onCancel,
  isSubmitting = false,
  isFinalStep = false,
  isFirstStep = false,
  isValid = true
}: { 
  currentStep: Step,
  onNext: () => void, 
  onBack: () => void,
  onCancel: () => void,
  isSubmitting?: boolean,
  isFinalStep?: boolean,
  isFirstStep?: boolean,
  isValid?: boolean
}) {
  return (
    <div className="flex justify-between items-center">
      <Button 
        variant="ghost"
        onClick={onCancel}
        disabled={isSubmitting}
        className="text-muted-foreground hover:text-foreground"
      >
        Cancel
      </Button>
      
      <div className="flex gap-3">
        <Button 
          variant="outline"
          onClick={onBack} 
          disabled={isFirstStep || isSubmitting}
        >
          Back
        </Button>
        
        <Button 
          onClick={onNext}
          disabled={isSubmitting || !isValid}
          className="min-w-[120px]"
        >
          {isSubmitting ? (
            <>
              <LoadingSpinner className="mr-2 h-4 w-4" />
              Saving...
            </>
          ) : isFinalStep ? "Save Changes" : "Continue"}
        </Button>
      </div>
    </div>
  )
}

export function PreferencesEditModal({ 
  open, 
  onOpenChange, 
  currentPreferences, 
  onPreferencesUpdated 
}: PreferencesEditModalProps) {
  // Step and navigation state
  const [currentStep, setCurrentStep] = useState<Step>("topics")
  const [stepIndex, setStepIndex] = useState(0)
  
  // Preferences state (working copy)
  const [preferences, setPreferences] = useState<UserPreferences>({
    topics: [],
    regions: [],
    languages: [],
    publications: []
  })
  
  // Original preferences for comparison
  const [originalPreferences, setOriginalPreferences] = useState<UserPreferences>({
    topics: [],
    regions: [],
    languages: [],
    publications: []
  })
  
  // Options from API
  const [options, setOptions] = useState<OnboardingOptions | null>(null)
  
  // Loading and error states
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [validationError, setValidationError] = useState<string | null>(null)
  
  // Unsaved changes alert
  const [showUnsavedAlert, setShowUnsavedAlert] = useState(false)
  const [pendingClose, setPendingClose] = useState(false)

  // Initialize when modal opens
  useEffect(() => {
    if (open) {
      initializeModal()
    } else {
      // Reset state when modal closes
      setCurrentStep("topics")
      setStepIndex(0)
      setError(null)
      setValidationError(null)
      setShowUnsavedAlert(false)
      setPendingClose(false)
    }
  }, [open, currentPreferences])

  const initializeModal = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Load onboarding options
      const data = await fetchOnboardingOptions()
      setOptions(data)
      
      // Set preferences (use current or defaults)
      const initialPrefs = currentPreferences || getDefaultPreferences(data)
      setPreferences(initialPrefs)
      setOriginalPreferences(initialPrefs)
      
    } catch (err) {
      console.error("Failed to load options", err)
      setError("Failed to load options. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  // Check if preferences have changed
  const hasChanges = () => {
    return JSON.stringify(preferences) !== JSON.stringify(originalPreferences)
  }

  // Handle close attempts
  const handleCloseAttempt = () => {
    if (hasChanges()) {
      setShowUnsavedAlert(true)
      setPendingClose(true)
    } else {
      onOpenChange(false)
    }
  }

  // Confirm close without saving
  const handleConfirmClose = () => {
    setShowUnsavedAlert(false)
    setPendingClose(false)
    onOpenChange(false)
  }

  // Cancel close and continue editing
  const handleCancelClose = () => {
    setShowUnsavedAlert(false)
    setPendingClose(false)
  }

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
    
    // Handle final step (publications)
    if (currentStep === "publications") {
      submitPreferences()
      return
    }
    
    // Regular navigation
    const nextIndex = stepIndex + 1
    if (nextIndex < STEPS.length) {
      setStepIndex(nextIndex)
      setCurrentStep(STEPS[nextIndex])
    }
  }
  
  const goToPrevStep = () => {
    setValidationError(null)
    
    const prevIndex = stepIndex - 1
    if (prevIndex >= 0) {
      setStepIndex(prevIndex)
      setCurrentStep(STEPS[prevIndex])
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
  
  // Submit preferences
  const submitPreferences = async () => {
    try {
      setIsSubmitting(true)
      setError(null)
      
      await saveUserPreferences(preferences)
      
      // Update parent component
      onPreferencesUpdated(preferences)
      
      // Close modal
      onOpenChange(false)
      
    } catch (err) {
      console.error("Failed to save preferences", err)
      setError("Failed to save preferences. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  // Progress percentage
  const progress = Math.max(
    5, 
    Math.min(100, ((stepIndex / (STEPS.length - 1)) * 100))
  )

  return (
    <>
      <Dialog open={open} onOpenChange={handleCloseAttempt}>
        <DialogContent className="w-screen h-screen overflow-hidden flex flex-col p-0 gap-0 sm:w-full sm:h-full sm:max-w-2xl sm:max-h-[800px] sm:rounded-lg sm:border">
        
          {/* Header */}
          <DialogHeader className="px-4 py-4 border-b bg-background">
            <div className="container max-w-md mx-auto">
              <DialogTitle className="mb-3">Edit News Preferences</DialogTitle>
              <DialogDescription>
                Update your topics, regions, languages, and news sources
              </DialogDescription>
              
              {/* Progress bar */}
              <div className="flex items-center gap-3 mt-4">
                <Progress 
                  value={progress} 
                  className="h-1.5 flex-1" 
                />
                <span className="text-xs text-muted-foreground w-12 text-right">
                  {Math.round(progress)}%
                </span>
              </div>
            </div>
          </DialogHeader>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="container max-w-md mx-auto px-4 py-6 pb-24">
              {isLoading || !options ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <LoadingSpinner size="lg" />
                  <p className="mt-4 text-muted-foreground">
                    Loading your preferences...
                  </p>
                </div>
              ) : (
                <>
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
                  
                  {/* Step content */}
                  <div className="relative">
                    {currentStep === "topics" && (
                      <TopicsStep 
                        topics={options.topics}
                        selectedTopics={preferences.topics}
                        onChange={(selected) => updatePreferences('topics', selected)}
                        error={validationError}
                      />
                    )}
                    
                    {currentStep === "regions" && (
                      <RegionsStep
                        regions={options.regions}
                        selectedRegions={preferences.regions}
                        onChange={(selected) => updatePreferences('regions', selected)}
                        error={validationError}
                      />
                    )}
                    
                    {currentStep === "languages" && (
                      <LanguagesStep
                        languages={options.languages}
                        selectedLanguages={preferences.languages}
                        onChange={(selected) => updatePreferences('languages', selected)}
                        error={validationError}
                      />
                    )}
                    
                    {currentStep === "publications" && (
                      <PublicationsStep
                        publications={options.publications}
                        topics={options.topics}
                        regions={options.regions}
                        selectedTopics={preferences.topics}
                        selectedRegions={preferences.regions}
                        selectedPublications={preferences.publications}
                        onChange={(selected) => updatePreferences('publications', selected)}
                        error={validationError}
                      />
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

                    {/* Footer navigation */}
          {!isLoading && options && (
            <div className="border-t bg-background py-3 px-4 shadow-sm">
              <div className="container max-w-md mx-auto">
                <StepNavigation
                  currentStep={currentStep}
                  onNext={goToNextStep}
                  onBack={goToPrevStep}
                  onCancel={handleCloseAttempt}
                  isSubmitting={isSubmitting}
                  isFinalStep={currentStep === "publications"}
                  isFirstStep={currentStep === "topics"}
                  isValid={
                    currentStep === "topics" ? preferences.topics.length > 0 :
                    currentStep === "regions" ? preferences.regions.length > 0 :
                    currentStep === "languages" ? preferences.languages.length > 0 :
                    preferences.publications.length > 0
                  }
                />
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Unsaved changes alert */}
      <AlertDialog open={showUnsavedAlert} onOpenChange={setShowUnsavedAlert}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Unsaved Changes
            </AlertDialogTitle>
            <AlertDialogDescription>
              You have unsaved changes to your preferences. Are you sure you want to close without saving? Your changes will be lost.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelClose}>
              Continue Editing
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmClose} className="bg-destructive hover:bg-destructive/90">
              Discard Changes
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
} 