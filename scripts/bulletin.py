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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEUIL_CONTACTS = 85.0   # le seuil que l'INSP s'est fixe depuis aout (cf. app.js, SEUIL_INSP)


def _lire(chemin):
    with io.open(os.path.join(ROOT, chemin), encoding="utf-8") as fh:
        return json.load(fh)


def _point(serie, date, cle="parDate"):
    points = serie.get(cle, []) if isinstance(serie, dict) else serie
    for p in points:
        if p.get("date") == date:
            return p
    return None


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


def render(lang, S, i18n_lang, fmt, fmt_decimal, fmt_cfr, long_date, esc, interp,
           province_forms, couleurs, urls):
    """Les graines de la maquette (dernier bulletin) et, sous seed.lettres,
    la lettre « agence » de chaque bulletin fige, par numero."""
    instantanes = _instantanes()
    nums = sorted(instantanes)
    lettres, seeds = {}, {}
    for i, num in enumerate(nums):
        prec_date = instantanes[nums[i - 1]]["meta"]["reportingDate"] if i else None
        s = _lettre(instantanes[num], nums[i - 1] if i else None, nums[i + 1] if i + 1 < len(nums) else None, nums,
                    lang, S, i18n_lang, fmt, fmt_decimal, fmt_cfr, long_date, esc, interp, province_forms, couleurs, urls, prec_date)
        lettres[num] = s["seed.bulletinAgence"]
        seeds = s
    seeds["seed.lettres"] = lettres
    return seeds


