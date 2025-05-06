"use client"

import { useState, useEffect, useMemo, useRef, useCallback } from "react"
import { motion } from "framer-motion"
import Image from "next/image" 
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Publication, Topic, Region, fetchPaginatedPublications } from "@/lib/onboarding-service"
import {
  Filter,
  RefreshCw,
  Search,
  X,
  Check,
} from "lucide-react"
import React from "react"
import { getTopicIcon } from "@/lib/topic-icons";
import { getRegionFlag } from "@/lib/region-flags";

interface PublicationsStepProps {
  publications: Publication[]
  topics: Topic[]
  regions: Region[]
  selectedTopics: number[]
  selectedRegions: string[]
  selectedPublications: number[]
  onChange: (publicationIds: number[]) => void
  error?: string | null
}

// Number of items to load at once for server pagination
const PAGE_SIZE = 20;

export function PublicationsStep({
  publications: initialPublications,
  topics,
  regions,
  selectedTopics,
  selectedRegions,
  selectedPublications,
  onChange,
  error
}: PublicationsStepProps) {
  // Tabs and filtering state
  const [activeTab, setActiveTab] = useState<"recommended" | "other">("recommended")
  const [searchTerm, setSearchTerm] = useState("")
  
  // Separate filter states for each tab
  const [recommendedTopicFilter, setRecommendedTopicFilter] = useState<number[]>([])
  const [recommendedRegionFilter, setRecommendedRegionFilter] = useState<string[]>([])
  const [otherTopicFilter, setOtherTopicFilter] = useState<number[]>([])
  const [otherRegionFilter, setOtherRegionFilter] = useState<string[]>([])
  
  // Computed current filters based on active tab
  const topicFilter = useMemo(() => 
    activeTab === "recommended" ? recommendedTopicFilter : otherTopicFilter, 
  [activeTab, recommendedTopicFilter, otherTopicFilter])
  
  const regionFilter = useMemo(() => 
    activeTab === "recommended" ? recommendedRegionFilter : otherRegionFilter, 
  [activeTab, recommendedRegionFilter, otherRegionFilter])
  
  const [showFilters, setShowFilters] = useState(false)
  
  // Maintain separate publication lists for each tab
  const [recommendedPublications, setRecommendedPublications] = useState<Publication[]>([])
  const [otherPublications, setOtherPublications] = useState<Publication[]>([])
  
  // Track pagination state for each tab independently
  const [recommendedPage, setRecommendedPage] = useState(1)
  const [otherPage, setOtherPage] = useState(1)
  const [recommendedHasMore, setRecommendedHasMore] = useState(true)
  const [otherHasMore, setOtherHasMore] = useState(true)
  const [recommendedReachedEnd, setRecommendedReachedEnd] = useState(false)
  const [otherReachedEnd, setOtherReachedEnd] = useState(false)
  const [recommendedTotalPages, setRecommendedTotalPages] = useState(1)
  const [otherTotalPages, setOtherTotalPages] = useState(1)
  
  // Common loading state
  const [loading, setLoading] = useState(false)
  
  // Image error handling state
  const [logoErrors, setLogoErrors] = useState<Record<number, boolean>>({})
  const [faviconErrors, setFaviconErrors] = useState<Record<number, boolean>>({})
  
  // Selected publications state
  const [selected, setSelected] = useState<number[]>(selectedPublications)
  // Track explicitly deselected publications to prevent auto-reselection
  const [userDeselectedIds, setUserDeselectedIds] = useState<Set<number>>(new Set())
  
  // Use refs to avoid stale closures and track state
  const loadingRef = useRef(false)
  const hasInitializedRef = useRef(false)
  const initialSelectionMadeRef = useRef(false)
  const activeTabRef = useRef(activeTab)
  
  // Computed current values based on active tab
  const currentPublications = useMemo(() => 
    activeTab === "recommended" ? recommendedPublications : otherPublications, 
  [activeTab, recommendedPublications, otherPublications])
  
  const currentPage = useMemo(() => 
    activeTab === "recommended" ? recommendedPage : otherPage, 
  [activeTab, recommendedPage, otherPage])
  
  const currentHasMore = useMemo(() => 
    activeTab === "recommended" ? recommendedHasMore : otherHasMore, 
  [activeTab, recommendedHasMore, otherHasMore])
  
  const currentReachedEnd = useMemo(() => 
    activeTab === "recommended" ? recommendedReachedEnd : otherReachedEnd,
  [activeTab, recommendedReachedEnd, otherReachedEnd])
  
  // Update refs when state changes
  useEffect(() => {
    loadingRef.current = loading
  }, [loading])
  
  useEffect(() => {
    activeTabRef.current = activeTab
  }, [activeTab])
  
  // Update local state when props change
  useEffect(() => {
    setSelected(selectedPublications)
  }, [selectedPublications])

  // Load publications for a specific tab
  const loadPublications = useCallback(async (
    tabMode: "recommended" | "other", 
    page: number = 1, 
    resetExisting: boolean = false
  ) => {
    // Prevent multiple simultaneous calls
    if (loadingRef.current) return
    
    try {
      setLoading(true)
      loadingRef.current = true
      
      // Create filter object for API call
      const filters: {
        topicIds?: number[];
        regionCodes?: string[];
        filterMode: "recommended" | "other";
        sortBy?: string;
      } = { 
        sortBy: '-authority',
        filterMode: tabMode
      }
      
      // Include topic and region filters
      if (selectedTopics.length > 0) {
        filters.topicIds = [...selectedTopics]
      }
      
      if (selectedRegions.length > 0) {
        filters.regionCodes = [...selectedRegions]
      }
      
      // Override with explicit UI filters for the specific tab
      if (tabMode === "recommended" && recommendedTopicFilter.length > 0) {
        filters.topicIds = [...recommendedTopicFilter]
      } else if (tabMode === "other" && otherTopicFilter.length > 0) {
        filters.topicIds = [...otherTopicFilter]
      }
      
      if (tabMode === "recommended" && recommendedRegionFilter.length > 0) {
        filters.regionCodes = [...recommendedRegionFilter]
      } else if (tabMode === "other" && otherRegionFilter.length > 0) {
        filters.regionCodes = [...otherRegionFilter]
      }
      
      console.log(`Loading ${tabMode} publications, page ${page}, filters:`, filters)
      
      const response = await fetchPaginatedPublications(page, PAGE_SIZE, filters)
      
      // Check for duplicate IDs in the response data
      const pubIds = new Set<number>()
      const duplicateIds: number[] = []
      response.results.forEach(pub => {
        if (pubIds.has(pub.id)) {
          duplicateIds.push(pub.id)
        } else {
          pubIds.add(pub.id)
        }
      })
      
      if (duplicateIds.length > 0) {
        console.warn(`⚠️ API returned duplicate publication IDs in ${tabMode} tab:`, duplicateIds)
      }
      
      // Update pagination state based on tab
      const isLastPage = page >= response.pagination.total_pages
      
      if (tabMode === "recommended") {
        setRecommendedHasMore(!isLastPage)
        setRecommendedReachedEnd(isLastPage && page > 1)
        setRecommendedTotalPages(response.pagination.total_pages)
        setRecommendedPage(page)
        
        // Update publications list - remove any duplicates if appending
        if (resetExisting) {
          setRecommendedPublications(response.results)
        } else {
          // When appending, make sure we don't add duplicates from the current response
          const existingIds = new Set(recommendedPublications.map(p => p.id))
          const newPubs = response.results.filter(p => !existingIds.has(p.id))
          
          if (response.results.length !== newPubs.length) {
            console.warn(`⚠️ Filtered out ${response.results.length - newPubs.length} duplicate publications when appending to ${tabMode} tab`)
          }
          
          setRecommendedPublications(prev => [...prev, ...newPubs])
        }
      } else {
        setOtherHasMore(!isLastPage)
        setOtherReachedEnd(isLastPage && page > 1)
        setOtherTotalPages(response.pagination.total_pages)
        setOtherPage(page)
        
        // Update publications list - remove any duplicates if appending
        if (resetExisting) {
          setOtherPublications(response.results)
        } else {
          // When appending, make sure we don't add duplicates from the current response
          const existingIds = new Set(otherPublications.map(p => p.id))
          const newPubs = response.results.filter(p => !existingIds.has(p.id))
          
          if (response.results.length !== newPubs.length) {
            console.warn(`⚠️ Filtered out ${response.results.length - newPubs.length} duplicate publications when appending to ${tabMode} tab`)
          }
          
          setOtherPublications(prev => [...prev, ...newPubs])
        }
      }
    } catch (error) {
      console.error(`Error loading ${tabMode} publications:`, error)
    } finally {
      setLoading(false)
      loadingRef.current = false
    }
  }, [recommendedTopicFilter, recommendedRegionFilter, otherTopicFilter, otherRegionFilter, selectedTopics, selectedRegions, recommendedPublications, otherPublications])

  // Initial load of both tabs
  useEffect(() => {
    if (!hasInitializedRef.current) {
      console.log('Initial publications load')
      hasInitializedRef.current = true
      
      // Load both tabs initially
      loadPublications("recommended", 1, true)
      loadPublications("other", 1, true)
    }
  }, [loadPublications])
  
  // Auto-select recommended publications
  useEffect(() => {
    // Only run this when:
    // 1. We're in the recommended tab
    // 2. We have publications data
    // 3. Initial selection hasn't been made yet OR publications data has changed
    if (activeTab === "recommended" && recommendedPublications.length > 0 && 
        (!initialSelectionMadeRef.current || loadingRef.current === false)) {
      console.log('Processing publications for auto-selection:', recommendedPublications.length);
      
      // Get all publications that should be selected (all in the recommended tab)
      const recommendedIds = recommendedPublications.map(pub => pub.id);
      
      // Filter out IDs that the user has explicitly deselected
      const idsToSelect = recommendedIds.filter(id => !userDeselectedIds.has(id));
      
      // Identify publications that should be selected but aren't currently
      const newSelectionsNeeded = idsToSelect.filter(id => !selected.includes(id));
      
      // If we need to update selections or haven't made the initial selection
      if (newSelectionsNeeded.length > 0 || !initialSelectionMadeRef.current) {
        console.log(`Auto-selecting ${idsToSelect.length} recommended publications`);
        
        // Create a new selection array, starting with recommended publications
        // that haven't been explicitly deselected
        const newSelected = [...idsToSelect];
        
        // Add any user-selected publications that aren't from the recommended tab
        // but were explicitly selected by the user in the other tab
        const userOtherSelections = selected.filter(id => 
          !recommendedIds.includes(id) && 
          otherPublications.some(pub => pub.id === id)
        );
        
        // Add those explicit selections to the new selected array
        newSelected.push(...userOtherSelections);
        
        console.log(`${userOtherSelections.length} publications selected from Other tab`);
        
        // Update state and call onChange
        setSelected(newSelected);
        onChange(newSelected);
        
        // Mark that we've done the initial selection
        initialSelectionMadeRef.current = true;
      }
    }
  }, [activeTab, recommendedPublications, otherPublications, selected, onChange, userDeselectedIds]);

  // Client-side filtering for search text and other filters
  const filteredPublications = useMemo(() => {
    let result = [...currentPublications]
    
    // Apply search filter
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase()
      result = result.filter(
        pub => pub.name.toLowerCase().includes(term) || 
               pub.description?.toLowerCase().includes(term)
      )
    }
    
    // Apply topic filters client-side
    if (topicFilter.length > 0) {
      result = result.filter(pub => 
        pub.topic_ids?.some(topicId => topicFilter.includes(topicId))
      )
    }
    
    // Apply region filters client-side
    if (regionFilter.length > 0) {
      result = result.filter(pub => 
        pub.region_ids?.some(regionId => 
          regionFilter.includes(String(regionId))
        )
      )
    }
    
    // Sort by selection status and authority
    result = result.sort((a, b) => {
      // First sort by selection status (selected publications first)
      const aSelected = selected.includes(a.id)
      const bSelected = selected.includes(b.id)
      
      if (aSelected && !bSelected) return -1
      if (!aSelected && bSelected) return 1
      
      // Then sort by authority (higher authority first)
      return b.authority - a.authority
    })
    
    // Check for and remove duplicates
    const seen = new Set<number>()
    const filteredResult: Publication[] = []
    
    result.forEach(pub => {
      if (seen.has(pub.id)) {
        console.warn(`⚠️ Duplicate publication ID detected in ${activeTab} tab:`, pub.id, pub.name)
      } else {
        seen.add(pub.id)
        filteredResult.push(pub)
      }
    })
    
    return filteredResult
  }, [currentPublications, searchTerm, topicFilter, regionFilter, selected, activeTab])

  // Handle tab changes
  const handleTabChange = useCallback((value: string) => {
    if (loadingRef.current) return
    
    const newTab = value as "recommended" | "other"
    console.log(`Tab changed to ${newTab}`)
    setActiveTab(newTab)
    setSearchTerm("")
    
    // If this tab hasn't been loaded yet, load it
    if (newTab === "recommended" && recommendedPublications.length === 0) {
      loadPublications("recommended", 1, true)
    } else if (newTab === "other" && otherPublications.length === 0) {
      loadPublications("other", 1, true)
    }
    
    // Reset the initial selection flag when switching to recommended tab
    if (newTab === "recommended") {
      initialSelectionMadeRef.current = false
    }
  }, [loadPublications, recommendedPublications.length, otherPublications.length])

  // Load more handler - load more for active tab only
  const handleLoadMore = useCallback(() => {
    if (loadingRef.current || !currentHasMore) return
    
    const nextPage = currentPage + 1
    console.log(`Loading more ${activeTab} publications, page ${nextPage}`)
    
    loadPublications(activeTab, nextPage, false)
  }, [currentHasMore, currentPage, activeTab, loadPublications])

  // Load more with Intersection Observer
  const observerCallback = useCallback((entries: IntersectionObserverEntry[]) => {
    const [entry] = entries
    if (entry?.isIntersecting && !loadingRef.current && currentHasMore) {
      handleLoadMore()
    }
  }, [handleLoadMore, currentHasMore])
  
  const observerTarget = useRef(null)
  
  useEffect(() => {
    const observer = new IntersectionObserver(observerCallback, { 
      threshold: 0.1,
      rootMargin: '200px' 
    })
    
    const target = observerTarget.current
    if (target) observer.observe(target)
    
    return () => {
      if (target) observer.unobserve(target)
      observer.disconnect()
    }
  }, [observerCallback])

  // Toggle publication selection
  const togglePublication = (publicationId: number) => {
    if (selected.includes(publicationId)) {
      // Remove publication if it's already selected
      const newSelected = selected.filter(id => id !== publicationId)
      setSelected(newSelected)
      onChange(newSelected)
      
      // Track that this was explicitly deselected by the user
      // to prevent auto-reselection in the recommended tab
      setUserDeselectedIds(prev => {
        const newSet = new Set(prev)
        newSet.add(publicationId)
        return newSet
      })
      
      console.log(`User deselected publication ${publicationId}`)
    } else {
      // Add publication if it's not selected
      const newSelected = [...selected, publicationId]
      setSelected(newSelected)
      onChange(newSelected)
      
      // Remove from deselected set if it was there
      setUserDeselectedIds(prev => {
        const newSet = new Set(prev)
        newSet.delete(publicationId)
        return newSet
      })
      
      console.log(`User selected publication ${publicationId}`)
    }
  }

  // Handle topic filter
  const handleTopicFilter = (topicId: number) => {
    if (loadingRef.current) return
    
    if (activeTab === "recommended") {
      const newFilter = recommendedTopicFilter.includes(topicId)
        ? recommendedTopicFilter.filter(id => id !== topicId)
        : [...recommendedTopicFilter, topicId]
      
      setRecommendedTopicFilter(newFilter)
    } else {
      const newFilter = otherTopicFilter.includes(topicId)
        ? otherTopicFilter.filter(id => id !== topicId)
        : [...otherTopicFilter, topicId]
      
      setOtherTopicFilter(newFilter)
    }
  }

  // Handle region filter
  const handleRegionFilter = (regionCode: string) => {
    if (loadingRef.current) return
    
    if (activeTab === "recommended") {
      const newFilter = recommendedRegionFilter.includes(regionCode)
        ? recommendedRegionFilter.filter(code => code !== regionCode)
        : [...recommendedRegionFilter, regionCode]
      
      setRecommendedRegionFilter(newFilter)
    } else {
      const newFilter = otherRegionFilter.includes(regionCode)
        ? otherRegionFilter.filter(code => code !== regionCode)
        : [...otherRegionFilter, regionCode]
      
      setOtherRegionFilter(newFilter)
    }
  }

  // Clear all filters
  const clearFilters = () => {
    if (loadingRef.current) return
    
    if (activeTab === "recommended") {
      setRecommendedTopicFilter([])
      setRecommendedRegionFilter([])
    } else {
      setOtherTopicFilter([])
      setOtherRegionFilter([])
    }
    
    setSearchTerm("")
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

  // Get topic name by ID
  const getTopicName = (topicId: number) => {
    const topic = topics.find(t => t.id === topicId);
    return topic ? topic.name : "";
  }

  // Get topic name and icon by ID
  const getTopicInfo = (topicId: number) => {
    const topic = topics.find(t => t.id === topicId);
    const name = topic ? topic.name : "";
    const TopicIcon = getTopicIcon(topic?.slug || "default");
    return { name, TopicIcon };
  }

  // Get region name by ID
  const getRegionName = (regionId: number) => {
    // Convert regionId to string for comparison
    const region = regions.find(r => r.code === String(regionId))
    return region ? region.name : ""
  }

  // Filtered topics and regions based on active tab
  const filteredTopics = useMemo(() => {
    if (activeTab === "recommended") {
      // Only show topics the user has selected
      return topics.filter(topic => selectedTopics.includes(topic.id));
    }
    // Show all topics in "other" tab
    return topics;
  }, [activeTab, topics, selectedTopics]);

  const filteredRegions = useMemo(() => {
    if (activeTab === "recommended") {
      // Only show regions the user has selected
      return regions.filter(region => selectedRegions.includes(region.code));
    }
    // Show all regions in "other" tab
    return regions;
  }, [activeTab, regions, selectedRegions]);

  // Render publication item
  const renderPublicationItem = (publication: Publication) => {
    const hasLogoError = logoErrors[publication.id]
    const hasFaviconError = faviconErrors[publication.id]
    const faviconUrl = getFaviconUrl(publication.website_url)
    
    // Create a unique key by prefixing with the active tab
    const uniqueKey = `${activeTab}-${publication.id}`
    
    return (
      <button
        key={uniqueKey}
        onClick={() => togglePublication(publication.id)}
        className={`p-3 rounded-md border transition-all duration-200 flex flex-col hover:border-primary/70 ${
          selected.includes(publication.id)
            ? "bg-primary/10 border-primary shadow-sm"
            : "bg-card hover:bg-background"
        }`}
      >
        <div className="flex items-center justify-between w-full">
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
            <div className="flex flex-col items-start text-left w-full">
              <span className="font-medium">{publication.name}</span>
              <span className="text-xs text-muted-foreground line-clamp-2 w-full">
                {publication.description ? publication.description.substring(0, 80) + (publication.description.length > 80 ? '...' : '') : ''}
              </span>
            </div>
          </div>
          {selected.includes(publication.id) && (
            <Check size={18} className="text-primary flex-shrink-0 ml-2" />
          )}
        </div>
        
        {/* Tags for topics and regions with icons */}
        {(publication.topic_ids?.length || publication.region_ids?.length) && (
          <div className="flex flex-wrap gap-1.5 mt-2 ml-12">
            {/* Topic icons */}
            {publication.topic_ids?.map(topicId => {
              const { name, TopicIcon } = getTopicInfo(topicId);
              return (
                <div 
                  key={`topic-${topicId}`} 
                  className="flex items-center justify-center w-6 h-6 rounded-full bg-muted text-muted-foreground"
                  title={name}
                >
                  <TopicIcon size={14} />
                </div>
              );
            })}
            
            {/* Region flags */}
            {publication.region_ids?.map(regionId => (
              <div 
                key={`region-${regionId}`} 
                className="flex items-center justify-center w-6 h-6"
                title={getRegionName(regionId)}
              >
                {getRegionFlag(String(regionId))}
              </div>
            ))}
          </div>
        )}
      </button>
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
        <CardHeader className="pb-3">
          <CardTitle className="text-2xl font-bold">Choose your news sources</CardTitle>
          <p className="text-muted-foreground">Select publications you trust and want to read</p>
        </CardHeader>
        
        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
              {error}
            </div>
          )}
          
          {/* Tabs for Recommended vs All Publications */}
          <Tabs defaultValue="recommended" className="w-full" onValueChange={handleTabChange}>
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="recommended">Recommended</TabsTrigger>
              <TabsTrigger value="other">All Sources</TabsTrigger>
            </TabsList>
            
            <div className="flex items-center justify-between mb-3">
              {/* Search input */}
              <div className="relative flex-1 mr-2">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  type="text"
                  placeholder="Search publications..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-full"
                />
              </div>
              
              {/* Filter toggle button */}
              <button 
                onClick={() => setShowFilters(!showFilters)}
                className={`p-2 rounded-md border ${showFilters ? 'bg-primary/10 border-primary' : 'border-input'}`}
                disabled={loading}
              >
                <Filter size={16} />
              </button>
            </div>
            
            {/* Filters panel */}
            {showFilters && (
              <div className="mb-3 p-3 border rounded-md bg-background">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-medium">Filters</h3>
                  <button 
                    onClick={clearFilters} 
                    className="text-xs text-primary hover:underline"
                    disabled={loading}
                  >
                    Clear all
                  </button>
                </div>
                
                <div className="mb-2">
                  <h4 className="text-sm text-muted-foreground mb-1">Topics</h4>
                  <div className="flex flex-wrap gap-1">
                    {filteredTopics.map(topic => {
                      const TopicIcon = getTopicIcon(topic.slug || "default");
                      return (
                        <Badge 
                          key={topic.id} 
                          variant={topicFilter.includes(topic.id) ? "default" : "outline"}
                          className={`cursor-pointer ${loading ? 'opacity-50' : ''}`}
                          onClick={() => handleTopicFilter(topic.id)}
                        >
                          <TopicIcon size={14} className="mr-1" />
                          {topic.name}
                          {topicFilter.includes(topic.id) && (
                            <X size={12} className="ml-1" />
                          )}
                        </Badge>
                      );
                    })}
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm text-muted-foreground mb-1">Regions</h4>
                  <div className="flex flex-wrap gap-1">
                    {filteredRegions.map(region => (
                      <Badge 
                        key={region.code} 
                        variant={regionFilter.includes(region.code) ? "default" : "outline"}
                        className={`cursor-pointer ${loading ? 'opacity-50' : ''}`}
                        onClick={() => handleRegionFilter(region.code)}
                      >
                        <span className="mr-1 text-xs">{getRegionFlag(region.code)}</span>
                        {region.name}
                        {regionFilter.includes(region.code) && (
                          <X size={12} className="ml-1" />
                        )}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            {/* Applied filters display */}
            {(topicFilter.length > 0 || regionFilter.length > 0) && (
              <div className="flex flex-wrap gap-1 mb-3">
                {topicFilter.map(topicId => {
                  const topic = topics.find(t => t.id === topicId);
                  if (!topic) return null;
                  const TopicIcon = getTopicIcon(topic.slug || "default");
                  return (
                    <Badge key={`active-${topicId}`} variant="secondary" className="flex items-center gap-1">
                      <TopicIcon size={14} className="mr-1" />
                      {topic.name}
                      <X 
                        size={12} 
                        className="cursor-pointer" 
                        onClick={() => handleTopicFilter(topicId)}
                      />
                    </Badge>
                  );
                })}
                
                {regionFilter.map(regionCode => {
                  const region = regions.find(r => r.code === regionCode);
                  return region ? (
                    <Badge key={`active-${regionCode}`} variant="secondary" className="flex items-center gap-1">
                      <span className="mr-1 text-xs">{getRegionFlag(regionCode)}</span>
                      {region.name}
                      <X 
                        size={12} 
                        className="cursor-pointer" 
                        onClick={() => handleRegionFilter(regionCode)}
                      />
                    </Badge>
                  ) : null;
                })}
                
                <button 
                  onClick={clearFilters} 
                  className="text-xs text-primary hover:underline ml-1 flex items-center"
                  disabled={loading}
                >
                  Clear all
                </button>
              </div>
            )}
            
            {/* Tab contents */}
            <TabsContent value="recommended" className="m-0">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {filteredPublications.map((pub) => (
                  <React.Fragment key={`recommended-${pub.id}`}>
                    {renderPublicationItem(pub)}
                  </React.Fragment>
                ))}
              </div>
              
              {/* Loading indicator */}
              {loading && (
                <div className="flex justify-center py-4 mt-4">
                  <div className="animate-pulse flex space-x-2">
                    <div className="rounded-full bg-muted h-2 w-2"></div>
                    <div className="rounded-full bg-muted h-2 w-2"></div>
                    <div className="rounded-full bg-muted h-2 w-2"></div>
                  </div>
                </div>
              )}
              
              {/* Empty state when no publications are found */}
              {filteredPublications.length === 0 && !loading && (
                <div className="py-8 text-center text-muted-foreground">
                  {searchTerm || topicFilter.length > 0 || regionFilter.length > 0 
                    ? "No publications match your criteria" 
                    : "No recommended publications based on your selections"}
                </div>
              )}
              
              {/* End of list indicator */}
              {currentReachedEnd && !loading && filteredPublications.length > 0 && (
                <div className="mt-6 mb-2 bg-primary/5 border border-primary/20 rounded-lg text-center p-4">
                  <div className="flex justify-center mb-3">
                    <div className="bg-primary/10 p-2 rounded-full">
                      <Check className="h-5 w-5 text-primary" />
                    </div>
                  </div>
                  <h3 className="text-base font-medium mb-2">You've seen all publications</h3>
                  <p className="text-sm text-muted-foreground">
                    {activeTab === "recommended" 
                      ? "All recommended publications are listed above." 
                      : "You've reached the end of our publications directory."}
                  </p>
                </div>
              )}
              
              {/* Infinite scroll trigger - important to keep outside the grid */}
              {currentHasMore && !loading && filteredPublications.length > 0 && (
                <div ref={observerTarget} className="h-24 w-full" />
              )}
            </TabsContent>
            
            <TabsContent value="other" className="m-0">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {filteredPublications.map((pub) => (
                  <React.Fragment key={`other-${pub.id}`}>
                    {renderPublicationItem(pub)}
                  </React.Fragment>
                ))}
              </div>
              
              {/* Loading indicator */}
              {loading && (
                <div className="flex justify-center py-4 mt-4">
                  <div className="animate-pulse flex space-x-2">
                    <div className="rounded-full bg-muted h-2 w-2"></div>
                    <div className="rounded-full bg-muted h-2 w-2"></div>
                    <div className="rounded-full bg-muted h-2 w-2"></div>
                  </div>
                </div>
              )}
              
              {/* Empty state when no publications are found */}
              {filteredPublications.length === 0 && !loading && (
                <div className="py-8 text-center text-muted-foreground">
                  {searchTerm || topicFilter.length > 0 || regionFilter.length > 0 
                    ? "No publications match your criteria" 
                    : "No additional publications available"}
                </div>
              )}
              
              {/* End of list indicator */}
              {currentReachedEnd && !loading && filteredPublications.length > 0 && (
                <div className="mt-6 mb-2 bg-primary/5 border border-primary/20 rounded-lg text-center p-4">
                  <div className="flex justify-center mb-3">
                    <div className="bg-primary/10 p-2 rounded-full">
                      <Check className="h-5 w-5 text-primary" />
                    </div>
                  </div>
                  <h3 className="text-base font-medium mb-2">You've seen all publications</h3>
                  <p className="text-sm text-muted-foreground">
                    {activeTab === "recommended" 
                      ? "All recommended publications are listed above." 
                      : "You've reached the end of our publications directory."}
                  </p>
                </div>
              )}
              
              {/* Infinite scroll trigger - important to keep outside the grid */}
              {currentHasMore && !loading && filteredPublications.length > 0 && (
                <div ref={observerTarget} className="h-24 w-full" />
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </motion.div>
  )
} 