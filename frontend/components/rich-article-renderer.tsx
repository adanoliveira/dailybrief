"use client"

import React, { useState } from 'react'
import { ContentBlock, MediaAsset, FormattingData } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Play, Pause, Volume2, VolumeX, ExternalLink, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Tweet } from 'react-tweet'
import parse from 'html-react-parser'

interface RichArticleRendererProps {
  blocks: ContentBlock[]
  mediaAssets: MediaAsset[]
  formattingData: FormattingData
  fallbackContent?: string
  className?: string
}

export function RichArticleRenderer({ 
  blocks, 
  mediaAssets, 
  formattingData, 
  fallbackContent,
  className 
}: RichArticleRendererProps) {
  // If no rich content blocks, fall back to regular content
  if (!blocks || blocks.length === 0) {
    return (
      <div className={cn("prose prose-gray max-w-none dark:prose-invert", className)}>
        {fallbackContent ? (
          parse(fallbackContent)
        ) : (
          <p className="text-muted-foreground">No content available</p>
        )}
      </div>
    )
  }

  // Sort blocks by position
  const sortedBlocks = [...blocks].sort((a, b) => a.position - b.position)

  return (
    <div className={cn("space-y-6", className)}>
      {sortedBlocks.map((block, index) => (
        <ContentBlockRenderer 
          key={`${block.type}-${block.position}-${index}`}
          block={block}
          mediaAssets={mediaAssets}
        />
      ))}
    </div>
  )
}

interface ContentBlockRendererProps {
  block: ContentBlock
  mediaAssets: MediaAsset[]
}

function ContentBlockRenderer({ block, mediaAssets }: ContentBlockRendererProps) {
  switch (block.type) {
    case 'heading':
      return <HeadingBlock block={block} />
    case 'paragraph':
      return <ParagraphBlock block={block} />
    case 'subtitle':
      return <SubtitleBlock block={block} />
    case 'pullquote':
      return <PullquoteBlock block={block} />
    case 'image':
    case 'img':  // Backend creates 'img' type blocks
    case 'figure':  // Backend also creates 'figure' type blocks
      return <ImageBlock block={block} mediaAssets={mediaAssets} />
    case 'video':
    case 'video_embed':
      return <VideoBlock block={block} mediaAssets={mediaAssets} />
    case 'audio':
      return <AudioBlock block={block} mediaAssets={mediaAssets} />
    case 'quote':
      return <QuoteBlock block={block} />
    case 'list':
      return <ListBlock block={block} />
    case 'code':
      return <CodeBlock block={block} />
    case 'table':
      return <TableBlock block={block} />
    case 'embed':
      return <EmbedBlock block={block} />
    case 'twitter_embed':
      return <TwitterEmbedBlock block={block} />
    default:
      return null
  }
}

// Enhanced content rendering with better HTML formatting support
const renderContentWithLineBreaks = (content: string) => {
  // Always use HTML parsing to ensure consistent JSX return type
  // This handles both line breaks and existing HTML tags properly
  return parse(content)
}

// Enhanced content wrapper with formatting support
export const withFormattingSupport = (className: string = "") => cn(
  className,
  // Basic typography
  "prose prose-gray max-w-none dark:prose-invert",
  // Enhanced formatting element styling
  "[&_em]:italic [&_em]:text-inherit [&_em]:font-medium",
  "[&_strong]:font-semibold [&_strong]:text-inherit",
  "[&_u]:underline [&_u]:underline-offset-2 [&_u]:decoration-current",
  "[&_mark]:bg-yellow-200 [&_mark]:dark:bg-yellow-900/30 [&_mark]:px-1 [&_mark]:py-0.5 [&_mark]:rounded",
  "[&_code]:bg-muted [&_code]:text-foreground [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_code]:font-mono",
  "[&_sub]:text-xs [&_sub]:align-sub",
  "[&_sup]:text-xs [&_sup]:align-super",
  "[&_small]:text-sm [&_small]:text-muted-foreground",
  // Link styling
  "[&_a]:text-primary [&_a]:underline [&_a]:underline-offset-4 [&_a]:decoration-primary/60",
  "[&_a:hover]:text-primary/80 [&_a:hover]:decoration-primary/80 [&_a]:transition-colors"
)

// Helper function to render content with HTML formatting support
export const renderWithFormatting = (content: string) => {
  if (typeof content === 'string' && content.includes('<')) {
    return parse(content)
  }
  return content
}

