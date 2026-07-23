/* VagrantForge Desktop — enveloppe Electron autour du frontend web existant.
 *
 * Ne duplique PAS le frontend : charge directement web/frontend/index.html
 * tel quel (même HTML/CSS/JS que la version navigateur/PWA). Le site est
 * déjà 100 % autonome côté client (aucune dépendance au DOM du navigateur
 * dans generateur.js/donnees.js, service worker déjà désactivé sur
 * `file://` par app.js) — il tourne donc ici sans aucune modification.
 *
 * Sécurité : contextIsolation activé, nodeIntegration désactivé — le
 * frontend n'a pas besoin d'accès Node.js, seulement d'être affiché.
 */
'use strict';
const { app, BrowserWindow, Menu, shell } = require('electron');
const path = require('path');

// En dev : web/frontend/ à côté du dossier desktop/, dans le dépôt.
// Une fois packagé (electron-builder) : copié en tant qu'`extraResources`
// dans resources/frontend/ (voir desktop/package.json → build.extraResources).
const CHEMIN_FRONTEND = app.isPackaged
  ? path.join(process.resourcesPath, 'frontend', 'index.html')
  : path.join(__dirname, '..', 'web', 'frontend', 'index.html');

function creerFenetre() {
  const fenetre = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'VagrantForge',
    backgroundColor: '#0f1115',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  fenetre.loadFile(CHEMIN_FRONTEND);

  // Les liens externes (ex. doc Vagrant Cloud) s'ouvrent dans le navigateur
  // système plutôt que dans une fenêtre Electron.
  fenetre.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  return fenetre;
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);
  creerFenetre();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) creerFenetre();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
