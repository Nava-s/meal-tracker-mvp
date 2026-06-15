const CACHE = "meal-tracker-v1";
const FILES = ["/", "/index.html", "/css/app.css", "/js/app.js", "/js/api.js", "/js/scanner.js", "/js/camera.js", "/manifest.json"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener("fetch", (e) => {
  if (e.request.url.startsWith(self.location.origin) && !e.request.url.includes("/api/")) {
    e.respondWith(
      caches.match(e.request).then((r) => r || fetch(e.request))
    );
  }
});
