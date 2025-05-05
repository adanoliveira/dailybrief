"use client"

import { useState, useEffect } from "react"
import { signIn, useSession } from "next-auth/react"
import { Button, buttonVariants } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LogoHorizontal } from "@/components/ui/logo"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"
import { FaGoogle, FaApple } from "react-icons/fa"
import { cn } from "@/lib/utils"
import { useRouter } from "next/navigation"
import { useUser } from "@/lib/user-context"

// Rate limiting constants
const COOLDOWN_PERIOD_MS = 20000; // 20 seconds

export default function AuthPage() {
  const [isEmailSent, setIsEmailSent] = useState(false)
  const [email, setEmail] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cooldownRemaining, setCooldownRemaining] = useState(0)
  const [lastRequestTime, setLastRequestTime] = useState<number | null>(null)
  const [isRedirecting, setIsRedirecting] = useState(false)
  const { data: session, status: sessionStatus } = useSession()
  const { userStatus, isLoading: isUserLoading, refreshUserStatus } = useUser()
  const router = useRouter()

  // Redirect based on auth status - use direct approach rather than depending on SessionRedirect
  useEffect(() => {
    // Skip if we're already in the process of redirecting
    if (isRedirecting) return;

    // Only run when we have definitive session and user status info
    if (sessionStatus === "loading" || isUserLoading) {
      console.log("Auth page: Still loading session or user data...");
      return;
    }

    // If authenticated, check onboarding status and redirect
    if (sessionStatus === "authenticated" && session?.user) {
      console.log("Auth page: User authenticated with token. Checking onboarding status...");
      setIsRedirecting(true);
      
      // Check for onboarding status directly from session first
      if (session.user.has_completed_onboarding === true) {
        console.log("Auth page: Session indicates onboarding completed. Redirecting to home...");
        router.replace("/home");
        return;
      }
      
      // If we have user status from context, use it
      if (userStatus) {
        if (userStatus.has_completed_onboarding === true) {
          console.log("Auth page: Context indicates onboarding completed. Redirecting to home...");
          router.replace("/home");
        } else {
          console.log("Auth page: Context indicates onboarding not completed. Redirecting to onboarding...");
          router.replace("/onboarding");
        }
        return;
      }
      
      // If we don't have user status yet, refresh and then decide
      refreshUserStatus().then(refreshedStatus => {
        if (refreshedStatus?.has_completed_onboarding === true) {
          console.log("Auth page: Refreshed status indicates onboarding completed. Redirecting to home...");
          router.replace("/home");
        } else {
          console.log("Auth page: Refreshed status indicates onboarding not completed. Redirecting to onboarding...");
          router.replace("/onboarding");
        }
      }).catch(err => {
        console.error("Auth page: Failed to refresh user status", err);
        // Default to onboarding if we can't determine status
        router.replace("/onboarding");
      });
    }
  }, [sessionStatus, session, userStatus, isUserLoading, router, refreshUserStatus, isRedirecting]);

  useEffect(() => {
    // Check if there's a cooldown in localStorage
    const storedRequestTime = localStorage.getItem('lastMagicLinkRequest');
    if (storedRequestTime) {
      const lastTime = parseInt(storedRequestTime, 10);
      const now = Date.now();
      const elapsed = now - lastTime;
      
      if (elapsed < COOLDOWN_PERIOD_MS) {
        // Still in cooldown period
        setLastRequestTime(lastTime);
        setCooldownRemaining(Math.ceil((COOLDOWN_PERIOD_MS - elapsed) / 1000));
      }
    }
  }, []);

  // Countdown timer for cooldown
  useEffect(() => {
    if (cooldownRemaining <= 0) return;
    
    const timer = setTimeout(() => {
      setCooldownRemaining(prev => {
        if (prev <= 1) {
          setLastRequestTime(null);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearTimeout(timer);
  }, [cooldownRemaining]);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Clear any previous errors
    setError(null)
    
    // Check if email is valid
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address')
      return
    }
    
    // Check if we're in cooldown period
    if (cooldownRemaining > 0) {
      setError(`Please wait ${cooldownRemaining} seconds before requesting another link`)
      return
    }
    
    setIsSubmitting(true)
    
    try {
      // Use NextAuth to send the magic link
      const result = await signIn("email", { 
        email, 
        redirect: false,
      })
      
      if (result?.error) {
        throw new Error(result.error)
      }
      
      // Set cooldown
      const now = Date.now();
      localStorage.setItem('lastMagicLinkRequest', now.toString());
      setLastRequestTime(now);
      setCooldownRemaining(COOLDOWN_PERIOD_MS / 1000);
      
      setIsEmailSent(true)
    } catch (error) {
      console.error("Error sending magic link:", error)
      setError('Failed to send magic link. Please try again later.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleGoogleSignIn = async () => {
    await signIn("google", { redirect: false })
  }

  const handleAppleSignIn = async () => {
    await signIn("apple", { redirect: false })
  }

  // Show loading state if session is loading, user data is loading, or we're redirecting
  if (sessionStatus === "loading" || (sessionStatus === "authenticated" && (isUserLoading || isRedirecting))) {
    return (
      <div className="container flex flex-col items-center justify-center min-h-screen py-12">
        <div className="mb-8">
          <LogoHorizontal width={200} priority />
        </div>
        <div className="w-full max-w-md text-center">
          <div className="flex justify-center my-8">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
          </div>
          <p className="text-muted-foreground">Setting up your account...</p>
        </div>
      </div>
    )
  }

  // If authenticated but not yet redirected, show loading
  if (sessionStatus === "authenticated") {
    return (
      <div className="container flex flex-col items-center justify-center min-h-screen py-12">
        <div className="mb-8">
          <LogoHorizontal width={200} priority />
        </div>
        <div className="w-full max-w-md text-center">
          <div className="flex justify-center my-8">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
          </div>
          <p className="text-muted-foreground">Redirecting you to the right place...</p>
        </div>
      </div>
    )
  }

  // Show login UI for unauthenticated users
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

          {error && (
            <Alert variant="destructive" className="text-sm">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

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
              
              <Button 
                type="submit" 
                className="w-full"
                disabled={isSubmitting || cooldownRemaining > 0}
              >
                {isSubmitting 
                  ? "Sending..." 
                  : cooldownRemaining > 0 
                    ? `Wait ${cooldownRemaining}s` 
                    : "Continue with Email"}
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
                <p className="text-xs text-muted-foreground mt-2">
                  The link will expire in 5 minutes.
                </p>
              </div>
              <button 
                className={cn(buttonVariants({ variant: "outline" }), "w-full")}
                onClick={() => setIsEmailSent(false)}
                disabled={cooldownRemaining > 0}
              >
                {cooldownRemaining > 0 
                  ? `Try again in ${cooldownRemaining}s` 
                  : "Try another email"}
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 