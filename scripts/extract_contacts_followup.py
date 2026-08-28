#!/usr/bin/env python3
"""
Extrait le taux de suivi des contacts (%) pour TOUS les SitReps disponibles,
avec leur vraie date de rapportage (pas juste leur numéro), et écrit le
résultat complet dans data/contacts-followup.json.

Contrairement à scan_contacts_poepoc.py (diagnostic, échantillon limité à
15 valeurs pour la lisibilité du log), ce script exporte l'intégralité des
valeurs trouvées — c'est le fichier de données réel destiné à alimenter un
graphique sur le site, pas un simple sondage de fiabilité.

La valeur est lue dans le TABLEAU « Suivi des contacts des cas confirmés »,
ligne « Total », et non plus par une regex sur le texte linéaire. Cette
regex cherchait le premier « nombre% » dans les 80 caractères suivant une
formule comme « suivi des contacts » ; à partir du SitRep 034 l'INSP a
ajouté un commentaire qui écrit le taux à côté de sa CIBLE (« cible 95% »)
et déplacé la valeur réelle plus bas dans la page. Résultat : elle ne
trouvait plus rien (17 juin → 3 juillet perdus) ou attrapait le mauvais
nombre — le SitRep 038 s'est vu attribuer 95,0 % (la cible) au lieu de
70,8 % (le Total réel), et le 048 un taux de zone de santé isolée (67,3 %)
au lieu de 82,7 %. Lire une cellule d'un tableau explicitement intitulé
« Taux de suivi (%) » supprime cette classe d'erreur : la cible ne figure
pas dans ce tableau.

Usage: python3 scripts/extract_contacts_followup.py
"""
import glob
import json
import os
import re

import pdfplumber

from update_data import (
    extract_meta,
    extract_number_from_filename,
    norm_int,
    norm_pct,
)

REPORTS_DIR = "reports"
OUTPUT_PATH = "data/contacts-followup.json"

# SitRep écartés du graphique — non pas parce que la valeur est illisible,
# mais parce qu'elle n'est pas comparable aux autres points.
#
# "028" (11 juin, 28,4 %) : ce jour-là les zones de santé n'ayant pas
# rapporté ont été laissées AU DÉNOMINATEUR, sans contrepartie au
# numérateur — le bulletin le dit lui-même en note 3 (« Ce faible taux
# global est la résultante de données non rapportées dans la province de
# l'Ituri », Rwampara et Bunia concentrant 55,6 % des contacts de la
# province). Tous les autres bulletins excluent au contraire ces zones des
# deux termes du rapport. Tracer 28,4 % au milieu d'une série à ~70 %
# montrerait un effondrement du suivi qui n'a pas eu lieu.
#
# "038" et "048" ont été retirés de cette liste : ils n'y figuraient qu'à
# cause du bug de la regex décrit plus haut, et la lecture du tableau leur
# rend leurs vraies valeurs (70,8 % et 82,7 %) — celle du 038 est d'ailleurs
# confirmée à l'identique par la lecture manuelle du rapport OMS du 21 juin.
CONTACTS_EXCLUDED_SITREPS = {"028"}

TABLE_TITLE_RE = re.compile(r"Tableau\s*\d*\s*[.:]\s*Suivi des contacts", re.IGNORECASE)
TABLE_HEADER_RE = re.compile(r"Taux\s+de\s+suivi", re.IGNORECASE)
PROVINCE_RE = re.compile(
    r"^(Ituri|Nord-Kivu|Sud-Kivu|Haut-Uélé|Tshopo|Bas Uélé)\s*\*?$", re.IGNORECASE
)

