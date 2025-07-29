"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PublicationBadge } from "@/components/ui/publication-badge"
import Link from "next/link"
import { getTopicIcon } from "@/lib/topic-icons"
import parse from 'html-react-parser'
import { cn } from "@/lib/utils"

interface ArticlePreviewWithTopics {
  id: string;
  title: string;
  description: string;
  source: {
    name: string;
    logoUrl?: string;
  };
  publishedAt: string;
  imageUrl?: string;
  readTime?: number;
  topics?: Array<{
    id: number;
    name: string;
    slug: string;
  }>;
}

interface NewsCardProps {
  article: ArticlePreviewWithTopics;
  formatDate: (date: string) => string;
  onArticleClick?: () => void; // Add optional click handler
}

export function NewsCard({ article, formatDate, onArticleClick }: NewsCardProps) {
  const [imageError, setImageError] = useState(false);
  const hasImage = article.imageUrl && !imageError;
  
  // Determine topic from article or use a default
  const displayTopic = useMemo(() => {
    // If article has topics array, use the first one
    if (article.topics && article.topics.length > 0) {
      return article.topics[0];
    }
    
    // Otherwise try to extract topic from topic slug in the query params
    const urlParams = new URLSearchParams(window.location.search);
    const topicParam = urlParams.get('topic');
    
    if (topicParam && topicParam !== 'for-you' && topicParam !== 'all') {
      // Format the slug as a readable name
      const topicName = topicParam
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      
      return {
        id: 0,
        name: topicName,
        slug: topicParam
      };
    }
    
    // Default to "World" if no topic is found
    return {
      id: 0,
      name: "World",
      slug: "world"
    };
  }, [article.topics]);
  
  // Get the topic icon
  const TopicIcon = getTopicIcon(displayTopic.slug);

  return (
    <Link href={`/article/${article.id}`} className="block" onClick={onArticleClick}>
      <Card className={cn("overflow-hidden transition-all cursor-pointer hover:shadow-md dark:hover:shadow-white/15 dark:hover:shadow-lg")}>
        <div className="flex flex-col md:flex-row">
          {/* Image section - conditional rendering based on image availability */}
          {hasImage && (
            <div className="md:w-1/3 h-48 md:h-auto relative overflow-hidden">
              <div 
                className="w-full h-full bg-cover bg-center md:rounded-l" 
                style={{ 
                  backgroundImage: `url(${article.imageUrl})`, 
                  backgroundPosition: 'center',
                  backgroundSize: 'cover'
                }}
                role="img"
                aria-label={article.title}
                onError={() => setImageError(true)}
              />
              {/* Absolute positioned topic tag at the top right of the image */}
              <div className="absolute top-2 right-2">
                <div className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-black/70 text-white backdrop-blur-sm">
                  <TopicIcon className="h-3 w-3 mr-1" />
                  {displayTopic.name}
                </div>
              </div>
            </div>
          )}
          
          {/* Content section */}
          <div className={`flex flex-col ${hasImage ? 'md:w-2/3' : 'w-full'}`}>
            <CardHeader className="pb-3">
              {/* Topic tag if not showing image (or showing in a prominent way if there's no image) */}
              {!hasImage && (
                <div className="mb-2">
                  <div className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-primary/10 text-primary">
                    <TopicIcon className="h-3 w-3 mr-1" />
                    {displayTopic.name}
                  </div>
                </div>
              )}
              
              <CardTitle className="line-clamp-2 text-lg hover:underline prose prose-gray max-w-none dark:prose-invert [&_em]:italic [&_em]:text-inherit [&_em]:font-medium [&_strong]:font-semibold [&_strong]:text-inherit [&_u]:underline [&_u]:underline-offset-2 [&_mark]:bg-yellow-200 [&_mark]:dark:bg-yellow-900/30 [&_mark]:px-1 [&_mark]:py-0.5 [&_mark]:rounded [&_code]:bg-muted [&_code]:text-foreground [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-sm [&_code]:font-mono">
                {typeof article.title === 'string' && article.title.includes('<') 
                  ? parse(article.title) 
                  : article.title
                }
              </CardTitle>
              <CardDescription className="flex items-center gap-2 text-sm flex-wrap">
                <PublicationBadge source={article.source} size="md" />
                <span>•</span>
                <span>{formatDate(article.publishedAt)}</span>
                {/* Always show reading time with 1 min minimum */}
                <>
                  <span>•</span>
                  <span>{Math.max(1, Math.round(article.readTime || 1))} min read</span>
                </>
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-sm text-muted-foreground line-clamp-3">{article.description}</p>
            </CardContent>
          </div>
        </div>
      </Card>
    </Link>
  );
}

// Export the interface for use in other components
export type { ArticlePreviewWithTopics, NewsCardProps }; 