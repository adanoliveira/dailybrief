import * as React from "react"
import Image from "next/image"

interface LogoProps {
  width?: number
  height?: number
  className?: string
  priority?: boolean
}

// Cache-busting timestamp to force image reload
const cacheVersion = Date.now()

export function LogoHorizontal({ 
  width = 150, 
  height = 40, 
  className = "", 
  priority = false 
}: LogoProps) {
  return (
    <React.Fragment>
      <Image 
        src={`/logo-horizontal-black.svg?v=${cacheVersion}`}
        alt="DailyBrief"
        width={width}
        height={height}
        className={`dark:hidden ${className}`}
        priority={priority}
        unoptimized
      />
      <Image 
        src={`/logo-horizontal-white.svg?v=${cacheVersion}`}
        alt="DailyBrief"
        width={width}
        height={height}
        className={`hidden dark:block ${className}`}
        priority={priority}
        unoptimized
      />
    </React.Fragment>
  )
}

export function LogoIcon({ 
  width = 24, 
  height = 24, 
  className = "", 
  priority = false 
}: LogoProps) {
  return (
    <React.Fragment>
      <Image 
        src={`/logo-icon-black.svg?v=${cacheVersion}`}
        alt="DailyBrief"
        width={width}
        height={height}
        className={`dark:hidden ${className}`}
        priority={priority}
        unoptimized
      />
      <Image 
        src={`/logo-icon-white.svg?v=${cacheVersion}`}
        alt="DailyBrief"
        width={width}
        height={height}
        className={`hidden dark:block ${className}`}
        priority={priority}
        unoptimized
      />
    </React.Fragment>
  )
}

export function LogoFull({ 
  width = 240, 
  height = 60, 
  className = "", 
  priority = false 
}: LogoProps) {
  return (
    <React.Fragment>
      <Image 
        src={`/logo-horizontal-black.svg?v=${cacheVersion}`}
        alt="DailyBrief"
        width={width}
        height={height}
        className={`dark:hidden ${className}`}
        priority={priority}
        unoptimized
      />
      <Image 
        src={`/logo-horizontal-white.svg?v=${cacheVersion}`}
        alt="DailyBrief"
        width={width}
        height={height}
        className={`hidden dark:block ${className}`}
        priority={priority}
        unoptimized
      />
    </React.Fragment>
  )
} 