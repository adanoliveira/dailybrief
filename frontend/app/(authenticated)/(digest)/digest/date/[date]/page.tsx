"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, RefreshCw } from "lucide-react"
import Link from "next/link"
import { DigestReader } from "@/components/digest/digest-reader"
import { dataManager } from "@/lib/data-manager"
import { type Digest } from "@/lib/digest-service"

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

function DigestErrorPage({ error, onRetry, date }: { error: string; onRetry: () => void; date: string }) {
  return (
    <div className="container px-4 md:px-6 lg:px-8 max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto py-6">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl mb-3">
            Daily Brief - {new Date(date).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </h1>
          <p className="text-muted-foreground">Failed to load digest</p>
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

function NoDigestPage({ date }: { date: string }) {
  return (
    <div className="container px-4 md:px-6 lg:px-8 max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto py-6">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl mb-3">
            Daily Brief - {new Date(date).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </h1>
          <p className="text-muted-foreground">No digest available for this date</p>
        </div>

        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No daily brief was generated for this date. This might be because you weren't following any topics yet, or there wasn't enough content to generate a digest.
          </AlertDescription>
        </Alert>

        <div className="flex gap-3">
          <Link href="/digest/latest">
            <Button>View Latest Digest</Button>
          </Link>
          <Link href="/digest/archive">
            <Button variant="outline">View Archive</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function DigestByDate({ params }: { params: { date: string } }) {
  const [digest, setDigest] = useState<Digest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDigest = async (forceRefresh: boolean = false) => {
    try {
      setLoading(true)
      setError(null)
      
      // Use DataManager for local-first behavior
      const response = await dataManager.getDigestByDate(params.date, {
        maxAge: forceRefresh ? 0 : 30 * 60 * 1000, // 30 minutes unless force refresh
        backgroundSync: !forceRefresh // Enable background sync unless forcing refresh
      })
      
      setDigest(response.digest)
    } catch (err) {
      console.error('Failed to load digest:', err)
      setError('Failed to load digest for this date. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    loadDigest(true) // Force refresh on retry
  }

  useEffect(() => {
    loadDigest() // Initial load with background sync
  }, [params.date])

  if (loading) {
    return <DigestPageSkeleton />
  }

  if (error) {
    return <DigestErrorPage error={error} onRetry={handleRetry} date={params.date} />
  }

  if (!digest) {
    return <NoDigestPage date={params.date} />
  }

  return (
    <div className="min-h-screen">
      <DigestReader digest={digest} />
    </div>
  )
} 