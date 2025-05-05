"use client"

import { useSession } from "next-auth/react"
import { usePathname, useRouter } from "next/navigation"
import { useEffect, useState, useRef, ReactNode } from "react"
import { LoadingState } from "@/components/ui/loading-state"

interface SessionRedirectProps {
  children: ReactNode;
}

/**
 * SessionRedirect - Handles basic authentication protection
 * 
 * This component has a reduced scope: it only redirects unauthenticated users 
 * away from protected routes. All other redirection logic (like onboarding status)
 * is now handled by individual pages.
 */
export default function SessionRedirect({ children }: SessionRedirectProps) {
  const { status: sessionStatus } = useSession()
  const pathname = usePathname() || "/"
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const lastRedirectTime = useRef<number>(0)
  const isRedirecting = useRef<boolean>(false)
  
  // Function to handle redirects with rate limiting
  const handleRedirect = (destination: string, reason: string) => {
    const now = Date.now()
    // Prevent redirect if we've redirected in the last 2 seconds or already redirecting
    if (isRedirecting.current || (now - lastRedirectTime.current < 2000)) {
      console.log(`SessionRedirect: Skipping redirect to ${destination} - too frequent`)
      return
    }
    
    console.log(`SessionRedirect: Redirecting to ${destination} - ${reason}`)
    isRedirecting.current = true
    lastRedirectTime.current = now
    
    // Use setTimeout to prevent immediate navigation
    // This helps prevent potential redirect loops
    setTimeout(() => {
      router.replace(destination)
      // Reset redirecting flag after timeout
      setTimeout(() => {
        isRedirecting.current = false
      }, 500)
    }, 100)
  }
  
  useEffect(() => {
    // Only run on client
    if (typeof window === "undefined") return
    
    console.log("SessionRedirect: Basic protection check", {
      path: pathname,
      authStatus: sessionStatus,
    })
    
    // If session is still loading, wait
    if (sessionStatus === "loading") {
      console.log("SessionRedirect: Session still loading, waiting...")
      return
    }
    
    // Define public routes that don't require authentication
    const isPublicRoute = 
      pathname === "/" || 
      pathname === "/auth" || 
      pathname.startsWith("/auth/") ||
      pathname === "/terms" || 
      pathname === "/privacy" ||
      pathname.endsWith(".svg") || 
      pathname.endsWith(".png") || 
      pathname.endsWith(".jpg") ||
      pathname.endsWith(".ico") ||
      pathname.endsWith(".json")
    
    // Very basic protection: only redirect unauthenticated users from protected routes
    if (sessionStatus === "unauthenticated" && !isPublicRoute) {
      handleRedirect("/auth", "protected route to auth (unauthenticated)")
      return
    }
    
    // Otherwise, render the children
    console.log("SessionRedirect: No protection needed, rendering page")
    setIsLoading(false)
  }, [sessionStatus, pathname, router])
  
  // Show loading state while determining access
  if (isLoading) {
    return <LoadingState fullScreen message="Loading..." />
  }
  
  // When not loading, show the children
  return <>{children}</>
} 