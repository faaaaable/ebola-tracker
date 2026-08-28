#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patients hospitalisés, lits et taux d'occupation des CTE, par province.

Lit chaque bulletin et écrit data/cte.json. C'est le chiffre qui explique
l'onglet « Décès en communauté » : quand le centre de traitement est plein, on
meurt chez soi.

Deux sources selon l'époque :

  C  (059-083) un tableau « OCCUPATION DES STRUCTURES DE SOINS » avec une
     colonne par province : « Nombre de lits 709 141 ND 10 860 » et
     « Patients au lit (J-1) 551 170 ND 3 724 ».
  D  (084-…)  une puce par province en prose :
     « l'occupation atteint 501 patients pour 840 lits (60 %) »
     « 470 patients sont hospitalisés (172 confirmés et 298 suspects) pour
       996 lits, soit un taux d'occupation de 47,2 % »
     « 167 malades sont hospitalisés pour 206 lits, soit 81,1 % d'occupation »
     « une nouvelle admission … portent à 4 le nombre de patients isolés
       (1 confirmé et 3 suspects) pour 14 lits, soit 28,6 % d'occupation »

L'époque B ne publie que « Patients au lit » sans le nombre de lits : la
série des hospitalisés remonte plus loin que celle de l'occupation, et le
graphique ne trace l'occupation que là où les lits sont connus. Une province
dont on ne lit pas les patients est écartée ce jour-là. L'occupation par CTE
(« Isiro 120 % ») reste de la prose : non sommable, elle n'entre pas ici.

Le taux d'occupation publié fait foi ; s'il manque, il est recalculé et
marqué comme tel (`occupationCalculee`). Un taux au-dessus de 100 % est
possible et publié tel quel par la source.

    python scripts/extraire_cte.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textes_pdf import ROOT, rapports, numero, texte_du_rapport, entier, pourcent  # noqa: E402
from update_data import extract_meta, PROVINCE_CANON  # noqa: E402

OUTPUT_PATH = os.path.join(ROOT, "data", "cte.json")

PROVINCES_RE = r"Ituri|Nord[\s-]+Kivu|Haut[\s-]+U[ée]l[ée]|Tshopo|Sud[\s-]+Kivu|Bas[\s-]+U[ée]l[ée]"


def canon(nom):
    """« Haut Uélé », « Haut-Uele », « Haut\nUélé » -> « Haut-Uélé », etc."""
    n = re.sub(r"[\s-]+", " ", nom).replace("Uele", "Uélé").replace("Uelé", "Uélé").replace("Uélè", "Uélé")
    n = {"Nord Kivu": "Nord-Kivu", "Sud Kivu": "Sud-Kivu", "Haut Uélé": "Haut-Uélé"}.get(n, n)
    return PROVINCE_CANON.get(n, n)


# ---------------------------------------------------------------- prose (D)
# La prose n'est lue que sous le titre de l'époque D, « Continuité des
# soins ». Sous « Prise en charge » (B, C) la même section aligne des cumuls
# et des indicateurs qui ressemblent à des hospitalisés du jour — le 060
# donnait 753 hospitalisés au Nord-Kivu, son cumul de cas — et ces époques
# ont un tableau, lu en premier.
DEBUT_RE = re.compile(r"(?:^|\n)[^\n]{0,12}Continuit[ée] des soins[^\n]{0,60}\n", re.IGNORECASE)
FIN_RE = re.compile(r"\n[^\n]{0,12}(?:Communication|CREC|Logistique|S[ée]curit[ée]|Recherche)", re.IGNORECASE)
REPERE_RE = re.compile(r"(?:^|[\n•→▪\-\uf000-\uf0ff]|\bEn |\bAu |\bÀ la |\bA la |\bau |\ben |\bà la |\bL[’'])\s*(%s)\b" % PROVINCES_RE)

HOSPITALISES_RES = [
    re.compile(r"occupation\s+atteint\s+(\d[\d ]{0,4}\d|\d)\s+patients", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades|cas suspects|cas)\s+(?:sont|restent|demeurent)?\s*(?:en\s+)?hospitalis", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+sont\s+(?:en\s+)?isol", re.I),
    re.compile(r"port(?:e|ent|ant)\s+à\s+(\d[\d ]{0,4}\d|\d)\s+le\s+nombre\s+de\s+patients", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+(?:en\s+)?(?:hospitalisation|isolement)", re.I),
]
LITS_RE = re.compile(r"pour\s+(\d[\d ]{0,4}\d|\d)\s+lits", re.I)
OCCUPATION_RES = [
    re.compile(r"taux\s+d[’']occupation[^%\d]{0,30}?(\d+(?:[,.]\d+)?)\s*%", re.I),
    re.compile(r"(\d+(?:[,.]\d+)?)\s*%\s+d[’']occupation", re.I),
    re.compile(r"lits\s*\((\d+(?:[,.]\d+)?)\s*%\)", re.I),
]


