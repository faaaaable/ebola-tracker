#!/usr/bin/env python3
"""
Met à jour data/latest.json à partir du dernier SitRep MVE (RDC) téléchargé
dans reports/. Conçu pour tourner dans le workflow GitHub Actions après
le téléchargement des SitRep (sync-sitreps.yml).

Usage: python3 scripts/update_data.py
"""
import pdfplumber
import re
import json
import glob
import os
import sys

REPORTS_DIR = "reports"
DATA_PATH = "data/latest.json"

PROVINCE_NAMES_MAIN = ["Ituri", "Nord-Kivu", "Haut-Uélé", "Tshopo", "Sud-Kivu", "Bas Uélé"]
# Nom canonique utilisé côté site (avec tiret pour Bas-Uélé)
PROVINCE_CANON = {
    "Ituri": "Ituri", "Nord-Kivu": "Nord-Kivu", "Haut-Uélé": "Haut-Uélé",
    "Tshopo": "Tshopo", "Sud-Kivu": "Sud-Kivu", "Bas Uélé": "Bas-Uélé",
}

MONTHS_FR = {
    "janvier": "01", "février": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12",
}


def norm_int(s):
    if s is None:
        return None
    raw = str(s).strip()
    if raw in ("", "NA", "ND"):
        return None
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        return None
    return int(digits)


def norm_pct(s):
    if s is None:
        return None
    raw = str(s).strip()
    if raw in ("", "NA", "ND"):
        return None
    m = re.search(r"(\d+)[,.](\d+)", raw)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    m2 = re.search(r"(\d+)\s*%", raw)
    if m2:
        return float(m2.group(1))
    return None


def find_latest_report():
    """Trouve le SitRep le plus récent (numéro le plus élevé) dans reports/."""
    pdfs = glob.glob(os.path.join(REPORTS_DIR, "*.pdf"))
    best = None
    best_num = -1
    for p in pdfs:
        m = re.search(r"(\d{3})", os.path.basename(p))
        if not m:
            continue
        num = int(m.group(1))
        if num > best_num:
            best_num = num
            best = p
    return best, best_num


def extract_sidebar_text(page):
    """Reconstruit la colonne de gauche (provinces/zones/aires touchées)
    en se basant sur les positions x/y des mots, car l'extraction de texte
    linéaire mélange les deux colonnes de la page 1."""
    words = page.extract_words()
    col = [w for w in words if w["x0"] < 210 and w["top"] > 340]
    col.sort(key=lambda w: (round(w["top"] / 3), w["x0"]))
    return " ".join(w["text"] for w in col)


def extract_kpi_band(page):
    """Reconstruit la ligne des 6 chiffres clés (cumul cas, cumul décès,
    létalité, patients CTE, cumul guéris, taux de suivi des contacts) en
    se basant sur les positions x des mots, car ces cases se chevauchent
    dans l'extraction de texte linéaire."""
    words = page.extract_words()
    band = [w for w in words if 245 < w["top"] < 275 and w["height"] > 9]

    def collect(xmin, xmax):
        ws = sorted([w for w in band if xmin <= w["x0"] < xmax], key=lambda w: w["x0"])
        return "".join(w["text"] for w in ws)

    return {
        "confirmed": norm_int(collect(60, 155)),
        "deaths": norm_int(collect(155, 250)),
        "cfr": norm_pct(collect(250, 320)),
        "inCTE": norm_int(collect(320, 410)),
        "recovered": norm_int(collect(410, 480)),
        "contactsFollowUpRate": norm_pct(collect(480, 560)),
    }


