# -*- coding: utf-8 -*-
"""La lettre d'un bulletin (maquette du 8 septembre 2026, SitRep 114).

Une page par bulletin, lue comme une lettre : un objet, un chapeau, des
paragraphes courts qui relient les chiffres, les chiffres sous chaque
paragraphe, une rubrique « A surveiller » redigee a la main, un pied.

Trois natures de phrases, a distinguer :
- COMPOSEES depuis les donnees, a tournures conditionnelles (« aucune
  nouvelle zone » / « une nouvelle zone : Kayna ») — elles se regenerent
  seules ; elles decrivent, jamais n'interpretent ;
- CITEES mot pour mot (les « Defis »), entre guillemets ;
- REDIGEES par l'assistant au signal du proprietaire : le resume des Defis
  (data/bulletin-notes.json), date.
Un indicateur absent du bulletin s'ecrit « non publie ».
"""
import io
import json
import os
import re

import harmonisations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lire(chemin):
    with io.open(os.path.join(ROOT, chemin), encoding="utf-8") as fh:
        return json.load(fh)


def _point(serie, date, cle="parDate"):
    points = serie.get(cle, []) if isinstance(serie, dict) else serie
    for p in points:
        if p.get("date") == date:
            return p
    return None


# « en deux jours » se lit mieux que « en 2 jours » dans une lettre ecrite en
# langage courant ; au-dela de neuf, le chiffre reprend la main.
JOURS_EN_LETTRES = {
    "fr": {2: "deux", 3: "trois", 4: "quatre", 5: "cinq", 6: "six", 7: "sept",
           8: "huit", 9: "neuf"},
    "en": {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
           8: "eight", 9: "nine"},
    "sw": {2: "mbili", 3: "tatu", 4: "nne", 5: "tano", 6: "sita", 7: "saba",
           8: "nane", 9: "tisa"},
}


def _jours_mot(n, lang, fmt):
    return JOURS_EN_LETTRES.get(lang, {}).get(n) or fmt(n, lang)


def _nb_jours(debut, fin):
    """Jours entre deux dates ISO, pour dire sur combien de temps porte un
    ecart de cumul quand une province saute un bulletin."""
    import datetime
    a = datetime.date(*map(int, debut.split("-")))
    b = datetime.date(*map(int, fin.split("-")))
    return (b - a).days


def _liste(items, et):
    items = list(items)
    return items[0] if len(items) == 1 else (", ".join(items[:-1]) + et + items[-1]) if items else ""


def _extrait(texte, maxi=210):
    """La premiere phrase d'une citation, ou ses premiers mots suivis de « … »."""
    t = " ".join(texte.split())
    m = re.match(r"(.{20,%d}?[.;])\s" % maxi, t)
    if m:
        return m.group(1)
    if len(t) <= maxi:
        return t
    return t[:maxi].rsplit(" ", 1)[0] + "…"


LETTRES = os.path.join(ROOT, "data", "lettres")


def _cle_zone(z):
    """Identite d'une zone de sante : (province, nom normalise). Le bulletin
    ecrit tantot « Boma Mangbetu », tantot « Boma-Mangbetu » (ou « Nia Nia »,
    « Miti Murhesa », « BAMBU ») : comparer les noms bruts faisait d'une
    simple graphie une « nouvelle zone » (la lettre 140, le 3 octobre 2026).
    Meme normalisation que build_pages.normalise_zone : accents, casse, tirets,
    espaces."""
    import unicodedata
    nom = unicodedata.normalize("NFD", str(z.get("name") or ""))
    nom = "".join(c for c in nom if unicodedata.category(c) != "Mn")
    return (z.get("province"), re.sub(r"[^a-z0-9]", "", nom.lower()))


def reclassements(zones, avant, date):
    """Paires de zones d'une meme province dont l'une gagne exactement ce que
    l'autre perd, hors nouveaux cas annonces (6 novembre 2026, SitRep 174 :
    Beni 737 -> 775 pour 16 annonces, Biena 48 -> 26 pour 0 ; 22 cas de part
    et d'autre, le cumul du pays tombe juste). Le site ne dit pas qu'il s'agit
    d'un reclassement, le bulletin ne l'ecrit pas : il dit les deux chiffres en
    une phrase, et les tableaux n'ont pas de note (rien n'entre dans le cumul
    du pays). A partir du 4 novembre 2026 : les lettres publiees ne changent
    pas. Renvoie {cle_zone: (zone, autre_zone, ecart)} pour les deux zones."""
    if date < "2026-11-04":
        return {}
    ec = []
    for z in zones:
        a = avant.get(_cle_zone(z))
        if z.get("cases") is None or a is None:
            continue
        e = z["cases"] - a - (z.get("newCases24h") or 0)
        if e:
            ec.append((z, a, e))
    out = {}
    for prov in {z["province"] for z, _, _ in ec}:
        plus = [x for x in ec if x[0]["province"] == prov and x[2] > 0]
        moins = [x for x in ec if x[0]["province"] == prov and x[2] < 0]
        if len(plus) == 1 and len(moins) == 1 and plus[0][2] == -moins[0][2]:
            out[_cle_zone(plus[0][0])] = (plus[0], moins[0])
            out[_cle_zone(moins[0][0])] = None
    return out


def ajouts_cumul(zones, zh, date):
    """Les zones dont le cumul monte plus que les nouveaux cas annonces, au
    bulletin du `date` (30 octobre 2026, SitRep 167 : Yakoma entre avec 3 cas,
    0 annonce). Memes conditions que la note d'ecart de la Lettre : bulletin
    precedent de la veille, a partir du 160. Liste de {name, province, ecart},
    vide sinon : la note des tableaux disparait au bulletin suivant."""
    from datetime import date as _d
    # Une harmonisation (SitRep 169) ne compte pas comme un ajout.
    zh = harmonisations.rebaser(zh, date)
    zi = next((i for i, z in enumerate(zh) if z["date"] == date), None)
    if not zi or date < "2026-10-21":
        return []
    j0, j1 = (_d(*(int(x) for x in zh[k]["date"].split("-"))) for k in (zi - 1, zi))
    if (j1 - j0).days != 1:
        return []
    avant = {_cle_zone(z): z.get("cases") for z in zh[zi - 1]["zones"]}
    paires = reclassements(zones, avant, date)
    out = []
    for z in zones:
        if z.get("cases") is None or _cle_zone(z) in paires:
            continue
        ecart = z["cases"] - (avant.get(_cle_zone(z)) or 0) - (z.get("newCases24h") or 0)
        if ecart > 0:
            out.append({"name": z["name"], "province": z["province"], "ecart": ecart})
    return out


def _instantanes():
    """Une lettre par bulletin (8 septembre 2026) : data/lettres/<num>.json
    est la copie de data/latest.json au moment ou le bulletin a ete integre.
    Les series par date (alertes, labo, contacts, CTE, deces, defis, zones)
    gardent leur historique d'elles-memes ; seul l'instantane national et
    provincial devait etre fige. Le dernier bulletin est fige ici, a chaque
    generation, s'il ne l'etait pas encore."""
    latest = _lire("data/latest.json")
    num = latest["meta"]["sitrepNumber"]
    if not os.path.isdir(LETTRES):
        os.makedirs(LETTRES)
    chemin = os.path.join(LETTRES, "%s.json" % num)
    if not os.path.exists(chemin) or _lire("data/lettres/%s.json" % num) != latest:
        with io.open(chemin, "w", encoding="utf-8") as fh:
            json.dump(latest, fh, ensure_ascii=False, indent=1); fh.write("\n")
    out = {}
    for f in sorted(os.listdir(LETTRES)):
        m = re.match(r"(\d{3})\.json$", f)
        if m:
            out[m.group(1)] = _lire("data/lettres/%s" % f)
    return out


def pages_lettres(config):
    """Les pages /lettre/<num>/ a ajouter a config["pages"] avant de
    construire les URL : une par instantane, mise en page « agence »."""
    modele = next(p for p in config["pages"] if p["id"] == "bulletin")
    titres = {"fr": "La lettre n°%s — Ebola RDC", "en": "The letter no. %s — Ebola DRC", "sw": "Barua na. %s — Ebola DRC"}
    pages = []
    for num in sorted(_instantanes()):
        meta = {}
        for lg, m in modele["meta"].items():
            meta[lg] = dict(m); meta[lg]["title"] = titres.get(lg, titres["fr"]) % num
        pages.append({"id": "bulletin-%s" % num, "fragment": "bulletin-num.html", "lettreNum": num,
                      "noindex": modele.get("noindex", False), "needs": ["bulletin"], "changefreq": "daily", "priority": "0.6",
                      "schema": [], "navLabelKey": modele["navLabelKey"], "bodyClass": modele.get("bodyClass", ""),
                      # /lettre/<num>/, /en/letter/<num>/, /sw/barua/<num>/ : sous le slug de la page (9 septembre 2026)
                      "slug": {lg: "%s%s/" % (sl, num) for lg, sl in modele["slug"].items()},
                      "meta": meta})
    return pages


_DATES = {}
_NATIONAL = {}


