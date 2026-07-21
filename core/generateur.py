"""VagrantForge — génération du Vagrantfile à partir d'une config JSON.

Le schéma de config est le même que celui du générateur web (voir README.md).
Les champs sont en anglais car ils collent au vocabulaire Vagrant lui-même,
mais tout le reste (messages, commentaires générés) est en français.

Génération avec gabarit personnalisé
-------------------------------------
Par défaut, `construire_vagrantfile(config)` produit le Vagrantfile standard.
Pour personnaliser l'en-tête ou l'agencement sans toucher au cœur Python, on
peut fournir un **gabarit** (texte avec des variables `$NOM`, syntaxe
`string.Template` de la stdlib — pas de dépendance externe type Jinja2) :

    forge generer config.json --gabarit mon_style.txt

Variables disponibles dans un gabarit (voir aussi `GABARIT_DEFAUT`) :
    $ENTETE       bannière de commentaires + Vagrant.configure(...) + box_check_update
    $VMS          bloc(s) `config.vm.define ... end` de toutes les VMs
    $PIED         le `end` final qui ferme Vagrant.configure
    $DATE         date de génération (AAAA-MM-JJ)
    $NB_VMS       nombre de VMs
    $RAM_TOTALE   RAM totale en Mo
    $CPU_TOTAL    total de vCPU
    $PROVIDER     provider global

Les variables inconnues dans un gabarit sont laissées telles quelles
(`safe_substitute`) : une coquille dans un gabarit personnalisé ne doit pas
empêcher de voir le résultat.
"""

import re
from datetime import date
from string import Template

PROVIDERS_CONNUS = ("virtualbox", "vmware_desktop", "libvirt")

# Namespaces/box connus qui publient des images Windows (WinRM, pas SSH).
PREFIXES_BOX_WINDOWS = ("gusztavvargadr/", "StefanScherer/")


def est_box_windows(vm):
    """Détermine si une VM doit être traitée comme un invité Windows.

    Priorité au champ explicite `guest_os` (« windows » ou « linux » /
    absent). À défaut, déduit du nom de la box via les namespaces Windows
    connus — pratique pour les configs qui ne renseignent pas `guest_os`.
    """
    guest_os = vm.get("guest_os")
    if guest_os:
        return guest_os == "windows"
    box = vm.get("box", "") or ""
    return box.startswith(PREFIXES_BOX_WINDOWS)


def echapper(valeur):
    """Échappe les guillemets doubles pour insertion dans une string Ruby."""
    return str(valeur).replace('"', '\\"')


def nom_variable(nom):
    """Transforme un nom de VM en identifiant Ruby valide."""
    propre = re.sub(r"[^a-zA-Z0-9_]", "_", nom or "vm")
    if propre[0].isdigit():
        propre = "vm_" + propre
    return propre


def bloc_provider(var, provider, memoire, cpus, nom, gui=False, ip_statique=False):
    """Bloc de configuration spécifique au provider."""
    if provider == "virtualbox":
        return (
            f'    {var}.vm.provider "virtualbox" do |vb|\n'
            f'      vb.name = "{echapper(nom)}"\n'
            f'      vb.memory = {memoire}\n'
            f'      vb.cpus = {cpus}\n'
            f'      vb.gui = {"true" if gui else "false"}\n'
            f'    end\n'
        )
    if provider == "vmware_desktop":
        reglage_reseau = ""
        if ip_statique:
            reglage_reseau = (
                '      vw.vmx["ethernet0.virtualDev"] = "vmxnet3"'
                "  # évite les soucis d'IP statique avec l'adaptateur par défaut\n"
            )
        return (
            f'    {var}.vm.provider "vmware_desktop" do |vw|\n'
            f'      vw.gui = {"true" if gui else "false"}\n'
            f'      vw.vmx["displayName"] = "{echapper(nom)}"\n'
            f'      vw.vmx["memsize"] = "{memoire}"\n'
            f'      vw.vmx["numvcpus"] = "{cpus}"\n'
            f'      vw.vmx["cpuid.coresPerSocket"] = "{cpus}"\n'
            f'{reglage_reseau}'
            f'    end\n'
        )
    if provider == "libvirt":
        return (
            f'    {var}.vm.provider "libvirt" do |lv|\n'
            f'      lv.memory = {memoire}\n'
            f'      lv.cpus = {cpus}\n'
            f'    end\n'
        )
    return ""