def extract_meta(full_text):
    m = re.search(r"SitRep N°(\d+)/MVEBDB/(\d{2})/(\d{2})/(\d{4})", full_text)
    if not m:
        raise ValueError("Impossible de trouver la référence du SitRep dans le PDF.")
    sitrep_number = m.group(1)
    sitrep_ref = m.group(0)

    md = re.search(
        r"Date de rapportage\s*:\s*(\d{1,2})\s+(\w+)\s+(\d{4}).*?"
        r"Date de publication\s*:\s*(\d{1,2})\s+(\w+)\s+(\d{4})",
        full_text, re.DOTALL,
    )
    reporting_date = publication_date = None
    if md:
        d1, mo1, y1, d2, mo2, y2 = md.groups()
        mo1n = MONTHS_FR.get(mo1.lower())
        mo2n = MONTHS_FR.get(mo2.lower())
        if mo1n:
            reporting_date = f"{y1}-{mo1n}-{int(d1):02d}"
        if mo2n:
            publication_date = f"{y2}-{mo2n}-{int(d2):02d}"

    return {
        "sitrepNumber": sitrep_number,
        "sitrepRef": sitrep_ref,
        "reportingDate": reporting_date,
        "publicationDate": publication_date,
        "source": "INSP RDC / Task Force Présidentielle Ebola 17",
    }


def extract_province_summary(pdf):
    """Table 'Répartition des cas et décès confirmés par province touchée'."""
    for page in pdf.pages:
        for t in page.extract_tables():
            if t and t[0] and t[0][0] and "Province" in str(t[0][0]):
                header = t[0]
                if len(header) >= 6 and "Cas" in str(header[1]):
                    return t
    return None


def parse_province_summary(table):
    provinces = []
    total_row = None
    for row in table[1:]:
        if not row or not row[0]:
            continue
        name = row[0].strip()
        if name == "Total":
            total_row = row
            continue
        zones_raw = row[4] or ""
        zm = re.search(r"(\d+)\s*/\s*(\d+)", zones_raw)
        n_zones, tot_zones = (int(zm.group(1)), int(zm.group(2))) if zm else (None, None)
        provinces.append({
            "name": PROVINCE_CANON.get(name, name),
            "confirmed": norm_int(row[1]),
            "deaths": norm_int(row[2]),
            "cfr": norm_pct(row[3]),
            "healthZonesAffected": {"n": n_zones, "total": tot_zones},
            "newCases24h": norm_int(row[5]),
        })
    return provinces, total_row


def extract_zone_detail_rows(pdf):
    """Collecte les lignes du tableau détaillé 'Cas et décès confirmés par
    province et zone de santé', qui s'étale sur plusieurs pages."""
    rows = []
    for page in pdf.pages:
        for t in page.extract_tables():
            for row in t:
                if not row or len(row) < 7:
                    continue
                name = row[0]
                if not name or not str(name).strip():
                    continue
                name = str(name).strip().replace("\n", "-")
                if name.startswith("Province /"):
                    continue
                if row[1] is None:
                    continue
                rows.append([name] + list(row[1:]))
    return rows


ZONE_LINE_RE = re.compile(
    r"^(?P<name>[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'\.\- ]*?)\s+"
    r"(?P<cas>\d[\d ]*|NA)\s+(?P<deces>\d[\d ]*|NA)\s+(?P<cfr>[\d,]+%|NA)\s*(?P<tail>.*)$"
)

# Ligne de sous-total de province dans le tableau détaillé (ex :
# "Ituri 4105 1791 43,6% 85 31 15 46"). Contrairement aux lignes de zone,
# ces lignes affichent TOUJOURS leurs 4 colonnes du jour explicitement
# (même à 0), donc pas d'ambiguïté de colonnes manquantes ici.
PROV_SUBTOTAL_RE = re.compile(
    r"^(?P<name>Ituri|Nord-Kivu|Haut-Uélé|Tshopo|Sud-Kivu|Bas Uélé)\s+"
    r"(?P<cas>\d[\d ]*)\s+(?P<deces>\d[\d ]*)\s+(?P<cfr>[\d,]+%)\s+"
    r"(?P<newcases>\d[\d ]*)\s+(?P<deathscomm>\d[\d ]*)\s+"
    r"(?P<deathsintracte>\d[\d ]*)\s+(?P<total>\d[\d ]*)\s*$"
)


def get_zone_section_text(full_text):
    start = full_text.find("Cas et décès confirmés par province et zone de santé")
    end = full_text.find("Situation des alertes notifiées")
    if start == -1 or end == -1 or end <= start:
        return None
    return full_text[start:end]