// Individual block components
function HeadingBlock({ block }: { block: ContentBlock }) {
  const level = block.level || 2
  const HeadingTag = `h${Math.min(Math.max(level, 1), 6)}` as keyof JSX.IntrinsicElements
  
  return (
    <HeadingTag 
      id={block.id}
      className={withFormattingSupport(cn(
        "font-black tracking-tight scroll-m-20 text-foreground [&:not(:first-child)]:mt-12 mb-6",
        level === 1 && "text-3xl md:text-4xl lg:text-5xl",
        level === 2 && "text-2xl md:text-3xl lg:text-4xl",
        level === 3 && "text-xl md:text-2xl lg:text-3xl",
        level === 4 && "text-lg md:text-xl lg:text-2xl",
        level === 5 && "text-lg md:text-xl lg:text-2xl",
        level === 6 && "text-base md:text-lg lg:text-xl",
        block.classes?.join(' ')
      ))}
    >
      {parse(block.content || block.text || '')}
    </HeadingTag>
  )
}

function SubtitleBlock({ block }: { block: ContentBlock }) {
  // Enhanced subtitle rendering with robust HTML link handling
  const renderContentWithLinks = () => {
    let content = block.content || block.text || ''
    
    // Check if content already contains HTML anchor tags
    if (content.includes('<a ')) {
      // Content already has HTML links, apply additional processing for safety
      // Ensure target="_blank" and rel="noopener noreferrer" are set for security
      content = content.replace(
        /<a\s+href="([^"]*)"(?![^>]*target=)/g, 
        '<a href="$1" target="_blank" rel="noopener noreferrer"'
      )
      return renderContentWithLineBreaks(content)
    }
    
    // Fallback: If no HTML links but we have metadata links, inject them
    const links = block.metadata?.links || []
    if (links.length > 0) {
      links.forEach((link: { text: string; href: string }) => {
        // Escape regex special characters in href for pattern matching
        const linkPattern = new RegExp(`\\[${link.href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'g')
        content = content.replace(linkPattern, '')
        
        // Replace the link text with a clickable link (only if not already a link)
        const textPattern = new RegExp(`\\b${link.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g')
        content = content.replace(textPattern, (match, offset, string) => {
          // Check if this text is already inside an HTML tag
          const beforeMatch = string.substring(0, offset)
          const lastOpenTag = beforeMatch.lastIndexOf('<')
          const lastCloseTag = beforeMatch.lastIndexOf('>')
          
          // If we're inside an HTML tag, don't replace
          if (lastOpenTag > lastCloseTag) {
            return match
          }
          
          return `<a href="${link.href}" target="_blank" rel="noopener noreferrer" class="text-primary hover:text-primary/80 underline underline-offset-4 transition-colors">${link.text}</a>`
        })
      })
    }
    
    return renderContentWithLineBreaks(content)
  }

  return (
    <div 
      className={withFormattingSupport(cn(
        "text-xl leading-8 text-foreground/80 font-semibold tracking-tight [&:not(:first-child)]:mt-8 mb-4",
        block.classes?.join(' ')
      ))}
    >
      {renderContentWithLinks()}
    </div>
  )
}

function ParagraphBlock({ block }: { block: ContentBlock }) {
  // Enhanced paragraph rendering with robust HTML link handling
  const renderContentWithLinks = () => {
    let content = block.content || block.text || ''
    
    // Check if content already contains HTML anchor tags
    if (content.includes('<a ')) {
      // Content already has HTML links, apply additional processing for safety
      // Ensure target="_blank" and rel="noopener noreferrer" are set for security
      content = content.replace(
        /<a\s+href="([^"]*)"(?![^>]*target=)/g, 
        '<a href="$1" target="_blank" rel="noopener noreferrer"'
      )
      return renderContentWithLineBreaks(content)
    }
    
    // Fallback: If no HTML links but we have metadata links, inject them
    const links = block.metadata?.links || []
    if (links.length > 0) {
      links.forEach((link: { text: string; href: string }) => {
        // Escape regex special characters in href for pattern matching
        const linkPattern = new RegExp(`\\[${link.href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'g')
        content = content.replace(linkPattern, '')
        
        // Replace the link text with a clickable link (only if not already a link)
        const textPattern = new RegExp(`\\b${link.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g')
        content = content.replace(textPattern, (match, offset, string) => {
          // Check if this text is already inside an HTML tag
          const beforeMatch = string.substring(0, offset)
          const lastOpenTag = beforeMatch.lastIndexOf('<')
          const lastCloseTag = beforeMatch.lastIndexOf('>')
          
          // If we're inside an HTML tag, don't replace
          if (lastOpenTag > lastCloseTag) {
            return match
          }
          
          return `<a href="${link.href}" target="_blank" rel="noopener noreferrer" class="text-primary hover:text-primary/80 underline underline-offset-4 transition-colors">${link.text}</a>`
        })
      })
    }
    
    return renderContentWithLineBreaks(content)
  }

  return (
    <div 
      className={withFormattingSupport(cn(
        "text-base leading-7 [&:not(:first-child)]:mt-6",
        block.classes?.join(' ')
      ))}
    >
      {renderContentWithLinks()}
    </div>
  )
}

