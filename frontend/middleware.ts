import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { getToken } from "next-auth/jwt"

export async function middleware(request: NextRequest) {
  // Get the path
  const path = request.nextUrl.pathname
  
  // Define public routes that don't require authentication
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

  // Define protected routes that require authentication
  const isProtectedPath = !isPublicPath
  
  // Get the token from the request
  const token = await getToken({ req: request })
  const isAuthenticated = !!token

  // Log for debugging
  console.log(`Middleware: Path ${path}, isAuthenticated: ${isAuthenticated}, isPublicPath: ${isPublicPath}`)

  // --- SIMPLIFIED REDIRECT LOGIC ---
  
  // Only redirect unauthenticated users from protected routes to auth
  if (!isAuthenticated && isProtectedPath) {
    console.log(`Middleware: Redirecting unauthenticated user from ${path} to /auth`)
    return NextResponse.redirect(new URL("/auth", request.url))
  }
  
  // Don't handle any other redirects here - let client components handle them
  // This avoids conflicts with the SessionRedirect component
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
