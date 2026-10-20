# -*- coding: utf-8 -*-
"""La vue « Pays touches » de la carte de l'accueil (8 octobre 2026, en local).

Un bouton de la carte recule jusqu'aux pays touches hors de RDC : l'Ouganda,
le Kenya et, depuis le 20 octobre 2026, le Nigeria. (La France, 1 cas importe, a ete retiree le 8 octobre 2026.) Ces chiffres ne viennent pas des
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
               court_fini="terminée", court_gueri="guéri",
               fini_le="terminée le {d}", cours_depuis="en cours depuis le {d}", cas1="cas",
               voir_souris="Cliquez pour ouvrir la page du pays",
               voir_doigt="Touchez à nouveau pour ouvrir la page du pays"),
    "en": dict(premier="First case", dernier="Last case", seul="Single case", cas="confirmed case",
               cas_pl="confirmed cases", deces="death", deces_pl="deaths", cours="Ongoing outbreak",
               fini="Outbreak over", source="Source", court_cas="cases", court_cours="ongoing",
               court_fini="over", court_gueri="recovered",
               fini_le="over since {d}", cours_depuis="ongoing since {d}", cas1="case",
               voir_souris="Click to open the country page",
               voir_doigt="Tap again to open the country page"),
    "sw": dict(premier="Mgonjwa wa kwanza", dernier="Mgonjwa wa mwisho", seul="Mgonjwa pekee",
               cas="mgonjwa aliyethibitishwa", cas_pl="wagonjwa waliothibitishwa", deces="kifo",
               deces_pl="vifo", cours="Mlipuko unaendelea", fini="Mlipuko umemalizika",
               source="Chanzo", court_cas="wagonjwa", court_cours="unaendelea",
               court_fini="umemalizika", court_gueri="amepona",
               fini_le="ulimalizika {d}", cours_depuis="unaendelea tangu {d}", cas1="mgonjwa",
               voir_souris="Bofya kufungua ukurasa wa nchi",
               voir_doigt="Gusa tena kufungua ukurasa wa nchi"),
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


def _jour_mois(iso, lang):
    """« 27 août », « 6 octobre » : la date sans l'annee, sous le nom du pays."""
    _, m, j = iso.split("-")
    return "%d %s" % (int(j), MOIS[lang][int(m) - 1])


# Une seule source pour les chiffres d'un pays (21 octobre 2026) : etat, cas,
# deces, premier cas et fin sont lus dans data/autres-pays.json (la fiche) et
# poses sur l'entree de data/hors-rdc.json (la carte), qui ne garde que ce qui
# est propre a la carte : ville, places des noms, unites coloriees, note,
# date du dernier cas. Avant, les deux fichiers portaient les memes nombres et
# un nouveau cas devait etre ecrit deux fois. check_coherence bloque si un
# champ deplace reapparait dans hors-rdc.json avec une autre valeur.
CHAMPS_FICHE = ("etat", "cas", "deces", "premier", "fin")


def _hors():
    fiches = {A3_PAGE[p["id"]]: p for p in _lire("data", "autres-pays.json")["pays"] if p["id"] in A3_PAGE}
    out = []
    for p in _lire("data", "hors-rdc.json")["pays"]:
        f = fiches[p["a3"]]
        p = dict(p)
        p.update(etat=f["etat"], cas=int(f["chiffres"][0]["n"]), deces=int(f["chiffres"][1]["n"]),
                 premier=f["premier"], fin=f.get("fin"))
        out.append(p)
    return out


