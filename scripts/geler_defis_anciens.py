#!/usr/bin/env python3
"""Gele dans data/defis-anciens.json les sections « Defis » des bulletins que
data/defis.json ne couvre pas (avant le 084), lues dans le corpus
data/corpus/qualitatif.jsonl.

Pourquoi : le corpus n'est pas versionne (gitignore), or la frise de la page
« Riposte & defis » remonte au 31 mai. Sans ce fichier, un clone frais ou le
workflow GitHub regenererait une frise qui commence le 6 aout. Le fichier
est versionne, petit (~60 ko), et ne change que si le corpus est refait.

    python scripts/geler_defis_anciens.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUALITATIF = os.path.join(ROOT, "data", "corpus", "qualitatif.jsonl")
DEFIS = os.path.join(ROOT, "data", "defis.json")
SORTIE = os.path.join(ROOT, "data", "defis-anciens.json")

with io.open(DEFIS, encoding="utf-8") as fh:
    couverts = {p["sitrepNumber"] for p in json.load(fh).get("parDate", [])}

entrees = []
with io.open(QUALITATIF, encoding="utf-8") as fh:
    for ligne in fh:
        r = json.loads(ligne)
        if not r.get("difficulte"):
            continue
        num = r["rapport"].replace("INSP_", "")
        if num in couverts:
            continue
        entrees.append({"date": r["date"], "sitrepNumber": num,
                        "texte": r["difficulte"], "provinces": r.get("provinces", [])})
entrees.sort(key=lambda e: (e["date"], e["sitrepNumber"]))
with io.open(SORTIE, "w", encoding="utf-8") as fh:
    json.dump({"_comment": "Sections « Defis » des bulletins anterieurs a data/defis.json, "
                           "gelees depuis data/corpus/qualitatif.jsonl par scripts/geler_defis_anciens.py. "
                           "Lu par scripts/defis_synthese.py.",
               "entrees": entrees}, fh, ensure_ascii=False, indent=1)
nums = sorted({e["sitrepNumber"] for e in entrees})
print("data/defis-anciens.json : %d entrees, bulletins %s a %s" % (len(entrees), nums[0], nums[-1]))
