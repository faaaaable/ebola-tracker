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
import unicodedata

REPORTS_DIR = "reports"
DATA_PATH = "data/latest.json"
SITREPS_PATH = "data/sitreps.json"
ZONES_HISTORY_PATH = "data/zones-history.json"

PROVINCE_NAMES_MAIN = ["Ituri", "Nord-Kivu", "Haut-Uélé", "Tshopo", "Sud-Kivu", "Bas Uélé"]
PROVINCE_CANON = {
    "Ituri": "Ituri", "Nord-Kivu": "Nord-Kivu", "Haut-Uélé": "Haut-Uélé",
    "Tshopo": "Tshopo", "Sud-Kivu": "Sud-Kivu", "Bas Uélé": "Bas-Uélé",
}

MONTHS_FR = {
    "janvier": "01", "février": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12",
}


def normalize_month(s):
    """Retire les accents et met en minuscule avant de chercher dans
    MONTHS_FR : certains bulletins écrivent 'Aout' sans accent (au lieu de
    'août'), ce qui faisait échouer silencieusement tout le mapping du mois
    — et donc la date de rapportage entière — pour ces rapports (SitRep
    079 à 083 notamment). Une normalisation Unicode générique règle ce cas
    et tout autre accent manquant, sans avoir à lister chaque variante."""
    s = unicodedata.normalize("NFD", s.strip().lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# Table de recherche à clés normalisées (sans accent), construite une seule
# fois à partir de MONTHS_FR — indispensable : normaliser seulement le texte
# d'entrée ne sert à rien si les clés du dictionnaire restent accentuées.
MONTHS_FR_NORMALIZED = {normalize_month(k): v for k, v in MONTHS_FR.items()}


def month_to_number(mo):
    return MONTHS_FR_NORMALIZED.get(normalize_month(mo))


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


def extract_kpi_band_from_table(page):
    """Repli quand extract_kpi_band() (positions x/y fixes, calibrées sur
    la mise en page insp.cd) ne trouve rien — vu avec un PDF sante.gouv.cd
    où cette bande de chiffres clés est en réalité déjà correctement
    isolée par pdfplumber comme un TABLEAU à 6 cases (une par indicateur),
    chaque cellule ayant la forme 'LIBELLÉ\\nSUR PLUSIEURS\\nLIGNES\\nVALEUR'.
    On prend juste la dernière ligne de chaque cellule."""
    for t in page.extract_tables():
        for row in t:
            cells = [c for c in row if c]
            if len(cells) < 6:
                continue
            joined = " ".join(cells).upper()
            if "CAS" in joined and ("DÉCÈS" in joined or "DECES" in joined) and "LETALITE" in joined.replace("É", "E"):
                last_lines = [c.strip().split("\n")[-1] for c in cells[:6]]
                return {
                    "confirmed": norm_int(last_lines[0]),
                    "deaths": norm_int(last_lines[1]),
                    "cfr": norm_pct(last_lines[2]),
                    "inCTE": norm_int(last_lines[3]),
                    "recovered": norm_int(last_lines[4]),
                    "contactsFollowUpRate": norm_pct(last_lines[5]),
                }
    return None


def extract_one_date(full_text, label):
    """Cherche UNE date précédée du libellé donné ('Date de rapportage' ou
    'Date de publication'), indépendamment de l'autre. Auparavant, les deux
    dates étaient capturées par un seul regex combiné (DOTALL) : si l'une
    des deux lignes avait une formulation ou un espacement inhabituel dans
    un PDF particulier, les DEUX dates échouaient d'un coup (cas du SitRep
    058, entre autres).

    Cherche la date dans une FENÊTRE après le libellé (jusqu'à 60
    caractères), plutôt que d'exiger qu'elle le suive immédiatement : sur
    certains SitRep (079 à 083 notamment), le libellé et sa valeur ne sont
    pas adjacents dans le texte linéaire extrait par pdfplumber — la mise
    en page en tableau de cette zone du PDF fait que d'autres caractères
    (espaces, retours à la ligne, voire un autre mot) peuvent s'intercaler
    entre les deux, même s'ils sont visuellement côte à côte dans le PDF."""
    idx = full_text.find(label)
    if idx == -1:
        return None
    window = full_text[idx + len(label): idx + len(label) + 60]
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", window)
    if not m:
        return None
    d, mo, y = m.groups()
    mon = month_to_number(mo)
    if not mon:
        return None
    return f"{y}-{mon}-{int(d):02d}"


def extract_meta(full_text, fallback_number=None):
    compact = re.sub(r"\s+", "", full_text)
    m = re.search(r"SitRep(?:MVE)?N.0*(\d{1,3})", compact)
    sitrep_number = None
    sitrep_ref = None
    if m:
        sitrep_number = m.group(1).zfill(3)
        m2 = re.search(r"SitRep\s+(?:MVE\s+)?N°?\s*0*\d{1,3}[^\n]*", full_text)
        sitrep_ref = m2.group(0).strip() if m2 else f"SitRep N°{sitrep_number}"
        # Le nom de fichier (déduit du téléchargement, ex: SITREP_MVE_059.pdf)
        # est plus fiable que le numéro lu dans le texte du PDF : on a déjà vu
        # ce dernier corrompu (ex: le SitRep 059 s'est vu attribuer le numéro
        # "058" par cette regex, créant un doublon avec le vrai 058). Si les
        # deux se contredisent, on privilégie le nom de fichier — connu avec
        # certitude — plutôt que le texte, plus fragile.
        if fallback_number and sitrep_number != fallback_number:
            print(f"  ! numéro lu dans le texte ({sitrep_number}) différent du nom de "
                  f"fichier ({fallback_number}) — nom de fichier retenu par prudence.")
            sitrep_number = fallback_number
    elif fallback_number:
        sitrep_number = fallback_number
        sitrep_ref = f"SitRep N°{fallback_number} (référence illisible dans le PDF)"
    else:
        raise ValueError("Impossible de trouver la référence du SitRep dans le PDF.")

    reporting_date = extract_one_date(full_text, "Date de rapportage")
    publication_date = extract_one_date(full_text, "Date de publication")

    return {
        "sitrepNumber": sitrep_number,
        "sitrepRef": sitrep_ref,
        "reportingDate": reporting_date,
        "publicationDate": publication_date,
        "source": "INSP RDC / Task Force Présidentielle Ebola 17",
    }


def extract_province_summary(pdf):
    for page in pdf.pages:
        for t in page.extract_tables():
            if t and t[0] and t[0][0] and "Province" in str(t[0][0]):
                header = t[0]
                if len(header) >= 6 and "Cas" in str(header[1]):
                    return t
    return None


PROVINCE_SUMMARY_ROW_RE = re.compile(
    r"^(?P<name>Ituri|Nord-Kivu|Haut-Uélé|Tshopo|Sud-Kivu|Bas Uélé|Total)\s+"
    r"(?P<numbers>[\d ]+?)\s*(?P<cfr>[\d,]+)%\s+"
    r"(?P<zn>\d+)/(?P<zt>\d+)\s*\([\d,]+\s*%\)\s+"
    r"(?P<newcases>\d+)\s*$",
    re.MULTILINE,
)


def _best_cas_deces_split(numbers_str, cfr_target):
    """Désambiguïse 'cas décès' quand les deux nombres sont collés sans
    séparateur fiable (ex: '4257 1 878' — impossible de savoir
    syntaxiquement si c'est cas=4257/décès=1878 ou cas=42571/décès=878).
    Essaie toutes les coupures possibles de la séquence de tokens et
    retient celle dont la létalité calculée (décès/cas) colle le mieux à
    la létalité donnée en toutes lettres dans le texte — un ancrage fiable
    puisqu'elle n'a pas cette ambiguïté de collage."""
    tokens = numbers_str.split()
    best = None
    for k in range(1, len(tokens)):
        try:
            cas = int("".join(tokens[:k]))
            deces = int("".join(tokens[k:]))
        except ValueError:
            continue
        if cas == 0:
            continue
        implied_cfr = deces / cas * 100
        diff = abs(implied_cfr - cfr_target)
        if best is None or diff < best[0]:
            best = (diff, cas, deces)
    if best is None:
        return None, None
    return best[1], best[2]


def parse_province_summary_from_text(full_text):
    """Repli quand extract_province_summary() ne trouve pas la table via
    pdfplumber (mise en page en colonnes différente selon la source, vu
    avec un PDF provenant de sante.gouv.cd plutôt que insp.cd — la
    section très 'Total cas' ne tombe alors plus dans la colonne attendue
    du tableau). Relit directement le texte brut de la section, ligne par
    ligne, comme pour les sous-totaux de province du tableau détaillé."""
    start = full_text.find("Répartition des cas et décès confirmés par province touchée")
    end = full_text.find("Cas et décès confirmés par province et zone de santé")
    if start == -1 or end == -1 or end <= start:
        return None, None
    section = full_text[start:end]

    provinces = []
    total_row = None
    for line in section.split("\n"):
        line = line.strip()
        m = PROVINCE_SUMMARY_ROW_RE.match(line)
        if not m:
            continue
        cfr_target = float(m.group("cfr").replace(",", "."))
        cas, deces = _best_cas_deces_split(m.group("numbers"), cfr_target)
        if cas is None:
            continue
        row_dict = {
            "name": m.group("name"),
            "confirmed": cas,
            "deaths": deces,
            "cfr": cfr_target,
            "healthZonesAffected": {"n": int(m.group("zn")), "total": int(m.group("zt"))},
            "newCases24h": int(m.group("newcases")),
        }
        if m.group("name") == "Total":
            total_row = ["Total", cas, deces, cfr_target, None, int(m.group("newcases"))]
        else:
            row_dict["name"] = PROVINCE_CANON.get(m.group("name"), m.group("name"))
            provinces.append(row_dict)

    if not provinces or total_row is None:
        return None, None
    return provinces, total_row


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
    reliable = [(p, n, r) for p, n, r in zones_raw if not zone_row_looks_unreliable(r)]
    dropped = len(zones_raw) - len(reliable)
    if dropped:
        print(f"  ! {dropped} ligne(s) de zone jugée(s) non fiable(s) côté tableau "
              f"(colonnes décalées) — reconstruites depuis le texte brut.")
    return gap_fill_missing_zones(full_text, reliable)


def zone_row_to_dict(province, name, row):
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
    fallback_num = None
    fm = re.search(r"(\d{3})", os.path.basename(pdf_path))
    if fm:
        fallback_num = fm.group(1)
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        meta = extract_meta(full_text, fallback_number=fallback_num)
        prov_table = extract_province_summary(pdf)
        confirmed = deaths = None
        if prov_table:
            _, total_row = parse_province_summary(prov_table)
        else:
            # Même repli que dans main() : certains PDF (ex: sante.gouv.cd
            # plutôt qu'insp.cd) ont une mise en page en colonnes que
            # pdfplumber ne détecte pas comme la table attendue.
            _, total_row = parse_province_summary_from_text(full_text)
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
        # Distingue "jamais encore essayé" (confirmedExtractionFailed absent)
        # de "essayé, table introuvable par aucune des deux méthodes" (True)
        # — sans ça, rebuild_reports_list() retenterait indéfiniment, à
        # chaque run, les tout premiers SitRep (format d'époque sans cette
        # table), qui ne réussiront jamais quel que soit le nombre de
        # tentatives.
        "confirmedExtractionFailed": confirmed is None,
    }


