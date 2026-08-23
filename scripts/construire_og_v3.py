# -*- coding: utf-8 -*-
"""Trois images de partage batties sur la carte de l'epicentre.

Reprend le principe de la v3 en ligne — la courbe cumulee en pied de cadre,
aucun chiffre ecrit — mais remplace le titre par un zoom cartographique sur le
foyer, avec le domaine au centre.

Le cadrage n'est pas choisi a la main : il se calcule sur la boite englobante
des zones de sante qui ont rapporte des cas. La carte suit donc l'epidemie, et
se recentrera d'elle-meme si le foyer se deplace.

Aucun chiffre n'est ecrit : ces images ne peuvent donc pas afficher un total
faux dans un apercu que les reseaux sociaux garderaient en cache des semaines.

    python scripts/construire_og_v3.py
    node scripts/rendu_image.mjs tmp/og-v3/a-epicentre.html \\
         tmp/og-v3/a-epicentre.png 1200 630 2

Sorties dans tmp/og-v3/. La proposition retenue est C — « le plein cadre » —
copiee dans assets/og-image-v3.png et referencee par site/pages.json. Les deux
autres restent la comme brouillons.

Pour la remplacer un jour : regenerer, copier vers assets/og-image-v4.png, et
changer ogImage dans site/pages.json. Le numero de version doit changer —
reecrire la meme URL ne fait pas relire l'image par les caches des reseaux
sociaux.
"""
import io
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tmp", "og-v3")

BG = "#FDFAF6"
INK = "#1F1A13"
INK_FAINT = "#777068"
LINE = "#DEDAD5"
ACCENT = "#1B6C8C"
ACCENT_STRONG = "#005073"
ACCENT_LIGHT = "#D5ECF8"
CRITICAL = "#993A2E"
QUIET = "#E6E2DC"
QUIET_LINE = "#D9D4CC"
SCALE = ["#CFE0EA", "#9CC2D6", "#5E97B8", "#1B6C8C", "#005073"]
NUM = re.compile(r"-?\d+(?:\.\d+)?")
SEUILS = [10, 50, 200]


def lire(chemin):
    with io.open(os.path.join(ROOT, chemin), encoding="utf-8") as fh:
        return json.load(fh)


geo = lire("site/geo/zones-overview.json")
latest = lire("data/latest.json")
history = lire("data/province-history.json")


def normalise(nom):
    t = "".join(c for c in (nom or "").lower() if c.isalnum())
    return geo.get("aliases", {}).get(t, t)


CAS = {}
for z in latest["healthZones"]:
    CAS[(normalise(z["name"]), normalise(z.get("province")))] = z.get("cases") or 0


def cas_de(z):
    return CAS.get((z["key"], normalise(z["province"])), 0)


def palier(n):
    if not n:
        return 0
    for i, seuil in enumerate(SEUILS):
        if n < seuil:
            return i + 1
    return len(SEUILS) + 1