function ImageBlock({ block, mediaAssets }: { block: ContentBlock; mediaAssets: MediaAsset[] }) {
  const [imageError, setImageError] = useState(false)
  const [imageLoading, setImageLoading] = useState(true)
  
  // Find corresponding media asset
  const mediaAsset = mediaAssets.find(asset => 
    asset.type === 'image' && asset.position === block.position
  )
  
  // Read from metadata first, then fallback to direct properties, then mediaAsset
  const src = block.metadata?.src || block.src || mediaAsset?.src
  const alt = block.metadata?.alt || block.alt || mediaAsset?.alt || ''
  
  // Enhanced caption handling: only show meaningful captions
  let caption = block.metadata?.caption || block.caption || mediaAsset?.caption
  
  // If caption is empty or just the content placeholder, don't use content as fallback
  if (!caption || caption.trim() === '') {
    caption = block.content && block.content.trim() !== '' ? block.content : ''
  }
  
  // Don't show caption if it's just generic text or empty
  const shouldShowCaption = caption && caption.trim() !== '' && caption !== 'Image' && caption !== 'Figure'
  
  const title = block.title || mediaAsset?.title
  
  // Debug logging in development
  if (process.env.NODE_ENV === 'development') {
    console.log('ImageBlock render:', { 
      blockType: block.type, 
      position: block.position,
      src, 
      alt, 
      caption,
      shouldShowCaption,
      imageError,
      imageLoading 
    })
  }
  
  // If no src or permanent error, show caption-only version
  if (!src || imageError) {
    if (shouldShowCaption && process.env.NODE_ENV === 'development') {
      console.log('Showing caption-only for image:', caption)
    }
    
    // Show caption in a styled box when image fails (only if meaningful)
    if (shouldShowCaption) {
      return (
        <figure className="my-8">
          <div className="border border-dashed border-muted-foreground/20 rounded-lg p-4 bg-muted/20 text-center">
            <p className="text-sm text-muted-foreground mb-2">📷 Image unavailable</p>
            <figcaption className={withFormattingSupport("text-sm text-muted-foreground italic")}>
              {parse(caption)}
            </figcaption>
          </div>
        </figure>
      )
    }
    return null
  }

  return (
    <figure className="my-8 -mx-4 md:-mx-6 lg:-mx-8">
      <div className="relative overflow-hidden bg-muted">
        {imageLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        )}
        <img
          src={src}
          alt={alt}
          title={title}
          className={cn(
            "w-full h-auto transition-opacity duration-300",
            imageLoading ? "opacity-0" : "opacity-100"
          )}
          onLoad={() => {
            setImageLoading(false)
            if (process.env.NODE_ENV === 'development') {
              console.log('Image loaded successfully:', src)
            }
          }}
          onError={(e) => {
            setImageError(true)
            setImageLoading(false)
            if (process.env.NODE_ENV === 'development') {
              console.error('Image failed to load:', src, e)
            }
          }}
          loading="lazy"
        />
      </div>
      {shouldShowCaption && (
        <figcaption className={withFormattingSupport("mt-3 mx-4 md:mx-6 lg:mx-8 text-sm text-muted-foreground text-center italic")}>
          {parse(caption)}
        </figcaption>
      )}
    </figure>
  )
}

