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
- **3 presets réseau ajoutés** (thème BTS SISR) : `haproxy-lb` (HAProxy +
  2 backends web, round-robin), `dns-dhcp` (BIND9 + isc-dhcp-server + VM
  client de test), `wireguard` (VPN moderne, alternative à `openvpn`).
  Ajoutés aux deux côtés (`core/presets.py` + `js/donnees.js`) + icônes
  dans `app.js` (`ICP`) + tests dans `tests/test_generateur.py`.
- **2 presets supplémentaires** : `samba-ad` (contrôleur AD via Samba 4,
  alternative libre à `windows-ad`), `reverse-proxy-nginx` (proxy TLS
  auto-signé devant 2 apps backend). Même traitement des deux côtés + tests.
- **3 presets « services réseau classiques »** : `nfs-file-server` (partage
  NFS + client), `mail-server` (Postfix + Dovecot, SMTP/IMAP), `squid-proxy`
  (proxy sortant avec ACL de filtrage web). Même traitement des deux côtés
  (core Python + JS + icône `ICP` + tests). Total presets : 21. Suite de
  tests : 53/53 passent.
- **Dette technique comblée : parité JS/Python testée automatiquement.**
  Jusqu'ici la « règle d'or » (toute évolution de génération/validation
  répercutée des deux côtés) n'était vérifiée qu'à l'œil — le commentaire de
  `normaliserVMs` dans `generateur.js` documentait d'ailleurs un vrai bug de
  divergence déjà rencontré. Ajout de `tests/js_parity_harness.cjs` (exécute
  `generateur.js`/`donnees.js` hors navigateur via le module `vm` de Node,
  sans DOM nécessaire) et `tests/test_parite_js.py` (compare, pour chaque
  preset + quelques configs synthétiques ciblant disques/locale/Ansible/
  Windows/vmware, le Vagrantfile + inventaire Ansible (INI/YAML) + topologie
  Mermaid générés côté JS contre le cœur Python, caractère pour caractère).
  Sauté proprement si `node` est absent du PATH (même logique que `ruby -c`
  dans `core/lint.py`). **A immédiatement trouvé et corrigé 2 vraies
  divergences pré-existantes** (commentaires manquants côté JS sur
  `public_network` et sur le réglage réseau `vmware_desktop`). CI
  (`.github/workflows/tests.yml`) mise à jour pour installer Node dans le
  job pytest, sinon ces tests y seraient silencieusement sautés. Suite
  totale : 133 tests passent (dont 80 de parité).
- **Audit complet du reste du projet** (API Flask, `core/verif_box.py`,
  `core/export_projet.py`) — a trouvé et corrigé 3 bugs réels de plus, et
  comblé deux modules sans AUCUNE couverture de tests :
  1. `web/api/main.py` : un corps JSON non-objet (liste, chaîne…) posté sur
     `/api/exporter` faisait planter l'endpoint en 500 (`AttributeError`
     sur `corps.get(...)` appelé sur une liste). Factorisé dans un helper
     `_extraire_config()` réutilisé par les 4 endpoints POST, et couvert par
     un nouveau `tests/test_api.py` (32 tests, aucune couverture avant —
     CI mise à jour pour installer Flask dans le job pytest).
  2. `core/verif_box.py` : logique réseau/erreurs dupliquée à l'identique
     entre `recuperer_providers_distants` et `recuperer_versions_distantes`
     — factorisée dans `_recuperer_json_box()`. Couvert par un nouveau
     `tests/test_verif_box.py` (10 tests, réseau moqué, aucune couverture
     avant).
  3. `core/export_projet.py` : `dossier.lstrip("./")` retire un ENSEMBLE de
     caractères (pas le préfixe littéral) — un synced_folder nommé
     `.config` perdait son point, et un chemin avec `..` ailleurs qu'au
     tout début (ex. `data/../../etc`) n'était pas filtré (risque de
     zip-slip). Remplacé par une suppression explicite du préfixe `./` +
     un rejet de tout segment `..`. 2 tests de régression ajoutés dans
     `tests/test_generateur.py`.
  Suite totale après audit : **177 tests passent**.
