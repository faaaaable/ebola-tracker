# -*- coding: utf-8 -*-
"""Les sections « Defis » des bulletins, pilier par pilier, pour la page
« Riposte & defis ».

Depuis l'epoque D (SitRep 084 et suivants), chaque pilier du bulletin porte
une sous-section « x.y.z Defis » en prose : c'est la seule source des
bulletins sur les CAUSES de persistance de l'epidemie — refus d'isolement,
points de controle en greve, sang securise indisponible, zones qui ne
rapportent pas. Le site les cite mot pour mot, rattachees a leur pilier,
sans les reformuler ni les classer : le codage thematique demande un regard
metier, et il ne se fait pas ici.

Lecture : le titre « Defis » (avec ou sans numero devant) ouvre un bloc qui
court jusqu'au titre numerote suivant ou a un intertitre en capitales
(« MESSAGES CLES »). Le pilier est celui du titre numerote qui precede,
en sautant « Principales actions » — la numerotation des bulletins est
capricieuse (« 1.1.3 Defis » sous « 1.1.1 Surveillance epidemiologique »,
« 1.10.4 Defis » sous « 1.10.2 Securite »), on se cale sur le mot, pas sur
le numero. Un bloc se decoupe sur ses puces ; les lignes qui ne sont qu'un
numero de page sont ecartees.

    python scripts/extraire_defis.py

Sortie : data/defis.json — { periode, parDate: [ { date, sitrepNumber,
piliers: [ { pilier, titre, items, provinces } ] } ] }.
"""
import io
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textes_pdf import ROOT, rapports, numero, texte_du_rapport  # noqa: E402
from update_data import extract_meta  # noqa: E402

OUTPUT_PATH = os.path.join(ROOT, "data", "defis.json")
PREMIER_BULLETIN = 84   # epoque D : avant, les defis sont un tableau, non lu ici

PROVINCES = ["Ituri", "Nord-Kivu", "Sud-Kivu", "Haut-Uélé", "Bas-Uélé", "Tshopo"]

# Le pilier d'apres le titre de sa section. Ordre important : « Continuite
# des soins » avant « soins » n'a pas de defis propre ; « Securite » est un
# sous-titre de « Logistique » et doit passer avant lui.
PILIERS = [
    ("surveillance", ["surveillance"]),
    ("poe_poc", ["point de controle", "points de controle", "poe", "poc", "point d entree", "points d entree"]),
    ("laboratoire", ["laboratoire"]),
    ("pci_eds", ["prevention et controle", "pci", "eds"]),
    ("soins", ["prise en charge", "continuite des soins"]),
    ("vaccination", ["vaccination"]),
    ("crec", ["communication", "engagement communautaire"]),
    ("smsps", ["sante mentale", "smsps", "psychosocial"]),
    ("securite", ["securite"]),
    ("logistique", ["logistique"]),
    ("psea", ["psea", "exploitation"]),
    ("coordination", ["coordination"]),
]

TITRE_NUMEROTE = re.compile(r'(?m)^\s*(\d+(?:\.\d+)+)\.?\s+([^\n]{3,140})$')
TITRE_DEFIS = re.compile(r'(?im)^[\s\d.]*d[ée]fis?\s*:?\s*$')
TITRE_CAPITALES = re.compile(r'(?m)^\s*[A-ZÉÈÀÇ][A-ZÉÈÀÇ\s]{7,}$')


def sans_accent(t):
    return "".join(c for c in unicodedata.normalize("NFD", t or "")
                   if unicodedata.category(c) != "Mn")


def propre(t):
    return re.sub(r'\s+', " ", (t or "").replace("\n", " ")).strip()


def pilier_du_titre(titre):
    t = sans_accent(titre).lower().replace("'", " ").replace("’", " ")
    for nom, cles in PILIERS:
        if any(c in t for c in cles):
            return nom
    return "autre"


