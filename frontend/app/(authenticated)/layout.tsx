"use client"

import type React from "react"
import { MobileNav } from "@/components/mobile-nav"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Home, Globe, User } from "lucide-react"
import { LogoHorizontal } from "@/components/ui/logo"
import Link from "next/link"
import { Suspense } from "react"
import { NotificationPermission } from "@/components/notification-permission"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { useLanguage } from "@/components/language-provider"

interface DesktopNavItemProps {
  href: string
  icon: React.ReactNode
  label: string
  isActive: boolean
}

function DesktopNavItem({ href, icon, label, isActive }: DesktopNavItemProps) {
  const { t } = useLanguage()
  
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
        isActive 
          ? "text-primary bg-primary/10" 
          : "text-muted-foreground hover:text-foreground hover:bg-accent"
      )}
    >
      {icon}
      {t(label.toLowerCase())}
    </Link>
  )
}

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-background pb-16 md:pb-0">
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/home" className="flex items-center gap-2">
            <LogoHorizontal priority />
          </Link>
          <div className="hidden md:flex items-center gap-2">
            <DesktopNavItem 
              href="/home" 
              icon={<Home className="h-4 w-4" />} 
              label="Home" 
              isActive={pathname === "/home"} 
            />
            <DesktopNavItem 
              href="/world" 
              icon={<Globe className="h-4 w-4" />} 
              label="Headlines" 
              isActive={pathname === "/world"} 
            />
            <DesktopNavItem 
              href="/profile" 
              icon={<User className="h-4 w-4" />} 
              label="Profile" 
              isActive={pathname === "/profile"} 
            />
          </div>
        </div>
      </header>

      <main>
        <Suspense>{children}</Suspense>
      </main>

      <NotificationPermission />
      <MobileNav />
    </div>
  )
}
