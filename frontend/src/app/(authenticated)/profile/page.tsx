"use client"

import { useState } from "react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LogOut, Settings, User, Edit, Sun, Moon } from "lucide-react"
import { PreferencesModal } from "@/components/preferences-modal"

export default function Profile() {
  const [preferencesOpen, setPreferencesOpen] = useState(false)
  const { theme, setTheme } = useTheme()

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
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>News Preferences</CardTitle>
                  <CardDescription>Manage your news feed preferences</CardDescription>
                </div>
                <Button onClick={() => setPreferencesOpen(true)} className="gap-2">
                  <Edit className="h-4 w-4" />
                  Edit Preferences
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium mb-1">Topics</h3>
                    <p className="text-sm text-muted-foreground">Business, Technology, Science</p>
                  </div>
                  <div>
                    <h3 className="font-medium mb-1">Region</h3>
                    <p className="text-sm text-muted-foreground">United States (US)</p>
                  </div>
                  <div>
                    <h3 className="font-medium mb-1">Publishers</h3>
                    <p className="text-sm text-muted-foreground">BBC News, Reuters</p>
                  </div>
                  <div>
                    <h3 className="font-medium mb-1">Languages</h3>
                    <p className="text-sm text-muted-foreground">English</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Reading Preferences</CardTitle>
                <CardDescription>Customize your reading experience</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Dark Mode</h3>
                    <p className="text-sm text-muted-foreground">Switch between light and dark mode</p>
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
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Text Size</h3>
                    <p className="text-sm text-muted-foreground">Adjust the size of article text</p>
                  </div>
                  <Button variant="outline">Adjust</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="account" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Account Information</CardTitle>
                <CardDescription>Manage your account details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h3 className="font-medium">Email</h3>
                  <div className="rounded-md border px-3 py-2 text-sm">user@example.com</div>
                </div>
                <div className="space-y-2">
                  <h3 className="font-medium">Account created</h3>
                  <div className="rounded-md border px-3 py-2 text-sm">April 15, 2025</div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Sign Out</CardTitle>
                <CardDescription>Sign out from your account</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  You will be redirected to the sign in page after signing out.
                </p>
              </CardContent>
              <CardFooter>
                <Button variant="destructive" className="gap-2">
                  <LogOut className="h-4 w-4" />
                  Sign out
                </Button>
              </CardFooter>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      <PreferencesModal open={preferencesOpen} onOpenChange={setPreferencesOpen} />
    </div>
  )
}
