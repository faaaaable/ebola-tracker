#!/usr/bin/env python3
"""
Inspecte UN SEUL SitRep en détail pour comprendre pourquoi l'extraction de
la table province (et donc du national confirmed/deaths) échoue dessus.

N'affiche PAS le contenu intégral du PDF : seulement les en-têtes de tous
les tableaux détectés par pdfplumber sur chaque page, la première ligne de
donnée de chaque tableau, et un court extrait de texte brut autour des
mots-clés "Province" et "zone de santé" (quelques lignes avant/après),
pour comprendre la structure sans exposer tout le bulletin.

Usage: python3 scripts/inspect_report.py 010
(le numéro est cherché dans le nom de fichier, comme find_latest_report)
"""
import glob
import os
import re
import sys

import pdfplumber


REPORTS_DIR = "reports"


def find_report_by_number(number):
    number = number.zfill(3)
    for p in glob.glob(os.path.join(REPORTS_DIR, "*.pdf")):
        m = re.search(r"(\d{3})", os.path.basename(p))
        if m and m.group(1) == number:
            return p
    return None


def print_text_context(full_text, keyword, context_lines=3):
    lines = full_text.split("\n")
    found_any = False
    for i, line in enumerate(lines):
        if keyword.lower() in line.lower():
            found_any = True
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            print(f"  --- autour de la ligne {i} (mot-clé « {keyword} ») ---")
            for j in range(start, end):
                marker = ">> " if j == i else "   "
                print(f"  {marker}{lines[j]}")
            print()
    if not found_any:
        print(f"  (mot-clé « {keyword} » introuvable dans le texte de ce SitRep)\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/inspect_report.py <numéro, ex: 010>")
        return 1

    number = sys.argv[1]
    pdf_path = find_report_by_number(number)
    if not pdf_path:
        print(f"Aucun PDF trouvé pour le numéro {number} dans {REPORTS_DIR}/.")
        return 1

    print(f"Inspection de {pdf_path}\n")
    print("=" * 72)
    print("EN-TÊTES DE TOUS LES TABLEAUX DÉTECTÉS (page par page)")
    print("=" * 72)

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])

        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if not tables:
                continue
            print(f"\n--- Page {page_num} : {len(tables)} tableau(x) détecté(s) ---")
            for t_idx, table in enumerate(tables):
                if not table:
                    continue
                header = table[0]
                first_data_row = table[1] if len(table) > 1 else None
                print(f"  Tableau {t_idx + 1} ({len(table)} lignes) :")
                print(f"    en-tête      : {header}")
                print(f"    1ère donnée  : {first_data_row}")

        print()
        print("=" * 72)
        print("EXTRAIT DE TEXTE AUTOUR DES MOTS-CLÉS")
        print("=" * 72)
        print_text_context(full_text, "Province")
        print_text_context(full_text, "zone de santé")
        print_text_context(full_text, "Total")

    return 0


if __name__ == "__main__":
    sys.exit(main())
