#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trois piliers que le pipeline ne lisait pas encore (8 septembre 2026) :
les points de controle et d'entree (PoC/PoE), la prevention (rings ouverts,
enterrements dignes et securises, EDS) et la vaccination Ervebo.

Les sections correspondantes des SitRep sont en prose, a tournures
variables ; on n'en retient que des nombres nommes sans ambiguite, et
l'absence d'un nombre laisse le champ vide (la lettre ecrit alors rien).
Sortie : data/piliers.json, une entree par bulletin (parDate).

Usage : python scripts/extract_piliers.py [--seulement 114]
"""
import io
import json
import os
import re
import sys

import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "piliers.json")

NUM = r"(\d{1,3}(?:[   ]\d{3})+|\d+)"
MOTS = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
        "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "quinze": 15, "vingt": 20}


def entier(s):
    return int(re.sub(r"[   ]", "", s))


def dates_par_numero():
    """SitRep -> date de rapportage, d'apres les series deja extraites."""
    m = {}
    for chemin, cle_num, cle_date in (("data/zones-history.json", "sitrep", "date"),
                                       ("data/alertes.json", "sitrepNumber", "date"),
                                       ("data/laboratoire.json", "sitrepNumber", "date"),
                                       ("data/cte.json", "sitrepNumber", "date")):
        with io.open(os.path.join(ROOT, chemin), encoding="utf-8") as fh:
            d = json.load(fh)
        for e in (d if isinstance(d, list) else d.get("parDate", [])):
            if e.get(cle_num) and e.get(cle_date):
                m.setdefault(str(e[cle_num]).zfill(3), e[cle_date])
    return m


def texte_pdf(chemin):
    with pdfplumber.open(chemin) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages)


def sections(txt):
    """Decoupe en sections « x.y. Titre » (les x.y.z. restent dedans)."""
    bornes = [m for m in re.finditer(r"\n\s*(\d\.\d{1,2})\.\s+(?!\d)([^\n]+)", txt)]
    out = []
    for i, m in enumerate(bornes):
        fin = bornes[i + 1].start() if i + 1 < len(bornes) else len(txt)
        out.append((m.group(2).strip(), txt[m.start():fin]))
    return out


def trouver(secs, *mots):
    for titre, corps in secs:
        t = titre.lower()
        if all(w in t for w in mots):
            return corps
    return None


def puces(corps):
    parts = re.split(r"\n\s*[•\-–]\s+", corps)
    return [" ".join(p.split()) for p in parts if p.strip()]


def nombre_ou_mot(s):
    s = s.strip().lower()
    return entier(s) if re.match(r"^[\d   ]+$", s) else MOTS.get(s)


def lire_pci(corps):
    """Rings ouverts / attendus et EDS (alertes, realisees, corps preleves,
    corps non preleves), sommes des provinces qui donnent le chiffre."""
    rings_o = rings_a = None
    eds = {"alertes": None, "realisees": None, "swabes": None, "nonSwabes": None}

    def add(cle, v):
        eds[cle] = (eds[cle] or 0) + v

    for p in puces(corps):
        for m in re.finditer(r"(\d+) rings? (?:ont été|a été) ouverts? (?:sur les|autour des|sur) (\d+)", p):
            rings_o = (rings_o or 0) + int(m.group(1)); rings_a = (rings_a or 0) + int(m.group(2))
        m = re.search(r"les (\d+) rings attendus ont tous été ouverts", p)
        if m:
            rings_o = (rings_o or 0) + int(m.group(1)); rings_a = (rings_a or 0) + int(m.group(1))
        if "EDS" not in p:
            continue
        m = (re.search(r"(\d+|[A-Za-zéÉ]+) alertes(?: EDS)? ont été enregistrées", p)
             or re.search(r"reçu (\d+) alertes", p) or re.search(r"(\d+) alertes ont été enregistrées", p))
        if m:
            v = nombre_ou_mot(m.group(1))
            if v is not None:
                add("alertes", v)
        m = re.search(r"(\d+) EDS réalis", p) or re.search(r"réalisé (\d+) EDS", p)
        if m:
            add("realisees", int(m.group(1)))
        m = re.search(r"(\d+) corps swab", p) or re.search(r"swabé (?:les )?(\d+) corps", p)
        if m:
            add("swabes", int(m.group(1)))
        m = re.search(r"(\d+) corps n[’']ayant pu", p) or re.search(r"(\d+) corps non swab", p)
        if m:
            add("nonSwabes", int(m.group(1)))
    rings = {"ouverts": rings_o, "attendus": rings_a} if rings_a else None
    eds = eds if any(v is not None for v in eds.values()) else None
    return rings, eds


