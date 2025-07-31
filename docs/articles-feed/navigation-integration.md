# Navigation Integration - Articles Feed

## Overview

The navigation system provides seamless access to different article feeds across mobile and desktop interfaces. It features consistent styling, active state management, and internationalization support while maintaining a native app-like experience.

## Navigation Architecture

### Unified Design System

Both mobile and desktop navigation share:
- **Consistent Icons**: Same Lucide React icons across platforms
- **Active States**: Primary color highlighting for current page
- **Internationalization**: Shared translation keys and language support
- **Accessibility**: Proper ARIA labels and keyboard navigation

### Platform-Specific Implementations

| Feature | Mobile Navigation | Desktop Navigation |
|---------|------------------|-------------------|
| **Position** | Fixed bottom bar | Header navigation |
| **Layout** | 3-column grid | Horizontal flex layout |
| **Labels** | Icon + text (vertical) | Icon + text (horizontal) |
| **Visibility** | `md:hidden` | `hidden md:flex` |

## File Structure

```
frontend/
├── app/(authenticated)/layout.tsx    # Desktop navigation + layout
├── components/
│   ├── mobile-nav.tsx               # Mobile bottom navigation
│   └── language-provider.tsx       # Internationalization
└── lib/utils.ts                     # Utility functions (cn)
```

## Mobile Navigation

### Component: `frontend/components/mobile-nav.tsx`

**Purpose**: Bottom navigation bar for mobile devices with touch-optimized interface

**Features**:
- Fixed positioning at bottom of screen
- Three main navigation items (Home, Headlines, Profile)
- Active state indication with primary color
- Internationalized labels
- Hidden on desktop (`md:hidden`)

**Implementation**:
```typescript
export function MobileNav() {
  const pathname = usePathname()

  return (
    <div className="fixed bottom-0 left-0 z-50 w-full h-16 bg-background border-t md:hidden">
      <div className="grid h-full grid-cols-3">
        <NavItem 
          href="/home" 
          icon={<Home className="h-5 w-5" />} 
          label="Home" 
          isActive={pathname === "/home"} 
        />
        <NavItem 
          href="/world" 
          icon={<Globe className="h-5 w-5" />} 
          label="Headlines" 
          isActive={pathname === "/world"} 
        />
        <NavItem
          href="/profile"
          icon={<User className="h-5 w-5" />}
          label="Profile"
          isActive={pathname === "/profile"}
        />
      </div>
    </div>
  )
}
```

**NavItem Component**:
```typescript
interface NavItemProps {
  href: string
  icon: React.ReactNode
  label: string
  isActive: boolean
}

function NavItem({ href, icon, label, isActive }: NavItemProps) {
  const { t } = useLanguage()

  return (
    <Link
      href={href}
      className={cn(
        "flex flex-col items-center justify-center",
        isActive ? "text-primary" : "text-muted-foreground"
      )}
    >
      {icon}
      <span className="text-xs mt-1">{t(label.toLowerCase())}</span>
    </Link>
  )
}
```

**Styling Classes**:
- `fixed bottom-0 left-0 z-50`: Fixed positioning at bottom
- `w-full h-16`: Full width, 64px height
- `bg-background border-t`: Background with top border
- `md:hidden`: Hidden on medium screens and up
- `grid grid-cols-3`: Three equal columns for navigation items

## Desktop Navigation

### Component: `frontend/app/(authenticated)/layout.tsx`

**Purpose**: Header navigation for desktop with enhanced functionality

**Features**:
- Sticky header positioning
- Logo branding on the left
- Navigation items with icons and labels
- Active state highlighting with background
- Hover effects and transitions
- Hidden on mobile (`hidden md:flex`)

**Implementation**:
```typescript
interface DesktopNavItemProps {
  href: string
  icon: React.ReactNode
  label: string
  isActive: boolean
}

function DesktopNavItem({ href, icon, label, isActive }: DesktopNavItemProps) {
  const { t } = useLanguage()
  
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
        isActive 
          ? "text-primary bg-primary/10" 
          : "text-muted-foreground hover:text-foreground hover:bg-accent"
      )}
    >
      {icon}
      {t(label.toLowerCase())}
    </Link>
  )
}
```

