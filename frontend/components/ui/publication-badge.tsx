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
    container: "h-5 w-5 md:h-6 md:w-6",
    image: "h-3.5 w-3.5 md:h-4 md:w-4",
    text: "text-sm md:text-base font-semibold",
    gap: "gap-1.5 md:gap-2"
  },
  md: {
    container: "h-6 w-6 md:h-7 md:w-7",
    image: "h-4.5 w-4.5 md:h-5 md:w-5", 
    text: "text-base md:text-lg font-semibold",
    gap: "gap-2 md:gap-2.5"
  },
  lg: {
    container: "h-7 w-7 md:h-8 md:w-8 lg:h-9 lg:w-9",
    image: "h-5.5 w-5.5 md:h-6 md:w-6 lg:h-7 lg:w-7",
    text: "text-lg md:text-xl lg:text-2xl font-semibold", 
    gap: "gap-2 md:gap-2.5 lg:gap-3"
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