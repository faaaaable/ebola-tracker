#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'entonnoir des alertes : reçues, vérifiées, validées, par province et par
jour. Écrit data/alertes.json.

Une alerte est un signalement — un malade, un décès, une rumeur — que la
surveillance doit vérifier. Une part est validée comme cas suspect, prélevée,
et parfois confirmée. Le nombre d'alertes dit si l'on cherche ; la part
validée dit ce qu'on trouve.

Trois mises en page, deux entonnoirs :

  B  (026-058) « Tableau 2. Gestion des alertes épidémiologiques (24h) »,
     une colonne par province : « Alertes remontées 152 332 23 507 »,
     « Alertes investiguées 106 332 22 460 », « Alertes validées Vivantes
     54 25 8 87 » / « Décédées 30 19 0 49 ».
  C  (059-083) « TABLEAU 3 — GESTION DES ALERTES EPIDEMIOLOGIQUES », même
     forme, plus de provinces : « Nouvelles alertes reçues 532 924 ND 27 ND
     1 483 », « Alertes validées — vivantes … », « — décédées (comm.) … ».
  D  (087-…)   « Situation des alertes notifiées par province », une ligne
     par province et neuf nombres : reçues (vivants, décédés, total),
     validées (vivants, décédés), invalidées (vivants, décédés), suspects
     investigués, transférés au CTE.

En B et C, « investiguée » qualifie l'alerte qu'on est allé voir ; en D, ce
travail s'appelle « vérifiée » (validée ou invalidée) et « investigué » désigne
le cas suspect pris en charge. Le schéma commun garde les trois étapes qui
existent partout — `recues`, `verifiees`, `validees` — et ajoute, pour D
seulement, `suspectsInvestigues` et `transferes`. Les « reports de la veille »
des époques B-C ne sont pas comptés : `recues` sont les alertes NOUVELLES du
jour, comme en D.

Une province sans ligne lisible est écartée ce jour-là ; le total est celui
que la source imprime quand elle l'imprime, la somme des provinces sinon.

    python scripts/extraire_alertes.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textes_pdf import ROOT, rapports, numero, texte_du_rapport, texte_par_couches, entier  # noqa: E402
from update_data import extract_meta, PROVINCE_CANON  # noqa: E402

OUTPUT_PATH = os.path.join(ROOT, "data", "alertes.json")

PROVINCES_RE = r"Ituri|Nord[\s-]+Kivu|Haut[\s-]+U[ée]l[ée]|Tshopo|Sud[\s-]+Kivu|Bas[\s-]+U[ée]l[ée]"


def canon(nom):
    """« Haut Uélé », « Haut-Uele », « Haut\nUélé » -> « Haut-Uélé », etc."""
    n = re.sub(r"[\s-]+", " ", nom).replace("Uele", "Uélé").replace("Uelé", "Uélé").replace("Uélè", "Uélé")
    n = {"Nord Kivu": "Nord-Kivu", "Sud Kivu": "Sud-Kivu", "Haut Uélé": "Haut-Uélé"}.get(n, n)
    return PROVINCE_CANON.get(n, n)


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


# ------------------------------------------------------------------ D
TITRE_D_RE = re.compile(r"Situation des alertes notifi[ée]es par province", re.I)
LIGNE_D_RE = re.compile(r"\n\s*(%s)\s*\*?\s+([^\n]+)" % PROVINCES_RE)
TOTAL_D_RE = re.compile(r"\n\s*Total\s*(?:\n\s*)?G[ée]n[ée]ral\s+([^\n]+)", re.I)


def lire_D(texte):
    m = TITRE_D_RE.search(texte)
    if not m:
        return None
    section = texte[m.end():m.end() + 1800]
    provinces = {}
    for lm in LIGNE_D_RE.finditer(section):
        nom = canon(lm.group(1))
        c = cellules(lm.group(2), 9,
                     valide=lambda c: c[2] is not None and c[2] == (c[0] or 0) + (c[1] or 0))
        if c is None or nom in provinces:
            continue
        recues_v, recues_d, recues, val_v, val_d, inv_v, inv_d, investigues, transferes = c
        validees = (val_v or 0) + (val_d or 0)
        invalidees = (inv_v or 0) + (inv_d or 0)
        provinces[nom] = {
            "recues": recues if recues is not None else (recues_v or 0) + (recues_d or 0),
            "verifiees": validees + invalidees,
            "validees": validees,
            "suspectsInvestigues": investigues,
            "transferes": transferes,
        }
    if not provinces:
        return None
    total = None
    tm = TOTAL_D_RE.search(section)
    if tm:
        c = cellules(tm.group(1), 9,
                     valide=lambda c: c[2] is not None and c[2] == (c[0] or 0) + (c[1] or 0))
        if c:
            total = {"recues": c[2], "verifiees": (c[3] or 0) + (c[4] or 0) + (c[5] or 0) + (c[6] or 0),
                     "validees": (c[3] or 0) + (c[4] or 0), "suspectsInvestigues": c[7],
                     "transferes": c[8]}
    return provinces, total, "tableau par province (D)"


