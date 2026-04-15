/**
 * Utility for handling country/region flags
 */

/**
 * Get an emoji flag for a country code
 * 
 * @param countryCode The 2-letter ISO country code
 * @returns An emoji flag representing the country
 */
export function getCountryFlag(countryCode: string): string {
  // Handle empty or invalid input
  if (!countryCode || typeof countryCode !== 'string' || countryCode.length !== 2) {
    return '🌐'; // Globe emoji as fallback
  }

  // Convert country code to uppercase
  const code = countryCode.toUpperCase();
  
  // Convert the country code to regional indicator symbols
  // Regional indicator symbols are Unicode characters in the range U+1F1E6 to U+1F1FF
  // They represent the 26 letters A-Z and are used to form country flag emojis
  const firstLetter = code.charCodeAt(0) - 65 + 0x1F1E6;
  const secondLetter = code.charCodeAt(1) - 65 + 0x1F1E6;
  
  // Convert the code points to emoji
  const flagEmoji = String.fromCodePoint(firstLetter) + String.fromCodePoint(secondLetter);
  
  return flagEmoji;
}

/**
 * Component that renders a country flag emoji
 */
export function CountryFlag({ code }: { code: string }) {
  return (
    <span role="img" aria-label={`Flag of ${code.toUpperCase()}`} className="text-xl">
      {getCountryFlag(code)}
    </span>
  );
}

/**
 * Map of region codes to custom flag components for regions that don't have standard flags
 * or need special handling
 */
export const specialRegionFlags: Record<string, JSX.Element> = {
  // Example for a region that isn't a country (e.g., European Union)
  "eu": <span role="img" aria-label="European Union">🇪🇺</span>,
  
  // Example for a custom region
  "global": <span role="img" aria-label="Global">🌍</span>,

  // Fix for China - using language code instead of country code
  "zh": <span role="img" aria-label="China">🇨🇳</span>,

  // Fix for Israel - using language code instead of country code
  "is": <span role="img" aria-label="Israel">🇮🇱</span>,
  
  // Add more special cases as needed
};

/**
 * Get a flag representation (either emoji or custom component) for a region code
 * 
 * @param regionCode The region code (usually a 2-letter ISO country code)
 * @returns A flag representation as JSX element
 */
export function getRegionFlag(regionCode: string): JSX.Element {
  // Check if we have a special case for this region
  if (regionCode in specialRegionFlags) {
    return specialRegionFlags[regionCode];
  }
  
  // Otherwise return the country flag component
  return <CountryFlag code={regionCode} />;
} 