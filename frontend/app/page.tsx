"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useUser } from "@/lib/user-context"
import { Button } from "@/components/ui/button"
import { HeroSection } from "@/components/hero-section"
import { WorldNewsFeed } from "@/components/world-news-feed"
import { PublicFeedCTA } from "@/components/public-feed-cta"
import { LogoHorizontal } from "@/components/ui/logo"
import { Badge } from "@/components/ui/badge"
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

    // Wait for all data to be loaded
    if (sessionStatus === "loading" || isUserLoading) {
      return
    }

    // Mark loading as complete
    setIsLoading(false)

    // Handle unauthenticated users - show the landing page (no redirection)
    if (sessionStatus === "unauthenticated") {
      return
    }

    // Handle authenticated users
    if (sessionStatus === "authenticated") {
      setIsRedirecting(true)
      
      // First check the session for onboarding status
      if (session?.user?.has_completed_onboarding === true) {
        router.replace("/home")
        return
      }
      
      // Then check the user context
      if (userStatus) {
        if (userStatus.has_completed_onboarding === true) {
          router.replace("/home") 
        } else {
          router.replace("/onboarding")
        }
        return
      }
      
      // Default to onboarding if we can't determine status
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
        <header className="sticky top-0 z-50 border-b bg-background">
          <div className="container flex h-16 items-center justify-between min-w-0">
            <Link href="/" className="flex items-center gap-2 shrink-0">
              <LogoHorizontal priority />
              <Badge variant="outline" className="text-xs border-amber-500/50 text-amber-700 dark:text-amber-300">
                v1.0.0-alpha
              </Badge>
            </Link>
            <div className="flex items-center gap-4 shrink-0">
              <Link href="/auth">
                <Button variant="ghost" size="sm">
                  Sign In
                </Button>
              </Link>
              {/* <Link href="/auth">
                <Button size="sm">Get Started</Button>
              </Link> */}
            </div>
          </div>
        </header>

        <HeroSection />
        <WorldNewsFeed publicMode={true} />
        <PublicFeedCTA />
        
        <footer className="border-t bg-background">
          <div className="container py-8 text-center">
            <div className="text-xs text-muted-foreground">
              DailyBrief v1.0.0-alpha • Built with ❤️ • Early Access Preview
            </div>
          </div>
        </footer>
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
