# -*- coding: utf-8 -*-
"""Catalogue unifie : tout ce qui est chiffre dans le corpus, avec sa couverture.

Fusionne les deux volets — cellules de tableaux et nombres de la prose — en une
seule liste de candidats, chacun decrit par ce qui permet de decider s'il est
utilisable :

    combien de rapports le portent, sur quelle plage de dates, quelles epoques,
    quelle continuite dans sa plage, quelle amplitude de valeurs, et un exemple
    verifiable dans le PDF.

La continuite est l'indicateur le plus utile : un candidat present sur 40
rapports repartis sur toute l'epidemie est inexploitable, alors que 40 rapports
consecutifs font une serie. Le nombre brut de rapports ne distingue pas les
deux.

    python scripts/catalogue_corpus.py

Sorties : data/corpus/catalogue.json
          data/corpus/observations.jsonl   (les deux volets, schema commun)
"""
import io
import json
import os
import re
import unicodedata
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(ROOT, "data", "corpus")
CARTE = os.path.join(DOSSIER, "carte.json")
CELLULES = os.path.join(DOSSIER, "cellules.jsonl")
NOMBRES = os.path.join(DOSSIER, "nombres.jsonl")
CATALOGUE = os.path.join(DOSSIER, "catalogue.json")
OBSERVATIONS = os.path.join(DOSSIER, "observations.jsonl")

PILIERS = [
    ("laboratoire", ["echantillon", "positivite", "resultat positif",
                     "resultats positifs", "gene xpert", "preleve", "teste",
                     "analyse"]),
    ("pci_eds", ["ring", "decontamin", "swab", "enterrement", " eds", "eds ",
                 "score pci", "desinfection"]),
    ("soins", ["admission", "hospitalis", "lit", "occupation", "gueri",
               "sortie", "isolement", "transit", "cte", "prise en charge"]),
    ("surveillance", ["alerte", "suspect", "investig", "notifi", "completude",
                      "promptitude", "validee", "invalidee"]),
    ("contacts", ["contact"]),
    ("crec", ["sensibilis", "causerie", "visite a domicile", "menage",
              "radio", "iec", "journaliste"]),
    ("poe_poc", ["voyageur", "point d entree", "poe", "poc", "screen",
                 "lavage des mains"]),
    ("vaccination", ["vaccin", "dose", "ervebo"]),
    ("logistique", ["intrant", "moto", "vehicule", "ambulance", "kit",
                    "carburant", "stock", "entrepot"]),
    ("securite", ["incident securitaire", "attaque", "escorte", "insecurite"]),
    ("financement", ["us$", "usd", "budget", "financement", "funding"]),
    ("demographie", ["sexe", "femme", "homme", "enfant", "age", "ans", "tranche"]),
    ("epidemio", ["cas confirme", "deces", "letalite", "cfr", "nouveaux cas",
                  "zone de sante", "cumul", "cases", "province"]),
]


