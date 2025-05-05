"use client"

import { useState, useEffect, useMemo } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Region } from "@/lib/onboarding-service"

interface RegionsStepProps {
  regions: Region[]
  selectedRegions: string[]
  onChange: (regionCodes: string[]) => void
  onNext: () => void
  onBack: () => void
}

export function RegionsStep({
  regions,
  selectedRegions,
  onChange,
  onNext,
  onBack
}: RegionsStepProps) {
  const [selected, setSelected] = useState<string[]>(selectedRegions)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")

  // Update local state when props change
  useEffect(() => {
    setSelected(selectedRegions)
  }, [selectedRegions])

  // Filter regions based on search term
  const filteredRegions = useMemo(() => {
    if (!searchTerm.trim()) {
      return regions
    }
    
    const term = searchTerm.toLowerCase()
    return regions.filter(
      region => 
        region.name.toLowerCase().includes(term) ||
        region.code.toLowerCase().includes(term)
    )
  }, [regions, searchTerm])

  // Sort regions by selection status and then alphabetically
  const sortedRegions = useMemo(() => {
    return [...filteredRegions].sort((a, b) => {
      // First, sort by selection status (selected regions first)
      const aSelected = selected.includes(a.code)
      const bSelected = selected.includes(b.code)
      
      if (aSelected && !bSelected) return -1
      if (!aSelected && bSelected) return 1
      
      // Then sort alphabetically by name
      return a.name.localeCompare(b.name)
    })
  }, [filteredRegions, selected])

  // Toggle region selection
  const toggleRegion = (regionCode: string) => {
    setError(null)
    
    if (selected.includes(regionCode)) {
      // Remove region if it's already selected
      const newSelected = selected.filter(code => code !== regionCode)
      setSelected(newSelected)
      onChange(newSelected)
    } else {
      // Add region if it's not selected
      const newSelected = [...selected, regionCode]
      setSelected(newSelected)
      onChange(newSelected)
    }
  }

  // Handle next step
  const handleNext = () => {
    if (selected.length === 0) {
      setError("Please select at least one region")
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
          <CardTitle className="text-2xl font-bold">Where do you want news from?</CardTitle>
          <p className="text-muted-foreground">Select regions you want to follow</p>
        </CardHeader>
        
        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
              {error}
            </div>
          )}
          
          <div className="mb-4">
            <Input
              type="text"
              placeholder="Search regions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-3 max-h-[300px] overflow-y-auto pr-1">
            {sortedRegions.map((region) => (
              <button
                key={region.code}
                onClick={() => toggleRegion(region.code)}
                className={`p-3 rounded-md border transition-all duration-200 flex items-center justify-between hover:border-primary/70 ${
                  selected.includes(region.code)
                    ? "bg-primary/10 border-primary shadow-sm"
                    : "bg-card hover:bg-background"
                }`}
              >
                <div className="flex items-center">
                  <span className="font-medium">{region.name}</span>
                  <span className="ml-2 text-xs text-muted-foreground">({region.code.toUpperCase()})</span>
                </div>
                {selected.includes(region.code) && (
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
          
          {filteredRegions.length === 0 && (
            <div className="py-8 text-center text-muted-foreground">
              No regions matched your search
            </div>
          )}
          
          <div className="mt-4 text-sm text-muted-foreground">
            <p>You've selected {selected.length} regions</p>
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