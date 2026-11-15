"""Les nouveaux cas et deces de chaque zone de sante, jour par jour
(data/zones-jour.json, 10 novembre 2026).

Ils alimentent le chapitre « Zones de sante » des pages province : le
tableau (nouveaux cas et deces sur 24 h, 7, 14 ou 30 jours), le grand
graphique d'une zone et les petits graphiques de toutes les zones.

Meme calcul que les graphiques des provinces (partsQuotidiennes d'app.js) :
la barre d'un jour est l'ecart entre deux cumuls de la zone publies par les
SitRep de l'INSP (data/zones-history.json).
- Un cumul qui baisse (reclassement) donne une barre a zero, marquee
  « baisse » : le recul n'est pas retranche.
- Un bulletin qui suit un jour sans bulletin couvre plusieurs journees
  (« n ») ; les 22 et 30 juillet sont des rattrapages annonces (« ratt ») :
  les deux passent en teinte claire, « Rattrapage ».
- L'harmonisation de l'Ituri (SitRep 169, defaite au 170) : les cas des
  cumuls anterieurs sont remis sur la base harmonisee (harmonisations.rebaser),
  ce qui redonne exactement les nouveaux cas imprimes ; pour les deces des
  deux journees, on prend les deces du jour du tableau 2 (« decesJourZones »
  de data/harmonisations.json), l'ecart des cumuls n'ayant pas de sens.
- Le premier cumul d'une zone n'est pas une journee : les cas deja comptes
  au premier instantane (« casAvant ») et les deces au premier jour ou les
  deces par zone sont publies (« decesAvant », 1er juin) restent hors barres.
  Une zone qui apparait plus tard part de zero : sa premiere barre est son
  premier cumul, comme dans le tableau des zones.

- Les nouveaux cas (et deces) du jour par zone que publient certains
  bulletins (data/zones-jour-annonces.json, scripts/extraire_zones_annonces.py,
  15 novembre 2026) separent la journee du reste, province par province et
  seulement quand la somme des zones retombe sur l'annonce de la province :
  une seule journee manquante devient la barre de la veille, calculee par
  soustraction (« calc », « nc »/« nd » = 1 journee) ; sinon la part du
  jour (« ca », « da ») est pleine et seul le reste reste en rattrapage.

Seules les journees non nulles sont ecrites. Un jour sans bulletin n'a pas
de barre ; il se retrouve dans « sansBulletin »."""
import json
import os
import unicodedata
from datetime import date, timedelta

import harmonisations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(ROOT, "data", "zones-jour.json")

# Les rattrapages annonces par les bulletins : memes dates que
# RATTRAPAGE_ADMIN (assets/js/app.js). Leur part du jour n'est publiee
# qu'au niveau national : a l'echelle d'une zone, toute la barre est claire.
RATTRAPAGES = {"2026-07-22", "2026-07-30"}

# Variantes d'orthographe d'une meme zone : KNOWN_ALIASES de
# update_data.normalize_zone_key (Gethy / Gety, Ituri).
ALIAS = {"GETHY": "GETY"}


