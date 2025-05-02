import NextAuth, { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import AppleProvider from "next-auth/providers/apple"
import EmailProvider from "next-auth/providers/email"
import { JWT } from "next-auth/jwt"
import { SendVerificationRequestParams } from "next-auth/providers/email"
import { PrismaAdapter } from "@auth/prisma-adapter"
import { prisma } from "../../../../lib/prisma"
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
    // Use our custom email service to send the magic link
    await sendMagicLinkEmail({ email, url })
  } catch (error) {
    console.error("Error sending verification email", error)
    
    // In development, always log the magic link URL to the console as a fallback
    if (process.env.NODE_ENV === "development") {
      console.log(`[DEV FALLBACK] Magic link for ${email}: ${url}`)
    }
  }
}

// Function to sync user with Django backend
async function syncUserWithBackend(user: any): Promise<any> {
  try {
    const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/sync/`
    
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
    })
    
    if (!response.ok) {
      throw new Error(`Backend sync failed: ${response.status}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error("Error syncing user with backend:", error)
    return null
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
      maxAge: 24 * 60 * 60, // 24 hours
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
      // Add user data to token when first signing in
      if (user) {
        token.user = user
        
        // If user just signed in, sync with backend
        if (account) {
          const backendUser = await syncUserWithBackend({
            ...user,
            provider: account.provider
          })
          
          if (backendUser) {
            token.django_user_id = backendUser.id
            token.django_token = backendUser.django_token
            token.has_completed_onboarding = backendUser.has_completed_onboarding
          }
        }
      }
      return token
    },
    async session({ session, token }: { session: any; token: JWT }) {
      // Add user data to session
      session.user = token.user as SessionUser || session.user
      
      // Add Django data to session
      if (token.django_user_id) {
        session.user.django_user_id = token.django_user_id
      }
      if (token.django_token) {
        session.user.django_token = token.django_token
      }
      if (token.has_completed_onboarding !== undefined) {
        session.user.has_completed_onboarding = token.has_completed_onboarding
      }
      
      return session
    },
    async redirect({ url, baseUrl }: { url: string; baseUrl: string }) {
      // Handle redirects
      if (url.startsWith("/")) {
        // Relative URLs are allowed
        return `${baseUrl}${url}`
      } else if (new URL(url).origin === baseUrl) {
        // URLs with the same origin are allowed
        return url
      }
      // Default to redirecting to the base URL
      return baseUrl
    },
  },
  session: {
    strategy: "jwt",
  },
  // Enable debug in development
  debug: process.env.NODE_ENV === "development",
}

const handler = NextAuth(authOptions)

export { handler as GET, handler as POST } 