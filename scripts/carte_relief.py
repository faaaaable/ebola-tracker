# -*- coding: utf-8 -*-
"""Carte « Ebola, l'Est en relief », redessinee a chaque bulletin.

La RDC en relief, une colonne par zone de sante, haute de ses cas confirmes.
Le dessin vit dans scripts/relief/ (pages fr, en et vignette sans texte,
commun.js) ; le fond (relief, fleuves, routes, pays, villes, CTE) est fige
dans relief/data/fond.json et dem.png. Ce script :
  1. ecrit relief/data/carto.js (fond + zones, cas et totaux du dernier bulletin) ;
  2. capture les trois pages dans Chrome sans fenetre (capture_page.mjs) ;
  3. ecrit dans assets/img/visuels/ le PNG portrait 4:5 (3200 x 4000), son
     JPEG reduit pour la page Visuels et la vignette de l'accueil ;
  4. note le SitRep et la date dans data/carte-relief.json (lu par visuels.py).

    python scripts/carte_relief.py      # avant build_pages.py ; Node 20+ et Chrome
"""
from __future__ import annotations

import datetime
import http.server
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
from functools import partial

import shapefile
from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = os.path.join(ROOT, "scripts", "relief")
SORTIE = os.path.join(ROOT, "assets", "img", "visuels")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_geo as bg  # noqa: E402

NOMS = {"fr": "ebola-est-en-relief-fr", "en": "ebola-east-in-relief-en"}
FOND = (247, 243, 238)


def lire(*p):
    return json.load(io.open(os.path.join(ROOT, *p), encoding="utf-8"))


def r4(v):
    return round(v, 4)


def centre(ring):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        f = x0 * y1 - x1 * y0
        a += f; cx += (x0 + x1) * f; cy += (y0 + y1) * f
    if abs(a) < 1e-12:
        return ring[0], 0
    return (cx / (3 * a), cy / (3 * a)), abs(a) / 2


def zones_du_bulletin(latest, history, overview):
    """Contours OCHA et chiffres du dernier bulletin, cas des 21 derniers jours."""
    reader = shapefile.Reader(bg.load_shapefile(), encoding="utf-8", encodingErrors="replace")
    champs = [f[0] for f in reader.fields[1:]]
    records = [(dict(zip(champs, sr.record)), sr.shape) for sr in reader.iterShapeRecords()]
    records += bg.zones_supplementaires()
    data, _rapport, alias = bg.match_zones(records, latest["healthZones"])
    alias = dict(overview.get("aliases", {}), **alias)
    cle = lambda n: alias.get(bg.normalise(n, True), bg.normalise(n, True))
    fin = datetime.date.fromisoformat(latest["meta"]["reportingDate"])
    seuil = (fin - datetime.timedelta(days=21)).isoformat()
    avant = [s for s in history if s["date"] <= seuil][-1]
    cumul_avant = {cle(z["name"]): z.get("cases") or 0 for z in avant["zones"]}
    premier = {}
    for snap in history:
        for z in snap["zones"]:
            if (z.get("cases") or 0) > 0:
                premier.setdefault(cle(z["name"]), snap["date"])
    cles = [bg.normalise(rec["Nom"], True) for rec, _ in records]
    simples = bg.simplify_shared([bg.rings(shp) for _, shp in records], [0.01 if k in data else 0.04 for k in cles])
    zones = []
    for (rec, _), k, anneaux in zip(records, cles, simples):
        if not anneaux:
            continue
        (cx, cy), _a = centre(max(anneaux, key=lambda r: centre(r)[1]))
        z = data.get(k)
        if z and bg.normalise(z["province"], True) != bg.normalise(rec["PROVINCE"], True):
            z = None   # homonyme d'une autre province (Lubunga : Tshopo et Kasai)
        zones.append({
            "name": z["name"] if z else rec["Nom"], "key": k,
            "province": z["province"] if z else rec["PROVINCE"],
            "rings": [[[r4(x), r4(y)] for x, y in ring] for ring in anneaux],
            "c": [r4(cx), r4(cy)],
            "cases": z["cases"] if z else 0, "deaths": z["deaths"] if z else 0,
            "first": premier.get(k) if z else None,
            "recent": max(0, z["cases"] - cumul_avant.get(k, 0)) if z else 0,
        })
    manquantes = sorted(set(data) - {z["key"] for z in zones})
    if manquantes:
        print("zones sans contour :", manquantes)
    return zones, avant["date"]


