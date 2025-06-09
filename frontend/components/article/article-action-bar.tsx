"use client"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { ArrowLeft, Heart, MessageCircle, Share, ThumbsDown, ThumbsUp } from "lucide-react"
import { useState, useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

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

  // Check if native sharing is available
  useEffect(() => {
    setCanShare(typeof navigator !== 'undefined' && 'share' in navigator);
  }, []);

  // Determine contextual back navigation
  const getBackNavigation = () => {
    if (pathname?.includes('/article/')) {
      // Default to home, but could be enhanced with referrer tracking
      return {
        label: "Home",
        path: "/home"
      };
    }
    return {
      label: "Back",
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
    // TODO: Implement backend API call
  };

  const handleDislike = () => {
    setDisliked(!disliked);
    if (liked) setLiked(false);
    // TODO: Implement backend API call
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
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-sm border-t border-border">
        <div className="flex items-center justify-between px-4 py-3 max-w-screen-sm mx-auto">
          
          {/* Back Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(backNav.path)}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="text-sm font-medium">{backNav.label}</span>
          </Button>

          {/* Action Buttons */}
          <div className="flex items-center gap-1">
            
            {/* Like Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLike}
              className={cn(
                "p-2",
                liked ? "text-red-500 hover:text-red-600" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <ThumbsUp className={cn("h-5 w-5", liked && "fill-current")} />
            </Button>

            {/* Dislike Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDislike}
              className={cn(
                "p-2",
                disliked ? "text-blue-500 hover:text-blue-600" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <ThumbsDown className={cn("h-5 w-5", disliked && "fill-current")} />
            </Button>

            {/* Share Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleShare}
              className="p-2 text-muted-foreground hover:text-foreground"
            >
              <Share className="h-5 w-5" />
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
                  value={window.location.href}
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
                  window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(article.title)}&url=${encodeURIComponent(window.location.href)}`, '_blank');
                }}
                className="flex-1"
              >
                Share on Twitter
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}`, '_blank');
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