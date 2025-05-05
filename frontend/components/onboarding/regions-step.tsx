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
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {sortedRegions.map((region) => (
              <button
                key={region.code}
                onClick={() => toggleRegion(region.code)}
                className={`w-full p-3 rounded-md border transition-all duration-200 flex items-center justify-between hover:border-primary/70 ${
                  selected.includes(region.code)
                    ? "bg-primary/10 border-primary shadow-sm"
                    : "bg-card hover:bg-background"
                }`}
              >
                <div className="flex items-center overflow-hidden">
                  <span className="flex items-center justify-center bg-primary/10 w-10 h-10 rounded-full flex-shrink-0 mr-3">
                    {getRegionFlag(region.code)}
                  </span>
                  <span className="font-medium truncate">{region.name}</span>
                </div>
                
                {selected.includes(region.code) && (
                  <Check size={18} className="text-primary flex-shrink-0 ml-2" />
                )}
              </button>
            ))}
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