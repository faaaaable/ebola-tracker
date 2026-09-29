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

PROVINCES_RE = r"Ituri|Nord[\s-]+Kivu|Haut[\s-]+U[ée]l[ée]|Tshopo|Sud[\s-]+Kivu|Bas[\s-]+U[ée]l[ée]|Sud[\s-]+Ubangi"


def canon(nom):
    """« Haut Uélé », « Haut-Uele », « Haut\nUélé » -> « Haut-Uélé », etc."""
    n = re.sub(r"[\s-]+", " ", nom).replace("Uele", "Uélé").replace("Uelé", "Uélé").replace("Uélè", "Uélé")
    n = {"Nord Kivu": "Nord-Kivu", "Sud Kivu": "Sud-Kivu", "Haut Uélé": "Haut-Uélé", "Sud Ubangi": "Sud-Ubangi"}.get(n, n)
    return PROVINCE_CANON.get(n, n)


# ---------------------------------------------------------------- prose (D)
# La prose n'est lue que sous le titre de l'époque D, « Continuité des
# soins ». Sous « Prise en charge » (B, C) la même section aligne des cumuls
# et des indicateurs qui ressemblent à des hospitalisés du jour — le 060
# donnait 753 hospitalisés au Nord-Kivu, son cumul de cas — et ces époques
# ont un tableau, lu en premier.
# Le SitRep 109 (31 août) renomme la section « Prise en charge holistique »,
# avec la meme prose que « Continuite des soins » (« 539 patients sont
# hospitalises pour 978 lits, soit un taux d'occupation de 55,1 % »). Le mot
# « holistique » la distingue du « Prise en charge » des epoques B et C, qui
# reste exclu.
DEBUT_RE = re.compile(r"(?:^|\n)[^\n]{0,12}(?:Continuit[ée] des soins|Prise en charge holistique)[^\n]{0,60}\n", re.IGNORECASE)
FIN_RE = re.compile(r"\n[^\n]{0,12}(?:Communication|CREC|Logistique|S[ée]curit[ée]|Recherche)", re.IGNORECASE)
# « Le Nord-Kivu suit avec 8 patients en isolement », « Le Sud-Kivu maintient
# une file active de 5 patients » (SitRep 018) : sans « Le », ces phrases
# restaient dans le morceau de l'Ituri, qui recevait les 8 patients du
# Nord-Kivu. Corrige le 4 septembre 2026.
REPERE_RE = re.compile(r"(?:^|[\n•→▪\-\uf000-\uf0ff]|\bEn |\bAu |\bÀ la |\bA la |\bau |\ben |\bà la |\bLe |\bL[’'])\s*(%s)\b" % PROVINCES_RE)

