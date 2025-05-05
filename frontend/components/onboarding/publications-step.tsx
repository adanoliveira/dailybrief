"use client"

import { useState, useEffect, useMemo } from "react"
import { motion } from "framer-motion"
import Image from "next/image" 
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { Publication } from "@/lib/onboarding-service"

interface PublicationsStepProps {
  publications: Publication[]
  selectedPublications: number[]
  onChange: (publicationIds: number[]) => void
  onNext: () => void
  onBack: () => void
  isSubmitting: boolean
}

export function PublicationsStep({
  publications,
  selectedPublications,
  onChange,
  onNext,
  onBack,
  isSubmitting
}: PublicationsStepProps) {
  const [selected, setSelected] = useState<number[]>(selectedPublications)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")

  // Update local state when props change
  useEffect(() => {
    setSelected(selectedPublications)
  }, [selectedPublications])

  // Filter publications based on search term
  const filteredPublications = useMemo(() => {
    if (!searchTerm.trim()) {
      return publications
    }
    
    const term = searchTerm.toLowerCase()
    return publications.filter(
      pub => pub.name.toLowerCase().includes(term)
    )
  }, [publications, searchTerm])

  // Sort publications by selection status and then by authority
  const sortedPublications = useMemo(() => {
    return [...filteredPublications].sort((a, b) => {
      // First sort by selection status (selected publications first)
      const aSelected = selected.includes(a.id)
      const bSelected = selected.includes(b.id)
      
      if (aSelected && !bSelected) return -1
      if (!aSelected && bSelected) return 1
      
      // Then sort by authority (higher authority first)
      return b.authority - a.authority
    })
  }, [filteredPublications, selected])

  // Toggle publication selection
  const togglePublication = (publicationId: number) => {
    setError(null)
    
    if (selected.includes(publicationId)) {
      // Remove publication if it's already selected
      const newSelected = selected.filter(id => id !== publicationId)
      setSelected(newSelected)
      onChange(newSelected)
    } else {
      // Add publication if it's not selected
      const newSelected = [...selected, publicationId]
      setSelected(newSelected)
      onChange(newSelected)
    }
  }

  // Handle next step
  const handleNext = () => {
    if (selected.length === 0) {
      setError("Please select at least one news source")
      return
    }
    
    onNext()
  }

  // Default placeholder image for publications without a logo
  const defaultLogo = (pubName: string) => {
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(pubName)}&background=random&color=fff&size=128`
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
          <CardTitle className="text-2xl font-bold">Choose your news sources</CardTitle>
          <p className="text-muted-foreground">Select publications you trust and want to read</p>
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
              placeholder="Search publications..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full"
            />
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[350px] overflow-y-auto pr-1">
            {sortedPublications.map((publication) => (
              <button
                key={publication.id}
                onClick={() => togglePublication(publication.id)}
                className={`p-3 rounded-md border transition-all duration-200 flex items-center justify-between hover:border-primary/70 ${
                  selected.includes(publication.id)
                    ? "bg-primary/10 border-primary shadow-sm"
                    : "bg-card hover:bg-background"
                }`}
              >
                <div className="flex items-center">
                  <div className="w-8 h-8 rounded overflow-hidden mr-3 bg-muted flex-shrink-0">
                    <Image
                      src={publication.logo_url || defaultLogo(publication.name)}
                      alt={publication.name}
                      width={32}
                      height={32}
                      className="w-full h-full object-cover"
                      unoptimized
                    />
                  </div>
                  <div className="flex flex-col items-start text-left">
                    <span className="font-medium">{publication.name}</span>
                    <span className="text-xs text-muted-foreground truncate max-w-[180px]">
                      {publication.description ? publication.description.substring(0, 40) + (publication.description.length > 40 ? '...' : '') : ''}
                    </span>
                  </div>
                </div>
                {selected.includes(publication.id) && (
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
          
          {filteredPublications.length === 0 && (
            <div className="py-8 text-center text-muted-foreground">
              No publications matched your search
            </div>
          )}
          
          <div className="mt-4 text-sm text-muted-foreground">
            <p>You've selected {selected.length} publications</p>
          </div>
        </CardContent>
        
        <CardFooter className="flex justify-between">
          <Button 
            onClick={onBack} 
            variant="outline"
            disabled={isSubmitting}
          >
            Back
          </Button>
          <Button 
            onClick={handleNext}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <div className="flex items-center">
                <LoadingSpinner size="sm" className="mr-2" />
                <span>Saving...</span>
              </div>
            ) : (
              "Complete Setup"
            )}
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  )
} 