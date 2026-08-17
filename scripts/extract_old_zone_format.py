#!/usr/bin/env python3
"""
Extrait le détail cumulatif par zone de santé pour les SitRep identifiés
comme utilisant l'ancien format "zones groupées par province avec
Sous total / Total" (voir scan_old_zone_format.py) : 005, 006, 007, 008,
009, 010, 013, 015.

PRINCIPE DE SÉCURITÉ : ces tables contiennent plusieurs groupes de
colonnes mélangés (valeurs cumulées ET nouveaux cas du jour), et pdfplumber
ne permet pas de les distinguer de façon fiable par la seule position. Ce
script ne DEVINE jamais quelle colonne correspond aux cas confirmés
cumulés : il compare chaque colonne candidate au total national déjà
vérifié dans data/sitreps.json (restauré et confirmé par ailleurs) pour
la même date. Si aucune colonne ne correspond avec certitude, ce SitRep
est ignoré et signalé — jamais de donnée insérée sans validation.

N'écrit dans data/zones_history.json qu'en fusionnant avec le contenu
existant (jamais d'écrasement), et seulement pour les SitRep validés.

Usage: python3 scripts/extract_old_zone_format.py
"""
import glob
import json
import os
import re
import sys

import pdfplumber

REPORTS_DIR = "reports"
ZONES_HISTORY_PATH = "data/zones_history.json"
SITREPS_PATH = "data/sitreps.json"

TARGET_SITREPS = ["005", "006", "007", "008", "009", "010", "013", "015"]

PROVINCE_NAMES = ["Ituri", "Nord-Kivu", "Haut-Uélé", "Tshopo", "Sud-Kivu", "Bas-Uélé", "Nord Kivu", "Sud Kivu"]
PROVINCE_CANON = {"Nord Kivu": "Nord-Kivu", "Sud Kivu": "Sud-Kivu"}

ZONE_LINE_RE = re.compile(
    r"^(?P<name>[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'\.\- ]*?)\s+"
    r"(?P<nums>(?:\d+|ND)(?:\s+(?:\d+|ND))+)\s*$"
)


def norm_num(s):
    return None if s == "ND" else int(s)


def find_report_by_number(number):
    for p in glob.glob(os.path.join(REPORTS_DIR, "*.pdf")):
        m = re.search(r"(\d{3})", os.path.basename(p))
        if m and m.group(1) == number:
            return p
    return None


def extract_meta_date(full_text):
    """Cherche 'Date de rapportage : JJ mois AAAA' dans le texte, pour
    récupérer la date exacte du SitRep sans dupliquer toute la logique de
    update_data.py."""
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


def parse_zone_blocks(full_text):
    """Extrait les blocs de zones groupés par province, en s'arrêtant à
    chaque 'Sous total' (fin de province) puis au 'Total' général."""
    lines = full_text.split("\n")
    current_province = None
    zones = []  # (province, name, [numbers])
    sous_totaux = {}  # province -> [numbers]
    total_line = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        matched_prov = None
        for pname in PROVINCE_NAMES:
            if line.startswith(pname):
                matched_prov = PROVINCE_CANON.get(pname, pname)
                # La ligne peut être "Nord-Kivu Katwa 0 0 ND ND ND 0" (province
                # + première zone sur la même ligne) : on retire le préfixe
                # et on retraite le reste comme une ligne de zone normale.
                line = line[len(pname):].strip()
                break
        if matched_prov:
            current_province = matched_prov
            if not line:
                continue

        if line.lower().startswith("sous total") or line.lower().startswith("sous-total"):
            if current_province:
                nums = re.findall(r"\d+|ND", line)
                sous_totaux[current_province] = [norm_num(n) for n in nums]
            continue

        if line.startswith("Total") and not line.startswith("Total en") and not line.startswith("Total des"):
            nums = re.findall(r"\d+|ND", line)
            if nums:
                total_line = [norm_num(n) for n in nums]
            # Le "Total" général marque la fin de cette table pour nos besoins.
            break

        if current_province is None:
            continue

        m = ZONE_LINE_RE.match(line)
        if not m:
            continue
        name = m.group("name").strip()
        nums = [norm_num(n) for n in m.group("nums").split()]
        zones.append((current_province, name, nums))

    return zones, sous_totaux, total_line


