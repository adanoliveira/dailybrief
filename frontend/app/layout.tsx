import type React from "react"
import { ThemeProvider } from "@/components/theme-provider"
import { LanguageProvider } from "@/components/language-provider"
import { AuthProvider } from "@/components/auth-provider"
import { UserProvider } from "@/lib/user-context"
import { Toaster } from "@/components/ui/toaster"
import { Inter } from "next/font/google"
import "./globals.css"
import { ServiceWorkerRegistration } from "@/components/service-worker-registration"
import SessionRedirect from "@/components/session-redirect"

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "DailyBrief - Your Personalized News Digest",
  description:
    "Get daily news summaries tailored to your interests. Skip the endless scrolling and focus on what matters to you.",
  manifest: "/manifest.json",
  generator: 'v0.dev',
  icons: {
    icon: [
      { url: '/favicon.svg' },
      { url: '/favicon.ico' },
    ],
    apple: [
      { url: '/apple-icon.png' },
    ],
  },
}

export const viewport = {
  themeColor: "#3b82f6",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Immediate scroll restoration - runs before React hydration
              (function() {
                try {
                  // Only run on feed pages
                  const path = window.location.pathname;
                  const isFeedPage = path.includes('/home') || path.includes('/world') || path.includes('/headlines');
                  
                  if (!isFeedPage) return;
                  
                  // Parse feed type from URL
                  let feedType = 'personalized';
                  let topicSlug = undefined;
                  
                  if (path.includes('/world') || path.includes('/headlines')) {
                    feedType = 'world';
                    topicSlug = 'all';
                  } else if (path.includes('/home')) {
                    feedType = 'personalized';
                    topicSlug = 'for-you';
                  }
                  
                  // Generate cache key (same format as React code: feedType:topicSlug::relevance)
                  const cacheKey = feedType + ':' + (topicSlug || '') + '::relevance';
                  const savedPosition = sessionStorage.getItem('scroll-' + cacheKey);
                  
                  if (savedPosition) {
                    const position = parseInt(savedPosition, 10);
                    
                    // Restore immediately - no animation to prevent flash
                    window.scrollTo(0, position);
                    
                    // Mark as restored to prevent React from doing it again
                    sessionStorage.setItem('scroll-restored-' + cacheKey, 'true');
                    window.__scrollRestored = cacheKey;
                  }
                } catch (error) {
                  console.warn('Failed to restore scroll immediately:', error);
                }
              })();
            `,
          }}
        />
      </head>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <AuthProvider>
            <UserProvider>
              <LanguageProvider>
                <SessionRedirect>
                  {children}
                </SessionRedirect>
                <Toaster />
                <ServiceWorkerRegistration />
              </LanguageProvider>
            </UserProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
