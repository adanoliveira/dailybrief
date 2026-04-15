import { ContentBlock } from "./api";

/**
 * Extract the first image from content blocks to use as hero image
 */
export function extractHeroImage(contentBlocks: ContentBlock[]): {
  heroImage: string | null;
  filteredBlocks: ContentBlock[];
} {
  if (!contentBlocks || contentBlocks.length === 0) {
    return { heroImage: null, filteredBlocks: [] };
  }

  // Find the first image block
  const firstImageIndex = contentBlocks.findIndex(block => 
    (block.type === 'image' || block.type === 'img' || block.type === 'figure') &&
    (block.metadata?.src || block.src)
  );

  if (firstImageIndex === -1) {
    return { heroImage: null, filteredBlocks: contentBlocks };
  }

  const imageBlock = contentBlocks[firstImageIndex];
  const heroImage = imageBlock.metadata?.src || imageBlock.src || null;

  // Filter out the hero image from content blocks to avoid duplication
  const filteredBlocks = contentBlocks.filter((_, index) => index !== firstImageIndex);

  return { heroImage, filteredBlocks };
}

/**
 * Get the best available hero image from article data
 */
export function getHeroImage(article: any): {
  heroImage: string | null;
  filteredBlocks: ContentBlock[];
} {
  const fallbackImage = article.imageUrl || null;
  const allBlocks = article.richContent?.blocks || [];
  
  // First try to extract from rich content blocks
  if (allBlocks.length > 0) {
    const result = extractHeroImage(allBlocks);
    
    // If we found an image in rich content, use it (rich content is primary source)
    if (result.heroImage) {
      // Log the decision for debugging
      const isArchivedUrl = result.heroImage.includes('web.archive.org') || 
                           result.heroImage.includes('archive.') ||
                           result.heroImage.includes('/dims4/') ||
                           result.heroImage.includes('wayback');
      
      if (isArchivedUrl) {
        console.log('Using rich content image (archived URL) with fallback available:', {
          richContentImage: result.heroImage,
          fallbackImage: fallbackImage
        });
      } else {
        console.log('Using rich content image (direct URL):', result.heroImage);
      }
      
      return result;
    }
    
    // No image found in rich content blocks, but we have blocks to filter
    return {
      heroImage: fallbackImage,
      filteredBlocks: allBlocks
    };
  }

  // Fallback to article image from NewsAPI when no rich content
  return {
    heroImage: fallbackImage,
    filteredBlocks: []
  };
}

/**
 * Format date for article display
 */
export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(date);
  } catch (e) {
    return dateString;
  }
}

/**
 * Get best title from article data (visual title or regular title)
 */
export function getBestTitle(article: any): string {
  // Check rich content for visual title first
  if (article.richContent?.blocks) {
    const headingBlock = article.richContent.blocks.find(
      (block: ContentBlock) => block.type === 'heading' && (block.level === 1 || block.level === undefined) && block.content
    );
    if (headingBlock?.content) {
      return headingBlock.content;
    }
  }

  // Fallback to visual title or regular title
  return article.visualTitle || article.title;
}

/**
 * Truncate text to specified length with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
} 

// ===== ARTICLE PROCESSING STATUS UTILITIES =====

/**
 * Article processing pipeline status types
 */
export type ArticleProcessingStatus = 'pending' | 'fetching' | 'processing' | 'completed' | 'failed';

/**
 * Article content quality levels
 */
export type ArticleContentQuality = 'rich' | 'clean' | 'basic' | 'insufficient' | 'failed' | 'processing';

/**
 * Determines if an article can generate summaries based on content availability.
 * 
 * Three "sad paths" are handled:
 * 1. Article not processed yet: Still in fetch/processing pipeline
 *    → Summary block is NOT shown (article still being processed)
 * 2. Article processing failed: Processing completed but failed or insufficient content
 *    → Summary block is NOT shown (can't generate meaningful summaries)
 * 3. Article processed successfully: Has content but no summary generated yet  
 *    → Summary block IS shown with "generate" option
 */
export function canGenerateSummary(article: any): boolean {
  if (!article) return false;
  
  // Check processing pipeline status
  const fetchStatus = article.fetchStatus;
  const processStatus = article.processStatus;
  
  // Case 1: Article hasn't been processed yet - don't show summary block
  const isStillProcessing = 
    fetchStatus === 'pending' || 
    fetchStatus === 'fetching' ||
    processStatus === 'pending' || 
    processStatus === 'processing';
  
  if (isStillProcessing) return false;
  
  // Case 2: Article processing explicitly failed - don't show summary block
  const isProcessingFailed = 
    fetchStatus === 'failed' || 
    processStatus === 'failed';
  
  if (isProcessingFailed) return false;
  
  // Priority 1: Check if we have rich content blocks (fully processed article)
  const hasRichContent = article.richContent?.blocks && article.richContent.blocks.length > 0;
  
  // Priority 2: Check if we have adequate clean content for summary generation  
  const hasCleanContent = article.cleanContent && article.cleanContent.length > 300;
  
  // Priority 3: Check if we have basic content as fallback
  const hasBasicContent = article.content && article.content.length > 200;
  
  // Case 3: Show summary block if we have any adequate content for summarization
  return hasRichContent || hasCleanContent || hasBasicContent;
}

/**
 * Determines if the summary block should be shown for an article.
 * Alias for canGenerateSummary for better readability in components.
 */
export function shouldShowSummaryBlock(article: any): boolean {
  return canGenerateSummary(article);
}

/**
 * Gets the content quality level for debugging and potential future features.
 * Returns: 'rich' | 'clean' | 'basic' | 'insufficient' | 'failed' | 'processing'
 */
