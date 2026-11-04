# -*- coding: utf-8 -*-
"""Lieu des deces confirmes du jour, PAR ZONE DE SANTE : en communaute ou en
CTE (demande de Luz, 4 novembre 2026).

Le tableau 2 des SitRep (« Repartition des cas et deces confirmes par
province et zone ») porte depuis le 13 juillet 2026 (SitRep 060), pour chaque
zone, la situation du jour : nouveaux cas, deces communautaires, deces
intra-CTE, total des deces. `extraire_deces_lieu.py` n'en lit que les lignes
province ; celui-ci lit les zones.

LA DIFFICULTE. Le PDF n'imprime pas une case vide : « Mongbwalu 336 182
54,2 % 1 1 » (SitRep 060) dit un deces du jour, mais le texte seul ne dit pas
s'il est communautaire ou intra-CTE. Le pipeline quotidien laisse ces lignes
« n n » non ventilees, sauf deduction par la ligne de province. Ici on lit
la POSITION des chiffres sur la page : chaque chiffre est rendu a la colonne
de l'en-tete dont il est le plus proche (« Nouv. cas », « communautaires »,
« intra-CTE », « Total »). Le « 1 1 » de Mongbwalu tombe sous intra-CTE et
sous Total : la case communautaire est vide, le deces est intra-CTE.

DEUX LECTURES, UN ARBITRE. Pour chaque province et chaque bulletin :
1. la lecture par colonnes (ci-dessous) ;
2. a defaut, la lecture du pipeline quotidien (`update_data` : grille
   pdfplumber, repli texte, recoupements, ventilation par soustraction),
   completee par la deduction `deduire()` ;
L'arbitre est la ligne de la province (deces-lieu.json, ou a defaut la
ligne de province lue par colonnes si elle est coherente) : les zones
classees doivent sommer exactement ses deces communautaires, et pas plus que
ses intra-CTE — le surplus d'intra-CTE de la province est celui des lignes
« A ventiler », que le bulletin ne rattache a aucune zone (`aVentiler`).
La premiere lecture qui tombe juste est retenue. Si aucune ne tombe juste, la
lecture par colonnes est gardee telle que le PDF la donne et la province est
marquee `concordeProvince: false` : la source se contredit (SitRep 080,
ligne Nord-Kivu a 0/0/0 quand ses zones portent 22 deces), on la recopie et
on le dit.

Une zone n'est CLASSEE que si ses deux compteurs sont connus et que leur somme
tombe sur le total imprime. Sinon `communautaires` et `intraCte` sont null :
on sait combien de deces, pas ou.

Bulletin ecarte : le 087 (9 aout), tableau du jour seul, « ND » dans la colonne
intra-CTE de chaque zone de l'Ituri.

Sortie : data/deces-lieu-zones.json. Journal : tmp/deces-lieu-zones.log.
"""
from __future__ import annotations

import collections
import contextlib
import glob
import io
import itertools
import json
import os
import re
import sys

import pdfplumber

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
import update_data as U  # noqa: E402

SORTIE = os.path.join(RACINE, "data", "deces-lieu-zones.json")
JOURNAL = os.path.join(RACINE, "tmp", "deces-lieu-zones.log")
PREMIER = 60   # SitRep 060, 13 juillet 2026 : premiere apparition des colonnes
SANS_VENTILATION = {"087"}

PROVINCES = ["Ituri", "Nord-Kivu", "Sud-Kivu", "Haut-Uélé", "Tshopo",
             "Bas-Uélé", "Sud-Ubangi", "Nord-Ubangi"]
CLE_PROVINCE = {U.normalize_zone_key(p): p for p in PROVINCES}
NUM = re.compile(r"^\d+$")


# ---------------------------------------------------------------------------
# Lecture 1 : par position des colonnes
# ---------------------------------------------------------------------------

def _centre(w):
    return (w["x0"] + w["x1"]) / 2


