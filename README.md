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
  (« Debian 12 Bookworm », « Ubuntu 24.04 LTS », Rocky, Alma, Alpine, Arch, Kali,
  FreeBSD…), regroupées par famille. Plus besoin de deviner `debian/quoi64`.
- **RAM & CPU en listes** : niveaux nommés (512 Mo → 8 Go, « recommandé » repéré),
  option personnalisée.
- **Langue & clavier de la VM** : Français (AZERTY), Anglais, Espagnol… réglés
  automatiquement au premier démarrage.
- **Aide au provisioning** : une **bibliothèque de commandes** prêtes (MàJ système,
  Nginx, Docker, Node, PostgreSQL, UFW, fail2ban…) qui s'insèrent dans le script.
- **3 providers** : `virtualbox`, `vmware_desktop`, `libvirt` (global ou par VM).
- **Réseau** : IP privées auto-incrémentées, réseau public en pont, ports redirigés.
- **Presets prêts à l'emploi** : `solo`, `k3s`, `lamp`, `devsecops`, `pentest`.
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
| `/api/generer` | POST | `{vagrantfile, erreurs, avertissements}` |

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
│   ├── generateur.py     construction du Vagrantfile
│   ├── schema.py         validation + table de compat box/provider
│   └── presets.py        labs prêts à l'emploi
├── cli/main.py           interface ligne de commande
├── web/
│   ├── api/main.py       serveur Flask (optionnel)
│   └── frontend/         interface web (HTML / CSS / JS séparés)
│       ├── index.html
│       ├── css/style.css
│       └── js/           donnees · generateur · validation · app
├── tests/                tests du cœur
├── exemples/             configs d'exemple
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
