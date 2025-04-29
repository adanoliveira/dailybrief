"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TopicsPreferences } from "@/components/preferences/topics-preferences"
import { RegionPreferences } from "@/components/preferences/region-preferences"
import { PublishersPreferences } from "@/components/preferences/publishers-preferences"
import { LanguagesPreferences } from "@/components/preferences/languages-preferences"

interface PreferencesModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function PreferencesModal({ open, onOpenChange }: PreferencesModalProps) {
  const [activeTab, setActiveTab] = useState("topics")

  const handleSave = () => {
    // In a real app, this would save the preferences to the backend
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit News Preferences</DialogTitle>
          <DialogDescription>Customize your news feed by selecting your preferences</DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-2">
          <TabsList className="grid grid-cols-4 mb-4">
            <TabsTrigger value="topics">Topics</TabsTrigger>
            <TabsTrigger value="region">Region</TabsTrigger>
            <TabsTrigger value="publishers">Publishers</TabsTrigger>
            <TabsTrigger value="languages">Languages</TabsTrigger>
          </TabsList>

          <TabsContent value="topics" className="mt-0">
            <TopicsPreferences />
          </TabsContent>

          <TabsContent value="region" className="mt-0">
            <RegionPreferences />
          </TabsContent>

          <TabsContent value="publishers" className="mt-0">
            <PublishersPreferences />
          </TabsContent>

          <TabsContent value="languages" className="mt-0">
            <LanguagesPreferences />
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave}>Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
