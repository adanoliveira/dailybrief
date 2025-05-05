"use client"

import { useState, useEffect } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { LogoHorizontal } from "@/components/ui/logo"
import { useToast } from "@/components/ui/use-toast"
import { useUser } from "@/lib/user-context"
import { useRouter } from "next/navigation"
import { useSession } from "next-auth/react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { FaSpinner } from "react-icons/fa"
import { Textarea } from "@/components/ui/textarea"
import apiClient from "@/lib/api-client"

const formSchema = z.object({
  timezone: z.string().optional(),
  interests: z.array(z.string()).min(1, {
    message: "Please select at least one interest.",
  }),
  custom_interests: z.string().optional(),
  news_sources: z.array(z.string()).min(1, {
    message: "Please select at least one source.",
  }),
  receive_daily_email: z.boolean().default(true),
  receive_notifications: z.boolean().default(true),
  preferred_language: z.string().default("en"),
})

type FormValues = z.infer<typeof formSchema>

const interests = [
  { id: "world", label: "World News" },
  { id: "technology", label: "Technology" },
  { id: "business", label: "Business" },
  { id: "science", label: "Science" },
  { id: "health", label: "Health" },
  { id: "sports", label: "Sports" },
  { id: "entertainment", label: "Entertainment" },
  { id: "politics", label: "Politics" },
]

const sources = [
  { id: "reuters", label: "Reuters" },
  { id: "ap", label: "Associated Press" },
  { id: "bbc", label: "BBC" },
  { id: "nyt", label: "New York Times" },
  { id: "guardian", label: "The Guardian" },
]

const languages = [
  { id: "en", label: "English" },
  { id: "es", label: "Spanish" },
  { id: "fr", label: "French" },
  { id: "de", label: "German" },
  { id: "pt", label: "Portuguese" },
]

