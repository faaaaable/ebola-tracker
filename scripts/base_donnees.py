# -*- coding: utf-8 -*-
"""La base de donnees du site (9 octobre 2026) : toutes les donnees, une ligne
par date et par territoire (pays, province, zone de sante), epidemie et
riposte fusionnees, avec le bulletin source de chaque ligne.

Ecrit a chaque generation par build_pages.py, a partir des fichiers de data/
deja produits par le pipeline : aucune nouvelle lecture de PDF.
- data/base-ebola-rdc.csv  : virgule, point decimal, UTF-8 (format standard,
  celui que lisent R, Python, Google Dataset Search) ;
- data/base-ebola-rdc.json : la meme chose, un objet a champs nommes par
  ligne (une case vide y vaut null), plus les metadonnees (licence, source,
  periode, avertissement, dictionnaire des colonnes) ;
- data/base-ebola-rdc-dictionnaire.csv : une ligne par colonne (unite,
  origine publiee ou calculee, definition) ;
- data/ebola-drc-database.csv, .json et -dictionary.csv : la version anglaise
  (4 novembre 2026), colonnes et libelles traduits, offerte sur les pages en
  et sw ;
- data/base-page.json : la forme compacte que lit la page /base-de-donnees/
  (10 novembre 2026), pour qu'elle reste legere.

Regles, a garder alignees sur la page et sur le reste du site :
- une zone = sa cle normalisee (jamais le nom brut) plus les alias du site
  (« Gety » est « Gethy ») ; le nom retenu est celui du dernier bulletin ; une
  zone qui n'a jamais eu de cas (« Karissibi », ligne parasite) est ecartee ;
- « nouveaux » = ecart de cumul avec le releve precedent du meme territoire,
  NEGATIF COMPRIS (une revision a la baisse se voit) ; ecart_jours dit combien
  de journees il couvre ;
- les rattrapages des 22 et 30 juillet et le jour reconstitue du 3 octobre
  (SitRep 142 absent) portent une mention ;
- un releve de riposte rejoint la ligne du pays ou de la province du meme jour ;
- une case vide est une valeur que la source ne donne pas. Licence CC BY 4.0.
"""
from __future__ import annotations

import csv
import io
import json
import os
import unicodedata

import harmonisations
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RATTRAPAGES = {"2026-07-22", "2026-07-30"}
HARMONISATIONS = harmonisations.charger()
ALIAS_ZONES = {"gety": "gethy"}
LICENCE = "https://creativecommons.org/licenses/by/4.0/"

# Les colonnes, dans l'ordre du fichier : cle, groupe (epi/rip/id), type.
COLONNES = [
    ("date", "id", "date"), ("niveau", "id", "txt"), ("province", "id", "txt"), ("zone", "id", "txt"),
    ("sitrep", "id", "int"), ("source_pdf", "id", "txt"), ("mention", "id", "txt"),
    ("cas", "epi", "int"), ("nouveaux_cas", "epi", "int"), ("ecart_jours", "epi", "int"),
    ("deces", "epi", "int"), ("nouveaux_deces", "epi", "int"), ("letalite", "epi", "pct"), ("gueris", "epi", "int"),
    ("nouveaux_gueris", "epi", "int"),
    ("deces_communaute", "rip", "int"), ("deces_cte", "rip", "int"),
    ("alertes_recues", "rip", "int"), ("alertes_validees", "rip", "int"),
    ("labo_echantillons", "rip", "int"), ("labo_positifs", "rip", "int"), ("labo_positivite", "rip", "pct"),
    ("cte_hospitalises", "rip", "int"), ("cte_lits", "rip", "int"), ("cte_occupation", "rip", "pct"),
    ("contacts_a_suivre", "rip", "int"), ("contacts_vus", "rip", "int"), ("contacts_vus_pct", "rip", "pct"),
    ("vaccines_cumul", "rip", "int"),
]
RIPOSTE = [c for c, g, _ in COLONNES if g == "rip"]

