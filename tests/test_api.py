"""VagrantForge — tests de l'API Flask (web/api/main.py).

Avant cet audit, l'API n'avait aucune couverture de tests alors qu'elle
contenait un vrai bug (voir test_generer_avec_corps_non_objet ci-dessous) :
un corps JSON qui n'est pas un objet (liste, chaîne…) faisait planter
`/api/exporter` avec un 500 (`AttributeError` sur `corps.get(...)` appelé
sur une liste). Corrigé via le helper `_extraire_config`.

Nécessite `flask` installé (déjà requis par requirements.txt pour ce module).
"""

import pytest

from web.api.main import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


CONFIG_VALIDE = {
    "provider": "virtualbox", "box_check_update": False,
    "vms": [{"name": "web", "box": "debian/bookworm64", "memory": 1024, "cpus": 1,
             "ip": "192.168.56.10"}],
}


# ── Robustesse : corps JSON qui n'est pas un objet (le bug trouvé à l'audit) ──

@pytest.mark.parametrize("endpoint", ["/api/generer", "/api/inventaire", "/api/topologie", "/api/exporter"])
@pytest.mark.parametrize("corps", [[1, 2, 3], "une chaine", 42, None])
def test_endpoints_ne_plantent_pas_sur_corps_non_objet(client, endpoint, corps):
    """Avant correction : /api/exporter renvoyait un 500 sur ces corps."""
    reponse = client.post(endpoint, json=corps)
    assert reponse.status_code != 500


# ── Comportement nominal ──

def test_liste_presets(client):
    reponse = client.get("/api/presets")
    assert reponse.status_code == 200
    donnees = reponse.get_json()
    assert "k3s" in donnees and "solo" in donnees


def test_preset_inconnu_404(client):
    reponse = client.get("/api/preset/ce-preset-nexiste-pas")
    assert reponse.status_code == 404


def test_preset_connu(client):
    reponse = client.get("/api/preset/solo")
    assert reponse.status_code == 200
    assert reponse.get_json()["vms"]


def test_valider_config_ok(client):
    reponse = client.post("/api/valider", json=CONFIG_VALIDE)
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps["valide"] is True
    assert corps["erreurs"] == []


def test_valider_config_invalide(client):
    reponse = client.post("/api/valider", json={"provider": "virtualbox", "vms": [{"name": ""}]})
    corps = reponse.get_json()
    assert corps["valide"] is False
    assert corps["erreurs"]


def test_generer_config_valide(client):
    reponse = client.post("/api/generer", json=CONFIG_VALIDE)
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert "Vagrant.configure" in corps["vagrantfile"]
    assert corps["erreurs"] == []


def test_generer_config_invalide_sans_forcer_422(client):
    reponse = client.post("/api/generer", json={"provider": "virtualbox", "vms": [{"name": ""}]})
    assert reponse.status_code == 422
    assert reponse.get_json()["vagrantfile"] is None


def test_generer_config_invalide_avec_forcer_200(client):
    reponse = client.post("/api/generer?forcer=1", json={"provider": "virtualbox", "vms": [{"name": ""}]})
    assert reponse.status_code == 200
    assert reponse.get_json()["vagrantfile"] is not None


def test_generer_accepte_enveloppe_config_et_gabarit(client):
    """Forme {"config": {...}, "gabarit": "..."}."""
    gabarit = "# En-tête perso\n$VMS\n"
    reponse = client.post("/api/generer", json={"config": CONFIG_VALIDE, "gabarit": gabarit})
    assert reponse.status_code == 200
    assert "# En-tête perso" in reponse.get_json()["vagrantfile"]


def test_inventaire_ini_par_defaut(client):
    reponse = client.post("/api/inventaire", json=CONFIG_VALIDE)
    assert reponse.status_code == 200
    assert "[web]" in reponse.get_json()["inventaire"] or "ansible_host" in reponse.get_json()["inventaire"]


def test_inventaire_yaml(client):
    reponse = client.post("/api/inventaire?format=yaml", json=CONFIG_VALIDE)
    assert reponse.status_code == 200
    assert reponse.get_json()["inventaire"]


def test_topologie_mermaid(client):
    reponse = client.post("/api/topologie", json=CONFIG_VALIDE)
    assert reponse.status_code == 200
    assert "graph" in reponse.get_json()["mermaid"] or "flowchart" in reponse.get_json()["mermaid"]


def test_exporter_renvoie_un_zip(client):
    reponse = client.post("/api/exporter", json=CONFIG_VALIDE)
    assert reponse.status_code == 200
    assert reponse.mimetype == "application/zip"
    assert reponse.data[:2] == b"PK"  # signature de fichier zip


def test_exporter_config_invalide_sans_forcer_422(client):
    reponse = client.post("/api/exporter", json={"provider": "virtualbox", "vms": [{"name": ""}]})
    assert reponse.status_code == 422


def test_verifier_box_inconnue_404(client):
    reponse = client.get("/api/verifier-box?box=cette-box-nexiste-pas-du-tout")
    assert reponse.status_code == 404


def test_box_versions_sans_parametre_400(client):
    reponse = client.get("/api/box-versions")
    assert reponse.status_code == 400