# Repli pour les bulletins SANS ce tableau (017, et à partir du 059 où la
# valeur ne figure plus que dans la bande de chiffres clés de la page 1).
CONTACTS_RE = re.compile(
    r"(?:taux de suivi des contacts|suivi des contacts|proportion des contacts suivis)"
    r".{0,80}?(\d[\d,]*)\s*%",
    re.IGNORECASE | re.DOTALL,
)
# Un « % » précédé de « cible » n'est pas une mesure mais un objectif : c'est
# exactement ce que l'ancienne regex confondait. On regarde le texte qui
# précède immédiatement le nombre capturé.
TARGET_RE = re.compile(r"cible", re.IGNORECASE)


def cell(c):
    """Normalise une cellule pdfplumber (None, retours à la ligne, espaces
    insécables) en une chaîne simple."""
    if c is None:
        return ""
    return " ".join(str(c).replace("\xa0", " ").split())


def first_cell(row):
    """Le premier libellé non vide d'une ligne.

    On ne peut pas se contenter de row[0] : la grille reconstruite par
    pdfplumber ouvre très souvent une colonne vide en tête, si bien que
    « Total » se retrouve en deuxième cellule (SitReps 034, 038, 041...)."""
    for c in row or ():
        text = cell(c)
        if text:
            return text
    return ""


def find_contacts_rows(pdf):
    """Renvoie les lignes du tableau « Suivi des contacts », ou None.

    On localise la PAGE par son titre, puis on parcourt ses tableaux à plat.
    Le regroupement en tableaux ne peut pas servir de découpage : selon la
    façon dont le bulletin est tramé, pdfplumber rend ici trois « tableaux »
    d'une seule ligne chacun (l'en-tête, puis la ligne Total, puis un
    tableau d'indicateurs sans rapport) plutôt qu'un tableau de quatre
    lignes. On accumule donc les lignes à partir de l'en-tête « Taux de
    suivi » — ou, à défaut, de la première ligne provinciale — et on
    s'arrête à la ligne « Total », ce qui laisse dehors ce qui suit sur la
    même page."""
    for page in pdf.pages:
        text = page.extract_text() or ""
        if not TABLE_TITLE_RE.search(text):
            continue
        rows = []
        started = False
        for table in page.extract_tables():
            for row in table:
                if not row:
                    continue
                first = first_cell(row)
                if not started:
                    joined = " ".join(cell(c) for c in row)
                    if not (TABLE_HEADER_RE.search(joined) or PROVINCE_RE.match(first)):
                        continue
                    started = True
                rows.append(row)
                if first.lower().startswith("total"):
                    return rows
        if rows:
            return rows
    return None


def row_numbers(row):
    """Les effectifs d'une ligne, dans l'ordre (contacts sous suivi, vus).

    On écarte explicitement les cellules de pourcentage : norm_int() ne
    garde que les chiffres, donc « 82,5% » lui vaut 825 et se glisserait
    dans la liste comme un troisième effectif."""
    out = []
    for c in row:
        raw = cell(c)
        if not raw or norm_pct(raw) is not None:
            continue
        n = norm_int(raw)
        if n is not None:
            out.append(n)
    return out


def row_percent(row):
    """Le dernier pourcentage plausible de la ligne. norm_pct() ne reconnaît
    que les formes « 71,1 % » / « 43,9 » et rend None sur « 6 043 » ou
    « NA », donc les colonnes d'effectifs ne peuvent pas être prises pour un
    taux."""
    best = None
    for c in row:
        v = norm_pct(cell(c))
        if v is not None and 0 <= v <= 100:
            best = v
    return best


