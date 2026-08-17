#!/usr/bin/env python3
"""
Diagnostic d'extraction sur TOUS les SitRep archivés dans reports/.

Ne modifie aucun fichier de données existant (latest.json, sitreps.json...).
Teste, pour chaque PDF, les 4 étapes d'extraction utilisées par
update_data.py (méta, KPI nationaux, table provinces, détail zones) et
rapporte un résumé compact : combien de SitRep s'extraient proprement à
chaque étape, et la liste de ceux qui échouent, groupés par décennie de
numéro (001-010, 011-020, etc.) pour repérer si les échecs sont concentrés
sur une période (= changement de format de PDF à cette époque).

Écrit aussi data/diagnostic_report.json (détail complet, un objet par
SitRep) pour inspection ultérieure, mais l'affichage console reste
volontairement condensé.

Usage: python3 scripts/diagnose_reports.py
"""
import glob
import json
import os
import re
import sys

import pdfplumber

# Réutilise les fonctions d'extraction déjà éprouvées par update_data.py,
# plutôt que de les dupliquer / risquer une divergence de comportement.
sys.path.insert(0, os.path.dirname(__file__))
import update_data as ud

REPORTS_DIR = "reports"
OUT_PATH = "data/diagnostic_report.json"


def diagnose_one(pdf_path):
    """Tente les 4 étapes d'extraction sur un PDF, indépendamment les unes
    des autres (une étape qui échoue n'empêche pas de tester les suivantes),
    pour savoir précisément QUOI échoue, pas juste QUE ça échoue."""
    fname = os.path.basename(pdf_path)
    fm = re.search(r"(\d{3})", fname)
    fallback_num = fm.group(1) if fm else None

    result = {
        "file": fname,
        "numberFromFilename": fallback_num,
        "meta": {"ok": False, "error": None, "sitrepNumber": None, "reportingDate": None},
        # "kpis" teste ici national confirmed/deaths, EXACTEMENT comme le fait
        # main() : via le total de la table province (prov_total_row), pas
        # via extract_kpi_band (qui sert seulement à recovered/cfr/inCTE/
        # contactsFollowUpRate — jamais à confirmed/deaths).
        "kpis": {"ok": False, "error": None, "confirmed": None, "deaths": None},
        "provinceTable": {"ok": False, "error": None, "rowCount": None},
        # "zoneDetail" applique désormais la même reconstruction que le vrai
        # pipeline (revalidate_zones -> gap_fill_missing_zones), pas
        # seulement l'extraction brute des tableaux pdfplumber.
        "zoneDetail": {"ok": False, "error": None, "zoneCount": None},
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])

            try:
                meta = ud.extract_meta(full_text, fallback_number=fallback_num)
                result["meta"]["ok"] = bool(meta.get("reportingDate"))
                result["meta"]["sitrepNumber"] = meta.get("sitrepNumber")
                result["meta"]["reportingDate"] = meta.get("reportingDate")
                if not meta.get("reportingDate"):
                    result["meta"]["error"] = "dates non trouvées dans le texte"
            except Exception as e:
                result["meta"]["error"] = str(e)

            prov_table = None
            try:
                prov_table = ud.extract_province_summary(pdf)
                if prov_table is None:
                    result["provinceTable"]["error"] = "table introuvable (en-tête différent ou absente)"
                else:
                    provinces, total_row = ud.parse_province_summary(prov_table)
                    result["provinceTable"]["ok"] = bool(provinces) and total_row is not None
                    result["provinceTable"]["rowCount"] = len(provinces)
                    if not result["provinceTable"]["ok"]:
                        result["provinceTable"]["error"] = "table trouvée mais lignes/total non exploitables"

                    # national.confirmed/deaths viennent de CETTE ligne de
                    # total dans le vrai pipeline (main()), pas de la bande
                    # KPI en haut de page.
                    if total_row:
                        result["kpis"]["confirmed"] = ud.norm_int(total_row[1])
                        result["kpis"]["deaths"] = ud.norm_int(total_row[2])
                        result["kpis"]["ok"] = result["kpis"]["confirmed"] is not None
                        if not result["kpis"]["ok"]:
                            result["kpis"]["error"] = "ligne de total trouvée mais confirmed illisible"
                    else:
                        result["kpis"]["error"] = "pas de ligne de total dans la table province"
            except Exception as e:
                result["provinceTable"]["error"] = str(e)
                result["kpis"]["error"] = f"dépend de la table province : {e}"

            try:
                zone_rows = ud.extract_zone_detail_rows(pdf)
                _, zones_raw, _ = ud.parse_zone_detail(zone_rows)
                # Réplique exactement l'étape de reconstruction du vrai
                # pipeline : revalidate_zones() retire les lignes suspectes
                # PUIS les reconstruit depuis le texte brut (et complète
                # aussi les zones totalement absentes du tableau).
                zones_raw = ud.revalidate_zones(full_text, zones_raw)
                result["zoneDetail"]["ok"] = len(zones_raw) > 0
                result["zoneDetail"]["zoneCount"] = len(zones_raw)
                if not result["zoneDetail"]["ok"]:
                    result["zoneDetail"]["error"] = "aucune ligne de zone détectée, même après reconstruction texte (bulletin sans ce détail, ou format différent)"
            except Exception as e:
                result["zoneDetail"]["error"] = str(e)

    except Exception as e:
        # Le PDF lui-même n'a pas pu être ouvert (fichier corrompu, protégé...)
        for stage in ("meta", "kpis", "provinceTable", "zoneDetail"):
            result[stage]["error"] = f"PDF illisible : {e}"

    return result


def decade_bucket(num_str):
    if not num_str or not num_str.isdigit():
        return "???"
    n = int(num_str)
    start = (n // 10) * 10 + 1
    end = start + 9
    return f"{start:03d}-{end:03d}"


def main():
    pdfs = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")))
    if not pdfs:
        print("Aucun PDF trouvé dans reports/.")
        return 1

    print(f"Diagnostic sur {len(pdfs)} SitRep archivés...\n")

    results = []
    for pdf_path in pdfs:
        results.append(diagnose_one(pdf_path))

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # ---------- résumé condensé ----------
    stages = ["meta", "kpis", "provinceTable", "zoneDetail"]
    stage_labels = {
        "meta": "Date/numéro",
        "kpis": "KPI nationaux",
        "provinceTable": "Table provinces",
        "zoneDetail": "Détail zones",
    }

    print("=" * 72)
    print("TAUX DE RÉUSSITE GLOBAL")
    print("=" * 72)
    for stage in stages:
        ok_count = sum(1 for r in results if r[stage]["ok"])
        print(f"  {stage_labels[stage]:<20} : {ok_count:3d} / {len(results)} SitRep OK")

    print()
    print("=" * 72)
    print("ÉCHECS PAR TRANCHE DE NUMÉROS (pour repérer un changement de format)")
    print("=" * 72)
    buckets = {}
    for r in results:
        b = decade_bucket(r["numberFromFilename"])
        buckets.setdefault(b, {s: [] for s in stages})
        for stage in stages:
            if not r[stage]["ok"]:
                buckets[b][stage].append(r["numberFromFilename"] or r["file"])

    for b in sorted(buckets.keys()):
        line_parts = []
        for stage in stages:
            failing = buckets[b][stage]
            if failing:
                line_parts.append(f"{stage_labels[stage]}: {len(failing)} échec(s) ({', '.join(failing)})")
        if line_parts:
            print(f"  [{b}]")
            for part in line_parts:
                print(f"      - {part}")

    print()
    print(f"Détail complet écrit dans {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
