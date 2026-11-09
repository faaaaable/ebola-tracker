# -*- coding: utf-8 -*-
"""La base de donnees du site (9 octobre 2026) : toutes les donnees, une ligne
par date et par territoire (pays, province, zone de sante), epidemie et
riposte fusionnees, avec le bulletin source de chaque ligne.

Ecrit a chaque generation par build_pages.py, a partir des fichiers de data/
deja produits par le pipeline : aucune nouvelle lecture de PDF.
- data/base-ebola-rdc.csv  : virgule, point decimal, UTF-8 (format standard,
  celui que lisent R, Python, Google Dataset Search) ;
- data/base-ebola-rdc.json : la meme chose en colonnes + lignes, plus les
  metadonnees (licence, source, periode). La page /base-de-donnees/ le lit.
- data/ebola-drc-database.csv et .json : la version anglaise (4 novembre
  2026), colonnes et libelles traduits, offerte sur les pages en et sw.

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
    "deces": "deaths", "nouveaux_deces": "new_deaths", "letalite": "cfr", "gueris": "recovered",
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
             ["nouveaux_cas", "nouveaux_deces", "ecart_jours"], ["letalite"], ["gueris"],
             ["deces_communaute", "deces_cte"], ["alertes_recues", "alertes_validees"],
             ["labo_echantillons", "labo_positifs", "labo_positivite"],
             ["cte_hospitalises", "cte_lits", "cte_occupation"],
             ["contacts_a_suivre", "contacts_vus", "contacts_vus_pct"], ["vaccines_cumul"]]
NIVEAUX_EN = {"pays": "country", "province": "province", "zone": "zone"}
MENTIONS_EN = {"rattrapage": "catch-up", "reconstitue": "reconstructed", "harmonisation": "harmonisation"}
FICHIERS = {"fr": "base-ebola-rdc", "en": "ebola-drc-database"}


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

    ordre = {"pays": 0, "province": 1, "zone": 2}
    lignes.sort(key=lambda o: (o["date"], ordre[o["niveau"]], o["province"], o["zone"]))
    for o in lignes:
        o["mention"] = " + ".join(o["mention"])
    return lignes


def _ecrire_fichiers(nom, lignes, cles, entete, meta, origin):
    sortie = io.StringIO()
    w = csv.writer(sortie, lineterminator="\n")
    w.writerow(entete)
    for o in lignes:
        w.writerow(["" if o.get(k) is None else o.get(k) for k in cles])
    with io.open(os.path.join(ROOT, "data", nom + ".csv"), "w", encoding="utf-8-sig", newline="") as f:
        f.write(sortie.getvalue())
    # Le JSON ne repete pas l'adresse du PDF sur chaque ligne (elle doublait
    # le poids du fichier) : meta.pdf donne le fichier de chaque numero.
    meta["pdf"] = {str(o["sitrep"]): o["source_pdf"].replace(origin, "") for o in lignes if o.get("source_pdf")}
    sans_pdf = [k if k != "source_pdf" else None for k in cles]
    with io.open(os.path.join(ROOT, "data", nom + ".json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "lignes": [[o.get(k) if k else None for k in sans_pdf] for o in lignes]}, f,
                  ensure_ascii=False, separators=(",", ":"))


def ecrire(origin="https://ebola-tracker.org"):
    """Ecrit le CSV et le JSON, en francais et en anglais ; renvoie un resume
    pour la page."""
    lignes = construire(origin)
    cles = [c for c, _, _ in COLONNES]
    dates = sorted({o["date"] for o in lignes})
    zones = sorted({(o["province"], o["zone"]) for o in lignes if o["niveau"] == "zone"})
    # Le JSON francais est celui que lit la page, dans les trois langues ;
    # « en » donne a base.js le nom de chaque colonne dans le fichier anglais.
    meta = {
        "titre": "Base de donnees de l'epidemie d'Ebola Bundibugyo en RDC (2026)",
        "source": "Rapports de situation (SitRep) de l'Institut national de sante publique (INSP), RDC",
        "licence": LICENCE, "citation": "Ebola Tracker (ebola-tracker.org), d'apres les SitRep de l'INSP",
        "debut": dates[0], "fin": dates[-1], "lignes": len(lignes),
        "colonnes": [{"cle": c, "en": COLONNES_EN[c], "groupe": g, "type": t} for c, g, t in COLONNES],
    }
    _ecrire_fichiers(FICHIERS["fr"], lignes, cles, cles, meta, origin)
    meta_en = {
        "title": "Database of the 2026 Bundibugyo Ebola outbreak in the DRC",
        "source": "Situation reports (SitReps) of the National Institute of Public Health (INSP), DRC",
        "licence": LICENCE, "citation": "Ebola Tracker (ebola-tracker.org), from INSP SitReps",
        "start": dates[0], "end": dates[-1], "rows": len(lignes),
        "columns": [{"key": COLONNES_EN[c], "type": t} for c, g, t in COLONNES],
    }
    _ecrire_fichiers(FICHIERS["en"], [_ligne_en(o) for o in lignes], cles,
                     [COLONNES_EN[c] for c in cles], meta_en, origin)
    return {"lignes": lignes, "dates": dates, "zones": zones}
