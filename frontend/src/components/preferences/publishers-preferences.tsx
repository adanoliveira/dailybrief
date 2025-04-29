"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { useState } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"

const publishers = [
  "BBC News",
  "CNN",
  "The New York Times",
  "Reuters",
  "Associated Press",
  "The Guardian",
  "The Washington Post",
  "Al Jazeera",
  "Bloomberg",
  "CNBC",
  "Financial Times",
  "The Economist",
  "Time",
  "Wired",
  "TechCrunch",
  "The Verge",
]

export function PublishersPreferences() {
  const [searchTerm, setSearchTerm] = useState("")

  const filteredPublishers = publishers.filter((publisher) =>
    publisher.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Select publishers you prefer (optional)</p>

      <div className="relative">
        <Input
          type="search"
          placeholder="Search publishers..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="mb-4"
        />
      </div>

      <ScrollArea className="h-[300px] pr-4">
        <div className="grid gap-4">
          {filteredPublishers.map((publisher) => (
            <div key={publisher} className="flex items-center space-x-2">
              <Checkbox id={`publisher-${publisher}`} defaultChecked={["BBC News", "Reuters"].includes(publisher)} />
              <Label htmlFor={`publisher-${publisher}`}>{publisher}</Label>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
