# -*- coding: utf-8 -*-
"""Aplatit tous les tableaux du corpus en cellules nommees.

Plutot que d'ecrire un parseur par type de tableau — il y en a 596 —, on
applique le meme traitement a tous : reperer les lignes d'en-tete, reporter les
cellules fusionnees, puis emettre une ligne par nombre, avec son libelle de
ligne et son en-tete de colonne.

    « Ituri | Cas confirmes | 4 510 »

C'est moins precis qu'un parseur dedie, mais c'est exhaustif, et ca ne demande
aucune decision prealable sur ce qui merite d'etre extrait. Les parseurs dedies
viendront apres, la ou la mesure de couverture montrera que ca vaut le coup.

Deux details qui font la difference entre des donnees justes et des donnees
plausibles :

  - pdfplumber rend None pour une cellule fusionnee ; sans report vers la
    droite, « Nouvelles alertes recues » perdrait ses sous-colonnes Vivants et
    Decedes, et les nombres se retrouveraient sous un en-tete vide ;
  - les en-tetes tiennent sur une, deux ou trois lignes selon les tableaux. On
    les detecte par l'absence de nombres plutot que par une position fixe ;
  - un tableau sur trois est TRANSPOSE : « Indicateurs | Ituri | Nord-Kivu |
    Global » met les lieux en colonnes et les indicateurs en lignes, l'inverse
    du tableau par province. Supposer une seule orientation revenait a nommer
    des indicateurs « ituri » et a fabriquer des series qui n'existent pas.

    python scripts/extraire_cellules.py

Sortie : data/corpus/cellules.jsonl
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
SORTIE = os.path.join(ROOT, "data", "corpus", "cellules.jsonl")

GENERIQUES = {"global", "ensemble", "total", "cumul", "national", "overall",
              "tous", "toutes", "rdc", "drc"}

ESPACES = "    "
CELLULE_NOMBRE = re.compile(r'^-?\d[\d%s]*(?:[.,]\d+)?\s*%%?$' % ESPACES)
UN_CHIFFRE = re.compile(r'\d')


def sans_accent(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def propre(cellule):
    return re.sub(r'\s+', " ", (cellule or "").replace("\n", " ")).strip()


def valeur_de(texte, source):
    """Nombre d'une cellule, avec son unite si elle en porte une."""
    t = propre(texte)
    if not t or not CELLULE_NOMBRE.match(t):
        return None, None
    unite = "pourcentage" if "%" in t else "effectif"
    t = t.rstrip("%").strip()
    for e in ESPACES:
        t = t.replace(e, "")
    try:
        if source == "OMS":
            return float(t.replace(",", "")), unite
        if "," in t:
            return float(t.replace(".", "").replace(",", ".")), unite
        return float(t), unite
    except ValueError:
        return None, None


def cle_lieu(nom):
    """Forme de comparaison d'un nom de lieu.

    Doit etre exactement celle qu'applique est_lieu(), sinon « Nord-Kivu »
    entre dans la reference avec son trait d'union et n'est jamais reconnu
    dans un en-tete, ou il arrive sous la forme « nord kivu ».
    """
    t = sans_accent(nom or "").lower()
    t = re.sub(r'[^a-z ]+', " ", t)
    return re.sub(r'\s+', " ", t).strip()


