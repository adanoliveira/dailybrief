import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { getToken } from "next-auth/jwt"

export async function middleware(request: NextRequest) {
  // Get the path
  const path = request.nextUrl.pathname
  
  // Check for special query parameters
  const searchParams = request.nextUrl.searchParams
  const skipChecks = 
    searchParams.get('skip_check') === 'true' || 
    searchParams.get('force') === 'true' ||
    searchParams.get('new_session') === 'true'

  // If any bypass parameters are present, skip all checks
  if (skipChecks) {
    console.log(`Middleware: Skip parameter detected, allowing access to ${path}`)
    return NextResponse.next()
  }

  // Define route types
  const isPublicPath = 
    path.startsWith("/_next") ||
    path.startsWith("/api") ||
    path === "/auth" ||
    path.startsWith("/auth/") ||
    path === "/terms" ||
    path === "/privacy" ||
    path === "/" ||
    path.endsWith(".svg") ||
    path.endsWith(".png") ||
    path.endsWith(".jpg") ||
    path.endsWith(".ico") ||
    path.endsWith(".json")

  const isLoadingCheckPage = path === "/loading-check"
  const isOnboardingPage = path.startsWith("/onboarding")
  const isAuthenticatedPath = !isPublicPath && !isLoadingCheckPage && !isOnboardingPage

  // Get the token from the request
  const token = await getToken({ req: request })
  
  console.log(`Middleware: Path ${path}, isAuthenticated: ${!!token}, hasCompletedOnboarding: ${token?.has_completed_onboarding}`)

  // --- MAIN REDIRECT LOGIC ---
  
  // 1. Access control: Unauthenticated users can only access public routes and auth
  if (!token && isAuthenticatedPath) {
    console.log(`Middleware: Redirecting unauthenticated user from ${path} to /auth`)
    return NextResponse.redirect(new URL("/auth", request.url))
  }

  // 2. Loading check is special - always allow if user is authenticated
  if (token && isLoadingCheckPage) {
    console.log(`Middleware: Allowing access to loading-check page`)
    return NextResponse.next()
  }
  
  // 3. Direct authenticated users away from auth pages
  if (token && path === "/auth") {
    console.log(`Middleware: Redirecting authenticated user from /auth to /loading-check`)
    return NextResponse.redirect(new URL("/loading-check", request.url))
  }

  // 4. Handle onboarding check only for authenticated protected routes
  const hasCompletedOnboarding = token?.has_completed_onboarding === true
  
  if (token && !hasCompletedOnboarding && isAuthenticatedPath && !isOnboardingPage) {
    console.log(`Middleware: Redirecting to onboarding: ${path} → /onboarding`)
    return NextResponse.redirect(new URL("/onboarding", request.url))
  }

  // 5. Root path handling - redirect to appropriate place
  if (path === "/") {
    if (token) {
      return NextResponse.redirect(new URL("/loading-check", request.url))
    } else {
      return NextResponse.redirect(new URL("/auth", request.url))
    }
  }

  // Allow all other requests
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