def entete(ws):
    """Centres x des quatre colonnes du jour, ancres sur le mot « intra-CTE »
    de l'en-tete (« intra- » seul au 088), et bas de l'en-tete. Les autres
    mots varient : « Nouv. » manque au 102 (colonne alors placee a egale
    distance), « communautaires » manque au 168 (on prend le « Décès » le plus
    proche a gauche de intra-CTE)."""
    for w in ws:
        if not w["text"].lower().startswith("intra-"):
            continue
        prox = [v for v in ws if abs(v["top"] - w["top"]) <= 22 and v is not w]
        tot = sorted([v for v in prox if v["text"] == "Total" and v["x0"] > w["x1"] - 5],
                     key=lambda v: v["x0"])
        com = [v for v in prox if v["text"].lower().startswith("communau") and v["x1"] < w["x0"] + 5]
        if not com:
            com = sorted([v for v in prox if v["text"] == "Décès" and v["x1"] < w["x0"]],
                         key=lambda v: -v["x0"])[:1]
        if not (tot and com):
            continue
        nouv = [v for v in prox if v["text"].startswith("Nouv") and v["x1"] < com[0]["x0"] + 5]
        xc, xi = _centre(com[0]), _centre(w)
        xn = _centre(nouv[0]) if nouv else xc - (xi - xc)
        bas = max(v["bottom"] for v in [w, com[0], tot[0]] + nouv[:1]) + 0.5
        return {"nouv": xn, "comm": xc, "intra": xi, "total": _centre(tot[0])}, bas
    return None


def _rangees(ws, y0):
    ws = sorted([w for w in ws if w["top"] > y0], key=lambda w: (w["top"], w["x0"]))
    rangs = []
    for w in ws:
        if rangs and abs(w["top"] - rangs[-1][0]) <= 3.5:
            rangs[-1][1].append(w)
        else:
            rangs.append([w["top"], [w]])
    for r in rangs:
        r[1].sort(key=lambda w: w["x0"])
    return rangs


def _est_letalite(mots, i):
    t = mots[i]["text"]
    if t == "NA" or re.match(r"^\d{1,3},\d{1,2}%?$|^\d{1,3}%$", t):
        return True
    return bool(re.match(r"^\d{1,3}$", t)) and i + 1 < len(mots) and mots[i + 1]["text"] == "%"


def lire_colonnes(chemin):
    """Lignes du tableau 2 : [(nom, cle, {nouv, comm, intra, total}, cumul deces)]."""
    out, cols = [], None
    with pdfplumber.open(chemin) as pdf:
        for pg in pdf.pages:
            ws = pg.extract_words()
            h = entete(ws)
            if h:
                cols, y0 = h
            elif cols is None or not out:
                continue
            else:
                y0 = 0          # suite du tableau sur la page suivante
            rangs = _rangees(ws, y0)
            for k, (top, mots) in enumerate(rangs):
                i_let = next((i for i in range(1, len(mots)) if _est_letalite(mots, i)), None)
                if i_let is None:
                    continue
                nom = []
                for w in mots[:i_let]:
                    if NUM.match(w["text"]) or w["text"] == "NA":
                        break
                    nom.append(w["text"])
                nom = " ".join(nom)
                if not nom:
                    # Nom coupe autour de la ligne des chiffres : « Boma » au-dessus,
                    # « Mangbetu » en dessous (SitRep 171).
                    sans_chiffre = lambda r: not any(re.search(r"\d", w["text"]) for w in r[1])
                    av = [r for r in rangs[max(0, k - 2):k] if sans_chiffre(r)]
                    ap = [r for r in rangs[k + 1:k + 3] if sans_chiffre(r)]
                    parts = []
                    if av and top - av[-1][0] < 14:
                        parts.append(" ".join(w["text"] for w in av[-1][1]))
                    if ap and ap[0][0] - top < 14:
                        parts.append(" ".join(w["text"] for w in ap[0][1]))
                    nom = " ".join(parts).replace("- ", "-")
                if nom.lower().startswith("total"):
                    return out
                tete = [w["text"] for w in mots[:i_let] if NUM.match(w["text"])]
                vals = []
                for t in tete:          # recoller les milliers « 1 808 »
                    if vals and len(t) == 3 and len(vals[-1]) <= 3 and len(tete) > 2:
                        vals[-1] += t
                    else:
                        vals.append(t)
                jour = {}
                for w in mots[i_let + 1:]:
                    if not NUM.match(w["text"]):
                        continue
                    x = _centre(w)
                    # Chiffres d'une autre colonne de la page (SitRep 060 : la
                    # ligne Ituri du tableau 1 collee sur celle du Sud-Kivu).
                    if x > cols["total"] + 35 or x < cols["nouv"] - 35:
                        continue
                    col = min(cols, key=lambda c: abs(cols[c] - x))
                    jour.setdefault(col, int(w["text"]))
                out.append((nom, U.normalize_zone_key(nom), jour, int(vals[-1]) if vals else None))
    return out