def premier(regexes, texte):
    for rx in regexes:
        m = rx.search(texte)
        if m:
            return entier(m.group(1))
    return None


def lire_prose(morceau):
    hosp = premier(HOSPITALISES_RES, morceau)
    if hosp is None:
        return None
    ligne = {"hospitalises": hosp}
    m = LITS_RE.search(morceau)
    if m:
        ligne["lits"] = entier(m.group(1))
    occ = None
    for rx in OCCUPATION_RES:
        mo = rx.search(morceau)
        if mo:
            occ = pourcent(mo.group(1))
            break
    if occ is not None:
        ligne["occupation"] = occ
    elif ligne.get("lits"):
        ligne["occupation"] = round(hosp / ligne["lits"] * 100, 1)
        ligne["occupationCalculee"] = True
    # Admissions, sorties et guéris sont dans la même phrase, mais sous des
    # tournures trop variables pour être publiés sans relecture : on ne garde
    # que ce que la page affiche, hospitalisés, lits et occupation.
    return ligne


def section_prose(texte):
    m = DEBUT_RE.search(texte)
    if not m:
        return None
    reste = texte[m.end():]
    f = FIN_RE.search(reste)
    return (reste[:f.start()] if f else reste[:3000])[:4000]


def lire_par_prose(texte):
    section = section_prose(texte)
    if not section:
        return {}
    reperes = list(REPERE_RE.finditer(section))
    provinces = {}
    for i, m in enumerate(reperes):
        nom = canon(m.group(1))
        fin = reperes[i + 1].start() if i + 1 < len(reperes) else len(section)
        ligne = lire_prose(section[m.end():fin])
        if ligne and nom not in provinces:
            provinces[nom] = ligne
    return provinces


# -------------------------------------------------------------- tableau (C)
ENTETE_RE = re.compile(r"\n\s*Indicateurs?\s+((?:(?:%s|Ensemble|Total|Global)\s*)+)\n" % PROVINCES_RE)
LITS_LIGNE_RE = re.compile(r"\n\s*Nombre\s+de\s+lits\s+([^\n]+)")
# « 60 Patients au lit (J-1) 551 170 … » : le « 860 » de la ligne des lits
# s'est cassé sur deux lignes, et son morceau ouvre celle des patients.
PATIENTS_LIGNE_RE = re.compile(r"\n(?:\d+\s+)?Patients?\s+au\s+lit\s*\(J-1\)\s+([^\n]+)")


def decoupages(ligne, n):
    """Tous les découpages d'une ligne de tableau en n cellules.

    Un espace entre deux nombres est tantôt une frontière de colonnes, tantôt
    un séparateur de milliers (« 1 483 ») : « 532 924 ND 27 ND 1 483 » a deux
    lectures à six cellules, et seule la somme des colonnes dit laquelle est
    la bonne. On renvoie toutes les lectures possibles, l'appelant choisit —
    celle qui se vérifie, ou à défaut la première, où le préfixe de milliers
    est le plus court et le plus à gauche (« 1 014 » plutôt que « 7 146 »)."""
    jetons = ligne.strip().split()
    if len(jetons) < n:
        return []
    if len(jetons) == n:
        return [[None if j.upper() in ("ND", "NA", "-", "—") else entier(j) for j in jetons]]
    fusions = [i for i in range(len(jetons) - 1)
               if jetons[i].isdigit() and len(jetons[i]) <= 2
               and jetons[i + 1].isdigit() and len(jetons[i + 1]) == 3]
    fusions.sort(key=lambda i: (len(jetons[i]), i))
    out = []
    for i in fusions:
        j2 = jetons[:i] + [jetons[i] + jetons[i + 1]] + jetons[i + 2:]
        for d in decoupages(" ".join(j2), n):
            if d not in out:
                out.append(d)
    return out


def cellules(ligne, n, valide=None):
    """Le découpage retenu : le premier que `valide` accepte, sinon le premier."""
    cands = decoupages(ligne, n)
    if not cands:
        return None
    if valide:
        for c in cands:
            if valide(c):
                return c
    return cands[0]


