"use client"

import React, { createContext, useContext, useEffect, useState, useRef } from 'react'
import { useSession } from 'next-auth/react'
import apiClient from './api-client'

// User data type definition
export interface UserStatus {
  id: string
  public_id: string
  email: string
  name: string
  has_completed_onboarding: boolean
  created_at?: string
  updated_at?: string
  topics?: number[]
  topics_details?: Array<{id: number, name: string, slug: string}>
}

// Context type definition
interface UserContextType {
  userStatus: UserStatus | null
  isLoading: boolean
  error: string | null
  refreshUserStatus: () => Promise<UserStatus | null>
  setOnboardingComplete: (value: boolean) => void
}

// Create context with default values
const UserContext = createContext<UserContextType>({
  userStatus: null,
  isLoading: true,
  error: null,
  refreshUserStatus: async () => null,
  setOnboardingComplete: () => {}
})

// Provider component
export function UserProvider({ children }: { children: React.ReactNode }) {
  const { data: session, status: sessionStatus } = useSession()
  const [userStatus, setUserStatus] = useState<UserStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [lastLoadTime, setLastLoadTime] = useState<number>(0)
  const lastSyncRef = useRef<number>(0)

  // Load from localStorage only once on mount
  useEffect(() => {
    console.log("UserContext: Initial load from localStorage")
    // Try to load from localStorage on initial render for faster UI
    try {
      const cached = localStorage.getItem('userStatus')
      if (cached) {
        const parsedCache = JSON.parse(cached)
        setUserStatus(parsedCache)
        console.log("UserContext: Loaded from localStorage:", parsedCache)
      }
    } catch (err) {
      console.error('Failed to load cached user status', err)
      // Clear potentially corrupted cache
      localStorage.removeItem('userStatus')
    }
  }, [])

  // Main effect to sync user status when session changes
  useEffect(() => {
    const syncUserStatus = async () => {
      console.log("UserContext: Session state changed:", sessionStatus, "Has token:", !!session?.user?.django_token)
      
      // Allow session status changes to proceed immediately
      // Only rate-limit backend API calls, not session state processing
      const now = Date.now()
      const shouldRateLimit = (now - lastSyncRef.current < 2000) && (sessionStatus === 'authenticated')
      
      if (shouldRateLimit) {
        console.log("UserContext: Skipping sync - too frequent (authenticated user)")
        return
      }
      
      // If session is loading, wait
      if (sessionStatus === 'loading') {
        console.log("UserContext: Session still loading, waiting...")
        return
      }

      // If user is not authenticated, clear state and exit
      if (sessionStatus === 'unauthenticated' || !session?.user) {
        console.log("UserContext: User is not authenticated, clearing state")
        setUserStatus(null)
        setIsLoading(false)
        localStorage.removeItem('userStatus')
        setIsInitialized(true)
        lastSyncRef.current = now  // Reset rate limit for next auth cycle
        return
      }

      // Skip if we already have recent data for this user
      const currentUserId = session?.user?.django_user_id
      const timeSinceLastLoad = Date.now() - lastLoadTime
      const hasRecentData = userStatus?.id === String(currentUserId) && timeSinceLastLoad < 60000 // 1 minute

      if (hasRecentData && isInitialized) {
        console.log("UserContext: Skipping sync - have recent data for this user")
        return
      }

      // User is authenticated, fetch their status
      try {
        console.log("UserContext: User is authenticated, fetching status")
        setIsLoading(true)
        setError(null)
        
        // Set rate limit timer for API calls
        lastSyncRef.current = now

        // Always fetch fresh data from backend when session changes or first load
        const data = await apiClient.get<UserStatus>(
          '/api/accounts/sync/',
          { forceRefresh: true }
        )
        
        // Update state and cache
        console.log("UserContext: Fetched fresh user status:", data)
        setUserStatus(data)
        localStorage.setItem('userStatus', JSON.stringify(data))
        setLastLoadTime(Date.now())
      } catch (err) {
        console.error('UserContext: Failed to sync user status:', err)
        setError('Failed to load user data')
      } finally {
        setIsLoading(false)
        setIsInitialized(true)
      }
    }

    syncUserStatus()
  }, [sessionStatus, session?.user?.django_user_id])

  // Function to manually refresh user status
  const refreshUserStatus = async (): Promise<UserStatus | null> => {
    // Clear cache for this endpoint to ensure fresh data
    apiClient.clearEndpointCache('/api/accounts/sync/')
    
    // Skip if no session or no token
    if (!session?.user?.django_token) {
      console.log("UserContext: Cannot refresh user status - no authentication token")
      return null
    }
    
    try {
      console.log("UserContext: Manual refresh of user status requested")
      setIsLoading(true)
      setError(null)
      
      // Fetch user status with forced refresh
      const data = await apiClient.get<UserStatus>(
        '/api/accounts/sync/',
        { forceRefresh: true }
      )
      
      // Update state and cache
      console.log("UserContext: Manually refreshed user status:", data)
      setUserStatus(data)
      localStorage.setItem('userStatus', JSON.stringify(data))
      setLastLoadTime(Date.now())
      
      return data
    } catch (err) {
      console.error('UserContext: Failed to refresh user status:', err)
      setError('Failed to refresh user data')
      return null
    } finally {
      setIsLoading(false)
    }
  }
  
  // Function to update onboarding status
  const setOnboardingComplete = (value: boolean) => {
    // Skip if no user status
    if (!userStatus) {
      console.log("UserContext: Cannot set onboarding status - no user status")
      return
    }
    
    // Create updated user status
    const updatedStatus = {
      ...userStatus,
      has_completed_onboarding: value
    }
    
    // Update state and localStorage immediately for better UX
    console.log("UserContext: Setting onboarding status to:", value)
    setUserStatus(updatedStatus)
    localStorage.setItem('userStatus', JSON.stringify(updatedStatus))
    
    // Then refresh from the API to ensure consistency
    setTimeout(() => {
      console.log("UserContext: Refreshing user status after onboarding update")
      refreshUserStatus().catch(err => {
        console.error('UserContext: Failed to refresh after onboarding update:', err)
      })
    }, 1000)
  }
  
  const contextValue = {
    userStatus,
    isLoading,
    error,
    refreshUserStatus,
    setOnboardingComplete
  }
  
  return (
    <UserContext.Provider value={contextValue}>
      {children}
    </UserContext.Provider>
  )
}

// Custom hook for using the context
export function useUser() {
  const context = useContext(UserContext)
  if (!context) {
    throw new Error('useUser must be used within a UserProvider')
  }
  return context
} 