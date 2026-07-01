// ============================================================
// SCAS Service Worker
// Place this file at: scas/static/service-worker.js
//
// IMPORTANT: Update CACHE_VERSION every time you change
// CSS or JS files so users get the fresh version.
// e.g. 'scas-v1' → 'scas-v2'
// ============================================================

var CACHE_VERSION = 'scas-v1';

// Static assets to cache for faster loading
// Do NOT add login, dashboard, or attendance pages —
// they need live data from the server every time
var STATIC_ASSETS = [
  '/static/css/styles.css',
  '/static/js/app.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/manifest.json'
];

// Pages that must ALWAYS come from the network (never cached)
var NEVER_CACHE = [
  '/api/',
  '/login',
  '/logout',
  '/dashboard',
  '/mark-attendance',
  '/history',
  '/entry-exit',
  '/admin',
  '/admin/',
  '/admin/students',
  '/admin/attendance',
  '/admin/reports',
  '/admin/entry-exit',
  '/admin/api/'
];

// ── INSTALL ──────────────────────────────────────────────────
// Runs once when service worker is first registered.
// Caches static assets.
self.addEventListener('install', function (event) {
  console.log('[SW] Installing version:', CACHE_VERSION);
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  // Activate immediately without waiting for old tabs to close
  self.skipWaiting();
});

// ── ACTIVATE ─────────────────────────────────────────────────
// Runs after install. Deletes old cache versions.
self.addEventListener('activate', function (event) {
  console.log('[SW] Activating version:', CACHE_VERSION);
  event.waitUntil(
    caches.keys().then(function (cacheNames) {
      return Promise.all(
        cacheNames
          .filter(function (name) { return name !== CACHE_VERSION; })
          .map(function (name) {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    })
  );
  // Take control of all open pages immediately
  self.clients.claim();
});

// ── FETCH ─────────────────────────────────────────────────────
// Intercepts every network request.
// Dynamic pages → always network.
// Static assets → network first, cache fallback.
self.addEventListener('fetch', function (event) {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;

  var url = new URL(event.request.url);

  // Skip cross-origin requests (fonts, external APIs)
  if (url.origin !== self.location.origin) return;

  // Check if this URL should never be cached
  var skipCache = NEVER_CACHE.some(function (path) {
    return url.pathname === path || url.pathname.startsWith(path);
  });

  if (skipCache) {
    // Always fetch from network — these pages have live data
    event.respondWith(
      fetch(event.request).catch(function () {
        // If network fails on a page request, show offline message
        return new Response(
          '<html><body style="font-family:sans-serif;text-align:center;padding:2rem;background:#0b0f1a;color:#e8ecf4">' +
          '<h2>📡 No Internet Connection</h2>' +
          '<p>SCAS needs an internet connection to load attendance data.</p>' +
          '<p>Please check your connection and try again.</p>' +
          '<button onclick="location.reload()" style="background:#3d7eff;color:#fff;border:none;padding:.75rem 1.5rem;border-radius:8px;font-size:14px;cursor:pointer;margin-top:1rem">Retry</button>' +
          '</body></html>',
          { headers: { 'Content-Type': 'text/html' } }
        );
      })
    );
    return;
  }

  // Static assets: try network first, fall back to cache
  event.respondWith(
    fetch(event.request)
      .then(function (networkResponse) {
        // Got a valid response — update the cache
        if (networkResponse && networkResponse.status === 200) {
          var responseToCache = networkResponse.clone();
          caches.open(CACHE_VERSION).then(function (cache) {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(function () {
        // Network failed — serve from cache
        return caches.match(event.request);
      })
  );
});
