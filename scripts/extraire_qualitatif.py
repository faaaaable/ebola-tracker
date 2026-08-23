# -*- coding: utf-8 -*-
"""Catalogue le contenu non chiffre : les difficultes de la riposte.

Les sections « Defis » sont la seule source du corpus sur les CAUSES de
persistance de l'epidemie — greves de prestataires impayes, refus de sepulture
securisee, rumeurs, ruptures de stock, zones qui ne rapportent pas. Le reste du
corpus decrit des effets.

Elles prennent deux formes selon l'epoque, et ne pas traiter les deux revient a
perdre les trois quarts du materiau :

  - epoques B et C : un tableau « Defis | Impact | Actions requises » ;
  - epoque D : des sections en prose « x.y.2 Defis » sous chaque pilier.

Rien n'est code en categories fermees ici : chaque difficulte est enregistree
telle qu'elle est ecrite, datee, rattachee a son pilier et aux provinces
qu'elle cite. Le codage thematique demande un regard metier, et il se fera sur
ce fichier — sans jamais rouvrir un PDF.

    python scripts/extraire_qualitatif.py

Sortie : data/corpus/qualitatif.jsonl
"""
import io
import json
import glob
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "data", "corpus", "textes")
CARTE = os.path.join(ROOT, "data", "corpus", "carte.json")
SORTIE = os.path.join(ROOT, "data", "corpus", "qualitatif.jsonl")

PROVINCES = ["Ituri", "Nord-Kivu", "Sud-Kivu", "Haut-Uélé", "Bas-Uélé",
             "Tshopo", "Nord Kivu", "Sud Kivu", "Haut Uélé", "Bas Uélé"]

PILIERS = [
    ("coordination", ["coordination"]),
    ("surveillance", ["surveillance", "alerte", "investigation"]),
    ("laboratoire", ["laboratoire", "echantillon", "positivite"]),
    ("pci_eds", ["pci", "eds", "enterrement", "decontamin", "swab", "ring"]),
    ("soins", ["prise en charge", "continuite des soins", "cte", "hospitalis",
               "lit", "isolement", "ambulance"]),
    ("crec", ["communication", "communautaire", "crec", "rumeur",
              "sensibilis", "engagement"]),
    ("poe_poc", ["poe", "poc", "point d entree", "voyageur"]),
    ("logistique", ["logistique", "intrant", "stock", "carburant", "moto",
                    "vehicule", "approvisionnement"]),
    ("securite", ["securite", "insecurite", "attaque", "escorte"]),
    ("vaccination", ["vaccin", "riposte vaccinale"]),
    ("financement", ["financement", "budget", "paiement", "prime", "salaire",
                     "remuneration", "impaye"]),
    ("rh", ["personnel", "prestataire", "greve", "effectif", "formation"]),
]

# Un intitule de section « Defis », avec ou sans numerotation devant.
TITRE_DEFIS = re.compile(r'(?im)^[\s\d.]*(d[ée]fis?)\s*:?\s*$')
# Le titre de section suivant, qui borne le bloc.
TITRE_SUIVANT = re.compile(r'(?m)^\s*\d\.\d')


def sans_accent(t):
    return "".join(c for c in unicodedata.normalize("NFD", t or "")
                   if unicodedata.category(c) != "Mn")


def pilier(texte):
    t = sans_accent(texte).lower()
    for nom, cles in PILIERS:
        if any(c in t for c in cles):
            return nom
    return "autre"


def provinces_citees(texte):
    t = sans_accent(texte).lower()
    trouvees = []
    for p in PROVINCES:
        cle = sans_accent(p).lower()
        if cle in t and p.split()[0] not in [x.split()[0] for x in trouvees]:
            trouvees.append(p)
    return trouvees


def propre(t):
    return re.sub(r'\s+', " ", (t or "").replace("\n", " ")).strip()


def section_amont(fiche, page, position_titre, texte_avant):
    """Le pilier auquel se rattache un bloc « Defis » : celui du titre qui le
    precede immediatement. « 1.5.2 Defis » depend de « 1.5 PCI/EDS »."""
    titres = re.findall(r'(?m)^\s*(\d\.\d)\.?\s+([^\n]{3,60})$', texte_avant)
    return propre(titres[-1][1]) if titres else ""


ECART_COLONNE = 80        # points ; largeur minimale d'une colonne du tableau