PROVINCES = {"Ituri": "Ituri", "Nord-Kivu": "Nord-Kivu", "Nord Kivu": "Nord-Kivu", "Sud-Kivu": "Sud-Kivu", "Sud Kivu": "Sud-Kivu",
             "Haut-Uélé": "Haut-Uélé", "Haut Uélé": "Haut-Uélé", "Bas-Uélé": "Bas-Uélé", "Bas Uélé": "Bas-Uélé", "Tshopo": "Tshopo",
             "Buta": "Bas-Uélé", "Makiso": "Tshopo", "Kisangani": "Tshopo"}


def _province(phrase):
    """La province citee en premier dans la phrase (le texte des tableaux
    peut s'intercaler et citer d'autres provinces plus loin)."""
    meilleur = None
    for cle, nom in PROVINCES.items():
        i = phrase.find(cle)
        if i >= 0 and (meilleur is None or i < meilleur[0]):
            meilleur = (i, nom)
    return meilleur[1] if meilleur else None


def lire_vaccination(corps, texte_entier):
    """Personnes vaccinees Ervebo, EN CUMUL par province.

    Lecture des bulletins 104 a 114 (8 septembre 2026) : le SitRep ne donne
    jamais un nombre de vaccines du jour. Il ecrit soit un total depuis le
    debut (« Au total, 1 834 personnes ont ete vaccinees dont 1 375 a la
    Tshopo et 459 au Bas Uele », n°112 ; « cumul personnes vaccinees : 486 »,
    n°113), soit le nombre de personnes que le stock d'une zone a couvert
    (« au profit de 500 personnes ... portant le stock residuel a zero »,
    n°114, qui suit le cumul 486 de la veille), soit le chiffre du jour de
    lancement (20 PPL a Buta le 26 aout, 122 personnes a Kisangani le
    27 aout), qui est aussi un cumul ce jour-la. On range donc tout en
    cumulParProvince, et la lettre additionne les derniers cumuls connus."""
    t = " ".join((corps or texte_entier).split())
    cumul = {}
    def pose(prov, v):
        if prov and v is not None:
            cumul[prov] = max(cumul.get(prov, 0), v)
    prec = ""
    for phr in re.split(r"(?<=[.;])\s+", t):
        if "vaccin" not in phr.lower():
            prec = phr; continue
        # La province : citee avant le nombre dans la phrase, sinon dans la
        # phrase precedente (« Tshopo : lancement ... ; 122 personnes vaccinees »).
        _province_ici = lambda m: _province(phr[:m.start()]) or _province(prec) or _province(phr)
        m = re.search(r"Au total, " + NUM + r" personnes ont été vaccinées", phr)
        if m:
            for n, prov in re.findall(NUM + r" (?:à la|au|en) (Tshopo|Bas.Uélé|Haut.Uélé|Ituri|Nord.Kivu|Sud.Kivu)", phr):
                pose(_province(prov), entier(n))
            continue
        m = re.search(r"cumul (?:des )?personnes vaccinées\s*:\s*" + NUM, phr)
        if m:
            pose(_province_ici(m), entier(m.group(1))); prec = phr; continue
        m = re.search(r"au profit de " + NUM + r" personnes", phr)
        if m and ("vaccin" in phr.lower()):
            pose(_province_ici(m), entier(m.group(1))); prec = phr; continue
        m = re.search(NUM + r" (?:PPL|personnes)(?: de première ligne)? (?:ont été )?vaccinée?s", phr)
        if m:
            pose(_province_ici(m), entier(m.group(1)))
        prec = phr
    rupture = bool(re.search(r"[Rr]upture de stock d[’']Ervebo|stock résiduel à zéro", t))
    if not cumul and not rupture:
        return None
    return {"cumulParProvince": cumul, "rupture": rupture}


