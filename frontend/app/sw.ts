/// <reference lib="webworker" />
export {}

const serviceWorker = globalThis as unknown as ServiceWorkerGlobalScope
const CACHE_NAME = "dailybrief-cache-v1"

// Add list of files to cache here
const urlsToCache = ["/", "/home", "/world", "/offline"]

serviceWorker.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache)
    }),
  )
})

serviceWorker.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // Cache hit - return response
      if (response) {
        return response
      }

      return fetch(event.request)
        .then((response) => {
          // Check if we received a valid response
          if (!response || response.status !== 200 || response.type !== "basic") {
            return response
          }

          // Clone the response
          const responseToCache = response.clone()

          // Don't cache API requests
          if (!event.request.url.includes("/api/")) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache)
            })
          }

          return response
        })
        .catch(() => {
          // If the network is unavailable, try to return the offline page
          if (event.request.mode === "navigate") {
            return caches.match("/offline").then(
              (offlinePage) =>
                offlinePage ||
                new Response("Offline", {
                  status: 503,
                  statusText: "Offline",
                  headers: { "Content-Type": "text/plain" },
                }),
            )
          }
          return new Response("Network error", {
            status: 504,
            statusText: "Gateway Timeout",
            headers: { "Content-Type": "text/plain" },
          })
        })
    }),
  )
})

serviceWorker.addEventListener("activate", (event) => {
  const cacheWhitelist = [CACHE_NAME]
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName)
          }
        }),
      )
    }),
  )
})
