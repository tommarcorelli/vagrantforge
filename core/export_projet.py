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
        "Généré par [VagrantForge](https://github.com/) — "
        "https://github.com/ (voir le lien du projet).",
    ]
    return "\n".join(lignes) + "\n"


def construire_zip_projet(config, vagrantfile, inventaire_ansible=None):
    """Construit une archive .zip (bytes) prête à distribuer.

    Contenu :
    - `Vagrantfile`
    - `README.md` (résumé de la config + commandes utiles)
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
        if inventaire_ansible:
            zf.writestr("inventaire-ansible.ini", inventaire_ansible)

        dossiers_vus = set()
        for vm in vms:
            dossier = vm.get("synced_folder", "")
            if not dossier or vm.get("disable_synced_folder"):
                continue
            # Uniquement les chemins relatifs simples (./nom, nom/sous-dossier) :
            # un chemin absolu pointe déjà vers quelque chose qui existe côté hôte.
            propre = dossier.lstrip("./").strip("/")
            if not propre or propre in dossiers_vus or dossier.startswith(("/", "~")) or ":" in dossier:
                continue
            dossiers_vus.add(propre)
            zf.writestr(f"{propre}/.gitkeep", "")

    return tampon.getvalue()