def render(lang, S, i18n_lang, fmt, fmt_decimal, fmt_cfr, long_date, esc, interp,
           province_forms, couleurs, urls):
    """Les graines de la maquette (dernier bulletin) et, sous seed.lettres,
    la lettre « agence » de chaque bulletin fige, par numero."""
    instantanes = _instantanes()
    nums = sorted(instantanes)
    # Date de chaque lettre, pour la liste du pied (5 novembre 2026).
    _DATES.clear()
    _DATES.update({n: instantanes[n]["meta"].get("reportingDate") for n in nums})
    _NATIONAL.clear()
    _NATIONAL.update({n: instantanes[n].get("national") for n in nums})
    lettres, seeds = {}, {}
    for i, num in enumerate(nums):
        prec_date = instantanes[nums[i - 1]]["meta"]["reportingDate"] if i else None
        s = _lettre(instantanes[num], nums[i - 1] if i else None, nums[i + 1] if i + 1 < len(nums) else None, nums,
                    lang, S, i18n_lang, fmt, fmt_decimal, fmt_cfr, long_date, esc, interp, province_forms, couleurs, urls, prec_date)
        lettres[num] = s["seed.bulletinAgence"]
        seeds = s
    seeds["seed.lettres"] = lettres
    return seeds


# Premiere lettre avec les cases gueris et en CTE (19 octobre 2026) :
# celle-ci et toutes les suivantes, pas les anciennes.
UNE_GUERIS_CTE_DEPUIS = 156
# Premiere lettre ou la phrase des points de controle dit aussi les alertes
# et les corps interceptes aux postes (26 octobre 2026, data/points-controle.json).
POE_ALERTES_DEPUIS = 163
# Style « fluide » de la Lettre (5 novembre 2026, demande de Fable) : dates en
# toutes lettres sans annee, moyennes a l'unite, un verbe qui donne le sens,
# phrases reliees, un paragraphe par sujet. A partir de cette lettre ; les
# lettres deja publiees gardent leurs tournures.
STYLE_FLUIDE_DEPUIS = 174


def _abonnement(lang, S, esc):
    """Encadre « Recevoir la Lettre par mail » sous l'en-tete (19 octobre
    2026) : formulaire Brevo redessine, poste par app.js (form[data-brevo]).
    Rien dans une langue sans formulaire (site.brevoLettre)."""
    action = (_lire("site/pages.json")["site"].get("brevoLettre") or {}).get(lang)
    if not action:
        return ""
    return ('<form class="lq-abo" id="abonnement" data-brevo method="POST" action="%s">'
            '<div class="lq-abo-t"><b>%s</b></div>'
            '<div class="lq-abo-f"><div class="al-ligne"><input name="EMAIL" type="email" required placeholder="%s" autocomplete="email" aria-label="%s">'
            '<button type="submit" data-sending="%s">%s</button></div>'
            '<label class="al-consent"><input type="checkbox" name="OPT_IN" value="1" required> <span>%s</span></label>'
            '<input type="text" name="email_address_check" value="" class="al-leurre" tabindex="-1" autocomplete="off" aria-hidden="true">'
            '<input type="hidden" name="locale" value="%s">'
            '<p class="al-msg al-ok" role="status" hidden>%s</p><p class="al-msg al-err" role="alert" hidden>%s</p></div></form>'
            % (esc(action), esc(S["lettreAboTitre"]), esc(S["alertesPlaceholder"]), esc(S["alertesLabel"]),
               esc(S["alertesSending"]), esc(S["alertesSubmit"]), esc(S["lettreAboConsentement"]), "fr" if lang == "fr" else "en",
               esc(S["lettreAboSucces"]), esc(S["alertesError"])))


