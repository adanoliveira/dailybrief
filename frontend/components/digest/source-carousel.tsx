"use client"

import React, { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { MoreHorizontal } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import type { DigestArticle } from "@/lib/digest-service"

interface SourceCarouselProps {
  articles: DigestArticle[];
  className?: string;
}

interface SourceCardProps {
  article: DigestArticle;
  index: number;
  variant?: 'carousel' | 'popover';
}

function getPublicationInitials(publication: string | null | undefined): string {
  if (!publication) return 'N/A';
  
  return publication
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .substring(0, 2)
    .toUpperCase();
}

function SmallFavicon({ article }: { article: DigestArticle }) {
  const [faviconError, setFaviconError] = useState(false);
  const faviconUrl = article.publicationLogoUrl;
  const initials = getPublicationInitials(article.publication);

  return (
    <div className="w-4 h-4 rounded-full bg-background border border-background flex items-center justify-center overflow-hidden">
      {faviconUrl && !faviconError ? (
        <img
          src={faviconUrl}
          alt={article.publication || 'Unknown'}
          className="w-full h-full object-cover"
          onError={() => setFaviconError(true)}
        />
      ) : (
        <span className="text-[6px] font-bold text-muted-foreground">
          {initials}
        </span>
      )}
    </div>
  );
}

function SourceCard({ article, index, variant = 'carousel' }: SourceCardProps) {
  const [imageError, setImageError] = useState(false);
  const [faviconError, setFaviconError] = useState(false);
  const isCarousel = variant === 'carousel';
  const faviconUrl = article.publicationLogoUrl;
  const initials = getPublicationInitials(article.publication);

  return (
    <Link 
      href={`/article/${article.id}`}
      className={cn(
        "group block",
        isCarousel ? "flex-shrink-0" : "w-full"
      )}
    >
      <div className={cn(
        "border border-muted/30 rounded-lg p-2 bg-background hover:bg-muted/20 transition-all duration-200",
        "hover:border-muted/50 hover:shadow-sm dark:hover:shadow-white/10",
        isCarousel ? "w-36" : "w-full"
      )}>
        {/* Header with favicon, publication name and number */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 min-w-0 flex-1">
            {/* Publication favicon */}
            <div className="w-3 h-3 rounded-full bg-muted/50 flex items-center justify-center overflow-hidden flex-shrink-0">
              {faviconUrl && !faviconError ? (
                <img
                  src={faviconUrl}
                  alt={article.publication || 'Unknown'}
                  className="w-full h-full object-cover"
                  onError={() => setFaviconError(true)}
                />
              ) : (
                <span className="text-[6px] font-bold text-muted-foreground">
                  {initials}
                </span>
              )}
            </div>
            {/* Publication name - muted */}
            <span className="text-[10px] text-muted-foreground truncate">
              {article.publication || 'Unknown'}
            </span>
          </div>
        </div>

        {/* Content area with thumbnail alongside title */}
        <div className="flex gap-2">
          {/* Thumbnail on the left */}
          {article.imageUrl && !imageError && (
            <div className="flex-shrink-0">
              <img
                src={article.imageUrl}
                alt={article.title}
                className="w-12 h-12 object-cover rounded"
                onError={() => setImageError(true)}
              />
            </div>
          )}
          
          {/* Title on the right */}
          <div className="flex-1 min-w-0">
            <h4 className={cn(
              "text-xs font-medium text-foreground group-hover:text-primary transition-colors",
              isCarousel ? "line-clamp-3" : "line-clamp-4"
            )}>
              {article.title}
            </h4>
          </div>
        </div>
      </div>
    </Link>
  );
}

export function SourceCarousel({ articles, className }: SourceCarouselProps) {
  const [popoverOpen, setPopoverOpen] = useState(false);
  
  if (!articles || articles.length === 0) {
    return null;
  }

  // Show first 3 sources in carousel, rest in popover
  const carouselSources = articles.slice(0, 3);
  const remainingSources = articles.slice(3);
  const hasMoreSources = remainingSources.length > 0;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center gap-2">
        <h5 className="text-base md:text-lg font-bold text-foreground">Sources</h5>
      </div>
      
      {/* Horizontal scrolling carousel */}
      <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-2">
        {/* Main source cards */}
        {carouselSources.map((article, index) => (
          <SourceCard
            key={article.id}
            article={article}
            index={index}
            variant="carousel"
          />
        ))}

        {/* More sources aggregate card */}
        {hasMoreSources && (
          <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
            <PopoverTrigger asChild>
              <div className="flex-shrink-0">
                <Button
                  variant="outline"
                  className="w-36 h-full min-h-[80px] border-muted/30 hover:bg-muted/20 transition-all duration-200 hover:border-muted/50 hover:shadow-sm"
                >
                  <div className="flex flex-col items-center justify-center gap-2 p-2">
                    <div className="flex items-center gap-1">
                      {/* Show up to 3 small favicons */}
                      {remainingSources.slice(0, 3).map((article, index) => (
                        <SmallFavicon key={article.id} article={article} />
                      ))}
                      {remainingSources.length > 3 && (
                        <MoreHorizontal className="w-4 h-4 text-muted-foreground" />
                      )}
                    </div>
                    <span className="text-xs font-medium text-muted-foreground">
                      +{remainingSources.length} sources
                    </span>
                  </div>
                </Button>
              </div>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-0" align="start">
              <div className="p-3">
                <h6 className="font-medium text-sm mb-3 text-foreground">All Sources</h6>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {remainingSources.map((article, index) => (
                    <SourceCard
                      key={article.id}
                      article={article}
                      index={carouselSources.length + index}
                      variant="popover"
                    />
                  ))}
                </div>
              </div>
            </PopoverContent>
          </Popover>
        )}
      </div>
    </div>
  );
}