def zones_par_colonnes(chemin):
    """{province: {"ligne": (comm, intra, total) | None, "zones": [...]}}"""
    res, cur = {}, None
    for nom, cle, j, cum in lire_colonnes(chemin):
        if cle in CLE_PROVINCE and not (cle == "TSHOPO" and cur == "Tshopo"):
            cur = CLE_PROVINCE[cle]
            c, i, t = j.get("comm"), j.get("intra"), j.get("total")
            ligne = None
            if t is not None:
                c = c if c is not None else (0 if i == t else None)
                i = i if i is not None else (0 if c == t else None)
                # Le jour ne depasse pas le cumul (SitRep 060 : « Sud-Kivu 3 1
                # 33,3 % 47 8 14 22 », chiffres du tableau voisin).
                if c is not None and i is not None and c + i == t and (cum is None or t <= cum):
                    ligne = (c, i, t)
            res[cur] = {"ligne": ligne, "zones": []}
            continue
        # Lignes sans zone : « A ventiler », « À ventiler* », ou « ** » seul
        # (SitRep 106 a 109), « Non identifiées », sous-totaux.
        if (not cur or not re.search(r"[A-Za-z]", cle) or "VENTILER" in cle
                or cle.startswith(("NON ID", "SOUS TOTAL"))):
            continue
        c, i, t = j.get("comm"), j.get("intra"), j.get("total")
        if t is None and c is not None and i is not None:
            t = c + i           # total non lu (Katwa, SitRep 074)
        if not t:
            continue
        if c is None and i == t:
            c = 0
        if i is None and c == t:
            i = 0
        ok = c is not None and i is not None and c + i == t and (cum is None or t <= cum)
        res[cur]["zones"].append({"zone": nom, "total": t,
                                  "communautaires": c if ok else None,
                                  "intraCte": i if ok else None})
    return res


# ---------------------------------------------------------------------------
# Lecture 2 : celle du pipeline quotidien
# ---------------------------------------------------------------------------

def zones_par_pipeline(chemin, numero):
    with pdfplumber.open(chemin) as pdf:
        texte = "\n".join(p.extract_text() or "" for p in pdf.pages)
        meta = U.extract_meta(texte, fallback_number=numero)
        prov_table = U.extract_province_summary(pdf)
        provinces = []
        if prov_table is not None:
            provinces, _ = U.parse_province_summary(prov_table)
        if not provinces:
            provinces, _ = U.parse_province_summary_from_text(texte)
            provinces = provinces or []
        rows = U.extract_zone_detail_rows(pdf)
        _, zones_raw, _ = U.parse_zone_detail(rows)
        zones_raw = U.revalidate_zones(texte, zones_raw)
        sous_totaux = U.extract_province_subtotals_from_text(texte)
    for p in provinces:
        sub = sous_totaux.get(p["name"])
        if sub:
            p["newDeathsCommunity24h"] = U.norm_int(sub["deathscomm"]) or 0
            p["newDeathsIntraCTE24h"] = U.norm_int(sub["deathsintracte"]) or 0
    zones = [U.zone_row_to_dict(pr, nom, row) for pr, nom, row in zones_raw]
    U.recouper_avec_la_veille(zones, meta)
    U.recouper_avec_la_province(zones, provinces)
    U.ventiler_par_soustraction(zones, provinces)
    res = {}
    for z in zones:
        if U.is_placeholder_zone_name(z["name"]) or z["name"].lower().startswith(("sous-total", "total")):
            continue
        t = z["newDeaths24h"] or 0
        if t <= 0:
            continue
        c, i = z["deathsCommunity24h"], z["deathsIntraCTE24h"]
        ok = c is not None and i is not None and c + i == t
        res.setdefault(z["province"], []).append({"zone": z["name"], "total": t,
                                                  "communautaires": c if ok else None,
                                                  "intraCte": i if ok else None})
    return meta, res


