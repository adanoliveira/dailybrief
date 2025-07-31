# Frontend Implementation - Articles Feed

## Overview

The frontend implementation provides a responsive, mobile-first interface for consuming news articles through personalized feeds and world headlines. Built with Next.js 15, React, and TypeScript, it features infinite scrolling, real-time search, and seamless navigation.

## File Structure

```
frontend/
├── app/(authenticated)/
│   ├── home/page.tsx           # Personalized feed page
│   ├── world/page.tsx          # World headlines page
│   ├── article/[id]/page.tsx   # Article detail page
│   └── layout.tsx              # Authenticated layout with navigation
├── components/
│   ├── infinite-news-feed.tsx  # Main feed component
│   ├── news-card.tsx          # Individual article card
│   ├── mobile-nav.tsx         # Mobile navigation
│   └── ui/                    # shadcn/ui components
├── lib/
│   ├── api.ts                 # API integration functions
│   └── user-context.tsx      # User state management
└── types/
    └── api.ts                 # TypeScript interfaces
```

## Core Components

### 1. InfiniteNewsFeed Component (`frontend/components/infinite-news-feed.tsx`)

**Purpose**: Main feed component that handles article loading, pagination, and filtering

**Key Features**:
- Infinite scrolling with Intersection Observer
- Debounced search functionality
- Loading states and error handling
- Support for both personalized and world feeds

**Props Interface**:
```typescript
interface InfiniteNewsFeedProps {
  feedType?: 'personalized' | 'world';
  topicSlug?: string;
  searchQuery?: string;
  sortOrder?: 'relevance' | 'newest' | 'oldest';
}
```

**State Management**:
```typescript
const [articles, setArticles] = useState<ArticlePreviewWithTopics[]>([])
const [page, setPage] = useState(1)
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)
const [hasMore, setHasMore] = useState(true)
const [reachedEnd, setReachedEnd] = useState(false)
```

**Infinite Scroll Implementation**:
```typescript
const lastArticleRef = useCallback(
  (node: HTMLDivElement | null) => {
    if (loading) return

    if (observer.current) observer.current.disconnect()

    observer.current = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasMore) {
        setPage(prevPage => prevPage + 1)
      }
    })

    if (node) observer.current.observe(node)
  },
  [loading, hasMore],
)
```

**API Integration**:
```typescript
const loadArticles = useCallback(async (pageNum: number, reset: boolean = false) => {
  setLoading(true)
  setError(null)
  
  try {
    const params: ArticleQueryParams = {
      page: pageNum,
      page_size: 10,
    }

    // Add parameters based on props
    if (feedType === 'personalized') {
      params.sort = sortOrder
    }
    
    if (topicSlug && topicSlug !== 'for-you' && topicSlug !== 'all') {
      params.topic = topicSlug
    }
    
    if (searchQuery) {
      params.search = searchQuery
    }
    
    // Choose appropriate API endpoint
    const data = feedType === 'world' 
      ? await getWorldFeed(params)
      : await getPersonalizedFeed(params)
    
    // Update state
    if (reset) {
      setArticles(data.articles)
    } else {
      setArticles(prev => [...prev, ...data.articles])
    }
    
    setHasMore(data.pagination.hasNext)
    setReachedEnd(!data.pagination.hasNext)
    
  } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to load articles")
  } finally {
    setLoading(false)
  }
}, [feedType, topicSlug, searchQuery, sortOrder])
```

### 2. NewsCard Component (`frontend/components/news-card.tsx`)

**Purpose**: Individual article card with responsive design and rich metadata

**Features**:
- Responsive image handling with fallbacks
- Topic badges with icons
- Read time estimation
- Publication branding
- Accessibility optimizations

**Component Structure**:
```typescript
interface NewsCardProps {
  article: ArticlePreviewWithTopics
  onRead?: (articleId: string) => void
}

export function NewsCard({ article, onRead }: NewsCardProps) {
  return (
    <Card className="overflow-hidden hover:shadow-md transition-shadow">
      <div className="aspect-video relative overflow-hidden">
        {article.imageUrl && (
          <Image
            src={article.imageUrl}
            alt={article.title}
            fill
            className="object-cover"
            onError={() => setImageError(true)}
          />
        )}
      </div>
      
      <CardHeader>
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
          <span>{article.source.name}</span>
          <span>•</span>
          <time>{formatDate(article.publishedAt)}</time>
          {article.readTime && (
            <>
              <span>•</span>
              <span>{article.readTime} min read</span>
            </>
          )}
        </div>
        
        <CardTitle className="line-clamp-2">{article.title}</CardTitle>
        
        {article.description && (
          <p className="text-muted-foreground line-clamp-3">
            {article.description}
          </p>
        )}
      </CardHeader>
      
      <CardFooter>
        <div className="flex items-center justify-between w-full">
          <div className="flex flex-wrap gap-1">
            {article.topics.map(topic => (
              <TopicBadge key={topic.id} topic={topic} />
            ))}
          </div>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => onRead?.(article.id)}
          >
            Read
          </Button>
        </div>
      </CardFooter>
    </Card>
  )
}
```