# La version anglaise (4 novembre 2026 : « une bdd
# francaise et une bdd anglaise ») : memes lignes, memes valeurs, colonnes et
# libelles traduits. Les noms de provinces et de zones restent ceux des
# bulletins. Ecrite par le meme appel, elle ne peut pas diverger.
COLONNES_EN = {
    "date": "date", "niveau": "level", "province": "province", "zone": "zone",
    "sitrep": "sitrep", "source_pdf": "source_pdf", "mention": "note",
    "cas": "cases", "nouveaux_cas": "new_cases", "ecart_jours": "days_covered",
    "deces": "deaths", "nouveaux_deces": "new_deaths", "letalite": "cfr", "gueris": "recovered", "nouveaux_gueris": "new_recoveries",
    "deces_communaute": "community_deaths", "deces_cte": "etc_deaths",
    "alertes_recues": "alerts_received", "alertes_validees": "alerts_validated",
    "labo_echantillons": "lab_samples", "labo_positifs": "lab_positives", "labo_positivite": "lab_positivity",
    "cte_hospitalises": "etc_admitted", "cte_lits": "etc_beds", "cte_occupation": "etc_occupancy",
    "contacts_a_suivre": "contacts_to_follow", "contacts_vus": "contacts_seen", "contacts_vus_pct": "contacts_seen_pct",
    "vaccines_cumul": "vaccinated_total",
}
assert set(COLONNES_EN) == {c for c, _, _ in COLONNES}
# Les colonnes que decrit chaque ligne du dictionnaire de la page, dans
# l'ordre de bddDico (strings.json, onze lignes dans les trois langues).
DICO_CLES = [["date", "niveau", "province", "zone", "sitrep", "source_pdf", "mention"], ["cas", "deces"],
             ["nouveaux_cas", "nouveaux_deces", "ecart_jours"], ["letalite"], ["gueris", "nouveaux_gueris"],
             ["deces_communaute", "deces_cte"], ["alertes_recues", "alertes_validees"],
             ["labo_echantillons", "labo_positifs", "labo_positivite"],
             ["cte_hospitalises", "cte_lits", "cte_occupation"],
             ["contacts_a_suivre", "contacts_vus", "contacts_vus_pct"], ["vaccines_cumul"]]
# Le dictionnaire des colonnes (10 novembre 2026) : une seule source pour les
# fichiers dictionnaire (CSV francais et anglais), le « meta » des JSON
# telechargeables et les bulles des en-tetes du tableau de la page (trois
# langues). Unite, origine (« publie » = recopie du bulletin, « calcule » =
# calcule par le site) et definition. Le swahili n'a pas encore ete relu par
# un locuteur.
UNITES = {"date": ("AAAA-MM-JJ", "YYYY-MM-DD"), "txt": ("texte", "text"), "int": ("nombre", "count"),
          "pct": ("%", "%"), "jours": ("jours", "days")}
ORIGINES = {"id": ("identification", "identification"), "pub": ("publié", "published"),
            "calc": ("calculé", "computed"), "pubcalc": ("publié, sinon calculé", "published, otherwise computed")}
