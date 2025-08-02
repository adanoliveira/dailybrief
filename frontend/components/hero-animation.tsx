"use client"

export function HeroAnimation() {
  // Generate mobile-optimized dots - same sophisticated pattern as desktop
  const generateMobileDots = () => {
    const dots: Array<{ id: number; x: number; y: number; r: number; opacity: number }> = []
    
    const width = 320
    const height = 260
    const sectionWidth = width / 10 // 24px per section
    const dotSize = 3 // Slightly smaller for mobile
    
    let dotId = 0
    
        // Generate dots for sections 1-9 (section 10 handled separately)
    for (let section = 0; section < 9; section++) {
      const sectionStartX = section * sectionWidth
      const sectionEndX = (section + 1) * sectionWidth
      
      // Same density pattern as desktop but scaled for mobile
      const densityPercents = [100, 90, 75, 60, 45, 30, 20, 10, 5]
      const densityPercent = densityPercents[section]
    const maxDotsThisSection = Math.round((50 * densityPercent) / 100) // 25 max for mobile (vs 40 desktop)
    
          // Sections 6-9 (columns 6-9): More uniform distribution with decreasing noise
      if (section >= 5) {
        // Same minimal noise factors as desktop: 0.15, 0.1, 0.05, 0.03
        const noiseFactors = [0.15, 0.1, 0.05, 0.03]
        const noiseFactor = noiseFactors[section - 5] || 0.03
      
      for (let i = 0; i < maxDotsThisSection; i++) {
        // Calculate symmetrical vertical position
        const baseY = height * (i + 1) / (maxDotsThisSection + 1)
        
        // Add minimal noise to the base position
        const noiseY = (Math.random() - 0.5) * height * noiseFactor
        const finalY = Math.max(5, Math.min(height - 5, baseY + noiseY))
        
        // X position: centered for column 9, random for others
        let x
        if (section === 8) { // Column 9
          const baseX = sectionStartX + sectionWidth / 2
          const noiseX = (Math.random() - 0.5) * sectionWidth * 0.1
          x = baseX + noiseX
        } else {
          x = sectionStartX + Math.random() * sectionWidth
        }
        
        dots.push({
          id: dotId++,
          x: Math.max(sectionStartX + 1, Math.min(sectionEndX - 1, x)),
          y: finalY,
          r: dotSize,
          opacity: 1.0,
        })
      }
    } else {
      // Sections 1-5 (columns 1-5): Keep full random distribution
      for (let i = 0; i < maxDotsThisSection; i++) {
        const x = sectionStartX + Math.random() * sectionWidth
        const y = Math.random() * height
        
        dots.push({
          id: dotId++,
          x: Math.max(sectionStartX + 1, Math.min(sectionEndX - 1, x)),
          y: Math.max(1, Math.min(height - 1, y)),
          r: dotSize,
          opacity: 1.0,
        })
      }
    }
    }
    
    // Section 10 (Column 10): Single centered dot
    dots.push({
      id: dotId++,
      x: 9 * sectionWidth + sectionWidth / 2, // Center of section 10
      y: height / 2, // Vertically centered
      r: dotSize*1.5,
      opacity: 1.0,
    })
    
    return dots
  }

  // Generate desktop-optimized dots - 10 sections with decreasing density and chaos
  const generateDesktopDots = () => {
    const dots: Array<{ id: number; x: number; y: number; r: number; opacity: number }> = []
    
    const width = 240
    const height = 180
    const sectionWidth = width / 10 // 24px per section
    const dotSize = 2.5 // All dots same size (slightly larger for desktop)
    
    let dotId = 0
    
    // Generate dots for sections 1-9 (section 10 handled separately)
    for (let section = 0; section < 9; section++) {
      const sectionStartX = section * sectionWidth
      const sectionEndX = (section + 1) * sectionWidth
      
      // More dramatic density decrease: 100%, 90%, 80%, 70%, 50%, 40%, 20%, 10%, 5%
      const densityPercents = [100, 90, 75, 60, 45, 30, 20, 10, 5]
      const densityPercent = densityPercents[section]
      const maxDotsThisSection = Math.round((50 * densityPercent) / 100) // Increased base from 25 to 60
      
      // Sections 6-9 (columns 6-9): More uniform distribution with decreasing noise
      if (section >= 5) {
        // Noise factors: 0.15, 0.1, 0.05, 0.03 for columns 6, 7, 8, 9
        const noiseFactors = [0.15, 0.1, 0.05, 0.03]
        const noiseFactor = noiseFactors[section - 5] || 0.03
        
        for (let i = 0; i < maxDotsThisSection; i++) {
          // Calculate symmetrical vertical position
          const baseY = height * (i + 1) / (maxDotsThisSection + 1)
          
          // Add noise to the base position
          const noiseY = (Math.random() - 0.5) * height * noiseFactor
          const finalY = Math.max(5, Math.min(height - 5, baseY + noiseY))
          
          // X position: centered for column 9, random for others
          let x
          if (section === 8) { // Column 9
            const baseX = sectionStartX + sectionWidth / 2
            const noiseX = (Math.random() - 0.5) * sectionWidth * 0.1
            x = baseX + noiseX
          } else {
            x = sectionStartX + Math.random() * sectionWidth
          }
          
          dots.push({
            id: dotId++,
            x: Math.max(sectionStartX + 1, Math.min(sectionEndX - 1, x)),
            y: finalY,
            r: dotSize,
            opacity: 1.0,
          })
        }
      } else {
        // Sections 1-5 (columns 1-5): Keep full random distribution
        for (let i = 0; i < maxDotsThisSection; i++) {
          const x = sectionStartX + Math.random() * sectionWidth
          const y = Math.random() * height
          
          dots.push({
            id: dotId++,
            x: Math.max(sectionStartX + 1, Math.min(sectionEndX - 1, x)),
            y: Math.max(1, Math.min(height - 1, y)),
            r: dotSize,
            opacity: 1.0,
          })
        }
      }
    }
    
    // Section 10: Single centered dot
    dots.push({
      id: dotId++,
      x: 9 * sectionWidth + sectionWidth / 2, // Center of section 10
      y: height / 2, // Vertically centered
      r: dotSize*1.5,
      opacity: 1.0,
    })
    
    return dots
  }

  const mobileDots = generateMobileDots()
  const desktopDots = generateDesktopDots()

  return (
    <div className="relative w-full h-full rounded-lg overflow-hidden">
      {/* Mobile Version - Shorter and more compact */}
      <div className="absolute inset-0 lg:hidden">
        <svg
          width="100%"
          height="100%"
          viewBox="-10 35 340 180"
          className="absolute inset-0"
          preserveAspectRatio="xMidYMid meet"
        >
          {mobileDots.map((dot) => (
            <circle
              key={`mobile-${dot.id}`}
              cx={dot.x}
              cy={dot.y}
              r={dot.r}
              fill="currentColor"
              opacity={dot.opacity}
              className="text-foreground/90"
            />
          ))}
        </svg>
      </div>

      {/* Desktop Version - Full height and coverage */}
      <div className="absolute inset-0 hidden lg:block">
        <svg
          width="100%"
          height="100%"
          viewBox="-10 0 250 180"
          className="absolute inset-0"
          preserveAspectRatio="xMidYMid meet"
        >
          {desktopDots.map((dot) => (
            <circle
              key={`desktop-${dot.id}`}
              cx={dot.x}
              cy={dot.y}
              r={dot.r}
              fill="currentColor"
              opacity={dot.opacity}
              className="text-foreground/90"
            />
          ))}
        </svg>
      </div>
    </div>
  )
} 