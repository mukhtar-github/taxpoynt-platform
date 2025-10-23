/* eslint-disable no-restricted-globals */
/**
 * Service Worker Reset
 * ====================
 *
 * Legacy deployments shipped an aggressive caching service worker that now
 * serves outdated application bundles (causing the role management crash) and
 * throws when encountering browser-extension URLs. This replacement script
 * immediately clears all caches and unregisters itself so the application
 * falls back to default network behaviour.
 *
 * We keep the file at `/sw.js` so existing registrations update and run this
 * cleanup logic automatically.
 */

const cleanUpAndUnregister = async () => {
  try {
    const cacheKeys = await caches.keys();
    await Promise.all(cacheKeys.map((key) => caches.delete(key)));
  } catch (error) {
    console.warn('[SW] Failed to clear caches during reset:', error);
  }

  try {
    await self.registration.unregister();
  } catch (error) {
    console.warn('[SW] Failed to unregister legacy service worker:', error);
  }

  await self.clients.claim();
};

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(cleanUpAndUnregister());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(cleanUpAndUnregister());
});

self.addEventListener('fetch', (event) => {
  // Avoid touching browser-extension schemes that legacy workers attempted to cache.
  if (event.request.url.startsWith('chrome-extension://')) {
    return;
  }

  // Passthrough network request while the worker is still active for this page load.
  event.respondWith(fetch(event.request));
});