def lire_par_tableau(texte):
    """Le tableau d'occupation de l'époque C : une colonne par province."""
    # Le tableau des soins est le seul dont l'en-tete precede une ligne
    # « Nombre de lits » : on cherche l'en-tete le plus proche avant elle.
    ml = LITS_LIGNE_RE.search(texte)
    mp = PATIENTS_LIGNE_RE.search(texte)
    if not mp:
        return {}
    avant = texte[:mp.start()]
    entetes = list(ENTETE_RE.finditer(avant))
    if not entetes:
        return {}
    colonnes = entetes[-1].group(1).split()
    # « Nord-Kivu » tient en un jeton, « Haut Uélé » en deux : on recolle.
    noms = []
    i = 0
    while i < len(colonnes):
        j = colonnes[i]
        if j in ("Haut", "Bas", "Nord", "Sud") and i + 1 < len(colonnes):
            j = j + " " + colonnes[i + 1]
            i += 1
        noms.append(j)
        i += 1
    n = len(noms)
    i_total = next((k for k, nom in enumerate(noms) if nom in ("Ensemble", "Total", "Global")), None)

    def somme_ok(c):
        if i_total is None or c[i_total] is None:
            return True
        return c[i_total] == sum(v or 0 for k, v in enumerate(c) if k != i_total)
    patients = cellules(mp.group(1), n, valide=somme_ok)
    lits = cellules(ml.group(1), n, valide=somme_ok) if ml and ml.start() < mp.start() + 2000 else None
    if patients is None:
        return {}
    provinces = {}
    for k, nom in enumerate(noms):
        if nom in ("Ensemble", "Total", "Global"):
            continue
        if patients[k] is None:
            continue
        ligne = {"hospitalises": patients[k]}
        if lits and lits[k]:
            ligne["lits"] = lits[k]
            ligne["occupation"] = round(patients[k] / lits[k] * 100, 1)
            ligne["occupationCalculee"] = True
        provinces[canon(nom)] = ligne
    return provinces


# ----------------------------------------------------------------- commun
def avertissements(nom, ligne):
    out = []
    h, l, o = ligne.get("hospitalises"), ligne.get("lits"), ligne.get("occupation")
    if h is not None and l and o is not None and not ligne.get("occupationCalculee"):
        calc = round(h / l * 100, 1)
        if abs(calc - o) > 1.5:
            out.append("%s : occupation publiée %s %%, recalculée %s %% (%d/%d)" % (nom, o, calc, h, l))
    return out


def lire_rapport(chemin):
    texte = texte_du_rapport(chemin)
    meta = extract_meta(texte, fallback_number=numero(chemin))
    if not meta.get("reportingDate"):
        return None, []
    # Le tableau d'abord : là où il existe (époques B et C), la prose de la
    # même section porte des cumuls et des indicateurs qui ressemblent à des
    # hospitalisés du jour — « 4 035 cas… », « 6 275… » — et trompe les motifs.
    provinces = lire_par_tableau(texte)
    methode = "tableau"
    if not provinces:
        provinces = lire_par_prose(texte)
        methode = "prose"
    if not provinces:
        return None, []
    alertes = []
    for nom, ligne in provinces.items():
        alertes.extend(avertissements(nom, ligne))
    avec_lits = [p for p in provinces.values() if p.get("lits")]
    total = {
        "hospitalises": sum(p["hospitalises"] for p in provinces.values()),
        "provinces": len(provinces),
    }
    if avec_lits:
        total["lits"] = sum(p["lits"] for p in avec_lits)
        total["hospitalisesAvecLits"] = sum(p["hospitalises"] for p in avec_lits)
        total["occupation"] = round(total["hospitalisesAvecLits"] / total["lits"] * 100, 1)
    return {
        "date": meta["reportingDate"],
        "sitrepNumber": meta["sitrepNumber"],
        "methode": methode,
        "provinces": provinces,
        "total": total,
        "source": "SitRep INSP (automatique)",
    }, alertes


def main():
    points, alertes, sans = [], [], []
    for chemin in rapports():
        try:
            point, av = lire_rapport(chemin)
        except Exception as e:
            print("  ! %s : %s" % (os.path.basename(chemin), e))
            continue
        if point is None:
            sans.append(numero(chemin))
            continue
        alertes.extend("%s : %s" % (point["sitrepNumber"], a) for a in av)
        points.append(point)
    par_date = {}
    for p in points:
        par_date[p["date"]] = p
    final = sorted(par_date.values(), key=lambda p: p["date"])
    sortie = {
        "periode": {"debut": final[0]["date"], "fin": final[-1]["date"]} if final else None,
        "parDate": final,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(sortie, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    methodes = {}
    for p in final:
        methodes[p["methode"]] = methodes.get(p["methode"], 0) + 1
    print("%s écrit : %d date(s), du %s au %s — %s" % (
        os.path.relpath(OUTPUT_PATH, ROOT), len(final),
        final[0]["date"] if final else "-", final[-1]["date"] if final else "-",
        ", ".join("%d par %s" % (n, m) for m, n in sorted(methodes.items()))))
    print("Rapports sans donnée CTE lisible (%d) : %s" % (len(sans), ", ".join(sans)))
    if alertes:
        print("\n%d avertissement(s) :" % len(alertes))
        for a in alertes:
            print("  - " + a)


if __name__ == "__main__":
    main()
