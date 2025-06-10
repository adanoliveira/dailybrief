"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import { shadowPatterns } from "@/lib/shadow-utils"

interface BackToTopProps {
  className?: string
  showAfter?: number // Show button after scrolling this many pixels
}

export function BackToTop({ className, showAfter = 400 }: BackToTopProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const toggleVisibility = () => {
      if (window.pageYOffset > showAfter) {
        setIsVisible(true)
      } else {
        setIsVisible(false)
      }
    }

    // Add scroll event listener
    window.addEventListener("scroll", toggleVisibility)

    // Clean up event listener on component unmount
    return () => {
      window.removeEventListener("scroll", toggleVisibility)
    }
  }, [showAfter])

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth"
    })
  }

  return (
    <Button
      onClick={scrollToTop}
      size="icon"
      variant="outline"
      className={cn(
        // Base styles
        "fixed bottom-20 right-6 z-50 h-12 w-12 rounded-full transition-all duration-300",
        // Consistent shadow pattern
        shadowPatterns.floating(),
        // Background and borders
        "bg-background/95 backdrop-blur-sm border-border/50 hover:bg-accent",
        // Dark mode enhanced border for better visibility
        "dark:border-white/20 dark:bg-background/90",
        // Visibility and animation
        isVisible
          ? "opacity-100 translate-y-0 pointer-events-auto"
          : "opacity-0 translate-y-4 pointer-events-none",
        // Desktop adjustments  
        "md:bottom-24 md:right-8",
        className
      )}
      aria-label="Back to top"
    >
      <ChevronUp className="h-5 w-5" />
    </Button>
  )
} 