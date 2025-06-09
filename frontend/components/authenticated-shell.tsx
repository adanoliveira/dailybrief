"use client"

import { MobileNav } from "@/components/mobile-nav"
import { NotificationPermission } from "@/components/notification-permission"

export function AuthenticatedShell() {
  return (
    <>
      <NotificationPermission />
      <MobileNav />
    </>
  )
} 