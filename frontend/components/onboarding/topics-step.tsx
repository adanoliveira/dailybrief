"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Topic } from "@/lib/onboarding-service"
import { getTopicIcon } from "@/lib/topic-icons"
import { Check } from "lucide-react"

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
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {topics.map((topic) => {
              // Get the appropriate icon for this topic
              const TopicIcon = getTopicIcon(topic.slug);
              
              return (
                <button
                  key={topic.id}
                  onClick={() => toggleTopic(topic.id)}
                  className={`w-full p-3 rounded-md border transition-all duration-200 flex items-center justify-between hover:border-primary/70 ${
                    selected.includes(topic.id)
                      ? "bg-primary/10 border-primary shadow-sm"
                      : "bg-card hover:bg-background"
                  }`}
                >
                  <div className="flex items-center overflow-hidden">
                    <span className="flex items-center justify-center bg-primary/10 text-primary w-10 h-10 rounded-full flex-shrink-0 mr-3">
                      <TopicIcon size={20} />
                    </span>
                    <span className="font-medium truncate">{topic.name}</span>
                  </div>
                  
                  {selected.includes(topic.id) && (
                    <Check size={18} className="text-primary flex-shrink-0 ml-2" />
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