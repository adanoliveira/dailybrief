import { apiClient } from './api-client'

// Types matching backend API response structure
export interface DigestArticle {
  id: string
  title: string
  url: string
  imageUrl?: string | null
  publication?: string | null
  publicationLogoUrl?: string | null
  published_at?: string | null
}

export interface DigestTopic {
  id: string
  title: string
  abstract: string
  score: number
  stories: DigestStory[]
}

export interface DigestStory {
  id: string
  title: string
  abstract: string
  key_facts: string[]
  perspectives: string[]
  articles: DigestArticle[]
  article_count: number
  event_score: number
  event?: {
    id: string
    title: string
  }
}

export interface DigestMetrics {
  topics_included: number
  events_included: number
  articles_processed: number
  reading_time_minutes: number
  generation_cost_usd: number
  generation_tokens_total: number
}

export interface Digest {
  id: string
  title: string
  headline?: string
  date: string
  introduction: string
  conclusion?: string
  topics: DigestTopic[]
  generation_status: 'GENERATING' | 'COMPLETED' | 'FAILED'
  created_at: string
  updated_at: string
  article_date_range?: {
    min_published_at: string
    max_published_at: string
  } | null
  metrics: DigestMetrics
}

export interface DigestSummary {
  id: string
  title: string
  headline?: string
  date: string
  introduction: string
  generation_status: 'GENERATING' | 'COMPLETED' | 'FAILED'
  created_at: string
  topics_included: number
  events_included: number
  articles_processed: number
  reading_time_minutes: number
  generation_cost_usd: number
}

export interface DigestListResponse {
  digests: DigestSummary[]
  pagination: {
    page: number
    page_size: number
    total_pages: number
    total_count: number
    has_next: boolean
    has_previous: boolean
  }
}

export interface GenerateDigestRequest {
  date?: string // YYYY-MM-DD format, optional
  force_regenerate?: boolean
}

export interface GenerateDigestResponse {
  digest_id?: string
  task_id?: string
  status: 'processing' | 'completed' | 'failed'
  message: string
}

export interface DigestStatusResponse {
  digest_id: string
  status: 'processing' | 'completed' | 'failed'
  created_at: string
  updated_at: string
  error_message?: string
  metrics?: DigestMetrics
}

export class DigestService {
  async getLatestDigest(): Promise<{ digest: Digest | null; message?: string }> {
    try {
      const response = await apiClient.get<any>('/digest/latest/')
      
      // Handle different response formats
      if (typeof response === 'string') {
        // Direct string response (non-standardized)
        return {
          digest: null,
          message: response
        }
      }
      
      if (response && typeof response === 'object') {
        // Check if it's already in the expected format
        if ('digest' in response) {
          return response as { digest: Digest | null; message?: string }
        }
        
        // If it's a direct digest object
        if ('id' in response && 'title' in response) {
          return {
            digest: response as Digest
          }
        }
        
        // If it's some other object format, treat as no digest with message
        return {
          digest: null,
          message: response.message || 'No digest available'
        }
      }
      
      // Fallback
      return {
        digest: null,
        message: 'No digest available'
      }
    } catch (error) {
      console.error('Failed to fetch latest digest:', error)
      throw error
    }
  }

  async getDigestByDate(date: string): Promise<{ digest: Digest | null; date: string; message?: string }> {
    try {
      const response = await apiClient.get<any>(`/digest/date/${date}/`)
      
      // Handle different response formats
      if (typeof response === 'string') {
        return {
          digest: null,
          date: date,
          message: response
        }
      }
      
      if (response && typeof response === 'object') {
        // Check if it's already in the expected format
        if ('digest' in response) {
          return response as { digest: Digest | null; date: string; message?: string }
        }
        
        // If it's a direct digest object
        if ('id' in response && 'title' in response) {
          return {
            digest: response as Digest,
            date: date
          }
        }
        
        // If it's some other object format
        return {
          digest: null,
          date: date,
          message: response.message || `No digest found for ${date}`
        }
      }
      
      // Fallback
      return {
        digest: null,
        date: date,
        message: `No digest found for ${date}`
      }
    } catch (error) {
      console.error(`Failed to fetch digest for ${date}:`, error)
      throw error
    }
  }

  async listDigests(page: number = 1, pageSize: number = 10): Promise<DigestListResponse> {
    try {
      const params = new URLSearchParams()
      params.append('page', page.toString())
      params.append('page_size', pageSize.toString())

      const response = await apiClient.get<DigestListResponse>(`/digest/list/?${params.toString()}`)
      return response
    } catch (error) {
      console.error('Failed to fetch digest list:', error)
      throw error
    }
  }

  async generateDigest(request: GenerateDigestRequest = {}): Promise<GenerateDigestResponse> {
    try {
      const response = await apiClient.post<GenerateDigestResponse>('/digest/generate/', request)
      return response
    } catch (error) {
      console.error('Failed to generate digest:', error)
      throw error
    }
  }

  async getDigestStatus(digestId: string): Promise<DigestStatusResponse> {
    try {
      const response = await apiClient.get<DigestStatusResponse>(`/digest/${digestId}/status/`)
      return response
    } catch (error) {
      console.error(`Failed to fetch digest status for ${digestId}:`, error)
      throw error
    }
  }

  async getDigestHtml(digestId: string): Promise<{ html_content: string; digest_id: string }> {
    try {
      const response = await apiClient.get<{ html_content: string; digest_id: string }>(`/digest/${digestId}/html/`)
      return response
    } catch (error) {
      console.error(`Failed to fetch digest HTML for ${digestId}:`, error)
      throw error
    }
  }

  async pollForDigestCompletion(
    digestId: string,
    maxAttempts: number = 30,
    intervalMs: number = 2000
  ): Promise<DigestStatusResponse> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const status = await this.getDigestStatus(digestId)
      
      if (status.status === 'completed' || status.status === 'failed') {
        return status
      }
      
      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, intervalMs))
    }
    
    throw new Error(`Digest generation timed out after ${maxAttempts} attempts`)
  }

  formatDate(date: Date): string {
    return date.toISOString().split('T')[0] // Returns YYYY-MM-DD
  }

  parseDigestDate(dateString: string): Date {
    return new Date(dateString)
  }

  formatDigestDate(dateString: string): string {
    const date = this.parseDigestDate(dateString)
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  getRelativeDigestDate(dateString: string): string {
    const digestDate = this.parseDigestDate(dateString)
    const today = new Date()
    const diffTime = today.getTime() - digestDate.getTime()
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    
    return this.formatDigestDate(dateString)
  }
}

export const digestService = new DigestService()
export default digestService 