#!/usr/bin/env python3
"""
Diagnostic : pour un PDF précis, montre pourquoi l'extraction du tableau
"Répartition des cas et décès confirmés par province touchée" échoue —
compare le chemin tableau (extract_province_summary + parse_province_summary)
et le chemin texte de repli (parse_province_summary_from_text), avec le
détail de ce que chacun trouve ou ne trouve pas.

Usage: python3 scripts/inspect_province_summary.py reports/SITREP_MVE_086.pdf
"""
import sys
import pdfplumber

from update_data import (
    extract_province_summary,
    parse_province_summary,
    parse_province_summary_from_text,
)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/inspect_province_summary.py <chemin_du_pdf>")
        return 1
    pdf_path = sys.argv[1]

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        print("=" * 90)
        print("CHEMIN TABLEAU (extract_province_summary)")
        print("=" * 90)
        prov_table = extract_province_summary(pdf)
        if prov_table is None:
            print("extract_province_summary() n'a RIEN trouvé.")
        else:
            print(f"Table trouvée, {len(prov_table)} ligne(s) brute(s) :")
            for row in prov_table:
                print(" ", repr(row))
            provinces, total_row = parse_province_summary(prov_table)
            print()
            print(f"parse_province_summary() en tire {len(provinces)} province(s) :")
            for p in provinces:
                print(" ", p)

    print()
    print("=" * 90)
    print("CHEMIN TEXTE DE REPLI (parse_province_summary_from_text)")
    print("=" * 90)
    start = full_text.find("Répartition des cas et décès confirmés par province touchée")
    end = full_text.find("Cas et décès confirmés par province et zone de santé")
    print(f"Marqueur de début trouvé : {start != -1} (position {start})")
    print(f"Marqueur de fin trouvé   : {end != -1} (position {end})")
    if start != -1 and end != -1:
        print()
        print("--- Contenu de la section repérée ---")
        print(full_text[start:end])
        print("--- fin de la section ---")
    provinces2, total2 = parse_province_summary_from_text(full_text)
    print()
    print(f"parse_province_summary_from_text() en tire : "
          f"{len(provinces2) if provinces2 else 0} province(s)")
    if provinces2:
        for p in provinces2:
            print(" ", p)


if __name__ == "__main__":
    main()
