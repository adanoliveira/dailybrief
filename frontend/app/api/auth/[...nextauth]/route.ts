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
    await sendMagicLinkEmail({ email, url })
  } catch (error) {
    console.error("Error sending verification email", error)
    
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
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    // Remove trailing slash if present
    const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    // Check if baseUrl already contains /api
    const apiPath = cleanBaseUrl.endsWith('/api') ? '/auth/sync/' : '/api/auth/sync/';
    const apiUrl = `${cleanBaseUrl}${apiPath}`;
    
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: user.email,
        name: user.name || user.email.split("@")[0],
        provider: user.provider || "email",
        nextauth_id: user.id,
        image: user.image || "",
      }),
      // Add a timeout to prevent hanging if backend is down
      signal: AbortSignal.timeout(5000)
    })
    
    if (!response.ok) {
      throw new Error(`Backend sync failed: ${response.status}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error("Error syncing user with backend:", error)
    // Return a default response that allows the user to continue
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
    
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    // Remove trailing slash if present
    const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    // Check if baseUrl already contains /api
    const apiPath = cleanBaseUrl.endsWith('/api') ? '/auth/onboarding-status/' : '/api/auth/onboarding-status/';
    const apiUrl = `${cleanBaseUrl}${apiPath}`;
    
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
      console.error(`Failed to check onboarding status: ${response.status}`)
      return false
    }
    
    const data = await response.json()
    return !!data.has_completed_onboarding
  } catch (error) {
    console.error("Error checking onboarding status:", error)
    return false
  }
}

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    AppleProvider({
      clientId: process.env.APPLE_ID!,
      clientSecret: process.env.APPLE_SECRET!,
    }),
    EmailProvider({
      server: process.env.EMAIL_SERVER,
      from: process.env.EMAIL_FROM || "noreply@dailybrief.com",
      // Custom function to send the verification email
      maxAge: 5 * 60, // 5 minutes instead of 24 hours
      generateVerificationToken: async () => {
        // Generate a random token
        const token = Array.from(
          { length: 32 },
          () => Math.floor(Math.random() * 36).toString(36)
        ).join("");
        
        return token;
      },
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
    async jwt({ token, user, account }): Promise<JWT> {
      // Add debugging for incoming token and user data
      console.log("JWT callback received:", JSON.stringify({
        hasToken: !!token,
        hasUser: !!user,
        hasAccount: !!account,
        accountProvider: account?.provider
      }));
      
      // Add user data to token when first signing in
      if (user) {
        token.user = user;
        
        // If user just signed in, sync with backend
        if (account) {
          try {
            console.log("Syncing user with backend:", user.email);
            const backendUser = await syncUserWithBackend({
              ...user,
              provider: account.provider
            });
            
            console.log("Backend sync response:", JSON.stringify({
              ...backendUser,
              django_token: backendUser?.django_token ? "[PRESENT]" : "[MISSING]"
            }));
            
            if (backendUser) {
              token.django_user_id = backendUser.id;
              token.django_token = backendUser.django_token;
              token.has_completed_onboarding = backendUser.has_completed_onboarding;
            }
          } catch (error) {
            console.error("JWT callback error syncing with backend:", error);
            // Continue with auth flow even if backend sync fails
            token.django_user_id = 0;
            token.django_token = "offline_mode_token";
            token.has_completed_onboarding = false;
          }
        }
      }
      
      // Log the token being returned
      console.log("JWT callback returning token with:", JSON.stringify({
        user_id: (token.user as any)?.id || "not set",
        django_user_id: token.django_user_id || "not set",
        django_token: token.django_token ? "[PRESENT]" : "[MISSING]",
        has_completed_onboarding: token.has_completed_onboarding
      }));
      
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
      
      // Add debugging info
      console.log("Session callback returning:", JSON.stringify({
        user: {
          ...session.user,
          django_token: session.user.django_token ? "[PRESENT]" : "[MISSING]",
        }
      }));
      
      return session;
    },
    async redirect({ url, baseUrl, token }: { url: string; baseUrl: string; token?: JWT }) {
      // Check if this is a verification or error page
      if (url.includes("/auth/verify-request") || url.includes("/auth/error")) {
        return url;
      }
      
      // For callback and sign-in URLs, always redirect to onboarding
      // This handles the post-authentication redirect
      if (url.includes("/callback") || url.includes("/signin")) {
        console.log("Auth flow completed, redirecting to onboarding");
        return `${baseUrl}/onboarding`;
      }
      
      // For homepage requests, direct to onboarding if token exists, otherwise auth
      if (url === baseUrl || url === `${baseUrl}/`) {
        if (token) {
          console.log("Token exists for homepage request, redirecting to onboarding");
          return `${baseUrl}/onboarding`;
        } else {
          console.log("No token for homepage request, redirecting to auth");
          return `${baseUrl}/auth`;
        }
      }
      
      // Default redirects for all other URLs
      if (url.startsWith("/")) {
        // Relative URLs are allowed
        console.log(`Default redirect to: ${baseUrl}${url}`);
        return `${baseUrl}${url}`;
      } else if (new URL(url).origin === baseUrl) {
        // URLs with the same origin are allowed
        console.log(`Default redirect to same origin: ${url}`);
        return url;
      }
      
      // Default to redirecting to the base URL
      console.log(`Fallback redirect to base URL: ${baseUrl}`);
      return baseUrl;
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