import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ExternalLink } from "lucide-react"
import Link from "next/link"

export default function Article({ params }: { params: { id: string } }) {
  return (
    <div className="container py-6 max-w-3xl">
      <div className="space-y-6">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            <span>Technology</span>
            <span>•</span>
            <span>April 28, 2025</span>
            <span>•</span>
            <span>TechNews</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
            Major Tech Company Announces Revolutionary AI Assistant
          </h1>
        </div>

        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-4">
            <h2 className="font-semibold mb-2">AI-Generated Abstract</h2>
            <p className="text-sm">
              A leading tech company has unveiled a new AI assistant that represents a significant leap in natural
              language processing capabilities. The assistant can understand complex queries, perform multi-step tasks,
              and learn from user interactions to improve over time. Industry analysts predict this could reshape how
              consumers and businesses interact with technology, potentially disrupting multiple sectors including
              customer service, education, and healthcare. The company plans a phased rollout starting next month with
              enterprise customers.
            </p>
          </CardContent>
        </Card>

        <div className="prose max-w-none">
          <p>
            In a highly anticipated announcement today, one of the world's leading technology companies revealed what
            they're calling "the next generation of AI assistants," promising capabilities far beyond what's currently
            available in the market.
          </p>

          <p>
            The new assistant, which will be available both as a standalone device and integrated into the company's
            existing ecosystem of products, features unprecedented natural language understanding and processing
            capabilities.
          </p>

          <p>
            "We've completely reimagined what an AI assistant can do," said the company's CEO during the announcement.
            "This isn't just an incremental improvement—it's a fundamental shift in how humans can interact with
            technology."
          </p>

          <p>
            According to the company, the assistant can understand complex, multi-part questions, remember context from
            previous conversations, and even anticipate user needs based on patterns and preferences it learns over
            time.
          </p>

          <p>
            Industry analysts are already speculating about the potential impact of this technology across various
            sectors, from customer service to healthcare and education.
          </p>

          <p>
            "If it works as advertised, this could be a game-changer," said Dr. Sarah Chen, a leading AI researcher not
            affiliated with the company. "The ability to have truly natural conversations with AI has been something of
            a holy grail in the field."
          </p>

          <p>
            The company plans to begin rolling out the new assistant to enterprise customers next month, with consumer
            availability scheduled for later this year.
          </p>
        </div>

        <div className="flex justify-center pt-4">
          <Link href="https://example.com/full-article" target="_blank" rel="noopener noreferrer">
            <Button className="gap-2">
              Read the full article
              <ExternalLink className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
