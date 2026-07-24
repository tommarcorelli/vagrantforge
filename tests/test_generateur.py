"""Tests du cœur VagrantForge — génération, validation, presets.

Lancement :
    python -m pytest tests/ -v
    (ou sans pytest : python tests/test_generateur.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.generateur import (construire_vagrantfile, nom_variable, echapper, construire_sections,
                              est_box_windows, construire_inventaire_ansible,
                              construire_inventaire_ansible_yaml)
from core.schema import valider_config
from core.presets import PRESETS, obtenir_preset
from core.lint import linter_vagrantfile
from core.export_projet import construire_zip_projet
from core.topologie import construire_topologie_mermaid
from core.doctor import diagnostiquer, au_moins_un_provider


def test_nom_variable_prefixe_les_chiffres():
    assert nom_variable("3proxy") == "vm_3proxy"
    assert nom_variable("web-01") == "web_01"
    assert nom_variable("") == "vm"


def test_echapper_guillemets():
    assert echapper('a"b') == 'a\\"b'


def test_generation_minimale():
    config = {"provider": "virtualbox", "vms": [
        {"name": "web", "box": "debian/bookworm64", "memory": 1024, "cpus": 1}
    ]}
    vf = construire_vagrantfile(config)
    assert 'Vagrant.configure("2")' in vf
    assert 'config.vm.define "web"' in vf
    assert 'vb.memory = 1024' in vf
    assert vf.strip().endswith("end")


def test_generation_ports_et_ip():
    config = {"provider": "virtualbox", "vms": [
        {"name": "web", "box": "debian/bookworm64", "memory": 512, "cpus": 1,
         "ip": "192.168.56.10", "ports": [{"guest": 80, "host": 8080}]}
    ]}
    vf = construire_vagrantfile(config)
    assert 'private_network", ip: "192.168.56.10"' in vf
    assert 'forwarded_port", guest: 80, host: 8080' in vf


def test_provision_shell_avec_root_password():
    config = {"provider": "virtualbox", "vms": [
        {"name": "web", "box": "debian/bookworm64", "memory": 512, "cpus": 1,
         "root_password": "secret", "provision": {"type": "shell", "script": "echo salut\n"}}
    ]}
    vf = construire_vagrantfile(config)
    assert 'echo "root:secret" | chpasswd' in vf
    assert "echo salut" in vf


def test_generation_locale_et_clavier():
    config = {"provider": "virtualbox", "vms": [
        {"name": "web", "box": "debian/bookworm64", "memory": 1024, "cpus": 1,
         "locale": "fr_FR.UTF-8", "keymap": "fr"}
    ]}
    vf = construire_vagrantfile(config)
    assert "update-locale LANG=fr_FR.UTF-8" in vf
    assert 'XKBLAYOUT=fr' in vf
    assert "Langue & clavier" in vf


def test_validation_detecte_noms_dupliques():
    config = {"provider": "virtualbox", "vms": [
        {"name": "web", "box": "debian/bookworm64", "memory": 1024, "cpus": 1},
        {"name": "web", "box": "debian/bookworm64", "memory": 1024, "cpus": 1},
    ]}
    erreurs, _ = valider_config(config)
    assert any("déjà utilisé" in e for e in erreurs)


def test_validation_detecte_ip_dupliquee():
    config = {"provider": "virtualbox", "vms": [
        {"name": "a", "box": "debian/bookworm64", "memory": 1024, "cpus": 1, "ip": "192.168.56.10"},
        {"name": "b", "box": "debian/bookworm64", "memory": 1024, "cpus": 1, "ip": "192.168.56.10"},
    ]}
    erreurs, _ = valider_config(config)
    assert any("déjà attribuée" in e for e in erreurs)


def test_validation_provider_incompatible_avertit():
    # debian/bookworm64 ne publie pas de variante vmware_desktop
    config = {"provider": "vmware_desktop", "vms": [
        {"name": "web", "box": "debian/bookworm64", "memory": 1024, "cpus": 1},
    ]}
    _, avertissements = valider_config(config)
    assert any("vmware_desktop" in a for a in avertissements)


def test_validation_memoire_invalide():
    config = {"provider": "virtualbox", "vms": [
        {"name": "web", "box": "debian/bookworm64", "memory": 32, "cpus": 1},
    ]}
    erreurs, _ = valider_config(config)
    assert any("memory" in e for e in erreurs)


def test_tous_les_presets_sont_valides():
    for nom in PRESETS:
        config = obtenir_preset(nom)
        erreurs, _ = valider_config(config)
        assert erreurs == [], f"Preset « {nom} » invalide : {erreurs}"
        # et il doit se générer sans exploser
        assert construire_vagrantfile(config).strip().endswith("end")


def test_catalogue_presets_attendu():
    # Verrou anti-régression : si un preset disparaît sans le vouloir, ce test le dit.
    attendus = {"solo", "k3s", "lamp", "devsecops", "pentest",
                "monitoring", "elk", "wordpress", "gitlab-runner", "nextcloud"}
    assert attendus <= set(PRESETS)


def test_gabarit_par_defaut_identique_a_lhistorique():
    config = obtenir_preset("solo")
    assert construire_vagrantfile(config) == construire_vagrantfile(config, gabarit=None)


def test_gabarit_personnalise_insere_les_sections():
    config = obtenir_preset("solo")
    gabarit = "# Mon en-tête maison\n$ENTETE\n$VMS\n$PIED\n# Généré le $DATE, $NB_VMS VM(s)\n"
    resultat = construire_vagrantfile(config, gabarit=gabarit)
    assert resultat.startswith("# Mon en-tête maison\n")
    assert "Vagrant.configure" in resultat
    assert resultat.rstrip().endswith("VM(s)")


def test_gabarit_variable_inconnue_ne_plante_pas():
    config = obtenir_preset("solo")
    resultat = construire_vagrantfile(config, gabarit="$ENTETE $VMS $PIED $CECI_NEXISTE_PAS")
    assert "$CECI_NEXISTE_PAS" in resultat  # laissé tel quel (safe_substitute)


def test_construire_sections_expose_les_metadonnees():
    config = obtenir_preset("k3s")
    sections = construire_sections(config)
    assert sections["NB_VMS"] == "3"
    assert sections["PROVIDER"] == "virtualbox"
    assert "k3s-master" in sections["VMS"]


def test_lint_valide_tous_les_presets():
    for nom in PRESETS:
        contenu = construire_vagrantfile(obtenir_preset(nom))
        erreurs, _ = linter_vagrantfile(contenu, utiliser_ruby=False)
        assert erreurs == [], f"Preset « {nom} » : Vagrantfile généré invalide : {erreurs}"


def test_lint_detecte_bloc_do_non_ferme():
    casse = 'Vagrant.configure("2") do |config|\n  config.vm.box = "x"\n'
    erreurs, _ = linter_vagrantfile(casse, utiliser_ruby=False)
    assert any("jamais refermé" in e for e in erreurs)


def test_lint_detecte_heredoc_non_ferme():
    casse = 'config.vm.provision "shell", inline: <<-SHELL\n  echo hi\n'
    erreurs, _ = linter_vagrantfile(casse, utiliser_ruby=False)
    assert any("heredoc" in e for e in erreurs)


def test_lint_ignore_do_end_dans_un_heredoc():
    # "do" et "end" à l'intérieur d'un heredoc shell ne doivent pas fausser le compte.
    contenu = (
        'Vagrant.configure("2") do |config|\n'
        '  config.vm.provision "shell", inline: <<-SHELL\n'
        '    for i in 1 2 3; do echo $i; end\n'
        '  SHELL\n'
        'end\n'
    )
    erreurs, _ = linter_vagrantfile(contenu, utiliser_ruby=False)
    assert erreurs == []


def test_lint_vagrantfile_vide():
    erreurs, _ = linter_vagrantfile("", utiliser_ruby=False)
    assert erreurs == ["le Vagrantfile généré est vide."]


def test_windows_detecte_par_namespace_de_box():
    config = obtenir_preset("solo")
    config["vms"][0]["box"] = "gusztavvargadr/windows-server"
    config["vms"][0]["winrm_password"] = "vagrant"
    contenu = construire_vagrantfile(config)
    assert ".vm.guest = :windows" in contenu
    assert '.vm.communicator = "winrm"' in contenu
    assert ".ssh.username" not in contenu
    erreurs, _ = valider_config(config)
    assert erreurs == []


def test_windows_provisioning_bascule_en_powershell():
    config = obtenir_preset("solo")
    config["vms"][0]["box"] = "gusztavvargadr/windows-10"
    config["vms"][0]["provision"] = {"type": "shell", "script": "Write-Host 'salut'\n"}
    contenu = construire_vagrantfile(config)
    assert "#ps1_sysnative" in contenu
    erreurs, _ = linter_vagrantfile(contenu, utiliser_ruby=False)
    assert erreurs == []


def test_windows_avertit_si_locale_ou_ssh_renseignes():
    config = obtenir_preset("solo")
    config["vms"][0]["box"] = "gusztavvargadr/windows-server"
    config["vms"][0]["locale"] = "fr_FR.UTF-8"
    config["vms"][0]["ssh_username"] = "vagrant"
    config["vms"][0]["winrm_password"] = "vagrant"
    _, avert = valider_config(config)
    texte = " ".join(avert)
    assert "locale" in texte and "ignorés" in texte
    assert "ssh_username" in texte


def test_guest_os_explicite_prend_le_pas_sur_le_nom_de_box():
    # Un box « generic/whatever » forcé en windows via guest_os doit rester détecté.
    vm = {"box": "generic/whatever", "guest_os": "windows"}
    assert est_box_windows(vm)
    vm2 = {"box": "gusztavvargadr/windows-11", "guest_os": "linux"}
    assert not est_box_windows(vm2)


def test_disque_additionnel_virtualbox():
    config = {"provider": "virtualbox", "vms": [
        {"name": "data", "box": "debian/bookworm64", "memory": 1024, "cpus": 1,
         "extra_disks": [{"name": "stockage", "size_gb": 20}]}
    ]}
    erreurs, avertissements = valider_config(config)
    assert erreurs == []
    vf = construire_vagrantfile(config)
    assert "createhd" in vf
    assert "storageattach" in vf
    assert '"--size", 20480' in vf
    lint_err, _ = linter_vagrantfile(vf, utiliser_ruby=False)
    assert lint_err == []


def test_disque_additionnel_taille_invalide():
    config = {"provider": "virtualbox", "vms": [
        {"name": "data", "box": "debian/bookworm64", "memory": 1024, "cpus": 1,
         "extra_disks": [{"name": "stockage", "size_gb": 0}]}
    ]}
    erreurs, _ = valider_config(config)
    assert any("size_gb" in e for e in erreurs)


def test_disque_additionnel_libvirt():
    config = {"provider": "libvirt", "vms": [
        {"name": "data", "box": "generic/debian12", "memory": 1024, "cpus": 1,
         "extra_disks": [{"name": "stockage", "size_gb": 10}]}
    ]}
    vf = construire_vagrantfile(config)
    assert 'lv.storage :file, size: "10G"' in vf


def test_preset_windows_ad_valide_et_genere():
    config = obtenir_preset("windows-ad")
    erreurs, _ = valider_config(config)
    assert erreurs == []
    vf = construire_vagrantfile(config)
    assert "winrm" in vf
    assert "#ps1_sysnative" in vf
    lint_err, _ = linter_vagrantfile(vf, utiliser_ruby=False)
    assert lint_err == []


def test_inventaire_ansible_ssh():
    config = obtenir_preset("k3s")
    inventaire = construire_inventaire_ansible(config)
    assert "[tous]" in inventaire
    assert "k3s-master ansible_host=192.168.56.10" in inventaire
    assert "[k3s]" in inventaire
    assert "ansible_user=vagrant" in inventaire


def test_inventaire_ansible_winrm():
    config = obtenir_preset("windows-ad")
    inventaire = construire_inventaire_ansible(config)
    assert "ansible_connection=winrm" in inventaire
    assert "ansible_port=5985" in inventaire


def test_inventaire_ansible_config_vide():
    assert "vide" in construire_inventaire_ansible({"vms": []})


def test_export_zip_contient_vagrantfile_et_readme():
    config = obtenir_preset("solo")
    vf = construire_vagrantfile(config)
    archive = construire_zip_projet(config, vf)
    import zipfile
    import io
    zf = zipfile.ZipFile(io.BytesIO(archive))
    noms = zf.namelist()
    assert "Vagrantfile" in noms
    assert "README.md" in noms
    assert any(n.startswith("box/") for n in noms)  # dossier synced_folder du preset solo


def test_export_zip_contient_gitignore_qui_exclut_vagrant():
    config = obtenir_preset("solo")
    vf = construire_vagrantfile(config)
    archive = construire_zip_projet(config, vf)
    import zipfile
    import io
    zf = zipfile.ZipFile(io.BytesIO(archive))
    assert ".gitignore" in zf.namelist()
    contenu = zf.read(".gitignore").decode("utf-8")
    assert ".vagrant/" in contenu


def test_readme_projet_liste_les_ports_exposes():
    config = obtenir_preset("jenkins")
    vf = construire_vagrantfile(config)
    archive = construire_zip_projet(config, vf)
    import zipfile
    import io
    zf = zipfile.ZipFile(io.BytesIO(archive))
    readme = zf.read("README.md").decode("utf-8")
    assert "## Accès (ports exposés)" in readme
    assert "`localhost:8080`" in readme


def test_readme_projet_sans_ports_exposes_omet_la_section_acces():
    config = obtenir_preset("k3s")  # pas de forwarded_port dans ce preset
    vf = construire_vagrantfile(config)
    archive = construire_zip_projet(config, vf)
    import zipfile
    import io
    zf = zipfile.ZipFile(io.BytesIO(archive))
    readme = zf.read("README.md").decode("utf-8")
    assert "## Accès" not in readme


def test_export_zip_avec_inventaire():
    config = obtenir_preset("k3s")
    vf = construire_vagrantfile(config)
    inventaire = construire_inventaire_ansible(config)
    archive = construire_zip_projet(config, vf, inventaire)
    import zipfile
    import io
    zf = zipfile.ZipFile(io.BytesIO(archive))
    assert "inventaire-ansible.ini" in zf.namelist()


def test_export_zip_conserve_le_point_dun_dossier_cache():
    """Régression : `lstrip("./")` mangeait le point d'un dossier commençant
    par un point (ex. .config) car lstrip retire un ENSEMBLE de caractères,
    pas le préfixe littéral "./"."""
    import zipfile
    import io
    config = {
        "provider": "virtualbox", "box_check_update": False,
        "vms": [{"name": "vm1", "box": "debian/bookworm64", "memory": 512, "cpus": 1,
                  "synced_folder": ".config"}],
    }
    vf = construire_vagrantfile(config)
    archive = construire_zip_projet(config, vf)
    noms = zipfile.ZipFile(io.BytesIO(archive)).namelist()
    assert ".config/.gitkeep" in noms


def test_export_zip_rejette_la_traversee_de_chemin():
    """Un synced_folder contenant un segment ".." ne doit jamais produire une
    entrée de zip hors de l'archive (zip-slip)."""
    import zipfile
    import io
    config = {
        "provider": "virtualbox", "box_check_update": False,
        "vms": [{"name": "vm1", "box": "debian/bookworm64", "memory": 512, "cpus": 1,
                  "synced_folder": "data/../../../etc"}],
    }
    vf = construire_vagrantfile(config)
    archive = construire_zip_projet(config, vf)
    noms = zipfile.ZipFile(io.BytesIO(archive)).namelist()
    assert not any(".." in n for n in noms)
    assert noms == ["Vagrantfile", "README.md", ".gitignore"]  # aucun .gitkeep ajouté, dossier rejeté


