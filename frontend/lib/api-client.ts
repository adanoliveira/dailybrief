import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'
import { getSession } from 'next-auth/react'
import type { Session } from 'next-auth'

// NEW: Standardized API response interfaces
export interface StandardApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
}

export interface StandardApiErrorResponse {
  success: false
  error: string
  error_code?: string
  details?: Record<string, any>
}

// Define common API error class (enhanced)
export class ApiError extends Error {
  status: number
  error_code?: string
  details?: Record<string, any>

  constructor(message: string, status: number, error_code?: string, details?: Record<string, any>) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.error_code = error_code
    this.details = details
  }
}

// Type for API client options
type ApiClientOptions = {
  forceRefresh?: boolean;
  headers?: Record<string, string>;
};

// In-memory cache for API responses
// NOTE: This replaces the previously separate api-cache module so transport
// and cache invalidation behavior stay co-located in the canonical client.
const cache: Record<string, { data: any; timestamp: number }> = {};
const CACHE_TTL = 60 * 1000; // 60 seconds
const pendingRequests: Record<string, Promise<any> | null> = {};

/**
 * Enhanced API client with caching, authentication, and standardized response handling
 */
class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    // Ensure baseUrl doesn't end with a slash
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl
    console.log(`API Client initialized with base URL: ${this.baseUrl}`)
  }

  /**
   * Construct the full URL for the API endpoint
   */
  private getUrl(endpoint: string): string {
    // Apply hostname conversion at request time for browser requests
    let currentBaseUrl = this.baseUrl;
    
    if (typeof window !== 'undefined') {
      // We're in the browser - check if we need to convert Docker hostname
      if (currentBaseUrl.includes('backend:8000')) {
        currentBaseUrl = currentBaseUrl.replace('backend:8000', 'localhost:8000');
        console.log(`API Client: Converted Docker hostname for browser request: ${currentBaseUrl}`);
      }
    }
    
    // Clean the endpoint - ensure it starts with /
    let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
    
    // If endpoint already has /api/ prefix, remove it since we'll add it properly
    if (cleanEndpoint.startsWith('/api/')) {
      cleanEndpoint = cleanEndpoint.substring(4) // Remove '/api'
    }
    
    // Ensure baseUrl ends with /api (no trailing slash)
    let finalBaseUrl = currentBaseUrl
    if (!finalBaseUrl.endsWith('/api')) {
      finalBaseUrl += '/api'
    }
    
    // Combine base URL with clean endpoint
    const fullUrl = `${finalBaseUrl}${cleanEndpoint}`
    
    // Clean up any double slashes except after protocol
    return fullUrl.replace(/([^:]\/)\/+/g, '$1')
  }

  /**
   * Get authentication headers for authenticated requests
   */
  private async getAuthHeaders(): Promise<Record<string, string>> {
    const session = await getSession()
    
    if (!session?.user?.django_token) {
      console.warn('No authentication token available')
      return {}
    }
    
    // Ensure the token is properly formatted
    const token = session.user.django_token.trim()
    
    // Log token format for debugging (without exposing the actual token)
    console.log(`Token format check: length=${token.length}, has dots=${token.includes('.')}, segments=${token.split('.').length}`)
    
    if (!token || token === "offline_mode_token" || !token.includes('.') || token.split('.').length !== 3) {
      console.warn('Invalid token format detected')
      return {}
    }
    
    return {
      Authorization: `Bearer ${token}`
    }
  }

  /**
   * NEW: Process standardized API response and extract data
   */
  private processApiResponse<T>(response: AxiosResponse<StandardApiResponse<T> | StandardApiErrorResponse>): T {
    const responseData = response.data

    // Handle standardized success response with 'data' field
    if ('success' in responseData && responseData.success === true && 'data' in responseData) {
      console.log(`API client: Success response - ${responseData.message || 'Success'}`)
      return (responseData as StandardApiResponse<T>).data as T
    }

    // Handle standardized error response
    if ('success' in responseData && responseData.success === false) {
      const errorResponse = responseData as StandardApiErrorResponse
      console.error('API client: Error response received:', errorResponse)
      
      throw new ApiError(
        errorResponse.error || 'API request failed',
        response.status,
        errorResponse.error_code,
        errorResponse.details
      )
    }

    // Handle success response without 'data' wrapper (digest endpoints and others)
    if ('success' in responseData && responseData.success === true) {
      console.log(`API client: Success response - ${responseData.message || 'Success'}`)
      return responseData as T
    }

    // Fallback: assume direct data (for backward compatibility)
    console.log('API client: Non-standardized response detected, returning direct data')
    return responseData as T
  }

  /**
   * Clear all cache
   */
  clearCache(): void {
    console.log('API client: Clearing entire cache');
    Object.keys(cache).forEach(key => delete cache[key]);
  }

  /**
   * Clear specific endpoint cache
   */
  clearEndpointCache(endpoint: string): void {
    console.log(`API client: Clearing cache for endpoint: ${endpoint}`);
    const keysToDelete = Object.keys(cache).filter(key => key.includes(endpoint));
    keysToDelete.forEach(key => delete cache[key]);
  }

  /**
   * Clear user status cache specifically
   */
  clearUserStatusCache(): void {
    console.log('API client: Clearing user status cache');
    this.clearEndpointCache('/api/accounts/sync/');
  }

  /**
   * GET request (updated to handle standardized responses)
   */
  async get<T>(endpoint: string, options: ApiClientOptions = {}): Promise<T> {
    const { forceRefresh = false, headers = {} } = options;
    const fullUrl = this.getUrl(endpoint);
    const cacheKey = fullUrl;
    
    // Check if we have a valid cache entry and not forcing refresh
    if (!forceRefresh && cache[cacheKey] && (Date.now() - cache[cacheKey].timestamp < CACHE_TTL)) {
      console.log(`API client: Using cached response for ${endpoint}`);
      return cache[cacheKey].data as T;
    }
    
    // Check if there's already a pending request for this URL
    const existingRequest = pendingRequests[cacheKey];
    if (existingRequest) {
      console.log(`API client: Reusing pending request for ${endpoint}`);
      return existingRequest as Promise<T>;
    }
    
    console.log(`API client: Sending GET request to ${fullUrl}`);
    
    // Create the promise and store it
    const requestPromise = (async () => {
      try {
        // Get auth headers if available
        const authHeaders = await this.getAuthHeaders();
        
        const axiosConfig: AxiosRequestConfig = {
          method: 'GET',
          url: fullUrl,
          headers: {
            'Content-Type': 'application/json',
            ...authHeaders,
            ...headers,
          },
          withCredentials: true,
        };

        const response = await axios<StandardApiResponse<T> | StandardApiErrorResponse>(axiosConfig);

        if (response.status !== 200) {
          throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        // Process standardized response and extract data
        const extractedData = this.processApiResponse<T>(response);

        // Cache the extracted data (not the wrapped response)
        cache[cacheKey] = {
          data: extractedData,
          timestamp: Date.now(),
        };
        
        console.log(`API client: Successful response from ${endpoint}`);
        return extractedData;
      } finally {
        // Clean up the pending request after some time to prevent race conditions
        setTimeout(() => {
          pendingRequests[cacheKey] = null;
        }, 100);
      }
    })();
    
    // Store the promise so other calls can reuse it
    pendingRequests[cacheKey] = requestPromise;
    
    try {
      return await requestPromise;
    } catch (error) {
      console.error(`API client: Error fetching ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * POST request (updated to handle standardized responses)
   */
  async post<T>(endpoint: string, data: any, options: ApiClientOptions = {}): Promise<T> {
    const { headers = {} } = options;
    const fullUrl = this.getUrl(endpoint);
    
    try {
      console.log(`API client: Sending POST request to ${fullUrl}`);
      
      // Get auth headers if available
      const authHeaders = await this.getAuthHeaders();
      
      const axiosConfig: AxiosRequestConfig = {
        method: 'POST',
        url: fullUrl,
        data,
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
          ...headers,
        },
        withCredentials: true,
      };
      
      const response = await axios<StandardApiResponse<T> | StandardApiErrorResponse>(axiosConfig);

      if (response.status < 200 || response.status >= 300) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      // Process standardized response and extract data
      const extractedData = this.processApiResponse<T>(response);

      // Clear cache for any endpoints that might be affected by this POST
      if (endpoint.includes('accounts/')) {
        this.clearEndpointCache('/api/accounts/sync/');
      }
      
      console.log(`API client: Successful response from POST ${endpoint}`);
      return extractedData;
    } catch (error) {
      console.error(`API client: Error posting to ${endpoint}:`, error);
      this.handleApiError(error as AxiosError, endpoint);
      throw error;
    }
  }

  /**
   * PUT request (updated to handle standardized responses)
   */
  async put<T>(endpoint: string, data: any, options: ApiClientOptions = {}): Promise<T> {
    const { headers = {} } = options;
    const fullUrl = this.getUrl(endpoint);
    
    try {
      console.log(`API client: Sending PUT request to ${fullUrl}`);
      
      // Get auth headers if available
      const authHeaders = await this.getAuthHeaders();
      
      const axiosConfig: AxiosRequestConfig = {
        method: 'PUT',
        url: fullUrl,
        data,
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
          ...headers,
        },
        withCredentials: true,
      };
      
      const response = await axios<StandardApiResponse<T> | StandardApiErrorResponse>(axiosConfig);

      if (response.status < 200 || response.status >= 300) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      // Process standardized response and extract data
      const extractedData = this.processApiResponse<T>(response);

      // Clear any related cache
      if (endpoint.includes('accounts/')) {
        this.clearEndpointCache('/api/accounts/sync/');
      }
      
      console.log(`API client: Successful response from PUT ${endpoint}`);
      return extractedData;
    } catch (error) {
      console.error(`API client: Error putting to ${endpoint}:`, error);
      this.handleApiError(error as AxiosError, endpoint);
      throw error;
    }
  }

  /**
   * DELETE request (updated to handle standardized responses)
   */
  async delete<T>(endpoint: string, options: ApiClientOptions = {}): Promise<T> {
    const { headers = {} } = options;
    const fullUrl = this.getUrl(endpoint);
    
    try {
      console.log(`API client: Sending DELETE request to ${fullUrl}`);
      
      // Get auth headers if available
      const authHeaders = await this.getAuthHeaders();
      
      const axiosConfig: AxiosRequestConfig = {
        method: 'DELETE',
        url: fullUrl,
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
          ...headers,
        },
        withCredentials: true,
      };
      
      const response = await axios<StandardApiResponse<T> | StandardApiErrorResponse>(axiosConfig);

      if (response.status < 200 || response.status >= 300) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      // Process standardized response and extract data
      const extractedData = this.processApiResponse<T>(response);
      
      console.log(`API client: Successful response from DELETE ${endpoint}`);
      return extractedData;
    } catch (error) {
      console.error(`API client: Error deleting ${endpoint}:`, error);
      this.handleApiError(error as AxiosError, endpoint);
      throw error;
    }
  }

  /**
   * Handle API errors consistently (enhanced for new format)
   */
  private handleApiError(error: Error | AxiosError, endpoint: string): void {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status
      const data = error.response?.data
      
      console.error(`API Error on ${endpoint}: ${status}`, data)
      
      // Handle specific error cases
      if (status === 401) {
        console.warn('Authentication error, user might need to re-login')
        // Could trigger a re-authentication flow here
      }

      // Handle standardized error responses
      if (data && typeof data === 'object' && 'error_code' in data) {
        console.error(`Standardized API Error - Code: ${data.error_code}, Message: ${data.error}`)
        if (data.details) {
          console.error('Error details:', data.details)
        }
      }
    } else {
      console.error(`Network error on ${endpoint}:`, error.message)
    }
  }
}

// Create a singleton instance with the API URL from environment variables
const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = new ApiClient(baseUrl);

export default apiClient;
