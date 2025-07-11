"use client"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { ArrowLeft, Share, ThumbsUp, ThumbsDown } from "lucide-react"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import type { Digest } from "@/lib/digest-service"

interface DigestActionBarProps {
  digest: Digest;
}

export function DigestActionBar({ digest }: DigestActionBarProps) {
  const router = useRouter();
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [canShare, setCanShare] = useState(false);
  const [referrerInfo, setReferrerInfo] = useState<{label: string; path: string} | null>(null);
  const [liked, setLiked] = useState(false);
  const [disliked, setDisliked] = useState(false);

  // Check if native sharing is available and get referrer info
  useEffect(() => {
    setCanShare(typeof navigator !== 'undefined' && 'share' in navigator);
    
    // Get referrer information with smart fallback logic
    const getReferrerInfo = () => {
      // First, try to get from sessionStorage (most reliable for SPA navigation)
      const storedReferrer = sessionStorage.getItem('digest-referrer');
      if (storedReferrer) {
        try {
          const parsed = JSON.parse(storedReferrer);
          // Only trust /home as valid source, fallback to /home for others
          if (parsed.path === '/home') {
            return parsed;
          }
          // Invalid stored referrer, clear it and fallback
          sessionStorage.removeItem('digest-referrer');
        } catch (e) {
          // Invalid JSON, clear it and continue
          sessionStorage.removeItem('digest-referrer');
        }
      }

      // Fallback to document.referrer
      const referrer = document.referrer;
      if (referrer) {
        try {
          const url = new URL(referrer);
          const path = url.pathname;
          
          // Only trust /home from document.referrer
          if (path === '/home') return { label: "Home", path: "/home" };
          
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
        sessionStorage.setItem('digest-referrer', JSON.stringify(referrerInfo));
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
      title: digest.title,
      text: `Check out today's Daily Brief`,
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
    // TODO: Connect to backend API for digest likes/dislikes tracking
  };

  const handleDislike = () => {
    setDisliked(!disliked);
    if (liked) setLiked(false);
    // TODO: Connect to backend API for digest likes/dislikes tracking
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
      {/* Desktop action bar - horizontal layout, hidden on mobile */}
      <div className="hidden md:flex items-center justify-between">
        {/* Back Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push(backNav.path)}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground h-10 px-3"
        >
          <ArrowLeft className="size-5" />
          <span className="text-sm font-medium">{backNav.label}</span>
        </Button>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLike}
            className={cn(
              "h-10 w-10 rounded-full transition-colors",
              liked ? "text-foreground" : "text-muted-foreground hover:text-foreground"
            )}
            title="Like Digest"
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
            title="Dislike Digest"
          >
            <ThumbsDown className={cn("h-5 w-5", disliked && "fill-current")} />
          </Button>
          
          <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleShare}
                className="h-10 w-10 rounded-full text-muted-foreground hover:text-foreground transition-colors"
                title="Share Digest"
              >
                <Share className="h-5 w-5" />
              </Button>
            </DialogTrigger>
            
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Share Daily Brief</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Share this daily brief with others
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={copyToClipboard}
                  >
                    Copy Link
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Mobile action bar - fixed bottom, hidden on desktop */}
      <div className={cn(
        "md:hidden fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-sm border-t border-border",
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
              title="Like Digest"
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
              title="Dislike Digest"
            >
              <ThumbsDown className={cn("size-5", disliked && "fill-current")} />
            </Button>

            {/* Share Button */}
            <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleShare}
                  className="h-12 w-12 rounded-full transition-colors hover:bg-transparent text-muted-foreground hover:text-foreground"
                  title="Share Digest"
                >
                  <Share className="size-5" />
                </Button>
              </DialogTrigger>
              
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Share Daily Brief</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Share this daily brief with others
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={copyToClipboard}
                    >
                      Copy Link
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>
    </>
  )
} 