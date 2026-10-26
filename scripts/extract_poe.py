#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le tableau des points d'entree et de controle (PoE/PoC), ligne par ligne
et province par province (14 octobre 2026).

extract_piliers.py n'en retient que trois nombres pour la lettre (personnes
passees, % screenes, refus). Ici, tout le tableau « Situation indicateurs
cles des PoE/PoC par province » : completude, postes fonctionnels, flux de
voyageurs, screening, lavage des mains, sensibilisation, alertes, alertes
vivantes validees, corps interceptes, transferts, swabs, investigations.

Le tableau est lu par pdfplumber (extract_tables), pas dans le texte : dans
le texte, les valeurs d'une ligne tombent souvent au-dessus ou au-dessous
de son libelle coupe en deux. Chaque valeur garde sa chaine brute (« brut »)
a cote de sa lecture ; « ND », « NA », « s.o. » et « - » se lisent null.

Ce sont des chiffres DU JOUR (le flux de voyageurs n'est pas un cumul).

Sortie : data/points-controle.json, une entree par bulletin (parDate).

Usage : python scripts/extract_poe.py [--seulement 149]
"""
import io
import json
import os
import re
import sys

import pdfplumber

from extract_piliers import dates_par_numero

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "points-controle.json")

# Libelle de ligne -> cle. L'ordre compte : « alertes vivantes validees »
# avant « alertes notifiees », « refus du screening » avant « screenes ».
INDICATEURS = [
    ("completude", r"compl[ée]tude"),
    ("posteStrategiquesFonctionnels", r"strat[ée]giques"),
    ("postesActives", r"activ[ée]s"),
    ("personnes", r"(personnes|voyageurs) pass[ée]"),
    ("refusScreening", r"refus du (screening|d[ée]pistage)"),
    ("refusLavage", r"refus de lavage"),
    ("screenes", r"screen[ée]s|d[ée]pist[ée]s"),
    ("lavageMains", r"lav[ée]s? (les|le) mains"),
    ("sensibilises", r"sensibilis[ée]s"),
    ("alertesVivantesValidees", r"alertes (vivantes )?valid[ée]es$|alertes vivantes valid[ée]es"),
    ("alertesInvestiguees24h", r"alertes investigu[ée]es"),
    ("alertesTransferees", r"alertes transf[ée]r[ée]es"),
    ("alertes", r"alertes notifi[ée]es|alertes remont[ée]es"),
    ("corpsInterceptes", r"corps sans vie intercept"),
    ("contactsInterceptes", r"contacts .*intercept"),
    ("suspectsTransferes", r"(transf[ée]r[ée]s|r[ée]f[ée]r[ée]es) au"),
    ("corpsSwabes", r"swab"),
    ("suspectsInvestigues24h", r"investigu[ée]s dans"),
    ("positifsReferes", r"r[ée]sultats? positifs?"),
]

VIDE = {"", "nd", "na", "s.o.", "so", "-", "–", "n/a"}
PROVINCES = ["Ituri", "Nord-Kivu", "Sud-Kivu", "Haut-Uélé", "Bas-Uélé", "Tshopo",
             "Kinshasa", "Sud-Ubangi", "Tanganyika", "Global"]


def propre(c):
    return " ".join((c or "").split())


def cle_indicateur(libelle):
    lib = propre(libelle).lower().replace("’", "'")
    for cle, motif in INDICATEURS:
        if re.search(motif, lib):
            return cle
    return None


def province(entete):
    # « Sud -Kivu » (112) : espaces autour du tiret
    e = re.sub(r"\s*-\s*", "-", propre(entete)).lower().replace(" ", "-")
    if e in ("global", "total", "ensemble", "resultats", "résultats"):
        return "Global"
    for p in PROVINCES:
        if p.lower() == e or p.lower().replace("é", "e") == e.replace("é", "e"):
            return p
    return None


def valeur(brut):
    """« 96,0 % (58/60) » -> {pct, num, den} ; « 140 888 » -> 140888."""
    # « 14 057 ... » (017) : colonnes vides imprimees en points de suspension
    b = re.sub(r"(?:\s*(?:\.\.\.|…))+$", "", propre(brut)).rstrip("*").strip()
    # « NA (0/0) » (107, 108) : non applicable, la fraction le confirme
    b_sans = re.sub(r"\(\s*0\s*/\s*0\s*\)", "", b).strip()
    if b.lower() in VIDE or b_sans.lower() in VIDE:
        return None
    # « 18 010 (98,7%) » (015, 016) : un effectif et sa part
    m = re.match(r"^(\d{1,3}(?: \d{3})+|\d+)\s*\(\s*([\d,.]+)\s*%\s*\)$", b)
    if m:
        return {"num": int(m.group(1).replace(" ", "")), "pct": float(m.group(2).replace(",", "."))}
    # « 17900 98,6% », « 18 153 NA » (018) : l'effectif, puis son taux
    m = re.match(r"^(\d{1,3}(?: \d{3})+|\d+)\s+([\d,.]+)\s*%$", b)
    if m:
        return {"num": int(m.group(1).replace(" ", "")), "pct": float(m.group(2).replace(",", "."))}
    m = re.match(r"^(\d{1,3}(?: \d{3})+|\d+)\s+(?:NA|ND)$", b)
    if m:
        return int(m.group(1).replace(" ", ""))
    m = re.match(r"^([\d ]+(?:[,.][\d ]+)?)\s*%\s*(?:\((\d[\d ]*)\s*/\s*(\d[\d ]*)\))?$", b)
    if m:
        v = {"pct": float(m.group(1).replace(" ", "").replace(",", "."))}
        if m.group(2):
            v["num"], v["den"] = int(m.group(2).replace(" ", "")), int(m.group(3).replace(" ", ""))
        return v
    # « (2/2) 100% » (111) : la fraction avant le taux
    m = re.match(r"^\((\d+)\s*/\s*(\d+)\)\s*([\d,.]+)\s*%$", b)
    if m:
        return {"pct": float(m.group(3).replace(",", ".")), "num": int(m.group(1)), "den": int(m.group(2))}
    # « 2(66 ,6%) » (SitRep 022) : un effectif et son pourcentage
    m = re.match(r"^(\d+)\s*\(\s*([\d ,.]+)\s*%\s*\)$", b)
    if m:
        return {"num": int(m.group(1)), "pct": float(m.group(2).replace(" ", "").replace(",", "."))}
    if re.match(r"^\d{1,3}(?: \d{3})+$|^\d+$", b):
        return int(b.replace(" ", ""))
    return b  # illisible : on garde la chaine telle quelle


def tableaux_poe(pdf):
    """Les lignes du tableau PoE/PoC, en-tete compris, sur une ou deux pages."""
    lignes, page_debut = [], None
    for i, page in enumerate(pdf.pages):
        txt = page.extract_text() or ""
        if not re.search(r"voyageurs|alertes notifi|PoE|PoC", txt):
            continue
        for t in page.extract_tables():
            rangs = [[propre(c) for c in r] for r in t]
            # Les cellules vides de mise en page (SitRep 060) decalent les
            # colonnes : on les retire, la ligne garde ses seules valeurs.
            rangs = [[c for c in r if c] for r in rangs]
            rangs = [r for r in rangs if r]
            if not any(cle_indicateur(r[0]) in ("screenes", "personnes", "alertes") for r in rangs):
                # suite d'un tableau coupe par le saut de page
                if not (lignes and page_debut is not None and i == page_debut + 1
                        and any(cle_indicateur(r[0]) for r in rangs)):
                    continue
            if page_debut is None:
                page_debut = i
            lignes.extend(rangs)
        if lignes and page_debut is not None and i > page_debut:
            break
    return lignes


# ------------------------------------------------------------------ texte
# SitReps 022 a 092 : le tableau est imprime sans filets, extract_tables n'y
# voit rien. On le relit dans le texte : une ligne d'en-tete « Indicateurs
# Ituri Nord-Kivu … Global », puis une ligne par indicateur, libelle puis
# valeurs. Les fractions « (60/60) », qui passent souvent a la ligne, sont
# ecartees : seuls les taux et les effectifs sont lus dans ce mode.
ENTETE_TEXTE_RE = re.compile(r"(?mi)^\s*(?:indicateurs?|variables)\s+(.+)$")
MOT_VALEUR_RE = re.compile(r"^(?:[\d,.%()/*]+|ND|NA|s\.o\.?|-|–)$", re.I)
JETON_RE = re.compile(r"\d+(?:[,.]\d+)?\s*%|ND|NA|s\.o\.?|[-–]|\d+", re.I)
FIN_TABLEAU_RE = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?\s+[A-ZÉ]|TABLEAU|Tableau|Source)")


def entete_texte(ligne, suivante):
    mots = ligne.split()
    suite = suivante.split()
    cols = []
    for m in mots:
        if m.endswith("-") and suite:  # « Haut- Global » puis « Uélé » (080)
            m = m + suite.pop(0)
        cols.append(province(m))
    # 053 : « INDICATEURS Ituri Nord-Kivu », sans colonne Global
    return cols if cols and all(cols) and ("Global" in cols or len(cols) >= 2) else None


def decoupages(jetons, n):
    """Les facons de lire les jetons en n valeurs : un entier peut absorber
    les groupes de trois chiffres qui le suivent (« 98 289 » = 98289)."""
    if not jetons:
        return [[]] if n == 0 else []
    if n == 0:
        return []
    j = jetons[0]
    out = []
    if re.match(r"^\d+$", j) and len(j) <= 3:
        k = 1
        while True:
            nombre = "".join(jetons[:k])
            out += [[nombre] + reste for reste in decoupages(jetons[k:], n - 1)]
            if k < len(jetons) and re.match(r"^\d{3}$", jetons[k]):
                k += 1
            else:
                break
    else:
        out += [[j] + reste for reste in decoupages(jetons[1:], n - 1)]
    return out


def valeurs_texte(brut, colonnes):
    # « 21, 8% (12/55) », « 2(66 ,6%) » (022) : espaces autour de la virgule
    brut = re.sub(r"(\d)\s*,\s+(\d)|(\d)\s+,\s*(\d)",
                  lambda m: (m.group(1) or m.group(3)) + "," + (m.group(2) or m.group(4)), brut)
    if len(colonnes) == 1:
        return [brut]  # une seule colonne : la chaine entiere est la valeur
    s = re.sub(r"\(\s*\d+\s*/\s*\d+\s*\)", " ", brut).replace("*", " ")
    jetons = [j.replace(" ", "") for j in JETON_RE.findall(s)]
    cands = decoupages(jetons, len(colonnes))
    if "Global" in colonnes and len(colonnes) > 1:
        def entiers(c):
            # une ligne d'effectifs : des entiers, et des ND/NA comptant pour 0
            return all(re.match(r"^\d+$", x) or valeur(x) is None for x in c) \
                and re.match(r"^\d+$", c[-1])
        def somme_ok(c):
            return int(c[-1]) == sum(int(x) for x in c[:-1] if re.match(r"^\d+$", x))
        if cands and all(entiers(c) for c in cands):
            # aucune lecture ne retombe sur le Global : on ne devine pas
            cands = [c for c in cands if somme_ok(c)]
    # plusieurs lectures : seule celle qui ne colle aucun nombre est sure
    if len(cands) > 1:
        sans_collage = [c for c in cands if len(c) == len(jetons)]
        cands = sans_collage if len(sans_collage) == 1 else []
    return cands[0] if len(cands) == 1 else None


def lire_texte(texte):
    lignes = texte.split("\n")
    for i, l in enumerate(lignes):
        m = ENTETE_TEXTE_RE.match(l)
        if not m:
            continue
        bloc = "\n".join(lignes[i:i + 30])
        if not re.search(r"voyageurs|alertes notifi", bloc, re.I):
            continue
        suivante = lignes[i + 1] if i + 1 < len(lignes) else ""
        if re.match(r"^\s*(?:r[ée]sultats?|total|PoE/PoC\s+valeur\b.*)\s*$", m.group(1), re.I):
            # 022 : « Indicateurs Resultats » ; 012 : « VARIABLES TOTAL » ;
            # 018 : « Indicateur PoE/PoC Valeur (24h) Taux »
            colonnes = ["Global"]
        else:
            colonnes = entete_texte(m.group(1), suivante)
        if not colonnes:
            continue
        out, ecarts = {}, []
        for l2 in lignes[i + 1:i + 40]:
            if FIN_TABLEAU_RE.match(l2) and out:
                break
            # 017 : le tableau de surveillance (« Indicateur Valeur Cible
            # Performance », 192 alertes) precede celui des PoE/PoC ; un
            # nouvel en-tete ferme le tableau en cours.
            me = ENTETE_TEXTE_RE.match(l2)
            if me:
                # 059, 061 : l'en-tete se repete apres le saut de page — meme
                # tableau, on continue
                if entete_texte(me.group(1), "") == colonnes:
                    continue
                break
            mots = l2.split()
            debut = next((k for k in range(len(mots)) if all(MOT_VALEUR_RE.match(w) for w in mots[k:])), None)
            if debut is None or debut == 0:
                continue
            libelle, brut = " ".join(mots[:debut]), " ".join(mots[debut:])
            cle = cle_indicateur(libelle)
            if not cle or cle in out:
                continue
            vals = valeurs_texte(brut, colonnes)
            if vals is None:
                ecarts.append("%s : « %s » illisible pour %d colonnes (texte)" % (cle, brut, len(colonnes)))
                continue
            out[cle] = {p: {"valeur": valeur(v), "brut": v} for p, v in zip(colonnes, vals)}
        # un tableau PoE/PoC compte des voyageurs ; sinon c'est un autre tableau
        if out and ({"personnes", "screenes"} & set(out)):
            return {"colonnes": colonnes, "indicateurs": out, "ecarts": ecarts, "lecture": "texte"}
    return None


# ------------------------------------------------------------------ prose
# SitReps 087 a 092 : pas de tableau, deux phrases — « Vingt alertes ont été
# détectées aux différents PoE/PoC (10 au Haut-Uélé, 6 en Ituri et 4 au
# Nord-Kivu) » et « Au total, 106 546 voyageurs ont été contrôlés (92 432 en
# Ituri, 14 114 au Haut-Uélé), avec un taux de dépistage de 98 % ».
NOMBRE = r"\d{1,3}(?:[ \u00a0\u202f]\d{3})+|\d+"
VOYAGEURS_RE = re.compile(r"(%s)\s+voyageurs\s+ont\s+été\s+contr[ôo]l[ée]s\s*(?:\(([^)]*)\))?"
                          r"[^.%%]{0,40}?taux\s+de\s+d[ée]pistage\s+de\s+([\d,]+)\s*%%" % NOMBRE, re.I)
ALERTES_PROSE_RE = re.compile(r"(\w+)\s*(?:\((\d+)\)\s*)?alertes?\s+(?:ont\s+été|a\s+été)\s+d[ée]tect[ée]es?"
                              r"\s+aux\s+diff[ée]rents\s+PoE/PoC\s*(?:\(([^)]*)\))?", re.I)
MOTS_NOMBRES = {"une": 1, "un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
                "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "treize": 13, "quatorze": 14,
                "quinze": 15, "seize": 16, "vingt": 20, "trente": 30, "aucune": 0}


def par_province(texte_parenthese):
    """« 92 432 en Ituri, 14 114 au Haut-Uélé » -> {Ituri: 92432, …}"""
    out = {}
    for m in re.finditer(r"(%s)\s+(?:en|au|à\s+la|à|dans\s+la)\s+([A-ZÉ][\w-]+(?:[- ][A-ZÉ][\w]+)?)" % NOMBRE,
                         texte_parenthese or ""):
        p = province(m.group(2))
        if p and p != "Global":
            out[p] = int(re.sub(r"\D", "", m.group(1)))
    return out


def lire_prose(texte):
    plat = " ".join(texte.split())
    out = {}
    m = VOYAGEURS_RE.search(plat)
    if m:
        provs = par_province(m.group(2))
        total = int(re.sub(r"\D", "", m.group(1)))
        out["personnes"] = {p: {"valeur": v, "brut": str(v)} for p, v in provs.items()}
        out["personnes"]["Global"] = {"valeur": total, "brut": m.group(1)}
        out["screenes"] = {"Global": {"valeur": {"pct": float(m.group(3).replace(",", "."))},
                                      "brut": m.group(3) + " %"}}
    m = ALERTES_PROSE_RE.search(plat)
    if m:
        n = int(m.group(2)) if m.group(2) else MOTS_NOMBRES.get(m.group(1).lower())
        if n is None and m.group(1).isdigit():
            n = int(m.group(1))
        if n is not None:
            provs = par_province(m.group(3))
            out["alertes"] = {p: {"valeur": v, "brut": str(v)} for p, v in provs.items()}
            out["alertes"]["Global"] = {"valeur": n, "brut": m.group(0)[:40]}
    if not out:
        return None
    colonnes = sorted({p for ind in out.values() for p in ind if p != "Global"}) + ["Global"]
    return {"colonnes": colonnes, "indicateurs": out, "ecarts": [], "lecture": "prose"}


def lire(chemin):
    with pdfplumber.open(chemin) as pdf:
        tab = lire_tableau(pdf)
        brut = "\n".join((p.extract_text() or "") for p in pdf.pages)
        txt = lire_texte(brut)
    # La lecture qui donne le plus d'indicateurs l'emporte ; a egalite, le
    # tableau, qui garde les fractions. La prose ne sert qu'a defaut des deux.
    cands = [r for r in (tab, txt) if r and r["indicateurs"]]
    if not cands:
        pr = lire_prose(brut)
        return pr
    if not cands:
        return None
    return max(cands, key=lambda r: (len(r["indicateurs"]), r.get("lecture") != "texte"))


def lire_tableau(pdf):
    lignes = tableaux_poe(pdf)
    if not lignes:
        return None
    colonnes = None
    for i, r in enumerate(lignes):
        cellules = list(r)
        # SitRep 100 : « Nord- », « Sud- », « Haut- », « Bas- » en en-tete, la
        # fin du nom sur la ligne suivante (« Kivu », « Kivu », « Uélé »…).
        if any(c.endswith("-") for c in cellules) and i + 1 < len(lignes):
            suite = list(lignes[i + 1])
            cellules = [c + suite.pop(0) if c.endswith("-") and suite else c for c in cellules]
        for depart in (0, 1):  # 094 : pas de cellule « Indicateurs »
            provs = [province(c) for c in cellules[depart:]]
            if provs and all(provs) and "Global" in provs:
                colonnes = provs
                break
        if colonnes:
            break
    if colonnes is None:
        colonnes = ["Global"]  # tableau a une colonne « Resultats » (SitRep 022)
    out, ecarts = {}, []
    for r in lignes:
        cle = cle_indicateur(r[0]) if r else None
        if not cle or cle in out:
            continue
        vals = r[1:]
        if len(vals) != len(colonnes):
            ecarts.append("%s : %d valeurs pour %d colonnes" % (cle, len(vals), len(colonnes)))
            continue
        out[cle] = {p: {"valeur": valeur(v), "brut": v} for p, v in zip(colonnes, vals)}
    return {"colonnes": colonnes, "indicateurs": out, "ecarts": ecarts, "lecture": "tableau"}


def controle_somme(entree):
    """Pour les effectifs, Global = somme des provinces ? (alerte, pas blocage)"""
    notes = []
    ind = entree["indicateurs"]
    provs = [p for p in entree["colonnes"] if p != "Global"]
    if not provs or "Global" not in entree["colonnes"]:
        return notes
    for cle in ("personnes", "alertes", "alertesVivantesValidees", "corpsInterceptes"):
        if cle not in ind or not all(p in ind[cle] for p in provs) or "Global" not in ind[cle]:
            continue  # prose : toutes les provinces ne sont pas citees
        vs = [ind[cle][p]["valeur"] for p in provs]
        g = ind[cle]["Global"]["valeur"]
        if isinstance(g, int) and all(isinstance(v, int) for v in vs) and sum(vs) != g:
            notes.append("%s : somme des provinces %d, Global %d" % (cle, sum(vs), g))
    return notes


# Valeurs ecartees a la demande du proprietaire (26 octobre 2026), apres
# relecture des PDF. Les trois chiffres sont bien imprimes, et la ligne
# s'additionne juste avec le total : le bulletin ne se contredit pas, mais
# un flux qui triple d'un jour a l'autre sur une douzaine de postes, puis
# revient a son niveau, se lit comme une coquille ou un cumul de plusieurs
# jours. La valeur garde sa chaine « brut » et porte « ecarte » ; le total
# du jour, qui la contient, est ecarte avec elle. Liste nominative, comme
# JOURNEES_ECARTEES d'extraire_alertes : on n'y ajoute rien sans relire le PDF.
VALEURS_ECARTEES = [
    # SitRep 040 (23 juin) : « Nombre des personnes passées aux PoE/PoC
    # 72 530 150 276 222 806 » — le Nord-Kivu fait 48 419 la veille, 51 100
    # le 25 juin.
    ("040", "personnes", ("Nord-Kivu", "Global"), "Nord-Kivu 150 276, hors de proportion avec les jours voisins"),
    # SitRep 041 (24 juin) : « 92 533 171 591 264 124 ».
    ("041", "personnes", ("Nord-Kivu", "Global"), "Nord-Kivu 171 591, hors de proportion avec les jours voisins"),
    # SitRep 047 (30 juin) : « Nombre de personnes passées aux PoE/PoC
    # 166 171 63 837 230 008 » — l'Ituri fait 95 558 la veille, 89 504 le
    # 2 juillet.
    ("047", "personnes", ("Ituri", "Global"), "Ituri 166 171, hors de proportion avec les jours voisins"),
]


def ecarter(entree):
    for num, cle, colonnes, motif in VALEURS_ECARTEES:
        if entree["sitrepNumber"] != num:
            continue
        for col in colonnes:
            v = entree["indicateurs"].get(cle, {}).get(col)
            if v is not None:
                v["valeur"] = None
                v["ecarte"] = motif


def main(argv):
    seulement = None
    if "--seulement" in argv:
        seulement = argv[argv.index("--seulement") + 1].zfill(3)
    dates = dates_par_numero()
    existant = {}
    if os.path.exists(OUT):
        with io.open(OUT, encoding="utf-8") as fh:
            existant = {e["sitrepNumber"]: e for e in json.load(fh).get("parDate", [])}
    for f in sorted(os.listdir(os.path.join(ROOT, "reports"))):
        m = re.match(r"SITREP_MVE_(\d+)\.pdf$", f)
        if not m:
            continue
        num = m.group(1).zfill(3)
        if (seulement and num != seulement) or num not in dates:
            continue
        try:
            t = lire(os.path.join(ROOT, "reports", f))
        except Exception as exc:  # un PDF illisible ne bloque pas les autres
            print("SitRep %s : %s" % (num, exc), file=sys.stderr)
            continue
        if t is None:
            existant.pop(num, None)
            continue
        e = {"date": dates[num], "sitrepNumber": num}
        e.update(t)
        e["ecarts"] = t["ecarts"] + controle_somme(e)
        ecarter(e)
        e["source"] = "SitRep INSP, tableau PoE/PoC"
        existant[num] = e
    par_date = sorted(existant.values(), key=lambda e: (e["date"], e["sitrepNumber"]))
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"periode": {"debut": par_date[0]["date"] if par_date else None,
                               "fin": par_date[-1]["date"] if par_date else None},
                   "parDate": par_date}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("%d bulletins avec un tableau PoE/PoC" % len(par_date))


if __name__ == "__main__":
    main(sys.argv)