def _court(p, lang):
    """« 20 cas, 2 décès » et « terminée le 27 août » : les deux lignes sous le
    nom du pays (option 2 des maquettes du 9 octobre 2026). Les deces sont
    toujours ecrits, meme a zero."""
    t = TEXTES[lang]
    if p["etat"] == "cours":
        etat = t["cours_depuis"].replace("{d}", _jour_mois(p["premier"], lang))
    elif p.get("fin"):
        etat = t["fini_le"].replace("{d}", _jour_mois(p["fin"], lang))
    else:
        etat = t["court_fini"]
    n = "%d %s, %d %s" % (p["cas"], t["cas1"] if p["cas"] == 1 else t["court_cas"],
                          p["deces"], t["deces"] if p["deces"] == 1 else t["deces_pl"])
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
            '<p>%s</p><p class="hb-s"><span class="on-hover">%s</span><span class="on-touch">%s</span></p>') % (
        p["etat"], _esc(p["nom"][lang]), t["cours"] if p["etat"] == "cours" else t["fini"], dates,
        p["cas"], t["cas"] if p["cas"] == 1 else t["cas_pl"],
        p["deces"], t["deces"] if p["deces"] == 1 else t["deces_pl"],
        _esc(p["note"][lang]), _esc(t["voir_souris"]), _esc(t["voir_doigt"]))
    # La derniere ligne dit que le pays mene a sa page (21 octobre 2026) :
    # un clic a la souris, un second toucher au doigt (app.js, setupMonde).
    # Plus de ligne « Source : … » (21 octobre 2026, demande de Fable) : les
    # sources sont sur la page de chaque pays, avec leurs liens ; le champ
    # source de data/hors-rdc.json reste comme trace.


def greffer(svg_html, geo, lang, seuils):
    """Ajoute a la carte de l'accueil le fond des pays voisins (.zm-monde, sous
    les zones) et les pays touches (.zm-hors, au-dessus). Les deux restent
    caches hors de la vue « Pays touches »."""
    pj = geo["projection"]
    pr = _Proj(pj["minLon"], pj["maxLat"], pj["scale"])
    region = _lire("site", "geo", "region-monde.json")["pays"]
    admin = _lire("site", "geo", "hors-rdc-admin.json")
    hors = _hors()
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
        n, _etat = _court(p, lang)
        x, y = pr.xy(p["lon"], p["lat"])
        if p.get("point", True):
            villes.append(
                '<g class="zm-mark hr-ville is-%s" data-a3="%s" data-x="%.1f" data-y="%.1f" transform="translate(%.1f %.1f)">'
                '<circle class="hr-halo" r="9"/><circle class="hr-pt" r="4.4"/></g>'
                % (p["etat"], a3, x, y, x, y))
        lx, ly = pr.xy(*p["label"])
        # Sur telephone le nom a sa propre place (labelTel, 20 octobre 2026) :
        # le cadre y va du Nigeria au Kenya et les noms, de taille fixe, se
        # chevauchaient. app.js la prend a la place de data-x / data-y.
        tx, ty = pr.xy(*p.get("labelTel", p["label"]))
        noms.append(
            '<g class="zm-mark hr-nom is-%s" data-a3="%s" data-x="%.1f" data-y="%.1f" data-x-tel="%.1f" data-y-tel="%.1f" transform="translate(%.1f %.1f)">'
            '<text class="hr-n1" y="0">%s</text><text class="hr-n2" y="19">%s</text></g>'
            % (p["etat"], a3, lx, ly, tx, ty, lx, ly, _esc(p["nom"][lang]), n))
        # Plus de troisieme ligne « en cours depuis le… » / « terminee le… »
        # (21 octobre 2026, demande de Fable : elle encombrait la carte et
        # doublait l'infobulle) ; l'etat passe par la couleur (site.css).

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
    # Elargi a l'ouest le 20 octobre 2026 pour le premier cas du Nigeria
    # (Abuja) : du Nigeria a la cote kenyane, la RDC au milieu.
    x0, y0 = pr.xy(2.5, 14.2)
    x1, y1 = pr.xy(46.5, -5.5)
    # Sur telephone (carte de ~310 px), le cadre complet rendait l'Ouganda et
    # le Kenya minuscules : on cadre sur l'est, de l'Ituri a la cote kenyane.
    # Resserre encore le 8 octobre 2026 (demande du proprietaire, comme sur
    # ordinateur) : l'Ouganda et le Kenya seuls, avec la frange est de l'Ituri.
    # Depuis le 20 octobre 2026 il doit aussi montrer le Nigeria : il part de
    # sa frontiere ouest et coupe l'ocean a droite du Kenya.
    m0, n0 = pr.xy(2.6, 14.0)
    m1, n1 = pr.xy(42.0, -5.0)
    return svg_html.replace('<svg class="zonemap"',
                            '<svg class="zonemap" data-monde-box="%.1f %.1f %.1f %.1f" data-monde-box-tel="%.1f %.1f %.1f %.1f" data-monde-src="/assets/geo/%s?v=%s"'
                            % (x0, y0, x1 - x0, y1 - y0, m0, n0, m1 - m0, n1 - n0, nom, empreinte), 1)


