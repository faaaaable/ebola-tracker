#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patients hospitalisés, lits et taux d'occupation des CTE, par province.

Lit chaque bulletin et écrit data/cte.json. C'est le chiffre qui explique
l'onglet « Décès en communauté » : quand le centre de traitement est plein, on
meurt chez soi.

Deux sources selon l'époque :

  C  (059-083) un tableau « OCCUPATION DES STRUCTURES DE SOINS » avec une
     colonne par province : « Nombre de lits 709 141 ND 10 860 » et
     « Patients au lit (J-1) 551 170 ND 3 724 ».
  D  (084-…)  une puce par province en prose :
     « l'occupation atteint 501 patients pour 840 lits (60 %) »
     « 470 patients sont hospitalisés (172 confirmés et 298 suspects) pour
       996 lits, soit un taux d'occupation de 47,2 % »
     « 167 malades sont hospitalisés pour 206 lits, soit 81,1 % d'occupation »
     « une nouvelle admission … portent à 4 le nombre de patients isolés
       (1 confirmé et 3 suspects) pour 14 lits, soit 28,6 % d'occupation »

L'époque B ne publie que « Patients au lit » sans le nombre de lits : la
série des hospitalisés remonte plus loin que celle de l'occupation, et le
graphique ne trace l'occupation que là où les lits sont connus. Une province
dont on ne lit pas les patients est écartée ce jour-là. L'occupation par CTE
(« Isiro 120 % ») reste de la prose : non sommable, elle n'entre pas ici.

Le taux d'occupation publié fait foi ; s'il manque, il est recalculé et
marqué comme tel (`occupationCalculee`). Un taux au-dessus de 100 % est
possible et publié tel quel par la source.

    python scripts/extraire_cte.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textes_pdf import ROOT, rapports, numero, texte_du_rapport, entier, pourcent  # noqa: E402
from update_data import extract_meta, PROVINCE_CANON  # noqa: E402

OUTPUT_PATH = os.path.join(ROOT, "data", "cte.json")

PROVINCES_RE = r"Ituri|Nord[\s-]+Kivu|Haut[\s-]+U[ée]l[ée]|Tshopo|Sud[\s-]+Kivu|Bas[\s-]+U[ée]l[ée]|Sud[\s-]+Ubangi|Nord[\s-]+Ubangi"


def canon(nom):
    """« Haut Uélé », « Haut-Uele », « Haut\nUélé » -> « Haut-Uélé », etc."""
    n = re.sub(r"[\s-]+", " ", nom).replace("Uele", "Uélé").replace("Uelé", "Uélé").replace("Uélè", "Uélé")
    n = {"Nord Kivu": "Nord-Kivu", "Sud Kivu": "Sud-Kivu", "Haut Uélé": "Haut-Uélé", "Sud Ubangi": "Sud-Ubangi", "Nord Ubangi": "Nord-Ubangi"}.get(n, n)
    return PROVINCE_CANON.get(n, n)


# ---------------------------------------------------------------- prose (D)
# La prose n'est lue que sous le titre de l'époque D, « Continuité des
# soins ». Sous « Prise en charge » (B, C) la même section aligne des cumuls
# et des indicateurs qui ressemblent à des hospitalisés du jour — le 060
# donnait 753 hospitalisés au Nord-Kivu, son cumul de cas — et ces époques
# ont un tableau, lu en premier.
# Le SitRep 109 (31 août) renomme la section « Prise en charge holistique »,
# avec la meme prose que « Continuite des soins » (« 539 patients sont
# hospitalises pour 978 lits, soit un taux d'occupation de 55,1 % »). Le mot
# « holistique » la distingue du « Prise en charge » des epoques B et C, qui
# reste exclu.
DEBUT_RE = re.compile(r"(?:^|\n)[^\n]{0,12}(?:Continuit[ée] des soins|Prise en charge holistique)[^\n]{0,60}\n", re.IGNORECASE)
FIN_RE = re.compile(r"\n[^\n]{0,12}(?:Communication|CREC|Logistique|S[ée]curit[ée]|Recherche)", re.IGNORECASE)
# « Le Nord-Kivu suit avec 8 patients en isolement », « Le Sud-Kivu maintient
# une file active de 5 patients » (SitRep 018) : sans « Le », ces phrases
# restaient dans le morceau de l'Ituri, qui recevait les 8 patients du
# Nord-Kivu. Corrige le 4 septembre 2026.
REPERE_RE = re.compile(r"(?:^|[\n•→▪\-\uf000-\uf0ff]|\bEn |\bAu |\bÀ la |\bA la |\bau |\ben |\bà la |\bLe |\bL[’'])\s*(%s)\b" % PROVINCES_RE)

CAS_CONF_SUSP_RE = re.compile(r"(\d[\d ]{0,4}\d|\d)\s+cas\s+confirm[ée]s\s+et\s+(\d[\d ]{0,4}\d|\d)\s+cas\s+suspects\s+"
                              r"(?:sont\s+(?:actuellement\s+)?hospitalis|isol[ée]s)", re.I)
