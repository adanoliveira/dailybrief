"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { useRouter, useSearchParams } from "next/navigation"
import { useUser } from "@/lib/user-context"
import apiClient from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { Loader2 } from "lucide-react"

// Form schema using zod
const onboardingSchema = z.object({
  news_preference: z.enum(["all", "tech", "business", "science", "general"], {
    required_error: "Please select a news preference",
  }),
  digest_time: z.enum(["morning", "afternoon", "evening"], {
    required_error: "Please select a digest time",
  }),
  subscribed_to_digest: z.boolean().default(true),
})

type OnboardingFormValues = z.infer<typeof onboardingSchema>

const defaultValues: Partial<OnboardingFormValues> = {
  news_preference: "tech",
  digest_time: "morning",
  subscribed_to_digest: true,
}

export default function OnboardingPage() {
  const { data: session } = useSession()
  const { userStatus, setOnboardingComplete } = useUser()
  const router = useRouter()
  const searchParams = useSearchParams()
  const skipCheck = searchParams?.get("skip_check") === "true"
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Check if user has already completed onboarding
  useEffect(() => {
    if (skipCheck) {
      setIsLoading(false)
      return
    }

    // First check from context
    if (userStatus?.has_completed_onboarding) {
      console.log("Onboarding: User has already completed onboarding (context), redirecting to home")
      router.replace("/home")
      return
    }

    // Fallback to localStorage
    const hasDoneOnboarding = localStorage.getItem("has_completed_onboarding") === "true"
    if (hasDoneOnboarding) {
      console.log("Onboarding: User has already completed onboarding (localStorage), redirecting to home")
      router.replace("/home")
      return
    }

    setIsLoading(false)
  }, [router, userStatus, skipCheck])

  // Initialize form
  const form = useForm<OnboardingFormValues>({
    resolver: zodResolver(onboardingSchema),
    defaultValues,
  })

  // Handle form submission
  const handleSubmit = async (data: OnboardingFormValues) => {
    if (!session?.user?.django_token) {
      setError("You must be logged in to complete onboarding")
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      // Send preferences to API
      await apiClient.post("/api/accounts/onboarding/complete/", {
        preferences: {
          news_preference: data.news_preference,
          digest_time: data.digest_time,
          subscribed_to_digest: data.subscribed_to_digest,
        },
      })

      // Update status locally
      setOnboardingComplete(true)
      
      // Redirect to home
      router.replace("/home?onboarding_complete=true")
    } catch (err) {
      console.error("Error completing onboarding:", err)
      setError("Failed to complete onboarding. Please try again.")
      setIsSubmitting(false)
    }
  }

  // Show loading state while checking onboarding status
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="container max-w-md py-10">
      <div className="mb-8 flex justify-center">
        <div className="flex items-center text-xl font-bold">
          <Loader2 className="mr-2 h-6 w-6 text-primary" />
          DailyBrief
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Welcome to DailyBrief</CardTitle>
          <CardDescription>
            Let's get your news feed set up. You can always change these settings later.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="news_preference"
                render={({ field }) => (
                  <FormItem className="space-y-3">
                    <FormLabel>What news interests you most?</FormLabel>
                    <FormControl>
                      <RadioGroup
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                        className="space-y-1"
                      >
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="tech" id="tech" />
                          <Label htmlFor="tech">Technology</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="business" id="business" />
                          <Label htmlFor="business">Business</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="science" id="science" />
                          <Label htmlFor="science">Science</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="general" id="general" />
                          <Label htmlFor="general">General News</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="all" id="all" />
                          <Label htmlFor="all">All Categories</Label>
                        </div>
                      </RadioGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="digest_time"
                render={({ field }) => (
                  <FormItem className="space-y-3">
                    <FormLabel>When would you like to receive your daily digest?</FormLabel>
                    <FormControl>
                      <RadioGroup
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                        className="space-y-1"
                      >
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="morning" id="morning" />
                          <Label htmlFor="morning">Morning (8:00 AM)</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="afternoon" id="afternoon" />
                          <Label htmlFor="afternoon">Afternoon (12:00 PM)</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="evening" id="evening" />
                          <Label htmlFor="evening">Evening (6:00 PM)</Label>
                        </div>
                      </RadioGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="subscribed_to_digest"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel>
                        Email me a daily digest
                      </FormLabel>
                      <FormDescription>
                        Get a summary of yesterday's top news in your inbox.
                      </FormDescription>
                    </div>
                  </FormItem>
                )}
              />

              {error && (
                <div className="rounded bg-destructive/15 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Setting up your feed...
                  </>
                ) : (
                  "Continue to DailyBrief"
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex justify-center border-t p-4">
          <p className="text-xs text-muted-foreground">
            You can always update your preferences later in settings.
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
