# -*- coding: utf-8 -*-
"""Trois images de partage (Open Graph / Twitter Card), 1200x630.

Elles sont bâties depuis data/latest.json et site/geo/zones-overview.json : les
chiffres et la carte sont donc toujours ceux du dernier bulletin, sans saisie
manuelle. Les fichiers produits sont des HTML autonomes, à rendre avec
scripts/rendu_image.mjs :

    python scripts/construire_og.py
    node scripts/rendu_image.mjs assets/social/og-1-chiffres.html \\
         assets/social/og-1-chiffres.png 1200 630 2

Mise en garde : les réseaux sociaux mettent les images de partage en cache très
longtemps. Régénérer une image à la même URL ne rafraîchit pas les aperçus déjà
diffusés. Une image qui porte des chiffres doit donc soit changer de nom de
fichier à chaque mise à jour, soit être acceptée comme datée — c'est pourquoi
la troisième proposition n'en porte aucun.
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "social")

BG = "#FDFAF6"
INK = "#1F1A13"
INK_LABEL = "#635D54"
INK_FAINT = "#777068"
LINE = "#DEDAD5"
ACCENT = "#1B6C8C"
ACCENT_STRONG = "#005073"
CRITICAL = "#993A2E"
STABLE = "#327957"
QUIET = "#E6E2DC"
QUIET_LINE = "#D9D4CC"
SCALE = ["#CFE0EA", "#9CC2D6", "#5E97B8", "#1B6C8C", "#005073"]

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
NUM = re.compile(r"-?\d+(?:\.\d+)?")
THRESHOLDS = [10, 50, 200]


def read(path):
    with io.open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


def fmt(n):
    """Séparateur de milliers du site : espace fine insécable."""
    return "{:,}".format(int(n)).replace(",", " ")


def date_longue(iso):
    y, m, d = iso.split("-")
    return "%d %s %s" % (int(d), MOIS[int(m) - 1], y)


geo = read("site/geo/zones-overview.json")
latest = read("data/latest.json")
national = latest["national"]
meta = latest["meta"]


def normalise(name):
    n = "".join(c for c in (name or "").lower() if c.isalnum())
    return geo.get("aliases", {}).get(n, n)


cases = {}
for z in latest["healthZones"]:
    cases[(normalise(z["name"]), normalise(z.get("province")))] = z.get("cases") or 0


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


def carte_svg(hauteur_relative=1.0):
    """La carte du pays, dans la même palette que le site."""
    fond, dessus = [], []
    for z in geo["zones"]:
        lv = level(zone_cases(z))
        if lv == 0:
            fond.append('<path d="%s" fill="%s" stroke="%s" stroke-width="0.5"/>'
                        % (z["d"], QUIET, QUIET_LINE))
        else:
            dessus.append('<path d="%s" fill="%s" stroke="%s" stroke-width="0.6"/>'
                          % (z["d"], SCALE[min(lv + 1, len(SCALE) - 1)], BG))
    x0, y0, x1, y1 = bbox([z["d"] for z in geo["zones"]])
    pad = (x1 - x0) * 0.02
    view = "%.1f %.1f %.1f %.1f" % (x0 - pad, y0 - pad,
                                    (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad)
    return ('<svg viewBox="%s" xmlns="http://www.w3.org/2000/svg" '
            'preserveAspectRatio="xMidYMid meet">%s%s</svg>'
            % (view, "".join(fond), "".join(dessus)))


TETE = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>%(titre)s</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box;}
  html,body{width:1200px;height:630px;overflow:hidden;}
  body{background:%(bg)s;color:%(ink)s;
       font-family:'Public Sans',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;
       -webkit-font-smoothing:antialiased;}
  .kicker{font-size:15px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
          color:%(accent_strong)s;}
  .kicker sup{font-size:.72em;vertical-align:super;line-height:0;}
  /* text-wrap:balance comme sur le site : sans lui, chaque titre laissait un
     mot seul sur la dernière ligne. */
  .accroche{font-family:'Source Serif 4',Georgia,serif;font-weight:400;
            line-height:1.14;letter-spacing:-0.02em;text-wrap:balance;}
  /* Une SVG sans dimensions se cale sur la largeur et déborde en hauteur : la
     pointe sud du pays sortait du cadre. */
  svg{display:block;width:100%%;height:100%%;}
  .accroche em{font-style:italic;color:%(accent_strong)s;}
  .marque{font-size:19px;font-weight:700;letter-spacing:-0.01em;}
  .marque span{color:%(accent)s;}
  .source{font-size:15px;color:%(faint)s;}
  .num{font-variant-numeric:tabular-nums;}
</style></head><body>
"""


def page(nom, titre, corps):
    html = (TETE % {"titre": titre, "bg": BG, "ink": INK, "accent": ACCENT,
                    "accent_strong": ACCENT_STRONG, "faint": INK_FAINT}
            + corps + "\n</body></html>\n")
    path = os.path.join(OUT, nom + ".html")
    io.open(path, "w", encoding="utf-8", newline="\n").write(html)
    print("  ", os.path.relpath(path, ROOT).replace("\\", "/"))