SOMME_RES = (CAS_CONF_SUSP_RE,)
HOSPITALISES_RES = [
    # SitRep 150 (11 octobre 2026, Nord-Kivu) : « 471 patients dont 67
    # enfants de moins de 5 ans) sont hospitalisés : 330 dans les CTE/CT pour
    # 374 lits » — une incise en « dont », parenthese ouvrante oubliee.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s*\(?\s*dont\s[^)]{0,60}\)\s*sont\s+hospitalis", re.I),
    # « 328 patients (97 confirmés et 231 suspects) sont hospitalisés, dont
    # 223 dans les CTE pour 354 lits » (135, Nord-Kivu) : la ventilation
    # s'intercale entre « patients » et le verbe. Sans ce motif, la ligne
    # prenait les « 105 autres » pris en charge hors CTE.
    # 151 : « 445 patients (176 confirmés et 269 suspects, dont 52 enfants de
    # moins de 5 ans) sont hospitalisés » — 66 caracteres dans la parenthese.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s*\(\s*\d[^)]{0,90}\)\s*sont\s+hospitalis", re.I),
    re.compile(r"occupation\s+atteint\s+(\d[\d ]{0,4}\d|\d)\s+patients", re.I),
    # « Au total, 368 patients demeuraient en isolement à la fin de la
    # journée » et « 345 patients demeuraient hospitalisés » (136).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+demeuraient\s+(?:en\s+isolement|hospitalis)", re.I),
    # SitRep 144 (5 octobre 2026) : la ventilation s'intercale aussi avant
    # « demeuraient » et « sont en isolement » — « 417 patients (139
    # confirmés et 278 suspects) demeuraient hospitalisés » (Nord-Kivu),
    # « 18 patients (8 confirmés et 10 suspects) demeuraient en isolement »
    # (Tshopo), « 60 patients (31 confirmés et 29 suspects) sont en
    # isolement dans les CTE » (Haut-Uele).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s*\(\s*\d[^)]{0,60}\)\s*(?:demeuraient|sont)\s+(?:en\s+isolement|hospitalis)", re.I),
    # « Au total, 595 patients (197 confirmés et 398 suspects, dont 67 enfants
    # de moins de 5 ans et 27 malades critiques) restent en isolement » (173 et
    # 174, Nord-Kivu ; 174 Haut-Uele) : « restent », et une parenthese plus
    # longue. Sans ce motif, le Nord-Kivu n'etait lu que dans les « Defis »
    # (« 210 patients sont pris en charge hors CTE/CT ») : trouve le 6 novembre 2026.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s*\(\s*\d[^)]{0,110}\)\s*restent\s+en\s+(?:isolement|hospitalisation)", re.I),
    # « L'occupation des structures de prise en charge atteint 488 lits sur
    # 833 (59 %) » (084, 6 aout) : les patients comptes en lits occupes.
    re.compile(r"occupation[^.;]{0,60}?atteint\s+(\d[\d ]{0,4}\d|\d)\s+lits\s+sur\s+\d", re.I),
    # « 53 patients sont pris en charge (36 confirmés et 17 suspects) » (097,
    # Haut-Uele) : la ventilation entre parentheses ancre la tournure.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+patients\s+sont\s+pris\s+en\s+charge\s*\(\d", re.I),
    # « Ainsi, 447 patients sont pris en charge dont 61 enfants de moins de
    # 5 ans, 5 malades critiques et 107 hors CTE/CT » (162, Nord-Kivu) : sans
    # parenthese, la province manquait et le total tombait a 571 pour 1 018.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+patients\s+sont\s+pris\s+en\s+charge,?\s+dont\s+\d", re.I),
    # « 39 cas confirmés restent hospitalisés » (156, Haut-Uele)
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades|cas suspects|cas\s+confirm[ée]s|cas)\s+(?:sont|restent|demeurent)?\s*(?:en\s+)?hospitalis", re.I),
    # « Huit (8) patients sont en isolement pour 25 lits » (109 Sud-Kivu) : le
    # nombre est entre parentheses, d'ou la parenthese fermante optionnelle.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\)?\s+(?:patients|malades)\s+sont\s+(?:en\s+)?isol", re.I),
    re.compile(r"port(?:e|ent|ant)\s+à\s+(\d[\d ]{0,4}\d|\d)\s+le\s+nombre\s+de\s+patients", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+(?:en\s+)?(?:hospitalisation|isolement)", re.I),
    # « 472 patients sont pris en charge en hospitalisation pour 1015 lits » et
    # « 7 patients restent en isolement » (122) : un verbe s'intercale entre les
    # patients et le mot qui les qualifie, que les motifs ci-dessus collent.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+(?:sont\s+pris\s+en\s+charge\s+en|restent\s+en|demeurent\s+en|sont\s+plac[ée]s?\s+en)\s+(?:hospitalisation|isolement)", re.I),
    # « Au terme de la journee, 62 patients, soit un taux d'occupation global
    # de 51,7% (120 lits) » (110 Haut-Uele) : ni « hospitalises » ni
    # « isolement », le nombre de patients est directement suivi du taux.
    # En dernier, pour ne jamais prendre le pas sur les tournures explicites.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades),?\s+soit\s+un\s+taux\s+d[’']occupation", re.I),
    # « L'Ituri concentre 91 % des patients hospitalisés (158/171) » et « une
    # file active de 5 patients au CTE Lwiro » (018, epoque A tardive).
    re.compile(r"patients\s+hospitalis\w*\s*\((\d[\d ]{0,4}\d|\d)\s*/\s*\d", re.I),
    re.compile(r"file\s+active\s+de\s+(\d[\d ]{0,4}\d|\d)\s+patients", re.I),
    # Tournures d'octobre 2026, lues en dernier (29 octobre 2026) :
    # « 523 patients (178 confirmés et 345 suspects) sont pris en charge, dont
    # 160 hors CTE/CT » (166 Nord-Kivu), « 497 patients sont pris en charge
    # CTE/CT » (164 Nord-Kivu), « 32 patients (16 confirmés et 16 suspects)
    # hospitalisés pour 149 lits » (165-166 Haut-Uele, sans « sont ») et
    # « 124 patients suspects demeurent en isolement » (165 Bas-Uele).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s*(?:\(\s*\d[^)]{0,90}\)\s*)?sont\s+pris\s+en\s+charge\b", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s*\(\s*\d[^)]{0,90}\)\s*hospitalis", re.I),
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)(?:\s+(?:suspects|confirm[ée]s))?\s+demeurent\s+en\s+(?:isolement|hospitalisation)", re.I),
    # « Six suspects restent isolés (Dakwa 1, Viadana 2 et Ganga 3) avec 2
    # confirmés » (153 Bas-Uele) : les deux.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+suspects\s+restent\s+isol[ée]s\s*\([^)]{0,60}\)\s*avec\s+(\d[\d ]{0,4}\d|\d)\s+confirm", re.I),
    # « 47 suspects restent isolés dans les ESS faute de CTE fonctionnel »
    # (173 et 174, Bas-Uele).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+suspects\s+restent\s+isol[ée]s", re.I),
    # Tournures relevees le 11 novembre 2026 en recoupant la somme des
    # provinces avec le chiffre national du bandeau, bulletin par bulletin :
    # « 6 patients (1 confirmé à Ganga et 5 suspects) demeurent en isolement »
    # (132-135 Bas-Uele), « 16 patients suspects étaient en isolement » (141),
    # « 12 patients (5 confirmés et 7 suspects) sont isolés » (175
    # Nord-Ubangi), « Au total, 68 patients demeuraient en 6 isolement » (149
    # Haut-Uele, numero de page colle dans la phrase).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)(?:\s+(?:suspects|confirm[ée]s))?\s*(?:\(\s*\d[^)]{0,90}\)\s*)?"
               r"(?:demeurent|demeuraient|[ée]taient|restent|sont)\s+(?:en\s+(?:\d{1,2}\s+)?isolement|isol[ée]s)", re.I),
    # « 29 suspects demeuraient en isolement » (144 Bas-Uele), « 10 cas
    # suspects sont isolés » (146 Bas-Uele).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:cas\s+)?suspects\s+(?:demeurent|demeuraient|restent|sont)\s+(?:en\s+isolement|isol[ée]s)", re.I),
    # « et 52 en isolement à la fin de la journée » (143 Bas-Uele).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+en\s+isolement\s+[àa]\s+la\s+fin\s+de\s+la\s+journ[ée]e", re.I),
    # « au total, 26 patients sont rapportés en isolement » (148 Bas-Uele).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+patients\s+sont\s+rapport[ée]s\s+en\s+isolement", re.I),
    # « portant à 106 le nombre de suspects isolés » (167, 169-171 Bas-Uele),
    # « ramenant à 38 le nombre… » (168).
    re.compile(r"(?:portant|ramenant)\s+[àa]\s+(\d[\d ]{0,4}\d|\d)\s+le\s+nombre\s+de\s+(?:suspects|patients|cas)\s+(?:isol|en\s+isolement|hospitalis)", re.I),
    # « Le total des patients actuellement en isolement s'élève à 18 cas
    # suspects » (179 Bas-Uele).
    re.compile(r"total\s+des\s+patients\s+(?:actuellement\s+)?en\s+isolement\s+s[’']\s*[ée]l[eè]ve\s+[àa]\s+(\d[\d ]{0,4}\d|\d)", re.I),
    # « 6 patients (2 confirmés, 4 suspects) au CTE Météo » (178 Tshopo).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+patients\s*\(\s*\d[^)]{0,60}\)\s*aux?\s+(?:CTE|CT|lits)\b", re.I),
    # « 21 confirmés et 34 suspects aux lits » (178 Haut-Uele) : la somme.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+confirm[ée]s\s+et\s+(\d[\d ]{0,4}\d|\d)\s+suspects\s+aux\s+lits\b", re.I),
    # « 364 patients aux lits (124 confirmés, 240 suspects) » (Ituri, 178 et
    # 179 ; Nord-Kivu au 178) : jamais lu, l'Ituri disparaissait du
    # graphique. En dernier : au 147, « 523 patients demeuraient en
    # isolement (…325 patients aux lits des CTE/CT…) », le total passe avant.
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+aux\s+lits\b", re.I),
    # Tournures du 180 (10 novembre 2026) : « 376 patients au total (128
    # confirmés et 248 suspects) » (Ituri) ; « 22 cas confirmés et 37 cas
    # suspects sont actuellement hospitalisés » (Haut-Uele) ; « 4 cas
    # confirmés et 15 cas suspects isolés à l'HGR Wapinda […] Et Yakoma : 2
    # cas confirmés et 12 cas suspects isolés au CTE Yakoma » (Nord-Ubangi,
    # deux sites : SOMME_RES les additionne).
    re.compile(r"(\d[\d ]{0,4}\d|\d)\s+(?:patients|malades)\s+au\s+total\s*\(\s*\d", re.I),
    CAS_CONF_SUSP_RE,
]
LITS_RE = re.compile(r"pour\s+(\d[\d ]{0,4}\d|\d)\s+lits|atteint\s+\d[\d ]{0,4}\s+lits\s+sur\s+(\d[\d ]{0,4}\d|\d)", re.I)
# « taux d'occupation global de 51,7% (120 lits) » (110 Haut-Uele) : les lits
# entre parentheses apres le taux, sans « pour ».
LITS_PARENTHESE_RE = re.compile(r"\((?:\d[\d ]{0,4}\d?\s*/\s*)?(\d[\d ]{0,4}\d|\d)\s+lits\)", re.I)
# « (18/36 lits) », « (60/153 lits) » (144) : la fraction hospitalises/lits
# entre parentheses ; le motif ci-dessus la lit aussi, par son denominateur.
# « en sursaturation (118,6 % ; 220 lits disponibles) » (111 Nord-Kivu) : les
# lits suivent le taux, apres le point-virgule, sans fraction ni « pour ».
# Le taux et le point-virgule sont exiges : sans eux, le motif mordait sur la
# synthese du SitRep 018 (« 71 lits disponibles au Nord-Kivu pour 8
# patients »), rattachee au morceau de l'Ituri.
LITS_DISPONIBLES_RE = re.compile(r"%\s*;\s*(\d[\d ]{0,4}\d|\d)\s+lits\s+disponibles", re.I)
# « en sursaturation (128,2 % ; 282/220) » (108 Nord-Kivu) : le dénominateur
# de la fraction qui suit le taux est le nombre de lits
# « en sursaturation (130,5 % ; 287/220 lits disponibles) » (117 Nord-Kivu) :
# la fraction du 108 ET le « lits disponibles » du 111 dans la meme parenthese.
# Sans ce motif, le 117 sortait avec l'occupation mais sans les lits, et la
# lettre plantait sur la province saturee.
LITS_FRACTION_RE = re.compile(r"%\s*(?:;|\()\s*\d[\d ]{0,4}\d?\s*/\s*(\d[\d ]{0,4}\d|\d)\s*(?:\)|lits\s+disponibles)")
# « 74,2 % (271/365) » (144 Nord-Kivu) : la fraction suit le taux entre
# parentheses, sans point-virgule ; meme lecture, denominateur = lits.
# « 392 patients sont hospitalisés dont 224 dans les structures normées avec
# une capacité d'accueil de 228 lits, soit un taux d'occupation global de
# 98,2 % » (125 a 127, Nord-Kivu) : la capacite remplace « pour N lits », et
# le taux porte sur les seuls patients des structures normees — 224/228 fait
# bien 98,2 %, quand 392/228 en ferait 172. Sans ce motif, la province sortait
# avec son taux mais sans lits, et la vue nationale du graphique des CTE
# l'ecartait : neuf jours de courbe perdus (vu le 20 septembre 2026).
# Le 125 glisse le numero de page au milieu de la tournure — « capacité
# d'accueil 6 de 228 lits » — d'ou l'ancrage sur « lits » et non sur « de ».
# « portant la capacité provinciale à 130 lits » (097, Haut-Uele).
LITS_CAPACITE_RE = re.compile(
    r"capacit[ée]\s+(?:d[’']\s*accueil|provinciale\s+à)[^.;%]{0,24}?(\d[\d ]{0,4}\d|\d)\s+lits", re.I)