export default function OnboardingPage() {
  const { userStatus, isLoading: isUserLoading, setOnboardingComplete } = useUser()
  const { data: session, status: sessionStatus } = useSession()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isRedirecting, setIsRedirecting] = useState(false)
  const router = useRouter()
  const { toast } = useToast()

  // Check if the user has already completed onboarding and redirect if necessary
  useEffect(() => {
    // Skip if already redirecting
    if (isRedirecting) return;

    // Check authentication first
    if (sessionStatus === "loading" || isUserLoading) {
      console.log("Onboarding page: Loading user data...");
      return;
    }

    if (sessionStatus === "unauthenticated") {
      console.log("Onboarding page: User not authenticated, redirecting to auth");
      setIsRedirecting(true);
      router.replace("/auth");
      return;
    }

    // Check onboarding status
    console.log("Onboarding page: Checking onboarding status", {
      sessionOnboarded: session?.user?.has_completed_onboarding,
      contextOnboarded: userStatus?.has_completed_onboarding
    });

    // If user has completed onboarding, redirect to home
    const hasCompletedOnboarding = 
      session?.user?.has_completed_onboarding === true || 
      userStatus?.has_completed_onboarding === true;

    if (hasCompletedOnboarding) {
      console.log("Onboarding page: User has already completed onboarding, redirecting to home");
      setIsRedirecting(true);
      router.replace("/home");
    }
  }, [session, sessionStatus, userStatus, isUserLoading, router, isRedirecting]);

  // Default form values including system timezone detection
  const defaultValues: Partial<FormValues> = {
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    interests: ["world", "technology"],
    custom_interests: "",
    news_sources: ["reuters", "bbc"],
    receive_daily_email: true,
    receive_notifications: true,
    preferred_language: "en",
  }

  // Initialize form with default values
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues,
  })

  // Handle form submission
  const onSubmit = async (values: FormValues) => {
    try {
      setIsSubmitting(true)
      setSubmitError(null)
      
      console.log("Submitting preferences:", values);
      
      // Send preferences to the API
      await apiClient.post("/api/accounts/preferences/", values)
      
      // Update onboarding status in context
      setOnboardingComplete(true)
      
      // Show success toast
      toast({
        title: "Preferences saved!",
        description: "You're all set up and ready to go.",
      })
      
      // Redirect to home
      router.replace("/home")
    } catch (error) {
      console.error("Failed to save preferences:", error)
      setSubmitError("Failed to save your preferences. Please try again.")
      setIsSubmitting(false)
    }
  }

  // Show loading state while checking auth or redirecting
  if (sessionStatus === "loading" || isUserLoading || isRedirecting) {
    return (
      <div className="container flex flex-col items-center justify-center min-h-screen py-12">
        <div className="mb-8">
          <LogoHorizontal width={200} priority />
        </div>
        <div className="w-full max-w-md text-center">
          <div className="flex justify-center my-8">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
          </div>
          <p className="text-muted-foreground">Getting things ready...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-10 max-w-4xl">
      <div className="flex justify-center mb-8">
        <LogoHorizontal width={160} priority />
      </div>
      
      <Card className="shadow-lg">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl">Welcome to DailyBrief</CardTitle>
          <CardDescription className="text-lg">
            Let's personalize your news experience
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {submitError && (
            <Alert variant="destructive" className="mb-6">
              <AlertDescription>{submitError}</AlertDescription>
            </Alert>
          )}
          
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <FormField
                control={form.control}
                name="interests"
                render={() => (
                  <FormItem>
                    <FormLabel className="text-base">What topics interest you?</FormLabel>
                    <FormDescription>
                      Select topics you'd like to see in your daily brief.
                    </FormDescription>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
                      {interests.map((item) => (
                        <FormField
                          key={item.id}
                          control={form.control}
                          name="interests"
                          render={({ field }) => {
                            return (
                              <FormItem
                                key={item.id}
                                className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4"
                              >
                                <FormControl>
                                  <Checkbox
                                    checked={field.value?.includes(item.id)}
                                    onCheckedChange={(checked) => {
                                      return checked
                                        ? field.onChange([...field.value, item.id])
                                        : field.onChange(
                                            field.value?.filter(
                                              (value) => value !== item.id
                                            )
                                          )
                                    }}
                                  />
                                </FormControl>
                                <FormLabel className="font-normal cursor-pointer">
                                  {item.label}
                                </FormLabel>
                              </FormItem>
                            )
                          }}
                        />
                      ))}
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="custom_interests"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Any specific interests not listed above?</FormLabel>
                    <FormDescription>
                      Separate multiple interests with commas (e.g., "Architecture, Coffee, Space Exploration")
                    </FormDescription>
                    <FormControl>
                      <Textarea
                        placeholder="Enter any custom interests..."
                        className="resize-none"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="news_sources"
                render={() => (
                  <FormItem>
                    <FormLabel className="text-base">Preferred news sources</FormLabel>
                    <FormDescription>
                      Select news sources you trust most.
                    </FormDescription>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-2">
                      {sources.map((source) => (
                        <FormField
                          key={source.id}
                          control={form.control}
                          name="news_sources"
                          render={({ field }) => {
                            return (
                              <FormItem
                                key={source.id}
                                className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4"
                              >
                                <FormControl>
                                  <Checkbox
                                    checked={field.value?.includes(source.id)}
                                    onCheckedChange={(checked) => {
                                      return checked
                                        ? field.onChange([...field.value, source.id])
                                        : field.onChange(
                                            field.value?.filter(
                                              (value) => value !== source.id
                                            )
                                          )
                                    }}
                                  />
                                </FormControl>
                                <FormLabel className="font-normal cursor-pointer">
                                  {source.label}
                                </FormLabel>
                              </FormItem>
                            )
                          }}
                        />
                      ))}
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="preferred_language"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Preferred Language</FormLabel>
                    <FormDescription>
                      Select your preferred language for news content.
                    </FormDescription>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      {...field}
                    >
                      {languages.map((lang) => (
                        <option key={lang.id} value={lang.id}>
                          {lang.label}
                        </option>
                      ))}
                    </select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="receive_daily_email"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel className="cursor-pointer">
                        Receive Daily Email Digest
                      </FormLabel>
                      <FormDescription>
                        Get a daily email with your personalized news summary.
                      </FormDescription>
                    </div>
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="receive_notifications"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel className="cursor-pointer">
                        Receive Browser Notifications
                      </FormLabel>
                      <FormDescription>
                        Get notified about important news based on your interests.
                      </FormDescription>
                    </div>
                  </FormItem>
                )}
              />
            </form>
          </Form>
        </CardContent>
        
        <CardFooter className="flex justify-end gap-4">
          <Button
            type="submit"
            size="lg"
            onClick={form.handleSubmit(onSubmit)}
            disabled={isSubmitting}
            className="w-full md:w-auto"
          >
            {isSubmitting ? (
              <>
                <FaSpinner className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              "Complete Setup"
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}