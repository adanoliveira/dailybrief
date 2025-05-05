"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Topic } from "@/lib/onboarding-service"

interface TopicsStepProps {
  topics: Topic[]
  selectedTopics: number[]
  onChange: (topicIds: number[]) => void
  onNext: () => void
  onBack: () => void
}

export function TopicsStep({
  topics,
  selectedTopics,
  onChange,
  onNext,
  onBack
}: TopicsStepProps) {
  const [selected, setSelected] = useState<number[]>(selectedTopics)
  const [error, setError] = useState<string | null>(null)

  // Update local state when props change
  useEffect(() => {
    setSelected(selectedTopics)
  }, [selectedTopics])

  // Toggle topic selection
  const toggleTopic = (topicId: number) => {
    setError(null)
    
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

  // Handle next step
  const handleNext = () => {
    if (selected.length === 0) {
      setError("Please select at least one topic")
      return
    }
    
    onNext()
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -50 }}
      transition={{ duration: 0.3 }}
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
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {topics.map((topic) => (
              <button
                key={topic.id}
                onClick={() => toggleTopic(topic.id)}
                className={`p-3 h-full rounded-md border transition-all duration-200 flex items-center justify-between hover:border-primary/70 ${
                  selected.includes(topic.id)
                    ? "bg-primary/10 border-primary shadow-sm"
                    : "bg-card hover:bg-background"
                }`}
              >
                <span className="font-medium">{topic.name}</span>
                {selected.includes(topic.id) && (
                  <span className="ml-2 text-primary">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M20 6 9 17l-5-5" />
                    </svg>
                  </span>
                )}
              </button>
            ))}
          </div>
          
          <div className="mt-4 text-sm text-muted-foreground">
            <p>You've selected {selected.length} topics</p>
          </div>
        </CardContent>
        
        <CardFooter className="flex justify-between">
          <Button 
            onClick={onBack} 
            variant="outline"
          >
            Back
          </Button>
          <Button 
            onClick={handleNext}
          >
            Continue
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  )
} 