"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Language } from "@/lib/onboarding-service"

interface LanguagesStepProps {
  languages: Language[]
  selectedLanguages: string[]
  onChange: (languageCodes: string[]) => void
  onNext: () => void
  onBack: () => void
}

export function LanguagesStep({
  languages,
  selectedLanguages,
  onChange,
  onNext,
  onBack
}: LanguagesStepProps) {
  const [selected, setSelected] = useState<string[]>(selectedLanguages)
  const [error, setError] = useState<string | null>(null)

  // Update local state when props change
  useEffect(() => {
    setSelected(selectedLanguages)
  }, [selectedLanguages])

  // Sort languages alphabetically
  const sortedLanguages = [...languages].sort((a, b) => {
    // English first, then alphabetical
    if (a.iso_code === 'en') return -1
    if (b.iso_code === 'en') return 1
    return a.name.localeCompare(b.name)
  })

  // Toggle language selection
  const toggleLanguage = (languageCode: string) => {
    setError(null)
    
    if (selected.includes(languageCode)) {
      if (selected.length <= 1) {
        setError("You must select at least one language")
        return
      }
      
      // Remove language if it's already selected
      const newSelected = selected.filter(code => code !== languageCode)
      setSelected(newSelected)
      onChange(newSelected)
    } else {
      // Add language if it's not selected
      const newSelected = [...selected, languageCode]
      setSelected(newSelected)
      onChange(newSelected)
    }
  }

  // Handle next step
  const handleNext = () => {
    if (selected.length === 0) {
      setError("Please select at least one language")
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
          <CardTitle className="text-2xl font-bold">Which languages do you read?</CardTitle>
          <p className="text-muted-foreground">Select languages for your news content</p>
        </CardHeader>
        
        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
              {error}
            </div>
          )}
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {sortedLanguages.map((language) => (
              <button
                key={language.iso_code}
                onClick={() => toggleLanguage(language.iso_code)}
                className={`p-3 rounded-md border transition-all duration-200 flex items-center justify-between hover:border-primary/70 ${
                  selected.includes(language.iso_code)
                    ? "bg-primary/10 border-primary shadow-sm"
                    : "bg-card hover:bg-background"
                }`}
              >
                <span className="font-medium">{language.name}</span>
                {selected.includes(language.iso_code) && (
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
            <p>You've selected {selected.length} languages</p>
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