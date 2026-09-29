const CACHE_PREFIX = 'dhl-board-shell-';
const CACHE_NAME = `${CACHE_PREFIX}v207`;
const APP_SHELL = ['./', './index.html', './styles.css', './framework-theme.css', './components.css', './layout-v2.css', './meeting-status.css', './interactions.css', './workforce-edit.css', './clear-step.css', './day-tools.css', './shifts.css', './validation-status.css', './reference-theme.css', './tv-fit.css', './html2canvas.min.js', './app.js', './manifest.webmanifest', './icon.svg', './icon-192.png', './icon-512.png', './oms-first-choice.png', './dhl-logo.svg', './lucide.min.js', './Inter-Variable.ttf', './BarlowCondensed-SemiBold.ttf', './BarlowCondensed-ExtraBold.ttf'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(
    [...APP_SHELL, './aramark-logo.svg'].map(url => new Request(url, { cache: 'reload' }))
  )).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    const previous = keys
      .filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
      .sort((a, b) => Number(b.slice(CACHE_PREFIX.length + 1)) - Number(a.slice(CACHE_PREFIX.length + 1)))[0];
    await Promise.all(keys
      .filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME && key !== previous)
      .map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

async function cachedShell() {
  const indexUrl = new URL('./index.html', self.registration.scope).href;
  const rootUrl = new URL('./', self.registration.scope).href;
  const current = await caches.open(CACHE_NAME);
  return (await current.match(indexUrl, { ignoreSearch: true }))
    || (await current.match(rootUrl, { ignoreSearch: true }))
    || (await caches.match(indexUrl, { ignoreSearch: true }))
    || (await caches.match(rootUrl, { ignoreSearch: true }));
}

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    // Every navigation uses the same complete, versioned offline shell.
    if (event.request.mode === 'navigate') {
      const shell = await cachedShell();
      // Cloudflare redirects /index.html to /. A redirected cached response
      // cannot satisfy every navigation mode; return a clean HTML response.
      return shell ? new Response(shell.body, {
        status: shell.status,
        statusText: shell.statusText,
        headers: shell.headers
      }) : fetch(event.request).catch(() => new Response(
        '<!doctype html><meta charset="utf-8"><title>Diálogo Táctico DHL</title><style>body{margin:0;display:grid;place-items:center;min-height:100vh;background:#061f35;color:#fff;font:700 22px Arial;text-align:center}b{color:#ffcc00}</style><p><b>Diálogo Táctico DHL</b><br>Conecta una vez para completar la instalación sin conexión.</p>',
        { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
      ));
    }
    const cached = (await cache.match(event.request, { ignoreSearch: true }))
      || (await caches.match(event.request, { ignoreSearch: true }));
    if (cached) return cached;
    try {
      return await fetch(event.request);
    } catch {
      // Never return HTML in place of a missing image, script or font.
      return Response.error();
    }
  })());
});