export function getContentQualityLevel(article: any): ArticleContentQuality {
  if (!article) return 'insufficient';
  
  // Check processing pipeline status
  const fetchStatus = article.fetchStatus;
  const processStatus = article.processStatus;
  
  // Still processing
  const isStillProcessing = 
    fetchStatus === 'pending' || 
    fetchStatus === 'fetching' ||
    processStatus === 'pending' || 
    processStatus === 'processing';
  
  if (isStillProcessing) return 'processing';
  
  // Processing failed
  const isProcessingFailed = 
    fetchStatus === 'failed' || 
    processStatus === 'failed';
  
  if (isProcessingFailed) {
    return 'failed';
  }
  
  if (article.richContent?.blocks && article.richContent.blocks.length > 0) {
    return 'rich';
  }
  
  if (article.cleanContent && article.cleanContent.length > 300) {
    return 'clean';
  }
  
  if (article.content && article.content.length > 200) {
    return 'basic';
  }
  
  return 'insufficient';
}

/**
 * Gets a human-readable description of the article's processing status.
 * Useful for debugging, admin interfaces, or user-facing status messages.
 */
export function getProcessingStatusDescription(article: any): string {
  const quality = getContentQualityLevel(article);
  
  switch (quality) {
    case 'processing':
      return 'Article is being processed';
    case 'failed':
      return 'Article processing failed';
    case 'rich':
      return 'Article has rich content blocks';
    case 'clean':
      return 'Article has clean processed content';
    case 'basic':
      return 'Article has basic text content';
    case 'insufficient':
      return 'Article has insufficient content';
    default:
      return 'Unknown processing status';
  }
}

/**
 * Checks if an article is ready for display (has any usable content).
 * This is different from summary generation - articles can be displayed
 * even if they can't generate summaries.
 */
export function isArticleReadyForDisplay(article: any): boolean {
  if (!article) return false;
  
  // Check if we have any displayable content
  return !!(
    article.richContent?.blocks?.length > 0 ||
    article.cleanContent?.length > 100 ||
    article.content?.length > 100 ||
    article.description?.length > 50
  );
}

/**
 * Gets the best available content for summary generation.
 * Returns the content and its source type.
 */
export function getBestContentForSummarization(article: any): { 
  content: string | null; 
  sourceType: 'rich_content_blocks' | 'clean_content' | 'basic_content' | null;
} {
  if (!article) return { content: null, sourceType: null };
  
  // Priority 1: Rich content blocks (most structured)
  if (article.richContent?.blocks && article.richContent.blocks.length > 3) {
    // Convert blocks to markdown or text format
    // Note: This would need proper implementation based on content block structure
    return { 
      content: article.richContent.blocks.map((block: any) => block.content || '').join('\n\n'),
      sourceType: 'rich_content_blocks'
    };
  }
  
  // Priority 2: Clean content (processed)
  if (article.cleanContent && article.cleanContent.length > 200) {
    return { 
      content: article.cleanContent, 
      sourceType: 'clean_content' 
    };
  }
  
  // Priority 3: Basic content (fallback)
  if (article.content && article.content.length > 200) {
    return { 
      content: article.content, 
      sourceType: 'basic_content' 
    };
  }
  
  return { content: null, sourceType: null };
}

// ===== ARTICLE SUMMARY GENERATION UTILITIES =====

/**
 * Summary generation result types
 */
export type SummaryGenerationResult = {
  success: true;
  summary: any;
  status: 'completed';
} | {
  success: true;
  status: 'processing';
  taskId?: string;
} | {
  success: false;
  error: string;
  status: 'failed';
};

/**
 * Core business logic for generating article summaries.
 * Handles the API calls and polling logic without UI concerns.
 * 
 * @param articleId - The article ID to generate summary for
 * @param options - Generation options (async by default)
 * @returns Promise<SummaryGenerationResult>
 */
export async function generateArticleSummaryLogic(
  articleId: string,
  options: { async?: boolean } = { async: true }
): Promise<SummaryGenerationResult> {
  try {
    // Import the API functions dynamically to avoid circular dependencies
    const { generateArticleSummary, pollForSummaryCompletion } = await import('@/lib/api');
    
    // Start summary generation
    const response = await generateArticleSummary(articleId, options);
    
    if (response.status === 'processing') {
      // Poll for completion if async
      const statusResponse = await pollForSummaryCompletion(articleId, 20, 2000);
      
      if (statusResponse.status === 'completed' && statusResponse.summary) {
        return {
          success: true,
          summary: statusResponse.summary,
          status: 'completed'
        };
      } else if (statusResponse.status === 'failed') {
        return {
          success: false,
          error: statusResponse.errorMessage || 'Summary generation failed',
          status: 'failed'
        };
      } else {
        return {
          success: false,
          error: 'Summary generation timed out',
          status: 'failed'
        };
      }
    } else if (response.summary) {
      // Synchronous completion
      return {
        success: true,
        summary: response.summary,
        status: 'completed'
      };
    } else {
      return {
        success: false,
        error: response.error || 'Failed to start summary generation',
        status: 'failed'
      };
    }
  } catch (error) {
    console.error('Summary generation error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'An unexpected error occurred',
      status: 'failed'
    };
  }
}

/**
 * Check if an article already has a summary generated
 */
export function hasExistingSummary(article: any): boolean {
  return !!(article?.summary && (
    article.summary.keyPoints?.length > 0 ||
    article.summary.overview ||
    article.summary.oneLineStretch ||
    article.summary.oneLinePunchy
  ));
} 