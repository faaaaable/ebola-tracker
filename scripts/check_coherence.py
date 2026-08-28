# -*- coding: utf-8 -*-
"""Contrôle de cohérence des données avant publication.

Vérifie que les quatre fichiers de data/ racontent la même histoire, et que
chacun est cohérent avec lui-même. À lancer après scripts/update_data.py et
avant scripts/build_pages.py.

Sortie : une ligne par contrôle. Le script sort en code 1 s'il reste une
anomalie bloquante, 0 sinon. Les écarts connus et documentés du côté de la
source sont signalés mais ne bloquent pas.

    python scripts/check_coherence.py
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

blocking = []
notes = []


def read(name):
    with io.open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def check(label, ok, detail="", blocking_if_false=True):
    # Le detail n'a de sens que sur un ecart : l'afficher sur un controle
    # reussi donnait des lignes trompeuses du genre « ok  098 absent ».
    print("  %-52s %s%s" % (label, "ok" if ok else "ECART",
                            "  " + detail if detail and not ok else ""))
    if not ok:
        (blocking if blocking_if_false else notes).append("%s %s" % (label, detail))


latest = read("latest.json")
sitreps = read("sitreps.json")
zones_history = read("zones-history.json")
province_history = read("province-history.json")

national = latest["national"]
provinces = latest["provinces"]
zones = latest["healthZones"]
meta = latest.get("meta", {})

print("SitRep %s — rapport du %s, publié le %s"
      % (meta.get("sitrepNumber"), meta.get("reportingDate"), meta.get("publicationDate")))

print("\n1. Somme des provinces contre le total national")
for key, field in (("cas confirmés", "confirmed"), ("décès", "deaths")):
    total = sum(p.get(field) or 0 for p in provinces)
    check("somme des provinces = national (%s)" % key,
          total == national.get(field),
          "%s vs %s" % (total, national.get(field)))

for key, field in (("nouveaux cas 24 h", "newCases24h"),
                   ("décès communautaires 24 h", "newDeathsCommunity24h"),
                   ("décès intra-CTE 24 h", "newDeathsIntraCTE24h")):
    total = sum(p.get(field) or 0 for p in provinces)
    check("somme des provinces = national (%s)" % key,
          total == (national.get(field) or 0),
          "%s vs %s" % (total, national.get(field)))

nd = (national.get("newDeathsCommunity24h") or 0) + (national.get("newDeathsIntraCTE24h") or 0)
check("communautaires + intra-CTE = nouveaux décès",
      nd == (national.get("newDeaths24h") or 0),
      "%s vs %s" % (nd, national.get("newDeaths24h")))

print("\n2. Létalité recalculée")
if national.get("confirmed"):
    cfr = round(national["deaths"] / national["confirmed"] * 100, 1)
    check("létalité nationale", abs(cfr - (national.get("cfr") or 0)) <= 0.1,
          "calcul %.1f vs publié %s" % (cfr, national.get("cfr")))
for p in provinces:
    if p.get("confirmed"):
        cfr = round(p["deaths"] / p["confirmed"] * 100, 1)
        check("létalité %s" % p["name"], abs(cfr - (p.get("cfr") or 0)) <= 0.15,
              "calcul %.1f vs publié %s" % (cfr, p.get("cfr")))

print("\n3. Zones de santé")
by_province = {}
for z in zones:
    by_province.setdefault(z.get("province"), []).append(z)
declared = sum((p.get("healthZonesAffected") or {}).get("n") or 0 for p in provinces)
check("zones déclarées par province = total national",
      declared == (national.get("healthZonesAffected") or {}).get("n"),
      "%s vs %s" % (declared, (national.get("healthZonesAffected") or {}).get("n")))
check("zones détaillées = zones déclarées",
      len(zones) == declared,
      "%s détaillées vs %s déclarées ; la source ne détaille pas toujours "
      "chaque zone" % (len(zones), declared),
      blocking_if_false=False)

for p in provinces:
    mine = by_province.get(p["name"], [])
    if not mine:
        continue
    s = sum(z.get("cases") or 0 for z in mine)
    check("somme des zones = province (%s)" % p["name"],
          s == p.get("confirmed"),
          "%s vs %s ; certaines lignes sont « à ventiler »" % (s, p.get("confirmed")),
          blocking_if_false=False)

# Le controle qui manquait le 25 aout : la ventilation des deces du jour
# n'etait verifiee qu'entre provinces et national, jamais entre zones et
# province. Une lecture de colonnes decalee doublait les nouveaux deces de
# neuf zones sur dix sans qu'aucun garde-fou ne bronche — le Nord-Kivu en
# repartissait 16 sur trois zones quand la province en declarait 8.
# L'inegalite est large, pas une egalite : les lignes « a ventiler » de
# l'Ituri restent hors des zones, donc la somme des zones peut etre
# inferieure au total de la province, jamais superieure.
for p_ in provinces:
    mine = by_province.get(p_["name"], [])
    if not mine:
        continue
    somme = sum(z.get("newDeaths24h") or 0 for z in mine)
    total = (p_.get("newDeathsCommunity24h") or 0) + (p_.get("newDeathsIntraCTE24h") or 0)
    check("nouveaux décès des zones <= province (%s)" % p_["name"],
          somme <= total,
          "%s réparti(s) sur les zones vs %s déclaré(s) par la province" % (somme, total))

# Les NOUVEAUX CAS des zones contre le total de la province. Ce controle
# manquait, et c'est par la qu'est passe le SitRep 103 : une cellule vide
# deplacee d'un rang faisait lire la letalite « 9,1% » comme 91 nouveaux cas,
# et les 28 zones de l'Ituri totalisaient 10 161 nouveaux cas en 24 h quand la
# province en declarait 34. Rien ne l'avait vu.
#
# La tolerance n'est pas zero : le bulletin lui-meme n'est pas toujours
# coherent avec ses sous-totaux — au 103, le Nord-Kivu et le Haut-Uele
# depassent chacun d'une unite, et le site les recopie fidelement. On alerte
# donc sur un ECART DE FORME, pas sur l'unite : au-dela du double du total
# declare, ce n'est plus une divergence de source, c'est une colonne mal lue.
for p_ in provinces:
    mine = by_province.get(p_["name"], [])
    if not mine:
        continue
    somme = sum(z.get("newCases24h") or 0 for z in mine)
    total = p_.get("newCases24h") or 0
    plafond = max(total * 2, total + 5)
    check("nouveaux cas des zones plausibles (%s)" % p_["name"],
          somme <= plafond,
          "%s réparti(s) sur les zones vs %s déclaré(s) — colonne probablement décalée"
          % (somme, total))

negative = [z["name"] for z in zones if (z.get("cases") or 0) < 0
            or (z.get("deaths") or 0) < 0]
check("aucun effectif négatif", not negative, ", ".join(negative[:5]))
worse = [z["name"] for z in zones if (z.get("deaths") or 0) > (z.get("cases") or 0)]
check("décès <= cas dans chaque zone", not worse, ", ".join(worse[:5]))

print("\n4. Historiques")
last_sitrep = sitreps[-1] if sitreps else {}
check("dernier point de sitreps.json = date du rapport",
      last_sitrep.get("date") == meta.get("reportingDate"),
      "%s vs %s" % (last_sitrep.get("date"), meta.get("reportingDate")))
check("dernier point de sitreps.json = cumuls nationaux",
      last_sitrep.get("confirmed") == national.get("confirmed")
      and last_sitrep.get("deaths") == national.get("deaths"),
      "%s/%s vs %s/%s" % (last_sitrep.get("confirmed"), last_sitrep.get("deaths"),
                          national.get("confirmed"), national.get("deaths")))

dates = [s.get("date") for s in sitreps]
check("dates de sitreps.json strictement croissantes",
      all(a < b for a, b in zip(dates, dates[1:])))
cum = [s.get("confirmed") or 0 for s in sitreps]
drops = [(dates[i], cum[i - 1], cum[i]) for i in range(1, len(cum)) if cum[i] < cum[i - 1]]
check("cumul de cas jamais décroissant", not drops,
      "; ".join("%s %s->%s" % d for d in drops[:3]),
      blocking_if_false=False)

zh_last = zones_history[-1] if zones_history else {}
check("dernier instantané de zones-history = date du rapport",
      zh_last.get("date") == meta.get("reportingDate"),
      "%s vs %s" % (zh_last.get("date"), meta.get("reportingDate")))
zh_cases = sum(z.get("cases") or 0 for z in zh_last.get("zones", []))
latest_cases = sum(z.get("cases") or 0 for z in zones)
check("instantané de carte = zones de latest.json",
      zh_cases == latest_cases, "%s vs %s" % (zh_cases, latest_cases),
      blocking_if_false=False)

ph_dates = sorted(province_history) if isinstance(province_history, dict) else \
    [e.get("date") for e in province_history]
check("province-history couvre la date du rapport",
      meta.get("reportingDate") in ph_dates,
      "dernière date : %s" % (ph_dates[-1] if ph_dates else "aucune"))

print("\n5. Rapports listés")
reports = latest.get("reports", [])
numbers = [r.get("sitrepNumber") for r in reports if r.get("sitrepNumber")]
check("le rapport courant figure dans la liste",
      meta.get("sitrepNumber") in numbers,
      "%s absent" % meta.get("sitrepNumber"))
check("aucun doublon de numéro", len(numbers) == len(set(numbers)))
# "file" porte déjà le préfixe reports/ : on le résout depuis la racine.
missing = [r.get("file") for r in reports
           if r.get("file") and not os.path.exists(os.path.join(ROOT, r["file"]))]
check("chaque rapport listé a son PDF", not missing, ", ".join(missing[:4]))

print("\n6. Riposte (alertes, laboratoire, contacts, CTE)")
# Ces quatre fichiers ne portent pas de total national a comparer a
# latest.json : on verifie que chacun est coherent avec lui-meme — les
# invariants de la source — et qu'aucun ne date d'apres le bulletin courant.
# Un ecart qui vient de la source (une positivite publiee qui ne se recalcule
# pas) est signale sans bloquer ; une impossibilite (plus de positifs que
# d'echantillons) bloque.
def _lire_optionnel(name):
    path = os.path.join(ROOT, "data", name)
    return read(name) if os.path.exists(path) else None

alertes = _lire_optionnel("alertes.json")
laboratoire = _lire_optionnel("laboratoire.json")
contacts = _lire_optionnel("contacts-followup.json")
cte = _lire_optionnel("cte.json")
date_rapport = meta.get("reportingDate") or ""

for nom, fichier in (("alertes", alertes), ("laboratoire", laboratoire), ("cte", cte)):
    if not fichier:
        check("%s.json present" % nom, False, "fichier absent", blocking_if_false=False)
        continue
    points = fichier.get("parDate", [])
    derniere = points[-1]["date"] if points else None
    check("%s.json ne depasse pas la date du rapport" % nom,
          bool(derniere) and derniere <= date_rapport, "%s vs %s" % (derniere, date_rapport))

if laboratoire:
    impossibles = []
    ecarts = []
    for p in laboratoire.get("parDate", []):
        for prov, l in (p.get("provinces") or {}).items():
            e, pos, pv = l.get("echantillons"), l.get("positifs"), l.get("positivite")
            if e is not None and pos is not None and pos > e:
                impossibles.append("%s %s %d/%d" % (p["sitrepNumber"], prov, pos, e))
            if e and pos is not None and pv is not None and abs(pos / e * 100 - pv) > 1.5:
                ecarts.append("%s %s" % (p["sitrepNumber"], prov))
    check("laboratoire : positifs <= echantillons (chaque province)", not impossibles, ", ".join(impossibles[:4]))
    check("laboratoire : positivite publiee = recalculee (a 1,5 pt)", not ecarts,
          ", ".join(ecarts[:6]), blocking_if_false=False)
    dernier = laboratoire["parDate"][-1] if laboratoire.get("parDate") else None
    if dernier and dernier["date"] == date_rapport:
        t = dernier.get("total") or {}
        positifs = t.get("nouveauxCas", t.get("positifs"))
        if positifs is not None and national.get("newCases24h") is not None:
            check("laboratoire : positifs du jour = nouveaux cas du bulletin",
                  positifs == national["newCases24h"],
                  "%s vs %s" % (positifs, national["newCases24h"]), blocking_if_false=False)

if alertes:
    impossibles = []
    for p in alertes.get("parDate", []):
        if not p.get("methode", "").startswith("tableau par province"):
            continue  # en B-C, validees et verifiees comptent aussi la veille
        for prov, a in (p.get("provinces") or {}).items():
            r, v, va = a.get("recues"), a.get("verifiees"), a.get("validees")
            if va is not None and v is not None and va > v:
                impossibles.append("%s %s %d>%d" % (p["sitrepNumber"], prov, va, v))
    check("alertes : validees <= verifiees (format par province)", not impossibles, ", ".join(impossibles[:4]))

if cte:
    ecarts = []
    for p in cte.get("parDate", []):
        for prov, c in (p.get("provinces") or {}).items():
            h, l, o = c.get("hospitalises"), c.get("lits"), c.get("occupation")
            if h is not None and l and o is not None and not c.get("occupationCalculee") \
                    and abs(h / l * 100 - o) > 1.5:
                ecarts.append("%s %s" % (p["sitrepNumber"], prov))
    check("cte : occupation publiee = hospitalises / lits (a 1,5 pt)", not ecarts,
          ", ".join(ecarts[:6]), blocking_if_false=False)

if contacts:
    impossibles = []
    for e in contacts:
        c = e.get("contacts") or {}
        if c.get("vus") is not None and c.get("aSuivre") is not None and c["vus"] > c["aSuivre"]:
            impossibles.append(e["date"])
        for prov, pr in (e.get("provinces") or {}).items():
            if pr.get("vus") is not None and pr.get("aSuivre") is not None and pr["vus"] > pr["aSuivre"]:
                impossibles.append("%s %s" % (e["date"], prov))
    check("contacts : vus <= a suivre (national et provinces)", not impossibles, ", ".join(impossibles[:4]))
    derniere = contacts[-1]["date"] if contacts else None
    check("contacts-followup.json ne depasse pas la date du rapport",
          bool(derniere) and derniere <= date_rapport, "%s vs %s" % (derniere, date_rapport))

print()
if notes:
    print("%d écart(s) non bloquant(s), connus de la source :" % len(notes))
    for n in notes:
        print("  - %s" % n)
if blocking:
    print("\n%d ECART BLOQUANT :" % len(blocking))
    for b in blocking:
        print("  - %s" % b)
    sys.exit(1)
print("Aucun écart bloquant.")
