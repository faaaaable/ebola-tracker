# -*- coding: utf-8 -*-
"""La vue « Pays touches » de la carte de l'accueil (8 octobre 2026, en local).

Un bouton de la carte recule jusqu'aux pays touches hors de RDC : l'Ouganda et
le Kenya. (La France, 1 cas importe, a ete retiree le 8 octobre 2026.) Ces chiffres ne viennent pas des
bulletins de l'INSP mais de sources ouvertes (OMS, ministeres), citees dans
l'infobulle : data/hors-rdc.json.

L'Ouganda et le Kenya sont dessines COMME LA RDC (choix du proprietaire, 8
octobre 2026) : leurs districts et comtes en creme, ceux qui ont eu des cas
dans le bleu de la legende, aux memes paliers que les zones de sante. Par-dessus,
la proposition retenue parmi six : un point sur la ville du cas et le nom du
pays en couleur, avec sa ligne de chiffres. Fond : site/geo/hors-rdc-admin.json
(scripts/build_geo_hors_rdc.py) et, pour les pays non touches autour,
site/geo/region-monde.json (Natural Earth).

Tout est dessine dans le repere de la carte du pays (plate-carree de
site/geo/zones-overview.json).
"""
from __future__ import annotations

import hashlib
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MOIS = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
    "sw": ["Januari", "Februari", "Machi", "Aprili", "Mei", "Juni", "Julai", "Agosti",
           "Septemba", "Oktoba", "Novemba", "Desemba"],
}
TEXTES = {
    "fr": dict(premier="Premier cas", dernier="Dernier cas", seul="Seul cas", cas="cas confirmé",
               cas_pl="cas confirmés", deces="décès", deces_pl="décès", cours="Épidémie en cours",
               fini="Épidémie terminée", source="Source", court_cas="cas", court_cours="en cours",
               court_fini="terminée", court_gueri="guéri"),
    "en": dict(premier="First case", dernier="Last case", seul="Single case", cas="confirmed case",
               cas_pl="confirmed cases", deces="death", deces_pl="deaths", cours="Ongoing outbreak",
               fini="Outbreak over", source="Source", court_cas="cases", court_cours="ongoing",
               court_fini="over", court_gueri="recovered"),
    "sw": dict(premier="Mgonjwa wa kwanza", dernier="Mgonjwa wa mwisho", seul="Mgonjwa pekee",
               cas="mgonjwa aliyethibitishwa", cas_pl="wagonjwa waliothibitishwa", deces="kifo",
               deces_pl="vifo", cours="Mlipuko unaendelea", fini="Mlipuko umemalizika",
               source="Chanzo", court_cas="wagonjwa", court_cours="unaendelea",
               court_fini="umemalizika", court_gueri="amepona"),
}
# Pas de fond Natural Earth pour la RDC (ses zones), la France (hors cadre),
# les pays touches (leur decoupage administratif) ni les petites iles du fichier.
HORS_FOND = {"COD", "FRA", "NZL", "KIR", "FJI", "NLD"}


def _lire(*p):
    with io.open(os.path.join(ROOT, *p), encoding="utf-8") as fh:
        return json.load(fh)


def _date(iso, lang):
    a, m, j = iso.split("-")
    return "%d %s %s" % (int(j), MOIS[lang][int(m) - 1], a)


def date_longue(iso, lang):
    """« 8 octobre 2026 », « 8 October 2026 », « 8 Oktoba 2026 »."""
    return _date(iso, lang)


def _esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


class _Proj:
    def __init__(self, min_lon, max_lat, scale):
        self.min_lon, self.max_lat, self.scale = min_lon, max_lat, scale

    def xy(self, lon, lat):
        return (lon - self.min_lon) * self.scale, (self.max_lat - lat) * self.scale

    def anneaux(self, rings):
        return "".join("M" + "L".join("%.1f %.1f" % self.xy(x, y) for x, y in r) + "Z" for r in rings)

    def path(self, geom):
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        return self.anneaux([ring for poly in polys for ring in poly])


def _palier(cas, seuils):
    """Meme palier que les zones de sante : 0 sans cas, puis 1 a len(seuils)+1."""
    return 0 if not cas else 1 + sum(1 for s in seuils if cas >= s)


