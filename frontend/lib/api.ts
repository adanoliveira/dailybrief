import axios from 'axios';
import { getSession } from 'next-auth/react';

// Get the correct base URL based on environment
const getBaseUrl = () => {
  // Use NEXT_PUBLIC_API_URL if available, otherwise fallback based on environment
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Detect if running in browser or server for fallback
  const isBrowser = typeof window !== 'undefined';
  
  if (isBrowser) {
    // In browser - fallback to current hostname
    const hostname = window.location.hostname;
    return `http://${hostname}:8000`;
  } else {
    // In server - fallback to localhost
    return 'http://localhost:8000';
  }
};

// Create an axios instance with default config
export const api = axios.create({
  baseURL: (() => {
    const baseUrl = getBaseUrl();
    // Remove /api suffix if present to avoid double /api when used directly
    return baseUrl.endsWith('/api') ? baseUrl.slice(0, -4) : baseUrl;
  })(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  withCredentials: true // Include cookies in requests
});

// Log the API base URL in development mode
if (process.env.NODE_ENV === 'development') {
  console.log('API Base URL:', api.defaults.baseURL);
}

// Helper to get cookies (for CSRF token)
function getCookie(name: string): string | undefined {
  if (typeof document === 'undefined') return undefined;
  
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift();
  return undefined;
}

// Add request interceptor for auth and CSRF tokens
api.interceptors.request.use(async (config) => {
  // Add Django token from NextAuth session
  const session = await getSession();
  if (session?.user?.django_token) {
    config.headers.set('Authorization', `Bearer ${session.user.django_token}`);
  }
  
  // Add CSRF token for non-GET requests
  const csrfToken = getCookie('csrftoken');
  if (csrfToken && config.method !== 'get') {
    config.headers.set('X-CSRFToken', csrfToken);
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Add response interceptor for error logging (removed auto-unwrapping to avoid conflicts)
api.interceptors.response.use(
  (response) => {
    // Just log success responses, don't unwrap (fetchWithAuth handles unwrapping)
    if (response.data && typeof response.data === 'object' && 'success' in response.data) {
      if (response.data.success === true) {
        console.log(`Axios API success: ${response.data.message || 'Success'}`);
      } else {
        // This is an error response that came back as 200 OK
        const errorResponse = response.data as StandardApiErrorResponse;
        console.error('Axios API error response:', errorResponse);
        
        // Convert to proper error response
        const error = new Error(errorResponse.error || 'API request failed');
        const axiosError = {
          ...error,
          response: {
            ...response,
            status: response.status,
            statusText: response.statusText,
            data: errorResponse
          },
          config: response.config,
          isAxiosError: true
        };
        return Promise.reject(axiosError);
      }
    }
    
    // Always return response as-is (let individual functions handle unwrapping)
    return response;
  },
  (error) => {
    if (axios.isAxiosError(error)) {
      // Enhanced error logging for standardized format
      const errorData = error.response?.data;
      
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: errorData,
        message: error.message
      });
      
      // Handle standardized error responses
      if (errorData && typeof errorData === 'object' && 'success' in errorData && errorData.success === false) {
        console.error(`Standardized API Error - Code: ${errorData.error_code}, Message: ${errorData.error}`);
        if (errorData.details) {
          console.error('Error details:', errorData.details);
        }
      }
      
      // For debugging in development
      if (process.env.NODE_ENV === 'development') {
        console.log('Request headers:', error.config?.headers);
        console.log('Request data:', error.config?.data);
      }
    }
    
    return Promise.reject(error);
  }
);

// Handle API errors (enhanced for standardized format)
export function handleApiError(error: unknown) {
  if (axios.isAxiosError(error)) {
    const response = error.response;
    
    // Format error message from response
    if (response?.data) {
      // Handle standardized error response format
      if (typeof response.data === 'object' && response.data !== null && 'success' in response.data && response.data.success === false) {
        const errorData = response.data as StandardApiErrorResponse;
        return {
          message: errorData.error || 'An error occurred',
          statusCode: response.status || 500,
          error_code: errorData.error_code,
          details: errorData.details
        };
      }
      
      // Handle legacy error format
      const detail = typeof response.data === 'object' && response.data !== null
        ? response.data.detail || response.data.message || response.data.error || 'An error occurred'
        : 'An error occurred';
        
      return {
        message: detail,
        statusCode: response.status || 500
      };
    }
    
    // Network errors
    if (error.message === 'Network Error') {
      return {
        message: 'Unable to connect to the server. Please check your internet connection.',
        statusCode: 0
      };
    }
    
    return {
      message: error.message || 'An unknown error occurred',
      statusCode: response?.status || 500
    };
  }
  
  // Non-Axios errors
  return {
    message: error instanceof Error ? error.message : 'An unknown error occurred',
    statusCode: 500
  };
}

// Use the proper base URL from our getBaseUrl function
const API_BASE_URL = getBaseUrl();

// Interfaces for standardized API responses (matching backend format)
interface StandardApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
}

interface StandardApiErrorResponse {
  success: false
  error: string
  error_code?: string
  details?: Record<string, any>
}

/**
 * Unwrap standardized API response format
 */
function unwrapStandardizedResponse<T = any>(responseData: any): T {
  // Handle standardized success response - unwrap the data
  if (responseData && typeof responseData === 'object' && 'success' in responseData) {
    if (responseData.success === true) {
      console.log(`API success: ${responseData.message || 'Success'}`);
      return responseData.data;
    } else {
      // This is an error response that came back as 200 OK
      const errorResponse = responseData as StandardApiErrorResponse;
      console.error('API error response:', errorResponse);
      throw new Error(errorResponse.error || 'API request failed');
    }
  }
  
  // Fallback: return direct data (for backward compatibility)
  console.log('Non-standardized response detected, returning direct data');
  return responseData;
}

/**
 * Base fetch function with auth header and standardized response handling
 */
async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const session = await getSession();
  
  // Extract django_token from session if available
  const authToken = session?.user?.django_token || session?.accessToken;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}),
    ...options.headers,
  };
  
  // Clean endpoint construction
  let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // Remove /api prefix if present (we'll add it consistently)
  if (cleanEndpoint.startsWith('/api/')) {
    cleanEndpoint = cleanEndpoint.substring(4); // Remove '/api'
  }
  
  // Get base URL and apply hostname conversion for browser requests
  let baseUrl = getBaseUrl();
  
  // Apply hostname conversion at request time for browser requests
  if (typeof window !== 'undefined' && baseUrl.includes('backend:8000')) {
    baseUrl = baseUrl.replace('backend:8000', 'localhost:8000');
    console.log(`fetchWithAuth: Converted Docker hostname for browser request: ${baseUrl}`);
  }
  
  // Ensure base URL ends with /api
  let finalBaseUrl = baseUrl;
  if (!finalBaseUrl.endsWith('/api')) {
    finalBaseUrl += '/api';
  }
  
  // Construct final URL
  const fullUrl = `${finalBaseUrl}${cleanEndpoint}`;
  console.log(`fetchWithAuth: Requesting from: ${fullUrl}`);
    
  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error(`API error (${response.status}):`, error);
      
      // Handle standardized error response
      if (error.success === false) {
        throw new Error(error.error || error.message || `API error: ${response.status}`);
      }
      
      // Handle legacy error format
      throw new Error(error.detail || error.error || error.message || `API error: ${response.status}`);
    }
    
    const responseData = await response.json();
    return unwrapStandardizedResponse(responseData);
  } catch (err) {
    console.error(`Failed to fetch from ${fullUrl}:`, err);
    throw err;
  }
}