def rate_from_table(table):
    """(taux, méthode, avertissement). La valeur imprimée dans la ligne
    « Total » fait foi ; le rapport vus/sous suivi ne sert qu'à la
    corroborer, jamais à la rejeter — sur plusieurs bulletins (034, 037,
    041, 042, 044) les colonnes d'effectifs de cette ligne sont décalées
    d'une ligne par la mise en page alors que le pourcentage, lui, est
    juste. Quand le pourcentage est absent ou vaut « NA » (cas du 036), on
    le recalcule à partir de la somme des lignes provinciales."""
    total_row = None
    provinces = []
    for row in table:
        first = first_cell(row)
        if first.lower().startswith("total"):
            total_row = row
        elif PROVINCE_RE.match(first):
            provinces.append(row)

    # Tableau sans aucun libellé de ligne — ni « Total », ni nom de province,
    # seulement les colonnes de chiffres (SitRep 048). On accepte alors la
    # dernière ligne comme total, mais uniquement si elle est effectivement
    # la somme des précédentes : c'est ce contrôle qui autorise à se passer
    # du libellé, sans quoi on prendrait n'importe quelle ligne pour un total.
    if total_row is None and not provinces:
        pairs = [n[:2] for n in (row_numbers(r) for r in table) if len(n) >= 2]
        if len(pairs) >= 3:
            parts, last = pairs[:-1], pairs[-1]
            if (last[0] > 0
                    and sum(p[0] for p in parts) == last[0]
                    and sum(p[1] for p in parts) == last[1]):
                return (round(last[1] / last[0] * 100, 1),
                        "tableau (total non libellé, vérifié par la somme)", None)

    printed = row_percent(total_row) if total_row else None

    computed = None
    if total_row:
        nums = row_numbers(total_row)
        if len(nums) >= 2 and nums[0] > 0:
            computed = round(nums[1] / nums[0] * 100, 1)

    summed = None
    pairs = [row_numbers(r)[:2] for r in provinces]
    pairs = [p for p in pairs if len(p) == 2]
    if len(pairs) >= 2:
        suivi = sum(p[0] for p in pairs)
        vus = sum(p[1] for p in pairs)
        if suivi > 0:
            summed = round(vus / suivi * 100, 1)

    if printed is not None:
        warn = None
        corroboration = next((c for c in (computed, summed) if c is not None), None)
        # Un ratio > 100 % ne signale pas un désaccord sur la valeur mais une
        # ligne dont les colonnes ont glissé (« Total 80 80 71,1% ») : inutile
        # d'en faire un avertissement, le cas est déjà connu et sans remède.
        if corroboration is not None and corroboration <= 100 and abs(corroboration - printed) > 0.15:
            warn = (f"pourcentage imprimé {printed}% mais vus/sous suivi donne "
                    f"{corroboration}% (colonnes d'effectifs probablement décalées "
                    f"par la mise en page — le pourcentage imprimé est retenu)")
        return printed, "tableau (ligne Total)", warn

    fallback = summed if summed is not None else computed
    if fallback is not None:
        return fallback, "tableau (recalculé : vus / sous suivi)", None

    return None, None, None


TOTAL_LINE_RE = re.compile(r"^\s*Total\b(?P<mid>.*?)(?P<pct>[\d,]+)\s*%\s*$")
# « 9 971 8 126 » -> « 9971 8126 » : l'espace qui précède un groupe de
# exactement trois chiffres est un séparateur de milliers, pas une frontière
# entre deux nombres.
THOUSANDS_RE = re.compile(r"(\d) (?=\d{3}\b)")


def rate_from_lines(full_text):
    """Repli quand pdfplumber ne reconstruit AUCUNE grille sur la page du
    tableau — cas du SitRep 050, dont le tableau n'a pas de trame et où
    extract_tables() ne rend rien du tout. Le texte de la page, lui, reste
    parfaitement structuré : « Total 9 971 8 126 81,5% ».

    On ne balaie que les quelques lignes qui suivent le titre du tableau :
    la même page porte d'autres lignes « Total » (alertes du jour, cas
    suspects du jour) qui n'ont rien à voir avec le suivi des contacts."""
    lines = full_text.split("\n")
    start = next((i for i, l in enumerate(lines) if TABLE_TITLE_RE.search(l)), None)
    if start is None:
        return None, None, None

    for line in lines[start:start + 10]:
        m = TOTAL_LINE_RE.match(line)
        if not m:
            continue
        value = norm_pct(m.group("pct") + "%")
        if value is None or not 0 <= value <= 100:
            continue
        warn = None
        nums = [int(n) for n in
                re.findall(r"\d+", THOUSANDS_RE.sub(r"\1", m.group("mid")))]
        if len(nums) >= 2 and nums[0] > 0:
            computed = round(nums[1] / nums[0] * 100, 1)
            if computed <= 100 and abs(computed - value) > 0.15:
                warn = (f"ligne Total lue dans le texte : {value}% imprimé, "
                        f"{computed}% recalculé")
        return value, "ligne Total (texte de la page)", warn
    return None, None, None


