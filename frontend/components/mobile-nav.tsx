"use client"

import type React from "react"

import { Home, Globe, User } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { useLanguage } from "@/components/language-provider"

export function MobileNav() {
  const pathname = usePathname()

  return (
    <div className="fixed bottom-0 left-0 z-50 w-full h-16 bg-background border-t md:hidden">
      <div className="grid h-full grid-cols-3">
        <NavItem href="/home" icon={<Home className="h-5 w-5" />} label="Home" isActive={pathname === "/home"} />
        <NavItem href="/world" icon={<Globe className="h-5 w-5" />} label="Headlines" isActive={pathname === "/world"} />
        <NavItem
          href="/profile"
          icon={<User className="h-5 w-5" />}
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
      className={cn("flex flex-col items-center justify-center", isActive ? "text-primary" : "text-muted-foreground")}
    >
      {icon}
      <span className="text-xs mt-1">{t(label.toLowerCase())}</span>
    </Link>
  )
}
