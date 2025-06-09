"use client"

import { Button } from "@/components/ui/button"
import { PublicationBadge } from "@/components/ui/publication-badge"
import { ExternalLink, Clock, ArrowLeft } from "lucide-react"
import { formatDate, getBestTitle, truncateText } from "@/lib/article-utils"
import { renderWithFormatting } from "@/components/rich-article-renderer"
import { cn } from "@/lib/utils"
import { useRouter } from "next/navigation"

interface ArticleHeaderProps {
  article: {
    title: string;
    visualTitle?: string;
    author?: string;
    publishedAt: string;
    readTime?: number;
    url: string;
    source: {
      name: string;
      logoUrl?: string;
    };
    topics?: Array<{
      id: number;
      name: string;
      slug: string;
    }>;
  };
  heroImage?: string | null;
}

export function ArticleHeader({ article, heroImage }: ArticleHeaderProps) {
  const title = getBestTitle(article);
  const hasHeroImage = Boolean(heroImage);
  const router = useRouter();

  return (
    <div className="relative">
      {/* Hero Image - Full width */}
      {hasHeroImage && (
        <div className="relative -mx-4 md:-mx-6 lg:-mx-8">
          <div className="relative w-full aspect-[6/4] overflow-hidden">
            <img
              src={heroImage!}
              alt={title}
              className="w-full h-full object-cover"
              onError={(e) => {
                // Hide the image container if loading fails
                const container = (e.target as HTMLElement).closest('.relative') as HTMLElement;
                if (container) {
                  container.style.display = 'none';
                }
              }}
            />
            
            {/* Gradient overlay only behind text (bottom 1/5 of image) */}
            <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
            

            
            {/* Visit Original Button - always top right */}
            <div className="absolute top-4 right-4 z-20">
              <Button
                variant="ghost"
                size="xs"
                asChild
                className="text-white hover:text-white/80 bg-transparent hover:bg-white/10 border border-white/30 hover:border-white/50"
              >
                <a 
                  href={article.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center"
                >
                  <span>Read Original</span>
                  <ExternalLink />
                </a>
              </Button>
            </div>
            
            {/* Metadata overlay on image */}
            <div className="absolute bottom-4 left-4 right-4 z-10">
              <ArticleMetadata 
                article={article}
                variant="overlay"
              />
            </div>
          </div>
        </div>
      )}

      {/* Navigation when no hero image */}
      {!hasHeroImage && (
        <div className="flex justify-end mb-4">
          {/* Visit Original Button */}
          <Button
            variant="outline"
            size="xs"
            asChild
          >
            <a 
              href={article.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center"
            >
              <span>Visit Original</span>
              <ExternalLink />
            </a>
          </Button>
        </div>
      )}

      {/* Metadata above title (when no hero image) */}
      {!hasHeroImage && (
        <div className="mb-4">
          <ArticleMetadata article={article} variant="default" />
        </div>
      )}

      {/* Article Title */}
      <div className={cn("mt-4", hasHeroImage && "mt-6")}>
        <h1 className="text-3xl md:text-4xl lg:text-5xl font-black tracking-tight leading-tight text-foreground">
          {renderWithFormatting(title)}
        </h1>
      </div>
    </div>
  );
}

interface ArticleMetadataProps {
  article: ArticleHeaderProps['article'];
  variant: "default" | "overlay";
}

function ArticleMetadata({ article, variant }: ArticleMetadataProps) {
  const isOverlay = variant === "overlay";
  
  return (
    <div className="space-y-2">
      {/* Publication Badge - more prominent */}
      <PublicationBadge 
        source={article.source}
        size="lg"
        variant={isOverlay ? "overlay" : "default"}
        className={cn(
          isOverlay ? "text-white" : "text-foreground"
        )}
      />
      
      {/* Author, Date, Read Time - secondary hierarchy */}
      <div className={cn(
        "flex items-center gap-2 text-sm flex-wrap",
        isOverlay ? "text-white/90 font-normal" : "text-muted-foreground/90 font-normal"
      )}>
        {article.author && (
          <>
            <span>
              {truncateText(article.author, 19)}
            </span>
            <span>•</span>
          </>
        )}
        <span>{formatDate(article.publishedAt)}</span>
        {article.readTime && (
          <>
            <span>•</span>
            <span>
              {article.readTime} min read
            </span>
          </>
        )}
      </div>
    </div>
  );
} 