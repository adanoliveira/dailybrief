"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle } from "lucide-react"

interface FinishStepProps {
  onFinish: () => void
}

export function FinishStep({ onFinish }: FinishStepProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="border-none shadow-none text-center">
        <CardHeader className="pb-4">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
              <CheckCircle className="w-10 h-10 text-primary" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold">All Set!</CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <p className="text-lg">
            Thanks for personalizing your DailyBrief experience. Your preferences have been saved.
          </p>
          
          <div className="py-4 space-y-4">
            <p>We'll use your preferences to:</p>
            <ul className="space-y-3 text-left mx-auto max-w-xs">
              <li className="flex items-start">
                <span className="text-primary mr-2 mt-0.5">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                </span>
                <span>Customize your news feed with relevant content</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary mr-2 mt-0.5">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                </span>
                <span>Prioritize stories from sources you trust</span>
              </li>
              <li className="flex items-start">
                <span className="text-primary mr-2 mt-0.5">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                </span>
                <span>Send you a daily digest of important news</span>
              </li>
            </ul>
          </div>
          
          <p>
            You can always update these preferences later in your account settings.
          </p>
        </CardContent>
        
        <CardFooter>
          <Button 
            onClick={onFinish} 
            className="w-full"
            size="lg"
          >
            Go to My Feed
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  )
} 