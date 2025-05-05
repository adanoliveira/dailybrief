"use client"

import { useEffect, useState, useRef } from "react"
import { useSession } from "next-auth/react"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { AlertCircle } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { useUser } from "@/lib/user-context"

export default function LoadingCheck() {
  // Initialize all hooks at the top level
  const { data: session } = useSession()
  const { userStatus, isLoading, error, refreshUserStatus } = useUser()
  const [showManualLinks, setShowManualLinks] = useState(false)
  const hasRedirected = useRef(false)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  // Show manual navigation links after 5 seconds as a fallback
  useEffect(() => {
    timerRef.current = setTimeout(() => {
      setShowManualLinks(true)
    }, 5000)

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [])

  // Check user status and redirect if needed
  useEffect(() => {
    console.log("LoadingCheck: Component mounted", {
      hasSession: !!session,
      hasUserStatus: !!userStatus,
      onboardingStatus: userStatus?.has_completed_onboarding
    })

    // If we've already started a redirect, don't do anything else
    if (hasRedirected.current) {
      console.log("LoadingCheck: Already redirected, no further action needed")
      return
    }

    // Wait for user status to be loaded
    if (isLoading || !userStatus) {
      console.log("LoadingCheck: User status still loading...")
      return
    }

    // Now that we have user status, decide where to redirect
    hasRedirected.current = true
    
    if (userStatus.has_completed_onboarding) {
      console.log("LoadingCheck: User has completed onboarding, redirecting to home")
      window.location.href = "/home?new_session=true"
    } else {
      console.log("LoadingCheck: User has NOT completed onboarding, redirecting to onboarding")
      window.location.href = "/onboarding?skip_check=true"
    }
  }, [session, userStatus, isLoading])

  // Render UI based on component state
  // All hooks are called before any conditional returns

  const renderError = () => (
    <div className="container py-6">
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
        <Alert variant="destructive" className="mb-6 max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error syncing your account</AlertTitle>
          <AlertDescription className="mt-2">
            We couldn't fetch your profile information. This could be a temporary issue.
          </AlertDescription>
        </Alert>
        
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">You can try:</p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Button variant="default" onClick={() => refreshUserStatus()}>
              Retry
            </Button>
            <Button variant="outline" onClick={() => window.location.href = "/onboarding?skip_check=true"}>
              Go to Onboarding
            </Button>
            <Button variant="outline" onClick={() => window.location.href = "/home?force=true"}>
              Go to Home Page
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderLoading = () => (
    <div className="container py-6">
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
        <h2 className="text-xl font-semibold mb-4">Checking your profile...</h2>
        <div className="w-full max-w-md space-y-6 mb-8">
          <Skeleton className="h-8 w-32 mx-auto" />
          <Skeleton className="h-4 w-3/4 mx-auto" />
          <Skeleton className="h-4 w-1/2 mx-auto" />
        </div>
        
        {showManualLinks && (
          <div className="mt-8 border-t pt-8 w-full max-w-md">
            <p className="text-sm text-muted-foreground mb-4">
              Taking longer than expected? Try these direct links:
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button variant="outline" size="sm" onClick={() => window.location.href = "/onboarding?skip_check=true"}>
                Go to Onboarding
              </Button>
              <Button variant="outline" size="sm" onClick={() => window.location.href = "/home?force=true"}>
                Go to Home Page
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )

  // Now return the appropriate UI based on state
  if (error) {
    return renderError()
  }
  
  return renderLoading()
} 