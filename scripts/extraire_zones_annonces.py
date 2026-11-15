"""Nouveaux cas (et deces) du jour par zone de sante, tels que les annoncent
les bulletins qui suivent un jour sans tableau des zones ou qui portent un
rattrapage (15 novembre 2026) -> data/zones-jour-annonces.json.

Sans eux, la barre d'une zone ces jours-la est l'ecart de deux cumuls et
couvre plusieurs journees : elle passe en teinte claire, « Rattrapage ».
Avec eux, scripts/zones_jour.py separe la part du jour (pleine) du reste ;
quand une seule journee manque, le reste devient la barre de la veille,
calculee par soustraction (comme les provinces, JOURNEES_ANNONCEES).

Deux sources selon le bulletin :
- la phrase des faits saillants, « repartis dans les ZS de Mongbwalu (25),
  Bunia (13)… » (SitRep 018, 030, 034, 044, 046) ;
- la colonne « Nouv. cas » du tableau des zones, et le total des deces du
  jour quand il y est (015, 064, 069, 077, 087, 088).

Chaque jour est recoupe avec les nouveaux cas que le bulletin annonce par
province (PROVINCES, recopie a la main de l'en-tete ou des faits
saillants) : zones_jour.py n'utilise une province que si la somme de ses
zones, plus les cas non attribues (« sans fiche », deces « a ventiler »),
retombe exactement sur l'annonce.

    python scripts/extraire_zones_annonces.py
"""
from __future__ import annotations

import json
import os
import re
import sys

import pdfplumber

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zones_jour import cle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(ROOT, "data", "zones-jour-annonces.json")

# date -> (SitRep, lecture)
BULLETINS = {
    "2026-05-29": ("015", "tab015"), "2026-06-01": ("018", "texte"),
    "2026-06-13": ("030", "texte"), "2026-06-17": ("034", "texte"),
    "2026-06-27": ("044", "texte"), "2026-06-29": ("046", "texte"),
    "2026-07-17": ("064", "tab"), "2026-07-22": ("069", "tab"),
    "2026-07-30": ("077", "tab"), "2026-08-09": ("087", "tab087"),
    "2026-08-10": ("088", "tab"),
}

# Ce que le bulletin annonce par province pour la journee, et ce qui n'est
# rattache a aucune zone. « c » cas, « d » deces (absent : pas d'annonce).
PROVINCES = {
    # Tableau I : sous-totaux de la colonne « nouveaux cas confirmes » ;
    # 8 cas « sans fiche » en Ituri, hors zones.
    "2026-05-29": {"c": {"Ituri": 52, "Nord-Kivu": 0, "Sud-Kivu": 2}, "horsC": {"Ituri": 8}},
    "2026-06-01": {"c": {"Ituri": 23}},
    "2026-06-13": {"c": {"Ituri": 56, "Nord-Kivu": 16}},
    "2026-06-17": {"c": {"Ituri": 16, "Nord-Kivu": 5}},
    "2026-06-27": {"c": {"Ituri": 45, "Nord-Kivu": 2}},
    "2026-06-29": {"c": {"Ituri": 17, "Nord-Kivu": 9}},
    "2026-07-17": {"c": {"Ituri": 75, "Nord-Kivu": 7, "Haut-Uélé": 4, "Tshopo": 0, "Sud-Kivu": 0},
                   "d": {"Ituri": 25, "Nord-Kivu": 4, "Haut-Uélé": 0, "Tshopo": 0, "Sud-Kivu": 0}},
    "2026-07-22": {"c": {"Ituri": 73, "Nord-Kivu": 18, "Haut-Uélé": 6},
                   "d": {"Ituri": 45, "Nord-Kivu": 14, "Haut-Uélé": 3}},
    "2026-07-30": {"c": {"Ituri": 52, "Nord-Kivu": 15, "Haut-Uélé": 6, "Tshopo": 0, "Sud-Kivu": 0},
                   "d": {"Ituri": 20, "Nord-Kivu": 4, "Haut-Uélé": 0, "Tshopo": 0, "Sud-Kivu": 0}},
    "2026-08-09": {"c": {"Ituri": 57, "Nord-Kivu": 15, "Haut-Uélé": 15, "Tshopo": 0, "Sud-Kivu": 0}},
    # 12 deces intra-CTE de l'Ituri « a ventiler », hors zones ; le
    # Haut-Uele n'a rien transmis (ND).
    "2026-08-10": {"c": {"Ituri": 53, "Nord-Kivu": 15, "Tshopo": 0, "Sud-Kivu": 0},
                   "d": {"Ituri": 33, "Nord-Kivu": 17, "Tshopo": 0, "Sud-Kivu": 0}, "horsD": {"Ituri": 12}},
}


def k(nom):
    return cle(nom).replace(" ", "")


def lire(num):
    with pdfplumber.open(os.path.join(ROOT, "reports", "SITREP_MVE_%s.pdf" % num)) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages)