def bloc_disques(var, provider, disques):
    """Bloc(s) de disque(s) additionnel(s) pour une VM.

    `disques` : liste de `{"name": "data", "size_gb": 20}`. Chaque disque
    additionnel est attaché en plus du disque système. Le nom sert de port
    d'attache stable (VirtualBox) ou de volume (libvirt) — nécessaire pour
    que `vagrant up` réutilise le même disque au lieu d'en recréer un neuf
    à chaque fois.

    - VirtualBox : `vb.customize` avec `createhd` (idempotent — recrée le
      disque uniquement s'il n'existe pas déjà) + `storageattach`.
    - libvirt : `lv.storage :file` (plugin vagrant-libvirt).
    - vmware_desktop : non supporté nativement par le plugin Vagrant sans
      manipulation manuelle du .vmx ; un commentaire l'indique.
    """
    disques = [d for d in (disques or []) if d.get("size_gb")]
    if not disques:
        return ""
    lignes = []
    if provider == "virtualbox":
        for i, d in enumerate(disques):
            nom_disque = d.get("name") or f"disque{i + 1}"
            taille_mo = int(d["size_gb"]) * 1024
            # Nom de fichier connu à la génération (pas besoin d'interpolation Ruby
            # #{...} à l'exécution — en plus, #{...} perturbe le lint, qui traite
            # tout ce qui suit un « # » sur une ligne comme un commentaire).
            fichier = echapper(f"{var}_{nom_disque}_{i}.vdi")
            lignes.append(
                f'    {var}.vm.provider "virtualbox" do |vb|\n'
                f'      disque_{i} = File.join(Dir.pwd, ".vagrant", "disques", "{fichier}")\n'
                f'      FileUtils.mkdir_p(File.dirname(disque_{i})) unless '
                f'Dir.exist?(File.dirname(disque_{i}))\n'
                f'      vb.customize ["createhd", "--filename", disque_{i}, '
                f'"--size", {taille_mo}] unless File.exist?(disque_{i})\n'
                f'      vb.customize ["storageattach", :id, "--storagectl", "SATA Controller", '
                f'"--port", {i + 1}, "--device", 0, "--type", "hdd", "--medium", disque_{i}]\n'
                f'    end\n'
            )
    elif provider == "libvirt":
        for i, d in enumerate(disques):
            nom = d.get("name") or f"disque{i + 1}"
            lignes.append(
                f'    {var}.vm.provider "libvirt" do |lv|\n'
                f'      lv.storage :file, size: "{int(d["size_gb"])}G", '
                f'path: "{echapper(nom)}-disque{i}.qcow2"\n'
                f'    end\n'
            )
    else:
        noms = ", ".join(d.get("name") or f"disque{i + 1}" for i, d in enumerate(disques))
        lignes.append(
            f"    # Disque(s) additionnel(s) demandé(s) ({noms}) : non automatisable avec le "
            f'provider "{provider}" — à créer/attacher manuellement.\n'
        )
    return "\n".join(l.rstrip("\n") for l in lignes) + "\n"


