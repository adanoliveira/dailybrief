import { Button } from "@/components/ui/button"
import Link from "next/link"
import { HeroAnimation } from "@/components/hero-animation"

export function HeroSection() {
  return (
    <section className="container py-12 md:py-8">
      <div className="grid gap-8 lg:grid-cols-2 lg:gap-12 items-center">
        <div className="space-y-4 lg:order-1 text-center">
          <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
            Your personalized news digest, without the noise
          </h1>
          <p className="text-muted-foreground md:text-xl">
            Get daily news summaries tailored to your interests. Skip the endless scrolling and focus on what matters to
            you.
          </p>
          <div className="flex flex-col gap-3 pt-4 justify-center">
            <Link href="/auth">
              <Button size="lg" className="w-full sm:w-auto">
                Create your custom news feed
              </Button>
            </Link>
            {/* <Link href="#world-news">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                Browse top headlines
              </Button>
            </Link> */}

            {/* Fine print */}
            <p className="text-sm text-muted-foreground pt-4">
              Sign up free • 2-minute setup
            </p>
          </div>
        </div>
        <div className="relative h-[320px] sm:h-[340px] md:h-[420px] rounded-lg overflow-hidden lg:order-2 -mx-6 sm:-mx-4 lg:mx-0">
          <HeroAnimation />
        </div>
      </div>
    </section>
  )
}
