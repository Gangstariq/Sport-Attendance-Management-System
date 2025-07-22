const CACHE_NAME = "sportmanager-cache-v1";
const STATIC_ASSETS = [
    "/",
    "/static/style.css",
    "/static/Check_192_icon.png",
    "/static/Check_512_icon.png"
];
//#https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/display - Tutorial Used
// Install Service Worker
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
});

// Fetch from cache or network
self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});

// Activate new cache and remove old
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            );
        })
    );
});