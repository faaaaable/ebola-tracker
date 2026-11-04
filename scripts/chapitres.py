# -*- coding: utf-8 -*-
"""Mise en page en chapitres d'Ensemble du pays et des pages province
(4 novembre 2026, maquette 2b retenue par le proprietaire ; decisions dans
~/Desktop/rapport ebola tracker/_mis-de-cote-2026-11-04-mise-en-page-ensemble/).

Le gabarit (donnees.html, province.html et les fonctions qui rendent leurs
cadres) produit toujours des cadres numerotes « .cadre-fiche » ; ce module
les reorganise, a la generation, en chapitres :

  - menu a ancres de la page Kenya (.pp-sousnav), avec les numeros ;
  - chaque chapitre : numero 01 en bleu, titre, chapeau, filet fin au-dessus ;
  - les figures dessous en pleine largeur, titrees au-dessus (.chap-fig) ;
  - Ensemble du pays : Evolution, Lieu des deces, Provinces & zones de sante,
    Riposte, Defis, Chronologie ; province : les memes, avec « Zones de
    sante », et seulement ceux que la province a ;
  - Riposte des provinces : plus d'encart a gauche (styles dans site.css).

Les blocs sont reperes par leur contenu (id des canevas et des tableaux,
classes), jamais par le texte des titres, qui change avec la langue. Si une
page ne ressemble pas a ce qu'on attend, elle est rendue telle quelle.
"""
import re
from bs4 import BeautifulSoup, Comment


def _fig(titre, sous=""):
    sub = '<span class="section-sub">%s</span>' % sous if sous else ""
    return '<div class="section-head chap-fig"><h3 class="frame-title">%s</h3>%s</div>' % (titre, sub)


def _txt(el):
    return el.get_text(" ", strip=True) if el else ""


def _contenu(el):
    return "".join(str(x) for x in el.contents) if el else ""


def _tete_cadre(sec):
    """(titre, sous-titre) de la tete numerotee d'un cadre."""
    return _txt(sec.select_one(".fiche-tete .frame-title")), _txt(sec.select_one(".fiche-tete .section-sub"))


def _blocs(corps):
    """Coupe le corps d'un cadre en blocs, un par intertitre .section-head."""
    blocs, cur = [], []
    for x in list(corps.contents):
        if getattr(x, "name", None) and "section-head" in (x.get("class") or []) and cur and any(
                getattr(y, "name", None) for y in cur):
            blocs.append(cur)
            cur = []
        cur.append(x)
    if cur:
        blocs.append(cur)
    return blocs


def _separer_lieu(corps):
    """Detache du cadre des deces le bloc « Le lieu du deces » (intertitre,
    phrase, graphique, barres par zone). Rend (chapeau, html) ou None."""
    cv = corps.select_one("#decesLieuChart")
    if not cv:
        return None
    blocs = _blocs(corps)
    for b in blocs:
        if any(getattr(x, "select_one", None) and (x.get("id") == "decesLieuChart" or x.select_one("#decesLieuChart"))
               for x in b if getattr(x, "name", None)):
            chapo, reste = "", []
            for x in b:
                x.extract()
                if getattr(x, "name", None) and "section-head" in (x.get("class") or []):
                    continue  # le titre du chapitre le remplace
                if (getattr(x, "name", None) == "p" and "fiche-texte" in (x.get("class") or []) and not chapo):
                    chapo = _txt(x)
                    continue
                reste.append(str(x))
            return chapo, "".join(reste)
    return None


def _chapitre(cid, num, titre, chapo, corps):
    return ('<section class="section chap" id="%s"><header class="chap-ouv"><span class="chap-num">%02d</span>'
            '<div><h2 class="chap-t">%s</h2>%s</div></header><div class="chap-corps">%s</div></section>\n'
            % (cid, num, titre, ('<p class="chap-chapo">%s</p>' % chapo) if chapo else "", corps))


