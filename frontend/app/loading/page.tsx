"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { Skeleton } from "@/components/ui/skeleton"
import { getUserPreferences } from "@/lib/accounts-service"

export default function LoadingPage() {
  const { data: session, status, update: updateSession } = useSession()
  const [redirectTarget, setRedirectTarget] = useState<string | null>(null)
  
  // Check localStorage and authentication status once
  useEffect(() => {
    const checkUserStatus = async () => {
      // Wait for session to load
      if (status === "loading") return
      
      console.log("Loading page: Checking user status")
      
      // Not logged in? Go to auth
      if (status === "unauthenticated") {
        console.log("Loading page: User not authenticated, redirecting to /auth")
        window.location.replace("/auth")
        return
      }
      
      // SIMPLIFY: Direct check of localStorage first
      const hasDoneOnboarding = localStorage.getItem('has_completed_onboarding') === 'true'
      if (hasDoneOnboarding) {
        console.log("Loading page: User has completed onboarding according to localStorage")
        
        // Try to update session for future consistency
        try {
          await updateSession({ has_completed_onboarding: true })
        } catch (error) {
          console.error("Failed to update session, but proceeding", error)
        }
        
        // Set state to trigger UI update then redirect
        setRedirectTarget('/home')
        setTimeout(() => window.location.replace('/home'), 100)
        return
      }
      
      // Check if user has completed onboarding via session
      if (session?.user?.has_completed_onboarding) {
        console.log("Loading page: User has completed onboarding according to session")
        localStorage.setItem('has_completed_onboarding', 'true')
        setRedirectTarget('/home')
        setTimeout(() => window.location.replace('/home'), 100)
        return
      }
      
      // Check API as last resort
      try {
        console.log("Loading page: Checking API for user preferences")
        const preferences = await getUserPreferences()
        
        if (preferences?.topics && preferences.topics.length > 0) {
          console.log("Loading page: User has completed onboarding according to API")
          localStorage.setItem('has_completed_onboarding', 'true')
          
          // Try to update session
          await updateSession({ has_completed_onboarding: true })
          
          setRedirectTarget('/home')
          setTimeout(() => window.location.replace('/home'), 100)
        } else {
          console.log("Loading page: User needs to complete onboarding")
          setRedirectTarget('/onboarding')
          setTimeout(() => window.location.replace('/onboarding'), 100)
        }
      } catch (error) {
        console.error("Loading page: Error checking preferences:", error)
        // Default to onboarding on error
        setRedirectTarget('/onboarding')
        setTimeout(() => window.location.replace('/onboarding'), 100)
      }
    }
    
    checkUserStatus()
  }, [status, session, updateSession])
  
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-background">
      <div className="w-full max-w-md px-4">
        <div className="space-y-4 text-center">
          <h2 className="text-2xl font-bold">DailyBrief</h2>
          <p className="text-muted-foreground">
            {redirectTarget === '/home' 
              ? "Loading your personalized news feed..." 
              : "Preparing your setup..."}
          </p>
          
          {/* Indeterminate spinner instead of progress bar */}
          <div className="flex justify-center my-8">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
          </div>
        </div>

        <div className="mt-8 space-y-3">
          <Skeleton className="h-12 w-full rounded-md" />
          <Skeleton className="h-32 w-full rounded-md" />
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-24 w-full rounded-md" />
            <Skeleton className="h-24 w-full rounded-md" />
          </div>
          <Skeleton className="h-32 w-full rounded-md" />
          <div className="grid grid-cols-3 gap-2">
            <Skeleton className="h-8 w-full rounded-md" />
            <Skeleton className="h-8 w-full rounded-md" />
            <Skeleton className="h-8 w-full rounded-md" />
          </div>
        </div>
      </div>
    </div>
  )
} 