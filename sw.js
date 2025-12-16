const CACHE_NAME = "fast_io-docs-v11"; // bump version here
const urlsToCache = [
  "/",
  "/style.css",
  "/script.js",
  "/sw-register.js",
  "/manifest.json",
  "/icons/logo.webp",
  "/docs/intro/",
  // "/docs/api/",
  "/docs/01.io/",
  "/docs/01.io/01.helloworld/",
  "/docs/01.io/02.aplusb/",
  "/docs/01.io/03.pointer/",
  "/docs/01.io/04.fileio/",
  "/docs/01.io/05.filetypelayers/",
  "/docs/02.dsal/",
  "/docs/02.dsal/01.string/",
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