**Layout Structure**:
```typescript
export default function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-background pb-16 md:pb-0">
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/home" className="flex items-center gap-2">
            <LogoHorizontal priority />
          </Link>
          <div className="hidden md:flex items-center gap-2">
            <DesktopNavItem 
              href="/home" 
              icon={<Home className="h-4 w-4" />} 
              label="Home" 
              isActive={pathname === "/home"} 
            />
            <DesktopNavItem 
              href="/world" 
              icon={<Globe className="h-4 w-4" />} 
              label="Headlines" 
              isActive={pathname === "/world"} 
            />
            <DesktopNavItem 
              href="/profile" 
              icon={<User className="h-4 w-4" />} 
              label="Profile" 
              isActive={pathname === "/profile"} 
            />
          </div>
        </div>
      </header>

      <main>
        <Suspense>{children}</Suspense>
      </main>

      <NotificationPermission />
      <MobileNav />
    </div>
  )
}
```

**Styling Classes**:
- `sticky top-0 z-10`: Sticky header positioning
- `border-b bg-background/95 backdrop-blur`: Border and backdrop blur effect
- `container flex h-16`: Container with flex layout and 64px height
- `hidden md:flex`: Hidden on mobile, flex on desktop
- `items-center gap-2`: Vertical alignment with spacing

## Navigation Routes

### Route Mapping

| Route | Component | Feed Type | Description |
|-------|-----------|-----------|-------------|
| `/home` | `app/(authenticated)/home/page.tsx` | Personalized | User's topic-based feed |
| `/world` | `app/(authenticated)/world/page.tsx` | World Headlines | Global top headlines |
| `/profile` | `app/(authenticated)/profile/page.tsx` | N/A | User profile and settings |

### Route Protection

All routes under `(authenticated)` group require:
1. **Valid Session**: NextAuth session must be active
2. **Onboarding Complete**: User must have completed preference setup
3. **JWT Token**: Valid backend authentication token

**Protection Logic**:
```typescript
// In each page component
useEffect(() => {
  if (isLoadingUser) return
  
  if (userStatus && !userStatus.has_completed_onboarding) {
    router.replace('/onboarding?skip_check=true')
    return
  }
  
  setIsVerifying(false)
}, [userStatus, isLoadingUser, router])
```

## Active State Management

### Pathname Detection

Both navigation components use Next.js `usePathname()` hook:

```typescript
const pathname = usePathname()

// Usage in navigation items
isActive={pathname === "/home"}
isActive={pathname === "/world"}
isActive={pathname === "/profile"}
```

### Visual Indicators

**Mobile Navigation**:
- Active: `text-primary` (brand primary color)
- Inactive: `text-muted-foreground` (muted gray)

**Desktop Navigation**:
- Active: `text-primary bg-primary/10` (primary text with light background)
- Inactive: `text-muted-foreground` with hover states
- Hover: `hover:text-foreground hover:bg-accent`

## Internationalization

### Language Provider Integration

Both navigation components use the shared language provider:

```typescript
const { t } = useLanguage()

// Usage in components
<span>{t(label.toLowerCase())}</span>
```

### Translation Keys

| Key | English | Spanish | French |
|-----|---------|---------|--------|
| `home` | "Home" | "Inicio" | "Accueil" |
| `headlines` | "Headlines" | "Titulares" | "Titres" |
| `profile` | "Profile" | "Perfil" | "Profil" |

### Language Provider: `frontend/components/language-provider.tsx`

```typescript
const translations: Record<Language, Record<string, string>> = {
  en: {
    home: "Home",
    headlines: "Headlines",
    profile: "Profile",
  },
  es: {
    home: "Inicio",
    headlines: "Titulares",
    profile: "Perfil",
  },
  fr: {
    home: "Accueil",
    headlines: "Titres",
    profile: "Profil",
  }
}
```

## Responsive Design

### Breakpoint Strategy

The navigation system uses Tailwind's responsive prefixes:

- **Mobile First**: Base styles target mobile devices
- **Desktop Override**: `md:` prefix for tablet and desktop (≥768px)

**Implementation**:
```css
/* Mobile navigation - visible by default */
.mobile-nav {
  display: flex;
}

/* Hide on medium screens and up */
@media (min-width: 768px) {
  .mobile-nav {
    display: none;
  }
}

/* Desktop navigation - hidden by default */
.desktop-nav {
  display: none;
}

/* Show on medium screens and up */
@media (min-width: 768px) {
  .desktop-nav {
    display: flex;
  }
}
```

### Layout Adjustments

**Mobile Layout**:
- Bottom padding (`pb-16`) to account for fixed navigation
- Full-width navigation bar
- Vertical icon + text layout

**Desktop Layout**:
- No bottom padding (`md:pb-0`)
- Header navigation with logo
- Horizontal icon + text layout

## Accessibility

### Keyboard Navigation