def find_validated_column(zones, sous_totaux, total_line, known_value, label):
    """Teste chaque colonne candidate : la somme des zones par province
    doit égaler le sous-total de cette province (cohérence interne), ET
    le total général sur cette colonne doit correspondre à `known_value`
    (déjà vérifié dans sitreps.json). Retourne l'index de colonne si une
    seule correspond sans ambiguïté, sinon None."""
    if not zones or not total_line:
        return None
    n_cols = min(len(z[2]) for z in zones)
    candidates = []
    for col in range(n_cols):
        # Cohérence interne : somme par province == sous-total de cette colonne
        internally_consistent = True
        by_province = {}
        for prov, name, nums in zones:
            if col >= len(nums) or nums[col] is None:
                internally_consistent = False
                break
            by_province.setdefault(prov, 0)
            by_province[prov] += nums[col]
        if not internally_consistent:
            continue
        for prov, summed in by_province.items():
            expected = sous_totaux.get(prov)
            if expected is None or col >= len(expected) or expected[col] != summed:
                internally_consistent = False
                break
        if not internally_consistent:
            continue
        if col >= len(total_line) or total_line[col] != known_value:
            continue
        candidates.append(col)

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        print(f"    ! ambiguïté pour {label} : plusieurs colonnes correspondent ({candidates}), ignoré par prudence")
    return None


def main():
    # Table de vérité (cas confirmés / décès cumulés par date), issue du
    # data/sitreps.json déjà restauré et vérifié — sert uniquement à valider
    # les colonnes, jamais à écrire de nouvelles valeurs directement.
    known_by_date = {}
    if os.path.exists(SITREPS_PATH):
        with open(SITREPS_PATH, encoding="utf-8") as f:
            for entry in json.load(f):
                if entry.get("date"):
                    known_by_date[entry["date"]] = (entry.get("confirmed"), entry.get("deaths"))
    else:
        print(f"! {SITREPS_PATH} introuvable — impossible de valider quoi que ce soit, arrêt.")
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
        if not date or date not in known_by_date:
            print(f"[{number}] date introuvable ou absente de sitreps.json, ignoré.")
            continue

        known_confirmed, known_deaths = known_by_date[date]
        if known_confirmed is None:
            print(f"[{number}] pas de valeur 'confirmed' connue pour {date}, ignoré.")
            continue

        zones, sous_totaux, total_line = parse_zone_blocks(full_text)
        if not zones or not total_line:
            print(f"[{number}] table de zones non trouvée, ignoré.")
            continue

        cases_col = find_validated_column(zones, sous_totaux, total_line, known_confirmed, f"{number}/cas confirmés")
        deaths_col = None
        if known_deaths is not None:
            deaths_col = find_validated_column(zones, sous_totaux, total_line, known_deaths, f"{number}/décès")

        if cases_col is None:
            print(f"[{number}] ({date}) : colonne 'cas confirmés' non validée (attendu {known_confirmed}), ignoré.")
            continue
        if deaths_col is None:
            print(f"[{number}] ({date}) : colonne 'décès' non validée (attendu {known_deaths}), ignoré.")
            continue

        zone_entries = [
            {"name": name, "province": prov, "cases": nums[cases_col], "deaths": nums[deaths_col]}
            for prov, name, nums in zones
        ]
        validated_entries.append({"sitrep": number, "date": date, "zones": zone_entries})
        print(f"[{number}] ({date}) : VALIDÉ — {len(zone_entries)} zones "
              f"(colonne cas={cases_col}, colonne décès={deaths_col})")

    if not validated_entries:
        print("\nAucun SitRep validé, rien à écrire.")
        return 0

    # Fusion avec l'existant, jamais d'écrasement (même principe que pour
    # sitreps.json) : on indexe par numéro de sitrep, on complète les
    # nouvelles entrées, on garde toutes les entrées déjà présentes.
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