// Type augmentation for NextAuth session
declare module "next-auth" {
  interface Session {
    accessToken?: string;
  }
}

export interface ArticlePreview {
  id: string;
  title: string;
  visualTitle?: string; // Clean title without publication name
  description: string;
  source: {
    name: string;
    logoUrl?: string;
  };
  publishedAt: string;
  imageUrl?: string;
  url: string;
  isTopHeadline: boolean;
  readTime?: number;
}

export interface ArticleDetail extends ArticlePreview {
  content: string;
  author?: string;
  topics?: Array<{
    id: number;
    name: string;
    slug: string;
  }>;
  summary?: {
    headline?: string;
    abstract?: string;
    facts?: string[];
    opinions?: string[];
    impact?: string[];
    keyPoints?: string[];
  };
  richContent?: {
    blocks: ContentBlock[];
    mediaAssets: MediaAsset[];
    formattingData: FormattingData;
    hasRichContent: boolean;
    mediaCount: number;
    hasImages: boolean;
    hasVideos: boolean;
    hasAudio: boolean;
    formattingScore: number;
  };
  contentStatus?: string;
  contentQuality?: {
    completeness?: number;
    qualityScore?: number;
  };
}

export interface ContentBlock {
  type: 'heading' | 'paragraph' | 'subtitle' | 'pullquote' | 'image' | 'img' | 'figure' | 'video' | 'video_embed' | 'audio' | 'quote' | 'list' | 'code' | 'table' | 'embed' | 'twitter_embed';
  position: number;
  content?: string;
  text?: string;
  level?: number; // for headings
  id?: string;
  classes?: string[];
  // Media-specific fields
  src?: string;
  alt?: string;
  caption?: string;
  title?: string;
  // Enhanced metadata
  metadata?: {
    src?: string;
    alt?: string; 
    caption?: string;
    links?: Array<{ text: string; href: string }>;
    images?: Array<{ src: string; alt?: string; caption?: string }>;
    is_subtitle?: boolean;
    // Twitter embed specific metadata
    tweet_id?: string;
    embed_url?: string;
    embed_type?: string;
    // Video embed specific metadata
    video_id?: string;
    thumbnail?: string;
    // List specific metadata
    list_type?: 'ul' | 'ol';
    items?: string[];
    width?: number;
    height?: number;
    [key: string]: any;
  };
  // List-specific fields
  listType?: 'ul' | 'ol';
  items?: string[];
  // Quote-specific fields
  cite?: string;
  // Code-specific fields
  language?: string;
}

