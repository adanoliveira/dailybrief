"use client"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { 
  ArrowLeftIcon as ArrowLeft, 
  HeartIcon as Heart, 
  ShareIcon as Share, 
  HandThumbDownIcon as ThumbsDown, 
  HandThumbUpIcon as ThumbsUp, 
  ArrowTopRightOnSquareIcon as ExternalLink 
} from "@heroicons/react/24/outline"
import { useState, useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { shadowPatterns } from "@/lib/shadow-utils"

interface ArticleActionBarProps {
  article: {
    title: string;
    url: string;
    author?: string;
    source: {
      name: string;
    };
  };
}

export function ArticleActionBar({ article }: ArticleActionBarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [liked, setLiked] = useState(false);
  const [disliked, setDisliked] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [canShare, setCanShare] = useState(false);
  const [referrerInfo, setReferrerInfo] = useState<{label: string; path: string} | null>(null);

  // Check if native sharing is available and get referrer info
  useEffect(() => {
    setCanShare(typeof navigator !== 'undefined' && 'share' in navigator);
    
         // Get referrer information with smart fallback logic
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

  // Store referrer info when navigating away (for future reference)
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (referrerInfo) {
        sessionStorage.setItem('article-referrer', JSON.stringify(referrerInfo));
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [referrerInfo]);

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

  const handleShare = async () => {
    const shareData = {
      title: article.title,
      text: `Check out this article from ${article.source.name}`,
      url: window.location.href,
    };

    if (canShare) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        // User cancelled or error occurred, fallback to dialog
        setShareDialogOpen(true);
      }
    } else {
      // Desktop fallback - show share dialog
      setShareDialogOpen(true);
    }
  };

  const handleLike = () => {
    setLiked(!liked);
    if (disliked) setDisliked(false);
    // TODO: Connect to backend API for article likes/dislikes tracking
  };

  const handleDislike = () => {
    setDisliked(!disliked);
    if (liked) setLiked(false);
    // TODO: Connect to backend API for article likes/dislikes tracking
  };

  const handleReadOriginal = () => {
    window.open(article.url, '_blank', 'noopener,noreferrer');
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setShareDialogOpen(false);
      // Could add a toast notification here
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  return (
    <>
      {/* Fixed bottom action bar - mobile first */}
      <div className={cn(
        "fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-sm border-t border-border",
        // Add shadow for better separation, especially in dark mode
        "shadow-lg dark:shadow-white/10 dark:shadow-2xl"
      )}>
        <div className="flex items-center justify-between px-4 py-2 max-w-screen-sm mx-auto">
          
          {/* Back Button */}
          <Button
            variant="ghost"
            size="default"
            onClick={() => router.push(backNav.path)}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground h-12 px-3"
          >
            <ArrowLeft className="size-5" />
            <span className="text-sm font-medium">{backNav.label}</span>
          </Button>

          {/* Action Buttons - Icon only with bigger touch targets */}
          <div className="flex items-center gap-1">
            
            {/* Like Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLike}
              className={cn(
                "h-12 w-12 rounded-full transition-colors hover:bg-transparent",
                liked 
                  ? "text-foreground" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <ThumbsUp className={cn("size-5", liked && "fill-current")} />
            </Button>

            {/* Dislike Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDislike}
              className={cn(
                "h-12 w-12 rounded-full transition-colors hover:bg-transparent",
                disliked 
                  ? "text-foreground" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <ThumbsDown className={cn("size-5", disliked && "fill-current")} />
            </Button>

            {/* Share Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleShare}
              className="h-12 w-12 rounded-full text-muted-foreground hover:text-foreground hover:bg-transparent transition-colors"
            >
              <Share className="size-5" />
            </Button>

            {/* Read Original Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleReadOriginal}
              className="h-12 w-12 rounded-full text-muted-foreground hover:text-foreground hover:bg-transparent transition-colors"
            >
              <ExternalLink className="size-5" />
            </Button>

          </div>
        </div>
      </div>

      {/* Share Dialog for Desktop */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Share Article</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-4">
                Share this article with others
              </p>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={typeof window !== 'undefined' ? window.location.href : ''}
                  readOnly
                  className="flex-1 px-3 py-2 text-sm border border-border rounded-md bg-muted"
                />
                <Button onClick={copyToClipboard} size="sm">
                  Copy
                </Button>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (typeof window !== 'undefined') {
                    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(article.title)}&url=${encodeURIComponent(window.location.href)}`, '_blank');
                  }
                }}
                className="flex-1"
              >
                Share on Twitter
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (typeof window !== 'undefined') {
                    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}`, '_blank');
                  }
                }}
                className="flex-1"
              >
                Share on Facebook
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 