def test_nouveaux_presets_presents():
    attendus = {"hashistack", "matomo", "minecraft", "openvpn", "mattermost", "redis-cluster",
                "haproxy-lb", "dns-dhcp", "wireguard", "samba-ad", "reverse-proxy-nginx",
                "nfs-file-server", "mail-server", "squid-proxy"}
    assert attendus <= set(PRESETS)


def test_presets_k8s_cicd_backup_presents():
    attendus = {"kubeadm", "jenkins", "borg-backup", "gitea"}
    assert attendus <= set(PRESETS)


def test_preset_kubeadm_a_trois_vms_et_calico():
    config = obtenir_preset("kubeadm")
    assert [vm["name"] for vm in config["vms"]] == ["k8s-control", "k8s-worker1", "k8s-worker2"]
    vf = construire_vagrantfile(config)
    assert "kubeadm init" in vf
    assert "calico.yaml" in vf


def test_preset_jenkins_expose_le_port_8080():
    config = obtenir_preset("jenkins")
    controller = next(vm for vm in config["vms"] if vm["name"] == "jenkins-controller")
    assert {"guest": 8080, "host": 8080} in controller["ports"]


def test_preset_borg_backup_a_deux_vms():
    config = obtenir_preset("borg-backup")
    assert {vm["name"] for vm in config["vms"]} == {"backup-server", "backup-client"}


