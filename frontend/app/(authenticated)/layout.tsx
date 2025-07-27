import type React from "react"
import { Suspense } from "react"
import { AuthenticatedShell } from "@/components/authenticated-shell"
import { BackgroundSyncProvider } from "@/components/background-sync-provider"

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <BackgroundSyncProvider>
      <div className="min-h-screen bg-background pb-16 md:pb-0">
        <Suspense fallback={<div>Loading...</div>}>
          {children}
        </Suspense>

        <AuthenticatedShell />
      </div>
    </BackgroundSyncProvider>
  )
}