def entete_defis(mots):
    """Abscisses des trois intitules de colonne et ordonnee de la ligne.

    Les mots sont [x0, x1, top, texte]. Piege : le titre de la section,
    « Principaux defis, impacts et actions requises », contient les trois mots
    dans l'ordre et se fait passer pour l'en-tete — mais ses mots se suivent a
    37 points d'intervalle, la ou les vraies colonnes sont espacees d'environ
    150. C'est l'ecart qui les distingue, pas le vocabulaire.
    """
    par_ligne = {}
    for x0, _x1, top, texte in mots:
        par_ligne.setdefault(round(top / 3.0), []).append(
            (x0, top, sans_accent(texte).lower()))
    for _cle, ligne in sorted(par_ligne.items()):
        pos, hauteur = {}, None
        for x0, top, mot in ligne:
            for prefixe, nom in (("defi", "defi"), ("impact", "impact"),
                                 ("action", "action")):
                if mot.startswith(prefixe) and nom not in pos:
                    pos[nom] = x0
                    hauteur = top if hauteur is None else min(hauteur, top)
        if len(pos) < 3:
            continue
        if not pos["defi"] < pos["impact"] < pos["action"]:
            continue
        if (pos["impact"] - pos["defi"] < ECART_COLONNE
                or pos["action"] - pos["impact"] < ECART_COLONNE):
            continue
        return pos, hauteur
    return None, None


def depuis_cadre(doc, ep, date):
    """Epoques B et C : le tableau « Defis | Impact | Actions requises ».

    Ce tableau resiste aux deux lectures textuelles. Par grille, pdfplumber en
    detache l'en-tete puis eclate les cellules. Par rendu spatial, les colonnes
    se chevauchent : une cellule large deborde sous l'intitule de la colonne
    suivante, et la decoupe a l'abscisse de l'intitule tranche les mots en deux
    (« ontinuite des servic »).

    Les coordonnees des mots, elles, sont sans ambiguite : chaque mot appartient
    a la colonne dont l'intitule est le dernier a sa gauche. Les lignes se
    regroupent par ordonnee, et un numero dans la marge ouvre une nouvelle
    difficulte.
    """
    sorties = []
    for page in doc["pages"]:
        mots = page.get("mots") or []
        pos, haut_entete = entete_defis(mots)
        if not pos:
            continue
        x_defi, x_impact, x_action = pos["defi"], pos["impact"], pos["action"]
        # Marge de tolerance : un mot peut commencer legerement avant
        # l'intitule de sa colonne sans appartenir a la precedente.
        bord_impact = x_impact - 6
        bord_action = x_action - 6

        lignes = {}
        for x0, _x1, top, texte in mots:
            # Tout ce qui est au-dessus de l'en-tete, ou sur sa ligne, n'est
            # pas une donnee. Sans cette borne, « Impact » et « Actions
            # requises » se retrouvaient dans le contenu de la premiere
            # difficulte.
            if top <= haut_entete + 2:
                continue
            lignes.setdefault(round(top / 3.0), []).append((x0, texte))

        # Le numero de rang est centre verticalement dans sa cellule, pas pose
        # a son sommet : ouvrir une difficulte a la ligne du numero coupait
        # chaque bloc en son milieu et collait sa fin au debut du suivant. Les
        # frontieres sont donc a mi-chemin entre deux numeros consecutifs.
        numeros = sorted(
            top for cle, ligne in lignes.items()
            for x0, texte in ligne
            if x0 < x_defi - 4 and re.fullmatch(r'\d{1,2}', texte)
            for top in [cle * 3.0])
        bornes = [(a + b) / 2.0 for a, b in zip(numeros, numeros[1:])]

        def rang(hauteur):
            n = 0
            for borne in bornes:
                if hauteur >= borne:
                    n += 1
            return n

        lots = {}
        for cle, ligne in sorted(lignes.items()):
            for x0, texte in sorted(ligne):
                if x0 < x_defi - 4:
                    continue
                cible = ("action" if x0 >= bord_action
                         else "impact" if x0 >= bord_impact else "defi")
                lot = lots.setdefault(rang(cle * 3.0),
                                      {"defi": [], "impact": [], "action": []})
                lot[cible].append(texte)
        lots = [lots[k] for k in sorted(lots)]

        for lot in lots:
            defi = propre(" ".join(lot["defi"]))
            impact = propre(" ".join(lot["impact"]))
            action = propre(" ".join(lot["action"]))
            if len(defi) < 20:
                continue
            sorties.append({
                "rapport": doc["id"], "epoque": ep, "date": date,
                "page": page["page"], "forme": "tableau",
                "pilier": pilier(defi + " " + impact),
                "section": "Defis / Impact / Actions requises",
                "difficulte": defi[:700],
                "impact": impact[:400] or None,
                "action": action[:500] or None,
                "provinces": provinces_citees(defi + " " + impact),
            })
    return sorties


def colonnes_defis(ligne):
    """Position des colonnes Defis / Impact / Actions, ou None."""
    col = {}
    for i, c in enumerate(ligne):
        c = sans_accent(propre(c)).lower()
        if "defi" in c:
            col["defi"] = i
        elif "impact" in c:
            col["impact"] = i
        elif "action" in c:
            col["action"] = i
    return col if "defi" in col else None


