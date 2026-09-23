/* Service worker: network-first for everything on this origin, cache as offline fallback.
   Every request goes to the network first, and data requests bypass the HTTP cache's
   freshness (they revalidate with the server), so a new data commit is picked up on the
   very next load; the cache is only used when the network is unavailable. */
const CACHE = 'ski-bums-v3';
const SHELL = [
  './index.html', './css/app.css', './js/app.js', './manifest.webmanifest',
  './data/resorts.json', './data/meta.json',
  './assets/logo.png', './assets/favicon-32.png', './assets/icon-192.png',
];
const isData = (url) => /\/data\/[^/]+\.json$/.test(url.pathname);

self.addEventListener('install', (event) => {
  // Registration happens a couple of seconds after load, so these mostly come from the HTTP cache.
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => Promise.all(SHELL.map((u) => cache.add(u).catch(() => undefined))))
      .then(() => self.skipWaiting())
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
  const isNav = req.mode === 'navigate';
  const netReq = isData(url) ? new Request(req, { cache: 'no-cache' }) : req; // always revalidate data
  event.respondWith(
    fetch(netReq).then((res) => {
      if (res && res.ok && res.type === 'basic') {
        const copy = res.clone();
        // Navigations are keyed by index.html so filter/deep-link query strings do not pile up copies.
        caches.open(CACHE).then((cache) => cache.put(isNav ? './index.html' : req, copy)).catch(() => undefined);
      }
      return res;
    }).catch(async () => {
      const cache = await caches.open(CACHE);
      if (isNav) return (await cache.match('./index.html')) || Response.error();
      const hit = await cache.match(req, { ignoreSearch: true });
      return hit || Response.error();
    })
  );
});