### 3. Page Components

#### Home Page (`frontend/app/(authenticated)/home/page.tsx`)

**Purpose**: Personalized news feed with user's topic preferences

**Key Features**:
- Onboarding verification
- Dynamic topic tabs based on user preferences
- Search and sorting controls
- Daily digest integration

**State Management**:
```typescript
const [selectedTopic, setSelectedTopic] = useState('for-you')
const [searchQuery, setSearchQuery] = useState('')
const [debouncedSearch, setDebouncedSearch] = useState('')
const [sortOrder, setSortOrder] = useState<'relevance' | 'newest' | 'oldest'>('relevance')
```

**Search Debouncing**:
```typescript
useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedSearch(searchQuery)
  }, 500) // 500ms debounce
  
  return () => clearTimeout(timer)
}, [searchQuery])
```

**Topic Tabs**:
```typescript
<Tabs value={selectedTopic} onValueChange={setSelectedTopic}>
  <TabsList className="mb-4 overflow-auto py-1 w-full justify-start">
    <TabsTrigger value="for-you">For You</TabsTrigger>
    {userStatus?.topics_details?.map(topic => (
      <TabsTrigger key={topic.id} value={topic.slug}>
        {topic.name}
      </TabsTrigger>
    ))}
  </TabsList>
  <TabsContent value={selectedTopic}>
    <InfiniteNewsFeed 
      topicSlug={selectedTopic} 
      searchQuery={debouncedSearch}
      sortOrder={sortOrder}
    />
  </TabsContent>
</Tabs>
```

#### World Page (`frontend/app/(authenticated)/world/page.tsx`)

**Purpose**: Global headlines from user's preferred regions

**Key Features**:
- Region-based filtering
- All topic categories available
- Search functionality
- Chronological sorting

**Topic Filtering**:
```typescript
<Tabs value={selectedTopic} onValueChange={setSelectedTopic}>
  <TabsList className="mb-4 overflow-auto py-1 w-full justify-start">
    <TabsTrigger value="all">All</TabsTrigger>
    <TabsTrigger value="business">Business</TabsTrigger>
    <TabsTrigger value="technology">Technology</TabsTrigger>
    <TabsTrigger value="science">Science</TabsTrigger>
    <TabsTrigger value="health">Health</TabsTrigger>
    <TabsTrigger value="entertainment">Entertainment</TabsTrigger>
    <TabsTrigger value="sports">Sports</TabsTrigger>
  </TabsList>
  <TabsContent value={selectedTopic}>
    <InfiniteNewsFeed 
      feedType="world"
      topicSlug={selectedTopic}
      searchQuery={debouncedSearch}
    />
  </TabsContent>
</Tabs>
```

#### Article Detail Page (`frontend/app/(authenticated)/article/[id]/page.tsx`)

**Purpose**: Full article view with AI summaries

**Features**:
- Dynamic route with UUID parameter
- AI summary display
- Full content rendering
- Related metadata
- Loading and error states

**Data Fetching**:
```typescript
useEffect(() => {
  const fetchArticle = async () => {
    try {
      setLoading(true)
      setError(null)
      const articleData = await getArticleDetail(id)
      setArticle(articleData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load article')
    } finally {
      setLoading(false)
    }
  }

  if (id) {
    fetchArticle()
  }
}, [id])
```

## API Integration

### API Functions (`frontend/lib/api.ts`)

**Purpose**: Centralized API communication with type safety

**Authentication Helper**:
```typescript
async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const session = await getSession()
  
  if (!session?.accessToken) {
    throw new Error('No authentication token available')
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.accessToken}`,
    ...options.headers,
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.error || `HTTP ${response.status}`)
  }

  return response
}
```

**Feed API Functions**:
```typescript
export async function getPersonalizedFeed(params: ArticleQueryParams = {}): Promise<PaginatedResponse<ArticlePreview>> {
  const searchParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, value.toString())
    }
  })

  const response = await fetchWithAuth(
    `${API_BASE_URL}/articles/personalized-feed/?${searchParams}`
  )
  
  return response.json()
}