def rate_from_text(full_text):
    """Repli sur le texte linéaire, en refusant tout nombre annoncé comme
    une cible."""
    for m in CONTACTS_RE.finditer(full_text):
        before = full_text[max(0, m.start(1) - 40): m.start(1)]
        if TARGET_RE.search(before):
            continue
        value = float(m.group(1).replace(",", "."))
        if 0 <= value <= 100:
            return value, "texte (repli)"
    return None, None


# ---------------------------------------------------------------------------
# Le détail par province et les effectifs nationaux, pour la page « Riposte ».
#
# Le taux national suffisait à l'onglet de /donnees/ ; la page « Riposte »
# veut aussi le NOMBRE de contacts à suivre — c'est la taille de l'épidémie
# vue par la riposte — et le taux de chaque province, là où le suivi faiblit.
# Trois écritures selon l'époque :
#
#   B    les lignes de province du tableau « Suivi des contacts » :
#        « Ituri 10 183 7 957 78,1 % »
#   C    la bande de chiffres clés de la page 1 :
#        « 11 351/ 15 358 vus · Ituri 72,1 % - N-Kivu 78,9 % - Tshopo 100,0 % »
#   D    la phrase de surveillance :
#        « 83,4 % (14 277 vus sur 17 127 à suivre) … Ituri 85,8 % (5 954/6 940),
#          Tshopo 100 % (490/490) »
#
# Un effectif n'est gardé que s'il se vérifie : vus ≤ à suivre, et vus / à
# suivre à moins d'un point du taux imprimé. Sinon seul le taux reste.
PROVINCES_DETAIL_RE = r"Ituri|Nord[\s-]+Kivu|N-Kivu|Haut[\s-]+U[ée]l[ée]|H-U[ée]l[ée]|Tshopo|Sud[\s-]+Kivu|S-Kivu|Bas[\s-]+U[ée]l[ée]|B-U[ée]l[ée]"
PROV_D_RE = re.compile(r"(%s)\s+(\d+(?:[,.]\d+)?)\s*%%\s*\((\d[\d ]*)\s*/\s*(\d[\d ]*)\)" % PROVINCES_DETAIL_RE)
# « (22\n091 vus sur 26 850 à suivre) » : le nombre peut se casser sur deux
# lignes, d'où \s et non l'espace seule dans les milliers.
# Un nombre est un groupe de un a trois chiffres suivi de groupes de trois :
# « 14 466 » oui, « 16 14 466 » non. La bande de chiffres cles de l'epoque C
# colle le nombre de patients en isolement du Sud-Kivu aux contacts vus
# (« Sud-Kivu 16 14 466 / 18 276 vus ») ; un motif qui acceptait n'importe
# quels chiffres et espaces lisait 1 614 466 vus, puis rejetait le tout —
# huit jours d'effectifs perdus fin juillet.
NOMBRE = r"(?:\d{1,3}(?:\s\d{3})+|\d+)"
NATIONAL_D_RE = re.compile(r"(%s)\s*vus\s+sur\s+(%s)\s+(?:à|a)\s+suivre" % (NOMBRE, NOMBRE), re.IGNORECASE)
NATIONAL_C_RE = re.compile(r"(?<![\d])(%s)\s*/\s*(%s)\s*vus\b" % (NOMBRE, NOMBRE), re.IGNORECASE)
# Forme libre des premiers bulletins D (086-092) : « performances faibles au
# Haut-Uélé (76,1 %) et au Nord-Kivu (80,2 %) ; l'Ituri atteint 87,7% ».
PROV_D1_RE = re.compile(r"(%s)\s*\((\d+(?:[,.]\d+)?)\s*%%\)" % PROVINCES_DETAIL_RE)
PROV_D1_ATTEINT_RE = re.compile(r"l[’']?\s*(%s)\s+(?:atteint|est à|se situe à)\s+(\d+(?:[,.]\d+)?)\s*%%" % PROVINCES_DETAIL_RE)
PROV_C_RE = re.compile(r"(%s)\s+(\d+(?:[,.]\d+)?)\s*%%" % PROVINCES_DETAIL_RE)
PROV_LIGNE_B_RE = re.compile(
    r"\n\s*(%s)\s*\*?\s+(\d{1,3}(?: \d{3})*)\s+(\d{1,3}(?: \d{3})*)\s+(\d+(?:[,.]\d+)?)\s*%%" % PROVINCES_DETAIL_RE)


