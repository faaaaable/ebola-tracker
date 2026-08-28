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
PROVINCE_HISTORY_PATH = "data/province-history.json"

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


def _clef_province(name):
    """Forme comparable d'un nom de province : sans accent, sans casse, le
    trait d'union et l'espace confondus."""
    s = unicodedata.normalize("NFD", str(name or "").strip().lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.replace("-", " ").split())


# Dérivée de PROVINCE_CANON plutôt qu'écrite à côté : une province ajoutée
# là-haut se retrouve ici sans qu'on y pense.
PROVINCE_LOOKUP = {}
for _brut, _canon in PROVINCE_CANON.items():
    for _forme in (_brut, _canon):
        PROVINCE_LOOKUP[_clef_province(_forme)] = _canon


def canon_province(name):
    """Nom canonique d'une province, ou None si ce n'en est pas une.

    Les bulletins écrivent tantôt « Haut-Uélé », tantôt « Haut Uélé » — celui
    du 14 août a produit la seconde forme, et la courbe du Haut-Uélé y a perdu
    son point sans que rien ne le signale : `app.js` cherche les provinces par
    leur nom exact, dans `PROVINCE_COLORS`. Et un découpage raté a fait entrer
    le 19 mai une « province » nommée « touchées », reste de « provinces
    touchées », avec des valeurs nulles.

    Un nom absent de la table est donc écarté plutôt que recopié : mieux vaut
    une province manquante ce jour-là, visible comme telle, qu'une septième
    courbe fantôme."""
    return PROVINCE_LOOKUP.get(_clef_province(name))

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
    # « Cas » etait cherche en header[1] exactement. Le SitRep 099 dedouble la
    # cellule « Province » (artefact de fusion : pdfplumber rend la meme
    # valeur dans deux colonnes), ce qui repousse « Cas confirmes » en
    # header[2] : la table n'etait plus reconnue du tout, et le repli texte
    # echouait a son tour. On cherche donc dans les premieres cellules.
    for page in pdf.pages:
        for t in page.extract_tables():
            if t and t[0] and t[0][0] and "Province" in str(t[0][0]):
                header = t[0]
                if len(header) >= 6 and any("Cas" in str(c or "") for c in header[:4]):
                    return t
    return None


def letalite_de_ligne(cellule):
    """La letalite portee par une cellule, ou None si elle n'en porte pas.

    Le SitRep 103 laisse la cellule de letalite VIDE sur sa ligne « Total » —
    le rapport ne publie pas la letalite nationale dans ce tableau. Or
    compacte_ligne retire les cellules vides, c'est son role : la ligne tombe
    a cinq cellules, tout ce qui suit les deces se decale d'un cran, et
    l'index 3 atterrit sur la fraction de zones. Lue comme une letalite,
    « 58/151 (38,4 %) » donnait 38,4 % la ou le rapport dit 48,0 % — et
    l'index 5 des nouveaux cas sortait du tableau, ce qui a fait planter le
    pipeline. Le plantage a evite le pire : un chiffre faux publie en silence.

    Le test tient en une ligne, parce qu'un pourcentage precede d'une fraction
    n'est jamais une letalite.
    """
    if cellule is None:
        return None
    if re.search(r"\d\s*/\s*\d", str(cellule)):
        return None
    return norm_pct(cellule)


def compacte_ligne(row):
    """Ramene une ligne de tableau a ses cellules porteuses.

    Le nombre de colonnes de remplissage varie d'un rapport a l'autre — le
    096 en a deux a la fin, le 099 en a une apres le nom et deux avant les
    nouveaux cas. Les index fixes du parseur (row[1] = cas, row[4] = zones)
    ne tenaient que par accident. Une fois les vides retires, les six
    formats rencontres retombent sur le meme schema :

        nom | cas | deces | letalite | zones | nouveaux cas

    Seul le doublon de tete est supprime — celui d'une cellule fusionnee
    rendue deux fois (« Province | Province », « Total | Total »). Jamais
    ailleurs : deux nombres egaux qui se suivent sont legitimes (une
    province a 3 cas et 3 deces existe), et les collapser fabriquerait un
    chiffre faux.
    """
    cellules = [c for c in row if c is not None and str(c).strip()]
    if len(cellules) >= 2 and str(cellules[0]).strip() == str(cellules[1]).strip():
        del cellules[1]
    return cellules


PROVINCE_SUMMARY_ROW_RE = re.compile(
    r"^(?P<name>Ituri|Nord-Kivu|Haut-Uélé|Tshopo|Sud-Kivu|Bas Uélé|Total)\**\s+"
    r"(?P<numbers>[\d ]+?)\**\s*(?P<cfr>[\d,]+)\s*%\s+"
    r"(?P<zn>\d+)\s*(?:/|sur)\s*(?P<zt>\d+)\s*(?:\([\d,]+\s*%\))?\s+"
    r"(?P<newcases>\d+)\s*$",
    re.MULTILINE,
)


