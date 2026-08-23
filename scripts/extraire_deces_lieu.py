#!/usr/bin/env python3
"""
Repartition des deces confirmes entre deces survenus en communaute et deces
survenus en centre de traitement, province par province.

POURQUOI UN NOUVEAU SCRIPT

extract_community_deaths.py existe deja, mais il ne retient qu'une province :
l'Ituri, sur 30 jours. Il valide une ligne en la reconciliant avec d'autres
chiffres du bulletin, et cette reconciliation echoue partout ailleurs.

Ici la validation est locale. Le bulletin imprime, sur une meme ligne :

    Ituri   4572   2043   44,7%   62   17   17   34
            cas   deces  letalite  nouv  comm  intra  total

La ligne n'est retenue que si comm + intra == total, c'est-a-dire si le
bulletin est d'accord avec lui-meme sur cette ligne-la. Chaque province se
controle alors independamment des autres, et six provinces passent au lieu
d'une.

CE QUE LA DONNEE PERMET, ET CE QU'ELLE NE PERMET PAS

Les quatre colonnes n'apparaissent qu'a partir du 13 juillet 2026 : les
epoques A (15 bulletins) et B (39 bulletins) ne distinguent pas le lieu du
deces, et aucune extraction ne creera cette information. La fenetre est donc
bornee, et le site doit le dire.

Le total national n'est PAS publie : sur 32 dates, la somme des provinces
retrouve la variation du cumul national 20 fois. Les 12 ecarts sont soit les
deux dates de rattrapage administratif (22 et 30 juillet), soit des journees
ou une seule province a ete captee, soit les contradictions internes des
bulletins. Un chiffre par province se defend ; leur somme, non.

Usage : python scripts/extraire_deces_lieu.py
"""
import glob
import io
import json
import os
import re
import sys

import pdfplumber

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from update_data import extract_meta, extract_number_from_filename  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "data", "deces-lieu.json")

# Les bulletins ecrivent tantot « Haut-Uele », tantot « Haut Uele ».
NOMS = {
    "Ituri": "Ituri",
    "Nord-Kivu": "Nord-Kivu",
    "Nord Kivu": "Nord-Kivu",
    "Haut-Uélé": "Haut-Uélé",
    "Haut Uélé": "Haut-Uélé",
    "Tshopo": "Tshopo",
    "Sud-Kivu": "Sud-Kivu",
    "Sud Kivu": "Sud-Kivu",
    "Bas-Uélé": "Bas-Uélé",
    "Bas Uélé": "Bas-Uélé",
}

LIGNE_PROVINCE = re.compile(
    r"\b(%s)\s+([\d ]{1,7})\s+([\d ]{1,6})\s+([\d,]+)\s*%%\s+"
    r"(\d{1,4})\s+(\d{1,4})\s+(\d{1,4})\s+(\d{1,4})\b" % "|".join(NOMS)
)


def entier(brut):
    return int(str(brut).replace(" ", "").replace(" ", ""))


def lignes_du_rapport(texte):
    """Les lignes province auto-coherentes de ce bulletin, ou {} s'il n'en a pas.

    Trois controles, et il en faut trois. Les bulletins de l'epoque C sont mis
    en page sur deux colonnes : quand une province n'a rien a declarer, ses
    cases de droite sont vides, et le texte extrait colle sur sa ligne des
    chiffres appartenant a une autre colonne de la page. Vu au 13 juillet :

        Sud-Kivu 3 1 33,3 % 47 8 14 22

    8 + 14 = 22, donc le controle d'addition passe — et pourtant c'est faux :
    le Sud-Kivu compte 3 cas et 1 deces au total depuis le debut. Les deux
    invariants qui suivent l'attrapent : on ne peut pas notifier 47 nouveaux
    cas dans une province qui en compte 3, ni 22 deces du jour quand le cumul
    en affiche 1.
    """
    trouvees = {}
    for m in LIGNE_PROVINCE.finditer(texte):
        province = NOMS[m.group(1)]
        cas_cumul, deces_cumul = entier(m.group(2)), entier(m.group(3))
        nouveaux = entier(m.group(5))
        communautaires, intra, total = (entier(m.group(6)), entier(m.group(7)),
                                        entier(m.group(8)))
        # 1. Le bulletin doit etre d'accord avec lui-meme sur cette ligne.
        if communautaires + intra != total:
            continue
        # 2. Le jour ne peut pas depasser le cumul dont il fait partie.
        if nouveaux > cas_cumul or total > deces_cumul:
            continue
        # 3. Premiere occurrence seulement : la meme province peut reapparaitre
        #    plus loin (recapitulatifs, annexes) avec d'autres colonnes.
        trouvees.setdefault(province, (communautaires, intra, deces_cumul))
    return trouvees


