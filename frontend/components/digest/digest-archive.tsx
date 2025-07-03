"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  Calendar,
  Clock,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Newspaper,
  FileText
} from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { digestService, type DigestSummary, type DigestListResponse } from "@/lib/digest-service"

interface DigestArchiveProps {
  className?: string
}

interface DigestSummaryCardProps {
  digest: DigestSummary
}

function DigestSummaryCard({ digest }: DigestSummaryCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const getRelativeDate = (dateString: string) => {
    const digestDate = new Date(dateString)
    const today = new Date()
    const diffTime = today.getTime() - digestDate.getTime()
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    
    return formatDate(dateString)
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'default'
      case 'generating': return 'secondary'
      case 'failed': return 'destructive'
      default: return 'outline'
    }
  }

  const getStatusText = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'Ready'
      case 'generating': return 'Generating'
      case 'failed': return 'Failed'
      default: return status
    }
  }

  const isClickable = digest.generation_status.toLowerCase() === 'completed'

  const cardContent = (
    <Card className={cn(
      "transition-all duration-200",
      isClickable && "hover:shadow-md hover:scale-[1.02] cursor-pointer",
      !isClickable && "opacity-75"
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="text-lg leading-tight line-clamp-2">
              {digest.title}
            </CardTitle>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span>{getRelativeDate(digest.date)}</span>
            </div>
          </div>
          <Badge variant={getStatusColor(digest.generation_status)}>
            {getStatusText(digest.generation_status)}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground line-clamp-3">
          {digest.introduction}
        </p>

        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="text-xs">
            <FileText className="h-3 w-3 mr-1" />
            {digest.topics_included} topics
          </Badge>
          <Badge variant="outline" className="text-xs">
            <TrendingUp className="h-3 w-3 mr-1" />
            {digest.events_included} stories
          </Badge>
          <Badge variant="outline" className="text-xs">
            <Newspaper className="h-3 w-3 mr-1" />
            {digest.articles_processed} articles
          </Badge>
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>Created {new Date(digest.created_at).toLocaleDateString()}</span>
          </div>
          {digest.generation_cost_usd > 0 && (
            <span>${digest.generation_cost_usd.toFixed(4)}</span>
          )}
        </div>
      </CardContent>
    </Card>
  )

  if (isClickable) {
    return (
      <Link href={`/digest/date/${digest.date.split('T')[0]}`}>
        {cardContent}
      </Link>
    )
  }

  return cardContent
}

function DigestArchiveSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 6 }).map((_, index) => (
        <Card key={index}>
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-2 flex-1">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
              <Skeleton className="h-6 w-16" />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
              <Skeleton className="h-4 w-2/3" />
            </div>
            <div className="flex gap-2">
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-5 w-16" />
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
  
  const pageSize = 10

  const loadDigests = async (page: number) => {
    try {
      setLoading(true)
      setError(null)
      
      const response: DigestListResponse = await digestService.listDigests(page, pageSize)
      
      setDigests(response.digests)
      setTotalPages(response.pagination.total_pages)
      setTotalCount(response.pagination.total_count)
      setCurrentPage(page)
    } catch (err) {
      console.error('Failed to load digests:', err)
      setError('Failed to load digest archive. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDigests(1)
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
    loadDigests(currentPage)
  }

  if (loading) {
    return (
      <div className={cn("space-y-6", className)}>
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <DigestArchiveSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn("space-y-6", className)}>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Digest Archive</h2>
          <p className="text-muted-foreground">Your daily brief history</p>
        </div>
        
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
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Digest Archive</h2>
          <p className="text-muted-foreground">Your daily brief history</p>
        </div>
        
        <Card className="p-8 text-center">
          <div className="space-y-4">
            <Newspaper className="h-12 w-12 mx-auto text-muted-foreground" />
            <div>
              <h3 className="text-lg font-medium">No digests yet</h3>
              <p className="text-muted-foreground">
                Your daily briefs will appear here once they're generated.
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Digest Archive</h2>
          <p className="text-muted-foreground">
            {totalCount} {totalCount === 1 ? 'digest' : 'digests'} in your history
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {digests.map((digest) => (
          <DigestSummaryCard key={digest.id} digest={digest} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
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