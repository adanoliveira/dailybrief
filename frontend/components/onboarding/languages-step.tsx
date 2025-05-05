"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Language } from "@/lib/onboarding-service"
import { getLanguageAutonym } from "@/lib/language-autonyms"
import { Check } from "lucide-react"

interface LanguagesStepProps {
  languages: Language[]
  selectedLanguages: string[]
  onChange: (languageCodes: string[]) => void
  error?: string | null
}

/**
 * Get language abbreviation suitable for display in a circle
 */
function getLanguageAbbreviation(languageCode: string): string {
  // For languages with non-Latin scripts, use first character
  const autonym = getLanguageAutonym(languageCode);
  
  // Use language code directly for Latin script languages
  if (['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'sv', 'no', 'fi', 'da', 'cs', 'ro', 'hu'].includes(languageCode.toLowerCase())) {
    return languageCode.toUpperCase();
  }
  
  // For non-Latin scripts, use the first character
  return autonym.charAt(0);
}

export function LanguagesStep({
  languages,
  selectedLanguages,
  onChange,
  error
}: LanguagesStepProps) {
  const [selected, setSelected] = useState<string[]>(selectedLanguages)

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
    if (selected.includes(languageCode)) {
      if (selected.length <= 1) {
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

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="relative w-full"
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
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {sortedLanguages.map((language) => (
              <button
                key={language.iso_code}
                onClick={() => toggleLanguage(language.iso_code)}
                className={`w-full p-3 rounded-md border transition-all duration-200 flex items-center justify-between hover:border-primary/70 ${
                  selected.includes(language.iso_code)
                    ? "bg-primary/10 border-primary shadow-sm"
                    : "bg-card hover:bg-background"
                }`}
              >
                <div className="flex items-center overflow-hidden">
                  <span className="flex items-center justify-center bg-background dark:bg-gray-800 w-9 h-9 rounded-full flex-shrink-0 mr-3">
                    <span className="font-mono text-sm tracking-wider font-semibold">
                      {language.iso_code.toUpperCase()}
                    </span>
                  </span>
                  <div className="flex flex-col items-start overflow-hidden">
                    <span className="font-medium text-left truncate">{language.name}</span>
                    <span className="text-xs text-left text-muted-foreground truncate">
                      {getLanguageAutonym(language.iso_code)}
                    </span>
                  </div>
                </div>
                
                {selected.includes(language.iso_code) && (
                  <Check size={18} className="text-primary flex-shrink-0 ml-2" />
                )}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
} 