# Le denominateur du taux quand la province distingue les deux : « dont 224
# dans les structures normées », « dont 216 dans les structures dédiées »,
# « dont 250 dans les structures de prise en charge normées » (132, sans
# nombre de lits : la capacite se deduit alors du taux et se recoupe),
# « dont 223 dans les CTE pour 354 lits » (135), « sont hospitalisés : 330
# dans les CTE/CT pour 374 lits » (150).
HOSPITALISES_NORMES_RE = re.compile(
    r"(?:dont|hospitalis[ée]s\s*:)\s+(\d[\d ]{0,4}\d|\d)\s+dans\s+(?:les\s+structures\s+(?:de\s+prise\s+en\s+charge\s+)?"
    r"(?:norm[ée]es|d[ée]di[ée]es)|les\s+CTE\b)", re.I)
# SitReps 146 a 148 (7 au 9 octobre 2026, Nord-Kivu) : « 519 patients
# demeuraient en isolement …, soit un taux d'occupation global des lits de
# 84,2 % (315/374) », « … de 91,8 % (325 patients aux lits des CTE/CT sur 354
# lits) », « … de 87,2 % : (326/374) ». La fraction qui suit le taux ne porte
# que sur les patients couches dans les lits des CTE/CT — les autres (156,
# 149, 148) sont soignes dans des ESS qui ne sont pas des CTE : c'est le
# « dont N dans les structures normees » des bulletins precedents, ecrit
# autrement. Groupes : patients aux lits, lits. Retenu comme
# hospitalisesNormes seulement s'il est inferieur au total hospitalise ET
# si la fraction retombe sur le taux publie a 1,5 point pres : le motif est
# ancre sur « occupation » (le 121 ecrit « complétude … de 38 % (5/13) » au
# Bas-Uele), et le Haut-Uele du 146 imprime « 49,7 % (54/153) » quand 54/153
# fait 35,3 % — fraction fausse, ignoree.
HOSPITALISES_AUX_LITS_RE = re.compile(
    r"occupation[^%;]{0,60}?(\d+(?:[,.]\d+)?)\s*%\s*:?\s*\(\s*(\d[\d ]{0,4}\d|\d)\s*(?:/|patients\s+aux\s+lits[^)]{0,40}?sur)\s*(\d[\d ]{0,4}\d|\d)\s*(?:lits)?\s*\)", re.I)
CTE_FRACTION_RE = re.compile(
    r"\(\s*(\d+(?:[,.]\d+)?)\s*%\s*dans\s+les\s+CTE[^;)]{0,12};\s*(\d[\d ]{0,4}\d|\d)\s*/\s*(\d[\d ]{0,4}\d|\d)\s+lits\s*\)", re.I)
# « dont 184 hors CTE/CT, les CTE/CT étant occupés à 90,8 % (394/434 lits) »
# (175, Nord-Kivu) : meme lecture que CTE_FRACTION_RE, autre tournure.
CTE_OCCUPES_RE = re.compile(
    r"CTE/CT\s+[ée]tant\s+occup[ée]s\s+[àa]\s+(\d+(?:[,.]\d+)?)\s*%\s*\(\s*(\d[\d ]{0,4}\d|\d)\s*/\s*(\d[\d ]{0,4}\d|\d)\s+lits\s*\)", re.I)
OCCUPATION_RES = [
    re.compile(r"taux\s+d[’']occupation[^%\d]{0,30}?(\d+(?:[,.]\d+)?)\s*%", re.I),
    re.compile(r"(\d+(?:[,.]\d+)?)\s*%\s+d[’']occupation", re.I),
    # « 68 patients sont en isolement, soit 56,7% des lits occupés » (104)
    re.compile(r"(\d+(?:[,.]\d+)?)\s*%\s+des\s+lits\s+occup", re.I),
    re.compile(r"lits\s*\((\d+(?:[,.]\d+)?)\s*%\)", re.I),
    # « en sursaturation (128,2 % ; 282/220) » (108 Nord-Kivu)
    re.compile(r"occupation[^%\n]{0,60}?\((\d+(?:[,.]\d+)?)\s*%\s*;", re.I),
    # « est en⏎sursaturation (118,6 % ; 220 lits disponibles) » (111 Nord-Kivu) :
    # le saut de ligne entre « en » et « sursaturation » echappe au motif
    # precedent, qui interdit \n ; le mot lui-meme suffit a ancrer le taux.
    re.compile(r"sursaturation\s*\((\d+(?:[,.]\d+)?)\s*%", re.I),
]


