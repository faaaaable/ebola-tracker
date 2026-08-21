#!/usr/bin/env python3
"""
Diagnostic groupé : pour TOUS les SitRep déjà téléchargés, catégorise
pourquoi l'extraction du tableau "Répartition par province touchée" a
échoué (ou réussi) — sans dumper le détail complet de chacun, juste un
résumé des causes, pour repérer un motif commun plutôt que d'inspecter
un rapport à la fois.

Usage: python3 scripts/scan_province_summary.py
"""
import glob
import os

import pdfplumber

from update_data import (
    extract_number_from_filename,
    extract_province_summary,
    parse_province_summary,
    parse_province_summary_from_text,
)


def diagnose_one(pdf_path):
    """Renvoie une courte étiquette expliquant le résultat pour ce PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            prov_table = extract_province_summary(pdf)
    except Exception as e:
        return f"ERREUR LECTURE ({e})"

    if prov_table is None:
        table_status = "table introuvable"
    else:
        provinces, _ = parse_province_summary(prov_table)
        table_status = f"table OK ({len(provinces)} prov.)" if provinces else "table trouvée mais 0 province extraite"

    if prov_table is not None:
        provinces, _ = parse_province_summary(prov_table)
        if provinces:
            return f"OK via tableau ({len(provinces)} provinces)"

    # Toujours appeler la vraie fonction — elle gère elle-même en interne le
    # cas où les marqueurs de section habituels sont absents (repli sur tout
    # le texte). Refaire ici une vérification préalable des marqueurs
    # court-circuitait ce repli et rendait ce diagnostic obsolète dès qu'un
    # correctif touchait parse_province_summary_from_text() sans que ce
    # script ne soit mis à jour en miroir.
    provinces2, total2 = parse_province_summary_from_text(full_text)
    if provinces2:
        return f"OK via texte ({len(provinces2)} provinces)"

    start = full_text.find("Répartition des cas et décès confirmés par province touchée")
    end = full_text.find("Cas et décès confirmés par province et zone de santé")
    markers_found = start != -1 and end != -1 and end > start
    text_status = ("marqueurs trouvés mais 0 province extraite (regex ne matche rien)"
                   if markers_found else
                   "marqueurs absents, repli plein texte tenté mais 0 province extraite")

    return f"ÉCHEC — {table_status} / {text_status}"


def main():
    pdfs = glob.glob(os.path.join("reports", "*.pdf"))
    dated = []
    for p in pdfs:
        num = extract_number_from_filename(p)
        if num:
            dated.append((num, p))
    dated.sort(key=lambda t: t[0])

    print(f"{len(dated)} rapport(s) à diagnostiquer.\n")
    print("=" * 90)

    from collections import Counter
    category_counts = Counter()

    for num, pdf_path in dated:
        result = diagnose_one(pdf_path)
        # Catégorie courte pour le comptage groupé
        if result.startswith("OK via tableau"):
            cat = "OK (tableau)"
        elif result.startswith("OK via texte"):
            cat = "OK (texte)"
        elif "table introuvable" in result and "marqueurs texte introuvables" in result:
            cat = "ÉCHEC total (rien trouvé nulle part)"
        elif "0 province extraite (regex" in result:
            cat = "ÉCHEC (marqueurs texte OK, mais regex ne matche rien)"
        elif "table trouvée mais 0 province" in result:
            cat = "ÉCHEC (table trouvée mais parsing à 0)"
        else:
            cat = "ÉCHEC (autre)"
        category_counts[cat] += 1
        print(f"{num:8} : {result}")

    print("=" * 90)
    print("\nRésumé par catégorie :")
    for cat, count in category_counts.most_common():
        print(f"  {count:3} × {cat}")


if __name__ == "__main__":
    main()