def lignes_jointes(texte):
    """Les lignes du texte, un nom coupe en deux autour de ses chiffres
    recolle (« Boma » / « 12 4 33,3% … » / « Mangbetu », SitRep 077)."""
    ls = texte.split("\n")
    sortie, i = [], 0
    while i < len(ls):
        a = ls[i].strip()
        if (i + 2 < len(ls) and re.fullmatch(r"[A-Za-zÀ-ÿ\-]+", a)
                and re.match(r"\d", ls[i + 1].strip()) and "%" in ls[i + 1]
                and re.fullmatch(r"[A-Za-zÀ-ÿ\-]+", ls[i + 2].strip())):
            sortie.append("%s %s %s" % (a, ls[i + 2].strip(), ls[i + 1].strip()))
            i += 3
            continue
        sortie.append(a)
        i += 1
    return sortie


def extraire(date, num, mode, zones):
    t = lire(num)
    res = {}
    if mode == "texte":
        i = t.find("FAITS SAILLANTS")
        seg = t[i:i + 1600].replace("\n", " ")
        # La seule phrase des nouveaux cas : pas la liste des cas probables
        # qui suit au 034.
        m = re.search(r"(r[ée]partis|proviennent)[^•]*", seg)
        seg = m.group(0) if m else ""
        seg = re.sub(r"\bZS\s+(de\s+)?", "", seg)
        for m in re.finditer(r"([A-ZÀ-Ý][\w’'\-]+(?:[ \-][A-ZÀ-Ý][\w\-]+)?)\s*\((\d+)\)", seg):
            nm = k(m.group(1))
            if nm in zones:
                res[nm] = {"c": int(m.group(2))}
        return res
    lignes = lignes_jointes(t)
    if mode == "tab015":
        debut = next(i for i, l in enumerate(lignes) if l.startswith("Tableau I."))
        lignes = lignes[debut:debut + 60]
    for l in lignes:
        toks = l.split()
        # Le nom s'arrete au premier mot sans lettre : « Butembo - - » se
        # reduirait sinon a « BUTEMBO » (cle() efface les tirets).
        n_mots = next((i for i, x in enumerate(toks) if not re.search(r"[A-Za-zÀ-ÿ]", x)), len(toks))
        for L in [x for x in (3, 2, 1) if x <= n_mots]:
            nm = k(" ".join(toks[:L]))
            if nm in zones and nm not in res:
                break
        else:
            continue
        rest = toks[L:]
        # Une ligne de tableau : le nom, puis tout de suite des nombres. Une
        # phrase qui commence par un nom de zone (« Rwampara (481), Nizi… »)
        # n'en est pas une.
        if not rest or not re.fullmatch(r"\d[\d,.]*%?|-|—|ND|NA", rest[0]):
            continue
        if mode == "tab015":
            if len(rest) >= 4:
                res[nm] = {"c": int(rest[2]) if rest[2].isdigit() else 0}
            continue
        pi = next((i for i, x in enumerate(rest) if "%" in x), None)
        if pi is None:
            continue
        if mode == "tab087":
            if rest[0].isdigit():
                res[nm] = {"c": int(rest[0])}
            continue
        apres = [x for x in rest[pi + 1:] if re.fullmatch(r"\d+", x)]
        r = {"c": int(apres[0]) if apres else 0}
        # Le dernier nombre est le total des deces du jour (« 22 7 7 » au
        # 088 : nouveaux cas, communautaires, total ; quatre colonnes au 064).
        r["d"] = int(apres[-1]) if len(apres) >= 2 else 0
        res[nm] = r
    return res


def main():
    hist = {h["date"]: h for h in json.load(open(os.path.join(ROOT, "data", "zones-history.json"), encoding="utf-8"))}
    sortie = {}
    for date, (num, mode) in BULLETINS.items():
        zones = {k(z["name"]): (z["province"], z["name"]) for z in hist[date]["zones"]}
        res = extraire(date, num, mode, zones)
        p = PROVINCES[date]
        avec_d = "d" in p
        e = {"sitrep": num, "provinces": {}}
        for x, v in sorted(res.items(), key=lambda kv: zones[kv[0]][1]):
            prov, nom = zones[x]
            b = e["provinces"].setdefault(prov, {"zones": {}})
            b["zones"][nom] = {"c": v["c"], **({"d": v["d"]} if avec_d and "d" in v else {})}
        lignes = []
        for prov in sorted(set(p["c"]) | set(e["provinces"])):
            b = e["provinces"].setdefault(prov, {"zones": {}})
            sc = sum(z["c"] for z in b["zones"].values()) + p.get("horsC", {}).get(prov, 0)
            b["annonceCas"] = p["c"].get(prov)
            b["casValides"] = b["annonceCas"] is not None and sc == b["annonceCas"]
            if avec_d:
                sd = sum(z.get("d", 0) for z in b["zones"].values()) + p.get("horsD", {}).get(prov, 0)
                b["annonceDeces"] = p["d"].get(prov)
                b["decesValides"] = b["annonceDeces"] is not None and sd == b["annonceDeces"]
                lignes.append("%s %s/%s cas, %s/%s deces" % (prov, sc, b["annonceCas"], sd, b["annonceDeces"]))
            else:
                lignes.append("%s %s/%s cas" % (prov, sc, b["annonceCas"]))
        sortie[date] = e
        print(date, num, " ; ".join(lignes))
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