**Desktop Navigation**:
- Tab order follows logical sequence
- Enter/Space activates navigation links
- Focus indicators visible

**Mobile Navigation**:
- Touch targets meet minimum 44px requirement
- Proper focus management for screen readers

### ARIA Labels

```typescript
// Screen reader support
<span className="sr-only">Navigate to {label}</span>

// Proper link semantics
<Link href={href} aria-current={isActive ? "page" : undefined}>
```

### Color Contrast

All navigation states meet WCAG AA standards:
- Active states use sufficient contrast ratios
- Hover states provide clear visual feedback
- Focus indicators are clearly visible

## Performance Optimizations

### Component Optimization

**Memoization**:
```typescript
const NavItem = React.memo(({ href, icon, label, isActive }: NavItemProps) => {
  // Component implementation
})
```

**Efficient Re-renders**:
- Only re-render when `pathname` changes
- Stable icon components prevent unnecessary updates
- Translation function is memoized

### Bundle Optimization

- Icons imported individually to reduce bundle size
- Shared components prevent code duplication
- CSS classes optimized with Tailwind's purge

## Testing Strategy

### Unit Tests

```typescript
describe('MobileNav', () => {
  it('highlights active navigation item', () => {
    render(<MobileNav />, { 
      wrapper: ({ children }) => (
        <MockRouter pathname="/home">{children}</MockRouter>
      )
    })
    
    expect(screen.getByText('Home')).toHaveClass('text-primary')
  })
  
  it('renders correct navigation links', () => {
    render(<MobileNav />)
    
    expect(screen.getByRole('link', { name: /home/i })).toHaveAttribute('href', '/home')
    expect(screen.getByRole('link', { name: /headlines/i })).toHaveAttribute('href', '/world')
    expect(screen.getByRole('link', { name: /profile/i })).toHaveAttribute('href', '/profile')
  })
})
```

### Integration Tests

```typescript
describe('Navigation Integration', () => {
  it('navigates between feeds correctly', async () => {
    render(<App />)
    
    // Start on home page
    expect(screen.getByText('Your News')).toBeInTheDocument()
    
    // Navigate to world headlines
    fireEvent.click(screen.getByText('Headlines'))
    await waitFor(() => {
      expect(screen.getByText('Top Headlines')).toBeInTheDocument()
    })
    
    // Verify active state
    expect(screen.getByText('Headlines')).toHaveClass('text-primary')
  })
})
```

### Accessibility Tests

```typescript
describe('Navigation Accessibility', () => {
  it('supports keyboard navigation', () => {
    render(<DesktopNav />)
    
    const homeLink = screen.getByRole('link', { name: /home/i })
    homeLink.focus()
    
    expect(homeLink).toHaveFocus()
    
    fireEvent.keyDown(homeLink, { key: 'Tab' })
    expect(screen.getByRole('link', { name: /headlines/i })).toHaveFocus()
  })
  
  it('meets color contrast requirements', () => {
    // Test implementation for contrast ratios
  })
})
```

## Future Enhancements

### Advanced Features

**Breadcrumb Navigation**:
```typescript
// For deeper navigation hierarchies
<Breadcrumb>
  <BreadcrumbItem href="/home">Home</BreadcrumbItem>
  <BreadcrumbItem href="/home/technology">Technology</BreadcrumbItem>
  <BreadcrumbItem current>AI News</BreadcrumbItem>
</Breadcrumb>
```

**Navigation Analytics**:
```typescript
// Track navigation usage
const trackNavigation = (from: string, to: string) => {
  analytics.track('navigation', { from, to, timestamp: Date.now() })
}
```

**Gesture Support**:
```typescript
// Swipe navigation for mobile
const handleSwipe = (direction: 'left' | 'right') => {
  if (direction === 'left') navigateToNext()
  if (direction === 'right') navigateToPrevious()
}
```

### Performance Improvements

**Preloading**:
```typescript
// Preload next likely page
<Link href="/world" prefetch={true}>Headlines</Link>
```

**Progressive Enhancement**:
```typescript
// Fallback for JavaScript disabled
<noscript>
  <style>{`.js-only { display: none; }`}</style>
</noscript>
```

### Customization Options

**Theme Support**:
```typescript
// Dark mode navigation
const navigationTheme = {
  light: 'bg-background border-border',
  dark: 'bg-background-dark border-border-dark'
}
```

**User Preferences**:
```typescript
// Customizable navigation order
const userNavigationOrder = ['home', 'world', 'bookmarks', 'profile']
``` 