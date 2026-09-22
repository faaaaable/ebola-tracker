#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Échantillons analysés et résultats positifs, par province et par jour.

Lit la section « Laboratoire » de chaque bulletin et écrit
data/laboratoire.json. C'est la donnée qui répond à « teste-t-on assez ? » :
une positivité qui monte pendant que le nombre d'échantillons stagne signifie
qu'on ne prélève que les malades évidents.

La phrase a changé de forme à chaque époque éditoriale, sans jamais changer de
fond — un nombre d'échantillons, un nombre de positifs, une positivité :

  B  « Ituri : 139 nouveaux échantillons collectés et analysés
        (positivité 40,3% ; n=56) »
     « Nord-Kivu : 97 échantillons reçus dont 77 analysés, (positivité 11,7% ;
        n=9) »
     « Sud-Kivu : 8 échantillons collectés et analysés, tous sont revenus
        négatifs »
  C  « Ituri : 229 échantillons analysés (208 sang, 21 swab) dont 42 positifs,
        soit un taux de positivité de 18,3% »
     « Ituri : 155 échantillons documentés dans le réseau de collecte, dont 51
        positifs (33 vivants et 18 décès), soit une positivité apparente de
        32,9 % »
  D  « L'Ituri a enregistré 80 résultats positifs (249 échantillons analysés),
        dont 67 nouveaux cas (58 vivants et 9 décès) et 13 réprélèvements »
     « Ituri : 35 nouveaux résultats positifs (23 vivants et 12 décès) sur 173
        nouveaux échantillons reçus et analysés (positivité : 20,2 %) »

Plutôt qu'un motif par forme, on découpe la section par province et on cherche
dans chaque morceau les trois nombres, chacun sous ses quelques écritures. Une
province dont on ne lit ni les échantillons ni les positifs est écartée ce
jour-là — mieux vaut un trou visible qu'un nombre deviné. Les réprélèvements
(un même patient testé à nouveau) ne sont PAS des nouveaux cas : quand le
bulletin les sépare, seuls les nouveaux cas comptent comme positifs, et le
contrôle « somme des positifs = nouveaux cas du jour » de check_coherence.py
n'a de sens que pour ces bulletins-là.

Rien n'est recalculé à la place de la source : si le bulletin donne la
positivité sans les positifs, la positivité seule est gardée.

    python scripts/extraire_laboratoire.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textes_pdf import ROOT, rapports, numero, texte_du_rapport, entier, pourcent  # noqa: E402
from update_data import extract_meta, PROVINCE_CANON  # noqa: E402

OUTPUT_PATH = os.path.join(ROOT, "data", "laboratoire.json")

PROVINCES_RE = r"Ituri|Nord[\s-]+Kivu|Haut[\s-]+U[ée]l[ée]|Tshopo|Sud[\s-]+Kivu|Bas[\s-]+U[ée]l[ée]|Sud[\s-]+Ubangi"


def canon(nom):
    """« Haut Uélé », « Haut-Uele », « Haut\nUélé » -> « Haut-Uélé », etc."""
    n = re.sub(r"[\s-]+", " ", nom).replace("Uele", "Uélé").replace("Uelé", "Uélé").replace("Uélè", "Uélé")
    n = {"Nord Kivu": "Nord-Kivu", "Sud Kivu": "Sud-Kivu", "Haut Uélé": "Haut-Uélé", "Sud Ubangi": "Sud-Ubangi"}.get(n, n)
    return PROVINCE_CANON.get(n, n)


# Début de la section : un titre qui contient « Laboratoire ». Fin : le titre
# de la section suivante, PCI dans toutes les époques.
DEBUT_RE = re.compile(r"(?:^|\n)[^\n]{0,20}Laboratoire(?:\s*[:—–-]\s*tests et positivit[ée])?", re.IGNORECASE)
FIN_RE = re.compile(r"\n[^\n]{0,12}(?:Prévention et Contrôle|PCI\b|Pr[ée]vention.{0,5}contr[ôo]le|Enterrements|EDS\b)",
                    re.IGNORECASE)