def ecrire_carto(latest):
    carto = json.load(io.open(os.path.join(REL, "data", "fond.json"), encoding="utf-8"))
    zones, depuis = zones_du_bulletin(latest, lire("data", "zones-history.json"), lire("site", "geo", "zones-overview.json"))
    carto.update({"meta": latest["meta"], "national": latest["national"], "provinces": latest["provinces"],
                  "zones": zones, "recentDepuis": depuis})
    with io.open(os.path.join(REL, "data", "carto.js"), "w", encoding="utf-8") as f:
        f.write("window.CARTO=" + json.dumps(carto, ensure_ascii=False, separators=(",", ":")) + ";\n")
    return sum(1 for z in zones if z["cases"])


def capturer(dossier):
    """Les trois pages a taille reelle (?export), echelle 2 : 3200 x 4000."""
    class Muet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), partial(Muet, directory=REL))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    try:
        for page in ("fr", "en", "vignette"):
            out = os.path.join(dossier, page + ".png")
            subprocess.run(["node", "--experimental-websocket", os.path.join(ROOT, "scripts", "verif", "capture_page.mjs"),
                            "http://127.0.0.1:%d/%s.html?export" % (port, page), out, ".affiche", "1616", "2"],
                           check=True, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not os.path.exists(out):
                sys.exit("capture manquee : " + page)
    finally:
        srv.shutdown()


def affiche(chemin):
    """L'affiche seule, sans le fond sombre de la page autour."""
    im = Image.open(chemin).convert("RGB"); w, h = im.size; px = im.load(); clair = lambda p: sum(p) > 600
    x0 = next(x for x in range(w) if clair(px[x, h // 2])); x1 = next(x for x in range(w - 1, -1, -1) if clair(px[x, h // 2]))
    y0 = next(y for y in range(h) if clair(px[w // 2, y])); y1 = next(y for y in range(h - 1, -1, -1) if clair(px[w // 2, y]))
    return im.crop((x0, y0, x1 + 1, y1 + 1))


def contenu(a, marge):
    bb = ImageChops.difference(a, Image.new("RGB", a.size, FOND)).convert("L").point(lambda v: 255 if v > 10 else 0).getbbox()
    return a.crop((max(0, bb[0] - marge), max(0, bb[1] - marge), min(a.size[0], bb[2] + marge), min(a.size[1], bb[3] + marge)))


def main():
    latest = lire("data", "latest.json")
    touchees = ecrire_carto(latest)
    with tempfile.TemporaryDirectory() as d:
        capturer(d)
        for lang, nom in NOMS.items():
            hd = affiche(os.path.join(d, lang + ".png"))
            print(lang, "affiche", hd.size)
            if hd.size != (3200, 4000):
                hd = hd.resize((3200, 4000), Image.LANCZOS)
            hd.save(os.path.join(SORTIE, nom + "-4x5.png"), optimize=True)
            hd.resize((1000, 1250), Image.LANCZOS).save(os.path.join(SORTIE, nom + "-4x5-web.jpg"), quality=86, optimize=True, progressive=True)
        v = contenu(affiche(os.path.join(d, "vignette.png")), 10)
        v.thumbnail((900, 900), Image.LANCZOS)
        v.save(os.path.join(SORTIE, "vitrine-relief.jpg"), quality=86, optimize=True, progressive=True)
    meta = {"sitrep": str(latest["meta"]["sitrepNumber"]), "date": latest["meta"]["reportingDate"], "vignette": list(v.size)}
    with io.open(os.path.join(ROOT, "data", "carte-relief.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("carte en relief : SitRep %s, %d zones touchees, vignette %dx%d" % (meta["sitrep"], touchees, *v.size))


if __name__ == "__main__":
    main()
