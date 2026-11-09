#!/usr/bin/env python3
"""
Diagnostic combiné (pas d'extraction) : scanne les 13 "Weekly External
Situation Report" OMS déjà téléchargés dans reports/who/, en une seule
passe par PDF, à la recherche de PLUSIEURS pistes de données
complémentaires à la fois — plutôt que de relancer un script par piste :

1. Répartition communautaire/intra-CTE des décès (Figure 3)
2. Cas exportés hors RDC/Ouganda (Allemagne, France...)
3. Niveau de risque OMS (national/régional/mondial)
4. Cas confirmés en Ouganda spécifiquement (distinct du total RDC)

N'écrit aucun fichier de données — sert à décider quelles pistes valent
la peine d'une vraie extraction.

Usage: python3 scripts/scan_who_supplementary_data.py
"""
import glob
import os
import re

import pdfplumber

WHO_REPORTS_DIR = "reports/who"

FIGURE_CAPTION_RE = re.compile(
    r"Figure\s*\d+\.?\s*Weekly proportion of confirmed[^\n]*deaths[^\n]*place of death",
    re.IGNORECASE,
)
PERCENT_RE = re.compile(r"\b\d{1,3}[.,]\d%")

# Cherche une section/figure mentionnant explicitement une ventilation par
# âge et/ou sexe — le libellé exact varie probablement d'un rapport à
# l'autre ("age and sex", "sex and age group", "age group distribution"...),
# donc plusieurs formulations sont tolérées plutôt qu'une seule regex rigide.
AGE_SEX_RE = re.compile(
    r"[^\n]*(?:age\s*(?:and|&)\s*sex|sex\s*(?:and|&)\s*age|age\s*group)[^\n]*",
    re.IGNORECASE,
)


def scan_one(path):
    name = os.path.basename(path)
    with pdfplumber.open(path) as pdf:
        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

    result = {"name": name}

    # 1. Répartition des décès
    caption_match = FIGURE_CAPTION_RE.search(full_text)
    if caption_match:
        window = full_text[caption_match.end(): caption_match.end() + 1000]
        percents = PERCENT_RE.findall(window)
        result["death_breakdown"] = f"section trouvée, {len(percents)} % détecté(s)" if percents \
            else "section trouvée, mais aucun % exploitable (probable image)"
    else:
        result["death_breakdown"] = "absente"

    # 2. Répartition par âge/sexe — toutes les lignes correspondantes sont
    # gardées (pas juste la première), le libellé exact étant incertain.
    age_sex_lines = [m.strip() for m in AGE_SEX_RE.findall(full_text) if m.strip()]
    result["age_sex"] = age_sex_lines[:3] if age_sex_lines else None

    return result


def main():
    paths = sorted(glob.glob(os.path.join(WHO_REPORTS_DIR, "*.pdf")))
    if not paths:
        print(f"Aucun PDF trouvé dans {WHO_REPORTS_DIR}/.")
        return 1

    print(f"Scan combiné de {len(paths)} rapport(s) OMS...\n")

    results = []
    for path in paths:
        try:
            r = scan_one(path)
            results.append(r)
        except Exception as e:
            print(f"[{os.path.basename(path)}] ERREUR : {e}")
            continue

        print(f"=== {r['name']} ===")
        print(f"  Répartition décès  : {r['death_breakdown']}")
        if r["age_sex"]:
            print(f"  Âge/sexe           : {len(r['age_sex'])} mention(s) trouvée(s) :")
            for line in r["age_sex"]:
                print(f"      - {line[:150]}")
        else:
            print(f"  Âge/sexe           : —")
        print()

    print(f"{'=' * 90}")
    print("RÉSUMÉ")
    print(f"{'=' * 90}")
    n = len(results)
    print(f"Répartition décès exploitable en texte : "
          f"{sum(1 for r in results if 'détecté' in r['death_breakdown'])}/{n}")
    print(f"Mentions âge/sexe trouvées               : {sum(1 for r in results if r['age_sex'])}/{n}")


if __name__ == "__main__":
    main()
