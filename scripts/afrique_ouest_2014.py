"""Construit data/afrique-ouest-2014.csv : l'epidemie d'Afrique de l'Ouest
2014-2016, pays par pays (Guinee, Liberia, Sierra Leone), cas et deces
cumules (confirmes, probables et suspects, la definition du bilan de l'OMS :
28 616 cas, 11 310 deces, rapport de situation du 2 juin 2016), A LA DATE DES
DONNEES. Sert au visuel « comparaison avec 2014 » de la page Visuels.

Deux sources, sans recouvrement :
  - jusqu'au 24 aout 2014 : C. Rivers, github.com/cmrivers/ebola,
    country_timeseries.csv (releves de l'OMS recopies a la main) ;
  - a partir du 25 aout 2014 : OMS, rapports de situation, via HDX
    (data.humdata.org/dataset/ebola-cases-2014,
    ebola-cases-and-deaths-who-gar-sitrep.xls) : une feuille par rapport,
    pour chaque pays la date de ses donnees (« Country Report Date ») et la
    ligne « All ». Exemple : rapport du 22 septembre 2014, Guinee au 20,
    Liberia au 17, Sierra Leone au 19 ; 5 843 cas, 2 803 deces.

Ne tourne qu'une fois (donnees figees) ; demande xlrd 2.x :
    python scripts/afrique_ouest_2014.py country_timeseries.csv who-gar-sitrep.xls
"""
from __future__ import annotations

import csv
import datetime as dt
import os
import re
import sys

import xlrd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYS = {"Guinea": "Guinee", "Liberia": "Liberia", "Sierra Leone": "Sierra Leone"}
DEBUT_OMS = dt.date(2014, 8, 25)
MOIS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def date_rapport(nom, donnees):
    """« Sep 22 », « Sep 16 2014 », « Dec 30, 2015 » : l'annee manque parfois,
    c'est celle des donnees (ou la suivante, rapport de janvier sur decembre)."""
    m = re.match(r"([A-Za-z]{3})[a-z]*\.?\s+(\d+),?\s*(\d{4})?", nom.strip())
    mois, jour = MOIS[m.group(1).lower()], int(m.group(2))
    an = int(m.group(3)) if m.group(3) else donnees.year + (mois < donnees.month)
    return dt.date(an, mois, jour)


def main(rivers, gar):
    lignes = []
    for r in csv.DictReader(open(rivers, encoding="utf-8")):
        d = dt.datetime.strptime(r["Date"], "%m/%d/%Y").date()
        if d >= DEBUT_OMS:
            continue
        for p, col in (("Guinea", "Guinea"), ("Liberia", "Liberia"), ("Sierra Leone", "SierraLeone")):
            if r["Cases_" + col]:
                lignes.append((d, PAYS[p], int(float(r["Cases_" + col])),
                               int(float(r["Deaths_" + col])) if r["Deaths_" + col] else "", "", "C. Rivers"))
    b = xlrd.open_workbook(gar)
    for s in b.sheets():
        h = [str(x).strip().lower() for x in s.row_values(0)]
        ic, idd = h.index("total cases"), h.index("total deaths")
        it = [i for i, x in enumerate(h) if x.startswith("country report date")][0]
        cur = date = None
        for i in range(1, s.nrows):
            v = s.row_values(i)
            if str(v[0]).strip() and str(v[0]).strip() != cur:
                cur, date = str(v[0]).strip(), None
            if v[it] not in ("", None):
                date = xlrd.xldate_as_datetime(v[it], b.datemode).date()
            if str(v[1]).strip().lower() == "all" and cur in PAYS and date and date >= DEBUT_OMS:
                lignes.append((date, PAYS[cur], int(v[ic]), int(v[idd]) if v[idd] != "" else "",
                               date_rapport(s.name, date).isoformat(), "OMS"))
    # un meme pays a la meme date dans deux rapports : le plus recent l'emporte
    garde = {}
    for x in sorted(lignes, key=lambda x: (x[0], x[1], x[4])):
        garde[(x[0], x[1])] = x
    with open(os.path.join(ROOT, "data", "afrique-ouest-2014.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date_donnees", "pays", "cas", "deces", "rapport_oms", "source"])
        for x in sorted(garde.values(), key=lambda x: (x[0], x[1])):
            w.writerow([x[0].isoformat(), *x[1:]])
    print(len(garde), "lignes")


if __name__ == "__main__":
    main(*sys.argv[1:3])