- **8 nouveaux presets** (thème Kubernetes / CI-CD / sauvegarde, à la
  demande explicite) : `kubeadm` (cluster K8s complet control-plane +
  2 workers, CNI Calico — pendant « lourd » au `k3s` déjà présent),
  `docker-swarm` (manager + 2 workers, orchestration plus légère),
  `jenkins` (contrôleur + agent Docker en SSH), `github-runner` (runner
  GitHub Actions auto-hébergé), `awx` (Ansible AWX/Tower libre),
  `gitea` (Git auto-hébergé léger via Docker), `borg-backup` (sauvegarde
  chiffrée/dédupliquée en SSH + cron), `duplicati` (sauvegarde chiffrée
  avec interface web, complément GUI à `borg-backup`). Même traitement
  systématique des deux côtés (`core/presets.py` + `js/donnees.js`,
  vérifié par script de diff des clés) + icône dédiée dans `ICP`
  (`app.js`) + tests de verrouillage dans `tests/test_generateur.py`.
  Piège rencontré deux fois : le régex `REGEX_IPV4` de `schema.py`
  rejette tout octet > 255 (donc pas de suffixe d'IP à 3 chiffres du
  genre `.260` sans vérifier — l'erreur est silencieuse tant qu'on ne
  relance pas `valider_config`). Total presets : **33**. Suite de
  tests : **208/208** passent.
- **Audit de vérification systématique** (suite à une demande explicite
  « vérifie les codes et tout ») : `pyflakes` sur `core/`, `cli/`,
  `web/api/` (a trouvé et corrigé un f-string sans placeholder dans
  `cli/main.py`, cosmétique) ; `node --check` sur les 5 JS du frontend ;
  script de diff des clés `PRESETS` Python vs JS (33/33, aucun écart) ;
  script vérifiant que les 33 presets passent tous par `valider_config`,
  `construire_topologie_mermaid`, `construire_inventaire_ansible(_yaml)`
  et `construire_zip_projet` sans erreur ; CLI de bout en bout (`preset`
  + `valider`) sur les 8 nouveaux ; `forge doctor` ; parité i18n FR/EN
  (119 clés) rejouée manuellement comme le fait la CI. Rien d'autre
  trouvé — le reste du projet est propre.
- **Nouvelle fonctionnalité** (pas un preset, cette fois — le domaine
  presets K8s/CI-CD/backup était saturé) : `hosts_file` (champ global,
  booléen, défaut `false`). Si activé, chaque VM ayant une `ip` reçoit un
  provisioner supplémentaire qui ajoute dans `/etc/hosts` (Linux) ou le
  fichier hosts Windows (PowerShell, `guest_os: "windows"`) une entrée
  par IP pour toutes les **autres** VMs de la config — résolution par nom
  (`ping web`, `curl http://db`) sans DNS, idempotent (pas de doublon au
  `vagrant provision` répété). Nouvelle fonction `bloc_hosts()` dans
  `core/generateur.py`, insérée dans `_lignes_vm()` juste avant le
  provisioning utilisateur (donc les services démarrés par le script
  du lab peuvent déjà résoudre les autres VMs par nom). Miroir JS
  (`blocHosts()` dans `generateur.js`), vérifié caractère pour caractère
  y compris pour le cas Windows (`js_parity_harness.cjs` + nouveau cas
  synthétique `hosts_file_mixte` dans `test_parite_js.py`). Case à
  cocher dédiée dans les réglages globaux du web (`#g-hostsfile`),
  câblée partout où `box_check_update` l'était (config courante,
  sauvegarde/restauration `localStorage`, lien partagé en base64,
  import JSON) — piège classique du projet : oublier un des 5 points de
  câblage rend le champ silencieusement perdu à l'export/import. 3 clés
  i18n FR/EN ajoutées et vérifiées synchronisées (121 clés au total).
  3 tests Python dédiés + 1 cas de parité synthétique. Suite complète :
  **212/212 tests passent**.
- **Enrichissement de l'export .zip** (`core/export_projet.py`, non
  mirroré en JS — l'export zip n'existe que côté serveur/CLI, jamais
  côté navigateur seul) : ajout d'un `.gitignore` (exclut `.vagrant/`,
  sinon un `git init && git add .` naïf sur le projet exporté committe
  l'état local propre à chaque machine hôte) et d'une section « Accès
  (ports exposés) » dans le `README.md` généré, qui liste tous les
  `forwarded_port` de la config. Piège évité de justesse : ma première
  version affichait systématiquement `http://localhost:<port>`, ce qui
  est faux pour la moitié des ports du projet (SSH sur `gitea` :22,
  SMTP/IMAP sur `mail-server`, JNLP sur `jenkins` :50000, Redis, VPN
  WireGuard, Minecraft…) — un simple inventaire de tous les ports
  utilisés par les 33 presets (script one-off) a suffi à s'en rendre
  compte avant de livrer. Corrigé en présentation neutre
  (`` `localhost:<port>` `` sans présumer le protocole) + une note
  explicative unique. 4 tests dédiés ajoutés, 1 test existant adapté
  (le zip contient désormais aussi `.gitignore`). Suite complète :
  **215/215 tests passent**.

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