def _court(p, lang):
    """« 20 cas, 2 décès » et « terminée » : les deux lignes sous le nom du
    pays. Sur une seule ligne, celle de l'Ouganda etait plus large que le pays."""
    t = TEXTES[lang]
    etat = t["court_cours"] if p["etat"] == "cours" else (
        t["court_gueri"] if p["cas"] == 1 and p["deces"] == 0 else t["court_fini"])
    n = "%d %s" % (p["cas"], t["court_cas"])
    if p["deces"]:
        n += ", %d %s" % (p["deces"], t["deces"] if p["deces"] == 1 else t["deces_pl"])
    return n, etat


def _bulle(p, lang):
    t = TEXTES[lang]
    if p["dernier"]:
        dates = ('<div class="hb-l"><span>%s</span><b>%s</b></div>'
                 '<div class="hb-l"><span>%s</span><b>%s</b></div>') % (
            t["premier"], _date(p["premier"], lang), t["dernier"], _date(p["dernier"], lang))
    else:
        dates = '<div class="hb-l"><span>%s</span><b>%s</b></div>' % (t["seul"], _date(p["premier"], lang))
    return ('<div class="hb-t"><i class="hb-pt is-%s"></i><b>%s</b><em>%s</em></div>%s'
            '<div class="hb-n"><div><b>%d</b><span>%s</span></div><div><b>%d</b><span>%s</span></div></div>'
            '<p>%s</p><p class="hb-s">%s : %s</p>') % (
        p["etat"], _esc(p["nom"][lang]), t["cours"] if p["etat"] == "cours" else t["fini"], dates,
        p["cas"], t["cas"] if p["cas"] == 1 else t["cas_pl"],
        p["deces"], t["deces"] if p["deces"] == 1 else t["deces_pl"],
        _esc(p["note"][lang]), t["source"], _esc(p["source"][lang]))


