import { Button } from "@/components/ui/button"
import Link from "next/link"
import Image from "next/image"

export function HeroSection() {
  return (
    <section className="container py-12 md:py-16">
      <div className="grid gap-6 lg:grid-cols-2 lg:gap-12 items-center">
        <div className="space-y-4">
          <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
            Your personalized news digest, without the noise
          </h1>
          <p className="text-muted-foreground md:text-xl">
            Get daily news summaries tailored to your interests. Skip the endless scrolling and focus on what matters to
            you.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            <Link href="/auth/signup">
              <Button size="lg" className="w-full sm:w-auto">
                Create your custom news feed
              </Button>
            </Link>
            <Link href="#world-news">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                Browse top headlines
              </Button>
            </Link>
          </div>
        </div>
        <div className="relative h-[300px] md:h-[400px] rounded-lg overflow-hidden">
          <Image
            src="/placeholder.svg?height=400&width=600"
            alt="DailyBrief app showcase"
            fill
            className="object-cover"
            priority
          />
        </div>
      </div>
    </section>
  )
}