def rebuild_reports_list(current_reports):
    existing_by_num = {r["sitrepNumber"]: r for r in current_reports}
    all_pdfs = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")))
    reports = []
    for pdf_path in all_pdfs:
        m = re.search(r"(\d{3})", os.path.basename(pdf_path))
        if not m:
            continue
        num = m.group(1)
        existing = existing_by_num.get(num)
        # confirmed manquant ne déclenche une nouvelle tentative que si on
        # n'a pas déjà marqué cet échec comme définitif (voir
        # confirmedExtractionFailed dans parse_report_summary) — sinon les
        # tout premiers SitRep (001-003..., format d'époque sans cette
        # table) seraient retentés indéfiniment à chaque run, pour rien.
        confirmed_retry_worthwhile = existing is not None \
            and existing.get("confirmed") is None \
            and not existing.get("confirmedExtractionFailed")
        needs_parse = existing is None or not existing.get("reportingDate") \
            or confirmed_retry_worthwhile
        if existing is not None and not needs_parse:
            entry = dict(existing)
            entry["file"] = pdf_path.replace("\\", "/")
            reports.append(entry)
        else:
            try:
                reports.append(parse_report_summary(pdf_path))
                tag = "nouveau rapport détecté et ajouté" if existing is None else \
                      "date/donnée manquante, ré-analysé"
                print(f"  + {tag} : {os.path.basename(pdf_path)}")
            except Exception as e:
                print(f"  ! avertissement : impossible d'analyser {pdf_path} ({e}), ignoré.")
                if existing is not None:
                    entry = dict(existing)
                    entry["file"] = pdf_path.replace("\\", "/")
                    reports.append(entry)
    reports.sort(key=lambda r: r["sitrepNumber"])
    return reports


