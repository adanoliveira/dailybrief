"use client"

import { useEffect } from "react"

export function ServiceWorkerRegistration() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return
    if (!("serviceWorker" in navigator)) return

    const registerServiceWorker = async () => {
      try {
        // Avoid noisy registration failures when sw.js is not emitted.
        const response = await fetch("/sw.js", { method: "HEAD", cache: "no-store" })
        if (!response.ok) {
          console.log("ServiceWorker skipped: /sw.js not found")
          return
        }

        const registration = await navigator.serviceWorker.register("/sw.js")
        console.log("ServiceWorker registration successful with scope: ", registration.scope)
      } catch (err) {
        console.log("ServiceWorker registration failed: ", err)
      }
    }

    window.addEventListener("load", registerServiceWorker)

    return () => {
      window.removeEventListener("load", registerServiceWorker)
    }
  }, [])

  return null
}
