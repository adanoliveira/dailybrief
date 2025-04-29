"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Check, Coffee, Newspaper } from "lucide-react"

interface Article {
  id: string
  title: string
  description: string
  source: {
    name: string
  }
  publishedAt: string
}

export function InfiniteNewsFeed() {
  const [articles, setArticles] = useState<Article[]>([])
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [reachedEnd, setReachedEnd] = useState(false)
  const observer = useRef<IntersectionObserver | null>(null)

  // Mock data for demonstration
  const mockArticles = [
    {
      id: "1",
      title: "Major Tech Company Announces Revolutionary AI Assistant",
      description:
        "The new AI assistant promises to revolutionize how users interact with technology, offering unprecedented natural language understanding and task automation capabilities.",
      source: { name: "TechNews" },
      publishedAt: "2 hours ago",
    },
    {
      id: "2",
      title: "Global Markets React to New Economic Policy",
      description:
        "Stock markets worldwide showed mixed reactions to the announcement of a major economic policy shift by one of the world's largest economies.",
      source: { name: "Financial Times" },
      publishedAt: "3 hours ago",
    },
    {
      id: "3",
      title: "Breakthrough in Renewable Energy Storage",
      description:
        "Scientists have developed a new type of battery that could solve one of the biggest challenges in renewable energy adoption.",
      source: { name: "Science Daily" },
      publishedAt: "5 hours ago",
    },
    {
      id: "4",
      title: "New Study Links Exercise to Improved Mental Health",
      description:
        "Researchers have found strong evidence that regular physical activity can significantly reduce symptoms of anxiety and depression.",
      source: { name: "Health Journal" },
      publishedAt: "6 hours ago",
    },
    {
      id: "5",
      title: "Film Festival Announces Award Winners",
      description:
        "The international film festival concluded yesterday with the announcement of this year's award winners, celebrating diverse storytelling from around the world.",
      source: { name: "Entertainment Weekly" },
      publishedAt: "8 hours ago",
    },
  ]

  // Function to load more articles
  const loadMoreArticles = useCallback(async () => {
    if (loading || !hasMore) return

    setLoading(true)

    // In a real app, this would be an API call
    // For now, we'll simulate with a timeout and mock data
    setTimeout(() => {
      // If we've loaded 3 pages, simulate reaching the end
      if (page >= 3) {
        setHasMore(false)
        setReachedEnd(true)
        setLoading(false)
        return
      }

      setArticles((prev) => [
        ...prev,
        ...mockArticles.map((article) => ({
          ...article,
          id: `${article.id}-${page}`,
        })),
      ])
      setPage((prev) => prev + 1)
      setLoading(false)
    }, 1000)
  }, [loading, hasMore, page])

  // Set up the intersection observer
  const lastArticleRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (loading) return

      if (observer.current) observer.current.disconnect()

      observer.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasMore) {
          loadMoreArticles()
        }
      })

      if (node) observer.current.observe(node)
    },
    [loading, hasMore, loadMoreArticles],
  )

  // Initial load
  useEffect(() => {
    setArticles(mockArticles)
  }, [])

  return (
    <div className="space-y-4">
      {articles.map((article, index) => {
        if (articles.length === index + 1) {
          return (
            <div ref={lastArticleRef} key={article.id}>
              <NewsCard article={article} />
            </div>
          )
        } else {
          return <NewsCard key={article.id} article={article} />
        }
      })}

      {loading && (
        <div className="flex justify-center py-4">
          <div className="animate-pulse flex space-x-2">
            <div className="rounded-full bg-muted h-2 w-2"></div>
            <div className="rounded-full bg-muted h-2 w-2"></div>
            <div className="rounded-full bg-muted h-2 w-2"></div>
          </div>
        </div>
      )}

      {reachedEnd && (
        <Card className="bg-primary/5 border-primary/20 text-center">
          <CardContent className="pt-6 pb-4">
            <div className="flex justify-center mb-4">
              <div className="bg-primary/10 p-3 rounded-full">
                <Check className="h-6 w-6 text-primary" />
              </div>
            </div>
            <h3 className="text-lg font-medium mb-2">You're all caught up!</h3>
            <p className="text-muted-foreground">
              You've read all the top stories for today. Enjoy the rest of your day!
            </p>
            <div className="flex justify-center mt-4 gap-2">
              <Coffee className="h-5 w-5 text-muted-foreground" />
              <Newspaper className="h-5 w-5 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

interface NewsCardProps {
  article: Article
}

function NewsCard({ article }: NewsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="line-clamp-2">
          <Link href={`/article/${article.id}`} className="hover:underline">
            {article.title}
          </Link>
        </CardTitle>
        <CardDescription className="flex items-center gap-2 text-xs">
          <span>{article.source.name}</span>
          <span>•</span>
          <span>{article.publishedAt}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-3">{article.description}</p>
      </CardContent>
      <CardFooter>
        <Link href={`/article/${article.id}`}>
          <Button variant="ghost" size="sm">
            Read more
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}
