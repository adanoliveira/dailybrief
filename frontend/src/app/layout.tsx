import type React from "react"
import { ThemeProvider } from "@/components/theme-provider"
import { LanguageProvider } from "@/components/language-provider"
import { Toaster } from "@/components/ui/toaster"
import { Inter } from "next/font/google"
import "./globals.css"
import { ServiceWorkerRegistration } from "@/components/service-worker-registration"

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "DailyBrief - Your Personalized News Digest",
  description:
    "Get daily news summaries tailored to your interests. Skip the endless scrolling and focus on what matters to you.",
  manifest: "/manifest.json",
  themeColor: "#3b82f6",
  viewport: "width=device-width, initial-scale=1, maximum-scale=1",
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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="light">
          <LanguageProvider>
            {children}
            <Toaster />
            <ServiceWorkerRegistration />
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
