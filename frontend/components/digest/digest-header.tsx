"use client"

import React, { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Clock, Globe, Languages } from "lucide-react"
import { getUserPreferences, UserPreferences } from "@/lib/api"
import { fetchOnboardingOptions, Region, Language } from "@/lib/onboarding-service"

// Updated Digest interface to include article_date_range
interface DigestArticle {
  id: string
  title: string
  url: string
  imageUrl?: string | null
  publication?: string | null
  publicationLogoUrl?: string | null
  published_at?: string | null
}

interface DigestStory {
  id: string
  title: string
  abstract: string
  key_facts: string[]
  perspectives: string[]
  articles: DigestArticle[]
  article_count: number
  event_score: number
}

interface DigestTopic {
  id: string
  title: string
  abstract: string
  score: number
  stories: DigestStory[]
}

interface Digest {
  id: string
  title: string
  headline?: string
  date: string
  introduction: string
  conclusion?: string
  topics: DigestTopic[]
  generation_status: 'GENERATING' | 'COMPLETED' | 'FAILED'
  created_at: string
  updated_at: string
  article_date_range?: {
    min_published_at: string
    max_published_at: string
  } | null
  metrics: {
    topics_included: number
    events_included: number
    articles_processed: number
    reading_time_minutes: number
    generation_cost_usd: number
    generation_tokens_total: number
  }
}

interface DigestHeaderProps {
  digest: Digest;
}

