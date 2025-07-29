"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ArrowPathIcon as RefreshCw, CheckIcon as Check } from "@heroicons/react/24/outline"

export interface FeedRefreshResult {
  hasNewData: boolean;
}

interface FeedRefreshButtonProps {
  onRefresh: () => Promise<FeedRefreshResult>;
  disabled?: boolean;
  className?: string;
}

export function FeedRefreshButton({ onRefresh, disabled = false, className }: FeedRefreshButtonProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [refreshState, setRefreshState] = useState<'idle' | 'updated' | 'no-new-data'>('idle')

  const handleRefresh = async () => {
    if (isRefreshing || disabled) return
    
    setIsRefreshing(true)
    setRefreshState('idle')
    
    try {
      const result = await onRefresh()
      
      // Show different feedback based on whether new data was found
      if (result.hasNewData) {
        setRefreshState('updated')
      } else {
        setRefreshState('no-new-data')
      }
      
      setTimeout(() => {
        setRefreshState('idle')
      }, 2000) // Show feedback for 2 seconds
      
    } catch (error) {
      console.error('Feed refresh failed:', error)
      setRefreshState('idle')
    } finally {
      setIsRefreshing(false)
    }
  }

  return (
    <Button
      onClick={handleRefresh}
      disabled={disabled || isRefreshing}
      variant="ghost"
      size="sm"
      className={`hidden md:flex text-muted-foreground hover:text-foreground ${className || ''}`}
    >
      {refreshState === 'updated' ? (
        <>
          <Check className="h-4 w-4 mr-1" />
          Updated!
        </>
      ) : refreshState === 'no-new-data' ? (
        <>
          <Check className="h-4 w-4 mr-1" />
          Up to date
        </>
      ) : (
        <>
          <RefreshCw className={`h-4 w-4 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? 'Updating...' : 'Refresh'}
        </>
      )}
    </Button>
  )
} 