export interface MediaAsset {
  type: 'image' | 'video' | 'audio' | 'video_embed';
  src: string;
  alt?: string;
  caption?: string;
  title?: string;
  position: number;
  context?: string;
  platform?: string; // for video embeds
  metadata: {
    width?: number;
    height?: number;
    format?: string;
    size?: number;
    duration?: number;
    [key: string]: any;
  };
}

export interface FormattingData {
  headings?: Array<{
    level: number;
    text: string;
    id?: string;
    classes?: string[];
  }>;
  emphasis?: Array<{
    type: 'em' | 'i' | 'strong' | 'b';
    text: string;
    context?: string;
  }>;
  links?: Array<{
    text: string;
    href: string;
    title?: string;
    target?: string;
  }>;
  lists?: Array<{
    type: 'ul' | 'ol';
    items: string[];
    classes?: string[];
  }>;
  quotes?: Array<{
    text: string;
    cite?: string;
    classes?: string[];
  }>;
  codeBlocks?: Array<{
    type: 'pre' | 'code';
    content: string;
    language?: string;
    classes?: string[];
  }>;
}

export interface PaginatedResponse<T> {
  articles: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalPages: number;
    totalItems: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  // Enhanced fields for new article detection
  new_articles_count?: number;
  has_newer_content?: boolean;
  reference_time?: string;  // ISO timestamp used as reference
}

export interface ArticleQueryParams {
  page?: number;
  page_size?: number;
  sort?: 'relevance' | 'newest' | 'oldest';
  topic?: string;
  search?: string;
  // Enhanced parameters for efficient new article detection
  since?: string;  // ISO timestamp to get articles published after this time
  count_only?: boolean;  // Return just the count of new articles
  latest_article_id?: string;  // Alternative reference point to 'since'
}

