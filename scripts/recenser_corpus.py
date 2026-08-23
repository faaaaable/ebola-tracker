# -*- coding: utf-8 -*-
"""Recense tout ce qui est chiffre dans le corpus, sans rien decider.

Le but n'est pas d'extraire : c'est de savoir ce qui existe, ou, sur combien de
rapports, et si ca bouge. Deux volets.

TABLEAUX — chaque tableau est reduit a la signature de ses en-tetes, puis les
signatures sont regroupees. Un groupe present sur 45 rapports est une serie
exploitable ; un groupe present sur 3 est une curiosite.

PROSE — l'unite de recensement est le NOMBRE, pas la phrase. « 63 nouveaux
resultats positifs (57 vivants et 6 deces) sur 344 nouveaux echantillons » ne
compte pas pour une observation mais pour quatre, chacune avec son propre
contexte. Chaque nombre est donc decrit par les mots qui l'entourent, reduits
a leur forme nue ; les contextes identiques sont ensuite regroupes.

Un premier essai regroupait les phrases entieres : 3 975 gabarits pour 5 929
phrases, c'est-a-dire presque aucun regroupement. Le contexte immediat du
nombre, lui, se repete d'un rapport a l'autre meme quand la phrase change.

Deux tris automatiques rendent le resultat lisible :

  - un contexte dont la valeur ne bouge jamais d'un rapport a l'autre est du
    decor, pas un indicateur — « une population estimee a 5 millions
    d'habitants » revient a l'identique dans 36 rapports ;
  - un contexte qui n'apparait que sur un rapport ne fera jamais une serie.

    python scripts/recenser_corpus.py

Sorties : data/corpus/recensement-tableaux.json
          data/corpus/recensement-prose.json
          data/corpus/nombres.jsonl        (une ligne par nombre trouve)
"""
import io
import json
import glob
import os
import re
import unicodedata
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "data", "corpus", "textes")
CARTE = os.path.join(ROOT, "data", "corpus", "carte.json")
OUT_TAB = os.path.join(ROOT, "data", "corpus", "recensement-tableaux.json")
OUT_PROSE = os.path.join(ROOT, "data", "corpus", "recensement-prose.json")
OUT_NOMBRES = os.path.join(ROOT, "data", "corpus", "nombres.jsonl")

ESPACES = "    "
# « 1 984 », « 18,3 », « 1,759 » cote OMS, « 47.6 ». Le signe et l'unite
# eventuelle sont captures a part.
NOMBRE = re.compile(r'(?<![\w/.,-])(\d[\d%s]*(?:[.,]\d+)?)(?![\w])' % ESPACES)

VIDES = {"de", "du", "des", "la", "le", "les", "et", "en", "a", "au", "aux",
         "sur", "dans", "pour", "par", "un", "une", "d", "l", "avec", "ont",
         "ete", "est", "sont", "ce", "cette", "ces", "qui", "que", "au",
         "of", "the", "in", "to", "and", "for", "a", "on", "as", "by", "with",
         "were", "was", "has", "have", "been", "at", "from", "during"}

# Ordre important : le premier motif qui matche l'emporte, donc du plus
# specifique au plus general. « incident » etait classe en securite et
# ramassait le pied de page « systeme de gestion de l'incident MVE17 ».
PILIERS = [
    ("laboratoire", ["echantillon", "positivite", "resultat positif",
                     "resultats positifs", "gene xpert", "analyses et",
                     "collectes et analyses", "testes"]),
    ("pci_eds", ["ring", "decontamin", "swab", "enterrement digne", " eds",
                 "score pci", "desinfection", "corps preleve"]),
    ("soins", ["admission", "hospitalis", " lit", "occupation", "gueri",
               "sortie", "isolement", "centre de transit", "cte"]),
    ("surveillance", ["alerte", "cas suspect", "investigue", "notifie",
                      "completude", "promptitude"]),
    ("contacts", ["contact"]),
    ("crec", ["sensibilis", "causerie", "visite a domicile", "menage touche",
              "radio", "outils iec", "journaliste"]),
    ("poe_poc", ["voyageur", "point d entree", "poe", "poc", "screen",
                 "lavage des mains", "passees aux"]),
    ("vaccination", ["vaccin", "dose", "ervebo"]),
    ("logistique", ["intrant", "moto", "vehicule", "ambulance", "kit ",
                    "carburant", "rupture de stock", "entrepot", "starlink"]),
    ("securite", ["incident securitaire", "attaque", "escorte", "insecurite",
                  "braquage", "enlevement"]),
    ("financement", ["us$", "usd", "budget", "financement", "funding",
                     "dollars"]),
    ("demographie", ["ans", "sexe", "femme", "homme", "enfant", "age median",
                     "tranche d age"]),
    ("epidemio", ["cas confirme", "deces confirme", "letalite", "nouveaux cas",
                  "zone de sante touchee", "cumul"]),
]


