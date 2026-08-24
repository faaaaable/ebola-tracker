#!/usr/bin/env python3
"""
Compose le message a publier sur X a partir des donnees du site.

    python scripts/message_reseaux.py            # affiche le message du dernier bulletin
    python scripts/message_reseaux.py --copier   # ... et le met dans le presse-papiers
    python scripts/message_reseaux.py --date 2026-08-21

Pourquoi un script plutot qu'un modele a recopier : la mise en page se
deformait d'une publication a l'autre. Le message etait aligne avec des suites
d'espaces, or une suite d'espaces ordinaires n'est pas conservee de la meme
facon par le compositeur et par les differents clients. Chaque element tient
donc ici sur sa propre ligne, et l'espace des milliers est une espace fine
insecable (U+202F) : elle ne se replie pas, et elle ne peut pas etre avalee
comme une suite d'espaces ordinaires.

Les ecarts sont calcules par difference avec le point precedent de
data/sitreps.json, ce qui est la convention deja suivie dans les messages
precedents. Attention : cet ecart ne recoupe pas toujours le nombre de
nouvelles confirmations annonce par le bulletin. Au 22 aout, le cumul monte de
56 alors que la source annonce 55 nouveaux cas — un cas ajoute au Haut-Uele
apres reconciliation, hors comptage du jour. C'est bien l'ecart de cumul qu'il
faut publier : sinon le message du jour ne se raccorde pas au precedent.
"""

import argparse
import json
import os
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINE = " "  # espace fine insecable, separateur des milliers

MOIS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet",
        "aout", "septembre", "octobre", "novembre", "decembre"]
MOIS_ACCENTS = {"fevrier": "février", "aout": "août", "decembre": "décembre"}


def lire(nom):
    with open(os.path.join(RACINE, "data", nom), encoding="utf-8") as f:
        return json.load(f)


def date_longue(iso):
    annee, mois, jour = (int(x) for x in iso.split("-"))
    nom = MOIS[mois - 1]
    return "%d %s %d" % (jour, MOIS_ACCENTS.get(nom, nom), annee)


def nombre(n):
    """5514 -> « 5 514 », avec une espace fine insecable."""
    return format(int(n), ",").replace(",", FINE)


def ecart(n):
    return "(+%s)" % nombre(n) if n >= 0 else "(%s)" % nombre(n)


def composer(date=None, compact=False):
    points = lire("sitreps.json")
    if date:
        indices = [i for i, p in enumerate(points) if p["date"] == date]
        if not indices:
            raise SystemExit("Aucun bulletin au %s. Dernier disponible : %s."
                             % (date, points[-1]["date"]))
        i = indices[0]
    else:
        i = len(points) - 1
    if i == 0:
        raise SystemExit("Pas de point precedent : impossible de calculer un ecart.")
    p, veille = points[i], points[i - 1]

    lignes = [
        "Ebola RDC - Situation au %s" % date_longue(p["date"]),
        "",
        "Cas confirmés : %s %s" % (nombre(p["confirmed"]),
                                   ecart(p["confirmed"] - veille["confirmed"])),
        "Décès : %s %s" % (nombre(p["deaths"]),
                           ecart(p["deaths"] - veille["deaths"])),
        "Guéris : %s %s" % (nombre(p["recovered"]),
                            ecart(p["recovered"] - veille["recovered"])),
        "",
        "Suivi complet : https://ebola-tracker.org",
        "",
        "#Ebola #RDC",
    ]
    if compact:
        lignes = [l for l in lignes if l]
    return "\n".join(lignes)


def copier(texte):
    """clip.exe lit de l'UTF-16LE : sans cela les accents ressortent casses.

    Sans BOM : clip.exe ne la retire pas, et le U+FEFF se retrouve colle en
    tete du message sous la forme d'un caractere invisible."""
    try:
        subprocess.run(["clip"], input=texte.encode("utf-16-le"), check=True)
        return True
    except (OSError, subprocess.CalledProcessError) as err:
        print("  ! copie impossible (%s) — le message reste affiche ci-dessus."
              % err, file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--date", help="date de rapportage (AAAA-MM-JJ), defaut : le dernier bulletin")
    ap.add_argument("--copier", action="store_true", help="copier dans le presse-papiers")
    ap.add_argument("--compact", action="store_true", help="sans les lignes vides de separation")
    args = ap.parse_args()

    texte = composer(args.date, args.compact)
    sys.stdout.reconfigure(encoding="utf-8")
    print(texte)
    print("\n--- %d caracteres sur les 280 autorises ---" % len(texte),
          file=sys.stderr)
    if args.copier and copier(texte):
        print("--- copie dans le presse-papiers : plus qu'a coller ---",
              file=sys.stderr)


if __name__ == "__main__":
    main()
