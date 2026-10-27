// LandSafe Connect - Service Worker Cache Invalidation & Network Passthrough
const CACHE_NAME = "landsafe-pwa-v3-purge";

self.addEventListener("install", (event) => {
    // Activate immediately without waiting for existing clients to close
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    // Delete all legacy caches immediately to ensure fresh UI assets
    event.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(
                keyList.map((key) => {
                    console.log("[ServiceWorker] Purging legacy cache:", key);
                    return caches.delete(key);
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (event) => {
    // Network passthrough — never intercept or serve stale HTML
    return;
});

