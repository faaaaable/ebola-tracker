# -*- coding: utf-8 -*-
"""Jours sans bulletin reconstitués par simple soustraction (6 octobre 2026).

Le SitRep n°142 (3 octobre) n'a jamais été publié par l'INSP ; le n°143
l'encadre pourtant : il donne les nouveaux cas, les nouveaux décès et les
guéris de SA journée, par pays, par province et par zone de santé. Le cumul du
jour manquant est donc le cumul du 143 moins ces chiffres de 24 h.

    cumul(142) = cumul(143) - nouveaux(143)

Ce n'est pas un chiffre du bulletin : il est figé dans data/jours-calcules.json
(le latest.json du 143 sera remplacé par celui du 144), marqué « calcule »
dans les trois historiques, et signalé par une note sous les graphiques et
tableaux. Il disparaît de lui-même, remplacé, si l'INSP publie un jour le
vrai 142 : `appliquer()` ne touche jamais une date qui porte un vrai bulletin.

Mesure du 6 octobre 2026 : sur 51 couples de bulletins consécutifs, le « +24 h »
retombe sur l'écart de cumuls 48 fois ; les 3 autres diffèrent d'un cas.
Les provinces ont leur propre jeu de 24 h (somme = national), les zones aussi.

Usage :
    python scripts/jours_calcules.py --apres 143 --jour 2026-10-03 --sitrep 142
        fige le jour à partir de data/latest.json (qui doit être le bulletin 143)
    python scripts/jours_calcules.py
        réapplique les jours figés (appelé aussi à la fin de update_data.py)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(RACINE, "data")
FIGES = os.path.join(DATA, "jours-calcules.json")


def lire(nom):
    with open(os.path.join(DATA, nom), encoding="utf-8") as f:
        return json.load(f)


def ecrire(nom, valeur):
    with open(os.path.join(DATA, nom), "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False, indent=2)
        f.write("\n")


def gueris_du_jour(sitrep):
    """« N patients (…) ont été déclarés guéris », première page du bulletin."""
    import pdfplumber
    chemin = os.path.join(RACINE, "reports", "SITREP_MVE_%s.pdf" % sitrep)
    texte = re.sub(r"\s+", " ", pdfplumber.open(chemin).pages[0].extract_text() or "")
    m = re.search(r"(\d+) patients? (?:\([^)]*\) )?ont été déclarés? guéris", texte.replace(" e t ", " et "))
    return (int(m.group(1)), m.group(0)) if m else (None, None)


def morts_zone(z):
    total = z.get("newDeaths24h")
    if total is not None:
        return total
    return (z.get("deathsCommunity24h") or 0) + (z.get("deathsIntraCTE24h") or 0)


def calculer(apres, jour, sitrep):
    latest = lire("latest.json")
    meta, nat = latest["meta"], latest["national"]
    if str(meta.get("sitrepNumber")) != str(apres):
        sys.exit("latest.json est le SitRep %s, pas le %s : relancer update_data.py --sitrep %s d'abord."
                 % (meta.get("sitrepNumber"), apres, apres))
    gueris, citation = gueris_du_jour(apres)
    national = {
        "confirmed": nat["confirmed"] - nat["newCases24h"],
        "deaths": nat["deaths"] - nat["newDeaths24h"],
        "recovered": (nat["recovered"] - gueris) if gueris is not None else None,
    }
    provinces = []
    for p in latest["provinces"]:
        morts = (p.get("newDeathsCommunity24h") or 0) + (p.get("newDeathsIntraCTE24h") or 0)
        provinces.append({"name": p["name"],
                          "confirmed": p["confirmed"] - (p.get("newCases24h") or 0),
                          "deaths": p["deaths"] - morts})
    zones = []
    for z in latest["healthZones"]:
        c = z["cases"] - (z.get("newCases24h") or 0)
        d = z["deaths"] - morts_zone(z)
        if c > 0 or d > 0:
            zones.append({"name": z["name"], "province": z["province"], "cases": c, "deaths": d})

    # Garde-fous : le jour calculé doit tomber entre ses deux voisins.
    avant = [s for s in lire("sitreps.json") if s["date"] < jour and not s.get("calcule")][-1]
    erreurs = []
    if sum(p["confirmed"] for p in provinces) != national["confirmed"]:
        erreurs.append("somme des provinces (cas) != national")
    if sum(p["deaths"] for p in provinces) != national["deaths"]:
        erreurs.append("somme des provinces (décès) != national")
    for cle in ("confirmed", "deaths"):
        if not avant[cle] <= national[cle] <= nat[cle]:
            erreurs.append("%s : %s hors de [%s ; %s]" % (cle, national[cle], avant[cle], nat[cle]))
    hist = [h for h in lire("province-history.json") if h["date"] == avant["date"]]
    if hist:
        veille = {p["name"]: p for p in hist[0]["provinces"]}
        for p in provinces:
            v = veille.get(p["name"])
            if v and (p["confirmed"] < v["confirmed"] or p["deaths"] < v["deaths"]):
                erreurs.append("province %s recule par rapport au %s" % (p["name"], avant["date"]))
    if erreurs:
        sys.exit("Jour %s non figé :\n  - %s" % (jour, "\n  - ".join(erreurs)))

    figes = {}
    if os.path.exists(FIGES):
        figes = lire("jours-calcules.json")
    figes[jour] = {
        "sitrep": str(sitrep),
        "apres": str(apres),
        "methode": "cumul du SitRep %s moins ses nouveaux cas, décès et guéris de 24 h (pays, provinces, zones)" % apres,
        "citationGueris": citation,
        "national": national,
        "provinces": provinces,
        "zones": zones,
    }
    ecrire("jours-calcules.json", figes)
    print("Jour %s figé (SitRep %s calculé depuis le %s) : %s cas, %s décès, %s guéris ; %d provinces, %d zones."
          % (jour, sitrep, apres, national["confirmed"], national["deaths"], national["recovered"],
             len(provinces), len(zones)))


def appliquer():
    """Insère chaque jour figé dans sitreps, province-history et zones-history,
    sauf si cette date porte déjà un vrai bulletin."""
    if not os.path.exists(FIGES):
        return
    figes = lire("jours-calcules.json")
    for jour, j in sorted(figes.items()):
        marque = {"calcule": True, "sitrep": j["sitrep"], "apres": j["apres"]}

        sit = lire("sitreps.json")
        if any(s["date"] == jour and not s.get("calcule") for s in sit):
            print("  (jour %s : un vrai bulletin existe, jour calculé ignoré)" % jour)
            continue
        sit = [s for s in sit if s["date"] != jour]
        sit.append(dict({"date": jour}, **j["national"], **marque))
        ecrire("sitreps.json", sorted(sit, key=lambda s: s["date"]))

        ph = [h for h in lire("province-history.json") if h["date"] != jour]
        ph.append(dict({"date": jour, "provinces": j["provinces"]}, **marque))
        ecrire("province-history.json", sorted(ph, key=lambda h: h["date"]))

        zh = [e for e in lire("zones-history.json") if e["date"] != jour]
        zh.append({"sitrep": j["sitrep"], "date": jour, "zones": j["zones"], "calcule": True, "apres": j["apres"]})
        ecrire("zones-history.json", sorted(zh, key=lambda e: e["date"]))
        print("  jour %s (SitRep %s) calculé et inséré dans les trois historiques." % (jour, j["sitrep"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apres")
    ap.add_argument("--jour")
    ap.add_argument("--sitrep")
    a = ap.parse_args()
    if a.apres:
        calculer(a.apres, a.jour, a.sitrep)
    appliquer()
