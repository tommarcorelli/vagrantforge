#!/usr/bin/env python3
"""VagrantForge — CLI de génération de Vagrantfile.

Exemples :
    forge generer config.json                 # écrit ./Vagrantfile
    forge generer config.json -o infra/Vagrantfile
    cat config.json | forge generer -         # lit stdin, écrit stdout
    forge preset k3s                          # génère depuis un preset
    forge preset pentest --sous-reseau 10.10.10 -o Vagrantfile
    forge valider config.json                 # vérifie sans générer
    forge presets                             # liste les presets dispo
"""

import argparse
import json
import sys
from pathlib import Path

# La console Windows est souvent en cp1252 : force l'UTF-8 pour ne pas planter
# sur les accents et les caractères de dessin du Vagrantfile généré.
for _flux in (sys.stdout, sys.stderr):
    try:
        _flux.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# Permet l'exécution directe (python cli/main.py) comme via `python -m cli.main`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.generateur import construire_vagrantfile          # noqa: E402
from core.schema import valider_config                      # noqa: E402
from core.presets import PRESETS, obtenir_preset            # noqa: E402


class C:
    """Codes couleur ANSI, désactivés si la sortie n'est pas un terminal."""
    actif = sys.stderr.isatty()
    ROUGE = "\033[31m" if actif else ""
    VERT = "\033[32m" if actif else ""
    JAUNE = "\033[33m" if actif else ""
    BLEU = "\033[36m" if actif else ""
    GRAS = "\033[1m" if actif else ""
    RAZ = "\033[0m" if actif else ""


def err(msg):
    print(msg, file=sys.stderr)


def afficher_diagnostics(erreurs, avertissements):
    for a in avertissements:
        err(f"{C.JAUNE}⚠ {a}{C.RAZ}")
    for e in erreurs:
        err(f"{C.ROUGE}✗ {e}{C.RAZ}")


def charger_json(chemin):
    try:
        brut = sys.stdin.read() if chemin == "-" else Path(chemin).read_text(encoding="utf-8")
    except FileNotFoundError:
        err(f"{C.ROUGE}✗ Fichier introuvable : {chemin}{C.RAZ}")
        sys.exit(2)
    try:
        return json.loads(brut)
    except json.JSONDecodeError as e:
        err(f"{C.ROUGE}✗ JSON invalide : {e}{C.RAZ}")
        sys.exit(2)


def ecrire_sortie(contenu, sortie):
    if sortie and sortie != "-":
        Path(sortie).write_text(contenu, encoding="utf-8")
        err(f"{C.VERT}✓ Vagrantfile écrit dans {sortie}{C.RAZ}")
    else:
        sys.stdout.write(contenu)


def _generer_depuis_config(config, sortie, forcer):
    erreurs, avertissements = valider_config(config)
    afficher_diagnostics(erreurs, avertissements)
    if erreurs and not forcer:
        err(f"{C.ROUGE}{C.GRAS}Génération annulée : {len(erreurs)} erreur(s).{C.RAZ} "
            f"Utilise --forcer pour passer outre.")
        sys.exit(1)
    ecrire_sortie(construire_vagrantfile(config), sortie)
    return 0


def cmd_generer(args):
    config = charger_json(args.config)
    return _generer_depuis_config(config, args.output, args.forcer)


def cmd_preset(args):
    try:
        config = obtenir_preset(args.nom, args.sous_reseau)
    except KeyError:
        err(f"{C.ROUGE}✗ Preset inconnu : {args.nom}{C.RAZ}")
        err(f"  Presets disponibles : {', '.join(PRESETS)}")
        sys.exit(2)
    if args.json:
        sys.stdout.write(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
        return 0
    return _generer_depuis_config(config, args.output, forcer=True)


def cmd_valider(args):
    config = charger_json(args.config)
    erreurs, avertissements = valider_config(config)
    afficher_diagnostics(erreurs, avertissements)
    if erreurs:
        err(f"{C.ROUGE}{C.GRAS}{len(erreurs)} erreur(s), {len(avertissements)} avertissement(s).{C.RAZ}")
        sys.exit(1)
    err(f"{C.VERT}✓ Config valide{C.RAZ}"
        + (f" ({len(avertissements)} avertissement(s))" if avertissements else "") + ".")
    return 0


def cmd_presets(args):
    print(f"{C.GRAS}Presets VagrantForge :{C.RAZ}")
    for nom, (desc, _) in PRESETS.items():
        print(f"  {C.BLEU}{nom:<12}{C.RAZ} {desc}")
    return 0


def construire_parser():
    p = argparse.ArgumentParser(
        prog="forge",
        description="VagrantForge — forge des Vagrantfile multi-VM proprement.",
    )
    sous = p.add_subparsers(dest="commande", required=True)

    g = sous.add_parser("generer", help="Génère un Vagrantfile depuis une config JSON.")
    g.add_argument("config", help="Chemin du JSON, ou '-' pour stdin.")
    g.add_argument("-o", "--output", help="Fichier de sortie (défaut : stdout).")
    g.add_argument("--forcer", action="store_true", help="Génère malgré les erreurs de validation.")
    g.set_defaults(fonc=cmd_generer)

    pr = sous.add_parser("preset", help="Génère un Vagrantfile depuis un preset.")
    pr.add_argument("nom", help="Nom du preset (voir « forge presets »).")
    pr.add_argument("-o", "--output", help="Fichier de sortie (défaut : stdout).")
    pr.add_argument("--sous-reseau", default="192.168.56", dest="sous_reseau",
                    help="Sous-réseau privé de base (défaut : 192.168.56).")
    pr.add_argument("--json", action="store_true", help="Sort la config JSON au lieu du Vagrantfile.")
    pr.set_defaults(fonc=cmd_preset)

    v = sous.add_parser("valider", help="Valide une config sans générer.")
    v.add_argument("config", help="Chemin du JSON, ou '-' pour stdin.")
    v.set_defaults(fonc=cmd_valider)

    lp = sous.add_parser("presets", help="Liste les presets disponibles.")
    lp.set_defaults(fonc=cmd_presets)

    return p


def main(argv=None):
    parser = construire_parser()
    args = parser.parse_args(argv)
    return args.fonc(args)


if __name__ == "__main__":
    sys.exit(main())
