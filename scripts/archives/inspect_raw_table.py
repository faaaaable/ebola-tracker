#!/usr/bin/env python3
"""
Dump TOUTES les lignes (pas juste l'en-tête) des tableaux détectés par
pdfplumber sur un ou plusieurs SitRep, pour évaluer si l'extraction par
TABLE BRUTE garde mieux l'alignement des colonnes que le texte linéaire
(utilisé
par extract_old_zone_format.py, qui avait échoué sur ce format).

Ne filtre que les tableaux dont l'en-tête contient "Province" ou
"Zones de santé" ou "zone de santé", pour éviter de dumper les tableaux
sans intérêt (PoE/PoC, laboratoire, etc.).

Usage: python3 scripts/inspect_raw_table.py 060,074,081,088,093
       python3 scripts/inspect_raw_table.py 007
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


def looks_relevant(table):
    if not table or not table[0]:
        return False
    header_text = " ".join(str(c) for c in table[0] if c)
    return bool(re.search(r"province|zone.*sant", header_text, re.IGNORECASE))


def dump_one(number):
    pdf_path = find_report_by_number(number)
    if not pdf_path:
        print(f"### SitRep {number} : aucun PDF trouvé, ignoré.\n")
        return

    print(f"\n{'#' * 80}")
    print(f"### SitRep {number} — {pdf_path}")
    print(f"{'#' * 80}\n")

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for t_idx, table in enumerate(tables):
                if not looks_relevant(table):
                    continue
                print("=" * 80)
                print(f"Page {page_num}, tableau {t_idx + 1} — {len(table)} lignes")
                print("=" * 80)
                for row_idx, row in enumerate(table):
                    print(f"  [{row_idx:>3}] {row}")
                print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/inspect_raw_table.py <numéro(s), ex: 007 ou 060,074,081>")
        return 1

    # Accepte un ou plusieurs numéros séparés par des virgules (et/ou espaces).
    numbers = [n.strip() for n in re.split(r"[,\s]+", sys.argv[1]) if n.strip()]
    for number in numbers:
        dump_one(number)

    return 0


if __name__ == "__main__":
    sys.exit(main())
