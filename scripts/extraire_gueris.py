#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guéris déclarés par province, bulletin par bulletin, et cumuls par province.

Un guéri est déclaré à sa sortie d'une structure de prise en charge (CTE,
centre de transit, hôpital, ESS hors CTE) après deux tests négatifs ; les
bulletins ne comptent aucun guéri en communauté.

Lit tous les SitRep de l'INSP et écrit data/gueris-provinces.json. Chaque
bulletin dit les guéris du jour de plusieurs façons, selon l'époque ; toutes
sont lues, et la première dont la somme des provinces retombe sur son total
est retenue :

  tableau            (006-079) ligne « Guéris » du tableau « Mouvement des
                     patients » : « Guéris 15 1 0 16 » sous « Indicateur
                     Ituri Nord-Kivu Sud-Kivu Ensemble ».
  faits saillants    les phrases du début, sous toutes leurs formes :
                     « 39 patients (15 au Nord-Kivu, …) ont été déclarés
                     guéris » (131-) ; « 24 patients ont été déclarés guéris
                     après … (12 en Ituri, 11 au Haut-Uélé et 1 au Nord-Kivu) »
                     (085-130) ; « +15 guéris (Ituri 13 · N-Kivu 2) »
                     (059-083) ; « Seize (16) patients … dont 15 dans la
                     province de l'Ituri (6 au CTE Mongbwalu, …) et 1 au CTE
                     Katwa dans la province du Nord-Kivu ont été déclarés
                     guéris » (021-058), avec les zones et les CTE rattachés à
                     leur province.
  prise en charge    la rubrique par province : « → Ituri : 13 nouveaux
                     guéris », « o Ituri : … et 32 guérisons », « En Ituri, …
                     contre 95 sorties, dont 22 guéris ». Retenue seulement si
                     sa somme retombe sur un total lu ailleurs.

Le tableau « Non-cas / Guéris » (022-026) mêle deux sorties : il n'est pas lu.
Les cumuls par province, publiés par endroits (« le cumul des patients guéris
est de 122 dont 113 en Ituri, 7 au Nord-Kivu et 2 au Sud-Kivu », « Le cumul
des guéris de la province atteint 1 836 »), sont relevés à part, tels quels.

    python scripts/extraire_gueris.py