def _lettre(latest, prec_num, suiv_num, nums, lang, S, i18n_lang, fmt, fmt_decimal, fmt_cfr, long_date, esc, interp,
            province_forms, couleurs, urls, prec_date=None):
    meta, nat = latest["meta"], latest["national"]
    num, date = meta["sitrepNumber"], meta["reportingDate"]
    serie = sorted([s for s in _lire("data/sitreps.json") if s.get("date")], key=lambda s: s["date"])
    veille = next((s for s in reversed(serie) if s["date"] < date), None)
    zh = _lire("data/zones-history.json")
    alertes, labo = _lire("data/alertes.json"), _lire("data/laboratoire.json")
    contacts, cte = _lire("data/contacts-followup.json"), _lire("data/cte.json")
    deces, defis = _lire("data/deces-lieu.json"), _lire("data/defis.json")
    piliers_data = _lire("data/piliers.json") if os.path.exists(os.path.join(ROOT, "data", "piliers.json")) else None
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
        return '    <p class="fiche-texte lettre-texte">%s</p>\n' % txt
    non_publie = []
    html = []

    # ---------------------------------------------------------------- zones nouvelles
    nouvelles = []
    zi = next((i for i, z in enumerate(zh) if z["date"] == date), None)
    if zi:
        avant = {(z["province"], z["name"].lower()) for z in zh[zi - 1]["zones"]}
        nouvelles = [z for z in zh[zi]["zones"] if (z["province"], z["name"].lower()) not in avant]
    # Date de la derniere zone nouvelle, pour ecrire « aucune nouvelle zone
    # depuis le ... » (8 septembre 2026).
    derniere_nouvelle = None
    for i in range(1, (zi or 0) + 1):
        avant_i = {(z["province"], z["name"].lower()) for z in zh[i - 1]["zones"]}
        if any((z["province"], z["name"].lower()) not in avant_i for z in zh[i]["zones"]):
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
        return (a[cle] - b[cle]) / float(n) if n > 0 else None
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
    jour = P("lettreJour", rapport=long_date(date, i18n_lang), publie=long_date(meta.get("publicationDate") or date, i18n_lang),
             cas=fmt(nat.get("newCases24h"), lang), deces=fmt(nat.get("newDeaths24h"), lang))
    if moy_cas is not None and nat.get("newCases24h") is not None:
        r = nat["newCases24h"] / moy_cas if moy_cas else None
        cle = "lettreJourNiveauMoyen" if r is None else ("lettreJourNiveauHaut" if r > 1.1 else "lettreJourNiveauBas" if r < 0.9 else "lettreJourNiveauMoyen")
        jour += " " + P(cle, cas=fmt(nat["newCases24h"], lang), moy=un_dec(moy_cas))
    if nouvelles:
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
    txt = P("lettreBilan", cas=fmt(nat.get("confirmed"), lang), deces=fmt(nat.get("deaths"), lang), cfr=fmt_cfr(nat.get("cfr"), lang), gueris=fmt(nat.get("recovered"), lang))
    if gueris_delta is not None and gueris_delta > 0:
        txt += " " + P("lettreBilanGueris", n=fmt(gueris_delta, lang))
    if nat.get("inCTE") is not None:
        txt += " " + P("lettreBilanCte", n=fmt(nat.get("inCTE"), lang))
    if None not in (moy_cas, moy_cas_prec, moy_dec, moy_dec_prec):
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
    if avec:
        premiere = avec[0]
        txt = maj(P("lettreOuPremiere", the=forms(premiere["name"])["the"], n=fmt(premiere["newCases24h"], lang), total=fmt(nat.get("newCases24h"), lang)))
        if len(avec) > 1:
            txt += " " + P("lettreOuSuite", liste=_liste([P("lettreOuItem", the=forms(p["name"])["the"], n=fmt(p["newCases24h"], lang)) for p in avec[1:]], et))
    else:
        txt = S["lettreOuAucun"]
    if sans and avec:
        txt += " " + (P("lettreOuSansPlusieurs", n=fmt(len(sans), lang)) if len(sans) > 1 else maj(P("lettreOuSansUne", the=forms(sans[0]["name"])["the"])))
    actives = sorted([z for z in latest["healthZones"] if (z.get("newCases24h") or 0) > 0], key=lambda z: -(z.get("newCases24h") or 0))[:5]
    if actives and nat.get("newCases24h"):
        somme = sum(z["newCases24h"] for z in actives)
        txt += " " + P("lettreOuZones", k=fmt(len(actives), lang), somme=fmt(somme, lang), total=fmt(nat["newCases24h"], lang),
                       liste=_liste(["%s %s" % (z["name"], fmt(z["newCases24h"], lang)) for z in actives], et))
    # Zones actives : au moins un cas notifie dans les 21 derniers jours,
    # d'apres les cumuls par zone de l'instantane le plus proche 21 jours
    # avant (8 septembre 2026).
    if zi is not None:
        from datetime import date as _d, timedelta
        cible = (_d(*(int(x) for x in date.split("-"))) - timedelta(days=21)).isoformat()
        z21 = next((z for z in reversed(zh[:zi]) if z["date"] <= cible), None)
        if z21:
            avant21 = {(z["province"], z["name"].lower()): z.get("cases") or 0 for z in z21["zones"]}
            zones_now = zh[zi]["zones"]
            k = sum(1 for z in zones_now if (z.get("cases") or 0) > avant21.get((z["province"], z["name"].lower()), 0))
            n = len(zones_now)
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
              '      <tbody>\n%s      </tbody></table></div>\n'
              % (esc(S["bulThProvince"]), esc(S["bulThNewCases"]), esc(S["bulThNewDeaths"]), esc(i18n_lang["labelConfirmed"]), esc(i18n_lang["labelDeaths"]), esc(S["bulThZones"]), lignes))
    html.append(cadre("02", S["lettreOuTitle"], "", corps, "ou", prose(esc(txt)), corps[len(prose(esc(txt))):]))

    # ---------------------------------------------------------------- 03 les deces
    d_comm, d_cte = nat.get("newDeathsCommunity24h"), nat.get("newDeathsIntraCTE24h")
    if d_comm is not None and d_cte is not None:
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
        s1 = P("lettreAlertes", recues=fmt(t["recues"], lang), verifiees=fmt(t.get("verifiees"), lang), validees=fmt(t.get("validees"), lang))
        if muets:
            s1 += " " + maj(P("lettreAlertesMuet", liste=_liste([forms(m)["the"] for m in muets], et)))
        phrases.append(s1)
        cases += kpi("alerts", S["lettreKpiAlertes"], fmt(t["recues"], lang), P("lettreKpiAlertesSub", verifiees=fmt(t.get("verifiees"), lang), validees=fmt(t.get("validees"), lang)))
    else:
        cases += kpi("alerts", S["lettreKpiAlertes"], "—", S["riposteKpiNone"]); non_publie.append(S["lettreKpiAlertes"])
    if pl and (pl.get("total") or {}).get("echantillons"):
        t = pl["total"]
        s2 = P("lettreLabo", positifs=fmt(t.get("positifs"), lang), echantillons=fmt(t.get("echantillons"), lang), taux=pct(t.get("positivite")))
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
        s3 = P("lettreContactsAuDessus" if taux >= SEUIL_CONTACTS else "lettreContactsEnDessous", taux=pct(taux), seuil=fmt(int(SEUIL_CONTACTS), lang))
        bas = [nom for nom, v in (pc.get("provinces") or {}).items() if v.get("taux") is not None and v["taux"] < 75]
        if bas:
            s3 += " " + P("lettreContactsBas", liste=_liste(sorted(bas), et))
        phrases.append(s3)
        cases += kpi("contacts", S["lettreKpiContacts"], pct(taux), P("lettreKpiContactsSub", vus=fmt(c.get("vus"), lang), aSuivre=fmt(c.get("aSuivre"), lang)) if c.get("vus") is not None else "")
    else:
        cases += kpi("contacts", S["lettreKpiContacts"], "—", S["riposteKpiNone"]); non_publie.append(S["lettreKpiContacts"])
    if pk and (pk.get("total") or {}).get("occupation") is not None:
        t = pk["total"]
        s4 = P("lettreCte", taux=pct(t["occupation"]), hospitalises=fmt(t.get("hospitalisesAvecLits") or t.get("hospitalises"), lang), lits=fmt(t.get("lits"), lang))
        satures = [(nom, v) for nom, v in (pk.get("provinces") or {}).items() if (v.get("occupation") or 0) > 100]
        if satures:
            s4 += " " + P("lettreCteSature", liste=_liste([P("lettreCteItem", the=forms(nom)["the"], hospitalises=fmt(v["hospitalises"], lang), lits=fmt(v["lits"], lang)) for nom, v in satures], et))
        phrases.append(s4)
        cases += kpi("cte", S["lettreKpiCte"], pct(t["occupation"]), P("lettreKpiCteSub", hospitalises=fmt(t.get("hospitalisesAvecLits") or t.get("hospitalises"), lang), lits=fmt(t.get("lits"), lang)))
    else:
        cases += kpi("cte", S["lettreKpiCte"], "—", S["riposteKpiNone"]); non_publie.append(S["lettreKpiCte"])
    # Trois piliers lus depuis le 8 septembre 2026 (data/piliers.json) :
    # enterrements securises et rings, vaccination, points de controle.
    # Chaque phrase n'existe que si le bulletin donne le chiffre.
    pp = _point(piliers_data, date) if piliers_data else None
    if pp:
        rg, ed, va, po = pp.get("rings"), pp.get("eds"), pp.get("vaccination"), pp.get("poe")
        if ed and ed.get("alertes") is not None and ed.get("realisees") is not None:
            s5 = P("lettreEds", alertes=fmt(ed["alertes"], lang), realisees=fmt(ed["realisees"], lang), swabes=fmt(ed.get("swabes"), lang) if ed.get("swabes") is not None else "—")
            if ed.get("nonSwabes"):
                s5 += " " + P("lettreEdsRefus", n=fmt(ed["nonSwabes"], lang))
            phrases.append(s5)
            cases += kpi("eds", S["lettreKpiEds"], fmt(ed["realisees"], lang), P("lettreKpiEdsSub", realisees=fmt(ed["realisees"], lang), alertes=fmt(ed["alertes"], lang)))
        if rg and rg.get("attendus"):
            phrases.append(P("lettreRings", ouverts=fmt(rg.get("ouverts") or 0, lang), attendus=fmt(rg["attendus"], lang)))
        # Vaccination : le bulletin ne donne que des cumuls, par province ou
        # par zone (voir extract_piliers.lire_vaccination). On additionne le
        # dernier cumul connu de chaque province a la date de la lettre, en
        # datant ceux qui viennent d'un bulletin anterieur.
        connus, debut = {}, None
        for e in piliers_data.get("parDate", []):
            if e["date"] > date:
                break
            for prov, v in ((e.get("vaccination") or {}).get("cumulParProvince") or {}).items():
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
                s6 = P("lettreVaccination", total=fmt(total, lang), debut=long_date(debut, i18n_lang), detail=_liste(items, et))
                cases += kpi("vaccin", S["lettreKpiVaccin"], fmt(total, lang), P("lettreKpiVaccinSub", date=long_date(debut, i18n_lang)))
            if va and va.get("rupture"):
                s6 = (s6 + " " if s6 else "") + S["lettreVaccinationRupture"]
            phrases.append(s6)
        if po and po.get("personnes") is not None and po.get("screenesPct") is not None:
            s7 = P("lettrePoe", personnes=fmt(po["personnes"], lang), pct=pct(po["screenesPct"]))
            if po.get("refusScreening"):
                s7 += " " + P("lettrePoeRefus", n=fmt(po["refusScreening"], lang))
            phrases.append(s7)
    p_ri = prose(esc(" ".join(phrases)))
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
    toutes = [('<a href="%s">n°%s</a>' % (_url(n), n)) if n != num and _url(n) else ('<b>n°%s</b>' % n) for n in reversed(nums)]
    archive_html = '<p class="ag-archive">%s %s</p>' % (esc(S["lettreToutes"]), " · ".join(toutes)) if len(nums) > 1 else ""
    # Lexique (8 septembre 2026) : les mots du bulletin expliques en une
    # ligne, pour un lecteur qui ne connait pas le vocabulaire de la riposte.
    lex = [S[k] for k in ("lettreLexCasConfirme", "lettreLexCasSuspect", "lettreLexAlerte", "lettreLexContact", "lettreLexZone",
                          "lettreLexCte", "lettreLexEds", "lettreLexRing", "lettreLexPoc", "lettreLexPilier")]
    lex.sort(key=lambda x: x.split(":", 1)[0].lower())   # ordre alphabetique dans chaque langue
    archive_html += '<details class="ag-lexique"><summary>%s</summary><ul>%s</ul></details>' % (
        esc(S["lettreLexiqueTitre"]), "".join('<li>%s</li>' % esc(x) for x in lex))
    html.append('  <section class="section">\n    <p class="map-note lettre-pied">%s</p>\n  </section>\n' % pied_html)
    tete = {"num": num, "date": long_date(date, i18n_lang), "publie": long_date(meta.get("publicationDate") or date, i18n_lang),
            "objet": objet, "jour": jour, "ref": meta.get("sitrepRef") or "", "pdf": pdf, "pied": pied, "pied_html": pied_html, "sous": sous_titre,
            "nav_html": nav_html, "archive_html": archive_html}
    return {"seed.bulletinAgence": assembler_agence(tete, chapitres, S, esc, interp)}


