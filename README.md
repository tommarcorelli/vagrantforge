# 🔨 VagrantForge

**Forge des `Vagrantfile` multi-VM proprement — sans écrire une ligne de Ruby.**

VagrantForge décrit une infra de labs (plusieurs VMs, réseau privé, ports,
provisioning) sous forme d'une config simple, et génère un `Vagrantfile` propre,
commenté et **validé**. Trois interfaces, **un seul cœur** partagé :

| Interface | Pour qui | Point d'entrée |
|-----------|----------|----------------|
| 🖥️ **Web** | tout le monde, aperçu en direct | `web/frontend/index.html` |
| ⌨️ **CLI** | scripts, CI, terminal | `cli/main.py` |
| 🧩 **API** | intégrations HTTP | `web/api/main.py` |

---

## ✨ Ce que ça fait

- **Multi-VM** : autant de machines que tu veux, chacune avec son OS, RAM, CPU, IP.
- **Catalogue d'OS lisible** : les vraies images publiques par leur **nom complet**
  (Debian 10/11/12/testing, Ubuntu 18.04→24.04 LTS, Rocky, Alma, Fedora, Oracle
  Linux, CentOS Stream, Alpine, Arch, openSUSE, Kali, FreeBSD… ~35 images),
  regroupées par famille. Plus besoin de deviner `debian/quoi64`.
- **RAM & CPU en listes** : niveaux nommés (512 Mo → 32 Go, 1 → 16 cœurs,
  « recommandé » repéré), option personnalisée.
- **Langue & clavier de la VM** : Français (AZERTY), Anglais, Espagnol… réglés
  automatiquement au premier démarrage.
- **Aide au provisioning** : une **bibliothèque de ~40 commandes** prêtes,
  classées par thème (système, web/proxy, bases de données, conteneurs &
  orchestration, langages, files de messages, réseau/VPN, supervision/logs,
  sauvegarde, sécurité) qui s'insèrent dans le script.
- **3 providers** : `virtualbox`, `vmware_desktop`, `libvirt` (global ou par VM).
- **Réseau** : IP privées auto-incrémentées, réseau public en pont, ports redirigés.
- **Presets prêts à l'emploi** : `solo`, `k3s`, `lamp`, `devsecops`, `pentest`,
  `monitoring` (Prometheus/Grafana), `elk` (Elasticsearch/Kibana), `wordpress`,
  `gitlab-runner`, `nextcloud`, `windows-ad` (contrôleur de domaine Active
  Directory + poste client, WinRM).
- **Disques additionnels par VM** : ajoute un ou plusieurs disques virtuels
  en plus du disque système (VirtualBox `createhd`/`storageattach`
  idempotent, libvirt `lv.storage`) — utile pour séparer les données du
  système.
- **Inventaire Ansible** : génère un inventaire statique (format INI) à
  partir de la config, avec groupes automatiques par préfixe de nom
  (`k3s-master`/`k3s-worker1` → groupe `[k3s]`) et détection SSH/WinRM.
  `forge inventaire config.json`, `POST /api/inventaire`, ou le bouton
  « Inventaire Ansible » côté web.
- **Export de projet complet en .zip** : Vagrantfile + `README.md` généré +
  arborescence des dossiers partagés (`.gitkeep`) + inventaire Ansible en
  option, prêt à dézipper et lancer. `forge exporter config.json -o
  projet.zip`, ou `POST /api/exporter`.
- **Lien de partage** : encode toute la config dans l'URL (`#cfg=...`,
  base64) pour la partager en un clic sans passer par un fichier — bouton
  « Partager » côté web.
- **Thème clair / sombre** : bascule persistante (respecte aussi la
  préférence système au premier lancement).
- **Installable en PWA** : manifest + service worker (app shell en cache,
  fonctionne hors-ligne une fois chargée), icône néon dédiée.
- **Interface bilingue FR/EN** : bouton de bascule, persisté — couvre la nav,
  le formulaire de VM, la modale d'aide. Les messages de validation et le
  contenu généré restent en français (voir `js/i18n.js`).
- **Déploiement GitHub Pages en 1 push** : workflow prêt à l'emploi
  (`.github/workflows/deploy-pages.yml`), il suffit d'activer Pages côté dépôt.