def boite(chemins):
    xs, ys = [], []
    for d in chemins:
        v = [float(t) for t in NUM.findall(d)]
        xs += v[0::2]
        ys += v[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def cadrage(zoom, ratio):
    """Fenetre centree sur le foyer reel, au ratio du cadre.

    Deux pieges evites ici. Cadrer sur la province figerait l'image le jour ou
    l'epidemie deborde. Et cadrer sur le centre GEOMETRIQUE des zones touchees
    le placerait a (826, 257), alors que l'epidemie pese a (930, 204) : les
    zones de l'ouest, qui ne comptent que quelques cas, tiraient le cadre vers
    un vide gris. Le centre pondere par le nombre de cas suit le foyer.

    `zoom` est la hauteur de la fenetre en part de la boite des zones
    touchees : 1.0 les montre toutes, 0.6 resserre sur le coeur.
    """
    touchees = [z for z in geo["zones"] if cas_de(z)]
    if not touchees:
        touchees = geo["zones"]
    x0, y0, x1, y1 = boite([z["d"] for z in touchees])
    total = sum(cas_de(z) for z in touchees) or 1
    cx = cy = 0.0
    for z in touchees:
        a0, b0, a1, b1 = boite([z["d"]])
        poids = cas_de(z) / float(total)
        cx += (a0 + a1) / 2.0 * poids
        cy += (b0 + b1) / 2.0 * poids
    hauteur = (y1 - y0) * zoom
    largeur = hauteur * ratio
    return cx - largeur / 2.0, cy - hauteur / 2.0, largeur, hauteur


def carte_svg(marge, ratio, avec_point=True):
    x0, y0, w, h = cadrage(marge, ratio)
    fond, dessus = [], []
    for z in geo["zones"]:
        lv = palier(cas_de(z))
        if lv == 0:
            fond.append('<path d="%s" fill="%s" stroke="%s" stroke-width="0.4"/>'
                        % (z["d"], QUIET, QUIET_LINE))
        else:
            dessus.append('<path d="%s" fill="%s" stroke="%s" stroke-width="0.5"/>'
                          % (z["d"], SCALE[min(lv + 1, len(SCALE) - 1)], BG))
    point = ""
    if avec_point:
        bunia = next((m for m in geo["landmarks"] if m.get("kind") == "epicenter"), None)
        if bunia:
            r = w / 150.0
            point = ('<circle cx="%.1f" cy="%.1f" r="%.2f" fill="none" stroke="%s" '
                     'stroke-width="%.2f" opacity=".55"/>'
                     '<circle cx="%.1f" cy="%.1f" r="%.2f" fill="%s"/>'
                     % (bunia["x"], bunia["y"], r * 2.6, CRITICAL, r * 0.5,
                        bunia["x"], bunia["y"], r, CRITICAL))
    return ('<svg viewBox="%.1f %.1f %.1f %.1f" xmlns="http://www.w3.org/2000/svg" '
            'preserveAspectRatio="xMidYMid slice">%s%s%s</svg>'
            % (x0, y0, w, h, "".join(fond), "".join(dessus), point))


def courbe_svg(w, h, epaisseur=5.0, point=True, aire=True):
    serie = sorted((e["date"], sum((p["confirmed"] or 0) for p in e["provinces"]))
                   for e in history)
    n = len(serie)
    haut = max(v for _d, v in serie) or 1
    pad_x = epaisseur * 3 + 6
    pad_y = epaisseur * 1.6

    def x(i):
        return pad_x + (w - 2 * pad_x) * i / float(n - 1)

    def y(v):
        return h - pad_y - (h - 2 * pad_y) * v / float(haut)

    pts = [(x(i), y(v)) for i, (_d, v) in enumerate(serie)]
    ligne = "M" + " L".join("%.1f %.1f" % p for p in pts)
    remplissage = ""
    if aire:
        ferme = ligne + " L%.1f %.1f L%.1f %.1f Z" % (pts[-1][0], h, pts[0][0], h)
        remplissage = '<path d="%s" fill="%s" opacity=".5"/>' % (ferme, ACCENT_LIGHT)
    fin = ""
    if point:
        fin = ('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" '
               'stroke-width="%.1f"/>'
               % (pts[-1][0], pts[-1][1], epaisseur * 1.5, CRITICAL, BG, epaisseur * 0.6))
    return ('<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" '
            'preserveAspectRatio="none">%s'
            '<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" '
            'stroke-linecap="round" stroke-linejoin="round"/>%s</svg>'
            % (w, h, remplissage, ligne, ACCENT_STRONG, epaisseur, fin))


def position_bunia(zoom, ratio):
    """Position de Bunia dans la fenetre, en pourcentage de largeur et de
    hauteur.

    Sert a poser le marqueur PAR-DESSUS le voile. Dessine a l'interieur de la
    carte, il passait sous un degrade opaque a pres de 80 % a cette hauteur, et
    disparaissait — c'est ce qui le rendait invisible dans la version C.
    """
    x0, y0, w, h = cadrage(zoom, ratio)
    bunia = next((m for m in geo["landmarks"] if m.get("kind") == "epicenter"), None)
    if not bunia:
        return 50.0, 50.0
    return 100.0 * (bunia["x"] - x0) / w, 100.0 * (bunia["y"] - y0) / h


MARQUE = 'ebola-tracker<span>.org</span>'

TETE = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>%(titre)s</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box;}
  html,body{width:%(largeur)dpx;height:%(hauteur)dpx;overflow:hidden;}
  body{background:%(bg)s;color:%(ink)s;
       font-family:'Public Sans',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;
       -webkit-font-smoothing:antialiased;}
  svg{display:block;width:100%%;height:100%%;}
  .marque{font-weight:700;letter-spacing:-0.015em;line-height:1;}
  .marque span{color:%(accent)s;}
