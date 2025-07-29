"use client"

import { MobileNav } from "@/components/mobile-nav"
import { useNavigationTracking } from "@/hooks/use-navigation-tracking"
import { useBackgroundSync } from "@/lib/use-local-data"
import { usePathname } from "next/navigation"

export function AuthenticatedShell() {
  const pathname = usePathname()
  const isArticlePage = pathname?.includes('/article/')
  const isDigestPage = pathname?.includes('/digest/')
  
  // Track navigation for contextual back buttons
  useNavigationTracking()

  // Enable background sync for all authenticated pages (runs once)
  useBackgroundSync(10 * 60 * 1000) // 10 minutes

  return (
    <>
      {!isArticlePage && !isDigestPage && <MobileNav />}
    </>
  )
} 