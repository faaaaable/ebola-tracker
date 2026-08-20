#!/usr/bin/env python3
"""
Diagnostic : vérifie sur TOUS les SitReps déjà téléchargés (reports/*.pdf)
si deux métriques précises sont extractibles de façon fiable :
  1. Taux de suivi des contacts (%)
  2. Nombre de personnes passées aux PoE/PoC (dépistées)

Ne modifie aucune donnée du site — sortie purement informative, pour décider
si ça vaut le coup de construire de nouveaux graphiques dessus.

Usage: python3 scripts/scan_contacts_poepoc.py
"""
import glob
import os
import re

import pdfplumber

REPORTS_DIR = "reports"

CONTACTS_RE = re.compile(
    r"(?:taux de suivi des contacts|suivi des contacts|proportion des contacts suivis)"
    r".{0,80}?(\d[\d,]*)\s*%",
    re.IGNORECASE | re.DOTALL,
)
POEPOC_RE = re.compile(
    r"(\d[\d\s]{2,10}\d)\s*(?:voyageurs|personnes)?\s*(?:dépisté(?:e)?s?|contrôlé(?:e)?s?|screened)",
    re.IGNORECASE,
)


def extract_number_from_filename(path):
    m = re.search(r"(\d{3})[-_]?(bis|ter|quater)?", os.path.basename(path), re.IGNORECASE)
    if not m:
        return None
    num, suffix = m.group(1), m.group(2)
    return f"{num}-{suffix.lower()}" if suffix else num


def main():
    pdfs = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")))
    print(f"{len(pdfs)} PDF trouvé(s) dans {REPORTS_DIR}/\n")

    found_contacts = 0
    found_poepoc = 0
    missing_contacts = []
    missing_poepoc = []
    sample_contacts = []
    sample_poepoc = []

    for pdf_path in pdfs:
        num = extract_number_from_filename(pdf_path) or "???"
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        except Exception as e:
            print(f"  ! {os.path.basename(pdf_path)} : erreur de lecture ({e})")
            continue

        m1 = CONTACTS_RE.search(full_text)
        if m1:
            found_contacts += 1
            if len(sample_contacts) < 5:
                sample_contacts.append((num, m1.group(1)))
        else:
            missing_contacts.append(num)

        m2 = POEPOC_RE.search(full_text)
        if m2:
            found_poepoc += 1
            if len(sample_poepoc) < 5:
                sample_poepoc.append((num, m2.group(1).replace(" ", "")))
        else:
            missing_poepoc.append(num)

    total = len(pdfs)
    print("=" * 70)
    print(f"Taux de suivi des contacts : trouvé dans {found_contacts}/{total} rapports")
    print(f"  Échantillon : {sample_contacts}")
    if missing_contacts:
        print(f"  Absent pour {len(missing_contacts)} rapport(s) : "
              f"{missing_contacts[:15]}{'...' if len(missing_contacts) > 15 else ''}")
    print()
    print(f"PoE/PoC (personnes dépistées) : trouvé dans {found_poepoc}/{total} rapports")
    print(f"  Échantillon : {sample_poepoc}")
    if missing_poepoc:
        print(f"  Absent pour {len(missing_poepoc)} rapport(s) : "
              f"{missing_poepoc[:15]}{'...' if len(missing_poepoc) > 15 else ''}")
    print("=" * 70)


if __name__ == "__main__":
    main()
