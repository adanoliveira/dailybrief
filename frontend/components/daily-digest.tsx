"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  NewspaperIcon as Newspaper,
  ClockIcon as Clock,
  ExclamationCircleIcon as AlertCircle,
    ArrowPathIcon as RefreshCw,
  ArrowRightIcon as ArrowRight
} from "@heroicons/react/24/outline"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { digestService, type Digest } from "@/lib/digest-service"
import { dataManager } from "@/lib/data-manager"

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



function GeneratingDigest({ hasOldDigest = false, isFirstTime = false }: { hasOldDigest?: boolean, isFirstTime?: boolean }) {
  return (
    <Card className={cn(
      "bg-gradient-to-br from-primary/8 via-primary/4 to-transparent border-primary/30",
      "transition-all duration-300 ease-out hover:shadow-lg hover:shadow-primary/20 hover:border-primary/40",
      "focus-within:ring-2 focus-within:ring-primary/30 focus-within:ring-offset-2",
      "relative overflow-hidden group"
    )}>
      {/* Subtle background accent */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50" />
      
      <CardHeader className="pb-4 relative z-10">
        <div className="space-y-2">
          {/* Main headline - matches successful digest styling */}
          <CardTitle className="text-xl md:text-2xl font-bold leading-tight text-foreground">
            {isFirstTime ? "Creating your first digest..." : "Creating your digest..."}
          </CardTitle>
        </div>
      </CardHeader>      
      
      <CardContent className="pb-5 relative z-10">
        {/* Context text - matches successful digest intro styling */}
        <p className="text-sm md:text-base leading-relaxed text-muted-foreground mb-4">
          Analyzing stories across your topics
        </p>
        
        {/* Skeleton placeholders for introduction */}
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-4 w-3/5" />
        </div>
      </CardContent>
      
      <CardFooter className="flex items-center justify-between pt-0 relative z-10">
        {/* Button skeletons - match successful digest layout */}
        <div className="flex-1 mr-3">
          <Skeleton className="h-10 w-full rounded-md" />
        </div>
        <Skeleton className="h-8 w-20 rounded-md" />
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
    <Card className={cn(
      "bg-gradient-to-br from-primary/8 via-primary/4 to-transparent border-primary/30",
      "transition-all duration-300 ease-out hover:shadow-lg hover:shadow-primary/20 hover:border-primary/40",
      "focus-within:ring-2 focus-within:ring-primary/30 focus-within:ring-offset-2",
      "relative overflow-hidden group",
      "animate-in slide-in-from-top-2 duration-300",
      // Subtle error tint
      "border-destructive/30"
    )}>
      {/* Subtle background accent */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50" />
      
      <CardHeader className="pb-4 relative z-10">
        <div className="space-y-2">
          {/* Main headline with emoji - matches successful digest styling */}
          <CardTitle className="text-xl md:text-2xl font-bold leading-tight text-foreground">
            😞 {errorInfo.title}
          </CardTitle>
        </div>
      </CardHeader>      
      
      <CardContent className="pb-5 relative z-10">
        {/* Error description - matches successful digest intro styling */}
        <p className="text-sm md:text-base leading-relaxed text-muted-foreground mb-4">
          {errorInfo.description}
        </p>
        
        {/* Skeleton placeholders for introduction */}
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-4 w-3/5" />
        </div>
      </CardContent>
      
      <CardFooter className="flex items-center justify-between pt-0 relative z-10">
        {/* Retry button - matches successful digest primary button layout */}
        <div className="flex-1 mr-3">
          <Button 
            onClick={onRetry}
            className={cn(
              "w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm",
              "transition-all duration-200 ease-out hover:shadow-md hover:scale-[1.02]",
              "focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:ring-offset-2",
              "font-medium group/btn"
            )}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            <span>{errorInfo.action}</span>
            <ArrowRight className="h-4 w-4 ml-2 transition-transform group-hover/btn:translate-x-0.5" />
          </Button>
        </div>
        
        {/* Archive button - matches successful digest secondary button */}
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

export function DailyDigest({ className }: DailyDigestProps) {
  const [digest, setDigest] = useState<Digest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [apiMessage, setApiMessage] = useState<string | null>(null)
  const [isFirstTimeUser, setIsFirstTimeUser] = useState(false)
  const [generationStartTime, setGenerationStartTime] = useState<number | null>(null)

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

  // Helper function to check if digest is recent (within 24h)
  const isDigestRecent = (digestDate: string): boolean => {
    const digest = new Date(digestDate)
    const now = new Date()
    const hoursAgo = (now.getTime() - digest.getTime()) / (1000 * 60 * 60)
    return hoursAgo < 24
  }

  const loadLatestDigest = async () => {
    try {
      setLoading(true)
      setError(null)
      setApiMessage(null)
      
      const response = await digestService.getLatestDigest()
      
      // Check if we have a recent digest (within 24h)
      const hasRecentDigest = response.digest && isDigestRecent(response.digest.date)
      
      if (hasRecentDigest) {
        // State A: Recent digest found - show it normally
        setDigest(response.digest)
        setIsFirstTimeUser(false)
        console.log('DailyDigest: Found recent digest, displaying')
      } else if (response.digest && !hasRecentDigest) {
        // State C: Old digest found - show it while generating new one
        setDigest(response.digest)
        setIsFirstTimeUser(false)
        console.log('DailyDigest: Found old digest, showing while generating new one')
        await autoGenerateDigest()
      } else {
        // State B: No digest found - start generation immediately (default behavior)
        console.log('DailyDigest: No digest found, starting auto-generation')
        setDigest(null) // Explicitly clear digest state
        setIsFirstTimeUser(true)
        setApiMessage(response.message || null)
        
        // Immediately set generating state - this is now the default for any user without recent digest
        setGenerating(true)
        setGenerationStartTime(Date.now())
        
        await autoGenerateDigest()
      }
    } catch (err) {
      console.error('Failed to load latest digest:', err)
      setError('Failed to load your daily digest. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Poll for digest completion with extended timeout for first-time users
  const pollForCompletion = async (digestId: string, attempts: number = 0) => {
    console.log(`DailyDigest: Polling attempt ${attempts + 1} for digestId: ${digestId}`)
    // Extended timeout for first-time users (5 minutes vs 2 minutes)
    const maxAttempts = isFirstTimeUser ? 100 : 40 // 5 min for new users, 2 min for returning users
    const pollInterval = 3000 // 3 seconds
    
    if (attempts >= maxAttempts) {
      console.log('DailyDigest: Polling timeout, stopping')
      setGenerating(false)
      
      // Provide helpful timeout message for first-time users
      if (isFirstTimeUser) {
        setError('Your first digest is taking longer than expected (5+ minutes). This sometimes happens with new accounts processing lots of content. Please try generating again.')
      } else {
        setError('Digest generation is taking longer than expected (2+ minutes). Please try again.')
      }
      return
    }
    
    try {
      console.log(`DailyDigest: Calling getDigestStatus for digestId: ${digestId}`)
      const status = await digestService.getDigestStatus(digestId)
      console.log('DailyDigest: Status response:', status)
      
      if (status.status === 'completed') {
        console.log('DailyDigest: Generation completed, reloading digest')
        setGenerating(false)
        setGenerationStartTime(null)
        
        // Invalidate cache to ensure fresh data in detail pages
        console.log('DailyDigest: Invalidating digest cache for new digest')
        await dataManager.invalidateDigestCache()
        
        await loadLatestDigest() // Reload with new digest
      } else if (status.status === 'failed') {
        console.log('DailyDigest: Generation failed')
        setGenerating(false)
        setGenerationStartTime(null)
        
        if (isFirstTimeUser) {
          setError('We couldn\'t create your first digest. This might be because you need to follow some topics first. Please check your topic preferences and try again.')
        } else {
          setError('Digest generation failed. Please try again.')
        }
      } else {
        // Still generating, poll again
        setTimeout(() => pollForCompletion(digestId, attempts + 1), pollInterval)
      }
    } catch (err) {
      console.error('DailyDigest: Polling error:', err)
      setGenerating(false)
      setGenerationStartTime(null)
      setError('Failed to check generation status. Please try again.')
    }
  }

  // Auto-generate digest when needed (background operation)
  const autoGenerateDigest = async () => {
    try {
      console.log('DailyDigest: Auto-generating digest for user...')
      console.log('DailyDigest: About to call digestService.generateDigest()')
      
      const result = await digestService.generateDigest({ force_regenerate: true })
      console.log('DailyDigest: generateDigest() response:', result)
      
      if (result.status === 'processing' && result.digest_id) {
        console.log('DailyDigest: Generation started, polling for completion', { 
          digestId: result.digest_id, 
          status: result.status,
          fullResult: result 
        })
        // Ensure generating state is set 
        setGenerating(true)
        setGenerationStartTime(Date.now())
        pollForCompletion(result.digest_id)
      } else if (result.status === 'completed') {
        console.log('DailyDigest: Generation already completed, reloading')
        setGenerating(false)
        setGenerationStartTime(null)
        await loadLatestDigest()
      } else {
        console.log('DailyDigest: Unexpected response from generateDigest:', result)
        setGenerating(false)
        setGenerationStartTime(null)
        
        // Show error to user for first-time users since they're waiting
        if (isFirstTimeUser) {
          setError('Unable to start digest generation. Please make sure you\'ve followed some topics and try again.')
        }
      }
    } catch (err) {
      console.error('DailyDigest: Auto-generation error:', err)
      setGenerating(false)
      setGenerationStartTime(null)
      
      // Show error to user for first-time users since they're waiting
      if (isFirstTimeUser) {
        setError('Failed to start digest generation. Please check that you\'ve followed some topics and try again.')
      }
    }
  }

  // Retry function that resets all states and starts fresh
  const retryGeneration = async () => {
    console.log('DailyDigest: Retrying digest generation')
    
    // Reset all states
    setError(null)
    setDigest(null)
    setGenerating(true)
    setIsFirstTimeUser(true)
    setGenerationStartTime(Date.now())
    
    // Start fresh generation
    try {
      await autoGenerateDigest()
    } catch (err) {
      console.error('DailyDigest: Retry failed:', err)
      setGenerating(false)
      setError('Retry failed. Please check your connection and try again.')
    }
  }

  useEffect(() => {
    loadLatestDigest()
  }, [])

  if (loading) {
    return <DigestLoading />
  }

  if (error) {
    return <DigestError error={error} onRetry={retryGeneration} />
  }



  // Default state: If no recent digest, always show generating state
  if (!digest) {
    console.log('DailyDigest: Rendering GeneratingDigest state (default)', { generating, digest, isFirstTimeUser })
    return <GeneratingDigest hasOldDigest={false} isFirstTime={isFirstTimeUser} />
  }

  // State A (recent digest) or State C (old digest + generating)

  return (
    <Card className={cn(
      "bg-gradient-to-br from-primary/8 via-primary/4 to-transparent border-primary/30",
      "transition-all duration-300 ease-out hover:shadow-lg hover:shadow-primary/20 hover:border-primary/40",
      "focus-within:ring-2 focus-within:ring-primary/30 focus-within:ring-offset-2",
      "relative overflow-hidden group",
      "animate-in fade-in-0 slide-in-from-bottom-4 duration-700"
    )}>
      {/* Subtle background accent */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50" />
      
      <CardHeader className="pb-4 relative z-10">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
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
            {generating && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full">
                <div className="w-2 h-2 bg-primary/60 rounded-full animate-pulse" />
                <span>Preparing today's digest...</span>
              </div>
            )}
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
            <span>{generating ? `Read ${digestDate}'s Digest` : 'Read Digest'}</span>
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