def greffer(svg_html, geo, lang, seuils):
    """Ajoute a la carte de l'accueil le fond des pays voisins (.zm-monde, sous
    les zones) et les pays touches (.zm-hors, au-dessus). Les deux restent
    caches hors de la vue « Pays touches »."""
    pj = geo["projection"]
    pr = _Proj(pj["minLon"], pj["maxLat"], pj["scale"])
    region = _lire("site", "geo", "region-monde.json")["pays"]
    admin = _lire("site", "geo", "hors-rdc-admin.json")
    hors = _lire("data", "hors-rdc.json")["pays"]
    touches = {p["a3"] for p in hors}

    fond = "".join('<path d="%s"/>' % pr.path(c["geometry"])
                   for c in region if c["a3"] not in HORS_FOND and c["a3"] not in touches)
    monde = '          <g class="zm-monde" aria-hidden="true">%s</g>\n' % fond

    pays, villes, noms = [], [], []
    for p in hors:
        a3 = p["a3"]
        if a3 not in admin:
            continue
        # Une unite touchee porte les cas de son groupe : en Ouganda, Kampala et
        # Wakiso partagent 20 cas dont la repartition n'est pas publiee.
        cas_de = {}
        for g in p.get("unites", []):
            for nom in g["noms"]:
                cas_de[nom] = g["cas"]
        chemins = "".join('<path class="hr-adm is-%d" d="%s"/>'
                          % (_palier(cas_de.get(u["nom"], 0), seuils), pr.anneaux(u["anneaux"]))
                          for u in admin[a3])
        # Un fin trait sur la frontiere exterieure, par-dessus les districts
        # (demande du 8 octobre 2026) : le pays se detache du fond voisin.
        bord = '<path class="hr-bord" d="%s"/>' % pr.anneaux(admin["contours"][a3])
        pays.append('<g class="hr-pays is-%s" data-a3="%s">%s%s</g>' % (p["etat"], a3, chemins, bord))
        n, etat = _court(p, lang)
        x, y = pr.xy(p["lon"], p["lat"])
        if p.get("point", True):
            villes.append(
                '<g class="zm-mark hr-ville is-%s" data-a3="%s" data-x="%.1f" data-y="%.1f" transform="translate(%.1f %.1f)">'
                '<circle class="hr-halo" r="9"/><circle class="hr-pt" r="4.4"/></g>'
                % (p["etat"], a3, x, y, x, y))
        lx, ly = pr.xy(*p["label"])
        noms.append(
            '<g class="zm-mark hr-nom is-%s" data-a3="%s" data-x="%.1f" data-y="%.1f" transform="translate(%.1f %.1f)">'
            '<text class="hr-n1" y="0">%s</text><text class="hr-n2" y="15">%s</text>'
            '<text class="hr-n2" y="29">%s</text></g>'
            % (p["etat"], a3, lx, ly, lx, ly, _esc(p["nom"][lang]).upper(), n, etat))

    couche = ('          <g class="zm-hors"><g class="hr-g-noms">%s</g><g class="hr-g-villes">%s</g></g>\n'
              % ("".join(noms), "".join(villes)))
    # Les pays touches se posent avec le fond, sous les zones de la RDC : leurs
    # frontieres communes ne se chevauchent pas, et le maillage reste d'un seul
    # tenant. Les reperes, eux, passent au-dessus de tout.
    monde += '          <g class="zm-monde zm-monde-touches">%s</g>\n' % "".join(pays)

    # Ces deux couches pesent ~150 Ko : ecrites dans la page, elles la
    # faisaient s'afficher a moitie lue (carte grise, puis la vraie : un
    # clignotement mesure le 8 octobre 2026). Elles vont dans un fichier a
    # part, que app.js ne charge qu'a la demande (setupMonde).
    contenu = json.dumps({"monde": monde, "hors": couche}, ensure_ascii=False)
    empreinte = hashlib.sha256(contenu.encode("utf-8")).hexdigest()[:10]
    nom = "monde-%s.json" % lang
    os.makedirs(os.path.join(ROOT, "assets", "geo"), exist_ok=True)
    with io.open(os.path.join(ROOT, "assets", "geo", nom), "w", encoding="utf-8") as fh:
        fh.write(contenu)
    # Cadre resserre sur l'est (8 octobre 2026, demande du proprietaire :
    # « stopper le focus de la RDC ») : de l'Ituri a la cote kenyane, avec de
    # l'ocean a droite pour que le Kenya ne passe pas sous le panneau des
    # chiffres, pose en haut a droite de la carte.
    x0, y0 = pr.xy(26.0, 6.0)
    x1, y1 = pr.xy(46.5, -5.5)
    # Sur telephone (carte de ~310 px), le cadre complet rendait l'Ouganda et
    # le Kenya minuscules : on cadre sur l'est, de l'Ituri a la cote kenyane.
    # Resserre encore le 8 octobre 2026 (demande du proprietaire, comme sur
    # ordinateur) : l'Ouganda et le Kenya seuls, avec la frange est de l'Ituri.
    m0, n0 = pr.xy(28.8, 5.0)
    m1, n1 = pr.xy(42.3, -5.0)
    return svg_html.replace('<svg class="zonemap"',
                            '<svg class="zonemap" data-monde-box="%.1f %.1f %.1f %.1f" data-monde-box-tel="%.1f %.1f %.1f %.1f" data-monde-src="/assets/geo/%s?v=%s"'
                            % (x0, y0, x1 - x0, y1 - y0, m0, n0, m1 - m0, n1 - n0, nom, empreinte), 1)


def encart_html(lang):
    """L'infobulle des pays touches et ses textes, poses dans le cadre de la
    carte. (L'encart de la France a ete retire le 8 octobre 2026.)"""
    hors = _lire("data", "hors-rdc.json")["pays"]
    bulles = {p["a3"]: _bulle(p, lang) for p in hors}
    return ('<div class="hr-bulle" role="tooltip" aria-live="polite"></div>\n'
            '<script type="application/json" id="horsRdcBulles">%s</script>\n'
            % json.dumps(bulles, ensure_ascii=False).replace("</", "<\\/"))


A3_PAGE = {"ouganda": "UGA", "kenya": "KEN", "france": "FRA"}