def lieux_connus():
    """Provinces, zones de sante et agregats.

    Sert a savoir si le dernier etage d'un en-tete designe un lieu — auquel cas
    c'est le sujet de la mesure, pas la mesure.
    """
    with io.open(os.path.join(ROOT, "data", "latest.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    noms = {z["name"] for z in d.get("healthZones", []) if z.get("name")}
    noms |= {p["name"] for p in d.get("provinces", []) if p.get("name")}
    noms |= {"Ituri", "Nord-Kivu", "Sud-Kivu", "Haut-Uélé", "Bas-Uélé",
             "Tshopo", "North Kivu", "South Kivu", "Haut Uele", "Bas Uele"}
    return {cle_lieu(n) for n in noms if cle_lieu(n)} | GENERIQUES


LIEUX = set()


def est_lieu(libelle):
    """Egalite stricte apres normalisation, jamais sous-chaine.

    Le test par sous-chaine classait « Deces confirmes cumules (n) / ITURI »
    comme un lieu, puisqu'il contient « ituri » — et tout le tableau basculait
    du mauvais cote.
    """
    t = cle_lieu(libelle)
    return bool(t) and t in LIEUX


def denoue(entete_colonne, libelle_ligne):
    """Demele ce qui est mesure de ce sur quoi ca l'est.

    Les rapports melangent trois structures, et prendre la mauvaise fabrique
    des indicateurs qui s'appellent « ituri » :

      1. lignes = lieux, colonnes = indicateurs   (tableau par province)
         -> indicateur en colonne, sujet en ligne
      2. lignes = indicateurs, colonnes = lieux   (« Indicateurs | Ituri |... »)
         -> indicateur en ligne, sujet en colonne
      3. en-tete a deux etages, indicateur au-dessus des lieux
         (« Deces confirmes (n) / ITURI ») -> indicateur au-dessus, lieu dessous

    Une seule regle les couvre : si le dernier etage de l'en-tete de colonne
    est un lieu, ce lieu est le sujet, et l'indicateur est ce qui le surmonte —
    ou, s'il n'y a rien au-dessus, le libelle de ligne.
    """
    etages = [e.strip() for e in (entete_colonne or "").split(" / ") if e.strip()]
    if etages and est_lieu(etages[-1]):
        dessus = " / ".join(etages[:-1])
        return (dessus or libelle_ligne), etages[-1], True
    return (entete_colonne or libelle_ligne), libelle_ligne, False


def lignes_entete(grille):
    """Nombre de lignes de tete : les premieres qui ne portent aucun chiffre.

    Plafonne a 3 — au-dela, c'est que le tableau n'a pas d'en-tete du tout et
    qu'on lirait des donnees comme des libelles.
    """
    n = 0
    for ligne in grille[:3]:
        texte = " ".join(propre(c) for c in ligne)
        if texte and not UN_CHIFFRE.search(texte):
            n += 1
        else:
            break
    return n or 1


def entetes_colonnes(grille, nb_tete):
    """Libelle de chaque colonne, cellules fusionnees reportees vers la droite."""
    largeur = max(len(l) for l in grille)
    morceaux = [[] for _ in range(largeur)]
    for ligne in grille[:nb_tete]:
        dernier = ""
        for i in range(largeur):
            cellule = propre(ligne[i]) if i < len(ligne) else ""
            if cellule:
                dernier = cellule
            # Report : une cellule vide sous un en-tete fusionne herite du
            # libelle a sa gauche.
            valeur = cellule or dernier
            if valeur and (not morceaux[i] or morceaux[i][-1] != valeur):
                morceaux[i].append(valeur)
    return [" / ".join(m)[:90] for m in morceaux]


def main():
    global LIEUX
    LIEUX = lieux_connus()
    with io.open(CARTE, encoding="utf-8") as fh:
        carte = {f["id"]: f for f in json.load(fh)}

    sortie = io.open(SORTIE, "w", encoding="utf-8", newline="\n")
    total = tableaux = sans_valeur = transposes = 0
    par_epoque = Counter()

    for chemin in sorted(glob.glob(os.path.join(CORPUS, "*.json"))):
        with io.open(chemin, encoding="utf-8") as fh:
            doc = json.load(fh)
        ident, source = doc["id"], doc["source"]
        fiche = carte.get(ident, {})
        ep = fiche.get("epoque", "?")
        date = fiche.get("date_rapportage")

        for t in doc["tableaux"]:
            grille = t["grille"]
            if not grille or len(grille) < 2:
                continue
            tableaux += 1
            nb_tete = lignes_entete(grille)
            colonnes = entetes_colonnes(grille, nb_tete)
            emis = 0
            for ligne in grille[nb_tete:]:
                libelle = ""
                for cellule in ligne:
                    c = propre(cellule)
                    if c and not CELLULE_NOMBRE.match(c):
                        libelle = c[:90]
                        break
                for i, cellule in enumerate(ligne):
                    valeur, unite = valeur_de(cellule, source)
                    if valeur is None:
                        continue
                    colonne = colonnes[i] if i < len(colonnes) else ""
                    if not libelle and not colonne:
                        continue
                    indicateur, sujet, lieu_col = denoue(colonne, libelle)
                    transposes += 1 if lieu_col else 0
                    sortie.write(json.dumps({
                        "rapport": ident, "source": source, "epoque": ep,
                        "date": date, "page": t["page"], "tableau": t["index"],
                        "ligne": libelle, "colonne": colonne,
                        # Ce qui est mesure, et sur quoi. L'orientation du
                        # tableau decide lequel des deux est lequel.
                        "indicateur": indicateur, "sujet": sujet,
                        "lieu_en_colonne": lieu_col,
                        "brut": propre(cellule), "valeur": valeur,
                        "unite": unite,
                    }, ensure_ascii=False) + "\n")
                    emis += 1
                    total += 1
                    par_epoque[ep] += 1
            if emis == 0:
                sans_valeur += 1
    sortie.close()

    print("%d tableaux parcourus, %d sans aucune valeur numerique, %d cellules a lieu en colonne"
          % (tableaux, sans_valeur, transposes))
    print("%d cellules chiffrees extraites" % total)
    print("\nPar epoque")
    for ep, n in sorted(par_epoque.items()):
        print("   %-4s %7d" % (ep, n))
    print("\nsortie : data/corpus/cellules.jsonl")


if __name__ == "__main__":
    main()