def encart_html(lang, liens=None):
    """L'infobulle des pays touches et ses textes, poses dans le cadre de la
    carte. (L'encart de la France a ete retire le 8 octobre 2026.) liens : la
    page de chaque pays (id de page -> adresse), vers laquelle mene un clic
    sur le pays (21 octobre 2026)."""
    hors = _hors()
    bulles = {p["a3"]: _bulle(p, lang) for p in hors}
    pages = {A3_PAGE[pid]: url for pid, url in (liens or {}).items() if pid in A3_PAGE}
    return ('<div class="hr-bulle" role="tooltip" aria-live="polite"></div>\n'
            '<script type="application/json" id="horsRdcBulles">%s</script>\n'
            '<script type="application/json" id="horsRdcLiens">%s</script>\n'
            % (json.dumps(bulles, ensure_ascii=False).replace("</", "<\\/"),
               json.dumps(pages, ensure_ascii=False).replace("</", "<\\/")))


A3_PAGE = {"ouganda": "UGA", "kenya": "KEN", "france": "FRA", "nigeria": "NGA"}


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


# ---------------------------------------------------------------------------
# Refonte du 17 octobre 2026 (melange des options 1 et 2 des maquettes
# tmp/proto-pays-1017) : la page d'un pays prend l'en-tete des pages province
# (grand titre, « Situation au », chiffres bleu / rouge, carte a droite), puis
# sa chronologie « Jour apres jour » (data/autres-pays.json, « evenements »),
# l'escalier des cas quand chaque cas a sa date d'annonce (« courbe »), le
# recit complet replie, les questions et les sources. La page « Autres pays »
# devient un tableau a filets (une ligne par pays, vers sa page) et une frise
# de mai a octobre.

