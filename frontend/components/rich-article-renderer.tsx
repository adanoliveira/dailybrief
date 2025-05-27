"use client"

import React, { useState } from 'react'
import { ContentBlock, MediaAsset, FormattingData } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Play, Pause, Volume2, VolumeX, ExternalLink, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

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
          <div dangerouslySetInnerHTML={{ __html: fallbackContent }} />
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
    case 'image':
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
    default:
      return <ParagraphBlock block={block} />
  }
}

// Individual block components
function HeadingBlock({ block }: { block: ContentBlock }) {
  const level = block.level || 2
  const HeadingTag = `h${Math.min(Math.max(level, 1), 6)}` as keyof JSX.IntrinsicElements
  
  return (
    <HeadingTag 
      id={block.id}
      className={cn(
        "font-bold tracking-tight scroll-m-20",
        level === 1 && "text-4xl lg:text-5xl",
        level === 2 && "text-3xl lg:text-4xl",
        level === 3 && "text-2xl lg:text-3xl",
        level === 4 && "text-xl lg:text-2xl",
        level === 5 && "text-lg lg:text-xl",
        level === 6 && "text-base lg:text-lg",
        block.classes?.join(' ')
      )}
    >
      {block.content || block.text}
    </HeadingTag>
  )
}

function ParagraphBlock({ block }: { block: ContentBlock }) {
  return (
    <div 
      className={cn(
        "text-base leading-7 [&:not(:first-child)]:mt-6",
        block.classes?.join(' ')
      )}
      dangerouslySetInnerHTML={{ 
        __html: block.content || block.text || '' 
      }}
    />
  )
}

function ImageBlock({ block, mediaAssets }: { block: ContentBlock; mediaAssets: MediaAsset[] }) {
  const [imageError, setImageError] = useState(false)
  const [imageLoading, setImageLoading] = useState(true)
  
  // Find corresponding media asset
  const mediaAsset = mediaAssets.find(asset => 
    asset.type === 'image' && asset.position === block.position
  )
  
  const src = block.src || mediaAsset?.src
  const alt = block.alt || mediaAsset?.alt || ''
  const caption = block.caption || mediaAsset?.caption
  const title = block.title || mediaAsset?.title
  
  if (!src || imageError) {
    return null
  }

  return (
    <figure className="my-8">
      <div className="relative overflow-hidden rounded-lg bg-muted">
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
          onLoad={() => setImageLoading(false)}
          onError={() => {
            setImageError(true)
            setImageLoading(false)
          }}
          loading="lazy"
        />
      </div>
      {caption && (
        <figcaption className="mt-3 text-sm text-muted-foreground text-center italic">
          {caption}
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
  
  const src = block.src || mediaAsset?.src
  const caption = block.caption || mediaAsset?.caption
  const platform = mediaAsset?.platform
  
  if (!src) {
    return null
  }

  // Handle embedded videos (YouTube, Vimeo, etc.)
  if (platform || src.includes('youtube.com') || src.includes('youtu.be') || src.includes('vimeo.com')) {
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
          <figcaption className="mt-3 text-sm text-muted-foreground text-center italic">
            {caption}
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
        <figcaption className="mt-3 text-sm text-muted-foreground text-center italic">
          {caption}
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
            <p className="mt-3 text-sm text-muted-foreground italic">
              {caption}
            </p>
          )}
        </CardContent>
      </Card>
    </figure>
  )
}

function QuoteBlock({ block }: { block: ContentBlock }) {
  return (
    <blockquote className={cn(
      "my-6 border-l-4 border-primary pl-6 italic text-lg",
      block.classes?.join(' ')
    )}>
      <p>{block.content || block.text}</p>
      {block.cite && (
        <cite className="mt-2 block text-sm text-muted-foreground not-italic">
          — {block.cite}
        </cite>
      )}
    </blockquote>
  )
}

function ListBlock({ block }: { block: ContentBlock }) {
  const ListTag = block.listType === 'ol' ? 'ol' : 'ul'
  
  return (
    <ListTag className={cn(
      "my-6 ml-6 list-disc [&>li]:mt-2",
      block.listType === 'ol' && "list-decimal",
      block.classes?.join(' ')
    )}>
      {block.items?.map((item, index) => (
        <li key={index} dangerouslySetInnerHTML={{ __html: item }} />
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