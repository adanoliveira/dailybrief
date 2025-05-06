"use client"

import { useState, useEffect, useMemo } from "react"
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
  const sortedLanguages = useMemo(() => {
    return [...languages].sort((a, b) => {
      // First, sort by selection status (selected languages first)
      const aSelected = selected.includes(a.iso_code);
      const bSelected = selected.includes(b.iso_code);
      
      if (aSelected && !bSelected) return -1;
      if (!aSelected && bSelected) return 1;
      
      // Then English first
      if (a.iso_code === 'en') return -1;
      if (b.iso_code === 'en') return 1;
      
      // Then sort alphabetically
      return a.name.localeCompare(b.name);
    });
  }, [languages, selected]);

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
                Please select at least one language to continue. English is a common choice to start with.
              </div>
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