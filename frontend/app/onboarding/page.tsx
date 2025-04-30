"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { setCookie } from "@/lib/cookies"

export default function Onboarding() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])

  const handleNext = () => {
    if (step < 4) {
      setStep(step + 1)
    } else {
      // Save preferences and mark onboarding as completed
      completeOnboarding()
      router.push("/home")
    }
  }

  const completeOnboarding = () => {
    // Set the onboarding_completed cookie
    setCookie("onboarding_completed", "true", 365) // Expires in 365 days
    
    // Here you would typically send the preferences to your API
    console.log("Onboarding completed with topics:", selectedTopics)
  }

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1)
    }
  }

  const handleTopicChange = (topic: string) => {
    setSelectedTopics((prev) => (prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]))
  }

  return (
    <div className="container flex items-center justify-center min-h-screen py-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Set up your news preferences</CardTitle>
          <CardDescription>
            Step {step} of 4: {step === 1 ? "Topics" : step === 2 ? "Region" : step === 3 ? "Publishers" : "Languages"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === 1 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">Select topics you're interested in (at least 1)</p>
              <div className="grid grid-cols-2 gap-4">
                {["Business", "Entertainment", "General", "Health", "Science", "Sports", "Technology"].map((topic) => (
                  <div key={topic} className="flex items-center space-x-2">
                    <Checkbox
                      id={topic}
                      checked={selectedTopics.includes(topic)}
                      onCheckedChange={() => handleTopicChange(topic)}
                    />
                    <Label htmlFor={topic}>{topic}</Label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">Select your region of interest (at least 1)</p>
              <RadioGroup defaultValue="us">
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="us" id="us" />
                  <Label htmlFor="us">United States</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="gb" id="gb" />
                  <Label htmlFor="gb">United Kingdom</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="ca" id="ca" />
                  <Label htmlFor="ca">Canada</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="au" id="au" />
                  <Label htmlFor="au">Australia</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="in" id="in" />
                  <Label htmlFor="in">India</Label>
                </div>
              </RadioGroup>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">Select publishers (optional)</p>
              <div className="grid gap-4">
                {["BBC News", "CNN", "The New York Times", "Reuters", "Associated Press"].map((publisher) => (
                  <div key={publisher} className="flex items-center space-x-2">
                    <Checkbox id={publisher} />
                    <Label htmlFor={publisher}>{publisher}</Label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">Select languages (up to 3)</p>
              <Select defaultValue="en">
                <SelectTrigger>
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                  <SelectItem value="it">Italian</SelectItem>
                </SelectContent>
              </Select>
              <div className="flex flex-wrap gap-2 pt-2">
                <div className="flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1 text-sm">
                  <span>English</span>
                  <button className="ml-1 rounded-full hover:bg-primary/20 p-1">×</button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={handleBack} disabled={step === 1}>
            Back
          </Button>
          <Button onClick={handleNext}>{step === 4 ? "Finish" : "Next"}</Button>
        </CardFooter>
      </Card>
    </div>
  )
}