def test_presets_runner_awx_duplicati_presents():
    attendus = {"github-runner", "awx", "duplicati"}
    assert attendus <= set(PRESETS)


def test_preset_duplicati_expose_le_port_8200():
    config = obtenir_preset("duplicati")
    assert {"guest": 8200, "host": 8200} in config["vms"][0]["ports"]


def test_preset_docker_swarm_a_trois_vms():
    config = obtenir_preset("docker-swarm")
    assert [vm["name"] for vm in config["vms"]] == ["swarm-manager", "swarm-worker1", "swarm-worker2"]


def test_hosts_file_ajoute_une_entree_par_autre_vm_avec_ip():
    config = {
        "provider": "virtualbox",
        "hosts_file": True,
        "vms": [
            {"name": "web", "box": "debian/bookworm64", "memory": 1024, "cpus": 1, "ip": "192.168.56.10"},
            {"name": "db", "box": "debian/bookworm64", "memory": 1024, "cpus": 1, "ip": "192.168.56.11"},
            {"name": "sans-ip", "box": "debian/bookworm64", "memory": 512, "cpus": 1},
        ],
    }
    vf = construire_vagrantfile(config)
    # web reçoit une entrée pour db (mais pas pour elle-même, ni pour sans-ip qui n'a pas d'IP)
    bloc_web = vf.split('config.vm.define "web"')[1].split('config.vm.define "db"')[0]
    assert "192.168.56.11" in bloc_web and "db" in bloc_web
    assert "192.168.56.10\\tweb" not in bloc_web  # pas d'auto-référence
    # sans-ip reçoit les deux entrées (elle a pas d'IP mais peut quand même résoudre les autres)
    bloc_sans_ip = vf.split('config.vm.define "sans-ip"')[1]
    assert "192.168.56.10" in bloc_sans_ip and "192.168.56.11" in bloc_sans_ip