def main():
    fichiers = sorted(glob.glob(os.path.join(RACINE, "reports", "SITREP_MVE_*.pdf")))
    par_date, sans, erreurs = {}, [], []
    for chemin in fichiers:
        numero = extract_number_from_filename(chemin)
        try:
            with pdfplumber.open(chemin) as pdf:
                texte = "\n".join(p.extract_text() or "" for p in pdf.pages)
            meta = extract_meta(texte, fallback_number=numero)
        except Exception as exc:                                  # noqa: BLE001
            erreurs.append((numero, str(exc)[:70]))
            continue
        date = meta.get("reportingDate")
        lignes = lignes_du_rapport(re.sub(r"\s+", " ", texte))
        if not date or not lignes:
            sans.append(numero)
            continue
        par_date[date] = {"sitrep": numero,
                          "provinces": {p: {"communautaires": v[0], "intraCte": v[1]}
                                        for p, v in sorted(lignes.items())},
                          # Hors JSON publie : sert au calcul de couverture.
                          "_cumul": {p: v[2] for p, v in lignes.items()}}

    if not par_date:
        sys.exit("Aucune ligne exploitable : le format a peut-etre change.")

    # Agregat par province sur toute la fenetre.
    cumul = {}
    for date in sorted(par_date):
        jour = par_date[date]
        for province, v in jour["provinces"].items():
            c = cumul.setdefault(province, {"communautaires": 0, "intraCte": 0,
                                            "releves": 0, "premier": None, "dernier": None})
            c["communautaires"] += v["communautaires"]
            c["intraCte"] += v["intraCte"]
            c["releves"] += 1
            dc = jour["_cumul"].get(province)
            if dc is not None:
                if c["premier"] is None:
                    # Le cumul AVANT la premiere journee classee : on retire
                    # les deces de ce jour-la, qui sont deja comptes.
                    c["premier"] = dc - (v["communautaires"] + v["intraCte"])
                c["dernier"] = dc
    # En deca de ce volume, une part n'est pas un signal : le Bas-Uele affiche
    # 100 % de deces communautaires sur UN deces, la Tshopo 66,7 % sur trois.
    # Ces provinces restent dans le fichier — le site les cite en note — mais
    # elles ne prennent pas une barre a cote de l'Ituri et ses 1 040 deces.
    SEUIL_LISIBILITE = 20

    provinces = []
    for province, c in cumul.items():
        total = c["communautaires"] + c["intraCte"]
        provinces.append({
            "name": province,
            "communautaires": c["communautaires"],
            "intraCte": c["intraCte"],
            "total": total,
            # Arrondi a une decimale : au-dela on afficherait une precision que
            # 22 deces ne portent pas.
            "partCommunautaire": round(c["communautaires"] / total * 100, 1) if total else None,
            "releves": c["releves"],
            "assezDeVolume": total >= SEUIL_LISIBILITE,
            # Part des deces de la fenetre que ces colonnes classent. Le reste
            # tombe soit sur les deux dates de rattrapage administratif, soit
            # sur des journees ou le bulletin laisse les colonnes vides.
            "couverture": (round(total / (c["dernier"] - c["premier"]) * 100)
                           if c["dernier"] is not None and c["premier"] is not None
                           and c["dernier"] > c["premier"] else None),
        })
    provinces.sort(key=lambda p: -(p["partCommunautaire"] or 0))

    dates = sorted(par_date)
    sortie = {
        "periode": {"debut": dates[0], "fin": dates[-1]},
        "releves": len(dates),
        "seuilLisibilite": SEUIL_LISIBILITE,
        "provinces": provinces,
        # Conserve pour une eventuelle lecture hebdomadaire : c'est le meme
        # fichier, pas une seconde extraction a refaire.
        "parDate": [{"date": d, "sitrep": par_date[d]["sitrep"],
                     "provinces": par_date[d]["provinces"]} for d in dates],
    }
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    with io.open(SORTIE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sortie, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print("%d releve(s) exploitable(s), du %s au %s" % (len(dates), dates[0], dates[-1]))
    print("%d bulletin(s) sans ces colonnes (attendu avant le 13 juillet)" % len(sans))
    if erreurs:
        print("%d erreur(s) de lecture : %s" % (len(erreurs), erreurs[:3]))
    print()
    print("%-12s %8s %8s %9s %9s %11s  %s"
          % ("province", "comm.", "intra", "part", "releves", "couverture", "affichee"))
    for p in provinces:
        print("%-12s %8d %8d %8s %9d %10s  %s"
              % (p["name"], p["communautaires"], p["intraCte"],
                 "%.1f %%" % p["partCommunautaire"] if p["partCommunautaire"] is not None else "—",
                 p["releves"],
                 "%d %%" % p["couverture"] if p["couverture"] is not None else "—",
                 "oui" if p["assezDeVolume"] else "non (volume trop faible)"))
    print()
    print("ecrit dans", os.path.relpath(SORTIE, RACINE))


if __name__ == "__main__":
    main()
