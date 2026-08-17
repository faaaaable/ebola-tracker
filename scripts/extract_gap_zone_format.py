#!/usr/bin/env python3
"""
Extrait le détail cumulatif par zone de santé pour les SitRep utilisant le
format "Tableau 2. Répartition des cas et décès confirmés... par province
et zone de santé" — provinces en MAJUSCULES suivies de leurs zones,
3 colonnes numériques (Cas confirmés cumulés / Décès confirmés cumulés /
Létalité %). Voir scan_gap_zone_format.py pour la liste des candidats.

Contrairement à l'ancien format de mai (plusieurs groupes de colonnes
mélangés), celui-ci n'a qu'un seul triplet de colonnes par ligne — pas
d'ambiguïté de position. On valide quand même chaque extraction contre le
total national déjà connu dans data/sitreps.json avant d'écrire quoi que
ce soit, par principe (jamais de donnée non vérifiée insérée).

N'écrit dans data/zones-history.json qu'en fusionnant avec l'existant.

Usage: python3 scripts/extract_gap_zone_format.py
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

TARGET_SITREPS = ["033", "034", "035", "036", "037", "038", "039", "040",
                   "041", "042", "044", "046", "047", "048", "049", "050",
                   "051", "052", "053", "054", "055", "056", "057", "058"]

PROVINCE_UPPER = ["ITURI", "NORD-KIVU", "SUD-KIVU", "HAUT-UÉLÉ", "TSHOPO", "BAS-UÉLÉ"]
PROVINCE_CANON = {p: p.title().replace("Uélé", "Uélé") for p in PROVINCE_UPPER}
PROVINCE_CANON["NORD-KIVU"] = "Nord-Kivu"
PROVINCE_CANON["SUD-KIVU"] = "Sud-Kivu"
PROVINCE_CANON["HAUT-UÉLÉ"] = "Haut-Uélé"
PROVINCE_CANON["BAS-UÉLÉ"] = "Bas-Uélé"

# Ligne de province : "ITURI 1214 335 27,6%" — le symbole % est parfois
# absent selon le bulletin (variation d'extraction), donc rendu optionnel.
# Un astérisque de renvoi de note peut aussi apparaître collé au nom ou à
# n'importe quel nombre (ex: "Ituri 1214 335* 27,6%") : toléré partout.
PROVINCE_LINE_RE = re.compile(
    r"^(?P<prov>ITURI|NORD-KIVU|SUD-KIVU|HAUT-UÉLÉ|TSHOPO|BAS-UÉLÉ)\*?\s+"
    r"(?P<cases>\d+)\*?\s+(?P<deaths>\d+)\*?\s+[\d,]+%?\*?\s*$"
)
# Ligne de zone : "Bunia 358 82 22,9%" (ou "22,9" sans %). Certains
# bulletins accolent un astérisque de renvoi directement au nom de la zone
# (ex: "Nia-Nia* 12 5 41,7%") : sans cette tolérance, la ligne entière ne
# matche plus et la zone disparaît silencieusement de l'extraction — c'est
# ce qui s'est produit avec Nia-Nia sur plusieurs SitRep de fin juin.
ZONE_LINE_RE = re.compile(
    r"^(?P<name>[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'\.\- ]*?)\*?\s+"
    r"(?P<cases>\d+)\*?\s+(?P<deaths>\d+)\*?\s+[\d,]+%?\*?\s*$"
)
TOTAL_LINE_RE = re.compile(r"^TOTAL\*?\s+(?P<cases>\d+)\*?\s+(?P<deaths>\d+)\*?\s+[\d,]+%?\*?\s*$")

# Deux formats d'en-tête observés selon les bulletins :
#  - "Province / Zone de santé ... cumulés (n) cumulés (n)"  (ex: 046, 052)
#  - "Zone de santé  Cas confirmés cumulés  Décès confirmés cumulés  Létalité (CFR%)"  (ex: 048)
HEADER_MARKERS = [
    re.compile(r"Province\s*/\s*Zone de santé", re.IGNORECASE),
    re.compile(r"Zone de santé\s+Cas confirmés cumulés", re.IGNORECASE),
]


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


def find_report_by_number(number):
    for p in glob.glob(os.path.join(REPORTS_DIR, "*.pdf")):
        m = re.search(r"(\d{3})", os.path.basename(p))
        if m and m.group(1) == number:
            return p
    return None


def reconstruct_total(digit_tokens, known_confirmed, known_deaths):
    """La ligne TOTAL utilise parfois un espace comme séparateur de
    milliers (ex: 'TOTAL 1 460 452 30,9%' au lieu de '1460 452'), ce que
    les autres lignes du tableau n'ont pas. Plutôt que de deviner où
    couper, on essaie toutes les concaténations possibles de tokens
    consécutifs jusqu'à retrouver exactement les valeurs déjà connues et
    vérifiées dans sitreps.json — élimine toute ambiguïté."""
    n = len(digit_tokens)
    for split1 in range(1, n):
        try:
            candidate_cases = int("".join(digit_tokens[:split1]))
        except ValueError:
            continue
        if candidate_cases != known_confirmed:
            continue
        for split2 in range(split1 + 1, n + 1):
            try:
                candidate_deaths = int("".join(digit_tokens[split1:split2]))
            except ValueError:
                continue
            if candidate_deaths == known_deaths:
                return (candidate_cases, candidate_deaths)
    return None


def parse_zone_table(full_text, known_confirmed=None, known_deaths=None):
    """Repère le bloc entre l'en-tête du tableau et 'TOTAL', et associe
    chaque zone à la province MAJUSCULE la précédant."""
    lines = full_text.split("\n")
    start_idx = None
    for i, line in enumerate(lines):
        if any(pattern.search(line) for pattern in HEADER_MARKERS):
            start_idx = i
            break
    if start_idx is None:
        return [], None

    current_province = None
    zones = []  # (province, name, [numbers])
    total = None

    for line in lines[start_idx + 1:]:
        line = line.strip()
        if not line:
            continue

        if line.startswith("TOTAL"):
            digit_tokens = re.findall(r"\d+", re.sub(r"[\d,]+%", "", line))
            if known_confirmed is not None and known_deaths is not None:
                total = reconstruct_total(digit_tokens, known_confirmed, known_deaths)
            if total is None and len(digit_tokens) >= 2:
                # Repli si aucune valeur connue n'est fournie (ne devrait pas
                # arriver dans le flux normal, où on valide toujours avant) :
                # tente la lecture directe sans espace de milliers.
                m = TOTAL_LINE_RE.match(line)
                if m:
                    total = (int(m.group("cases")), int(m.group("deaths")))
            break

        pm = PROVINCE_LINE_RE.match(line)
        if pm:
            current_province = PROVINCE_CANON.get(pm.group("prov"), pm.group("prov"))
            continue

        if current_province is None:
            continue

        zm = ZONE_LINE_RE.match(line)
        if not zm:
            continue
        zones.append((current_province, zm.group("name").strip(),
                       int(zm.group("cases")), int(zm.group("deaths"))))

    return zones, total


def main():
    known_by_date = {}
    if os.path.exists(SITREPS_PATH):
        with open(SITREPS_PATH, encoding="utf-8") as f:
            for entry in json.load(f):
                if entry.get("date"):
                    known_by_date[entry["date"]] = (entry.get("confirmed"), entry.get("deaths"))
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
        if not date or date not in known_by_date:
            print(f"[{number}] date introuvable ou absente de sitreps.json, ignoré.")
            continue

        known_confirmed, known_deaths = known_by_date[date]
        if known_confirmed is None:
            print(f"[{number}] ({date}) : pas de valeur 'confirmed' connue, ignoré.")
            continue

        zones, total = parse_zone_table(full_text, known_confirmed, known_deaths)
        if not zones or not total:
            print(f"[{number}] ({date}) : table de zones introuvable dans ce format, ignoré.")
            continue

        total_cases, total_deaths = total
        if total_cases != known_confirmed or total_deaths != known_deaths:
            print(f"[{number}] ({date}) : TOTAL du tableau ({total_cases}/{total_deaths}) "
                  f"!= sitreps.json ({known_confirmed}/{known_deaths}), ignoré par prudence.")
            continue

        # Note : certains bulletins signalent explicitement des "cas non
        # ventilés par zone de santé" (attribués à la province mais à
        # aucune zone précise). La somme des zones peut donc légitimement
        # être inférieure au total — ce n'est pas une erreur d'extraction,
        # c'est une caractéristique du bulletin source lui-même. On ne
        # l'exige donc pas ; seule la correspondance du TOTAL général avec
        # sitreps.json (déjà vérifiée ci-dessus) garantit qu'on lit la
        # bonne table, à la bonne date.
        sum_cases = sum(z[2] for z in zones)
        sum_deaths = sum(z[3] for z in zones)
        if sum_cases != total_cases or sum_deaths != total_deaths:
            print(f"    (note : somme des zones {sum_cases}/{sum_deaths} < total {total_cases}/{total_deaths} "
                  f"— probablement des cas non ventilés par zone, mentionnés dans le bulletin)")

        zone_entries = [
            {"name": name, "province": prov, "cases": cases, "deaths": deaths}
            for prov, name, cases, deaths in zones
        ]
        validated_entries.append({"sitrep": number, "date": date, "zones": zone_entries})
        print(f"[{number}] ({date}) : VALIDÉ — {len(zone_entries)} zones, total {total_cases}/{total_deaths} confirmé.")

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
