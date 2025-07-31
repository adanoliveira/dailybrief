"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Clock, ExternalLink, Image, Video, Volume2, Sparkles } from "lucide-react"
import Link from "next/link"
import { format } from "date-fns"
import { useArticleDetail } from "@/lib/use-local-data"
import { ArticleDetail } from "@/lib/api"
import { Skeleton } from "@/components/ui/skeleton"
import { RichArticleRenderer, withFormattingSupport, renderWithFormatting } from "@/components/rich-article-renderer"
import { getBestTitle, shouldShowSummaryBlock, getContentQualityLevel, getProcessingStatusDescription } from "@/lib/article-utils"
import { ArticleHeader } from "@/components/article/article-header"
import { ArticleActionBar } from "@/components/article/article-action-bar"
import { getHeroImage } from "@/lib/article-utils"
import { cn } from "@/lib/utils"
import { BackToTop } from "@/components/ui/back-to-top"
import { SummaryBlock } from "@/components/article/summary-block"

export default function Article({ params }: { params: { id: string } }) {
  // Use local-first article detail hook
  const { data: article, isLoading: loading, error, refresh } = useArticleDetail(params.id, { backgroundSync: true })
  
  const [heroImage, setHeroImage] = useState<string | null>(null)
  const [heroImageFallback, setHeroImageFallback] = useState<string | null>(null)
  const [heroImageError, setHeroImageError] = useState(false)
  const [filteredBlocks, setFilteredBlocks] = useState<any[]>([])

  // State for summary generation (stub for now)
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  // Handler to generate summary - delegates to business logic
  const handleGenerateSummary = async () => {
    if (!article) return;
    
    setSummaryLoading(true);
    setSummaryError(null);
    
    try {
      const { generateArticleSummaryLogic } = await import('@/lib/article-utils');
      const result = await generateArticleSummaryLogic(article.id, { async: true });
      
      if (result.success && result.status === 'completed') {
        // Summary updated in backend, refresh to get updated data
        refresh();
      } else if (!result.success) {
        setSummaryError(result.error);
      }
    } catch (error) {
      console.error('Summary generation error:', error);
      setSummaryError(error instanceof Error ? error.message : 'An unexpected error occurred');
    } finally {
      setSummaryLoading(false);
    }
  };

  // Extract hero image and filter content blocks when article loads
  useEffect(() => {
    if (article) {
      const { heroImage: extractedHeroImage, filteredBlocks: filtered } = getHeroImage(article)
        setHeroImage(extractedHeroImage)
      setHeroImageFallback(article.imageUrl || null) // Keep original imageUrl as fallback
        setHeroImageError(false) // Reset error state
        setFilteredBlocks(filtered)
    }
  }, [article])

  // Format date
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return format(date, 'MMMM d, yyyy')
    } catch (e) {
      return dateString
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="container py-6 max-w-3xl">
        <div className="space-y-6">
          <div>
            <Skeleton className="h-4 w-1/3 mb-2" />
            <Skeleton className="h-10 w-full" />
          </div>
          <Card>
            <CardContent className="p-4">
              <Skeleton className="h-4 w-40 mb-2" />
              <Skeleton className="h-24 w-full" />
            </CardContent>
          </Card>
          <div className="space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="container py-6 max-w-3xl">
        <Card className="bg-destructive/5 border-destructive/20 text-center">
          <CardContent className="pt-6 pb-4">
            <div className="flex justify-center mb-4">
              <div className="bg-destructive/10 p-3 rounded-full">
                <AlertCircle className="h-6 w-6 text-destructive" />
              </div>
            </div>
            <h3 className="text-lg font-medium mb-2">Failed to load article</h3>
            <p className="text-muted-foreground mb-4">
              {error}
            </p>
            <div className="flex justify-center gap-4">
              <Button onClick={() => window.location.reload()} variant="outline">
                Try again
              </Button>
              <Link href="/home">
                <Button>Back to feed</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // No article found
  if (!article) {
    return (
      <div className="container py-6 max-w-3xl">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold">Article not found</h1>
          <p className="text-muted-foreground">The article you're looking for doesn't exist or has been removed.</p>
          <Link href="/home">
            <Button>Back to feed</Button>
          </Link>
        </div>
      </div>
    )
  }

  // Filter content blocks to remove duplicate titles and hero image
  const getFilteredContentBlocks = () => {
    if (!filteredBlocks) return []
    
    const primaryTitle = article?.visualTitle || article?.title
    
    return filteredBlocks.filter(block => {
      // Remove heading blocks that duplicate the main title
      if (block.type === 'heading' && (block.level === 1 || block.level === undefined)) {
        // Check if this heading is the same as our primary title (with or without HTML)
        const blockText = block.content?.replace(/<[^>]*>/g, '').trim() || ''
        const titleText = primaryTitle?.replace(/<[^>]*>/g, '').trim() || ''
        
        // Remove if they're very similar (allow for minor differences)
        if (blockText && titleText) {
          const similarity = blockText.length > titleText.length ? 
            titleText.length / blockText.length : 
            blockText.length / titleText.length
          
          // If 80%+ similar, consider it a duplicate
          return similarity < 0.8
        }
      }
      return true
    })
  }

  // Get the current hero image to display (with fallback logic)
  const currentHeroImage = heroImageError && heroImageFallback ? heroImageFallback : heroImage;
  const shouldShowHeroImage = currentHeroImage && (!heroImageError || heroImageFallback);

  return (
    <div className="min-h-screen">
      {/* Hero Image - Full width, outside container constraints */}
      {shouldShowHeroImage && (
        <div className="relative w-full">
          <div className="relative w-full aspect-[6/4] md:aspect-[8/5] lg:aspect-[12/7] xl:aspect-[16/9] overflow-hidden lg:rounded-b-lg lg:max-w-5xl lg:mx-auto xl:rounded-b-xl">
            <img
              src={currentHeroImage}
              alt={article.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                console.log('Hero image failed to load:', currentHeroImage);
                // Try fallback if we haven't already
                if (!heroImageError && heroImageFallback && currentHeroImage !== heroImageFallback) {
                  console.log('Switching to fallback image:', heroImageFallback);
                  setHeroImageError(true);
                } else {
                  // No fallback available, log and hide
                  console.log('No fallback available, hiding hero image');
                  setHeroImage(null);
                }
              }}
              onLoad={() => {
                console.log('Hero image loaded successfully:', currentHeroImage);
              }}
            />
            
            {/* Gradient overlay */}
            <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
            
            {/* Content container aligned with article body */}
            <div className="absolute inset-0 z-10">
              <div className="container mx-auto px-4 md:px-6 lg:px-8 max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl h-full">
                <div className="relative h-full">
                  <ArticleHeader article={article} heroImage={null} isOverlay={true} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header content - aligned with body container (only when no hero image) */}
      {!shouldShowHeroImage && (
        <div className={cn(
          "container px-4 md:px-6 lg:px-8",
          // Same max widths as body content for perfect alignment
          "max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto",
          "pt-8" // Add top padding when no hero image
        )}>
          <ArticleHeader article={article} heroImage={null} isOverlay={false} />
        </div>
      )}

      {/* Article Title - positioned between hero and content */}
      <div className={cn(
        "container px-4 md:px-6 lg:px-8",
        "max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto",
        shouldShowHeroImage ? "mt-6" : "mt-8" // More spacing between header and title when no hero image
      )}>
        <h1 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black tracking-tight leading-tight text-foreground">
          {renderWithFormatting(getBestTitle(article))}
        </h1>
        {/* Summary Block: show only if article can generate summaries */}
        {shouldShowSummaryBlock(article) && (
          <div className="mt-4 md:mt-6">
            <SummaryBlock
              summary={article.summary as any}
              loading={summaryLoading}
              error={summaryError}
              onGenerate={handleGenerateSummary}
            />
          </div>
        )}
      </div>
      
      {/* Article content - matching container constraints */}
      <div className={cn(
        "container px-4 md:px-6 lg:px-8 space-y-6 mt-6 pb-20 md:pb-8",
        // Same max widths as header for perfect alignment
        "max-w-full md:max-w-3xl lg:max-w-4xl xl:max-w-4xl mx-auto"
      )}>

        {/* Article Content */}
        <div className="article-content">
          {article.richContent && article.richContent.blocks && article.richContent.blocks.length > 0 ? (
            <RichArticleRenderer
              blocks={getFilteredContentBlocks()}
              mediaAssets={article.richContent.mediaAssets}
              formattingData={article.richContent.formattingData}
              fallbackContent={article.content}
              className="prose prose-gray max-w-none dark:prose-invert prose-base md:prose-lg lg:prose-xl article-content-font"
            />
          ) : (
            <div className="prose prose-gray max-w-none dark:prose-invert prose-base md:prose-lg lg:prose-xl article-content-font">
          {article.content ? (
            <div dangerouslySetInnerHTML={{ __html: article.content }} />
          ) : (
                <p className="text-muted-foreground">{article.description}</p>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-center pt-4 md:pt-8">
          <Link href={article.url} target="_blank" rel="noopener noreferrer">
            <Button className="gap-2 h-10 md:h-11 px-4 md:px-6 text-sm md:text-base">
              Read the full article
              <ExternalLink className="h-4 w-4 md:h-5 md:w-5" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Article Action Bar - Only show on mobile */}
      <div className="md:hidden">
        <ArticleActionBar article={article} />
      </div>

      {/* Back to Top Button */}
      <BackToTop showAfter={300} />
    </div>
  )
}
