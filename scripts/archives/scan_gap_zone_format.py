#!/usr/bin/env python3
"""
Scanne TOUS les SitRep archivés pour détecter la présence du format
"Tableau 2. Répartition des cas et décès confirmés... par province et
zone de santé" — un troisième format de détail par zone, distinct des
deux autres déjà cartographiés (le format "Sous total" de mai, et le
format actuel avec colonnes 24h) : ici seulement 3 colonnes cumulées
(Cas confirmés cumulés / Décès confirmés cumulés / Létalité), avec les
noms de province en MAJUSCULES suivis des zones en-dessous (vu sur le
SitRep 046, 29 juin 2026).

Heuristique : présence du texte "confirmés cumulés" (qui n'apparaît pas
dans les deux autres formats) et d'un bloc "Province / Zone de santé"
avec "Létalité (CFR". N'écrit aucun fichier, diagnostic seul.

Usage: python3 scripts/scan_gap_zone_format.py
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

    print(f"Scan de {len(pdfs)} SitRep pour le format 'cas/décès cumulés à 3 colonnes'...\n")

    results = []
    for pdf_path in pdfs:
        fname = os.path.basename(pdf_path)
        m = re.search(r"(\d{3})", fname)
        number = m.group(1) if m else "???"
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            # "cumulés (n)" est le motif d'en-tête de colonne le plus fiable :
            # "confirmés" et "cumulés" se retrouvent souvent séparés par un
            # retour à la ligne (colonnes wrappées), donc on ne les cherche
            # pas adjacents.
            has_marker = bool(re.search(r"cumulés\s*\(n\)", full_text, re.IGNORECASE))
            has_header = bool(re.search(r"Province\s*/\s*Zone de santé", full_text, re.IGNORECASE))
            # Compte les lignes "PROVINCE_EN_MAJUSCULES nombre nombre pourcentage%"
            # (ex: "ITURI 1214 335 27,6%") pour confirmer la structure, pas
            # juste la présence du mot-clé isolé.
            province_total_lines = len(re.findall(
                r"^(ITURI|NORD-KIVU|SUD-KIVU|HAUT-UÉLÉ|TSHOPO|BAS-UÉLÉ)\s+\d+\s+\d+\s+[\d,]+%",
                full_text, re.MULTILINE
            ))
            results.append((number, fname, has_marker, has_header, province_total_lines))
        except Exception as e:
            results.append((number, fname, False, False, -1))
            print(f"  ! Erreur sur {fname} : {e}")

    print("=" * 78)
    print("RÉSULTAT : présence du format 'cas/décès cumulés à 3 colonnes'")
    print("=" * 78)
    print(f"{'N°':<6}{'confirmés cumulés':<20}{'Province/Zone hdr':<20}{'Lignes province MAJ':<20}")
    print("-" * 78)

    likely_matches = []
    for number, fname, has_marker, has_header, prov_lines in results:
        is_match = has_marker and prov_lines >= 2
        marker = " <-- probable" if is_match else ""
        print(f"{number:<6}{str(has_marker):<20}{str(has_header):<20}{prov_lines:<20}{marker}")
        if is_match:
            likely_matches.append(number)

    print()
    print("=" * 78)
    print(f"SitRep probablement au format 'cumulés à 3 colonnes' ({len(likely_matches)}) :")
    print(", ".join(likely_matches) if likely_matches else "(aucun)")
    print("=" * 78)

    return 0


if __name__ == "__main__":
    sys.exit(main())
