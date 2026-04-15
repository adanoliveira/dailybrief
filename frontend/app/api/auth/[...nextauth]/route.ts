import NextAuth, { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
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

const OFFLINE_MODE_TOKEN = "offline_mode_token"
const IS_DEVELOPMENT = process.env.NODE_ENV === "development"

function getBackendSyncUrl(): string {
  const envApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim()
  if (envApiUrl) {
    const cleanUrl = envApiUrl.endsWith("/api") ? envApiUrl.slice(0, -4) : envApiUrl
    return `${cleanUrl}/api/accounts/sync/`
  }

  const isDocker = process.env.DATABASE_URL?.includes("db:5432") || process.env.SUPABASE_DB_HOST === "db"
  return isDocker ? "http://backend:8000/api/accounts/sync/" : "http://localhost:8000/api/accounts/sync/"
}

function debugLog(message: string): void {
  if (IS_DEVELOPMENT) {
    console.log(message)
  }
}

// Custom function to handle email verification requests
async function sendVerificationRequest(params: SendVerificationRequestParams) {
  const { identifier: email, url } = params
  
  debugLog("[NextAuth] sendVerificationRequest called")
  
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
      console.warn("Could not access EmailVerificationRequest model")
    }
    
    // Use our custom email service to send the magic link
    debugLog("[NextAuth] Sending magic link email")
    await sendMagicLinkEmail({ email, url });
    debugLog("[NextAuth] Magic link email sent")
  } catch (error) {
    console.error("Error sending verification email")
    if (IS_DEVELOPMENT) {
      console.error(error)
    }
    
    // In development, always log the magic link URL to the console as a fallback
    if (IS_DEVELOPMENT) {
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
    const apiUrl = getBackendSyncUrl()
    
    const requestData = {
      email: user.email,
      name: user.name || user.email.split("@")[0],
      provider: user.provider || "email",
      nextauth_id: user.id,
      image: user.image || "",
    };
    
    debugLog("[Sync] Syncing user with backend")
    
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestData),
      // Add a timeout to prevent hanging if backend is down
      signal: AbortSignal.timeout(10000) // Increased to 10 seconds
    })
    
    debugLog(`[Sync] Backend sync response status: ${response.status}`)
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Backend sync failed with status ${response.status}`)
      throw new Error(`Backend sync failed: ${response.status} - ${errorText}`)
    }
    
    const data = await response.json();
    
    // Validate the token format before returning
    if (data.django_token) {
      const token = data.django_token.trim();
      
      // Basic JWT validation - should have 3 segments separated by dots
      if (!token || token === OFFLINE_MODE_TOKEN || !token.includes('.') || token.split('.').length !== 3) {
        console.error("Invalid token format received from backend")
        throw new Error("Invalid token format received from backend");
      }
      
      // JWT token validated successfully
    } else {
      console.error("No django_token in backend response")
      throw new Error("No django_token received from backend");
    }
    
    return data;
  } catch (error) {
    console.error("Error syncing user with backend")
    if (IS_DEVELOPMENT) {
      console.error(error)
    }
    
    // Return a default response that allows the user to continue
    debugLog("Falling back to offline mode token")
    return {
      id: 0,
      django_token: OFFLINE_MODE_TOKEN,
      has_completed_onboarding: false
    }
  }
}

// Check onboarding status from the Django backend
async function checkOnboardingStatus(token: string): Promise<boolean> {
  if (!token) return false;
  
  try {
    // If using the offline mode token, return false to direct to onboarding
    if (token === OFFLINE_MODE_TOKEN) return false;
    const apiUrl = getBackendSyncUrl()
    
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
      console.error(`Failed to check user status: ${response.status}`)
      return false;
    }
    
    const data = await response.json();
    return !!data.has_completed_onboarding;
  } catch (error) {
    console.error("Error checking onboarding status")
    if (IS_DEVELOPMENT) {
      console.error(error)
    }
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
        debugLog(`Sign in allowed for provider ${account?.provider}`)
        return true;
      } catch (error) {
        console.error("Sign in callback error")
        if (IS_DEVELOPMENT) {
          console.error(error)
        }
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
            debugLog(`[JWT] Starting backend sync (provider: ${account.provider})`)
            const backendUser = await syncUserWithBackend({
              ...user,
              provider: account.provider
            });
            
            debugLog("[JWT] Backend sync completed")
            
            if (backendUser) {
              token.django_user_id = backendUser.id;
              token.django_token = backendUser.django_token;
              token.has_completed_onboarding = backendUser.has_completed_onboarding;
            }
          } catch (error) {
            console.error("[JWT] Backend sync failed, using offline mode")
            if (IS_DEVELOPMENT) {
              console.error(error)
            }
            // Continue with auth flow even if backend sync fails
            token.django_user_id = 0;
            token.django_token = OFFLINE_MODE_TOKEN;
            token.has_completed_onboarding = false;
          }
        }
      }
      
      // Handle session updates (triggered manually by updateSession() call)
      if (trigger === "update" && token.django_token && token.django_token !== OFFLINE_MODE_TOKEN) {
        try {
          debugLog("JWT callback: Session update triggered, refreshing onboarding status")
          const onboardingCompleted = await checkOnboardingStatus(token.django_token);
          
          if (onboardingCompleted) {
            debugLog("JWT callback: User has completed onboarding, updating token")
            token.has_completed_onboarding = true;
          }
        } catch (error) {
          console.error("JWT callback: Error checking onboarding status during session update")
          if (IS_DEVELOPMENT) {
            console.error(error)
          }
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