def section_laboratoire(texte):
    m = DEBUT_RE.search(texte)
    if not m:
        return None
    reste = texte[m.end():]
    f = FIN_RE.search(reste)
    section = reste[:f.start()] if f else reste[:2500]
    return section[:3000]


# Repère de province : le nom, en tête de puce ou précédé de « L' » / « le » /
# « la » / « au ». On découpe la section aux repères.
REPERE_RE = re.compile(r"(?:^|[\n•→▪\-\uf000-\uf0ff]|\bL[’']|\ble |\bla |\bau |\bà la |\ben )\s*(%s)\b" % PROVINCES_RE)

ECHANTILLONS_RES = [
    # « 76 nouveaux échantillons collectés dont 39 ont été analysés » (B)
    # « dont 1 swab analyse » (106 Tshopo) : « swab » peut s'intercaler, l'accent manquer
    re.compile(r"[ée]chantillons?\s+(?:ont\s+[ée]t[ée]\s+)?(?:collect[ée]s?|re[çc]us?|pr[ée]lev[ée]s?)\s*,?\s*dont\s+(\d[\d ]{0,6}\d|\d)\s+(?:swabs?\s+)?(?:ont\s+[ée]t[ée]\s+)?analys[ée]s?", re.I),
    # « 7 échantillons ont été collectés et analysés » (B), « 1 échantillon reçu et analysé » (D)
    re.compile(r"(\d[\d ]{0,6}\d|\d)\s*(?:nouveaux?\s+)?[ée]chantillons?\s+(?:ont\s+[ée]t[ée]\s+)?(?:re[çc]us?|collect[ée]s?)\s+et\s+(?:analys[ée]s?|test[ée]s?)", re.I),
    re.compile(r"(\d[\d ]{0,6}\d|\d)\s*(?:nouveaux\s+)?[ée]chantillons\s+(?:re[çc]us\s+et\s+|collect[ée]s\s+et\s+|re[çc]us,?\s+|nouveaux\s+)?(?:analys[ée]s|document[ée]s|test[ée]s)", re.I),
    re.compile(r"sur\s+(\d[\d ]{0,6}\d|\d)\s*(?:nouveaux\s+)?[ée]chantillons", re.I),
    re.compile(r"\((\d[\d ]{0,6}\d|\d)\s*[ée]chantillons\s+analys[ée]s\)", re.I),
    re.compile(r"[ée]chantillons\s+(?:re[çc]us|pr[ée]lev[ée]s)\s*,?\s*dont\s+(\d[\d ]{0,6}\d|\d)\s+(?:ont\s+[ée]t[ée]\s+)?analys[ée]s", re.I),
    re.compile(r"(\d[\d ]{0,6}\d|\d)\s*[ée]chantillons\s+ont\s+[ée]t[ée]\s+analys[ée]s", re.I),
    re.compile(r"(\d[\d ]{0,6}\d|\d)\s*[ée]chantillons\s+re[çc]us\b(?=[^.]*positi)", re.I),
    # « 1 échantillon analysé » au singulier (119 Sud-Ubangi, « sur l'échantillon analysé » réécrit en amont)
    re.compile(r"(\d[\d ]{0,6}\d|\d)\s*[ée]chantillon\s+analys[ée]\b", re.I),
    # « 1 swab reçu et testé » (D, 108 Bas-Uélé)
    re.compile(r"(\d[\d ]{0,6}\d|\d)\s*swabs?\s+re[çc]us?\s+et\s+test[ée]s?", re.I),
    # « 2 nouveaux échantillons ont été reçus, tous sont revenus négatifs » (D, 108 Tshopo) —
    # en dernier : ailleurs, « reçus » sans « analysés » compte des échantillons pas encore testés
    re.compile(r"(\d[\d ]{0,6}\d|\d)\s*(?:nouveaux\s+)?[ée]chantillons\s+ont\s+[ée]t[ée]\s+re[çc]us\b(?=[^.]*(?:positi|n[ée]gati))", re.I),
]
POSITIFS_RES = [
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s*(?:nouveaux?\s+)?r[ée]sultats?\s+positifs?", re.I),
    re.compile(r"dont\s+(\d[\d ]{0,4}\d|\d)\s*(?:nouveaux\s+cas\s+)?positifs?", re.I),
    re.compile(r"a\s+confirm[ée]\s+(\d[\d ]{0,4}\d|\d)\s+(?:nouveaux\s+)?cas", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+cas\s+confirm[ée]s\s+sur", re.I),
    re.compile(r"(\d+)\s+(?:est|sont)\s+revenus?\s+positifs?", re.I),
    re.compile(r"soit\s+(\d[\d ]{0,4}\d|\d)\s+positifs?", re.I),
    re.compile(r"parmi\s+lesquels\s+(\d[\d ]{0,4}\d|\d)\s+positifs?", re.I),
    re.compile(r"confirmant\s+(\d[\d ]{0,4}\d|\d)\s+nouveaux\s+cas", re.I),
    re.compile(r"\bn\s*=\s*(\d+)", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+positifs?\b", re.I),
]
NOUVEAUX_CAS_RE = re.compile(r"dont\s+(\d+)\s+nouveaux\s+cas", re.I)
VIVANTS_DECES_RE = re.compile(r"\((\d+)\s*vivants?\s+et\s+(\d+)\s*d[ée]c[èe]s\)", re.I)
POSITIVITE_RE = re.compile(r"positivit[ée][^%\d\n]{0,30}?(\d+(?:[,.]\d+)?)\s*%", re.I)
NEGATIFS_RE = re.compile(r"n[ée]gatifs?\b|aucun[^.;\n]{0,30}?positif", re.I)
RECUS_TESTES_SUR_RE = re.compile(
    r"(\d[\d ]{0,4}\d|\d)\s*[ée]chantillons\s+re[çc]us\s+et\s+test[ée]s\s*"
    r"\((\d+)\s*vivants?\s+et\s+(\d+)\s*d[ée]c[èe]s\)\s*sur\s+(\d[\d ]{0,6}\d|\d)\s*[ée]chantillons\s+analys[ée]s", re.I)
TOUS_POSITIFS_RE = re.compile(r"(?:s[’']est\s+r[ée]v[ée]l[ée]\s+positif\b|tous\s+se\s+sont\s+r[ée]v[ée]l[ée]s\s+positifs|tous\s+(?:sont\s+)?revenus\s+positifs)", re.I)


def candidats(regexes, texte):
    """Tous les nombres que les motifs trouvent, dans l'ordre des motifs."""
    out = []
    for rx in regexes:
        for m in rx.finditer(texte):
            v = entier(m.group(1))
            if v is not None and v not in out:
                out.append(v)
    return out


def choisir(cands_e, cands_p, positivite):
    """Le couple (échantillons, positifs) que la positivité publiée désigne.

    Un bulletin peut écrire « 132 échantillons reçus, dont 47 analysés à Beni
    (3 positifs) et 85 à Butembo (15 positifs), soit 18 positifs et une
    positivité de 13,6 % » : quatre nombres candidats, un seul couple qui
    donne 13,6 % — 18 sur 132. Sans positivité publiée, le premier motif
    l'emporte, dans l'ordre où ils sont écrits (du plus spécifique au moins
    spécifique)."""
    e = cands_e[0] if cands_e else None
    p = cands_p[0] if cands_p else None
    if positivite is None or not cands_e or not cands_p:
        return e, p
    meilleur = None
    for ce in cands_e:
        for cp in cands_p:
            if ce <= 0 or cp > ce:
                continue
            ecart = abs(cp / ce * 100 - positivite)
            if meilleur is None or ecart < meilleur[0]:
                meilleur = (ecart, ce, cp)
    if meilleur and meilleur[0] <= 1.5:
        return meilleur[1], meilleur[2]
    return e, p


# Un morceau s'arrête avant un cumul (« cumul 238 analysés, 3 positifs »),
# une synthèse (« Au total, 516 échantillons… ») ou un paragraphe de
# commentaire : ces nombres ne sont pas ceux de la journée.
COUPURE_RE = re.compile(r"\bcumul\b|\bAu total\b|\n(?=(?:Les |La |Le |Dans |FIGURE|TABLEAU|Figure|\d+\.\d))", re.I)


def lire_province(morceau):
    """Les nombres d'un morceau de section consacré à une province."""
    c = COUPURE_RE.search(morceau)
    if c:
        morceau = morceau[:c.start()]
    # « sur l'échantillon analysé » (119, Sud-Ubangi) : un seul, sans chiffre
    morceau = re.sub(r"\bl[’']\s*([ée]chantillon\s+(?:re[çc]u\s+et\s+)?analys[ée]\b)", r"1 \1", morceau, flags=re.I)
    mp = POSITIVITE_RE.search(morceau)
    positivite = pourcent(mp.group(1)) if mp else None
    echantillons, positifs = choisir(candidats(ECHANTILLONS_RES, morceau),
                                     candidats(POSITIFS_RES, morceau), positivite)
    # « Nord-Kivu : 21 échantillons reçus et testés (14 vivants et 7 décès) sur
    # 160 échantillons analysés (positivité de 13,1%) » (124, 15 septembre
    # 2026) : le bulletin a ecrit « échantillons reçus et testés » la ou il
    # ecrivait « nouveaux résultats positifs » la veille. Les 21 sont les
    # positifs — 14 vivants et 7 deces font 21, et 21 sur 160 font 13,1 % —,
    # les 160 les analyses. Lu tel quel, le Nord-Kivu passait a 21 echantillons
    # sans positif, et le total du jour a null. Le motif ne joue que si les
    # deux verifications tombent juste.
    mr = RECUS_TESTES_SUR_RE.search(morceau)
    if mr:
        n, total = int(re.sub(r"\D", "", mr.group(1))), int(re.sub(r"\D", "", mr.group(4)))
        if int(mr.group(2)) + int(mr.group(3)) == n and total >= n and (
                positivite is None or abs(n / total * 100 - positivite) <= 0.15):
            echantillons, positifs = total, n
    if positifs is None and NEGATIFS_RE.search(morceau):
        positifs = 0
    # « 1 échantillon reçu et testé (1 vivant), s'est révélé positif » (120,
    # Bas-Uélé et Tshopo), « 3 échantillons reçus et testés (vivants) tous se
    # sont révélés positifs » (121, Tshopo) : tous positifs, le nombre est
    # celui des échantillons. Sans cela le total du jour restait à null et le
    # garde-fou « positifs = nouveaux cas » ne pouvait pas jouer (14 septembre 2026).
    if positifs is None and echantillons and TOUS_POSITIFS_RE.search(morceau):
        positifs = echantillons
    # « le résultat est revenu positif » : un seul échantillon, pas de chiffre
    if positifs is None and re.search(r"le\s+r[ée]sultat\s+est\s+revenu\s+positif", morceau, re.I):
        positifs = 1
    if positifs is None and positivite == 0:
        positifs = 0
    # « 1 nouveau résultat positif sur 4 échantillons (positivité 25 %) » se lit
    # en clair ; mais un bulletin peut ne donner que « 4 échantillons analysés
    # (positivité 25 %) ». Le produit des deux nombres publiés est alors un
    # entier sans ambiguïté : on le retient, en le marquant, plutôt que de
    # perdre le total du jour pour une province à quatre échantillons.
    deduit = False
    if positifs is None and positivite is not None and echantillons:
        brut = echantillons * positivite / 100
        if abs(brut - round(brut)) < 0.05:
            positifs, deduit = int(round(brut)), True
    nouveaux = NOUVEAUX_CAS_RE.search(morceau)
    m = VIVANTS_DECES_RE.search(morceau)
    vivants, deces = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    if echantillons is None and positifs is None:
        return None
    ligne = {"echantillons": echantillons, "positifs": positifs}
    if deduit:
        ligne["positifsDeduits"] = True
    if nouveaux:
        # Positifs = nouveaux cas + réprélèvements : les seconds ne sont pas des
        # cas. On garde les deux, le graphique ne trace que les nouveaux.
        ligne["nouveauxCas"] = int(nouveaux.group(1))
    if vivants is not None:
        ligne["vivants"], ligne["deces"] = vivants, deces
    if positivite is not None:
        ligne["positivite"] = positivite
    return ligne


def avertissements(nom, ligne):
    """Les invariants de la source elle-même, vérifiés ligne par ligne."""
    out = []
    e, p, pv = ligne.get("echantillons"), ligne.get("positifs"), ligne.get("positivite")
    if e is not None and p is not None and p > e:
        out.append("%s : %d positifs pour %d échantillons" % (nom, p, e))
    if e and p is not None and pv is not None:
        calc = round(p / e * 100, 1)
        if abs(calc - pv) > 1.5:
            out.append("%s : positivité publiée %s %%, recalculée %s %%" % (nom, pv, calc))
    return out


NATIONAL_RE = re.compile(
    r"(\d[\d ]{0,6}\d|\d)\s*[ée]chantillons\s+ont\s+[ée]t[ée]\s+analys[ée]s\s*,?\s*confirmant\s+"
    r"(\d[\d ]{0,4}\d|\d)\s+nouveaux\s+cas[^%]{0,60}?(\d+(?:[,.]\d+)?)\s*%", re.I | re.S)


# ---------------------------------------------------------------------------
# REPLI « POINT DU JOUR » (22 septembre 2026)
#
# Dix-neuf rapports ne donnaient rien : leur section laboratoire existe, mais
# elle ne porte ni la phrase nationale ni un tableau par province — les
# bulletins de la fin mai tiennent le point dans un tableau « Indicateurs
# clés » à une ou deux colonnes (jour, cumul), et deux rapports le disent en
# toutes lettres. Sept journées manquaient au graphique pour cette seule
# raison de forme.
#
# Ce repli ne s'exécute QUE si la lecture normale n'a rien rendu : les 102
# journées déjà extraites ne peuvent pas changer.
#
# LA REGLE DE SURETE. Un tableau a deux colonnes colle ses nombres —
# « Nbre d'echantillons analyses 3 648 » vaut 3 puis 648, et non 3 648, ce
# qu'aucun motif ne peut trancher seul. On lit donc les deux hypotheses et on
# ne garde que celle dont le rapport positifs/analyses retombe sur le taux
# imprime a 0,3 point pres. Sans taux imprime, on n'accepte que les lectures
# sans ambiguite : un seul nombre de chaque cote.
# ---------------------------------------------------------------------------

JOUR_NOMBRE_RE = r"(\d[\d  \u202f\u00a0]*\d|\d)"

JOUR_ANALYSES_RES = [re.compile(motif, re.I) for motif in [
    r"chantillons?\s+analys[ée]s?\s+du\s+jour\s*:?\s*" + JOUR_NOMBRE_RE,
    r"Nbre\s+d.[ée]chantillons?\s+analys[ée]s?\s+" + JOUR_NOMBRE_RE,
    r"[•\-]\s*[ÉE]chantillons?\s+analys[ée]s?\s*:?\s*" + JOUR_NOMBRE_RE,
    r"[ÉE]chantillons?\s+analys[ée]s?\s+" + JOUR_NOMBRE_RE + r"\s+\d+[,.]\d+\s*%",
    JOUR_NOMBRE_RE + r"\s+nouveaux\s+[ée]chantillons?\s+ont\s+[ée]t[ée]\s+collect[ée]s\s+et\s+analys[ée]s",
]]
JOUR_POSITIFS_RES = [re.compile(motif, re.I) for motif in [
    r"Positifs?\s+du\s+jour\s*:?\s*" + JOUR_NOMBRE_RE,
    r"Nbre\s+des?\s+cas\s+positifs\s+" + JOUR_NOMBRE_RE,
    r"[ÉE]chantillons?\s+positifs\s+" + JOUR_NOMBRE_RE + r"\s+Taux",
    JOUR_NOMBRE_RE + r"\s+sont\s+revenus?\s+positifs",
]]
# « Taux de positivité 0 19,2% » : le premier nombre est celui du jour.
JOUR_TAUX_COLONNE_RE = re.compile(r"[Tt]aux\s+de\s+positivit[ée]\s+(\d+)\s+\d+[,.]\d+\s*%")
JOUR_TAUX_RES = [re.compile(motif, re.I) for motif in [
    r"[Tt]aux\s+de\s+positivit[ée]\s*:?\s*(\d+[,.]\d+)\s*%",
    r"positivit[ée]\s+(?:de\s+)?(\d+[,.]\d+)\s*%",
    r"\((\d+[,.]\d+)\s*%\s*de\s+taux",
]]
# « — Ituri : 203 échantillons analysés — 27 positifs (positivité 13,3 %) »
JOUR_PROVINCE_PHRASE_RE = re.compile(
    r"(%s)\s*:\s*" % PROVINCES_RE + JOUR_NOMBRE_RE +
    r"\s+[ée]chantillons?\s+analys[ée]s?[^—\n]*—\s*" + JOUR_NOMBRE_RE +
    r"\s+positifs?\s*\(positivit[ée]\s+(\d+[,.]\d+)\s*%", re.I)


def _lectures(brut):
    """« 3 648 » vaut 3648, ou 3 suivi de 648 : les deux sont rendues."""
    valeurs = [entier(brut)]
    morceaux = re.split(r"[  \u202f\u00a0]+", brut.strip())
    if len(morceaux) == 2:
        valeurs.append(entier(morceaux[0]))
    return [v for v in valeurs if v is not None]


def _candidats(motifs, section):
    for motif in motifs:
        trouve = motif.search(section)
        if trouve:
            return _lectures(trouve.group(1))
    return []


def _taux_imprime(section):
    jour = JOUR_TAUX_COLONNE_RE.search(section)
    if jour:
        return float(jour.group(1))
    for motif in JOUR_TAUX_RES:
        trouve = motif.search(section)
        if trouve:
            return float(trouve.group(1).replace(",", "."))
    return None


def point_du_jour(section):
    """Les analyses et les positifs du jour, quand la section ne tient ni
    phrase nationale ni tableau par province. Rend None des qu'un doute
    subsiste : une journee absente vaut mieux qu'une journee fausse."""
    analyses, positifs = _candidats(JOUR_ANALYSES_RES, section), _candidats(JOUR_POSITIFS_RES, section)
    if not analyses or not positifs:
        return None
    taux = _taux_imprime(section)
    if taux:
        # Un taux nul ne departage rien : 0 positif sur 3 analyses et 0 sur
        # 3 648 valent tous deux 0 %. Le 27 mai, « Nbre d'echantillons
        # analyses 3 648 » serait passe pour 3 648 analyses. On n'accepte
        # donc un taux comme arbitre que s'il est non nul, et le jour
        # ambigu reste dehors.
        valides = [(a, p) for a in analyses for p in positifs
                   if a and abs(round(p / a * 100, 1) - taux) <= 0.3]
        if len(valides) == 1:
            a, p = valides[0]
            return {"echantillons": a, "positifs": p,
                    "positivite": round(p / a * 100, 1)}
        if len(valides) > 1:
            return None
    if len(analyses) == 1 and len(positifs) == 1 and analyses[0]:
        return {"echantillons": analyses[0], "positifs": positifs[0],
                "positivite": round(positifs[0] / analyses[0] * 100, 1)}
    return None


def provinces_redigees(section):
    """Le point par province quand il est ecrit en toutes lettres plutot que
    dispose en tableau. Le taux imprime valide chaque ligne."""
    lues = {}
    for m in JOUR_PROVINCE_PHRASE_RE.finditer(section):
        nom = canon(m.group(1))
        ech, pos = entier(m.group(2)), entier(m.group(3))
        taux = float(m.group(4).replace(",", "."))
        if nom and ech and abs(round(pos / ech * 100, 1) - taux) <= 0.3:
            lues[nom] = {"echantillons": ech, "positifs": pos, "positivite": taux}
    return lues


def lire_rapport(chemin):
    texte = texte_du_rapport(chemin)
    meta = extract_meta(texte, fallback_number=numero(chemin))
    section = section_laboratoire(texte)
    if not section or not meta.get("reportingDate"):
        return None, []
    national = None
    mn = NATIONAL_RE.search(section)
    if mn:
        national = {"echantillons": entier(mn.group(1)), "positifs": entier(mn.group(2)),
                    "positivite": pourcent(mn.group(3))}
    reperes = list(REPERE_RE.finditer(section))
    provinces = {}
    alertes = []
    for i, m in enumerate(reperes):
        nom = canon(m.group(1))
        fin = reperes[i + 1].start() if i + 1 < len(reperes) else len(section)
        morceau = section[m.end():fin]
        ligne = lire_province(morceau)
        if ligne is None or nom in provinces:
            continue
        alertes.extend(avertissements(nom, ligne))
        provinces[nom] = ligne
    if not provinces:
        # Repli : le point ecrit en toutes lettres, province par province.
        provinces = provinces_redigees(section)
    jour = None
    if not provinces and not national:
        # Repli : le tableau « Indicateurs cles » de la fin mai, sans detail
        # par province — le laboratoire de Bunia y porte alors l'essentiel de
        # l'activite, l'epidemie n'ayant pas encore quitte l'Ituri.
        jour = point_du_jour(section)
        if jour is None:
            return None, []
    # Le total n'est une somme que si chaque province lue porte le nombre :
    # une province dont on ne connaît que la positivité laisserait un trou
    # qu'une somme partielle ferait passer pour un chiffre.
    total = {"provinces": len(provinces)}
    for cle in ("echantillons", "positifs"):
        valeurs = [p.get(cle) for p in provinces.values()]
        total[cle] = sum(valeurs) if valeurs and all(v is not None for v in valeurs) else None
    if jour is not None:
        # Le point du jour tient lieu de total : il n'y a pas de province a
        # sommer, le bulletin ne les distingue pas encore.
        total["echantillons"], total["positifs"] = jour["echantillons"], jour["positifs"]
    if total["echantillons"] and total["positifs"] is not None:
        total["positivite"] = round(total["positifs"] / total["echantillons"] * 100, 1)
    if any("nouveauxCas" in p for p in provinces.values()):
        total["nouveauxCas"] = sum(p.get("nouveauxCas", p.get("positifs") or 0) for p in provinces.values())
    point = {
        "date": meta["reportingDate"],
        "sitrepNumber": meta["sitrepNumber"],
        "provinces": provinces,
        "total": total,
        # La provenance est tracee : « point du jour » signale une lecture
        # obtenue par le repli, sans detail par province.
        "source": "SitRep INSP (point du jour)" if jour is not None else "SitRep INSP (automatique)",
    }
    if national:
        point["national"] = national
        if total["positifs"] is not None and national["positifs"] is not None \
                and total.get("nouveauxCas", total["positifs"]) != national["positifs"]:
            alertes.append("somme des provinces %s ≠ national %s (positifs)"
                           % (total.get("nouveauxCas", total["positifs"]), national["positifs"]))
    return point, alertes


def main():
    points = []
    alertes = []
    sans = []
    for chemin in rapports():
        try:
            point, av = lire_rapport(chemin)
        except Exception as e:  # un PDF illisible ne doit pas arrêter les autres
            print("  ! %s : %s" % (os.path.basename(chemin), e))
            continue
        if point is None:
            sans.append(numero(chemin))
            continue
        alertes.extend("%s : %s" % (point["sitrepNumber"], a) for a in av)
        points.append(point)

    # Une valeur par date, la dernière lue l'emporte (ordre des numéros).
    par_date = {}
    for p in points:
        par_date[p["date"]] = p
    final = sorted(par_date.values(), key=lambda p: p["date"])

    sortie = {
        "periode": {"debut": final[0]["date"], "fin": final[-1]["date"]} if final else None,
        "parDate": final,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(sortie, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print("%s écrit : %d date(s), du %s au %s" % (
        os.path.relpath(OUTPUT_PATH, ROOT), len(final),
        final[0]["date"] if final else "-", final[-1]["date"] if final else "-"))
    print("Rapports sans section laboratoire lisible (%d) : %s" % (len(sans), ", ".join(sans)))
    if alertes:
        print("\n%d avertissement(s) :" % len(alertes))
        for a in alertes:
            print("  - " + a)


if __name__ == "__main__":
    main()
