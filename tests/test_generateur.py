"""Tests du cœur VagrantForge — génération, validation, presets.

Lancement :
    python -m pytest tests/ -v
    (ou sans pytest : python tests/test_generateur.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.generateur import construire_vagrantfile, nom_variable, echapper
from core.schema import valider_config
from core.presets import PRESETS, obtenir_preset


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