export async function getWorldFeed(params: ArticleQueryParams = {}): Promise<PaginatedResponse<ArticlePreview>> {
  const searchParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, value.toString())
    }
  })

  const response = await fetchWithAuth(
    `${API_BASE_URL}/articles/world-feed/?${searchParams}`
  )
  
  return response.json()
}

export async function getArticleDetail(id: string): Promise<ArticleDetail> {
  const response = await fetchWithAuth(`${API_BASE_URL}/articles/${id}/`)
  return response.json()
}
```

### TypeScript Interfaces

**Article Types**:
```typescript
export interface ArticlePreview {
  id: string
  title: string
  description: string
  source: {
    name: string
    logoUrl?: string
  }
  publishedAt: string
  imageUrl?: string
  url: string
  isTopHeadline: boolean
  readTime?: number
}

export interface ArticlePreviewWithTopics extends ArticlePreview {
  topics: Array<{
    id: number
    name: string
    slug: string
  }>
}

export interface ArticleDetail extends ArticlePreviewWithTopics {
  content: string
  author?: string
  summary?: {
    abstract?: string
    keyPoints?: string[]
  }
}

export interface PaginatedResponse<T> {
  articles: T[]
  pagination: {
    page: number
    pageSize: number
    totalPages: number
    totalItems: number
    hasNext: boolean
    hasPrevious: boolean
  }
}

export interface ArticleQueryParams {
  page?: number
  page_size?: number
  sort?: 'relevance' | 'newest' | 'oldest'
  topic?: string
  search?: string
}
```

## Navigation System

### Mobile Navigation (`frontend/components/mobile-nav.tsx`)

**Purpose**: Bottom navigation for mobile devices

**Features**:
- Active state indication
- Icon-based navigation
- Internationalization support

```typescript
export function MobileNav() {
  const pathname = usePathname()

  return (
    <div className="fixed bottom-0 left-0 z-50 w-full h-16 bg-background border-t md:hidden">
      <div className="grid h-full grid-cols-3">
        <NavItem 
          href="/home" 
          icon={<Home className="h-5 w-5" />} 
          label="Home" 
          isActive={pathname === "/home"} 
        />
        <NavItem 
          href="/world" 
          icon={<Globe className="h-5 w-5" />} 
          label="Headlines" 
          isActive={pathname === "/world"} 
        />
        <NavItem
          href="/profile"
          icon={<User className="h-5 w-5" />}
          label="Profile"
          isActive={pathname === "/profile"}
        />
      </div>
    </div>
  )
}
```

### Desktop Navigation (`frontend/app/(authenticated)/layout.tsx`)

**Purpose**: Header navigation for desktop devices

**Features**:
- Consistent styling with mobile nav
- Active state highlighting
- Icon and text labels

```typescript
function DesktopNavItem({ href, icon, label, isActive }: DesktopNavItemProps) {
  const { t } = useLanguage()
  
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
        isActive 
          ? "text-primary bg-primary/10" 
          : "text-muted-foreground hover:text-foreground hover:bg-accent"
      )}
    >
      {icon}
      {t(label.toLowerCase())}
    </Link>
  )
}
```

## State Management

### User Context (`frontend/lib/user-context.tsx`)

**Purpose**: Global user state and preferences management

```typescript
interface UserContextType {
  userStatus: UserStatus | null
  isLoading: boolean
  error: string | null
  refreshUserStatus: () => Promise<void>
}

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [userStatus, setUserStatus] = useState<UserStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refreshUserStatus = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const status = await getUserStatus()
      setUserStatus(status)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load user status')
    } finally {
      setIsLoading(false)
    }
  }, [])

  return (
    <UserContext.Provider value={{ userStatus, isLoading, error, refreshUserStatus }}>
      {children}
    </UserContext.Provider>
  )
}
```

## Error Handling

### Error States

**Loading States**:
```typescript
const renderSkeletons = () => (
  <div className="space-y-4">
    {[1, 2, 3].map((i) => (
      <Card key={i}>
        <CardHeader>
          <Skeleton className="h-6 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/3" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
      </Card>
    ))}
  </div>
)
```

**Error States**:
```typescript
const renderErrorState = () => (
  <Card className="bg-destructive/5 border-destructive/20 text-center">
    <CardContent className="pt-6 pb-4">
      <div className="flex justify-center mb-4">
        <div className="bg-destructive/10 p-3 rounded-full">
          <AlertTriangle className="h-6 w-6 text-destructive" />
        </div>
      </div>
      <h3 className="text-lg font-medium mb-2">
        Failed to load articles
      </h3>
      <p className="text-muted-foreground mb-4">
        {error || "Something went wrong. Please try again."}
      </p>
      <Button onClick={handleRetry} variant="outline">
        Try again
      </Button>
    </CardContent>
  </Card>
)
```

**Empty States**:
```typescript
const renderEmptyState = () => (
  <Card className="bg-primary/5 border-primary/20 text-center">
    <CardContent className="pt-6 pb-4">
      <div className="flex justify-center mb-4">
        <div className="bg-primary/10 p-3 rounded-full">
          <Newspaper className="h-6 w-6 text-primary" />
        </div>
      </div>
      <h3 className="text-lg font-medium mb-2">No articles found</h3>
      <p className="text-muted-foreground">
        {searchQuery 
          ? "No articles match your search criteria. Try a different search term."
          : "We couldn't find any articles for your preferences. Update your interests or check back later."}
      </p>
    </CardContent>
  </Card>
)
```

## Performance Optimizations

### Debounced Search
```typescript
useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedSearch(searchQuery)
  }, 500) // 500ms debounce
  
  return () => clearTimeout(timer)
}, [searchQuery])
```

### Memoized Callbacks
```typescript
const loadArticles = useCallback(async (pageNum: number, reset: boolean = false) => {
  // ... implementation
}, [feedType, topicSlug, searchQuery, sortOrder])

