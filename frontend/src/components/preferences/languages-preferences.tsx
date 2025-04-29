"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useState } from "react"

// Full list of languages from the specs
const languages = [
  { code: "ar", name: "Arabic" },
  { code: "de", name: "German" },
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  { code: "he", name: "Hebrew" },
  { code: "it", name: "Italian" },
  { code: "nl", name: "Dutch" },
  { code: "no", name: "Norwegian" },
  { code: "pt", name: "Portuguese" },
  { code: "ru", name: "Russian" },
  { code: "sv", name: "Swedish" },
  { code: "ud", name: "Urdu" },
  { code: "zh", name: "Chinese" },
]

export function LanguagesPreferences() {
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(["en"])

  const handleLanguageChange = (language: string) => {
    setSelectedLanguages((prev) => {
      // If already selected, remove it
      if (prev.includes(language)) {
        return prev.filter((l) => l !== language)
      }

      // If trying to add more than 3, don't add
      if (prev.length >= 3 && !prev.includes(language)) {
        return prev
      }

      // Otherwise add it
      return [...prev, language]
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="text-sm text-muted-foreground">Select languages (up to 3)</p>
        <Badge variant="outline" className="ml-2">
          {selectedLanguages.length}/3 selected
        </Badge>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {selectedLanguages.map((code) => {
          const lang = languages.find((l) => l.code === code)
          return (
            <Badge key={code} variant="secondary" className="gap-1">
              {lang?.name}
              <button className="ml-1 rounded-full hover:bg-primary/20 p-1" onClick={() => handleLanguageChange(code)}>
                ×
              </button>
            </Badge>
          )
        })}
      </div>

      <ScrollArea className="h-[250px] pr-4">
        <div className="grid gap-4">
          {languages.map((language) => (
            <div key={language.code} className="flex items-center space-x-2">
              <Checkbox
                id={`lang-${language.code}`}
                checked={selectedLanguages.includes(language.code)}
                onCheckedChange={() => handleLanguageChange(language.code)}
                disabled={selectedLanguages.length >= 3 && !selectedLanguages.includes(language.code)}
              />
              <Label htmlFor={`lang-${language.code}`}>
                {language.name} ({language.code})
              </Label>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
