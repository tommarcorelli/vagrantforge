#!/usr/bin/env python3
"""VagrantForge — serveur web (Flask).

Sert le frontend et expose une petite API partageant le cœur Python :
    GET  /                        -> l'interface
    GET  /api/presets             -> liste des presets
    GET  /api/preset/<nom>        -> config JSON d'un preset
    POST /api/valider             -> {erreurs, avertissements}
    POST /api/generer             -> {vagrantfile, erreurs, avertissements,
                                       lint_erreurs, lint_avertissements}
                                      corps optionnel : {"config": {...}, "gabarit": "texte"}
    POST /api/inventaire[?format=yaml] -> {inventaire, erreurs, avertissements} (Ansible, INI par défaut)
    POST /api/topologie            -> {mermaid, erreurs, avertissements} (diagramme réseau Mermaid)
    POST /api/exporter             -> renvoie un .zip (Vagrantfile + arborescence + README)
    GET  /api/verifier-box[?box=nom] -> compare le catalogue local à Vagrant Cloud
                                         (nécessite un accès réseau sortant depuis le serveur)

Le frontend fonctionne aussi 100 % en autonome (ouvrir index.html) : cette API
est un bonus pour générer côté serveur ou scripter via HTTP.

Lancement :
    pip install -r requirements.txt
    python web/api/main.py         # http://127.0.0.1:5000
"""

import sys
from pathlib import Path

import io

from flask import Flask, jsonify, request, send_from_directory, send_file

RACINE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RACINE))

from core.generateur import (                                   # noqa: E402
    construire_vagrantfile, construire_inventaire_ansible, construire_inventaire_ansible_yaml,
)
from core.schema import valider_config, BOX_PROVIDERS        # noqa: E402
from core.presets import PRESETS, obtenir_preset              # noqa: E402
from core.lint import linter_vagrantfile                      # noqa: E402
from core.verif_box import verifier_catalogue, recuperer_versions_distantes  # noqa: E402
from core.export_projet import construire_zip_projet           # noqa: E402
from core.topologie import construire_topologie_mermaid        # noqa: E402

FRONTEND = RACINE / "web" / "frontend"

app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/<path:fichier>")
def statique(fichier):
    return send_from_directory(FRONTEND, fichier)


def _extraire_config(corps):
    """Normalise le corps JSON reçu par les endpoints POST : accepte soit la
    config brute (comportement historique), soit {"config": {...}, "gabarit":
    "texte optionnel"}. Toujours sûr même si le corps n'est pas un objet JSON
    (tableau, nombre, chaîne…) — évite un 500 sur `corps.get(...)`.
    """
    if not isinstance(corps, dict):
        return {}, None
    if isinstance(corps.get("config"), dict):
        return corps["config"], corps.get("gabarit") or None
    return corps, None


@app.get("/api/presets")
def api_presets():
    return jsonify({nom: desc for nom, (desc, _) in PRESETS.items()})


@app.get("/api/preset/<nom>")
def api_preset(nom):
    sous_reseau = request.args.get("sous_reseau", "192.168.56")
    try:
        return jsonify(obtenir_preset(nom, sous_reseau))
    except KeyError:
        return jsonify({"erreur": f"Preset inconnu : {nom}"}), 404


@app.post("/api/valider")
def api_valider():
    config = request.get_json(silent=True) or {}
    erreurs, avertissements = valider_config(config)
    return jsonify({"erreurs": erreurs, "avertissements": avertissements,
                    "valide": not erreurs})


@app.post("/api/generer")
def api_generer():
    corps = request.get_json(silent=True) or {}
    config, gabarit = _extraire_config(corps)

    erreurs, avertissements = valider_config(config)
    if erreurs and not request.args.get("forcer"):
        return jsonify({"erreurs": erreurs, "avertissements": avertissements,
                        "vagrantfile": None,
                        "lint_erreurs": [], "lint_avertissements": []}), 422

    vagrantfile = construire_vagrantfile(config, gabarit)
    lint_erreurs, lint_avertissements = linter_vagrantfile(vagrantfile)
    return jsonify({
        "vagrantfile": vagrantfile,
        "erreurs": erreurs,
        "avertissements": avertissements,
        "lint_erreurs": lint_erreurs,
        "lint_avertissements": lint_avertissements,
    })


