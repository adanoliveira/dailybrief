"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

const topics = ["Business", "Entertainment", "General", "Health", "Science", "Sports", "Technology"]

export function TopicsPreferences() {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Select topics you're interested in (at least 1)</p>
      <div className="grid grid-cols-2 gap-4">
        {topics.map((topic) => (
          <div key={topic} className="flex items-center space-x-2">
            <Checkbox id={`topic-${topic}`} defaultChecked={["Business", "Technology", "Science"].includes(topic)} />
            <Label htmlFor={`topic-${topic}`}>{topic}</Label>
          </div>
        ))}
      </div>
    </div>
  )
}