export function DigestHeader({ digest }: DigestHeaderProps) {
  const [userPreferences, setUserPreferences] = useState<UserPreferences | null>(null)
  const [regions, setRegions] = useState<Region[]>([])
  const [languages, setLanguages] = useState<Language[]>([])

  // Load user preferences and reference data
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load both preferences and reference data in parallel
        const [prefs, onboardingData] = await Promise.all([
          getUserPreferences(),
          fetchOnboardingOptions()
        ])
        
        setUserPreferences(prefs)
        setRegions(onboardingData.regions)
        setLanguages(onboardingData.languages)
      } catch (error) {
        console.error('Failed to load user preferences or reference data:', error)
      }
    }
    loadData()
  }, [])

  // Get reading time from backend
  const readingTime = digest.metrics.reading_time_minutes || 1

  // Dynamic time period calculation using actual article dates
  const getTimeDescription = React.useMemo(() => {
    // Use backend article_date_range if available
    if (digest.article_date_range?.min_published_at && digest.article_date_range?.max_published_at) {
      const minDate = new Date(digest.article_date_range.min_published_at)
      const maxDate = new Date(digest.article_date_range.max_published_at)
      
      // Normalize dates to start of day using UTC to avoid timezone issues
      const minDay = new Date(Date.UTC(minDate.getUTCFullYear(), minDate.getUTCMonth(), minDate.getUTCDate()))
      const maxDay = new Date(Date.UTC(maxDate.getUTCFullYear(), maxDate.getUTCMonth(), maxDate.getUTCDate()))
      
      // Calculate difference in days
      const diffDays = Math.floor((maxDay.getTime() - minDay.getTime()) / (1000 * 60 * 60 * 24))
      
      if (diffDays === 0) {
        // All articles from the same day
        const today = new Date()
        const todayNormalized = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()))
        const diffFromToday = Math.floor((todayNormalized.getTime() - minDay.getTime()) / (1000 * 60 * 60 * 24))
        
        if (diffFromToday === 0) {
          return 'Today'
        } else if (diffFromToday === 1) {
          return 'Yesterday'
        } else if (diffFromToday <= 7) {
          return `${diffFromToday} days ago`
        } else {
          return minDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
        }
      } else {
        // Articles span multiple days - use actual date span, not search window
        const today = new Date()
        const todayNormalized = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()))
        const daysSinceMax = Math.floor((todayNormalized.getTime() - maxDay.getTime()) / (1000 * 60 * 60 * 24))
        
        // For very recent multi-day ranges
        if (daysSinceMax <= 1 && diffDays <= 7) {
          if (diffDays === 1) {
            // Two consecutive days
            if (daysSinceMax === 0) {
              return 'Today and Yesterday'
            } else {
              return 'the past 2 days'
            }
          } else {
            // Multiple days (3+)
            return `the past ${diffDays + 1} days`
          }
        }
        // For older ranges, use specific dates
        else if (diffDays <= 7) {
          return `${diffDays + 1} days ago`
        } else {
          // Longer range - show specific dates
          const minFormatted = minDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })
          const maxFormatted = maxDate.toLocaleDateString('en-US', { 
            month: 'long', 
            day: 'numeric', 
            year: minDate.getFullYear() !== maxDate.getFullYear() ? 'numeric' : undefined
          })
          return `${minFormatted} to ${maxFormatted}`
        }
      }
    }
    
    // Fallback: Extract dates from individual articles
    const allArticles = digest.topics.flatMap(topic => 
      topic.stories.flatMap(story => story.articles || [])
    )
    
    const publishedDates = allArticles
      .map(article => article.published_at)
      .filter((date): date is string => date !== null && date !== undefined)
      .map(date => new Date(date))
      .sort((a, b) => a.getTime() - b.getTime())

    if (publishedDates.length === 0) {
      // Final fallback to digest date
      const date = new Date(digest.date)
      const today = new Date()
      const todayNormalized = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()))
      const dateNormalized = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()))
      const diffFromToday = Math.floor((todayNormalized.getTime() - dateNormalized.getTime()) / (1000 * 60 * 60 * 24))
      
      if (diffFromToday === 0) return 'Today'
      if (diffFromToday === 1) return 'Yesterday'
      return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    }

    const earliest = publishedDates[0]
    const latest = publishedDates[publishedDates.length - 1]
    
    // Normalize dates to start of day using UTC to avoid timezone issues
    const earliestDay = new Date(Date.UTC(earliest.getUTCFullYear(), earliest.getUTCMonth(), earliest.getUTCDate()))
    const latestDay = new Date(Date.UTC(latest.getUTCFullYear(), latest.getUTCMonth(), latest.getUTCDate()))
    
    // Calculate difference in days
    const diffDays = Math.floor((latestDay.getTime() - earliestDay.getTime()) / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) {
      // All articles from the same day - use the actual article date, not the digest date
      const today = new Date()
      const todayNormalized = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()))
      const diffFromToday = Math.floor((todayNormalized.getTime() - earliestDay.getTime()) / (1000 * 60 * 60 * 24))
      
      if (diffFromToday === 0) return 'Today'
      if (diffFromToday === 1) return 'Yesterday'
      return earliest.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    } else if (diffDays === 1) {
      // Articles span exactly 2 days - be more careful about this calculation
      const today = new Date()
      const todayNormalized = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()))
      const daysSinceLatest = Math.floor((todayNormalized.getTime() - latestDay.getTime()) / (1000 * 60 * 60 * 24))
      const daysSinceEarliest = Math.floor((todayNormalized.getTime() - earliestDay.getTime()) / (1000 * 60 * 60 * 24))
      
      // If latest article is from today and earliest is from yesterday
      if (daysSinceLatest === 0 && daysSinceEarliest === 1) {
        return 'Today and Yesterday'
      } 
      // If latest article is from yesterday and earliest is from day before
      else if (daysSinceLatest === 1 && daysSinceEarliest === 2) {
        return 'the past 2 days'
      }
      // If both are from yesterday (edge case with timezone/date boundary issues)
      else if (daysSinceLatest === 1 && daysSinceEarliest === 1) {
        return 'Yesterday'
      }
      // Default to generic "past 2 days"
      else {
        return 'the past 2 days'
      }
    } else if (diffDays <= 7) {
      // Articles span multiple days within a week
      return `the past ${diffDays + 1} days`
    }
    
    // Longer range - show specific dates
    return `${earliest.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })} to ${latest.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`
  }, [digest])

  // Generate subtitle with dynamic time description
  const getSubtitle = () => {
    if (!digest.headline) return digest.title
    
    return `Top stories from ${getTimeDescription}`
  }

  // Format relative time for generation
  const getRelativeTime = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffMinutes = Math.floor(diffMs / (1000 * 60))

    if (diffMinutes < 60) {
      return diffMinutes <= 1 ? 'just now' : `${diffMinutes}m ago`
    } else if (diffHours < 24) {
      return `${diffHours}h ago`
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      })
    }
  }

  // Format date for display
  const formatDigestDate = (dateString: string): string => {
    const date = new Date(dateString)
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
  }

  const digestDate = formatDigestDate(digest.date)
  const generatedTime = getRelativeTime(digest.created_at)

  // Prepare user preferences for display using backend data
  const displayRegions = React.useMemo(() => {
    if (!userPreferences?.regions || !regions.length) return []
    
    return userPreferences.regions
      .slice(0, 3)
      .map(regionCode => {
        const region = regions.find(r => r.code === regionCode.toString())
        return region?.name || regionCode.toString()
      })
  }, [userPreferences, regions])
  
  const displayLanguages = React.useMemo(() => {
    if (!userPreferences?.languages || !languages.length) return []
    
    return userPreferences.languages
      .slice(0, 3)
      .map(langCode => {
        const language = languages.find(l => l.iso_code === langCode.toString())
        return language?.name || langCode.toString()
      })
  }, [userPreferences, languages])

  return (
    <div className="relative mb-10">
      <div className="space-y-4">
        {/* Page label with reading time */}
        <div className="mb-3 md:mb-4">
          <span className={cn(
            "text-sm md:text-sm font-medium uppercase tracking-wider",
            "text-muted-foreground/70 font-sans flex items-center gap-1"
          )}>
            {digestDate === 'Today' ? 
              <>Daily Digest • Today • <Clock className="h-3 w-3" /> {readingTime} min read</> : 
              digestDate === 'Yesterday' ?
                <>Daily Digest • Yesterday • <Clock className="h-3 w-3" /> {readingTime} min read</> :
                <>Daily Digest • {new Date(digest.date).toLocaleDateString('en-US', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric'
                })} • <Clock className="h-3 w-3" /> {readingTime} min read</>
            }
          </span>
        </div>

        {/* Main headline */}
        <h1 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black text-foreground leading-tight">
        {digest.headline || digest.title}
        </h1>

        {/* Subtitle only */}
        <div className="text-lg md:text-xl lg:text-xl text-muted-foreground ">
        <span>{getSubtitle()}</span>
        </div>


      </div>
    </div>
  );
} 