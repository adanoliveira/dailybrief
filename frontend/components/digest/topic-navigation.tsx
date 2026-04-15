"use client"

import React, { useState, useEffect, useRef } from 'react'
import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import type { DigestTopic } from "@/lib/digest-service"

interface TopicNavigationProps {
  topics: DigestTopic[]
  className?: string
}

export function TopicNavigation({ topics, className }: TopicNavigationProps) {
  const [activeTopicId, setActiveTopicId] = useState<string>(topics[0]?.id || '')
  const [isSticky, setIsSticky] = useState(false)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(true)
  
  const desktopScrollContainerRef = useRef<HTMLDivElement>(null)
  const mobileScrollContainerRef = useRef<HTMLDivElement>(null)
  const navigationRef = useRef<HTMLDivElement>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)

  // Get the active scroll container based on screen size
  const getActiveScrollContainer = () => {
    // Check if we're on mobile by looking at window width
    const isMobile = window.innerWidth < 768 // md breakpoint
    return isMobile ? mobileScrollContainerRef.current : desktopScrollContainerRef.current
  }

  // Smooth scroll to topic section
  const scrollToTopic = (topicId: string) => {
    const element = document.getElementById(`topic-${topicId}`)
    if (element) {
      // Get the navigation height for offset
      const navHeight = navigationRef.current?.offsetHeight || 0
      const offsetTop = element.offsetTop - navHeight - 16 // 16px additional buffer
      
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      })
      
      // Remove focus from the button to prevent focus styling
      if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur()
      }
    }
  }

  // Handle horizontal scrolling in the carousel
  const scrollCarousel = (direction: 'left' | 'right') => {
    const container = getActiveScrollContainer()
    if (!container) return

    const scrollAmount = 200 // Adjust based on button width
    const newScrollLeft = direction === 'left' 
      ? container.scrollLeft - scrollAmount 
      : container.scrollLeft + scrollAmount

    container.scrollTo({
      left: newScrollLeft,
      behavior: 'smooth'
    })
  }

  // Update scroll button states
  const updateScrollButtons = () => {
    // For desktop arrows, only check the desktop container
    const desktopContainer = desktopScrollContainerRef.current
    if (!desktopContainer) {
      setCanScrollLeft(false)
      setCanScrollRight(false)
      return
    }

    // Check if content extends beyond the left side (scrolled from start)
    const canScrollToLeft = desktopContainer.scrollLeft > 0
    
    // Check if content extends beyond the right side (more content to scroll)
    const canScrollToRight = desktopContainer.scrollLeft < (desktopContainer.scrollWidth - desktopContainer.clientWidth - 1)

    setCanScrollLeft(canScrollToLeft)
    setCanScrollRight(canScrollToRight)
  }

  // Set up sticky behavior detection
  useEffect(() => {
    let originalOffsetTop: number | null = null

    const handleScroll = () => {
      if (!navigationRef.current) return
      
      // Store the original offset position on first call
      if (originalOffsetTop === null) {
        originalOffsetTop = navigationRef.current.offsetTop
      }
      
      const scrollY = window.scrollY
      
      // The navigation should stick when we've scrolled past its original position
      // And unstick when we scroll back above it
      const shouldBeSticky = scrollY > originalOffsetTop
      setIsSticky(shouldBeSticky)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    // Initial check
    handleScroll()
    
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Set up intersection observer for topic sections
  useEffect(() => {
    const observerOptions = {
      rootMargin: '-10% 0px -70% 0px', // More aggressive detection - trigger when topic enters upper 10% of viewport
      threshold: [0, 0.1, 0.25, 0.5, 0.75, 1.0] // Multiple thresholds for better detection
    }

    observerRef.current = new IntersectionObserver((entries) => {
      const intersectingEntries = entries.filter((entry) => entry.isIntersecting)
      if (intersectingEntries.length > 0) {
        const bestEntry = [...intersectingEntries].sort(
          (a, b) => b.intersectionRatio - a.intersectionRatio,
        )[0]
        const topicId = (bestEntry.target as HTMLElement).id.replace('topic-', '')
        setActiveTopicId(topicId)
        return
      }

      // Fallback: pick the entry closest to the top of the viewport
      const closestEntry = [...entries].sort(
        (a, b) => Math.abs(a.boundingClientRect.top) - Math.abs(b.boundingClientRect.top),
      )[0]
      if (closestEntry) {
        const topicId = (closestEntry.target as HTMLElement).id.replace('topic-', '')
        setActiveTopicId(topicId)
      }
    }, observerOptions)

    // Delay to ensure DOM elements are rendered
    const timer = setTimeout(() => {
      // Observe all topic sections
      topics.forEach((topic) => {
        const element = document.getElementById(`topic-${topic.id}`)
        if (element && observerRef.current) {
          observerRef.current.observe(element)
        }
      })
    }, 200) // Increased delay to 200ms

    return () => {
      clearTimeout(timer)
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [topics])

  // Set up scroll event for carousel buttons
  useEffect(() => {
    const desktopContainer = desktopScrollContainerRef.current
    if (!desktopContainer) return

    // Only listen to desktop container for button state updates
    desktopContainer.addEventListener('scroll', updateScrollButtons, { passive: true })
    
    // Initial check after content loads
    updateScrollButtons()
    
    // Also check when content resizes (topics change)
    const resizeObserver = new ResizeObserver(() => {
      updateScrollButtons()
    })
    resizeObserver.observe(desktopContainer)

    return () => {
      desktopContainer.removeEventListener('scroll', updateScrollButtons)
      resizeObserver.disconnect()
    }
  }, [topics]) // Re-run when topics change

  // Auto-scroll active topic into view in carousel
  useEffect(() => {
    const desktopContainer = desktopScrollContainerRef.current
    const mobileContainer = mobileScrollContainerRef.current
    
    // Try both containers to find the active button
    const containers = [desktopContainer, mobileContainer].filter(Boolean)
    
    for (const container of containers) {
      const activeButton = container?.querySelector(`[data-topic-id="${activeTopicId}"]`) as HTMLElement
      
      if (container && activeButton) {
        const containerRect = container.getBoundingClientRect()
        const buttonRect = activeButton.getBoundingClientRect()
        
        // Check if button is out of view
        if (buttonRect.left < containerRect.left || buttonRect.right > containerRect.right) {
          const scrollLeft = activeButton.offsetLeft - (container.clientWidth / 2) + (activeButton.clientWidth / 2)
          container.scrollTo({
            left: scrollLeft,
            behavior: 'smooth'
          })
        }
        break // Found the active container, no need to check others
      }
    }
  }, [activeTopicId])

  return (
    <>
      {/* Placeholder div to prevent content jump when sticky */}
      {isSticky && (
        <div 
          style={{ height: navigationRef.current?.offsetHeight || 0 }}
          className="w-full"
        />
      )}
      
      <div 
        ref={navigationRef}
        className={cn(
          "w-full bg-background/95 backdrop-blur-sm border-b border-muted/30 transition-all duration-300",
          isSticky && "fixed top-0 left-0 right-0 z-40 shadow-sm",
          className
        )}
      >
        {/* Desktop: Standard container with padding for scroll buttons */}
        <div className="hidden md:block">
          <div className="container px-4 md:px-6 lg:px-8 max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto">
            <div className="relative flex items-center py-3">
              
              {/* Left scroll button */}
              {canScrollLeft && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => scrollCarousel('left')}
                  className="absolute left-0 z-10 h-8 w-8 p-0 bg-background/90 backdrop-blur-sm border border-muted/30 shadow-sm hover:bg-background"
                  aria-label="Scroll left"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              )}

              {/* Topics carousel - Desktop */}
              <div 
                ref={desktopScrollContainerRef}
                className={cn(
                  "flex gap-2 overflow-x-auto scrollbar-hide scroll-smooth",
                  "px-10 -mx-10", // Padding for scroll buttons
                  !canScrollLeft && "pl-0 -ml-0",
                  !canScrollRight && "pr-0 -mr-0"
                )}
                style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
              >
                {topics.map((topic, index) => (
                  <Button
                    key={topic.id}
                    variant="ghost"
                    size="sm"
                    data-topic-id={topic.id}
                    onClick={() => scrollToTopic(topic.id)}
                    className={cn(
                      "flex-shrink-0 whitespace-nowrap transition-all duration-200",
                      "h-8 px-3 text-sm font-medium rounded-full",
                      "border border-muted/30 hover:border-muted/50",
                      "focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none",
                      "active:scale-100 active:translate-y-0",
                      activeTopicId === topic.id
                        ? "bg-primary border-primary shadow-sm focus-visible:ring-primary/20 hover:bg-primary/90 focus:bg-primary active:bg-primary text-primary-foreground hover:text-primary-foreground focus:text-primary-foreground active:text-primary-foreground [&]:text-primary-foreground"
                        : "bg-background hover:bg-muted/50 text-muted-foreground hover:text-foreground focus-visible:ring-muted/30 focus:bg-muted/30 focus:text-foreground active:bg-muted/30 active:text-foreground"
                    )}
                  >
                    {topic.title}
                  </Button>
                ))}
              </div>

              {/* Right scroll button */}
              {canScrollRight && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => scrollCarousel('right')}
                  className="absolute right-0 z-10 h-8 w-8 p-0 bg-background/90 backdrop-blur-sm border border-muted/30 shadow-sm hover:bg-background"
                  aria-label="Scroll right"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Mobile: Full-width carousel extending to screen edges */}
        <div className="block md:hidden">
          <div className="py-3">
            {/* Topics carousel - Mobile (full width) */}
            <div 
              ref={mobileScrollContainerRef}
              className={cn(
                "flex gap-2 overflow-x-auto scrollbar-hide scroll-smooth",
                "px-4" // Small padding from screen edges for first/last items
              )}
              style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
            >
              {topics.map((topic, index) => (
                <Button
                  key={topic.id}
                  variant="ghost"
                  size="sm"
                  data-topic-id={topic.id}
                  onClick={() => scrollToTopic(topic.id)}
                  className={cn(
                    "flex-shrink-0 whitespace-nowrap transition-all duration-200",
                    "h-8 px-3 text-sm font-medium rounded-full",
                    "border border-muted/30 hover:border-muted/50",
                    "focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none",
                    "active:scale-100 active:translate-y-0",
                    activeTopicId === topic.id
                      ? "bg-primary border-primary shadow-sm focus-visible:ring-primary/20 hover:bg-primary/90 focus:bg-primary active:bg-primary text-primary-foreground hover:text-primary-foreground focus:text-primary-foreground active:text-primary-foreground [&]:text-primary-foreground"
                      : "bg-background hover:bg-muted/50 text-muted-foreground hover:text-foreground focus-visible:ring-muted/30 focus:bg-muted/30 focus:text-foreground active:bg-muted/30 active:text-foreground"
                  )}
                >
                  {topic.title}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  )
} 
