"use client"

import React, { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { 
  ChevronDown, 
  ChevronUp, 
  ChevronLeft,
  ChevronRight,
  Clock, 
  Newspaper,
  ExternalLink,
  Share,
  BookOpen,
  Lightbulb,
  MessageSquare,
  Image as ImageIcon,
  MoreHorizontal
} from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { BackToTop } from "@/components/ui/back-to-top"
import { SourceCarousel } from "@/components/digest/source-carousel"
import { DigestHeader } from "@/components/digest/digest-header"
import { DigestActionBar } from "@/components/digest/digest-action-bar"
import { TopicNavigation } from "@/components/digest/topic-navigation"
import type { Digest, DigestTopic, DigestStory } from "@/lib/digest-service"

interface DigestReaderProps {
  digest: Digest
  className?: string
}

interface DigestStoryCardProps {
  story: DigestStory
  topicIndex: number
  storyIndex: number
}

function DigestStoryCard({ story, topicIndex, storyIndex }: DigestStoryCardProps) {
  // Smart defaults: Auto-expand first story of first topic
  const shouldAutoExpand = topicIndex === 0 && storyIndex === 0
  const [isExpanded, setIsExpanded] = useState(shouldAutoExpand)
  const [failedImages, setFailedImages] = useState<Set<string>>(new Set())
  const [currentImageIndex, setCurrentImageIndex] = useState(0)

  // Get articles with images (excluding failed ones) - limit to 3 for slider
  const articlesWithImages = (story.articles?.filter(article => 
    article.imageUrl && !failedImages.has(article.imageUrl)
  ) || []).slice(0, 3)
  
  // Get first available image for cover
  const coverArticle = articlesWithImages[currentImageIndex]
  const hasImage = !!coverArticle?.imageUrl
  const imageCount = articlesWithImages.length
  const hasMultipleImages = imageCount > 1

  const handleImageError = (imageUrl: string) => {
    console.log('Image failed to load:', imageUrl)
    setFailedImages(prev => new Set([...prev, imageUrl]))
    // If current image failed and there are others, move to next
    if (currentImageIndex < articlesWithImages.length - 1) {
      setCurrentImageIndex(prev => prev + 1)
    } else if (currentImageIndex > 0) {
      setCurrentImageIndex(0)
    }
  }

  const goToPrevImage = () => {
    setCurrentImageIndex(prev => prev === 0 ? imageCount - 1 : prev - 1)
  }

  const goToNextImage = () => {
    setCurrentImageIndex(prev => prev === imageCount - 1 ? 0 : prev + 1)
  }

  return (
    <Card className={cn(
      "border border-muted/30 bg-card/50 backdrop-blur-sm overflow-hidden",
      "transition-all duration-200 ease-in-out",
      "hover:border-muted/50 hover:shadow-sm dark:hover:shadow-white/8",
      "max-w-none md:max-w-xl lg:max-w-2xl mx-auto" // Reduced desktop max-width
    )}>
      {/* Image section - always on top for both mobile and desktop */}
      {hasImage && coverArticle?.imageUrl && (
        <div className="w-full h-48 md:h-64 lg:h-72 relative overflow-hidden bg-muted/10">
          <img
            src={coverArticle.imageUrl}
            alt={story.title}
            className="w-full h-full object-cover"
            onError={() => {
              if (coverArticle.imageUrl) {
                handleImageError(coverArticle.imageUrl)
              }
            }}
            onLoad={() => console.log('Image loaded successfully:', coverArticle.imageUrl)}
          />
          
          {/* Navigation arrows - only show if multiple images */}
          {hasMultipleImages && (
            <>
              <button
                onClick={goToPrevImage}
                className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 md:w-10 md:h-10 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center transition-colors backdrop-blur-sm"
                aria-label="Previous image"
              >
                <ChevronLeft className="h-4 w-4 md:h-5 md:w-5 text-white" />
              </button>
              <button
                onClick={goToNextImage}
                className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 md:w-10 md:h-10 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center transition-colors backdrop-blur-sm"
                aria-label="Next image"
              >
                <ChevronRight className="h-4 w-4 md:h-5 md:w-5 text-white" />
              </button>
            </>
          )}
          
          {/* Image indicators - show current position */}
          {hasMultipleImages && (
            <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
              {articlesWithImages.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentImageIndex(index)}
                  className={cn(
                    "w-2 h-2 rounded-full transition-colors",
                    index === currentImageIndex 
                      ? "bg-white" 
                      : "bg-white/50 hover:bg-white/70"
                  )}
                  aria-label={`Go to image ${index + 1}`}
                />
              ))}
            </div>
          )}
          
          {/* Image count badge - updated to show current/total */}
          {imageCount > 1 && (
            <div className="absolute top-3 right-3 md:top-4 md:right-4">
              <Badge className="h-5 px-2 md:h-6 md:px-3 text-xs md:text-sm bg-black/70 text-white border-none backdrop-blur-sm">
                {currentImageIndex + 1} of {imageCount}
              </Badge>
            </div>
          )}
        </div>
      )}

      {/* Content section - always full width below image */}
      <div className="w-full">
        <CardHeader className="pb-3 px-4 pt-4 md:px-6 md:pt-6 lg:px-8">
          <div className="space-y-2 md:space-y-3">
            <h4 className="text-lg md:text-xl lg:text-2xl xl:text-3xl font-black tracking-tight leading-tight text-foreground">
              {story.title}
            </h4>
            
            {/* Story abstract - always visible */}
            <div className="max-w-none">
              <p className="text-lg md:text-xl lg:text-xl text-foreground leading-relaxed m-0 article-content-font">
                {story.abstract}
              </p>
            </div>
          </div>
        </CardHeader>

        {/* Expandable content */}
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <CardContent className="pt-0 px-4 pb-4 md:px-6 md:pb-6 lg:px-8">
            
            {/* Collapsed preview of Main Takeaways */}
            {!isExpanded && story.key_facts && story.key_facts.length > 0 && (
              <div className="space-y-2 md:space-y-3 mb-3 md:mb-4">
                <div className="flex items-center gap-2">
                  <h5 className="text-base md:text-lg font-bold text-foreground">Main Takeaways</h5>
                </div>
                <div className="relative">
                  <div className="space-y-1.5 md:space-y-2 pl-4 md:pl-5 lg:pl-6">
                    <div className="flex items-start gap-2 md:gap-3 text-lg md:text-xl lg:text-xl">
                      <div className="h-1.5 w-1.5 md:h-2 md:w-2 rounded-full bg-primary mt-1.5 md:mt-2 shrink-0" />
                      <span className="text-foreground leading-relaxed article-content-font">
                        {story.key_facts[0].length > 50 
                          ? `${story.key_facts[0].substring(0, 50)}...` 
                          : story.key_facts[0]
                        }
                      </span>
                    </div>
                  </div>
                  
                  {/* Gradient overlay - theme-aware with larger shadow */}
                  <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-card to-transparent pointer-events-none" />
                </div>
              </div>
            )}

            <CollapsibleContent className="space-y-3 md:space-y-4">
              {/* Key Facts - Full version when expanded */}
              {story.key_facts && story.key_facts.length > 0 && (
                <div className="space-y-2 md:space-y-3">
                  <div className="flex items-center gap-2">
                    <h5 className="text-base md:text-lg font-bold text-foreground">Main Takeaways</h5>
                  </div>
                  <div className="space-y-1.5 md:space-y-2 pl-4 md:pl-5 lg:pl-6">
                    {story.key_facts.map((fact, index) => (
                      <div key={index} className="flex items-start gap-2 md:gap-3 text-lg md:text-xl lg:text-xl">
                        <div className="h-1.5 w-1.5 md:h-2 md:w-2 rounded-full bg-primary mt-1.5 md:mt-2 shrink-0" />
                        <span className="text-foreground leading-relaxed article-content-font">{fact}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Perspectives */}
              {story.perspectives && story.perspectives.length > 0 && (
                <div className="space-y-2 md:space-y-3">
                  <div className="flex items-center gap-2">
                    <h5 className="text-base md:text-lg font-bold text-foreground">Key Perspectives</h5>
                  </div>
                  <div className="pl-4 md:pl-5 lg:pl-6 space-y-1.5 md:space-y-2">
                    {story.perspectives.map((perspective, index) => (
                      <blockquote key={index} className="text-lg md:text-xl lg:text-xl text-foreground italic border-none p-0 m-0 leading-relaxed article-content-font">
                        "{perspective}"
                      </blockquote>
                    ))}
                  </div>
                </div>
              )}

              {/* Sources section - Perplexity style carousel */}
              {story.articles && story.articles.length > 0 && (
                <div className="space-y-2 md:space-y-3 pt-2 border-t border-muted/30">
                  <SourceCarousel articles={story.articles} />
                </div>
              )}
            </CollapsibleContent>

            {/* Expand/Collapse button */}
            <div className="pt-2 md:pt-3">
              <CollapsibleTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm"
     className={cn(
                    "w-full h-8 md:h-9 text-sm md:text-base font-medium",
                    "transition-all duration-200 ease-in-out",
                    "hover:bg-muted/50 border border-muted/30 hover:border-muted/50",
                    "focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:ring-offset-2"
                  )}
                >
                  <span>{isExpanded ? 'View less' : 'Read more'}</span>
                  <div className="transition-transform duration-200 ease-in-out ml-2">
                    {isExpanded ? (
                      <ChevronUp className="h-3 w-3 md:h-4 md:w-4" />
                    ) : (
                      <ChevronDown className="h-3 w-3 md:h-4 md:w-4" />
                    )}
                  </div>
                </Button>
              </CollapsibleTrigger>
            </div>
          </CardContent>
        </Collapsible>
      </div>
    </Card>
  )
}

export function DigestReader({ digest, className }: DigestReaderProps) {
  // Get reading time from backend
  const readingTime = digest.metrics.reading_time_minutes || 1

  return (
    <div className="min-h-screen bg-background">
      {/* Header container */}
      <div className={cn(
        "container px-4 md:px-6 lg:px-8",
        "max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto",
        "pt-6 md:pt-8"
      )}>
        
        {/* 1. Digest Action Bar (first block) */}
        <DigestActionBar digest={digest} />
        
        {/* 2. Digest Header (second block) */}
        <div className={cn(
          "space-y-4 mt-2 md:mt-6"
        )}>
          <DigestHeader digest={digest} />
          
          {/* Introduction - below header */}
          <div className="max-w-none">
            <p className="text-lg md:text-xl lg:text-xl text-muted-foreground leading-relaxed m-0 article-content-font">
              {digest.introduction}
            </p>
          </div>
        </div>
      </div>

      {/* Topic Navigation - Sticky carousel */}
      <div className="mt-2">
        <TopicNavigation topics={digest.topics} />
      </div>

      {/* Content */}
      <div className={cn(
        "container px-4 md:px-6 lg:px-8 mt-6 pb-20",
        "max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto"
      )}>
        <div className="space-y-10">
          {digest.topics.map((topic, topicIndex) => (
            <section 
              key={topic.id}
              id={`topic-${topic.id}`}
              className={cn(
                "space-y-6",
                topicIndex > 0 && "pt-8"
              )}
            >
              {/* Topic Header - Clear hierarchy */}
              <header className="space-y-4 pb-2">
                <div className="flex items-center gap-3">
                  <h2 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black tracking-tight text-foreground">
                    {topic.title}
                  </h2>
                </div>
                <div className="max-w-none">
                  <p className="text-lg md:text-xl lg:text-xl text-foreground leading-relaxed m-0 article-content-font">
                    {topic.abstract}
                  </p>
                </div>
              </header>

              {/* Top Stories Section */}
              {topic.stories && topic.stories.length > 0 && (
                <div className="space-y-4">
                  {/* Top Stories Heading */}
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl md:text-2xl lg:text-3xl xl:text-4xl font-black tracking-tight text-foreground">
                      Top Stories
                    </h3>
                  </div>
                  
                  {/* Story Cards */}
                  <div className="space-y-4 pl-0 md:pl-4">
                    {topic.stories.map((story, storyIndex) => (
                      <DigestStoryCard 
                        key={story.id} 
                        story={story}
                        topicIndex={topicIndex}
                        storyIndex={storyIndex}
                      />
                    ))}
                  </div>
                </div>
              )}
            </section>
          ))}
        </div>

        {/* Conclusion Section */}
        {digest.conclusion && (
          <section className="mt-16 space-y-4">
            <div className="max-w-none">
              <p className="text-lg md:text-xl lg:text-xl text-foreground leading-relaxed m-0 article-content-font">
                {digest.conclusion}
              </p>
            </div>
          </section>
        )}
      </div>

      {/* Back to Top */}
      <BackToTop showAfter={300} />
    </div>
  )
} 