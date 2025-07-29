"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  Calendar,
  Clock,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Newspaper
} from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { dataManager } from "@/lib/data-manager"
import { type DigestSummary, type DigestListResponse } from "@/lib/digest-service"

interface DigestArchiveProps {
  className?: string
}

interface DigestSummaryCardProps {
  digest: DigestSummary
}

function DigestSummaryCard({ digest }: DigestSummaryCardProps) {
  const getRelativeDate = (dateString: string) => {
    const digestDate = new Date(dateString)
    const today = new Date()
    const diffTime = today.getTime() - digestDate.getTime()
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const readingTime = digest.reading_time_minutes || 1

  return (
    <Link href={`/digest/date/${digest.date.split('T')[0]}`}>
      <Card className={cn(
        "transition-all duration-200 hover:shadow-md hover:scale-[1.01] cursor-pointer",
        "bg-gradient-to-br from-primary/4 via-primary/2 to-transparent border-primary/20",
        "hover:border-primary/30 hover:shadow-primary/10",
        "relative overflow-hidden group"
      )}>
        {/* Subtle background accent */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/3 to-transparent opacity-50" />
        
        <CardHeader className="pb-3 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground/70">
              <span>Daily Digest</span>
              <span>•</span>
              <span>{getRelativeDate(digest.date)}</span>
              <span>•</span>
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>{readingTime} min read</span>
              </div>
            </div>
            <CardTitle className="text-lg md:text-xl leading-tight line-clamp-2 group-hover:text-primary transition-colors">
              {digest.headline || digest.title}
            </CardTitle>
          </div>
        </CardHeader>
        
        <CardContent className="relative z-10">
          <p className="text-sm md:text-base leading-relaxed text-muted-foreground line-clamp-3 group-hover:text-foreground/90 transition-colors">
            {digest.introduction}
          </p>
        </CardContent>
      </Card>
    </Link>
  )
}

function DigestArchiveSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 6 }).map((_, index) => (
        <Card key={index} className="relative overflow-hidden">
          <CardHeader className="pb-3">
            <div className="space-y-2">
              <Skeleton className="h-4 w-64" />
              <Skeleton className="h-6 w-3/4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

export function DigestArchive({ className }: DigestArchiveProps) {
  const [digests, setDigests] = useState<DigestSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  
  const pageSize = 12

  const loadDigests = async (page: number, forceRefresh: boolean = false) => {
    try {
      setLoading(true)
      setError(null)
      
      // Use DataManager for local-first behavior
      const response = await dataManager.listDigests(page, pageSize, {
        maxAge: forceRefresh ? 0 : 30 * 60 * 1000, // 30 minutes unless force refresh
        backgroundSync: !forceRefresh // Enable background sync unless forcing refresh
      })
      
      // Filter to only show completed digests
      const completedDigests = response.digests.filter(
        (digest: DigestSummary) => digest.generation_status.toLowerCase() === 'completed'
      )
      
      setDigests(completedDigests)
      setTotalPages(response.pagination.total_pages)
      setTotalCount(completedDigests.length)
      setCurrentPage(page)
    } catch (err) {
      console.error('Failed to load digests:', err)
      setError('Failed to load digest archive. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDigests(1) // Initial load with background sync
  }, [])

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      loadDigests(currentPage - 1)
    }
  }

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      loadDigests(currentPage + 1)
    }
  }

  const handleRetry = () => {
    loadDigests(currentPage, true) // Force refresh on retry
  }

  if (loading) {
    return (
      <div className={cn("space-y-6", className)}>
        <DigestArchiveSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn("space-y-6", className)}>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={handleRetry}>
              Try Again
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (digests.length === 0) {
    return (
      <div className={cn("space-y-6", className)}>
        <Card className="p-8 text-center bg-muted/20 border-muted">
          <div className="space-y-4">
            <Newspaper className="h-12 w-12 mx-auto text-muted-foreground/60" />
            <div>
              <h3 className="text-lg font-medium">No digests yet</h3>
              <p className="text-muted-foreground">
                Your daily digests will appear here once they're generated.
              </p>
            </div>
            <Link href="/home">
              <Button>Go to Home</Button>
            </Link>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      <div className="grid gap-4">
        {digests.map((digest) => (
          <DigestSummaryCard key={digest.id} digest={digest} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4">
          <Button
            variant="outline"
            onClick={handlePreviousPage}
            disabled={currentPage === 1}
            className="flex items-center gap-2"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>
              Page {currentPage} of {totalPages}
            </span>
          </div>
          
          <Button
            variant="outline"
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
            className="flex items-center gap-2"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
} 