# ---------------------------------------------------------------------------
# La mise en page « agence », seule retenue le 8 septembre 2026 (les
# variantes cadres, gazette et revue ont ete supprimees le meme jour).
# ---------------------------------------------------------------------------
def assembler_agence(t, chapitres, S, esc, interp):
    """Une depeche : bande ambre, manchette centree (sans objet encadre
    depuis le 8 septembre 2026), prose a gauche et colonne des chiffres a
    droite, qui suit le defilement."""
    prose_all = "".join('<section class="ag-chap" id="%s"><h2 class="ag-titre"><span>%s</span>%s</h2>%s</section>' % (ident, n, esc(titre), prose) for ident, n, titre, prose, _ in chapitres)
    # Les Defis n'ont pas de chiffres : leurs textes complets restent dans la prose.
    chiffres_all = "".join('<div class="ag-bloc"><div class="ag-bloc-titre">%s</div>%s</div>' % (esc(titre), chiffres) for ident, n, titre, _, chiffres in chapitres if chiffres and ident != "defis")
    # Sur telephone, les colonnes n'existent plus : chaque chapitre porte
    # ses chiffres juste sous sa prose (.ag-chiffres-inline, visible sous
    # 900 px), et la colonne de droite se cache. Sur ordinateur c'est
    # l'inverse. Le meme bloc est donc rendu deux fois (8 septembre 2026).
    prose_all = "".join('<section class="ag-chap" id="%s"><h2 class="ag-titre"><span>%s</span>%s</h2>%s%s</section>'
                        % (ident, n, esc(titre), prose,
                           (chiffres if ident == "defis" else ('<div class="ag-chiffres-inline">%s</div>' % chiffres if chiffres else "")))
                        for ident, n, titre, prose, chiffres in chapitres)
    out = ['<div class="ag">',
           # Manchette centree (8 septembre 2026) : le nom en tres grand au
           # milieu, puis edition et date sur une ligne, puis le sous-titre.
           '<header class="ag-tete"><div class="ag-barre"></div><div class="ag-manchette">'
           '<p class="ag-marque">%s</p>'
           '<p class="ag-edition"><span>%s</span><i></i><span>%s</span></p>'
           '<p class="ag-sous">%s</p></div>%s</header>'
           % (esc(S["lettreEyebrow"]), esc(S["agEdition"] % t["num"]), esc(interp(S["lettreSituationAu"], {"date": t["date"]})), esc(t["sous"]), t["nav_html"]),
           '<div class="ag-grille"><div class="ag-prose"><p class="ag-jour">%s</p>%s</div><aside class="ag-chiffres"><div class="ag-chiffres-titre">%s</div>%s</aside></div>'
           % (esc(t["jour"]), prose_all, esc(S["agChiffres"]), chiffres_all),
           # Navigation precedente / suivante repetee en bas (8 septembre 2026).
           '<footer class="ag-pied">%s%s%s</footer></div>' % (t["nav_html"], t["pied_html"], t["archive_html"])]
    return "\n".join(out)
