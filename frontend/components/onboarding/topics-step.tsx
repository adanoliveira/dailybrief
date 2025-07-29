"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Topic } from "@/lib/onboarding-service"
import { getTopicIcon } from "@/lib/topic-icons"
import { CheckIcon as Check } from "@heroicons/react/24/outline"
import { cn } from "@/lib/utils"

interface TopicsStepProps {
  topics: Topic[]
  selectedTopics: number[]
  onChange: (topicIds: number[]) => void
  error?: string | null
}

export function TopicsStep({
  topics,
  selectedTopics,
  onChange,
  error
}: TopicsStepProps) {
  const [selected, setSelected] = useState<number[]>(selectedTopics)

  // Update local state when props change
  useEffect(() => {
    setSelected(selectedTopics)
  }, [selectedTopics])

  // Toggle topic selection
  const toggleTopic = (topicId: number) => {
    if (selected.includes(topicId)) {
      // Remove topic if it's already selected
      const newSelected = selected.filter(id => id !== topicId)
      setSelected(newSelected)
      onChange(newSelected)
    } else {
      // Add topic if it's not selected
      const newSelected = [...selected, topicId]
      setSelected(newSelected)
      onChange(newSelected)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="relative w-full"
    >
      <Card className="border-none shadow-none">
        <CardHeader className="pb-4">
          <CardTitle className="text-2xl font-bold">What topics interest you?</CardTitle>
          <p className="text-muted-foreground">Select topics you'd like to see in your feed</p>
        </CardHeader>
        
        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
              {error}
            </div>
          )}
          
          {selected.length === 0 && !error && (
            <div className="mb-4 p-3 bg-yellow-100/50 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200 rounded-md text-sm flex items-start">
              <div className="shrink-0 mr-2 mt-0.5">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                  <line x1="12" y1="9" x2="12" y2="13"></line>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
              </div>
              <div>
                Please select at least one topic to continue. The "General" topic is a good place to start.
              </div>
            </div>
          )}
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {topics.map((topic) => {
              // Get the appropriate icon for this topic
              const TopicIcon = getTopicIcon(topic.slug);
              
              return (
                <button
                  key={topic.id}
                  onClick={() => toggleTopic(topic.id)}
                  className={cn(
                    "flex items-center justify-between w-full p-3 rounded-lg border-2 transition-all duration-200",
                    "hover:shadow-md hover:border-primary/30",
                    selected.includes(topic.id)
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-muted bg-background"
                  )}
                >
                  <div className="flex items-center overflow-hidden">
                    <span className="flex items-center justify-center bg-primary/10 text-primary w-10 h-10 rounded-full flex-shrink-0 mr-3">
                      <TopicIcon className="h-5 w-5" />
                    </span>
                    <span className="font-medium truncate">{topic.name}</span>
                  </div>
                  
                  {selected.includes(topic.id) && (
                    <Check className="h-4 w-4 text-primary flex-shrink-0 ml-2" />
                  )}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
} 