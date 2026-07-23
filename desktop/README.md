# VagrantForge Desktop

Enveloppe Electron autour du frontend web existant (`web/frontend/`). Aucun
code n'est dupliqué : `main.js` charge directement `web/frontend/index.html`
tel quel — le même HTML/CSS/JS que la version navigateur/PWA. Toute
évolution du site (nouveaux presets, nouveaux champs…) se retrouve donc
automatiquement dans la version desktop, sans rien à recopier ici.

## Lancer en développement

```powershell
cd desktop
npm install
npm start
```

## Construire l'installateur Windows (.exe)

```powershell
cd desktop
npm install
npm run dist:win
```

Le fichier `VagrantForge-Setup-<version>.exe` est généré dans `desktop/dist/`.
C'est un installateur NSIS classique (assistant next-next-finish, choix du
dossier d'installation, raccourcis Bureau + menu Démarrer).

Fonctionne aussi en croisé depuis Linux/macOS *si* Wine est installé
(`electron-builder` en a besoin pour construire un `.exe`) ; sinon, lance
`npm run dist:win` directement sous Windows.

Autres cibles disponibles :

```bash
npm run dist:linux   # AppImage
npm run dist:mac     # .dmg
```

## Pourquoi une version desktop en plus du site ?

La version web (navigateur ou PWA installée) fait déjà tout ce qui touche à
la génération/validation — c'est le même moteur JS ici. Ce que le
bac à sable du navigateur ne permet pas et qu'une vraie appli desktop
ouvrirait comme possibilité (non implémenté pour l'instant, juste
l'enveloppe) :

- écrire le Vagrantfile directement sur le disque sans passer par un
  téléchargement manuel,
- lancer `vagrant up` / `vagrant status` / `vagrant destroy` depuis
  l'interface et afficher leur sortie,
- accès direct au système de fichiers pour éditer un projet existant.

## Sécurité

`contextIsolation: true`, `nodeIntegration: false`, `sandbox: true` dans
`main.js` — le frontend n'a accès à rien de plus que dans un onglet de
navigateur classique. Les liens externes s'ouvrent dans le navigateur
système plutôt que dans une fenêtre Electron.
