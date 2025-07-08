"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Newspaper, Clock, AlertCircle, RefreshCw, Sparkles, Users, ArrowRight } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { digestService, type Digest } from "@/lib/digest-service"

interface DailyDigestProps {
  className?: string
}

function DigestLoading() {
  return (
    <Card className="border-muted bg-muted/30">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Skeleton className="h-5 w-5 rounded" />
          <Skeleton className="h-5 w-32" />
        </CardTitle>
        <CardDescription>
          <Skeleton className="h-4 w-24" />
        </CardDescription>
      </CardHeader>
      <CardContent className="pb-4">
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-4 w-3/5" />
        </div>
      </CardContent>
      <CardFooter className="flex justify-between pt-0">
        <Skeleton className="h-9 w-32" />
        <Skeleton className="h-9 w-20" />
      </CardFooter>
    </Card>
  )
}

function GeneratingDigest() {
  return (
    <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <div className="relative">
            <Newspaper className="h-5 w-5 text-primary" />
            <Sparkles className="h-3 w-3 absolute -top-1 -right-1 text-primary animate-pulse" />
          </div>
          <span className="font-semibold tracking-tight">Your Daily Digest</span>
        </CardTitle>
        <CardDescription className="text-sm">
          AI is crafting your personalized news digest...
        </CardDescription>
      </CardHeader>
      <CardContent className="pb-4">
        <div className="flex items-center justify-center py-6">
          <div className="flex space-x-2">
            <div className="rounded-full bg-primary h-2 w-2 animate-bounce [animation-delay:-0.3s]"></div>
            <div className="rounded-full bg-primary h-2 w-2 animate-bounce [animation-delay:-0.15s]"></div>
            <div className="rounded-full bg-primary h-2 w-2 animate-bounce"></div>
          </div>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground">
            This usually takes 30-60 seconds
          </p>
        </div>
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
            Your Daily Digest
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
            <span>Follow topics in your profile to enable daily digests</span>
            </div>
          </div>
        </CardContent>
      <CardFooter className="flex justify-between">
        <Button onClick={onGenerate} variant="default" size="sm">
          <Sparkles className="h-4 w-4 mr-2" />
          Generate Today's Digest
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
        description: "We couldn't create your daily digest right now. Please try again in a moment.",
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
          Your Daily Digest
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

  // Get reading time from backend - moved before any conditional returns
  const readingTime = React.useMemo(() => {
    if (!digest) return 1
    return digest.metrics.reading_time_minutes || 1
  }, [digest])

  // Format date for display - moved before any conditional returns
  const digestDate = React.useMemo(() => {
    if (!digest) return 'Today'
    
    const date = new Date(digest.date)
    const today = new Date()
    const diffTime = today.getTime() - date.getTime()
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday' 
    
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric'
    })
  }, [digest])

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
      setError('Failed to load your daily digest. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const generateDigest = async () => {
    try {
      setGenerating(true)
      setError(null)
      await digestService.generateDigest()
      // After generation request, reload to get the latest
      await loadLatestDigest()
    } catch (err) {
      console.error('Failed to generate digest:', err)
      setError('Failed to generate digest. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  useEffect(() => {
    loadLatestDigest()
  }, [])

  if (loading) {
    return <DigestLoading />
  }

  if (error) {
    return <DigestError error={error} onRetry={loadLatestDigest} />
  }

  if (generating) {
    return <GeneratingDigest />
  }

  if (!digest) {
    return <NoDigestAvailable onGenerate={generateDigest} message={apiMessage || undefined} />
  }

  return (
    <Card className={cn(
      "bg-gradient-to-br from-primary/8 via-primary/4 to-transparent border-primary/30",
      "transition-all duration-300 ease-out hover:shadow-lg hover:shadow-primary/20 hover:border-primary/40",
      "focus-within:ring-2 focus-within:ring-primary/30 focus-within:ring-offset-2",
      "relative overflow-hidden group",
    )}>
      {/* Subtle background accent */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50" />
      
      <CardHeader className="pb-4 relative z-10">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground/80">
            <span>Daily Digest</span>
            <span>•</span>
            <span>{digestDate}</span>
            <span>•</span>
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{readingTime} min read</span>
            </div>
          </div>
          <CardTitle className="text-xl md:text-2xl font-bold leading-tight text-foreground group-hover:text-primary transition-colors">
            {digest.headline || digest.title}
          </CardTitle>
        </div>
      </CardHeader>      
      
      <CardContent className="pb-5 relative z-10">
        <p className="text-sm md:text-base leading-relaxed text-muted-foreground line-clamp-3 group-hover:text-foreground/90 transition-colors">
          {digest.introduction}
        </p>
      </CardContent>
      
      <CardFooter className="flex items-center justify-between pt-0 relative z-10">
        <Link href="/digest/latest" className="flex-1 mr-3">
          <Button 
            className={cn(
              "w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm",
              "transition-all duration-200 ease-out hover:shadow-md hover:scale-[1.02]",
              "focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:ring-offset-2",
              "font-medium group/btn"
            )}
          >
            <span>Read Digest</span>
            <ArrowRight className="h-4 w-4 ml-2 transition-transform group-hover/btn:translate-x-0.5" />
          </Button>
        </Link>
        <Link href="/digest/archive">
          <Button 
            variant="ghost" 
            size="sm"
            className={cn(
              "text-muted-foreground hover:text-primary hover:bg-primary/10",
              "transition-all duration-200 ease-out",
              "focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:ring-offset-1",
              "font-medium"
            )}
          >
            View Archive
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}
