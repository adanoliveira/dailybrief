"use client"

import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { LogoHorizontal } from "@/components/ui/logo"

export default function AuthErrorPage() {
  const searchParams = useSearchParams()
  const error = searchParams?.get("error") || ""

  // Get the error message and help text based on the error code
  const { title, message, helpText } = getErrorDetails(error)

  return (
    <div className="container flex flex-col items-center justify-center min-h-screen py-12">
      <div className="mb-8">
        <LogoHorizontal width={200} priority />
      </div>
      
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3">
          <CardTitle className="text-2xl font-bold text-center">{title}</CardTitle>
          <CardDescription className="text-center">
            There was a problem signing you in
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-destructive p-4 text-center">
            <p className="text-sm text-destructive">{message}</p>
            {helpText && (
              <p className="text-xs text-muted-foreground mt-2">{helpText}</p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex justify-center">
          <Button asChild>
            <Link className="bg-primary/10 hover:bg-primary/20 text-primary px-4 py-2 rounded-md" href="/auth">Try Again</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

// Helper function to get error details based on the error code
function getErrorDetails(errorCode: string): { 
  title: string; 
  message: string; 
  helpText?: string 
} {
  switch (errorCode) {
    case "OAuthAccountNotLinked":
      return {
        title: "Account Already Exists",
        message: "This email is already associated with another sign-in method.",
        helpText: "Please sign in using the original provider you used previously."
      };
    case "Verification":
      return {
        title: "Verification Failed",
        message: "The verification link is invalid or has expired.",
        helpText: "Magic links are only valid for 5 minutes. Please request a new one."
      };
    case "AccessDenied":
      return {
        title: "Access Denied",
        message: "You do not have permission to sign in.",
      };
    case "EmailSignin":
      return {
        title: "Email Sign-in Failed",
        message: "The email sign-in failed. Please check your email address and try again.",
      };
    case "RateLimitExceeded":
      return {
        title: "Too Many Attempts",
        message: "You've made too many sign-in attempts in a short period.",
        helpText: "Please wait a while before trying again."
      };
    case "ExpiredToken":
      return {
        title: "Link Expired",
        message: "The magic link has expired.",
        helpText: "Magic links are only valid for 5 minutes. Please request a new one."
      };
    case "TokenAlreadyUsed":
      return {
        title: "Link Already Used",
        message: "This magic link has already been used.",
        helpText: "For security reasons, magic links can only be used once. Please request a new one."
      };
    default:
      return {
        title: "Authentication Error",
        message: "Something went wrong during authentication. Please try again.",
      };
  }
} 