def provinces_citees(texte):
    t = sans_accent(texte).lower()
    return [p for p in PROVINCES if sans_accent(p).lower().replace("-", " ") in t.replace("-", " ")]


def titre_parent(texte, position):
    """Le dernier titre numerote avant `position` qui n'est ni « Principales
    actions » ni « Defis »."""
    parent = ""
    for m in TITRE_NUMEROTE.finditer(texte, 0, position):
        t = propre(m.group(2))
        bas = sans_accent(t).lower()
        if bas.startswith("principales action") or bas.startswith("defi"):
            continue
        # Une puce ou une phrase entiere n'est pas un titre de section : le
        # 085 collait « 1.10.1 » a la ligne « En Ituri, 29 ambulances... ».
        if t.startswith(("•", "▪")) or len(t.split()) > 14:
            continue
        parent = t
    return parent


def blocs_defis(texte):
    sorties = []
    for m in TITRE_DEFIS.finditer(texte):
        debut = m.end()
        fins = [x.start() for x in (TITRE_NUMEROTE.search(texte, debut),
                                    TITRE_CAPITALES.search(texte, debut)) if x]
        fin = min(fins) if fins else len(texte)
        bloc = texte[debut:fin]
        # Les numeros de page seuls sur leur ligne, et les lignes vides.
        bloc = "\n".join(l for l in bloc.split("\n") if not re.match(r'^\s*\d{1,2}\s*$', l))
        items = []
        for morceau in re.split(r'\n\s*[•▪]\s*|(?<=\.)\n(?=\s*[•▪])', bloc):
            morceau = propre(morceau).lstrip("•▪ ").strip()
            if len(morceau) < 25:
                continue
            items.append(morceau)
        if not items:
            continue
        parent = titre_parent(texte, m.start())
        sorties.append({
            "pilier": pilier_du_titre(parent),
            "titre": parent,
            "items": items,
            "provinces": provinces_citees(" ".join(items)),
        })
    return sorties


def lire_rapport(chemin):
    if int(numero(chemin)) < PREMIER_BULLETIN:
        return None
    texte = texte_du_rapport(chemin)
    meta = extract_meta(texte)
    piliers = blocs_defis(texte)
    if not piliers:
        return {"date": meta["reportingDate"], "sitrepNumber": meta["sitrepNumber"],
                "piliers": [], "source": "SitRep INSP (automatique)"}
    return {"date": meta["reportingDate"], "sitrepNumber": meta["sitrepNumber"],
            "piliers": piliers, "source": "SitRep INSP (automatique)"}


def main():
    points, sans, erreurs = [], [], []
    for chemin in rapports():
        try:
            point = lire_rapport(chemin)
        except Exception as e:  # noqa: BLE001
            erreurs.append("%s : %s" % (os.path.basename(chemin), e))
            continue
        if point is None:
            continue
        if not point["piliers"]:
            sans.append(point["sitrepNumber"])
        points.append(point)
    par_date = {p["date"]: p for p in points}
    final = sorted(par_date.values(), key=lambda p: p["date"])
    sortie = {
        "periode": {"debut": final[0]["date"], "fin": final[-1]["date"]} if final else None,
        "parDate": final,
    }
    with io.open(OUTPUT_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sortie, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    n_blocs = sum(len(p["piliers"]) for p in final)
    print("data/defis.json écrit : %d bulletin(s) du %s au %s, %d bloc(s) « Défis »"
          % (len(final), sortie["periode"]["debut"], sortie["periode"]["fin"], n_blocs))
    if sans:
        print("Bulletins sans section Défis lisible (%d) : %s" % (len(sans), ", ".join(sans)))
    autres = [(p["sitrepNumber"], b["titre"]) for p in final for b in p["piliers"] if b["pilier"] == "autre"]
    if autres:
        print("Piliers non reconnus (%d) : %s" % (len(autres), "; ".join("%s « %s »" % a for a in autres[:12])))
    for e in erreurs:
        print("  ! " + e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
