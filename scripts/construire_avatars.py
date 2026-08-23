# -*- coding: utf-8 -*-
"""Trois photos de profil pour X, batties sur les vraies donnees du site.

Contrainte de depart : dans un fil, une photo de profil fait environ 48 px de
cote et se decoupe en rond. Tout ce qui est fin, texte compris, disparait. Les
trois propositions n'utilisent donc que des masses et une seule couleur
d'accent, et sont cadrees pour tenir dans le cercle inscrit.

Sortie : trois fichiers HTML de 400x400, a rendre avec scripts/rendu_image.mjs.
"""
import io
import json
import os
import re

ROOT = r"C:\Users\pemoi\projects\ebola-tracker"
OUT = os.path.dirname(os.path.abspath(__file__))

BG = "#FDFAF6"
INK = "#1F1A13"
QUIET = "#EFECE8"
QUIET_LINE = "#E4E0DB"
SCALE = ["#CFE0EA", "#9CC2D6", "#5E97B8", "#1B6C8C", "#005073"]
ACCENT_STRONG = "#005073"


def read(path):
    with io.open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


geo = read("site/geo/zones-overview.json")
latest = read("data/latest.json")
sitreps = read("data/sitreps.json")

VB = [float(x) for x in geo["viewBox"].split()]
NUM = re.compile(r"-?\d+(?:\.\d+)?")


def normalise(name):
    n = "".join(c for c in (name or "").lower() if c.isalnum())
    return geo.get("aliases", {}).get(n, n)


# Cas par zone, en departageant les homonymes par la province.
cases = {}
for z in latest["healthZones"]:
    cases[(normalise(z["name"]), normalise(z.get("province")))] = z.get("cases") or 0

THRESHOLDS = [10, 50, 200]


def level(n):
    if not n:
        return 0
    for i, limit in enumerate(THRESHOLDS):
        if n < limit:
            return i + 1
    return len(THRESHOLDS) + 1


def zone_cases(z):
    return cases.get((z["key"], normalise(z["province"])), 0)


def bbox(paths):
    xs, ys = [], []
    for d in paths:
        v = [float(t) for t in NUM.findall(d)]
        xs += v[0::2]
        ys += v[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def square_view(x0, y0, x1, y1, pad=0.10):
    """Cadre carre centre sur la boite, marge relative — un avatar est carre
    puis rogne en rond, tout etirement se verrait."""
    w, h = x1 - x0, y1 - y0
    side = max(w, h) * (1 + 2 * pad)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    return "%.1f %.1f %.1f %.1f" % (cx - side / 2, cy - side / 2, side, side)


PAGE = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>%(titre)s</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box;}
  html,body{width:400px;height:400px;overflow:hidden;}
  body{background:%(bg)s;display:flex;align-items:center;justify-content:center;
       font-family:'Public Sans',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;}
  svg{display:block;width:400px;height:400px;}
</style></head>
<body>
%(corps)s
</body></html>
"""


def write(name, titre, corps):
    path = os.path.join(OUT, name + ".html")
    io.open(path, "w", encoding="utf-8", newline="\n").write(
        PAGE % {"titre": titre, "bg": BG, "corps": corps})
    print("  ", name + ".html")


# ---------------------------------------------------------------- 1. la RDC
# Le pays en silhouette pleine plutot qu'en maillage clair : a 48 px, un
# maillage gris pale sur fond creme ne fait plus qu'une tache. Une masse
# sombre avec la grappe bleue au nord-est garde du contraste.
paths = []
for z in geo["zones"]:
    lv = level(zone_cases(z))
    if lv == 0:
        paths.append('<path d="%s" fill="#D9D4CC" stroke="#D9D4CC" stroke-width="1.2"/>'
                     % z["d"])
for z in geo["zones"]:
    lv = level(zone_cases(z))
    if lv:
        paths.append('<path d="%s" fill="%s" stroke="%s" stroke-width="0.6"/>'
                     % (z["d"], SCALE[min(lv + 1, len(SCALE) - 1)], BG))
cx0, cy0, cx1, cy1 = bbox([z["d"] for z in geo["zones"]])
write("avatar-1-rdc", "RDC",
      '<svg viewBox="%s" xmlns="http://www.w3.org/2000/svg">%s</svg>'
      % (square_view(cx0, cy0, cx1, cy1, pad=0.10), "".join(paths)))

# --------------------------------------------------------- 2. l'epicentre
# Cadrage serre sur les zones touchees : a 48 px, une mosaique bleue lit
# beaucoup mieux qu'un pays entier reduit a un pate.
touched = [z for z in geo["zones"] if zone_cases(z) > 0]
x0, y0, x1, y1 = bbox([z["d"] for z in touched])
near = []
for z in geo["zones"]:
    bx0, by0, bx1, by1 = bbox([z["d"]])
    if bx1 < x0 - 40 or bx0 > x1 + 40 or by1 < y0 - 40 or by0 > y1 + 40:
        continue
    n = zone_cases(z)
    lv = level(n)
    if lv == 0:
        near.append('<path d="%s" fill="%s" stroke="%s" stroke-width="0.6"/>'
                    % (z["d"], QUIET, QUIET_LINE))
    else:
        near.append('<path d="%s" fill="%s" stroke="%s" stroke-width="0.9"/>'
                    % (z["d"], SCALE[min(lv, len(SCALE) - 1)], BG))
write("avatar-2-epicentre", "Epicentre",
      '<svg viewBox="%s" xmlns="http://www.w3.org/2000/svg">%s</svg>'
      % (square_view(x0, y0, x1, y1, pad=0.07), "".join(near)))

# ------------------------------------------------------------- 3. la courbe
# La courbe des cas cumules, du premier bulletin au dernier. Une seule forme,
# montante : c'est ce que le site raconte, et ca tient a n'importe quelle
# taille.
pts = [(s["date"], s.get("confirmed") or 0) for s in sitreps]
peak = max(v for _d, v in pts) or 1
W, H = 100.0, 62.0
coords = []
for i, (_d, v) in enumerate(pts):
    x = i / float(len(pts) - 1) * W
    y = H - (v / float(peak)) * H
    coords.append((x, y))
line = "M" + "L".join("%.2f %.2f" % c for c in coords)
area = line + "L%.2f %.2f L0 %.2f Z" % (W, H, H)
# Pas d'aire fermee : le retour a la ligne de base dessinait un bord droit
# vertical qui donnait un triangle rectangle. La courbe seule suffit, et le
# cadrage laisse de l'air pour que le rond ne la rogne pas.
corps = (
    '<svg viewBox="-26 -30 152 122" xmlns="http://www.w3.org/2000/svg">'
    '<path d="%s" fill="none" stroke="%s" stroke-width="6" '
    'stroke-linejoin="round" stroke-linecap="round"/>'
    '<circle cx="%.2f" cy="%.2f" r="7.5" fill="%s" stroke="%s" stroke-width="3.5"/>'
    '</svg>' % (line, ACCENT_STRONG,
                coords[-1][0], coords[-1][1], ACCENT_STRONG, BG))
write("avatar-3-courbe", "Courbe", corps)

print("\n  %d zones touchees tracees, courbe sur %d bulletins (pic %d cas)"
      % (len(touched), len(pts), peak))
