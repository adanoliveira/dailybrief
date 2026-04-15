import apiService from "./api-service"

export interface User {
  id: string
  email: string
  createdAt: string
}

export interface AuthResponse {
  user: User
  token: string
}

class AuthService {
  private static instance: AuthService

  private constructor() {}

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService()
    }
    return AuthService.instance
  }

  public async signIn(email: string): Promise<boolean> {
    const response = await apiService.post<{ success: boolean }>("/auth/signin", { email })
    return response.status === 200
  }

  public async verifyToken(token: string): Promise<AuthResponse> {
    const response = await apiService.post<AuthResponse>("/auth/verify", { token })

    if (response.error) {
      throw new Error(response.error)
    }

    // Save the token
    apiService.setToken(response.data!.token)

    return response.data!
  }

  public async signInWithGoogle(token: string): Promise<AuthResponse> {
    const response = await apiService.post<AuthResponse>("/auth/google", { token })

    if (response.error) {
      throw new Error(response.error)
    }

    // Save the token
    apiService.setToken(response.data!.token)

    return response.data!
  }

  public async signUp(email: string): Promise<boolean> {
    const response = await apiService.post<{ success: boolean }>("/auth/signup", { email })
    return response.status === 200
  }

  public async signOut(): Promise<void> {
    apiService.clearToken()
  }

  public isAuthenticated(): boolean {
    return apiService.isAuthenticated()
  }

  public async getUser(): Promise<User> {
    const response = await apiService.get<User>("/user/me")

    if (response.error) {
      throw new Error(response.error)
    }

    return response.data!
  }

  public async checkOnboardingStatus(): Promise<{ has_completed_onboarding: boolean }> {
    try {
      const response = await apiService.get<{ has_completed_onboarding: boolean }>("/auth/onboarding-status/");
      
      if (response.error) {
        console.error("Error checking onboarding status:", response.error);
        // Default to not completed if there's an error
        return { has_completed_onboarding: false };
      }
      
      return response.data!;
    } catch (error) {
      console.error("Failed to check onboarding status:", error);
      // Default to not completed if there's an error
      return { has_completed_onboarding: false };
    }
  }
}

export default AuthService.getInstance()
