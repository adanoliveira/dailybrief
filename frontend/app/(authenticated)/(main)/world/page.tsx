"use client"

import { useState, useEffect } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Search, Wifi, WifiOff, RefreshCw } from "lucide-react"
import { useUserPreferences, useOfflineStatus, useBackgroundSync } from "@/lib/use-local-data"
import { dataManager } from "@/lib/data-manager"
import { InfiniteNewsFeed } from "@/components/infinite-news-feed"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function World() {
  const [selectedTopic, setSelectedTopic] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  
  // Refresh state
  const [isRefreshing, setIsRefreshing] = useState(false)
  
  // Use local storage hooks - NO direct API calls
  const { 
    data: userPreferences, 
    isLoading: preferencesLoading, 
    error: preferencesError 
  } = useUserPreferences({ backgroundSync: true })
  
  const { isOnline, wasOffline } = useOfflineStatus()
  
  // Enable background sync for this page
  useBackgroundSync(10 * 60 * 1000) // 10 minutes
  
  // Handle manual refresh
  const handleRefresh = async () => {
    if (isRefreshing) return
    
    setIsRefreshing(true)
    try {
      // Refresh the current world feed
      const topicSlug = selectedTopic === 'all' ? undefined : selectedTopic
      await dataManager.getFeed(
        'world', 
        topicSlug,
        1, // page 1
        10, // page size
        { forceRefresh: true }
      )
    } catch (error) {
      console.error('Failed to refresh world feed:', error)
    } finally {
      setIsRefreshing(false)
    }
  }
  
  // Handle search debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
    }, 500) // 500ms debounce
    
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Note: Loading state is now handled by InfiniteNewsFeed component
  // No need for page-level loading skeleton

  // Show error state if preferences failed to load and we're online
  if (preferencesError && isOnline && !userPreferences) {
    return (
      <div className="container py-6">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight">Top Headlines</h1>
              
              {/* Desktop refresh button */}
              <Button
                onClick={handleRefresh}
                disabled={isRefreshing}
                variant="ghost"
                size="sm"
                className="hidden md:flex text-muted-foreground hover:text-foreground"
              >
                <RefreshCw className={`h-4 w-4 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'Updating...' : 'Refresh'}
              </Button>
            </div>
          </div>
          <Alert variant="destructive">
            <AlertDescription>
              {preferencesError}. Please refresh the page to try again.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    )
  }

  // Show message if user has no region preferences (and we have loaded preferences)
  if (userPreferences && userPreferences.regions.length === 0) {
    return (
      <div className="container py-6">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight">Top Headlines</h1>
              
              {/* Desktop refresh button */}
              <Button
                onClick={handleRefresh}
                disabled={isRefreshing}
                variant="ghost"
                size="sm"
                className="hidden md:flex text-muted-foreground hover:text-foreground"
              >
                <RefreshCw className={`h-4 w-4 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'Updating...' : 'Refresh'}
              </Button>
            </div>
          </div>
          <Alert>
            <AlertDescription>
              No region preferences found. Please update your preferences to see headlines from your preferred regions.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    )
  }
  
  return (
    <div className="container py-6">
      <div className="flex flex-col gap-6">
        {/* Header with offline indicator */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">Top Headlines</h1>
            
            {/* Desktop refresh button */}
            <Button
              onClick={handleRefresh}
              disabled={isRefreshing}
              variant="ghost"
              size="sm"
              className="hidden md:flex text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className={`h-4 w-4 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Updating...' : 'Refresh'}
            </Button>
            
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
          <div className="relative w-full sm:w-[300px]">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              type="search" 
              placeholder="Search headlines..." 
              className="w-full pl-8"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Offline notice */}
        {!isOnline && (
          <Alert>
            <WifiOff className="h-4 w-4" />
            <AlertDescription>
              You're offline. Showing cached headlines. Connect to the internet to get the latest updates.
            </AlertDescription>
          </Alert>
        )}

        <Tabs 
          defaultValue="all"
          value={selectedTopic}
          onValueChange={setSelectedTopic}
        >
          <TabsList className="mb-4 overflow-auto py-1 w-full justify-start">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="business">Business</TabsTrigger>
            <TabsTrigger value="technology">Technology</TabsTrigger>
            <TabsTrigger value="science">Science</TabsTrigger>
            <TabsTrigger value="health">Health</TabsTrigger>
            <TabsTrigger value="entertainment">Entertainment</TabsTrigger>
            <TabsTrigger value="sports">Sports</TabsTrigger>
          </TabsList>
          <TabsContent value={selectedTopic}>
            <InfiniteNewsFeed 
              feedType="world"
              topicSlug={selectedTopic}
              searchQuery={debouncedSearch}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}


