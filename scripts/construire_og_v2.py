# -*- coding: utf-8 -*-
"""Trois nouvelles propositions d'image de partage (1200x630).

Elles corrigent ce que la serie precedente ratait a la taille reelle
d'affichage (~500 px de large dans un fil) :

  - composition centree, pour survivre au recadrage carre que font WhatsApp,
    iMessage et certains apercus Slack ;
  - le domaine remonte hors du coin, la ou aucun recadrage ne l'emporte ;
  - une seule ligne d'accroche, qui ne concurrence plus les chiffres ;
  - aucun element porteur de sens sous 24 px.

Sorties dans tmp/og-v2/ tant que le choix n'est pas fait : rien ne touche
assets/. Rendu :

    python scripts/construire_og_v2.py
    node scripts/rendu_image.mjs tmp/og-v2/p1-compteur.html \\
         tmp/og-v2/p1-compteur.png 1200 630 2

Rappel de cache : une image qui porte des chiffres doit changer d'URL a chaque
regeneration, sinon les apercus deja diffuses resteront figes. P3 n'ecrit
aucun chiffre : elle ne peut donc pas afficher de total faux.
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tmp", "og-v2")

BG = "#FDFAF6"
INK = "#1F1A13"
INK_LABEL = "#635D54"
INK_FAINT = "#777068"
LINE = "#DEDAD5"
ACCENT = "#1B6C8C"
ACCENT_STRONG = "#005073"
ACCENT_LIGHT = "#D5ECF8"
CRITICAL = "#993A2E"
STABLE = "#327957"

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


def read(path):
    with io.open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


def fmt(n):
    """Separateur de milliers du site : espace fine insecable."""
    return "{:,}".format(int(n)).replace(",", " ")


def date_longue(iso):
    y, m, d = iso.split("-")
    return "%d %s %s" % (int(d), MOIS[int(m) - 1], y)


latest = read("data/latest.json")
national = latest["national"]
meta = latest["meta"]
history = read("data/province-history.json")

SOURCE = "SitRep N°%s de l'INSP · %s" % (
    meta["sitrepNumber"], date_longue(meta["reportingDate"]))
MARQUE = "ebola-tracker<span>.org</span>"
KICKER = ("17<sup>e</sup> épidémie d'Ebola en République "
          "démocratique du Congo")

CHIFFRES = [
    ("Cas confirmés", fmt(national["confirmed"]), ACCENT_STRONG,
     "+%s en 24 h" % fmt(national.get("newCases24h") or 0)),
    ("Décès", fmt(national["deaths"]), CRITICAL,
     "+%s en 24 h" % fmt(national.get("newDeaths24h") or 0)),
    ("Guéris", fmt(national["recovered"]), STABLE, "&nbsp;"),
]


# --------------------------------------------------------------------------
# La courbe cumulee nationale, reconstruite depuis l'historique par province.
# --------------------------------------------------------------------------
def courbe_svg(w, h, epaisseur=5.0, point=True):
    serie = [(e["date"], sum((p["confirmed"] or 0) for p in e["provinces"]))
             for e in history]
    serie.sort()
    n = len(serie)
    top = max(v for _d, v in serie) or 1
    # Le point final est un disque : il lui faut sa place, sinon il sort du
    # cadre a droite. Le premier rendu le coupait en deux.
    pad_x = epaisseur * 1.5 + (epaisseur * 1.5 if point else 0) + 6
    pad_y = epaisseur * 1.6

    def x(i):
        return pad_x + (w - 2 * pad_x) * i / float(n - 1)

    def y(v):
        return h - pad_y - (h - 2 * pad_y) * v / float(top)

    pts = [(x(i), y(v)) for i, (_d, v) in enumerate(serie)]
    ligne = "M" + " L".join("%.1f %.1f" % p for p in pts)
    aire = ligne + " L%.1f %.1f L%.1f %.1f Z" % (pts[-1][0], h, pts[0][0], h)
    fin = ""
    if point:
        fin = ('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" '
               'stroke-width="%.1f"/>'
               % (pts[-1][0], pts[-1][1], epaisseur * 1.5, CRITICAL, BG,
                  epaisseur * 0.6))
    return ('<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" '
            'preserveAspectRatio="none">'
            '<path d="%s" fill="%s" opacity=".55"/>'
            '<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" '
            'stroke-linecap="round" stroke-linejoin="round"/>%s</svg>'
            % (w, h, aire, ACCENT_LIGHT, ligne, ACCENT_STRONG, epaisseur, fin))


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
  .kicker{font-size:16px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
          color:%(accent_strong)s;}
  .kicker sup{font-size:.72em;vertical-align:super;line-height:0;}
  .accroche{font-family:'Source Serif 4',Georgia,serif;font-weight:400;
            line-height:1.14;letter-spacing:-0.02em;text-wrap:balance;}
  .accroche em{font-style:italic;color:%(accent_strong)s;}
  .marque{font-size:22px;font-weight:700;letter-spacing:-0.01em;}
  .marque span{color:%(accent)s;}
  .source{font-size:16px;color:%(faint)s;}
  .num{font-variant-numeric:tabular-nums;}
  svg{display:block;width:100%%;height:100%%;}
</style></head><body>
"""


