import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  const token = request.cookies.get("next-auth.session-token")?.value
  const isAuthPage = request.nextUrl.pathname === "/auth" || 
                     request.nextUrl.pathname.startsWith("/auth/") ||
                     request.nextUrl.pathname === "/terms" ||
                     request.nextUrl.pathname === "/privacy"
  const isOnboardingPage = request.nextUrl.pathname.startsWith("/onboarding")
  const isTestPage = request.nextUrl.pathname.startsWith("/test")

  // If the user is not authenticated and trying to access a protected route
  if (
    !token &&
    !isAuthPage &&
    !isTestPage &&
    !request.nextUrl.pathname.startsWith("/_next") &&
    !request.nextUrl.pathname.startsWith("/api") &&
    request.nextUrl.pathname !== "/" &&
    !request.nextUrl.pathname.endsWith(".svg") && // Exclude SVG files
    !request.nextUrl.pathname.endsWith(".png") && // Exclude PNG files
    !request.nextUrl.pathname.endsWith(".jpg") && // Exclude JPG files
    !request.nextUrl.pathname.endsWith(".ico") && // Exclude ICO files
    !request.nextUrl.pathname.endsWith(".json") // Exclude JSON files (for manifest)
  ) {
    return NextResponse.redirect(new URL("/auth", request.url))
  }

  // If the user is authenticated but trying to access auth pages
  if (token && isAuthPage) {
    return NextResponse.redirect(new URL("/home", request.url))
  }

  // If the user is authenticated but hasn't completed onboarding
  // This would require checking a user preference in a real app
  // For now, we'll use a simple cookie check
  const hasCompletedOnboarding = request.cookies.get("onboarding_completed")?.value === "true"

  if (
    token &&
    !hasCompletedOnboarding &&
    !isOnboardingPage &&
    !isTestPage &&
    !request.nextUrl.pathname.startsWith("/_next") &&
    !request.nextUrl.pathname.startsWith("/api") &&
    !request.nextUrl.pathname.endsWith(".svg") && // Exclude SVG files
    !request.nextUrl.pathname.endsWith(".png") && // Exclude PNG files
    !request.nextUrl.pathname.endsWith(".jpg") && // Exclude JPG files
    !request.nextUrl.pathname.endsWith(".ico") && // Exclude ICO files
    !request.nextUrl.pathname.endsWith(".json") // Exclude JSON files (for manifest)
  ) {
    return NextResponse.redirect(new URL("/onboarding", request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - sw.js (service worker)
     */
    "/((?!_next/static|_next/image|favicon.ico|sw.js).*)",
  ],
}
