var CACHE_NAME = 'tpv-cafe-v1';
var URLS_TO_CACHE = [
    '/',
    '/static/manifest.json',
    'https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/darkly/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/sweetalert2@11',
    'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap',
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            return cache.addAll(URLS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(names) {
            return Promise.all(names.filter(function(name) { return name !== CACHE_NAME; }).map(function(name) { return caches.delete(name); }));
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', function(event) {
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request).catch(function() {
                return new Response(JSON.stringify({ error: 'Sin conexion - modo offline' }), {
                    headers: { 'Content-Type': 'application/json' }
                });
            })
        );
        return;
    }
    event.respondWith(
        caches.match(event.request).then(function(cached) {
            return cached || fetch(event.request).then(function(response) {
                if (response.status === 200) {
                    var clone = response.clone();
                    caches.open(CACHE_NAME).then(function(cache) { cache.put(event.request, clone); });
                }
                return response;
            });
        }).catch(function() {
            return new Response('<h1 style="color:#fff;background:#0a0e1a;padding:40px;text-align:center;font-family:Inter,sans-serif;">Sin conexion a internet<br><small style="color:#64748b;">El TPV funciona en modo offline basico</small></h1>', {
                headers: { 'Content-Type': 'text/html' }
            });
        })
    );
});
