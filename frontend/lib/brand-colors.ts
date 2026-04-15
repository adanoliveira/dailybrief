const brandTokens = {
  light: {
    primary: "hsl(var(--primary))",
    background: "hsl(var(--background))",
    foreground: "hsl(var(--foreground))",
  },
  dark: {
    primary: "hsl(var(--primary))",
    background: "hsl(var(--background))",
    foreground: "hsl(var(--foreground))",
  },
}

// Helper to generate CSS variables for light and dark themes
export function generateThemeVariables() {
  return {
    light: brandTokens.light,
    dark: brandTokens.dark,
  }
}

export default brandTokens
