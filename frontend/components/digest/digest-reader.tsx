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
  const [imageError, setImageError] = useState(false)

  // Get first article with image for cover
  const coverArticle = story.articles?.find(article => article.imageUrl && !imageError)
  const hasImage = coverArticle?.imageUrl && !imageError
  const imageCount = story.articles?.length || 0

  return (
    <Card className={cn(
      "border border-muted/30 bg-card/50 backdrop-blur-sm overflow-hidden",
      "transition-all duration-200 ease-in-out",
      "hover:border-muted/50 hover:shadow-sm",
      "max-w-none md:max-w-xl lg:max-w-2xl mx-auto" // Reduced desktop max-width
    )}>
      {/* Image section - always on top for both mobile and desktop */}
      {hasImage && (
        <div className="w-full h-48 md:h-64 lg:h-72 relative overflow-hidden">
          <div 
            className="w-full h-full bg-cover bg-center" 
            style={{ 
              backgroundImage: `url(${coverArticle.imageUrl})`, 
              backgroundPosition: 'center',
              backgroundSize: 'cover'
            }}
            role="img"
            aria-label={story.title}
            onError={() => setImageError(true)}
          />
          {/* Image count badge */}
          {imageCount > 1 && (
            <div className="absolute top-3 right-3 md:top-4 md:right-4">
              <Badge className="h-5 px-2 md:h-6 md:px-3 text-xs md:text-sm bg-black/70 text-white border-none backdrop-blur-sm">
                +{imageCount - 1} more
              </Badge>
            </div>
          )}
        </div>
      )}

      {/* Content section - always full width below image */}
      <div className="w-full">
        <CardHeader className="pb-3 px-4 pt-4 md:px-6 md:pt-6 lg:px-8">
          <div className="space-y-2 md:space-y-3">
            <h4 className="text-base md:text-lg lg:text-xl font-semibold tracking-tight leading-tight text-foreground">
              {story.title}
            </h4>
            
            {/* Story abstract - always visible */}
            <div className="prose prose-sm md:prose-base max-w-none dark:prose-invert">
              <p className="text-sm md:text-base lg:text-lg text-muted-foreground leading-relaxed m-0">
                {story.abstract}
              </p>
            </div>
          </div>
        </CardHeader>

        {/* Expandable content */}
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <CardContent className="pt-0 px-4 pb-4 md:px-6 md:pb-6 lg:px-8">
            <CollapsibleContent className="space-y-3 md:space-y-4">
              {/* Key Facts */}
              {story.key_facts && story.key_facts.length > 0 && (
                <div className="space-y-2 md:space-y-3">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="h-3.5 w-3.5 md:h-4 md:w-4 text-primary" />
                    <span className="text-sm md:text-base font-medium text-foreground">Key Facts</span>
                  </div>
                  <div className="space-y-1.5 md:space-y-2 pl-4 md:pl-5 lg:pl-6">
                    {story.key_facts.map((fact, index) => (
                      <div key={index} className="flex items-start gap-2 md:gap-3 text-sm md:text-base">
                        <div className="h-1.5 w-1.5 md:h-2 md:w-2 rounded-full bg-primary mt-1.5 md:mt-2 shrink-0" />
                        <span className="text-muted-foreground leading-relaxed">{fact}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Perspectives */}
              {story.perspectives && story.perspectives.length > 0 && (
                <div className="space-y-2 md:space-y-3">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-3.5 w-3.5 md:h-4 md:w-4 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm md:text-base font-medium text-foreground">Perspectives</span>
                  </div>
                  <div className="pl-4 md:pl-5 lg:pl-6 space-y-1.5 md:space-y-2">
                    {story.perspectives.map((perspective, index) => (
                      <blockquote key={index} className="text-sm md:text-base text-muted-foreground italic border-none p-0 m-0 leading-relaxed">
                        "{perspective}"
                      </blockquote>
                    ))}
                  </div>
                </div>
              )}

              {/* Sources section - Perplexity style */}
              {story.articles && story.articles.length > 0 && (
                <div className="space-y-2 md:space-y-3 pt-2 border-t border-muted/30">
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-3.5 w-3.5 md:h-4 md:w-4 text-muted-foreground" />
                    <span className="text-sm md:text-base font-medium text-foreground">Sources</span>
                  </div>
                  <div className="grid gap-2 pl-4 md:pl-5 lg:pl-6">
                    {story.articles.map((article, index) => (
                      <div key={article.id} className="flex items-start gap-2 md:gap-3 p-2 md:p-3 rounded-md bg-muted/20 hover:bg-muted/30 transition-colors">
                        <Badge variant="outline" className="text-xs w-5 h-5 md:w-6 md:h-6 p-0 flex items-center justify-center shrink-0 mt-0.5">
                          {index + 1}
                        </Badge>
                        <div className="flex-1 min-w-0">
                          <Link href={article.url} target="_blank" rel="noopener noreferrer" className="group">
                            <p className="text-sm md:text-base font-medium text-foreground group-hover:text-primary transition-colors line-clamp-1">
                              {article.title}
                            </p>
                            <p className="text-xs md:text-sm text-muted-foreground mt-0.5">
                              {article.publication} • {article.published_at ? new Date(article.published_at).toLocaleDateString() : 'Unknown date'}
                            </p>
                          </Link>
                        </div>
                        <ExternalLink className="h-3 w-3 md:h-4 md:w-4 text-muted-foreground shrink-0 mt-1" />
                      </div>
                    ))}
                  </div>
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
                  <span>{isExpanded ? 'View less' : 'View more'}</span>
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
  // Reading time calculation
  const readingTime = React.useMemo(() => {
    const wordsPerMinute = 200
    let totalWords = digest.introduction.split(' ').length
    
    digest.topics.forEach(topic => {
      totalWords += topic.abstract.split(' ').length
      topic.stories.forEach(story => {
        totalWords += story.abstract.split(' ').length
        totalWords += story.key_facts.join(' ').split(' ').length
      })
    })
    
    return Math.max(1, Math.ceil(totalWords / wordsPerMinute))
  }, [digest])

  return (
    <div className="min-h-screen bg-background">
      {/* Header - Exact article page pattern */}
      <div className={cn(
        "container px-4 md:px-6 lg:px-8",
        "max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto",
        "pt-6 md:pt-8"
      )}>
        <div className="space-y-4">
          {/* Metadata breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Newspaper className="h-4 w-4" />
            <span>Daily Brief</span>
            <span>•</span>
            <time>{new Date(digest.date).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric', 
              month: 'long',
              day: 'numeric'
            })}</time>
            <span>•</span>
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{readingTime} min read</span>
            </div>
          </div>
          
          {/* Title */}
          <header>
            <h1 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black tracking-tight leading-tight text-foreground">
              {digest.title}
            </h1>
            
            {/* Introduction */}
            <div className="mt-4 md:mt-6">
              <div className="prose prose-gray max-w-none dark:prose-invert prose-lg md:prose-xl lg:prose-2xl">
                <p className="text-muted-foreground leading-relaxed m-0">
                  {digest.introduction}
                </p>
              </div>
            </div>
          </header>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            <Button 
              variant="ghost" 
              size="sm"
              className={cn(
                "transition-colors duration-200 ease-in-out",
                "hover:bg-muted/50",
                "focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:ring-offset-2"
              )}
            >
              <Share className="h-4 w-4 mr-2" />
              Share
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className={cn(
        "container px-4 md:px-6 lg:px-8 mt-8 pb-20 md:pb-8",
        "max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto"
      )}>
        <div className="space-y-16">
          {digest.topics.map((topic, topicIndex) => (
            <section 
              key={topic.id} 
              className={cn(
                "space-y-6",
                topicIndex > 0 && "pt-16 border-t-2 border-muted/50"
              )}
            >
              {/* Topic Header - Clear hierarchy */}
              <header className="space-y-4 pb-2">
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold tracking-tight text-foreground">
                    {topic.title}
                  </h2>
                </div>
                <div className="prose prose-gray max-w-none dark:prose-invert prose-base md:prose-lg">
                  <p className="text-muted-foreground leading-relaxed m-0">
                    {topic.abstract}
                  </p>
                </div>
              </header>

              {/* Topic Stories - Card grid */}
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
            </section>
          ))}
        </div>
      </div>

      {/* Back to Top */}
      <BackToTop showAfter={300} />
    </div>
  )
} 