AVERTISSEMENT = {
    "fr": "Une ligne par date et par territoire. Les lignes du pays, des provinces et des zones se "
          "recouvrent : filtrer sur la colonne « niveau » avant d'additionner. Une case vide est une "
          "valeur que le bulletin ne donne pas, jamais un zéro.",
    "en": "One row per date and area. Country, province and zone rows overlap: filter on the "
          "\u201clevel\u201d column before adding up. An empty cell is a value the bulletin does not "
          "give, never a zero.",
}
DICTIONNAIRE = {
    "date": ("date", "id", {
        "fr": "Date du rapport de situation dont la ligne est tirée.",
        "en": "Date of the situation report the row is taken from.",
        "sw": "Tarehe ya ripoti ya hali ambayo mstari umetoka."}),
    "niveau": ("txt", "id", {
        "fr": "Niveau de la ligne : pays, province ou zone. Les trois niveaux se recouvrent : filtrer sur cette colonne avant d'additionner.",
        "en": "Level of the row: country, province or zone. The three levels overlap: filter on this column before adding up.",
        "sw": "Kiwango cha mstari: nchi, jimbo au eneo. Viwango vitatu vinaingiliana: chuja safu hii kabla ya kujumlisha."}),
    "province": ("txt", "id", {
        "fr": "Province. Vide sur les lignes du pays.",
        "en": "Province. Empty on country rows.",
        "sw": "Jimbo. Tupu kwenye mistari ya nchi."}),
    "zone": ("txt", "id", {
        "fr": "Zone de santé, sous le nom du dernier bulletin. Vide sur les lignes du pays et des provinces.",
        "en": "Health zone, as named in the latest bulletin. Empty on country and province rows.",
        "sw": "Eneo la afya, kwa jina la ripoti ya mwisho. Tupu kwenye mistari ya nchi na majimbo."}),
    "sitrep": ("int", "id", {
        "fr": "Numéro du rapport de situation (SitRep) de l'INSP dont la ligne est tirée.",
        "en": "Number of the INSP situation report (SitRep) the row is taken from.",
        "sw": "Namba ya ripoti ya hali (SitRep) ya INSP ambayo mstari umetoka."}),
    "source_pdf": ("txt", "id", {
        "fr": "Adresse du PDF de ce SitRep. Vide sur une ligne reconstituée.",
        "en": "Address of the PDF of this SitRep. Empty on a reconstructed row.",
        "sw": "Anwani ya PDF ya SitRep hii. Tupu kwenye mstari uliojengwa upya."}),
    "mention": ("txt", "id", {
        "fr": "Signale une ligne à part. « rattrapage » : l'écart couvre plus d'une journée (22 et 30 juillet). "
              "« reconstitue » : SitRep 142 jamais publié, jour calculé par soustraction à partir du 143. "
              "« harmonisation » : la source a corrigé ses séries ce jour-là (Ituri : +314 décès anciens le 30 octobre, "
              "retirés le 31) ; l'écart ne correspond pas à des cas ou décès nouveaux. "
              "« guéris contradictoires » : deux passages du bulletin donnent des guéris du jour différents. "
              "« guéris annoncés ≠ cumul » : les guéris annoncés pour la journée ne font pas la hausse du cumul national depuis la veille. "
              "« OMS Weekly Report … (lecture manuelle) » : valeur lue dans un rapport de l'OMS.",
        "en": "Flags a special row. \u201ccatch-up\u201d: the difference covers more than one day (22 and 30 July). "
              "\u201creconstructed\u201d: SitRep 142 was never published; the day is computed by subtraction from SitRep 143. "
              "\u201charmonisation\u201d: the source corrected its series that day (Ituri: +314 earlier deaths on 30 October, "
              "removed on 31 October); the difference does not reflect new cases or deaths. "
              "\u201cconflicting recoveries\u201d: two passages of the bulletin give different recoveries for the day. "
              "\u201cannounced recoveries \u2260 total\u201d: the recoveries announced for the day do not match the rise in the national total since the day before. "
              "\u201cWHO Weekly Report \u2026 (manual reading)\u201d: value read from a WHO report.",
        "sw": "Inaonyesha mstari maalum: ucheleweshaji, siku iliyojengwa upya, marekebisho ya chanzo, au thamani kutoka ripoti ya WHO."}),
    "cas": ("int", "pub", {
        "fr": "Cas confirmés cumulés depuis le début de l'épidémie, tels que publiés par le bulletin.",
        "en": "Cumulative confirmed cases since the start of the outbreak, as published by the bulletin.",
        "sw": "Jumla ya visa vilivyothibitishwa tangu mwanzo wa mlipuko, kama ilivyochapishwa na ripoti."}),
    "nouveaux_cas": ("int", "calc", {
        "fr": "Écart de cas cumulés avec le relevé précédent du même territoire. Négatif : révision à la baisse par la source. Peut différer des nouveaux cas annoncés par le bulletin.",
        "en": "Difference in cumulative cases from the previous reading for the same area. Negative: downward revision by the source. May differ from the new cases announced by the bulletin.",
        "sw": "Tofauti ya jumla ya visa na takwimu iliyotangulia ya eneo hilo. Hasi: marekebisho ya kupunguza na chanzo."}),
    "ecart_jours": ("jours", "calc", {
        "fr": "Nombre de jours couverts par l'écart, depuis le relevé précédent du même territoire (1 = d'un jour au suivant).",
        "en": "Number of days covered by the difference, since the previous reading for the same area (1 = from one day to the next).",
        "sw": "Idadi ya siku zinazohusika na tofauti, tangu takwimu iliyotangulia ya eneo hilo."}),
    "deces": ("int", "pub", {
        "fr": "Décès cumulés depuis le début de l'épidémie, tels que publiés par le bulletin.",
        "en": "Cumulative deaths since the start of the outbreak, as published by the bulletin.",
        "sw": "Jumla ya vifo tangu mwanzo wa mlipuko, kama ilivyochapishwa na ripoti."}),
    "nouveaux_deces": ("int", "calc", {
        "fr": "Écart de décès cumulés avec le relevé précédent du même territoire. Négatif : révision à la baisse par la source.",
        "en": "Difference in cumulative deaths from the previous reading for the same area. Negative: downward revision by the source.",
        "sw": "Tofauti ya jumla ya vifo na takwimu iliyotangulia ya eneo hilo. Hasi: marekebisho ya kupunguza na chanzo."}),
    "letalite": ("pct", "calc", {
        "fr": "Létalité : décès cumulés divisés par cas confirmés cumulés, en pour cent.",
        "en": "Case fatality rate: cumulative deaths divided by cumulative confirmed cases, in per cent.",
        "sw": "Kiwango cha vifo: jumla ya vifo kugawanywa kwa jumla ya visa, kwa asilimia."}),
    "gueris": ("int", "pub", {
        "fr": "Guéris cumulés, publiés pour le pays seulement, depuis le 21 mai (SitRep 007).",
        "en": "Cumulative recoveries, published for the country only, since 21 May (SitRep 007).",
        "sw": "Jumla ya waliopona, kwa nchi tu."}),
    "nouveaux_gueris": ("int", "pub", {
        "fr": "Guéris déclarés ce jour-là par les structures de prise en charge (CTE, centres de transit, hôpitaux), "
              "pour le pays et chaque province, depuis le 4 juin. Lus dans le bulletin : tableau « Mouvement des patients », "
              "faits saillants ou rubrique Prise en charge ; la somme des provinces retombe sur le total du jour. "
              "0 pour une province que le bulletin ne nomme pas ce jour-là. Pas de cumul par province : "
              "des bulletins manquent. « guéris contradictoires » : deux passages du bulletin ne s'accordent pas.",
        "en": "Recoveries declared that day by treatment facilities (ETCs, transit centres, hospitals), "
              "for the country and each province, since 4 June. Read in the bulletin: \u201cpatient movement\u201d table, "
              "highlights or treatment section; the provinces add up to the day\u2019s total. "
              "0 for a province the bulletin does not name that day. No provincial total: some bulletins are missing. "
              "\u201cconflicting recoveries\u201d: two passages of the bulletin disagree.",
        "sw": "Waliopona waliotangazwa siku hiyo na vituo vya matibabu (CTE, vituo vya mpito, hospitali), "
              "kwa nchi na kila jimbo, tangu 4 Juni. Jumla ya majimbo inalingana na jumla ya siku. "
              "Hakuna jumla kwa jimbo: baadhi ya ripoti hazipo."}),
    "deces_communaute": ("int", "pub", {
        "fr": "Décès confirmés du jour survenus dans la communauté, depuis le 13 juillet.",
        "en": "Confirmed deaths of the day in the community, since 13 July.",
        "sw": "Vifo vilivyothibitishwa vya siku katika jamii, tangu 13 Julai."}),
    "deces_cte": ("int", "pub", {
        "fr": "Décès confirmés du jour survenus en centre de traitement (CTE), depuis le 13 juillet. Par zone, certains ne sont rattachés à aucune zone et ne figurent qu'à la province.",
        "en": "Confirmed deaths of the day in a treatment centre (ETC), since 13 July. By zone, some are not assigned to any zone and appear only under the province.",
        "sw": "Vifo vilivyothibitishwa vya siku katika kituo cha matibabu (CTE), tangu 13 Julai."}),
    "alertes_recues": ("int", "pub", {
        "fr": "Alertes reçues ce jour-là, depuis le 1er juin.",
        "en": "Alerts received that day, since 1 June.",
        "sw": "Tahadhari zilizopokelewa siku hiyo, tangu 1 Juni."}),
    "alertes_validees": ("int", "pub", {
        "fr": "Alertes validées comme cas suspects ce jour-là.",
        "en": "Alerts validated as suspected cases that day.",
        "sw": "Tahadhari zilizothibitishwa kama visa vinavyoshukiwa siku hiyo."}),
    "labo_echantillons": ("int", "pub", {
        "fr": "Échantillons analysés par les laboratoires ce jour-là.",
        "en": "Samples tested by laboratories that day.",
        "sw": "Sampuli zilizochambuliwa na maabara siku hiyo."}),
    "labo_positifs": ("int", "pub", {
        "fr": "Échantillons positifs ce jour-là.",
        "en": "Positive samples that day.",
        "sw": "Sampuli chanya siku hiyo."}),
    "labo_positivite": ("pct", "calc", {
        "fr": "Positifs divisés par échantillons analysés, en pour cent ; seulement quand les deux sont publiés.",
        "en": "Positive results divided by samples tested, in per cent; only when both are published.",
        "sw": "Chanya kugawanywa kwa sampuli, kwa asilimia; pale tu zote mbili zinapochapishwa."}),
    "cte_hospitalises": ("int", "pub", {
        "fr": "Personnes hospitalisées en centre de traitement (CTE) ce jour-là.",
        "en": "People hospitalised in treatment centres (ETC) that day.",
        "sw": "Watu waliolazwa katika vituo vya matibabu (CTE) siku hiyo."}),
    "cte_lits": ("int", "pub", {
        "fr": "Lits disponibles dans les CTE.",
        "en": "Beds available in the ETCs.",
        "sw": "Vitanda vilivyopo katika CTE."}),
    "cte_occupation": ("pct", "pubcalc", {
        "fr": "Taux d'occupation des lits publié par le bulletin ; s'il manque, hospitalisés divisés par lits.",
        "en": "Bed occupancy rate published by the bulletin; if missing, patients divided by beds.",
        "sw": "Kiwango cha vitanda vilivyojaa kilichochapishwa na ripoti; kikikosekana, waliolazwa kugawanywa kwa vitanda."}),
    "contacts_a_suivre": ("int", "pub", {
        "fr": "Contacts à suivre ce jour-là.",
        "en": "Contacts to follow up that day.",
        "sw": "Watu wa karibu wa kufuatiliwa siku hiyo."}),
    "contacts_vus": ("int", "pub", {
        "fr": "Contacts vus ce jour-là.",
        "en": "Contacts seen that day.",
        "sw": "Watu wa karibu walioonekana siku hiyo."}),
    "contacts_vus_pct": ("pct", "pub", {
        "fr": "Part des contacts vus, telle que publiée par le bulletin.",
        "en": "Share of contacts seen, as published by the bulletin.",
        "sw": "Sehemu ya watu wa karibu walioonekana, kama ilivyochapishwa na ripoti."}),
    "vaccines_cumul": ("int", "pub", {
        "fr": "Personnes vaccinées cumulées, publiées par province.",
        "en": "Cumulative people vaccinated, published by province.",
        "sw": "Jumla ya watu waliochanjwa, kwa jimbo."}),
}
assert set(DICTIONNAIRE) == set(COLONNES_EN)
NIVEAUX_EN = {"pays": "country", "province": "province", "zone": "zone"}
MENTIONS_EN = {"rattrapage": "catch-up", "reconstitue": "reconstructed", "harmonisation": "harmonisation",
               "guéris contradictoires": "conflicting recoveries",
               "guéris annoncés ≠ cumul": "announced recoveries ≠ total"}
