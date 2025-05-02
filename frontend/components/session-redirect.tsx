"use client"

import { useSession } from "next-auth/react"
import { useRouter, usePathname } from "next/navigation"
import { useEffect } from "react"

// Extend the user type to include our custom fields
interface ExtendedUser {
  id: string;
  name?: string | null;
  email?: string | null;
  image?: string | null;
  django_user_id?: number;
  django_token?: string;
  has_completed_onboarding?: boolean;
}

interface ExtendedSession {
  user?: ExtendedUser;
  expires: string;
}

export default function SessionRedirect() {
  const { data: session, status } = useSession() as { 
    data: ExtendedSession | null;
    status: "loading" | "authenticated" | "unauthenticated"
  }
  const router = useRouter()
  const pathname = usePathname() || "/"
  
  useEffect(() => {
    // Only run on client
    if (typeof window === "undefined") return
    
    console.log("SessionRedirect checking auth status:", status, "path:", pathname);
    
    // If we're loading, don't do anything yet
    if (status === "loading") return
    
    // If the user is authenticated
    if (status === "authenticated" && session?.user) {
      console.log("User is authenticated, session data:", JSON.stringify({
        user_data: session.user ? "exists" : "missing",
        onboarding_status: session.user.has_completed_onboarding
      }));
      
      // Routes that should redirect to /home or /onboarding for authenticated users
      const publicRoutes = ["/", "/auth", "/auth/verify-request", "/auth/error"]
      
      if (publicRoutes.includes(pathname)) {
        // Check if user has completed onboarding
        if (session.user.has_completed_onboarding) {
          console.log("Redirecting authenticated user to /home");
          router.push("/home")
        } else {
          console.log("Redirecting authenticated user to /onboarding");
          router.push("/onboarding")
        }
      }
    } 
    // If the user is not authenticated
    else if (status === "unauthenticated") {
      console.log("User is unauthenticated");
      
      // Routes that require authentication
      const protectedRoutes = [
        "/home", 
        "/onboarding",
        "/profile",
        "/settings",
        "/world",
        "/article",
        "/digest"
      ]
      
      // Check if the current path starts with any protected route
      const isProtectedRoute = protectedRoutes.some(route => 
        pathname === route || pathname.startsWith(`${route}/`)
      )
      
      if (isProtectedRoute) {
        console.log("Unauthenticated user trying to access protected route, redirecting to /auth");
        router.push("/auth")
      }
    }
  }, [status, session, router, pathname])
  
  // This component doesn't render anything
  return null
} 