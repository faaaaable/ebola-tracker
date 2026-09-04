# -*- coding: utf-8 -*-
"""Compte les genomes du virus Bundibugyo sequences pendant l'epidemie de 2026.

Source : Pathoplexus (pathoplexus.org/ebola-bdbv), la base ou l'INRB et ses
partenaires deposent les sequences ; interrogee par son API LAPIS, en
AGREGATS seulement (comptes par zone et par mois). Aucune sequence, aucune
metadonnee individuelle n'est telechargee : la plupart des depots sont sous
conditions « restreintes », qui ne s'opposent pas a un compte mais
interdisent de publier une analyse sans prevenir les deposants — la note de
la page le dit.

Les noms de zone de Pathoplexus sont libres (« BUNIA », « MUNGWALU »,
« rwampara », une aire de sante comme « Hoho »…) : ils sont ramenes aux zones
de latest.json par la meme normalisation que le reste du site, les alias
connus en plus ; ce qui ne correspond a aucune zone est compte a part,
jamais devine.

Sortie : data/genomes.json. Ne tourne pas dans le pipeline quotidien — a
relancer a la main quand on veut rafraichir le compte.
"""
import datetime as dt
import io
import json
import os
import re
import sys
import unicodedata

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAPIS = "https://lapis.pathoplexus.org/ebola-bdbv/sample/aggregated"
PAYS = "Democratic Republic of the Congo"
ALIAS = {"mungwalu": "mongbwalu", "mongwalu": "mongbwalu", "mongbalu": "mongbwalu",
         "nyakunde": "nyankunde", "gethy": "gety", "nia": "niania"}


def normalise(nom):
    s = unicodedata.normalize("NFKD", nom or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z]", "", s.lower())
    return ALIAS.get(s, s)


def lapis(**params):
    r = requests.get(LAPIS, params=params, timeout=60, headers={"User-Agent": "ebola-tracker.org"})
    r.raise_for_status()
    return r.json()["data"]


def main():
    latest = json.load(open(os.path.join(ROOT, "data", "latest.json")))
    zones = {}
    for z in latest["healthZones"]:
        zones[normalise(z["name"])] = (z["name"], z.get("province"))

    lignes = lapis(geoLocCountry=PAYS, fields="geoLocAdmin1,geoLocAdmin2,sampleCollectionDate")
    par_zone, par_mois, autres, non_precise = {}, {}, {}, 0
    total = 0
    for x in lignes:
        n = x["count"]
        total += n
        date = x.get("sampleCollectionDate") or ""
        mois = date[:7] if date.startswith("2026") else ("2012" if date.startswith("2012") else "?")
        par_mois[mois] = par_mois.get(mois, 0) + n
        if not date.startswith("2026"):
            continue        # les 23 sequences de 2012 sont l'epidemie precedente
        cle = normalise(x.get("geoLocAdmin2"))
        if cle in zones:
            par_zone[cle] = par_zone.get(cle, 0) + n
        elif x.get("geoLocAdmin2"):
            autres[x["geoLocAdmin2"]] = autres.get(x["geoLocAdmin2"], 0) + n
        else:
            # admin1 « Isiro » sans zone : Isiro est aussi une zone de sante
            cle1 = normalise(x.get("geoLocAdmin1"))
            if cle1 in zones:
                par_zone[cle1] = par_zone.get(cle1, 0) + n
            else:
                non_precise += n
    termes = {}
    for x in lapis(geoLocCountry=PAYS, fields="dataUseTerms"):
        termes[x["dataUseTerms"]] = termes.get(x["dataUseTerms"], 0) + x["count"]
    groupes = {}
    for x in lapis(geoLocCountry=PAYS, fields="groupName"):
        groupes[x["groupName"]] = groupes.get(x["groupName"], 0) + x["count"]
    pays = {}
    for x in lapis(fields="geoLocCountry,sampleCollectionDate"):
        if (x.get("sampleCollectionDate") or "").startswith("2026"):
            pays[x["geoLocCountry"] or "?"] = pays.get(x["geoLocCountry"] or "?", 0) + x["count"]

    rdc_2026 = sum(v for k, v in par_mois.items() if k.startswith("2026"))
    out = {
        "source": "Pathoplexus, ebola-bdbv, via LAPIS (agregats)",
        "consulte": dt.date.today().isoformat(),
        "totalRdc": total,
        "rdc2026": rdc_2026,
        "parPays2026": pays,
        "parMois": [{"mois": k, "n": v} for k, v in sorted(par_mois.items()) if k.startswith("2026")],
        "parZone": sorted([{"zone": zones[k][0], "province": zones[k][1], "n": v} for k, v in par_zone.items()],
                          key=lambda r: (-r["n"], r["zone"])),
        "autresLieux": autres,          # libelles qui ne sont pas des zones de sante
        "nonPrecise": non_precise,
        "termes": termes,
        "groupes": groupes,
    }
    out["zonesLocalisees"] = sum(r["n"] for r in out["parZone"])
    with io.open(os.path.join(ROOT, "data", "genomes.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("%d sequences RDC dont %d de 2026 ; %d localisees dans %d zones ; autres lieux %s ; non precisees %d"
          % (total, rdc_2026, out["zonesLocalisees"], len(out["parZone"]), autres, non_precise))
    print("termes :", termes, "| groupes :", groupes)


if __name__ == "__main__":
    main()
