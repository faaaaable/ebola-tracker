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

# Numéros de SitRep dont le détail par zone est jugé trop peu fiable pour
# la carte (mise en page source trop différente, extraction trop
# incertaine malgré les replis) — leur entrée est simplement ignorée par
# rebuild_zones_history(), la carte s'arrête alors au dernier SitRep fiable
# précédent. Ajouter/retirer un numéro ici n'affecte que la carte, pas les
# autres chiffres du site (cas/décès nationaux, courbe épidémique...), qui
# continuent d'utiliser normalement ce même SitRep par ailleurs.
#
# Anciennement {"094"} : le fichier renommé en "094" (ex-"095", second
# SitRep sante.gouv.cd) a été revérifié le 20/08/2026 après correction du
# doublon "093" à la source — 18 zones extraites, aucune pollution (pas de
# "TOTAL RDC", pas de doublon de province, pas de fragment de type
# "Karissibi"/"Kilo Mission"). Les correctifs accumulés au pipeline
# suffisent maintenant à le traiter proprement ; l'exclusion est retirée.
ZONES_HISTORY_EXCLUDED_SITREPS = set()

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


# Tolère un suffixe optionnel après les 3 chiffres (bis/ter/quater, avec ou
# sans tiret/underscore) — pour les cas où la source elle-même a publié un
# numéro en double par erreur (ex: deux bulletins "N°093" à des dates
# différentes) : plutôt que de décaler indéfiniment toute la numérotation
# suivante, on isole l'erreur à cet unique bulletin ("093-bis") et on
# reprend la vraie numérotation de la source dès le suivant.
FILENAME_NUMBER_RE = re.compile(r"(\d{3})[-_]?(bis|ter|quater)?", re.IGNORECASE)


def extract_number_from_filename(path):
    """Renvoie le numéro de SitRep tel qu'identifiable depuis le nom de
    fichier (ex: '094', '093bis' -> '093-bis'), ou None si aucun trouvé.
    Le tri alphabétique naturel place bien '093' < '093-bis' < '094'."""
    m = FILENAME_NUMBER_RE.search(os.path.basename(path))
    if not m:
        return None
    num, suffix = m.group(1), m.group(2)
    return f"{num}-{suffix.lower()}" if suffix else num


def find_latest_report():
    """Trouve le SitRep le plus récent (numéro le plus élevé) dans reports/."""
    pdfs = glob.glob(os.path.join(REPORTS_DIR, "*.pdf"))
    best = None
    best_id = None
    for p in pdfs:
        num_id = extract_number_from_filename(p)
        if num_id is None:
            continue
        if best_id is None or num_id > best_id:
            best_id = num_id
            best = p
    return best, best_id


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
    # Numéro tel qu'imprimé DANS LE PDF, conservé même quand on lui préfère
    # le nom de fichier — pour pouvoir le signaler honnêtement sur le site
    # plutôt que de corriger silencieusement une erreur de numérotation de
    # la source (un visiteur qui télécharge et ouvre le PDF verrait sinon
    # un numéro différent de celui affiché chez nous, sans explication).
    source_printed_number = None
    if m:
        sitrep_number = m.group(1).zfill(3)
        source_printed_number = sitrep_number
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
        # None si les deux concordent (cas normal) — rempli seulement en
        # cas d'écart, pour ne pas alourdir latest.json/reports.json inutilement.
        "sourceNumberMismatch": source_printed_number if source_printed_number != sitrep_number else None,
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
    r"(?P<numbers>[\d ]+?)\s*(?P<cfr>[\d,]+)\s*%\s+"
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
    # Bornée à la section "Cas et décès confirmés par province et zone de
    # santé" (mêmes repères que get_zone_section_text) : sans ça, la
    # fonction aspire aussi les tableaux d'autres sections plus loin dans
    # le document (ex: le tableau des alertes par province, avec ses
    # colonnes 'DPS'/'Total Général' qui ont accidentellement la même
    # forme — vu avec le SitRep 094/sante.gouv.cd, qui a fait apparaître
    # 'DPS' et 'Total Général' comme si c'étaient des zones de santé).
    rows = []
    in_section = False
    for page in pdf.pages:
        page_text = page.extract_text() or ""
        if "Situation des alertes notifiées" in page_text:
            break
        if "Cas et décès confirmés par province et zone de santé" in page_text:
            in_section = True
        if not in_section:
            continue
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
    r"(?P<cas>\d[\d ]*|NA)\s+(?P<deces>\d[\d ]*|NA)\s+(?P<cfr>[\d,]+\s*%|NA)\s*(?P<tail>.*)$"
)

