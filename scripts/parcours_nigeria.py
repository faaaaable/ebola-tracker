# -*- coding: utf-8 -*-
"""Carte du parcours du premier cas du Nigeria, d'Abuja a Abuja (page
Nigeria, 29 octobre 2026 ; maquette tmp/proto-parcours-nigeria-1029). En
francais seulement pour l'instant : les pages anglaise et swahilie n'ont pas
cette partie.

Fond : la carte de l'accueil au 3 octobre 2026, jour de son retour (zones de
sante de la RDC coloriees selon les cas confirmes de ce jour, reconstitues
depuis le SitRep 143, le 142 n'ayant pas ete publie ; scripts/jours_calcules.py).
Kenya et Nigeria en gris, sans cas a cette date ; l'Ouganda garde ses cas de
mai a aout, epidemie close le 27 aout. Meme projection et meme cadre de
legende que la carte du Kenya (scripts/parcours.py).

Sources des etapes :
- depart d'Abuja le 16 septembre : representant de l'OMS au Nigeria, Pavel
  Ursu (Reuters, 22 octobre 2026) ;
- retour le 3 octobre, d'Ouganda par Entebbe et Addis-Abeba jusqu'a Abuja ;
  symptomes le 7 ; etablissements prives le 10 et le 11 ; NCDC prevenu le 19,
  confirmation le 20 : rapport de situation du NCDC du 24 octobre 2026 ;
- genome apparente a un cas du Kenya (23 octobre) ; evacuation le 26 octobre :
  ministere federal de la Sante ; Hopitaux universitaires de Geneve :
  autorites suisses (AP).
Le trajet aller n'est pas connu : un pointille courbe par le nord, pour ne pas
passer au-dessus de la RDC (passage affirme par l'Ouganda, dementi par la
Suisse, l'Africa CDC et l'OMS). Le mari et le premier malade du Kenya ne sont
pas mentionnes (demande du proprietaire, 29 octobre 2026)."""
import json, math, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATE_FOND = "2026-10-03"
L = {"Entebbe": (32.46, 0.05), "Addis-Abeba": (38.75, 9.0), "Abuja": (7.49, 9.06), "Ouganda": (32.4, 1.7)}
COUL = {"uga": "#A06F30", "eth": "#6E6355", "nga": "#993A2E"}
CADRE = (1.5, 15.5, 42.5, -4.5)   # ouest, nord, est, sud
ALLER_CTRL = ((16.0, 9.6), (31.6, 9.0))
PALIERS = ["1–9", "10–49", "50–199", "200–499", "500–999", "1 000 et plus"]
FRISE = [
    ("16 sept.", "Départ d’Abuja vers l’Ouganda", "Elle reste en Ouganda jusqu’au 3 octobre ; les lieux visités ne sont pas connus."),
    ("3 oct.", "Entebbe → Addis-Abeba → Abuja", "Elle quitte l’Ouganda par l’aéroport d’Entebbe, vol international par Addis-Abeba jusqu’à Abuja."),
    ("7 oct.", "Premiers symptômes", "Fièvre, diarrhée, douleurs dans tout le corps, mal de gorge, sans saignement."),
    ("10 oct.", "Premier établissement privé", "Elle consulte dans un établissement privé d’Abuja."),
    ("11 oct.", "Admise", "Admise dans un second établissement privé du Territoire de la capitale fédérale."),
    ("19 oct.", "Le NCDC est prévenu", "Enquête et prélèvement."),
    ("20 oct.", "Ebola confirmé", "Par le laboratoire national de référence du NCDC."),
    ("23 oct.", "Virus apparenté au Kenya", "Le génome est apparenté à celui d’un cas du Kenya ; une transmission directe n’est pas établie."),
    ("26 oct.", "Évacuée vers Genève", "Son état s’étant nettement amélioré, elle est soignée aux Hôpitaux universitaires de Genève."),
]


