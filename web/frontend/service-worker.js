/* VagrantForge — service worker : cache offline de l'app shell.
   Stratégie "cache d'abord, filet réseau" pour les fichiers du cœur front ;
   tout le reste (ex. appels à l'API Vagrant Cloud) part directement au
   réseau, sans passer par le cache. Un SW ne s'active pas en file:// —
   normal, l'app fonctionne aussi bien sans lui dans ce cas. */

const CACHE = 'vagrantforge-v1';
const FICHIERS_APP_SHELL = [
  './',
  './index.html',
  './css/style.css',
  './js/i18n.js',
  './js/donnees.js',
  './js/generateur.js',
  './js/validation.js',
  './js/app.js',
  './manifest.webmanifest',
  './icons/icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
];

self.addEventListener('install', (evenement) => {
  evenement.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(FICHIERS_APP_SHELL)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (evenement) => {
  evenement.waitUntil(
    caches.keys().then((cles) =>
      Promise.all(cles.filter((c) => c !== CACHE).map((c) => caches.delete(c)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (evenement) => {
  const url = new URL(evenement.request.url);
  // Seules les requêtes GET vers notre propre origine passent par le cache ;
  // les appels vers Vagrant Cloud / l'API locale restent en direct.
  if (evenement.request.method !== 'GET' || url.origin !== self.location.origin) {
    return;
  }
  evenement.respondWith(
    caches.match(evenement.request).then((reponse) => {
      if (reponse) return reponse;
      return fetch(evenement.request)
        .then((reponseReseau) => {
          const copie = reponseReseau.clone();
          caches.open(CACHE).then((cache) => cache.put(evenement.request, copie)).catch(() => {});
          return reponseReseau;
        })
        .catch(() => caches.match('./index.html'));
    })
  );
});
