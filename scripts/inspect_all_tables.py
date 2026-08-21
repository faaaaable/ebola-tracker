#!/usr/bin/env python3
"""
Diagnostic approfondi : montre TOUTES les tables brutes détectées par
pdfplumber sur les premières pages (pas seulement celle choisie par
extract_province_summary), plus le contexte textuel autour de "Ituri" —
pour comprendre le vrai format d'un rapport où le tableau par province
n'est pas extrait correctement.

Usage: python3 scripts/inspect_all_tables.py reports/SITREP_MVE_057.pdf
"""
import sys
import pdfplumber


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/inspect_all_tables.py <chemin_du_pdf>")
        return 1
    pdf_path = sys.argv[1]

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        print("=" * 90)
        print("TOUTES LES TABLES BRUTES, PAGE PAR PAGE (3 premières pages)")
        print("=" * 90)
        for page_num, page in enumerate(pdf.pages[:3]):
            tables = page.extract_tables()
            print(f"\n--- Page {page_num+1} : {len(tables)} table(s) ---")
            for i, table in enumerate(tables):
                print(f"  Table {i+1} ({len(table)} ligne(s)) :")
                for row in table:
                    print("   ", repr(row))

    print()
    print("=" * 90)
    print("CONTEXTE AUTOUR DE 'ITURI' DANS LE TEXTE BRUT")
    print("=" * 90)
    lines = full_text.split("\n")
    for i, line in enumerate(lines):
        if "ituri" in line.lower():
            start = max(0, i-3)
            end = min(len(lines), i+4)
            print(f"\n--- autour de la ligne {i} ---")
            for j in range(start, end):
                marker = ">> " if j == i else "   "
                print(f"{marker}{lines[j]}")


if __name__ == "__main__":
    main()
