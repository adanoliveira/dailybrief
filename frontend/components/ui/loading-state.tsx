import { Loader2 } from "lucide-react"

interface LoadingStateProps {
  message?: string
  fullScreen?: boolean
}

export function LoadingState({ 
  message = "Loading...", 
  fullScreen = false 
}: LoadingStateProps) {
  const containerClasses = fullScreen 
    ? "fixed inset-0 flex flex-col items-center justify-center bg-background" 
    : "flex flex-col items-center justify-center py-8"

  return (
    <div className={containerClasses}>
      <div className="w-full max-w-md px-4 text-center">
        <div className="flex justify-center my-8">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
        </div>
        <p className="text-muted-foreground">{message}</p>
      </div>
    </div>
  )
} 