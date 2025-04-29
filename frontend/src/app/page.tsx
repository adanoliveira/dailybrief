import { Button } from "@/components/ui/button"
import { HeroSection } from "@/components/hero-section"
import { WorldNewsFeed } from "@/components/world-news-feed"
import Link from "next/link"

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold">DailyBrief</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/auth/signin">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link href="/auth/signup">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      <HeroSection />
      <WorldNewsFeed />
    </main>
  )
}
