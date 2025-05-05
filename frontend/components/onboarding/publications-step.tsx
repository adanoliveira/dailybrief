"use client"

import { useState, useEffect, useMemo } from "react"
import { motion } from "framer-motion"
import Image from "next/image" 
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Publication } from "@/lib/onboarding-service"
import { Check } from "lucide-react"

interface PublicationsStepProps {
  publications: Publication[]
  selectedPublications: number[]
  onChange: (publicationIds: number[]) => void
  error?: string | null
}

export function PublicationsStep({
  publications,
  selectedPublications,
  onChange,
  error
}: PublicationsStepProps) {
  const [selected, setSelected] = useState<number[]>(selectedPublications)
  const [searchTerm, setSearchTerm] = useState("")
  const [logoErrors, setLogoErrors] = useState<Record<number, boolean>>({})
  const [faviconErrors, setFaviconErrors] = useState<Record<number, boolean>>({})

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

  // Handle logo loading errors
  const handleLogoError = (pubId: number) => {
    setLogoErrors(prev => ({ ...prev, [pubId]: true }))
  }

  // Handle favicon loading errors
  const handleFaviconError = (pubId: number) => {
    setFaviconErrors(prev => ({ ...prev, [pubId]: true }))
  }

  // Get favicon URL from website URL
  const getFaviconUrl = (websiteUrl: string) => {
    if (!websiteUrl) return null
    try {
      const url = new URL(websiteUrl)
      return `${url.origin}/favicon.ico`
    } catch {
      return null
    }
  }

  // Text-based avatar as final fallback
  const getTextAvatar = (pubName: string) => {
    // Get first 2 letters of publication name
    const initials = pubName.trim().substring(0, 2).toUpperCase()
    return (
      <div className="flex items-center justify-center w-full h-full bg-primary/20 font-mono text-xs font-semibold">
        {initials}
      </div>
    )
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
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {sortedPublications.map((publication) => {
              const hasLogoError = logoErrors[publication.id]
              const hasFaviconError = faviconErrors[publication.id]
              const faviconUrl = getFaviconUrl(publication.website_url)
              
              return (
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
                    <div className="flex items-center justify-center bg-background dark:bg-gray-800 w-9 h-9 rounded-full flex-shrink-0 mr-3 overflow-hidden">
                      {!hasLogoError && publication.logo_url ? (
                        <div className="flex items-center justify-center w-full h-full bg-primary/5">
                          <Image
                            src={publication.logo_url}
                            alt={publication.name}
                            width={24}
                            height={24}
                            className="max-w-[24px] max-h-[24px] rounded-full object-contain"
                            onError={() => handleLogoError(publication.id)}
                            unoptimized
                          />
                        </div>
                      ) : !hasFaviconError && faviconUrl ? (
                        <div className="flex items-center justify-center w-full h-full bg-primary/5">
                          <Image
                            src={faviconUrl}
                            alt={publication.name}
                            width={24}
                            height={24}
                            className="max-w-[24px] max-h-[24px] rounded-full object-contain"
                            onError={() => handleFaviconError(publication.id)}
                            unoptimized
                          />
                        </div>
                      ) : (
                        <span className="font-mono text-sm tracking-wider font-semibold">
                          {publication.name.substring(0, 2).toUpperCase()}
                        </span>
                      )}
                    </div>
                    <div className="flex flex-col items-start text-left">
                      <span className="font-medium">{publication.name}</span>
                      <span className="text-xs text-muted-foreground truncate max-w-[180px]">
                        {publication.description ? publication.description.substring(0, 40) + (publication.description.length > 40 ? '...' : '') : ''}
                      </span>
                    </div>
                  </div>
                  {selected.includes(publication.id) && (
                    <Check size={18} className="text-primary flex-shrink-0 ml-2" />
                  )}
                </button>
              )
            })}
          </div>
          
          {filteredPublications.length === 0 && (
            <div className="py-8 text-center text-muted-foreground">
              No publications matched your search
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
} 