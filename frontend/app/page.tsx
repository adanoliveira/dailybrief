"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useUser } from "@/lib/user-context"
import { LogoHorizontal } from "@/components/ui/logo"

export default function HomePage() {
  const { data: session, status: sessionStatus } = useSession()
  const { userStatus, isLoading: isUserLoading } = useUser()
  const router = useRouter()
  const [isRedirecting, setIsRedirecting] = useState(false)

  useEffect(() => {
    // Skip if we're already in the process of redirecting
    if (isRedirecting) return;

    // Log for debugging
    console.log("Root page: Checking auth status", {
      sessionStatus,
      userOnboarded: session?.user?.has_completed_onboarding,
      contextOnboarded: userStatus?.has_completed_onboarding,
      isUserLoading
    })
    
    // Wait for all data to be loaded
    if (sessionStatus === "loading" || isUserLoading) {
      console.log("Root page: Still loading session or user data, waiting...")
      return
    }

    // Handle unauthenticated users - redirect to auth
    if (sessionStatus === "unauthenticated") {
      console.log("Root page: User is not authenticated, redirecting to auth")
      setIsRedirecting(true)
      router.replace("/auth")
      return
    }

    // Handle authenticated users
    if (sessionStatus === "authenticated") {
      setIsRedirecting(true)
      
      // First check the session for onboarding status
      if (session?.user?.has_completed_onboarding === true) {
        console.log("Root page: Session indicates onboarding completed, redirecting to home")
        router.replace("/home")
        return
      }
      
      // Then check the user context
      if (userStatus) {
        if (userStatus.has_completed_onboarding === true) {
          console.log("Root page: Context indicates onboarding completed, redirecting to home")
          router.replace("/home") 
        } else {
          console.log("Root page: Context indicates onboarding not completed, redirecting to onboarding")
          router.replace("/onboarding")
        }
        return
      }
      
      // Default to onboarding if we can't determine status
      console.log("Root page: No user status available, defaulting to onboarding")
      router.replace("/onboarding")
    }
  }, [sessionStatus, session, userStatus, isUserLoading, router, isRedirecting])

  // Show a minimal loading screen while determining redirect
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <LogoHorizontal width={200} priority />
      <div className="mt-8 animate-pulse text-muted-foreground">
        Loading...
      </div>
    </div>
  )
}
