"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight, Zap, Brain, Star } from "lucide-react"
import Link from "next/link"

export function PublicFeedCTA() {
  return (
    <section className="container py-12 md:py-8">
      <div className="text-center space-y-6">
        {/* Main Headline */}
        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
          Ready to go beyond headlines?
        </h2>
        
        {/* Subheading */}
        <p className="text-muted-foreground md:text-xl max-w-2xl mx-auto">
          You've just experienced a preview. Get personalized news, AI-powered summaries, and daily digests tailored to your interests.
        </p>

        {/* Benefits Grid */}
        <div className="grid md:grid-cols-3 gap-8 py-8">
          <div className="text-center space-y-3">
            <div className="mx-auto w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
              <Zap className="h-6 w-6 text-primary" />
            </div>
            <h3 className="font-semibold">Personalized Feed</h3>
            <p className="text-sm text-muted-foreground">
              Articles curated based on your interests and reading habits
            </p>
          </div>
          
          <div className="text-center space-y-3">
            <div className="mx-auto w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
              <Brain className="h-6 w-6 text-primary" />
            </div>
            <h3 className="font-semibold">AI Summaries</h3>
            <p className="text-sm text-muted-foreground">
              Get the key insights from long articles in seconds
            </p>
          </div>
          
          <div className="text-center space-y-3">
            <div className="mx-auto w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
              <Star className="h-6 w-6 text-primary" />
            </div>
            <h3 className="font-semibold">Daily Digest</h3>
            <p className="text-sm text-muted-foreground">
              Yesterday's most important news, delivered every morning
            </p>
          </div>
        </div>

        {/* CTA Button */}
        <div className="flex justify-center pt-4">
          <Link href="/auth">
            <Button size="lg" className="group">
              Start Reading Smarter
              <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Button>
          </Link>
        </div>

        {/* Fine print */}
        <p className="text-sm text-muted-foreground pt-4">
          Sign up free • 2-minute setup
        </p>
      </div>
    </section>
  )
} 