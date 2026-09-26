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
    # Combien de provinces alimentent chaque champ. Les trois nombres ne
    # couvrent PAS forcement les memes : au 111, seul l'Ituri publie ses
    # alertes quand le Nord-Kivu ne donne que ses EDS et ses swabs, si bien
    # que les EDS realises depassent les alertes sans que rien soit faux.
    # Sans ce compte, la lettre alignait trois nombres incomparables.
    eds_prov = {"alertes": set(), "realisees": set(), "swabes": set(), "nonSwabes": set()}
    puce_en_cours = [0]

    def add(cle, v):
        eds[cle] = (eds[cle] or 0) + v
        eds_prov[cle].add(puce_en_cours[0])

    for numero_puce, p in enumerate(puces(corps)):
        puce_en_cours[0] = numero_puce
        for m in re.finditer(r"(\d+) rings?(?: ouverts?)? (?:ont été|a été) ouverts? (?:sur les|autour des|sur) (\d+)", p):
            rings_o = (rings_o or 0) + int(m.group(1)); rings_a = (rings_a or 0) + int(m.group(2))
        m = re.search(r"les (\d+) rings attendus ont tous été ouverts", p)
        if m:
            rings_o = (rings_o or 0) + int(m.group(1)); rings_a = (rings_a or 0) + int(m.group(1))
        # Le sigle ne suffit pas : au 103, la Tshopo ecrit « Deux alertes de
        # deces ont ete recues et 2 corps swabes » sans jamais dire « EDS »,
        # et la puce entiere etait sautee.
        if not re.search(r"\bEDS\b|enterrement|inhum|swab|[ée]couvillon|corps pr[ée]lev", p, re.IGNORECASE):
            continue
        # Un motif par tournure vue dans le corpus ; le premier qui mord
        # l'emporte, mais PHRASE PAR PHRASE : une puce peut porter deux
        # provinces (au 103, le Nord-Kivu et la Tshopo dans la meme), et une
        # lecture par puce perdait la seconde.
        #
        # Exception, le recapitulatif « soit N EDS sur M alertes » : quand il
        # est la, la phrase qui precede detaille les memes EDS par lieu
        # (menages, structures de soins, CTE) et tout compter doublerait le
        # total. Il vaut alors pour la puce entiere.
        #
        # Tournures ajoutees le 19 septembre 2026, apres la question d'un
        # lecteur sur l'origine de ces chiffres : « 70 EDS ont ete realises »
        # en phrase isolee (101, Ituri), « 62 ont ete swabes » (101), « les 2
        # corps ont ete swabes » (101), « 61 alertes ont ete recues » (121,
        # Nord-Kivu, la ou le motif attendait « enregistrees »), « Deux
        # alertes de deces ont ete recues » (103, Tshopo, nombre en lettres),
        # et les formes anciennes « N corps preleves post-mortem » ou « par
        # ecouvillonnage » (084 a 100).
        MOT = r"(\d+|[A-Za-zéÉ]+)"
        MOTIFS = (
            ("alertes", [MOT + r" alertes?(?: EDS)?(?: de d[ée]c[èe]s)? (?:ont|a) [ée]t[ée] (?:enregistr|re[çc]u)",
                         r"re[çc]u " + MOT + r" alertes?",
                         r"EDS r[ée]alis\w+ sur (\d+) alertes",
                         MOT + r" alertes?(?: EDS)? re[çc]ues?",
                         MOT + r" alertes? de d[ée]c[èe]s"]),
            ("realisees", [r"(\d+) EDS (?:ont [ée]t[ée] |a [ée]t[ée] )?r[ée]alis",
                           r"r[ée]alis[ée] (?:les )?(\d+) EDS"]),
            ("swabes", [r"(\d+) corps (?:ont [ée]t[ée] |a [ée]t[ée] )?(?:pr[ée]lev|swab|[ée]couvillonn)",
                        r"(\d+) corps (?:ont [ée]t[ée] )?swab",
                        r"swab[ée] (?:les )?(\d+) corps",
                        r"les (\d+) corps ont [ée]t[ée] swab",
                        r"(\d+) ont [ée]t[ée] swab",
                        r"(\d+) corps pr[ée]lev"]),
            ("nonSwabes", [r"(\d+) corps n[’']ayant pu",
                           r"(\d+) corps non swab",
                           r"(\d+) corps n[’']ont pu [êe]tre swab",
                           r"(\d+) n[’']ont pas pu [êe]tre swab"]),
        )

        def lire_phrase(txt, cles):
            for cle, motifs in MOTIFS:
                if cle not in cles:
                    continue
                for motif in motifs:
                    m = re.search(motif, txt, re.IGNORECASE)
                    if m:
                        v = nombre_ou_mot(m.group(1))
                        if v is not None:
                            add(cle, v)
                        break

        recap = re.search(r"soit (\d+) EDS sur (\d+) alertes", p, re.IGNORECASE)
        if recap:
            add("realisees", int(recap.group(1)))
            add("alertes", int(recap.group(2)))
            restantes = {"swabes", "nonSwabes"}
        else:
            restantes = {"alertes", "realisees", "swabes", "nonSwabes"}
        for phrase in re.split(r"\s*;\s*|(?<=[.)])\s+(?=[A-ZÀ-Ý])", p):
            lire_phrase(phrase, restantes)

    rings = {"ouverts": rings_o, "attendus": rings_a} if rings_a else None
    if any(v is not None for v in eds.values()):
        eds["provinces"] = {k: len(v) for k, v in eds_prov.items() if v}
    else:
        eds = None
    return rings, eds


