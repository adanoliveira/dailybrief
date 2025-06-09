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
    container: "h-5 w-5",
    image: "h-3.5 w-3.5",
    text: "text-sm font-semibold",
    gap: "gap-1.5"
  },
  md: {
    container: "h-6 w-6",
    image: "h-4.5 w-4.5", 
    text: "text-base font-semibold",
    gap: "gap-2"
  },
  lg: {
    container: "h-7 w-7",
    image: "h-5.5 w-5.5",
    text: "text-lg font-semibold", 
    gap: "gap-1.5"
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