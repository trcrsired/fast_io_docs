const CACHE_NAME = "fast_io-docs-v13"; // bump version here
const urlsToCache = [
  "/",
  "/style.css",
  "/script.js",
  "/sw-register.js",
  "/manifest.json",
  "/icons/logo.webp",
  "/docs/intro/",
  "/docs/introfastio/",
  // "/docs/api/",
  "/docs/01.compile/",
  "/docs/01.compile/01.pwastore/",
  "/docs/01.compile/01.pwastore/01.webp",
  "/docs/01.compile/01.pwastore/02.webp",
  "/docs/01.compile/01.pwastore/03.webp",
  "/docs/01.compile/02.vscode/",
  "/docs/01.compile/02.vscode/autosavedisable.webp",
  "/docs/01.compile/03.compilers/",
  "/docs/03.dsal/",
  "/docs/03.dsal/01.string/",
];

// Install: pre-cache resources
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
  self.skipWaiting(); // activate new worker immediately
});

// Activate: remove old caches
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim(); // take control of all pages
});

// Fetch: cache-first with network fallback
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