def extract_province_subtotals_from_text(full_text):
    """Relit les lignes de sous-total de province directement dans le texte
    brut plutôt que dans le tableau pdfplumber : plus fiable, car ces lignes
    ont un format fixe et toujours complet (voir PROV_SUBTOTAL_RE)."""
    section = get_zone_section_text(full_text)
    if not section:
        return {}
    out = {}
    for line in section.split("\n"):
        line = line.strip()
        m = PROV_SUBTOTAL_RE.match(line)
        if m:
            out[m.group("name")] = {
                "cas": m.group("cas"), "deces": m.group("deces"), "cfr": m.group("cfr"),
                "newcases": m.group("newcases"), "deathscomm": m.group("deathscomm"),
                "deathsintracte": m.group("deathsintracte"), "total": m.group("total"),
            }
    return out


def gap_fill_missing_zones(full_text, zones_raw):
    """pdfplumber peut perdre ou mal aligner une ligne de zone (saut de
    page, colonnes ambiguës). On reconstruit TOUTES les zones absentes (ou
    marquées non fiables en amont, voir revalidate_zones) en relisant le
    texte brut de la section, ligne par ligne, avec une regex fiable."""
    section = get_zone_section_text(full_text)
    if not section:
        return zones_raw

    already = {(prov, name) for prov, name, _ in zones_raw}
    current_province = None
    extra = []

    for line in section.split("\n"):
        line = line.strip()
        if not line:
            continue
        matched_province = None
        for pname in PROVINCE_NAMES_MAIN:
            if line.startswith(pname):
                matched_province = pname
                break
        if matched_province:
            current_province = matched_province
            continue
        if line.startswith("A ventiler") or line.startswith("Total"):
            continue
        if current_province is None:
            continue
        m = ZONE_LINE_RE.match(line)
        if not m:
            continue
        name = m.group("name").strip()
        if (current_province, name) in already:
            continue
        row = [name, m.group("cas"), m.group("deces"), m.group("cfr")]
        tail_nums = re.findall(r"\d+", m.group("tail"))
        row += tail_nums
        extra.append((current_province, name, row))
        already.add((current_province, name))

    return zones_raw + extra


def parse_zone_detail(rows):
    """Sépare les lignes en (sous-totaux par province, zones de santé, total général)."""
    province_subtotals = {}
    seen_subtotal = set()
    zones = []
    current_province = None
    total_row = None

    for row in rows:
        name = row[0]
        if name in PROVINCE_NAMES_MAIN and name not in seen_subtotal:
            seen_subtotal.add(name)
            current_province = name
            province_subtotals[name] = row
            continue
        if name == "A ventiler":
            continue
        if name == "Total":
            total_row = row
            continue
        if current_province is None:
            continue
        zones.append((current_province, name, row))

    return province_subtotals, zones, total_row


def zone_row_looks_unreliable(row):
    """Détecte les lignes où le décalage de colonnes pdfplumber a fait
    atterrir la létalité (ex: '9,1%' -> 91 une fois les caractères non-
    numériques supprimés) dans une case qui devrait être vide, tout en
    laissant les décès/létalité réels à 0. Signature : cas>0 mais décès ET
    létalité manquants/nuls alors que ce ne devrait pas être le cas."""
    try:
        cases = norm_int(row[1])
        deaths = norm_int(row[2]) if len(row) > 2 else None
        cfr = norm_pct(row[3]) if len(row) > 3 else None
    except Exception:
        return True
    if cases and cases > 0 and not deaths and cfr in (None, 0.0):
        return True
    return False


def revalidate_zones(full_text, zones_raw):
    """Retire du jeu de résultats les lignes suspectes (voir
    zone_row_looks_unreliable), puis relance gap_fill_missing_zones pour
    qu'elles soient reconstruites correctement depuis le texte brut, comme
    si elles avaient été manquantes."""
    reliable = [(p, n, r) for p, n, r in zones_raw if not zone_row_looks_unreliable(r)]
    dropped = len(zones_raw) - len(reliable)
    if dropped:
        print(f"  ! {dropped} ligne(s) de zone jugée(s) non fiable(s) côté tableau "
              f"(colonnes décalées) — reconstruites depuis le texte brut.")
    return gap_fill_missing_zones(full_text, reliable)