def rebuild_sitreps_json(reports, national_recovered_by_sitrep):
    by_date = {}
    if os.path.exists(SITREPS_PATH):
        try:
            with open(SITREPS_PATH, encoding="utf-8") as f:
                for entry in json.load(f):
                    if entry.get("date"):
                        by_date[entry["date"]] = entry
        except Exception:
            pass

    for r in reports:
        date = r.get("reportingDate")
        if not date or r.get("confirmed") is None:
            continue
        recovered = national_recovered_by_sitrep.get(r["sitrepNumber"])
        if recovered is None:
            prev = by_date.get(date)
            recovered = prev.get("recovered") if prev else None
        by_date[date] = {
            "date": date,
            "confirmed": r["confirmed"],
            "deaths": r.get("deaths"),
            "recovered": recovered,
        }

    sitreps = sorted(by_date.values(), key=lambda s: s["date"])

    os.makedirs(os.path.dirname(SITREPS_PATH), exist_ok=True)
    with open(SITREPS_PATH, "w", encoding="utf-8") as f:
        json.dump(sitreps, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return sitreps


def rebuild_zones_history(meta, health_zones):
    if not health_zones:
        print("  (pas de détail par zone exploitable pour ce SitRep, "
              "zones-history.json non modifié)")
        return

    reporting_date = meta.get("reportingDate")
    sitrep_number = meta.get("sitrepNumber")
    if not reporting_date or not sitrep_number:
        print("  (date ou numéro de SitRep manquant, zones-history.json non modifié)")
        return

    existing = []
    if os.path.exists(ZONES_HISTORY_PATH):
        with open(ZONES_HISTORY_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    by_sitrep = {e["sitrep"]: e for e in existing}

    by_sitrep[sitrep_number] = {
        "sitrep": sitrep_number,
        "date": reporting_date,
        "zones": [
            {"name": z["name"], "province": z["province"],
             "cases": z["cases"], "deaths": z["deaths"]}
            for z in health_zones
        ],
    }

    merged = sorted(by_sitrep.values(), key=lambda e: e["date"])

    os.makedirs(os.path.dirname(ZONES_HISTORY_PATH), exist_ok=True)
    with open(ZONES_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"  zones-history.json mis à jour : {len(merged)} point(s) au total "
          f"(SitRep {sitrep_number} ajouté/rafraîchi, {len(health_zones)} zones).")


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
        meta = extract_meta(full_text, fallback_number=f"{report_num:03d}")
        kpis = extract_kpi_band(pdf.pages[0])
        if kpis.get("confirmed") is None and kpis.get("inCTE") is None:
            # Méthode positionnelle vide : probablement une mise en page
            # différente (voir extract_kpi_band_from_table pour le détail).
            fallback_kpis = extract_kpi_band_from_table(pdf.pages[0])
            if fallback_kpis:
                print("  ! bande de chiffres clés introuvable via positions x/y, "
                      "repli sur le tableau détecté par pdfplumber.")
                kpis = fallback_kpis
        sidebar = extract_sidebar_text(pdf.pages[0])

        prov_table = extract_province_summary(pdf)
        if prov_table is not None:
            provinces, prov_total_row = parse_province_summary(prov_table)
        else:
            # Repli texte brut : vu sur un PDF sante.gouv.cd dont la mise en
            # page en colonnes diffère de celle d'insp.cd (voir
            # parse_province_summary_from_text pour le détail).
            print("  ! table de répartition par province introuvable via pdfplumber, "
                  "repli sur une lecture du texte brut.")
            provinces, prov_total_row = parse_province_summary_from_text(full_text)
            if provinces is None:
                raise ValueError("Table de répartition par province introuvable "
                                  "(ni via tableau, ni via texte brut).")

        zone_rows = extract_zone_detail_rows(pdf)
        _, zones_raw, detail_total_row = parse_zone_detail(zone_rows)
        zones_raw = revalidate_zones(full_text, zones_raw)
        province_subtotals_text = extract_province_subtotals_from_text(full_text)

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

    national_recovered_by_sitrep = {meta["sitrepNumber"]: national["recovered"]}
    sitreps = rebuild_sitreps_json(reports, national_recovered_by_sitrep)

    rebuild_zones_history(meta, health_zones)

    print(f"data/latest.json mis à jour : SitRep {meta['sitrepNumber']} "
          f"({national['confirmed']} cas, {national['deaths']} décès) — "
          f"{len(reports)} rapport(s) listé(s) dans l'onglet.")
    print(f"data/sitreps.json régénéré : {len(sitreps)} point(s) de données "
          f"(du {sitreps[0]['date']} au {sitreps[-1]['date']}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
