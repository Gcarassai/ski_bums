/* Service worker: network-first for everything on this origin, cache as offline fallback.
   Because every request goes to the network first, a new data commit is picked up on the
   very next load; the cache is only used when the network is unavailable. */
const CACHE = 'ski-bums-v1';
const SHELL = [
  './', './index.html', './css/app.css', './js/app.js',
  './data/resorts.json', './data/meta.json',
  './assets/logo.png', './assets/manifest.webmanifest', './assets/favicon-32.png', './assets/icon-192.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL).catch(() => undefined)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // never touch external links
  event.respondWith(
    fetch(req).then((res) => {
      if (res && res.ok && res.type === 'basic') {
        const copy = res.clone();
        caches.open(CACHE).then((cache) => cache.put(req, copy)).catch(() => undefined);
      }
      return res;
    }).catch(async () => {
      const cache = await caches.open(CACHE);
      const hit = await cache.match(req, { ignoreSearch: true });
      if (hit) return hit;
      if (req.mode === 'navigate') return (await cache.match('./index.html')) || (await cache.match('./'));
      return Response.error();
    })
  );
});
