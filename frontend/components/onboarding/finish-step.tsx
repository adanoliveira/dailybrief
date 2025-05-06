"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, Book, Globe, Languages, Newspaper, ChevronRight } from "lucide-react"
import { UserPreferences } from "@/lib/onboarding-service"
import Link from "next/link"

interface FinishStepProps {
  preferences?: UserPreferences
}

export function FinishStep({ preferences = { topics: [], regions: [], languages: [], publications: [] } }: FinishStepProps) {
  // Count selected preferences
  const topicCount = preferences.topics?.length || 0
  const regionCount = preferences.regions?.length || 0
  const languageCount = preferences.languages?.length || 0
  const publicationCount = preferences.publications?.length || 0
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="relative w-full"
    >
      <div className="flex flex-col items-center justify-center space-y-6 py-4">
        <div className="relative flex items-center justify-center w-24 h-24">
          <div className="absolute inset-0 bg-green-100 rounded-full animate-ping opacity-25"></div>
          <div className="relative bg-green-100 rounded-full p-5">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-green-600"
            >
              <path d="M20 6 9 17l-5-5" />
            </svg>
          </div>
        </div>

        <h2 className="text-2xl font-bold text-center">All set!</h2>
        
        <p className="text-center text-muted-foreground max-w-xs">
          Your preferences have been saved. We'll use them to personalize your news feed.
        </p>
        
        {/* Preference summary */}
        <div className="w-full max-w-xs bg-muted/30 rounded-lg p-4 border">
          <h3 className="font-medium text-sm mb-3 text-center">Your Selections</h3>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Book size={16} className="text-primary" />
                <span className="text-sm">Topics</span>
              </div>
              <span className="text-sm font-medium">{topicCount}</span>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Globe size={16} className="text-primary" />
                <span className="text-sm">Regions</span>
              </div>
              <span className="text-sm font-medium">{regionCount}</span>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Languages size={16} className="text-primary" />
                <span className="text-sm">Languages</span>
              </div>
              <span className="text-sm font-medium">{languageCount}</span>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Newspaper size={16} className="text-primary" />
                <span className="text-sm">Publications</span>
              </div>
              <span className="text-sm font-medium">{publicationCount}</span>
            </div>
          </div>
        </div>
        
        <div className="py-2 text-center">
          <p className="text-center text-muted-foreground max-w-xs">You can update your preferences anytime from the <Link className="underline" href="/profile">profile page</Link>.</p>
        </div>
      </div>
    </motion.div>
  )
} 