def test_hosts_file_desactive_par_defaut():
    config = {
        "provider": "virtualbox",
        "vms": [
            {"name": "web", "box": "debian/bookworm64", "memory": 1024, "cpus": 1, "ip": "192.168.56.10"},
            {"name": "db", "box": "debian/bookworm64", "memory": 1024, "cpus": 1, "ip": "192.168.56.11"},
        ],
    }
    vf = construire_vagrantfile(config)
    assert "/etc/hosts" not in vf


def test_hosts_file_windows_utilise_powershell():
    config = {
        "provider": "virtualbox",
        "hosts_file": True,
        "vms": [
            {"name": "win-dc", "box": "gusztavvargadr/windows-server", "memory": 2048, "cpus": 1,
             "ip": "192.168.56.90", "guest_os": "windows"},
            {"name": "linux-client", "box": "debian/bookworm64", "memory": 1024, "cpus": 1,
             "ip": "192.168.56.91"},
        ],
    }
    vf = construire_vagrantfile(config)
    bloc_win = vf.split('config.vm.define "win-dc"')[1].split('config.vm.define "linux-client"')[0]
    assert "drivers\\\\etc\\\\hosts" in bloc_win or "drivers\\etc\\hosts" in bloc_win
    assert "#ps1_sysnative" in bloc_win