/**
 * Get personalized feed articles based on user preferences
 */
export async function getPersonalizedFeed(params: ArticleQueryParams = {}): Promise<PaginatedResponse<ArticlePreview>> {
  // Build query string from params
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params.sort) queryParams.append('sort', params.sort);
  if (params.topic) queryParams.append('topic', params.topic);
  if (params.search) queryParams.append('search', params.search);
  // Enhanced parameters for new article detection
  if (params.since) queryParams.append('since', params.since);
  if (params.count_only) queryParams.append('count_only', params.count_only.toString());
  if (params.latest_article_id) queryParams.append('latest_article_id', params.latest_article_id);
  
  const queryString = queryParams.toString();
  const endpoint = `/articles/feed${queryString ? `?${queryString}` : ''}`;
  
  console.log(`Requesting personalized feed with params:`, params);
  try {
    const result = await fetchWithAuth(endpoint);
    console.log(`Received ${result.articles?.length || 0} articles`);
    return result;
  } catch (err) {
    console.error('Failed to get personalized feed:', err);
    throw err;
  }
}

/**
 * Get world feed articles (top headlines from user's preferred regions)
 */
export async function getWorldFeed(params: ArticleQueryParams = {}): Promise<PaginatedResponse<ArticlePreview>> {
  // Build query string from params
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params.topic) queryParams.append('topic', params.topic);
  if (params.search) queryParams.append('search', params.search);
  // Enhanced parameters for new article detection
  if (params.since) queryParams.append('since', params.since);
  if (params.count_only) queryParams.append('count_only', params.count_only.toString());
  if (params.latest_article_id) queryParams.append('latest_article_id', params.latest_article_id);
  
  const queryString = queryParams.toString();
  const endpoint = `/articles/world${queryString ? `?${queryString}` : ''}`;
  
  console.log(`Requesting world feed with params:`, params);
  try {
    const result = await fetchWithAuth(endpoint);
    console.log(`Received ${result?.articles?.length || 0} articles`);
    return result;
  } catch (err) {
    console.error('Failed to get world feed:', err);
    throw err;
  }
}

/**
 * Get public world feed articles (works for both authenticated and unauthenticated users)
 * For use on public marketing pages where authentication is optional
 */
export async function getPublicWorldFeed(params: ArticleQueryParams = {}): Promise<PaginatedResponse<ArticlePreview>> {
  // Build query string from params
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params.topic) queryParams.append('topic', params.topic);
  if (params.search) queryParams.append('search', params.search);
  
  const queryString = queryParams.toString();
  const endpoint = `/api/articles/public-world${queryString ? `?${queryString}` : ''}`;
  
  // Use regular fetch instead of fetchWithAuth to work for unauthenticated users
  const baseUrl = getBaseUrl();
  const fullUrl = `${baseUrl}${endpoint}`;
  
  console.log(`Requesting public world feed from: ${fullUrl}`);
  
  try {
    const response = await fetch(fullUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error(`Public world feed API error (${response.status}):`, error);
      
      // Handle standardized error response
      if (error.success === false) {
        throw new Error(error.error || error.message || `API error: ${response.status}`);
      }
      
      // Handle legacy error format
      throw new Error(error.detail || error.error || error.message || `API error: ${response.status}`);
    }
    
    const responseData = await response.json();
    const result = unwrapStandardizedResponse<PaginatedResponse<ArticlePreview>>(responseData);
    
    console.log(`Received ${result?.articles?.length || 0} public articles`);
    return result;
  } catch (err) {
    console.error('Failed to get public world feed:', err);
    throw err;
  }
}

/**
 * Get details for a specific article
 */
export async function getArticleDetail(id: string): Promise<ArticleDetail> {
  const endpoint = `/articles/${id}`;
  console.log(`Requesting article details for ID: ${id}`);
  
  try {
    const result = await fetchWithAuth(endpoint);
    return result;
  } catch (err) {
    console.error(`Failed to get article details for ID ${id}:`, err);
    throw err;
  }
}

/**
 * User preferences interface
 */