# La ligne « Total » sans sa fraction de zones.
#
# Au SitRep 102, pdfplumber a rejete la cellule « 58/151 (38,4 %) » sur les
# lignes qui precedent et suivent :
#
#     58/151 (38,4
#     Total 5 656 2 715 48,0% 72
#     %)
#
# PROVINCE_SUMMARY_ROW_RE exige cette fraction — elle sert de garde-fou contre
# les autres tableaux du document — et la ligne Total ne correspondait donc
# plus. Les six provinces passaient, le total non, et le script s'arretait sur
# « Table de repartition par province introuvable ». Ce motif la rattrape.
#
# Il ne relache pas la garde : « Total » en tete est deja tres specifique, et
# on exige toujours les deux cumuls, la letalite et UN seul nombre en fin de
# ligne. La ligne Total du tableau detaille, qui en porte quatre
# (« 72 18 17 35 »), ne peut pas correspondre. La fraction de zones n'est de
# toute facon pas conservee : total_row la stocke deja a None, elle est
# recalculee depuis la somme des provinces.
PROVINCE_TOTAL_ROW_RE = re.compile(
    r"^Total\**\s+(?P<numbers>[\d ]+?)\**\s*(?P<cfr>[\d,]+)\s*%\s+"
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
    ligne, comme pour les sous-totaux de province du tableau détaillé.

    Les marqueurs de début/fin de section ("Répartition des cas et décès
    confirmés par province touchée" / "Cas et décès confirmés par
    province et zone de santé") n'existent pas dans les tout premiers
    formats de rapport (vu avec le SitRep 057 : la section s'appelle
    juste "3. ANALYSE ÉPIDÉMIOLOGIQUE DÉTAILLÉE") — dans ce cas, on
    scanne le texte entier plutôt que de renoncer. La regex elle-même
    (PROVINCE_SUMMARY_ROW_RE) est assez spécifique (exige la fraction de
    zones entre parenthèses ET un nombre de nouveaux cas en fin de ligne)
    pour ne pas se faire piéger par d'autres tableaux du document
    (suivi des contacts, alertes, PoE/PoC) qui n'ont pas cette structure."""
    start = full_text.find("Répartition des cas et décès confirmés par province touchée")
    end = full_text.find("Cas et décès confirmés par province et zone de santé")
    if start != -1 and end != -1 and end > start:
        section = full_text[start:end]
    else:
        section = full_text

    provinces = []
    total_row = None
    for line in section.split("\n"):
        line = line.strip()
        m = PROVINCE_SUMMARY_ROW_RE.match(line)
        if not m and total_row is None:
            # Le total, dont la fraction de zones peut avoir ete rejetee sur
            # une autre ligne par l'extraction (voir PROVINCE_TOTAL_ROW_RE).
            mt = PROVINCE_TOTAL_ROW_RE.match(line)
            if mt:
                cfr_total = float(mt.group("cfr").replace(",", "."))
                cas_t, deces_t = _best_cas_deces_split(mt.group("numbers"), cfr_total)
                if cas_t is not None:
                    total_row = ["Total", cas_t, deces_t, cfr_total, None,
                                 int(mt.group("newcases"))]
                    print("  ! ligne « Total » relue sans sa fraction de zones "
                          "(cellule eclatee par l'extraction).")
                    continue
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


PROVINCE_NAMES = ("Ituri", "Nord-Kivu", "Haut-Uélé", "Haut Uélé", "Tshopo",
                  "Sud-Kivu", "Bas Uélé", "Bas-Uélé", "Total")


def roles_entete_resume(table):
    """Le role de chaque colonne du tableau resume, lu dans son en-tete.

    Le SitRep 104 a deplace « Nouveaux cas confirmes (24h) » de la DERNIERE
    colonne a la DEUXIEME, juste apres le nom de la province. La lecture par
    position (cas en row[1], deces en row[2], nouveaux cas en row[-1]) a
    alors publie, sans un seul avertissement : 52 cas confirmes en Ituri au
    lieu de 4 802, 4 802 deces au lieu de 2 159, 2 836 778 nouveaux cas — la
    fraction « 28/36 (77,8 %) » lue comme un entier — et 481 nouveaux cas
    nationaux, la letalite « 48,1% » de la ligne Total lue de la meme facon.

    L'en-tete, lui, dit ou est chaque colonne. Il peut s'etaler sur plusieurs
    lignes (« Nouveaux cas » / « confirmes(24h) », « Zones de » / « sante » /
    « touchees ») : on fusionne colonne par colonne toutes les lignes qui
    precedent la premiere ligne de donnees. Renvoie une liste de roles, un par
    colonne, None pour une colonne de remplissage ou non reconnue.
    """
    entete = None
    for row in table:
        premier = str(row[0] or "").strip().rstrip("*").strip() if row else ""
        if premier in PROVINCE_NAMES:
            break
        cellules = [str(c or "").replace("\n", " ") for c in row]
        if entete is None:
            entete = cellules
        else:
            entete = [(a + " " + b).strip() for a, b in zip(entete, cellules)]
    roles = []
    for cellule in entete or []:
        s = cellule.lower()
        if not s.strip():
            roles.append(None)
        elif "province" in s:
            roles.append("name")
        elif "nouveau" in s:
            roles.append("newcases")
        elif re.search(r"\bcas\b", s):
            roles.append("confirmed")
        elif "décès" in s or "deces" in s:
            roles.append("deaths")
        elif "létalité" in s or "letalite" in s:
            roles.append("cfr")
        elif "zone" in s:
            roles.append("zones")
        else:
            roles.append(None)
    return roles


def nouveaux_cas_en_tete(roles):
    """Vrai quand l'en-tete place les nouveaux cas AVANT les cas cumules —
    la mise en page du SitRep 104. C'est le seul cas ou la lecture par
    position se trompe, et le seul ou l'on s'en remet a l'en-tete."""
    if "newcases" not in roles or "confirmed" not in roles:
        return False
    return roles.index("newcases") < roles.index("confirmed")


def parse_province_summary_par_entete(table, roles):
    """Lecture du tableau resume par les colonnes de son en-tete.

    On travaille sur la ligne BRUTE, pas compactee : dans cette mise en page
    la cellule « nouveaux cas » de la ligne Total est vide, et la compacter
    aurait decale la letalite sur les nouveaux cas. Le tableau etant
    rectangulaire, l'index d'en-tete vaut pour chaque ligne.

    La ligne Total est rendue dans l'ORDRE HISTORIQUE — nom, cas, deces,
    letalite, zones, nouveaux cas — parce que l'aval la lit par position
    (prov_total_row[1], [2], [3] et [-1]).
    """
    index = {}
    for i, role in enumerate(roles):
        if role and role not in index:
            index[role] = i

    def cellule(row, role):
        i = index.get(role)
        if i is None or i >= len(row) or row[i] is None:
            return ""
        return str(row[i]).strip()

    provinces = []
    total_row = None
    for row in table:
        if not row or not row[0]:
            continue
        name = str(row[0]).strip().rstrip("*").strip()
        if name not in PROVINCE_NAMES:
            continue
        cas = cellule(row, "confirmed")
        deces = cellule(row, "deaths")
        cfr = cellule(row, "cfr")
        zones = cellule(row, "zones")
        nouveaux = cellule(row, "newcases")
        if name == "Total":
            total_row = ["Total", cas, deces, cfr, zones, nouveaux]
            continue
        zm = re.search(r"(\d+)\s*/\s*(\d+)", zones)
        n_zones, tot_zones = (int(zm.group(1)), int(zm.group(2))) if zm else (None, None)
        provinces.append({
            "name": PROVINCE_CANON.get(name, name),
            "confirmed": norm_int(cas),
            "deaths": norm_int(deces),
            "cfr": letalite_de_ligne(cfr),
            "healthZonesAffected": {"n": n_zones, "total": tot_zones},
            "newCases24h": norm_int(nouveaux),
        })
    return provinces, total_row


def parse_province_summary(table):
    roles = roles_entete_resume(table)
    if nouveaux_cas_en_tete(roles):
        print("  · tableau des provinces : nouveaux cas en deuxième colonne, "
              "lecture guidée par l'en-tête (mise en page du SitRep 104).")
        return parse_province_summary_par_entete(table, roles)
    provinces = []
    total_row = None
    for row in table[1:]:
        if not row or not row[0]:
            continue
        # Retire les astérisques de renvoi de note (ex: "Tshopo*") avant la
        # recherche dans PROVINCE_CANON — sans ça, le nom brut "Tshopo*"
        # échoue à correspondre à "Tshopo" et s'affiche tel quel, astérisque
        # inclus, dans le tableau "Par province" (vu avec le SitRep 097).
        row = compacte_ligne(row)
        if not row:
            continue
        name = str(row[0]).strip().rstrip("*").strip()
        if name == "Total":
            total_row = row
            continue
        zones_raw = row[4] if len(row) > 4 else ""
        zm = re.search(r"(\d+)\s*/\s*(\d+)", zones_raw)
        n_zones, tot_zones = (int(zm.group(1)), int(zm.group(2))) if zm else (None, None)
        # "Nouveaux cas confirmés(24h)" est toujours la DERNIÈRE cellule de
        # la ligne, mais le nombre de colonnes de remplissage avant (sous
        # "Zones de santé") a varié d'un rapport à l'autre — un index fixe
        # (row[5]) pointait dans le vide pour ce nouveau format et
        # renvoyait toujours 0 (vu avec le SitRep 096 : row[5] était None,
        # la vraie valeur était en row[7]).
        provinces.append({
            "name": PROVINCE_CANON.get(name, name),
            "confirmed": norm_int(row[1]),
            "deaths": norm_int(row[2]),
            "cfr": letalite_de_ligne(row[3] if len(row) > 3 else None),
            "healthZonesAffected": {"n": n_zones, "total": tot_zones},
            "newCases24h": norm_int(row[-1]),
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
            # Le SitRep 099 place le resume par province et le detail par zone
            # sur la meme page : le premier tombait donc dans la moisson du
            # second, et sa ligne « Total » etait prise pour celle du detail.
            # Les colonnes ne coincidant pas, newDeaths24h valait 57151377
            # (la fraction « 57/151 (37,7 » lue comme un entier) et
            # newDeathsCommunity24h 477 (la letalite « 47,7% »). Les deux
            # tableaux se distinguent par leur en-tete : « Province » seul
            # pour le resume, « Province / Zone de sante » pour le detail.
            entete = t[0][0] if t and t[0] else None
            if entete and str(entete).strip() == "Province":
                continue
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


NAME_FRAGMENT_RE = re.compile(r"^[^\W\d_][^\W\d_.'\u2019\-]*[-.']?[^\W\d_]*$", re.UNICODE)
NUMERIC_ROW_RE = re.compile(r"^[\d\s,%]+$")

TOTAL_SUBTOTAL_RE = re.compile(
    r"^Total\s+(?P<cas>\d[\d ]*)\s+(?P<deces>\d[\d ]*)\s+(?P<cfr>[\d,]+\s*%)\s+"
    r"(?P<newcases>\d[\d ]*)\s+(?P<deathscomm>\d[\d ]*)\s+"
    r"(?P<deathsintracte>\d[\d ]*)\s+(?P<total>\d[\d ]*)\s*$"
)


def unwrap_split_names(section):
    """Recompose les libellés que la mise en page coupe sur trois lignes.

    Le PDF écrit parfois le nom de part et d'autre de ses propres chiffres :

        Nord-
        680 463 68,1% 17 10 1 11
        Kivu

    On en refait « Nord-Kivu 680 463 68,1% 17 10 1 11 ». Sans cela la ligne
    n'est reconnue ni comme province ni comme zone, et sa ventilation des
    décès est perdue en silence — le site affichait « +0 » là où onze
    personnes étaient mortes.

    Le trait d'union final dit si les deux moitiés se recollent directement
    (« Nord-Kivu ») ou avec une espace (« Boma Mangbetu »). La reconstruction
    reste locale à cette lecture : le texte brut continue de servir ailleurs,
    inchangé.
    """
    lines = [line.strip() for line in section.split("\n")]
    out = []
    i = 0
    while i < len(lines):
        head = lines[i]
        if (i + 2 < len(lines) and head and NAME_FRAGMENT_RE.match(head)
                and lines[i + 1] and NUMERIC_ROW_RE.match(lines[i + 1])
                and lines[i + 2] and NAME_FRAGMENT_RE.match(lines[i + 2])):
            joiner = "" if head.endswith("-") else " "
            out.append("%s%s%s %s" % (head, joiner, lines[i + 2], lines[i + 1]))
            i += 3
            continue
        out.append(head)
        i += 1
    return "\n".join(out)


def extract_detail_total_from_text(full_text):
    """Ligne « Total » du tableau détaillé : cumuls et ventilation nationale
    des décès des dernières 24 h. Repli quand la phrase des faits saillants
    change de tournure — ce qu'elle fait d'un rapport à l'autre."""
    section = get_zone_section_text(full_text)
    if not section:
        return None
    for line in unwrap_split_names(section).split("\n"):
        m = TOTAL_SUBTOTAL_RE.match(line.strip())
        if m:
            return m.groupdict()
    return None


def extract_province_subtotals_from_text(full_text):
    section = get_zone_section_text(full_text)
    if not section:
        return {}
    out = {}
    for line in unwrap_split_names(section).split("\n"):
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

    # Recomposition prealable des libelles coupes sur trois lignes : sans
    # elle, l'en-tete « Nord-Kivu » n'est jamais reconnu et toutes les zones
    # qui suivent restent attribuees a la province precedente. Vu avec le
    # SitRep 098, ou les douze zones du Nord-Kivu et les six du Haut-Uele se
    # retrouvaient en Ituri.
    for line in unwrap_split_names(section).split("\n"):
        line = line.strip()
        if not line:
            continue
        # Tiret/espace tolérés dans le nom de province ("Bas Uélé" vs
        # "Bas-Uélé" — vu varier d'un rapport à l'autre) : on compare une
        # version normalisée (tiret → espace) des deux côtés. Un éventuel
        # préfixe "Sous-total " est aussi retiré (variante rencontrée avec
        # le SitRep 087 : "Sous-total Ituri" au lieu de "Ituri" seul).
        line_normalized = re.sub(r"^sous.total\s+", "", line.replace("-", " "), flags=re.IGNORECASE)
        matched_province = None
        for pname in PROVINCE_NAMES_MAIN:
            if line_normalized.startswith(pname.replace("-", " ")):
                matched_province = pname
                break
        # Meme regle que dans parse_zone_detail : une ligne qui commence par
        # le nom de la province EN COURS decrit une zone homonyme, pas un
        # nouvel en-tete. Sans quoi la zone de sante « Tshopo », dans la
        # province du meme nom, disparait — et ce repli est justement celui
        # qui reconstruit les lignes que pdfplumber rate.
        if matched_province and matched_province == current_province:
            matched_province = None
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
        if line_upper.startswith("TOTAL"):
            # Le Total ferme un tableau : la province en cours retombe a
            # zero, pour que la regle ci-dessus reste vraie si un second
            # tableau s'ouvre sur la province qui vient de se fermer.
            current_province = None
            continue
        if line_upper.startswith("A VENTILER") or line_upper.startswith("AUTRES ZONES"):
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
    zones = []
    current_province = None
    total_row = None

    # Normalisation tiret/espace, même logique que dans gap_fill_missing_zones
    # (variantes vues d'un rapport à l'autre : "Bas Uélé" / "Bas-Uélé").
    province_by_normalized = {p.replace("-", " "): p for p in PROVINCE_NAMES_MAIN}

    for row in rows:
        name = row[0]
        # Retire les astérisques de renvoi de note (ex: "Tshopo*", collé au
        # nom sans espace) avant la comparaison — sans ça, cette variante
        # échappe à la détection de province au même titre que le nom exact,
        # et se retrouve traitée comme une fausse zone (vu avec le SitRep
        # 097 : "Tshopo*" non reconnu malgré le nom "Tshopo" déjà couvert).
        name_normalized = (name or "").rstrip("*").strip().replace("-", " ")
        # Retire aussi un éventuel préfixe "Sous-total " (variante rencontrée
        # avec le SitRep 087 : "Sous-total Ituri" au lieu de "Ituri" seul) —
        # insensible à la casse et au tiret/espace, comme le reste.
        name_normalized = re.sub(r"^sous.total\s+", "", name_normalized, flags=re.IGNORECASE)
        canon_province = province_by_normalized.get(name_normalized)
        # Une ligne qui porte le nom de la province EN COURS n'est pas un
        # nouvel en-tete : c'est une zone de sante homonyme de sa province.
        # La Tshopo en compte une, et elle etait avalee ici depuis toujours —
        # absente des tableaux, absente de la carte, et son sous-total de
        # province ecrase au passage par la ligne de la zone (1 cas au lieu
        # de 15), puisque « le sous-total garde est celui de la DERNIERE
        # occurrence ». Un en-tete legitime arrive toujours alors qu'une
        # AUTRE province est en cours, ou apres le Total qui remet le
        # compteur a zero : la confusion n'est donc pas possible.
        if canon_province and canon_province == current_province:
            canon_province = None
        if canon_province:
            # Pas de garde "vu une seule fois" : certains PDF incluent DEUX
            # tableaux distincts avec un sous-total par province chacun (le
            # résumé "Répartition par province touchée" ET le détail "Cas et
            # décès confirmés par province et zone de santé") — sans ça, la
            # deuxième occurrence légitime d'un nom de province (celle du
            # bon tableau) tombait à travers cette protection et se
            # retrouvait traitée comme une fausse zone (vu avec le SitRep
            # 096 : Ituri, Nord-Kivu, Haut-Uélé, Tshopo, Sud-Kivu, Bas Uélé
            # tous remontés comme "zones jamais vues"). Le sous-total gardé
            # est simplement celui de la DERNIÈRE occurrence rencontrée.
            current_province = canon_province
            province_subtotals[canon_province] = row
            continue
        name_upper = (name or "").upper()
        if name_upper.startswith("A VENTILER"):
            continue
        if name_upper.startswith("TOTAL"):
            total_row = row
            # Le Total ferme un tableau. Remettre la province a zero rend la
            # regle ci-dessus infaillible quand le PDF enchaine deux tableaux
            # dont le dernier et le premier nomment la meme province.
            current_province = None
            continue
        if is_placeholder_zone_name(name or ""):
            continue
        if current_province is None:
            continue
        zones.append((current_province, name, row))

    return province_subtotals, zones, total_row


def zone_row_looks_unreliable(row):
    """Une ligne dont on ne sait pas lire les colonnes.

    Le test ne portait que sur la TETE de la ligne — cas, deces, letalite — et
    laissait passer une queue decalee. Le SitRep 103 est exactement ce cas :
    ses lignes ont des cas et des deces justes, et des nouveaux cas qui sont la
    letalite privee de sa virgule. Faute de reperer la letalite, on ne sait pas
    non plus ou commence la queue : la ligne entiere est alors douteuse.
    """
    try:
        i_let = index_letalite_zone(row)
        if i_let is None:
            return True
        tete = [c for c in row[1:i_let] if c not in (None, "")]
        cases = norm_int(tete[0]) if len(tete) > 0 else None
        deaths = norm_int(tete[1]) if len(tete) > 1 else None
        cfr = norm_pct(row[i_let])
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


def parse_zone_day_columns(row, i_letalite=None):
    """Lit la queue d'une ligne de zone : nouveaux cas et deces des 24 h.

    Le tableau du bulletin porte QUATRE colonnes apres la letalite :
    nouveaux cas, deces communautaires, deces intra-CTE, puis un TOTAL des
    deces. Ce total etait ignore, et c'est ce qui faisait doubler les chiffres
    publies : quand une zone n'a de deces que dans une seule des deux
    categories, le PDF n'imprime pas la cellule vide de l'autre. La lecture
    par position tombait alors sur le total en croyant lire l'intra-CTE, et
    « 3 deces communautaires » devenait « 3 communautaires + 3 intra-CTE ».
    Constate sur le SitRep 101 : Bunia affichait (+6) pour 3 deces reels, et
    le Nord-Kivu repartissait 16 deces sur trois zones quand la province en
    declarait 8.

    Le total fait desormais foi, parce qu'il est la seule valeur que le
    bulletin imprime toujours. La ventilation communaute / CTE n'est
    renseignee que lorsque la ligne la donne sans ambiguite ; sinon elle
    reste None. On sait alors qu'un des deux compteurs porte le total, mais
    pas lequel, et le depot ne devine pas : le site n'affiche de toute facon
    que le total.

    LA QUEUE COMMENCE APRES LA LETALITE, reperee par sa forme et non par son
    rang — voir index_letalite_zone. L'index fixe row[4:] lisait la letalite
    elle-meme comme un nombre de nouveaux cas des que le bulletin deplacait une
    cellule vide.

    Retourne (nouveaux_cas, deces_comm, deces_intracte, total_deces).
    """
    depart = (i_letalite + 1) if i_letalite is not None else 4
    tail = row[depart:]

    # Chemin pdfplumber : les cellules vides sont conservees, donc les
    # positions tiennent. On ne s'y fie que si les trois valeurs se recoupent.
    if len(tail) >= 4:
        c, t, tot = norm_int(tail[1]), norm_int(tail[2]), norm_int(tail[3])
        if tot is not None and (c or 0) + (t or 0) == tot:
            return norm_int(tail[0]) or 0, c or 0, t or 0, tot

    # Chemin texte brut : les cellules vides ont disparu, seules restent les
    # valeurs imprimees. On les compte pour savoir ce qu'on tient.
    vals = [v for v in (norm_int(x) for x in tail) if v is not None]
    if not vals:
        return 0, 0, 0, 0
    new_cases = vals[0]
    rest = vals[1:]
    if not rest:                       # aucun deces ce jour dans cette zone
        return new_cases, 0, 0, 0
    if len(rest) >= 3:                 # comm, intra-CTE, total : tout est dit
        return new_cases, rest[0], rest[1], rest[2]
    # Une seule categorie imprimee, suivie du total : le total fait foi et la
    # ventilation reste indeterminee.
    return new_cases, None, None, rest[-1]


def index_letalite_zone(row):
    """Position de la cellule de letalite dans une ligne de zone.

    LE NOMBRE DE CELLULES VIDES AVANT ELLE VARIE D'UN BULLETIN A L'AUTRE. Le
    SitRep 102 ecrit ['Aru', '7', None, '6', None, None, '85,7%', ...], le 103
    ecrit ['Adja', '11', '1', None, '9,1%', ...] — une cellule vide s'est
    deplacee. Les index fixes (row[2] pour les deces, row[4:] pour la queue)
    ne tenaient que par accident, et le 103 les a fait tomber a cote : « 9,1% »
    lu par norm_int donnait 91 nouveaux cas en 24 h. Les 28 zones de l'Ituri
    totalisaient 10 161 nouveaux cas quand la province en declarait 34.

    Un pourcentage ne se confond avec rien d'autre sur cette ligne : tout ce
    qui l'entoure est un effectif. C'est donc lui le repere, et non un rang.
    """
    for i in range(2, len(row)):
        if row[i] and re.search(r"\d\s*%", str(row[i])):
            return i
    return None


def zone_row_to_dict(province, name, row):
    i_let = index_letalite_zone(row)
    if i_let is not None:
        # Les cumules sont les cellules PORTEUSES entre le nom et la letalite :
        # les cas d'abord, les deces ensuite, quel que soit le nombre de vides.
        tete = [c for c in row[1:i_let] if c not in (None, "")]
        cases = norm_int(tete[0]) if len(tete) > 0 else None
        deaths = norm_int(tete[1]) if len(tete) > 1 else None
        cfr = norm_pct(row[i_let])
    else:
        cases = norm_int(row[1])
        deaths = norm_int(row[2]) if len(row) > 2 else None
        cfr = norm_pct(row[3]) if len(row) > 3 else None
    if cfr is None and cases:
        cfr = round((deaths or 0) / cases * 100, 1)
    new_cases, deaths_comm, deaths_intracte, new_deaths = parse_zone_day_columns(row, i_let)
    return {
        "name": name,
        "province": PROVINCE_CANON.get(province, province),
        "cases": cases or 0,
        "deaths": deaths or 0,
        "cfr": cfr if cfr is not None else 0.0,
        "newCases24h": new_cases or 0,
        "newDeaths24h": new_deaths or 0,
        "deathsCommunity24h": deaths_comm,
        "deathsIntraCTE24h": deaths_intracte,
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
        existing = by_date.get(date)
        # Deux rapports peuvent partager la même date (ex: SitRep 004 et 005,
        # tous deux datés du 19 mai 2026) — si les DEUX ont un "confirmed"
        # exploitable, celui traité en second écraserait silencieusement
        # l'autre sans ce signalement, sans fusion ni avertissement.
        if existing and existing.get("confirmed") is not None and existing["confirmed"] != r["confirmed"]:
            print(f"  ! ATTENTION : plusieurs SitRep partagent la date {date} avec des "
                  f"valeurs de \"confirmed\" DIFFÉRENTES ({existing['confirmed']} puis "
                  f"{r['confirmed']} pour le SitRep {r['sitrepNumber']}) — seule la "
                  f"dernière valeur est conservée dans sitreps.json, l'autre est perdue "
                  f"pour la courbe épidémique (mais reste visible dans l'onglet Rapports).")
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


def rebuild_province_history(meta, provinces):
    """Historique quotidien des cumuls par province — cas ET décès.

    Sert le graphique « Par province » de la page de données et les courbes de
    chaque page province. Toujours complet par construction (le
    total provincial est présent dans chaque SitRep, contrairement au détail
    par zone parfois partiel) — pas besoin de report de dernière valeur.

    Les décès ont longtemps été jetés ici alors que le tableau des bulletins
    les imprime à côté des cas : les pages province ne pouvaient donc afficher
    aucune courbe de mortalité. Les sommer depuis zones-history.json n'aurait
    pas convenu, le détail par zone ne couvrant pas tout — l'Ituri y perd les
    233 décès « à ventiler », et la courbe aurait contredit le chiffre affiché
    en haut de la même page."""
    reporting_date = meta.get("reportingDate")
    if not reporting_date or not provinces:
        return

    history = []
    if os.path.exists(PROVINCE_HISTORY_PATH):
        with open(PROVINCE_HISTORY_PATH, encoding="utf-8") as f:
            history = json.load(f)
    by_date = {h["date"]: h for h in history}

    by_date[reporting_date] = {
        "date": reporting_date,
        "provinces": [
            {"name": canon, "confirmed": p.get("confirmed"),
             "deaths": p.get("deaths")}
            for canon, p in ((canon_province(p.get("name")), p) for p in provinces)
            if canon
        ],
    }

    merged = sorted(by_date.values(), key=lambda h: h["date"])
    os.makedirs(os.path.dirname(PROVINCE_HISTORY_PATH), exist_ok=True)
    with open(PROVINCE_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"  province-history.json mis à jour : {len(merged)} jour(s) au total.")


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

        # Toujours essayer le tableau D'ABORD, mais retomber sur le texte
        # s'il est vide (pas seulement s'il est absent) — une table ne
        # contenant que l'en-tête (0 ligne de donnée, sans lignes Ituri/
        # Nord-Kivu/etc.) est un cas fréquent selon la mise en page du
        # rapport, et doit aussi déclencher le repli texte. Sans ce garde-
        # fou, la plupart des rapports d'une certaine période (juin-août)
        # produisaient silencieusement une liste de provinces vide au lieu
        # d'utiliser le repli qui, lui, fonctionne (vu lors du rattrapage
        # complet de l'historique par province, 49 rapports concernés).
        prov_table = extract_province_summary(pdf)
        provinces = []
        if prov_table is not None:
            provinces, prov_total_row = parse_province_summary(prov_table)
        if not provinces:
            # Repli texte brut : vu sur un PDF sante.gouv.cd dont la mise en
            # page en colonnes diffère de celle d'insp.cd (voir
            # parse_province_summary_from_text pour le détail).
            print("  ! table de répartition par province introuvable ou vide via "
                  "pdfplumber, repli sur une lecture du texte brut.")
            provinces, prov_total_row = parse_province_summary_from_text(full_text)
            if provinces is None:
                raise ValueError("Table de répartition par province introuvable "
                                  "(ni via tableau, ni via texte brut).")

        zone_rows = extract_zone_detail_rows(pdf)
        _, zones_raw, detail_total_row = parse_zone_detail(zone_rows)
        zones_raw = revalidate_zones(full_text, zones_raw)
        province_subtotals_text = extract_province_subtotals_from_text(full_text)
        detail_total_text = extract_detail_total_from_text(full_text)

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
            # Ici vivait « daysNoCase », un compteur de jours sans nouveau cas
            # que RIEN n'affichait : ni le generateur de pages, ni le
            # JavaScript. Seul « status » sert, via l'etiquette « Aucun cas
            # recent ». Il est retire plutot que repare.
            #
            # Il etait faux, de deux facons opposees. Il s'incrementait a
            # chaque EXECUTION du script et non par jour ecoule : trois
            # passages sur un meme bulletin ajoutaient trois jours, et toute
            # reprise apres echec ou tout rattrapage faisait de meme. A
            # l'inverse, un jour sans bulletin ne declenchait aucune
            # execution, donc le temps passait sans que le compteur bouge —
            # sept numeros manquent dans la serie. Il annonçait 109 jours
            # sans cas au Sud-Kivu quand la serie entiere ne couvre que
            # 100 jours, du 14 mai au 22 aout.
            #
            # Le jour ou ce chiffre servira, il se calcule depuis les dates
            # et non par incrementation : province-history.json porte le
            # cumul de chaque province par date, la derniere hausse donne le
            # jour du dernier cas. A savoir : cet historique commence le
            # 31 mai, donc pour le Sud-Kivu la reponse honnete serait « plus
            # de 83 jours », pas un nombre exact.
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

    # Faute de letalite dans la ligne « Total » (cas du SitRep 103), on garde
    # celle des indicateurs de tete plutot que d'inventer.
    cfr_total = (letalite_de_ligne(prov_total_row[3])
                 if prov_total_row and len(prov_total_row) > 3 else None)

    national = {
        "confirmed": norm_int(prov_total_row[1]) if prov_total_row else None,
        "deaths": norm_int(prov_total_row[2]) if prov_total_row else None,
        "recovered": kpis["recovered"],
        "cfr": cfr_total if cfr_total is not None else kpis["cfr"],
        "inCTE": kpis["inCTE"],
        "contactsFollowUpRate": kpis["contactsFollowUpRate"],
        "provincesAffected": len(provinces),
        "healthZonesAffected": {"n": zones_total_n, "total": zones_total_tot},
        "healthAreasAffected": health_areas,
        "newCases24h": norm_int(prov_total_row[-1]) if prov_total_row else None,
        "newDeaths24h": norm_int(detail_total_row[6]) if detail_total_row and len(detail_total_row) > 6 else None,
        "newDeathsCommunity24h": norm_int(detail_total_row[4]) if detail_total_row and len(detail_total_row) > 4 else None,
        "newDeathsIntraCTE24h": norm_int(detail_total_row[5]) if detail_total_row and len(detail_total_row) > 5 else None,
    }

    # Repli sur la ligne « Total » du tableau détaillé quand la lecture par
    # colonnes n'a rien donné : elle porte les mêmes chiffres, en clair.
    if detail_total_text:
        for key, field in (("newCases24h", "newcases"),
                           ("newDeaths24h", "total"),
                           ("newDeathsCommunity24h", "deathscomm"),
                           ("newDeathsIntraCTE24h", "deathsintracte")):
            if national.get(key) is None:
                national[key] = norm_int(detail_total_text[field])

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
    rebuild_province_history(meta, provinces)

    print(f"data/latest.json mis à jour : SitRep {meta['sitrepNumber']} "
          f"({national['confirmed']} cas, {national['deaths']} décès) — "
          f"{len(reports)} rapport(s) listé(s) dans l'onglet.")
    print(f"data/sitreps.json régénéré : {len(sitreps)} point(s) de données "
          f"(du {sitreps[0]['date']} au {sitreps[-1]['date']}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
