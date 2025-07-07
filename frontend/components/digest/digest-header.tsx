"use client"

import { cn } from "@/lib/utils"
import type { Digest } from "@/lib/digest-service"

interface DigestHeaderProps {
  digest: Digest;
}

export function DigestHeader({ digest }: DigestHeaderProps) {
  return (
    <div className="relative">
      {/* Title and date - both mobile and desktop */}
      <div className="space-y-2">
        <h1 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black text-foreground leading-tight">
          {digest.title}
        </h1>
        <p className="text-base md:text-lg text-muted-foreground">
          {new Date(digest.date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </p>
      </div>
    </div>
  );
} 