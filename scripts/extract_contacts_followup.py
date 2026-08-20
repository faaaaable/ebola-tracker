#!/usr/bin/env python3
"""
Extrait le taux de suivi des contacts (%) pour TOUS les SitReps disponibles,
avec leur vraie date de rapportage (pas juste leur numéro), et écrit le
résultat complet dans data/contacts-followup.json.

Contrairement à scan_contacts_poepoc.py (diagnostic, échantillon limité à
15 valeurs pour la lisibilité du log), ce script exporte l'intégralité des
valeurs trouvées — c'est le fichier de données réel destiné à alimenter un
graphique sur le site, pas un simple sondage de fiabilité.

Usage: python3 scripts/extract_contacts_followup.py
"""
import glob
import json
import os
import re

import pdfplumber

from update_data import extract_meta, extract_number_from_filename

REPORTS_DIR = "reports"
OUTPUT_PATH = "data/contacts-followup.json"

# SitRep dont la valeur extraite est jugée trop isolée pour être fiable
# (chacune entourée d'un grand trou de données des deux côtés, sans point
# voisin pour la remettre en contexte) — écartés du graphique sur demande,
# le 20/08/2026 : "038" (95,0%, 21 juin) et "048" (67,3%, 1er juillet).
CONTACTS_EXCLUDED_SITREPS = {"038", "048"}

CONTACTS_RE = re.compile(
    r"(?:taux de suivi des contacts|suivi des contacts|proportion des contacts suivis)"
    r".{0,80}?(\d[\d,]*)\s*%",
    re.IGNORECASE | re.DOTALL,
)


def norm_pct(raw):
    return float(raw.replace(",", "."))


def main():
    pdfs = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")))
    print(f"{len(pdfs)} PDF trouvé(s) dans {REPORTS_DIR}/\n")

    results = []
    found = 0
    excluded = 0
    missing = []

    for pdf_path in pdfs:
        fallback_num = extract_number_from_filename(pdf_path)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        except Exception as e:
            print(f"  ! {os.path.basename(pdf_path)} : erreur de lecture ({e})")
            continue

        meta = extract_meta(full_text, fallback_number=fallback_num)
        if meta.get("sitrepNumber") in CONTACTS_EXCLUDED_SITREPS:
            excluded += 1
            continue
        m = CONTACTS_RE.search(full_text)
        if m and meta.get("reportingDate"):
            results.append({
                "date": meta["reportingDate"],
                "sitrepNumber": meta["sitrepNumber"],
                "contactsFollowUpRate": norm_pct(m.group(1)),
                "source": "SitRep INSP (automatique)",
            })
            found += 1
        else:
            missing.append(meta.get("sitrepNumber") or fallback_num)

    # Une seule valeur par date (comme sitreps.json) : si deux rapports
    # partagent une date, on garde le dernier rencontré (ordre croissant de
    # numéro), avec un avertissement si les deux valeurs diffèrent.
    by_date = {}
    for r in results:
        existing = by_date.get(r["date"])
        if existing and existing["contactsFollowUpRate"] != r["contactsFollowUpRate"]:
            print(f"  ! ATTENTION : dates en double pour {r['date']} avec des valeurs "
                  f"différentes ({existing['contactsFollowUpRate']}% puis "
                  f"{r['contactsFollowUpRate']}% pour le SitRep {r['sitrepNumber']})")
        by_date[r["date"]] = r

    # Préserve tout point déjà présent dans le fichier qui ne vient PAS de
    # cette extraction automatique (ex: lecture manuelle des rapports OMS,
    # marquée par un "source" différent) — sans ce garde-fou, exécuter ce
    # script automatiquement chaque jour effacerait silencieusement ces
    # ajouts manuels à chaque régénération. Une vraie donnée INSP fraîche
    # reste toujours prioritaire si elle existe pour la même date (source
    # primaire), le point manuel n'intervient qu'en comblement de trou.
    preserved = 0
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            previous = json.load(f)
        for e in previous:
            if "INSP" in (e.get("source") or "") :
                continue  # sera régénéré fraîchement ci-dessus si toujours valide
            if e["date"] not in by_date:
                by_date[e["date"]] = e
                preserved += 1

    final = sorted(by_date.values(), key=lambda r: r["date"])

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\n{OUTPUT_PATH} écrit : {len(final)} point(s) de données "
          f"({found}/{len(pdfs)} rapports exploitables, {excluded} exclu(s) "
          f"volontairement, {preserved} point(s) manuel(s) préservé(s) — voir "
          f"CONTACTS_EXCLUDED_SITREPS).")
    if missing:
        print(f"Rapports sans cette donnée ({len(missing)}) : {missing}")


if __name__ == "__main__":
    main()
