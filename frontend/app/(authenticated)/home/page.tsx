"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useSession } from "next-auth/react"
import { useUser } from "@/lib/user-context"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Filter, Search } from "lucide-react"
import { DailyDigest } from "@/components/daily-digest"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { InfiniteNewsFeed } from "@/components/infinite-news-feed"
import { useToast } from "@/components/ui/use-toast"

export default function Home() {
  // Declare all hooks at the top level
  const router = useRouter()
  const searchParams = useSearchParams()
  const { data: session } = useSession()
  const { userStatus, isLoading: isLoadingUser } = useUser()
  const { toast } = useToast()
  const [isVerifying, setIsVerifying] = useState(true)
  
  // Article filtering state
  const [selectedTopic, setSelectedTopic] = useState('for-you')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [sortOrder, setSortOrder] = useState<'relevance' | 'newest' | 'oldest'>('relevance')
  
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
    if (userStatus) {
      if (!userStatus.has_completed_onboarding) {
        console.log("Home: User has NOT completed onboarding, redirecting")
        router.replace('/onboarding?skip_check=true')
        return
      }
      
      // User has completed onboarding, allow access to home
      setIsVerifying(false)
    }
    
    // If user status isn't available yet but session is, check localStorage as fallback
    if (!userStatus && session) {
      const hasDoneOnboarding = localStorage.getItem('has_completed_onboarding') === 'true'
      if (!hasDoneOnboarding) {
        console.log("Home: User has NOT completed onboarding (localStorage), redirecting")
        router.replace('/onboarding?skip_check=true')
        return
      }
      
      // Onboarding is complete according to localStorage, allow access to home
      setIsVerifying(false)
    }
  }, [userStatus, isLoadingUser, session, router, searchParams])

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
        <p className="text-muted-foreground">Loading your personalized feed...</p>
      </div>
    </div>
  )

  const renderMainContent = () => (
    <div className="container py-6">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold tracking-tight">Your News</h1>
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
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
              <span className="sr-only">Filter</span>
            </Button>
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

        <DailyDigest />

        <Tabs 
          defaultValue="for-you"
          value={selectedTopic}
          onValueChange={setSelectedTopic}
        >
          <TabsList className="mb-4 overflow-auto py-1 w-full justify-start">
            <TabsTrigger value="for-you">For You</TabsTrigger>
            {userStatus?.topics_details?.map(topic => (
              <TabsTrigger key={topic.id} value={topic.slug}>{topic.name}</TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value={selectedTopic}>
            <InfiniteNewsFeed 
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
