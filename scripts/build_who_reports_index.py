#!/usr/bin/env python3
"""
Construit data/who-reports.json à partir des PDF déjà présents dans
reports/who/ — le nom de fichier encode déjà le numéro et la date
(WHO_WeeklyExtSitRep_<numéro>_<date>.pdf), donc pas besoin de relire le
contenu des PDF pour cette liste.

Usage: python3 scripts/build_who_reports_index.py
"""
import glob
import json
import os
import re

WHO_REPORTS_DIR = "reports/who"
OUTPUT_PATH = "data/who-reports.json"

FILENAME_RE = re.compile(r"WHO_WeeklyExtSitRep_(\d+)_(\d{4}-\d{2}-\d{2})\.pdf$")


def main():
    paths = sorted(glob.glob(os.path.join(WHO_REPORTS_DIR, "*.pdf")))
    reports = []
    for path in paths:
        m = FILENAME_RE.search(os.path.basename(path))
        if not m:
            print(f"  ! nom de fichier inattendu, ignoré : {path}")
            continue
        reports.append({
            "number": m.group(1),
            "date": m.group(2),
            "file": path.replace("\\", "/"),
        })
    reports.sort(key=lambda r: r["number"])

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"{OUTPUT_PATH} écrit : {len(reports)} rapport(s) listé(s).")


if __name__ == "__main__":
    main()
