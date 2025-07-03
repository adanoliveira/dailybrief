import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { DigestArchive } from "@/components/digest/digest-archive"

export default function DigestArchivePage() {
  return (
    <div className="container py-6 max-w-4xl">
      <div className="space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Link href="/home">
            <Button variant="ghost" size="sm" className="gap-1">
              <ArrowLeft className="h-4 w-4" />
              Back to feed
            </Button>
          </Link>
        </div>

        <DigestArchive />
      </div>
    </div>
  )
} 