_N = r"(\d[\d ]{0,4}\d|\d|une?)"
# « 63 nouvelles admissions », « 1 nouvelle admission », « 16 nouveaux cas
# suspects ont été admis » (148 Bas-Uele).
ADMISSIONS_RE = re.compile(r"%s\s+nouvel(?:le)?s?\s+admissions?|%s\s+nouveaux\s+cas\s+suspects\s+ont\s+[ée]t[ée]\s+admis"
                           % (_N, _N), re.I)
SORTIES_RE = re.compile(r"contre\s+%s\s+sorties?\b" % _N, re.I)
SANS_SORTIE_RE = re.compile(r"sans\s+aucune\s+sortie|aucune\s+sortie\s+n[’']a\s+[ée]t[ée]", re.I)
# « dont 23 guérisons », « (78 non-cas, 11 guérisons et 7 décès) », « : 14
# guérisons », « dont 12 patients guéris » ; jamais un nombre isolé, qui
# pourrait venir d'une autre phrase.
# « 118 sorties, incluant 15 guérisons » (179 Nord-Kivu) : « incluant » et
# « y compris » s'ajoutent le 11 novembre 2026.
GUERIS_RE = re.compile(r"(?:dont|:|\(|,|incluant|y\s+compris)\s*%s\s+(?:patients?\s+)?gu[ée]ri(?:s|sons?)?\b" % _N, re.I)
# Un nombre de guéris dans le bilan du traitement expérimental n'est pas un
# flux du jour : « 679 cas ont reçu le traitement expérimental (dont 67
# confirmés, 48 guéris, 17 décès) » (179 Tshopo) était lu comme 48 guéris.
TRAITEMENT_RE = re.compile(r"traitement\s+exp[ée]rimental|th[ée]rapeutique|mol[ée]cule|anticorps", re.I)

# Les guéris du jour par province sont lus par extraire_gueris.py
# (data/gueris-provinces.json), sur tous les bulletins.


def nombre_ou_un(t):
    return 1 if t.lower() in ("un", "une") else entier(t)


def numerateur(ligne):
    """L'effectif que le site rapporte aux lits : TOUS les patients
    hospitalisés, toujours, y compris ceux installés hors des lits prévus.

    C'est la définition que l'INSP a tenue jusqu'au 14 septembre 2026, et
    celle qui mesure la saturation. Depuis le 15 il ne met au numérateur que
    les patients des structures normées du Nord-Kivu (216 sur 373), ce qui
    fait tomber le taux publié de 152,6 % à 94,7 % alors que le nombre de
    patients monte : les 157 malades couchés hors lits prévus — justement ce
    que le dépassement de 100 % sert à signaler — sortent du calcul. Le site
    rétablit donc la série à définition constante, et garde le taux du
    bulletin dans `occupationPubliee`. Depuis le 20 septembre 2026."""
    return ligne.get("hospitalises")


def premier(regexes, texte):
    for rx in regexes:
        for m in rx.finditer(texte):
            # « 155 patients sont hospitalisés hors CTE/CT » (178) : pas des
            # patients des centres de traitement.
            # « 252 patients sont pris en charge en dehors des CTE/CT (dans
            # des ESS non structurés) » (180 Nord-Kivu) : de même.
            if re.match(r"\w*\s+(?:en\s+dehors|hors)\b", texte[m.end():m.end() + 30]):
                continue
            if rx in SOMME_RES:
                return sum(entier(g) or 0 for mm in rx.finditer(texte) for g in mm.groups() if g)
            # Deux groupes : « 21 confirmés et 34 suspects aux lits » (178
            # Haut-Uele), la somme est le nombre de patients.
            vals = [entier(g) for g in m.groups() if g]
            return sum(v for v in vals if v is not None) if vals else None
    return None


# Les nombres en toutes lettres (11 novembre 2026) : « Treize patients
# demeuraient en isolement » (136 a 140 Tshopo et Bas-Uele), « Seize (16)
# patients … sont en isolement » (132 Tshopo), « Six suspects restent
# isoles » (153 Bas-Uele). Le mot suivi de son chiffre entre parentheses
# garde le chiffre ; seul, il devient chiffre devant patients, suspects,
# cas ou confirmes.
NOMBRES_MOTS = {
    "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6,
    "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12,
    "treize": 13, "quatorze": 14, "quinze": 15, "seize": 16, "dix-sept": 17,
    "dix-huit": 18, "dix-neuf": 19, "vingt": 20,
}
_MOTS = "|".join(sorted(NOMBRES_MOTS, key=len, reverse=True))
MOT_PARENTHESE_RE = re.compile(r"\b(?:%s)\s*\((\d+)\)" % _MOTS, re.I)
MOT_SEUL_RE = re.compile(r"\b(%s)\s+(?=(?:patients?|malades|suspects?|cas|confirm[ée]s?)\b)" % _MOTS, re.I)


def chiffrer(morceau):
    morceau = MOT_PARENTHESE_RE.sub(r"\1", morceau)
    return MOT_SEUL_RE.sub(lambda m: "%d " % NOMBRES_MOTS[m.group(1).lower()], morceau)


def lire_prose(morceau):
    morceau = chiffrer(morceau)
    hosp = premier(HOSPITALISES_RES, morceau)
    if hosp is None:
        return None
    ligne = {"hospitalises": hosp}
    m = (LITS_RE.search(morceau) or LITS_FRACTION_RE.search(morceau)
         or LITS_PARENTHESE_RE.search(morceau) or LITS_DISPONIBLES_RE.search(morceau)
         or LITS_CAPACITE_RE.search(morceau))
    if m:
        ligne["lits"] = entier(next(g for g in m.groups() if g))
    # Les hospitalises des seules structures normees, quand la province
    # distingue les deux : c'est EUX que le taux publie rapporte aux lits.
    # Garde-fou : pas plus que le total hospitalise, et le couple doit tomber
    # sur le taux publie, sinon on ne garde que le nombre.
    mn = HOSPITALISES_NORMES_RE.search(morceau)
    if mn:
        normes = entier(mn.group(1))
        if normes is not None and normes <= hosp:
            ligne["hospitalisesNormes"] = normes
    # « soit un taux d'occupation global de 108,8 % (90,8 % dans les CTE/CT ;
    # 385/424 lits) » (173 et 174, Nord-Kivu) : patients aux lits des CTE/CT
    # et lits, retenus si la fraction retombe sur le taux a 1,5 point pres.
    mc = CTE_FRACTION_RE.search(morceau) or CTE_OCCUPES_RE.search(morceau)
    if mc and "hospitalisesNormes" not in ligne:
        taux_c, aux_lits, lits_c = pourcent(mc.group(1)), entier(mc.group(2)), entier(mc.group(3))
        if aux_lits is not None and lits_c and aux_lits <= hosp and taux_c is not None and abs(aux_lits / lits_c * 100 - taux_c) <= 1.5:
            ligne["hospitalisesNormes"] = aux_lits
            ligne["lits"] = lits_c
            ligne["_occCte"] = taux_c
    ma = HOSPITALISES_AUX_LITS_RE.search(morceau)
    if ma and "hospitalisesNormes" not in ligne:
        taux_frac, aux_lits, lits_frac = pourcent(ma.group(1)), entier(ma.group(2)), entier(ma.group(3))
        if (aux_lits is not None and lits_frac and aux_lits < hosp and taux_frac is not None
                and abs(aux_lits / lits_frac * 100 - taux_frac) <= 1.5):
            ligne["hospitalisesNormes"] = aux_lits
            if not ligne.get("lits"):
                ligne["lits"] = lits_frac
    occ = None
    for rx in OCCUPATION_RES:
        mo = rx.search(morceau)
        # « 7 % de taux d'occupation global (50 % pour les suspects et 24 %
        # pour les confirmés) » (180 Ituri) : le premier taux trouve apres le
        # mot est celui des seuls suspects, pas un taux global.
        if mo and re.match(r"\s*pour\s+les\s+(?:cas\s+)?(?:suspects|confirm)", morceau[mo.end():mo.end() + 40], re.I):
            continue
        if mo:
            occ = pourcent(mo.group(1))
            break
    # Le taux « dans les CTE/CT » est celui qui porte sur les patients aux
    # lits : c'est lui le taux publie comparable, pas le taux « global ».
    if "_occCte" in ligne:
        occ = ligne.pop("_occCte")
    normes = ligne.get("hospitalisesNormes")
    if occ is not None and normes is not None and normes != hosp:
        # Le taux publie ne porte que sur les structures normees : on le garde
        # tel quel, et on trace la serie a definition constante. Les lits, que
        # le 124 ne publie pas, se deduisent alors du couple publie
        # (216 vus comme 94,7 % font 228,1) — mais seulement si la deduction
        # retombe sur une capacite que le bulletin a imprimee par ailleurs,
        # sinon on ne deduit rien.
        ligne["occupationPubliee"] = occ
        if not ligne.get("lits"):
            deduits = round(normes / occ * 100)
            ligne["litsDeduits"] = deduits
        if ligne.get("lits"):
            ligne["occupation"] = round(hosp / ligne["lits"] * 100, 1)
            ligne["occupationCalculee"] = True
        else:
            ligne["occupation"] = occ
    elif occ is not None:
        ligne["occupation"] = occ
    elif ligne.get("lits"):
        ligne["occupation"] = round(numerateur(ligne) / ligne["lits"] * 100, 1)
        ligne["occupationCalculee"] = True
    # Flux du jour (29 octobre 2026) : admissions, sorties et guéris, sous
    # leurs trois formes stables (« 63 nouvelles admissions … contre 99
    # sorties, dont 23 guérisons », « sans aucune sortie »). Les décès en CTE,
    # trop variables (« 11 décès (dont 8 confirmés) », « 1 décès confirmé à
    # Paw »), ne sont pas lus : la série des décès intra-CTE vient d'ailleurs.
    m = ADMISSIONS_RE.search(morceau)
    if m:
        ligne["admissions"] = nombre_ou_un(m.group(1) or m.group(2))
    m = SORTIES_RE.search(morceau)
    if m:
        ligne["sorties"] = nombre_ou_un(m.group(1))
    elif SANS_SORTIE_RE.search(morceau):
        ligne["sorties"] = 0
    for m in GUERIS_RE.finditer(morceau):
        if TRAITEMENT_RE.search(morceau[max(0, m.start() - 160):m.start()]):
            continue
        ligne["gueris"] = nombre_ou_un(m.group(1))
        break
    return ligne


