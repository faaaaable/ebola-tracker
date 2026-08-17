#!/usr/bin/env python3
"""
Scanne TOUS les SitRep archivés pour détecter lesquels contiennent le
format "ancien" de détail par zone : une table où les zones de santé sont
groupées sous des en-têtes de province, avec une ligne "Sous total" après
chaque groupe et une ligne "Total" générale à la fin (vu sur les SitRep
005, 007, 009, 010 lors de l'inspection manuelle).

Ce format n'est pas déjà couvert par diagnose_reports.py, qui teste
l'extraction du format ACTUEL (table province séparée + table zones avec
colonnes différentes) — un SitRep peut donc apparaître "en échec" dans ce
diagnostic-là tout en ayant un détail par zone exploitable via CE format
ancien, et inversement.

Heuristique utilisée : compter les occurrences de "Sous total" dans le
texte brut. Le format ancien en a une par province touchée (typiquement
2 à 4 sur cette période) ; son absence signale que ce format n'est pas
utilisé dans ce SitRep (soit le format narratif du tout début, soit le
format "résumé province uniquement" qui a suivi).

N'écrit aucun fichier de données. Affiche un résumé compact.

Usage: python3 scripts/scan_old_zone_format.py
"""
import glob
import os
import re
import sys

import pdfplumber

REPORTS_DIR = "reports"


def main():
    pdfs = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")))
    if not pdfs:
        print("Aucun PDF trouvé dans reports/.")
        return 1

    print(f"Scan de {len(pdfs)} SitRep pour le format 'sous-totaux par province'...\n")

    results = []
    for pdf_path in pdfs:
        fname = os.path.basename(pdf_path)
        m = re.search(r"(\d{3})", fname)
        number = m.group(1) if m else "???"
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            sous_total_count = len(re.findall(r"Sous\s*total", full_text, re.IGNORECASE))
            has_total = bool(re.search(r"\bTotal\b", full_text))
            results.append((number, fname, sous_total_count, has_total))
        except Exception as e:
            results.append((number, fname, -1, False))
            print(f"  ! Erreur sur {fname} : {e}")

    print("=" * 72)
    print("RÉSULTAT : présence du format 'Sous total par province'")
    print("=" * 72)
    print(f"{'N°':<6}{'Occurrences Sous total':<26}{'A un Total':<12}")
    print("-" * 72)

    likely_old_format = []
    for number, fname, count, has_total in results:
        marker = " <-- probable" if count >= 1 else ""
        print(f"{number:<6}{count:<26}{str(has_total):<12}{marker}")
        if count >= 1:
            likely_old_format.append(number)

    print()
    print("=" * 72)
    print(f"SitRep probablement au format 'ancien avec sous-totaux' ({len(likely_old_format)}) :")
    print(", ".join(likely_old_format) if likely_old_format else "(aucun)")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    sys.exit(main())