</style></head><body>
"""


def page(nom, titre, corps, largeur=1200, hauteur=630):
    """Ecrit la page. La taille est un parametre, pas une constante.

    Elle etait figee a 1200x630 dans la feuille de style : sur la banniere, qui
    fait 1500 px de large, `overflow:hidden` coupait tout au-dela de 1200 — soit
    le dernier quart de la courbe, son point final, et un pan de carte que
    j'avais pris pour un vide geographique.
    """
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    html = (TETE % {"titre": titre, "bg": BG, "ink": INK, "accent": ACCENT,
                    "largeur": largeur, "hauteur": hauteur}
            + corps + "\n</body></html>\n")
    io.open(os.path.join(OUT, nom + ".html"), "w",
            encoding="utf-8", newline="\n").write(html)
    print("   tmp/og-v3/%s.html" % nom)


# --------------------------------------------------------- A. L'epicentre
# Carte plein cadre, legerement voilee pour que le domaine reste lisible
# par-dessus, courbe en bande basse.
page("a-epicentre", "Epicentre", """
<div style="position:relative;width:1200px;height:630px;">
  <div style="position:absolute;inset:0;">%s</div>
  <div style="position:absolute;inset:0;background:%s;opacity:.62;"></div>
  <div style="position:absolute;left:0;right:0;bottom:0;height:168px;">%s</div>
  <div style="position:absolute;inset:0;display:flex;align-items:center;
              justify-content:center;padding-bottom:70px;">
    <div class="marque" style="font-size:62px;">%s</div>
  </div>
</div>
""" % (carte_svg(0.78, 1200 / 630.0), BG, courbe_svg(1200, 168), MARQUE))

# ------------------------------------------------------- B. La capture
# La carte prise comme une capture d'ecran : panneau arrondi, bordure fine,
# fond papier autour. Le domaine se pose a la jonction carte / courbe.
page("b-capture", "Capture", """
<div style="position:relative;width:1200px;height:630px;padding:34px 34px 0;">
  <div style="position:relative;height:396px;border-radius:14px;overflow:hidden;
              border:1px solid %s;background:%s;">
    <div style="position:absolute;inset:0;">%s</div>
  </div>
  <div style="position:absolute;left:34px;right:34px;bottom:0;height:170px;
              border-radius:0 0 14px 14px;overflow:hidden;">%s</div>
  <div style="position:absolute;left:0;right:0;top:352px;display:flex;
              justify-content:center;">
    <div style="background:%s;border:1px solid %s;border-radius:40px;
                padding:16px 38px;box-shadow:0 2px 14px rgba(31,26,19,.10);">
      <div class="marque" style="font-size:40px;">%s</div>
    </div>
  </div>
