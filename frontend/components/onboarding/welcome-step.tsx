"use client"

import { motion } from "framer-motion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Newspaper, Globe, Languages, BookMarked } from "lucide-react"

export function WelcomeStep() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="relative w-full"
    >
      <Card className="border-none shadow-none">
        <CardHeader className="pb-4">
          <CardTitle className="text-3xl font-bold text-center">Welcome to DailyBrief</CardTitle>
          <CardDescription className="text-center text-lg">
            Let's personalize your news experience
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="space-y-5 text-center">
            <p className="text-muted-foreground">
              In the next few steps, we'll help you customize your news feed:
            </p>
            
            <ul className="space-y-4 text-left mx-auto max-w-xs">
              <li className="flex items-center">
                <span className="flex items-center justify-center bg-primary/10 text-primary w-10 h-10 rounded-full mr-3">
                  <Newspaper size={20} />
                </span>
                <span>Topics you're interested in</span>
              </li>
              <li className="flex items-center">
                <span className="flex items-center justify-center bg-primary/10 text-primary w-10 h-10 rounded-full mr-3">
                  <Globe size={20} />
                </span>
                <span>Regions you want to follow</span>
              </li>
              <li className="flex items-center">
                <span className="flex items-center justify-center bg-primary/10 text-primary w-10 h-10 rounded-full mr-3">
                  <Languages size={20} />
                </span>
                <span>Languages you prefer</span>
              </li>
              <li className="flex items-center">
                <span className="flex items-center justify-center bg-primary/10 text-primary w-10 h-10 rounded-full mr-3">
                  <BookMarked size={20} />
                </span>
                <span>News sources you trust</span>
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
} 