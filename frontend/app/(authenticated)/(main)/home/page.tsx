"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useSession } from "next-auth/react"
import { useUserPreferences, useOfflineStatus } from "@/lib/use-local-data"
import { dataManager } from "@/lib/data-manager"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  FunnelIcon as Filter, 
  MagnifyingGlassIcon as Search, 
  WifiIcon as Wifi, 
  NoSymbolIcon as WifiOff 
} from "@heroicons/react/24/outline"
import { DailyDigest } from "@/components/daily-digest"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { InfiniteNewsFeed } from "@/components/infinite-news-feed"
import { FeedRefreshButton, type FeedRefreshResult } from "@/components/feed-refresh-button"
import { useToast } from "@/components/ui/use-toast"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function Home() {
  // Declare all hooks at the top level
  const router = useRouter()
  const searchParams = useSearchParams()
  const { data: session } = useSession()
  const { toast } = useToast()
  const [isVerifying, setIsVerifying] = useState(true)
  
  // Article filtering state
  const [selectedTopic, setSelectedTopic] = useState('for-you')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [sortOrder, setSortOrder] = useState<'relevance' | 'newest' | 'oldest'>('relevance')
  
  // Refresh state
  // Refresh state now handled by FeedRefreshButton component
  
  // Use local storage hooks - NO direct API calls
  const { 
    data: userPreferences, 
    isLoading: isLoadingUser, 
    error: userError 
  } = useUserPreferences({ backgroundSync: true })
  
  const { isOnline, wasOffline } = useOfflineStatus()
  
  // Background sync moved to layout level to prevent multiple instances
  
  // Handle manual refresh - returns promise for FeedRefreshButton component
  const handleRefresh = async () => {
    const topicSlug = selectedTopic === 'for-you' ? undefined : selectedTopic
    
    // Get current article count before refresh
    const beforeRefresh = await dataManager.getFeed(
      'personalized', 
      topicSlug,
      1, // page 1
      10, // page size
      { forceRefresh: false }
    )
    const countBefore = beforeRefresh?.articles.length || 0
    
    // Force refresh the feed
    const afterRefresh = await dataManager.getFeed(
      'personalized', 
      topicSlug,
      1, // page 1
      10, // page size
      { forceRefresh: true }
    )
    const countAfter = afterRefresh?.articles.length || 0
    
    // Determine if we got new data by checking if content changed
    // For page 1, if we have different articles or different timestamps, consider it new data
    const hasNewData = countAfter !== countBefore || 
      (afterRefresh && beforeRefresh && 
       JSON.stringify(afterRefresh.articles.slice(0, 3).map(a => a.id)) !== 
       JSON.stringify(beforeRefresh.articles.slice(0, 3).map(a => a.id))) || false
    
    return { hasNewData }
  }
  
  // Handle search debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
    }, 500) // 500ms debounce
    
    return () => clearTimeout(timer)
  }, [searchQuery])
  
  // Check if user has completed onboarding
  useEffect(() => {
    const forceParam = searchParams?.get('force') === 'true'
    
    // Skip verification if force parameter is present
    if (forceParam) {
      setIsVerifying(false)
      return
    }
    
    // Wait for user status to be loaded
    if (isLoadingUser) {
      return
    }
    
    // If we have user status, check onboarding status
    if (userPreferences) {
      if (!userPreferences.has_completed_onboarding) {
        // User needs to complete onboarding
        router.replace('/onboarding?skip_check=true')
        return
      }
      
      // User has completed onboarding, allow access to home
      setIsVerifying(false)
    }
    
    // If user status isn't available yet but session is, check localStorage as fallback
    if (!userPreferences && session) {
      const hasDoneOnboarding = localStorage.getItem('has_completed_onboarding') === 'true'
      if (!hasDoneOnboarding) {
        // User needs to complete onboarding
        router.replace('/onboarding?skip_check=true')
        return
      }
      
      // Onboarding is complete according to localStorage, allow access to home
      setIsVerifying(false)
    }
  }, [userPreferences, isLoadingUser, session, router, searchParams])

  // Check if user just completed onboarding
  useEffect(() => {
    const justCompletedOnboarding = searchParams?.get('onboarding_complete') === 'true' || 
                                    searchParams?.get('new_session') === 'true'
    
    if (justCompletedOnboarding) {
      // Remove the query parameter without navigation
      window.history.replaceState({}, document.title, '/home')
      
      toast({
        title: "Setup complete!",
        description: "Welcome to your personalized news feed.",
        duration: 3000,
      })
    }
  }, [searchParams, toast])

  // Define render functions for different states
  const renderVerifying = () => (
    <div className="container py-6">
      <div className="flex justify-center items-center min-h-[50vh]">
        <div className="text-center space-y-4">
          <p className="text-muted-foreground">Loading your personalized news...</p>
        </div>
      </div>
    </div>
  )

  const renderMainContent = () => (
    <div className="container py-6">
      <div className="flex flex-col gap-6">
        {/* Header with offline indicator */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">Your News</h1>
            
            {/* Desktop refresh button */}
            <FeedRefreshButton onRefresh={handleRefresh} />
            
            {!isOnline && (
              <div className="flex items-center gap-1 text-amber-600 text-sm">
                <WifiOff className="h-4 w-4" />
                <span>Offline</span>
              </div>
            )}
            {isOnline && wasOffline && (
              <div className="flex items-center gap-1 text-green-600 text-sm">
                <Wifi className="h-4 w-4" />
                <span>Back online</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative w-full sm:w-[260px]">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input 
                type="search" 
                placeholder="Search articles..." 
                className="w-full pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Select 
              defaultValue={sortOrder}
              onValueChange={(value) => setSortOrder(value as 'relevance' | 'newest' | 'oldest')}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="relevance">Relevance</SelectItem>
                <SelectItem value="newest">Newest</SelectItem>
                <SelectItem value="oldest">Oldest</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Offline notice */}
        {!isOnline && (
          <Alert>
            <WifiOff className="h-4 w-4" />
            <AlertDescription>
              You're offline. Showing cached articles. Connect to the internet to get the latest updates.
            </AlertDescription>
          </Alert>
        )}

        {/* User preferences error notice */}
        {userError && (
          <Alert variant="destructive">
            <AlertDescription>
              Failed to load your preferences: {userError}. Some features may not work properly.
            </AlertDescription>
          </Alert>
        )}

        <DailyDigest />

        <Tabs 
          defaultValue="for-you"
          value={selectedTopic}
          onValueChange={setSelectedTopic}
        >
          <TabsList className="mb-4 overflow-auto py-1 w-full justify-start">
            <TabsTrigger value="for-you">For You</TabsTrigger>
            {userPreferences?.topics_details?.map(topic => (
              <TabsTrigger key={topic.id} value={topic.slug}>{topic.name}</TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value={selectedTopic}>
            <InfiniteNewsFeed 
              feedType="personalized"
              topicSlug={selectedTopic} 
              searchQuery={debouncedSearch}
              sortOrder={sortOrder}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )

  // Now render the appropriate content after all hooks have been called
  if (isVerifying) {
    return renderVerifying()
  }

  return renderMainContent()
}
