"use client"

import { MobileNav } from "@/components/mobile-nav"
import { NotificationPermission } from "@/components/notification-permission"
import { useNavigationTracking } from "@/hooks/use-navigation-tracking"
import { usePathname } from "next/navigation"

export function AuthenticatedShell() {
  const pathname = usePathname()
  const isArticlePage = pathname?.includes('/article/')
  const isDigestPage = pathname?.includes('/digest/')
  
  // Track navigation for contextual back buttons
  useNavigationTracking()

  return (
    <>
      <NotificationPermission />
      {!isArticlePage && !isDigestPage && <MobileNav />}
    </>
  )
} 