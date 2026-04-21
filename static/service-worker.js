const CACHE_NAME = 'armar-equipos-v2';
const urlsToCache = [
  '/static/css/style.css',
  '/static/js/main.min.js',
  '/static/images/armar-equipos-logo-circle.png',
  '/static/favicon/android-chrome-192x192.png',
  '/static/favicon/android-chrome-512x512.png'
];

const STATIC_DESTINATIONS = ['script', 'style', 'image', 'font'];

function isSameOrigin(requestUrl) {
  return requestUrl.origin === self.location.origin;
}

function isStaticAssetRequest(request) {
  const requestUrl = new URL(request.url);

  if (!isSameOrigin(requestUrl)) {
    return false;
  }

  return requestUrl.pathname.startsWith('/static/')
    || STATIC_DESTINATIONS.includes(request.destination);
}

function isDocumentRequest(request) {
  return request.mode === 'navigate' || request.destination === 'document';
}

function offlineResponse() {
  return new Response('Offline - No cached content available', {
    status: 503,
    statusText: 'Service Unavailable',
    headers: new Headers({
      'Content-Type': 'text/html'
    })
  });
}

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(cacheName => cacheName !== CACHE_NAME)
          .map(cacheName => caches.delete(cacheName))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') {
    event.respondWith(fetch(event.request));
    return;
  }

  if (isStaticAssetRequest(event.request)) {
    event.respondWith(
      caches.match(event.request).then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(event.request).then(response => {
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache);
          });

          return response;
        });
      })
    );
    return;
  }

  if (isDocumentRequest(event.request)) {
    event.respondWith(
      fetch(event.request).catch(() => offlineResponse())
    );
    return;
  }

  event.respondWith(fetch(event.request));
});
