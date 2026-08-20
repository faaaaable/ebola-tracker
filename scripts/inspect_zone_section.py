#!/usr/bin/env python3
"""
Affiche la section "Cas et décès confirmés par province et zone de santé"
d'un PDF précis, TELLE QUE le pipeline la découpe réellement (réutilise
get_zone_section_text() de update_data.py) — pour diagnostiquer les cas où
des en-têtes de province sont mal reconnus et finissent traités comme de
fausses "zones".

Usage: python3 scripts/inspect_zone_section.py reports/SITREP_MVE_096.pdf
"""
import sys
import pdfplumber

from update_data import get_zone_section_text


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/inspect_zone_section.py <chemin_du_pdf>")
        return 1
    pdf_path = sys.argv[1]

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

    section = get_zone_section_text(full_text)
    if not section:
        print("! get_zone_section_text() n'a rien trouvé — les marqueurs de "
              "début/fin de section ne correspondent à rien dans ce PDF.")
        return 1

    print(f"Section trouvée : {len(section)} caractères, "
          f"{len(section.splitlines())} lignes.")
    print("=" * 90)
    for i, line in enumerate(section.splitlines()):
        print(f"{i:4} | {line}")
    print("=" * 90)


if __name__ == "__main__":
    main()
