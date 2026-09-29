# -*- coding: utf-8 -*-
"""Seconde partie de la maquette « Riposte & defis » : les obstacles depuis
mai, REDIGES, avec une mise en page propre — une bande sombre d'ouverture,
une frise « quand chaque obstacle apparait dans les bulletins », puis une
fiche par obstacle.

La matiere est data/defis-synthese.json (texte fr/en/sw). Ce qui dit quel
obstacle est cite, dans quel bulletin et pour quelle province, est le CODAGE
data/defis-codage.json : chaque texte des sections « Defis » y a ete lu et
classe a la main (deux lectures independantes, les desaccords tranches), avec
la province de chaque proposition. Plus aucun mot-cle ne decide : un texte
absent du codage fait echouer la generation (voir manquants()), pour qu'un
bulletin nouveau ne passe jamais sans avoir ete lu.
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNTHESE = os.path.join(ROOT, "data", "defis-synthese.json")
DEFIS = os.path.join(ROOT, "data", "defis.json")
CODAGE = os.path.join(ROOT, "data", "defis-codage.json")
# Les bulletins d'avant le 084, geles depuis le corpus (non versionne) par
# scripts/geler_defis_anciens.py — voir ce script pour la raison.
DEFIS_ANCIENS = os.path.join(ROOT, "data", "defis-anciens.json")
PROVINCES = ["Ituri", "Nord-Kivu", "Haut-Uélé", "Tshopo", "Sud-Kivu", "Bas-Uélé", "Sud-Ubangi"]


def cle(t):
    """La cle d'un texte dans le codage : minuscules, ponctuation et espaces
    neutralises, chiffres remplaces par #. Deux bulletins qui ne different que
    par un chiffre partagent un codage."""
    return re.sub(r"\d+", "#", re.sub(r"\W+", " ", (t or "").lower())).strip()


def codage():
    with io.open(CODAGE, encoding="utf-8") as fh:
        return json.load(fh)["unites"]


def entrees_brutes():
    """(date, numero, texte) pour chaque difficulte citee.

    data/defis.json (extracteur dedie, 084 et suivants), puis
    data/defis-anciens.json pour les bulletins anterieurs, retranscrits du PDF
    a la main le 29 septembre 2026 (l'extraction automatique perdait les
    lignes apres un saut de page, melangeait les cellules et ramassait le
    tableau des perspectives et des legendes de photos)."""
    out = []
    vus = set()
    if os.path.exists(DEFIS):
        with io.open(DEFIS, encoding="utf-8") as fh:
            d = json.load(fh)
        for p in d.get("parDate", []):
            for b in p["piliers"]:
                for it in b["items"]:
                    out.append((p["date"], p["sitrepNumber"], it))
            vus.add(p["sitrepNumber"])
    if os.path.exists(DEFIS_ANCIENS):
        with io.open(DEFIS_ANCIENS, encoding="utf-8") as fh:
            for e in json.load(fh).get("entrees", []):
                if e["sitrepNumber"] in vus:
                    continue
                out.append((e["date"], e["sitrepNumber"], e["texte"]))
    return out


def manquants():
    """Les textes des sections « Defis » que le codage n'a pas lus."""
    c = codage()
    return sorted({t for _, _, t in entrees_brutes() if cle(t) not in c})


def entrees():
    """(date, numero, texte, attributions) : attributions = [{province,
    obstacles}] lues dans le codage. Leve une erreur si un texte n'a pas ete
    code : mieux vaut ne rien generer qu'une frise qui ignore un bulletin."""
    c = codage()
    out, absents = [], []
    for date, num, texte in entrees_brutes():
        a = c.get(cle(texte))
        if a is None:
            absents.append((num, texte))
            continue
        out.append((date, num, texte, a))
    if absents:
        raise RuntimeError("defis-codage.json ne couvre pas %d texte(s), ex. bulletin %s : %s"
                           % (len(absents), absents[0][0], absents[0][1][:120]))
    return out


def mentions(theme, ent, province=None):
    """Les mentions d'un obstacle : un texte compte si son codage l'attribue a
    l'obstacle, pour la province demandee (ou pour n'importe laquelle)."""
    hits = [e for e in ent
            if any(theme["id"] in a["obstacles"] and (province is None or a["province"] == province)
                   for a in e[3])]
    if not hits:
        return None
    hits.sort(key=lambda e: e[0])
    nums = sorted({e[1] for e in hits})
    prov = {}
    for e in hits:
        for a in e[3]:
            if theme["id"] in a["obstacles"] and a["province"] != "aucune":
                prov[a["province"]] = prov.get(a["province"], 0) + 1
    return {"premier": hits[0], "dernier": hits[-1], "bulletins": len(nums),
            "dates": sorted({e[0] for e in hits}),
            "provinces": [p for p, _ in sorted(prov.items(), key=lambda kv: -kv[1])][:3]}