function VideoBlock({ block, mediaAssets }: { block: ContentBlock; mediaAssets: MediaAsset[] }) {
  const [isPlaying, setIsPlaying] = useState(false)
  
  // Find corresponding media asset
  const mediaAsset = mediaAssets.find(asset => 
    (asset.type === 'video' || asset.type === 'video_embed') && asset.position === block.position
  )
  
  // Read from metadata structure that backend provides
  const src = block.metadata?.src || block.src || mediaAsset?.src
  const caption = block.metadata?.caption || block.caption || mediaAsset?.caption || block.content
  const embedType = block.metadata?.embed_type || mediaAsset?.platform
  
  if (!src) {
    return null
  }

  // Handle embedded videos (YouTube, Vimeo, etc.)
  if (embedType || src.includes('youtube.com') || src.includes('youtu.be') || src.includes('vimeo.com')) {
    return (
      <figure className="my-8">
        <div className="relative aspect-video overflow-hidden rounded-lg bg-muted">
          <iframe
            src={src}
            className="absolute inset-0 w-full h-full"
            allowFullScreen
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            title={caption || "Embedded video"}
          />
        </div>
        {caption && (
          <figcaption className={withFormattingSupport("mt-3 text-sm text-muted-foreground text-center italic")}>
            {parse(caption)}
          </figcaption>
        )}
      </figure>
    )
  }

  // Handle native HTML5 video
  return (
    <figure className="my-8">
      <div className="relative aspect-video overflow-hidden rounded-lg bg-muted">
        <video
          src={src}
          controls
          className="w-full h-full object-cover"
          preload="metadata"
        >
          Your browser does not support the video tag.
        </video>
      </div>
      {caption && (
        <figcaption className={withFormattingSupport("mt-3 text-sm text-muted-foreground text-center italic")}>
          {parse(caption)}
        </figcaption>
      )}
    </figure>
  )
}

function AudioBlock({ block, mediaAssets }: { block: ContentBlock; mediaAssets: MediaAsset[] }) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  
  // Find corresponding media asset
  const mediaAsset = mediaAssets.find(asset => 
    asset.type === 'audio' && asset.position === block.position
  )
  
  const src = block.src || mediaAsset?.src
  const caption = block.caption || mediaAsset?.caption
  
  if (!src) {
    return null
  }

  return (
    <figure className="my-8">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsPlaying(!isPlaying)}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMuted(!isMuted)}
              >
                {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              </Button>
            </div>
            <div className="flex-1">
              <audio
                src={src}
                controls
                className="w-full"
                preload="metadata"
              >
                Your browser does not support the audio tag.
              </audio>
            </div>
          </div>
          {caption && (
            <p className={withFormattingSupport("mt-3 text-sm text-muted-foreground italic")}>
              {parse(caption)}
            </p>
          )}
        </CardContent>
      </Card>
    </figure>
  )
}

function QuoteBlock({ block }: { block: ContentBlock }) {
  // Simplified quote rendering using universal line break handling
  const content = block.content || block.text || ''

  return (
    <blockquote className={withFormattingSupport(cn(
      "my-6 border-l-4 border-primary pl-6 italic text-lg leading-relaxed",
      block.classes?.join(' ')
    ))}>
      <div className="space-y-2">
        {renderContentWithLineBreaks(content)}
      </div>
      {block.cite && (
        <cite className={withFormattingSupport("mt-4 block text-sm text-muted-foreground not-italic")}>
          — {parse(block.cite)}
        </cite>
      )}
    </blockquote>
  )
}

function ListBlock({ block }: { block: ContentBlock }) {
  // Read from metadata structure that backend provides
  const listType = block.metadata?.list_type || block.listType || 'ul'
  const items: string[] = block.metadata?.items || block.items || []
  
  const ListTag = listType === 'ol' ? 'ol' : 'ul'
  
  return (
    <ListTag className={withFormattingSupport(cn(
      "my-6 ml-6 list-disc [&>li]:mt-2",
      listType === 'ol' && "list-decimal",
      block.classes?.join(' ')
    ))}>
      {items.map((item: string, index: number) => (
        <li key={index}>{parse(item)}</li>
      ))}
    </ListTag>
  )
}

