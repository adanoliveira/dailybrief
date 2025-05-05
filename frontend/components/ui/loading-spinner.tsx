import { cn } from "@/lib/utils"

type SpinnerSize = "sm" | "md" | "lg"

const sizeClasses: Record<SpinnerSize, string> = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-8 w-8 border-3",
}

interface LoadingSpinnerProps {
  size?: SpinnerSize
  className?: string
}

export function LoadingSpinner({ size = "md", className }: LoadingSpinnerProps) {
  return (
    <div
      className={cn(
        "animate-spin rounded-full border-solid border-primary border-t-transparent",
        sizeClasses[size],
        className
      )}
      aria-hidden="true"
    />
  )
} 