"use client"

import { useState, useEffect } from "react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { LogOut, Settings, User, Edit, Sun, Moon, Loader2 } from "lucide-react"
import { signOut } from "next-auth/react"
import { deleteCookie } from "@/lib/cookies"
import { getUserPreferences, fetchOnboardingOptions } from "@/lib/onboarding-service"
import type { UserPreferences, OnboardingOptions } from "@/lib/onboarding-service"
import { PreferencesEditModal } from "@/components/preferences-edit-modal"

export default function Profile() {
  const [preferencesEditOpen, setPreferencesEditOpen] = useState(false)
  const { theme, setTheme } = useTheme()
  const [isSigningOut, setIsSigningOut] = useState(false)
  
  // Preferences state
  const [userPreferences, setUserPreferences] = useState<UserPreferences | null>(null)
  const [onboardingOptions, setOnboardingOptions] = useState<OnboardingOptions | null>(null)
  const [isLoadingPreferences, setIsLoadingPreferences] = useState(true)
  const [preferencesError, setPreferencesError] = useState<string | null>(null)

  // Load user preferences and options
  useEffect(() => {
    const loadUserData = async () => {
      try {
        setIsLoadingPreferences(true)
        setPreferencesError(null)
        
        // Load both preferences and options in parallel
        const [preferences, options] = await Promise.all([
          getUserPreferences(),
          fetchOnboardingOptions()
        ])
        
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
    
    loadUserData()
  }, [])

  // Handle preferences update
  const handlePreferencesUpdated = (newPreferences: UserPreferences) => {
    setUserPreferences(newPreferences)
  }

  const handleSignOut = async () => {
    try {
      setIsSigningOut(true)
      // Delete the onboarding cookie to ensure the user goes through onboarding again if they sign back in
      deleteCookie("onboarding_completed")
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
                    disabled={isLoadingPreferences}
                  >
                    <Edit className="h-4 w-4" />
                    Edit
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingPreferences ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin mr-2" />
                    <span className="text-muted-foreground">Loading your preferences...</span>
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
