"""VagrantForge — export d'un projet complet en archive .zip.

Au lieu de ne livrer que le `Vagrantfile`, `construire_zip_projet` produit
une archive prête à dézipper et lancer : le `Vagrantfile`, un dossier par
VM ayant un dossier partagé (`synced_folder`) avec un `.gitkeep` (Vagrant
râle si le dossier source d'un synced_folder n'existe pas), et un petit
`README.md` de démarrage généré à partir de la config.

Zéro dépendance : `zipfile` de la bibliothèque standard.
"""

import io
import zipfile
from datetime import date


def _readme_projet(config, nb_vms, ram_totale, cpu_total):
    provider = config.get("provider", "virtualbox")
    vms = config.get("vms", [])
    lignes = [
        "# Projet VagrantForge",
        "",
        f"Généré le {date.today().isoformat()} — {nb_vms} VM(s), "
        f"{ram_totale} Mo RAM, {cpu_total} vCPU, provider `{provider}`.",
        "",
        "## Démarrage",
        "",
        "```bash",
        "vagrant up",
        "```",
        "",
        "## Machines",
        "",
        "| VM | Box | IP | RAM | CPU |",
        "|----|-----|-----|-----|-----|",
    ]
    for vm in vms:
        lignes.append(
            f"| {vm.get('name', '?')} | {vm.get('box', '?')} | "
            f"{vm.get('ip') or 'dynamique'} | {vm.get('memory', '?')} Mo | "
            f"{vm.get('cpus', '?')} |"
        )

    acces = [(vm.get("name", "?"), p) for vm in vms for p in (vm.get("ports") or [])]
    if acces:
        lignes += [
            "",
            "## Accès (ports exposés)",
            "",
            "| VM | Port invité | Depuis ton PC |",
            "|----|-------------|-----------------|",
        ]
        for nom_vm, port in acces:
            hote = port.get("host")
            invite = port.get("guest")
            lignes.append(f"| {nom_vm} | {invite} | `localhost:{hote}` |")
        lignes.append(
            "\n*Si c'est un service web, ouvre `http://localhost:<port>` dans ton "
            "navigateur. Sinon (SSH, base de données, VPN, jeu, etc.), utilise "
            "l'outil adapté à ce port. `auto_correct: true` — si un port hôte "
            "est déjà pris, Vagrant en choisit un autre au `vagrant up` : "
            "vérifie avec `vagrant port <vm>`.*"
        )

    lignes += [
        "",
        "## Commandes utiles",
        "",
        "```bash",
        "vagrant status       # état des VMs",
        "vagrant ssh <nom>    # se connecter à une VM (SSH) ou",
        "vagrant halt         # éteindre",
        "vagrant destroy      # supprimer",
        "```",
        "",
        "---",
        "Généré par **VagrantForge** — générateur de Vagrantfile multi-VM.",
    ]
    return "\n".join(lignes) + "\n"


def _gitignore_projet():
    return "\n".join([
        "# Généré par VagrantForge — état local Vagrant, à ne jamais committer",
        ".vagrant/",
        "*.log",
        "",
    ])


def construire_zip_projet(config, vagrantfile, inventaire_ansible=None):
    """Construit une archive .zip (bytes) prête à distribuer.

    Contenu :
    - `Vagrantfile`
    - `README.md` (résumé de la config + commandes utiles + accès aux ports exposés)
    - `.gitignore` (exclut `.vagrant/`, l'état local propre à chaque machine hôte)
    - `<synced_folder>/.gitkeep` pour chaque VM ayant un dossier partagé
      relatif (évite l'erreur Vagrant « host path does not exist »)
    - `inventaire-ansible.ini` si fourni
    """
    vms = config.get("vms", [])
    ram_totale = sum(int(vm.get("memory", 0) or 0) for vm in vms)
    cpu_total = sum(int(vm.get("cpus", 0) or 0) for vm in vms)

    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Vagrantfile", vagrantfile)
        zf.writestr("README.md", _readme_projet(config, len(vms), ram_totale, cpu_total))
        zf.writestr(".gitignore", _gitignore_projet())
        if inventaire_ansible:
            zf.writestr("inventaire-ansible.ini", inventaire_ansible)

        dossiers_vus = set()
        for vm in vms:
            dossier = vm.get("synced_folder", "")
            if not dossier or vm.get("disable_synced_folder"):
                continue
            # Uniquement les chemins relatifs simples (./nom, nom/sous-dossier) :
            # un chemin absolu pointe déjà vers quelque chose qui existe côté hôte.
            # Note : `lstrip("./")` retire un ENSEMBLE de caractères, pas le
            # préfixe "./" — sur un dossier ".config" ça mangerait le point
            # utile. On retire donc explicitement le préfixe "./" s'il est
            # présent, rien d'autre.
            propre = dossier[2:] if dossier.startswith("./") else dossier
            propre = propre.strip("/")
            segments = [s for s in propre.split("/") if s]
            if (not propre or propre in dossiers_vus or dossier.startswith(("/", "~"))
                    or ":" in dossier or ".." in segments):
                continue
            dossiers_vus.add(propre)
            zf.writestr(f"{propre}/.gitkeep", "")

    return tampon.getvalue()
