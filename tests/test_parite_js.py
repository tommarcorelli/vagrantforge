"""VagrantForge — tests de parité entre le cœur Python (core/) et son miroir
JS côté navigateur (web/frontend/js/generateur.js + donnees.js).

Contexte : la « règle d'or » du projet veut que toute évolution de la
génération/validation soit répercutée des deux côtés (voir PROMPT-PROJET.md
et le commentaire de `normaliserVMs` dans generateur.js, qui documente un
vrai bug de divergence déjà rencontré : des champs silencieusement
`undefined` côté JS alors que présents côté Python). Cette règle n'était
vérifiée qu'à l'œil jusqu'ici — ces tests l'automatisent en faisant tourner
le JS hors navigateur (Node, sans DOM) sur les mêmes configs que le cœur
Python, et en comparant les sorties caractère pour caractère.

Nécessite `node` dans le PATH ; le module est entièrement sauté sinon (même
philosophie de dégradation gracieuse que `ruby -c` dans core/lint.py).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from core.presets import PRESETS, obtenir_preset
from core.generateur import (
    construire_vagrantfile, construire_inventaire_ansible, construire_inventaire_ansible_yaml,
)
from core.topologie import construire_topologie_mermaid

NODE = shutil.which("node")
HARNAIS = Path(__file__).parent / "js_parity_harness.cjs"

pytestmark = pytest.mark.skipif(NODE is None, reason="Node.js introuvable dans le PATH")


def _generer_cote_js(config):
    """Appelle le harnais Node avec la config JSON, retourne le dict résultat."""
    resultat = subprocess.run(
        [NODE, str(HARNAIS)],
        input=json.dumps(config),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert resultat.returncode == 0, f"harnais Node en échec : {resultat.stderr}"
    return json.loads(resultat.stdout)


@pytest.mark.parametrize("nom_preset", sorted(PRESETS))
def test_parite_vagrantfile(nom_preset):
    """Le Vagrantfile généré par le JS doit être identique à celui du cœur Python."""
    config = obtenir_preset(nom_preset)
    attendu = construire_vagrantfile(config)
    obtenu = _generer_cote_js(config)["vagrantfile"]
    assert obtenu == attendu, f"preset « {nom_preset} » : divergence JS/Python sur le Vagrantfile."


@pytest.mark.parametrize("nom_preset", sorted(PRESETS))
def test_parite_inventaire_ansible(nom_preset):
    config = obtenir_preset(nom_preset)
    attendu_ini = construire_inventaire_ansible(config)
    attendu_yaml = construire_inventaire_ansible_yaml(config)
    obtenu = _generer_cote_js(config)
    assert obtenu["inventaire_ini"] == attendu_ini, f"preset « {nom_preset} » : divergence inventaire INI."
    assert obtenu["inventaire_yaml"] == attendu_yaml, f"preset « {nom_preset} » : divergence inventaire YAML."


@pytest.mark.parametrize("nom_preset", sorted(PRESETS))
def test_parite_topologie(nom_preset):
    config = obtenir_preset(nom_preset)
    attendu = construire_topologie_mermaid(config)
    obtenu = _generer_cote_js(config)["topologie"]
    assert obtenu == attendu, f"preset « {nom_preset} » : divergence JS/Python sur la topologie Mermaid."


def test_parite_config_vide():
    """Cas limite partagé : aucune VM."""
    config = {"provider": "virtualbox", "box_check_update": False, "vms": []}
    attendu = construire_vagrantfile(config)
    obtenu = _generer_cote_js(config)["vagrantfile"]
    assert obtenu == attendu


CONFIGS_SYNTHETIQUES = {
    "disques_et_locale": {
        "provider": "virtualbox", "box_check_update": True,
        "vms": [{
            "name": "poste-fr", "box": "debian/bookworm64", "box_version": "12.5.0",
            "memory": 2048, "cpus": 2, "ip": "192.168.56.50",
            "locale": "fr_FR", "keymap": "fr",
            "extra_disks": [{"name": "data", "size_gb": 20}, {"size_gb": 5}],
            "ssh_username": "tom", "ssh_password": "unMotDePasseSolide!42",
            "root_password": "unAutreMotDePasse!99",
        }],
    },
    "provision_ansible": {
        "provider": "libvirt", "box_check_update": False,
        "vms": [{
            "name": "cible", "box": "generic/debian12", "memory": 1024, "cpus": 1,
            "extra_disks": [{"name": "logs", "size_gb": 10}],
            "provision": {"type": "ansible", "script": "playbooks/site.yml"},
            "root_password": "vagrant",
        }],
    },
    "windows_explicite": {
        "provider": "virtualbox", "box_check_update": False,
        "vms": [{
            "name": "win-client", "box": "gusztavvargadr/windows-10", "guest_os": "windows",
            "memory": 4096, "cpus": 2, "winrm_username": "vagrant", "winrm_password": "Vagrant123!",
            "public_network": True, "ports": [{"guest": 3389, "host": 33890}],
        }],
    },
    "dossier_desactive_vmware": {
        "provider": "vmware_desktop", "box_check_update": False,
        "vms": [{
            "name": "vm-vmware", "box": "bento/debian-12", "memory": 1024, "cpus": 1,
            "ip": "192.168.56.60", "disable_synced_folder": True,
            "extra_disks": [{"name": "data", "size_gb": 15}],
        }],
    },
}


@pytest.mark.parametrize("nom_cas", sorted(CONFIGS_SYNTHETIQUES))
def test_parite_cas_synthetiques(nom_cas):
    """Cas synthétiques ciblant des champs peu exercés par les presets
    (disques additionnels, locale/clavier, provisioning ansible, Windows
    explicite, dossier synchronisé désactivé, vmware_desktop)."""
    config = CONFIGS_SYNTHETIQUES[nom_cas]
    attendu = construire_vagrantfile(config)
    obtenu = _generer_cote_js(config)["vagrantfile"]
    assert obtenu == attendu, f"cas « {nom_cas} » : divergence JS/Python sur le Vagrantfile."
