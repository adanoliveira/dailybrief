"use client"

import Image from "next/image"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

interface WelcomeStepProps {
  onNext: () => void
}

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="border-none shadow-none">
        <CardHeader className="pb-4">
          <CardTitle className="text-3xl font-bold text-center">Welcome to DailyBrief</CardTitle>
          <CardDescription className="text-center text-lg">
            Let's personalize your news experience
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="flex justify-center py-4">
            <div className="relative w-64 h-64">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-primary-foreground/5 rounded-full animate-pulse" />
              <Image
                src="/images/onboarding-welcome.svg"
                alt="Welcome illustration"
                width={240}
                height={240}
                className="relative z-10"
                priority
              />
            </div>
          </div>
          
          <div className="space-y-4 text-center">
            <p>
              In the next few steps, we'll help you customize your news experience based on:
            </p>
            
            <ul className="space-y-3 text-left mx-auto max-w-xs">
              <li className="flex items-center">
                <span className="flex items-center justify-center bg-primary/10 text-primary w-8 h-8 rounded-full mr-3">1</span>
                <span>Topics you're interested in</span>
              </li>
              <li className="flex items-center">
                <span className="flex items-center justify-center bg-primary/10 text-primary w-8 h-8 rounded-full mr-3">2</span>
                <span>Regions you want to follow</span>
              </li>
              <li className="flex items-center">
                <span className="flex items-center justify-center bg-primary/10 text-primary w-8 h-8 rounded-full mr-3">3</span>
                <span>Languages you prefer</span>
              </li>
              <li className="flex items-center">
                <span className="flex items-center justify-center bg-primary/10 text-primary w-8 h-8 rounded-full mr-3">4</span>
                <span>News sources you trust</span>
              </li>
            </ul>
          </div>
        </CardContent>
        
        <CardFooter>
          <Button 
            onClick={onNext} 
            className="w-full"
            size="lg"
          >
            Let's Get Started
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  )
} 