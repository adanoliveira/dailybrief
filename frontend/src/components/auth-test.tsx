"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useRouter } from "next/navigation"

export function AuthTest() {
  const [token, setToken] = useState("")
  const router = useRouter()

  const handleSetToken = () => {
    if (token) {
      // In a real app, you would validate the token
      localStorage.setItem("auth_token", token)
      document.cookie = `auth_token=${token}; path=/; max-age=86400`

      // Set onboarding as completed for testing
      document.cookie = `onboarding_completed=true; path=/; max-age=86400`

      // Refresh to apply the new auth state
      router.refresh()
    }
  }

  const handleClearToken = () => {
    localStorage.removeItem("auth_token")
    document.cookie = "auth_token=; path=/; max-age=0"
    document.cookie = "onboarding_completed=; path=/; max-age=0"
    router.refresh()
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
        <div className="text-sm text-muted-foreground">
          <p>Current status: {localStorage.getItem("auth_token") ? "Authenticated" : "Not authenticated"}</p>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={handleClearToken}>
          Clear Token
        </Button>
        <Button onClick={handleSetToken}>Set Token</Button>
      </CardFooter>
    </Card>
  )
}