def test_preset_redis_cluster_a_trois_noeuds():
    config = obtenir_preset("redis-cluster")
    assert len(config["vms"]) == 3
    noms = {vm["name"] for vm in config["vms"]}
    assert noms == {"redis-0", "redis-1", "redis-2"}


def test_preset_haproxy_lb_a_trois_vms():
    config = obtenir_preset("haproxy-lb")
    noms = {vm["name"] for vm in config["vms"]}
    assert noms == {"haproxy", "web1", "web2"}


def test_preset_dns_dhcp_valide():
    config = obtenir_preset("dns-dhcp")
    erreurs, _ = valider_config(config)
    assert erreurs == []


def test_preset_wireguard_expose_le_bon_port():
    config = obtenir_preset("wireguard")
    vm = config["vms"][0]
    assert vm["ports"] == [{"guest": 51820, "host": 51820}]
    assert vm["public_network"] is True


def test_preset_samba_ad_valide():
    config = obtenir_preset("samba-ad")
    erreurs, _ = valider_config(config)
    assert erreurs == []
    noms = {vm["name"] for vm in config["vms"]}
    assert noms == {"samba-dc", "client"}


def test_preset_reverse_proxy_nginx_a_trois_vms():
    config = obtenir_preset("reverse-proxy-nginx")
    noms = {vm["name"] for vm in config["vms"]}
    assert noms == {"reverse-proxy", "app1", "app2"}
    proxy = next(vm for vm in config["vms"] if vm["name"] == "reverse-proxy")
    assert {"guest": 443, "host": 8443} in proxy["ports"]