def deduire(lst, pc, pi):
    """Lignes non ventilees : un seul compteur imprime, qui porte le total. On
    cherche toutes les repartitions communaute / CTE qui tombent sur la ligne
    de province ; une seule : retenue et marquee `deduit`. Plusieurs : rien."""
    amb = [e for e in lst if e["communautaires"] is None]
    if not amb or len(amb) > 14:
        return
    rc = pc - sum(e["communautaires"] or 0 for e in lst if e not in amb)
    ri = pi - sum(e["intraCte"] or 0 for e in lst if e not in amb)
    sols = []
    for choix in itertools.product((0, 1), repeat=len(amb)):
        c = sum(e["total"] for e, k in zip(amb, choix) if k)
        i = sum(e["total"] for e, k in zip(amb, choix) if not k)
        if c == rc and 0 <= i <= ri:
            sols.append(choix)
            if len(sols) > 1:
                return
    if len(sols) == 1:
        for e, k in zip(amb, sols[0]):
            e["communautaires"], e["intraCte"] = (e["total"], 0) if k else (0, e["total"])
            e["deduit"] = True


def concorde(lst, ref):
    if ref is None:
        return False
    if any(e["communautaires"] is None for e in lst):
        return False
    return (sum(e["communautaires"] for e in lst) == ref[0]
            and sum(e["intraCte"] for e in lst) <= ref[1])


# ---------------------------------------------------------------------------