def cle(nom):
    t = unicodedata.normalize("NFD", str(nom or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    for ch in "-_'’.":
        t = t.replace(ch, " ")
    t = " ".join(t.replace("*", " ").upper().split())
    return ALIAS.get(t, t)


def calculer(zones_history):
    hist = sorted(harmonisations.rebaser(zones_history), key=lambda h: h["date"])
    harm = harmonisations.charger()
    dates = [h["date"] for h in hist]
    d0, d1 = date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
    connues = set(dates)
    sans = [(d0 + timedelta(i)).isoformat() for i in range((d1 - d0).days + 1)]
    sans = [d for d in sans if d not in connues]
    premiers_deces = next((h["date"] for h in hist
                           if any(z.get("deaths") is not None for z in h["zones"])), None)

    # Les zones de chaque province, sous le nom du dernier bulletin.
    der = hist[-1]
    provinces = {}
    for z in der["zones"]:
        provinces.setdefault(z["province"], {})[cle(z["name"])] = {
            "nom": z["name"], "cas": z.get("cases") or 0, "deces": z.get("deaths") or 0,
            "casAvant": 0, "decesAvant": 0, "j": {}}

    # Le dernier cumul connu de chaque zone, champ par champ, avec sa date :
    # une zone absente d'un bulletin (Bambu le 22 mai) garde son cumul de la
    # veille, sinon son recul du lendemain se perdrait et elle repartirait de
    # zero ; le SitRep 087 (9 aout) ne donne aucun deces par zone, l'ecart du
    # 10 aout se prend donc sur le 8 et couvre plusieurs journees (« nd »).
    connu_c, connu_d = {}, {}
    prev_date = None
    for h in hist:
        cur = {}
        for z in h["zones"]:
            cur.setdefault(z["province"], {})[cle(z["name"])] = z
        hx = harm.get(h["date"])
        jour = date.fromisoformat(h["date"])
        for prov, zones in provinces.items():
            ici = cur.get(prov, {})
            for k, sortie in zones.items():
                z = ici.get(k) or {}
                cc, cd = z.get("cases"), z.get("deaths")
                pk = (prov, k)
                if prev_date is None:
                    sortie["casAvant"] = cc or 0
                    if cc is not None:
                        connu_c[pk] = (h["date"], cc)
                    continue
                if cd is not None and h["date"] == premiers_deces and pk in connu_c:
                    # Premier jour des deces par zone : le cumul n'est pas une journee.
                    sortie["decesAvant"] = cd
                    connu_d[pk] = (h["date"], cd)
                    cd = None
                dc = None if cc is None else cc - connu_c.get(pk, (None, 0))[1]
                dd = None if cd is None else cd - connu_d.get(pk, (None, 0))[1]
                rec = {"c": max(dc or 0, 0)}
                if dd is not None:
                    rec["d"] = max(dd, 0)
                    if pk in connu_d:
                        nd = (jour - date.fromisoformat(connu_d[pk][0])).days
                        if nd > 1 and nd != (jour - date.fromisoformat(prev_date)).days:
                            rec["nd"] = nd
                baisse = [min(dc or 0, 0), min(dd or 0, 0)]
                if hx and hx.get("province") == prov:
                    # Journee d'harmonisation : deces du jour du tableau 2.
                    rec["d"] = (hx.get("decesJourZones") or {}).get(sortie["nom"], 0)
                    rec["annonce"] = 1
                    baisse[1] = 0
                if any(baisse):
                    rec["baisse"] = baisse
                ecart = (jour - date.fromisoformat(prev_date)).days
                if ecart > 1:
                    rec["n"] = ecart
                if h["date"] in RATTRAPAGES:
                    rec["ratt"] = 1
                if cc is not None:
                    connu_c[pk] = (h["date"], cc)
                if cd is not None:
                    connu_d[pk] = (h["date"], cd)
                if rec["c"] or rec.get("d") or "baisse" in rec:
                    if not rec.get("d"):
                        rec.pop("d", None)
                        rec.pop("nd", None)
                    sortie["j"][h["date"]] = rec
        prev_date = h["date"]

    sitreps = {h["date"]: h.get("sitrep") for h in hist}
    for veille, num in appliquer_annonces(provinces).items():
        if veille in sans:
            sans.remove(veille)
        sitreps.setdefault(veille, num)

    return {
        "debut": dates[0], "fin": dates[-1], "premiersDeces": premiers_deces,
        "sansBulletin": sans,
        "sitrep": dict(sorted(sitreps.items())),
        "provinces": {prov: sorted(zones.values(), key=lambda z: (-z["cas"], z["nom"]))
                      for prov, zones in provinces.items()},
    }


def appliquer_annonces(provinces):
    """Separe les journees reunies d'apres les nouveaux cas et deces du jour
    publies par zone. Renvoie {veille calculee: numero du SitRep}."""
    chemin = os.path.join(ROOT, "data", "zones-jour-annonces.json")
    if not os.path.exists(chemin):
        return {}
    with open(chemin, encoding="utf-8") as f:
        annonces = json.load(f)
    veilles = {}
    for d, e in sorted(annonces.items()):
        veille = (date.fromisoformat(d) - timedelta(1)).isoformat()
        for prov, b in e["provinces"].items():
            zones = provinces.get(prov)
            if not zones:
                continue
            ann = {cle(n): v for n, v in b["zones"].items()}
            for champ, valide, part, empan in (("c", "casValides", "ca", "nc"), ("d", "decesValides", "da", "nd")):
                if not b.get(valide):
                    continue
                # Toutes les zones de la province ou aucune : un reste
                # negatif (cumul revu a la baisse) laisse la province entiere
                # en rattrapage.
                restes = {}
                for k, z in zones.items():
                    x = z["j"].get(d) or {}
                    restes[k] = x.get(champ, 0) - (ann.get(k) or {}).get(champ, 0)
                if any(r < 0 for r in restes.values()):
                    continue
                for k, z in zones.items():
                    x = z["j"].get(d)
                    if not x:
                        continue
                    n = x.get(empan) or x.get("n") or 1
                    if n <= 1 and not x.get("ratt"):
                        continue
                    a, r = x.get(champ, 0) - restes[k], restes[k]
                    if n == 2 and not x.get("ratt"):
                        # Une seule journee manque : elle prend le reste.
                        if r:
                            v = z["j"].setdefault(veille, {"c": 0})
                            v[champ] = r
                            v["calc"] = 1
                            veilles[veille] = "%03d" % (int(e["sitrep"]) - 1)
                        x[champ] = a
                        x[empan] = 1
                    else:
                        # Part du jour pleine, reste en rattrapage (aucun
                        # reste : la barre est pleine en entier).
                        x[part] = a
                for k, z in zones.items():
                    x = z["j"].get(d)
                    if x and not x.get("c") and not x.get("d") and "baisse" not in x:
                        del z["j"][d]
    for z in (z for zs in provinces.values() for z in zs.values()):
        z["j"] = dict(sorted(z["j"].items()))
    return veilles


def periode(zone, fin, jours):
    """Nouveaux cas et deces d'une zone sur les `jours` derniers jours
    (fin comprise)."""
    debut = (date.fromisoformat(fin) - timedelta(days=jours - 1)).isoformat()
    c = d = 0
    for k, v in zone["j"].items():
        if k >= debut:
            c += v.get("c", 0)
            d += v.get("d", 0)
    return c, d


def charger_historique():
    with open(os.path.join(ROOT, "data", "zones-history.json"), encoding="utf-8") as f:
        return json.load(f)


def ecrire(zones_history=None):
    donnees = calculer(zones_history if zones_history is not None else charger_historique())
    texte = json.dumps(donnees, ensure_ascii=False, separators=(",", ":")) + "\n"
    try:
        with open(SORTIE, encoding="utf-8") as f:
            if f.read() == texte:
                return donnees
    except OSError:
        pass
    with open(SORTIE, "w", encoding="utf-8") as f:
        f.write(texte)
    return donnees


if __name__ == "__main__":
    d = ecrire()
    print("%s -> %s, %d provinces, %d jours sans bulletin, %d octets"
          % (d["debut"], d["fin"], len(d["provinces"]), len(d["sansBulletin"]), os.path.getsize(SORTIE)))
