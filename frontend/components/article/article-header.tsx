"use client"

import { Button } from "@/components/ui/button"
import { PublicationBadge } from "@/components/ui/publication-badge"
import { ExternalLink, Clock, ArrowLeft, ThumbsUp, ThumbsDown, Share } from "lucide-react"
import { formatDate, getBestTitle, truncateText } from "@/lib/article-utils"
import { renderWithFormatting } from "@/components/rich-article-renderer"
import { cn } from "@/lib/utils"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"

interface ArticleHeaderProps {
  article: {
    title: string;
    visualTitle?: string;
    author?: string;
    publishedAt: string;
    readTime?: number;
    url: string;
    source: {
      name: string;
      logoUrl?: string;
    };
    topics?: Array<{
      id: number;
      name: string;
      slug: string;
    }>;
  };
  heroImage?: string | null;
  isOverlay?: boolean;
}

interface BackButtonProps {
  variant: "overlay" | "default";
  onClick: () => void;
  label: string;
}

function BackButton({ variant, onClick, label }: BackButtonProps) {
  const isOverlay = variant === "overlay";
  
  return (
    <Button
      variant="ghost"
      size="default"
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 transition-colors h-10 px-3",
        isOverlay 
          ? "text-white hover:text-white/80 bg-black/20 hover:bg-black/40 border border-white/20 hover:border-white/40"
          : "text-muted-foreground hover:text-foreground"
      )}
    >
      <ArrowLeft className="h-5 w-5" />
      <span className="text-sm font-medium">{label}</span>
    </Button>
  );
}

interface ReadOriginalButtonProps {
  variant: "overlay" | "default";
  size: "xs" | "sm";
  onClick: () => void;
  className?: string;
}

function ReadOriginalButton({ variant, size, onClick, className }: ReadOriginalButtonProps) {
  const isOverlay = variant === "overlay";
  
  const baseClassName = cn(
    isOverlay 
      ? "text-white hover:text-white/80 bg-black/20 hover:bg-black/40 border border-white/20 hover:border-white/40"
      : "",
    className
  );
  
  if (isOverlay) {
    return (
      <Button
        variant="ghost"
        size={size}
        onClick={onClick}
        className={baseClassName}
      >
        Read Original
        <ExternalLink />
      </Button>
    );
  }
  
  return (
    <Button
      variant="outline"
      size={size}
      onClick={onClick}
      className={baseClassName}
    >
      Read Original
      <ExternalLink />
    </Button>
  );
}

