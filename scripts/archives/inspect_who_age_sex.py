#!/usr/bin/env python3
"""
Diagnostic : extrait le texte complet de toute page mentionnant une
répartition par tranche d'âge/sexe, pour un rapport OMS donné — pour voir
si les chiffres sont du texte exploitable ou juste une image de graphique.

Usage: python3 scripts/inspect_who_age_sex.py reports/who/WHO_WeeklyExtSitRep_06_2026-06-21.pdf
"""
import sys
import pdfplumber


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/inspect_who_age_sex.py <chemin_du_pdf>")
        return 1
    path = sys.argv[1]

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if "age group and sex" in text.lower() or "age and sex" in text.lower():
                print(f"=== Page {i + 1} (texte complet) ===")
                print(text)
                print()
                tables = page.extract_tables()
                print(f"=== Page {i + 1} : {len(tables)} tableau(x) détecté(s) ===")
                for t in tables:
                    for row in t:
                        print(row)
                print()


if __name__ == "__main__":
    main()
