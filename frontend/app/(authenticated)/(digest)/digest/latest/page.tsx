"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, RefreshCw } from "lucide-react"
import Link from "next/link"
import { DigestReader } from "@/components/digest/digest-reader"
import { DigestActionBar } from "@/components/digest/digest-action-bar"
import { digestService, type Digest } from "@/lib/digest-service"

function DigestPageSkeleton() {
  return (
    <div className="container px-4 md:px-6 lg:px-8 max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto py-6">
      <div className="space-y-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
          </div>

          <div className="flex gap-2">
            <Skeleton className="h-6 w-16" />
            <Skeleton className="h-6 w-16" />
            <Skeleton className="h-6 w-16" />
          </div>
        </div>

        <Skeleton className="h-px w-full" />

        <div className="space-y-6">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="space-y-4">
              <Skeleton className="h-20 w-full" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function DigestErrorPage({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="container px-4 md:px-6 lg:px-8 max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto py-6">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl mb-3">
            Daily Brief
          </h1>
          <p className="text-muted-foreground">Failed to load your daily digest</p>
        </div>

        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    </div>
  )
}

function NoDigestPage() {
  return (
    <div className="container px-4 md:px-6 lg:px-8 max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto py-6">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl mb-3">
            Daily Brief
          </h1>
          <p className="text-muted-foreground">No digest available yet</p>
        </div>

        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No daily brief has been generated yet. Follow some topics in your profile to start receiving personalized daily briefs.
          </AlertDescription>
        </Alert>

        <div className="flex gap-3">
          <Link href="/profile">
            <Button>Follow Topics</Button>
          </Link>
          <Link href="/digest/archive">
            <Button variant="outline">View Archive</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function LatestDigest() {
  const [digest, setDigest] = useState<Digest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadLatestDigest = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await digestService.getLatestDigest()
      setDigest(response.digest)
    } catch (err) {
      console.error('Failed to load latest digest:', err)
      setError('Failed to load your daily brief. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    loadLatestDigest()
  }

  useEffect(() => {
    loadLatestDigest()
  }, [])

  if (loading) {
    return <DigestPageSkeleton />
  }

  if (error) {
    return <DigestErrorPage error={error} onRetry={handleRetry} />
  }

  if (!digest) {
    return <NoDigestPage />
  }

  return (
    <div className="min-h-screen">
      <DigestReader digest={digest} />

      {/* Digest Action Bar - Only show on mobile */}
      <div className="md:hidden">
        <DigestActionBar digest={digest} />
      </div>
    </div>
  )
}