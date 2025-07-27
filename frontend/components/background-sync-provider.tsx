"use client"

import { useEffect } from 'react'
import { backgroundSync } from '@/lib/background-sync'
import { useCacheInvalidation } from '@/hooks/use-cached-data'

interface BackgroundSyncProviderProps {
  children: React.ReactNode
}

export function BackgroundSyncProvider({ children }: BackgroundSyncProviderProps) {
  // Initialize cache invalidation hooks
  useCacheInvalidation()

  useEffect(() => {
    // Start background sync when component mounts
    console.log('Initializing background sync service')
    backgroundSync.start()

    // Cleanup on unmount
    return () => {
      console.log('Cleaning up background sync service')
      backgroundSync.stop()
    }
  }, [])

  // Log sync stats periodically in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      const interval = setInterval(() => {
        const stats = backgroundSync.getStats()
        console.log('Background sync stats:', stats)
      }, 30000) // Every 30 seconds

      return () => clearInterval(interval)
    }
  }, [])

  return <>{children}</>
} 