def _silhouette(pid, w=64):
    """La silhouette d'un pays, pour l'en-tete de sa fiche : contour OCHA pour
    l'Ouganda et le Kenya (le meme que la carte), Natural Earth pour la France."""
    a3 = A3_PAGE[pid]
    admin = _lire("site", "geo", "hors-rdc-admin.json")
    if a3 in admin.get("contours", {}):
        rings = admin["contours"][a3]
    else:
        g = next(c["geometry"] for c in _lire("site", "geo", "region-monde.json")["pays"] if c["a3"] == a3)
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings = [r for poly in polys for r in poly if len(r) > 30]
    xs = [x for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    k = w / (x1 - x0)
    d = "".join("M" + "L".join("%.1f %.1f" % ((x - x0) * k, (y1 - y) * k) for x, y in r) + "Z" for r in rings)
    return ('<svg class="ap-sil" viewBox="-2 -2 %.0f %.0f" aria-hidden="true"><path d="%s"/></svg>'
            % (w + 4, (y1 - y0) * k + 4, d))


def _fiche_html(p, lang, libelles, lien=""):
    """Une fiche pays : la date du premier cas en grand, la silhouette, le nom,
    l'etat, les chiffres, tout le resume et les sources. lien : HTML ajoute
    apres le resume (sur « Autres pays », le renvoi vers la page du pays)."""
    a, m, j = p["premier"].split("-")
    jour_mois = "%d %s" % (int(j), MOIS[lang][int(m) - 1])
    chiffres = "".join(
        '<div class="ap-c"><b>%s</b><span>%s</span></div>'
        % (_esc(c.get({"en": "nEn", "sw": "nSw"}.get(lang, "n"), c["n"])), _esc(c["l"][lang]))
        for c in p["chiffres"])
    texte = "".join("<p>%s</p>" % _esc(t) for t in p["texte"][lang])
    sources = "".join(
        '<li><a href="%s"%s>%s</a></li>'
        % (_esc(s["url"]), ' target="_blank" rel="noopener"' if s["url"].startswith("http") else "",
           _esc(s["l"][lang]))
        for s in p["sources"])
    return (
        '      <article class="ap-pays is-%s" id="%s">\n'
        '        <div class="ap-date"><span class="ap-pt"></span><small>%s</small>'
        '<time datetime="%s"><b>%s</b> %s</time></div>\n'
        '        <header>%s<h2>%s</h2><p class="ap-statut"><i></i>%s</p></header>\n'
        '        <div class="ap-chiffres">%s</div>\n'
        '        <div class="ap-texte">%s%s</div>\n'
        '        <div class="ap-sources"><span>%s</span><ul>%s</ul></div>\n'
        '      </article>'
        % (p["etat"], p["id"], _esc(libelles["premier"]), p["premier"], _esc(jour_mois), a,
           _silhouette(p["id"]), _esc(p["nom"][lang]), _esc(p["statut"][lang]),
           chiffres, texte, lien, _esc(libelles["sources"]), sources))


def page_html(lang, libelles, liens=None):
    """La page « Autres pays » (8 octobre 2026, option 1 des maquettes) : une
    fiche par pays touche hors de RDC, cote a cote, DANS L'ORDRE DU PREMIER CAS.
    La date du premier cas, posee sur un filet commun, se lit comme une frise.
    liens : {id du pays: url de sa page} (Kenya et Ouganda, 9 octobre 2026),
    pour renvoyer chaque fiche vers sa page. Contenu : data/autres-pays.json."""
    doc = _lire("data", "autres-pays.json")
    liens = liens or {}
    return "\n".join(
        _fiche_html(p, lang, libelles,
                    '<p class="ap-lien"><a class="teaser-more" href="%s">%s</a></p>'
                    % (_esc(liens[p["id"]]), _esc(p["pageLien"][lang])) if p["id"] in liens else "")
        for p in doc["pays"])


def _pays(pid):
    return next(p for p in _lire("data", "autres-pays.json")["pays"] if p["id"] == pid)


def pays_html(pid, lang, libelles):
    """La fiche seule, pour la page du pays (Kenya, Ouganda : 9 octobre 2026)."""
    return _fiche_html(_pays(pid), lang, libelles)


def questions_plain(pid, lang):
    """Les questions de la page du pays, en texte brut, pour le FAQPage."""
    return [{"q": x["q"][lang], "a": x["a"][lang]} for x in _pays(pid).get("questions", [])]


def questions_html(pid, lang):
    """Les memes questions en rubriques depliables, comme la FAQ du site."""
    return "\n".join(
        '      <details class="faq-item">\n        <summary>%s</summary>\n'
        '        <div class="faq-answer"><p>%s</p></div>\n      </details>'
        % (_esc(x["q"]), _esc(x["a"])) for x in questions_plain(pid, lang))
