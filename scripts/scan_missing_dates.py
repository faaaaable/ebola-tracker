#!/usr/bin/env python3
"""
Diagnostic groupé : pour chaque date manquante de zones-history.json (les
"trous" du curseur temporel de la carte), vérifie s'il existe un SitRep PDF
correspondant, et si oui pourquoi son détail par zone n'a jamais été
intégré (mise en page trop ancienne, section introuvable, etc.).

Ne modifie AUCUNE donnée — sortie purement informative, pour décider au cas
par cas quoi faire de chaque trou plutôt que de deviner.

Usage: python3 scripts/scan_missing_dates.py
"""
import glob
import os

import pdfplumber

from update_data import extract_meta, extract_number_from_filename, get_zone_section_text

REPORTS_DIR = "reports"

MISSING_DATES = [
    "2026-05-25", "2026-05-26",
    "2026-05-28", "2026-05-29", "2026-05-30", "2026-05-31",
    "2026-06-12",
    "2026-06-16",
    "2026-06-26",
    "2026-06-28",
    "2026-07-16",
    "2026-07-28", "2026-07-29",
    "2026-08-06", "2026-08-07", "2026-08-08", "2026-08-09",
]


def main():
    pdfs = glob.glob(os.path.join(REPORTS_DIR, "*.pdf"))

    # Indexe chaque PDF par sa date de rapportage réelle (pas son numéro),
    # pour retrouver directement le bon fichier pour chaque date manquante.
    by_date = {}
    for pdf_path in pdfs:
        fallback_num = extract_number_from_filename(pdf_path)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                meta = extract_meta(full_text, fallback_number=fallback_num)
        except Exception:
            continue
        if meta.get("reportingDate"):
            by_date[meta["reportingDate"]] = (pdf_path, meta["sitrepNumber"], full_text)

    print(f"{len(MISSING_DATES)} date(s) manquante(s) à vérifier.\n")
    print("=" * 90)

    for d in MISSING_DATES:
        if d not in by_date:
            print(f"{d} : AUCUN PDF trouvé pour cette date — probablement jamais publié par la source.")
            print("-" * 90)
            continue

        pdf_path, sitrep_num, full_text = by_date[d]
        section = get_zone_section_text(full_text)
        if not section:
            print(f"{d} (SitRep {sitrep_num}, {os.path.basename(pdf_path)}) : "
                  f"PDF présent, mais section zone-détail INTROUVABLE "
                  f"(mise en page trop ancienne/différente — même limite que le SitRep 010).")
        else:
            n_lines = len(section.splitlines())
            print(f"{d} (SitRep {sitrep_num}, {os.path.basename(pdf_path)}) : "
                  f"PDF présent, section trouvée ({n_lines} lignes) — "
                  f"EXTRACTION POSSIBLE, à rattraper avec backfill_zones_history.py.")
        print("-" * 90)

    print("=" * 90)


if __name__ == "__main__":
    main()
