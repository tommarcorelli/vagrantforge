#!/usr/bin/env python3
"""VagrantForge — serveur web (Flask).

Sert le frontend et expose une petite API partageant le cœur Python :
    GET  /                      -> l'interface
    GET  /api/presets           -> liste des presets
    GET  /api/preset/<nom>      -> config JSON d'un preset
    POST /api/valider           -> {erreurs, avertissements}
    POST /api/generer           -> {vagrantfile, erreurs, avertissements}

Le frontend fonctionne aussi 100 % en autonome (ouvrir index.html) : cette API
est un bonus pour générer côté serveur ou scripter via HTTP.

Lancement :
    pip install -r requirements.txt
    python web/api/main.py         # http://127.0.0.1:5000
"""

import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

RACINE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RACINE))

from core.generateur import construire_vagrantfile          # noqa: E402
from core.schema import valider_config                      # noqa: E402
from core.presets import PRESETS, obtenir_preset            # noqa: E402

FRONTEND = RACINE / "web" / "frontend"

app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/<path:fichier>")
def statique(fichier):
    return send_from_directory(FRONTEND, fichier)


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
    config = request.get_json(silent=True) or {}
    erreurs, avertissements = valider_config(config)
    if erreurs and not request.args.get("forcer"):
        return jsonify({"erreurs": erreurs, "avertissements": avertissements,
                        "vagrantfile": None}), 422
    return jsonify({
        "vagrantfile": construire_vagrantfile(config),
        "erreurs": erreurs,
        "avertissements": avertissements,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
