import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Newspaper } from "lucide-react"
import Link from "next/link"

export function DailyDigest() {
  const isGenerating = false

  if (isGenerating) {
    return (
      <Card className="bg-muted/40">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Newspaper className="h-5 w-5" />
            Your Daily Brief
          </CardTitle>
          <CardDescription>Your personalized news digest is being generated</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-16 flex items-center justify-center">
            <div className="animate-pulse flex space-x-2">
              <div className="rounded-full bg-muted h-2 w-2"></div>
              <div className="rounded-full bg-muted h-2 w-2"></div>
              <div className="rounded-full bg-muted h-2 w-2"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-primary/5 border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Newspaper className="h-5 w-5" />
          Your Daily Brief
        </CardTitle>
        <CardDescription>April 28, 2025 • 5 min read</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm line-clamp-3">
          Today's top stories: Tech innovations in AI, global market shifts, breakthrough in renewable energy, and more
          personalized updates based on your interests.
        </p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Link href="/digest/latest">
          <Button variant="default" size="sm">
            Read digest
          </Button>
        </Link>
        <Link href="/digest/archive">
          <Button variant="ghost" size="sm">
            See all digests
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}
