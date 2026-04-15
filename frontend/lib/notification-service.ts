export type NotificationType = "dailyDigest" | "breakingNews" | "savedArticle"

export interface NotificationOptions {
  title: string
  body: string
  icon?: string
  data?: any
  actions?: NotificationAction[]
}

export interface NotificationAction {
  action: string
  title: string
  icon?: string
}

export class NotificationService {
  private static instance: NotificationService
  private permission: NotificationPermission = "default"

  private constructor() {
    if (typeof window !== "undefined") {
      this.permission = Notification.permission
    }
  }

  public static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService()
    }
    return NotificationService.instance
  }

  public async requestPermission(): Promise<boolean> {
    if (!("Notification" in window)) {
      console.log("This browser does not support notifications")
      return false
    }

    if (this.permission === "granted") {
      return true
    }

    try {
      const permission = await Notification.requestPermission()
      this.permission = permission
      return permission === "granted"
    } catch (error) {
      console.error("Error requesting notification permission:", error)
      return false
    }
  }

  public async showNotification(type: NotificationType, options: NotificationOptions): Promise<boolean> {
    if (this.permission !== "granted") {
      const granted = await this.requestPermission()
      if (!granted) return false
    }

    try {
      const notification = new Notification(options.title, {
        body: options.body,
        icon: options.icon || "/icons/icon-192x192.png",
        data: { ...options.data, type },
        actions: options.actions,
      })

      notification.onclick = (event) => {
        event.preventDefault()
        window.focus()
        notification.close()

        // Handle click based on notification type
        switch (type) {
          case "dailyDigest":
            window.location.href = "/digest/latest"
            break
          case "breakingNews":
            if (options.data?.articleId) {
              window.location.href = `/article/${options.data.articleId}`
            } else {
              window.location.href = "/world"
            }
            break
          case "savedArticle":
            if (options.data?.articleId) {
              window.location.href = `/article/${options.data.articleId}`
            }
            break
        }
      }

      return true
    } catch (error) {
      console.error("Error showing notification:", error)
      return false
    }
  }

  public async scheduleDailyDigestNotification(time = "08:00"): Promise<void> {
    // This is a simplified implementation
    // In a real app, you would use a more robust scheduling mechanism
    const [hours, minutes] = time.split(":").map(Number)

    const now = new Date()
    const scheduledTime = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hours, minutes)

    if (scheduledTime < now) {
      scheduledTime.setDate(scheduledTime.getDate() + 1)
    }

    const timeUntilNotification = scheduledTime.getTime() - now.getTime()

    setTimeout(() => {
      this.showNotification("dailyDigest", {
        title: "Your Daily Brief is ready",
        body: "Check out your personalized news digest for today",
      })

      // Reschedule for the next day
      this.scheduleDailyDigestNotification(time)
    }, timeUntilNotification)
  }
}

export default NotificationService.getInstance()