def _lettre(latest, prec_num, suiv_num, nums, lang, S, i18n_lang, fmt, fmt_decimal, fmt_cfr, long_date, esc, interp,
            province_forms, couleurs, urls, prec_date=None):
    meta, nat = latest["meta"], latest["national"]
    num, date = meta["sitrepNumber"], meta["reportingDate"]
    serie = sorted([s for s in _lire("data/sitreps.json") if s.get("date")], key=lambda s: s["date"])
    veille = next((s for s in reversed(serie) if s["date"] < date), None)
    # Cumuls anterieurs a une harmonisation remis sur sa base : les ecarts
    # par zone et les zones actives ne comptent que les nouveaux cas.
    zh = harmonisations.rebaser(_lire("data/zones-history.json"), date)
    alertes, labo = _lire("data/alertes.json"), _lire("data/laboratoire.json")
    contacts, cte = _lire("data/contacts-followup.json"), _lire("data/cte.json")
    deces, defis = _lire("data/deces-lieu.json"), _lire("data/defis.json")
    piliers_data = _lire("data/piliers.json") if os.path.exists(os.path.join(ROOT, "data", "piliers.json")) else None
    poe_data = _lire("data/points-controle.json") if os.path.exists(os.path.join(ROOT, "data", "points-controle.json")) else None
    notes = _lire("data/bulletin-notes.json") if os.path.exists(os.path.join(ROOT, "data", "bulletin-notes.json")) else {}
    index = _lire("reports/_index.json") if os.path.exists(os.path.join(ROOT, "reports", "_index.json")) else {}
    fiche_pdf = index.get(num, {})
    et = S["timelineListAnd"]
    P = lambda _cle, **v: interp(S[_cle], dict(v))
    def maj(phrase):
        """Majuscule initiale d'une phrase qui commence par un nom de province
        avec son article (« l'Ituri » -> « L'Ituri », « le Nord-Kivu » -> « Le Nord-Kivu »)."""
        return phrase[:1].upper() + phrase[1:] if phrase else phrase
    pct = lambda v: (fmt_decimal(v, lang) + " %") if v is not None else "—"
    plus = lambda v: ("+" + fmt(v, lang)) if v is not None else "—"
    forms = lambda nom: province_forms(config_prov, nom, lang)
    config_prov = _lire("site/pages.json")

    def kpi(cls, label, valeur, sub):
        return ('      <div class="kpi %s"><div class="label">%s</div><div class="value">%s</div><div class="delta">%s</div></div>\n'
                % (cls, esc(label), esc(valeur), esc(sub)))
    chapitres = []   # (ident, numero, titre, prose html, chiffres html)
    def cadre(n, titre, sub, corps, ident, prose_html="", chiffres_html=""):
        chapitres.append((ident, n, titre, prose_html, chiffres_html))
        return ('  <section class="section cadre-fiche" id="%s">\n'
                '    <div class="fiche-tete"><span class="fiche-num">%s</span><div><h2 class="frame-title">%s</h2>'
                '%s</div></div>\n    <div class="cadre-corps">\n%s    </div>\n  </section>\n'
                % (ident, n, esc(titre), ('<div class="section-sub">%s</div>' % esc(sub)) if sub else "", corps))
    def prose(txt):
        # Paragraphes separes par une ligne vide (style fluide, 5 novembre 2026).
        return "".join('    <p class="fiche-texte lettre-texte">%s</p>\n' % t.strip()
                       for t in txt.split("\n\n") if t.strip())
    FL = num.isdigit() and int(num) >= STYLE_FLUIDE_DEPUIS
    mois_noms = S["lettreMoisNoms"].split(",")
    def jour_mois(d):
        """« 3 novembre » (style fluide) : l'annee seulement si elle differe
        de celle du bulletin."""
        if not FL or not d:
            return long_date(d, i18n_lang)
        t = "%d %s" % (int(d[8:10]), mois_noms[int(d[5:7]) - 1].lower() if lang == "fr" else mois_noms[int(d[5:7]) - 1])
        return t + (" " + d[:4] if d[:4] != date[:4] else "")
    petits = S["lettrePetitsNombres"].split(",")
    def nb(n):
        """Petit nombre en toutes lettres (style fluide) : « cinq zones »."""
        # Vide en swahili : le nombre s'y accorde avec le nom (« majimbo matano »).
        return petits[n] if FL and len(petits) > 1 and isinstance(n, int) and 0 <= n < len(petits) else fmt(n, lang)
    if FL:
        pct = lambda v: (fmt_decimal(v, lang).replace(",0", "").replace(".0", "") + "\u202f%") if v is not None else "—"
    non_publie = []
    html = []

    # ---------------------------------------------------------------- zones nouvelles
    nouvelles = []
    zi = next((i for i, z in enumerate(zh) if z["date"] == date), None)
    if zi:
        avant = {_cle_zone(z) for z in zh[zi - 1]["zones"]}
        nouvelles = [z for z in zh[zi]["zones"] if _cle_zone(z) not in avant]
    # Date de la derniere zone nouvelle, pour ecrire « aucune nouvelle zone
    # depuis le ... » (8 septembre 2026).
    derniere_nouvelle = None
    for i in range(1, (zi or 0) + 1):
        avant_i = {_cle_zone(z) for z in zh[i - 1]["zones"]}
        if any(_cle_zone(z) not in avant_i for z in zh[i]["zones"]):
            derniere_nouvelle = zh[i]["date"]
    # Tendance : moyenne par jour des sept derniers jours et des sept
    # precedents, calculee sur les cumuls aux dates les plus proches (les
    # bulletins ne sont pas tous quotidiens).
    def _cumul_avant(jours):
        from datetime import date as _d, timedelta
        y, m, d = (int(x) for x in date.split("-"))
        cible = (_d(y, m, d) - timedelta(days=jours)).isoformat()
        return next((s for s in reversed(serie) if s["date"] <= cible), None)
    s0 = next((s for s in serie if s["date"] == date), None)
    s7, s14 = _cumul_avant(7), _cumul_avant(14)
    def _moy(a, b, cle):
        if not (a and b and a.get(cle) is not None and b.get(cle) is not None):
            return None
        from datetime import date as _d
        ja = _d(*(int(x) for x in a["date"].split("-"))); jb = _d(*(int(x) for x in b["date"].split("-")))
        n = (ja - jb).days
        # Les deces entres par harmonisation n'appartiennent a aucune journee.
        hors = harmonisations.deces_entre(b["date"], a["date"]) if cle == "deaths" else 0
        return (a[cle] - b[cle] - hors) / float(n) if n > 0 else None
    moy_cas, moy_cas_prec = _moy(s0, s7, "confirmed"), _moy(s7, s14, "confirmed")
    moy_dec, moy_dec_prec = _moy(s0, s7, "deaths"), _moy(s7, s14, "deaths")
    un_dec = lambda v: fmt_decimal(round(v, 1), lang) if v is not None else "—"
    zt = nat.get("healthZonesAffected") or {}
    nb_prov = nat.get("provincesAffected") or len(latest["provinces"])
    if nouvelles:
        zones_phrase = P("lettreZonesNew" if len(nouvelles) == 1 else "lettreZonesNewPl", n=fmt(len(nouvelles), lang), zones=_liste(["%s (%s)" % (z["name"], z["province"]) for z in nouvelles], et))
    else:
        zones_phrase = S["lettreZonesNone"]

    # ---------------------------------------------------------------- en-tete : objet + jour en une phrase
    objet = P("lettreObjet", date=long_date(date, i18n_lang), cas=fmt(nat.get("newCases24h"), lang), deces=fmt(nat.get("newDeaths24h"), lang), zones=zones_phrase)
    if FL:
        pub = meta.get("publicationDate") or date
        ecart_pub = _nb_jours(date, pub) if pub != date else 0
        publie = (S["lettrePublieMemeJour"] if ecart_pub == 0 else S["lettrePublieLendemain"] if ecart_pub == 1
                  else P("lettrePublieLe", date=jour_mois(pub)))
        jour = P("lettreJourF", rapport=jour_mois(date), publie=publie,
                 cas=fmt(nat.get("newCases24h"), lang), deces=fmt(nat.get("newDeaths24h"), lang))
        if moy_cas is not None and nat.get("newCases24h") is not None:
            m_ = round(moy_cas); n_ = nat["newCases24h"]
            if n_ == m_:
                cle = "lettreNiveauEgalF"
            else:
                r = n_ / moy_cas if moy_cas else 2
                cle = ("lettreNiveauPlusF" if r > 1.1 else "lettreNiveauUnPeuPlusF" if n_ > m_ else
                       "lettreNiveauMoinsF" if r < 0.9 else "lettreNiveauUnPeuMoinsF")
            jour += " " + P(cle, moy=fmt(m_, lang))
        if nouvelles:
            jour += " " + P("lettreZonesNewF" if len(nouvelles) == 1 else "lettreZonesNewPlF",
                            zones=_liste(["%s (%s)" % (z["name"], z["province"]) for z in nouvelles], et),
                            n=fmt(zt.get("n"), lang), prov=fmt(nb_prov, lang))
        elif derniere_nouvelle:
            jour += " " + P("lettreZonesDepuisF", date=jour_mois(derniere_nouvelle), n=fmt(zt.get("n"), lang), prov=fmt(nb_prov, lang))
        else:
            jour += " " + P("lettreZonesNoneF", n=fmt(zt.get("n"), lang), prov=fmt(nb_prov, lang))
    else:
        jour = P("lettreJour", rapport=long_date(date, i18n_lang), publie=long_date(meta.get("publicationDate") or date, i18n_lang),
                 cas=fmt(nat.get("newCases24h"), lang), deces=fmt(nat.get("newDeaths24h"), lang))
    if not FL and moy_cas is not None and nat.get("newCases24h") is not None:
        r = nat["newCases24h"] / moy_cas if moy_cas else None
        cle = "lettreJourNiveauMoyen" if r is None else ("lettreJourNiveauHaut" if r > 1.1 else "lettreJourNiveauBas" if r < 0.9 else "lettreJourNiveauMoyen")
        jour += " " + P(cle, cas=fmt(nat["newCases24h"], lang), moy=un_dec(moy_cas))
    if FL:
        pass
    elif nouvelles:
        jour += " " + P("lettreJourZonesNew", zones=zones_phrase, n=fmt(zt.get("n"), lang), prov=fmt(nb_prov, lang))
    elif derniere_nouvelle:
        jour += " " + P("lettreJourZonesDepuis", date=long_date(derniere_nouvelle, i18n_lang), n=fmt(zt.get("n"), lang), prov=fmt(nb_prov, lang))
    else:
        jour += " " + P("lettreJourZonesNone", n=fmt(zt.get("n"), lang), prov=fmt(nb_prov, lang))
    sous_titre = P("bulSousTitre", date=long_date(date, i18n_lang), num=num)
    pdf = ""
    if fiche_pdf.get("file"):
        pdf = '<a href="/%s" rel="noopener">%s</a>' % (esc(fiche_pdf["file"]), esc(S["bulPdf"]))
        # Le lien « La page de l'INSP » a ete retire le 8 septembre 2026 ; seul le PDF reste.
    # ---------------------------------------------------------------- 01 le bilan
    gueris_delta = (nat.get("recovered") - veille.get("recovered")) if (veille and veille.get("recovered") is not None and nat.get("recovered") is not None) else None
    if FL:
        cfr_v = nat.get("cfr") or 0
        letal = P("lettreLetalPresF" if 45 <= cfr_v < 50 else "lettreLetalPlusF" if 50 < cfr_v <= 55 else "lettreLetalF",
                  cfr=fmt_cfr(nat.get("cfr"), lang))
        txt = P("lettreBilanF", cas=fmt(nat.get("confirmed"), lang), deces=fmt(nat.get("deaths"), lang), letal=letal)
    else:
        txt = P("lettreBilan", cas=fmt(nat.get("confirmed"), lang), deces=fmt(nat.get("deaths"), lang), cfr=fmt_cfr(nat.get("cfr"), lang), gueris=fmt(nat.get("recovered"), lang))
    if not FL and gueris_delta is not None and gueris_delta > 0:
        txt += " " + P("lettreBilanGueris", n=fmt(gueris_delta, lang))
    harm = harmonisations.charger().get(date)
    if harm:
        # Un retrait (SitRep 170 : les 314 du 169 sortent du total) a sa phrase.
        cle = "lettreBilanHarmonisationRetrait" if harm["deces"] < 0 else "lettreBilanHarmonisation"
        txt += " " + maj(P(cle, the=forms(harm["province"])["the"], n=fmt(abs(harm["deces"]), lang), jour=fmt(harm["decesJour"], lang)))
    if FL:
        # Gueris et malades en CTE dans une seule phrase.
        if nat.get("recovered") is not None:
            g = P("lettreGuerisF", gueris=fmt(nat.get("recovered"), lang))
            dont = gueris_delta is not None and gueris_delta > 0
            if dont:
                g += P("lettreGuerisDontF", n=fmt(gueris_delta, lang))
            if nat.get("inCTE") is not None:
                g = g + (", " if dont else " ") + P("lettreCteEtF", n=fmt(nat.get("inCTE"), lang))
            txt += " " + g.rstrip(",") + "."
        elif nat.get("inCTE") is not None:
            txt += " " + P("lettreCteSeulF", n=fmt(nat.get("inCTE"), lang))
        if None not in (moy_cas, moy_cas_prec, moy_dec, moy_dec_prec):
            mc, mcp, md, mdp = (round(v) for v in (moy_cas, moy_cas_prec, moy_dec, moy_dec_prec))
            if mc == mcp and md == mdp:
                txt += " " + P("lettreTendanceStableF", cas=fmt(mc, lang), deces=fmt(md, lang))
            else:
                sc, sd = (mc > mcp) - (mc < mcp), (md > mdp) - (md < mdp)
                ecart = max(abs(moy_cas / moy_cas_prec - 1) if moy_cas_prec else 1, abs(moy_dec / moy_dec_prec - 1) if moy_dec_prec else 1)
                if sc <= 0 and sd <= 0:
                    v_ = "lettreVerdictBaisseLegF" if ecart < 0.1 else "lettreVerdictBaisseF"
                elif sc >= 0 and sd >= 0:
                    v_ = "lettreVerdictHausseLegF" if ecart < 0.1 else "lettreVerdictHausseF"
                else:
                    v_ = "lettreVerdictCasBasDecesHautF" if sc < 0 else "lettreVerdictCasHautDecesBasF"
                txt += " " + P("lettreTendanceF", verdict=S[v_], cas=fmt(mc, lang), deces=fmt(md, lang),
                               casPrec=fmt(mcp, lang), decesPrec=fmt(mdp, lang))
    elif nat.get("inCTE") is not None:
        txt += " " + P("lettreBilanCte", n=fmt(nat.get("inCTE"), lang))
    if not FL and None not in (moy_cas, moy_cas_prec, moy_dec, moy_dec_prec):
        txt += " " + P("lettreTendance", cas=un_dec(moy_cas), deces=un_dec(moy_dec), casPrec=un_dec(moy_cas_prec), decesPrec=un_dec(moy_dec_prec))
    corps = prose(esc(txt))
    corps += '    <section class="kpis kpis-riposte" aria-label="%s">\n' % esc(S["bulBilanTitle"])
    corps += kpi("confirmed", i18n_lang["labelConfirmed"], fmt(nat.get("confirmed"), lang), P("bulDelta", n=plus(nat.get("newCases24h"))))
    corps += kpi("deaths", i18n_lang["labelDeaths"], fmt(nat.get("deaths"), lang), P("bulDelta", n=plus(nat.get("newDeaths24h"))))
    corps += kpi("recovered", i18n_lang["labelRecovered"], fmt(nat.get("recovered"), lang), P("bulDelta", n=plus(gueris_delta)) if gueris_delta is not None else "")
    corps += kpi("cte", i18n_lang["labelIsolation"], fmt(nat.get("inCTE"), lang), "")
    corps += kpi("cfr", i18n_lang["labelCfr"], fmt_cfr(nat.get("cfr"), lang), "")
    corps += kpi("zones", S["bulZonesLabel"], fmt(zt.get("n"), lang), P("bulZonesOf", total=fmt(zt.get("total"), lang)))
    corps += '    </section>\n'
    html.append(cadre("01", S["bulBilanTitle"], "", corps, "bilan", prose(esc(txt)), corps[len(prose(esc(txt))):]))

    # ---------------------------------------------------------------- 02 ou
    provs = sorted(latest["provinces"], key=lambda p: -(p.get("newCases24h") or 0))
    avec = [p for p in provs if (p.get("newCases24h") or 0) > 0]
    sans = [p for p in provs if not (p.get("newCases24h") or 0)]
    if FL and avec:
        premiere = avec[0]; tot = nat.get("newCases24h") or sum(p["newCases24h"] for p in avec)
        f0 = forms(premiere["name"])
        if len(avec) == 1:
            txt = P("lettreOuSeulF", **{"in": f0["in"]}) if tot == 1 else P("lettreOuTousF", total=fmt(tot, lang), **{"in": f0["in"]})
        elif avec[1]["newCases24h"] == premiere["newCases24h"]:
            # Egalite en tete (5 novembre 2026) : pas de « premiere », une liste.
            txt = P("lettreOuRepartitionF", total=fmt(tot, lang),
                    liste=_liste([P("lettreOuItemF", the=forms(p["name"])["the"], n=fmt(p["newCases24h"], lang)) for p in avec], et))
        else:
            part = premiere["newCases24h"] * 2
            cle = "lettreOuMoitiePlusF" if part > tot else "lettreOuMoitieF" if part == tot else "lettreOuPlusF"
            txt = maj(P(cle, the=f0["the"], n=fmt(premiere["newCases24h"], lang), total=fmt(tot, lang)))
            txt += " " + P("lettreOuSuiteF" if len(avec) > 2 else "lettreOuSuiteUneF",
                           liste=_liste([P("lettreOuItemF", the=forms(p["name"])["the"], n=fmt(p["newCases24h"], lang)) for p in avec[1:]], et))
    elif avec:
        premiere = avec[0]
        txt = maj(P("lettreOuPremiere", the=forms(premiere["name"])["the"], n=fmt(premiere["newCases24h"], lang), total=fmt(nat.get("newCases24h"), lang)))
        if len(avec) > 1:
            txt += " " + P("lettreOuSuite", liste=_liste([P("lettreOuItem", the=forms(p["name"])["the"], n=fmt(p["newCases24h"], lang)) for p in avec[1:]], et))
    else:
        txt = S["lettreOuAucun"]
    if sans and avec:
        txt += " " + ((P("lettreOuSansPlusieursF", n=nb(len(sans))) if FL else P("lettreOuSansPlusieurs", n=fmt(len(sans), lang))) if len(sans) > 1
                      else maj(P("lettreOuSansUne", the=forms(sans[0]["name"])["the"])))
    actives = sorted([z for z in latest["healthZones"] if (z.get("newCases24h") or 0) > 0], key=lambda z: -(z.get("newCases24h") or 0))[:5]
    if FL and actives and nat.get("newCases24h"):
        somme = sum(z["newCases24h"] for z in actives)
        tot = nat["newCases24h"]
        if len(actives) == 1:
            z = actives[0]
            txt += "\n\n" + (P("lettreOuZoneSeuleF", zone=z["name"]) if z["newCases24h"] >= tot
                              else P("lettreOuZoneUneF", zone=z["name"], n=fmt(z["newCases24h"], lang)))
        elif actives[1]["newCases24h"] == actives[0]["newCases24h"]:
            txt += "\n\n" + maj(P("lettreOuZonesToutesListeF" if somme >= tot else "lettreOuZonesListeF", k=nb(len(actives)),
                                    somme=fmt(somme, lang),
                                    liste=_liste([P("lettreOuZoneItemF", zone=z["name"], n=fmt(z["newCases24h"], lang)) for z in actives], et)))
        else:
            txt += "\n\n" + maj(P("lettreOuZonesToutesF" if somme >= tot else "lettreOuZonesF", k=nb(len(actives)),
                                somme=fmt(somme, lang), premiere=actives[0]["name"], n1=fmt(actives[0]["newCases24h"], lang),
                                liste=_liste([P("lettreOuZoneItemF", zone=z["name"], n=fmt(z["newCases24h"], lang)) for z in actives[1:]], et)))
    elif actives and nat.get("newCases24h"):
        somme = sum(z["newCases24h"] for z in actives)
        txt += " " + P("lettreOuZones", k=fmt(len(actives), lang), somme=fmt(somme, lang), total=fmt(nat["newCases24h"], lang),
                       liste=_liste(["%s %s" % (z["name"], fmt(z["newCases24h"], lang)) for z in actives], et))
    # Ecart entre cumuls et nouveaux cas annonces (24 octobre 2026, choix du
    # proprietaire) : au SitRep 160, le cumul de Beni recule de 553 a 552
    # malgre 9 nouveaux cas annonces. Le site ne corrige pas la source, il le
    # dit. Seulement si le bulletin precedent est celui de la veille, sinon
    # l'ecart couvre plusieurs jours et ne se compare pas a un chiffre du jour.
    # A partir du SitRep 160 seulement : les lettres deja publiees ne changent
    # pas (090, 103 et 151 auraient recu une note, sans relecture des PDF).
    ajouts, k_ajouts = [], 0
    if zi and date >= "2026-10-21":
        from datetime import date as _d0
        j0, j1 = (_d0(*(int(x) for x in zh[k]["date"].split("-"))) for k in (zi - 1, zi))
        if (j1 - j0).days == 1:
            avant = {_cle_zone(z): z.get("cases") for z in zh[zi - 1]["zones"]}
            paires = reclassements(latest["healthZones"], avant, date)
            for z in latest["healthZones"]:
                a, n = avant.get(_cle_zone(z)), z.get("newCases24h") or 0
                if z.get("cases") is None:
                    continue
                if _cle_zone(z) in paires:
                    pr = paires[_cle_zone(z)]
                    if pr:
                        (zp, ap, ep), (zm, am, _) = pr
                        txt += " " + P("lettreOuEcartPaire", zone=zp["name"], avant=fmt(ap, lang), apres=fmt(zp["cases"], lang),
                                       n=fmt(zp.get("newCases24h") or 0, lang), ecart=fmt(ep, lang),
                                       zone2=zm["name"], avant2=fmt(am, lang), apres2=fmt(zm["cases"], lang))
                    continue
                if a is not None and z["cases"] - a != n and z["cases"] < a + n:
                    cle = ("lettreOuEcartSans" if n == 0 else
                           "lettreOuEcartReste" if z["cases"] == a else "lettreOuEcart")
                    txt += " " + P(cle, zone=z["name"], avant=fmt(a, lang), apres=fmt(z["cases"], lang), n=fmt(n, lang))
                # Cumul qui monte plus que les nouveaux cas annonces (30 octobre
                # 2026, choix du proprietaire) : au SitRep 167, Yakoma entre
                # avec 3 cas, 0 annonce ; le total du pays les compte, le
                # chiffre des 24 heures non.
                elif z["cases"] > (a or 0) + n:
                    cle = ("lettreOuEcartNouvelle" if a is None else
                           "lettreOuEcartAjout" if n == 0 else "lettreOuEcart")
                    txt += " " + P(cle, zone=z["name"], avant=fmt(a or 0, lang), apres=fmt(z["cases"], lang), n=fmt(n, lang),
                                   ecart=fmt(z["cases"] - (a or 0) - n, lang))
                    k_ajouts += z["cases"] - (a or 0) - n
                    ajouts.append(P("lettreTableauEcartItem", n=fmt(z["cases"] - (a or 0) - n, lang), zone=z["name"], province=z["province"]))
    # Zones actives : au moins un cas notifie dans les 21 derniers jours,
    # d'apres les cumuls par zone de l'instantane le plus proche 21 jours
    # avant (8 septembre 2026).
    if zi is not None:
        from datetime import date as _d, timedelta
        cible = (_d(*(int(x) for x in date.split("-"))) - timedelta(days=21)).isoformat()
        z21 = next((z for z in reversed(zh[:zi]) if z["date"] <= cible), None)
        if z21:
            avant21 = {_cle_zone(z): z.get("cases") or 0 for z in z21["zones"]}
            zones_now = zh[zi]["zones"]
            k = sum(1 for z in zones_now if (z.get("cases") or 0) > avant21.get(_cle_zone(z), 0))
            n = len(zones_now)
            if FL:
                txt += (" " if "\n\n" in txt else "\n\n") + (
                    P("lettreZonesActivesToutesF", n=fmt(n, lang)) if k == n else
                    P("lettreZonesActivesUneF", k=fmt(k, lang), n=fmt(n, lang)) if n - k == 1 else
                    P("lettreZonesActivesF", k=fmt(k, lang), n=fmt(n, lang), s=fmt(n - k, lang)))
            else:
                txt += " " + (P("lettreZonesActivesToutes", n=fmt(n, lang)) if k == n
                              else P("lettreZonesActives", k=fmt(k, lang), n=fmt(n, lang), s=fmt(n - k, lang)))
    corps = prose(esc(txt))
    lignes = ""
    for p in provs:
        nom = p["name"]; zi = p.get("healthZonesAffected") or {}
        dj = (p.get("newDeathsCommunity24h") or 0) + (p.get("newDeathsIntraCTE24h") or 0)
        lignes += ('        <tr><td><a href="%s"><span class="dot" style="background:%s;"></span>%s</a></td>'
                   '<td class="is-num">%s</td><td class="is-num">%s</td><td class="is-num">%s</td><td class="is-num">%s</td><td class="is-num">%s</td></tr>\n'
                   % (urls.province_path(nom, lang), couleurs.get(nom, "var(--ink-faint)"), esc(nom),
                      plus(p.get("newCases24h")), plus(dj), fmt(p.get("confirmed"), lang), fmt(p.get("deaths"), lang),
                      "%s/%s" % (fmt(zi.get("n"), lang), fmt(zi.get("total"), lang)) if zi else "—"))
    corps += ('    <div class="panel panel-fit" style="padding:16px;"><table class="province-summary bul-table">\n'
              '      <thead><tr><th>%s</th><th class="is-num">%s</th><th class="is-num">%s</th><th class="is-num">%s</th><th class="is-num">%s</th><th class="is-num">%s</th></tr></thead>\n'
              '      <tbody>\n%s      </tbody></table>%s</div>\n'
              % (esc(S["bulThProvince"]), esc(S["bulThNewCases"]), esc(S["bulThNewDeaths"]), esc(i18n_lang["labelConfirmed"]), esc(i18n_lang["labelDeaths"]), esc(S["bulThZones"]), lignes,
                 # Note sous le tableau quand un cumul monte sans nouveaux cas
                 # annonces (30 octobre 2026, SitRep 167, Yakoma) : la colonne
                 # « Nouveaux cas » ne s'additionne plus a l'ecart des cumuls.
                 '\n      <p class="map-note zones-note">%s</p>' % esc(P("lettreTableauEcart", liste=_liste(ajouts, et), k=fmt(k_ajouts, lang),
                     n=fmt(nat.get("newCases24h"), lang), delta=fmt(nat["confirmed"] - veille["confirmed"], lang)))
                 if ajouts and veille and veille.get("confirmed") is not None and nat.get("confirmed") is not None else ""))
    corps += '    <p class="drill"><a href="%s">%s</a></p>\n' % (urls.path("donnees", lang), esc(S["lettreDonneesLien"]))
    html.append(cadre("02", S["lettreOuTitle"], "", corps, "ou", prose(esc(txt)), corps[len(prose(esc(txt))):]))

    # ---------------------------------------------------------------- 03 les deces
    d_comm, d_cte = nat.get("newDeathsCommunity24h"), nat.get("newDeathsIntraCTE24h")
    if FL and d_comm is not None and d_cte is not None:
        tot = nat.get("newDeaths24h") or (d_comm + d_cte)
        def _lst(cle_n):
            ps = sorted([p for p in provs if (p.get(cle_n) or 0) > 0], key=lambda p: -p[cle_n])
            if not ps:
                return ""
            return (" : " if lang == "fr" else ": ") + _liste([P("lettreDecesItem", n=fmt(p[cle_n], lang), the=forms(p["name"])["the"], **{"in": forms(p["name"])["in"]}) for p in ps], et)
        lc, lt = _lst("newDeathsCommunity24h"), _lst("newDeathsIntraCTE24h")
        if not tot:
            txt = S["lettreDecesAucunF"]
        elif d_cte == 0:
            txt = P("lettreDecesSeulCommF" if tot == 1 else "lettreDecesToutCommF", total=fmt(tot, lang), liste=lc)
        elif d_comm == 0:
            txt = P("lettreDecesSeulCteF" if tot == 1 else "lettreDecesToutCteF", total=fmt(tot, lang), liste=lt)
        else:
            txt = P("lettreDecesComm1F" if d_comm == 1 else "lettreDecesCommF", total=fmt(tot, lang), comm=fmt(d_comm, lang), liste=lc)
            txt += " " + P("lettreDecesCteAutre1F" if d_cte == 1 else "lettreDecesCteAutresF", cte=fmt(d_cte, lang), liste=lt)
        cte_prov = sorted([p for p in provs if (p.get("newDeathsIntraCTE24h") or 0) > 0], key=lambda p: -p["newDeathsIntraCTE24h"])
        for p in cte_prov:
            zones_p = [z for z in latest["healthZones"] if z.get("province") == p["name"]]
            if zones_p and sum(z.get("deathsIntraCTE24h") or 0 for z in zones_p) == 0:
                ecart = (p.get("deaths") or 0) - sum(z.get("deaths") or 0 for z in zones_p)
                if ecart > 0:
                    txt += " " + P("lettreDecesVentiler", n=fmt(p["newDeathsIntraCTE24h"], lang), of=forms(p["name"])["of"], **{"in": forms(p["name"])["in"]}, total=fmt(ecart - p["newDeathsIntraCTE24h"], lang))
    elif d_comm is not None and d_cte is not None:
        txt = P("lettreDeces", total=fmt(nat.get("newDeaths24h"), lang), comm=fmt(d_comm, lang), cte=fmt(d_cte, lang))
        # Les deces communautaires, province par province, du plus au moins
        # touche (demande du 8 septembre 2026).
        comm_prov = sorted([p for p in provs if (p.get("newDeathsCommunity24h") or 0) > 0], key=lambda p: -p["newDeathsCommunity24h"])
        if comm_prov and d_comm:
            txt += " " + P("lettreDecesCommProv", liste=_liste([P("lettreDecesItem", n=fmt(p["newDeathsCommunity24h"], lang), the=forms(p["name"])["the"], **{"in": forms(p["name"])["in"]}) for p in comm_prov], et))
        cte_prov = sorted([p for p in provs if (p.get("newDeathsIntraCTE24h") or 0) > 0], key=lambda p: -p["newDeathsIntraCTE24h"])
        if cte_prov and d_cte:
            txt += " " + P("lettreDecesCteProv", liste=_liste([P("lettreDecesItem", n=fmt(p["newDeathsIntraCTE24h"], lang), the=forms(p["name"])["the"], **{"in": forms(p["name"])["in"]}) for p in cte_prov], et))
        # « a ventiler » : des deces intra-CTE de province qu'aucune zone ne porte
        for p in cte_prov:
            zones_p = [z for z in latest["healthZones"] if z.get("province") == p["name"]]
            if zones_p and sum(z.get("deathsIntraCTE24h") or 0 for z in zones_p) == 0:
                ecart = (p.get("deaths") or 0) - sum(z.get("deaths") or 0 for z in zones_p)
                if ecart > 0:
                    txt += " " + P("lettreDecesVentiler", n=fmt(p["newDeathsIntraCTE24h"], lang), of=forms(p["name"])["of"], **{"in": forms(p["name"])["in"]}, total=fmt(ecart - p["newDeathsIntraCTE24h"], lang))
    else:
        txt = P("lettreDecesSansLieu", total=fmt(nat.get("newDeaths24h"), lang)); non_publie.append(S["bulDecesTitle"])
    html.append(cadre("03", S["lettreDecesTitle"], "", prose(esc(txt)), "deces", prose(esc(txt)), ""))

    # ---------------------------------------------------------------- 04 la riposte
    pa, pl, pc, pk = _point(alertes, date), _point(labo, date), _point(contacts, date, None), _point(cte, date)
    phrases, cases = [], ""
    if pa and (pa.get("total") or {}).get("recues") is not None:
        t = pa["total"]
        muets = [nom for nom, v in (pa.get("provinces") or {}).items() if not (v.get("recues") or 0) and v.get("suspectsInvestigues") is None]
        if FL:
            s1 = P("lettreAlertesTousF" if t.get("verifiees") == t["recues"] else "lettreAlertesF", recues=fmt(t["recues"], lang),
                   verifiees=fmt(t.get("verifiees"), lang), validees=fmt(t.get("validees"), lang))
        else:
            s1 = P("lettreAlertes", recues=fmt(t["recues"], lang), verifiees=fmt(t.get("verifiees"), lang), validees=fmt(t.get("validees"), lang))
        if muets:
            # Deux provinces muettes depuis l'arrivee du Nord-Ubangi (155) : le
            # verbe s'accorde (« le Sud-Ubangi et le Nord-Ubangi n'ont pas »).
            cle_muet = "lettreAlertesMuetPl" if len(muets) > 1 else "lettreAlertesMuet"
            s1 += " " + maj(P(cle_muet, liste=_liste([forms(m)["the"] for m in muets], et)))
        phrases.append(s1)
        cases += kpi("alerts", S["lettreKpiAlertes"], fmt(t["recues"], lang), P("lettreKpiAlertesSub", verifiees=fmt(t.get("verifiees"), lang), validees=fmt(t.get("validees"), lang)))
    else:
        cases += kpi("alerts", S["lettreKpiAlertes"], "—", S["riposteKpiNone"]); non_publie.append(S["lettreKpiAlertes"])
    # La phrase nationale prime sur la somme des provinces, comme sur la page
    # Riposte : du 6 au 11 octobre, elle est le seul total du bulletin.
    nl = (pl or {}).get("national") or {}
    if nl.get("echantillons") and nl.get("positifs") is not None:
        pl = dict(pl, total=dict(pl.get("total") or {}, **nl))
    if pl and (pl.get("total") or {}).get("echantillons"):
        t = pl["total"]
        s2 = P("lettreLaboF" if FL else "lettreLabo", positifs=fmt(t.get("positifs"), lang), echantillons=fmt(t.get("echantillons"), lang), taux=pct(t.get("positivite")))
        haut = [(nom, v) for nom, v in (pl.get("provinces") or {}).items() if (v.get("echantillons") or 0) >= 20 and v.get("positivite") is not None]
        if haut:
            nom, v = max(haut, key=lambda x: x[1]["positivite"])
            if v["positivite"] > (t.get("positivite") or 0) + 5:
                s2 += " " + P("lettreLaboHaut", the=forms(nom)["the"], taux=pct(v["positivite"]), **{"in": forms(nom)["in"]})
        phrases.append(s2)
        cases += kpi("labo", S["lettreKpiLabo"], pct(t.get("positivite")), P("lettreKpiLaboSub", positifs=fmt(t.get("positifs"), lang), echantillons=fmt(t.get("echantillons"), lang)))
    else:
        cases += kpi("labo", S["lettreKpiLabo"], "—", S["riposteKpiNone"]); non_publie.append(S["lettreKpiLabo"])
    if pc and pc.get("contactsFollowUpRate") is not None:
        c = pc.get("contacts") or {}; taux = pc["contactsFollowUpRate"]
        # Plus de seuil dans la phrase (decision du proprietaire, 25 octobre
        # 2026) : le site disait « le seuil de 85 % que l'INSP s'est fixe »
        # quand les bulletins ecrivent « seuil requis de 95,0 % ».
        s3 = P("lettreContactsF" if FL else "lettreContacts", taux=pct(taux))
        bas = [nom for nom, v in (pc.get("provinces") or {}).items() if v.get("taux") is not None and v["taux"] < 75]
        if bas and FL:
            s3 += " " + (maj(P("lettreContactsBasUneF", **{"in": forms(bas[0])["in"]})) if len(bas) == 1
                         else P("lettreContactsBasF", liste=_liste([forms(b)["in"] for b in sorted(bas)], et)))
        elif bas:
            s3 += " " + P("lettreContactsBas", liste=_liste(sorted(bas), et))
        phrases.append(s3)
        cases += kpi("contacts", S["lettreKpiContacts"], pct(taux), P("lettreKpiContactsSub", vus=fmt(c.get("vus"), lang), aSuivre=fmt(c.get("aSuivre"), lang)) if c.get("vus") is not None else "")
    else:
        cases += kpi("contacts", S["lettreKpiContacts"], "—", S["riposteKpiNone"]); non_publie.append(S["lettreKpiContacts"])
    if pk and (pk.get("total") or {}).get("occupation") is not None:
        t = pk["total"]
        s4 = P("lettreCteF" if FL else "lettreCte", taux=fmt(round(t["occupation"]), lang), hospitalises=fmt(t.get("hospitalisesAvecLits") or t.get("hospitalises"), lang), lits=fmt(t.get("lits"), lang))
        satures = [(nom, v) for nom, v in (pk.get("provinces") or {}).items() if (v.get("occupation") or 0) > 100]
        if satures:
            # Une province saturee dont le bulletin ne donne pas les lits (le 117
            # ecrivait « 287/220 lits disponibles » avant que le motif soit lu)
            # est citee avec son taux plutot que de faire tomber la lettre.
            s4 += " " + P("lettreCteSature", liste=_liste([
                (P("lettreCteItem", the=forms(nom)["the"], hospitalises=fmt(v["hospitalises"], lang), lits=fmt(v["lits"], lang))
                 if v.get("lits") is not None else
                 P("lettreCteItemTaux", the=forms(nom)["the"], hospitalises=fmt(v["hospitalises"], lang), taux=fmt(round(v["occupation"]), lang)))
                for nom, v in satures], et))
        phrases.append(s4)
        cases += kpi("cte", S["lettreKpiCte"], fmt(round(t["occupation"]), lang), P("lettreKpiCteSub", hospitalises=fmt(t.get("hospitalisesAvecLits") or t.get("hospitalises"), lang), lits=fmt(t.get("lits"), lang)))
    else:
        cases += kpi("cte", S["lettreKpiCte"], "—", S["riposteKpiNone"]); non_publie.append(S["lettreKpiCte"])
    # Trois piliers lus depuis le 8 septembre 2026 (data/piliers.json) :
    # enterrements securises et rings, vaccination, points de controle.
    # Chaque phrase n'existe que si le bulletin donne le chiffre.
    pp = _point(piliers_data, date) if piliers_data else None
    if pp:
        rg, ed, va, po = pp.get("rings"), pp.get("eds"), pp.get("vaccination"), pp.get("poe")
        if ed and ed.get("alertes") is not None and ed.get("realisees") is not None:
            # Les trois nombres ne couvrent pas toujours les memes provinces :
            # au 111, seul l'Ituri publie ses signalements quand le Nord-Kivu
            # ne donne que ses enterrements, si bien que les EDS realises
            # depassent les deces signales sans que rien soit faux. Les aligner
            # dans une meme phrase, ou ecrire « N realises sur M signales »,
            # ferait lire un rapport qui n'existe pas (19 septembre 2026).
            couv = ed.get("provinces") or {}
            memes = len({couv.get(k) for k in ("alertes", "realisees", "swabes") if couv.get(k)}) <= 1
            cle = "lettreEds" if memes else "lettreEdsPartiel"
            s5 = P(cle, alertes=fmt(ed["alertes"], lang), realisees=fmt(ed["realisees"], lang), swabes=fmt(ed.get("swabes"), lang) if ed.get("swabes") is not None else "—")
            if ed.get("nonSwabes"):
                s5 += " " + P("lettreEdsRefus", n=fmt(ed["nonSwabes"], lang))
            phrases.append(s5)
            sous = (P("lettreKpiEdsSub", realisees=fmt(ed["realisees"], lang), alertes=fmt(ed["alertes"], lang))
                    if memes else P("lettreKpiEdsSubSeul", realisees=fmt(ed["realisees"], lang)))
            cases += kpi("eds", S["lettreKpiEds"], fmt(ed["realisees"], lang), sous)
        if rg and rg.get("attendus"):
            phrases.append(P("lettreRings", ouverts=fmt(rg.get("ouverts") or 0, lang), attendus=fmt(rg["attendus"], lang)))
        # Vaccination : le bulletin ne donne que des cumuls, par province ou
        # par zone (voir extract_piliers.lire_vaccination). On additionne le
        # dernier cumul connu de chaque province a la date de la lettre, en
        # datant ceux qui viennent d'un bulletin anterieur.
        connus, avant, debut = {}, {}, None
        # Dernier total national publie (choix de Fable, 7 octobre 2026) : il
        # l'emporte sur la somme des provinces tant que celle-ci ne le depasse
        # pas, pour qu'un total cumule ne baisse jamais.
        nat_vacc = None
        for e in piliers_data.get("parDate", []):
            if e["date"] > date:
                break
            if (e.get("vaccination") or {}).get("national") is not None:
                nat_vacc = (e["vaccination"]["national"], e["date"])
            for prov, v in ((e.get("vaccination") or {}).get("cumulParProvince") or {}).items():
                # Le cumul precedent de CETTE province, pour en tirer le chiffre
                # du jour : le bulletin ne publie jamais de vaccines du jour,
                # seulement des cumuls (demande du proprietaire, 21 septembre
                # 2026). Une province qui saute un bulletin donne un ecart qui
                # porte sur plusieurs jours, et la lettre le dit.
                if prov in connus and connus[prov][0] != v:
                    avant[prov] = connus[prov]
                elif prov in connus:
                    # Cumul inchange (« le cumul reste de 2 448 », Ituri, SitRep
                    # 171) : la journee n'ajoute rien. Sans cet oubli, l'ecart
                    # du bulletin d'avant (+233 le 31 oct.) reparaissait comme
                    # un ajout « en deux jours » (corrige le 3 novembre 2026).
                    avant.pop(prov, None)
                connus[prov] = (v, e["date"]); debut = debut or e["date"]
        if connus or (va and va.get("rupture")):
            s6 = ""
            if connus:
                items = []
                for prov, (v, d_) in sorted(connus.items(), key=lambda x: -x[1][0]):
                    f = forms(prov)
                    if d_ == date:
                        items.append(P("lettreVaccinItem", n=fmt(v, lang), the=f["the"], **{"in": f["in"]}))
                    else:
                        items.append(P("lettreVaccinItemDate", n=fmt(v, lang), the=f["the"], date=long_date(d_, i18n_lang), **{"in": f["in"]}))
                total = sum(v for v, _ in connus.values())
                if FL:
                    # Total, puis l'ajout du jour en une incise ; le detail par
                    # province (dont les chiffres anciens) reste sur la page Riposte.
                    neufs_f = []
                    for prov, (v, d_) in sorted(connus.items(), key=lambda x: -x[1][0]):
                        if prov in avant and d_ == date and v > avant[prov][0]:
                            neufs_f.append((prov, v - avant[prov][0], _nb_jours(avant[prov][1], d_)))
                    dont = ""
                    if neufs_f:
                        neufs_f.sort(key=lambda x: -x[1])
                        js = {j for _, _, j in neufs_f}
                        quand = (S["lettreVaccinVeilleF"] if js == {1} else
                                 P("lettreVaccinJoursF", jours=_jours_mot(next(iter(js)), lang, fmt)) if len(js) == 1 else S["lettreVaccinPrecF"])
                        ou = ((", " + forms(neufs_f[0][0])["in"]) if len(neufs_f) == 1 else
                              " (%s)" % _liste([P("lettreVaccinItem", n=fmt(n_, lang), the=forms(pv)["the"], **{"in": forms(pv)["in"]}) for pv, n_, _ in neufs_f], et))
                        dont = P("lettreVaccinDontF", n=fmt(sum(n_ for _, n_, _ in neufs_f), lang), quand=quand, ou=ou)
                    if nat_vacc and nat_vacc[0] > total:
                        total = nat_vacc[0]
                        s6 = P("lettreVaccinationNationalF", total=fmt(total, lang), debut=jour_mois(debut), date=jour_mois(nat_vacc[1]), dont=dont)
                    else:
                        s6 = P("lettreVaccinationF", total=fmt(total, lang), debut=jour_mois(debut), dont=dont)
                elif nat_vacc and nat_vacc[0] > total:
                    total = nat_vacc[0]
                    s6 = P("lettreVaccinationNational", total=fmt(total, lang), debut=long_date(debut, i18n_lang),
                           date=long_date(nat_vacc[1], i18n_lang), detail=_liste(items, et))
                else:
                    s6 = P("lettreVaccination", total=fmt(total, lang), debut=long_date(debut, i18n_lang), detail=_liste(items, et))
                cases += kpi("vaccin", S["lettreKpiVaccin"], fmt(total, lang), P("lettreKpiVaccinSub", date=long_date(debut, i18n_lang)))
                # Ce que la journee a ajoute, province par province.
                neufs = []
                for prov, (v, d_) in sorted(connus.items(), key=lambda x: -x[1][0]):
                    # Seulement les provinces qui publient un cumul NEUF ce
                    # jour-la : sinon le meme ecart reparait de lettre en
                    # lettre, le cumul etant reporte. Le Bas-Uele ne publie
                    # rien le 18 septembre, et ses 108 du 17 s'affichaient
                    # deux fois (corrige le 21 septembre 2026).
                    if prov not in avant or d_ != date:
                        continue
                    v0, d0 = avant[prov]
                    if v <= v0:
                        continue
                    f = forms(prov)
                    jours = _nb_jours(d0, d_)
                    if jours > 1:
                        neufs.append(P("lettreVaccinJourItemJours", n=fmt(v - v0, lang),
                                       jours=_jours_mot(jours, lang, fmt),
                                       the=f["the"], **{"in": f["in"]}))
                    else:
                        neufs.append(P("lettreVaccinJourItem", n=fmt(v - v0, lang),
                                       the=f["the"], **{"in": f["in"]}))
                if neufs and not FL:
                    s6 += " " + P("lettreVaccinationJour", detail=_liste(neufs, et))
            if va and va.get("rupture"):
                s6 = (s6 + " " if s6 else "") + S["lettreVaccinationRupture"]
            phrases.append(s6)
        if po and po.get("personnes") is not None and po.get("screenesPct") is not None:
            s7 = P("lettrePoeF" if FL else "lettrePoe", personnes=fmt(po["personnes"], lang), pct=pct(po["screenesPct"]))
            if po.get("refusScreening"):
                s7 += " " + P("lettrePoeRefus", n=fmt(po["refusScreening"], lang))
            # Les alertes et les corps interceptes aux postes, lus dans le
            # tableau PoE/PoC du bulletin ; la province qui fait au moins la
            # moitie des alertes est nommee (13 sur 18 au Bas-Uele le 24 oct.).
            pp = _point(poe_data, date) if (poe_data and num.isdigit() and int(num) >= POE_ALERTES_DEPUIS) else None
            if pp and pp.get("date") == date:
                ind = pp.get("indicateurs") or {}
                lu = lambda cle, col="Global": (ind.get(cle) or {}).get(col, {}).get("valeur")
                na, nc = lu("alertes"), lu("corpsInterceptes")
                if isinstance(na, int) and isinstance(nc, int):
                    if na == 0 and nc == 0:
                        s7 += " " + S["lettrePoeRien"]
                    else:
                        detail = ""
                        parts = [(c, lu("alertes", c)) for c in pp.get("colonnes", []) if c != "Global"]
                        parts = [(c, n) for c, n in parts if isinstance(n, int)]
                        if parts and na >= 4:
                            c, n = max(parts, key=lambda x: x[1])
                            if n * 2 >= na and n < na:
                                detail = P("lettrePoeAlertesDont", n=fmt(n, lang), **{"in": forms(c)["in"]})
                        s7 += " " + P("lettrePoeAlertesF" if FL else "lettrePoeAlertes", alertes=fmt(na, lang), corps=fmt(nc, lang), detail=detail)
            phrases.append(s7)
    p_ri = prose(esc(("\n\n" if FL else " ").join(phrases)))
    c_ri = '    <section class="kpis kpis-riposte" aria-label="%s">\n%s    </section>\n' % (esc(S["bulRiposteTitle"]), cases)
    c_ri += '    <p class="drill"><a href="%s">%s</a></p>\n' % (urls.path("riposte", lang), esc(S["provinceRiposteLinkBul"]))
    html.append(cadre("04", S["lettreRiposteTitle"], "", p_ri + c_ri, "riposte", p_ri, c_ri))

    # ---------------------------------------------------------------- 05 ce que le bulletin dit de ses difficultes
    pf = _point(defis, date)
    if pf and pf.get("piliers"):
        piliers = pf["piliers"]
        resume = ((notes.get(num) or {}).get("defis") or {}).get(lang)
        if resume:
            # Le resume des Defis, redige par l'assistant au signal du
            # proprietaire quand le bulletin est integre (data/bulletin-notes.json).
            corps = prose(esc(resume))
            # La mention « Resume redige le ... d'apres les n piliers » a ete
            # retiree le 8 septembre 2026 a la demande du proprietaire.
        else:
            # Sans resume : le sommaire compose, piliers et provinces citees.
            sommaire = _liste([S.get("defiPilier_" + b["pilier"], b["pilier"]) + ((" (%s)" % ", ".join(b["provinces"])) if b.get("provinces") else "") for b in piliers], et)
            corps = prose(esc(P("lettreDefisSommaire", n=fmt(len(piliers), lang), liste=sommaire)))
        # Les neuf piliers en entier ont ete retires le 8 septembre 2026 a la
        # demande du proprietaire : le resume suffit, le PDF est en tete.
    else:
        corps = prose(esc(S["bulDefisNone"]))
    p_de = corps[:corps.index('    <details')] if '    <details' in corps else corps
    # Le lien suit le texte, hors du panneau que cadre() reserve au reste.
    lien = '    <p class="drill"><a href="%s">%s</a></p>\n' % (urls.path("defis", lang), esc(S["lettreDefisLien"]))
    corps = p_de + lien + corps[len(p_de):]
    p_de += lien
    html.append(cadre("05", S["lettreDefisTitle"], "", corps, "defis", p_de, corps[len(p_de):]))

    # ---------------------------------------------------------------- pied
    pied = P("lettrePied", ref=meta.get("sitrepRef") or "")
    # Le rythme de parution, avec la date du bulletin precedent (8 septembre 2026).
    pied += " " + (P("lettreRythme", date=long_date(prec_date, i18n_lang)) if prec_date else S["lettreRythmeSeul"])
    if non_publie:
        pied += " " + P("bulNonPublieTexte", liste=_liste(non_publie, et))
    # La reference du bulletin est elle-meme le lien vers le PDF (demande
    # du 8 septembre 2026) ; plus de lien « Le PDF du bulletin » a part.
    ref = meta.get("sitrepRef") or ""
    if fiche_pdf.get("file") and ref and ref in pied:
        pied_html = esc(pied).replace(esc(ref), '<a href="/%s" rel="noopener">%s</a>' % (esc(fiche_pdf["file"]), esc(ref)), 1)
    else:
        pied_html = esc(pied) + ((" · " + pdf) if pdf else "")
    # Navigation entre lettres (8 septembre 2026) : precedente / suivante
    # sous la manchette, toutes les lettres dans le pied.
    def _url(n):
        try:
            return urls.path("bulletin-%s" % n, lang)
        except KeyError:
            return None
    nav = ""
    if prec_num and _url(prec_num):
        nav += '<a class="ag-nav-prev" href="%s">%s</a>' % (_url(prec_num), esc(P("lettreNavPrev", num=prec_num)))
    if suiv_num and _url(suiv_num):
        nav += '<a class="ag-nav-next" href="%s">%s</a>' % (_url(suiv_num), esc(P("lettreNavNext", num=suiv_num)))
    nav_html = '<nav class="ag-nav">%s</nav>' % nav if nav else ""
    # Pied (5 novembre 2026) : toutes les lettres dans un depliant, en
    # registre comme la page Rapports (numero, date, cumuls), un onglet par
    # mois. Les 80 numeros alignes
    # d'un bloc faisaient quatre lignes illisibles.
    def _ligne(n):
        d = _DATES.get(n)
        nat = (_NATIONAL.get(n) or {})
        chiffres = interp(S["reportsCasDeces"], {"c": fmt(nat.get("confirmed"), lang), "d": fmt(nat.get("deaths"), lang)}) \
            if nat.get("confirmed") is not None and nat.get("deaths") is not None else ""
        corps = ('<span class="rg-n"><small class="rg-k">%s</small>%s</span><span class="rg-d">%s</span>'
                 '<span class="rg-c">%s</span><span class="rg-p" aria-hidden="true">%s</span>'
                 % (esc(S["lettreKicker"]), esc(n), esc(long_date(d, i18n_lang)) if d else "", esc(chiffres),
                    "" if n == num else "→"))
        if n == num or not _url(n):
            return '<div class="report-chip rg-l is-courante" aria-current="page">%s</div>' % corps
        return '<a class="report-chip rg-l" href="%s">%s</a>' % (_url(n), corps)
    archive_html = ""
    if len(nums) > 1:
        # « Les dernieres lettres » retire le 5 novembre 2026 (demande de
        # Fable) : doublon du lien « Lettre precedente » et de l'onglet du mois.
        mois_noms = S["lettreMoisNoms"].split(",")
        par_mois = {}
        for n in reversed(nums):
            par_mois.setdefault((_DATES.get(n) or "")[:7], []).append(n)
        # Un onglet par mois (5 novembre 2026) : tout afficher faisait une
        # liste de 2 600 px. Sans JS, tous les mois restent visibles.
        cles = sorted(par_mois, reverse=True)
        mois_courant = (_DATES.get(num) or "")[:7]
        actif = mois_courant if mois_courant in par_mois else cles[0]
        annees = {k[:4] for k in cles if k}
        def _nom(k):
            nom = (mois_noms[int(k[5:7]) - 1] + (" " + k[:4] if len(annees) > 1 else "")) if k else "—"
            return nom[:1].upper() + nom[1:]
        onglets = "".join('<button type="button" class="subtab-btn%s" data-mois="%s" aria-pressed="%s">%s <small>%d</small></button>'
                          % (" active" if k == actif else "", k, "true" if k == actif else "false",
                             esc(_nom(k)), len(par_mois[k])) for k in cles)
        panneaux = "".join('<div class="reports-grid is-registre ag-mois-p" data-mois="%s">%s</div>'
                           % (k, "".join(_ligne(n) for n in par_mois[k])) for k in cles)
        archive_html += ('<details class="ag-lexique ag-toutes"><summary>%s</summary>'
                         '<nav class="subtab-nav ag-onglets" aria-label="%s">%s</nav>%s</details>'
                         % (esc(interp(S["lettreToutesN"], {"n": len(nums)})),
                            esc(interp(S["lettreToutesN"], {"n": len(nums)})), onglets, panneaux))
    # Lexique (8 septembre 2026) : les mots du bulletin expliques en une
    # ligne, pour un lecteur qui ne connait pas le vocabulaire de la riposte.
    lex = [S[k] for k in ("lettreLexCasConfirme", "lettreLexCasSuspect", "lettreLexAlerte", "lettreLexContact", "lettreLexZone",
                          "lettreLexCte", "lettreLexEds", "lettreLexRing", "lettreLexPoc", "lettreLexPilier")]
    lex.sort(key=lambda x: x.split(":", 1)[0].lower())   # ordre alphabetique dans chaque langue
    archive_html += '<details class="ag-lexique"><summary>%s</summary><ul>%s</ul></details>' % (
        esc(S["lettreLexiqueTitre"]), "".join('<li>%s</li>' % esc(x) for x in lex))
    html.append('  <section class="section">\n    <p class="map-note lettre-pied">%s</p>\n  </section>\n' % pied_html)
    # La une du quotidien (6 octobre 2026) : manchette, encadre des chiffres
    # et nouveaux cas des 30 derniers jours jusqu'a ce bulletin.
    jusque = [x for x in serie if x["date"] <= date and x.get("confirmed") is not None]
    nouv30 = [(jusque[i]["date"], max(0, jusque[i]["confirmed"] - jusque[i - 1]["confirmed"])) for i in range(1, len(jusque))][-30:]
    if nouv30:
        mx = max(v for _, v in nouv30) or 1
        w = 100.0 / len(nouv30)
        rects = "".join('<rect x="%.2f" y="%.1f" width="%.2f" height="%.1f"%s><title>%s : %s</title></rect>'
                        % (i * w + w * .12, 56 - v / mx * 52, w * .76, v / mx * 52, ' class="is-der"' if i == len(nouv30) - 1 else "",
                           esc(long_date(d, i18n_lang)), fmt(v, lang)) for i, (d, v) in enumerate(nouv30))
        barres = '<svg class="lq-barres" viewBox="0 0 100 56" preserveAspectRatio="none" aria-hidden="true">%s</svg>' % rects
    else:
        barres = ""
    une = {"titre": P("lettreManchette", cas=fmt(nat.get("newCases24h"), lang), deces=fmt(nat.get("newDeaths24h"), lang)),
           "cas": fmt(nat.get("confirmed"), lang), "deces": fmt(nat.get("deaths"), lang), "cfr": fmt_cfr(nat.get("cfr"), lang),
           "plus_cas": plus(nat.get("newCases24h")), "plus_deces": plus(nat.get("newDeaths24h")), "barres": barres}
    # Cases guéris et en CTE dans l'encadre (19 octobre 2026), a partir de
    # la lettre UNE_GUERIS_CTE_DEPUIS. Le nombre en CTE n'a pas
    # d'ecart a la veille : aucune serie nationale ne le conserve.
    if num.isdigit() and int(num) >= UNE_GUERIS_CTE_DEPUIS:
        une["extra"] = ('<div class="lq-chiffre is-gueris"><b>%s</b><span>%s%s</span></div>'
                        % (fmt(nat.get("recovered"), lang), esc(S["lettreUneGueris"]),
                           (" · " + plus(gueris_delta)) if gueris_delta is not None else "")
                        if nat.get("recovered") is not None else "")
        une["extra"] += ('<div class="lq-chiffre is-cte"><b>%s</b><span>%s</span></div>'
                         % (fmt(nat.get("inCTE"), lang), esc(S["lettreUneCte"]))
                         if nat.get("inCTE") is not None else "")
    tete = {"une": une, "num": num, "date": long_date(date, i18n_lang), "publie": long_date(meta.get("publicationDate") or date, i18n_lang),
            "objet": objet, "jour": jour, "ref": meta.get("sitrepRef") or "", "pdf": pdf, "pied": pied, "pied_html": pied_html, "sous": sous_titre,
            "nav_html": nav_html, "archive_html": archive_html, "abo_html": _abonnement(lang, S, esc)}
    return {"seed.bulletinAgence": assembler_agence(tete, chapitres, S, esc, interp)}