@app.post("/api/inventaire")
def api_inventaire():
    """Génère un inventaire Ansible (INI par défaut, YAML avec ?format=yaml)
    depuis une config. Corps : la config JSON brute, ou {"config": {...}}."""
    corps = request.get_json(silent=True) or {}
    config, _ = _extraire_config(corps)
    erreurs, avertissements = valider_config(config)
    if erreurs and not request.args.get("forcer"):
        return jsonify({"erreurs": erreurs, "avertissements": avertissements, "inventaire": None}), 422
    fabrique = (construire_inventaire_ansible_yaml if request.args.get("format") == "yaml"
                else construire_inventaire_ansible)
    return jsonify({
        "inventaire": fabrique(config),
        "erreurs": erreurs,
        "avertissements": avertissements,
    })


@app.post("/api/topologie")
def api_topologie():
    """Génère un diagramme Mermaid de la topologie du lab. Corps : la config
    JSON brute, ou {"config": {...}}."""
    corps = request.get_json(silent=True) or {}
    config, _ = _extraire_config(corps)
    erreurs, avertissements = valider_config(config)
    if erreurs and not request.args.get("forcer"):
        return jsonify({"erreurs": erreurs, "avertissements": avertissements, "mermaid": None}), 422
    return jsonify({
        "mermaid": construire_topologie_mermaid(config),
        "erreurs": erreurs,
        "avertissements": avertissements,
    })


@app.post("/api/exporter")
def api_exporter():
    """Exporte un projet complet en .zip (Vagrantfile + arborescence + README).
    Corps : {"config": {...}, "gabarit": "texte optionnel", "avec_inventaire": bool}."""
    corps = request.get_json(silent=True) or {}
    config, gabarit = _extraire_config(corps)
    avec_inventaire = isinstance(corps, dict) and corps.get("avec_inventaire")

    erreurs, avertissements = valider_config(config)
    if erreurs and not request.args.get("forcer"):
        return jsonify({"erreurs": erreurs, "avertissements": avertissements}), 422

    vagrantfile = construire_vagrantfile(config, gabarit)
    inventaire = construire_inventaire_ansible(config) if avec_inventaire else None
    archive = construire_zip_projet(config, vagrantfile, inventaire)
    return send_file(
        io.BytesIO(archive),
        mimetype="application/zip",
        as_attachment=True,
        download_name="projet-vagrantforge.zip",
    )


@app.get("/api/verifier-box")
def api_verifier_box():
    """Compare le catalogue local à Vagrant Cloud. Nécessite le réseau côté
    serveur ; peut être lent (une requête HTTP par box) — utiliser ?box=nom
    pour ne vérifier qu'une seule entrée."""
    box = request.args.get("box")
    if box:
        if box not in BOX_PROVIDERS:
            return jsonify({"erreur": f"Box inconnue du catalogue local : {box}"}), 404
        catalogue = {box: BOX_PROVIDERS[box]}
    else:
        catalogue = BOX_PROVIDERS
    return jsonify({"rapports": verifier_catalogue(catalogue)})


@app.get("/api/box-versions")
def api_box_versions():
    """Retourne les vrais numéros de version publiés pour une box (Vagrant
    Cloud). Alimente le champ « Version de l'image » du frontend au lieu de
    laisser deviner un format."""
    box = request.args.get("box")
    if not box:
        return jsonify({"erreur": "paramètre ?box=nom requis"}), 400
    versions, erreur = recuperer_versions_distantes(box)
    if erreur:
        return jsonify({"box": box, "versions": [], "erreur": erreur}), 502
    return jsonify({"box": box, "versions": versions, "erreur": None})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
