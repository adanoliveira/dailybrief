"use client"

import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { useState } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"

// Full list of regions from the specs
const regions = [
  { code: "ae", name: "United Arab Emirates" },
  { code: "ar", name: "Argentina" },
  { code: "at", name: "Austria" },
  { code: "au", name: "Australia" },
  { code: "be", name: "Belgium" },
  { code: "bg", name: "Bulgaria" },
  { code: "br", name: "Brazil" },
  { code: "ca", name: "Canada" },
  { code: "ch", name: "Switzerland" },
  { code: "cn", name: "China" },
  { code: "co", name: "Colombia" },
  { code: "cu", name: "Cuba" },
  { code: "cz", name: "Czech Republic" },
  { code: "de", name: "Germany" },
  { code: "eg", name: "Egypt" },
  { code: "fr", name: "France" },
  { code: "gb", name: "United Kingdom" },
  { code: "gr", name: "Greece" },
  { code: "hk", name: "Hong Kong" },
  { code: "hu", name: "Hungary" },
  { code: "id", name: "Indonesia" },
  { code: "ie", name: "Ireland" },
  { code: "il", name: "Israel" },
  { code: "in", name: "India" },
  { code: "it", name: "Italy" },
  { code: "jp", name: "Japan" },
  { code: "kr", name: "South Korea" },
  { code: "lt", name: "Lithuania" },
  { code: "lv", name: "Latvia" },
  { code: "ma", name: "Morocco" },
  { code: "mx", name: "Mexico" },
  { code: "my", name: "Malaysia" },
  { code: "ng", name: "Nigeria" },
  { code: "nl", name: "Netherlands" },
  { code: "no", name: "Norway" },
  { code: "nz", name: "New Zealand" },
  { code: "ph", name: "Philippines" },
  { code: "pl", name: "Poland" },
  { code: "pt", name: "Portugal" },
  { code: "ro", name: "Romania" },
  { code: "rs", name: "Serbia" },
  { code: "ru", name: "Russia" },
  { code: "sa", name: "Saudi Arabia" },
  { code: "se", name: "Sweden" },
  { code: "sg", name: "Singapore" },
  { code: "si", name: "Slovenia" },
  { code: "sk", name: "Slovakia" },
  { code: "th", name: "Thailand" },
  { code: "tr", name: "Turkey" },
  { code: "tw", name: "Taiwan" },
  { code: "ua", name: "Ukraine" },
  { code: "us", name: "United States" },
  { code: "ve", name: "Venezuela" },
  { code: "za", name: "South Africa" },
]

export function RegionPreferences() {
  const [searchTerm, setSearchTerm] = useState("")

  const filteredRegions = regions.filter(
    (region) =>
      region.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      region.code.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Select your region of interest (at least 1)</p>

      <div className="relative">
        <Input
          type="search"
          placeholder="Search regions..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="mb-4"
        />
      </div>

      <ScrollArea className="h-[300px] pr-4">
        <RadioGroup defaultValue="us">
          {filteredRegions.map((region) => (
            <div key={region.code} className="flex items-center space-x-2 py-2">
              <RadioGroupItem value={region.code} id={`region-${region.code}`} />
              <Label htmlFor={`region-${region.code}`}>
                {region.name} ({region.code.toUpperCase()})
              </Label>
            </div>
          ))}
        </RadioGroup>
      </ScrollArea>
    </div>
  )
}