def bloc_locale(var, locale, keymap):
    """Bloc de provisioning qui règle la langue et le clavier (familles Debian/Ubuntu)."""
    if not locale and not keymap:
        return ""
    lignes = ["      # ── Langue & clavier (familles Debian/Ubuntu) ──",
              "      export DEBIAN_FRONTEND=noninteractive"]
    if locale:
        lignes.append(f"      sed -i 's/^# *{locale} UTF-8/{locale} UTF-8/' /etc/locale.gen")
        lignes.append("      locale-gen")
        lignes.append(f"      update-locale LANG={locale}")
    if keymap:
        lignes.append(f'      echo "XKBLAYOUT={keymap}" > /etc/default/keyboard')
        lignes.append("      setupcon -k --force || true")
    corps = "\n".join(lignes)
    return (
        f'    {var}.vm.provision "shell", inline: <<-SHELL\n'
        f'{corps}\n'
        f'    SHELL\n'
    )


def bloc_provision(var, provision, mdp_root="", windows=False):
    """Bloc(s) de provisioning (shell inline, ansible, ou juste le mot de passe root).

    `windows=True` bascule le script inline en PowerShell (marqueur
    `#ps1_sysnative` reconnu par Vagrant) au lieu de Bash, et adapte le
    changement de mot de passe root/administrateur en conséquence.
    """
    provision = provision or {}
    type_prov = provision.get("type", "none")
    script = provision.get("script", "")

    if type_prov == "shell":
        if mdp_root:
            if windows:
                script = (
                    f"$mdp = ConvertTo-SecureString \"{echapper(mdp_root)}\" -AsPlainText -Force\n"
                    f"Set-LocalUser -Name \"Administrator\" -Password $mdp\n"
                ) + script
            else:
                script = f'echo "root:{echapper(mdp_root)}" | chpasswd\n' + script
        if windows:
            # #ps1_sysnative en première ligne : convention Vagrant pour faire
            # exécuter le script inline par PowerShell plutôt que cmd.exe.
            script = "#ps1_sysnative\n" + script
        indente = "\n".join("      " + ligne for ligne in script.split("\n"))
        return (
            f'    {var}.vm.provision "shell", inline: <<-SHELL\n'
            f'{indente}\n'
            f'    SHELL\n'
        )
    if type_prov == "ansible":
        bloc = (
            f'    {var}.vm.provision "ansible" do |ansible|\n'
            f'      ansible.playbook = "{echapper(script)}"\n'
            f'    end\n'
        )
        if mdp_root:
            bloc += (
                f'    {var}.vm.provision "shell", '
                f'inline: \'echo "root:{echapper(mdp_root)}" | chpasswd\'\n'
            )
        return bloc
    if type_prov == "none" and mdp_root:
        return (
            f'    {var}.vm.provision "shell", '
            f'inline: \'echo "root:{echapper(mdp_root)}" | chpasswd\'\n'
        )
    return ""


