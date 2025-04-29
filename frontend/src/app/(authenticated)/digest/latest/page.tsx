import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ArrowLeft, ExternalLink } from "lucide-react"
import Link from "next/link"

export default function LatestDigest() {
  return (
    <div className="container py-6 max-w-3xl">
      <div className="space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Link href="/home">
            <Button variant="ghost" size="sm" className="gap-1">
              <ArrowLeft className="h-4 w-4" />
              Back to feed
            </Button>
          </Link>
        </div>

        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            <span>Daily Brief</span>
            <span>•</span>
            <span>April 28, 2025</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl">Your Daily News Digest</h1>
          <p className="text-muted-foreground mt-2">A summary of the most important stories based on your interests</p>
        </div>

        <div className="space-y-8">
          <DigestSection
            title="Technology"
            articles={[
              {
                title: "Major Tech Company Announces Revolutionary AI Assistant",
                summary:
                  "A leading tech company has unveiled a new AI assistant with unprecedented natural language capabilities, potentially disrupting multiple sectors.",
                source: "TechNews",
                link: "/article/1",
              },
              {
                title: "Quantum Computing Breakthrough Promises Faster Processing",
                summary:
                  "Researchers have achieved a significant milestone in quantum computing stability, bringing practical applications closer to reality.",
                source: "Science Daily",
                link: "/article/2",
              },
            ]}
          />

          <Separator />

          <DigestSection
            title="Business"
            articles={[
              {
                title: "Global Markets React to New Economic Policy",
                summary:
                  "Stock markets worldwide showed mixed reactions to the announcement of a major economic policy shift by one of the world's largest economies.",
                source: "Financial Times",
                link: "/article/3",
              },
              {
                title: "Startup Secures Record Funding for Sustainable Energy Solution",
                summary:
                  "A clean energy startup has secured the largest Series A funding round in the sector's history for its innovative carbon capture technology.",
                source: "Business Insider",
                link: "/article/4",
              },
            ]}
          />

          <Separator />

          <DigestSection
            title="Health"
            articles={[
              {
                title: "New Research Suggests Link Between Diet and Longevity",
                summary:
                  "A comprehensive 20-year study has revealed significant correlations between specific dietary patterns and increased lifespan.",
                source: "Health Journal",
                link: "/article/5",
              },
            ]}
          />
        </div>

        <div className="flex justify-between pt-4">
          <Link href="/digest/archive">
            <Button variant="outline">View past digests</Button>
          </Link>
          <Link href="/home">
            <Button variant="default">Back to feed</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

interface DigestSectionProps {
  title: string
  articles: {
    title: string
    summary: string
    source: string
    link: string
  }[]
}

function DigestSection({ title, articles }: DigestSectionProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">{title}</h2>
      <div className="space-y-4">
        {articles.map((article, index) => (
          <Card key={index}>
            <CardContent className="p-4">
              <h3 className="font-semibold mb-2">
                <Link href={article.link} className="hover:underline">
                  {article.title}
                </Link>
              </h3>
              <p className="text-sm text-muted-foreground mb-3">{article.summary}</p>
              <div className="flex justify-between items-center">
                <span className="text-xs text-muted-foreground">{article.source}</span>
                <Link href={article.link}>
                  <Button variant="ghost" size="sm" className="h-7 gap-1">
                    Read more
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