"""
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textes_pdf import ROOT, rapports, numero, texte_du_rapport  # noqa: E402
from update_data import extract_meta  # noqa: E402
from extraire_cte import canon, PROVINCES_RE, TRAITEMENT_RE  # noqa: E402

OUTPUT_PATH = os.path.join(ROOT, "data", "gueris-provinces.json")
SITREPS_PATH = os.path.join(ROOT, "data", "sitreps.json")
GEO_PATH = os.path.join(ROOT, "data", "health-zones.geojson")

PROVINCES = ["Ituri", "Nord-Kivu", "Sud-Kivu", "Haut-Uélé", "Bas-Uélé", "Tshopo", "Sud-Ubangi", "Nord-Ubangi"]


def compact(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", t)


CLES = {compact(p): p for p in PROVINCES}
CLES["nkivu"] = "Nord-Kivu"
CLES["huele"] = "Haut-Uélé"

# Zones de santé et structures des premiers bulletins, qui nomment le lieu
# sans la province (« Cinq (5) patients (Rwampara : 3, Mongbwalu : 1 et
# Mambasa : 1) »). Les zones viennent du fond de carte ; les CTE portent le nom
# d'un quartier ou d'un sigle.
STRUCTURES = {"cme": "Ituri", "istm": "Ituri", "elikya": "Ituri", "elykia": "Ituri", "sota": "Ituri",
              "kigonze": "Ituri", "kingoze": "Ituri", "kalunguta": "Nord-Kivu"}


def lieux():
    with open(GEO_PATH, encoding="utf-8") as fh:
        geo = json.load(fh)
    res = {}
    for f in geo["features"]:
        p = f["properties"]
        if p.get("province") in PROVINCES and len(compact(p["name"])) >= 4:
            res[compact(p["name"])] = p["province"]
    res.update(STRUCTURES)
    res["nyakunde"] = "Ituri"
    return res


LIEUX = lieux()

MOTS = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8,
        "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "treize": 13, "quatorze": 14, "quinze": 15, "seize": 16,
        "vingt": 20, "trente": 30, "quarante": 40, "cinquante": 50, "soixante": 60}


def en_lettres(mot):
    """« Trente-sept » -> 37, « Vingt-un » -> 21, « Dix-neuf » -> 19."""
    total = 0
    for p in re.split(r"[-\s]+(?:et[-\s]+)?", mot.lower()):
        if p not in MOTS:
            return None
        total += MOTS[p]
    return total or None


NOMBRE = r"(\d[\d\s]{0,5}|[A-Za-zéèÉ]+(?:-[a-zé]+){0,2})"


def lire_nombre(t):
    t = t.strip()
    c = re.sub(r"\s", "", t)
    if c.isdigit():
        return int(c)
    return en_lettres(t)


def souple(mot):
    """Le PDF coupe des mots (« d éclarés », « résultat s », « é té ») :
    une espace facultative entre chaque lettre."""
    return r"\s?".join(re.escape(ch) if ch not in "ée" else "[ée]" for ch in mot)


DECLARES = souple("déclar") + r"[ée]?s?\s+(?:comme\s+)?" + souple("guéri")

# Les colonnes de la marge (« 55 Zones de santé touchées sur 151 (37,1%) »,
# « 246 Aires de santé ») tombent au milieu des phrases.
BRUIT_RE = re.compile(r"\d[\d\s]{0,4}\s*(?:Zones?|Aires?)\s+de\s+sant[ée]|t\s?ouch[ée]e?s?(?:\s+[Ss]ur\s+\d[\d\s]{0,4}\d)?"
                      r"|\(\s*\d+[,.]\d+\s*%\s*\)|\b[Ss]ur\s+\d{3,4}\b")


def nettoyer(t):
    return re.sub(r"\s+", " ", BRUIT_RE.sub(" ", t))


def ventiler(passage, total):
    """{province: nombre} d'un passage « 16 en Ituri, 3 au Nord-Kivu… » ou
    « Ituri 13 · N-Kivu 2 ». Le nombre se prend devant le nom, sinon après
    (bandeau). Si une seule province nommée reste sans nombre, elle prend la
    différence. None si la somme ne retombe pas sur le total."""
    c = compact(passage)
    trouves = [(c.find(k), k, p) for k, p in CLES.items() if k in c]
    trouves = [x for x in trouves if not any(x[1] != y[1] and x[1] in y[1] and y[0] <= x[0] < y[0] + len(y[1]) for y in trouves)]
    if not trouves:
        return None
    # « Ituri 13 · N-Kivu 2 » (bandeau) : le nom vient d'abord, le nombre
    # après. « 16 en Ituri, 3 au Nord-Kivu » : le nombre d'abord.
    premier_chiffre = re.search(r"\d", c)
    ordre = ("apres", "avant") if premier_chiffre and premier_chiffre.start() > min(x[0] for x in trouves) else ("avant", "apres")
    for sens in ordre:
        res, sans = {}, []
        for _, k, p in sorted(trouves):
            if sens == "avant":
                m = re.search(r"(\d+)(?:en|au|aux|ala|a|la|le|dansla|dansle)?" + k, c)
            else:
                m = re.search(k + r"(\d+)", c)
            if m:
                res[p] = res.get(p, 0) + int(m.group(1))
            else:
                sans.append(p)
        s = sum(res.values())
        if not sans and s == total:
            return res
        if len(sans) == 1 and total is not None and total > s and res:
            res[sans[0]] = total - s
            return res
    return None


# ------------------------------------------------------------ le tableau
LIGNE_GUERIS_RE = re.compile(r"\n\s*Gu[ée]ris\s+((?:\d+|ND)(?:\s+(?:\d+|ND))*)\s*\n")
ENTETE_RE = re.compile(r"\n\s*Indicateurs?\s+([^\n]+)\n")


def lire_tableau(texte):
    """Ligne « Guéris » lue sous l'en-tête « Indicateur » le plus proche,
    pas plus de quinze lignes au-dessus (le 060 a un autre « Indicateur »
    plus haut, celui du pilier PoE)."""
    for m in LIGNE_GUERIS_RE.finditer(texte):
        entetes = [e for e in ENTETE_RE.finditer(texte, 0, m.start() + 1) if texte.count("\n", e.end(), m.start()) <= 15]
        if not entetes:
            continue
        tete = re.findall(PROVINCES_RE + r"|Ensemble|Total|Global", entetes[-1].group(1), re.I)
        cellules = m.group(1).split()
        if len(tete) != len(cellules) or len(tete) < 2 or not re.match(r"Ensemble|Total|Global", tete[-1], re.I):
            continue
        res = {}
        for nom, v in zip(tete[:-1], cellules[:-1]):
            if v.isdigit():
                res[canon(nom)] = int(v)
        ensemble = int(cellules[-1]) if cellules[-1].isdigit() else None
        return res, ensemble
    return None


# --------------------------------------------------- les faits saillants
PCT = r"(?:\(\s*[\d,.\s]+%\s*\)\s*)?"
ETE = souple("été")
PATIENTS = souple("patient") + "s?"
FORME_A = re.compile(NOMBRE + r"\s*(?:\(\d+\)\s*)?" + PATIENTS + r"\s*\(([^()]{3,260}?)\)?\s*" + PCT + r"ont\s+" + ETE + r"\s*" + PCT + DECLARES, re.I)
FORME_B = re.compile(r"\(?" + NOMBRE + r"\)?\s*" + PATIENTS + r"\s+(?:ont\s+" + ETE + r"\s+)?" + DECLARES + r"[^()]{0,180}?\(([^()]{3,260}?)\)", re.I)
FORME_BANDEAU = re.compile(r"\+\s*(\d[\d\s]{0,4})\s*gu[ée]ris\s*\(([^()]{3,120})\)", re.I)
FORME_RESPECTIVEMENT = re.compile(NOMBRE + r"\s*patients?\s+ont\s+" + ETE + r"\s+" + DECLARES + r"[^.]{0,120}?respectivement\s+([^.]{3,160})", re.I)
FORME_TOUS = re.compile(NOMBRE + r"\s*patients?,?\s+tou(?:s|tes)\s+(?:en|au|à\s+la|dans\s+la\s+province\s+d[eu]\s*l?['’]?)\s*(" + PROVINCES_RE + r")[^.]{0,30}?ont\s+" + ETE + r"\s+" + DECLARES, re.I)
# Époque des premiers bulletins : la phrase entière, de la puce au point.
PUCES = "•\uf0b7\uf0d8\uf0a7"
PHRASE_ANCIENNE = re.compile(r"(?:^|[" + PUCES + r"]|[\-.]\s)\s*([^" + PUCES + r".]{0,40}?(?:\(\d+\)\s*)?" + PATIENTS + r"\s[^" + PUCES + r"]{0,420}?" + DECLARES + r"[^" + PUCES + r".]{0,120})", re.I)
# « En Ituri, 11 patients ont été déclarés guéris » (091) : une province
# seule, sans total national ; retenue si elle retombe sur la hausse du cumul.
FORME_PROVINCE = re.compile(r"(?:En|Au|À\s+la)\s+(" + PROVINCES_RE + r"),\s*" + NOMBRE + r"\s*" + PATIENTS + r"\s+ont\s+" + ETE + r"\s+" + DECLARES, re.I)


def faits_saillants(texte):
    t = nettoyer(texte)
    for nom, R in (("A", FORME_A), ("B", FORME_B), ("respectivement", FORME_RESPECTIVEMENT), ("bandeau", FORME_BANDEAU)):
        for m in R.finditer(t):
            total = lire_nombre(m.group(1))
            if not total:
                continue
            avant = t[max(0, m.start() - 160):m.start()]
            if TRAITEMENT_RE.search(avant + m.group(0)):
                continue
            res = ventiler(m.group(2), total)
            if res:
                return res, total, nom
    for m in FORME_TOUS.finditer(t):
        total = lire_nombre(m.group(1))
        if total:
            return {canon(m.group(2)): total}, total, "tous"
    for m in PHRASE_ANCIENNE.finditer(t):
        r = lire_ancienne(m.group(1))
        if r:
            return r[0], r[1], "phrase ancienne"
    m = FORME_PROVINCE.search(t)
    if m and lire_nombre(m.group(2)):
        return {canon(m.group(1)): lire_nombre(m.group(2))}, None, "province seule"
    return None


def lire_ancienne(phrase):
    """« Huit (8) patients … dont 6 en Ituri et 2 au Sud-Kivu », « Seize (16)
    patients … dont 15 dans la province de l'Ituri (6 au CTE Mongbwalu, …) et
    1 au CTE Katwa dans la province du Nord-Kivu », « Trois (3) patients …
    dont deux (2) dans la zone de santé de Bunia (province de l'Ituri) et un
    (1) dans la zone de santé de Katwa », « Cinq (5) patients (Rwampara : 3,
    Mongbwalu : 1 et Mambasa : 1) », « Un patient … dans la ZS d'Aru ».

    La phrase devient une suite de nombres et de lieux ; chaque nombre va au
    lieu qui le suit (ou qui le précède, devant « : »). Deux comptes : les
    nombres posés sur une province, puis ceux posés sur une zone ou un CTE,
    rattachés à leur province. Le premier qui retombe sur le total gagne."""
    phrase = re.sub(r"^[^A-Za-zÀ-ÿ(\d]+", "", phrase)
    if re.search(r"d[ée]c[èe]s", phrase.split("atient")[0], re.I):
        return None
    m = re.match(r"(?:Au total,\s*)?(?:([A-Za-zÀ-ÿ\-]+)\s*)?(?:\((\d+)\)\s*)?(\d+\s*)?" + PATIENTS, phrase, re.I)
    if not m:
        return None
    total = int(m.group(2)) if m.group(2) else (int(m.group(3)) if m.group(3) else (en_lettres(m.group(1)) if m.group(1) else None))
    if not total:
        return None
    corps = phrase[m.end():]
    # Fin utile : « après avoir obtenu … négatifs » n'apporte rien, sauf la
    # ventilation qui le suit parfois (« … négatifs dont 6 en Ituri et 2 au
    # Sud-Kivu ») ; « dont un enfant de 3 mois » ne compte pas.
    corps = re.sub(r",?\s*dont\s+(?:un|une)\s+(?:enfant|patient|nouveau)[^,.;]*", " ", corps, flags=re.I)
    evts = []
    for x in re.finditer(r"\b([A-Za-zÀ-ÿ]+)\s*\((\d+)\)|\((\d+)\)|(?<!\d[,.])(?<!\d)(\d+)(?![\d%]|[,.]\d)", corps):
        if x.group(2):
            evts.append((x.start(), "n", int(x.group(2))))
        elif x.group(3) or x.group(4):
            evts.append((x.start(), "n", int(x.group(3) or x.group(4))))
    for x in re.finditer(PROVINCES_RE, corps):
        evts.append((x.start(), "p", canon(x.group(0))))
    mots = list(re.finditer(r"[A-Za-zÀ-ÿ]+", corps))
    for i, x in enumerate(mots):
        deux = corps[x.start():mots[i + 1].end()] if i + 1 < len(mots) and mots[i + 1].start() - x.end() <= 1 else None
        for cand in (deux, x.group(0)):
            if cand and compact(cand) in LIEUX and not re.match(PROVINCES_RE, cand):
                if not evts or evts[-1][0] != x.start() - 0:
                    evts.append((x.start(), "z", LIEUX[compact(cand)]))
                break
    evts.sort()
    # Des lieux, d'abord : « province de l'Ituri » cité seul suffit.
    provs = [e[2] for e in evts if e[1] == "p"]
    if len(set(provs)) == 1 and not any(e[1] == "z" and e[2] != provs[0] for e in evts):
        return {provs[0]: total}, total
    if not provs:
        zs = {e[2] for e in evts if e[1] == "z"}
        if len(zs) == 1:
            return {zs.pop(): total}, total
    for genre in ("p", "z"):
        res = {}
        for i, e in enumerate(evts):
            if e[1] != "n":
                continue
            suite = [f for f in evts[i + 1:] if f[0] - e[0] < 70]
            lieu = next((f for f in suite if f[1] in "pz"), None)
            if lieu and any(f[1] == "n" for f in suite if f[0] < lieu[0]):
                lieu = None
            avant = [f for f in evts[:i] if e[0] - f[0] < 25 and f[1] in "pz"]
            if not lieu and avant and re.search(r":\s*$", corps[avant[-1][0]:e[0]].split()[-1] if corps[avant[-1][0]:e[0]].split() else ""):
                lieu = avant[-1]
            if lieu is None and avant and corps[avant[-1][0]:e[0]].rstrip().endswith(":"):
                lieu = avant[-1]
            if lieu and lieu[1] == genre:
                res[lieu[2]] = res.get(lieu[2], 0) + e[2]
        s = sum(res.values())
        if res and s == total:
            return res, total
        nommees = set(provs)
        sans = [p for p in nommees if p not in res]
        if genre == "p" and res and len(sans) == 1 and total > s:
            res[sans[0]] = total - s
            return res, total
    return None


# ------------------------------------------------------ prise en charge
FLECHE_RE = re.compile(r"(?:→|\so\s)\s*(" + PROVINCES_RE + r")\s*:\s*([^→•]{0,300}?)(\d[\d\s]{0,4})\s*(?:nouveaux\s+)?gu[ée]ri(?:s|sons?)\b", re.I)
PUCE_PROVINCE_RE = re.compile(r"(?:•|\uf0b7|\uf0d8|\uf0a7|→)\s*(?:En|Au|Aux|À\s+la|A\s+la)?\s*(" + PROVINCES_RE + r")\s*,([^•\uf0b7\uf0d8\uf0a7→]{0,700})", re.I)
GUERIS_PUCE_RE = re.compile(r"(?:dont|incluant|y\s+compris|,|\(|:)\s*(\d[\d\s]{0,3}|une?|deux|trois|quatre|cinq|six|sept|huit|neuf|dix)\s+(?:patients?\s+)?gu[ée]ri(?:e?s|sons?)\b", re.I)
SECTION_PEC_RE = re.compile(r"(?:Prise\s+en\s+charge(?:\s+holistique)?|Continuit[ée]\s+des\s+soins|PECH)", re.I)
TOTAL_JOUR_RE = re.compile(r"(?:Au\s+total,[^.]{0,120}?dont\s+|et\s+)(\d[\d\s]{0,3})\s+gu[ée]risons?,?\s+ont\s+[ée]t[ée]\s+enregistr", re.I)


def prise_en_charge(texte):
    """Guéris par province de la rubrique Prise en charge : « → Ituri : 13
    nouveaux guéris » (060-083), « • En Ituri, … contre 57 sorties, dont 7
    guérisons » (084-). Le total du jour, quand la rubrique l'imprime (« Au
    total, 146 nouvelles admissions et 132 sorties, dont 18 guérisons, ont été
    enregistrées »), est rendu à part."""
    t = re.sub(r"\s+", " ", texte)
    res = {}
    for m in FLECHE_RE.finditer(t):
        p = canon(m.group(1))
        if p not in res and not TRAITEMENT_RE.search(m.group(2)) and "cumul" not in m.group(2).lower():
            res[p] = int(re.sub(r"\s", "", m.group(3)))
    if not res:
        for sec in SECTION_PEC_RE.finditer(t):
            bloc = t[sec.end():sec.end() + 6000]
            fin = re.search(r"D[ée]fis\b|\d\.\d+\.\s+[A-Z][a-z]+(?!\s+actions)", bloc[40:])
            bloc = bloc[:fin.start() + 40] if fin else bloc
            for b in PUCE_PROVINCE_RE.finditer(bloc):
                p = canon(b.group(1))
                if p in res:
                    continue
                # Le bilan national clôt parfois la dernière puce (136 : « Au
                # total, 146 nouvelles admissions et 132 sorties, dont 18
                # guérisons ») : il ne compte pas pour la province.
                texte_puce = re.split(r"Au\s+total,\s*\d[\d\s]*\s+nouvelles\s+admissions", b.group(2))[0]
                g = GUERIS_PUCE_RE.search(texte_puce)
                if g and not TRAITEMENT_RE.search(texte_puce[:g.start()]) and "cumul" not in texte_puce[max(0, g.start() - 30):g.start()].lower():
                    res[p] = lire_nombre(g.group(1))
            if res:
                break
    tot = TOTAL_JOUR_RE.search(t)
    return (res or None), (int(re.sub(r"\s", "", tot.group(1))) if tot else None)


# --------------------------------------------------------------- cumuls
CUMUL_RE = re.compile(r"cumul(?:atif)?\s+des\s+(?:patients\s+)?gu[ée]ris(?:\s+de\s+la\s+province)?,?\s*"
                      r"(?:passe\s+de\s+\d[\d\s]*\s+à|est\s+de|atteint|s['’]\s?[ée]l[èe]ve\s+à|s['’]\s?[ée]tablit\s+à|à)\s*"
                      r"(\d[\d\s]{0,6}?\d|\d)(?=\D)([^.]{0,160})", re.I)
PUCE_RE = re.compile(r"(?:•|→|\so\s|)\s*(?:En\s+|Au\s+|À\s+la\s+|A\s+la\s+)?(" + PROVINCES_RE + r")\s*[,:]")


def cumuls(texte):
    t = re.sub(r"\s+", " ", texte)
    res = {}
    for m in CUMUL_RE.finditer(t):
        total = int(re.sub(r"\s", "", m.group(1)))
        dont = re.match(r"\s*dont\s+([^.]+)", m.group(2))
        if dont:
            v = ventiler(dont.group(1), total)
            if v:
                for p, n in v.items():
                    res.setdefault(p, n)
            continue
        # Pas de liste : le cumul est celui de la province de la puce.
        debut = max(t.rfind(x, 0, m.start()) for x in ("•", "→", " o ", "\uf0d8", "\uf0a7", "\uf0b7"))
        if debut < 0 or m.start() - debut > 1200:
            continue
        p = PUCE_RE.match(t[debut:debut + 40])
        if p:
            res.setdefault(canon(p.group(1)), total)
    return res or None


# ------------------------------------------------------------ assemblage
def deltas_nationaux():
    with open(SITREPS_PATH, encoding="utf-8") as fh:
        s = sorted((x for x in json.load(fh) if x.get("date") and x.get("recovered") is not None), key=lambda x: x["date"])
    return {b["date"]: b["recovered"] - a["recovered"] for a, b in zip(s, s[1:])}


def lire(chemin):
    texte = texte_du_rapport(chemin)
    meta = extract_meta(texte, fallback_number=numero(chemin))
    lectures = []
    t = lire_tableau(texte)
    if t:
        lectures.append({"source": "tableau", "provinces": t[0], "total": t[1]})
    f = faits_saillants(texte)
    if f:
        lectures.append({"source": "faits saillants", "forme": f[2], "provinces": f[0], "total": f[1]})
    pc, total_jour = prise_en_charge(texte)
    if pc:
        lectures.append({"source": "prise en charge", "provinces": pc, "total": total_jour})
    elif total_jour is not None:
        lectures.append({"source": "total du jour", "provinces": {}, "total": total_jour})
    return meta, lectures, cumuls(texte)


def choisir(lectures, delta):
    """La première lecture dont la somme retombe sur son propre total. Un
    tableau dont la case « Ensemble » est fausse (079 : « Guéris 38 4 0 0
    15 ») est gardé si la somme de ses provinces retombe sur un total lu
    ailleurs dans le bulletin. La prise en charge sans total imprimé doit
    retomber sur celui d'une autre lecture ou sur la hausse du cumul national."""
    totaux = [l["total"] for l in lectures if l["total"] is not None]
    for l in lectures:
        s = sum(l["provinces"].values())
        if not l["provinces"]:
            continue
        if l["total"] is not None and s == l["total"]:
            return l
        autres = [t for x in lectures if x is not l for t in [x["total"]] if t is not None]
        if l["source"] == "tableau" and s and s in autres + ([delta] if delta is not None else []):
            return dict(l, total=s, note="case Ensemble du tableau a %s, somme des provinces retenue" % l["total"])
    for l in lectures:
        s = sum(l["provinces"].values())
        if l["total"] is None and s and (s in totaux or s == delta):
            return dict(l, total=s)
    return None