function CodeBlock({ block }: { block: ContentBlock }) {
  const [copied, setCopied] = useState(false)
  
  const handleCopy = async () => {
    if (block.content) {
      await navigator.clipboard.writeText(block.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }
  
  return (
    <div className="my-6">
      <div className="relative">
        <pre className={cn(
          "overflow-x-auto rounded-lg bg-muted p-4 text-sm",
          block.classes?.join(' ')
        )}>
          <code className={block.language ? `language-${block.language}` : ''}>
            {block.content}
          </code>
        </pre>
        <Button
          variant="ghost"
          size="sm"
          className="absolute top-2 right-2"
          onClick={handleCopy}
        >
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  )
}

function TableBlock({ block }: { block: ContentBlock }) {
  return (
    <div className="my-6 overflow-x-auto">
      <div 
        className="min-w-full"
        dangerouslySetInnerHTML={{ __html: block.content || '' }}
      />
    </div>
  )
}

function EmbedBlock({ block }: { block: ContentBlock }) {
  return (
    <div className="my-8">
      <Card>
        <CardContent className="p-4">
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: block.content || '' }}
          />
          {block.src && (
            <div className="mt-4 flex justify-center">
              <Button variant="outline" size="sm" asChild>
                <a href={block.src} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Original
                </a>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function TwitterEmbedBlock({ block }: { block: ContentBlock }) {
  // Extract Twitter embed data from metadata
  const tweetId = block.metadata?.tweet_id
  const embedUrl = block.metadata?.embed_url
  
  // Try to extract tweet ID from URL if not available directly
  const extractTweetId = (url: string): string | null => {
    if (!url) return null
    
    // Match various Twitter URL formats
    const patterns = [
      /twitter\.com\/\w+\/status\/(\d+)/,
      /x\.com\/\w+\/status\/(\d+)/,
      /platform\.twitter\.com\/embed.*[&?]id=(\d+)/
    ]
    
    for (const pattern of patterns) {
      const match = url.match(pattern)
      if (match && match[1]) {
        return match[1]
      }
    }
    
    return null
  }
  
  // Get the actual tweet ID to use
  const finalTweetId = tweetId || extractTweetId(embedUrl || '')
  
  // If we can't find a tweet ID, show fallback
  if (!finalTweetId) {
    return (
      <div className="my-8 flex justify-center">
        <Card className="mx-auto max-w-md">
          <CardContent className="p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">𝕏</span>
              </div>
              <div>
                <p className="font-semibold text-sm">Twitter</p>
                <p className="text-xs text-muted-foreground">@twitter</p>
              </div>
            </div>
            
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Unable to load tweet embed.
              </p>
              {embedUrl && (
                <Button variant="outline" size="sm" asChild className="w-full">
                  <a href={embedUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View on Twitter
                  </a>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  // Use the react-tweet component
  return (
    <div className="my-8 flex justify-center">
      <div className="w-full max-w-lg">
        <Tweet id={finalTweetId} />
      </div>
    </div>
  )
}

function PullquoteBlock({ block }: { block: ContentBlock }) {
  // Enhanced pullquote rendering with robust HTML link handling
  const renderContentWithLinks = () => {
    let content = block.content || block.text || ''
    
    // Check if content already contains HTML anchor tags
    if (content.includes('<a ')) {
      // Content already has HTML links, apply additional processing for safety
      // Ensure target="_blank" and rel="noopener noreferrer" are set for security
      content = content.replace(
        /<a\s+href="([^"]*)"(?![^>]*target=)/g, 
        '<a href="$1" target="_blank" rel="noopener noreferrer"'
      )
      return renderContentWithLineBreaks(content)
    }
    
    // Fallback: If no HTML links but we have metadata links, inject them
    const links = block.metadata?.links || []
    if (links.length > 0) {
      links.forEach((link: { text: string; href: string }) => {
        // Escape regex special characters in href for pattern matching
        const linkPattern = new RegExp(`\\[${link.href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'g')
        content = content.replace(linkPattern, '')
        
        // Replace the link text with a clickable link (only if not already a link)
        const textPattern = new RegExp(`\\b${link.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g')
        content = content.replace(textPattern, (match, offset, string) => {
          // Check if this text is already inside an HTML tag
          const beforeMatch = string.substring(0, offset)
          const lastOpenTag = beforeMatch.lastIndexOf('<')
          const lastCloseTag = beforeMatch.lastIndexOf('>')
          
          // If we're inside an HTML tag, don't replace
          if (lastOpenTag > lastCloseTag) {
            return match
          }
          
          return `<a href="${link.href}" target="_blank" rel="noopener noreferrer" class="text-primary hover:text-primary/80 underline underline-offset-4 transition-colors font-medium">${link.text}</a>`
        })
      })
    }
    
    return renderContentWithLineBreaks(content)
  }

  return (
    <div className="my-8">
      <blockquote 
        className={withFormattingSupport(cn(
          // Layout and spacing - minimal margins
          "mx-auto max-w-2xl px-8",
          
          // Typography - slightly larger and emphasis without being too bold
          "text-lg lg:text-xl leading-relaxed",
          "font-normal text-foreground/95",
          
          // Minimal visual accent - just a subtle left border
          "border-l-2 border-muted-foreground/20 pl-6",
          
          // Custom classes
          block.classes?.join(' ')
        ))}
      >
        {/* Clean content without extra decorations */}
        <div className="[&>*]:my-0">
          {renderContentWithLinks()}
        </div>
        
        {/* Citation if available - clean and minimal */}
        {block.cite && (
          <cite className={withFormattingSupport("mt-3 block text-sm text-muted-foreground not-italic")}>
            — {parse(block.cite)}
          </cite>
        )}
      </blockquote>
    </div>
  )
} 