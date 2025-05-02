import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { getToken } from "next-auth/jwt"

export async function middleware(request: NextRequest) {
  // Get the path
  const path = request.nextUrl.pathname

  // Check if this is a protected path 
  const isAuthPage = path === "/auth" || 
                     path.startsWith("/auth/") ||
                     path === "/terms" ||
                     path === "/privacy"
  const isOnboardingPage = path.startsWith("/onboarding")
  const isTestPage = path.startsWith("/test")
  const isPublicPath = 
    path.startsWith("/_next") ||
    path.startsWith("/api") ||
    path === "/" ||
    path.endsWith(".svg") ||
    path.endsWith(".png") ||
    path.endsWith(".jpg") ||
    path.endsWith(".ico") ||
    path.endsWith(".json")

  // Get the token from the request
  const token = await getToken({ req: request })

  // If the user is not authenticated and trying to access a protected route
  if (!token && !isAuthPage && !isTestPage && !isPublicPath) {
    return NextResponse.redirect(new URL("/auth", request.url))
  }

  // If the user is authenticated but trying to access auth pages
  if (token && isAuthPage) {
    return NextResponse.redirect(new URL("/home", request.url))
  }

  // Check if the user has completed onboarding
  const hasCompletedOnboarding = token?.has_completed_onboarding === true

  // If the user is authenticated but hasn't completed onboarding
  if (
    token &&
    !hasCompletedOnboarding &&
    !isOnboardingPage &&
    !isTestPage &&
    !isPublicPath
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
