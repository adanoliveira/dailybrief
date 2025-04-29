import type React from "react"
import { MobileNav } from "@/components/mobile-nav"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import Link from "next/link"
import { Suspense } from "react"
import { NotificationPermission } from "@/components/notification-permission"

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background pb-16 md:pb-0">
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/home" className="flex items-center gap-2">
            <span className="text-xl font-bold">DailyBrief</span>
          </Link>
          <div className="hidden md:flex items-center gap-4">
            <Link href="/home" className="text-sm font-medium">
              Home
            </Link>
            <Link href="/world" className="text-sm font-medium">
              World
            </Link>
            <div className="relative w-[200px]">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input type="search" placeholder="Search..." className="w-full pl-8" />
            </div>
            <Link href="/profile">
              <Button variant="ghost" size="sm">
                Profile
              </Button>
            </Link>
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