const lastArticleRef = useCallback((node: HTMLDivElement | null) => {
  // ... implementation
}, [loading, hasMore])
```

### Image Optimization
```typescript
<Image
  src={article.imageUrl}
  alt={article.title}
  fill
  className="object-cover"
  loading="lazy"
  onError={() => setImageError(true)}
/>
```

## Responsive Design

### Mobile-First Approach
```css
/* Base styles for mobile */
.container {
  padding: 1rem;
}

/* Desktop overrides */
@media (min-width: 768px) {
  .container {
    padding: 2rem;
  }
}
```

### Adaptive Layouts
```typescript
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  {articles.map(article => (
    <NewsCard key={article.id} article={article} />
  ))}
</div>
```

## Internationalization

### Language Support
```typescript
const { t } = useLanguage()

// Usage in components
<span>{t('home')}</span>
<span>{t('headlines')}</span>
<span>{t('profile')}</span>
```

### Translation Keys
```typescript
const translations = {
  en: {
    home: "Home",
    headlines: "Headlines", 
    profile: "Profile",
    // ... more translations
  },
  es: {
    home: "Inicio",
    headlines: "Titulares",
    profile: "Perfil",
    // ... more translations
  }
}
```

## Testing Strategy

### Component Testing
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { NewsCard } from '../news-card'

describe('NewsCard', () => {
  const mockArticle = {
    id: '1',
    title: 'Test Article',
    description: 'Test description',
    // ... other properties
  }

  it('renders article title', () => {
    render(<NewsCard article={mockArticle} />)
    expect(screen.getByText('Test Article')).toBeInTheDocument()
  })

  it('calls onRead when read button is clicked', () => {
    const onRead = jest.fn()
    render(<NewsCard article={mockArticle} onRead={onRead} />)
    
    fireEvent.click(screen.getByText('Read'))
    expect(onRead).toHaveBeenCalledWith('1')
  })
})
```

### API Testing
```typescript
import { getPersonalizedFeed } from '../api'

// Mock fetch
global.fetch = jest.fn()

describe('API functions', () => {
  beforeEach(() => {
    fetch.mockClear()
  })

  it('fetches personalized feed with correct parameters', async () => {
    const mockResponse = {
      articles: [],
      pagination: { page: 1, hasNext: false }
    }
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })

    const result = await getPersonalizedFeed({ page: 1, search: 'test' })
    
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('page=1&search=test'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': expect.stringContaining('Bearer')
        })
      })
    )
    
    expect(result).toEqual(mockResponse)
  })
})
```

## Future Enhancements

### Performance
- React Query integration for caching
- Virtual scrolling for large lists
- Image lazy loading optimization
- Service Worker for offline support

### Features
- Pull-to-refresh functionality
- Article bookmarking
- Social sharing
- Reading progress tracking
- Dark mode support

### Accessibility
- Screen reader optimization
- Keyboard navigation
- High contrast mode
- Focus management 