def zone_row_to_dict(province, name, row):
    # row = [name, cas, deces, letalite, nouv.cas, deces_comm, deces_intracte, (col vide?), total_deces]
    # la position du total varie selon le nb de colonnes réellement extraites
    cases = norm_int(row[1])
    deaths = norm_int(row[2])
    cfr = norm_pct(row[3]) if len(row) > 3 else None
    if cfr is None and cases:
        cfr = round((deaths or 0) / cases * 100, 1)
    new_cases = norm_int(row[4]) if len(row) > 4 else None
    deaths_comm = norm_int(row[5]) if len(row) > 5 else None
    deaths_intracte = norm_int(row[6]) if len(row) > 6 else None
    return {
        "name": name,
        "province": PROVINCE_CANON.get(province, province),
        "cases": cases or 0,
        "deaths": deaths or 0,
        "cfr": cfr if cfr is not None else 0.0,
        "newCases24h": new_cases or 0,
        "deathsCommunity24h": deaths_comm or 0,
        "deathsIntraCTE24h": deaths_intracte or 0,
    }


def parse_report_summary(pdf_path):
    """Analyse légère d'un SitRep pour la liste des rapports (onglet
    'Rapports de situation') : juste la méta et les totaux nationaux,
    sans le détail des zones de santé (inutile pour cet onglet)."""
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        meta = extract_meta(full_text)
        prov_table = extract_province_summary(pdf)
        confirmed = deaths = None
        if prov_table:
            _, total_row = parse_province_summary(prov_table)
            if total_row:
                confirmed = norm_int(total_row[1])
                deaths = norm_int(total_row[2])
    return {
        "sitrepNumber": meta["sitrepNumber"],
        "reportingDate": meta["reportingDate"],
        "publicationDate": meta["publicationDate"],
        "file": pdf_path.replace("\\", "/"),
        "confirmed": confirmed,
        "deaths": deaths,
    }


def rebuild_reports_list(current_reports):
    """Reconstruit la liste complète des rapports à partir de TOUS les PDF
    présents dans reports/, pas seulement celui du dernier passage. Les
    rapports déjà connus ne sont pas ré-analysés (juste leur chemin de
    fichier est rafraîchi) ; seuls les nouveaux PDF sont ouverts."""
    existing_by_num = {r["sitrepNumber"]: r for r in current_reports}
    all_pdfs = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")))
    reports = []
    for pdf_path in all_pdfs:
        m = re.search(r"(\d{3})", os.path.basename(pdf_path))
        if not m:
            continue
        num = m.group(1)
        if num in existing_by_num:
            entry = dict(existing_by_num[num])
            entry["file"] = pdf_path.replace("\\", "/")
            reports.append(entry)
        else:
            try:
                reports.append(parse_report_summary(pdf_path))
                print(f"  + nouveau rapport détecté et ajouté : {os.path.basename(pdf_path)}")
            except Exception as e:
                print(f"  ! avertissement : impossible d'analyser {pdf_path} ({e}), ignoré.")
    reports.sort(key=lambda r: r["sitrepNumber"])
    return reports