def main():
    with open(os.path.join(RACINE, "data", "zones-history.json"), encoding="utf-8") as f:
        historique = json.load(f)
    province_de = {}
    for e in historique:
        for z in e["zones"]:
            province_de.setdefault(U.normalize_zone_key(z["name"]), z["province"])
    with open(os.path.join(RACINE, "data", "deces-lieu.json"), encoding="utf-8") as f:
        ref_prov = {j["sitrep"]: j["provinces"] for j in json.load(f)["parDate"]}

    journal = io.StringIO()
    releves, ecartes = [], []
    compte = collections.Counter()
    for chemin in sorted(glob.glob(os.path.join(RACINE, "reports", "SITREP_MVE_*.pdf"))):
        numero = U.extract_number_from_filename(chemin)
        if int(numero) < PREMIER:
            continue
        sitrep = str(numero).zfill(3)
        if sitrep in SANS_VENTILATION:
            ecartes.append(sitrep)
            continue
        print("== SitRep %s" % sitrep, file=journal)
        par_col = zones_par_colonnes(chemin)
        with contextlib.redirect_stdout(journal):
            meta, par_pip = zones_par_pipeline(chemin, numero)
        # Une zone n'appartient qu'a une province : celle de l'historique.
        for src in (par_pip,):
            for prov in list(src):
                for e in list(src[prov]):
                    canon = province_de.get(U.normalize_zone_key(e["zone"]))
                    if canon and canon != prov:
                        src[prov].remove(e)
                        src.setdefault(canon, []).append(e)

        hist = {e["sitrep"]: e for e in historique}
        veille = {U.normalize_zone_key(z["name"]): z.get("deaths") or 0
                  for z in (hist.get(str(int(sitrep) - 1).zfill(3)) or {}).get("zones", [])}
        jour_hist = {U.normalize_zone_key(z["name"]): z.get("deaths") or 0
                     for z in (hist.get(sitrep) or {}).get("zones", [])}
        provinces = {}
        for prov in sorted(set(par_col) | set(par_pip) | set(ref_prov.get(sitrep) or {})):
            r = (ref_prov.get(sitrep) or {}).get(prov)
            col = par_col.get(prov) or {"ligne": None, "zones": []}
            if r:
                ref, origine_ref = (r["communautaires"], r["intraCte"]), "deces-lieu"
            elif col["ligne"]:
                ref, origine_ref = col["ligne"][:2], "ligne-colonnes"
            else:
                ref, origine_ref = None, None
            lc = [dict(e) for e in col["zones"]]
            lp = [dict(e) for e in par_pip.get(prov, [])]
            if not lc and not lp and not (ref and sum(ref)):
                continue
            choix, lecture = None, None
            if concorde(lc, ref):
                choix, lecture = lc, "colonnes"
            elif concorde(lp, ref):
                choix, lecture = lp, "pipeline"
            elif ref is not None:
                for cand, nom in ((lc, "colonnes"), (lp, "pipeline")):
                    d = [dict(e) for e in cand]
                    deduire(d, *ref)
                    if concorde(d, ref):
                        choix, lecture = d, nom + "+deduction"
                        break
            ok = choix is not None
            if not ok:
                choix, lecture = lc or lp, "colonnes" if lc else "pipeline"
            compte[lecture if ok else "discordant"] += 1
            bloc = {"province": ({"communautaires": ref[0], "intraCte": ref[1], "source": origine_ref}
                                 if ref else None),
                    "lecture": lecture, "concordeProvince": ok, "zones": choix}
            # Les deux lectures ne voient pas les memes deces : dit, pas tranche
            # (SitRep 080 : colonnes du jour du Nord-Kivu sans rapport avec la
            # ligne de province ni avec les cumuls des zones).
            tc, tp = sum(e["total"] for e in lc), sum(e["total"] for e in lp)
            if tc != tp:
                bloc_ecart = {"colonnes": tc, "pipeline": tp}
            else:
                bloc_ecart = None
            # Total du jour contre la hausse du cumul de la zone depuis le
            # bulletin precedent (zones-history.json), quand il existe.
            for e in choix:
                avant = veille.get(U.normalize_zone_key(e["zone"]))
                apres = jour_hist.get(U.normalize_zone_key(e["zone"]))
                if avant is not None and apres is not None and apres - avant != e["total"]:
                    e["ecartCumul"] = apres - avant
            if ok and ref and sum(e["intraCte"] for e in choix) < ref[1]:
                bloc["aVentiler"] = ref[1] - sum(e["intraCte"] for e in choix)
            if not ok:
                print("  ! %s %s : zones %s pour la province %s (%s)"
                      % (sitrep, prov, [(e["zone"], e["communautaires"], e["intraCte"], e["total"])
                                        for e in choix], ref, origine_ref), file=journal)
            if bloc_ecart:
                bloc["ecartLectures"] = bloc_ecart
            provinces[prov] = bloc
        releves.append({"date": meta.get("reportingDate"), "sitrep": sitrep, "provinces": provinces})

    releves.sort(key=lambda r: (r["date"] or "", r["sitrep"]))
    os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
    with io.open(JOURNAL, "w", encoding="utf-8") as fh:
        fh.write(journal.getvalue())

    # Agregat par zone sur toute la fenetre.
    agg = {}
    for r in releves:
        for prov, b in r["provinces"].items():
            for e in b["zones"]:
                a = agg.setdefault((prov, U.normalize_zone_key(e["zone"])),
                                   {"province": prov, "zone": e["zone"], "communautaires": 0,
                                    "intraCte": 0, "nonVentiles": 0, "jours": 0})
                a["jours"] += 1
                if e["communautaires"] is None:
                    a["nonVentiles"] += e["total"]
                else:
                    a["communautaires"] += e["communautaires"]
                    a["intraCte"] += e["intraCte"]
    zones_agg = sorted(agg.values(), key=lambda a: -(a["communautaires"] + a["intraCte"]))

    sortie = {
        "source": "SitRep INSP, tableau 2, colonnes « Situation du jour (24h) »",
        "periode": {"debut": releves[0]["date"], "fin": releves[-1]["date"]},
        "releves": len(releves),
        "bulletinsSansVentilation": ecartes,
        "zones": zones_agg,
        "parDate": releves,
    }
    with io.open(SORTIE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sortie, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    lignes = [e for r in releves for b in r["provinces"].values() for e in b["zones"]]
    cl = [e for e in lignes if e["communautaires"] is not None]
    print("%d bulletin(s), du %s au %s ; ecarte(s) : %s"
          % (len(releves), sortie["periode"]["debut"], sortie["periode"]["fin"], ecartes))
    print("zone-jours avec deces : %d classes (%d deces : %d communautaires, %d intra-CTE), "
          "%d non ventiles (%d deces)"
          % (len(cl), sum(e["total"] for e in cl), sum(e["communautaires"] for e in cl),
             sum(e["intraCte"] for e in cl), len(lignes) - len(cl),
             sum(e["total"] for e in lignes if e["communautaires"] is None)))
    print("province-jours par lecture retenue : %s" % dict(compte))
    print("province-jours ou les deux lectures divergent : %s"
          % [(r["sitrep"], p, b["ecartLectures"]) for r in releves for p, b in r["provinces"].items()
             if "ecartLectures" in b])
    print("zone-jours dont le total differe de la hausse du cumul : %d"
          % sum(1 for e in lignes if "ecartCumul" in e))


if __name__ == "__main__":
    main()