def page(nom, titre, corps):
    html = (TETE % {"titre": titre, "bg": BG, "ink": INK, "accent": ACCENT,
                    "accent_strong": ACCENT_STRONG, "faint": INK_FAINT}
            + corps + "\n</body></html>\n")
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    io.open(os.path.join(OUT, nom + ".html"), "w",
            encoding="utf-8", newline="\n").write(html)
    print("   tmp/og-v2/%s.html" % nom)


# ------------------------------------------------------- P1 . Le compteur
# Tout est centre et tenu dans les 630 px du milieu : c'est la seule
# disposition qui reste lisible quand l'apercu est rogne au carre.
blocs = "".join(
    '<div style="width:260px;text-align:center;">'
    '<div style="font-size:17px;color:%s;margin-bottom:10px;">%s</div>'
    '<div class="num" style="font-size:72px;font-weight:700;line-height:1;'
    'color:%s;">%s</div>'
    '<div class="num" style="font-size:17px;font-weight:600;color:%s;'
    'margin-top:9px;">%s</div>'
    '</div>' % (INK_LABEL, label, couleur, valeur, couleur, delta)
    for label, valeur, couleur, delta in CHIFFRES)

page("p1-compteur", "Compteur", """
<div style="height:630px;padding:54px 66px 46px;display:flex;flex-direction:column;
            align-items:center;text-align:center;">
  <p class="kicker">%s</p>
  <h1 class="accroche" style="font-size:46px;margin:18px 0 0;max-width:820px;">
    Le suivi quotidien, <em>bulletin apr&egrave;s bulletin</em>.</h1>
  <div style="flex:1;"></div>
  <div style="display:flex;gap:22px;justify-content:center;">%s</div>
  <div style="flex:1;"></div>
  <div style="border-top:1px solid %s;padding-top:22px;width:100%%;
              display:flex;justify-content:center;align-items:baseline;gap:18px;">
    <span class="marque">%s</span>
    <span class="source">%s</span>
  </div>
</div>
""" % (KICKER, blocs, LINE, MARQUE, SOURCE))

# --------------------------------------------------------- P2 . La courbe
mini = "".join(
    '<div style="text-align:center;">'
    '<div style="font-size:15px;color:%s;margin-bottom:6px;">%s</div>'
    '<div class="num" style="font-size:52px;font-weight:700;line-height:1;'
    'color:%s;">%s</div>'
    '</div>' % (INK_LABEL, label, couleur, valeur)
    for label, valeur, couleur, _d in CHIFFRES)

page("p2-courbe", "Courbe", """
<div style="height:630px;display:flex;flex-direction:column;">
  <div style="padding:52px 66px 0;display:flex;flex-direction:column;
              align-items:center;text-align:center;">
    <p class="kicker">%s</p>
    <h1 class="accroche" style="font-size:44px;margin:16px 0 26px;max-width:800px;">
      Trois mois d'&eacute;pid&eacute;mie, <em>jour apr&egrave;s jour</em>.</h1>
    <div style="display:flex;gap:72px;justify-content:center;">%s</div>
  </div>
  <div style="flex:1;"></div>
  <div style="height:206px;">%s</div>
  <div style="padding:26px 66px 34px;display:flex;justify-content:center;
              align-items:baseline;gap:18px;">
    <span class="marque">%s</span>
    <span class="source">%s</span>
  </div>
</div>
""" % (KICKER, mini, courbe_svg(1200, 210), MARQUE, SOURCE))

# --------------------------------------------------------- P3 . La source
# Aucun chiffre ecrit : rien qui puisse etre faux dans un apercu vieux de
# trois semaines. La courbe vieillit, elle, mais une forme sans valeurs
# n'affirme rien de verifiable — c'est un aging bien plus doux qu'un total
# perime.
MARQUE_SVG = ('<svg viewBox="0 0 32 32" style="width:56px;height:56px;">'
              '<rect width="32" height="32" rx="7" fill="#003455"/>'
              '<circle cx="16" cy="16" r="11" fill="none" stroke="#2C87AD" '
              'stroke-width="2"/>'
              '<circle cx="16" cy="16" r="4.6" fill="#C0503A"/></svg>')

page("p3-source", "Source", """
<div style="height:630px;display:flex;flex-direction:column;">
  <div style="flex:1;padding:0 78px;display:flex;flex-direction:column;
              align-items:center;justify-content:center;text-align:center;">
    <div style="margin-bottom:26px;">%s</div>
    <p class="kicker">%s</p>
    <h1 class="accroche" style="font-size:56px;margin:20px 0 0;max-width:920px;">
      Comprendre et suivre l'&eacute;pid&eacute;mie, <em>chiffre apr&egrave;s chiffre</em>.</h1>
    <p class="marque" style="font-size:24px;margin-top:34px;">%s</p>
  </div>
  <div style="height:186px;">%s</div>
</div>
""" % (MARQUE_SVG, KICKER, MARQUE, courbe_svg(1200, 186)))

print("\n   " + ("%s cas, %s deces, %s gueris - %s"
                 % (fmt(national["confirmed"]), fmt(national["deaths"]),
                    fmt(national["recovered"]), SOURCE)
                 ).encode("ascii", "replace").decode("ascii"))
