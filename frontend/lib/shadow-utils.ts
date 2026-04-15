import { cn } from "@/lib/utils"

/**
 * Shadow patterns for consistent light/dark mode shadows across the app
 * Light mode: Traditional dark shadows for depth
 * Dark mode: Light shadows for contrast and visibility
 * Note: Dark mode shadows need higher opacity than light mode but balanced for subtlety
 */
export const shadowPatterns = {
  // Small shadows for subtle elements
  sm: () => cn(
    "shadow-sm",
    "dark:shadow-white/8"
  ),

  // Default shadows for cards, buttons, etc.
  default: () => cn(
    "shadow-md",
    "dark:shadow-white/12"
  ),

  // Medium shadows for elevated elements
  md: () => cn(
    "shadow-md",
    "dark:shadow-white/15"
  ),

  // Large shadows for prominent elements
  lg: () => cn(
    "shadow-lg",
    "dark:shadow-white/18 dark:shadow-lg"
  ),

  // Extra large shadows for floating elements
  xl: () => cn(
    "shadow-xl",
    "dark:shadow-white/22 dark:shadow-xl"
  ),

  // Special patterns for specific components
  card: () => cn(
    "shadow-sm",
    "dark:shadow-white/10"
  ),

  button: () => cn(
    "shadow-sm hover:shadow-md",
    "dark:shadow-white/6 dark:hover:shadow-white/15"
  ),

  floating: () => cn(
    "shadow-lg hover:shadow-xl",
    "dark:shadow-white/15 dark:hover:shadow-white/20 dark:shadow-lg dark:hover:shadow-xl"
  ),

  dropdown: () => cn(
    "shadow-lg",
    "dark:shadow-white/18 dark:shadow-lg"
  ),

  modal: () => cn(
    "shadow-2xl",
    "dark:shadow-white/25 dark:shadow-2xl"
  )
}

/**
 * Utility function to apply shadow patterns with custom classes
 */
export const withShadow = (pattern: keyof typeof shadowPatterns, customClasses?: string) => {
  return cn(shadowPatterns[pattern](), customClasses)
} 