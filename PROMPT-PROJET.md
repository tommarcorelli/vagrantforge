# 🧭 Prompt de reprise — VagrantForge

> Colle ce fichier (ou son contenu) au début d'une nouvelle session Claude Code
> pour reprendre le projet sans tout ré-expliquer. Il décrit l'état exact, les
> conventions et les pièges. Mets-le à jour quand le projet évolue.

---

## Contexte à donner à l'assistant

Tu reprends **VagrantForge**, un générateur de `Vagrantfile` multi-VM.
Emplacement : `D:\Projet\Projet site\Generateur-Vagrant\vagrantforge`.
Environnement : Windows 11, PowerShell. **Python s'appelle avec `py`** (les alias
`python`/`python3` du Windows Store plantent). Tout le projet est **en français**
(interface, commentaires, messages).

### À quoi ça sert
On décrit des labs de VMs (OS, RAM, CPU, réseau, provisioning) dans un formulaire
web ou une config JSON, et l'outil produit un `Vagrantfile` propre, commenté et
**validé**. Public : étudiants/admins qui montent des labs (K8s, LAMP, pentest…).

### Architecture — RÈGLE D'OR
**Un cœur Python** (`core/`) est la source de vérité. Le frontend web embarque une
**copie JS qui doit rester fidèle** au Python.
➡️ **Toute modif de génération ou de validation doit être faite AUX DEUX ENDROITS :**
- Python : `core/generateur.py`, `core/schema.py`, `core/presets.py`
- JS : `web/frontend/js/generateur.js` (`buildVagrantfile`), `js/validation.js`
  (`valider`), `js/donnees.js` (`PRESETS`, `BOX_PROVIDERS`, `CATALOGUE`).
Sinon la CLI et le web divergent. Après toute modif du cœur : `py tests\test_generateur.py`.

### Structure
```
vagrantforge/
├── core/           cœur partagé, ZÉRO dépendance (stdlib only)
│   ├── generateur.py   construction du Vagrantfile (+ bloc langue/clavier)
│   ├── schema.py       validation FR + table compat box↔provider (BOX_PROVIDERS)
│   └── presets.py      labs prêts : solo, k3s, lamp, devsecops, pentest
├── cli/main.py     CLI : sous-commandes generer / preset / valider / presets
├── web/
│   ├── api/main.py     serveur Flask OPTIONNEL (sert le front + API JSON)
│   └── frontend/       MODULAIRE (HTML / CSS / JS séparés)
│       ├── index.html      structure (hero, nav, app, footer, modale)
│       ├── css/style.css   tout le style (CSS moderne, variables + nesting)
│       └── js/             donnees.js · generateur.js · validation.js · app.js
├── tests/test_generateur.py   11 tests (génération, validation, presets, locale)
├── exemples/lab-web.json
├── requirements.txt   Flask (seulement pour l'API web)
├── README.md          doc utilisateur
└── PROMPT-PROJET.md   ce fichier (doc de reprise)
```

### Décisions déjà prises (ne pas défaire sans raison)
- **Frontend MODULAIRE** (HTML / CSS / JS séparés). ⚠️ HISTORIQUE : j'avais d'abord
  fait un fichier unique « pour le partage », mais l'utilisateur préfère le
  découpage (comme ses autres projets). NE PAS refusionner. Ordre de chargement des
  scripts dans index.html : donnees → generateur → validation → app (globals partagés).
- **Design assumé** : page d'accueil (hero) avec dégradé animé, glassmorphism,
  badges dégradés, aperçu avec numéros de ligne (voir `.code`/`.cl` dans le CSS,
  générés par `highlightRuby`). Palette = dégradé vert→cyan→indigo (var `--brand`).
- **SCSS** écarté (nécessite un build) ; on utilise CSS natif (variables + nesting).
- **CLI reconfigure stdout/stderr en UTF-8** (console Windows cp1252 sinon plante
  sur les accents et le caractère `─`).
- Prototype d'origine conservé à côté dans `..\vagrant-generateur\` (référence) —
  ⚠️ ne pas confondre : ce vieux `vagrantfile-generator.html` n'est PAS le projet.
- **Partage** : zipper `web/frontend/` ou déposer sur GitHub Pages (piste à faire).

### Ce qui est FAIT
- Génération multi-VM, 3 providers (virtualbox / vmware_desktop / libvirt).
- Réseau privé host-only (IP auto), réseau public en pont, ports redirigés.
- Provisioning shell / Ansible, mot de passe root.
- **Catalogue d'OS lisible** (Debian, Ubuntu, Rocky, Alma, Alpine, Arch, Kali,
  FreeBSD, bento…) par nom complet, groupé par famille.
