"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useRouter } from "next/navigation"

export function AuthTest() {
  const [token, setToken] = useState("")
  const [authStatus, setAuthStatus] = useState({
    isAuthenticated: false,
    isOnboardingCompleted: false
  })
  const router = useRouter()

  // Check authentication status on component mount (client-side only)
  useEffect(() => {
    try {
      const storedToken = localStorage.getItem("auth_token")
      const onboardingCompleted = document.cookie.includes("onboarding_completed=true")
      
      setAuthStatus({
        isAuthenticated: !!storedToken,
        isOnboardingCompleted: onboardingCompleted
      })
    } catch (e) {
      console.error("Error checking auth status:", e)
    }
  }, [])

  const handleSetToken = () => {
    if (token) {
      try {
        // In a real app, you would validate the token
        localStorage.setItem("auth_token", token)
        document.cookie = `auth_token=${token}; path=/; max-age=86400`

        // Set onboarding as completed for testing
        document.cookie = `onboarding_completed=true; path=/; max-age=86400`
        
        setAuthStatus({
          isAuthenticated: true,
          isOnboardingCompleted: true
        })

        // Refresh to apply the new auth state
        router.refresh()
      } catch (e) {
        console.error("Error setting auth token:", e)
      }
    }
  }

  const handleClearToken = () => {
    try {
      localStorage.removeItem("auth_token")
      document.cookie = "auth_token=; path=/; max-age=0"
      document.cookie = "onboarding_completed=; path=/; max-age=0"
      
      setAuthStatus({
        isAuthenticated: false,
        isOnboardingCompleted: false
      })
      
      router.refresh()
    } catch (e) {
      console.error("Error clearing auth token:", e)
    }
  }

  const goToHome = () => {
    router.push("/")
  }

  const goToAuthedArea = () => {
    router.push("/home")
  }

  return (
    <Card className="w-full max-w-md mx-auto my-8">
      <CardHeader>
        <CardTitle>Auth Testing Tool</CardTitle>
        <CardDescription>Use this to test authenticated views</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="token">Auth Token</Label>
          <Input
            id="token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Enter any value as a test token"
          />
        </div>
        
        <div className="space-y-2 pt-2">
          <div className="text-sm font-medium">Current Status:</div>
          <div className="space-y-1">
            <div className={`text-sm px-2.5 py-0.5 rounded-full border inline-block ${authStatus.isAuthenticated ? 'bg-green-100 text-green-800 border-green-300' : 'bg-red-100 text-red-800 border-red-300'}`}>
              {authStatus.isAuthenticated ? "✓ Authenticated" : "✗ Not Authenticated"}
            </div>
            <div className={`text-sm px-2.5 py-0.5 rounded-full border inline-block ml-2 ${authStatus.isOnboardingCompleted ? 'bg-green-100 text-green-800 border-green-300' : 'bg-red-100 text-red-800 border-red-300'}`}>
              {authStatus.isOnboardingCompleted ? "✓ Onboarding Completed" : "✗ Onboarding Not Completed"}
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex flex-col gap-4">
        <div className="flex justify-between w-full">
          <Button variant="outline" onClick={handleClearToken}>
            Clear Token
          </Button>
          <Button onClick={handleSetToken}>Set Token</Button>
        </div>
        <div className="flex justify-between w-full">
          <Button variant="outline" onClick={goToHome}>
            Go to Home
          </Button>
          <Button onClick={goToAuthedArea}>
            Go to Authenticated Area
          </Button>
        </div>
      </CardFooter>
    </Card>
  )
}