def jours(a, b):
    from datetime import date
    ya, ma, da = map(int, a.split("-")); yb, mb, db = map(int, b.split("-"))
    return (date(yb, mb, db) - date(ya, ma, da)).days


def grille(L, esc, long_date, i18n_lang, debut, fin, ent_tous, themes, tl, lien, province=None, saute_vides=False):
    """La grille par semaine des obstacles (7 septembre 2026), pour le pays
    entier ou, avec `province`, pour une province (29 septembre 2026).

    Les colonnes (semaines) et le denominateur (les bulletins parus, ent_tous)
    sont ceux du pays dans les deux cas : la grille d'une province se lit
    contre celle du pays, case a case. Les dix obstacles y figurent toujours,
    dans l'ordre du pays, meme sans mention (saute_vides ne sert qu'au pays,
    ou un theme sans mention n'a pas de ligne)."""
    from datetime import date as _date, timedelta as _td
    d0 = _date.fromisoformat(debut)
    nb_sem = (_date.fromisoformat(fin) - d0).days // 7 + 1
    mois_abbr = {"fr": ["", "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
                 "en": ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                 "sw": ["", "Jan.", "Feb.", "Mac.", "Apr.", "Mei", "Juni", "Julai", "Ago.", "Sept.", "Okt.", "Nov.", "Des."]}[L]
    tete, mois_vu = [], None
    for k in range(nb_sem):
        ds_ = d0 + _td(days=7 * k + 3)  # le mois d'une semaine est celui de son milieu
        lab = mois_abbr[ds_.month] if ds_.month != mois_vu else ""
        mois_vu = ds_.month
        tete.append('<span>%s</span>' % esc(lab))
    parus = [0] * nb_sem
    for d in sorted({e[0] for e in ent_tous}):
        k = (_date.fromisoformat(d) - d0).days // 7
        if 0 <= k < nb_sem:
            parus[k] += 1
    survol = {"fr": "%s → %s · %d bulletin%s sur %d", "en": "%s → %s · %d bulletin%s of %d",
              "sw": "%s → %s · ripoti %d%s kati ya %d"}[L]
    html = ['<div class="grille" style="--sem:%d">'
            '<div class="grille-tete"><div class="frise-label"></div><div class="grille-mois">%s</div></div>'
            % (nb_sem, "".join(tete))]
    # --sem : le nombre de colonnes suit les semaines. Il etait ecrit « 14 »
    # dans site.css ; a la quinzieme semaine (SitRep 119, 10 septembre 2026)
    # la derniere case de chaque ligne passait a la ligne sous juin.

    def niveau(n, p):
        if n == 0 or p == 0:
            return 0
        part = n / p
        return 1 if part < 0.5 else 2 if part < 0.999 else 3

    for i, (t, mm_pays) in enumerate(themes, 1):
        if not mm_pays and saute_vides:
            continue
        mm = mentions(t, ent_tous, province) if province else mm_pays
        comptes = [0] * nb_sem
        for d in (mm["dates"] if mm else []):
            k = (_date.fromisoformat(d) - d0).days // 7
            if 0 <= k < nb_sem:
                comptes[k] += 1
        cases = []
        for k, (n, p) in enumerate(zip(comptes, parus)):
            ds_ = d0 + _td(days=7 * k)
            de_ = min(ds_ + _td(days=6), _date.fromisoformat(fin))
            info = survol % (long_date(ds_.isoformat(), i18n_lang), long_date(de_.isoformat(), i18n_lang), n, "" if (n == 1 or L == "sw") else "s", p)
            cases.append('<i class="n%d" data-semaine="%s"></i>' % (niveau(n, p), esc(info)))
        html.append('<div class="grille-row"><div class="frise-label"><a href="%s"><span class="frise-num">%02d</span>%s</a></div>'
                    '<div class="grille-cases">%s</div></div>' % (lien(t), i, esc(tl(t)["titre"]), "".join(cases)))
    legende = {"fr": "part des bulletins de la semaine : aucun, moins de la moitié, la plupart, tous",
               "en": "share of the week's bulletins: none, under half, most, all",
               "sw": "sehemu ya ripoti za wiki: hakuna, chini ya nusu, nyingi, zote"}[L]
    html.append('<div class="grille-legende"><i class="n0"></i><i class="n1"></i><i class="n2"></i><i class="n3"></i><span>%s</span></div>' % esc(legende))
    html.append('</div>')
    return "".join(html)


def grille_province(province, lang, i18n_lang, long_date, esc, numero, lien_riposte, prep_lien):
    """Le cadre « Des obstacles qui apparaissent dans chaque bulletin » d'une
    page province : la grille du pays, filtree sur les difficultes qui citent
    la province (29 septembre 2026). Les difficultes rattachees a aucune
    province ne comptent dans aucune grille provinciale."""
    with io.open(SYNTHESE, encoding="utf-8") as fh:
        S = json.load(fh)
    ent = entrees()
    if not ent:
        return ""
    L = lang if lang in ("fr", "en", "sw") else "fr"

    def tl(t):
        return t.get(L) or t["fr"]
    themes = [(t, mentions(t, ent)) for t in S["themes"]]
    themes.sort(key=lambda tm: tm[1]["premier"][0] if tm[1] else "9999-99-99")
    titre = {"fr": "Les principaux défis mentionnés dans les bulletins officiels",
             "en": "The main challenges mentioned in the official bulletins",
             "sw": "Changamoto kuu zilizotajwa katika ripoti rasmi"}[L]
    sub = {"fr": "%s : une case par semaine, teintée selon la part des bulletins qui citent l'obstacle dans la province",
           "en": "%s: one cell per week, shaded by the share of bulletins citing the obstacle in the province",
           "sw": "%s: kisanduku kimoja kwa wiki, rangi kulingana na sehemu ya ripoti zinazotaja kikwazo katika jimbo"}[L] % prep_lien
    g = grille(L, esc, long_date, i18n_lang, S["debut"], max(e[0] for e in ent), ent, themes, tl,
               lambda t: "%s#defi-%s" % (lien_riposte, t["id"]), province=province)
    return ('  <section class="section cadre-fiche cadre-obstacles">\n'
            '    <div class="fiche-tete"><span class="fiche-num">%s</span><div><h2 class="frame-title">%s</h2>'
            '<div class="section-sub">%s</div></div></div>\n'
            '    <div class="cadre-corps">\n%s\n    </div>\n  </section>\n' % (esc(numero), esc(titre), esc(sub), g))


def render(lang, strings_lang, i18n_lang, long_date, esc, couleurs):
    with io.open(SYNTHESE, encoding="utf-8") as fh:
        S = json.load(fh)
    ent = entrees()
    if not ent:
        return {"seed.defisSynthese": ""}
    fin = max(e[0] for e in ent)
    debut = S["debut"]
    total = jours(debut, fin) or 1
    nb_bulletins = len({e[1] for e in ent})
    # Le swahili est rendu depuis le 7 septembre 2026 (traduction de
    # l'assistant, a faire relire) ; toute autre langue tombe sur le francais
    # avec la note. Un theme sans texte dans la langue retombe sur le francais.
    L = lang if lang in ("fr", "en", "sw") else "fr"
    note_langue = lang not in ("fr", "en", "sw")

    def tl(t):
        return t.get(L) or t["fr"]
    themes = []
    for t in S["themes"]:
        m = mentions(t, ent)
        themes.append((t, m))
    # Du plus ancien au plus recent (date de premiere mention, tri stable) :
    # la frise dessine un escalier — les obstacles presents des le premier
    # bulletin, puis ceux que juillet ajoute. Numeros et fiches suivent
    # (7 septembre 2026).
    themes.sort(key=lambda tm: tm[1]["premier"][0] if tm[1] else "9999-99-99")

    # ---- bande d'ouverture ----
    tx = {
        "fr": ("Seconde partie", "Les principales difficultés",
               "Les dix obstacles principaux à la riposte, tirés des sections « Défis » des bulletins de l'INSP.",
               "obstacles", "bulletins lus", "%s → %s", "période couverte"),
        "en": ("Part two", "The main difficulties",
               "The ten main obstacles to the response, drawn from the “Challenges” sections of the INSP bulletins.",
               "obstacles", "bulletins read", "%s → %s", "period covered"),
        "sw": ("Sehemu ya pili", "Changamoto kuu",
               "Vikwazo kumi vikuu vya mapambano, vilivyotolewa katika sehemu za « Changamoto » za ripoti za INSP.",
               "vikwazo", "ripoti zilizosomwa", "%s → %s", "kipindi kilichofunikwa"),
    }[L]
    html = ['<section class="section dossier" id="defis">',
            '<div class="dossier-in">',
            '<div class="eyebrow dossier-eyebrow"><span class="dot"></span>%s</div>' % esc(tx[0]),
            '<h2 class="dossier-titre">%s</h2>' % esc(tx[1]),
            '<p class="dossier-lede">%s</p>' % esc(tx[2]),
            '<div class="dossier-chiffres">'
            # « bulletins lus » retire le 7 septembre 2026 a la demande du proprietaire ;
            # nb_bulletins et tx[4] restent calcules, inutilises.
            # Seule la periode reste : « 10 obstacles » doublonnait le chapeau
            # (7 septembre 2026). tx[3] reste, inutilise.
            '<div><b class="is-texte">%s</b><span>%s</span></div>'
            % (esc(tx[5] % (long_date(debut, i18n_lang), long_date(fin, i18n_lang))), esc(tx[6])),
            '</div>']
    if note_langue:
        html.append('<p class="dossier-note">%s</p>' % esc(strings_lang.get("defiLangNote", "")))
    html.append('</div></section>')

    # ---- frise : la grille par semaine (7 septembre 2026) ----
    # Une case par semaine depuis le premier bulletin, teintee selon la part
    # des bulletins parus cette semaine-la qui citent l'obstacle (aucun,
    # moins de la moitie, la plupart, tous). Elle a remplace les traits par
    # bulletin : a 330 px ils faisaient un code-barres, et meme a 1 000 px
    # ils ne disaient pas l'intensite — une ligne dense se lisait comme une
    # presence continue la ou l'obstacle va et vient. La part et non le
    # nombre : une semaine a cinq bulletins (28 et 29 juillet sans parution)
    # ne doit pas paraitre plus faible qu'une semaine a sept. La fiche garde
    # la trace au bulletin pres (« cite dans N bulletins, du SitRep X au Y »).
    from datetime import date as _date, timedelta as _td
    titre_frise = {"fr": "Des obstacles qui apparaissent dans chaque bulletin",
                   "en": "Obstacles that appear in every bulletin",
                   "sw": "Vikwazo vinavyoonekana katika kila ripoti"}[L]
    sub_frise = {"fr": "une case par semaine, teintée selon la part des bulletins qui citent l'obstacle",
                 "en": "one cell per week, shaded by the share of bulletins citing the obstacle",
                 "sw": "kisanduku kimoja kwa wiki, rangi kulingana na sehemu ya ripoti zinazotaja kikwazo"}[L]
    html.append('<section class="section frise-section"><div class="section-head"><h3 class="frame-title">%s</h3>'
                '<span class="section-sub">%s</span></div>' % (esc(titre_frise), esc(sub_frise)))
    html.append(grille(L, esc, long_date, i18n_lang, debut, fin, ent, themes, tl,
                       lambda t: "#defi-%s" % t["id"], saute_vides=True))
    html.append('</section>')

    # ---- fiches ----
    trace = {"fr": "Cité dans %d bulletins, du SitRep %s (%s) au SitRep %s (%s).",
             "en": "Cited in %d bulletins, from SitRep %s (%s) to SitRep %s (%s).",
             "sw": "Imetajwa katika ripoti %d, kutoka SitRep %s (%s) hadi SitRep %s (%s)."}[L]
    html.append('<section class="section fiches-section"><ol class="fiches">')
    for i, (t, mm) in enumerate(themes, 1):
        pts = "".join('<span class="fiche-prov"><i style="background:%s"></i>%s</span>'
                      % (couleurs.get(p, "var(--ink-faint)"), esc(p)) for p in (mm["provinces"] if mm else []))
        tr = ""
        if mm:
            tr = trace % (mm["bulletins"], mm["premier"][1], long_date(mm["premier"][0], i18n_lang),
                          mm["dernier"][1], long_date(mm["dernier"][0], i18n_lang))
        html.append('<li class="fiche" id="defi-%s"><span class="fiche-num">%02d</span><div class="fiche-corps">'
                    '<h3 class="frame-title">%s</h3><p class="fiche-texte">%s</p>'
                    '<p class="fiche-trace">%s %s</p></div></li>'
                    % (t["id"], i, esc(tl(t)["titre"]), esc(tl(t)["texte"]), esc(tr), pts))
    html.append('</ol></section>')
    return {"seed.defisSynthese": "\n".join(html)}
