#!/usr/bin/env python3
"""
Rattrapage ciblé : reconstruit l'entrée d'UN SitRep précis dans
data/zones-history.json, sans toucher au reste du fichier ni relancer tout
le pipeline habituel (qui ne retraite que le SitRep le plus récent).

Utile quand une entrée a disparu de zones-history.json pour une raison
externe au pipeline lui-même (ex: conflit git, incident de push) alors que
le PDF source est toujours intact dans reports/ — comme le SitRep 093
(15 août 2026), disparu après l'ajout du SitRep 094 (19/08/2026).

Réutilise directement les fonctions d'extraction de update_data.py plutôt
que de dupliquer la logique.

Usage: python3 scripts/backfill_zones_history.py reports/SITREP_MVE_093.pdf
"""
import sys
import pdfplumber

from update_data import (
    extract_meta,
    extract_zone_detail_rows,
    parse_zone_detail,
    revalidate_zones,
    zone_row_to_dict,
    rebuild_zones_history,
)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/backfill_zones_history.py <chemin_du_pdf>")
        return 1
    pdf_path = sys.argv[1]

    import os
    import re
    fallback_num = None
    fm = re.search(r"(\d{3})", os.path.basename(pdf_path))
    if fm:
        fallback_num = fm.group(1)

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        meta = extract_meta(full_text, fallback_number=fallback_num)

        zone_rows = extract_zone_detail_rows(pdf)
        _, zones_raw, _ = parse_zone_detail(zone_rows)
        zones_raw = revalidate_zones(full_text, zones_raw)

    health_zones = [zone_row_to_dict(prov, name, row) for prov, name, row in zones_raw]

    print(f"SitRep {meta['sitrepNumber']} ({meta['reportingDate']}) : "
          f"{len(health_zones)} zone(s) extraite(s).")

    rebuild_zones_history(meta, health_zones)


if __name__ == "__main__":
    main()
