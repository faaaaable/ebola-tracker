#!/usr/bin/env python3
"""
Affiche les lignes brutes extraites par extract_zone_detail_rows() — telles
que pdfplumber découpe les cellules du tableau — pour diagnostiquer les cas
où un nom de province n'est pas reconnu exactement (espace, fragment de
cellule mal séparé, etc.) et finit traité comme une fausse "zone".

Usage: python3 scripts/inspect_raw_zone_rows.py reports/SITREP_MVE_096.pdf
"""
import sys
import pdfplumber

from update_data import extract_zone_detail_rows, PROVINCE_NAMES_MAIN


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/inspect_raw_zone_rows.py <chemin_du_pdf>")
        return 1
    pdf_path = sys.argv[1]

    with pdfplumber.open(pdf_path) as pdf:
        rows = extract_zone_detail_rows(pdf)

    print(f"{len(rows)} ligne(s) brute(s) extraite(s) par extract_zone_detail_rows().\n")
    print("=" * 90)
    for i, row in enumerate(rows):
        name = row[0] if row else None
        is_province_like = any(
            (name or "").replace("-", " ").strip().upper() == p.replace("-", " ").upper()
            for p in PROVINCE_NAMES_MAIN
        )
        marker = " <-- ressemble à un nom de province" if is_province_like else ""
        print(f"{i:3} | repr={row!r}{marker}")
    print("=" * 90)


if __name__ == "__main__":
    main()