</div>
""" % (LINE, QUIET, carte_svg(0.86, 1132 / 396.0), courbe_svg(1132, 170),
       "#FFFDFB", LINE, MARQUE))

# ------------------------------------------------------ C. Le plein cadre
# Zoom serre : les zones deviennent de grandes formes, la carte est une
# texture plutot qu'un document.
#
# Trois choix propres a cette version. La courbe porte son aire bleu ciel,
# comme A et B. Elle monte un peu plus haut dans le cadre, la bande passant de
# 112 a 158 px. Et le marqueur de Bunia est dessine PAR-DESSUS le voile, sinon
# le degrade l'efface a cette hauteur.
ZOOM_C = 0.52
BUNIA_X, BUNIA_Y = position_bunia(ZOOM_C, 1200 / 630.0)

page("c-plein-cadre", "Plein cadre", """
<div style="position:relative;width:1200px;height:630px;">
  <div style="position:absolute;inset:0;">%s</div>
  <div style="position:absolute;inset:0;
              background:linear-gradient(180deg,rgba(253,250,246,.30) 0%%,
                                         rgba(253,250,246,.80) 46%%,
                                         rgba(253,250,246,.94) 100%%);"></div>
  <div style="position:absolute;left:%.2f%%;top:%.2f%%;transform:translate(-50%%,-50%%);
              width:60px;height:60px;display:flex;align-items:center;
              justify-content:center;">
    <span style="position:absolute;inset:0;border-radius:50%%;
                 border:3px solid %s;opacity:.24;"></span>
    <span style="width:20px;height:20px;border-radius:50%%;background:%s;
                 opacity:.68;box-shadow:0 0 0 5px rgba(253,250,246,.45);"></span>
  </div>
  <div style="position:absolute;left:0;right:0;bottom:0;height:158px;opacity:.92;">%s</div>
  <div style="position:absolute;inset:0;display:flex;align-items:center;
              justify-content:center;padding-top:96px;">
    <div style="text-align:center;">
      <div class="marque" style="font-size:74px;">%s</div>
    </div>
  </div>
</div>
""" % (carte_svg(ZOOM_C, 1200 / 630.0, avec_point=False),
       BUNIA_X, BUNIA_Y, CRITICAL, CRITICAL,
       courbe_svg(1200, 158, 4.5, True, True), MARQUE))

# ------------------------------------------------ D. Banniere X (1500x500)
# Meme composition que C, mais en 3:1 et avec deux contraintes propres a X :
# la photo de profil recouvre le coin bas-gauche sur environ 200 px, et
# l'application mobile rogne les cotes. Tout ce qui compte reste donc au
# centre, et le quart inferieur gauche est laisse libre.
ZOOM_D = 0.44
RATIO_D = 1500 / 500.0
BX, BY = position_bunia(ZOOM_D, RATIO_D)

page("d-banniere-x", "Banniere X", """
<div style="position:relative;width:1500px;height:500px;">
  <div style="position:absolute;inset:0;">%s</div>
  <div style="position:absolute;inset:0;
              background:linear-gradient(180deg,rgba(253,250,246,.34) 0%%,
                                         rgba(253,250,246,.80) 52%%,
                                         rgba(253,250,246,.93) 100%%);"></div>
  <div style="position:absolute;left:%.2f%%;top:%.2f%%;transform:translate(-50%%,-50%%);
              width:52px;height:52px;display:flex;align-items:center;
              justify-content:center;">
    <span style="position:absolute;inset:0;border-radius:50%%;
                 border:3px solid %s;opacity:.24;"></span>
    <span style="width:17px;height:17px;border-radius:50%%;background:%s;
                 opacity:.68;box-shadow:0 0 0 5px rgba(253,250,246,.45);"></span>
  </div>
  <!-- La courbe s'arrete a 320 px du bord gauche : au-dela, la photo de
       profil la recouvrirait. -->
  <div style="position:absolute;left:320px;right:0;bottom:0;height:132px;opacity:.92;">%s</div>
  <div style="position:absolute;inset:0;display:flex;align-items:center;
              justify-content:center;padding-top:64px;">
    <div class="marque" style="font-size:60px;">%s</div>
  </div>
</div>
""" % (carte_svg(ZOOM_D, RATIO_D, avec_point=False),
       BX, BY, CRITICAL, CRITICAL,
       courbe_svg(1180, 132, 4.0, True, True), MARQUE), 1500, 500)

x0, y0, w, h = cadrage(0.86, 1132 / 396.0)
touchees = sum(1 for z in geo["zones"] if cas_de(z))
print("\n   %d zones touchees, cadrage %.0fx%.0f centre sur (%.0f, %.0f)"
      % (touchees, w, h, x0 + w / 2, y0 + h / 2))
