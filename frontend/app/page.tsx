"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useUser } from "@/lib/user-context"
import { Button } from "@/components/ui/button"
import { HeroSection } from "@/components/hero-section"
import { WorldNewsFeed } from "@/components/world-news-feed"
import { LogoHorizontal } from "@/components/ui/logo"
import Link from "next/link"

export default function HomePage() {
  const { data: session, status: sessionStatus } = useSession()
  const { userStatus, isLoading: isUserLoading } = useUser()
  const router = useRouter()
  const [isRedirecting, setIsRedirecting] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

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

    // Mark loading as complete
    setIsLoading(false)

    // Handle unauthenticated users - show the landing page (no redirection)
    if (sessionStatus === "unauthenticated") {
      console.log("Root page: User is not authenticated, showing landing page")
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
  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center">
        <LogoHorizontal width={200} priority />
        <div className="mt-8 animate-pulse text-muted-foreground">
          Loading...
        </div>
      </div>
    )
  }

  // Show original landing page for unauthenticated users
  if (sessionStatus === "unauthenticated") {
    return (
      <main className="min-h-screen bg-background">
        <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
          <div className="container flex h-16 items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <LogoHorizontal priority />
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/auth">
                <Button variant="ghost" size="sm">
                  Sign In
                </Button>
              </Link>
              <Link href="/auth">
                <Button size="sm">Get Started</Button>
              </Link>
            </div>
          </div>
        </header>

        <HeroSection />
        <WorldNewsFeed publicMode={true} />
      </main>
    )
  }

  // Default loading screen (should rarely be seen)
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <LogoHorizontal width={200} priority />
      <div className="mt-8 text-muted-foreground">
        Preparing your experience...
      </div>
    </div>
  )
}
