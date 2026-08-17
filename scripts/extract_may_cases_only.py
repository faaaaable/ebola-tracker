#!/usr/bin/env python3
"""
Extrait les CAS CONFIRMÉS CUMULÉS par zone (les décès confirmés cumulés ne
sont pas publiés par zone dans ces bulletins — seulement des décès
"suspects", une notion différente) pour les 8 SitRep de mai identifiés
comme ayant une table cumulative par zone : 005, 006, 007, 008, 009, 010,
013, 015 (voir scan_old_zone_format.py).

Contrairement au premier essai (extract_old_zone_format.py, qui parsait le
TEXTE linéaire et échouait à cause du mélange de plusieurs groupes de
colonnes), ce script lit directement la TABLE BRUTE de pdfplumber
(page.extract_tables()), qui préserve un alignement de colonnes bien plus
fiable. Chaque ligne est "compactée" (cellules vides retirées) : le nombre
de cellules restantes indique sans ambiguïté s'il s'agit d'une ligne
"province + zone" (6 cellules) ou "zone seule, province inchangée"
(5 cellules) — une technique bien plus robuste que des index fixes.

Comme précédemment, le total de la table est validé contre la valeur déjà
connue dans data/sitreps.json avant tout écrit : un SitRep dont le total ne
correspond pas exactement est ignoré, jamais deviné.

Les entrées produites ont un champ "deaths": null — le site (fmt() dans
index.html) affiche déjà '—' pour une valeur null, aucune modification du
site n'est nécessaire.

N'écrit dans data/zones-history.json qu'en fusionnant avec l'existant.

Usage: python3 scripts/extract_may_cases_only.py
"""
import glob
import json
import os
import re
import sys

import pdfplumber

REPORTS_DIR = "reports"
ZONES_HISTORY_PATH = "data/zones-history.json"
SITREPS_PATH = "data/sitreps.json"

TARGET_SITREPS = ["005", "006", "007", "008", "009", "010", "013", "015"]

PROVINCE_CANON = {
    "Ituri": "Ituri", "Nord-Kivu": "Nord-Kivu", "Nord Kivu": "Nord-Kivu",
    "Sud-Kivu": "Sud-Kivu", "Sud Kivu": "Sud-Kivu",
    "Haut-Uélé": "Haut-Uélé", "Tshopo": "Tshopo", "Bas-Uélé": "Bas-Uélé",
}

EXCLUDE_NAME_PREFIXES = ("echantillons",)


def norm_num(s):
    """Extrait le premier nombre d'une chaîne, en ignorant tout caractère
    non numérique (astérisques de renvoi, espaces de milliers, 'ND'...)."""
    if s is None:
        return None
    digits = re.sub(r"[^\d]", "", str(s))
    return int(digits) if digits else None


def find_report_by_number(number):
    for p in glob.glob(os.path.join(REPORTS_DIR, "*.pdf")):
        m = re.search(r"(\d{3})", os.path.basename(p))
        if m and m.group(1) == number:
            return p
    return None


def extract_meta_date(full_text):
    months = {
        "janvier": "01", "février": "02", "mars": "03", "avril": "04",
        "mai": "05", "juin": "06", "juillet": "07", "août": "08",
        "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12",
    }
    m = re.search(r"Date de rapportage\s*:?\s*(\d{1,2})\s+(\w+)\s+(\d{4})", full_text)
    if not m:
        return None
    d, mo, y = m.groups()
    mon = months.get(mo.lower())
    if not mon:
        return None
    return f"{y}-{mon}-{int(d):02d}"


def find_cumulative_table(pdf):
    """Cherche la table 'Nbre de cas suspects / Nbre de décès suspects /
    Nbre de cas Confirmés / Nbre de contacts' — distincte de la table
    'Nouveaux cas confirmés du jour' (qui contient 'Guéris du jour' dans
    son en-tête, jamais 'Nbre de cas')."""
    for page in pdf.pages:
        for table in page.extract_tables():
            if not table:
                continue
            header_blob = " ".join(
                str(c) for row in table[:3] for c in row if c
            )
            if "Nbre de cas" in header_blob:
                return table
    return None