def differe(a, b):
    """Deux ventilations se contredisent si une province a deux valeurs non
    nulles différentes, ou une valeur non nulle d'un côté seulement alors que
    l'autre lecture est complète (somme juste)."""
    a = {p: v for p, v in a.items() if v}
    b = {p: v for p, v in b.items() if v}
    return any(p in b and a[p] != b[p] for p in a)


def main():
    deltas = deltas_nationaux()
    jours, cumul_lignes, sans = [], [], []
    for chemin in rapports():
        n = numero(chemin)
        try:
            meta, lectures, cum = lire(chemin)
        except Exception as e:
            print("  ! %s : %s" % (os.path.basename(chemin), e))
            continue
        date = meta.get("reportingDate")
        delta = deltas.get(date)
        retenue = choisir(lectures, delta)
        if cum:
            cumul_lignes.append({"sitrep": meta.get("sitrepNumber") or n, "date": date, "provinces": cum})
        if not retenue:
            if lectures:
                sans.append((n, lectures))
            continue
        jour = {"sitrep": meta.get("sitrepNumber") or n, "date": date,
                "provinces": {p: v for p, v in sorted(retenue["provinces"].items(), key=lambda x: PROVINCES.index(x[0]) if x[0] in PROVINCES else 99)},
                "total": retenue["total"], "source": retenue["source"]}
        if retenue.get("forme"):
            jour["forme"] = retenue["forme"]
        if retenue.get("note"):
            jour["note"] = retenue["note"]
        if delta is not None and delta != retenue["total"]:
            jour["hausseCumulNational"] = delta
        desaccord = {l["source"]: l["provinces"] for l in lectures
                     if l["source"] != retenue["source"] and l["provinces"] and differe(retenue["provinces"], l["provinces"])}
        if desaccord:
            jour["desaccord"] = desaccord
        jours.append(jour)
    par_date = {}
    for j in jours:
        par_date[j["date"]] = j
    jours = sorted(par_date.values(), key=lambda j: j["date"])
    sortie = {
        "description": "Guéris déclarés chaque jour par les structures de prise en charge (CTE, centres de transit, hôpitaux), par province, lus dans les SitRep de l'INSP "
                       "(tableau « Mouvement des patients », faits saillants, rubrique Prise en charge). "
                       "Les cumuls par province sont ceux que les bulletins publient, sans reconstitution.",
        "periode": {"debut": jours[0]["date"], "fin": jours[-1]["date"]} if jours else None,
        "parBulletin": jours,
        "cumulsPublies": sorted(cumul_lignes, key=lambda c: c["date"] or ""),
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(sortie, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    sources = {}
    for j in jours:
        sources[j["source"]] = sources.get(j["source"], 0) + 1
    print("%s écrit : %d bulletin(s), du %s au %s — %s ; %d relevé(s) de cumul" % (
        os.path.relpath(OUTPUT_PATH, ROOT), len(jours), sortie["periode"]["debut"], sortie["periode"]["fin"],
        ", ".join("%d par %s" % (v, k) for k, v in sorted(sources.items())), len(cumul_lignes)))
    if sans:
        print("Lectures sans somme juste (%d) :" % len(sans))
        for n, ls in sans:
            print("  - %s : %s" % (n, " | ".join("%s %s=%s" % (l["source"], l["provinces"], l["total"]) for l in ls)))


if __name__ == "__main__":
    main()
