#!/usr/bin/env python3
"""
Diagnostic pour maximiser la couverture des données communautaire/intra-CTE :

1. Liste, pour chaque numéro de 059 à 093, si un PDF existe réellement dans
   reports/ — distingue "fichier absent" de "fichier présent mais donnée
   non exploitable" (jusqu'ici confondus silencieusement).
2. Pour le SitRep 059 spécifiquement (le seul dans la fenêtre où un PDF
   existe et où la table est trouvée mais aucune ligne de province n'a été
   validée), dump la table brute complète pour comprendre ce qui bloque.
3. Pour tout SitRep hors de la table structurée (avant 060, ou comme 087),
   cherche quand même une mention narrative nationale (moins précis, pas
   de détail par province, mais mieux que rien).

N'écrit aucun fichier de données — diagnostic seul.

Usage: python3 scripts/diagnose_community_deaths_gaps.py
"""
import glob
import os
import re

import pdfplumber

REPORTS_DIR = "reports"

COMMUNITY_MENTION_RE = re.compile(
    r"[^.\n]*communaut[^.\n]*décès[^.\n]*\.|[^.\n]*décès[^.\n]*communaut[^.\n]*\.",
    re.IGNORECASE
)


def report_number(path):
    m = re.search(r"(\d{3})", os.path.basename(path))
    return m.group(1) if m else "???"


def find_report_by_number(number):
    for p in glob.glob(os.path.join(REPORTS_DIR, "*.pdf")):
        if report_number(p) == number:
            return p
    return None


def main():
    print("=" * 90)
    print("ÉTAPE 1 : présence réelle des PDF entre 001 et 093")
    print("=" * 90)

    present, absent = [], []
    for i in range(1, 94):
        num = f"{i:03d}"
        path = find_report_by_number(num)
        if path:
            present.append(num)
        else:
            absent.append(num)

    print(f"Présents ({len(present)}) : {present}")
    print(f"ABSENTS  ({len(absent)}) : {absent}")

    print(f"\n{'=' * 90}")
    print("ÉTAPE 2 : dump brut de la table du SitRep 059 (échec inexpliqué)")
    print(f"{'=' * 90}")
    path_059 = find_report_by_number("059")
    if not path_059:
        print("059 introuvable, rien à dumper.")
    else:
        with pdfplumber.open(path_059) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                for t_idx, table in enumerate(page.extract_tables()):
                    if not table:
                        continue
                    header_blob = " ".join(str(c) for row in table[:5] for c in row if c)
                    if "cumulatif" in header_blob.lower() or "communaut" in header_blob.lower():
                        print(f"\n--- Page {page_num}, tableau {t_idx + 1} ({len(table)} lignes) ---")
                        for row_idx, row in enumerate(table):
                            print(f"  [{row_idx:>3}] {row}")

    print(f"\n{'=' * 90}")
    print("ÉTAPE 3 : mentions narratives nationales — TOUS les SitRep 001-093")
    print("(y compris avant le 060, où aucune table structurée n'existe :")
    print(" seule cette mention narrative peut donner un point nationnal)")
    print(f"{'=' * 90}")
    found_count = 0
    for num in present:
        path = find_report_by_number(num)
        with pdfplumber.open(path) as pdf:
            full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        mentions = COMMUNITY_MENTION_RE.findall(full_text)
        if mentions:
            found_count += 1
            print(f"[{num}] {mentions[0].strip()[:200]}")

    print(f"\nTotal : {found_count} SitRep avec au moins une mention narrative "
          f"sur {len(present)} présents.")


if __name__ == "__main__":
    main()
