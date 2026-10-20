# -*- coding: utf-8 -*-
"""Decoupage administratif de l'Ouganda, du Kenya et du Nigeria pour la vue
« Pays touches » de la carte de l'accueil (8 octobre 2026 ; Nigeria ajoute le
20 octobre 2026, premier cas a Abuja).

Les pays touches hors de RDC sont dessines comme la RDC : leurs unites
administratives en creme, celles qui ont eu des cas dans le bleu de la
legende. Ce script ne tourne qu'une fois, comme build_geo.py.

Sources, toutes deux OCHA sur HDX (CC BY-IGO), la meme famille que les zones
de sante de la RDC :
- Ouganda : cod-ab-uga, 135 districts (Uganda Bureau of Statistics, 2020).
  Le district est l'echelon de la sante en Ouganda.
- Kenya : cod-ab-ken, 47 comtes (IEBC, 2019). Le comte est l'echelon de la
  sante au Kenya.
- Nigeria : cod-ab-nga, 36 Etats et le Territoire de la capitale federale
  (Abuja), 2019. L'Etat est l'echelon ou se pilote la riposte (NCDC et
  services de sante de chaque Etat).

geoBoundaries a ete ecarte pour l'Ouganda : son ADM2 est fait de 151 comtes
(subdivisions des districts), et Wakiso n'y existe pas.

Les frontieres exterieures des trois pays (admin0 des memes archives) sont
gardees a part, pour le fin trait qui les entoure sur la carte.

Usage (les fichiers viennent des archives geojson d'OCHA, decompressees) :
    python scripts/build_geo_hors_rdc.py uga_admin2.geojson ken_admin1.geojson \
        nga_admin1.geojson uga_admin0.geojson ken_admin0.geojson nga_admin0.geojson
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_geo import simplify_shared  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(ROOT, "site", "geo", "hors-rdc-admin.json")
# ~2 km : a l'echelle de la vue « Pays touches » un degre fait une trentaine
# de pixels ; simplify_shared garde Kampala (190 km2) et Nairobi.
TOL = 0.02


def contour(chemin):
    return [a for u in unites(chemin, None) for a in u["anneaux"]]


def unites(chemin, champ):
    """Les unites d'un pays, simplifiees ensemble (simplify_shared) : une
    frontiere commune a deux districts est simplifiee une fois, sans vide
    entre eux au zoom (12 octobre 2026)."""
    with io.open(chemin, encoding="utf-8") as fh:
        g = json.load(fh)
    noms, formes = [], []
    for f in g["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        noms.append(f["properties"][champ] if champ else "")
        formes.append([ring for poly in polys for ring in poly])
    out = []
    for nom, anneaux in zip(noms, simplify_shared(formes, [TOL] * len(formes))):
        out.append({"nom": nom, "anneaux": [[[round(x, 4), round(y, 4)] for x, y in a] for a in anneaux]})
    return sorted(out, key=lambda u: u["nom"])


def main():
    if len(sys.argv) != 7:
        sys.exit(__doc__)
    sys.setrecursionlimit(100000)
    doc = {
        "_comment": "Districts de l'Ouganda, comtes du Kenya et Etats du Nigeria, simplifies (Douglas-Peucker %.2f deg). "
                    "OCHA/HDX, CC BY-IGO : cod-ab-uga (UBOS 2020), cod-ab-ken (IEBC 2019), cod-ab-nga (2019). "
                    "Produit par scripts/build_geo_hors_rdc.py." % TOL,
        "UGA": unites(sys.argv[1], "adm2_name"),
        "KEN": unites(sys.argv[2], "adm1_name"),
        "NGA": unites(sys.argv[3], "adm1_name"),
        "contours": {"UGA": contour(sys.argv[4]), "KEN": contour(sys.argv[5]), "NGA": contour(sys.argv[6])},
    }
    with io.open(SORTIE, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
    print("%s : %d districts, %d comtes, %d Etats, %d Ko" % (
        SORTIE, len(doc["UGA"]), len(doc["KEN"]), len(doc["NGA"]), os.path.getsize(SORTIE) // 1024))


if __name__ == "__main__":
    main()