def transformer(contenu, s, pays, dans=""):
    """Rend le fragment de la page en chapitres. s = chaines de la langue ;
    pays = True pour Ensemble du pays, False pour une province ; dans = « en
    Ituri », « au Nord-Kivu »... (province_forms), pour les chapeaux."""
    def ch(cle):
        if not pays and (cle + "Prov") in s:
            cle += "Prov"
        return s[cle].replace("{in}", dans)
    soupe = BeautifulSoup(contenu, "html.parser")
    # Les commentaires du gabarit : str() d'un Comment rend son texte SANS
    # <!-- -->, il s'afficherait sur la page. On les retire.
    for c in soupe.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    hero = soupe.select_one("section.prov-hero-b")
    cadres = soupe.select("section.cadre-fiche")
    if not hero or not cadres:
        return contenu

    # Les figures sont titrees au-dessus : le graphique ne repete pas ce titre
    # (sauf ceux qui portent leur propre titre, data-titre).
    for cv in soupe.select("canvas"):
        if not cv.has_attr("data-titre"):
            cv["data-sans-titre"] = ""

    def trouve(test):
        for sec in cadres:
            if test(sec):
                return sec
        return None

    cas = trouve(lambda x: x.select_one("#casChart") or x.select_one('canvas[data-chart="provinceEpidemic"]:not([data-champ])'))
    deces = trouve(lambda x: x.select_one("#decesChart") or x.select_one('canvas[data-champ="deaths"]'))
    ou = trouve(lambda x: x.select_one("#provinceSummaryTable") or x.select_one("#zonesProvinceTable"))
    riposte = trouve(lambda x: x.get("id") == "riposte")
    defis = trouve(lambda x: "cadre-obstacles" in (x.get("class") or []))
    chrono = trouve(lambda x: x.select_one(".timeline-h, .th-scroller"))
    if not ou:
        return contenu

    chapitres = []  # (id, titre, chapeau, corps)
    if cas or deces:
        corps = ""
        if cas:
            t, st = _tete_cadre(cas)
            corps += _fig(t, st) + _contenu(cas.select_one(".cadre-corps"))
        lieu = None
        if deces:
            dc = deces.select_one(".cadre-corps")
            lieu = _separer_lieu(dc)
            t, st = _tete_cadre(deces)
            corps += '<span id="deces" class="chap-ancre"></span>' * bool(pays) + _fig(t, st) + _contenu(dc)
        chapitres.append(("cas" if pays else "evolution", s["chapEvolution"], ch("chapEvolutionChapo"), corps))
        if lieu:
            chapitres.append(("lieu", s["chapLieu"], lieu[0], lieu[1]))

    corps_ou = ou.select_one(".cadre-corps")
    if pays:
        # Le graphique par province en tete, puis les deux tableaux : du plus
        # large au plus fin.
        blocs = _blocs(corps_ou)
        graph = [b for b in blocs if any(getattr(x, "select_one", None) and x.select_one("#provChart") for x in b if getattr(x, "name", None))]
        autres = [b for b in blocs if b not in graph]
        ordre = graph + autres
        html_ou = "".join("".join(str(x) for x in b) for b in ordre)
        chapitres.append(("ou", s["chapGeo"], s["chapGeoChapo"], html_ou))
    else:
        chapitres.append(("zones", s["chapZones"], ch("chapZonesChapo"), _contenu(corps_ou)))

    if riposte:
        rc = riposte.select_one(".cadre-corps")
        p = rc.select_one(":scope > p.fiche-texte")
        chapo = _txt(p)
        if p:
            p.extract()
        chapitres.append(("riposte", s["chapRiposte"], chapo, _contenu(rc)))
    if defis:
        t, st = _tete_cadre(defis)
        dc = defis.select_one(".cadre-corps")
        for a in dc.select("p.drill a"):
            a.string = s["chapDefisLien"] + " →"
        chapitres.append(("defis", s["chapDefis"], ch("chapDefisChapo"), _fig(t, st) + _contenu(dc)))
    if chrono:
        chapitres.append(("chronologie", s["chapChrono"], ch("chapChronoChapoPays" if pays else "chapChronoChapo"),
                          _contenu(chrono.select_one(".cadre-corps"))))

    nav = ('<nav class="pp-sousnav chap-nav" aria-label="%s"><div>' % _txt(hero.select_one(".phb-pre") or hero.select_one(".page-title"))
           + "".join('<a href="#%s"><b class="chap-nav-n">%02d</b>%s</a>' % (cid, k + 1, t)
                     for k, (cid, t, _, _) in enumerate(chapitres))
           + "</div></nav>\n")
    chap_html = "".join(_chapitre(cid, k + 1, t, c, b) for k, (cid, t, c, b) in enumerate(chapitres))

    # La suite de la page (note de lecture) reste apres les chapitres ; le
    # vieux sommaire d'Ensemble du pays (.riposte-ancres) disparait.
    reste = []
    for sec in soupe.find_all("section", recursive=False):
        if sec is hero or sec in cadres or sec.select_one(".riposte-ancres"):
            continue
        reste.append(str(sec))
    return str(hero) + "\n" + nav + chap_html + "\n".join(reste)