def section_prose(texte):
    m = DEBUT_RE.search(texte)
    if not m:
        return None
    reste = texte[m.end():]
    f = FIN_RE.search(reste)
    reste = (reste[:f.start()] if f else reste[:3000])[:4000]
    # Le bilan national qui clot la section (« Au total, 146 nouvelles
    # admissions … Ainsi, 803 patients demeuraient en isolement », 136) serait
    # sinon lu comme la ligne de la derniere province citee.
    # Les « Defis » qui suivent la rubrique (« 2.5.2. Défis ») ne sont pas
    # des relevés : au 174, « au Nord-Kivu, … 210 patients sont pris en
    # charge hors CTE/CT » y etait lu comme la ligne du Nord-Kivu
    # (6 novembre 2026).
    # La rubrique suivante peut suivre sans retour a la ligne : « … contre 1
    # sortie. 2.5. Vaccination 2.5.1. » (176) ; sans cette coupe, la Tshopo
    # de la vaccination passait pour celle de la prise en charge.
    v = re.search(r"\b\d\.\d{1,2}\.?\s+Vaccination\b", reste)
    if v:
        reste = reste[:v.start()]
    d = re.search(r"\n[\d.\s]{0,12}D[ée]fis\b", reste)
    if d:
        reste = reste[:d.start()]
    g = re.search(r"\n\s*Au total,\s*\d[\d ]*\s+nouvelles\s+admissions", reste)
    return reste[:g.start()] if g else reste


def lire_par_prose(texte):
    section = section_prose(texte)
    if not section:
        return {}
    reperes = list(REPERE_RE.finditer(section))
    provinces = {}
    for i, m in enumerate(reperes):
        nom = canon(m.group(1))
        fin = reperes[i + 1].start() if i + 1 < len(reperes) else len(section)
        ligne = lire_prose(section[m.end():fin])
        if ligne and nom not in provinces:
            provinces[nom] = ligne
    return provinces


# -------------------------------------------------------------- tableau (C)
ENTETE_RE = re.compile(r"\n\s*Indicateurs?\s+((?:(?:%s|Ensemble|Total|Global)\s*)+)\n" % PROVINCES_RE)
LITS_LIGNE_RE = re.compile(r"\n\s*Nombre\s+de\s+lits\s+([^\n]+)")
# « 60 Patients au lit (J-1) 551 170 … » : le « 860 » de la ligne des lits
# s'est cassé sur deux lignes, et son morceau ouvre celle des patients.
PATIENTS_LIGNE_RE = re.compile(r"\n(?:\d+\s+)?Patients?\s+au\s+lit\s*\(J-1\)\s+([^\n]+)")
# Du 059 au 080 le meme tableau porte aussi « Patients en isolement (fin J)
# 551 168 ND 3 722 » : c'est le chiffre du jour, celui que la une, la prose et
# les « Defis » du bulletin citent (« 77,7 % en Ituri (551 patients pour 709
# lits) », 069). « Au lit (J-1) » est celui de la veille : le lire decalait la
# courbe d'un jour sur 19 bulletins (trouve le 28 septembre 2026 en croisant
# les Defis avec cte.json). Du 019 au 058, seule la ligne J-1 existe : elle
# reste lue, et le point porte `patientsVeille`.
PATIENTS_FIN_J_RE = re.compile(r"\n(?:\d+\s+)?Patients?\s+en\s+isolement\s*\(fin\s*J\)\s+([^\n]+)")


def decoupages(ligne, n):
    """Tous les découpages d'une ligne de tableau en n cellules.

    Un espace entre deux nombres est tantôt une frontière de colonnes, tantôt
    un séparateur de milliers (« 1 483 ») : « 532 924 ND 27 ND 1 483 » a deux
    lectures à six cellules, et seule la somme des colonnes dit laquelle est
    la bonne. On renvoie toutes les lectures possibles, l'appelant choisit —
    celle qui se vérifie, ou à défaut la première, où le préfixe de milliers
    est le plus court et le plus à gauche (« 1 014 » plutôt que « 7 146 »)."""
    jetons = ligne.strip().split()
    if len(jetons) < n:
        return []
    if len(jetons) == n:
        return [[None if j.upper() in ("ND", "NA", "-", "—") else entier(j) for j in jetons]]
    fusions = [i for i in range(len(jetons) - 1)
               if jetons[i].isdigit() and len(jetons[i]) <= 2
               and jetons[i + 1].isdigit() and len(jetons[i + 1]) == 3]
    fusions.sort(key=lambda i: (len(jetons[i]), i))
    out = []
    for i in fusions:
        j2 = jetons[:i] + [jetons[i] + jetons[i + 1]] + jetons[i + 2:]
        for d in decoupages(" ".join(j2), n):
            if d not in out:
                out.append(d)
    return out


def cellules(ligne, n, valide=None):
    """Le découpage retenu : le premier que `valide` accepte, sinon le premier."""
    cands = decoupages(ligne, n)
    if not cands:
        return None
    if valide:
        for c in cands:
            if valide(c):
                return c
    return cands[0]


def cellule_perdue(ligne, n, i_total, somme_ok, vides=None):
    """Une ligne a laquelle il manque une cellule vide (064 : « Patients en
    isolement (fin J) 548 174 ND 722 » sous cinq colonnes). On replace la
    cellule manquante a chaque position hors total ou, si `vides` est donne,
    seulement la ou la ligne de la veille porte « ND » (une province qui ne
    rapporte pas un jour ne rapporte pas le suivant) ; la lecture n'est retenue
    que si la somme retombe sur le total ET que toutes les positions possibles
    donnent les memes chiffres aux memes provinces. Sinon, rien."""
    if i_total is None:
        return None
    lectures = []
    for courte in decoupages(ligne, n - 1) or []:
        for k in range(n):
            if k == i_total or (vides is not None and k not in vides):
                continue
            c = courte[:k] + [None] + courte[k:]
            if c[i_total] is not None and somme_ok(c):
                lectures.append(c)
    if not lectures:
        return None
    for c in lectures[1:]:
        if any((a or 0) != (b or 0) for a, b in zip(c, lectures[0])):
            return None
    return lectures[0]


