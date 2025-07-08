"use client"

import React from 'react'
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { DigestArchive } from "@/components/digest/digest-archive"
import { useRouter } from "next/navigation"

export default function DigestArchivePage() {
  const router = useRouter()

  return (
    <div className="min-h-screen">
      <div className="container px-4 md:px-6 lg:px-8 max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto pt-6">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black tracking-tight leading-tight text-foreground">
              Daily Digests Archive
            </h1>
            <p className="text-lg md:text-xl lg:text-xl text-muted-foreground leading-relaxed mt-4">
              Browse your previous daily digests
            </p>
          </div>

          <DigestArchive />
        </div>
      </div>

      {/* Mobile Action Bar */}
      <div className="md:hidden">
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-sm border-t border-border shadow-lg dark:shadow-white/10 dark:shadow-2xl">
          <div className="flex items-center justify-between px-4 py-2 max-w-screen-sm mx-auto">
            <Button
              variant="ghost"
              size="default"
              onClick={() => router.push('/home')}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground h-12 px-3"
            >
              <ArrowLeft className="size-5" />
              <span className="text-sm font-medium">Home</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
} 