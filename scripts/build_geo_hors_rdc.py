# -*- coding: utf-8 -*-
"""Decoupage administratif de l'Ouganda et du Kenya pour la vue « Pays
touches » de la carte de l'accueil (8 octobre 2026).

Les pays touches hors de RDC sont dessines comme la RDC : leurs unites
administratives en creme, celles qui ont eu des cas dans le bleu de la
legende. Ce script ne tourne qu'une fois, comme build_geo.py.

Sources, toutes deux OCHA sur HDX (CC BY-IGO), la meme famille que les zones
de sante de la RDC :
- Ouganda : cod-ab-uga, 135 districts (Uganda Bureau of Statistics, 2020).
  Le district est l'echelon de la sante en Ouganda.
- Kenya : cod-ab-ken, 47 comtes (IEBC, 2019). Le comte est l'echelon de la
  sante au Kenya.

geoBoundaries a ete ecarte pour l'Ouganda : son ADM2 est fait de 151 comtes
(subdivisions des districts), et Wakiso n'y existe pas.

Les frontieres exterieures des deux pays (admin0 des memes archives) sont
gardees a part, pour le fin trait qui les entoure sur la carte.

Usage (les fichiers viennent des archives geojson d'OCHA, decompressees) :
    python scripts/build_geo_hors_rdc.py uga_admin2.geojson ken_admin1.geojson \
        uga_admin0.geojson ken_admin0.geojson
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_geo import simplify_safely  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(ROOT, "site", "geo", "hors-rdc-admin.json")
# ~2 km : a l'echelle de la vue « Pays touches » un degre fait une trentaine
# de pixels ; simplify_safely garde Kampala (190 km2) et Nairobi.
TOL = 0.02


def contour(chemin):
    return [a for u in unites(chemin, None) for a in u["anneaux"]]


def unites(chemin, champ):
    with io.open(chemin, encoding="utf-8") as fh:
        g = json.load(fh)
    out = []
    for f in g["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        anneaux = []
        for poly in polys:
            for ring in poly:
                s = simplify_safely([tuple(p[:2]) for p in ring], TOL)
                if s:
                    anneaux.append([[round(x, 4), round(y, 4)] for x, y in s])
        out.append({"nom": f["properties"][champ] if champ else "", "anneaux": anneaux})
    return sorted(out, key=lambda u: u["nom"])


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    sys.setrecursionlimit(100000)
    doc = {
        "_comment": "Districts de l'Ouganda et comtes du Kenya, simplifies (Douglas-Peucker %.2f deg). "
                    "OCHA/HDX, CC BY-IGO : cod-ab-uga (UBOS 2020), cod-ab-ken (IEBC 2019). "
                    "Produit par scripts/build_geo_hors_rdc.py." % TOL,
        "UGA": unites(sys.argv[1], "adm2_name"),
        "KEN": unites(sys.argv[2], "adm1_name"),
        "contours": {"UGA": contour(sys.argv[3]), "KEN": contour(sys.argv[4])},
    }
    with io.open(SORTIE, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
    print("%s : %d districts, %d comtes, %d Ko" % (
        SORTIE, len(doc["UGA"]), len(doc["KEN"]), os.path.getsize(SORTIE) // 1024))


if __name__ == "__main__":
    main()
