import NextAuth, { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import AppleProvider from "next-auth/providers/apple"
import EmailProvider from "next-auth/providers/email"
import { JWT } from "next-auth/jwt"
import { SendVerificationRequestParams } from "next-auth/providers/email"
import { PrismaAdapter } from "@auth/prisma-adapter"
import { prisma } from "@/lib/prisma"
import { sendMagicLinkEmail } from "@/lib/email-service"

interface SessionUser {
  id: string
  email: string
  name?: string
  image?: string
  django_user_id?: number
  django_token?: string
  has_completed_onboarding?: boolean
}

// Custom function to handle email verification requests
async function sendVerificationRequest(params: SendVerificationRequestParams) {
  const { identifier: email, url } = params
  
  console.log(`[NextAuth] sendVerificationRequest called with:`, { email, url, urlType: typeof url });
  
  try {
    // Try to use our custom token tracking, but continue even if it fails
    try {
      // Invalidate any previous tokens for this email
      if (prisma && typeof (prisma as any).emailVerificationRequest?.updateMany === 'function') {
        await (prisma as any).emailVerificationRequest.updateMany({
          where: { 
            email: email,
            invalidated: false
          },
          data: { invalidated: true }
        });
      
        // Create a new token record
        await (prisma as any).emailVerificationRequest.create({
          data: {
            email: email,
          }
        });
      
        // Check for rate limiting (no more than 10 requests in the last hour)
        const lastHour = new Date(Date.now() - 60 * 60 * 1000);
        const recentRequests = await (prisma as any).emailVerificationRequest.count({
          where: {
            email: email,
            createdAt: {
              gte: lastHour
            }
          }
        });
      
        // If too many requests, throw an error
        if (recentRequests > 10) {
          throw new Error("Rate limit exceeded. Please try again later.");
        }
      }
    } catch (modelError) {
      // Log error but continue with sending the email
      console.warn("Could not access EmailVerificationRequest model:", modelError);
    }
    
    // Use our custom email service to send the magic link
    console.log(`[NextAuth] About to call sendMagicLinkEmail with URL: "${url}"`);
    await sendMagicLinkEmail({ email, url });
    console.log(`[NextAuth] sendMagicLinkEmail completed successfully`);
  } catch (error) {
    console.error("Error sending verification email:", error);
    console.error("Error details:", {
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : 'No stack trace',
      email,
      url,
      urlType: typeof url
    });
    
    // In development, always log the magic link URL to the console as a fallback
    if (process.env.NODE_ENV === "development") {
      console.log(`[DEV FALLBACK] Magic link for ${email}: ${url}`)
    }
    
    // Only rethrow non-model errors
    if (!(error instanceof Error) || !error.message.includes("emailVerificationRequest")) {
      throw error;
    }
  }
}

// Function to sync user with Django backend
async function syncUserWithBackend(user: any): Promise<any> {
  try {
    // Handle server-side vs client-side URL construction
    let apiUrl: string;
    
    // Check if we're running on the server (NextAuth JWT callback runs server-side)
    if (typeof window === 'undefined') {
      // Server-side: Detect if we're in Docker by checking hostname resolution
      let backendHost: string;
      
      try {
        // Try to detect if we're in Docker by checking environment or using backend hostname
        const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
        
        // If we have a DATABASE_URL with 'db:5432', we're likely in Docker
        const isDocker = process.env.DATABASE_URL?.includes('db:5432') || false;
        
        if (isDocker) {
          // We're in Docker - use the backend service name
          backendHost = 'backend:8000';
          apiUrl = `http://${backendHost}/api/accounts/sync/`;
          console.log(`[Sync] Detected Docker environment, using backend service: ${apiUrl}`);
        } else {
          // Not in Docker - use NEXT_PUBLIC_API_URL (works for both localhost dev and production)
          const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
          if (envApiUrl) {
            // Remove /api suffix if present to avoid duplication  
            const cleanUrl = envApiUrl.endsWith('/api') ? envApiUrl.slice(0, -4) : envApiUrl;
            apiUrl = `${cleanUrl}/api/accounts/sync/`;
          } else {
            // Final fallback to localhost
            apiUrl = "http://localhost:8000/api/accounts/sync/";
          }
          console.log(`[Sync] Using environment API URL for server-side request: ${apiUrl}`);
        }
      } catch (error) {
        // Fallback to environment URL or localhost if detection fails
        const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (envApiUrl) {
          const cleanUrl = envApiUrl.endsWith('/api') ? envApiUrl.slice(0, -4) : envApiUrl;
          apiUrl = `${cleanUrl}/api/accounts/sync/`;
        } else {
          apiUrl = "http://localhost:8000/api/accounts/sync/";
        }
        console.log(`[Sync] Failed to detect environment, using fallback: ${apiUrl}`);
      }
    } else {
      // Client-side: Always use localhost (browser can't resolve Docker hostnames)
      const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (envApiUrl) {
        // Remove /api if it's already in the base URL to avoid duplication
        const cleanUrl = envApiUrl.endsWith('/api') ? envApiUrl.slice(0, -4) : envApiUrl;
        apiUrl = `${cleanUrl}/api/accounts/sync/`;
      } else {
        apiUrl = "http://localhost:8000/api/accounts/sync/";
      }
      console.log(`[Sync] Client-side request URL: ${apiUrl}`);
    }
    
    const requestData = {
      email: user.email,
      name: user.name || user.email.split("@")[0],
      provider: user.provider || "email",
      nextauth_id: user.id,
      image: user.image || "",
    };
    
    console.log(`[Sync] Syncing user with backend:`, {
      email: user.email,
      apiUrl,
      requestData
    });
    
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestData),
      // Add a timeout to prevent hanging if backend is down
      signal: AbortSignal.timeout(10000) // Increased to 10 seconds
    })
    
    console.log(`[Sync] Backend sync response status: ${response.status}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Backend sync failed with status ${response.status}: ${errorText}`);
      throw new Error(`Backend sync failed: ${response.status} - ${errorText}`)
    }
    
    const data = await response.json();
    
    // Validate the token format before returning
    if (data.django_token) {
      const token = data.django_token.trim();
      
      // Basic JWT validation - should have 3 segments separated by dots
      if (!token || token === "offline_mode_token" || !token.includes('.') || token.split('.').length !== 3) {
        console.error("Invalid token format received from backend:", 
          token ? `Length: ${token.length}, Segments: ${token.split('.').length}` : "No token");
        throw new Error("Invalid token format received from backend");
      }
      
      // JWT token validated successfully
    } else {
      console.error("No django_token in backend response:", data);
      throw new Error("No django_token received from backend");
    }
    
    return data;
  } catch (error) {
    console.error("Error syncing user with backend:", error);
    console.error("Error details:", {
      message: error instanceof Error ? error.message : 'Unknown error',
      name: error instanceof Error ? error.name : 'Unknown',
      stack: error instanceof Error ? error.stack : 'No stack trace'
    });
    
    // Return a default response that allows the user to continue
    console.log("Falling back to offline_mode_token");
    return {
      id: 0,
      django_token: "offline_mode_token",
      has_completed_onboarding: false
    }
  }
}