def depuis_tableaux(doc, ep, date):
    """Epoques B et C : « Defis | Impact | Actions requises ».

    pdfplumber rend l'en-tete et le corps comme DEUX tableaux distincts : une
    grille d'une seule ligne avec les intitules, puis les lignes de donnees
    sans en-tete. Chercher l'en-tete dans le tableau qu'on lit ne trouvait donc
    que les rares cas ou les deux tiennent ensemble — 14 sur 71.

    On memorise donc les colonnes des que l'en-tete apparait, et on les
    applique aux tableaux suivants de la MEME page.
    """
    sorties = []
    col = None
    page_courante = None
    for t in sorted(doc["tableaux"], key=lambda x: (x["page"], x["index"])):
        grille = t["grille"]
        if not grille:
            continue
        if t["page"] != page_courante:
            page_courante, col = t["page"], None
        for ligne in grille[:2]:
            trouve = colonnes_defis(ligne)
            if trouve:
                col = trouve
                break
        if col is None:
            continue
        entete = colonnes_defis(grille[0]) is not None
        for ligne in (grille[1:] if entete else grille):
            def cell(nom):
                i = col.get(nom)
                return propre(ligne[i]) if i is not None and i < len(ligne) else ""
            defi = cell("defi")
            if len(defi) < 12:
                continue
            # Le report d'en-tete d'un tableau au suivant ramassait aussi les
            # tableaux de realisations places sous le meme intitule de page
            # (« LOGISTIQUE -> Ituri : lancement officiel du CTE... »). Une
            # vraie ligne de defi remplit au moins une des deux colonnes qui
            # n'ont de sens que la : impact ou action requise.
            if not entete and not (cell("impact") or cell("action")):
                continue
            sorties.append({
                "rapport": doc["id"], "epoque": ep, "date": date,
                "page": t["page"], "forme": "tableau",
                "pilier": pilier(defi + " " + cell("impact")),
                "section": "Defis / Impact / Actions requises",
                "difficulte": defi[:600],
                "impact": cell("impact")[:400] or None,
                "action": cell("action")[:400] or None,
                "provinces": provinces_citees(defi + " " + cell("impact")),
            })
    return sorties


def depuis_prose(doc, ep, date):
    """Epoque D : sections « x.y.2 Defis » sous chaque pilier."""
    sorties = []
    for page in doc["pages"]:
        texte = page["texte"]
        for m in TITRE_DEFIS.finditer(texte):
            debut = m.end()
            suite = TITRE_SUIVANT.search(texte, debut)
            bloc = texte[debut:suite.start() if suite else len(texte)]
            parent = section_amont(None, page["page"], m.start(), texte[:m.start()])
            # Uniquement sur les puces et les lignes vides. Decouper aussi sur
            # les debuts de ligne en majuscule tranchait les phrases au milieu,
            # puisque le texte du PDF revient a la ligne tous les 90 signes.
            for morceau in re.split(r'\n\s*[••]\s*|\n{2,}', bloc):
                morceau = propre(morceau)
                morceau = re.sub(r'^\d+\s*', "", morceau).strip()
                if len(morceau) < 40:
                    continue
                sorties.append({
                    "rapport": doc["id"], "epoque": ep, "date": date,
                    "page": page["page"], "forme": "prose",
                    "pilier": pilier(parent + " " + morceau),
                    "section": parent or "Defis",
                    "difficulte": morceau[:900],
                    "impact": None, "action": None,
                    "provinces": provinces_citees(morceau),
                })
    return sorties


def main():
    with io.open(CARTE, encoding="utf-8") as fh:
        carte = {f["id"]: f for f in json.load(fh)}

    sortie = io.open(SORTIE, "w", encoding="utf-8", newline="\n")
    total = 0
    par_forme, par_pilier, par_epoque = {}, {}, {}

    for chemin in sorted(glob.glob(os.path.join(CORPUS, "*.json"))):
        with io.open(chemin, encoding="utf-8") as fh:
            doc = json.load(fh)
        fiche = carte.get(doc["id"], {})
        ep, date = fiche.get("epoque", "?"), fiche.get("date_rapportage")
        for e in depuis_cadre(doc, ep, date) + depuis_prose(doc, ep, date):
            sortie.write(json.dumps(e, ensure_ascii=False) + "\n")
            total += 1
            par_forme[e["forme"]] = par_forme.get(e["forme"], 0) + 1
            par_pilier[e["pilier"]] = par_pilier.get(e["pilier"], 0) + 1
            par_epoque[e["epoque"]] = par_epoque.get(e["epoque"], 0) + 1
    sortie.close()

    print("%d difficultes cataloguees" % total)
    print("\nPar forme");   [print("   %-9s %5d" % kv) for kv in sorted(par_forme.items())]
    print("\nPar epoque");  [print("   %-9s %5d" % kv) for kv in sorted(par_epoque.items())]
    print("\nPar pilier")
    for k, v in sorted(par_pilier.items(), key=lambda x: -x[1]):
        print("   %-14s %5d" % (k, v))
    print("\nsortie : data/corpus/qualitatif.jsonl")


if __name__ == "__main__":
    main()
