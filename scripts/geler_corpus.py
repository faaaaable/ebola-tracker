# -*- coding: utf-8 -*-
"""Gele les 104 rapports en un intermediaire complet, pour ne plus jamais
rouvrir un PDF.

Pour chaque rapport (SitRep INSP et Weekly External Situation Report OMS) on
ecrit un JSON dans data/corpus/textes/ contenant :

  - le texte de chaque page, dans les deux rendus de pdfplumber :
      "texte"        flux de lecture, le plus propre pour les phrases ;
      "texte_cadre"  rendu spatial (layout=True), qui garde les colonnes et
                     rattrape les bandeaux que le flux melange — le bandeau
                     KPI de la page 1 sort en « 5 375 C 2 O N 5 F 5 IR 7 M ES »
                     dans le premier et reste lisible dans le second ;
  - tous les tableaux detectes, en grilles de cellules brutes, sans
    interpretation ;
  - l'empreinte SHA-256 du PDF, qui permettra de reperer un bulletin republie
    apres correction — un evenement que rien ne signale aujourd'hui.

Rien n'est normalise, rien n'est filtre : c'est un gel, pas une extraction.
Le tri vient apres, et il se fera sur ce fichier, en quelques secondes.

    python scripts/geler_corpus.py            # gele ce qui manque
    python scripts/geler_corpus.py --tout     # regele tout

data/corpus/ est gitignore : volumineux, et regenerable en une commande depuis
des PDF qui sont, eux, versionnes.
"""
import argparse
import glob
import hashlib
import io
import json
import os
import sys
import time
import traceback

import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(ROOT, "data", "corpus", "textes")
MANIFESTE = os.path.join(ROOT, "data", "corpus", "manifeste.json")


def empreinte(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as fh:
        for bloc in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def identifiant(chemin):
    """INSP_098, OMS_14 — un identifiant stable, independant du nom de fichier."""
    nom = os.path.basename(chemin)
    if nom.startswith("SITREP_MVE_"):
        return "INSP_" + nom[len("SITREP_MVE_"):-4]
    if nom.startswith("WHO_WeeklyExtSitRep_"):
        return "OMS_" + nom.split("_")[2]
    return "AUTRE_" + os.path.splitext(nom)[0]


def rapports():
    fichiers = sorted(glob.glob(os.path.join(ROOT, "reports", "SITREP_MVE_*.pdf")))
    fichiers += sorted(glob.glob(os.path.join(ROOT, "reports", "who", "*.pdf")))
    return fichiers


def geler(chemin):
    rel = os.path.relpath(chemin, ROOT).replace("\\", "/")
    doc = {
        "id": identifiant(chemin),
        "source": "OMS" if "/who/" in rel else "INSP",
        "fichier": rel,
        "sha256": empreinte(chemin),
        "octets": os.path.getsize(chemin),
        "pages": [],
        "tableaux": [],
        "erreurs": [],
    }
    with pdfplumber.open(chemin) as pdf:
        doc["nb_pages"] = len(pdf.pages)
        for numero, page in enumerate(pdf.pages, 1):
            try:
                flux = page.extract_text() or ""
            except Exception as err:
                flux = ""
                doc["erreurs"].append("p%d texte : %s" % (numero, err))
            try:
                cadre = page.extract_text(layout=True) or ""
            except Exception as err:
                cadre = ""
                doc["erreurs"].append("p%d texte_cadre : %s" % (numero, err))
            # Position de chaque mot. Ni le flux ni le rendu spatial ne
            # permettent de recomposer un tableau a colonnes larges : le
            # premier melange les colonnes, le second les tasse, et le tableau
            # « Defis | Impact | Actions requises » — la seule source du corpus
            # sur les causes de persistance de l'epidemie — se retrouve
            # illisible dans les deux. Les abscisses, elles, tranchent.
            try:
                mots = [
                    [round(float(m["x0"]), 1), round(float(m["x1"]), 1),
                     round(float(m["top"]), 1), m["text"]]
                    for m in page.extract_words(use_text_flow=False,
                                                keep_blank_chars=False)
                ]
            except Exception as err:
                mots = []
                doc["erreurs"].append("p%d mots : %s" % (numero, err))
            doc["pages"].append({
                "page": numero,
                "largeur": round(float(page.width), 1),
                "hauteur": round(float(page.height), 1),
                "texte": flux,
                "texte_cadre": cadre,
                "mots": mots,
            })
            try:
                for index, grille in enumerate(page.extract_tables()):
                    doc["tableaux"].append({
                        "page": numero,
                        "index": index,
                        "lignes": len(grille),
                        "colonnes": max((len(r) for r in grille), default=0),
                        "grille": grille,
                    })
            except Exception as err:
                doc["erreurs"].append("p%d tableaux : %s" % (numero, err))
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tout", action="store_true",
                    help="regele meme les rapports deja traites")
    args = ap.parse_args()

    if not os.path.isdir(SORTIE):
        os.makedirs(SORTIE)

    fichiers = rapports()
    print("%d rapports a geler" % len(fichiers))
    manifeste, faits, sautes, echecs = [], 0, 0, 0
    depart = time.time()

    for i, chemin in enumerate(fichiers, 1):
        ident = identifiant(chemin)
        cible = os.path.join(SORTIE, ident + ".json")
        if os.path.exists(cible) and not args.tout:
            with io.open(cible, encoding="utf-8") as fh:
                doc = json.load(fh)
            sautes += 1
        else:
            try:
                doc = geler(chemin)
            except Exception:
                echecs += 1
                print("  [%3d/%d] %-10s ECHEC" % (i, len(fichiers), ident))
                traceback.print_exc(limit=2)
                continue
            with io.open(cible, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False)
            faits += 1
            car = sum(len(p["texte"]) for p in doc["pages"])
            print("  [%3d/%d] %-10s %2d p  %3d tabl  %6d car%s"
                  % (i, len(fichiers), ident, doc["nb_pages"],
                     len(doc["tableaux"]), car,
                     "  !%d erreur(s)" % len(doc["erreurs"]) if doc["erreurs"] else ""))
            sys.stdout.flush()

        manifeste.append({
            "id": doc["id"], "source": doc["source"], "fichier": doc["fichier"],
            "sha256": doc["sha256"], "octets": doc["octets"],
            "nb_pages": doc["nb_pages"], "nb_tableaux": len(doc["tableaux"]),
            "caracteres": sum(len(p["texte"]) for p in doc["pages"]),
            "erreurs": len(doc["erreurs"]),
        })

    with io.open(MANIFESTE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifeste, fh, ensure_ascii=False, indent=1)

    print("\ngeles %d | deja presents %d | echecs %d | %.0f s"
          % (faits, sautes, echecs, time.time() - depart))
    print("manifeste : data/corpus/manifeste.json")


if __name__ == "__main__":
    main()
