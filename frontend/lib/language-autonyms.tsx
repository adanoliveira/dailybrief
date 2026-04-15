/**
 * Utility for displaying language names in their native scripts (autonyms)
 */

// Map of ISO language codes to autonyms (language names in their native scripts)
export const languageAutonyms: Record<string, string> = {
  // Major languages
  "en": "English",
  "es": "Español",
  "fr": "Français",
  "de": "Deutsch",
  "it": "Italiano",
  "pt": "Português",
  "ru": "Русский",
  "zh": "中文",
  "ja": "日本語",
  "ko": "한국어",
  "ar": "العربية",
  "hi": "हिन्दी",
  "bn": "বাংলা",
  "ur": "اردو",
  "tr": "Türkçe",
  "nl": "Nederlands",
  "pl": "Polski",
  "vi": "Tiếng Việt",
  "th": "ไทย",
  "sv": "Svenska",
  "no": "Norsk",
  "fi": "Suomi",
  "da": "Dansk",
  "cs": "Čeština",
  "el": "Ελληνικά",
  "he": "עברית",
  "id": "Bahasa Indonesia",
  "ms": "Bahasa Melayu",
  "fa": "فارسی",
  "uk": "Українська",
  "ro": "Română",
  "hu": "Magyar",
  "ta": "தமிழ்",
  "te": "తెలుగు",
  "mr": "मराठी",
  "gu": "ગુજરાતી",
  "kn": "ಕನ್ನಡ",
  "ml": "മലയാളം",
  
  // Add more languages as needed
};

/**
 * Get the autonym (native name) for a language based on its ISO code
 * 
 * @param languageCode The ISO language code
 * @returns The language name in its native script, or the original code if not found
 */
export function getLanguageAutonym(languageCode: string): string {
  if (!languageCode) return "";
  
  const code = languageCode.toLowerCase();
  
  // Return the autonym if available, otherwise return the code itself
  return languageAutonyms[code] || code;
}

/**
 * Component that displays a language in its native script
 */
export function LanguageAutonym({ code, showCode = false }: { code: string, showCode?: boolean }) {
  const autonym = getLanguageAutonym(code);
  
  return (
    <div className="flex flex-col items-center justify-center">
      <span className="font-medium text-base">
        {autonym}
      </span>
      {showCode && (
        <span className="text-xs text-muted-foreground uppercase mt-0.5">
          {code}
        </span>
      )}
    </div>
  );
} 