- **RAM/CPU en listes**, option personnalisée.
- **Langue & clavier de la VM** (locale/keymap → provisioning locale-gen).
- **Bibliothèque de snippets shell** (Docker, Nginx, UFW, Node…).
- **Validation en direct** (erreurs + avertissements), pastille rouge par VM.
- **Aide** : bulles ⓘ + modale « Comment ça marche ».
- **Responsive + hamburger** + onglets Config/Aperçu en mobile.
- Import/export JSON, sauvegarde localStorage, copie/téléchargement.
- **Finition visuelle « premium »** : numéros de ligne dans l'aperçu (gutter façon
  IDE), grille de fond, animations d'apparition, halo pulsé du logo, icônes de
  presets, liseré dégradé des en-têtes. Bloc CSS dédié en fin de `<style>`
  (« Finition premium »).

### ⚠️ Piège à connaître (aperçu du code)
`highlightRuby()` (dans `js/generateur.js`) ne renvoie PAS du texte brut : il renvoie
`<div class="code">` avec un `<span class="cl">` par ligne (les numéros de ligne
viennent d'un `counter` CSS sur `.cl::before`). Le code BRUT copié/téléchargé vient
de `window.__vf` (variable séparée), pas du HTML colorisé — ne mélange pas les deux.

### Schéma de config (JSON)
```json
{
  "provider": "virtualbox",
  "box_check_update": false,
  "vms": [{
    "name": "web", "box": "debian/bookworm64",
    "box_version": "", "memory": 2048, "cpus": 1,
    "ip": "192.168.56.10", "provider": "", "gui": false,
    "public_network": false, "locale": "fr_FR.UTF-8", "keymap": "fr",
    "synced_folder": "./web", "disable_synced_folder": false,
    "ssh_username": "", "ssh_password": "", "root_password": "",
    "ports": [{ "guest": 80, "host": 8080 }],
    "provision": { "type": "shell", "script": "apt-get update -y\n" }
  }]
}
```

### Commandes utiles
```bash
py tests\test_generateur.py            # lancer les tests
py cli\main.py presets                 # lister les presets
py cli\main.py preset k3s -o Vagrantfile
py cli\main.py generer exemples\lab-web.json
py cli\main.py valider exemples\lab-web.json
py web\api\main.py                     # serveur web http://127.0.0.1:5000 (pip install -r requirements.txt)
```
Aperçu du front : ouvrir `web/frontend/index.html` dans un navigateur.
Test visuel headless (Chrome) : `--headless=new --screenshot=out.png "file:///..."`.

---

## 🚀 Futures améliorations (roadmap)

### ⭐ Prioritaire — PWA installable + logo néon
- [ ] **Transformer en PWA** (comme [[projet-linuxdojo]] / [[projet-annuaire]]) :
  - `manifest.webmanifest` : name « VagrantForge », short_name « Forge »,
    `display:standalone`, `theme_color:#070a10`, `background_color:#070a10`,
    start_url `./index.html`, icônes 192 + 512.
  - `service-worker.js` : cache offline de `index.html`, `css/style.css`, les 4 JS
    → l'appli marche **sans connexion** et devient **installable** (bouton « installer »).
  - Enregistrement du SW dans `app.js` (`navigator.serviceWorker.register`).
  - ⚠️ un SW ne s'active pas en `file://` : tester via `py web/api/main.py` ou un
    petit serveur statique. Prévoir un bouton « Installer l'appli » quand
    `beforeinstallprompt` se déclenche.
- [ ] **Logo néon stylé** : une enclume ⚒ « néon » (SVG) qui sert d'icône PWA et de
  logo dans la nav. Effet néon = traits en dégradé `--brand` (vert→cyan→indigo) +
  `filter: drop-shadow` multiples (halo) + léger flicker CSS. Décliner en PNG 192 &
  512 pour les icônes (piège connu : rendre l'icône en 512 puis redimensionner —
  voir [[chrome-headless-icones]]). Splash-friendly sur fond `#070a10`.

### Fonctionnalités
- [ ] **Preset Windows** (box `gusztavvargadr/windows-server`) — provisioning
      PowerShell, pas shell : adapter `bloc_provision` / le générateur.
- [ ] **Export `.zip` de projet** (Vagrantfile + arborescence des synced_folder +
      petit README de lancement) au lieu du seul Vagrantfile.
- [ ] **Disque additionnel** par VM (plugin `vagrant-disksize` ou disque libvirt).
- [ ] Générer en plus un **`ansible/inventory`** ou un `docker-compose` équivalent.
- [ ] **Thème clair** / bascule de thème (déjà tout en variables CSS → facile).
- [ ] **i18n** : externaliser les textes pour un futur mode anglais.
- [ ] Vérifier l'existence réelle des box via l'API **Vagrant Cloud** (au lieu de la
      table statique `BOX_PROVIDERS`).

### Diffusion
- [ ] **GitHub Pages** : publier `web/frontend/` pour une URL partageable cliquable.
- [ ] Bouton « Copier le lien de partage » (config encodée en base64 dans l'URL).

## Rappel avant de committer / partager
1. Modif du cœur ? → répercuter dans les JS `js/generateur.js` / `js/validation.js` /
   `js/donnees.js` ET lancer `py tests\test_generateur.py`.
2. Le front reste **modulaire** (HTML / CSS / JS séparés) — ne pas refusionner.
3. Tout en **français**.
