import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Filter, Search } from "lucide-react"
import Link from "next/link"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export default function World() {
  return (
    <div className="container py-6">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h1 className="text-2xl font-bold tracking-tight">World Headlines</h1>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative w-full sm:w-[260px]">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input type="search" placeholder="Search articles..." className="w-full pl-8" />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
              <span className="sr-only">Filter</span>
            </Button>
            <Select defaultValue="us">
              <SelectTrigger className="w-[100px]">
                <SelectValue placeholder="Region" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="us">US</SelectItem>
                <SelectItem value="gb">UK</SelectItem>
                <SelectItem value="ca">Canada</SelectItem>
                <SelectItem value="au">Australia</SelectItem>
                <SelectItem value="in">India</SelectItem>
              </SelectContent>
            </Select>
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
    </div>
  )
}

function NewsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="line-clamp-2">
          <Link href="/article/1" className="hover:underline">
            Global Summit Addresses Climate Change Initiatives
          </Link>
        </CardTitle>
        <CardDescription className="flex items-center gap-2 text-xs">
          <span>World News</span>
          <span>•</span>
          <span>3 hours ago</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-3">
          World leaders gathered to discuss ambitious new targets for reducing carbon emissions and funding renewable
          energy projects in developing nations.
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
