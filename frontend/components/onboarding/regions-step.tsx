"use client"

import { useState, useEffect, useMemo } from "react"
import { motion } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Region } from "@/lib/onboarding-service"
import { getRegionFlag } from "@/lib/region-flags"
import { Check } from "lucide-react"

interface RegionsStepProps {
  regions: Region[]
  selectedRegions: string[]
  onChange: (regionCodes: string[]) => void
  error?: string | null
}

export function RegionsStep({
  regions,
  selectedRegions,
  onChange,
  error
}: RegionsStepProps) {
  const [selected, setSelected] = useState<string[]>(selectedRegions)
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

  // Define available regions
  const availableRegions = ['us', 'br']
  
  // Check if a region is available
  const isRegionAvailable = (regionCode: string) => availableRegions.includes(regionCode.toLowerCase())
  
  // Sort regions by availability, selection status, and then alphabetically
  const sortedRegions = useMemo(() => {
    return [...filteredRegions].sort((a, b) => {
      // First, sort by availability (available regions first)
      const aAvailable = isRegionAvailable(a.code)
      const bAvailable = isRegionAvailable(b.code)
      
      if (aAvailable && !bAvailable) return -1
      if (!aAvailable && bAvailable) return 1
      
      // Then, sort by selection status (selected regions first within each group)
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
    // Don't allow selection of unavailable regions
    if (!isRegionAvailable(regionCode)) {
      return
    }
    
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

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="relative w-full"
    >
      <Card className="border-none shadow-none">
        <CardHeader className="pb-4">
          <CardTitle className="text-2xl font-bold">Where do you want news from?</CardTitle>
          <p className="text-muted-foreground">Select regions you want to follow</p>
          <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-md border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-900 dark:text-blue-100">
              Currently supporting United States and Brazil. More regions coming soon!
            </p>
          </div>
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
                Please select at least one region to continue. Your local region is a good place to start.
              </div>
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
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {sortedRegions.map((region) => {
              const isAvailable = isRegionAvailable(region.code)
              const isSelected = selected.includes(region.code)
              
              return (
                <button
                  key={region.code}
                  onClick={() => toggleRegion(region.code)}
                  disabled={!isAvailable}
                  className={`w-full p-3 rounded-md border transition-all duration-200 flex items-center justify-between relative ${
                    !isAvailable
                      ? "bg-muted/30 border-muted text-muted-foreground cursor-not-allowed opacity-60"
                      : isSelected
                        ? "bg-primary/10 border-primary shadow-sm hover:border-primary/70"
                        : "bg-card hover:bg-background hover:border-primary/70"
                  }`}
                >
                  <div className="flex items-center overflow-hidden">
                    <span className={`flex items-center justify-center w-10 h-10 rounded-full flex-shrink-0 mr-3 ${
                      isAvailable ? "bg-primary/10" : "bg-muted"
                    }`}>
                      {getRegionFlag(region.code)}
                    </span>
                    <div className="flex flex-col items-start">
                      <span className="font-medium truncate">{region.name}</span>
                      {!isAvailable && (
                        <span className="text-xs text-muted-foreground">Coming soon</span>
                      )}
                    </div>
                  </div>
                  
                  {isSelected && isAvailable && (
                    <Check size={18} className="text-primary flex-shrink-0 ml-2" />
                  )}
                </button>
              )
            })}
          </div>
          
          {filteredRegions.length === 0 && (
            <div className="py-8 text-center text-muted-foreground">
              No regions matched your search
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
} 