def parse_cumulative_table(table):
    """Parcourt la table compactée (cellules vides retirées) pour extraire
    (province, nom de zone, cas confirmés cumulés), plus le total général
    pour validation. Les lignes malformées (trop peu de cellules exploitables,
    ex: 'Karisimbi' avec presque toutes les valeurs manquantes) sont ignorées
    plutôt que mal interprétées."""
    zones = []
    total_confirmed = None
    current_province = None

    for row in table:
        compact = [v for v in row if v not in (None, "")]
        if not compact:
            continue
        label = str(compact[0]).strip()

        if label.lower() == "sous total":
            continue

        if label.lower() == "total":
            if len(compact) >= 4:
                total_confirmed = norm_num(compact[3])
            continue

        if len(compact) == 6:
            province_raw = str(compact[0]).strip()
            name = str(compact[1]).strip()
            current_province = PROVINCE_CANON.get(province_raw, province_raw)
            confirmed = norm_num(compact[4])
        elif len(compact) == 5:
            name = str(compact[0]).strip()
            confirmed = norm_num(compact[3])
        else:
            continue  # ligne malformée, ignorée par prudence

        if name.lower().startswith(EXCLUDE_NAME_PREFIXES):
            continue
        if current_province is None or confirmed is None:
            continue

        zones.append((current_province, name, confirmed))

    return zones, total_confirmed


def main():
    known_confirmed_by_date = {}
    if os.path.exists(SITREPS_PATH):
        with open(SITREPS_PATH, encoding="utf-8") as f:
            for entry in json.load(f):
                if entry.get("date"):
                    known_confirmed_by_date[entry["date"]] = entry.get("confirmed")
    else:
        print(f"! {SITREPS_PATH} introuvable, arrêt.")
        return 1

    validated_entries = []

    for number in TARGET_SITREPS:
        pdf_path = find_report_by_number(number)
        if not pdf_path:
            print(f"[{number}] PDF introuvable, ignoré.")
            continue

        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            date = extract_meta_date(full_text)
            table = find_cumulative_table(pdf)

        if not date or date not in known_confirmed_by_date:
            print(f"[{number}] date introuvable ou absente de sitreps.json, ignoré.")
            continue
        known_confirmed = known_confirmed_by_date[date]
        if known_confirmed is None:
            print(f"[{number}] ({date}) : pas de valeur 'confirmed' connue, ignoré.")
            continue

        if table is None:
            print(f"[{number}] ({date}) : table cumulative introuvable, ignoré.")
            continue

        zones, total_confirmed = parse_cumulative_table(table)
        if not zones or total_confirmed is None:
            print(f"[{number}] ({date}) : aucune zone exploitable extraite, ignoré.")
            continue

        if total_confirmed != known_confirmed:
            print(f"[{number}] ({date}) : total de la table ({total_confirmed}) "
                  f"!= sitreps.json ({known_confirmed}), ignoré par prudence.")
            continue

        sum_cases = sum(z[2] for z in zones)
        if sum_cases != total_confirmed:
            print(f"    (note : somme des zones {sum_cases} != total {total_confirmed} "
                  f"— lignes malformées exclues ou cas non ventilés)")

        zone_entries = [
            {"name": name, "province": prov, "cases": cases, "deaths": None}
            for prov, name, cases in zones
        ]
        validated_entries.append({"sitrep": number, "date": date, "zones": zone_entries})
        print(f"[{number}] ({date}) : VALIDÉ — {len(zone_entries)} zones, "
              f"total {total_confirmed} cas confirmé (décès non disponibles).")

    if not validated_entries:
        print("\nAucun SitRep validé, rien à écrire.")
        return 0

    existing = []
    if os.path.exists(ZONES_HISTORY_PATH):
        with open(ZONES_HISTORY_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    by_sitrep = {e["sitrep"]: e for e in existing}
    for entry in validated_entries:
        by_sitrep[entry["sitrep"]] = entry
    merged = sorted(by_sitrep.values(), key=lambda e: e["date"])

    os.makedirs(os.path.dirname(ZONES_HISTORY_PATH), exist_ok=True)
    with open(ZONES_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\n{ZONES_HISTORY_PATH} mis à jour : {len(merged)} point(s) au total "
          f"({len(validated_entries)} nouveau(x)/rafraîchi(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