def _total_ligne(jetons):
    """Segmente des jetons (groupes de chiffres) en nombres a milliers et
    renvoie le dernier s'il vaut la somme des precedents, sinon None."""
    def segs(i):
        if i == len(jetons):
            yield []
            return
        if jetons[i] in ("ND", "NA"):
            for reste in segs(i + 1):
                yield [0] + reste
            return
        if len(jetons[i]) > 3:
            return
        j = i + 1
        while True:
            for reste in segs(j):
                yield [int("".join(jetons[i:j]))] + reste
            if j < len(jetons) and len(jetons[j]) == 3:
                j += 1
            else:
                break
    if len(jetons) > 24:
        return None
    for nombres in segs(0):
        if len(nombres) >= 3 and nombres[-1] == sum(nombres[:-1]) and nombres[-1] > 0:
            return nombres[-1]
    return None


def lire_poe(corps):
    t = corps
    m = re.search(r"Nombre de personnes((?:\s+(?:\d[\d ]*|ND|NA))+)", t)
    personnes = None
    if m:
        # Une ligne de tableau : six provinces puis le total, chiffres a
        # espaces de milliers (« 128 777 89 946 ... 4 996 258 604 »). Le
        # decoupage est ambigu ; on retient la segmentation dont le dernier
        # nombre est la somme des autres.
        jetons = re.findall(r"\d+|ND|NA", m.group(1))
        personnes = _total_ligne(jetons)
    m = re.search(r"% des voyageurs screenés((?:\s+(?:[\d,]+\s*%|ND|NA))+)", t)
    pct = None
    if m:
        p = re.findall(r"([\d,]+)\s*%", m.group(1))
        if p:
            pct = float(p[-1].replace(",", "."))
    refus = sum(entier(x) for x in re.findall(NUM + r" refus de (?:screening|dépistage)", " ".join(t.split())))
    if personnes is None and pct is None and not refus:
        return None
    return {"personnes": personnes, "screenesPct": pct, "refusScreening": refus or 0}


def extraire(num, chemin, date):
    txt = texte_pdf(chemin)
    secs = sections(txt)
    poe = trouver(secs, "point", "contr") or trouver(secs, "poc/poe")
    pci = trouver(secs, "pci") or trouver(secs, "prévention")
    vac = trouver(secs, "vaccination")
    rings, eds = lire_pci(pci) if pci else (None, None)
    return {"date": date, "sitrepNumber": num,
            "poe": lire_poe(poe) if poe else None,
            "rings": rings, "eds": eds,
            "vaccination": lire_vaccination(vac, txt),
            "source": "SitRep INSP (automatique)"}


def main(argv):
    seulement = None
    if "--seulement" in argv:
        seulement = argv[argv.index("--seulement") + 1].zfill(3)
    dates = dates_par_numero()
    existant = {}
    if os.path.exists(OUT):
        with io.open(OUT, encoding="utf-8") as fh:
            existant = {e["sitrepNumber"]: e for e in json.load(fh).get("parDate", [])}
    for f in sorted(os.listdir(os.path.join(ROOT, "reports"))):
        m = re.match(r"SITREP_MVE_(\d+)\.pdf$", f)
        if not m:
            continue
        num = m.group(1).zfill(3)
        if seulement and num != seulement:
            continue
        if num not in dates:
            continue
        try:
            existant[num] = extraire(num, os.path.join(ROOT, "reports", f), dates[num])
        except Exception as e:  # un PDF illisible ne bloque pas les autres
            sys.stderr.write("%s : %s\n" % (f, e))
    entrees = sorted(existant.values(), key=lambda e: e["date"])
    out = {"periode": {"debut": entrees[0]["date"], "fin": entrees[-1]["date"]} if entrees else {},
           "parDate": entrees}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("%d bulletins -> %s" % (len(entrees), os.path.relpath(OUT, ROOT)))


if __name__ == "__main__":
    main(sys.argv[1:])