def main():
    report_path, report_num = find_latest_report()
    if not report_path:
        print("Aucun SitRep trouvé dans reports/, rien à faire.")
        return 0

    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            current = json.load(f)
    else:
        current = {}

    reports = rebuild_reports_list(current.get("reports", []))

    print(f"Régénération des données depuis {report_path} (SitRep {report_num:03d})...")

    with pdfplumber.open(report_path) as pdf:
        full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        meta = extract_meta(full_text)
        kpis = extract_kpi_band(pdf.pages[0])
        sidebar = extract_sidebar_text(pdf.pages[0])

        prov_table = extract_province_summary(pdf)
        if prov_table is None:
            raise ValueError("Table de répartition par province introuvable.")
        provinces, prov_total_row = parse_province_summary(prov_table)

        zone_rows = extract_zone_detail_rows(pdf)
        _, zones_raw, detail_total_row = parse_zone_detail(zone_rows)
        # Repère et reconstruit depuis le texte brut toute ligne de zone où
        # pdfplumber a mal aligné les colonnes (voir zone_row_looks_unreliable).
        zones_raw = revalidate_zones(full_text, zones_raw)
        # Sous-totaux de province : toujours relus depuis le texte brut,
        # plus fiable que les colonnes du tableau pour cette ligne précise.
        province_subtotals_text = extract_province_subtotals_from_text(full_text)

    # Enrichissement des provinces avec le détail décès communautaires/intra-CTE
    old_provinces = {p["name"]: p for p in current.get("provinces", [])}
    for p in provinces:
        canon = p["name"]
        src_name = next((k for k, v in PROVINCE_CANON.items() if v == canon), canon)
        sub = province_subtotals_text.get(src_name)
        if sub:
            p["newDeathsCommunity24h"] = norm_int(sub["deathscomm"]) or 0
            p["newDeathsIntraCTE24h"] = norm_int(sub["deathsintracte"]) or 0

        old = old_provinces.get(canon)
        has_new_cases = (p["newCases24h"] or 0) > 0
        if has_new_cases:
            p["status"] = "active-epicenter" if old and old.get("status") == "active-epicenter" else "active"
        elif old:
            p["status"] = old.get("status", "active")
            if "daysNoCase" in old:
                p["daysNoCase"] = old["daysNoCase"] + 1
        else:
            p["status"] = "active"

    health_zones = [zone_row_to_dict(prov, name, row) for prov, name, row in zones_raw]

    am = re.search(r"(\d[\d\s]*)\s*Aires de santé.*?Sur\s*(\d[\d\s]*)\s*\(", sidebar)
    health_areas = None
    if am:
        health_areas = {
            "n": norm_int(am.group(1)),
            "total": norm_int(am.group(2)),
        }

    zones_total_n = sum(p["healthZonesAffected"]["n"] or 0 for p in provinces)
    zones_total_tot = 151

    national = {
        "confirmed": norm_int(prov_total_row[1]) if prov_total_row else None,
        "deaths": norm_int(prov_total_row[2]) if prov_total_row else None,
        "recovered": kpis["recovered"],
        "cfr": norm_pct(prov_total_row[3]) if prov_total_row else kpis["cfr"],
        "inCTE": kpis["inCTE"],
        "contactsFollowUpRate": kpis["contactsFollowUpRate"],
        "provincesAffected": len(provinces),
        "healthZonesAffected": {"n": zones_total_n, "total": zones_total_tot},
        "healthAreasAffected": health_areas,
        "newCases24h": norm_int(prov_total_row[5]) if prov_total_row else None,
        "newDeaths24h": norm_int(detail_total_row[6]) if detail_total_row and len(detail_total_row) > 6 else None,
        "newDeathsCommunity24h": norm_int(detail_total_row[4]) if detail_total_row and len(detail_total_row) > 4 else None,
        "newDeathsIntraCTE24h": norm_int(detail_total_row[5]) if detail_total_row and len(detail_total_row) > 5 else None,
    }

    fs = re.search(
        r"(\d[\d\s]*)\s*nouveaux cas confirmés et\s*(\d[\d\s]*)\s*décès\s*\((\d[\d\s]*)\s*décès\s*communautaires?\s*et\s*(\d[\d\s]*)\s*intra",
        full_text,
    )
    if fs:
        national["newCases24h"] = national["newCases24h"] or norm_int(fs.group(1))
        national["newDeaths24h"] = norm_int(fs.group(2))
        national["newDeathsCommunity24h"] = norm_int(fs.group(3))
        national["newDeathsIntraCTE24h"] = norm_int(fs.group(4))

    result = dict(current)
    result["meta"] = meta
    result["national"] = national
    result["provinces"] = provinces
    result["healthZones"] = health_zones
    result["reports"] = reports

    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"data/latest.json mis à jour : SitRep {meta['sitrepNumber']} "
          f"({national['confirmed']} cas, {national['deaths']} décès) — "
          f"{len(reports)} rapport(s) listé(s) dans l'onglet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