export function ArticleHeader({ article, heroImage, isOverlay = false }: ArticleHeaderProps) {
  const title = getBestTitle(article);
  const hasHeroImage = Boolean(heroImage);
  const router = useRouter();
  const [liked, setLiked] = useState(false);
  const [disliked, setDisliked] = useState(false);
  const [referrerInfo, setReferrerInfo] = useState<{label: string; path: string} | null>(null);

  const handleLike = () => {
    setLiked(!liked);
    if (disliked) setDisliked(false);
  };

  const handleDislike = () => {
    setDisliked(!disliked);
    if (liked) setLiked(false);
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: title,
          text: `Check out this article from ${article.source.name}`,
          url: window.location.href,
        });
      } catch (err) {
        // User cancelled
      }
    } else {
      // Fallback - copy to clipboard
      try {
        await navigator.clipboard.writeText(window.location.href);
      } catch (err) {
        console.error('Failed to copy to clipboard:', err);
      }
    }
  };

  const handleReadOriginal = () => {
    window.open(article.url, '_blank', 'noopener,noreferrer');
  };

  // Get referrer information for back navigation
  useEffect(() => {
    const getReferrerInfo = () => {
      // First, try to get from sessionStorage (most reliable for SPA navigation)
      const storedReferrer = sessionStorage.getItem('article-referrer');
      if (storedReferrer) {
        try {
          const parsed = JSON.parse(storedReferrer);
          // Only trust /home and /world as valid sources, fallback to /home for others
          if (parsed.path === '/home' || parsed.path === '/world') {
            return parsed;
          }
          // Invalid stored referrer, clear it and fallback
          sessionStorage.removeItem('article-referrer');
        } catch (e) {
          // Invalid JSON, clear it and continue
          sessionStorage.removeItem('article-referrer');
        }
      }

      // Fallback to document.referrer
      const referrer = document.referrer;
      if (referrer) {
        try {
          const url = new URL(referrer);
          const path = url.pathname;
          
          // Only trust /home and /world from document.referrer
          if (path === '/home') return { label: "Home", path: "/home" };
          if (path === '/world') return { label: "Top Headlines", path: "/world" };
          
          // For any other referrer (including external sites), fallback to home
        } catch (e) {
          // Invalid URL, continue to fallback
        }
      }

      // Ultimate fallback for direct visits or unknown sources
      return { label: "Home", path: "/home" };
    };

    const info = getReferrerInfo();
    setReferrerInfo(info);
  }, []);

  // Determine contextual back navigation
  const getBackNavigation = () => {
    if (referrerInfo) {
      return referrerInfo;
    }
    
    // Fallback while loading
    return {
      label: "Home",
      path: "/home"
    };
  };

  const backNav = getBackNavigation();

  // If this is overlay mode, render overlay content only
  if (isOverlay) {
    return (
      <>
        {/* Desktop/Tablet overlay header */}
        <div className="hidden md:block">
          {/* Back button bar (separate at top) */}
          <div className="absolute top-4 left-0 right-0">
            <BackButton
              variant="overlay"
              onClick={() => router.push(backNav.path)}
              label={backNav.label}
            />
          </div>

          {/* Metadata left + Actions right (same horizontal line at bottom) */}
          <div className="absolute bottom-4 left-0 right-0">
            <div className="flex justify-between items-end">
              <div className="flex-1">
                <ArticleMetadata 
                  article={article}
                  variant="overlay"
                />
              </div>
              
              <div className="flex items-center gap-2 ml-6">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLike}
                  className={cn(
                    "h-10 w-10 rounded-full bg-black/20 hover:bg-black/40 border border-white/20 hover:border-white/40 transition-colors",
                    liked ? "text-white" : "text-white/80 hover:text-white"
                  )}
                >
                  <ThumbsUp className={cn("h-5 w-5", liked && "fill-current")} />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDislike}
                  className={cn(
                    "h-10 w-10 rounded-full bg-black/20 hover:bg-black/40 border border-white/20 hover:border-white/40 transition-colors",
                    disliked ? "text-white" : "text-white/80 hover:text-white"
                  )}
                >
                  <ThumbsDown className={cn("h-5 w-5", disliked && "fill-current")} />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleShare}
                  className="h-10 w-10 rounded-full bg-black/20 hover:bg-black/40 border border-white/20 hover:border-white/40 text-white/80 hover:text-white transition-colors"
                >
                  <Share className="h-5 w-5" />
                </Button>
                
                <ReadOriginalButton
                  variant="overlay"
                  size="sm"
                  onClick={handleReadOriginal}
                  className="px-4 h-10"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Mobile overlay header - Only "Read Original" at top right */}
        <div className="absolute top-4 right-0 md:hidden">
          <ReadOriginalButton
            variant="overlay"
            size="sm"
            onClick={handleReadOriginal}
            className="bg-transparent hover:bg-white/10 border border-white/30 hover:border-white/50"
          />
        </div>

        {/* Mobile overlay metadata - Only metadata at bottom, actions handled by mobile footer */}
        <div className="absolute bottom-4 left-0 right-0 md:hidden">
          <ArticleMetadata 
            article={article}
            variant="overlay"
          />
        </div>
      </>
    );
  }

  // Regular non-overlay content
  return (
    <div className="relative">
      {/* Desktop/Tablet header */}
      <div className="hidden md:block">
        {/* Back button bar (always separate at top) */}
        <div className="mb-6">
          <BackButton
            variant="default"
            onClick={() => router.push(backNav.path)}
            label={backNav.label}
          />
        </div>

        {/* Metadata left + Actions right (same horizontal line) */}
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <ArticleMetadata article={article} variant="default" />
          </div>
          
          <div className="flex items-center gap-2 ml-6">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLike}
              className={cn(
                "h-10 w-10 rounded-full transition-colors",
                liked ? "text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <ThumbsUp className={cn("h-5 w-5", liked && "fill-current")} />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDislike}
              className={cn(
                "h-10 w-10 rounded-full transition-colors",
                disliked ? "text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <ThumbsDown className={cn("h-5 w-5", disliked && "fill-current")} />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleShare}
              className="h-10 w-10 rounded-full text-muted-foreground hover:text-foreground transition-colors"
            >
              <Share className="h-5 w-5" />
            </Button>
            
            <ReadOriginalButton
              variant="default"
              size="sm"
              onClick={handleReadOriginal}
              className="px-4 h-10"
            />
          </div>
        </div>
      </div>

      {/* Mobile header (unchanged) */}
      <div className="md:hidden">
        <div className="flex justify-end mb-4">
          <ReadOriginalButton
            variant="default"
            size="sm"
            onClick={handleReadOriginal}
            className="bg-transparent hover:bg-accent/50 border border-border"
          />
        </div>
        
        <div className="mb-4">
          <ArticleMetadata article={article} variant="default" />
        </div>
      </div>
    </div>
  );
}

interface ArticleMetadataProps {
  article: ArticleHeaderProps['article'];
  variant: "default" | "overlay";
}

function ArticleMetadata({ article, variant }: ArticleMetadataProps) {
  const isOverlay = variant === "overlay";
  
  return (
    <div className="space-y-2 md:space-y-3">
      {/* Publication Badge - responsive sizing */}
      <PublicationBadge 
        source={article.source}
        size="lg"
        variant={isOverlay ? "overlay" : "default"}
        className={cn(
          isOverlay ? "text-white" : "text-foreground",
          "md:text-lg" // Bigger on tablet/desktop
        )}
      />
      
      {/* Author, Date, Read Time - responsive sizing */}
      <div className={cn(
        "flex items-center gap-2 text-sm md:text-base flex-wrap",
        isOverlay ? "text-white/90 font-normal" : "text-muted-foreground/90 font-normal"
      )}>
        {article.author && (
          <>
            <span>
              {truncateText(article.author, 19)}
            </span>
            <span>•</span>
          </>
        )}
        <span>{formatDate(article.publishedAt)}</span>
        {article.readTime && (
          <>
            <span>•</span>
            <span>
              {article.readTime} min read
            </span>
          </>
        )}
      </div>
    </div>
  );
} 