def lire_par_tableau(texte):
    """Le tableau d'occupation de l'époque C : une colonne par province."""
    # Le tableau des soins est le seul dont l'en-tete precede une ligne
    # « Nombre de lits » : on cherche l'en-tete le plus proche avant elle.
    ml = LITS_LIGNE_RE.search(texte)
    mp = PATIENTS_LIGNE_RE.search(texte)
    if not mp:
        return {}
    # +1 : le retour a la ligne qui clot l'en-tete est aussi celui qui ouvre
    # la ligne des patients ; sans lui, l'en-tete colle au tableau (059,
    # « Indicateur Ituri Nord-Kivu Sud-Kivu Ensemble ») n'etait pas vu et
    # celui du tableau des alertes, a cinq colonnes, etait pris (11 novembre 2026).
    avant = texte[:mp.start() + 1]
    entetes = list(ENTETE_RE.finditer(avant))
    if not entetes:
        return {}
    colonnes = entetes[-1].group(1).split()
    # « Nord-Kivu » tient en un jeton, « Haut Uélé » en deux : on recolle.
    noms = []
    i = 0
    while i < len(colonnes):
        j = colonnes[i]
        if j in ("Haut", "Bas", "Nord", "Sud") and i + 1 < len(colonnes):
            j = j + " " + colonnes[i + 1]
            i += 1
        noms.append(j)
        i += 1
    n = len(noms)
    i_total = next((k for k, nom in enumerate(noms) if nom in ("Ensemble", "Total", "Global")), None)

    def somme_ok(c):
        if i_total is None or c[i_total] is None:
            return True
        return c[i_total] == sum(v or 0 for k, v in enumerate(c) if k != i_total)
    mf = PATIENTS_FIN_J_RE.search(texte, mp.end())
    patients = None
    if mf and mf.start() - mp.end() < 2000:
        # la ligne du jour ne remplace celle de la veille que si sa somme tombe
        # juste : `cellules` rendrait sinon un decoupage non verifie
        patients = next((c for c in decoupages(mf.group(1), n) if i_total is not None and somme_ok(c)), None) \
            or cellule_perdue(mf.group(1), n, i_total, somme_ok,
                              vides={k for k, v in enumerate(cellules(mp.group(1), n, valide=somme_ok) or []) if v is None})
        # 061, 062, 080 : la ligne de la veille est elle-meme incomplete (cellules
        # vides non imprimees, pas de total au 080) et n'a jamais verifie sa somme.
        # La ligne du jour, de meme forme, est alors lue de la meme facon : pas
        # plus exigeant pour l'une que pour l'autre.
        if patients is None and not any(i_total is not None and somme_ok(c) for c in decoupages(mp.group(1), n) or []) \
                and len(mf.group(1).split()) == len(mp.group(1).split()):
            patients = cellules(mf.group(1), n, valide=somme_ok)
        veille = False
    if patients is None:
        patients = cellules(mp.group(1), n, valide=somme_ok)
        veille = True
    lits = cellules(ml.group(1), n, valide=somme_ok) if ml and ml.start() < mp.start() + 2000 else None
    if patients is None:
        return {}
    provinces = {}
    for k, nom in enumerate(noms):
        if nom in ("Ensemble", "Total", "Global"):
            continue
        if patients[k] is None:
            continue
        ligne = {"hospitalises": patients[k]}
        if veille:
            ligne["patientsVeille"] = True
        if lits and lits[k]:
            ligne["lits"] = lits[k]
            ligne["occupation"] = round(patients[k] / lits[k] * 100, 1)
            ligne["occupationCalculee"] = True
        provinces[canon(nom)] = ligne
    return provinces


# ------------------------------------------------------- bandeau (059-083)
# Le bandeau de tete des SitReps 059 a 083 ventile les patients en
# isolement : « PATIENTS EN ISOLEMENT … 717 … Ituri 471 · N-Kivu 196 ·
# Haut-Uélé 31 · +22 guéris (Ituri 21 · Haut-Uélé 1) Tshopo 3 · Sud-Kivu 16
# 14 300 / 18 243 vus » (081). Aux 081-083 la prose ne donne que l'Ituri :
# le bandeau complete les autres provinces, s'il retombe sur son total
# (11 novembre 2026). Jamais a la place d'une lecture du tableau ou de la prose.
BANDEAU_NOMS = [("Ituri", r"Ituri"), ("Nord-Kivu", r"N(?:ord)?[\s-]+Kivu"),
                ("Haut-Uélé", r"H(?:aut)?[\s-]+U[ée]l[ée]"), ("Tshopo", r"Tshopo"),
                ("Sud-Kivu", r"S(?:ud)?[\s-]+Kivu"), ("Bas-Uélé", r"B(?:as)?[\s-]+U[ée]l[ée]")]


def lire_bandeau(texte):
    i = texte.find("PATIENTS EN ISOLEMENT")
    if i < 0:
        return {}
    seg = texte[i:i + 500]
    # Un seul bloc de chiffres : « 717 749 » sont les patients puis les guéris
    # (le bandeau n'a jamais depasse 999 patients a cette epoque).
    mt = re.search(r"\n\s*(\d{1,4})\b", seg)
    if not mt:
        return {}
    total = entier(mt.group(1))
    seg = seg[mt.end():]
    seg = re.sub(r"\+\s*\d+\s+gu[ée]ris\s*(?:\([^)]*\))?", " ", seg)
    # Fin : la fraction des contacts vus (« 14 300 / 18 243 »), sans manger
    # le « 16 » du Sud-Kivu qui la precede.
    fin = re.search(r"cumul|\b\d{1,2} \d{3}\s*/|\b\d{3,6}\s*/|vus|Faits", seg, re.I)
    seg = seg[:fin.start()] if fin else seg
    provinces, autres = {}, 0
    motif = "|".join("(?P<p%d>%s)" % (k, rx) for k, (_, rx) in enumerate(BANDEAU_NOMS))
    for m in re.finditer(r"(?:%s|(?P<autres>autres))\s+(\d{1,4}|ND)\b" % motif, seg):
        v = m.group(m.lastindex)
        if m.group("autres"):
            autres = entier(v) or 0
            continue
        nom = next(BANDEAU_NOMS[k][0] for k in range(len(BANDEAU_NOMS)) if m.group("p%d" % k))
        if nom in provinces:
            break
        provinces[nom] = None if v == "ND" else entier(v)
    lus = {k: v for k, v in provinces.items() if v is not None}
    if not lus or total is None or sum(lus.values()) + autres != total:
        return {}
    return {k: {"hospitalises": v, "bandeau": True} for k, v in lus.items()}


# ----------------------------------------------------------------- commun
def avertissements(nom, ligne):
    out = []
    h, l, o = numerateur(ligne), ligne.get("lits"), ligne.get("occupation")
    if h is not None and l and o is not None and not ligne.get("occupationCalculee"):
        calc = round(h / l * 100, 1)
        if abs(calc - o) > 1.5:
            out.append("%s : occupation publiée %s %%, recalculée %s %% (%d/%d)" % (nom, o, calc, h, l))
    return out


