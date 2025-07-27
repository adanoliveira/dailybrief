"use client"

import { useState, useEffect } from "react"

import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Search } from "lucide-react"
import { InfiniteNewsFeed } from "@/components/infinite-news-feed"
import { Skeleton } from "@/components/ui/skeleton"
import { useUser } from "@/lib/user-context"

export default function World() {
  const { userPreferences, isPreferencesLoading } = useUser()
  const [selectedTopic, setSelectedTopic] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  
  // Handle search debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
    }, 500) // 500ms debounce
    
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Show loading state while preferences are being fetched
  if (isPreferencesLoading) {
    return (
      <div className="container py-6">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-10 w-full sm:w-[300px]" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </div>
    )
  }

  // Show message if user has no region preferences
  if (userPreferences && userPreferences.regions.length === 0) {
    return (
      <div className="container py-6">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h1 className="text-2xl font-bold tracking-tight">Top Headlines</h1>
          </div>
          <div className="bg-yellow-100/50 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200 p-4 rounded-md">
            <p>
              No region preferences found. Please update your preferences to see headlines from your preferred regions.
            </p>
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="container py-6">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold tracking-tight">Top Headlines</h1>
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