def lire_D_couches(chemin):
    """Repli quand le tableau D est illisible dans le texte ordinaire (105 :
    imprimé par-dessus le tableau des zones). Dans le texte par couches, les
    lignes d'une province suivies de neuf nombres dont reçues = vivants +
    décédés ne peuvent être que celles de ce tableau."""
    texte = texte_par_couches(chemin)
    provinces = {}
    for lm in LIGNE_D_RE.finditer(texte):
        nom = canon(lm.group(1))
        c = cellules(lm.group(2), 9,
                     valide=lambda c: c[2] is not None and c[2] == (c[0] or 0) + (c[1] or 0))
        if c is None or nom in provinces or c[2] is None or c[2] != (c[0] or 0) + (c[1] or 0):
            continue
        recues_v, recues_d, recues, val_v, val_d, inv_v, inv_d, investigues, transferes = c
        validees = (val_v or 0) + (val_d or 0)
        provinces[nom] = {
            "recues": recues, "verifiees": validees + (inv_v or 0) + (inv_d or 0),
            "validees": validees, "suspectsInvestigues": investigues, "transferes": transferes,
        }
    if len(provinces) < 3:
        return None
    return provinces, None, "tableau par province (D, couches de police)"


# --------------------------------------------------------------- B et C
TITRE_BC_RE = re.compile(r"Gestion des alertes [ée]pid[ée]miologiques", re.I)
ENTETE_RE = re.compile(r"Indicateurs?\s+((?:(?:%s|Total|Ensemble|Global)\s*)+)\n" % PROVINCES_RE)
LIGNES_BC = {
    "recues": re.compile(r"\n\s*(?:Nouvelles\s+alertes(?:\s+re[çc]ues)?|Alertes\s+remont[ée]es)\s+([^\n]+)", re.I),
    "verifiees": re.compile(r"\n\s*Alertes\s+investigu[ée]es\s+([^\n]+)", re.I),
    "validees_v": re.compile(r"\n\s*(?:Alertes\s+valid[ée]es\s*(?:[—–-]\s*)?)?[Vv]ivantes\s+([^\n]+)"),
    "validees_d": re.compile(r"\n\s*(?:Alertes\s+valid[ée]es\s*(?:[—–-]\s*)?)?[Dd][ée]c[ée]d[ée]es(?:\s*\(comm\.?\))?\s+([^\n]+)"),
    "suspects": re.compile(r"\n\s*Total\s+des\s+cas\s+suspects(?:\s+du\s+jour)?\s+([^\n]+)", re.I),
}


def lire_BC(texte):
    m = TITRE_BC_RE.search(texte)
    if not m:
        return None
    section = texte[m.start():m.start() + 2500]
    em = ENTETE_RE.search(section)
    if not em:
        return None
    jetons = em.group(1).split()
    noms = []
    i = 0
    while i < len(jetons):
        j = jetons[i]
        if j in ("Haut", "Bas", "Nord", "Sud") and i + 1 < len(jetons):
            j = j + " " + jetons[i + 1]
            i += 1
        noms.append(j)
        i += 1
    n = len(noms)
    # La colonne Total, quand elle existe, départage les découpages : elle
    # doit être la somme des provinces (les ND comptant pour zéro).
    i_total = next((k for k, nom in enumerate(noms) if nom in ("Total", "Ensemble", "Global")), None)

    def somme_ok(c):
        if i_total is None or c[i_total] is None:
            return True
        return c[i_total] == sum(v or 0 for k, v in enumerate(c) if k != i_total)
    lignes = {}
    for cle, rx in LIGNES_BC.items():
        lm = rx.search(section)
        if lm:
            c = cellules(lm.group(1), n, valide=somme_ok)
            if c:
                lignes[cle] = c
    if "recues" not in lignes:
        return None
    provinces = {}
    total = None
    for k, nom in enumerate(noms):
        recues = lignes["recues"][k]
        if recues is None:
            continue
        ligne = {"recues": recues}
        if "verifiees" in lignes and lignes["verifiees"][k] is not None:
            ligne["verifiees"] = lignes["verifiees"][k]
        if "validees_v" in lignes or "validees_d" in lignes:
            v = (lignes.get("validees_v") or [None] * n)[k]
            d = (lignes.get("validees_d") or [None] * n)[k]
            if v is not None or d is not None:
                ligne["validees"] = (v or 0) + (d or 0)
        elif "suspects" in lignes and lignes["suspects"][k] is not None:
            ligne["validees"] = lignes["suspects"][k]
        if nom in ("Total", "Ensemble", "Global"):
            total = ligne
        else:
            provinces[canon(nom)] = ligne
    if not provinces:
        return None
    return provinces, total, "tableau par indicateur (B-C)"