def confirmer_lits_deduits(points):
    """Les lits deduits d'un couple publie ne sont retenus que si le bulletin
    a imprime la meme capacite a moins de trois lits pres, dans les sept jours
    qui precedent ou qui suivent.

    Le 124 (15 septembre 2026) donne « 216 dans les structures dédiées » et
    94,7 % sans jamais ecrire le nombre de lits : 216/0,947 fait 228,1, et le
    125 comme le 126 impriment 228. La deduction est donc confirmee. Sans ce
    garde-fou, une coquille de la source fabriquerait une capacite qui n'a
    jamais existe."""
    for i, p in enumerate(points):
        for nom, ligne in (p.get("provinces") or {}).items():
            deduits = ligne.get("litsDeduits")
            if not deduits or ligne.get("lits"):
                continue
            voisins = []
            for q in points[max(0, i - 7):i + 8]:
                v = (q.get("provinces") or {}).get(nom) or {}
                if q is not p and v.get("lits") and not v.get("litsDeduits"):
                    voisins.append(v["lits"])
            proche = [l for l in voisins if abs(l - deduits) <= 3]
            if proche:
                ligne["lits"] = min(proche, key=lambda l: abs(l - deduits))
                ligne["litsDeduits"] = True
                if ligne.get("hospitalises") and ligne["lits"]:
                    ligne["occupation"] = round(
                        ligne["hospitalises"] / ligne["lits"] * 100, 1)
                    ligne["occupationCalculee"] = True
            else:
                del ligne["litsDeduits"]


def encadrer_lits(points):
    """Une province sans lits imprimes, entre deux bulletins qui impriment la
    MEME capacite dans les sept jours avant et apres, recoit cette capacite.

    Le 134 (25 septembre 2026) ecrit « 351 patients sont hospitalisés dont 271
    dans les structures normées, soit un taux d'occupation de 70,9 % », sans
    nombre de lits ; et 70,9 % est exactement 251/354, le calcul du 133 : taux
    recopie, dont aucune capacite ne se deduit (271/0,709 = 382). Le 133 et le
    135 impriment tous deux 354 lits. Sans cette regle, la serie a definition
    constante (tous les hospitalises sur les lits) tombait ce jour-la au taux
    publie, 70,9 %, entre 103,1 et 92,7 : une chute qui n'a pas eu lieu. Le
    point recoit 351/354 = 99,2 %, et le taux publie reste dans
    occupationPubliee. Depuis le 28 septembre 2026."""
    for i, p in enumerate(points):
        for nom, ligne in (p.get("provinces") or {}).items():
            if ligne.get("lits") or not ligne.get("hospitalises"):
                continue
            def imprime(q):
                v = (q.get("provinces") or {}).get(nom) or {}
                return v.get("lits") if v.get("lits") and not v.get("litsDeduits") else None
            avant = next((imprime(q) for q in reversed(points[max(0, i - 7):i]) if imprime(q)), None)
            apres = next((imprime(q) for q in points[i + 1:i + 8] if imprime(q)), None)
            if avant and avant == apres:
                ligne["lits"] = avant
                ligne["litsEncadres"] = True
                if "occupation" in ligne and "occupationPubliee" not in ligne:
                    ligne["occupationPubliee"] = ligne["occupation"]
                ligne["occupation"] = round(ligne["hospitalises"] / avant * 100, 1)
                ligne["occupationCalculee"] = True


def reporter_lits_taux_recopie(points):
    """Une province qui distingue ses patients (« 383 hospitalises dont 271
    dans les structures normees ») et publie un taux sans nombre de lits :
    la serie a definition constante (tous les hospitalises sur les lits) a
    besoin d'une capacite. Les SitReps 140, 141 et 143 (1er au 4 octobre
    2026, Nord-Kivu) impriment 63,0 % trois fois de suite, recopie du 138 :
    271/354 ferait 76,6 %. confirmer_lits_deduits n'y trouve aucune capacite
    (271/0,63 = 430 lits), et encadrer_lits non plus, le 135 imprimant 354
    et le 144 365. Le point tombait alors au taux publie, 63 %, entre
    101,7 % et 114,2 % : trois chutes qui n'ont pas eu lieu.

    Regle : la capacite imprimee la plus recente dans les sept bulletins
    precedents (a defaut, dans les sept suivants) ; le taux du bulletin reste
    dans occupationPubliee, et le point est marque litsReportes. Seules les
    lignes a deux definitions sont concernees — un taux qui porte deja sur
    tous les patients reste tel quel. Depuis le 12 octobre 2026.

    Meme traitement pour un taux RECOPIE a l'identique du bulletin precedent
    alors que le nombre de patients a change : le 136 (27 septembre) ecrit
    « 345 patients demeuraient hospitalisés … 63,0 % », le taux des seules
    structures normees du 135 (223/354), sans dire combien y sont. Une regle
    plus large (tout taux qui s'ecarte du calcul) abimerait les 120 a 123,
    ou l'ecart vient d'une capacite passee de 220 a 228 lits."""
    def publie(q, nom):
        v = (q.get("provinces") or {}).get(nom) or {}
        return v.get("occupationPubliee", None if v.get("occupationCalculee") else v.get("occupation")), v.get("hospitalises")
    for i, p in enumerate(points):
        for nom, ligne in (p.get("provinces") or {}).items():
            hosp, normes = ligne.get("hospitalises"), ligne.get("hospitalisesNormes")
            if ligne.get("lits") or not hosp or ligne.get("occupationCalculee"):
                continue
            deux_definitions = normes and normes != hosp
            taux_veille, hosp_veille = publie(points[i - 1], nom) if i else (None, None)
            recopie = (ligne.get("occupation") is not None and taux_veille == ligne["occupation"]
                       and hosp_veille is not None and hosp_veille != hosp)
            if not deux_definitions and not recopie:
                continue
            def imprime(q):
                v = (q.get("provinces") or {}).get(nom) or {}
                return v.get("lits") if v.get("lits") and not v.get("litsDeduits") else None
            lits = (next((imprime(q) for q in reversed(points[max(0, i - 7):i]) if imprime(q)), None)
                    or next((imprime(q) for q in points[i + 1:i + 8] if imprime(q)), None))
            if not lits:
                continue
            ligne.pop("litsDeduits", None)
            if "occupation" in ligne and "occupationPubliee" not in ligne:
                ligne["occupationPubliee"] = ligne["occupation"]
            ligne["lits"] = lits
            ligne["litsReportes"] = True
            ligne["occupation"] = round(hosp / lits * 100, 1)
            ligne["occupationCalculee"] = True


def lits_qui_recoupent(points, i, nom, ligne):
    """La capacite imprimee la plus recente, dans les trente bulletins
    precedents, sur laquelle le taux publie retombe a 0,15 point pres — pas
    seulement la derniere imprimee (6 novembre 2026). Au 173 et au 174, le
    Haut-Uele publie 23,9 % pour 33 patients et 25,4 % pour 35 : 138 lits,
    la capacite du 147, quand les derniers bulletins en imprimaient 162 ; la
    Tshopo, 19,4 % pour 6 et 25,8 % pour 8 : 31 lits (147), et non 36."""
    for q in reversed(points[max(0, i - 30):i]):
        v = (q.get("provinces") or {}).get(nom) or {}
        l = v.get("lits") if v.get("lits") and not v.get("litsDeduits") and not v.get("litsReportes") else None
        if l and abs(round(ligne["hospitalises"] / l * 100, 1) - ligne["occupation"]) <= 0.15:
            return l
    return None


def recouper_lits_historique(points):
    """Comme recouper_lits_precedents, pour les bulletins qui ne sont plus le
    dernier, mais seulement le cas strict : la capacite imprimee dans les
    trente bulletins precedents, si le taux publie retombe dessus a 0,15
    point pres (6 novembre 2026). Au 173, l'Ituri ecrit 343 patients et
    33,8 % sans nombre de lits ; 343/1 015 fait 33,8 %. Tant que le 173 etait
    le dernier, recouper_lits_precedents lui donnait ces 1 015 lits ; des
    l'arrivee du 174 il les perdait, et la Lettre 173 ne comptait plus que le
    Nord-Kivu (634 malades pour 424 lits, « 150 pour 100 lits »). Le report
    sans recoupement reste reserve au dernier bulletin."""
    for i, p in enumerate(points[:-1]):
        for nom, ligne in (p.get("provinces") or {}).items():
            if ligne.get("lits") or not ligne.get("hospitalises") or ligne.get("occupation") is None:
                continue
            def imprime(q):
                v = (q.get("provinces") or {}).get(nom) or {}
                return v.get("lits") if v.get("lits") and not v.get("litsDeduits") and not v.get("litsReportes") else None
            avant = lits_qui_recoupent(points, i, nom, ligne)
            if avant:
                ligne["lits"] = avant
                ligne["litsRecoupes"] = True


