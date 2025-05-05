"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle } from "lucide-react"

export function FinishStep() {
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
        
        <div className="py-4 text-center">
          <p className="text-muted-foreground">You can update your preferences anytime from the settings page.</p>
        </div>
      </div>
    </motion.div>
  )
} 