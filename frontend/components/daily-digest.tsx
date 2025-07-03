"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Newspaper, Clock, FileText, AlertCircle, RefreshCw, Sparkles, Users } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { digestService, type Digest } from "@/lib/digest-service"

interface DailyDigestProps {
  className?: string
}

function DigestSkeleton() {
  return (
    <Card className="bg-muted/40">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-5" />
          <Skeleton className="h-6 w-32" />
        </div>
        <Skeleton className="h-4 w-48" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-9 w-32" />
      </CardFooter>
    </Card>
  )
}

function GeneratingDigest() {
  return (
    <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <div className="relative">
            <Newspaper className="h-5 w-5" />
            <Sparkles className="h-3 w-3 absolute -top-1 -right-1 text-primary" />
          </div>
          Your Daily Brief
        </CardTitle>
        <CardDescription>AI is crafting your personalized news digest...</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-16 flex items-center justify-center">
          <div className="flex space-x-2">
            <div className="rounded-full bg-primary h-2 w-2 animate-bounce [animation-delay:-0.3s]"></div>
            <div className="rounded-full bg-primary h-2 w-2 animate-bounce [animation-delay:-0.15s]"></div>
            <div className="rounded-full bg-primary h-2 w-2 animate-bounce"></div>
          </div>
        </div>
        <p className="text-xs text-center text-muted-foreground mt-2">
          This usually takes 30-60 seconds
        </p>
      </CardContent>
    </Card>
  )
}

function NoDigestAvailable({ onGenerate, message }: { onGenerate: () => void; message?: string }) {
  return (
    <Card className="bg-muted/30 border-muted">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Newspaper className="h-5 w-5 text-muted-foreground" />
          Your Daily Brief
        </CardTitle>
        <CardDescription>No digest available yet</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            {message || "Get a personalized summary of yesterday's most important stories based on your interests."}
          </p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Users className="h-3 w-3" />
            <span>Follow topics in your profile to enable daily briefs</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button onClick={onGenerate} variant="default" size="sm">
          <Sparkles className="h-4 w-4 mr-2" />
          Generate Today's Brief
        </Button>
        <Link href="/profile">
          <Button variant="ghost" size="sm">
            Follow Topics
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}

function DigestError({ error, onRetry }: { error: string; onRetry: () => void }) {
  // Provide more specific error handling and helpful messaging
  const getErrorMessage = (errorText: string) => {
    if (errorText.includes('Failed to load')) {
      return {
        title: "Couldn't load your digest",
        description: "There might be a connection issue. Your digest might still be generating.",
        action: "Try again"
      }
    }
    if (errorText.includes('generate')) {
      return {
        title: "Generation failed",
        description: "We couldn't create your daily brief right now. Please try again in a moment.",
        action: "Retry generation"
      }
    }
    return {
      title: "Something went wrong",
      description: errorText,
      action: "Try again"
    }
  }

  const errorInfo = getErrorMessage(error)

  return (
    <Card className="bg-muted/40 border-destructive/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Newspaper className="h-5 w-5" />
          Your Daily Brief
        </CardTitle>
        <CardDescription>{errorInfo.title}</CardDescription>
      </CardHeader>
      <CardContent>
        <Alert variant="destructive" className="border-destructive/30">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{errorInfo.description}</AlertDescription>
        </Alert>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button onClick={onRetry} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          {errorInfo.action}
        </Button>
        <Link href="/digest/archive">
          <Button variant="ghost" size="sm">
            View past digests
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}

export function DailyDigest({ className }: DailyDigestProps) {
  const [digest, setDigest] = useState<Digest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [apiMessage, setApiMessage] = useState<string | null>(null)

  const loadLatestDigest = async () => {
    try {
      setLoading(true)
      setError(null)
      setApiMessage(null)
      
      const response = await digestService.getLatestDigest()
      setDigest(response.digest)
      
      // If no digest and we have a message, store it for display
      if (!response.digest && response.message) {
        console.log('Digest service message:', response.message)
        setApiMessage(response.message)
      }
    } catch (err) {
      console.error('Failed to load latest digest:', err)
      setError('Failed to load your daily brief. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateDigest = async () => {
    try {
      setGenerating(true)
      setError(null)
      
      // Generate digest for today
      const generateResponse = await digestService.generateDigest({})
      
      if (generateResponse.status === 'generating') {
        // Poll for completion if we have a digest_id
        if (generateResponse.digest_id) {
          try {
            await digestService.pollForDigestCompletion(generateResponse.digest_id)
            // Reload the digest after completion
            await loadLatestDigest()
          } catch (pollError) {
            console.error('Digest generation timed out:', pollError)
            setError('Digest generation is taking longer than expected. Please check back in a few minutes.')
          }
        } else {
          // No digest_id, just show generating state
          setError('Digest generation started. Please check back in a few minutes.')
        }
      } else if (generateResponse.status === 'completed') {
        // Reload the digest immediately
        await loadLatestDigest()
      }
    } catch (err) {
      console.error('Failed to generate digest:', err)
      setError('Failed to generate digest. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const handleRetry = () => {
    loadLatestDigest()
  }

  useEffect(() => {
    loadLatestDigest()
  }, [])

  if (loading) {
    return <DigestSkeleton />
  }

  if (generating) {
    return <GeneratingDigest />
  }

  if (error) {
    return <DigestError error={error} onRetry={handleRetry} />
  }

  if (!digest) {
    return <NoDigestAvailable onGenerate={handleGenerateDigest} message={apiMessage || undefined} />
  }

  // Calculate reading time
  const readingTime = digestService.estimateReadingTime(digest)
  
  // Format date
  const digestDate = digestService.getRelativeDigestDate(digest.date)

  // Get a compelling preview from the introduction
  const getDigestPreview = (introduction: string) => {
    // Extract the first sentence or first 120 characters, whichever is shorter
    const firstSentence = introduction.split('.')[0] + '.'
    return firstSentence.length <= 120 ? firstSentence : introduction.substring(0, 120) + '...'
  }

  return (
    <Card className={cn("bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20 transition-all hover:shadow-md", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <div className="relative">
            <Newspaper className="h-5 w-5 text-primary" />
            <div className="absolute -top-1 -right-1 h-2 w-2 bg-primary rounded-full animate-pulse" />
          </div>
          Your Daily Brief
        </CardTitle>
        <CardDescription className="flex items-center gap-2">
          <span>{digestDate}</span>
          <span>•</span>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>{readingTime} min read</span>
          </div>
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-3">
          <p className="text-sm line-clamp-2 font-medium">
            {getDigestPreview(digest.introduction)}
          </p>
          
          {/* Digest stats */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="text-xs bg-primary/10 text-primary border-primary/20">
              <FileText className="h-3 w-3 mr-1" />
              {digest.metrics.topics_included} topics
            </Badge>
            <Badge variant="secondary" className="text-xs bg-primary/10 text-primary border-primary/20">
              <Sparkles className="h-3 w-3 mr-1" />
              {digest.metrics.events_included} stories
            </Badge>
            <Badge variant="outline" className="text-xs">
              {digest.metrics.articles_processed} articles analyzed
            </Badge>
          </div>
        </div>
      </CardContent>
      
      <CardFooter className="flex justify-between">
        <Link href="/digest/latest">
          <Button variant="default" size="sm" className="bg-primary hover:bg-primary/90">
            <Newspaper className="h-4 w-4 mr-2" />
            Read digest
          </Button>
        </Link>
        <Link href="/digest/archive">
          <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-primary">
            See all digests
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}