def recouper_lits_precedents(points):
    """Le DERNIER bulletin n'a pas de voisin suivant, et encadrer_lits ne peut
    rien pour lui. Le 136 (27 septembre 2026) ne publie aucun nombre de lits :
    « 368 patients … Le taux d'occupation des lits était de 36,3 % » (Ituri).
    Une province sans lits recoit la capacite imprimee dans les sept jours
    precedents :
    - si le taux publie retombe dessus a 0,15 point pres (368/1 015 = 36,3 %,
      68/138 = 49,3 %), la capacite est recoupee ;
    - sinon le taux ne mesure pas la meme chose (Nord-Kivu : 63,0 % pour 345
      patients, recopie du 135, quand 345/354 = 97,5 %) : il passe en
      occupationPubliee, et la serie a definition constante prend la capacite
      de la veille, comme encadrer_lits le fait pour un taux recopie
      (depuis le 28 septembre 2026).
    Le bulletin suivant tranche : ce point n'est plus le dernier, et
    encadrer_lits le reprend ou le laisse sans lits. Seul le dernier point
    est concerne — l'historique garde ses taux publies."""
    if not points:
        return
    i = len(points) - 1
    p = points[i]
    for nom, ligne in (p.get("provinces") or {}).items():
        if ligne.get("lits") or not ligne.get("hospitalises") or ligne.get("occupation") is None:
            continue
        def imprime(q):
            v = (q.get("provinces") or {}).get(nom) or {}
            return v.get("lits") if v.get("lits") and not v.get("litsDeduits") else None
        # Quinze bulletins depuis le 7 octobre 2026 (sept jusque-la) : l'Ituri
        # n'imprime plus ses lits que de loin en loin, et le 144 restait sans
        # capacite. Le recoupement a 0,15 point pres reste exige.
        # Trente bulletins depuis le 3 novembre 2026 : le 171 sortait de la
        # fenetre de quinze (derniers lits de l'Ituri au 155), et la lettre
        # passait de 57 a 121 malades pour 100 lits, l'Ituri sorti du calcul.
        recoupe = lits_qui_recoupent(points, i, nom, ligne)
        avant = recoupe or next((imprime(q) for q in reversed(points[max(0, i - 30):i]) if imprime(q)), None)
        if not avant:
            continue
        calcule = round(ligne["hospitalises"] / avant * 100, 1)
        ligne["lits"] = avant
        if abs(calcule - ligne["occupation"]) <= 0.15:
            ligne["litsRecoupes"] = True
        else:
            ligne["litsReportes"] = True
            ligne["occupationPubliee"] = ligne["occupation"]
            ligne["occupation"] = calcule
            ligne["occupationCalculee"] = True


def recalculer_total(point):
    """Le cumul national suit les lignes de province, y compris celles dont la
    capacite vient d'etre confirmee."""
    provinces = point.get("provinces") or {}
    avec_lits = [v for v in provinces.values() if v.get("lits")]
    total = point["total"]
    for cle in ("lits", "hospitalisesAvecLits", "occupation"):
        total.pop(cle, None)
    if avec_lits:
        total["lits"] = sum(v["lits"] for v in avec_lits)
        total["hospitalisesAvecLits"] = sum(numerateur(v) for v in avec_lits)
        total["occupation"] = round(total["hospitalisesAvecLits"] / total["lits"] * 100, 1)


# Les 081 et 083 (3 et 5 aout) sont mis en page sur deux colonnes que
# l'extraction du texte entrelace : « → Ituri : 21 nouveaux guéris ; 471
# patients en isolement visites, 22 lors de 7 causeries éducatives, 30 en
# (302 confirmés, 169 suspects) sur 833 lits, soit 56,5 % … d'occupation ».
# Aucun motif ne s'y fie sans risque ; lus a la main (audit du 27 septembre
# 2026) et ajoutes s'ils manquent.
LECTURES_NOMMEES = {
    "081": {"Ituri": {"hospitalises": 471, "lits": 833, "occupation": 56.5}},
    # « 468 patients en isolement … pour 833 lits (56 %), dont 271 confirmés et
    # 197 suspects »
    "083": {"Ituri": {"hospitalises": 468, "lits": 833, "occupation": 56.0}},
}


def lire_rapport(chemin):
    texte = texte_du_rapport(chemin)
    meta = extract_meta(texte, fallback_number=numero(chemin))
    if not meta.get("reportingDate"):
        return None, []
    # Le tableau d'abord : là où il existe (époques B et C), la prose de la
    # même section porte des cumuls et des indicateurs qui ressemblent à des
    # hospitalisés du jour — « 4 035 cas… », « 6 275… » — et trompe les motifs.
    provinces = lire_par_tableau(texte)
    methode = "tableau"
    if not provinces:
        provinces = lire_par_prose(texte)
        methode = "prose"
    bandeau = lire_bandeau(texte)
    if bandeau and not provinces:
        methode = "bandeau"
    for nom, ligne in bandeau.items():
        if nom not in provinces:
            provinces[nom] = ligne
    for nom, ligne in LECTURES_NOMMEES.get(meta["sitrepNumber"], {}).items():
        if nom not in provinces:
            provinces[nom] = dict(ligne)
            methode = methode if provinces else "lecture nommée"
    if not provinces:
        return None, []
    alertes = []
    for nom, ligne in provinces.items():
        alertes.extend(avertissements(nom, ligne))
    avec_lits = [p for p in provinces.values() if p.get("lits")]
    total = {
        "hospitalises": sum(p["hospitalises"] for p in provinces.values()),
        "provinces": len(provinces),
    }
    if avec_lits:
        total["lits"] = sum(p["lits"] for p in avec_lits)
        total["hospitalisesAvecLits"] = sum(numerateur(p) for p in avec_lits)
        total["occupation"] = round(total["hospitalisesAvecLits"] / total["lits"] * 100, 1)
    point = {
        "date": meta["reportingDate"],
        "sitrepNumber": meta["sitrepNumber"],
        "methode": methode,
        "provinces": provinces,
        "total": total,
        "source": "SitRep INSP (automatique)",
    }
    return point, alertes


def main():
    points, alertes, sans = [], [], []
    for chemin in rapports():
        try:
            point, av = lire_rapport(chemin)
        except Exception as e:
            print("  ! %s : %s" % (os.path.basename(chemin), e))
            continue
        if point is None:
            sans.append(numero(chemin))
            continue
        alertes.extend("%s : %s" % (point["sitrepNumber"], a) for a in av)
        points.append(point)
    par_date = {}
    for p in points:
        par_date[p["date"]] = p
    final = sorted(par_date.values(), key=lambda p: p["date"])
    confirmer_lits_deduits(final)
    encadrer_lits(final)
    reporter_lits_taux_recopie(final)
    recouper_lits_historique(final)
    recouper_lits_precedents(final)
    for p in final:
        recalculer_total(p)
    sortie = {
        "periode": {"debut": final[0]["date"], "fin": final[-1]["date"]} if final else None,
        "parDate": final,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(sortie, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    methodes = {}
    for p in final:
        methodes[p["methode"]] = methodes.get(p["methode"], 0) + 1
    print("%s écrit : %d date(s), du %s au %s — %s" % (
        os.path.relpath(OUTPUT_PATH, ROOT), len(final),
        final[0]["date"] if final else "-", final[-1]["date"] if final else "-",
        ", ".join("%d par %s" % (n, m) for m, n in sorted(methodes.items()))))
    print("Rapports sans donnée CTE lisible (%d) : %s" % (len(sans), ", ".join(sans)))
    if alertes:
        print("\n%d avertissement(s) :" % len(alertes))
        for a in alertes:
            print("  - " + a)


if __name__ == "__main__":
    main()
