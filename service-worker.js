const CACHE_NAME = 'dhl-board-shell-v117';
const APP_SHELL = ['./', './index.html', './styles.css', './framework-theme.css', './components.css', './layout-v2.css', './meeting-status.css', './interactions.css', './workforce-edit.css', './clear-step.css', './day-tools.css', './shifts.css', './validation-status.css', './reference-theme.css', './app.js', './manifest.webmanifest', './assets/icon.svg', './assets/icon-192.png', './assets/icon-512.png', './assets/oms-first-choice.png', './assets/dhl-logo.svg', './assets/lucide.min.js', './assets/Inter-Variable.ttf', './assets/BarlowCondensed-SemiBold.ttf', './assets/BarlowCondensed-Bold.ttf', './assets/BarlowCondensed-ExtraBold.ttf'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))));
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    const copy = response.clone();
    caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
    return response;
  }).catch(() => caches.match('./index.html'))));
});
