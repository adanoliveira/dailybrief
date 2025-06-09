"use client"

import { usePathname } from "next/navigation"
import { useEffect } from "react"

export function useNavigationTracking() {
  const pathname = usePathname()

  useEffect(() => {
    // Don't track article pages as referrers
    if (pathname?.includes('/article/')) {
      return
    }

    // Only store /home and /world as valid referrers
    if (pathname === '/home' || pathname === '/world') {
      const referrerInfo = {
        label: getPageLabel(pathname),
        path: pathname
      }

      sessionStorage.setItem('article-referrer', JSON.stringify(referrerInfo))
    } else {
      // Clear any existing referrer for other pages
      sessionStorage.removeItem('article-referrer')
    }
  }, [pathname])
}

function getPageLabel(pathname: string | null): string {
  if (!pathname) return "Top Headlines"

  // Map common paths to user-friendly labels
  if (pathname === '/home') return "Home"
  if (pathname === '/headlines') return "Headlines" 
  if (pathname === '/world') return "Top Headlines"
  if (pathname === '/digest/latest') return "Digest"
  if (pathname.startsWith('/digest')) return "Digest"
  if (pathname === '/profile') return "Profile"
  
  // Generic fallback for other paths
  const pathSegments = pathname.split('/').filter(Boolean)
  if (pathSegments.length > 0) {
    const lastSegment = pathSegments[pathSegments.length - 1]
    return lastSegment.charAt(0).toUpperCase() + lastSegment.slice(1)
  }

  return "Top Headlines"
} 