def sans_accent(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def lieux_connus():
    with io.open(os.path.join(ROOT, "data", "latest.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    noms = {z["name"] for z in d.get("healthZones", []) if z.get("name")}
    noms |= {p["name"] for p in d.get("provinces", []) if p.get("name")}
    noms |= {"Ituri", "Nord-Kivu", "Sud-Kivu", "Haut-Uélé", "Bas-Uélé",
             "Tshopo", "Bas Uélé", "Haut Uélé", "Ouganda", "France", "Bunia"}
    return sorted((sans_accent(n).lower() for n in noms if len(n) > 3),
                  key=len, reverse=True)


LIEUX = []


def parse_nombre(brut, source):
    """Rend la valeur numerique, ou None.

    Les deux sources n'ecrivent pas les nombres pareil : « 1 759 » et « 18,3 »
    cote INSP, « 1,759 » et « 18.3 » cote OMS. Se tromper de convention
    transforme mille sept cent cinquante-neuf en un virgule sept.
    """
    t = brut
    for e in ESPACES:
        t = t.replace(e, "")
    try:
        if source == "OMS":
            return float(t.replace(",", ""))
        if "," in t:
            return float(t.replace(".", "").replace(",", "."))
        return float(t)
    except ValueError:
        return None


def mots(fragment, combien, depuis_la_fin):
    t = sans_accent(fragment).lower()
    for lieu in LIEUX:
        t = t.replace(lieu, "<lieu>")
    t = re.sub(r'\d+', "#", t)
    t = re.sub(r'[^a-z<>#%]+', " ", t)
    liste = [m for m in t.split() if m not in VIDES and len(m) > 1]
    return liste[-combien:] if depuis_la_fin else liste[:combien]


def pilier(phrase):
    t = " " + sans_accent(phrase).lower() + " "
    for nom, cles in PILIERS:
        if any(c in t for c in cles):
            return nom
    return "autre"


def unites(texte):
    """Decoupe une page en phrases, en recollant les retours a la ligne."""
    texte = re.sub(r'-\n', "", texte)
    texte = re.sub(r'\n(?=[a-zà-ÿ(«])', " ", texte)
    blocs = re.split(r'\n\s*[••\-–]\s*|\n{2,}|\n(?=\d\.\d)', texte)
    for bloc in blocs:
        bloc = re.sub(r'[ \t]+', " ", bloc).strip()
        for phrase in re.split(r'(?<=[.;:])\s+(?=[A-ZÀ-Þ«•])|\n', bloc):
            phrase = phrase.strip()
            if 15 <= len(phrase) <= 500:
                yield phrase


def signature(grille):
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


def main():
    global LIEUX
    LIEUX = lieux_connus()

    with io.open(CARTE, encoding="utf-8") as fh:
        carte = {f["id"]: f for f in json.load(fh)}

    groupes_tab = defaultdict(lambda: {"rapports": set(), "epoques": set(),
                                       "formes": set(), "pages": set(),
                                       "exemple": None})
    groupes = defaultdict(lambda: {"rapports": set(), "epoques": set(),
                                   "sources": set(), "valeurs": [],
                                   "occurrences": 0, "exemple": None,
                                   "pages": set()})

    nombres = io.open(OUT_NOMBRES, "w", encoding="utf-8", newline="\n")
    total = 0

    for chemin in sorted(glob.glob(os.path.join(CORPUS, "*.json"))):
        with io.open(chemin, encoding="utf-8") as fh:
            doc = json.load(fh)
        ident, source = doc["id"], doc["source"]
        fiche = carte.get(ident, {})
        ep = fiche.get("epoque", "?")
        date = fiche.get("date_rapportage")

        for sig in fiche.get("signatures", []):
            g = groupes_tab[sig["signature"]]
            g["rapports"].add(ident)
            g["epoques"].add(ep)
            g["formes"].add("%dx%d" % (sig["lignes"], sig["colonnes"]))
            g["pages"].add(sig["page"])
            if g["exemple"] is None:
                g["exemple"] = {"rapport": ident, "page": sig["page"]}

        for page in doc["pages"]:
            for phrase in unites(page["texte"]):
                for m in NOMBRE.finditer(phrase):
                    valeur = parse_nombre(m.group(1), source)
                    if valeur is None:
                        continue
                    gauche = mots(phrase[max(0, m.start() - 90):m.start()], 3, True)
                    droite = mots(phrase[m.end():m.end() + 90], 4, False)
                    if not gauche and not droite:
                        continue
                    cle = " ".join(gauche) + " ¤ " + " ".join(droite)
                    if len(cle) < 8:
                        continue
                    g = groupes[cle]
                    g["rapports"].add(ident)
                    g["epoques"].add(ep)
                    g["sources"].add(source)
                    g["pages"].add(page["page"])
                    g["occurrences"] += 1
                    if len(g["valeurs"]) < 400:
                        g["valeurs"].append(valeur)
                    if g["exemple"] is None:
                        g["exemple"] = {"rapport": ident, "page": page["page"],
                                        "phrase": phrase[:280]}
                    total += 1
                    nombres.write(json.dumps({
                        "rapport": ident, "source": source, "epoque": ep,
                        "date": date, "page": page["page"], "contexte": cle,
                        "brut": m.group(1), "valeur": valeur,
                        "phrase": phrase[:280],
                    }, ensure_ascii=False) + "\n")
    nombres.close()

    tabs = []
    for cle, g in groupes_tab.items():
        tabs.append({"signature": cle, "nb_rapports": len(g["rapports"]),
                     "epoques": sorted(g["epoques"]),
                     "formes": sorted(g["formes"])[:6],
                     "pages": sorted(g["pages"])[:10],
                     "rapports": sorted(g["rapports"]), "exemple": g["exemple"]})
    tabs.sort(key=lambda x: (-x["nb_rapports"], x["signature"]))

    def ligne_de_tableau(phrase):
        """« Nizi 580 244 42,1% 13 0 0 » est une ligne de tableau, pas une
        phrase. Le volet TABLEAUX la traite mieux, mais on la garde ici : la
        jeter reviendrait a perdre les rapports ou la detection de tableau
        echoue."""
        nb = len(NOMBRE.findall(phrase))
        mots_alpha = len(re.findall(r'[A-Za-zÀ-ÿ]{3,}', phrase))
        return nb >= 3 and mots_alpha <= nb

    prose = []
    for cle, g in groupes.items():
        vals = g["valeurs"]
        distinctes = len(set(vals))
        prose.append({
            "contexte": cle,
            "pilier": pilier((g["exemple"] or {}).get("phrase", cle)),
            "nb_rapports": len(g["rapports"]),
            "occurrences": g["occurrences"],
            "sources": sorted(g["sources"]),
            "epoques": sorted(g["epoques"]),
            "valeurs_distinctes": distinctes,
            "variable": distinctes > 1 and distinctes > len(vals) * 0.2,
            "min": min(vals), "max": max(vals),
            "pages": sorted(g["pages"])[:10],
            "rapports": sorted(g["rapports"]),
            "ligne_de_tableau": ligne_de_tableau((g["exemple"] or {}).get("phrase", "")),
            "exemple": g["exemple"],
        })
    prose.sort(key=lambda x: (-x["nb_rapports"], -x["occurrences"]))

    with io.open(OUT_TAB, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(tabs, fh, ensure_ascii=False, indent=1)
    with io.open(OUT_PROSE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(prose, fh, ensure_ascii=False, indent=1)

    print("TABLEAUX  %d signatures distinctes" % len(tabs))
    for s in (40, 20, 10, 5, 2):
        print("   sur >= %2d rapports : %3d"
              % (s, sum(1 for t in tabs if t["nb_rapports"] >= s)))

    print("\nPROSE     %d nombres releves, %d contextes distincts"
          % (total, len(prose)))
    exploitables = [p for p in prose if p["nb_rapports"] >= 10
                    and p["variable"] and not p["ligne_de_tableau"]]
    print("   sur >= 10 rapports              : %d"
          % sum(1 for p in prose if p["nb_rapports"] >= 10))
    print("   ... dont a valeur variable      : %d   <- candidats serie"
          % len(exploitables))
    print("   constants (decor, pas donnee)   : %d"
          % sum(1 for p in prose if p["nb_rapports"] >= 10 and not p["variable"]))
    print("   lignes de tableau dans le flux  : %d"
          % sum(1 for p in prose if p["nb_rapports"] >= 10 and p["variable"]
                and p["ligne_de_tableau"]))

    par_pilier = defaultdict(lambda: [0, 0])
    for p in exploitables:
        par_pilier[p["pilier"]][0] += 1
        par_pilier[p["pilier"]][1] += p["occurrences"]
    print("\n   Candidats serie par pilier")
    for nom, (c, o) in sorted(par_pilier.items(), key=lambda x: -x[1][0]):
        print("   %-14s %4d contextes  %6d occurrences" % (nom, c, o))

    print("\n   Les 25 meilleurs candidats")
    for p in exploitables[:25]:
        print("   %3d rap %-12s %-11s %s" % (p["nb_rapports"], p["pilier"],
                                             ",".join(p["epoques"]),
                                             p["contexte"][:78]))
    print("\nsorties : data/corpus/recensement-{tableaux,prose}.json, nombres.jsonl")


if __name__ == "__main__":
    main()