// Check onboarding status from the Django backend
async function checkOnboardingStatus(token: string): Promise<boolean> {
  if (!token) return false;
  
  try {
    // If using the offline mode token, return false to direct to onboarding
    if (token === "offline_mode_token") return false;
    
    // Handle server-side vs client-side URL construction
    let apiUrl: string;
    
    if (typeof window === 'undefined') {
      // Server-side: Detect if we're in Docker environment
      try {
        // If we have a DATABASE_URL with 'db:5432', we're likely in Docker
        const isDocker = process.env.DATABASE_URL?.includes('db:5432') || false;
        
        if (isDocker) {
          // We're in Docker - use the backend service name
          apiUrl = `http://backend:8000/api/accounts/sync/`;
          console.log(`[OnboardingCheck] Using Docker backend service: ${apiUrl}`);
        } else {
          // Not in Docker - use NEXT_PUBLIC_API_URL (works for both localhost dev and production)
          const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
          if (envApiUrl) {
            // Remove /api suffix if present to avoid duplication
            const cleanUrl = envApiUrl.endsWith('/api') ? envApiUrl.slice(0, -4) : envApiUrl;
            apiUrl = `${cleanUrl}/api/accounts/sync/`;
          } else {
            // Final fallback to localhost
            apiUrl = "http://localhost:8000/api/accounts/sync/";
          }
          console.log(`[OnboardingCheck] Using environment API URL: ${apiUrl}`);
        }
      } catch (error) {
        // Fallback to environment URL or localhost if detection fails
        const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (envApiUrl) {
          const cleanUrl = envApiUrl.endsWith('/api') ? envApiUrl.slice(0, -4) : envApiUrl;
          apiUrl = `${cleanUrl}/api/accounts/sync/`;
        } else {
          apiUrl = "http://localhost:8000/api/accounts/sync/";
        }
        console.log(`[OnboardingCheck] Failed to detect environment, using fallback: ${apiUrl}`);
      }
    } else {
      // Client-side: Always use localhost
      const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (envApiUrl) {
        const cleanUrl = envApiUrl.endsWith('/api') ? envApiUrl.slice(0, -4) : envApiUrl;
        apiUrl = `${cleanUrl}/api/accounts/sync/`;
      } else {
        apiUrl = "http://localhost:8000/api/accounts/sync/";
      }
    }
    
    // Checking onboarding status with backend
    
    const response = await fetch(apiUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      // Add a timeout to prevent hanging if backend is down
      signal: AbortSignal.timeout(5000)
    })
    
    if (!response.ok) {
      console.error(`Failed to check user status: ${response.status}`);
      const responseText = await response.text();
      console.error(`Response body: ${responseText}`);
      return false;
    }
    
    const data = await response.json();
    return !!data.has_completed_onboarding;
  } catch (error) {
    console.error("Error checking onboarding status:", error);
    return false;
  }
}

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      allowDangerousEmailAccountLinking: true,
      authorization: {
        params: {
          scope: "openid email profile",
          prompt: "select_account"
        }
      }
    }),
    // Apple Sign-in temporarily disabled - will be enabled later
    // @ts-ignore - The types for Apple provider don't have clientSecret as an object, but it actually accepts this format
    // AppleProvider({
    //   clientId: process.env.APPLE_ID!,
    //   clientSecret: {
    //     teamId: process.env.APPLE_TEAM_ID as string,
    //     privateKey: process.env.APPLE_SECRET as string,
    //     keyId: process.env.APPLE_KEY_ID as string,
    //   },
    //   authorization: {
    //     params: {
    //       scope: "name email",
    //       response_mode: "form_post"
    //     }
    //   }
    // }),
    EmailProvider({
      from: process.env.EMAIL_FROM || "noreply@dailybrief.com",
      sendVerificationRequest,
    }),
  ],
  pages: {
    signIn: "/auth",
    signOut: "/auth",
    error: "/auth/error",
    verifyRequest: "/auth/verify-request",
  },
  callbacks: {
    async signIn({ user, account, profile, email, credentials }) {
      try {
        // Allow sign in if:
        // 1. This is the first sign in (no account exists yet)
        // 2. The account is already linked to the user
        // 3. There's an existing user with the same email (auto-link)
        
        const userEmail = user?.email;
        
        if (!userEmail) {
          console.error("Sign in denied: User has no email", { provider: account?.provider });
          return false;
        }
        
        // Google OAuth accounts are inherently verified through the OAuth process
        // Email provider verification happens through magic link clicks
        console.log(`Sign in allowed: ${account?.provider} authentication for ${userEmail}`);
        return true;
      } catch (error) {
        console.error("Sign in callback error:", error);
        return false;
      }
    },
    async jwt({ token, user, account, trigger }): Promise<JWT> {
      // JWT callback: Processing authentication data
      
      // Add user data to token when first signing in
      if (user) {
        token.user = user;
        
        // If user just signed in, sync with backend
        if (account) {
          try {
            console.log(`[JWT] Starting backend sync for user: ${user.email} (provider: ${account.provider})`);
            const backendUser = await syncUserWithBackend({
              ...user,
              provider: account.provider
            });
            
            console.log(`[JWT] Backend sync completed:`, {
              userId: backendUser?.id,
              hasToken: !!backendUser?.django_token,
              tokenLength: backendUser?.django_token?.length,
              onboardingComplete: backendUser?.has_completed_onboarding
            });
            
            if (backendUser) {
              token.django_user_id = backendUser.id;
              token.django_token = backendUser.django_token;
              token.has_completed_onboarding = backendUser.has_completed_onboarding;
            }
          } catch (error) {
            console.error("[JWT] Backend sync failed, using offline mode:", error);
            // Continue with auth flow even if backend sync fails
            token.django_user_id = 0;
            token.django_token = "offline_mode_token";
            token.has_completed_onboarding = false;
          }
        }
      }
      
      // Handle session updates (triggered manually by updateSession() call)
      if (trigger === "update" && token.django_token && token.django_token !== "offline_mode_token") {
        try {
          console.log("JWT callback: Session update triggered, refreshing onboarding status");
          const onboardingCompleted = await checkOnboardingStatus(token.django_token);
          
          if (onboardingCompleted) {
            console.log("JWT callback: User has completed onboarding, updating token");
            token.has_completed_onboarding = true;
          }
        } catch (error) {
          console.error("JWT callback: Error checking onboarding status during session update:", error);
          // Don't update the token if the check fails, keep the existing value
        }
      }
      
      // JWT token prepared for session
      
      return token;
    },
    async session({ session, token }: { session: any; token: JWT }) {
      // Add user data to session
      session.user = session.user || {} as SessionUser;
      
      // Copy user data from token if available
      if (token.user) {
        session.user.id = (token.user as any).id;
        session.user.email = (token.user as any).email;
        session.user.name = (token.user as any).name;
        session.user.image = (token.user as any).image;
      }
      
      // Add Django data to session
      if (token.django_user_id) {
        session.user.django_user_id = token.django_user_id;
      }
      if (token.django_token) {
        session.user.django_token = token.django_token;
      }
      if (token.has_completed_onboarding !== undefined) {
        session.user.has_completed_onboarding = token.has_completed_onboarding;
      }
      
      // Session prepared for client
      
      return session;
    },
    async redirect({ url, baseUrl, token }: { url: string; baseUrl: string; token?: JWT }) {
      // Handle authentication-specific URLs
      
      // For callback and sign-in URLs, redirect to auth page (client will handle further routing)
      if (url.includes("/api/auth/callback") || url.includes("/api/auth/signin")) {
        return `${baseUrl}/auth`;
      }
      
      // For verification and error URLs, keep them as is
      if (url.includes("/auth/verify-request") || url.includes("/auth/error")) {
        return url;
      }
      
      // For all other URLs, don't interfere with the destination
      return url;
    },
  },
  session: {
    strategy: "jwt",
    maxAge: 180 * 24 * 60 * 60, // 180 days
  },
  // Enable debug in development
  debug: process.env.NODE_ENV === "development",
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST } 