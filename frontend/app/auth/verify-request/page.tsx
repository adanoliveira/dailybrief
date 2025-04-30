import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { LogoHorizontal } from "@/components/ui/logo"

export default function VerifyRequestPage() {
  return (
    <div className="container flex flex-col items-center justify-center min-h-screen py-12">
      <div className="mb-8">
        <LogoHorizontal width={200} priority />
      </div>
      
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3">
          <CardTitle className="text-2xl font-bold text-center">Check your email</CardTitle>
          <CardDescription className="text-center">
            A sign in link has been sent to your email address.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border p-4 text-center">
            <p className="text-sm">
              The link will expire after 24 hours. If you don't see the email, check your spam folder.
            </p>
          </div>
        </CardContent>
        <CardFooter className="flex justify-center">
          <Button asChild>
            <Link className="bg-primary/10 hover:bg-primary/20 text-primary px-4 py-2 rounded-md" href="/auth">Back to Sign In</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
} 