# -*- coding: utf-8 -*-
"""Carte du parcours du premier malade du Kenya, de Buta a Nairobi (page
Kenya, 20 octobre 2026 ; maquette 1 de tmp/proto-kenya-parcours-1019).

Fond : la carte de l'accueil (zones de sante coloriees par les cas, pays
voisins de assets/geo/monde-<lang>.json), meme projection que
site/geo/zones-overview.json. Etapes, trajets et textes :
data/parcours-kenya.json. Les reperes de l'accueil (Bunia, Isiro...) ne sont
pas repris : la carte nomme ses propres lieux."""
import json, math, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COUL = {"rdc": "#5B2A1F", "uga": "#A06F30", "ken": "#993A2E"}
AVION = ('<path d="M0 -6 L1.3 -1.6 L6 1 L6 2.4 L1.3 1 L1 4.4 L2.6 5.6 L2.6 6.6 L0 5.8 L-2.6 6.6 L-2.6 5.6 L-1 4.4 '
         'L-1.3 1 L-6 2.4 L-6 1 L-1.3 -1.6 Z"/>')
VOITURE = ('<path d="M-5.6 1.2 L-4.6 -2 Q-4.3 -3 -3.2 -3 L3.2 -3 Q4.3 -3 4.6 -2 L5.6 1.2 L5.6 3.4 L4.4 3.4 L4.4 4.6 '
           'L2.8 4.6 L2.8 3.4 L-2.8 3.4 L-2.8 4.6 L-4.4 4.6 L-4.4 3.4 L-5.6 3.4 Z M-3.6 -0.2 L3.6 -0.2 L3 -2 L-3 -2 Z" '
           'fill-rule="evenodd"/><circle cx="-3.4" cy="1.6" r=".9" fill="#fff"/><circle cx="3.4" cy="1.6" r=".9" fill="#fff"/>')
# Etiquettes : decalage (dx, dy) et ancrage, pour ne pas chevaucher les traits.
DECAL = {"Aketi": (-11, 4, "end"), "Likati": (-11, 4, "end"), "Bondo": (-11, 4, "end"), "Malalise": (11, -2, "start"),
         "Kasindi": (-11, 14, "end"), "Entebbe": (-2, 22, "middle"), "Kampala": (10, -8, "start"), "Beni": (-11, -6, "end"),
         "Kisangani": (-11, 16, "end")}
NOMS_PAYS = [("rdc", 21.6, 1.6), ("uga", 31.6, 2.6), ("ken", 36.9, 1.6)]
CADRE = (21.0, 5.0, 38.6, -2.6)   # ouest, nord, est, sud


