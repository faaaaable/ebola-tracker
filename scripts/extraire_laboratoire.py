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

PROVINCES_RE = r"Ituri|Nord[\s-]+Kivu|Haut[\s-]+U[ée]l[ée]|Tshopo|Sud[\s-]+Kivu|Bas[\s-]+U[ée]l[ée]"


def canon(nom):
    """« Haut Uélé », « Haut-Uele », « Haut\nUélé » -> « Haut-Uélé », etc."""
    n = re.sub(r"[\s-]+", " ", nom).replace("Uele", "Uélé").replace("Uelé", "Uélé").replace("Uélè", "Uélé")
    n = {"Nord Kivu": "Nord-Kivu", "Sud Kivu": "Sud-Kivu", "Haut Uélé": "Haut-Uélé"}.get(n, n)
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
    mp = POSITIVITE_RE.search(morceau)
    positivite = pourcent(mp.group(1)) if mp else None
    echantillons, positifs = choisir(candidats(ECHANTILLONS_RES, morceau),
                                     candidats(POSITIFS_RES, morceau), positivite)
    if positifs is None and NEGATIFS_RE.search(morceau):
        positifs = 0
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
    if not provinces and not national:
        return None, []
    # Le total n'est une somme que si chaque province lue porte le nombre :
    # une province dont on ne connaît que la positivité laisserait un trou
    # qu'une somme partielle ferait passer pour un chiffre.
    total = {"provinces": len(provinces)}
    for cle in ("echantillons", "positifs"):
        valeurs = [p.get(cle) for p in provinces.values()]
        total[cle] = sum(valeurs) if valeurs and all(v is not None for v in valeurs) else None
    if total["echantillons"] and total["positifs"] is not None:
        total["positivite"] = round(total["positifs"] / total["echantillons"] * 100, 1)
    if any("nouveauxCas" in p for p in provinces.values()):
        total["nouveauxCas"] = sum(p.get("nouveauxCas", p.get("positifs") or 0) for p in provinces.values())
    point = {
        "date": meta["reportingDate"],
        "sitrepNumber": meta["sitrepNumber"],
        "provinces": provinces,
        "total": total,
        "source": "SitRep INSP (automatique)",
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