CHIFFRES = [
    ("Cas confirmés", fmt(national["confirmed"]), ACCENT_STRONG,
     "+%s" % fmt(national.get("newCases24h") or 0)),
    ("Décès", fmt(national["deaths"]), CRITICAL,
     "+%s" % fmt(national.get("newDeaths24h") or 0)),
    ("Guéris", fmt(national["recovered"]), STABLE, ""),
]
SOURCE = "SitRep N°%s de l'INSP · %s" % (meta["sitrepNumber"],
                                         date_longue(meta["reportingDate"]))
MARQUE = 'ebola-tracker<span>.org</span>'

# ---------------------------------------------------------- 1. les chiffres
blocs = "".join(
    '<div style="flex:1;border-left:1px solid %s;padding-left:26px;">'
    '<div style="font-size:17px;color:%s;letter-spacing:.02em;margin-bottom:6px;">%s</div>'
    '<div class="num" style="font-size:76px;font-weight:700;line-height:1;color:%s;">%s</div>'
    '<div class="num" style="font-size:19px;font-weight:600;color:%s;margin-top:8px;">%s</div>'
    '</div>' % (LINE, INK_LABEL, label, couleur, valeur, couleur,
                (delta + " en 24 h") if delta else "&nbsp;")
    for label, valeur, couleur, delta in CHIFFRES)

page("og-1-chiffres", "Chiffres", """
<div style="height:630px;padding:62px 66px;display:flex;flex-direction:column;">
  <p class="kicker">17<sup>e</sup> épidémie d'Ebola en République démocratique du Congo</p>
  <h1 class="accroche" style="font-size:54px;margin:16px 0 0;max-width:940px;">
    Comprendre et suivre l'épidémie, <em>chiffre après chiffre</em>.</h1>
  <div style="flex:1;"></div>
  <div style="display:flex;gap:34px;margin-bottom:34px;">%s</div>
  <div style="display:flex;justify-content:space-between;align-items:baseline;
              border-top:1px solid %s;padding-top:20px;">
    <div class="marque">%s</div>
    <div class="source">%s</div>
  </div>
</div>
""" % (blocs, LINE, MARQUE, SOURCE))

# ------------------------------------------------------------- 2. la carte
mini = "".join(
    '<div style="border-left:1px solid %s;padding-left:18px;">'
    '<div style="font-size:14px;color:%s;margin-bottom:4px;">%s</div>'
    '<div class="num" style="font-size:38px;font-weight:700;line-height:1;color:%s;">%s</div>'
    '</div>' % (LINE, INK_LABEL, label, couleur, valeur)
    for label, valeur, couleur, _d in CHIFFRES)

page("og-2-carte", "Carte", """
<div style="height:630px;display:flex;">
  <div style="width:600px;padding:62px 0 52px 66px;display:flex;flex-direction:column;">
    <p class="kicker">17<sup>e</sup> épidémie d'Ebola en RDC</p>
    <h1 class="accroche" style="font-size:46px;margin:14px 0 0;max-width:470px;">
      L'épidémie, zone de santé par <em>zone de santé</em>.</h1>
    <div style="flex:1;"></div>
    <div style="display:flex;gap:26px;margin-bottom:26px;">%s</div>
    <div class="marque">%s</div>
    <div class="source" style="margin-top:8px;">%s</div>
  </div>
  <div style="flex:1;position:relative;padding:34px 46px 34px 0;">
    <div style="width:100%%;height:100%%;">%s</div>
  </div>
</div>
""" % (mini, MARQUE, SOURCE, carte_svg()))

# --------------------------------------------------------- 3. l'editorial
page("og-3-editorial", "Éditorial", """
<div style="height:630px;padding:0 78px;display:flex;flex-direction:column;
            justify-content:center;">
  <p class="kicker">17<sup>e</sup> épidémie d'Ebola en République démocratique du Congo</p>
  <h1 class="accroche" style="font-size:64px;margin:18px 0 0;max-width:1010px;">
    Comprendre et suivre l'épidémie d'Ebola en RDC, <em>chiffre après chiffre</em>.</h1>
  <div style="display:flex;align-items:baseline;gap:18px;margin-top:40px;">
    <div class="marque" style="font-size:22px;">%s</div>
    <div class="source">D'après les bulletins de l'INSP et de l'OMS Afrique</div>
  </div>
</div>
""" % MARQUE)

# La console Windows tourne en cp1252 : l'espace fine des milliers et le tiret
# cadratin la font échouer. Le récapitulatif se replie sur de l'ASCII.
resume = ("%s cas, %s deces, %s gueris - %s"
          % (fmt(national["confirmed"]), fmt(national["deaths"]),
             fmt(national["recovered"]), SOURCE))
print("\n  " + resume.encode("ascii", "replace").decode("ascii"))
