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
