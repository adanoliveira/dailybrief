# Progressive Content Rendering Strategy

## Overview
Smart content presentation based on article processing quality, ensuring users always get value while driving traffic back to publishers when appropriate.

## Article Filtering Logic

### What Gets Listed
- `process_status = 'completed'`
- `quality_score >= 0.3`
- Successfully structured content blocks

### What Gets Hidden
- `process_status = 'pending'` (not processed yet)
- `process_status = 'failed'` (processing failed)
- `quality_score < 0.3` (virtually no usable content)

### Database Query Enhancement
```python
# Update article listing queries
articles = Article.objects.filter(
    process_status='completed',
    content_quality_metrics__quality_score__gte=0.3
).order_by('-published_at')
```

## The 3 Content Cases

### Case 1: Full Article Content (Quality ≥ 0.9)
**Behavior**: Show complete article with rich content rendering
**Indicators**: 
- ✅ "Complete article"
- Completeness: "~95% captured"
**CTAs**:
- Top: Subtle "View original for multimedia" 
- Bottom: "Read on [Publisher]" button
**Content**: Full rich content blocks, all available elements

### Case 2: Partial Article Content (0.5 ≤ Quality < 0.9)
**Behavior**: Show preview with clear truncation at natural break
**Indicators**:
- 📖 "Article preview"
- Completeness: "~60% captured"
**CTAs**:
- Top: "Continue reading for full analysis"
- Bottom: Prominent "Read full article on [Publisher]" 
**Content**: First N paragraphs + "Continue reading..." indicator

### Case 3: Minimal Content (0.3 ≤ Quality < 0.5)
**Behavior**: List in feed but redirect immediately on article click
**Indicators**: 
- 🔗 "Full article on [Publisher]"
- No preview available
**CTAs**: Immediate redirect with overlay
**Content**: No article page shown, direct external redirect

## Technical Implementation

### Backend Enhancements

#### 1. Quality Score Refinement
```python
# In algorithmic_processor.py
def _assess_content_completeness(self, content_blocks: List[ContentBlock], 
                               clean_content: str) -> Dict[str, Any]:
    """Enhanced quality assessment for progressive rendering."""
    
    # Core content indicators
    paragraph_count = len([b for b in content_blocks if b.type == 'paragraph'])
    heading_count = len([b for b in content_blocks if b.type == 'heading'])
    content_length = len(clean_content.strip())
    
    # Missing content indicators
    has_twitter_failures = any('twitter' in str(b.metadata) for b in content_blocks)
    has_video_placeholders = any('video' in b.type for b in content_blocks)
    
    # Calculate completeness score
    base_score = min(1.0, content_length / 2000)  # 2000 chars = good article
    structure_bonus = min(0.2, (paragraph_count * 0.05))  # Bonus for structure
    
    return {
        'quality_score': base_score + structure_bonus,
        'content_type': self._determine_content_case(base_score + structure_bonus),
        'paragraph_count': paragraph_count,
        'estimated_completeness': min(100, int((base_score + structure_bonus) * 100)),
        'missing_elements': self._identify_missing_elements(content_blocks)
    }

def _determine_content_case(self, quality_score: float) -> str:
    """Determine which rendering case applies."""
    if quality_score >= 0.9:
        return 'full'
    elif quality_score >= 0.5:
        return 'partial'
    elif quality_score >= 0.3:
        return 'minimal'
    else:
        return 'failed'  # Don't list
```

#### 2. API Response Enhancement
```python
# In article serialization
{
    "id": "uuid",
    "title": "Article Title",
    "contentCase": "full" | "partial" | "minimal",
    "qualityMetrics": {
        "score": 0.95,
        "completeness": 95,
        "missingElements": ["twitter_embeds", "videos"],
        "contentType": "full"
    },
    "richContent": {
        "blocks": [...],
        "truncatedAt": null | 15,  // Block index where truncation occurs
        "hasMore": false | true
    }
}
```

### Frontend Implementation

#### 1. Content Status Component
```tsx
// components/ContentStatusBanner.tsx
interface ContentStatusBannerProps {
  contentCase: 'full' | 'partial' | 'minimal'
  publisher: string
  qualityMetrics: {
    completeness: number
    missingElements: string[]
  }
  originalUrl: string
}

export function ContentStatusBanner({ contentCase, publisher, qualityMetrics, originalUrl }: ContentStatusBannerProps) {
  const statusConfig = {
    full: {
      icon: "✅",
      label: "Complete article",
      description: `~${qualityMetrics.completeness}% captured`,
      ctaText: "View original for multimedia",
      ctaStyle: "subtle"
    },
    partial: {
      icon: "📖", 
      label: "Article preview",
      description: `~${qualityMetrics.completeness}% captured`,
      ctaText: "Continue reading for full analysis",
      ctaStyle: "prominent"
    },
    minimal: {
      icon: "🔗",
      label: "Full article on " + publisher,
      description: "Opening external link...",
      ctaText: null,
      ctaStyle: "redirect"
    }
  }

  const config = statusConfig[contentCase]
  
  return (
    <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-lg">{config.icon}</span>
          <div>
            <p className="font-medium text-gray-900">{config.label}</p>
            <p className="text-sm text-gray-600">{config.description}</p>
          </div>
        </div>
        
        {config.ctaText && (
          <Link 
            href={originalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium transition-colors",
              config.ctaStyle === "subtle" 
                ? "text-gray-700 bg-gray-100 hover:bg-gray-200"
                : "text-white bg-blue-600 hover:bg-blue-700"
            )}
          >
            {config.ctaText}
          </Link>
        )}
      </div>
    </div>
  )
}
```