def _lignes_vm(vm, provider_global):
    """Construit les lignes du bloc `config.vm.define ... end` d'une seule VM."""
    nom = vm.get("name", "vm")
    var = nom_variable(nom)
    box = vm.get("box", "debian/bookworm64")
    version_box = vm.get("box_version", "")
    memoire = vm.get("memory", 1024)
    cpus = vm.get("cpus", 1)
    ip = vm.get("ip", "")
    reseau_public = vm.get("public_network", False)
    dossier_sync = vm.get("synced_folder", "")
    sync_desactive = vm.get("disable_synced_folder", False)
    ports = vm.get("ports", [])
    provider = vm.get("provider") or provider_global
    gui = vm.get("gui", False)

    lignes = []
    recap_ip = ip if ip else "IP dynamique"
    lignes.append(f"  # ── {nom} — {box} | {memoire} Mo | {cpus} vCPU | {recap_ip}")
    lignes.append(f'  config.vm.define "{echapper(nom)}" do |{var}|')
    lignes.append(f'    {var}.vm.box = "{echapper(box)}"')
    if version_box:
        lignes.append(f'    {var}.vm.box_version = "{echapper(version_box)}"')
    lignes.append(f'    {var}.vm.hostname = "{echapper(nom)}"')
    if ip:
        lignes.append(f'    {var}.vm.network "private_network", ip: "{echapper(ip)}"')
    if reseau_public:
        lignes.append(f'    {var}.vm.network "public_network"  # pont réseau, interface choisie au démarrage')
    for port in ports:
        lignes.append(
            f'    {var}.vm.network "forwarded_port", '
            f'guest: {port["guest"]}, host: {port["host"]}, '
            f'auto_correct: true, id: "port-{port["guest"]}"'
        )
    if sync_desactive:
        lignes.append(f'    {var}.vm.synced_folder ".", "/vagrant", disabled: true')
    elif dossier_sync:
        type_dossier = {"virtualbox": "virtualbox", "vmware_desktop": "vmware"}.get(provider)
        type_str = f', type: "{type_dossier}"' if type_dossier else ""
        lignes.append(f'    {var}.vm.synced_folder "{echapper(dossier_sync)}", "/vagrant"{type_str}')

    windows = est_box_windows(vm)

    utilisateur_ssh = vm.get("ssh_username", "")
    mdp_ssh = vm.get("ssh_password", "")
    utilisateur_winrm = vm.get("winrm_username", "")
    mdp_winrm = vm.get("winrm_password", "")

    if windows:
        # Invité Windows : pas de SSH, on pilote en WinRM. Premier démarrage
        # souvent lent (Sysprep) → délai de boot généreux.
        lignes.append(f"    {var}.vm.guest = :windows")
        lignes.append(f'    {var}.vm.communicator = "winrm"')
        lignes.append(f"    {var}.vm.boot_timeout = 600")
        if utilisateur_winrm:
            lignes.append(f'    {var}.winrm.username = "{echapper(utilisateur_winrm)}"')
        if mdp_winrm:
            lignes.append(f'    {var}.winrm.password = "{echapper(mdp_winrm)}"')
    else:
        if utilisateur_ssh:
            lignes.append(f'    {var}.ssh.username = "{echapper(utilisateur_ssh)}"')
        if mdp_ssh:
            lignes.append(f'    {var}.ssh.password = "{echapper(mdp_ssh)}"')
            lignes.append(f'    {var}.ssh.insert_key = false')

    bloc_p = bloc_provider(var, provider, memoire, cpus, nom, gui, ip_statique=bool(ip))
    if bloc_p:
        lignes.append(bloc_p.rstrip("\n"))

    bloc_d = bloc_disques(var, provider, vm.get("extra_disks"))
    if bloc_d:
        lignes.append(bloc_d.rstrip("\n"))

    if not windows:
        bloc_l = bloc_locale(var, vm.get("locale", ""), vm.get("keymap", ""))
        if bloc_l:
            lignes.append(bloc_l.rstrip("\n"))

    bloc_prov = bloc_provision(var, vm.get("provision"), vm.get("root_password", ""), windows=windows)
    if bloc_prov:
        lignes.append(bloc_prov.rstrip("\n"))

    lignes.append("  end")
    return lignes