def sans_accent(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def pilier(texte):
    t = " " + sans_accent(texte).lower() + " "
    for nom, cles in PILIERS:
        if any(c in t for c in cles):
            return nom
    return "autre"


# Mots qui ne distinguent pas deux indicateurs : « Deces confirmes cumules
# (n) », « Nombre total de deces confirmes » et « Deces (confirmes) » designent
# la meme chose. Les retirer fait passer les candidats tableaux de 362, dont
# 203 vus une seule fois, a un ensemble ou chaque serie se retrouve d'un
# rapport a l'autre.
BAVARDAGE = {"nombre", "nbre", "total", "cumul", "cumule", "cumules",
             "cumulatif", "cumulative", "effectif", "effectifs", "de", "des",
             "du", "la", "le", "les", "et", "en", "au", "aux", "un", "une",
             "d", "l", "par", "pour", "dans", "sur", "n", "no", "num",
             "cum", "of", "the", "and", "in", "to", "a", "s"}


def normalise(libelle):
    t = sans_accent(libelle or "").lower()
    t = re.sub(r'\d+', "#", t)
    t = re.sub(r'[^a-z0-9#%/]+', " ", t)
    return re.sub(r'\s+', " ", t).strip()[:90]


def canonique(libelle):
    """Cle d'indicateur : les mots qui portent le sens, tries et dedoublonnes.

    Le tri detruit l'ordre des mots, donc un peu de sens — mais il fait
    coincider les variantes de redaction, ce qui est exactement ce qu'on
    cherche pour mesurer une couverture. Le libelle d'origine reste dans
    l'exemple, pour verification.
    """
    t = sans_accent(libelle or "").lower()
    t = re.sub(r'\d+', " ", t)
    t = re.sub(r'[^a-z%]+', " ", t)
    mots = {m for m in t.split() if m not in BAVARDAGE and len(m) > 1}
    return " ".join(sorted(mots))[:80]


def lire(chemin):
    with io.open(chemin, encoding="utf-8") as fh:
        for ligne in fh:
            yield json.loads(ligne)


def main():
    with io.open(CARTE, encoding="utf-8") as fh:
        carte = json.load(fh)
    dates = {f["id"]: f["date_rapportage"] for f in carte}
    # Rangs chronologiques, pour mesurer la continuite d'un candidat.
    ordre = sorted((d, i) for i, d in dates.items() if d)
    rang = {ident: n for n, (_d, ident) in enumerate(ordre)}

    groupes = defaultdict(lambda: {"rapports": set(), "epoques": set(),
                                   "sources": set(), "valeurs": [],
                                   "occurrences": 0, "exemple": None,
                                   "unites": set()})

    obs = io.open(OBSERVATIONS, "w", encoding="utf-8", newline="\n")
    total = 0

    for e in lire(CELLULES):
        brut_libelle = e.get("indicateur") or e["colonne"] or e["ligne"]
        # Jamais de perte : un libelle qui ne laisse aucun mot significatif
        # (« 203 », « # »)  garde sa forme normalisee, et a defaut sa place
        # dans le catalogue sous un intitule explicite. Une cellule ecartee
        # ici serait une donnee qu'il faudrait rouvrir les PDF pour retrouver.
        cle = ("tableau", canonique(brut_libelle) or normalise(brut_libelle)
               or "(libelle absent)")
        g = groupes[cle]
        g["rapports"].add(e["rapport"])
        g["epoques"].add(e["epoque"])
        g["sources"].add(e["source"])
        g["occurrences"] += 1
        g["unites"].add(e.get("unite") or "")
        if len(g["valeurs"]) < 600:
            g["valeurs"].append(e["valeur"])
        if g["exemple"] is None:
            g["exemple"] = {"rapport": e["rapport"], "page": e["page"],
                            "extrait": "%s | %s = %s" % (
                                (e.get("sujet") or "")[:44],
                                (e.get("indicateur") or e["colonne"])[:44],
                                e["brut"])}
        obs.write(json.dumps({
            "origine": "tableau", "rapport": e["rapport"], "source": e["source"],
            "epoque": e["epoque"], "date": e["date"], "page": e["page"],
            "cle": cle[1], "sujet": e.get("sujet"),
            "libelle": e.get("indicateur") or e["colonne"],
            "transpose": e.get("transpose"),
            "valeur": e["valeur"], "unite": e.get("unite"), "brut": e["brut"],
        }, ensure_ascii=False) + "\n")
        total += 1

    for e in lire(NOMBRES):
        cle = ("prose", e["contexte"][:90])
        g = groupes[cle]
        g["rapports"].add(e["rapport"])
        g["epoques"].add(e["epoque"])
        g["sources"].add(e["source"])
        g["occurrences"] += 1
        if len(g["valeurs"]) < 600:
            g["valeurs"].append(e["valeur"])
        if g["exemple"] is None:
            g["exemple"] = {"rapport": e["rapport"], "page": e["page"],
                            "extrait": e["phrase"][:220]}
        obs.write(json.dumps({
            "origine": "prose", "rapport": e["rapport"], "source": e["source"],
            "epoque": e["epoque"], "date": e["date"], "page": e["page"],
            "cle": cle[1], "sujet": None, "libelle": e["contexte"],
            "valeur": e["valeur"], "unite": None, "brut": e["brut"],
            "citation": e["phrase"],
        }, ensure_ascii=False) + "\n")
        total += 1
    obs.close()

    catalogue = []
    for (origine, cle), g in groupes.items():
        rapports = sorted(g["rapports"])
        rangs = sorted(rang[r] for r in rapports if r in rang)
        if not rangs:
            continue
        etendue = rangs[-1] - rangs[0] + 1
        vals = g["valeurs"]
        distinctes = len(set(vals))
        ds = sorted(d for d in (dates.get(r) for r in rapports) if d)
        catalogue.append({
            "origine": origine,
            "cle": cle,
            "pilier": pilier(cle if origine == "tableau"
                             else (g["exemple"] or {}).get("extrait", cle)),
            "nb_rapports": len(rapports),
            "occurrences": g["occurrences"],
            "date_min": ds[0] if ds else None,
            "date_max": ds[-1] if ds else None,
            "etendue": etendue,
            "continuite": round(len(rangs) / float(etendue), 3),
            "epoques": sorted(g["epoques"]),
            "sources": sorted(g["sources"]),
            "valeurs_distinctes": distinctes,
            "variable": distinctes > 1 and distinctes > len(vals) * 0.15,
            "min": min(vals), "max": max(vals),
            "unites": sorted(u for u in g["unites"] if u),
            "rapports": rapports,
            "exemple": g["exemple"],
        })

    catalogue.sort(key=lambda c: (-c["nb_rapports"], c["cle"]))
    with io.open(CATALOGUE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(catalogue, fh, ensure_ascii=False, indent=1)

    def serie(c):
        return (c["nb_rapports"] >= 10 and c["variable"]
                and c["continuite"] >= 0.6)

    series = [c for c in catalogue if serie(c)]
    print("%d observations ecrites, %d candidats distincts\n" % (total, len(catalogue)))
    print("Candidats retenus comme series exploitables : %d" % len(series))
    print("   critere : >= 10 rapports, valeur variable, continuite >= 0,6\n")

    print("   Par origine")
    for o in ("tableau", "prose"):
        n = sum(1 for c in series if c["origine"] == o)
        print("      %-8s %3d" % (o, n))

    print("\n   Par pilier")
    par = defaultdict(lambda: [0, 0])
    for c in series:
        par[c["pilier"]][0] += 1
        par[c["pilier"]][1] += c["occurrences"]
    for nom, (n, o) in sorted(par.items(), key=lambda x: -x[1][0]):
        print("      %-14s %3d series  %7d valeurs" % (nom, n, o))

    print("\n   Par epoque couverte")
    par_ep = defaultdict(int)
    for c in series:
        for ep in c["epoques"]:
            par_ep[ep] += 1
    for ep, n in sorted(par_ep.items()):
        print("      %-4s %3d" % (ep, n))

    print("\n   Les 30 series les plus continues (>= 20 rapports)")
    fortes = sorted([c for c in series if c["nb_rapports"] >= 20],
                    key=lambda c: (-c["continuite"], -c["nb_rapports"]))
    for c in fortes[:30]:
        print("      %3d rap  cont %.2f  %-12s %-9s %s"
              % (c["nb_rapports"], c["continuite"], c["pilier"],
                 c["origine"], c["cle"][:60]))

    print("\nsorties : data/corpus/catalogue.json, observations.jsonl")


if __name__ == "__main__":
    main()