#### 2. Progressive Article Renderer
```tsx
// components/ProgressiveArticleRenderer.tsx
interface ProgressiveArticleRendererProps {
  article: ArticleDetail
}

export function ProgressiveArticleRenderer({ article }: ProgressiveArticleRendererProps) {
  const { contentCase, qualityMetrics, richContent } = article
  
  // Case 3: Minimal content - redirect immediately
  useEffect(() => {
    if (contentCase === 'minimal') {
      // Show brief loading overlay then redirect
      const timer = setTimeout(() => {
        window.open(article.url, '_blank', 'noopener,noreferrer')
      }, 1500)
      return () => clearTimeout(timer)
    }
  }, [contentCase, article.url])

  if (contentCase === 'minimal') {
    return <MinimalContentRedirect publisher={article.source.name} />
  }

  // Case 1 & 2: Show content with appropriate truncation
  const blocksToShow = contentCase === 'partial' && richContent?.truncatedAt 
    ? richContent.blocks.slice(0, richContent.truncatedAt)
    : richContent?.blocks || []

  return (
    <article className="max-w-4xl mx-auto px-4 py-8">
      <ContentStatusBanner 
        contentCase={contentCase}
        publisher={article.source.name}
        qualityMetrics={qualityMetrics}
        originalUrl={article.url}
      />
      
      <RichArticleRenderer 
        blocks={blocksToShow}
        mediaAssets={richContent?.mediaAssets || []}
        formattingData={richContent?.formattingData || {}}
      />
      
      {contentCase === 'partial' && richContent?.hasMore && (
        <TruncationIndicator 
          publisher={article.source.name}
          originalUrl={article.url}
        />
      )}
      
      <ArticleFooterCTA 
        contentCase={contentCase}
        publisher={article.source.name}
        originalUrl={article.url}
      />
    </article>
  )
}
```

#### 3. Article List Filtering
```tsx
// Update article listing to only show appropriate articles
const { data: articles } = useSWR('/api/articles', async (url) => {
  const response = await fetchWithAuth(url)
  // API already filters, but double-check on frontend
  return response.articles.filter(article => 
    article.processStatus === 'completed' && 
    article.qualityMetrics?.score >= 0.3
  )
})
```

## Copywriting Guidelines

### Status Indicators
- **Full**: "✅ Complete article • View original for multimedia"
- **Partial**: "📖 Article preview • Continue for full analysis" 
- **Minimal**: "🔗 Full article on [Publisher]"

### Call-to-Action Copy
- **Subtle CTAs**: "View original source", "See full version"
- **Prominent CTAs**: "Continue reading on [Publisher]", "Read full article"
- **Value props**: "for expert interviews", "for data and analysis", "for multimedia content"

## Mobile Considerations

### Redirect Behavior (Case 3)
- **Web**: New tab with `target="_blank"`
- **Mobile**: Native browser behavior, overlay feel when possible
- **PWA**: Smooth transition maintaining app context

### Touch-Friendly CTAs
- Minimum 44px touch targets
- Clear visual hierarchy
- Thumb-friendly positioning

## Analytics & Monitoring

### Key Metrics
- Content case distribution (how many full vs partial vs minimal)
- Click-through rates by case type
- User engagement by content completeness
- Publisher-specific quality patterns

### Quality Improvement Loop
- Track which publishers consistently produce minimal content
- A/B test truncation points for partial content
- Monitor user feedback on content completeness

## Implementation Priority

### Phase 1: Core Infrastructure
1. ✅ Backend quality scoring enhancement
2. ✅ API response enrichment with content case
3. ✅ Frontend ContentStatusBanner component

### Phase 2: Progressive Rendering
1. ✅ ProgressiveArticleRenderer implementation
2. ✅ Truncation logic for partial content
3. ✅ Minimal content redirect behavior

### Phase 3: Polish & Analytics
1. ✅ Copywriting refinement
2. ✅ Mobile optimization
3. ✅ Analytics implementation
4. ✅ A/B testing framework

## Success Criteria

- **User Experience**: Clear expectations set, no confusion about content completeness
- **Publisher Relations**: Appropriate traffic direction to original sources
- **Engagement**: Users spend appropriate time on each content type
- **Technical**: Reliable quality scoring and progressive rendering

## Future Enhancements

### Smart Truncation
- ML-based natural break detection
- Section-aware truncation (end at heading boundaries)
- Teaser generation for missing content

### Personalized Thresholds  
- User preference for content completeness
- Subscription-aware quality adjustments
- Source reliability scoring

### Dynamic Quality Assessment
- Real-time content completeness validation
- User feedback integration
- Continuous improvement based on engagement patterns 