import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Filter, Search } from "lucide-react"
import Link from "next/link"

export function WorldNewsFeed() {
  return (
    <section id="world-news" className="container py-8 md:py-12">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 className="text-2xl font-bold tracking-tight">Top Headlines</h2>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative w-full sm:w-[260px]">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input type="search" placeholder="Search articles..." className="w-full pl-8" />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
              <span className="sr-only">Filter</span>
            </Button>
          </div>
        </div>

        <Tabs defaultValue="all">
          <TabsList className="mb-4 overflow-auto py-1 w-full justify-start">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="business">Business</TabsTrigger>
            <TabsTrigger value="technology">Technology</TabsTrigger>
            <TabsTrigger value="science">Science</TabsTrigger>
            <TabsTrigger value="health">Health</TabsTrigger>
            <TabsTrigger value="entertainment">Entertainment</TabsTrigger>
            <TabsTrigger value="sports">Sports</TabsTrigger>
          </TabsList>
          <TabsContent value="all" className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <NewsCard key={i} />
            ))}
          </TabsContent>
        </Tabs>
      </div>
    </section>
  )
}

function NewsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="line-clamp-2">
          <Link href="/article/1" className="hover:underline">
            Major Tech Company Announces Revolutionary AI Assistant
          </Link>
        </CardTitle>
        <CardDescription className="flex items-center gap-2 text-xs">
          <span>TechNews</span>
          <span>•</span>
          <span>2 hours ago</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-3">
          The new AI assistant promises to revolutionize how users interact with technology, offering unprecedented
          natural language understanding and task automation capabilities.
        </p>
      </CardContent>
      <CardFooter>
        <Link href="/article/1">
          <Button variant="ghost" size="sm">
            Read more
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}
