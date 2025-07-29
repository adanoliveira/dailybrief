"use client"

import { useState, useEffect } from "react"
import { useTheme } from "next-themes"
import { useSession } from "next-auth/react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { LogOut, Settings, User, Edit, Sun, Moon, Loader2 } from "lucide-react"
import { signOut } from "next-auth/react"
import { getUserPreferences, fetchOnboardingOptions } from "@/lib/onboarding-service"
import type { UserPreferences, OnboardingOptions } from "@/lib/onboarding-service"
import { PreferencesEditModal } from "@/components/preferences-edit-modal"
import { useToast } from "@/components/ui/use-toast"
import { dataManager } from "@/lib/data-manager"

export default function Profile() {
  const [preferencesEditOpen, setPreferencesEditOpen] = useState(false)
  const { theme, setTheme } = useTheme()
  const [isSigningOut, setIsSigningOut] = useState(false)
  const { toast } = useToast()
  const { data: session } = useSession()
  
  // Preferences state
  const [userPreferences, setUserPreferences] = useState<UserPreferences | null>(null)
  const [onboardingOptions, setOnboardingOptions] = useState<OnboardingOptions | null>(null)
  const [isLoadingPreferences, setIsLoadingPreferences] = useState(true)
  const [preferencesError, setPreferencesError] = useState<string | null>(null)
  const [isRefreshingPreferences, setIsRefreshingPreferences] = useState(false)

  // Load user preferences and options
  useEffect(() => {
    loadUserData()
  }, [])

  // Function to reload user data
  const loadUserData = async (forceRefresh: boolean = false) => {
    try {
      setIsLoadingPreferences(true)
      setPreferencesError(null)
      
      console.log(`📡 Loading user data (forceRefresh: ${forceRefresh})...`)
      
      // Load both preferences and options in parallel
      const [preferences, options] = await Promise.all([
        getUserPreferences(forceRefresh),
        fetchOnboardingOptions()
      ])
      
      console.log("📥 Received preferences from API:", preferences)
      console.log("📋 Received options from API:", options ? "✅ Options loaded" : "❌ No options")
      
      setUserPreferences(preferences)
      setOnboardingOptions(options)
      
      if (!preferences) {
        setPreferencesError("No preferences found. Please complete your setup.")
      }
    } catch (error) {
      console.error("Failed to load user data:", error)
      setPreferencesError("Failed to load your preferences. Please try again.")
    } finally {
      setIsLoadingPreferences(false)
    }
  }

  // Handle preferences update - reload fresh data from server
  const handlePreferencesUpdated = async (newPreferences: UserPreferences) => {
    console.log("🔄 Preferences updated, refreshing profile data...")
    console.log("📥 New preferences received:", newPreferences)
    
    try {
      setIsRefreshingPreferences(true)
      
      // Update local state immediately for better UX
      setUserPreferences(newPreferences)
      console.log("✅ Local state updated")
      
      // Give the backend a moment to process the save before reloading
      await new Promise(resolve => setTimeout(resolve, 500))
      console.log("⏱️ Waited 500ms for backend processing")
      
      // Reload fresh data from server with cache bypass
      console.log("🌐 Fetching fresh data from server with forceRefresh=true...")
      await loadUserData(true) // Force refresh to bypass API cache
      console.log("✅ Fresh data loaded successfully")
      
      // Show success message
      toast({
        title: "Preferences saved!",
        description: "Your news preferences have been updated successfully.",
        duration: 3000,
      })
      
      console.log("🎉 Profile data refreshed successfully")
    } catch (error) {
      console.error("❌ Failed to refresh profile data after preferences update:", error)
      
      // Show error message
      toast({
        title: "Preferences saved",
        description: "Your preferences were saved, but there was an issue refreshing the display. Please refresh the page.",
        variant: "default",
        duration: 5000,
      })
    } finally {
      setIsRefreshingPreferences(false)
    }
  }

  const handleSignOut = async () => {
    try {
      setIsSigningOut(true)
      
      // Clear session establishment marker for fresh sign-in detection next time
      sessionStorage.removeItem('user-session-established')
      
      // Clear any saved scroll positions for fresh start
      const feedTypes = ['personalized:for-you', 'world:all', 'personalized:', 'world:']
      feedTypes.forEach(feedKey => {
        sessionStorage.removeItem(`scroll-${feedKey}::relevance`)
        sessionStorage.removeItem(`scroll-restored-${feedKey}::relevance`)
      })
      
      // Sign out using NextAuth
      await signOut({ callbackUrl: "/auth" })
    } catch (error) {
      console.error("Error signing out:", error)
      setIsSigningOut(false)
    }
  }

  // Helper functions to format preferences for display
  const getTopicNames = () => {
    if (!userPreferences?.topics_details) {
      return userPreferences?.topics?.length ? `${userPreferences.topics.length} topics selected` : "No topics selected"
    }
    const names = userPreferences.topics_details.map((t: {id: number, name: string, slug: string}) => t.name)
    if (names.length <= 3) {
      return names.join(", ")
    }
    return `${names.slice(0, 3).join(", ")} +${names.length - 3} more`
  }

  const getRegionNames = () => {
    if (!userPreferences?.regions || !onboardingOptions?.regions) {
      return userPreferences?.regions?.length ? `${userPreferences.regions.length} regions selected` : "No regions selected"
    }
    const names = userPreferences.regions
      .map((code: string) => onboardingOptions.regions.find(r => r.code === code)?.name || code)
      .filter(Boolean)
    if (names.length <= 3) {
      return names.join(", ")
    }
    return `${names.slice(0, 3).join(", ")} +${names.length - 3} more`
  }

  const getLanguageNames = () => {
    if (!userPreferences?.languages || !onboardingOptions?.languages) {
      return userPreferences?.languages?.length ? `${userPreferences.languages.length} languages selected` : "No languages selected"
    }
    const names = userPreferences.languages
      .map((code: string) => onboardingOptions.languages.find(l => l.iso_code === code)?.name || code)
      .filter(Boolean)
    if (names.length <= 3) {
      return names.join(", ")
    }
    return `${names.slice(0, 3).join(", ")} +${names.length - 3} more`
  }

  const getPublicationNames = () => {
    if (!userPreferences?.publications || !onboardingOptions?.publications) {
      return userPreferences?.publications?.length ? `${userPreferences.publications.length} sources selected` : "No sources selected"
    }
    const names = userPreferences.publications
      .map((id: number) => onboardingOptions.publications.find(p => p.id === id)?.name)
      .filter(Boolean)
    if (names.length <= 3) {
      return names.join(", ")
    }
    return `${names.slice(0, 3).join(", ")} +${names.length - 3} more`
  }

  return (
    <div className="container py-6">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
        </div>

        <Tabs defaultValue="preferences">
          <TabsList className="mb-4">
            <TabsTrigger value="preferences">
              <Settings className="h-4 w-4 mr-2" />
              Preferences
            </TabsTrigger>
            <TabsTrigger value="account">
              <User className="h-4 w-4 mr-2" />
              Account
            </TabsTrigger>
          </TabsList>

          <TabsContent value="preferences" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <CardTitle className="mb-2">News Preferences</CardTitle>
                    <CardDescription>Customize what news you see and how it's presented to you</CardDescription>
                  </div>
                  <Button 
                    onClick={() => setPreferencesEditOpen(true)} 
                    variant="outline"
                    size="sm"
                    className="gap-2"
                    disabled={isLoadingPreferences || isRefreshingPreferences}
                  >
                    <Edit className="h-4 w-4" />
                    {isRefreshingPreferences ? "Refreshing..." : "Edit"}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {(isLoadingPreferences || isRefreshingPreferences) ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin mr-2" />
                    <span className="text-muted-foreground">
                      {isRefreshingPreferences ? "Refreshing your preferences..." : "Loading your preferences..."}
                    </span>
                  </div>
                ) : preferencesError ? (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground mb-4">{preferencesError}</p>
                    <Button onClick={() => setPreferencesEditOpen(true)} className="gap-2">
                      <Settings className="h-4 w-4" />
                      Set Up Preferences
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="grid gap-6 md:grid-cols-2">
                      <Card className="border-0 shadow-none bg-muted/30">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                            <h3 className="font-medium text-sm">Topics</h3>
                            <Badge variant="outline" className="text-xs ml-auto">
                              {userPreferences?.topics?.length || 0}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {getTopicNames()}
                          </p>
                        </CardContent>
                      </Card>
                      
                      <Card className="border-0 shadow-none bg-muted/30">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 rounded-full bg-green-500"></div>
                            <h3 className="font-medium text-sm">Regions</h3>
                            <Badge variant="outline" className="text-xs ml-auto">
                              {userPreferences?.regions?.length || 0}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {getRegionNames()}
                          </p>
                        </CardContent>
                      </Card>
                      
                      <Card className="border-0 shadow-none bg-muted/30">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                            <h3 className="font-medium text-sm">Languages</h3>
                            <Badge variant="outline" className="text-xs ml-auto">
                              {userPreferences?.languages?.length || 0}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {getLanguageNames()}
                          </p>
                        </CardContent>
                      </Card>
                      
                      <Card className="border-0 shadow-none bg-muted/30">
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                            <h3 className="font-medium text-sm">News Sources</h3>
                            <Badge variant="outline" className="text-xs ml-auto">
                              {userPreferences?.publications?.length || 0}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {getPublicationNames()}
                          </p>
                        </CardContent>
                      </Card>
                    </div>
                    
                    {userPreferences && (
                      <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 rounded-lg border border-blue-200/50 dark:border-blue-800/50">
                        <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                          Preferences Active
                        </p>
                        <p className="text-xs text-blue-700 dark:text-blue-300">
                          Your feed is personalized based on these preferences. Use the Edit button above to make changes.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="mb-2">Reading Experience</CardTitle>
                <CardDescription>Customize how you read and interact with news</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Appearance</h3>
                    <p className="text-sm text-muted-foreground">Choose your preferred theme</p>
                  </div>
                  <Button 
                    variant="outline" 
                    onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                    className="gap-2"
                  >
                    {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                    {theme === "dark" ? "Light Mode" : "Dark Mode"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="account" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="mb-2">Account Information</CardTitle>
                <CardDescription>Your account details and settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h3 className="font-medium">Email</h3>
                  <div className="rounded-md border px-3 py-2 text-sm bg-muted/50">user@example.com</div>
                </div>
                <div className="space-y-2">
                  <h3 className="font-medium">Member since</h3>
                  <div className="rounded-md border px-3 py-2 text-sm bg-muted/50">April 15, 2025</div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="mb-2">Sign Out</CardTitle>
                <CardDescription>End your current session</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  You'll be redirected to the sign in page. Your preferences and data will be saved.
                </p>
              </CardContent>
              <CardFooter>
                <Button 
                  variant="destructive" 
                  className="gap-2"
                  onClick={handleSignOut}
                  disabled={isSigningOut}
                >
                  <LogOut className="h-4 w-4" />
                  {isSigningOut ? "Signing out..." : "Sign out"}
                </Button>
              </CardFooter>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      <PreferencesEditModal 
        open={preferencesEditOpen} 
        onOpenChange={setPreferencesEditOpen}
        currentPreferences={userPreferences}
        onPreferencesUpdated={handlePreferencesUpdated}
      />
    </div>
  )
}
