import apiClient, { ApiError } from './api-client'

interface ApiErrorPayload {
  success?: boolean
  error?: string
  error_code?: string
  details?: Record<string, any>
  detail?: string
  message?: string
}

interface ApiErrorShape {
  message: string
  statusCode: number
  error_code?: string
  details?: Record<string, any>
}

type ApiRequestHeaders = Record<string, string>

interface ApiGetOptions {
  params?: Record<string, string | number | boolean | undefined>
  headers?: ApiRequestHeaders
  forceRefresh?: boolean
}

interface ApiWriteOptions {
  headers?: ApiRequestHeaders
}

interface ApiCompatibilityResponse<T> {
  data: T
  status: number
  statusText: string
  headers: Record<string, string>
  config: {
    url: string
    method: string
  }
}

const DEFAULT_STATUS = 200
const DEFAULT_STATUS_TEXT = 'OK'

function buildEndpoint(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`

  if (!params || Object.keys(params).length === 0) {
    return path
  }

  const queryParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return
    }

    queryParams.append(key, String(value))
  })

  const query = queryParams.toString()
  return query ? `${path}?${query}` : path
}

function toCompatResponse<T>(method: string, endpoint: string, data: T): ApiCompatibilityResponse<T> {
  return {
    data,
    status: DEFAULT_STATUS,
    statusText: DEFAULT_STATUS_TEXT,
    headers: {},
    config: {
      url: endpoint,
      method,
    },
  }
}

export const api = {
  async get<T>(endpoint: string, options: ApiGetOptions = {}): Promise<ApiCompatibilityResponse<T>> {
    const requestEndpoint = buildEndpoint(endpoint, options.params)
    const data = await apiClient.get<T>(requestEndpoint, {
      forceRefresh: options.forceRefresh,
      headers: options.headers,
    })

    return toCompatResponse('get', requestEndpoint, data)
  },

  async post<T>(endpoint: string, body?: unknown, options: ApiWriteOptions = {}): Promise<ApiCompatibilityResponse<T>> {
    const requestEndpoint = buildEndpoint(endpoint)
    const data = await apiClient.post<T>(requestEndpoint, body, {
      headers: options.headers,
    })

    return toCompatResponse('post', requestEndpoint, data)
  },

  async put<T>(endpoint: string, body?: unknown, options: ApiWriteOptions = {}): Promise<ApiCompatibilityResponse<T>> {
    const requestEndpoint = buildEndpoint(endpoint)
    const data = await apiClient.put<T>(requestEndpoint, body, {
      headers: options.headers,
    })

    return toCompatResponse('put', requestEndpoint, data)
  },

  async delete<T>(endpoint: string, options: ApiWriteOptions = {}): Promise<ApiCompatibilityResponse<T>> {
    const requestEndpoint = buildEndpoint(endpoint)
    const data = await apiClient.delete<T>(requestEndpoint, {
      headers: options.headers,
    })

    return toCompatResponse('delete', requestEndpoint, data)
  },
}

export function handleApiError(error: unknown): ApiErrorShape {
  if (error instanceof ApiError) {
    return {
      message: error.message,
      statusCode: error.status || 500,
      error_code: error.error_code,
      details: error.details,
    }
  }

  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { status?: number; data?: ApiErrorPayload } }).response
    const responseData = response?.data

    if (responseData) {
      if (responseData.success === false) {
        return {
          message: responseData.error || 'An error occurred',
          statusCode: response?.status || 500,
          error_code: responseData.error_code,
          details: responseData.details,
        }
      }

      return {
        message: responseData.detail || responseData.message || responseData.error || 'An error occurred',
        statusCode: response?.status || 500,
      }
    }
  }

  return {
    message: error instanceof Error ? error.message : 'An unknown error occurred',
    statusCode: 500,
  }
}

export interface ArticlePreview {
  id: string
  title: string
  visualTitle?: string
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

export interface ArticleDetail extends ArticlePreview {
  content: string
  author?: string
  topics?: Array<{
    id: number
    name: string
    slug: string
  }>
  summary?: {
    headline?: string
    abstract?: string
    facts?: string[]
    opinions?: string[]
    impact?: string[]
    keyPoints?: string[]
  }
  richContent?: {
    blocks: ContentBlock[]
    mediaAssets: MediaAsset[]
    formattingData: FormattingData
    hasRichContent: boolean
    mediaCount: number
    hasImages: boolean
    hasVideos: boolean
    hasAudio: boolean
    formattingScore: number
  }
  contentStatus?: string
  contentQuality?: {
    completeness?: number
    qualityScore?: number
  }
}

export interface ContentBlock {
  type: 'heading' | 'paragraph' | 'subtitle' | 'pullquote' | 'image' | 'img' | 'figure' | 'video' | 'video_embed' | 'audio' | 'quote' | 'list' | 'code' | 'table' | 'embed' | 'twitter_embed'
  position: number
  content?: string
  text?: string
  level?: number
  id?: string
  classes?: string[]
  src?: string
  alt?: string
  caption?: string
  title?: string
  metadata?: {
    src?: string
    alt?: string
    caption?: string
    links?: Array<{ text: string; href: string }>
    images?: Array<{ src: string; alt?: string; caption?: string }>
    is_subtitle?: boolean
    tweet_id?: string
    embed_url?: string
    embed_type?: string
    video_id?: string
    thumbnail?: string
    list_type?: 'ul' | 'ol'
    items?: string[]
    width?: number
    height?: number
    [key: string]: any
  }
  listType?: 'ul' | 'ol'
  items?: string[]
  cite?: string
  language?: string
}

export interface MediaAsset {
  type: 'image' | 'video' | 'audio' | 'video_embed'
  src: string
  alt?: string
  caption?: string
  title?: string
  position: number
  context?: string
  platform?: string
  metadata: {
    width?: number
    height?: number
    format?: string
    size?: number
    duration?: number
    [key: string]: any
  }
}

export interface FormattingData {
  headings?: Array<{
    level: number
    text: string
    id?: string
    classes?: string[]
  }>
  emphasis?: Array<{
    type: 'em' | 'i' | 'strong' | 'b'
    text: string
    context?: string
  }>
  links?: Array<{
    text: string
    href: string
    title?: string
    target?: string
  }>
  lists?: Array<{
    type: 'ul' | 'ol'
    items: string[]
    classes?: string[]
  }>
  quotes?: Array<{
    text: string
    cite?: string
    classes?: string[]
  }>
  codeBlocks?: Array<{
    type: 'pre' | 'code'
    content: string
    language?: string
    classes?: string[]
  }>
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
  new_articles_count?: number
  has_newer_content?: boolean
  reference_time?: string
}

export interface ArticleQueryParams {
  page?: number
  page_size?: number
  sort?: 'relevance' | 'newest' | 'oldest'
  topic?: string
  search?: string
  since?: string
  count_only?: boolean
  latest_article_id?: string
}

function buildArticleQuery(params: ArticleQueryParams): string {
  const queryParams = new URLSearchParams()

  if (params.page) queryParams.append('page', params.page.toString())
  if (params.page_size) queryParams.append('page_size', params.page_size.toString())
  if (params.sort) queryParams.append('sort', params.sort)
  if (params.topic) queryParams.append('topic', params.topic)
  if (params.search) queryParams.append('search', params.search)
  if (params.since) queryParams.append('since', params.since)
  if (params.count_only !== undefined) queryParams.append('count_only', String(params.count_only))
  if (params.latest_article_id) queryParams.append('latest_article_id', params.latest_article_id)

  const query = queryParams.toString()
  return query ? `?${query}` : ''
}

export async function getPersonalizedFeed(params: ArticleQueryParams = {}): Promise<PaginatedResponse<ArticlePreview>> {
  return apiClient.get<PaginatedResponse<ArticlePreview>>(`/articles/feed${buildArticleQuery(params)}`)
}

export async function getWorldFeed(params: ArticleQueryParams = {}): Promise<PaginatedResponse<ArticlePreview>> {
  return apiClient.get<PaginatedResponse<ArticlePreview>>(`/articles/world${buildArticleQuery(params)}`)
}

export async function getPublicWorldFeed(params: ArticleQueryParams = {}): Promise<PaginatedResponse<ArticlePreview>> {
  return apiClient.get<PaginatedResponse<ArticlePreview>>(`/articles/public-world${buildArticleQuery(params)}`)
}

export async function getArticleDetail(id: string): Promise<ArticleDetail> {
  return apiClient.get<ArticleDetail>(`/articles/${id}`)
}

export interface UserPreferences {
  topics: number[]
  topics_details?: Array<{ id: number; name: string; slug: string }>
  regions: number[]
  languages: number[]
  publications: number[]
  has_completed_onboarding: boolean
  user_id: number
  public_id: string
  email: string
  name: string
}

export async function getUserPreferences(): Promise<UserPreferences> {
  return apiClient.get<UserPreferences>('/accounts/preferences')
}

export interface Topic {
  id: number
  name: string
  slug: string
}

export async function getAllTopics(): Promise<Topic[]> {
  return apiClient.get<Topic[]>('/feeds/topics')
}

export interface SummaryGenerationOptions {
  forceRegenerate?: boolean
  async?: boolean
}

export interface SummaryMetadata {
  generatedAt: string
  costUsd: number
  processingTimeMs: number
  aiModel?: string
  contentSource: string
  wasRepaired?: boolean
  stagesCompleted?: string[]
  requiredCritic?: boolean
}

export interface ArticleSummary {
  headline: string
  abstract: string
  facts: string[]
  opinions: string[]
  impact: string[]
  keyPoints?: string[]
}

export interface SummaryGenerationResponse {
  success: boolean
  message?: string
  status?: 'processing' | 'completed' | 'failed'
  summary?: ArticleSummary
  metadata?: SummaryMetadata
  taskId?: string
  estimatedTimeSeconds?: number
  pollUrl?: string
  error?: string
  details?: string
  failedStage?: string
  canRetry?: boolean
}

export interface SummaryStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'unknown'
  summarizationStatus: string
  lastAttempt?: string
  attempts: number
  errorMessage?: string
  summary?: ArticleSummary
  metadata?: SummaryMetadata
  estimatedRemainingSeconds?: number
}

export async function generateArticleSummary(
  articleId: string,
  options: SummaryGenerationOptions = {}
): Promise<SummaryGenerationResponse> {
  return apiClient.post<SummaryGenerationResponse>(`/articles/${articleId}/generate-summary`, options)
}

export async function getArticleSummaryStatus(articleId: string): Promise<SummaryStatusResponse> {
  return apiClient.get<SummaryStatusResponse>(`/articles/${articleId}/summary-status`)
}

export async function pollForSummaryCompletion(
  articleId: string,
  maxAttempts: number = 20,
  intervalMs: number = 2000
): Promise<SummaryStatusResponse> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const status = await getArticleSummaryStatus(articleId)

    if (status.status === 'completed' || status.status === 'failed') {
      return status
    }

    if (attempt < maxAttempts - 1) {
      await new Promise((resolve) => setTimeout(resolve, intervalMs))
    }
  }

  throw new Error('Summary generation timed out')
}
