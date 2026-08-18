#!/usr/bin/env python3
"""
Extrait, pour chaque SitRep où la donnée existe, les décès COMMUNAUTAIRES
et INTRA-CTE DU JOUR (pas un cumul — cette ventilation n'est publiée que
comme delta quotidien, voir diagnostic précédent) au niveau de chaque
PROVINCE, dans le tableau combiné "Nombre cumulatif / Situation du jour".

Limité aux lignes de PROVINCE (ITURI, NORD-KIVU, etc.) plutôt qu'au détail
par zone : moins de lignes à traiter, donc moins de risque qu'un décalage
de colonnes (le remplissage des cellules vides varie entre None et ''
selon les rapports) ne produise un chiffre faux plutôt qu'une valeur
simplement absente.

Garde-fou clé : pour chaque ligne retenue, on vérifie que
communautaires + intra-CTE == total décès du jour. Si ce n'est pas le cas,
la ligne est ignorée (pas de donnée plutôt qu'une donnée fausse).

Écrit data/community-deaths-daily.json — une entrée par SitRep validé,
avec le détail par province ET le total national. Fusionne avec l'existant
(jamais d'écrasement).

Usage: python3 scripts/extract_community_deaths.py
"""
import glob
import json
import os
import re
import unicodedata

import pdfplumber

REPORTS_DIR = "reports"
OUTPUT_PATH = "data/community-deaths-daily.json"

PROVINCE_CANON = {
    "ituri": "Ituri", "nord-kivu": "Nord-Kivu", "nord kivu": "Nord-Kivu",
    "sud-kivu": "Sud-Kivu", "sud kivu": "Sud-Kivu",
    "haut-uele": "Haut-Uélé", "haut uele": "Haut-Uélé",
    "tshopo": "Tshopo",
    "bas-uele": "Bas-Uélé", "bas uele": "Bas-Uélé",
}


def normalize(s):
    s = unicodedata.normalize("NFD", str(s).strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def norm_num(s):
    if s is None:
        return None
    digits = re.sub(r"[^\d]", "", str(s))
    return int(digits) if digits else None


def report_number(path):
    m = re.search(r"(\d{3})", os.path.basename(path))
    return m.group(1) if m else "???"


def extract_meta_date(full_text):
    months = {
        "janvier": "01", "février": "02", "mars": "03", "avril": "04",
        "mai": "05", "juin": "06", "juillet": "07", "août": "08",
        "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12",
    }
    m = re.search(r"Date de rapportage\s*:?\s*(\d{1,2})\s+(\w+)\s+(\d{4})", full_text, re.IGNORECASE)
    if not m:
        return None
    d, mo, y = m.groups()
    mon = months.get(mo.lower())
    if not mon:
        return None
    return f"{y}-{mon}-{int(d):02d}"


def find_combined_table(pdf):
    """Cherche la table 'Nombre cumulatif / Situation du jour' — distincte
    du simple résumé par province (Tableau 1, sans ventilation
    communautaire/intra-CTE)."""
    for page in pdf.pages:
        for table in page.extract_tables():
            if not table:
                continue
            header_blob = " ".join(str(c) for row in table[:5] for c in row if c)
            if "Nombre cumulatif" in header_blob and "Situation du jour" in header_blob:
                return table
    return None


def parse_province_rows(table):
    """Ne retient que les lignes dont le premier token compacté correspond
    à un nom de province connu. Pour chaque ligne retenue, extrait les 3
    dernières valeurs numériques (communautaires, intra-CTE, total) et
    valide leur cohérence interne avant de les accepter."""
    results = {}
    for row in table:
        # On ne retire QUE les None ici (pas les '', qui peuvent représenter
        # un vrai zéro affiché comme cellule vide plutôt que comme '0').
        compact = [v for v in row if v is not None]
        if not compact:
            continue
        name_norm = normalize(compact[0])
        if name_norm not in PROVINCE_CANON:
            continue

        # Ne garde que les tokens numériques/pourcentages parmi les
        # suivants (ignore les '' de remplissage à ce stade).
        numeric_tokens = [t for t in compact[1:] if str(t).strip() != ""]
        if len(numeric_tokens) < 7:
            continue  # ligne incomplète, ignorée par prudence

        # Les 3 dernières valeurs numériques doivent être
        # [communautaires, intra-CTE, total décès du jour].
        try:
            community = norm_num(numeric_tokens[-3])
            intra_cte = norm_num(numeric_tokens[-2])
            total = norm_num(numeric_tokens[-1])
        except (IndexError, ValueError):
            continue

        if community is None or intra_cte is None or total is None:
            continue
        if community + intra_cte != total:
            continue  # incohérence interne : probable décalage de colonnes, ignorée

        province = PROVINCE_CANON[name_norm]
        results[province] = {"communityDeaths": community, "intraCteDeaths": intra_cte, "totalDeaths": total}

    return results


def main():
    paths = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")), key=report_number)
    validated = []

    for path in paths:
        num = report_number(path)
        try:
            with pdfplumber.open(path) as pdf:
                full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                table = find_combined_table(pdf)
        except Exception as e:
            print(f"[{num}] erreur d'ouverture : {e}")
            continue

        if table is None:
            continue  # table absente pour ce SitRep (format différent), silencieusement ignoré

        date = extract_meta_date(full_text)
        if not date:
            print(f"[{num}] date introuvable, ignoré.")
            continue

        provinces = parse_province_rows(table)
        if not provinces:
            print(f"[{num}] ({date}) : table trouvée mais aucune ligne de province validée, ignoré.")
            continue

        national_community = sum(p["communityDeaths"] for p in provinces.values())
        national_intra_cte = sum(p["intraCteDeaths"] for p in provinces.values())
        national_total = sum(p["totalDeaths"] for p in provinces.values())

        validated.append({
            "sitrep": num, "date": date,
            "provinces": provinces,
            "nationalCommunityDeaths": national_community,
            "nationalIntraCteDeaths": national_intra_cte,
            "nationalTotalDeaths": national_total,
        })
        print(f"[{num}] ({date}) : VALIDÉ — {len(provinces)} province(s), "
              f"national {national_community} communautaires / {national_intra_cte} intra-CTE "
              f"(total {national_total}).")

    if not validated:
        print("\nAucun SitRep validé, rien à écrire.")
        return 0

    existing = []
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    by_sitrep = {e["sitrep"]: e for e in existing}
    for entry in validated:
        by_sitrep[entry["sitrep"]] = entry
    merged = sorted(by_sitrep.values(), key=lambda e: e["date"])

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\n{OUTPUT_PATH} mis à jour : {len(merged)} jour(s) au total "
          f"({len(validated)} nouveau(x)/rafraîchi(s)).")
    return 0


if __name__ == "__main__":
    main()