def construire_sections(config):
    """Construit les sections du Vagrantfile + métadonnées, pour un gabarit personnalisé.

    Retourne un dict de chaînes prêtes à l'emploi dans un `string.Template`
    (voir le docstring du module) : ENTETE, VMS, PIED, DATE, NB_VMS,
    RAM_TOTALE, CPU_TOTAL, PROVIDER.
    """
    provider_global = config.get("provider", "virtualbox")
    verif_box = "true" if config.get("box_check_update", False) else "false"
    vms = config.get("vms", [])

    total_ram = sum(int(vm.get("memory", 1024) or 0) for vm in vms)
    total_cpu = sum(int(vm.get("cpus", 1) or 0) for vm in vms)

    entete = []
    entete.append("# -*- mode: ruby -*-")
    entete.append("# vi: set ft=ruby :")
    entete.append("#")
    entete.append("# " + "=" * 66)
    entete.append(f"#  Vagrantfile généré par VagrantForge — {date.today().isoformat()}")
    entete.append(f"#  {len(vms)} VM(s) | {total_ram} Mo RAM | {total_cpu} vCPU | provider : {provider_global}")
    entete.append("#  Démarrage : vagrant up   |   État : vagrant status")
    entete.append("# " + "=" * 66)
    entete.append("")
    entete.append('Vagrant.require_version ">= 2.3.0"')
    entete.append("")
    entete.append('Vagrant.configure("2") do |config|')
    entete.append(f"  config.vm.box_check_update = {verif_box}")

    blocs_vm = ["\n".join(_lignes_vm(vm, provider_global)) for vm in vms]
    corps_vms = "\n\n".join(blocs_vm)
    # Encadre le corps de lignes vides seulement s'il y a des VMs, pour que le
    # gabarit par défaut (qui colle $ENTETE-$VMS-$PIED) ne laisse pas de
    # doubles lignes vides quand la config ne définit aucune VM.
    vms_encadre = f"\n\n{corps_vms}\n\n" if corps_vms else "\n\n"

    return {
        "ENTETE": "\n".join(entete),
        "VMS": vms_encadre,
        "PIED": "end",
        "DATE": date.today().isoformat(),
        "NB_VMS": str(len(vms)),
        "RAM_TOTALE": str(total_ram),
        "CPU_TOTAL": str(total_cpu),
        "PROVIDER": provider_global,
    }


# Gabarit par défaut : reproduit exactement la mise en page historique du
# Vagrantfile (une ligne vide avant les VMs, une avant le `end` final).
# $VMS porte déjà ses propres lignes vides d'encadrement (voir construire_sections).
GABARIT_DEFAUT = "$ENTETE$VMS$PIED\n"


def rendre_gabarit(config, gabarit=None):
    """Rend un Vagrantfile à partir d'un gabarit texte (`string.Template`).

    `gabarit` est le contenu texte du gabarit (pas un chemin) ; `None` ou
    chaîne vide utilise `GABARIT_DEFAUT`. Les variables inconnues sont
    laissées telles quelles (substitution "safe").
    """
    sections = construire_sections(config)
    texte = gabarit if gabarit else GABARIT_DEFAUT
    return Template(texte).safe_substitute(sections)


def construire_vagrantfile(config, gabarit=None):
    """Construit le contenu complet du Vagrantfile à partir de la config (dict).

    `gabarit` (optionnel) : contenu texte d'un gabarit personnalisé. Sans
    gabarit, produit le Vagrantfile standard (comportement historique).
    """
    return rendre_gabarit(config, gabarit)


def _groupe_ansible(nom):
    """Déduit un nom de groupe Ansible à partir du nom de VM (préfixe avant
    le premier tiret/underscore, ex. « k3s-worker1 » -> « k3s »)."""
    base = re.split(r"[-_]", nom, maxsplit=1)[0]
    return base or "vagrantforge"


