"use client"

import { useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { useSession } from "next-auth/react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Filter, Search } from "lucide-react"
import { DailyDigest } from "@/components/daily-digest"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { InfiniteNewsFeed } from "@/components/infinite-news-feed"
import { api } from "@/lib/api"

export default function Home() {
  const searchParams = useSearchParams()
  const isNewSession = searchParams?.get('new_session') === 'true'
  const { data: session, update: updateSession } = useSession()

  // Check onboarding status directly from backend if this is a new session
  useEffect(() => {
    async function checkOnboardingStatus() {
      if (isNewSession) {
        try {
          console.log("New session detected, checking onboarding status...")
          // Remove the query parameter by replacing the URL without it
          window.history.replaceState({}, document.title, '/home')
          
          // Force session refresh
          await updateSession({ has_completed_onboarding: true })
          console.log("Session updated with completed onboarding")
        } catch (error) {
          console.error("Error updating session:", error)
        }
      }
    }
    
    checkOnboardingStatus()
  }, [isNewSession, updateSession])

  return (
    <div className="container py-6">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold tracking-tight">Your News</h1>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative w-full sm:w-[260px]">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input type="search" placeholder="Search articles..." className="w-full pl-8" />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
              <span className="sr-only">Filter</span>
            </Button>
            <Select defaultValue="relevance">
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

        <Tabs defaultValue="for-you">
          <TabsList className="mb-4 overflow-auto py-1 w-full justify-start">
            <TabsTrigger value="for-you">For You</TabsTrigger>
            <TabsTrigger value="business">Business</TabsTrigger>
            <TabsTrigger value="technology">Technology</TabsTrigger>
            <TabsTrigger value="science">Science</TabsTrigger>
            <TabsTrigger value="health">Health</TabsTrigger>
          </TabsList>
          <TabsContent value="for-you">
            <InfiniteNewsFeed />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