def test_preset_nfs_file_server_valide():
    config = obtenir_preset("nfs-file-server")
    erreurs, _ = valider_config(config)
    assert erreurs == []
    noms = {vm["name"] for vm in config["vms"]}
    assert noms == {"nfs-server", "client"}


def test_preset_mail_server_expose_smtp_et_imap():
    config = obtenir_preset("mail-server")
    vm = next(vm for vm in config["vms"] if vm["name"] == "mail-server")
    ports_guest = {p["guest"] for p in vm["ports"]}
    assert {25, 143} <= ports_guest


def test_preset_squid_proxy_valide():
    config = obtenir_preset("squid-proxy")
    erreurs, _ = valider_config(config)
    assert erreurs == []
    vm = next(vm for vm in config["vms"] if vm["name"] == "squid-proxy")
    assert {"guest": 3128, "host": 3128} in vm["ports"]


def test_validation_detecte_mot_de_passe_faible():
    config = {"provider": "virtualbox", "vms": [
        {"name": "web", "box": "debian/bookworm64", "memory": 1024, "cpus": 1,
         "ssh_password": "vagrant"}
    ]}
    _, avertissements = valider_config(config)
    assert any("courant" in a for a in avertissements)


def test_validation_detecte_port_sensible_expose_publiquement():
    config = {"provider": "virtualbox", "vms": [
        {"name": "db", "box": "debian/bookworm64", "memory": 1024, "cpus": 1,
         "public_network": True, "ports": [{"guest": 3306, "host": 3306}]}
    ]}
    _, avertissements = valider_config(config)
    assert any("réseau public" in a for a in avertissements)


def test_validation_avertit_cpu_total_eleve():
    config = {"provider": "virtualbox", "vms": [
        {"name": f"vm{i}", "box": "debian/bookworm64", "memory": 512, "cpus": 4}
        for i in range(5)
    ]}
    _, avertissements = valider_config(config)
    assert any("vCPU total" in a for a in avertissements)


def test_inventaire_ansible_yaml_contient_les_hotes():
    config = obtenir_preset("k3s")
    yaml = construire_inventaire_ansible_yaml(config)
    assert "k3s-master:" in yaml
    assert "ansible_host: 192.168.56.10" in yaml
    assert "children:" in yaml  # groupe k3s (3 membres)


def test_inventaire_ansible_yaml_config_vide():
    yaml = construire_inventaire_ansible_yaml({"provider": "virtualbox", "vms": []})
    assert "hosts: {}" in yaml


def test_topologie_mermaid_contient_les_vms():
    config = obtenir_preset("lamp")
    diagramme = construire_topologie_mermaid(config)
    assert diagramme.startswith("graph LR")
    assert "pfsense" in diagramme
    assert "lamp-server" in diagramme
    assert "hôte:8080" in diagramme


def test_topologie_mermaid_config_vide():
    diagramme = construire_topologie_mermaid({"provider": "virtualbox", "vms": []})
    assert "Aucune VM" in diagramme


def test_topologie_mermaid_tous_les_presets():
    for nom in PRESETS:
        config = obtenir_preset(nom)
        diagramme = construire_topologie_mermaid(config)
        assert diagramme.startswith("graph LR"), f"Preset « {nom} » : diagramme invalide"


def test_doctor_diagnostique_sans_exploser():
    rapports = diagnostiquer()
    assert len(rapports) > 0
    assert all("nom" in r and "present" in r for r in rapports)
    # ne doit pas planter même si aucun provider n'est installé sur la machine de test
    assert au_moins_un_provider(rapports) in (True, False)


if __name__ == "__main__":
    fonctions = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    echecs = 0
    for f in fonctions:
        try:
            f()
            print(f"  ok   {f.__name__}")
        except AssertionError as e:
            echecs += 1
            print(f"  FAIL {f.__name__} : {e}")
    print(f"\n{len(fonctions) - echecs}/{len(fonctions)} tests passés.")
    sys.exit(1 if echecs else 0)