export interface UserPreferences {
  topics: number[];
  topics_details?: Array<{id: number, name: string, slug: string}>;
  regions: number[];
  languages: number[];
  publications: number[];
  has_completed_onboarding: boolean;
  user_id: number;
  public_id: string;
  email: string;
  name: string;
}

/**
 * Fetch user preferences
 */
export async function getUserPreferences(): Promise<UserPreferences> {
  console.log(`Requesting user preferences`);
  try {
    const result = await fetchWithAuth('/accounts/preferences');
    console.log(`Received user preferences:`, result);
    return result;
  } catch (err) {
    console.error('Failed to get user preferences:', err);
    throw err;
  }
}

/**
 * Fetch all available topics
 */
export interface Topic {
  id: number;
  name: string;
  slug: string;
}

export async function getAllTopics(): Promise<Topic[]> {
  console.log(`Requesting all topics`);
  try {
    const result = await fetchWithAuth('/feeds/topics');
    console.log(`Received ${result.length || 0} topics`);
    return result;
  } catch (err) {
    console.error('Failed to get topics:', err);
    throw err;
  }
}

// Add these interfaces at the top with other interfaces
export interface SummaryGenerationOptions {
  forceRegenerate?: boolean;
  async?: boolean;
}

export interface SummaryMetadata {
  generatedAt: string;
  costUsd: number;
  processingTimeMs: number;
  aiModel?: string;
  contentSource: string;
  wasRepaired?: boolean;
  stagesCompleted?: string[];
  requiredCritic?: boolean;
}

export interface ArticleSummary {
  headline: string;
  abstract: string;
  facts: string[];
  opinions: string[];
  impact: string[];
  keyPoints?: string[]; // Legacy compatibility
}

export interface SummaryGenerationResponse {
  success: boolean;
  message?: string;
  status?: 'processing' | 'completed' | 'failed';
  summary?: ArticleSummary;
  metadata?: SummaryMetadata;
  taskId?: string;
  estimatedTimeSeconds?: number;
  pollUrl?: string;
  error?: string;
  details?: string;
  failedStage?: string;
  canRetry?: boolean;
}

export interface SummaryStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'unknown';
  summarizationStatus: string;
  lastAttempt?: string;
  attempts: number;
  errorMessage?: string;
  summary?: ArticleSummary;
  metadata?: SummaryMetadata;
  estimatedRemainingSeconds?: number;
}

/**
 * Generate or regenerate a summary for an article
 */
export async function generateArticleSummary(
  articleId: string, 
  options: SummaryGenerationOptions = {}
): Promise<SummaryGenerationResponse> {
  const endpoint = `/articles/${articleId}/generate-summary`;
  console.log(`Generating summary for article ID: ${articleId}`);
  
  try {
    const result = await fetchWithAuth(endpoint, {
      method: 'POST',
      body: JSON.stringify(options),
    });
    return result;
  } catch (err) {
    console.error(`Failed to generate summary for article ${articleId}:`, err);
    throw err;
  }
}

/**
 * Check the status of summary generation for an article
 */
export async function getArticleSummaryStatus(articleId: string): Promise<SummaryStatusResponse> {
  const endpoint = `/articles/${articleId}/summary-status`;
  console.log(`Checking summary status for article ID: ${articleId}`);
  
  try {
    const result = await fetchWithAuth(endpoint);
    return result;
  } catch (err) {
    console.error(`Failed to get summary status for article ${articleId}:`, err);
    throw err;
  }
}

/**
 * Poll for summary completion with automatic retries
 */
export async function pollForSummaryCompletion(
  articleId: string,
  maxAttempts: number = 20,
  intervalMs: number = 2000
): Promise<SummaryStatusResponse> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const status = await getArticleSummaryStatus(articleId);
    
    if (status.status === 'completed' || status.status === 'failed') {
      return status;
    }
    
    // Wait before next poll
    if (attempt < maxAttempts - 1) {
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
  }
  
  throw new Error('Summary generation timed out');
} 