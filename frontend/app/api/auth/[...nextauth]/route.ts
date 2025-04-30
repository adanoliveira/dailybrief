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
    async jwt({ token, user }): Promise<JWT> {
      // Add user data to token
      if (user) {
        token.user = user
      }
      return token
    },
    async session({ session, token }: { session: any; token: JWT }) {
      // Add user data to session
      session.user = token.user as SessionUser || session.user
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