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
import { Analytics } from "@vercel/analytics/react"
import { SpeedInsights } from "@vercel/speed-insights/next"

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
                  
                  // Check for onboarding completion or new session - these should start at top
                  const urlParams = new URLSearchParams(window.location.search);
                  const isOnboardingComplete = urlParams.get('onboarding_complete') === 'true';
                  const isNewSession = urlParams.get('new_session') === 'true';
                  const isForced = urlParams.get('force') === 'true';
                  
                  // Check if this is a page refresh/reload
                  const isPageRefresh = (
                    performance.navigation && performance.navigation.type === 1 // TYPE_RELOAD
                  ) || (
                    performance.getEntriesByType && 
                    performance.getEntriesByType('navigation')[0] && 
                    performance.getEntriesByType('navigation')[0].type === 'reload'
                  );
                  
                  // Check if this is a fresh sign-in (no existing scroll data)
                  const isSignIn = !sessionStorage.getItem('user-session-established');
                  
                  // Always start at top for these cases:
                  // 1. Onboarding completion
                  // 2. New session
                  // 3. Forced refresh
                  // 4. Page refresh/reload
                  // 5. Fresh sign-in
                  if (isOnboardingComplete || isNewSession || isForced || isPageRefresh || isSignIn) {
                    window.scrollTo(0, 0);
                    
                    // Mark session as established after sign-in
                    if (isSignIn) {
                      sessionStorage.setItem('user-session-established', 'true');
                    }
                    
                    // Clear any saved scroll positions for fresh start
                    if (isPageRefresh || isSignIn) {
                      const feedTypes = ['personalized:for-you', 'world:all', 'personalized:', 'world:'];
                      feedTypes.forEach(feedKey => {
                        sessionStorage.removeItem('scroll-' + feedKey + '::relevance');
                        sessionStorage.removeItem('scroll-restored-' + feedKey + '::relevance');
                      });
                    }
                    
                    return;
                  }
                  
                  // Parse feed type from URL for normal scroll restoration
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
                <Analytics />
                <SpeedInsights />
              </LanguageProvider>
            </UserProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