def construire_inventaire_ansible(config):
    """Construit un inventaire Ansible (format INI) à partir de la config.

    Chaque VM devient un hôte, avec `ansible_host` (IP privée si connue,
    sinon le nom), `ansible_user`/`ansible_password` (SSH) ou
    `ansible_connection=winrm` + identifiants WinRM pour les invités
    Windows. Les VMs sont aussi regroupées par préfixe de nom (« k3s-master »,
    « k3s-worker1 » -> groupe `[k3s]`) pour cibler un lab entier facilement.

    Utile pour piloter le lab avec Ansible depuis l'extérieur de Vagrant
    (sans passer par `config.vm.provision "ansible"`), ou en complément.
    """
    vms = config.get("vms", [])
    if not vms:
        return "# Aucune VM dans la config : inventaire vide.\n"

    groupes = {}
    lignes_hotes = ["[tous:vars]", "ansible_ssh_common_args='-o StrictHostKeyChecking=no'", ""]
    lignes_hotes.append("[tous]")
    for vm in vms:
        nom = vm.get("name", "vm")
        ip = vm.get("ip", "")
        cible = ip or nom
        windows = est_box_windows(vm)
        vars_hote = [f"ansible_host={cible}"]
        if windows:
            vars_hote.append("ansible_connection=winrm")
            vars_hote.append("ansible_winrm_transport=basic")
            vars_hote.append("ansible_port=5985")
            if vm.get("winrm_username"):
                vars_hote.append(f"ansible_user={vm['winrm_username']}")
            if vm.get("winrm_password"):
                vars_hote.append(f"ansible_password={vm['winrm_password']}")
        else:
            vars_hote.append(f"ansible_user={vm.get('ssh_username') or 'vagrant'}")
            if vm.get("ssh_password"):
                vars_hote.append(f"ansible_password={vm['ssh_password']}")
        lignes_hotes.append(f"{nom} " + " ".join(vars_hote))
        groupes.setdefault(_groupe_ansible(nom), []).append(nom)

    sortie = ["# Inventaire Ansible généré par VagrantForge — statique, format INI.",
              "# Utilisation : ansible-playbook -i inventaire.ini playbook.yml", ""]
    sortie += lignes_hotes
    sortie.append("")
    for groupe, membres in groupes.items():
        if len(membres) < 2 and groupe not in {"vagrantforge"}:
            continue  # groupe à un seul membre : redondant avec [tous], pas utile
        sortie.append(f"[{groupe}]")
        sortie.extend(membres)
        sortie.append("")
    return "\n".join(sortie).rstrip("\n") + "\n"


def construire_inventaire_ansible_yaml(config):
    """Construit un inventaire Ansible au format YAML (structure `all.hosts` +
    groupes par préfixe de nom), équivalent YAML de
    `construire_inventaire_ansible`. Zéro dépendance : YAML écrit à la main
    (pas de PyYAML), suffisamment simple pour rester fiable sans lib.
    """
    vms = config.get("vms", [])
    if not vms:
        return "# Aucune VM dans la config : inventaire vide.\nall:\n  hosts: {}\n"

    def _ligne_hote(vm, indent):
        nom = vm.get("name", "vm")
        ip = vm.get("ip", "") or nom
        windows = est_box_windows(vm)
        vars_hote = [f"ansible_host: {ip}"]
        if windows:
            vars_hote += ["ansible_connection: winrm", "ansible_winrm_transport: basic",
                          "ansible_port: 5985"]
            if vm.get("winrm_username"):
                vars_hote.append(f"ansible_user: {vm['winrm_username']}")
            if vm.get("winrm_password"):
                vars_hote.append(f"ansible_password: {vm['winrm_password']}")
        else:
            vars_hote.append(f"ansible_user: {vm.get('ssh_username') or 'vagrant'}")
            if vm.get("ssh_password"):
                vars_hote.append(f"ansible_password: {vm['ssh_password']}")
        pad = " " * indent
        lignes = [f"{pad}{nom}:"]
        lignes += [f"{pad}  {v}" for v in vars_hote]
        return lignes

    groupes = {}
    for vm in vms:
        groupes.setdefault(_groupe_ansible(vm.get("name", "vm")), []).append(vm)

    sortie = [
        "# Inventaire Ansible généré par VagrantForge — YAML.",
        "# Utilisation : ansible-playbook -i inventaire.yml playbook.yml",
        "all:",
        "  vars:",
        "    ansible_ssh_common_args: '-o StrictHostKeyChecking=no'",
        "  hosts:",
    ]
    for vm in vms:
        sortie += _ligne_hote(vm, 4)

    groupes_multi = {g: membres for g, membres in groupes.items() if len(membres) >= 2}
    if groupes_multi:
        sortie.append("  children:")
        for groupe, membres in groupes_multi.items():
            sortie.append(f"    {groupe}:")
            sortie.append("      hosts:")
            for vm in membres:
                sortie.append(f"        {vm.get('name', 'vm')}: {{}}")

    return "\n".join(sortie) + "\n"
