"use client"

import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { LogoHorizontal } from "@/components/ui/logo"

export default function AuthErrorPage() {
  const searchParams = useSearchParams()
  const error = searchParams.get("error")

  let errorMessage = "Something went wrong during authentication."

  // Handle specific error cases
  if (error === "OAuthAccountNotLinked") {
    errorMessage = "This email is already associated with another account. Please sign in using the original provider."
  } else if (error === "Verification") {
    errorMessage = "The verification link is invalid or has expired. Please try signing in again."
  } else if (error === "AccessDenied") {
    errorMessage = "Access denied. You do not have permission to sign in."
  }

  return (
    <div className="container flex flex-col items-center justify-center min-h-screen py-12">
      <div className="mb-8">
        <LogoHorizontal width={200} priority />
      </div>
      
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3">
          <CardTitle className="text-2xl font-bold text-center">Authentication Error</CardTitle>
          <CardDescription className="text-center">
            There was a problem signing you in
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-destructive p-4 text-center">
            <p className="text-sm text-destructive">{errorMessage}</p>
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