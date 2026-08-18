#!/usr/bin/env python3
"""
Diagnostic (pas d'extraction) : scanne l'ensemble des SitRep PDF à la
recherche de mentions d'un CUMUL de décès communautaires — par exemple
une phrase narrative du type "Au total de 392 décès sont enregistrés, dont
la majorité (359) est issue de la communauté... taux de létalité
communautaire global de 31,9%" — repérée dans au moins un SitRep (048).

But : évaluer si cette donnée est publiée de façon cohérente à travers
l'ensemble des bulletins (condition nécessaire avant d'envisager une
extraction fiable), et si un équivalent PAR PROVINCE existe quelque part
(table dédiée ou mention narrative).

N'écrit aucun fichier de données. Affiche un résumé de couverture, plus le
contexte exact trouvé pour chaque SitRep où une mention existe.

Usage: python3 scripts/scan_community_deaths.py
"""
import glob
import os
import re

import pdfplumber

REPORTS_DIR = "reports"

# Cherche une phrase contenant "communaut" (communauté/communautaire) à
# proximité du mot "décès" et d'au moins un nombre — plutôt qu'un motif
# rigide, on capture la phrase entière autour du terme pour revue humaine.
COMMUNITY_MENTION_RE = re.compile(
    r"[^.\n]*communaut[^.\n]*décès[^.\n]*\.|[^.\n]*décès[^.\n]*communaut[^.\n]*\.",
    re.IGNORECASE
)

PROVINCE_NAMES = ["Ituri", "Nord-Kivu", "Nord Kivu", "Sud-Kivu", "Sud Kivu",
                  "Haut-Uélé", "Haut-Uele", "Tshopo", "Bas-Uélé", "Bas-Uele"]


def report_number(path):
    m = re.search(r"(\d{3})", os.path.basename(path))
    return m.group(1) if m else "???"


def find_community_tables(pdf):
    """Cherche TOUTES les tables dont l'en-tête mentionne les décès
    communautaires (pas seulement la première trouvée — le paragraphe
    narratif "FAITS SAILLANTS" apparaît tôt dans le document et peut être
    extrait par pdfplumber comme un pseudo-tableau, masquant le vrai
    tableau détaillé par zone qui vient plus loin). Distingue la table
    cumulative structurée (contient aussi "cumulatif" ou "Total décès")
    du simple paragraphe narratif."""
    hits = []
    for page_num, page in enumerate(pdf.pages, start=1):
        for table in page.extract_tables():
            if not table:
                continue
            header_blob = " ".join(str(c) for row in table[:4] for c in row if c)
            if not re.search(r"communaut", header_blob, re.IGNORECASE):
                continue
            is_structured = bool(re.search(r"cumulatif|total\s*décès", header_blob, re.IGNORECASE))
            hits.append({
                "page": page_num,
                "structured": is_structured,
                "header": header_blob[:200],
                "n_rows": len(table),
            })
    return hits


def main():
    paths = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")),
                    key=lambda p: report_number(p))
    print(f"Scan de {len(paths)} SitRep...\n")

    found_national, missing_national, found_table = [], [], []

    for path in paths:
        num = report_number(path)
        try:
            with pdfplumber.open(path) as pdf:
                full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                table_hits = find_community_tables(pdf)
        except Exception as e:
            print(f"[{num}] ERREUR d'ouverture : {e}")
            continue

        mentions = COMMUNITY_MENTION_RE.findall(full_text)
        if mentions:
            found_national.append(num)
            print(f"[{num}] MENTION TROUVÉE : {mentions[0].strip()[:220]}")
        else:
            missing_national.append(num)

        structured_hits = [h for h in table_hits if h["structured"]]
        if structured_hits:
            found_table.append(num)
            best = structured_hits[-1]  # généralement la table détaillée, pas le résumé
            print(f"[{num}] TABLE CUMULATIVE structurée (page {best['page']}, "
                  f"{best['n_rows']} lignes) : {best['header']}")
        elif table_hits:
            print(f"[{num}] table 'communaut' trouvée mais non structurée "
                  f"(probablement narrative) : {table_hits[0]['header'][:150]}")

    print(f"\n{'=' * 90}")
    print("RÉSUMÉ DE COUVERTURE")
    print(f"{'=' * 90}")
    print(f"Mention narrative nationale trouvée : {len(found_national)}/{len(paths)} SitRep")
    print(f"  Présents : {found_national}")
    print(f"  Absents  : {missing_national}")
    print(f"\nTable dédiée avec 'communaut' dans l'en-tête : {len(found_table)}/{len(paths)} SitRep")
    print(f"  Présents : {found_table}")


if __name__ == "__main__":
    main()