- **Gabarits personnalisés** : en-tête, agencement libres via un simple fichier
  texte (`string.Template` stdlib, pas de dépendance Jinja2) — voir
  [Gabarits personnalisés](#-gabarits-personnalisés).
- **Lint du fichier généré** : vérifie que le Vagrantfile produit est
  structurellement cohérent (blocs `do…end`, heredocs bien fermés) avant de
  l'écrire ; utilise `ruby -c` en plus si Ruby est installé.
- **Vérification du catalogue de box** : `forge verifier-box` compare la table
  de compatibilité box/provider à Vagrant Cloud pour repérer ce qui a bougé.
- **Vraies versions d'image** : `forge versions-box <box>` en CLI, ou le
  bouton « 🔎 Versions dispo » côté web (essaie une requête directe depuis le
  navigateur, sans serveur — voir [ci-dessous](#-vérification-du-catalogue-de-box)
  pour les limites).
- **Windows (WinRM)** : sélectionne une box Windows (`gusztavvargadr/windows-*`)
  et VagrantForge bascule automatiquement en communicateur WinRM et
  provisioning PowerShell (`#ps1_sysnative`) — plus de champs SSH/locale
  inadaptés.
- **Validation en français** : erreurs bloquantes (noms/IP dupliqués, RAM absurde…)
  **et** avertissements (OS incompatible avec le provider, mot de passe en clair…),
  avec pastille rouge sur les VMs en faute.
- **Aide contextuelle** : bulles ⓘ sur chaque champ + modale « Comment ça marche ».
- **Aperçu instantané** style éditeur (numéros de ligne), coloration syntaxique,
  copie/téléchargement, import/export JSON, sauvegarde automatique locale.
- **Vrai design** : page d'accueil (hero) avec dégradé animé, panneaux vitrés
  (glassmorphism), badges dégradés, footer — **responsive + menu hamburger**.

Le tout **100 % en français**, sans dépendance pour le cœur (stdlib uniquement).

## 🎨 Frontend — structure modulaire

Le frontend est **découpé** (HTML / CSS / JS séparés), en CSS moderne
(variables + nesting natif, sensation SCSS sans étape de build) :

```
web/frontend/
├── index.html            structure de la page (hero, app, modale)
├── css/style.css         tout le style
└── js/
    ├── donnees.js        catalogue OS, compat, niveaux RAM/CPU, langues, snippets, presets
    ├── generateur.js     construction du Vagrantfile + coloration
    ├── validation.js     validation en direct
    └── app.js            interface (état, rendu, événements)
```

**Partager :** zippe le dossier `web/frontend/` (ou dépose-le sur GitHub Pages /
Netlify). Il fonctionne aussi en `file://` en ouvrant `index.html`.

**GitHub Pages en 1 push :** le workflow `.github/workflows/deploy-pages.yml`
publie automatiquement `web/frontend/` à chaque push sur `main`. Il suffit
d'activer Pages une fois : `Settings → Pages → Build and deployment → Source :
"GitHub Actions"`.

---

## 🚀 Démarrage rapide

### Interface web (aucune installation)

Ouvre simplement le fichier :

```
web/frontend/index.html
```

Tout se passe dans le navigateur (génération, validation, presets). Aucun serveur requis.

### CLI

```bash
# Générer depuis un preset
python cli/main.py preset k3s -o Vagrantfile

# Générer depuis ta propre config
python cli/main.py generer exemples/lab-web.json -o Vagrantfile

# Valider sans générer
python cli/main.py valider exemples/lab-web.json

# Lister les presets
python cli/main.py presets

# Piper depuis stdin
cat exemples/lab-web.json | python cli/main.py generer -

# Générer avec un gabarit personnalisé (en-tête/agencement maison)
python cli/main.py generer exemples/lab-web.json --gabarit exemples/gabarit-simple.txt

# Générer un inventaire Ansible (INI) depuis une config
python cli/main.py inventaire exemples/lab-web.json -o inventaire.ini

# Exporter un projet complet en .zip (Vagrantfile + arborescence + README)
python cli/main.py exporter exemples/lab-web.json -o projet.zip --avec-inventaire

# Vérifier que le catalogue de box colle encore à Vagrant Cloud (réseau requis)
python cli/main.py verifier-box
python cli/main.py verifier-box --box debian/bookworm64

# Voir les vraies versions publiées d'une box (réseau requis)
python cli/main.py versions-box debian/bookworm64
```

> Sous Windows, utilise `py` à la place de `python` si besoin.

### Serveur web + API (optionnel)

```bash
pip install -r requirements.txt
python web/api/main.py        # http://127.0.0.1:5000
```

| Route | Méthode | Rôle |
|-------|---------|------|
| `/` | GET | l'interface web |
| `/api/presets` | GET | liste des presets |
| `/api/preset/<nom>?sous_reseau=192.168.56` | GET | config d'un preset |
| `/api/valider` | POST | `{erreurs, avertissements, valide}` |
| `/api/generer` | POST | `{vagrantfile, erreurs, avertissements, lint_erreurs, lint_avertissements}` — corps : la config JSON brute (historique), ou `{"config": {...}, "gabarit": "texte"}` |
| `/api/verifier-box[?box=nom]` | GET | compare le catalogue local à Vagrant Cloud (réseau sortant requis côté serveur) |
| `/api/box-versions?box=nom` | GET | vraies versions publiées d'une box sur Vagrant Cloud (réseau requis) |

---

## 🖋️ Gabarits personnalisés

Par défaut, `construire_vagrantfile(config)` produit le Vagrantfile standard.
Pour personnaliser l'en-tête ou l'agencement sans toucher au cœur Python, on
peut passer un **gabarit** : un simple fichier texte avec des variables
`$NOM` (`string.Template` de la bibliothèque standard — toujours **zéro
dépendance**, pas de Jinja2).

```bash
forge generer config.json --gabarit mon_style.txt -o Vagrantfile
```

Variables disponibles dans un gabarit :

| Variable | Contenu |
|----------|---------|
| `$ENTETE` | bannière de commentaires + `Vagrant.configure(...)` + `box_check_update` |
| `$VMS` | bloc(s) `config.vm.define ... end` de toutes les VMs |
| `$PIED` | le `end` final qui ferme `Vagrant.configure` |
| `$DATE` | date de génération (AAAA-MM-JJ) |
| `$NB_VMS` | nombre de VMs |
| `$RAM_TOTALE` | RAM totale en Mo |
| `$CPU_TOTAL` | total de vCPU |
| `$PROVIDER` | provider global |

Une variable inconnue dans un gabarit est laissée telle quelle (pas
d'exception) : une coquille ne t'empêche pas de voir le résultat. Exemple
minimal dans `exemples/gabarit-simple.txt`.

---

## 🔍 Lint du Vagrantfile généré

Chaque génération (CLI comme API) passe par un lint léger avant l'écriture :
vérification des blocs `do … end` équilibrés et des heredocs shell
(`<<-SHELL … SHELL`) bien refermés, en pur Python (zéro dépendance). Si
l'exécutable `ruby` est présent dans le PATH, `ruby -c` (vérif de syntaxe
seule, rien n'est exécuté) est utilisé en complément pour une vraie
validation Ruby.

---

## 📦 Vérification du catalogue de box

`core/schema.py::BOX_PROVIDERS` recense à la main quels providers Vagrant
Cloud publie pour chaque box — une liste qui peut se périmer. `forge
verifier-box` interroge l'API publique Vagrant Cloud et signale les écarts
(box retirée, provider ajouté ou disparu). C'est un outil de maintenance
(réseau requis), pas une étape de la génération normale.

Dans le même esprit, `forge versions-box <box>` (en CLI) va chercher les
**vrais numéros de version publiés** au lieu de laisser deviner un format —
chaque box a sa propre convention (Debian : `12.20240905.1`, Ubuntu :
`20240701.0.0`…).

Côté web, le bouton **« 🔎 Versions dispo »** (à côté du champ « Version de
l'image ») essaie dans l'ordre :
1. une requête **directe depuis le navigateur** vers l'API Vagrant Cloud —
   ça marche même en ouvrant `index.html` en local, **sans serveur**, tant
   que Vagrant Cloud autorise la requête cross-origin et que tu es en ligne ;
2. si ça échoue (hors-ligne, CORS bloqué…) et que tu as lancé le petit
   serveur (`python web/api/main.py`), il relaie la requête côté serveur
   (pas soumis au CORS du navigateur) ;
3. sinon, un lien **« Voir sur Vagrant Cloud »** (toujours présent à côté du
   champ) ouvre la page de la box dans un nouvel onglet — garanti de
   marcher, aucune requête ni serveur nécessaire.

---

## 🪟 Windows (WinRM)

Les VMs Windows ne se pilotent pas en SSH mais en **WinRM**, et le
provisioning shell doit être du **PowerShell**, pas du Bash. VagrantForge le
détecte automatiquement :

- Choisis une box du groupe **Windows (WinRM)** dans le catalogue (namespace
  `gusztavvargadr/…`), ou force-le explicitement avec `"guest_os": "windows"`
  dans la config JSON.
- Le générateur bascule alors sur `config.vm.guest = :windows`,
  `communicator = "winrm"`, un `boot_timeout` généreux (premier démarrage
  Windows plus lent), et des identifiants **`winrm_username`/`winrm_password`**
  au lieu de `ssh_username`/`ssh_password`.
- Le script de provisioning `"shell"` est automatiquement préfixé par
  `#ps1_sysnative` (convention Vagrant qui le fait exécuter en PowerShell) —
  écris directement du PowerShell dans le champ script.
- Les champs `locale`/`keymap` (spécifiques Debian/Ubuntu) sont ignorés et la
  validation le signale si tu les as quand même remplis.

```json
{
  "provider": "virtualbox",
  "vms": [{
    "name": "win-dc",
    "box": "gusztavvargadr/windows-server",
    "memory": 4096,
    "cpus": 2,
    "ip": "192.168.56.20",
    "winrm_username": "vagrant",
    "winrm_password": "vagrant",
    "provision": {"type": "shell", "script": "Install-WindowsFeature -Name AD-Domain-Services\n"}
  }]
}
```

---

## 🧱 Schéma de config

```json
{
  "provider": "virtualbox",
  "box_check_update": false,
  "vms": [
    {
      "name": "web",
      "box": "debian/bookworm64",
      "box_version": "",
      "memory": 1024,
      "cpus": 1,
      "ip": "192.168.56.10",
      "provider": "",
      "gui": false,
      "public_network": false,
      "locale": "fr_FR.UTF-8",
      "keymap": "fr",
      "synced_folder": "./web",
      "disable_synced_folder": false,
      "ssh_username": "",
      "ssh_password": "",
      "root_password": "",
      "ports": [{ "guest": 80, "host": 8080 }],
      "provision": { "type": "shell", "script": "apt-get update -y\n" }
    }
  ]
}
```

- `provider` (par VM) vide → hérite du provider global.
- `provision.type` : `shell` | `ansible` | `none` (pour `ansible`, `script` = chemin du playbook).

---

## 🗂️ Structure

```
vagrantforge/
├── core/                 cœur partagé (zéro dépendance)
│   ├── generateur.py     construction du Vagrantfile + inventaire Ansible + gabarits
│   ├── schema.py         validation + table de compat box/provider
│   ├── presets.py        labs prêts à l'emploi (11 presets)
│   ├── lint.py           lint structurel du Vagrantfile généré (+ ruby -c si dispo)
│   ├── verif_box.py      vérification du catalogue de box vs Vagrant Cloud
│   └── export_projet.py  export d'un projet complet en .zip
├── cli/main.py           interface ligne de commande
├── web/
│   ├── api/main.py       serveur Flask (optionnel)
│   └── frontend/         interface web (HTML / CSS / JS séparés)
│       ├── index.html
│       ├── manifest.webmanifest, service-worker.js   PWA installable
│       ├── icons/        icône néon (svg + png 192/512)
│       ├── css/style.css thème clair/sombre via [data-theme]
│       └── js/           i18n · donnees · generateur · validation · app
├── tests/                tests du cœur
├── exemples/             configs d'exemple + gabarit-simple.txt
└── requirements.txt      Flask (uniquement pour l'API web)
```

Le JS du frontend (`js/generateur.js`, `js/validation.js`, `js/donnees.js`)
**reflète fidèlement** le cœur Python (`generateur`, `schema`, `presets`) :
mêmes règles de génération et de validation des deux côtés.

---

## 🧪 Tests

```bash
python -m pytest tests/ -v
# ou sans pytest :
python tests/test_generateur.py
```

---

## 📄 Licence

Projet perso — usage libre.