PROVINCES = {"Ituri": "Ituri", "Nord-Kivu": "Nord-Kivu", "Nord Kivu": "Nord-Kivu", "Sud-Kivu": "Sud-Kivu", "Sud Kivu": "Sud-Kivu",
             "Haut-Uélé": "Haut-Uélé", "Haut Uélé": "Haut-Uélé", "Bas-Uélé": "Bas-Uélé", "Bas Uélé": "Bas-Uélé", "Tshopo": "Tshopo",
             "Buta": "Bas-Uélé", "Makiso": "Tshopo", "Kisangani": "Tshopo",
             "Sud-Ubangi": "Sud-Ubangi", "Sud Ubangi": "Sud-Ubangi", "Bulu": "Sud-Ubangi"}


def _province(phrase):
    """La province citee en premier dans la phrase (le texte des tableaux
    peut s'intercaler et citer d'autres provinces plus loin)."""
    meilleur = None
    for cle, nom in PROVINCES.items():
        i = phrase.find(cle)
        if i >= 0 and (meilleur is None or i < meilleur[0]):
            meilleur = (i, nom)
    return meilleur[1] if meilleur else None


# ---------------------------------------------------------------- vaccination
# Le detail que la section « 1.6. Vaccination » publie depuis le 8 septembre
# 2026 (SitRep 117), toujours sous la meme tournure :
#
#   « À la Tshopo, 3 369 personnes ont été vaccinées à ce jour sur 11 703
#     TPL/PPL ciblés (28,8 %), dont 1 830 à Makiso-Kisangani, 466 à Kabondo,
#     422 à Mangobo, 316 à Tshopo, 173 à Bafwasende et 162 à Lubunga ; le
#     stock disponible au dépôt Hub s'élève à 500 doses congelées et 631
#     doses décongelées expirant le 24 septembre 2026. »
#
# Le Bas-Uele ecrit la meme chose sans cible : « 708 PPL ont été vaccinées à
# ce jour, dont 550 à Buta et 158 à Ganga ».
VAC_CUMUL_RE = re.compile(
    NUM + r"\s+(?:PPL|TPL|personnes)\s+ont\s+été\s+vaccinée?s\s+à\s+ce\s+jour", re.I)
# Depuis le SitRep 130 (21 septembre 2026), section renumerotee « 2.6 » et
# nouvelle tournure, sans « à ce jour » : « À la Tshopo, 3 874 TPL et PPL ont
# été vaccinés sur 3 549 pré-enregistrés (109 %), soit 33 % de la cible de
# 11 703, dont 1 909 à Makiso-Kisangani… » (131). Le 130 est parti en ligne
# sans son cumul (3 774) faute de ce motif : rattrape a l'integration du 131.
VAC_CUMUL_TPL_RE = re.compile(
    NUM + r"\s+(?:TPL\s+et\s+PPL|PPL\s+et\s+TPL)\s+ont\s+été\s+vaccinée?s", re.I)
VAC_CIBLE_SOIT_RE = re.compile(
    r"soit\s+(\d+(?:[,.]\d+)?)\s*%\s+de\s+la\s+cible\s+de\s+" + NUM, re.I)
VAC_CIBLE_RE = re.compile(
    r"sur\s+" + NUM + r"\s+(?:TPL/PPL\s+)?(?:cibles?|ciblés|ciblées)"
    r"(?:\s+TPL/PPL)?\s*\(\s*(\d+(?:[,.]\d+)?)\s*%", re.I)
# « dont 1 830 à Makiso-Kisangani, 466 à Kabondo … et 162 à Lubunga » : on ne
# lit QUE ce segment, jusqu'au point-virgule ou a la fin de la phrase, sinon
# le motif mord sur « 500 doses à Bafwasende » et sur les autres piliers.
VAC_DONT_RE = re.compile(r"\bdont\s+((?:\d[\d   ]*\d|\d)\s+à\s+[^;.]{0,220})", re.I)
VAC_ZONE_RE = re.compile(
    r"(\d[\d   ]*\d|\d)\s+à\s+([A-ZÉÈÀ][\w’'\-]*(?:[- ][A-ZÉÈÀ][\w’'\-]*)*)")
