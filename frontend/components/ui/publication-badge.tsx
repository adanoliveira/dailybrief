"use client"

import { cn } from "@/lib/utils"

interface PublicationBadgeProps {
  source: {
    name: string;
    logoUrl?: string;
  };
  size?: "sm" | "md" | "lg";
  className?: string;
  variant?: "default" | "overlay";
}

const sizeVariants = {
  sm: {
    container: "w-[1.3em] h-[1.3em]", 
    image: "w-[1.3em] h-[1.3em]", 
    text: "font-semibold",
    gap: "gap-[0.5em]" // 0.5x the text size
  },
  md: {
    container: "w-[1.5em] h-[1.5em]", 
    image: "w-[1.5em] h-[1.5em]",
    text: "font-semibold",
    gap: "gap-[0.5em]"
  },
  lg: {
    container: "w-[1.5em] h-[1.5em]", 
    image: "w-[1.5em] h-[1.5em]",
    text: "text-xl md:text-2xl lg:text-2xl font-semibold", 
    gap: "gap-[0.5em]"
  }
}

export function PublicationBadge({ source, size = "md", className, variant = "default" }: PublicationBadgeProps) {
  const sizeVariant = sizeVariants[size];
  const isOverlay = variant === "overlay";

  if (source.logoUrl) {
    return (
      <div className={cn(
        "inline-flex items-center", 
        sizeVariant.gap, 
        className
      )}>
        <div className={cn(
          "rounded-full flex items-center justify-center shrink-0 bg-white",
          sizeVariant.container,
          isOverlay 
            ? "ring-2 ring-white/20" 
            : "ring-1 ring-border/50"
        )}>
          <img 
            src={source.logoUrl} 
            alt={source.name}
            className={cn(
              "rounded-full object-cover",
              sizeVariant.image
            )}
            onError={(e) => {
              // Hide the image on error and show just the name
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        </div>
        
        <span className={cn(
          sizeVariant.text,
          "leading-none"
        )}>
          {source.name}
        </span>
      </div>
    );
  }

  return (
    <span className={cn(sizeVariant.text, "leading-none", className)}>
      {source.name}
    </span>
  );
} 