# ---------------------------------------------------------------- commun
def somme(provinces, cle):
    valeurs = [p.get(cle) for p in provinces.values()]
    if not valeurs or any(v is None for v in valeurs):
        return None
    return sum(valeurs)


def lire_rapport(chemin):
    texte = texte_du_rapport(chemin)
    meta = extract_meta(texte, fallback_number=numero(chemin))
    if not meta.get("reportingDate"):
        return None, []
    lu = lire_D(texte) or lire_BC(texte)
    # Le repli par couches suppose l'ordre des neuf colonnes du tableau par
    # province, qui n'existe qu'a partir du 087 : applique aux 084-086, il
    # lisait 948 validees sur 1 141 recues le 6 aout, quand les voisins sont
    # a 20 % — leurs colonnes ne sont pas celles-la.
    if not lu and "alertes" in texte.lower() and int(meta["sitrepNumber"]) >= 87:
        lu = lire_D_couches(chemin)
    if not lu:
        return None, []
    provinces, total, methode = lu
    alertes = []
    # Aux époques B et C, « investiguées » et « validées » portent aussi sur
    # les alertes reportées de la veille : elles peuvent dépasser les reçues
    # du jour (Tshopo, 062 : 39 investiguées pour 4 reçues) et les validées
    # dépasser les investiguées (Ituri, 061 : 318 pour 179). C'est la source,
    # pas une erreur de lecture — on ne l'annote qu'en D, où les colonnes se
    # somment strictement.
    if methode.startswith("tableau par province"):
        for nom, p in provinces.items():
            r, v, va = p.get("recues"), p.get("verifiees"), p.get("validees")
            if v is not None and r is not None and v > r:
                alertes.append("%s : %d vérifiées pour %d reçues" % (nom, v, r))
            if va is not None and v is not None and va > v:
                alertes.append("%s : %d validées pour %d vérifiées" % (nom, va, v))
    calc = {cle: somme(provinces, cle) for cle in ("recues", "verifiees", "validees",
                                                    "suspectsInvestigues", "transferes")}
    calc = {k: v for k, v in calc.items() if v is not None}
    if total is None:
        total = dict(calc)
        total["calcule"] = True
    else:
        # Un total qui ne se somme pas est une ligne mal découpée (le 020 lit
        # « 6409 » là où les provinces font 403), ou une source qui ne se
        # relit pas (le 055 : 605 pour 607). Dans les deux cas la somme des
        # provinces, toutes lues, est la valeur sûre — on la retient et on
        # le note.
        for cle, v in calc.items():
            if total.get(cle) is not None and total[cle] != v:
                alertes.append("total %s publié %s, somme des provinces %s retenue" % (cle, total[cle], v))
                total[cle] = v
                total["calcule"] = True
    if total.get("recues"):
        if total.get("verifiees") is not None:
            total["partVerifiee"] = round(total["verifiees"] / total["recues"] * 100, 1)
        if total.get("validees") is not None:
            total["partValidee"] = round(total["validees"] / total["recues"] * 100, 1)
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
    print("Rapports sans tableau d'alertes lisible (%d) : %s" % (len(sans), ", ".join(sans)))
    if alertes:
        print("\n%d avertissement(s) :" % len(alertes))
        for a in alertes:
            print("  - " + a)


if __name__ == "__main__":
    main()
