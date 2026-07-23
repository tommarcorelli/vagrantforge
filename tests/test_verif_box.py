"""VagrantForge — tests de core/verif_box.py.

Ce module n'avait aucune couverture de tests jusqu'ici (trouvé lors d'un
audit) alors qu'il contient de la logique réseau/erreurs non triviale,
ré-utilisée à l'identique par deux fonctions publiques (factorisées dans
`_recuperer_json_box` lors du même audit). Le réseau est moqué : ces tests
ne font aucun appel réel à Vagrant Cloud.
"""

import json
import urllib.error
from unittest.mock import patch, MagicMock

from core.verif_box import (
    recuperer_providers_distants, recuperer_versions_distantes, verifier_catalogue,
)


def _reponse_json(payload):
    """Fabrique un faux contexte `with urlopen(...) as r: r.read()`."""
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    return cm


PAYLOAD_DEBIAN = {
    "versions": [
        {"version": "12.20240905.1", "providers": [{"name": "virtualbox"}, {"name": "libvirt"}]},
        {"version": "12.20240701.0", "providers": [{"name": "virtualbox"}]},
    ]
}


@patch("core.verif_box.urllib.request.urlopen")
def test_recuperer_providers_distants_ok(mock_urlopen):
    mock_urlopen.return_value = _reponse_json(PAYLOAD_DEBIAN)
    providers, erreur = recuperer_providers_distants("debian/bookworm64")
    assert erreur is None
    assert providers == ["libvirt", "virtualbox"]


@patch("core.verif_box.urllib.request.urlopen")
def test_recuperer_versions_distantes_ok_et_ordre(mock_urlopen):
    mock_urlopen.return_value = _reponse_json(PAYLOAD_DEBIAN)
    versions, erreur = recuperer_versions_distantes("debian/bookworm64")
    assert erreur is None
    assert versions == ["12.20240905.1", "12.20240701.0"]


@patch("core.verif_box.urllib.request.urlopen")
def test_recuperer_versions_distantes_respecte_la_limite(mock_urlopen):
    payload = {"versions": [{"version": f"1.{i}"} for i in range(30)]}
    mock_urlopen.return_value = _reponse_json(payload)
    versions, erreur = recuperer_versions_distantes("box/quelconque", limite=5)
    assert erreur is None
    assert len(versions) == 5


@patch("core.verif_box.urllib.request.urlopen")
def test_box_introuvable_404(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
    providers, erreur = recuperer_providers_distants("box/inexistante")
    assert providers is None
    assert "404" in erreur


@patch("core.verif_box.urllib.request.urlopen")
def test_erreur_http_generique(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 503, "Service Unavailable", {}, None)
    providers, erreur = recuperer_providers_distants("box/quelconque")
    assert providers is None
    assert "503" in erreur


@patch("core.verif_box.urllib.request.urlopen")
def test_reseau_indisponible(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("pas de réseau")
    providers, erreur = recuperer_providers_distants("box/quelconque")
    assert providers is None
    assert "réseau" in erreur


@patch("core.verif_box.urllib.request.urlopen")
def test_json_invalide(mock_urlopen):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = b"pas du json"
    mock_urlopen.return_value = cm
    providers, erreur = recuperer_providers_distants("box/quelconque")
    assert providers is None
    assert "JSON" in erreur


@patch("core.verif_box.urllib.request.urlopen")
def test_verifier_catalogue_detecte_les_ecarts(mock_urlopen):
    # Catalogue local dit "virtualbox" seulement ; Vagrant Cloud dit
    # "virtualbox" + "libvirt" -> "libvirt" manque localement.
    mock_urlopen.return_value = _reponse_json(PAYLOAD_DEBIAN)
    rapports = verifier_catalogue({"debian/bookworm64": ["virtualbox"]})
    assert len(rapports) == 1
    rapport = rapports[0]
    assert rapport["box"] == "debian/bookworm64"
    assert rapport["manquants_localement"] == ["libvirt"]
    assert rapport["en_trop"] == []


@patch("core.verif_box.urllib.request.urlopen")
def test_verifier_catalogue_detecte_un_provider_en_trop(mock_urlopen):
    # Catalogue local dit "hyperv" en plus, jamais publié -> en_trop.
    mock_urlopen.return_value = _reponse_json(PAYLOAD_DEBIAN)
    rapports = verifier_catalogue({"debian/bookworm64": ["virtualbox", "libvirt", "hyperv"]})
    assert rapports[0]["en_trop"] == ["hyperv"]
    assert rapports[0]["manquants_localement"] == []


@patch("core.verif_box.urllib.request.urlopen")
def test_verifier_catalogue_conserve_lerreur_par_box(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
    rapports = verifier_catalogue({"box/disparue": ["virtualbox"]})
    assert rapports[0]["distants"] is None
    assert "404" in rapports[0]["erreur"]
    # Sans info distante, pas de faux positif sur les écarts.
    assert rapports[0]["manquants_localement"] == []
    assert rapports[0]["en_trop"] == []
