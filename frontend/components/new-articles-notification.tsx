"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { 
  ChevronUpIcon as ChevronUp, 
  ArrowPathIcon as Loader2, 
  CheckIcon as Check 
} from "@heroicons/react/24/outline"
import { cn } from "@/lib/utils"

interface NewArticlesNotificationProps {
  newArticlesCount: number;
  updatedArticlesCount: number;
  onLoadNewArticles: () => Promise<void>;
  className?: string;
}

export function NewArticlesNotification({ 
  newArticlesCount, 
  updatedArticlesCount, 
  onLoadNewArticles,
  className 
}: NewArticlesNotificationProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  
  // Don't render if no new content
  if (newArticlesCount === 0 && updatedArticlesCount === 0) {
    return null
  }

  const handleLoadArticles = async () => {
    if (isLoading) return
    
    setIsLoading(true)
    try {
      await onLoadNewArticles()
      
      // Show success state briefly
      setIsSuccess(true)
      setTimeout(() => {
        setIsSuccess(false)
      }, 1500)
      
    } catch (error) {
      console.error('NewArticlesNotification: Failed to load new articles:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getButtonText = () => {
    if (isSuccess) {
      return "Updated!"
    }
    if (isLoading) {
      return "Loading..."
    }
    
    const totalCount = newArticlesCount + updatedArticlesCount
    
    if (totalCount === 1) {
      return "See new story"
    } else {
      return `See ${totalCount} new stories`
    }
  }

  const getButtonIcon = () => {
    if (isSuccess) {
      return <Check className="h-4 w-4" />
    }
    if (isLoading) {
      return <Loader2 className="h-4 w-4 animate-spin" />
    }
    return <ChevronUp className="h-4 w-4" />
  }

  return (
    <div 
      className={cn(
        "sticky top-0 z-40 mb-4 transition-all duration-300 ease-out",
        "animate-in slide-in-from-top-2 fade-in-0",
        className
      )}
    >
      <Button
        onClick={handleLoadArticles}
        disabled={isLoading}
        variant="outline"
        size="sm"
        className={cn(
          "w-full font-normal transition-all duration-200",
          "border-muted-foreground/20 text-muted-foreground hover:text-foreground",
          "hover:border-muted-foreground/40 hover:bg-muted/50",
          "bg-background/95 backdrop-blur-sm",
          isSuccess && "border-green-500/50 text-green-600 hover:text-green-700",
          isLoading && "cursor-not-allowed opacity-70"
        )}
      >
        <div className="flex items-center justify-center gap-2">
          {getButtonIcon()}
          <span className="text-sm">{getButtonText()}</span>
        </div>
      </Button>
    </div>
  )
} 