FICHIERS = {"fr": "base-ebola-rdc", "en": "ebola-drc-database"}
# Le dictionnaire des colonnes, a cote de chaque base (10 novembre 2026).
DICOS = {"fr": "base-ebola-rdc-dictionnaire", "en": "ebola-drc-database-dictionary"}
# Le fichier compact que lit la page, a part des telechargements (10 novembre
# 2026) : lignes en tableaux de valeurs, sans l'adresse du PDF, pour rester
# leger sur les connexions lentes.
PAGE = "base-page"


def _mention_en(m):
    """« rattrapage + OMS Weekly Report 02 (lecture manuelle) » en anglais."""
    out = []
    for x in [x for x in (m or "").split(" + ") if x]:
        x = MENTIONS_EN.get(x, x)
        x = x.replace("OMS ", "WHO ").replace("(lecture manuelle)", "(manual reading)")
        out.append(x)
    return " + ".join(out)


def _ligne_en(o):
    o = dict(o)
    o["niveau"] = NIVEAUX_EN.get(o["niveau"], o["niveau"])
    o["mention"] = _mention_en(o["mention"])
    return o


def _lire(nom):
    with io.open(os.path.join(ROOT, "data", nom), encoding="utf-8") as f:
        return json.load(f)


def _cle(nom):
    t = unicodedata.normalize("NFD", str(nom or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    t = "".join(c for c in t if c.isalnum())
    return ALIAS_ZONES.get(t, t)


def _jours(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def construire(origin="https://ebola-tracker.org"):
    """Les lignes de la base, triees (date, niveau, province, zone)."""
    latest = _lire("latest.json")
    rapports = {r["reportingDate"]: r for r in latest.get("reports", []) if r.get("reportingDate")}
    calcules = _lire("jours-calcules.json") if os.path.exists(os.path.join(ROOT, "data", "jours-calcules.json")) else {}

    def source(d):
        if d in rapports:
            r = rapports[d]
            return int(r["sitrepNumber"]), origin + "/" + r["file"].lstrip("/"), []
        if d in calcules:
            return int(calcules[d]["sitrep"]), "", ["reconstitue"]
        return None, "", []

    lignes = []

    def ajoute(niveau, province, zone, serie):
        pc = pd = pdate = None
        for x in sorted(serie, key=lambda s: s["date"]):
            num, pdf, mention = source(x["date"])
            o = {"date": x["date"], "niveau": niveau, "province": province, "zone": zone,
                 "sitrep": num, "source_pdf": pdf, "mention": list(mention),
                 "cas": x.get("cas"), "deces": x.get("deces"), "gueris": x.get("gueris")}
            o["nouveaux_cas"] = o["cas"] - pc if (o["cas"] is not None and pc is not None) else None
            o["nouveaux_deces"] = o["deces"] - pd if (o["deces"] is not None and pd is not None) else None
            o["ecart_jours"] = _jours(pdate, x["date"]) if (o["nouveaux_cas"] is not None and pdate) else None
            o["letalite"] = round(o["deces"] / o["cas"] * 100, 1) if (o["cas"] and o["deces"] is not None) else None
            if x["date"] in RATTRAPAGES:
                o["mention"].append("rattrapage")
            # Harmonisation des donnees (SitRep 169, Ituri, 30 octobre 2026) :
            # le pays, la province et ses zones.
            h = HARMONISATIONS.get(x["date"])
            if h and (niveau == "pays" or province == h["province"]):
                o["mention"].append("harmonisation")
            if o["cas"] is not None:
                pc, pdate = o["cas"], x["date"]
            if o["deces"] is not None:
                pd = o["deces"]
            lignes.append(o)

    ajoute("pays", "", "", [{"date": s["date"], "cas": s.get("confirmed"), "deces": s.get("deaths"),
                             "gueris": s.get("recovered")} for s in _lire("sitreps.json") if s.get("date")])
    histo = _lire("province-history.json")
    for p in sorted({p["name"] for h in histo for p in h.get("provinces", [])}):
        ajoute("province", p, "", [{"date": h["date"], "cas": x.get("confirmed"), "deces": x.get("deaths")}
                                   for h in histo for x in h.get("provinces", []) if x["name"] == p])
    zones = {}
    for h in sorted(_lire("zones-history.json"), key=lambda s: s["date"]):
        for z in h.get("zones", []):
            k = (z["province"], _cle(z["name"]))
            e = zones.setdefault(k, {"province": z["province"], "zone": z["name"], "serie": []})
            e["zone"] = z["name"]
            e["serie"].append({"date": h["date"], "cas": z.get("cases"), "deces": z.get("deaths")})
    for e in zones.values():
        if any((x["cas"] or 0) > 0 for x in e["serie"]):
            ajoute("zone", e["province"], e["zone"], e["serie"])

    # ---- la riposte, par date et par province ("" = le pays)
    rip = {}
    def r(d, p):
        return rip.setdefault((d, p), {"date": d, "province": p})
    for x in _lire("alertes.json")["parDate"]:
        for p, v in (x.get("provinces") or {}).items():
            o = r(x["date"], p); o["alertes_recues"] = v.get("recues"); o["alertes_validees"] = v.get("validees")
        if x.get("total"):
            o = r(x["date"], ""); o["alertes_recues"] = x["total"].get("recues"); o["alertes_validees"] = x["total"].get("validees")
    def labo(o, v):
        o["labo_echantillons"], o["labo_positifs"] = v.get("echantillons"), v.get("positifs")
        o["labo_positivite"] = round(v["positifs"] / v["echantillons"] * 100, 1) if (v.get("positifs") is not None and v.get("echantillons")) else None
    for x in _lire("laboratoire.json")["parDate"]:
        for p, v in (x.get("provinces") or {}).items():
            labo(r(x["date"], p), v)
        if x.get("total"):
            labo(r(x["date"], ""), x["total"])
    def cte(o, v):
        o["cte_hospitalises"], o["cte_lits"], o["cte_occupation"] = v.get("hospitalises"), v.get("lits"), v.get("occupation")
    for x in _lire("cte.json")["parDate"]:
        for p, v in (x.get("provinces") or {}).items():
            cte(r(x["date"], p), v)
        if x.get("total"):
            cte(r(x["date"], ""), x["total"])
    for x in _lire("contacts-followup.json"):
        for p, v in (x.get("provinces") or {}).items():
            o = r(x["date"], p)
            o["contacts_a_suivre"], o["contacts_vus"], o["contacts_vus_pct"] = v.get("aSuivre"), v.get("vus"), v.get("taux")
        o = r(x["date"], "")
        o["contacts_a_suivre"] = (x.get("contacts") or {}).get("aSuivre")
        o["contacts_vus"] = (x.get("contacts") or {}).get("vus")
        o["contacts_vus_pct"] = x.get("contactsFollowUpRate")
        # Releve tire d'un autre document que le SitRep (28 juin 2026 : rapport
        # hebdomadaire n° 7 de l'OMS, le SitRep 045 n'ayant pas ete publie).
        if not x.get("sitrepNumber") and x.get("source"):
            o["_autre"] = x["source"]
    for x in _lire("deces-lieu.json")["parDate"]:
        c = t = 0
        for p, v in (x.get("provinces") or {}).items():
            o = r(x["date"], p); o["deces_communaute"], o["deces_cte"] = v.get("communautaires"), v.get("intraCte")
            c += v.get("communautaires") or 0; t += v.get("intraCte") or 0
        if x.get("provinces"):
            o = r(x["date"], ""); o["deces_communaute"], o["deces_cte"] = c, t
    # Par zone (deces-lieu-zones.json, 4 novembre 2026). Une zone classee
    # recoit sa ventilation ; une zone sans deces ce jour-la recoit 0 et 0,
    # mais seulement quand les zones de sa province tombent sur la ligne de
    # la province (concordeProvince) : ailleurs on ne sait pas, case vide.
    # Les deces intra-CTE « a ventiler » ne vont a aucune zone.
    zl = {}
    if os.path.exists(os.path.join(ROOT, "data", "deces-lieu-zones.json")):
        for x in _lire("deces-lieu-zones.json")["parDate"]:
            for p, b in x["provinces"].items():
                zl[(x["date"], p)] = (b.get("concordeProvince"),
                                      {_cle(e["zone"]): e for e in b["zones"]})
    for o in lignes:
        if o["niveau"] != "zone" or (o["date"], o["province"]) not in zl:
            continue
        concorde, par_zone = zl[(o["date"], o["province"])]
        e = par_zone.get(_cle(o["zone"]))
        if e is not None:
            o["deces_communaute"], o["deces_cte"] = e.get("communautaires"), e.get("intraCte")
        elif concorde:
            o["deces_communaute"], o["deces_cte"] = 0, 0

    for x in _lire("piliers.json")["parDate"]:
        for p, v in (((x.get("vaccination") or {}).get("provinces")) or {}).items():
            if v.get("cumul") is not None:
                r(x["date"], p)["vaccines_cumul"] = v["cumul"]
        # cumulParProvince porte aussi les cumuls que la lecture detaillee
        # ne remplit pas (16 couples date/province au 29 octobre 2026, dont
        # le Bas-Uele du 25 au 27) ; jamais de desaccord avec « cumul ».
        for p, n in (((x.get("vaccination") or {}).get("cumulParProvince")) or {}).items():
            if n is not None:
                o = r(x["date"], p)
                if o.get("vaccines_cumul") is None:
                    o["vaccines_cumul"] = n

    index = {(o["date"], o["province"] if o["niveau"] == "province" else ""): o
             for o in lignes if o["niveau"] != "zone"}
    for (d, p), v in rip.items():
        if not any(v.get(k) is not None for k in RIPOSTE):
            continue
        o = index.get((d, p))
        if o is None:
            num, pdf, mention = source(d)
            o = {"date": d, "niveau": "province" if p else "pays", "province": p, "zone": "",
                 "sitrep": num, "source_pdf": pdf, "mention": list(mention)}
            lignes.append(o)
        for k in RIPOSTE:
            if k in v:
                o[k] = v[k]
        if v.get("_autre"):
            o["mention"].append(v["_autre"])

    # Guéris du jour par province (data/gueris-provinces.json, 11 novembre
    # 2026). Une province qui a une ligne ce jour-la sans etre nommee par le
    # bulletin recoit 0 : la ventilation retombe sur le total du jour.
    if os.path.exists(os.path.join(ROOT, "data", "gueris-provinces.json")):
        index = {(o["date"], o["province"] if o["niveau"] == "province" else ""): o
                 for o in lignes if o["niveau"] != "zone"}
        par_date = {}
        for o in lignes:
            if o["niveau"] == "province":
                par_date.setdefault(o["date"], []).append(o)
        # Reconciliation avec le cumul national : d'un jour au suivant, sans
        # bulletin manquant, les gueris annonces doivent egaler la hausse du
        # cumul (160 : 32 annonces, cumul +23 ; 162 : 28, +11).
        cumul = sorted((s["date"], s["recovered"]) for s in _lire("sitreps.json")
                       if s.get("date") and s.get("recovered") is not None)
        veille = {b: (a, ca, cb) for (a, ca), (b, cb) in zip(cumul, cumul[1:])}
        for b in _lire("gueris-provinces.json")["parBulletin"]:
            d = b["date"]
            o = index.get((d, ""))
            if o is None:
                num, pdf, mention = source(d)
                o = {"date": d, "niveau": "pays", "province": "", "zone": "",
                     "sitrep": num, "source_pdf": pdf, "mention": list(mention)}
                lignes.append(o)
                index[(d, "")] = o
            o["nouveaux_gueris"] = b["total"]
            v = veille.get(d)
            if v and _jours(v[0], d) == 1 and v[2] - v[1] != b["total"]:
                o["mention"].append("guéris annoncés ≠ cumul")
            contradictoires = {p for v in (b.get("desaccord") or {}).values()
                               for p in set(v) | set(b["provinces"]) if v.get(p, 0) != b["provinces"].get(p, 0)}
            if b.get("desaccord"):
                o["mention"].append("guéris contradictoires")
            for p, n in b["provinces"].items():
                op = index.get((d, p))
                if op is None:
                    num, pdf, mention = source(d)
                    op = {"date": d, "niveau": "province", "province": p, "zone": "",
                          "sitrep": num, "source_pdf": pdf, "mention": list(mention)}
                    lignes.append(op)
                    index[(d, p)] = op
                    par_date.setdefault(d, []).append(op)
                op["nouveaux_gueris"] = n
            for op in par_date.get(d, []):
                if op.get("nouveaux_gueris") is None:
                    op["nouveaux_gueris"] = 0
                if op["province"] in contradictoires and b.get("desaccord") and "guéris contradictoires" not in op["mention"]:
                    op["mention"].append("guéris contradictoires")

    ordre = {"pays": 0, "province": 1, "zone": 2}
    lignes.sort(key=lambda o: (o["date"], ordre[o["niveau"]], o["province"], o["zone"]))
    for o in lignes:
        o["mention"] = " + ".join(o["mention"])
    return lignes


def _definition(cle, lang):
    texte = DICTIONNAIRE[cle][2][lang]
    return texte.replace("'", "\u2019") if lang != "en" else texte


def _dico(lang):
    """Le dictionnaire d'une langue : une entree par colonne, dans l'ordre du
    fichier, avec le nom de la colonne dans ce fichier."""
    k = 0 if lang == "fr" else 1
    nom = (lambda c: c) if lang == "fr" else (lambda c: COLONNES_EN[c])
    champs = ("colonne", "groupe", "type", "unite", "origine", "definition") if lang == "fr" else \
             ("column", "group", "type", "unit", "origin", "definition")
    groupes = {"id": ("identification", "identification"), "epi": ("épidémie", "outbreak"), "rip": ("riposte", "response")}
    sortie = []
    for c, g, t in COLONNES:
        u, o, _ = DICTIONNAIRE[c]
        sortie.append(dict(zip(champs, (nom(c), groupes[g][k], t, UNITES[u][k], ORIGINES[o][k], _definition(c, lang)))))
    return sortie


def _ecrire(nom, texte, encodage="utf-8"):
    with io.open(os.path.join(ROOT, "data", nom), "w", encoding=encodage, newline="") as f:
        f.write(texte)


def _csv(entete, rangs):
    sortie = io.StringIO()
    w = csv.writer(sortie, lineterminator="\n")
    w.writerow(entete)
    w.writerows(rangs)
    return sortie.getvalue()


def _ecrire_fichiers(lang, lignes, cles, entete, meta, cle_lignes):
    """La base d'une langue : CSV, JSON a champs nommes (un objet par ligne de
    fichier, l'adresse du PDF comprise) et dictionnaire des colonnes en CSV."""
    nom = FICHIERS[lang]
    _ecrire(nom + ".csv", _csv(entete, [["" if o.get(k) is None else o.get(k) for k in cles] for o in lignes]),
            "utf-8-sig")
    corps = ",\n".join(json.dumps(dict(zip(entete, (None if o.get(k) == "" else o.get(k) for k in cles))), ensure_ascii=False, separators=(",", ":"))
                       for o in lignes)
    tete = json.dumps(meta, ensure_ascii=False, indent=1)
    _ecrire(nom + ".json", '{"meta":%s,\n"%s":[\n%s\n]}\n' % (tete, cle_lignes, corps))
    dico = _dico(lang)
    _ecrire(DICOS[lang] + ".csv", _csv(list(dico[0]), [list(d.values()) for d in dico]), "utf-8-sig")


def _ecrire_page(lignes, cles, meta, origin):
    """Le fichier de la page : la forme compacte d'origine (lignes en tableaux
    de valeurs, sans l'adresse du PDF : meta.pdf donne le fichier de chaque
    numero), plus la definition de chaque colonne dans les trois langues pour
    les bulles des en-tetes."""
    meta = dict(meta)
    meta["pdf"] = {str(o["sitrep"]): o["source_pdf"].replace(origin, "") for o in lignes if o.get("source_pdf")}
    meta["colonnes"] = [dict(c, definition={lg: _definition(c["cle"], lg) for lg in ("fr", "en", "sw")})
                        for c in meta["colonnes"]]
    meta["harmonisations"] = {d: {"province": h["province"], "deces": h["deces"]} for d, h in HARMONISATIONS.items()}
    sans_pdf = [k if k != "source_pdf" else None for k in cles]
    _ecrire(PAGE + ".json", json.dumps(
        {"meta": meta, "lignes": [[o.get(k) if k else None for k in sans_pdf] for o in lignes]},
        ensure_ascii=False, separators=(",", ":")))


def ecrire(origin="https://ebola-tracker.org"):
    """Ecrit le CSV, le JSON et le dictionnaire, en francais et en anglais,
    puis le fichier compact de la page ; renvoie un resume pour la page."""
    lignes = construire(origin)
    cles = [c for c, _, _ in COLONNES]
    dates = sorted({o["date"] for o in lignes})
    zones = sorted({(o["province"], o["zone"]) for o in lignes if o["niveau"] == "zone"})
    commun = {"licence": LICENCE, "debut": dates[0], "fin": dates[-1], "lignes": len(lignes)}
    meta = {
        "titre": "Base de données de l\u2019épidémie d\u2019Ebola Bundibugyo en RDC (2026)",
        "source": "Rapports de situation (SitRep) de l\u2019Institut national de santé publique (INSP), RDC",
        "licence": LICENCE, "citation": "Ebola Tracker (ebola-tracker.org), d\u2019après les SitRep de l\u2019INSP",
        "avertissement": AVERTISSEMENT["fr"],
        "debut": dates[0], "fin": dates[-1], "lignes": len(lignes),
        "dictionnaire": "%s/data/%s.csv" % (origin, DICOS["fr"]),
        "colonnes": _dico("fr"),
    }
    _ecrire_fichiers("fr", lignes, cles, cles, meta, "lignes")
    meta_en = {
        "title": "Database of the 2026 Bundibugyo Ebola outbreak in the DRC",
        "source": "Situation reports (SitReps) of the National Institute of Public Health (INSP), DRC",
        "licence": LICENCE, "citation": "Ebola Tracker (ebola-tracker.org), from INSP SitReps",
        "warning": AVERTISSEMENT["en"],
        "start": dates[0], "end": dates[-1], "rows": len(lignes),
        "dictionary": "%s/data/%s.csv" % (origin, DICOS["en"]),
        "columns": _dico("en"),
    }
    _ecrire_fichiers("en", [_ligne_en(o) for o in lignes], cles, [COLONNES_EN[c] for c in cles], meta_en, "rows")
    # La page lit ce fichier dans les trois langues ; « en » donne a base.js
    # le nom de chaque colonne dans le fichier anglais.
    _ecrire_page(lignes, cles, dict(commun, colonnes=[{"cle": c, "en": COLONNES_EN[c], "groupe": g, "type": t}
                                                      for c, g, t in COLONNES]), origin)
    return {"lignes": lignes, "dates": dates, "zones": zones}