VAC_CONGELEES_RE = re.compile(NUM + r"\s+doses\s+congelées", re.I)
VAC_DECONGELEES_RE = re.compile(NUM + r"\s+doses\s+décongelées", re.I)
VAC_SOLDE_RE = re.compile(
    r"(?:solde|stock)[^;.]{0,70}?(?:s[’']\s*(?:élève|établit|établissant)\s+à|de)\s+" + NUM + r"\s+doses", re.I)
# « le solde s'établissant à 721 doses au niveau des zones et à 2 000 doses
# congelées au dépôt Hub » (118, 119) : deux soldes dans la meme phrase.
VAC_AUX_ZONES_RE = re.compile(NUM + r"\s+doses\s+au\s+niveau\s+des\s+zones", re.I)
VAC_DEPLOYEES_RE = re.compile(NUM + r"\s+doses\s+ont\s+été\s+déployées", re.I)
# « Insuffisance des doses disponibles à la Tshopo (4 500 reçues pour 11 000
# exprimées) » : la tension d'approvisionnement, citee dans les Defis.
VAC_RECUES_RE = re.compile(
    r"\(\s*" + NUM + r"\s+reçues\s+pour\s+" + NUM + r"\s+exprimées", re.I)
VAC_PEREMPTION_RE = re.compile(
    r"(?:expirant|péremption[^;.]{0,30}?)\s+(?:le|au)\s+(\d{1,2}\s+\w+\s+\d{4})", re.I)
VAC_MAPI_RE = re.compile(NUM + r"\s+MAPI\s+mineures", re.I)
VAC_MAPI_GRAVE_RE = re.compile(r"(?:sans\s+aucune|aucune)\s+MAPI\s+grave", re.I)
# Les entrees de la section, une par province.
VAC_ENTREE_RE = re.compile(
    r"(?:À|A)\s+la\s+Tshopo|Au\s+Bas[-\s]?Uélé|En\s+Ituri|Au\s+Nord[-\s]?Kivu"
    r"|Au\s+Haut[-\s]?Uélé|Au?\s+Sud[-\s]?Ubangi|Au\s+Sud[-\s]?Kivu", re.I)

MOIS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
        "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9,
        "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12}


def _date_iso(texte):
    m = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", texte.strip())
    if not m or m.group(2).lower() not in MOIS:
        return None
    return "%s-%02d-%02d" % (m.group(3), MOIS[m.group(2).lower()], int(m.group(1)))


def _segments_provinces(t):
    """La section decoupee en un morceau par province citee."""
    bornes = list(VAC_ENTREE_RE.finditer(t))
    for i, m in enumerate(bornes):
        fin = bornes[i + 1].start() if i + 1 < len(bornes) else len(t)
        prov = _province(m.group(0))
        if prov:
            yield prov, t[m.start():fin]