HOSPITALISES_RES = [
    # « 328 patients (97 confirmés et 231 suspects) sont hospitalisés, dont
    # 223 dans les CTE pour 354 lits » (135, Nord-Kivu) : la ventilation
    # s'intercale entre « patients » et le verbe. Sans ce motif, la ligne
    # prenait les « 105 autres » pris en charge hors CTE.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s*\(\s*\d[^)]{0,60}\)\s*sont\s+hospitalis", re.I),
    re.compile(r"occupation\s+atteint\s+(\d[\d ]{0,4}\d|\d)\s+patients", re.I),
    # « Au total, 368 patients demeuraient en isolement à la fin de la
    # journée » et « 345 patients demeuraient hospitalisés » (136).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+demeuraient\s+(?:en\s+isolement|hospitalis)", re.I),
    # « L'occupation des structures de prise en charge atteint 488 lits sur
    # 833 (59 %) » (084, 6 aout) : les patients comptes en lits occupes.
    re.compile(r"occupation[^.;]{0,60}?atteint\s+(\d[\d ]{0,4}\d|\d)\s+lits\s+sur\s+\d", re.I),
    # « 53 patients sont pris en charge (36 confirmés et 17 suspects) » (097,
    # Haut-Uele) : la ventilation entre parentheses ancre la tournure.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+patients\s+sont\s+pris\s+en\s+charge\s*\(\d", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades|cas suspects|cas)\s+(?:sont|restent|demeurent)?\s*(?:en\s+)?hospitalis", re.I),
    # « Huit (8) patients sont en isolement pour 25 lits » (109 Sud-Kivu) : le
    # nombre est entre parentheses, d'ou la parenthese fermante optionnelle.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\)?\s+(?:patients|malades)\s+sont\s+(?:en\s+)?isol", re.I),
    re.compile(r"port(?:e|ent|ant)\s+à\s+(\d[\d ]{0,4}\d|\d)\s+le\s+nombre\s+de\s+patients", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+(?:en\s+)?(?:hospitalisation|isolement)", re.I),
    # « 472 patients sont pris en charge en hospitalisation pour 1015 lits » et
    # « 7 patients restent en isolement » (122) : un verbe s'intercale entre les
    # patients et le mot qui les qualifie, que les motifs ci-dessus collent.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+(?:sont\s+pris\s+en\s+charge\s+en|restent\s+en|demeurent\s+en|sont\s+plac[ée]s?\s+en)\s+(?:hospitalisation|isolement)", re.I),
    # « Au terme de la journee, 62 patients, soit un taux d'occupation global
    # de 51,7% (120 lits) » (110 Haut-Uele) : ni « hospitalises » ni
    # « isolement », le nombre de patients est directement suivi du taux.
    # En dernier, pour ne jamais prendre le pas sur les tournures explicites.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades),?\s+soit\s+un\s+taux\s+d[’']occupation", re.I),
    # « L'Ituri concentre 91 % des patients hospitalisés (158/171) » et « une
    # file active de 5 patients au CTE Lwiro » (018, epoque A tardive).
    re.compile(r"patients\s+hospitalis\w*\s*\((\d[\d ]{0,4}\d|\d)\s*/\s*\d", re.I),
    re.compile(r"file\s+active\s+de\s+(\d[\d ]{0,4}\d|\d)\s+patients", re.I),
]
LITS_RE = re.compile(r"pour\s+(\d[\d ]{0,4}\d|\d)\s+lits|atteint\s+\d[\d ]{0,4}\s+lits\s+sur\s+(\d[\d ]{0,4}\d|\d)", re.I)
# « taux d'occupation global de 51,7% (120 lits) » (110 Haut-Uele) : les lits
# entre parentheses apres le taux, sans « pour ».
LITS_PARENTHESE_RE = re.compile(r"\((\d[\d ]{0,4}\d|\d)\s+lits\)", re.I)
# « en sursaturation (118,6 % ; 220 lits disponibles) » (111 Nord-Kivu) : les
# lits suivent le taux, apres le point-virgule, sans fraction ni « pour ».
# Le taux et le point-virgule sont exiges : sans eux, le motif mordait sur la
# synthese du SitRep 018 (« 71 lits disponibles au Nord-Kivu pour 8
# patients »), rattachee au morceau de l'Ituri.
LITS_DISPONIBLES_RE = re.compile(r"%\s*;\s*(\d[\d ]{0,4}\d|\d)\s+lits\s+disponibles", re.I)
# « en sursaturation (128,2 % ; 282/220) » (108 Nord-Kivu) : le dénominateur
# de la fraction qui suit le taux est le nombre de lits
# « en sursaturation (130,5 % ; 287/220 lits disponibles) » (117 Nord-Kivu) :
# la fraction du 108 ET le « lits disponibles » du 111 dans la meme parenthese.
# Sans ce motif, le 117 sortait avec l'occupation mais sans les lits, et la
# lettre plantait sur la province saturee.
LITS_FRACTION_RE = re.compile(r"%\s*;\s*\d[\d ]{0,4}\d?\s*/\s*(\d[\d ]{0,4}\d|\d)\s*(?:\)|lits\s+disponibles)")
# « 392 patients sont hospitalisés dont 224 dans les structures normées avec
# une capacité d'accueil de 228 lits, soit un taux d'occupation global de
# 98,2 % » (125 a 127, Nord-Kivu) : la capacite remplace « pour N lits », et
# le taux porte sur les seuls patients des structures normees — 224/228 fait
# bien 98,2 %, quand 392/228 en ferait 172. Sans ce motif, la province sortait
# avec son taux mais sans lits, et la vue nationale du graphique des CTE
# l'ecartait : neuf jours de courbe perdus (vu le 20 septembre 2026).
# Le 125 glisse le numero de page au milieu de la tournure — « capacité
# d'accueil 6 de 228 lits » — d'ou l'ancrage sur « lits » et non sur « de ».
# « portant la capacité provinciale à 130 lits » (097, Haut-Uele).
LITS_CAPACITE_RE = re.compile(
    r"capacit[ée]\s+(?:d[’']\s*accueil|provinciale\s+à)[^.;%]{0,24}?(\d[\d ]{0,4}\d|\d)\s+lits", re.I)
# Le denominateur du taux quand la province distingue les deux : « dont 224
# dans les structures normées », « dont 216 dans les structures dédiées »,
# « dont 250 dans les structures de prise en charge normées » (132, sans
# nombre de lits : la capacite se deduit alors du taux et se recoupe),
# « dont 223 dans les CTE pour 354 lits » (135).
HOSPITALISES_NORMES_RE = re.compile(
    r"dont\s+(\d[\d ]{0,4}\d|\d)\s+dans\s+(?:les\s+structures\s+(?:de\s+prise\s+en\s+charge\s+)?"
    r"(?:norm[ée]es|d[ée]di[ée]es)|les\s+CTE\b)", re.I)
OCCUPATION_RES = [
    re.compile(r"taux\s+d[’']occupation[^%\d]{0,30}?(\d+(?:[,.]\d+)?)\s*%", re.I),
    re.compile(r"(\d+(?:[,.]\d+)?)\s*%\s+d[’']occupation", re.I),
    # « 68 patients sont en isolement, soit 56,7% des lits occupés » (104)
    re.compile(r"(\d+(?:[,.]\d+)?)\s*%\s+des\s+lits\s+occup", re.I),
    re.compile(r"lits\s*\((\d+(?:[,.]\d+)?)\s*%\)", re.I),
    # « en sursaturation (128,2 % ; 282/220) » (108 Nord-Kivu)
    re.compile(r"occupation[^%\n]{0,60}?\((\d+(?:[,.]\d+)?)\s*%\s*;", re.I),
    # « est en⏎sursaturation (118,6 % ; 220 lits disponibles) » (111 Nord-Kivu) :
    # le saut de ligne entre « en » et « sursaturation » echappe au motif
    # precedent, qui interdit \n ; le mot lui-meme suffit a ancrer le taux.
    re.compile(r"sursaturation\s*\((\d+(?:[,.]\d+)?)\s*%", re.I),
]


def numerateur(ligne):
    """L'effectif que le site rapporte aux lits : TOUS les patients
    hospitalisés, toujours, y compris ceux installés hors des lits prévus.

    C'est la définition que l'INSP a tenue jusqu'au 14 septembre 2026, et
    celle qui mesure la saturation. Depuis le 15 il ne met au numérateur que
    les patients des structures normées du Nord-Kivu (216 sur 373), ce qui
    fait tomber le taux publié de 152,6 % à 94,7 % alors que le nombre de
    patients monte : les 157 malades couchés hors lits prévus — justement ce
    que le dépassement de 100 % sert à signaler — sortent du calcul. Le site
    rétablit donc la série à définition constante, et garde le taux du
    bulletin dans `occupationPubliee`. Décision du propriétaire, 20 septembre
    2026."""
    return ligne.get("hospitalises")


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
    m = (LITS_RE.search(morceau) or LITS_FRACTION_RE.search(morceau)
         or LITS_PARENTHESE_RE.search(morceau) or LITS_DISPONIBLES_RE.search(morceau)
         or LITS_CAPACITE_RE.search(morceau))
    if m:
        ligne["lits"] = entier(next(g for g in m.groups() if g))
    # Les hospitalises des seules structures normees, quand la province
    # distingue les deux : c'est EUX que le taux publie rapporte aux lits.
    # Garde-fou : pas plus que le total hospitalise, et le couple doit tomber
    # sur le taux publie, sinon on ne garde que le nombre.
    mn = HOSPITALISES_NORMES_RE.search(morceau)
    if mn:
        normes = entier(mn.group(1))
        if normes is not None and normes <= hosp:
            ligne["hospitalisesNormes"] = normes
    occ = None
    for rx in OCCUPATION_RES:
        mo = rx.search(morceau)
        if mo:
            occ = pourcent(mo.group(1))
            break
    normes = ligne.get("hospitalisesNormes")
    if occ is not None and normes is not None and normes != hosp:
        # Le taux publie ne porte que sur les structures normees : on le garde
        # tel quel, et on trace la serie a definition constante. Les lits, que
        # le 124 ne publie pas, se deduisent alors du couple publie
        # (216 vus comme 94,7 % font 228,1) — mais seulement si la deduction
        # retombe sur une capacite que le bulletin a imprimee par ailleurs,
        # sinon on ne deduit rien.
        ligne["occupationPubliee"] = occ
        if not ligne.get("lits"):
            deduits = round(normes / occ * 100)
            ligne["litsDeduits"] = deduits
        if ligne.get("lits"):
            ligne["occupation"] = round(hosp / ligne["lits"] * 100, 1)
            ligne["occupationCalculee"] = True
        else:
            ligne["occupation"] = occ
    elif occ is not None:
        ligne["occupation"] = occ
    elif ligne.get("lits"):
        ligne["occupation"] = round(numerateur(ligne) / ligne["lits"] * 100, 1)
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
    reste = (reste[:f.start()] if f else reste[:3000])[:4000]
    # Le bilan national qui clot la section (« Au total, 146 nouvelles
    # admissions … Ainsi, 803 patients demeuraient en isolement », 136) serait
    # sinon lu comme la ligne de la derniere province citee.
    g = re.search(r"\n\s*Au total,\s*\d[\d ]*\s+nouvelles\s+admissions", reste)
    return reste[:g.start()] if g else reste


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
# Du 059 au 080 le meme tableau porte aussi « Patients en isolement (fin J)
# 551 168 ND 3 722 » : c'est le chiffre du jour, celui que la une, la prose et
# les « Defis » du bulletin citent (« 77,7 % en Ituri (551 patients pour 709
# lits) », 069). « Au lit (J-1) » est celui de la veille : le lire decalait la
# courbe d'un jour sur 19 bulletins (trouve le 28 septembre 2026 en croisant
# les Defis avec cte.json). Du 019 au 058, seule la ligne J-1 existe : elle
# reste lue, et le point porte `patientsVeille`.
PATIENTS_FIN_J_RE = re.compile(r"\n(?:\d+\s+)?Patients?\s+en\s+isolement\s*\(fin\s*J\)\s+([^\n]+)")


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


def cellule_perdue(ligne, n, i_total, somme_ok, vides=None):
    """Une ligne a laquelle il manque une cellule vide (064 : « Patients en
    isolement (fin J) 548 174 ND 722 » sous cinq colonnes). On replace la
    cellule manquante a chaque position hors total ou, si `vides` est donne,
    seulement la ou la ligne de la veille porte « ND » (une province qui ne
    rapporte pas un jour ne rapporte pas le suivant) ; la lecture n'est retenue
    que si la somme retombe sur le total ET que toutes les positions possibles
    donnent les memes chiffres aux memes provinces. Sinon, rien."""
    if i_total is None:
        return None
    lectures = []
    for courte in decoupages(ligne, n - 1) or []:
        for k in range(n):
            if k == i_total or (vides is not None and k not in vides):
                continue
            c = courte[:k] + [None] + courte[k:]
            if c[i_total] is not None and somme_ok(c):
                lectures.append(c)
    if not lectures:
        return None
    for c in lectures[1:]:
        if any((a or 0) != (b or 0) for a, b in zip(c, lectures[0])):
            return None
    return lectures[0]


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
    mf = PATIENTS_FIN_J_RE.search(texte, mp.end())
    patients = None
    if mf and mf.start() - mp.end() < 2000:
        # la ligne du jour ne remplace celle de la veille que si sa somme tombe
        # juste : `cellules` rendrait sinon un decoupage non verifie
        patients = next((c for c in decoupages(mf.group(1), n) if i_total is not None and somme_ok(c)), None) \
            or cellule_perdue(mf.group(1), n, i_total, somme_ok,
                              vides={k for k, v in enumerate(cellules(mp.group(1), n, valide=somme_ok) or []) if v is None})
        # 061, 062, 080 : la ligne de la veille est elle-meme incomplete (cellules
        # vides non imprimees, pas de total au 080) et n'a jamais verifie sa somme.
        # La ligne du jour, de meme forme, est alors lue de la meme facon : pas
        # plus exigeant pour l'une que pour l'autre.
        if patients is None and not any(i_total is not None and somme_ok(c) for c in decoupages(mp.group(1), n) or []) \
                and len(mf.group(1).split()) == len(mp.group(1).split()):
            patients = cellules(mf.group(1), n, valide=somme_ok)
        veille = False
    if patients is None:
        patients = cellules(mp.group(1), n, valide=somme_ok)
        veille = True
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
        if veille:
            ligne["patientsVeille"] = True
        if lits and lits[k]:
            ligne["lits"] = lits[k]
            ligne["occupation"] = round(patients[k] / lits[k] * 100, 1)
            ligne["occupationCalculee"] = True
        provinces[canon(nom)] = ligne
    return provinces


# ----------------------------------------------------------------- commun
def avertissements(nom, ligne):
    out = []
    h, l, o = numerateur(ligne), ligne.get("lits"), ligne.get("occupation")
    if h is not None and l and o is not None and not ligne.get("occupationCalculee"):
        calc = round(h / l * 100, 1)
        if abs(calc - o) > 1.5:
            out.append("%s : occupation publiée %s %%, recalculée %s %% (%d/%d)" % (nom, o, calc, h, l))
    return out


def confirmer_lits_deduits(points):
    """Les lits deduits d'un couple publie ne sont retenus que si le bulletin
    a imprime la meme capacite a moins de trois lits pres, dans les sept jours
    qui precedent ou qui suivent.

    Le 124 (15 septembre 2026) donne « 216 dans les structures dédiées » et
    94,7 % sans jamais ecrire le nombre de lits : 216/0,947 fait 228,1, et le
    125 comme le 126 impriment 228. La deduction est donc confirmee. Sans ce
    garde-fou, une coquille de la source fabriquerait une capacite qui n'a
    jamais existe."""
    for i, p in enumerate(points):
        for nom, ligne in (p.get("provinces") or {}).items():
            deduits = ligne.get("litsDeduits")
            if not deduits or ligne.get("lits"):
                continue
            voisins = []
            for q in points[max(0, i - 7):i + 8]:
                v = (q.get("provinces") or {}).get(nom) or {}
                if q is not p and v.get("lits") and not v.get("litsDeduits"):
                    voisins.append(v["lits"])
            proche = [l for l in voisins if abs(l - deduits) <= 3]
            if proche:
                ligne["lits"] = min(proche, key=lambda l: abs(l - deduits))
                ligne["litsDeduits"] = True
                if ligne.get("hospitalises") and ligne["lits"]:
                    ligne["occupation"] = round(
                        ligne["hospitalises"] / ligne["lits"] * 100, 1)
                    ligne["occupationCalculee"] = True
            else:
                del ligne["litsDeduits"]


def encadrer_lits(points):
    """Une province sans lits imprimes, entre deux bulletins qui impriment la
    MEME capacite dans les sept jours avant et apres, recoit cette capacite.

    Le 134 (25 septembre 2026) ecrit « 351 patients sont hospitalisés dont 271
    dans les structures normées, soit un taux d'occupation de 70,9 % », sans
    nombre de lits ; et 70,9 % est exactement 251/354, le calcul du 133 : taux
    recopie, dont aucune capacite ne se deduit (271/0,709 = 382). Le 133 et le
    135 impriment tous deux 354 lits. Sans cette regle, la serie a definition
    constante (tous les hospitalises sur les lits) tombait ce jour-la au taux
    publie, 70,9 %, entre 103,1 et 92,7 : une chute qui n'a pas eu lieu. Le
    point recoit 351/354 = 99,2 %, et le taux publie reste dans
    occupationPubliee. Decision du proprietaire, 28 septembre 2026."""
    for i, p in enumerate(points):
        for nom, ligne in (p.get("provinces") or {}).items():
            if ligne.get("lits") or not ligne.get("hospitalises"):
                continue
            def imprime(q):
                v = (q.get("provinces") or {}).get(nom) or {}
                return v.get("lits") if v.get("lits") and not v.get("litsDeduits") else None
            avant = next((imprime(q) for q in reversed(points[max(0, i - 7):i]) if imprime(q)), None)
            apres = next((imprime(q) for q in points[i + 1:i + 8] if imprime(q)), None)
            if avant and avant == apres:
                ligne["lits"] = avant
                ligne["litsEncadres"] = True
                if "occupation" in ligne and "occupationPubliee" not in ligne:
                    ligne["occupationPubliee"] = ligne["occupation"]
                ligne["occupation"] = round(ligne["hospitalises"] / avant * 100, 1)
                ligne["occupationCalculee"] = True


def recouper_lits_precedents(points):
    """Le DERNIER bulletin n'a pas de voisin suivant, et encadrer_lits ne peut
    rien pour lui. Le 136 (27 septembre 2026) ne publie aucun nombre de lits :
    « 368 patients … Le taux d'occupation des lits était de 36,3 % » (Ituri).
    Une province sans lits recoit la capacite imprimee dans les sept jours
    precedents :
    - si le taux publie retombe dessus a 0,15 point pres (368/1 015 = 36,3 %,
      68/138 = 49,3 %), la capacite est recoupee ;
    - sinon le taux ne mesure pas la meme chose (Nord-Kivu : 63,0 % pour 345
      patients, recopie du 135, quand 345/354 = 97,5 %) : il passe en
      occupationPubliee, et la serie a definition constante prend la capacite
      de la veille, comme encadrer_lits le fait pour un taux recopie
      (decision du proprietaire du 28 septembre 2026).
    Le bulletin suivant tranche : ce point n'est plus le dernier, et
    encadrer_lits le reprend ou le laisse sans lits. Seul le dernier point
    est concerne — l'historique garde ses taux publies."""
    if not points:
        return
    i = len(points) - 1
    p = points[i]
    for nom, ligne in (p.get("provinces") or {}).items():
        if ligne.get("lits") or not ligne.get("hospitalises") or ligne.get("occupation") is None:
            continue
        def imprime(q):
            v = (q.get("provinces") or {}).get(nom) or {}
            return v.get("lits") if v.get("lits") and not v.get("litsDeduits") else None
        avant = next((imprime(q) for q in reversed(points[max(0, i - 7):i]) if imprime(q)), None)
        if not avant:
            continue
        calcule = round(ligne["hospitalises"] / avant * 100, 1)
        ligne["lits"] = avant
        if abs(calcule - ligne["occupation"]) <= 0.15:
            ligne["litsRecoupes"] = True
        else:
            ligne["litsReportes"] = True
            ligne["occupationPubliee"] = ligne["occupation"]
            ligne["occupation"] = calcule
            ligne["occupationCalculee"] = True


def recalculer_total(point):
    """Le cumul national suit les lignes de province, y compris celles dont la
    capacite vient d'etre confirmee."""
    provinces = point.get("provinces") or {}
    avec_lits = [v for v in provinces.values() if v.get("lits")]
    total = point["total"]
    for cle in ("lits", "hospitalisesAvecLits", "occupation"):
        total.pop(cle, None)
    if avec_lits:
        total["lits"] = sum(v["lits"] for v in avec_lits)
        total["hospitalisesAvecLits"] = sum(numerateur(v) for v in avec_lits)
        total["occupation"] = round(total["hospitalisesAvecLits"] / total["lits"] * 100, 1)


# Les 081 et 083 (3 et 5 aout) sont mis en page sur deux colonnes que
# l'extraction du texte entrelace : « → Ituri : 21 nouveaux guéris ; 471
# patients en isolement visites, 22 lors de 7 causeries éducatives, 30 en
# (302 confirmés, 169 suspects) sur 833 lits, soit 56,5 % … d'occupation ».
# Aucun motif ne s'y fie sans risque ; lus a la main (audit du 27 septembre
# 2026) et ajoutes s'ils manquent.
LECTURES_NOMMEES = {
    "081": {"Ituri": {"hospitalises": 471, "lits": 833, "occupation": 56.5}},
    # « 468 patients en isolement … pour 833 lits (56 %), dont 271 confirmés et
    # 197 suspects »
    "083": {"Ituri": {"hospitalises": 468, "lits": 833, "occupation": 56.0}},
}


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
    for nom, ligne in LECTURES_NOMMEES.get(meta["sitrepNumber"], {}).items():
        if nom not in provinces:
            provinces[nom] = dict(ligne)
            methode = methode if provinces else "lecture nommée"
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
        total["hospitalisesAvecLits"] = sum(numerateur(p) for p in avec_lits)
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
    confirmer_lits_deduits(final)
    encadrer_lits(final)
    recouper_lits_precedents(final)
    for p in final:
        recalculer_total(p)
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