def canon_detail(nom):
    n = re.sub(r"[\s-]+", " ", nom).replace("Uele", "Uélé")
    n = {"N Kivu": "Nord-Kivu", "Nord Kivu": "Nord-Kivu", "S Kivu": "Sud-Kivu",
         "Sud Kivu": "Sud-Kivu", "H Uélé": "Haut-Uélé", "Haut Uélé": "Haut-Uélé",
         "B Uélé": "Bas-Uélé", "Bas Uélé": "Bas-Uélé"}.get(n, n)
    return n


def effectifs_verifies(vus, a_suivre, taux):
    """(vus, à suivre) si le couple se tient, sinon None."""
    if vus is None or a_suivre is None or a_suivre <= 0 or vus > a_suivre:
        return None
    if taux is not None and abs(vus / a_suivre * 100 - taux) > 1.0:
        return None
    return vus, a_suivre


def details_contacts(full_text, rows, taux_national=None):
    """{"contacts": {"aSuivre", "vus"}, "provinces": {nom: {"taux", "vus", "aSuivre"}}}"""
    out = {}
    provinces = {}
    # D — la phrase de surveillance, puis chaque province entre parenthèses.
    m = NATIONAL_D_RE.search(full_text)
    if m:
        vus, a_suivre = norm_int(m.group(1)), norm_int(m.group(2))
        if effectifs_verifies(vus, a_suivre, taux_national):
            out["contacts"] = {"aSuivre": a_suivre, "vus": vus}
    for pm in PROV_D_RE.finditer(full_text):
        nom = canon_detail(pm.group(1))
        taux = norm_pct(pm.group(2) + "%")
        vus, a_suivre = norm_int(pm.group(3)), norm_int(pm.group(4))
        if taux is None or nom in provinces:
            continue
        ligne = {"taux": taux}
        ok = effectifs_verifies(vus, a_suivre, taux)
        if ok:
            ligne["vus"], ligne["aSuivre"] = ok
        provinces[nom] = ligne
    # D, forme libre (086-092) : des taux entre parentheses, sans effectifs.
    if not provinces and m:
        zone = full_text[max(0, m.start() - 400):m.end() + 400]
        for rx in (PROV_D1_RE, PROV_D1_ATTEINT_RE):
            for pm in rx.finditer(zone):
                nom = canon_detail(pm.group(1))
                taux = norm_pct(pm.group(2) + "%")
                if taux is not None and nom not in provinces:
                    provinces[nom] = {"taux": taux}
    # B — les lignes de province du tableau. pdfplumber ne rend souvent que
    # l'en-tête et la ligne Total dans sa grille ; les provinces sont dans le
    # texte de la page, sous le titre du tableau : « Ituri* 9 335 7 825 83,8% ».
    # Les groupes de trois chiffres délimitent les nombres.
    if not provinces:
        mt = TABLE_TITLE_RE.search(full_text)
        if mt:
            zone = full_text[mt.end():mt.end() + 700]
            for pm in PROV_LIGNE_B_RE.finditer(zone):
                nom = canon_detail(pm.group(1))
                a_suivre, vus = norm_int(pm.group(2)), norm_int(pm.group(3))
                taux = norm_pct(pm.group(4) + "%")
                if taux is None or nom in provinces:
                    continue
                ligne = {"taux": taux}
                ok = effectifs_verifies(vus, a_suivre, taux)
                if ok:
                    ligne["vus"], ligne["aSuivre"] = ok
                provinces[nom] = ligne
    if rows and "contacts" not in out:
        total_row = next((r for r in rows if first_cell(r).lower().startswith("total")), None)
        if total_row:
            nums = row_numbers(total_row)
            if len(nums) >= 2:
                ok = effectifs_verifies(nums[1], nums[0], row_percent(total_row) or taux_national)
                if ok:
                    out["contacts"] = {"aSuivre": ok[1], "vus": ok[0]}
    if not provinces and rows:
        for row in rows:
            first = first_cell(row)
            if not PROVINCE_RE.match(first):
                continue
            nom = canon_detail(first.rstrip("*").strip())
            nums = row_numbers(row)
            taux = row_percent(row)
            if taux is None and len(nums) >= 2 and nums[0] > 0:
                taux = round(nums[1] / nums[0] * 100, 1)
            if taux is None:
                continue
            ligne = {"taux": taux}
            if len(nums) >= 2:
                ok = effectifs_verifies(nums[1], nums[0], taux)
                if ok:
                    ligne["vus"], ligne["aSuivre"] = ok
            provinces[nom] = ligne
    # C — la bande de chiffres clés : « 11 351/ 15 358 vus · Ituri 72,1 % - … »
    if "contacts" not in out:
        m = NATIONAL_C_RE.search(full_text)
        if m:
            vus, a_suivre = norm_int(m.group(1)), norm_int(m.group(2))
            # Le 077 écrit « 17 828/ 13 420 vus » : plus de vus que de contacts
            # à suivre, impossible — mais 13 420 / 17 828 = 75,3 %, le taux
            # imprimé sur la même ligne. Les deux nombres sont publiés, dans
            # le mauvais ordre ; on ne les retient inversés que si le taux
            # le prouve.
            if vus is not None and a_suivre is not None and vus > a_suivre \
                    and effectifs_verifies(a_suivre, vus, taux_national):
                vus, a_suivre = a_suivre, vus
            if effectifs_verifies(vus, a_suivre, taux_national):
                out["contacts"] = {"aSuivre": a_suivre, "vus": vus}
                if not provinces:
                    bande = full_text[m.end():m.end() + 200]
                    for pm in PROV_C_RE.finditer(bande):
                        nom = canon_detail(pm.group(1))
                        taux = norm_pct(pm.group(2) + "%")
                        if taux is not None and nom not in provinces:
                            provinces[nom] = {"taux": taux}
    if provinces:
        out["provinces"] = provinces
    return out


