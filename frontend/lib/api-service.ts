const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
import { getSession } from 'next-auth/react'
import { Session } from 'next-auth'

// Extended session type
interface ExtendedSession extends Session {
  user: {
    id: string;
    name?: string | null;
    email?: string | null;
    image?: string | null;
    django_token?: string;
    django_user_id?: number;
    has_completed_onboarding?: boolean;
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
    // Initialize token from localStorage if available
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("auth_token")
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
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token)
    }
  }

  public clearToken(): void {
    this.token = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token")
    }
  }

  public isAuthenticated(): boolean {
    return !!this.token
  }

  private async getAuthToken(): Promise<string | null> {
    // First try to use the token from NextAuth session
    if (typeof window !== "undefined") {
      try {
        const session = await getSession() as ExtendedSession | null;
        if (session?.user?.django_token) {
          // Update our stored token
          this.setToken(session.user.django_token);
          return session.user.django_token;
        }
      } catch (error) {
        console.error("Error getting session:", error);
      }
    }
    
    // Fall back to stored token
    return this.token;
  }

  private async getHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    }

    const token = await this.getAuthToken()
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }

    return headers
  }

  public async get<T>(endpoint: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
    try {
      const url = new URL(`${API_BASE_URL}${endpoint}`)

      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          url.searchParams.append(key, value)
        })
      }

      const response = await fetch(url.toString(), {
        method: "GET",
        headers: await this.getHeaders(),
      })

      const data = await response.json()

      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.error || "An error occurred",
        status: response.status,
      }
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      }
    }
  }

  public async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: await this.getHeaders(),
        body: JSON.stringify(body),
      })

      const data = await response.json()

      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.error || "An error occurred",
        status: response.status,
      }
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      }
    }
  }

  public async put<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "PUT",
        headers: await this.getHeaders(),
        body: JSON.stringify(body),
      })

      const data = await response.json()

      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.error || "An error occurred",
        status: response.status,
      }
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      }
    }
  }

  public async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "DELETE",
        headers: await this.getHeaders(),
      })

      const data = await response.json()

      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.error || "An error occurred",
        status: response.status,
      }
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      }
    }
  }
}

export default ApiService.getInstance()
