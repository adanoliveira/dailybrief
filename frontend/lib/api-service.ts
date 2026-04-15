import { getSession } from 'next-auth/react'
import { Session } from 'next-auth'
import apiClient, { ApiError } from './api-client'

interface ExtendedSession extends Session {
  user: {
    id: string
    name?: string | null
    email?: string | null
    image?: string | null
    django_token?: string
    django_user_id?: number
    has_completed_onboarding?: boolean
  }
}

export interface ApiResponse<T> {
  data?: T
  error?: string
  status: number
}

export class ApiService {
  private static instance: ApiService
  private token: string | null = null

  private constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService()
    }

    return ApiService.instance
  }

  public setToken(token: string): void {
    this.token = token

    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token)
    }
  }

  public clearToken(): void {
    this.token = null

    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
  }

  public isAuthenticated(): boolean {
    return !!this.token
  }

  private async getAuthToken(): Promise<string | null> {
    if (typeof window !== 'undefined') {
      try {
        const session = (await getSession()) as ExtendedSession | null
        if (session?.user?.django_token) {
          this.setToken(session.user.django_token)
          return session.user.django_token
        }
      } catch (error) {
        console.error('Error getting session:', error)
      }
    }

    return this.token
  }

  private async getRequestHeaders(): Promise<Record<string, string>> {
    const token = await this.getAuthToken()

    if (!token) {
      return {}
    }

    return {
      Authorization: `Bearer ${token}`,
    }
  }

  private buildEndpoint(endpoint: string, params?: Record<string, string>): string {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`

    if (!params || Object.keys(params).length === 0) {
      return cleanEndpoint
    }

    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      query.append(key, value)
    })

    const queryString = query.toString()
    return queryString ? `${cleanEndpoint}?${queryString}` : cleanEndpoint
  }

  private successResponse<T>(data: T): ApiResponse<T> {
    return {
      data,
      status: 200,
    }
  }

  private errorResponse<T>(error: unknown): ApiResponse<T> {
    if (error instanceof ApiError) {
      return {
        error: error.message,
        status: error.status || 0,
      }
    }

    if (error instanceof Error) {
      return {
        error: error.message,
        status: 0,
      }
    }

    return {
      error: 'Network error',
      status: 0,
    }
  }

  public async get<T>(endpoint: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
    try {
      const data = await apiClient.get<T>(this.buildEndpoint(endpoint, params), {
        headers: await this.getRequestHeaders(),
      })

      return this.successResponse(data)
    } catch (error) {
      return this.errorResponse<T>(error)
    }
  }

  public async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const data = await apiClient.post<T>(this.buildEndpoint(endpoint), body, {
        headers: await this.getRequestHeaders(),
      })

      return this.successResponse(data)
    } catch (error) {
      return this.errorResponse<T>(error)
    }
  }

  public async put<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const data = await apiClient.put<T>(this.buildEndpoint(endpoint), body, {
        headers: await this.getRequestHeaders(),
      })

      return this.successResponse(data)
    } catch (error) {
      return this.errorResponse<T>(error)
    }
  }

  public async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const data = await apiClient.delete<T>(this.buildEndpoint(endpoint), {
        headers: await this.getRequestHeaders(),
      })

      return this.successResponse(data)
    } catch (error) {
      return this.errorResponse<T>(error)
    }
  }
}

export default ApiService.getInstance()
