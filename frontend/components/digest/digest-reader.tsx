"use client"

import React, { useState } from 'react'
import { Button } from "@/components/ui/button"
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
  ArrowUp
} from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { BackToTop } from "@/components/ui/back-to-top"
import type { Digest, DigestTopic, DigestStory } from "@/lib/digest-service"

interface DigestReaderProps {
  digest: Digest
  className?: string
}

interface DigestStoryProps {
  story: DigestStory
  isFirst?: boolean
  topicIndex: number
  storyIndex: number
}

function DigestStory({ story, isFirst = false, topicIndex, storyIndex }: DigestStoryProps) {
  // Smart defaults: Auto-expand first story of first topic for immediate engagement
  const shouldAutoExpand = topicIndex === 0 && storyIndex === 0
  const [showKeyFacts, setShowKeyFacts] = useState(shouldAutoExpand)
  const [showPerspectives, setShowPerspectives] = useState(false)

  return (
    <article className={cn(
      "space-y-4 scroll-mt-20", // scroll-mt for navigation offsets
      !isFirst && "pt-8 border-t border-muted/30"
    )}>
      {/* Story Title and Abstract - Article page typography patterns */}
      <header className="space-y-3">
        <h3 className="text-xl md:text-2xl lg:text-3xl font-bold tracking-tight leading-tight text-foreground">
          {story.title}
        </h3>
        <div className="prose prose-gray max-w-none dark:prose-invert prose-base md:prose-lg lg:prose-xl">
          <p className="text-muted-foreground leading-relaxed m-0">
            {story.abstract}
          </p>
        </div>
      </header>

      {/* Progressive Disclosure Sections */}
      <div className="space-y-4">
        {/* Key Facts - Enhanced interaction patterns */}
        {story.key_facts && story.key_facts.length > 0 && (
          <section className="space-y-3">
            <Collapsible open={showKeyFacts} onOpenChange={setShowKeyFacts}>
              <CollapsibleTrigger asChild>
                <Button 
                  variant="ghost" 
                  className={cn(
                    "h-auto p-0 font-medium text-left hover:bg-transparent",
                    "transition-colors duration-200 ease-in-out",
                    "focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:ring-offset-2",
                    "group" // For group hover effects
                  )}
                >
                  <div className="flex items-center gap-2 text-sm">
                    <Lightbulb className={cn(
                      "h-4 w-4 transition-colors",
                      showKeyFacts ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                    )} />
                    <span>Key Facts ({story.key_facts.length})</span>
                    <div className="transition-transform duration-200 ease-in-out">
                      {showKeyFacts ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                    </div>
                  </div>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="transition-all duration-300 ease-in-out data-[state=closed]:animate-out data-[state=open]:animate-in">
                <div className="mt-3 space-y-3 pl-6 border-l-2 border-primary/20">
                  {story.key_facts.map((fact, index) => (
                    <div key={index} className="flex items-start gap-3 text-sm leading-relaxed">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary mt-2 shrink-0" />
                      <span className="prose prose-sm max-w-none dark:prose-invert">{fact}</span>
                    </div>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          </section>
        )}

        {/* Perspectives - Enhanced styling */}
        {story.perspectives && story.perspectives.length > 0 && (
          <section className="space-y-3">
            <Collapsible open={showPerspectives} onOpenChange={setShowPerspectives}>
              <CollapsibleTrigger asChild>
                <Button 
                  variant="ghost" 
                  className={cn(
                    "h-auto p-0 font-medium text-left hover:bg-transparent",
                    "transition-colors duration-200 ease-in-out",
                    "focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:ring-offset-2",
                    "group"
                  )}
                >
                  <div className="flex items-center gap-2 text-sm">
                    <MessageSquare className={cn(
                      "h-4 w-4 transition-colors",
                      showPerspectives ? "text-blue-600 dark:text-blue-400" : "text-muted-foreground group-hover:text-foreground"
                    )} />
                    <span>Perspectives ({story.perspectives.length})</span>
                    <div className="transition-transform duration-200 ease-in-out">
                      {showPerspectives ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                    </div>
                  </div>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="transition-all duration-300 ease-in-out data-[state=closed]:animate-out data-[state=open]:animate-in">
                <div className="mt-3 space-y-3 pl-6 border-l-2 border-blue-200 dark:border-blue-800">
                  {story.perspectives.map((perspective, index) => (
                    <blockquote key={index} className="text-sm leading-relaxed italic text-muted-foreground border-none p-0 m-0">
                      "{perspective}"
                    </blockquote>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          </section>
        )}
      </div>

      {/* Source Articles - Thumb-friendly placement */}
      {story.articles && story.articles.length > 0 && (
        <footer className="pt-3">
          <Button 
            variant="outline" 
            size="sm" 
            className={cn(
              "h-9 px-3 text-sm font-medium",
              "transition-all duration-200 ease-in-out",
              "hover:bg-muted/50 hover:border-primary/40",
              "focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:ring-offset-2"
            )}
          >
            <BookOpen className="h-3 w-3 mr-2" />
            Read Sources ({story.articles.length})
            <ExternalLink className="h-3 w-3 ml-2" />
          </Button>
        </footer>
      )}
    </article>
  )
}

export function DigestReader({ digest, className }: DigestReaderProps) {
  // Reading time calculation - matches article page approach
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
    <div className="min-h-screen">
      {/* Header - Exact article page pattern */}
      <div className={cn(
        "container px-4 md:px-6 lg:px-8",
        "max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto",
        "pt-6 md:pt-8"
      )}>
        <div className="space-y-4">
          {/* Metadata breadcrumb - Article page pattern */}
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
          
          {/* Title - Exact article page typography */}
          <header>
            <h1 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black tracking-tight leading-tight text-foreground">
              {digest.title}
            </h1>
            
            {/* Introduction - Article page prose styling */}
            <div className="mt-4 md:mt-6">
              <div className="prose prose-gray max-w-none dark:prose-invert prose-lg md:prose-xl lg:prose-2xl">
                <p className="text-muted-foreground leading-relaxed m-0">
                  {digest.introduction}
                </p>
              </div>
            </div>
          </header>

          {/* Actions - Thumb-zone optimized */}
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

      {/* Content - Article page container pattern */}
      <div className={cn(
        "container px-4 md:px-6 lg:px-8 mt-8 pb-20 md:pb-8",
        "max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto"
      )}>
        <div className="space-y-12">
          {digest.topics.map((topic, topicIndex) => (
            <section 
              key={topic.id} 
              className={cn(
                "space-y-6",
                topicIndex > 0 && "pt-12 border-t-2 border-muted/50"
              )}
            >
              {/* Topic Header - Progressive hierarchy */}
              <header className="space-y-4">
                <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold tracking-tight text-foreground">
                  {topic.title}
                </h2>
                <div className="prose prose-gray max-w-none dark:prose-invert prose-base md:prose-lg lg:prose-xl">
                  <p className="text-muted-foreground leading-relaxed m-0">
                    {topic.abstract}
                  </p>
                </div>
              </header>

              {/* Topic Stories - Continuous reading flow */}
              <div className="space-y-1">
                {topic.stories.map((story, storyIndex) => (
                  <DigestStory 
                    key={story.id} 
                    story={story}
                    isFirst={storyIndex === 0}
                    topicIndex={topicIndex}
                    storyIndex={storyIndex}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>

      {/* Back to Top - Article page pattern */}
      <BackToTop showAfter={300} />
    </div>
  )
} 