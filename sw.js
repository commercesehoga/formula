/* ThunderStudy AI service worker
   - App shell + offline page are precached
   - HTML (navigations): network-first, falls back to cache, then offline.html
   - Assets (css, js, images, fonts, icons): cache-first
   - /api/ and non-GET requests are never touched */
const VERSION = 'v2-2026-10-03';
const CACHE = 'thunderstudy-' + VERSION;
const OFFLINE_URL = '/offline.html';

const SHELL = ['/', '/app', '/about', '/faq', '/new', '/formula', '/how-it-works', '/examples', '/hi',
  '/favicon.svg', '/manifest.json', '/icons/icon-192.png', '/icons/icon-512.png'];

// Cloudflare Pages redirects /x.html to /x. A redirected response cannot be used
// for a navigation, so copy it into a clean response before caching.
function clean(res) {
  if (!res.redirected) return res;
  return res.blob().then(function (b) {
    return new Response(b, { status: res.status, statusText: res.statusText, headers: res.headers });
  });
}

function precache(cache, url, key) {
  return fetch(url, { cache: 'reload' })
    .then(function (res) { return res.ok ? clean(res) : null; })
    .then(function (res) { if (res) return cache.put(key || url, res); })
    .catch(function () {});
}

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      // offline page: try the pretty URL first, store under /offline.html
      var jobs = [precache(cache, '/offline', OFFLINE_URL).then(function () {
        return cache.match(OFFLINE_URL).then(function (hit) {
          if (!hit) return precache(cache, OFFLINE_URL, OFFLINE_URL);
        });
      })];
      SHELL.forEach(function (u) { jobs.push(precache(cache, u)); });
      return Promise.all(jobs);
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) {
        return k.indexOf('thunderstudy-') === 0 && k !== CACHE;
      }).map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

function offlineResponse() {
  return caches.match(OFFLINE_URL).then(function (r) {
    return r || new Response('You are offline.', { status: 503, headers: { 'Content-Type': 'text/plain' } });
  });
}

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);

  var sameOrigin = url.origin === self.location.origin;
  var isFont = url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com';
  if (!sameOrigin && !isFont) return;
  if (sameOrigin && (url.pathname.indexOf('/api/') === 0 || url.pathname === '/sw.js')) return;

  // HTML pages: network-first
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').indexOf('text/html') !== -1) {
    event.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok && !res.redirected) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) { return hit || offlineResponse(); });
      })
    );
    return;
  }

  // Assets: cache-first
  event.respondWith(
    caches.match(req).then(function (hit) {
      if (hit) return hit;
      return fetch(req).then(function (res) {
        if (res && (res.ok || res.type === 'opaque')) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      });
    })
  );
});