def main():
    pdfs = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.pdf")))
    print(f"{len(pdfs)} PDF trouvé(s) dans {REPORTS_DIR}/\n")

    results = []
    by_method = {}
    excluded = 0
    warnings = []
    missing = []

    for pdf_path in pdfs:
        name = os.path.basename(pdf_path)
        fallback_num = extract_number_from_filename(pdf_path)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
                meta = extract_meta(full_text, fallback_number=fallback_num)
                if meta.get("sitrepNumber") in CONTACTS_EXCLUDED_SITREPS:
                    excluded += 1
                    continue
                rows = find_contacts_rows(pdf)
                rate, method, warn = rate_from_table(rows) if rows else (None, None, None)
        except Exception as e:
            print(f"  ! {name} : erreur de lecture ({e})")
            continue

        if rate is None:
            rate, method, warn = rate_from_lines(full_text)
        if rate is None:
            rate, method = rate_from_text(full_text)

        if rate is None or not meta.get("reportingDate"):
            missing.append(meta.get("sitrepNumber") or fallback_num)
            continue

        if warn:
            warnings.append(f"{name} : {warn}")
        by_method[method] = by_method.get(method, 0) + 1
        point = {
            "date": meta["reportingDate"],
            "sitrepNumber": meta["sitrepNumber"],
            "contactsFollowUpRate": rate,
            "source": "SitRep INSP (automatique)",
        }
        point.update(details_contacts(full_text, rows, rate))
        results.append(point)

    # Une seule valeur par date (comme sitreps.json) : si deux rapports
    # partagent une date, on garde le dernier rencontré (ordre croissant de
    # numéro), avec un avertissement si les deux valeurs diffèrent.
    by_date = {}
    for r in results:
        existing = by_date.get(r["date"])
        if existing and existing["contactsFollowUpRate"] != r["contactsFollowUpRate"]:
            print(f"  ! ATTENTION : dates en double pour {r['date']} avec des valeurs "
                  f"différentes ({existing['contactsFollowUpRate']}% puis "
                  f"{r['contactsFollowUpRate']}% pour le SitRep {r['sitrepNumber']})")
        by_date[r["date"]] = r

    # Préserve tout point déjà présent dans le fichier qui ne vient PAS de
    # cette extraction automatique (ex: lecture manuelle des rapports OMS,
    # marquée par un "source" différent) — sans ce garde-fou, exécuter ce
    # script automatiquement chaque jour effacerait silencieusement ces
    # ajouts manuels à chaque régénération. Une vraie donnée INSP fraîche
    # reste toujours prioritaire si elle existe pour la même date (source
    # primaire), le point manuel n'intervient qu'en comblement de trou.
    preserved = 0
    previous_by_date = {}
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            previous = json.load(f)
        previous_by_date = {e["date"]: e for e in previous}
        for e in previous:
            if "INSP" in (e.get("source") or ""):
                continue  # sera régénéré fraîchement ci-dessus si toujours valide
            if e["date"] not in by_date:
                by_date[e["date"]] = e
                preserved += 1

    final = sorted(by_date.values(), key=lambda r: r["date"])

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"\n{OUTPUT_PATH} écrit : {len(final)} point(s) de données "
          f"({excluded} exclu(s) volontairement, {preserved} point(s) manuel(s) "
          f"préservé(s) — voir CONTACTS_EXCLUDED_SITREPS).")
    for method, n in sorted(by_method.items()):
        print(f"  - {n} par {method}")

    # Écarts par rapport au fichier précédent : c'est la seule façon de voir
    # qu'une correction (ou une régression) a eu lieu, le script tournant
    # sans surveillance dans GitHub Actions.
    added = [r for r in final if r["date"] not in previous_by_date]
    changed = [(r, previous_by_date[r["date"]]) for r in final
               if r["date"] in previous_by_date
               and previous_by_date[r["date"]]["contactsFollowUpRate"] != r["contactsFollowUpRate"]]
    removed = [d for d in previous_by_date if d not in by_date]
    if added:
        print(f"\n{len(added)} date(s) ajoutée(s) : "
              + ", ".join(f"{r['date']} ({r['contactsFollowUpRate']}%)" for r in added))
    if changed:
        print(f"\n{len(changed)} valeur(s) corrigée(s) :")
        for new, old in changed:
            print(f"  {new['date']} : {old['contactsFollowUpRate']}% -> "
                  f"{new['contactsFollowUpRate']}% (SitRep {new['sitrepNumber']})")
    if removed:
        print(f"\n{len(removed)} date(s) disparue(s) : {', '.join(sorted(removed))}")

    if warnings:
        print(f"\n{len(warnings)} avertissement(s) de cohérence :")
        for w in warnings:
            print(f"  ! {w}")
    if missing:
        print(f"\nRapports sans cette donnée ({len(missing)}) : {missing}")


if __name__ == "__main__":
    main()
