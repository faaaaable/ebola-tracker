# -*- coding: utf-8 -*-
"""Cartographie le corpus gele : epoque editoriale, sections, metadonnees.

Le corpus n'a pas un format mais quatre, qui se succedent dans le temps. Un
extracteur ecrit pour l'un ne trouve rien dans les autres — silencieusement.
Cette carte existe pour que chaque extracteur puisse ensuite declarer les
epoques qu'il sait traiter, et que tout le reste soit marque « non couvert »
plutot qu'absent. C'est la difference entre une lacune connue et une lacune
invisible.

    python scripts/cartographier_corpus.py

Sortie : data/corpus/carte.json
"""
import io
import json
import glob
import os
import re
import unicodedata
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "data", "corpus", "textes")
CARTE = os.path.join(ROOT, "data", "corpus", "carte.json")

MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10,
        "novembre": 11, "decembre": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
        "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
        "november": 11, "december": 12}

# Un titre de section : « 1.4. Laboratoire », « 3.2 Repartition par zone ».
TITRE = re.compile(r'^[ \t]*(\d{1,2}(?:\.\d{1,2}){1,2})\.?[ \t]+'
                   r'([^\d\n][^\n]{2,70})$', re.M)
RAPPORTAGE = re.compile(r'[Dd]ate de rapportage\s*:?\s*(\d{1,2})\s+([A-Za-zéûôàè]+)\s+(\d{4})')
PUBLICATION = re.compile(r'[Dd]ate de publication\s*:?\s*(\d{1,2})\s+([A-Za-zéûôàè]+)\s+(\d{4})')
REF_SITREP = re.compile(r'SitRep\s*N\s*[°ºo]?\s*(\d{1,3})', re.I)
AS_OF = re.compile(r'[Aa]s of\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})')


def sans_accent(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def date_iso(jour, mois, annee):
    m = MOIS.get(sans_accent(mois).lower())
    return "%s-%02d-%02d" % (annee, m, int(jour)) if m else None


def epoque(niveaux, nb_tableaux):
    """Regime editorial, deduit de la numerotation des titres.

    Les piliers (Coordination, Surveillance, Laboratoire...) sont numerotes
    4.x, puis 3.x, puis 1.x selon la periode : la presence d'un niveau 4 est
    donc le marqueur le plus sur de l'epoque B, et ainsi de suite.

    Trois rapports (059 a 061) ouvrent l'epoque C avec des titres que le motif
    ne reconnait pas — mise en forme differente sur ces numeros-la. Ils sont
    rattrapes par la densite de tableaux, qui est le signe structurel de cette
    epoque : elle triple, passant d'une vingtaine a une soixantaine de
    tableaux par rapport.
    """
    if 4 in niveaux:
        return "B"
    if 2 in niveaux and 3 in niveaux:
        return "C"
    if 1 in niveaux and not (2 in niveaux or 3 in niveaux):
        return "D"
    if nb_tableaux >= 50:
        return "C"
    if not niveaux:
        return "A"
    return "?"


def signature(grille):
    """Empreinte d'un tableau : ses en-tetes normalises.

    Deux tableaux de deux rapports differents qui portent la meme signature
    sont le meme tableau — c'est ce qui permet de compter sur combien de
    rapports chaque type de tableau existe.
    """
    if not grille:
        return ""
    tete = []
    for cellule in grille[0]:
        t = sans_accent((cellule or "").replace("\n", " ")).lower()
        t = re.sub(r'[^a-z0-9%]+', " ", t).strip()
        t = re.sub(r'\d+', "#", t)
        if t:
            tete.append(t[:34])
    return " | ".join(tete)


def cartographier(doc):
    texte = "\n".join(p["texte"] for p in doc["pages"])
    page_de = []          # (offset de debut, numero de page)
    curseur = 0
    for p in doc["pages"]:
        page_de.append((curseur, p["page"]))
        curseur += len(p["texte"]) + 1

    def page_pour(offset):
        n = 1
        for debut, num in page_de:
            if debut <= offset:
                n = num
            else:
                break
        return n

    sections, vus = [], set()
    for m in TITRE.finditer(texte):
        cle = m.group(1)
        if cle in vus:
            continue
        vus.add(cle)
        sections.append({
            "numero": cle,
            "titre": re.sub(r'\s+', " ", m.group(2)).strip()[:80],
            "page": page_pour(m.start()),
        })
    sections.sort(key=lambda s: [int(x) for x in s["numero"].split(".")])
    niveaux = {int(s["numero"].split(".")[0]) for s in sections}

    fiche = {
        "id": doc["id"],
        "source": doc["source"],
        "fichier": doc["fichier"],
        "nb_pages": doc["nb_pages"],
        "nb_tableaux": len(doc["tableaux"]),
        "caracteres": sum(len(p["texte"]) for p in doc["pages"]),
        "epoque": (epoque(niveaux, len(doc["tableaux"]))
                   if doc["source"] == "INSP" else "OMS"),
        "niveaux": sorted(niveaux),
        "sections": sections,
        "signatures": [],
    }

    m = RAPPORTAGE.search(texte)
    fiche["date_rapportage"] = date_iso(*m.groups()) if m else None
    m = PUBLICATION.search(texte)
    fiche["date_publication"] = date_iso(*m.groups()) if m else None
    if doc["source"] == "OMS":
        m = AS_OF.search(texte)
        if m:
            fiche["date_rapportage"] = date_iso(*m.groups())
    m = REF_SITREP.search(texte)
    fiche["numero_dans_le_texte"] = m.group(1) if m else None

    for t in doc["tableaux"]:
        sig = signature(t["grille"])
        if sig and len(sig) > 8:
            fiche["signatures"].append({
                "page": t["page"], "lignes": t["lignes"],
                "colonnes": t["colonnes"], "signature": sig,
            })
    return fiche


def main():
    fichiers = sorted(glob.glob(os.path.join(CORPUS, "*.json")))
    if not fichiers:
        raise SystemExit("Corpus vide : lance d'abord scripts/geler_corpus.py")

    fiches = []
    for chemin in fichiers:
        with io.open(chemin, encoding="utf-8") as fh:
            fiches.append(cartographier(json.load(fh)))

    def cle(f):
        return (f["source"] != "INSP", f["id"])
    fiches.sort(key=cle)

    with io.open(CARTE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(fiches, fh, ensure_ascii=False, indent=1)

    insp = [f for f in fiches if f["source"] == "INSP"]
    oms = [f for f in fiches if f["source"] == "OMS"]
    print("%d fiches — %d INSP, %d OMS\n" % (len(fiches), len(insp), len(oms)))

    print("Repartition par epoque")
    for ep, n in sorted(Counter(f["epoque"] for f in insp).items()):
        ids = [f["id"].split("_")[1] for f in insp if f["epoque"] == ep]
        print("  %-3s %3d rapports   %s -> %s" % (ep, n, ids[0], ids[-1]))

    sans_date = [f["id"] for f in fiches if not f["date_rapportage"]]
    print("\nSans date de rapportage : %d %s"
          % (len(sans_date), sans_date[:12] if sans_date else ""))
    sans_section = [f["id"] for f in insp if not f["sections"]]
    print("Sans section numerotee  : %d %s"
          % (len(sans_section), sans_section[:12] if sans_section else ""))
    print("\ncarte : data/corpus/carte.json")


if __name__ == "__main__":
    main()