def _lire(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return json.load(f)


def _esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _courbe(a, b, h):
    """Un vol en arc leger : chemin, milieu de l'arc."""
    (x1, y1), (x2, y2) = a, b
    cx, cy = (x1 + x2) / 2 + (y2 - y1) * h, (y1 + y2) / 2 - (x2 - x1) * h
    return ("M%.1f %.1f Q%.1f %.1f %.1f %.1f" % (x1, y1, cx, cy, x2, y2),
            (0.25 * x1 + 0.5 * cx + 0.25 * x2, 0.25 * y1 + 0.5 * cy + 0.25 * y2))


def _svg(dessiner_zones):
    pj = _lire("site", "geo", "zones-overview.json")["projection"]
    P = lambda lon, lat: ((lon - pj["minLon"]) * pj["scale"], (pj["maxLat"] - lat) * pj["scale"])
    (x1, y1), (x2, y2) = P(CADRE[0], CADRE[1]), P(CADRE[2], CADRE[3])
    # Surcouche dans un repere de 1 100 unites de large, comme a l'ecran :
    # lieux, pastilles et notes gardent leur taille de texte.
    k = (x2 - x1) / 1100
    Q = lambda lon, lat: ((P(lon, lat)[0] - x1) / k, (P(lon, lat)[1] - y1) / k)
    from parcours import zones_au
    cartogram = dessiner_zones(zones_au(DATE_FOND))
    monde = _lire("assets", "geo", "monde-fr.json")["monde"]
    for a3 in ("KEN", "NGA"):
        m = re.search(r'<g class="hr-pays[^"]*" data-a3="%s">' % a3, monde)
        if m:
            fin = monde.find('<g class="hr-pays', m.end())
            fin = len(monde) if fin < 0 else fin
            monde = monde[:m.end()] + re.sub(r"hr-adm is-\d", "hr-adm is-0", monde[m.end():fin]) + monde[fin:]
    quiet = re.search(r'<g class="zm-quiet">.*?</g>', cartogram, re.S).group(0)
    active = re.sub(r'<g class="zm-marks">.*$', "", re.search(r'<g class="zm-active">.*?</g>\s*</g>|<g class="zm-active">.*?</g>',
                                                              cartogram, re.S).group(0), flags=re.S)
    out = []
    for nom, lon, lat in (("RDC", 21.5, -1.8), ("OUGANDA", 32.0, 2.9), ("KENYA", 37.6, 1.6), ("ÉTHIOPIE", 40.0, 6.3),
                          ("NIGERIA", 10.6, 11.4)):
        x, y = Q(lon, lat)
        out.append('<text class="pk-pays" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (x, y, nom))
    E, A, B, U = Q(*L["Entebbe"]), Q(*L["Addis-Abeba"]), Q(*L["Abuja"]), Q(*L["Ouganda"])
    # 1. L'aller du 16 septembre, trajet non connu : courbe par le nord,
    # points de controle au-dessus de la Centrafrique et du Soudan du Sud.
    C1, C2 = Q(*ALLER_CTRL[0]), Q(*ALLER_CTRL[1])
    out.append('<path class="pn-aller" d="M%.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f"/>'
               % (B[0] + 6, B[1] - 3, C1[0], C1[1], C2[0], C2[1], U[0], U[1]))
    ang = math.degrees(math.atan2(U[1] - C2[1], U[0] - C2[0]))
    out.append('<path class="pn-aller-pointe" transform="translate(%.1f %.1f) rotate(%.0f)" d="M0 0 L-11 -5 L-11 5 Z"/>' % (U[0], U[1], ang))
    mx, my = (B[0] + 3 * C1[0] + 3 * C2[0] + U[0]) / 8, (B[1] + 3 * C1[1] + 3 * C2[1] + U[1]) / 8
    num = [(mx, my, "#B0685D", 1)]
    out.append('<text class="pn-note pn-date" x="%.1f" y="%.1f" text-anchor="middle">16 septembre</text>' % (mx, my + 28))
    # 2 et 3. Les deux vols du retour, le 3 octobre
    for n, (a, b, h) in ((2, (E, A, -0.16)), (3, (A, B, -0.19))):
        d, (gx, gy) = _courbe(a, b, h)
        out.append('<path class="pk-avion" d="%s"/>' % d)
        num.append((gx, gy, "#1B6C8C", n))
        dx, dy, anc = (16, 5, "start") if n == 2 else (0, -17, "middle")
        out.append('<text class="pn-note pn-date" x="%.1f" y="%.1f" text-anchor="%s">3 octobre</text>' % (gx + dx, gy + dy, anc))
    # 4. Vers Geneve : une fleche qui sort par le haut (Geneve est hors cadre)
    x, y = B
    top = 8
    out.append('<path class="pn-suisse" d="M%.1f %.1f L%.1f %.1f"/>' % (x - 6, y - 12, x - 40, top + 14))
    out.append('<path class="pn-fleche" d="M%.1f %.1f l-4 10 l9 -3 z"/>' % (x - 41, top + 9))
    num.append(((x - 6 + x - 40) / 2, (y - 12 + top + 14) / 2, "#993A2E", 4))
    out.append('<text class="pn-note" x="%.1f" y="%.1f"><tspan x="%.1f" font-weight="700">26 octobre : vers Genève</tspan>'
               '<tspan x="%.1f" dy="15">évacuée vers les Hôpitaux universitaires</tspan></text>'
               % (x - 30, top + 16, x - 30, x - 30))
    # Les lieux : de simples points ; les numeros sont portes par les trajets.
    for lieu, pays, (dx, dy, anc) in (("Entebbe", "uga", (0, 22, "middle")), ("Addis-Abeba", "eth", (10, -8, "start")),
                                      ("Abuja", "nga", (-12, 20, "end"))):
        px, py = Q(*L[lieu])
        out.append('<circle class="pn-lieu" cx="%.1f" cy="%.1f" r="5.5" fill="%s"/>'
                   '<text class="pk-lieu" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                   % (px, py, COUL[pays], px + dx, py + dy, anc, lieu))
    out.append('<text class="pn-note" x="%.1f" y="%.1f" text-anchor="end"><tspan x="%.1f">départ le 16 sept.,</tspan>'
               '<tspan x="%.1f" dy="15">retour le 3 oct.</tspan></text>' % (B[0] - 12, B[1] + 36, B[0] - 12, B[0] - 12))
    for px, py, c, n in num:
        out.append('<g class="pk-pt pn-num" transform="translate(%.1f %.1f)"><circle r="9" fill="%s"/><text y="3.8">%d</text></g>'
                   % (px, py, c, n))
    # Carte statique, comme celle du Kenya : ni liens, ni infobulles.
    zones = re.sub(r"<title>.*?</title>", "", quiet + active, flags=re.S)
    zones = re.sub(r'<a class="(zm-zone[^"]*)"[^>]*>', r'<g class="\1">', zones).replace("</a>", "</g>")
    return ('<svg class="pk-carte is-monde" viewBox="%.1f %.1f %.1f %.1f" role="img" aria-label="%s" '
            'preserveAspectRatio="xMidYMid meet"><g class="zm-viewport">%s%s</g>'
            '<g transform="translate(%.1f %.1f) scale(%.4f)">%s</g></svg>'
            % (x1, y1, x2 - x1, y2 - y1, "Le trajet du premier cas : Abuja, l’Ouganda, Entebbe, Addis-Abeba, Abuja, puis Genève",
               monde, zones, x1, y1, k, "".join(out)))


def carte_html(lang, dessiner_zones):
    """La section « D'Abuja a Abuja » ; vide hors du francais."""
    if lang != "fr":
        return ""
    fige = os.path.join(ROOT, "site", "geo", "parcours-nigeria-fr.svg")
    if os.path.exists(fige):
        # Carte figee : le trace ne change plus avec les SitRep suivants.
        # Supprimer le fichier pour le refaire.
        with open(fige, encoding="utf-8") as f:
            svg = f.read()
    else:
        svg = _svg(dessiner_zones)
        with open(fige, "w", encoding="utf-8") as f:
            f.write(svg)
    frise = "".join('<li><time>%s</time><b>%s</b><span>%s</span></li>' % (_esc(d), _esc(t), _esc(x)) for d, t, x in FRISE)
    leg = ('<span><i class="l-avion"></i>avion</span>'
           '<span><i class="l-aller"></i>aller, trajet non connu</span>'
           '<span><i class="l-evac"></i>évacuation vers la Suisse</span>'
           '<span><b style="background:%s"></b>Ouganda</span><span><b style="background:%s"></b>Éthiopie (escale)</span>'
           '<span><b style="background:%s"></b>Nigeria</span>' % (COUL["uga"], COUL["eth"], COUL["nga"]))
    cas = "".join('<span><em class="pk-sw" style="background:var(--map-%d)"></em>%s</span>' % (i, p) for i, p in enumerate(PALIERS, 1))
    return ('  <section class="section pp-parcours" id="parcours">\n'
            '    <h2 class="pp-t">D’Abuja à Abuja, le trajet du premier cas</h2>'
            '<p class="pp-st">Partie d’Abuja le 16 septembre, elle rentre le 3 octobre par Entebbe et Addis-Abeba.</p>\n'
            '    <div class="pk-cadre">%s</div>\n'
            '    <div class="pk-leg">%s</div>\n'
            '    <div class="pk-leg pk-leg-cas"><strong>Cas confirmés au 3 octobre 2026</strong>%s</div>\n'
            '    <ol class="pn-frise">%s</ol>\n'
            '    <p class="pk-source">Départ d’Abuja le 16 septembre : représentant de l’OMS au Nigeria (Reuters, 22 octobre 2026). '
            'Retour : rapport de situation du NCDC du 24 octobre 2026 (Ouganda, Addis-Abeba, Abuja le 3 octobre). '
            'Évacuation : ministère fédéral de la Santé, 26 octobre 2026 ; Genève : autorités suisses (AP). Les établissements d’Abuja ne sont pas nommés. '
            'Zones de santé de la RDC coloriées selon les cas confirmés au 3 octobre 2026 ; '
            'aucun cas n’était encore confirmé au Kenya ni au Nigeria ; en Ouganda, l’épidémie de mai à août était close depuis le 27 août. '
            'L’Ouganda affirme qu’elle était passée par l’est de la RDC ; la Suisse le dément, le directeur de l’Africa CDC dit que ses documents de voyage n’en montrent aucune trace, et l’OMS n’a aucune information sur un voyage hors d’Ouganda.</p>\n'
            '  </section>' % (svg, leg, cas, frise))
