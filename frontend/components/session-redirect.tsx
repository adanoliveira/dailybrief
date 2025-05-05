"use client"

import { useSession } from "next-auth/react"
import { usePathname } from "next/navigation"
import { useEffect, useState, ReactNode, useRef } from "react"
import { Skeleton } from "@/components/ui/skeleton"

interface SessionRedirectProps {
  children: ReactNode;
}

export default function SessionRedirect({ children }: SessionRedirectProps) {
  const { status, data: session, update: updateSession } = useSession()
  const pathname = usePathname() || "/"
  const [isLoading, setIsLoading] = useState(true)
  const [isRedirecting, setIsRedirecting] = useState(false)
  const hasUpdatedSession = useRef(false)
  
  useEffect(() => {
    // Only run on client
    if (typeof window === "undefined") return
    
    // If we're already redirecting, don't do anything
    if (isRedirecting) return
    
    console.log("SessionRedirect: Auth check on", pathname)
    
    // Always show loading initially
    setIsLoading(true)
    
    // If we're still loading the session, wait
    if (status === "loading") return
    
    // List of public routes that don't require authentication
    const publicRoutes = ["/", "/auth", "/auth/verify-request", "/auth/error"]
    
    // List of auth-only routes that should redirect to /loading for initial check
    const protectedRoutes = [
      "/home", 
      "/onboarding",
      "/profile",
      "/settings",
      "/world",
      "/article",
      "/digest"
    ]
    
    const isPublicRoute = publicRoutes.includes(pathname)
    const isProtectedRoute = protectedRoutes.some(route => 
      pathname === route || pathname.startsWith(`${route}/`)
    )
    
    // Check if user has completed onboarding according to localStorage
    const hasDoneOnboarding = localStorage.getItem('has_completed_onboarding') === 'true'
    
    // IMPORTANT: Only update session once to prevent update loops
    if (hasDoneOnboarding && session?.user && !session.user.has_completed_onboarding && !hasUpdatedSession.current) {
      console.log("SessionRedirect: Fixing session based on localStorage (one-time update)")
      hasUpdatedSession.current = true
      updateSession({ has_completed_onboarding: true })
        .catch(err => console.error("Error updating session:", err))
    }
    
    // Loading page handles its own redirects, don't interfere
    if (pathname === "/loading") {
      console.log("SessionRedirect: On loading page, not redirecting")
      setIsLoading(false)
      return
    }
    
    // Onboarding page handles its own redirects if localStorage says completed
    if (pathname === "/onboarding" && hasDoneOnboarding) {
      console.log("SessionRedirect: User already completed onboarding, will be handled by onboarding page")
      setIsLoading(false)
      return
    }
    
    // Case 1: Unauthenticated user trying to access protected route
    if (status === "unauthenticated" && isProtectedRoute) {
      console.log("SessionRedirect: Unauthenticated user on protected route, redirecting to /auth")
      setIsRedirecting(true)
      window.location.replace("/auth")
      return
    }
    
    // Case 2: Authenticated user on public route
    if (status === "authenticated" && isPublicRoute) {
      // If localStorage says user has completed onboarding, go straight to home
      if (hasDoneOnboarding) {
        console.log("SessionRedirect: User has completed onboarding (localStorage), going to home")
        setIsRedirecting(true)
        window.location.replace("/home")
        return
      }
      
      console.log("SessionRedirect: Authenticated user on public route, redirecting to /loading")
      setIsRedirecting(true)
      window.location.replace("/loading")
      return
    }
    
    // All other cases: Show the page content after a brief delay
    setTimeout(() => {
      setIsLoading(false)
    }, 100)
  }, [status, pathname, session, updateSession, isRedirecting])
  
  // Simple loading spinner for brief transitions
  if (isLoading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    )
  }
  
  // When not loading, show the children
  return <>{children}</>
} 