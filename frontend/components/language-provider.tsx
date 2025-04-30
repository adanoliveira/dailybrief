"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"

type Language = "en" | "es" | "fr" | "de" | "it" | "zh" | "ar" | "ru" | "pt" | "ja"

type LanguageContextType = {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string) => string
}

const defaultLanguage = "en"

const translations: Record<Language, Record<string, string>> = {
  en: {
    home: "Home",
    world: "World",
    profile: "Profile",
    daily_brief: "Your Daily Brief",
    read_more: "Read more",
    sign_in: "Sign In",
    sign_up: "Sign Up",
    get_started: "Get Started",
    // Add more translations as needed
  },
  es: {
    home: "Inicio",
    world: "Mundo",
    profile: "Perfil",
    daily_brief: "Tu Resumen Diario",
    read_more: "Leer más",
    sign_in: "Iniciar Sesión",
    sign_up: "Registrarse",
    get_started: "Comenzar",
    // Add more translations as needed
  },
  fr: {
    home: "Accueil",
    world: "Monde",
    profile: "Profil",
    daily_brief: "Votre Résumé Quotidien",
    read_more: "Lire plus",
    sign_in: "Se Connecter",
    sign_up: "S'inscrire",
    get_started: "Commencer",
    // Add more translations as needed
  },
  // Add other languages with their translations
  de: {},
  it: {},
  zh: {},
  ar: {},
  ru: {},
  pt: {},
  ja: {},
}

const LanguageContext = createContext<LanguageContextType>({
  language: defaultLanguage,
  setLanguage: () => {},
  t: (key) => key,
})

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(defaultLanguage)

  useEffect(() => {
    // Try to detect user's language from browser
    const detectLanguage = () => {
      const browserLang = navigator.language.split("-")[0] as Language
      if (Object.keys(translations).includes(browserLang)) {
        setLanguage(browserLang)
      }
    }

    detectLanguage()
  }, [])

  const t = (key: string): string => {
    return translations[language][key] || translations.en[key] || key
  }

  return <LanguageContext.Provider value={{ language, setLanguage, t }}>{children}</LanguageContext.Provider>
}

export const useLanguage = () => useContext(LanguageContext)