PROV_SUBTOTAL_RE = re.compile(
    r"^(?P<name>Ituri|Nord-Kivu|Haut-Uélé|Tshopo|Sud-Kivu|Bas Uélé)\s+"
    r"(?P<cas>\d[\d ]*)\s+(?P<deces>\d[\d ]*)\s+(?P<cfr>[\d,]+\s*%)\s+"
    r"(?P<newcases>\d[\d ]*)\s+(?P<deathscomm>\d[\d ]*)\s+"
    r"(?P<deathsintracte>\d[\d ]*)\s+(?P<total>\d[\d ]*)\s*$"
)


def get_zone_section_text(full_text):
    start = full_text.find("Cas et décès confirmés par province et zone de santé")
    if start == -1:
        return None
    # Plusieurs libellés candidats pour la fin de section : le texte exact
    # a légèrement varié d'un rapport à l'autre (ex: "Situation des
    # alertes notifiées par province" vs "Suivi des indicateurs aux
    # PoE/PoC"), donc on prend le premier trouvé après le début plutôt que
    # de dépendre d'un seul libellé figé.
    end_candidates = [
        full_text.find(marker, start)
        for marker in ("Situation des alertes notifiées", "Suivi des indicateurs aux PoE/PoC")
    ]
    end_candidates = [e for e in end_candidates if e != -1]
    if not end_candidates:
        return None
    end = min(end_candidates)
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


def normalize_zone_key(name):
    """Clé de comparaison insensible à la casse, aux tirets/espaces et aux
    astérisques de note de bas de page — pour dédupliquer correctement les
    zones même quand leur orthographe varie légèrement (vu dans un même
    rapport : 'BAMBU' vs 'Bambu', 'Oicha**' vs 'Oicha', 'Nia-Nia' vs
    'Nia Nia', 'Makiso-Kisangani' vs 'Makiso--Kisangani')."""
    n = name.strip().rstrip("*").strip()
    n = re.sub(r"-+", " ", n)
    n = re.sub(r"\s+", " ", n)
    n = n.upper()
    # Variantes orthographiques CONNUES de la même zone réelle (pas une
    # simple différence de casse/tiret, donc pas couvert par les règles
    # ci-dessus) — liste explicite plutôt qu'un rapprochement flou
    # généralisé, pour ne jamais fusionner à tort deux zones différentes
    # qui se ressembleraient par coïncidence.
    KNOWN_ALIASES = {
        "GETHY": "GETY",
    }
    return KNOWN_ALIASES.get(n, n)


def is_placeholder_zone_name(name):
    """Détecte les noms de zone "fourre-tout"/non identifiés (ex: 'Autres
    zones non encore identifiées', 'Tshopo (zone non précisée)') — pas de
    vraies zones de santé, mais des libellés génériques pour des cas non
    ventilés. Existent dans de très vieux rapports (antérieurs à l'ajout de
    ce filtre côté extraction fraîche) et revenaient sinon indéfiniment via
    le report de dernière valeur (rebuild_zones_history), malgré leur
    exclusion de toute nouvelle extraction depuis. 'Karissibi' et 'Kilo
    Mission' sont aussi exclus par prudence (comptes très faibles, rapports
    très anciens, jamais confirmés comme de vraies zones — à corriger si
    une vérification future prouve le contraire)."""
    n = name.upper()
    if "AUTRES ZONE" in n or "NON PRÉCISÉE" in n or "NON PRECISEE" in n \
            or "NON IDENTIFIÉE" in n or "NON IDENTIFIEE" in n:
        return True
    if name in ("Karissibi", "Kilo Mission"):
        return True
    return False


