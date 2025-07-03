"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ArrowLeft, AlertCircle, RefreshCw, Calendar } from "lucide-react"
import Link from "next/link"
import { DigestReader } from "@/components/digest/digest-reader"
import { digestService, type Digest } from "@/lib/digest-service"

interface DigestByDatePageProps {
  params: {
    date: string
  }
}

function DigestPageSkeleton() {
  return (
    <div className="container py-6 max-w-3xl">
      <div className="space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Skeleton className="h-9 w-24" />
        </div>

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

function DigestErrorPage({ error, date, onRetry }: { error: string; date: string; onRetry: () => void }) {
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  return (
    <div className="container py-6 max-w-3xl">
      <div className="space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Link href="/digest/archive">
            <Button variant="ghost" size="sm" className="gap-1">
              <ArrowLeft className="h-4 w-4" />
              Back to archive
            </Button>
          </Link>
        </div>

        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            <Calendar className="h-4 w-4" />
            <span>Daily Brief</span>
            <span>•</span>
            <span>{formatDate(date)}</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl mb-3">
            Daily Brief
          </h1>
          <p className="text-muted-foreground">Failed to load digest for this date</p>
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
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  return (
    <div className="container py-6 max-w-3xl">
      <div className="space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Link href="/digest/archive">
            <Button variant="ghost" size="sm" className="gap-1">
              <ArrowLeft className="h-4 w-4" />
              Back to archive
            </Button>
          </Link>
        </div>

        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            <Calendar className="h-4 w-4" />
            <span>Daily Brief</span>
            <span>•</span>
            <span>{formatDate(date)}</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl mb-3">
            Daily Brief
          </h1>
          <p className="text-muted-foreground">No digest found for this date</p>
        </div>

        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No daily brief was generated for {formatDate(date)}. This might be because you weren't following any topics at the time, or there was an issue with generation.
          </AlertDescription>
        </Alert>

        <div className="flex gap-3">
          <Link href="/digest/archive">
            <Button>View Archive</Button>
          </Link>
          <Link href="/digest/latest">
            <Button variant="outline">Latest Digest</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function DigestByDatePage({ params }: DigestByDatePageProps) {
  const { date } = params
  const [digest, setDigest] = useState<Digest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Validate date format
  const isValidDate = (dateString: string) => {
    const regex = /^\d{4}-\d{2}-\d{2}$/
    if (!regex.test(dateString)) return false
    
    const date = new Date(dateString)
    return date.toISOString().split('T')[0] === dateString
  }

  const loadDigestByDate = async (dateString: string) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await digestService.getDigestByDate(dateString)
      setDigest(response.digest)
    } catch (err) {
      console.error(`Failed to load digest for ${dateString}:`, err)
      setError(`Failed to load digest for ${dateString}. Please try again.`)
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    if (isValidDate(date)) {
      loadDigestByDate(date)
    }
  }

  useEffect(() => {
    if (!isValidDate(date)) {
      setError('Invalid date format. Date should be in YYYY-MM-DD format.')
      setLoading(false)
      return
    }

    loadDigestByDate(date)
  }, [date])

  if (loading) {
    return <DigestPageSkeleton />
  }

  if (error) {
    return <DigestErrorPage error={error} date={date} onRetry={handleRetry} />
  }

  if (!digest) {
    return <NoDigestPage date={date} />
  }

  return (
    <div className="container py-6 max-w-3xl">
      <div className="space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Link href="/digest/archive">
            <Button variant="ghost" size="sm" className="gap-1">
              <ArrowLeft className="h-4 w-4" />
              Back to archive
            </Button>
          </Link>
        </div>

        <DigestReader digest={digest} />

        <div className="flex justify-between pt-4">
          <Link href="/digest/archive">
            <Button variant="outline">View archive</Button>
          </Link>
          <Link href="/digest/latest">
            <Button variant="default">Latest digest</Button>
          </Link>
        </div>
      </div>
    </div>
  )
} 