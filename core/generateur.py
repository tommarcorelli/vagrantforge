"""VagrantForge — génération du Vagrantfile à partir d'une config JSON.

Le schéma de config est le même que celui du générateur web (voir README.md).
Les champs sont en anglais car ils collent au vocabulaire Vagrant lui-même,
mais tout le reste (messages, commentaires générés) est en français.
"""

import re
from datetime import date

PROVIDERS_CONNUS = ("virtualbox", "vmware_desktop", "libvirt")


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


def bloc_provision(var, provision, mdp_root=""):
    """Bloc(s) de provisioning (shell inline, ansible, ou juste le mot de passe root)."""
    provision = provision or {}
    type_prov = provision.get("type", "none")
    script = provision.get("script", "")

    if type_prov == "shell":
        if mdp_root:
            script = f'echo "root:{echapper(mdp_root)}" | chpasswd\n' + script
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


def construire_vagrantfile(config):
    """Construit le contenu complet du Vagrantfile à partir de la config (dict)."""
    provider_global = config.get("provider", "virtualbox")
    verif_box = "true" if config.get("box_check_update", False) else "false"
    vms = config.get("vms", [])

    total_ram = sum(int(vm.get("memory", 1024) or 0) for vm in vms)
    total_cpu = sum(int(vm.get("cpus", 1) or 0) for vm in vms)

    out = []
    out.append("# -*- mode: ruby -*-")
    out.append("# vi: set ft=ruby :")
    out.append("#")
    out.append("# " + "=" * 66)
    out.append(f"#  Vagrantfile généré par VagrantForge — {date.today().isoformat()}")
    out.append(f"#  {len(vms)} VM(s) | {total_ram} Mo RAM | {total_cpu} vCPU | provider : {provider_global}")
    out.append("#  Démarrage : vagrant up   |   État : vagrant status")
    out.append("# " + "=" * 66)
    out.append("")
    out.append('Vagrant.require_version ">= 2.3.0"')
    out.append("")
    out.append('Vagrant.configure("2") do |config|')
    out.append(f"  config.vm.box_check_update = {verif_box}")
    out.append("")

    for vm in vms:
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

        recap_ip = ip if ip else "IP dynamique"
        out.append(f"  # ── {nom} — {box} | {memoire} Mo | {cpus} vCPU | {recap_ip}")
        out.append(f'  config.vm.define "{echapper(nom)}" do |{var}|')
        out.append(f'    {var}.vm.box = "{echapper(box)}"')
        if version_box:
            out.append(f'    {var}.vm.box_version = "{echapper(version_box)}"')
        out.append(f'    {var}.vm.hostname = "{echapper(nom)}"')
        if ip:
            out.append(f'    {var}.vm.network "private_network", ip: "{echapper(ip)}"')
        if reseau_public:
            out.append(f'    {var}.vm.network "public_network"  # pont réseau, interface choisie au démarrage')
        for port in ports:
            out.append(
                f'    {var}.vm.network "forwarded_port", '
                f'guest: {port["guest"]}, host: {port["host"]}, '
                f'auto_correct: true, id: "port-{port["guest"]}"'
            )
        if sync_desactive:
            out.append(f'    {var}.vm.synced_folder ".", "/vagrant", disabled: true')
        elif dossier_sync:
            type_dossier = {"virtualbox": "virtualbox", "vmware_desktop": "vmware"}.get(provider)
            type_str = f', type: "{type_dossier}"' if type_dossier else ""
            out.append(f'    {var}.vm.synced_folder "{echapper(dossier_sync)}", "/vagrant"{type_str}')

        utilisateur_ssh = vm.get("ssh_username", "")
        mdp_ssh = vm.get("ssh_password", "")
        if utilisateur_ssh:
            out.append(f'    {var}.ssh.username = "{echapper(utilisateur_ssh)}"')
        if mdp_ssh:
            out.append(f'    {var}.ssh.password = "{echapper(mdp_ssh)}"')
            out.append(f'    {var}.ssh.insert_key = false')

        bloc_p = bloc_provider(var, provider, memoire, cpus, nom, gui, ip_statique=bool(ip))
        if bloc_p:
            out.append(bloc_p.rstrip("\n"))

        bloc_l = bloc_locale(var, vm.get("locale", ""), vm.get("keymap", ""))
        if bloc_l:
            out.append(bloc_l.rstrip("\n"))

        bloc_prov = bloc_provision(var, vm.get("provision"), vm.get("root_password", ""))
        if bloc_prov:
            out.append(bloc_prov.rstrip("\n"))

        out.append("  end")
        out.append("")

    out.append("end")
    return "\n".join(out) + "\n"
