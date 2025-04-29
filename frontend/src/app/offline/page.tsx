import { Button } from "@/components/ui/button"
import { WifiOff } from "lucide-react"
import Link from "next/link"

export default function Offline() {
  return (
    <div className="container flex flex-col items-center justify-center min-h-screen py-12 text-center">
      <WifiOff className="h-16 w-16 text-muted-foreground mb-6" />
      <h1 className="text-3xl font-bold tracking-tight mb-2">You're offline</h1>
      <p className="text-muted-foreground mb-8 max-w-md">
        It looks like you're not connected to the internet. Some features may be unavailable until you're back online.
      </p>
      <div className="space-y-4">
        <p className="text-sm">You can still access your saved articles.</p>
        <Link href="/home">
          <Button>Try again</Button>
        </Link>
      </div>
    </div>
  )
}