LIB = {
    "fr": dict(situation="Situation au {d}", chrono="Jour après jour",
               chrono_note="Chaque ligne reprend un fait daté des sources citées en bas de page.",
               leg=("cas confirmés", "décès", "déplacement", "annonce officielle"),
               cumul=lambda n: "%d cas" % n, courbe="Les cas, un par un",
               courbe_note="cas confirmés cumulés, à la date de chaque annonce", deces="décès",
               recit="Le récit complet", pays="Pays", cas="Cas", morts="Décès", etat="État",
               frise="Hors de RDC, mois après mois",
               frise_note="du premier cas à la fin dans chaque pays ; en rouge, en cours",
               mois_c=["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]),
    "en": dict(situation="Situation as of {d}", chrono="Day by day",
               chrono_note="Each line restates a dated fact from the sources listed at the bottom of the page.",
               leg=("confirmed cases", "death", "travel", "official announcement"),
               cumul=lambda n: "%d case%s" % (n, "" if n == 1 else "s"), courbe="Cases, one by one",
               courbe_note="cumulative confirmed cases, on the date of each announcement", deces="death",
               recit="The full account", pays="Country", cas="Cases", morts="Deaths", etat="Status",
               frise="Outside the DRC, month by month",
               frise_note="from the first case to the end in each country; in red, ongoing",
               mois_c=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]),
    "sw": dict(situation="Hali kufikia tarehe {d}", chrono="Siku kwa siku",
               chrono_note="Kila mstari unarudia jambo lenye tarehe kutoka kwenye vyanzo vilivyotajwa chini ya ukurasa.",
               leg=("wagonjwa waliothibitishwa", "kifo", "safari", "tangazo rasmi"),
               cumul=lambda n: "wagonjwa %d" % n if n != 1 else "mgonjwa 1", courbe="Wagonjwa, mmoja baada ya mwingine",
               courbe_note="jumla ya wagonjwa waliothibitishwa, kwa tarehe ya kila tangazo", deces="kifo",
               recit="Simulizi kamili", pays="Nchi", cas="Wagonjwa", morts="Vifo", etat="Hali",
               frise="Nje ya DRC, mwezi baada ya mwezi",
               frise_note="kutoka mgonjwa wa kwanza hadi mwisho katika kila nchi; kwa rangi nyekundu, unaendelea",
               mois_c=["Jan", "Feb", "Mac", "Apr", "Mei", "Jun", "Jul", "Ago", "Sep", "Okt", "Nov", "Des"]),
}
TYPES_EV = ("cas", "deces", "geo", "officiel")


def _jour_court(iso, lang):
    a, m, j = iso.split("-")
    return "%d %s" % (int(j), LIB[lang]["mois_c"][int(m) - 1])


def _jours(a, b):
    import datetime as _dt
    return (_dt.date.fromisoformat(b) - _dt.date.fromisoformat(a)).days


def _anneaux_pays(a3):
    """Districts (Ouganda) ou comtes (Kenya) avec leur nom ; la France en un
    seul contour Natural Earth (metropole et Corse, sans les petites iles)."""
    admin = _lire("site", "geo", "hors-rdc-admin.json")
    if a3 in admin:
        return [(u["nom"], u["anneaux"]) for u in admin[a3]]
    g = next(c["geometry"] for c in _lire("site", "geo", "region-monde.json")["pays"] if c["a3"] == a3)
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return [("", [r for poly in polys for r in poly if len(r) > 30])]


def carte_pays_html(pid, lang, w=520):
    """La carte de l'en-tete : le pays seul, decoupe en districts ou comtes,
    ceux qui ont eu des cas au bleu fonce de la carte (data/hors-rdc.json,
    « unites »), la ville du premier cas marquee. Projection equirectangulaire
    corrigee du cosinus de la latitude moyenne, comme la carte de l'accueil."""
    import math
    a3 = A3_PAGE[pid]
    hr = next((p for p in _hors() if p["a3"] == a3), None)
    touchees = {n for u in (hr or {}).get("unites", []) for n in u["noms"]}
    unites = _anneaux_pays(a3)
    xs = [x for _, rs in unites for r in rs for x, _ in r]
    ys = [y for _, rs in unites for r in rs for _, y in r]
    c = math.cos(math.radians((min(ys) + max(ys)) / 2))
    x0, x1, y0, y1 = min(xs) * c, max(xs) * c, min(ys), max(ys)
    k = w / (x1 - x0)
    h = (y1 - y0) * k
    f = lambda x, y: "%.1f %.1f" % ((x * c - x0) * k, (y1 - y) * k)
    chemins = "".join(
        '<path class="pp-u%s" d="%s"><title>%s</title></path>'
        % (" is-on" if nom in touchees else "", "".join("M" + "L".join(f(x, y) for x, y in r) + "Z" for r in rs), _esc(nom))
        for nom, rs in unites)
    ville = ""
    if hr and hr.get("lon") is not None:
        vx, vy = (hr["lon"] * c - x0) * k, (y1 - hr["lat"]) * k
        ville = ('<g class="pp-ville"><circle cx="%.1f" cy="%.1f" r="5"/><text x="%.1f" y="%.1f">%s</text></g>'
                 % (vx, vy, vx + 10, vy + 5, _esc(hr["ville"][lang])))
    return ('<svg class="pp-carte" viewBox="-4 -4 %.0f %.0f" role="img" aria-label="%s">%s%s</svg>'
            % (w + 8, h + 8, _esc(_pays(pid)["nom"][lang]), chemins, ville))


def chiffres_html(p, lang, cls="pp-kpi"):
    classes = ["is-cas", "is-dc", ""]
    return '<div class="%s">%s</div>' % (cls, "".join(
        '<div class="k %s"><span class="lbl">%s</span><b>%s</b></div>'
        % (classes[i] if i < 3 else "", _esc(c["l"][lang]), _esc(c.get({"en": "nEn", "sw": "nSw"}.get(lang, "n"), c["n"])))
        for i, c in enumerate(p["chiffres"])))


def entete_pays_html(pid, lang, h1, lede, lien_autres, libelle_autres):
    """L'en-tete de la page d'un pays, sur le modele des pages province."""
    p = _pays(pid)
    doc = _lire("data", "autres-pays.json")
    return (
        '  <section class="section pp-hero">\n'
        '    <div class="pp-txt">\n'
        '      <div class="eyebrow"><span class="dot"></span><a href="%s">%s</a></div>\n'
        '      <h1 class="pp-titre">%s</h1>\n'
        '      <p class="pp-sit">%s</p>\n'
        '      <p class="pp-intro">%s</p>\n'
        '      %s\n'
        '      <p class="pp-statut is-%s"><i></i>%s</p>\n'
        '    </div>\n'
        '    <div class="pp-carte-wrap">%s</div>\n'
        '  </section>'
        % (_esc(lien_autres), _esc(libelle_autres), _esc(h1),
           _esc(LIB[lang]["situation"].format(d=_date(p.get("situation") or doc["maj"], lang))), lede,
           chiffres_html(p, lang), p["etat"], _esc(p["statut"][lang]), carte_pays_html(pid, lang)))


def chronologie_html(pid, lang):
    p = _pays(pid)
    L = LIB[lang]
    leg = "".join('<span class="is-%s">%s</span>' % (t, _esc(l)) for t, l in zip(TYPES_EV, L["leg"]))
    lignes = "".join(
        '<li class="pp-e is-%s"><time datetime="%s">%s</time><div><h3>%s%s</h3><p>%s</p></div></li>'
        % (e["type"], e["date"], _jour_court(e["date"], lang), _esc(e["titre"][lang]),
           ' <span class="pp-cum">%s</span>' % _esc(L["cumul"](e["cumul"])) if e.get("cumul") else "",
           _esc(e["texte"][lang]))
        for e in p.get("evenements", []))
    return ('<h2 class="pp-t">%s</h2><p class="pp-st">%s</p><div class="pp-leg">%s</div><ol class="pp-tl">%s</ol>'
            % (_esc(L["chrono"]), _esc(L["chrono_note"]), leg, lignes))


def courbe_html(pid, lang, w=680, h=220):
    """L'escalier des cas confirmes cumules, un palier par annonce. Seulement
    pour un pays dont chaque cas a sa date d'annonce (« courbe » : true)."""
    import datetime as _dt
    p = _pays(pid)
    if not p.get("courbe"):
        return ""
    L = LIB[lang]
    pts = [(e["date"], e["cumul"]) for e in p["evenements"] if e.get("cumul")]
    morts = [e["date"] for e in p["evenements"] if e["type"] == "deces"]
    debut = min([e["date"] for e in p["evenements"]])
    fin = (_dt.date.fromisoformat(_lire("data", "autres-pays.json")["maj"]) + _dt.timedelta(1)).isoformat()
    n = max(1, _jours(debut, fin))
    ymax = max(v for _, v in pts) + 1
    pas = 1 if ymax <= 5 else 2 if ymax <= 12 else 5
    ymax = ((ymax + pas - 1) // pas) * pas
    pl, pr, pt, pb = 34, 16, 16, 30
    X = lambda d: pl + _jours(debut, d) * (w - pl - pr) / float(n)
    Y = lambda v: pt + (h - pt - pb) * (1 - v / float(ymax))
    trace = "M%.1f %.1f" % (X(debut), Y(0)) + "".join("H%.1fV%.1f" % (X(d), Y(v)) for d, v in pts) + "H%.1f" % X(fin)
    grille = "".join('<line class="g" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/><text class="ax" x="%d" y="%.1f" text-anchor="end">%d</text>'
                     % (pl, w - pr, Y(v), Y(v), pl - 8, Y(v) + 4, v) for v in range(0, ymax + 1, pas))
    dates = "".join('<text class="ax" x="%.1f" y="%d" text-anchor="middle">%s</text>' % (X(d), h - 8, _jour_court(d, lang))
                    for d, _ in pts)
    marques = "".join('<circle class="pt" cx="%.1f" cy="%.1f" r="4"/><text class="lab" x="%.1f" y="%.1f">%d</text>'
                      % (X(d), Y(v), X(d) - 6, Y(v) - 9, v) for d, v in pts)
    dc = "".join('<g class="dc"><line x1="%.1f" x2="%.1f" y1="%d" y2="%.1f"/><text x="%.1f" y="%d">%s</text></g>'
                 % (X(d), X(d), pt, Y(0), X(d) + 5, pt + 10, _esc(L["deces"])) for d in morts)
    aria = ", ".join("%s : %d" % (_jour_court(d, lang), v) for d, v in pts)
    return ('<h2 class="pp-t">%s</h2><p class="pp-st">%s</p>'
            '<svg class="pp-esc" viewBox="0 0 %d %d" role="img" aria-label="%s">%s%s%s<path class="l" d="%s"/>%s</svg>'
            % (_esc(L["courbe"]), _esc(L["courbe_note"]), w, h, _esc(aria), grille, dates, dc, trace, marques))


def recit_html(pid, lang):
    p = _pays(pid)
    # Deplie en entier (17 octobre 2026, demande du proprietaire). Mise en
    # page legere : le premier paragraphe en chapeau, et la date qui ouvre un
    # paragraphe (« Le 16 octobre 2026, ») en gras, pour reperer les etapes.
    import re
    date_tete = re.compile(r"^((?:Le|Les|Au|On|As of|By|Tarehe|Kufikia tarehe) \d{1,2}(?: (?:et|and|na) \d{1,2})? \w+ 20\d\d)(,?)")
    def para(i, t):
        t = _esc(t) if i == 0 else date_tete.sub(lambda m: "<strong>%s</strong>%s" % (m.group(1), m.group(2)), _esc(t), count=1)
        return '<p%s>%s</p>' % (' class="pp-chapeau"' if i == 0 else "", t)
    return ('<div class="pp-recit"><h2 class="pp-t">%s</h2>%s</div>'
            % (_esc(LIB[lang]["recit"]), "".join(para(i, t) for i, t in enumerate(p["texte"][lang]))))


def sources_html(pid, lang, titre):
    p = _pays(pid)
    return ('<div class="pp-sources"><h2>%s</h2><ul>%s</ul></div>'
            % (_esc(titre), "".join('<li><a href="%s"%s>%s</a></li>'
                                    % (_esc(s["url"]), ' target="_blank" rel="noopener"' if s["url"].startswith("http") else "",
                                       _esc(s["l"][lang])) for s in p["sources"])))


def tableau_html(lang, libelles, liens):
    """Autres pays : une ligne par pays, dans l'ordre du premier cas, qui mene
    a la page du pays (toute la ligne est un lien)."""
    L = LIB[lang]
    doc = _lire("data", "autres-pays.json")
    tete = ('<div class="ap2-tete"><span>%s</span><span>%s</span><span>%s</span><span>%s</span><span>%s</span></div>'
            % tuple(_esc(x) for x in (L["pays"], L["cas"], L["morts"], libelles["premier"], L["etat"])))
    lignes = []
    for p in doc["pays"]:
        cas, morts = p["chiffres"][0]["n"], p["chiffres"][1]["n"]
        lignes.append(
            '<a class="ap2-l" href="%s"><span class="nm">%s<b>%s</b></span><span class="n">%s</span><span class="n dc">%s</span>'
            '<span class="d">%s</span><span class="st is-%s"><i></i>%s</span></a>'
            % (_esc(liens.get(p["id"], "#")), _silhouette(p["id"], 30), _esc(p["nom"][lang]), _esc(cas), _esc(morts),
               _esc(_date(p["premier"], lang)), p["etat"], _esc(p["etatCourt"][lang])))
    return '<div class="ap2-g">%s%s</div>' % (tete, "".join(lignes))


def panneau_html(lang, titre, liens):
    """Accueil, barre sous la carte (21 octobre 2026, option 4 de
    tmp/proto-hors-rdc-1021) : apres le bouton « Hors RDC », les autres pays
    touches dans l'ordre du premier cas, chacun avec ses cas confirmes et un
    lien vers sa page, precedes de « Cas confirmes hors RDC » qui dit ce que
    sont les nombres. Les cas sont ceux de la fiche (data/autres-pays.json),
    jamais additionnes a ceux de la RDC : sources et dates differentes."""
    doc = _lire("data", "autres-pays.json")
    pays = " ".join(
        '<a class="is-%s" href="%s">%s <b>%s</b></a>'
        % (p["etat"], _esc(liens.get(p["id"], "#")), _esc(p["nom"][lang]), _esc(p["chiffres"][0]["n"]))
        # Du plus grand nombre de cas au plus petit (21 octobre 2026) ; a
        # egalite, l'epidemie en cours passe devant la terminee.
        for p in sorted(doc["pays"], key=lambda p: (-int(p["chiffres"][0]["n"]), p["etat"] != "cours")))
    return ('              <span class="cd-hors" role="group" aria-label="%s"><span class="k">%s</span>%s</span>'
            % (_esc(titre), _esc(titre), pays))


def nav_pays(lang):
    """Menu « Hors RDC » (21 octobre 2026) : une ligne par pays, les epidemies
    en cours d'abord puis du plus grand nombre de cas au plus petit ; sous le
    nom, « 9 cas · en cours ». Rend (id du pays, nom, description)."""
    t = TEXTES[lang]
    doc = _lire("data", "autres-pays.json")
    out = []
    for p in sorted(doc["pays"], key=lambda p: (p["etat"] != "cours", -int(p["chiffres"][0]["n"]))):
        n = int(p["chiffres"][0]["n"])
        mot = t["cas1"] if n == 1 else t["court_cas"]
        cas = ("%s %d" % (mot, n)) if lang == "sw" else ("%d %s" % (n, mot))
        etat = t["court_cours"] if p["etat"] == "cours" else t["court_fini"]
        out.append((p["id"], p["nom"][lang], "%s · %s" % (cas, etat)))
    return out


def frise_html(lang, w=900):
    """Mai -> fin du mois courant : une bande par pays, du premier cas a la fin
    (« fin ») ou a la date de mise a jour pour une epidemie en cours."""
    import datetime as _dt
    L = LIB[lang]
    doc = _lire("data", "autres-pays.json")
    d0 = "2026-05-01"
    m = _dt.date.fromisoformat(doc["maj"])
    d1 = (_dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)).isoformat()
    pays = doc["pays"]
    h = 30 + 40 * len(pays)
    gauche = 110
    X = lambda d: gauche + _jours(d0, d) * (w - gauche - 20) / float(_jours(d0, d1))
    out = []
    mois = _dt.date.fromisoformat(d0)
    while mois.isoformat() < d1:
        x = X(mois.isoformat())
        out.append('<line class="g" x1="%.1f" x2="%.1f" y1="4" y2="%d"/><text class="ax" x="%.1f" y="%d">%s</text>'
                   % (x, x, h - 22, x + 4, h - 6, _esc(MOIS[lang][mois.month - 1])))
        mois = _dt.date(mois.year + (mois.month == 12), mois.month % 12 + 1, 1)
    for i, p in enumerate(pays):
        y = 12 + i * 40
        a, b = X(p["premier"]), X(p.get("fin") or doc["maj"])
        out.append('<text class="fn" x="0" y="%d">%s</text>' % (y + 13, _esc(p["nom"][lang])))
        out.append('<rect class="bande is-%s" x="%.1f" y="%d" width="%.1f" height="18" rx="9"><title>%s</title></rect>'
                   % (p["etat"], a, y, max(18, b - a), _esc(p["etatCourt"][lang])))
        out.append('<text class="bl" x="%.1f" y="%d">%s</text>' % (max(a + 18, b) + 10, y + 13, _esc(LIB[lang]["cumul"](int(p["chiffres"][0]["n"])))))
    return ('<h2 class="pp-t">%s</h2><p class="pp-st">%s</p><svg class="ap2-frise" viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>'
            % (_esc(L["frise"]), _esc(L["frise_note"]), w, h, _esc(L["frise"]), "".join(out)))


def resumes_html(lang, liens):
    """Autres pays (17 octobre 2026) : un court paragraphe par pays, sous le
    tableau, nom en gras vers sa page, puis « Ce qui relie ces cas »."""
    doc = _lire("data", "autres-pays.json")
    pays = "".join(
        '<p><a href="%s"><b>%s.</b></a> %s</p>' % (_esc(liens.get(p["id"], "#")), _esc(p["nom"][lang]), _esc(p["resume"][lang]))
        for p in doc["pays"] if p.get("resume"))
    relie = doc.get("relie")
    lien = ('<h2 class="pp-t">%s</h2><p>%s</p>' % (_esc(relie["titre"][lang]), _esc(relie["texte"][lang]))) if relie else ""
    return '<div class="ap2-resumes">%s</div>%s' % (pays, lien)
