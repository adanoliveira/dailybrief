"use client"

import type React from "react"

import { 
  HomeIcon as HomeOutline,
  GlobeAltIcon as GlobeOutline,
  UserIcon as UserOutline
} from "@heroicons/react/24/outline"
import { 
  HomeIcon as HomeSolid,
  GlobeAltIcon as GlobeSolid,
  UserIcon as UserSolid
} from "@heroicons/react/24/solid"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { useLanguage } from "@/components/language-provider"

export function MobileNav() {
  const pathname = usePathname()

  return (
    <div className="fixed bottom-0 left-0 z-50 w-full h-16 bg-background border-t md:hidden">
      <div className="grid h-full grid-cols-3">
        <NavItem 
          href="/home" 
          icon={pathname === "/home" ? <HomeSolid className="h-5 w-5" /> : <HomeOutline className="h-5 w-5" />}
          label="Home" 
          isActive={pathname === "/home"} 
        />
        <NavItem 
          href="/world" 
          icon={pathname === "/world" ? <GlobeSolid className="h-5 w-5" /> : <GlobeOutline className="h-5 w-5" />}
          label="Headlines" 
          isActive={pathname === "/world"} 
        />
        <NavItem
          href="/profile"
          icon={pathname === "/profile" ? <UserSolid className="h-5 w-5" /> : <UserOutline className="h-5 w-5" />}
          label="Profile"
          isActive={pathname === "/profile"}
        />
      </div>
    </div>
  )
}

interface NavItemProps {
  href: string
  icon: React.ReactNode
  label: string
  isActive: boolean
}

function NavItem({ href, icon, label, isActive }: NavItemProps) {
  const { t } = useLanguage()

  return (
    <Link
      href={href}
      className={cn(
        "flex flex-col items-center justify-center transition-all duration-200",
        isActive 
          ? "text-primary scale-105" 
          : "text-muted-foreground"
      )}
    >
      {icon}
      <span className={cn(
        "text-xs mt-1 transition-all duration-200",
        isActive ? "font-medium" : "font-normal"
      )}>
        {t(label.toLowerCase())}
      </span>
    </Link>
  )
}