def lire_vaccination_detail(corps):
    """{province: {cumul, cible, couverture, zones, zonesSomme, doses, mapi}}

    Le taux publie suit la cible que le bulletin cite, et celle-ci a change
    sous nos yeux : 11 703 au 117, 11 000 aux 118 et 119, 11 703 ensuite. On
    garde les deux nombres bruts, a charge du site de recalculer s'il veut une
    serie comparable.

    La somme des zones tombe exactement sur le cumul dans neuf bulletins sur
    dix — mais le 124 recopie la ventilation du 123 (somme 2 460 pour un cumul
    2 544). On garde la somme a cote du cumul : un graphique qui empile les
    zones doit savoir qu'il lui manque 84 personnes ce jour-la."""
    out = {}
    t = " ".join((corps or "").split())
    for prov, seg in _segments_provinces(t):
        ligne = {}
        m = VAC_CUMUL_RE.search(seg) or VAC_CUMUL_TPL_RE.search(seg)
        if m:
            ligne["cumul"] = entier(m.group(1))
        m = VAC_CIBLE_RE.search(seg)
        if m:
            ligne["cible"] = entier(m.group(1))
            ligne["couverture"] = float(m.group(2).replace(",", "."))
        else:
            m = VAC_CIBLE_SOIT_RE.search(seg)
            if m:
                ligne["cible"] = entier(m.group(2))
                ligne["couverture"] = float(m.group(1).replace(",", "."))
        m = VAC_DONT_RE.search(seg)
        if m:
            zones = {}
            for n, nom in VAC_ZONE_RE.findall(m.group(1)):
                nom = nom.strip()
                if nom not in zones:
                    zones[nom] = entier(n)
            if zones:
                ligne["zones"] = zones
                ligne["zonesSomme"] = sum(zones.values())
        doses = {}
        mc, md = VAC_CONGELEES_RE.search(seg), VAC_DECONGELEES_RE.search(seg)
        if mc:
            doses["congelees"] = entier(mc.group(1))
        if md:
            doses["decongelees"] = entier(md.group(1))
        mz = VAC_AUX_ZONES_RE.search(seg)
        if mz:
            doses["auxZones"] = entier(mz.group(1))
        mdep = VAC_DEPLOYEES_RE.search(seg)
        if mdep:
            doses["deployees"] = entier(mdep.group(1))
        if not doses:
            ms = VAC_SOLDE_RE.search(seg)
            if ms:
                doses["disponibles"] = entier(ms.group(1))
        mr = VAC_RECUES_RE.search(seg)
        if mr:
            doses["recues"] = entier(mr.group(1))
            doses["exprimees"] = entier(mr.group(2))
        mp = VAC_PEREMPTION_RE.search(seg)
        if mp:
            iso = _date_iso(mp.group(1))
            if iso:
                doses["peremption"] = iso
        if doses:
            ligne["doses"] = doses
        mm = VAC_MAPI_RE.search(seg)
        if mm:
            ligne["mapi"] = {"mineures": entier(mm.group(1)),
                             "graves": 0 if VAC_MAPI_GRAVE_RE.search(seg) else None}
        # Une province peut revenir dans « Défis » apres « Principales
        # actions » : au 127, « risque de péremption des 631 doses » y ajoute
        # une date que le premier morceau n'a pas. On complete donc sans
        # jamais ecraser — sinon le cumul de la Tshopo disparaissait derriere
        # le paragraphe des defis (vu le 20 septembre 2026).
        if not ligne:
            continue
        deja = out.setdefault(prov, {})
        for cle, val in ligne.items():
            if isinstance(val, dict) and isinstance(deja.get(cle), dict):
                for k, v in val.items():
                    deja[cle].setdefault(k, v)
            else:
                deja.setdefault(cle, val)
    return out


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
    # La puce « • » separe aussi deux provinces : au 133, « La Tshopo n'a
    # transmis aucune donnée de vaccination • En Ituri, [...] 135 personnes
    # ont été vaccinées » donnait 135 vaccines a la Tshopo (4 058 la veille).
    for phr in re.split(r"(?<=[.;])\s+|\s*•\s*", t):
        if "vaccin" not in phr.lower():
            prec = phr; continue
        # Un chiffre du jour n'est pas un cumul (Ituri, 133 : « 135 personnes
        # ont été vaccinées au cours des dernières 24 heures »).
        if re.search(r"derni[èe]res 24 ?h", phr):
            prec = phr; continue
        # La province : citee avant le nombre dans la phrase, sinon dans la
        # phrase precedente (« Tshopo : lancement ... ; 122 personnes vaccinees »).
        _province_ici = lambda m: _province(phr[:m.start()]) or _province(prec) or _province(phr)
        m = re.search(r"Au total, " + NUM + r" personnes ont été vaccinées", phr)
        if m:
            for n, prov in re.findall(NUM + r" (?:à la|au|en) (Tshopo|Bas.Uélé|Haut.Uélé|Sud.Ubangi|Ituri|Nord.Kivu|Sud.Kivu)", phr):
                pose(_province(prov), entier(n))
            continue
        # « 66 PPL ont été vaccinés à Bunia du 21 au 23 septembre, portant le
        # cumul à 96 » (132) : le cumul est le second nombre, pas le premier.
        m = re.search(r"portant le cumul à " + NUM, phr)
        if m:
            pose(_province_ici(m), entier(m.group(1))); prec = phr; continue
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
    detail = lire_vaccination_detail(corps)
    # Le cumul detaille fait foi quand il existe : il vient de la tournure
    # explicite « N ont été vaccinées à ce jour », la plus sure des deux.
    for prov, ligne in detail.items():
        if ligne.get("cumul") is not None:
            cumul[prov] = max(cumul.get(prov, 0), ligne["cumul"])
    if not cumul and not rupture and not detail:
        return None
    out = {"cumulParProvince": cumul, "rupture": rupture}
    if detail:
        out["provinces"] = detail
    return out


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
    # Les SitReps 123 et 124 (14 et 15 septembre 2026) coupent autrement le
    # libelle de la ligne : « Nombre de personnes passées aux 147 864 … PoE/PoC »
    # — « passées aux » s'intercale avant les nombres, et le total manquait.
    m = re.search(r"Nombre de personnes(?:\s+passées\s+aux)?((?:\s+(?:\d[\d ]*|ND|NA))+)", t)
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
