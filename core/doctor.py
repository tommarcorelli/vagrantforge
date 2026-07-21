"""VagrantForge — diagnostic de l'environnement local (`forge doctor`).

Vérifie ce qui est effectivement installé sur la machine (Vagrant, les
providers, Ruby, Ansible…) pour éviter la surprise classique « le
Vagrantfile est parfait mais `vagrant up` ne trouve pas VirtualBox ».
100 % local (aucun réseau), zéro dépendance : `shutil.which` + `subprocess`.
"""

import shutil
import subprocess

# (nom affiché, exécutable, arguments version, obligatoire)
OUTILS = [
    ("Vagrant",              "vagrant",         ["--version"], True),
    ("VirtualBox",           "VBoxManage",      ["--version"], False),
    ("VMware Workstation/Fusion (vmrun)", "vmrun", [],          False),
    ("libvirt (virsh)",      "virsh",           ["--version"], False),
    ("Ruby",                 "ruby",            ["-v"],         False),
    ("Ansible",              "ansible",         ["--version"], False),
    ("Git",                  "git",             ["--version"], False),
]


def _version(executable, args):
    chemin = shutil.which(executable)
    if not chemin:
        return None, None
    try:
        resultat = subprocess.run(
            [chemin, *args], capture_output=True, text=True, timeout=5, check=False,
        )
        sortie = (resultat.stdout or resultat.stderr or "").strip().splitlines()
        return chemin, (sortie[0] if sortie else "")
    except (OSError, subprocess.SubprocessError):
        return chemin, ""


def diagnostiquer():
    """Retourne une liste de rapports `{nom, present, obligatoire, chemin, version}`."""
    rapports = []
    for nom, executable, args, obligatoire in OUTILS:
        chemin, version = _version(executable, args)
        rapports.append({
            "nom": nom,
            "present": chemin is not None,
            "obligatoire": obligatoire,
            "chemin": chemin,
            "version": version,
        })
    return rapports


def au_moins_un_provider(rapports):
    """Vrai si au moins un provider Vagrant (VirtualBox/VMware/libvirt) est détecté."""
    providers = {"VirtualBox", "VMware Workstation/Fusion (vmrun)", "libvirt (virsh)"}
    return any(r["present"] for r in rapports if r["nom"] in providers)
