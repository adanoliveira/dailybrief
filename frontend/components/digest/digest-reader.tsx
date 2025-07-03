"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  TrendingUp, 
  Newspaper,
  ExternalLink,
  Share,
  BookOpen,
  Eye,
  Lightbulb,
  MessageSquare
} from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import type { Digest, DigestTopic, DigestStory } from "@/lib/digest-service"

interface DigestReaderProps {
  digest: Digest
  className?: string
}

interface DigestTopicCardProps {
  topic: DigestTopic
  isExpanded: boolean
  onToggle: () => void
}

interface DigestStoryCardProps {
  story: DigestStory
}

function DigestStoryCard({ story }: DigestStoryCardProps) {
  const [showKeyFacts, setShowKeyFacts] = useState(false)
  const [showPerspectives, setShowPerspectives] = useState(false)

  return (
    <Card className="border-l-4 border-l-primary/20">
      <CardContent className="pt-4">
        <div className="space-y-3">
          <div>
            <h3 className="font-semibold text-lg leading-tight mb-2">
              {story.title}
            </h3>
            <p className="text-muted-foreground leading-relaxed">
              {story.abstract}
            </p>
          </div>

          {story.key_facts && story.key_facts.length > 0 && (
            <Collapsible open={showKeyFacts} onOpenChange={setShowKeyFacts}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="h-auto p-0 font-normal">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="h-4 w-4" />
                    <span>Key Facts ({story.key_facts.length})</span>
                    {showKeyFacts ? (
                      <ChevronUp className="h-3 w-3" />
                    ) : (
                      <ChevronDown className="h-3 w-3" />
                    )}
                  </div>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="mt-2 space-y-2">
                  {story.key_facts.map((fact, index) => (
                    <div key={index} className="flex items-start gap-2 text-sm p-2 bg-muted/30 rounded">
                      <div className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                      <span>{fact}</span>
                    </div>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}

          {story.perspectives && story.perspectives.length > 0 && (
            <Collapsible open={showPerspectives} onOpenChange={setShowPerspectives}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="h-auto p-0 font-normal">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    <span>Perspectives ({story.perspectives.length})</span>
                    {showPerspectives ? (
                      <ChevronUp className="h-3 w-3" />
                    ) : (
                      <ChevronDown className="h-3 w-3" />
                    )}
                  </div>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="mt-2 space-y-2">
                  {story.perspectives.map((perspective, index) => (
                    <div key={index} className="text-sm p-2 bg-blue-50 dark:bg-blue-950/20 rounded border-l-2 border-blue-200 dark:border-blue-800">
                      <span className="italic">"{perspective}"</span>
                    </div>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}
        </div>

        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-muted-foreground">
            {story.article_count} {story.article_count === 1 ? 'article' : 'articles'}
          </div>
          {story.articles && story.articles.length > 0 && (
            <Button variant="outline" size="sm" className="h-7 text-xs">
              <BookOpen className="h-3 w-3 mr-1" />
              Read Sources
              <ExternalLink className="h-3 w-3 ml-1" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function DigestTopicCard({ topic, isExpanded, onToggle }: DigestTopicCardProps) {
  return (
    <div className="space-y-4">
      <Card className="overflow-hidden">
        <Collapsible open={isExpanded} onOpenChange={onToggle}>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CardTitle className="text-xl">{topic.title}</CardTitle>
                  <Badge variant="outline">
                    {topic.stories.length} {topic.stories.length === 1 ? 'story' : 'stories'}
                  </Badge>
                </div>
                {isExpanded ? (
                  <ChevronUp className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
              <p className="text-muted-foreground text-left">{topic.abstract}</p>
            </CardHeader>
          </CollapsibleTrigger>
          
          <CollapsibleContent>
            <CardContent className="pt-0">
              <Separator className="mb-4" />
              
              <div className="space-y-4">
                {topic.stories.map((story) => (
                  <DigestStoryCard 
                    key={story.id} 
                    story={story}
                  />
                ))}
              </div>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    </div>
  )
}

export function DigestReader({ digest, className }: DigestReaderProps) {
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set())
  
  const toggleTopic = (topicId: string) => {
    const newExpanded = new Set(expandedTopics)
    if (newExpanded.has(topicId)) {
      newExpanded.delete(topicId)
    } else {
      newExpanded.add(topicId)
    }
    setExpandedTopics(newExpanded)
  }

  const expandAll = () => {
    setExpandedTopics(new Set(digest.topics.map(t => t.id)))
  }

  const collapseAll = () => {
    setExpandedTopics(new Set())
  }

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
    <div className={cn("space-y-6", className)}>
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Newspaper className="h-4 w-4" />
          <span>Daily Brief</span>
          <span>•</span>
          <span>{new Date(digest.date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric', 
            month: 'long',
            day: 'numeric'
          })}</span>
          <span>•</span>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>{readingTime} min read</span>
          </div>
        </div>
        
        <div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl mb-3">
            {digest.title}
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            {digest.introduction}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">
            {digest.metrics.topics_included} topics
          </Badge>
          <Badge variant="secondary">
            {digest.metrics.events_included} stories
          </Badge>
          <Badge variant="secondary">
            {digest.metrics.articles_processed} articles analyzed
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={expandAll}>
            Expand All
          </Button>
          <Button variant="outline" size="sm" onClick={collapseAll}>
            Collapse All
          </Button>
          <Button variant="ghost" size="sm">
            <Share className="h-4 w-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      <Separator />

      <div className="space-y-6">
        {digest.topics.map((topic) => (
          <DigestTopicCard
            key={topic.id}
            topic={topic}
            isExpanded={expandedTopics.has(topic.id)}
            onToggle={() => toggleTopic(topic.id)}
          />
        ))}
      </div>

      <div className="text-center py-8">
        <div className="text-sm text-muted-foreground space-y-2">
          <p>
            Generated using {digest.metrics.generation_tokens_total.toLocaleString()} AI tokens
          </p>
          <p>
            Last updated: {new Date(digest.updated_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  )
} 