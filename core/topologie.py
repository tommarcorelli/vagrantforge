"""VagrantForge — diagramme de topologie réseau (Mermaid).

`construire_topologie_mermaid(config)` transforme une config en un graphe
Mermaid (`graph LR`) montrant les VMs, leurs IP privées, les ports redirigés
et le réseau public éventuel — pratique pour visualiser un lab d'un coup
d'œil sans ouvrir le Vagrantfile. Zéro dépendance : c'est juste du texte,
rendu ensuite par mermaid.js côté navigateur (ou n'importe quel outil
compatible Mermaid, ex. https://mermaid.live).
"""

from .generateur import est_box_windows, nom_variable


def _etiquette_vm(vm):
    nom = vm.get("name", "vm")
    box = vm.get("box", "?")
    memoire = vm.get("memory", "?")
    cpus = vm.get("cpus", "?")
    ip = vm.get("ip", "")
    lignes = [nom, box, f"{memoire} Mo · {cpus} vCPU"]
    if ip:
        lignes.append(ip)
    return "<br/>".join(lignes)


def construire_topologie_mermaid(config):
    """Construit un diagramme Mermaid (`graph LR`) de la topologie du lab.

    Représente : un nœud « réseau privé » central relié à chaque VM (avec
    son IP si connue), un nœud « Internet » si au moins une VM a
    `public_network`, et des flèches en pointillé « hôte -> port » pour
    chaque redirection de port.
    """
    vms = config.get("vms", [])
    if not vms:
        return "graph LR\n  vide[\"Aucune VM dans la config\"]\n"

    lignes = ["graph LR", '  reseau(("Réseau privé<br/>Vagrant"))']

    for vm in vms:
        var = nom_variable(vm.get("name", "vm"))
        icone = "🪟" if est_box_windows(vm) else "🐧"
        etiquette = f"{icone}<br/>{_etiquette_vm(vm)}"
        lignes.append(f'  {var}["{etiquette}"]')
        lignes.append(f"  reseau --- {var}")

        for port in vm.get("ports", []) or []:
            guest = port.get("guest")
            host = port.get("host")
            if guest is None or host is None:
                continue
            hote_id = f"hote_{var}_{host}"
            lignes.append(f'  {hote_id}(["hôte:{host}"])')
            lignes.append(f"  {hote_id} -.->|forward| {var}")
            lignes.append(f"  {var} -.-|:{guest}| {hote_id}")

        if vm.get("public_network"):
            lignes.append(f"  internet((Internet)) --- {var}")

    return "\n".join(lignes) + "\n"
