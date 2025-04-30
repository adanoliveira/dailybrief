"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Bell } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import notificationService from "@/lib/notification-service"

export function NotificationPermission() {
  const [showPrompt, setShowPrompt] = useState(false)
  const [permission, setPermission] = useState<NotificationPermission>("default")

  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window) {
      setPermission(Notification.permission)

      if (Notification.permission === "default") {
        // Only show the prompt after the user has interacted with the site
        const handleInteraction = () => {
          setShowPrompt(true)
          window.removeEventListener("click", handleInteraction)
        }

        window.addEventListener("click", handleInteraction)
        return () => window.removeEventListener("click", handleInteraction)
      }
    }
  }, [])

  const handleRequestPermission = async () => {
    const granted = await notificationService.requestPermission()
    setPermission(granted ? "granted" : "denied")
    setShowPrompt(false)

    if (granted) {
      // Schedule daily digest notification
      notificationService.scheduleDailyDigestNotification()
    }
  }

  if (!showPrompt || permission !== "default") {
    return null
  }

  return (
    <div className="fixed bottom-20 left-0 right-0 z-50 px-4 md:px-6 pb-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Stay updated with notifications
          </CardTitle>
          <CardDescription>Get notified when your daily digest is ready</CardDescription>
        </CardHeader>
        <CardContent className="pb-2">
          <p className="text-sm text-muted-foreground">
            We'll send you notifications for your daily news digest and important updates.
          </p>
        </CardContent>
        <CardFooter className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setShowPrompt(false)}>
            Not now
          </Button>
          <Button onClick={handleRequestPermission}>Enable notifications</Button>
        </CardFooter>
      </Card>
    </div>
  )
}