# ---------------------------------------------------------------------------
# La mise en page « agence », seule retenue le 8 septembre 2026 (les
# variantes cadres, gazette et revue ont ete supprimees le meme jour).
# ---------------------------------------------------------------------------
def assembler_agence(t, chapitres, S, esc, interp):
    """La lettre en « quotidien » (6 octobre 2026, option 1 du proprietaire :
    l'ancienne mise en page faisait « trop scolaire ») : une de journal avec
    numero, titre et date, manchette sur les chiffres du jour, chapeau et
    premier chapitre a gauche, encadre des chiffres et courbe des 30 jours a
    droite ; les autres chapitres en colonnes separees de filets ; les
    chiffres des chapitres (tableau des provinces, riposte) en bas."""
    u = t["une"]
    premier = chapitres[0]
    autres = chapitres[1:]
    cols = "".join('<section class="lq-art" id="%s"><h2><span>%s</span> %s</h2>%s</section>' % (ident, n, esc(titre), prose)
                   for ident, n, titre, prose, _ in autres)
    chiffres = "".join('<div class="lq-bloc"><h3>%s</h3>%s</div>' % (esc(titre), ch)
                       for ident, n, titre, prose, ch in autres if ch and ident != "defis")
    # Abonnement (19-20 octobre 2026) : en haut, un lien sous le sous-titre de
    # l'en-tete ; le formulaire en bas, une fois la lettre lue.
    abo = t.get("abo_html", "")
    lien = ('<p class="ag-abo"><a href="#abonnement">%s</a></p>' % esc(S["lettreAboTitre"])) if abo else ""
    out = ['<div class="lq">',
           # En-tete de l'ancienne lettre gardee (6 octobre 2026, demande du
           # proprietaire) : bande, nom en capitales, edition et date, sous-titre.
           '<header class="ag-tete"><div class="ag-barre"></div><div class="ag-manchette">'
           '<p class="ag-marque">%s</p>'
           '<p class="ag-edition"><span>%s</span><i></i><span>%s</span></p>'
           '<p class="ag-sous">%s</p>%s</div>%s</header>'
           % (esc(S["lettreEyebrow"]), esc(S["agEdition"] % t["num"]), esc(interp(S["lettreSituationAu"], {"date": t["date"]})), esc(t["sous"]), lien, t["nav_html"]),
           '<div class="lq-grille"><div class="lq-principal" id="%s"><div class="lq-eyebrow">%s</div><h1 class="lq-titre">%s</h1>'
           '<p class="lq-chapo">%s</p>%s</div>'
           % (premier[0], esc(S["lettreUneEyebrow"]), esc(u["titre"]), esc(t["jour"]), premier[3]),
           # Avec les cases gueris et CTE, les chiffres passent sur deux
           # colonnes : cas | deces, gueris | CTE, puis la letalite seule.
           ('<aside class="lq-encadre" aria-label="%s"><div class="lq-deux">'
            '<div class="lq-chiffre is-cas"><b>%s</b><span>%s · %s</span></div>'
            '<div class="lq-chiffre is-deces"><b>%s</b><span>%s · %s</span></div>%s'
            '<div class="lq-chiffre is-large"><b>%s</b><span>%s</span></div></div>'
            '<div class="lq-mini">%s<span>%s</span></div></aside></div>'
            % (esc(S["lettreUneChiffres"]), u["cas"], esc(S["lettreUneCas"]), u["plus_cas"], u["deces"], esc(S["lettreUneDeces"]), u["plus_deces"],
               u["extra"], u["cfr"], esc(S["lettreUneCfr"]), u["barres"], esc(S["lettreUneCourbe"])))
           if u.get("extra") else
           ('<aside class="lq-encadre" aria-label="%s">'
            '<div class="lq-chiffre is-cas"><b>%s</b><span>%s · %s</span></div>'
            '<div class="lq-chiffre is-deces"><b>%s</b><span>%s · %s</span></div>'
            '<div class="lq-chiffre"><b>%s</b><span>%s</span></div>'
            '<div class="lq-mini">%s<span>%s</span></div></aside></div>'
            % (esc(S["lettreUneChiffres"]), u["cas"], esc(S["lettreUneCas"]), u["plus_cas"], u["deces"], esc(S["lettreUneDeces"]), u["plus_deces"],
               u["cfr"], esc(S["lettreUneCfr"]), u["barres"], esc(S["lettreUneCourbe"]))),
           '<div class="lq-cols">%s</div>' % cols,
           ('<div class="lq-chiffres">%s</div>' % chiffres) if chiffres else "",
           abo,
           '<footer class="lq-pied">%s<p class="lq-ref">%s</p>%s</footer></div>' % (t["nav_html"], t["pied_html"], t["archive_html"])]
    return "\n".join(out)
