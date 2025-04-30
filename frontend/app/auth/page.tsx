"use client"

import { useState } from "react"
import { signIn } from "next-auth/react"
import { Button, buttonVariants } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LogoHorizontal } from "@/components/ui/logo"
import Link from "next/link"
import { FaGoogle, FaApple } from "react-icons/fa"
import { cn } from "@/lib/utils"

export default function AuthPage() {
  const [isEmailSent, setIsEmailSent] = useState(false)
  const [email, setEmail] = useState("")

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      // Use NextAuth to send the magic link
      await signIn("email", { email, redirect: false })
      setIsEmailSent(true)
    } catch (error) {
      console.error("Error sending magic link:", error)
      // Handle error
    }
  }

  const handleGoogleSignIn = async () => {
    await signIn("google", { callbackUrl: "/onboarding" })
  }

  const handleAppleSignIn = async () => {
    await signIn("apple", { callbackUrl: "/onboarding" })
  }

  return (
    <div className="container flex flex-col items-center justify-center min-h-screen py-12">
      <div className="mb-8">
        <LogoHorizontal width={200} priority />
      </div>
      
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3">
          <CardTitle className="text-2xl font-bold text-center">Welcome to DailyBrief</CardTitle>
          <CardDescription className="text-center">Your personalized news digest</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <button 
            className={cn(buttonVariants({ variant: "outline" }), "w-full")}
            onClick={handleGoogleSignIn}
          >
            <FaGoogle className="mr-2" size={16} />
            Continue with Google
          </button>
          
          <button 
            className={cn(buttonVariants({ variant: "outline" }), "w-full")}
            onClick={handleAppleSignIn}
          >
            <FaApple className="mr-2" size={16} />
            Continue with Apple
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t"></span>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
            </div>
          </div>

          {!isEmailSent ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input 
                  id="email" 
                  type="email" 
                  placeholder="name@example.com" 
                  value={email}
                  onChange={handleEmailChange}
                  required 
                />
              </div>
              
              <Button type="submit" className="w-full">
                Continue with Email
              </Button>

              <div className="text-balance text-center text-xs text-muted-foreground [&_a]:underline [&_a]:underline-offset-4 hover:[&_a]:text-primary">
                By continuing, you agree to our <Link href="/terms">Terms of Service</Link>{" "}
                and <Link href="/privacy">Privacy Policy</Link>.
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="rounded-lg border p-4 text-center">
                <p className="text-sm">Check your email for a magic link</p>
                <p className="text-xs text-muted-foreground mt-1">
                  We've sent a secure link to {email}
                </p>
              </div>
              <button 
                className={cn(buttonVariants({ variant: "outline" }), "w-full")}
                onClick={() => setIsEmailSent(false)}
              >
                Try another email
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 