def _lire(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return json.load(f)


def _esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def zones_au(date):
    """Les zones de sante telles qu'au jour date (data/zones-history.json)."""
    return next(j["zones"] for j in _lire("data", "zones-history.json") if j["date"] == date)


def carte_html(lang, dessiner_zones):
    """La section « De Buta a Nairobi ». dessiner_zones(zones) rend la carte
    de l'accueil pour ces zones ; on en reprend le trace colorie."""
    d = _lire("data", "parcours-kenya.json")
    t = d["textes"][lang]
    pj = _lire("site", "geo", "zones-overview.json")["projection"]
    P = lambda lon, lat: ((lon - pj["minLon"]) * pj["scale"], (pj["maxLat"] - lat) * pj["scale"])
    fige = os.path.join(ROOT, "site", "geo", "parcours-kenya-%s.svg" % lang)
    if os.path.exists(fige):
        # Carte figee (20 octobre 2026) : une fois ecrit, le trace d'une langue
        # ne change plus, quelles que soient les donnees des SitRep suivants.
        with open(fige, encoding="utf-8") as f:
            return _section(t, f.read())
    cartogram = dessiner_zones(zones_au(d["fond"]["date"]))
    monde = _lire("assets", "geo", "monde-%s.json" % lang)["monde"]
    # Un pays sans cas a cette date (le Kenya le 3 octobre) : ses comtes en gris.
    for a3 in d["fond"].get("paysSansCas", []):
        m = re.search(r'<g class="hr-pays[^"]*" data-a3="%s">' % a3, monde)
        if m:
            fin = monde.find('<g class="hr-pays', m.end())
            fin = len(monde) if fin < 0 else fin
            monde = monde[:m.end()] + re.sub(r'hr-adm is-\d', "hr-adm is-0", monde[m.end():fin]) + monde[fin:]
    quiet = re.search(r'<g class="zm-quiet">.*?</g>', cartogram, re.S).group(0)
    active = re.sub(r'<g class="zm-marks">.*$', "", re.search(r'<g class="zm-active">.*?</g>\s*</g>|<g class="zm-active">.*?</g>',
                                                              cartogram, re.S).group(0), flags=re.S)
    lieux = {k: P(*v) for k, v in d["lieux"].items()}
    out = []
    for cle, lon, lat in NOMS_PAYS:
        x, y = P(lon, lat)
        out.append('<text class="pk-pays" x="%.1f" y="%.1f">%s</text>' % (x, y, _esc(t["noms"][cle])))
    for a, b, mode in d["trajets"]:
        (x1, y1), (x2, y2) = lieux[a], lieux[b]
        out.append('<line class="pk-%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (mode, x1, y1, x2, y2))
        if mode in ("avion", "route") and math.hypot(x2 - x1, y2 - y1) > 60:
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) + 90 if mode == "avion" else 0
            out.append('<g class="pk-glyphe is-%s" transform="translate(%.1f %.1f) rotate(%.0f)"><circle r="9"/>%s</g>'
                       % (mode, (x1 + x2) / 2, (y1 + y2) / 2, ang, AVION if mode == "avion" else VOITURE))
    for n, lieu, pays in d["etapes"]:
        x, y = lieux[lieu]
        dx, dy, anc = DECAL.get(lieu, (11, 4, "start"))
        out.append('<g class="pk-pt" transform="translate(%.1f %.1f)"><circle r="8" fill="%s"/><text y="3.6">%d</text></g>'
                   '<text class="pk-lieu" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                   % (x, y, COUL[pays], n, x + dx, y + dy, anc, _esc(lieu)))
    (x1, y1), (x2, y2) = P(CADRE[0], CADRE[1]), P(CADRE[2], CADRE[3])
    # Carte statique (20 octobre 2026) : ni liens vers les provinces, ni
    # infobulles, ni la classe « zonemap » que app.js rend interactive.
    zones = re.sub(r"<title>.*?</title>", "", quiet + active, flags=re.S)
    zones = re.sub(r'<a class="(zm-zone[^"]*)"[^>]*>', r'<g class="\1">', zones).replace("</a>", "</g>")
    svg = ('<svg class="pk-carte is-monde" viewBox="%.1f %.1f %.1f %.1f" role="img" aria-label="%s" '
           'preserveAspectRatio="xMidYMid meet"><g class="zm-viewport">%s%s</g>%s</svg>'
           % (x1, y1, x2 - x1, y2 - y1, _esc(t["titre"] + " : " + ", ".join(e[1] for e in d["etapes"])),
              monde, zones, "".join(out)))
    with open(fige, "w", encoding="utf-8") as f:
        f.write(svg)
    return _section(t, svg)


def _section(t, svg):
    modes = "".join('<span><i class="l-%s"></i>%s</span>' % (m, _esc(t["modes"][m])) for m in ("avion", "route", "inconnu"))
    pays = "".join('<span><b style="background:%s"></b>%s</span>' % (COUL[c], _esc(t["pays"][c])) for c in ("rdc", "uga", "ken"))
    cas = "".join('<span><em class="pk-sw" style="background:var(--map-%d)"></em>%s</span>' % (i, _esc(p))
                  for i, p in enumerate(t["paliers"], 1))
    return ('  <section class="section pp-parcours" id="parcours">\n'
            '    <h2 class="pp-t">%s</h2><p class="pp-st">%s</p>\n'
            '    <div class="pk-cadre">%s</div>\n'
            '    <div class="pk-leg">%s%s</div>\n'
            '    <div class="pk-leg pk-leg-cas"><strong>%s</strong>%s</div>\n'
            '    <p class="pk-source">%s</p>\n'
            '  </section>'
            % (_esc(t["titre"]), _esc(t["chapo"]), svg, modes, pays, _esc(t["cas"]), cas, _esc(t["source"])))


def nav_libelle(lang):
    return _lire("data", "parcours-kenya.json")["textes"][lang]["nav"]
