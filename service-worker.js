const CACHE_PREFIX = 'dhl-board-shell-';
const CACHE_NAME = `${CACHE_PREFIX}v131`;
const APP_SHELL = ['./', './index.html', './styles.css', './framework-theme.css', './components.css', './layout-v2.css', './meeting-status.css', './interactions.css', './workforce-edit.css', './clear-step.css', './day-tools.css', './shifts.css', './validation-status.css', './reference-theme.css', './app.js', './manifest.webmanifest', './icon.svg', './icon-192.png', './icon-512.png', './oms-first-choice.png', './dhl-logo.svg', './lucide.min.js', './Inter-Variable.ttf', './BarlowCondensed-SemiBold.ttf', './BarlowCondensed-ExtraBold.ttf'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(
    [...APP_SHELL, './aramark-logo.svg'].map(url => new Request(url, { cache: 'reload' }))
  )).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    // Every navigation uses the same complete, versioned offline shell.
    if (event.request.mode === 'navigate') {
      const shell = await cache.match('./index.html');
      // Cloudflare redirects /index.html to /. A redirected cached response
      // cannot satisfy every navigation mode; return a clean HTML response.
      return shell ? new Response(shell.body, {
        status: shell.status,
        statusText: shell.statusText,
        headers: shell.headers
      }) : fetch(event.request);
    }
    const cached = await cache.match(event.request);
    if (cached) return cached;
    try {
      return await fetch(event.request);
    } catch {
      // Never return HTML in place of a missing image, script or font.
      return Response.error();
    }
  })());
});