### ⭐ Prioritaire — PWA installable + logo néon — **FAIT**
- [x] **Transformer en PWA** (comme [[projet-linuxdojo]] / [[projet-annuaire]]) :
  - `manifest.webmanifest` : name « VagrantForge », short_name « Forge »,
    `display:standalone`, `theme_color:#070a10`, `background_color:#070a10`,
    start_url `./index.html`, icônes 192 + 512.
  - `service-worker.js` : cache offline de `index.html`, `css/style.css`, les 4 JS
    → l'appli marche **sans connexion** et devient **installable** (bouton « installer »).
  - Enregistrement du SW dans `app.js` (`navigator.serviceWorker.register`).
  - ⚠️ un SW ne s'active pas en `file://` : tester via `py web/api/main.py` ou un
    petit serveur statique. Bouton « Installer l'appli » câblé sur
    `beforeinstallprompt`.
- [x] **Logo néon stylé** : une enclume ⚒ « néon » (SVG, `icons/icon.svg`) qui sert
  d'icône PWA (192 & 512, rendues avec cairosvg). Traits en dégradé
  vert→cyan→violet + `filter` de halo. Fond `#070a10`.

### Fonctionnalités
- [x] **Preset Windows** (`windows-ad` : contrôleur AD + client, box
      `gusztavvargadr/windows-*`) — provisioning PowerShell, WinRM automatique.
- [x] **Export `.zip` de projet** (Vagrantfile + arborescence des synced_folder +
      petit README de lancement) — `core/export_projet.py`, `forge exporter`,
      `POST /api/exporter`.
- [x] **Disque additionnel** par VM — `extra_disks`, VirtualBox (`createhd`/
      `storageattach` idempotent) et libvirt (`lv.storage`).
- [x] Générer en plus un **inventaire Ansible** (INI, groupes auto par préfixe) —
      `construire_inventaire_ansible`, `forge inventaire`, `POST /api/inventaire`.
      (`docker-compose` équivalent non fait — hors-sujet Vagrant, laissé de côté.)
- [x] **Thème clair/sombre** / bascule persistante — `[data-theme]` + `theme-btn`.
- [x] **i18n** : bascule FR/EN de l'interface — `js/i18n.js` (dictionnaire +
      `t()` + `appliquerI18nStatique()`), bouton « English »/« Français » dans
      la nav et le menu mobile, persisté comme le thème. Couvre : nav, hero,
      réglages globaux, sections, formulaire de VM (tous les libellés),
      modale d'aide, footer. **Restent volontairement en français** (gros
      chantiers à part, cf. commentaire en tête de `i18n.js`) : les messages
      de validation venant du cœur (`schema.py`/`validation.js`) et le
      contenu généré dans le Vagrantfile (commentaires, scripts).
- [x] Vérifier l'existence réelle des box via l'API **Vagrant Cloud** — déjà
      fait via `forge verifier-box` / `verif_box.py` (comparaison ponctuelle,
      pas de vérif automatique à chaque génération — resterait à faire si
      besoin, mais le principal est en place).

### Diffusion
- [x] **GitHub Pages** : `.github/workflows/deploy-pages.yml` publie
      `web/frontend/` à chaque push sur `main` (Settings → Pages → Source :
      "GitHub Actions", à activer une fois côté dépôt). `.nojekyll` ajouté.
- [x] Bouton « Copier le lien de partage » (config encodée en base64 dans l'URL,
      `#cfg=...`) — `partagerLien()` / bouton « Partager ».

## Rappel avant de committer / partager
1. Modif du cœur ? → répercuter dans les JS `js/generateur.js` / `js/validation.js` /
   `js/donnees.js` ET lancer `py tests\test_generateur.py`.
2. Le front reste **modulaire** (HTML / CSS / JS séparés) — ne pas refusionner.
3. Tout en **français**.
