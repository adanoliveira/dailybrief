import brandTokens from '../../tailwind.brand';

// Helper to generate CSS variables for light and dark themes
export function generateThemeVariables() {
  return {
    light: brandTokens.light,
    dark: brandTokens.dark,
  };
}

export default brandTokens; 