def gap_fill_missing_zones(full_text, zones_raw):
    section = get_zone_section_text(full_text)
    if not section:
        return zones_raw

    # Indexé par une clé NORMALISÉE (voir normalize_zone_key), pas par le
    # nom brut : une zone donnée n'appartient qu'à une seule province et ne
    # devrait apparaître qu'une fois, donc les variantes de casse/tiret/
    # note de bas de page doivent être reconnues comme la même zone plutôt
    # que de créer un doublon. On garde le premier nom "d'affichage"
    # rencontré pour chaque clé.
    by_key = {}
    for prov, name, row in zones_raw:
        by_key[normalize_zone_key(name)] = (name, prov, row)
    current_province = None

    for line in section.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Tiret/espace tolérés dans le nom de province ("Bas Uélé" vs
        # "Bas-Uélé" — vu varier d'un rapport à l'autre) : on compare une
        # version normalisée (tiret → espace) des deux côtés.
        line_normalized = line.replace("-", " ")
        matched_province = None
        for pname in PROVINCE_NAMES_MAIN:
            if line_normalized.startswith(pname.replace("-", " ")):
                matched_province = pname
                break
        if matched_province:
            current_province = matched_province
            continue
        # Insensible à la casse : ce rapport écrit "TOTAL RDC" tout en
        # majuscules, ce que l'ancienne comparaison ("Total" figé) ratait.
        # "Autres zones..." : catégorie fourre-tout pour cas non encore
        # attribués à une zone précise, pas une vraie zone de santé — vue
        # dupliquée 3 fois (fragments d'une ligne repliée sur plusieurs
        # lignes : "Autres zones non" / "... non encore" / "... encore
        # identifiées").
        line_upper = line.upper()
        if line_upper.startswith("A VENTILER") or line_upper.startswith("TOTAL") \
                or line_upper.startswith("AUTRES ZONES"):
            continue
        if current_province is None:
            continue
        m = ZONE_LINE_RE.match(line)
        if not m:
            continue
        name = m.group("name").strip()
        if is_placeholder_zone_name(name):
            continue
        key = normalize_zone_key(name)
        existing = by_key.get(key)
        if existing is not None and existing[1] == current_province:
            continue
        row = [name, m.group("cas"), m.group("deces"), m.group("cfr")]
        tail_nums = re.findall(r"\d+", m.group("tail"))
        row += tail_nums
        by_key[key] = (name, current_province, row)

    return [(prov, name, row) for name, prov, row in by_key.values()]


def parse_zone_detail(rows):
    province_subtotals = {}
    seen_subtotal = set()
    zones = []
    current_province = None
    total_row = None

    # Normalisation tiret/espace, même logique que dans gap_fill_missing_zones
    # (variantes vues d'un rapport à l'autre : "Bas Uélé" / "Bas-Uélé").
    province_by_normalized = {p.replace("-", " "): p for p in PROVINCE_NAMES_MAIN}

    for row in rows:
        name = row[0]
        name_normalized = (name or "").replace("-", " ")
        canon_province = province_by_normalized.get(name_normalized)
        if canon_province and canon_province not in seen_subtotal:
            seen_subtotal.add(canon_province)
            current_province = canon_province
            province_subtotals[canon_province] = row
            continue
        name_upper = (name or "").upper()
        if name_upper.startswith("A VENTILER"):
            continue
        if name_upper.startswith("TOTAL"):
            total_row = row
            continue
        if is_placeholder_zone_name(name or ""):
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
    fallback_num = extract_number_from_filename(pdf_path)
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
        "sourceNumberMismatch": meta.get("sourceNumberMismatch"),
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
        num = extract_number_from_filename(pdf_path)
        if num is None:
            continue
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

    # Garde-fou : signale tout numéro de SitRep partagé par deux dates
    # différentes — la source ayant déjà réutilisé un même numéro par
    # erreur (voir échanges du 19/08/2026), un mauvais renommage manuel
    # (ou une nouvelle erreur de la source) provoquerait sinon un
    # écrasement silencieux d'un rapport par un autre dans by_sitrep,
    # sans que rien ne le signale ailleurs dans le pipeline.
    dates_by_number = {}
    for r in reports:
        if r.get("reportingDate"):
            dates_by_number.setdefault(r["sitrepNumber"], set()).add(r["reportingDate"])
    for num, dates in dates_by_number.items():
        if len(dates) > 1:
            print(f"  ! ATTENTION : le numéro de SitRep {num} est partagé par plusieurs dates "
                  f"différentes ({', '.join(sorted(dates))}) — un des deux rapports écrase "
                  f"probablement l'autre silencieusement. Vérifier les noms de fichiers dans "
                  f"reports/.")

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
    sitrep_number = meta.get("sitrepNumber")
    if sitrep_number in ZONES_HISTORY_EXCLUDED_SITREPS:
        print(f"  (SitRep {sitrep_number} exclu de zones-history.json — voir "
              f"ZONES_HISTORY_EXCLUDED_SITREPS ; les autres chiffres du site "
              f"restent basés sur ce SitRep normalement.)")
        return

    if not health_zones:
        print("  (pas de détail par zone exploitable pour ce SitRep, "
              "zones-history.json non modifié)")
        return

    reporting_date = meta.get("reportingDate")
    if not reporting_date or not sitrep_number:
        print("  (date ou numéro de SitRep manquant, zones-history.json non modifié)")
        return

    existing = []
    if os.path.exists(ZONES_HISTORY_PATH):
        with open(ZONES_HISTORY_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    by_sitrep = {e["sitrep"]: e for e in existing}

    # Indexé par clé normalisée (voir normalize_zone_key), pas par nom brut
    # — sinon un décalage de casse/tiret entre deux rapports (ex: "Bambu"
    # ici, "BAMBU" côté report précédent) créerait un doublon au lieu
    # d'être reconnu comme la même zone.
    new_zones_by_key = {normalize_zone_key(z["name"]): z for z in health_zones}

    # Reporte la dernière valeur connue pour toute zone absente de CE
    # rapport mais présente dans un rapport antérieur — un cercle de la
    # carte ne doit jamais disparaître juste parce qu'un bulletin a cessé
    # de citer une zone dont les cas restent comptés dans le total
    # provincial (vu avec le SitRep 095, où le total Ituri ne correspondait
    # plus à la somme des zones listées : 4309 vs 3961, écart de 348 cas
    # correspondant exactement aux zones disparues du tableau).
    previous_entries = [e for e in existing if e.get("date") and e["date"] < reporting_date
                         and e.get("sitrep") != sitrep_number]

    # Alerte sur toute zone JAMAIS vue dans aucun rapport antérieur — une
    # vraie nouvelle zone touchée pour la première fois est possible (donc
    # on ne la bloque pas), mais on préfère un signal visible dans le log
    # pour vérification manuelle plutôt qu'un ajout silencieux, après avoir
    # vu passer "Karissibi" et "Kilo Mission" sans explication au SitRep 095.
    if previous_entries:
        all_known_keys = set()
        for e in previous_entries:
            for z in e.get("zones", []):
                all_known_keys.add(normalize_zone_key(z["name"]))
        never_seen = [z["name"] for z in health_zones
                      if normalize_zone_key(z["name"]) not in all_known_keys]
        if never_seen:
            print(f"  ! zone(s) jamais vue(s) dans aucun rapport antérieur, à vérifier "
                  f"manuellement (vraie nouvelle zone touchée, ou fragment d'extraction "
                  f"erroné) : {', '.join(never_seen)}")

    # Reporte la dernière valeur connue pour toute zone absente de CE
    # rapport mais présente dans un rapport antérieur — un cercle de la
    # carte ne doit jamais disparaître juste parce qu'un bulletin a cessé
    # de citer une zone dont les cas restent comptés dans le total
    # provincial (vu avec le SitRep 095, où le total Ituri ne correspondait
    # plus à la somme des zones listées : 4309 vs 3961, écart de 348 cas
    # correspondant exactement aux zones disparues du tableau).
    #
    # Exclut du report les noms de zones "fourre-tout"/non identifiées via
    # is_placeholder_zone_name() (voir sa docstring) — sans ça, ces noms
    # reviendraient indéfiniment via ce mécanisme de report, malgré leur
    # exclusion de toute extraction fraîche depuis.
    if previous_entries:
        previous_entries.sort(key=lambda e: e["date"])
        last_known = {}
        for e in previous_entries:
            for z in e.get("zones", []):
                if is_placeholder_zone_name(z["name"]):
                    continue
                last_known[normalize_zone_key(z["name"])] = z
        carried_forward = 0
        for key, z in last_known.items():
            if key not in new_zones_by_key:
                new_zones_by_key[key] = z
                carried_forward += 1
        if carried_forward:
            print(f"  {carried_forward} zone(s) absente(s) de ce rapport, "
                  f"dernière valeur connue reportée (cercle jamais retiré de la carte).")

    by_sitrep[sitrep_number] = {
        "sitrep": sitrep_number,
        "date": reporting_date,
        "zones": [
            {"name": z["name"], "province": z["province"],
             "cases": z["cases"], "deaths": z["deaths"]}
            for z in new_zones_by_key.values()
        ],
    }

    merged = sorted(by_sitrep.values(), key=lambda e: e["date"])

    os.makedirs(os.path.dirname(ZONES_HISTORY_PATH), exist_ok=True)
    with open(ZONES_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"  zones-history.json mis à jour : {len(merged)} point(s) au total "
          f"(SitRep {sitrep_number} ajouté/rafraîchi, {len(new_zones_by_key)} zones).")


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

    print(f"Régénération des données depuis {report_path} (SitRep {report_num})...")

    with pdfplumber.open(report_path) as pdf:
        full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        meta = extract_meta(full_text, fallback_number=report_num)
        kpis = extract_kpi_band(pdf.pages[0])
        # N'importe lequel des 6 champs manquant suffit à déclencher le
        # repli — exiger que confirmed ET inCTE soient vides simultanément
        # (version précédente) a laissé passer le cas réel du SitRep 094 :
        # confirmed avait récupéré une valeur non-vide (mais sans rapport,
        # à une mauvaise position de page), donc inCTE/recovered sont
        # restés vides sans jamais déclencher le repli.
        if any(kpis.get(k) is None for k in
               ("confirmed", "deaths", "cfr", "inCTE", "recovered", "contactsFollowUpRate")):
            fallback_kpis = extract_kpi_band_from_table(pdf.pages[0])
            if fallback_kpis:
                print("  ! au moins un champ de la bande de chiffres clés manquant via "
                      "positions x/y, repli sur le tableau détecté par pdfplumber.")
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
