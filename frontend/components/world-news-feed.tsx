"use client"

import { InfiniteNewsFeed } from "@/components/infinite-news-feed"

interface WorldNewsFeedProps {
  publicMode?: boolean; // New prop to enable public/unauthenticated mode
}

export function WorldNewsFeed({ publicMode = false }: WorldNewsFeedProps) {
  return (
    <section className="py-16 bg-muted/30">
      <div className="container max-w-4xl">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold tracking-tight mb-4">
            Latest World Headlines
          </h2>
          <p className="text-lg text-muted-foreground">
            Stay informed with the most important stories from around the world
          </p>
        </div>
        
        <div className="space-y-6">
          <InfiniteNewsFeed 
            feedType="world" 
            sortOrder="newest"
            publicMode={publicMode}
          />
        </div>
      </div>
    </section>
  )
} 