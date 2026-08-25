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
