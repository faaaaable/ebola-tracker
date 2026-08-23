# -*- coding: utf-8 -*-
"""Repartition par age et par sexe, lue dans les figures des SitRep.

Cette donnee n'existe nulle part ailleurs dans le corpus : ni tableau, ni
prose. Elle vit uniquement dans deux images, « FIGURE 5 — CAS CONFIRMES PAR
SEXE ET GROUPE D'AGE » et « FIGURE 6 — DECES PAR SEXE ET GROUPE D'AGE », que
22 rapports d'epoque C portent, du 12 juillet au 5 aout 2026.

Les valeurs sont ECRITES sur les barres : ce ne sont donc pas des estimations
tirees de la hauteur des pixels, mais des entiers lus. Et chaque figure imprime
son effectif total, ce qui donne un controle integre — la somme des dix valeurs
doit retomber exactement sur ce total. Une lecture qui echoue a ce test est
rejetee, jamais publiee.

Trois pieges rencontres, qui condamnent toute automatisation naive :

  - le n°078 INVERSE les deux figures, deces a gauche et cas a droite ;
  - trois rapports consecutifs peuvent porter la meme figure sans changement
    (069, 070 et 071 donnent tous n = 2570), la liste lineaire DHIS2 n'etant
    pas rafraichie chaque jour ;
  - certaines legendes sont rognees par la mise en page ; c'est le controle
    arithmetique qui restitue alors l'effectif.

    python scripts/demographie_figures.py

Sorties : data/corpus/demographie.jsonl   la serie complete, 22 dates
          data/demographie.json           l'instantane publiable, versionne

Le second est celui que lit le site. Il ne porte que la derniere situation
connue — le 5 aout 2026 — parce qu'une serie quotidienne serait trompeuse :
sept rapports sur vingt-deux reprennent la figure de la veille sans
changement, la liste lineaire DHIS2 n'etant pas rafraichie chaque jour.

Il porte aussi la couverture, qui est la mise en garde principale : la figure
ne voit que 61 % des deces, les deces communautaires n'etant le plus souvent
pas identifies. Publier une letalite par age sans cette precision reviendrait
a publier un chiffre faux.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(ROOT, "data", "corpus", "demographie.jsonl")

TRANCHES = ["50 et plus", "30-49", "18-29", "5-17", "0-4"]

# (cas [(F, M) par tranche], n_cas, deces [(F, M)], n_deces)
# Valeurs relevees a l'oeil sur les figures rendues a 210 dpi, puis validees
# par la somme. Les rapports qui partagent une figure identique partagent
# leur releve.
RELEVES = {
    "059": ([(166,149),(363,352),(341,228),(128,120),(72,79)], 1998,
            [(39,48),(63,87),(85,70),(31,38),(46,46)], 553),
    "060": ([(166,152),(366,358),(345,234),(129,122),(72,79)], 2023,
            [(39,50),(63,89),(86,74),(31,39),(46,46)], 563),
    "064": ([(184,161),(423,396),(378,263),(146,136),(90,94)], 2271,
            [(45,52),(74,99),(96,81),(32,42),(55,56)], 632),
    "065": ([(185,163),(427,397),(384,266),(148,138),(91,99)], 2298,
            [(46,52),(74,99),(96,81),(32,44),(55,58)], 637),
    "066": ([(195,169),(444,415),(396,269),(155,145),(95,112)], 2395,
            [(52,56),(78,104),(98,80),(34,47),(58,67)], 674),
    "067": ([(202,172),(456,428),(407,272),(158,151),(99,117)], 2462,
            [(55,58),(82,110),(99,82),(34,49),(60,68)], 697),
    "068": ([(209,177),(468,444),(418,285),(164,157),(100,129)], 2551,
            [(61,59),(89,113),(103,86),(36,50),(60,74)], 731),
    "069": ([(208,178),(470,450),(420,289),(168,157),(101,129)], 2570,
            [(60,60),(90,116),(103,86),(37,50),(60,73)], 735),
    "072": ([(220,198),(500,487),(451,316),(188,166),(116,142)], 2784,
            [(66,67),(103,131),(121,93),(49,57),(71,82)], 840),
    "073": ([(222,200),(512,497),(460,321),(195,168),(118,144)], 2837,
            [(67,68),(108,135),(123,97),(52,57),(73,84)], 864),
    "077": ([(241,222),(571,543),(497,345),(220,186),(132,168)], 3125,
            [(77,78),(125,150),(141,107),(63,60),(80,99)], 980),
    "078": ([(241,225),(579,552),(502,354),(225,186),(140,174)], 3178,
            [(77,79),(127,153),(146,110),(67,60),(88,105)], 1012),
    "079": ([(247,230),(591,562),(513,359),(231,190),(144,178)], 3245,
            [(79,80),(130,157),(148,112),(70,61),(89,110)], 1036),
    "081": ([(265,249),(615,589),(533,372),(245,204),(152,191)], 3415,
            [(89,91),(140,164),(157,117),(74,67),(95,117)], 1111),
    "082": ([(268,252),(623,594),(538,379),(247,208),(152,193)], 3454,
            [(89,93),(140,166),(158,121),(75,69),(95,118)], 1124),
}

# Rapports qui reprennent a l'identique la figure d'un autre — verifie par
# empreinte du rendu et par egalite des effectifs imprimes.
REPRISES = {"061": "060", "062": "060", "070": "069", "071": "069",
            "074": "073", "080": "079", "083": "082"}


def totaux_nationaux(ident):
    """Cumul national de cas et de deces, lu sur la page 1 du meme bulletin.

    C'est ce rapprochement qui donne la couverture reelle de la figure, et donc
    la seule mise en garde qui compte. On le lit plutot que de l'ecrire en dur :
    un chiffre saisi a la main serait invisible le jour ou il devient faux.
    """
    chemin = os.path.join(ROOT, "data", "corpus", "textes", ident + ".json")
    with io.open(chemin, encoding="utf-8") as fh:
        page1 = json.load(fh)["pages"][0]["texte"]

    def entier(brut):
        for e in "  ":
            brut = brut.replace(e, "")
        return int(brut)

    # Le bandeau ecrit le cumul des cas, puis celui des deces suivi de la
    # letalite entre parentheses. C'est cette letalite qui sert de preuve :
    # prendre « les deux plus grands nombres de la page » donnait 18 886, un
    # nombre qui n'existe nulle part dans le bulletin.
    motif = re.compile(r'(\d[\d  ]*\d)\s*\n\s*(\d[\d  ]*\d)\s*'
                       r'[·.]?\s*\(?\s*(\d{1,2},\d)\s*%')
    for m in motif.finditer(page1):
        cas, deces, letalite = entier(m.group(1)), entier(m.group(2)), \
            float(m.group(3).replace(",", "."))
        if deces < cas and abs(100.0 * deces / cas - letalite) < 0.6:
            return cas, deces
    return None, None


def main():
    carte = {f["id"]: f for f in json.load(
        io.open(os.path.join(ROOT, "data", "corpus", "carte.json"), encoding="utf-8"))}

    lignes, refuses = [], []
    for numero in sorted(set(RELEVES) | set(REPRISES)):
        source_releve = REPRISES.get(numero, numero)
        cas, n_cas, deces, n_deces = RELEVES[source_releve]
        ident = "INSP_" + numero
        fiche = carte.get(ident)
        if not fiche:
            refuses.append((ident, "rapport absent de la carte"))
            continue

        for mesure, valeurs, total in (("cas_confirmes", cas, n_cas),
                                       ("deces", deces, n_deces)):
            somme = sum(f + m for f, m in valeurs)
            if somme != total:
                refuses.append((ident, "%s : somme %d != n imprime %d"
                                % (mesure, somme, total)))
                continue
            for tranche, (f, m) in zip(TRANCHES, valeurs):
                for sexe, valeur in (("feminin", f), ("masculin", m)):
                    lignes.append({
                        "rapport": ident, "source": "INSP",
                        "epoque": fiche["epoque"], "date": fiche["date_rapportage"],
                        "page": None, "origine": "image",
                        "mesure": mesure, "tranche_age": tranche, "sexe": sexe,
                        "valeur": valeur, "effectif_figure": total,
                        "methode": "lecture d'image, valeur imprimee sur la barre",
                        "controle": "somme des 10 valeurs = effectif imprime",
                        "reprise_de": ("INSP_" + source_releve
                                       if numero in REPRISES else None),
                    })

    if refuses:
        print("RELEVES REFUSES")
        for ident, motif in refuses:
            print("   %-9s %s" % (ident, motif))
        sys.exit("Aucune ecriture : un releve ne passe pas son controle.")

    with io.open(SORTIE, "w", encoding="utf-8", newline="\n") as fh:
        for l in lignes:
            fh.write(json.dumps(l, ensure_ascii=False) + "\n")

    rapports = sorted({l["rapport"] for l in lignes})
    dates = sorted({l["date"] for l in lignes})
    print("%d valeurs sur %d rapports, du %s au %s"
          % (len(lignes), len(rapports), dates[0], dates[-1]))
    print("tous les controles arithmetiques passent")

    print("\nDerniere situation connue — %s" % dates[-1])
    dernier = [l for l in lignes if l["date"] == dates[-1]]
    print("   %-11s %>8s %8s %8s %8s" .replace(">", "") % ("tranche", "cas F", "cas M", "deces F", "deces M"))
    for t in TRANCHES:
        def v(mes, sx):
            return next((x["valeur"] for x in dernier
                         if x["tranche_age"] == t and x["mesure"] == mes
                         and x["sexe"] == sx), 0)
        cf, cm = v("cas_confirmes", "feminin"), v("cas_confirmes", "masculin")
        df, dm = v("deces", "feminin"), v("deces", "masculin")
        letal = 100.0 * (df + dm) / max(1, cf + cm)
        print("   %-11s %8d %8d %8d %8d   letalite %.1f %%"
              % (t, cf, cm, df, dm, letal))

    ecrire_instantane(lignes, dates[-1])
    print("\nsorties : data/corpus/demographie.jsonl, data/demographie.json")


def ecrire_instantane(lignes, date):
    """L'instantane publiable : parts par tranche, et couverture."""
    dernier = [l for l in lignes if l["date"] == date]
    ident = dernier[0]["rapport"]

    def v(tranche, mesure, sexe):
        return next((x["valeur"] for x in dernier if x["tranche_age"] == tranche
                     and x["mesure"] == mesure and x["sexe"] == sexe), 0)

    total_cas = sum(x["valeur"] for x in dernier if x["mesure"] == "cas_confirmes")
    total_deces = sum(x["valeur"] for x in dernier if x["mesure"] == "deces")
    nat_cas, nat_deces = totaux_nationaux(ident)

    tranches = []
    for t in reversed(TRANCHES):          # du plus jeune au plus age
        cas = v(t, "cas_confirmes", "feminin") + v(t, "cas_confirmes", "masculin")
        dec = v(t, "deces", "feminin") + v(t, "deces", "masculin")
        tranches.append({
            "tranche": t,
            "cas": cas, "deces": dec,
            "casFeminin": v(t, "cas_confirmes", "feminin"),
            "casMasculin": v(t, "cas_confirmes", "masculin"),
            "decesFeminin": v(t, "deces", "feminin"),
            "decesMasculin": v(t, "deces", "masculin"),
            "partCas": round(100.0 * cas / total_cas, 1),
            "partDeces": round(100.0 * dec / total_deces, 1),
        })

    # Repartition par sexe, tous ages confondus. Le rapport femmes/hommes des
    # cas est donne par tranche : c'est lui qui porte l'information, l'exces
    # feminin etant concentre sur les 18-29 ans et s'inversant chez les
    # nourrissons. L'ecart d'ensemble, lui, est faible.
    par_sexe = {}
    for mesure in ("cas_confirmes", "deces"):
        prefixe = "cas" if mesure == "cas_confirmes" else "deces"
        f = sum(v(t, mesure, "feminin") for t in TRANCHES)
        m = sum(v(t, mesure, "masculin") for t in TRANCHES)
        par_sexe[prefixe] = {
            "feminin": f, "masculin": m,
            "partFeminin": round(100.0 * f / (f + m), 1),
            "partMasculin": round(100.0 * m / (f + m), 1),
        }

    instantane = {
        "date": date,
        "sitrep": ident.split("_")[1],
        "source": "INSP",
        "parSexe": par_sexe,
        "derniereFigurePubliee": date,
        "totaux": {"cas": total_cas, "deces": total_deces},
        "couverture": {
            "casNational": nat_cas, "decesNational": nat_deces,
            "partCas": round(100.0 * total_cas / nat_cas, 1) if nat_cas else None,
            "partDeces": round(100.0 * total_deces / nat_deces, 1) if nat_deces else None,
        },
        "tranches": tranches,
    }
    chemin = os.path.join(ROOT, "data", "demographie.json")
    with io.open(chemin, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(instantane, fh, ensure_ascii=False, indent=1)

    c = instantane["couverture"]
    print("\nInstantane publiable — %s (SitRep n°%s)" % (date, instantane["sitrep"]))
    print("   cas   %d sur %s nationaux = %s %%"
          % (total_cas, c["casNational"], c["partCas"]))
    print("   deces %d sur %s nationaux = %s %%"
          % (total_deces, c["decesNational"], c["partDeces"]))


if __name__ == "__main__":
    main()
