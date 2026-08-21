#!/usr/bin/env python3
"""
Rattrapage complet : reconstruit data/province-history.json à partir de
TOUS les SitRep déjà téléchargés dans reports/, du tout premier au plus
récent — pour que le graphique "Cas cumulés / région" couvre toute
l'épidémie dès le premier lancement, sans attendre l'accumulation
quotidienne naturelle.

Réutilise directement les mêmes fonctions d'extraction que le pipeline
normal (extract_province_summary, parse_province_summary, repli texte
brut) — même fiabilité, pas de logique dupliquée.

Contrairement au détail par zone (parfois absent des tout premiers
SitRep), le total par province est présent dans la quasi-totalité des
rapports depuis le début — un historique quasi complet est donc attendu.

Usage: python3 scripts/backfill_province_history.py
"""
import glob
import os

import pdfplumber

from update_data import (
    extract_meta,
    extract_number_from_filename,
    extract_province_summary,
    parse_province_summary,
    parse_province_summary_from_text,
    rebuild_province_history,
)

REPORTS_DIR = "reports"


def main():
    pdfs = glob.glob(os.path.join(REPORTS_DIR, "*.pdf"))
    dated = []
    for p in pdfs:
        num = extract_number_from_filename(p)
        if num:
            dated.append((num, p))
    dated.sort(key=lambda t: t[0])

    print(f"{len(dated)} rapport(s) à traiter, du {dated[0][0]} au {dated[-1][0]}.\n")

    ok = 0
    failed = []
    for num, pdf_path in dated:
        fallback_num = extract_number_from_filename(pdf_path)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                meta = extract_meta(full_text, fallback_number=fallback_num)

                prov_table = extract_province_summary(pdf)
                if prov_table is not None:
                    provinces, _ = parse_province_summary(prov_table)
                else:
                    provinces, _ = parse_province_summary_from_text(full_text)
        except Exception as e:
            failed.append((num, f"erreur : {e}"))
            continue

        if not provinces:
            failed.append((num, "aucune donnée province exploitable"))
            continue

        rebuild_province_history(meta, provinces)
        ok += 1

    print(f"\n{ok}/{len(dated)} rapport(s) intégré(s) avec succès.")
    if failed:
        print(f"{len(failed)} rapport(s) sans donnée exploitable :")
        for num, reason in failed:
            print(f"  SitRep {num} : {reason}")


if __name__ == "__main__":
    main()
