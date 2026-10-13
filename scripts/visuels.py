# -*- coding: utf-8 -*-
"""La page « Visuels » (12 octobre 2026) : douze images de l'epidemie, en SVG,
redessinees a chaque generation du site, dans la langue de la page.

Trois rythmes, choisis par le proprietaire le 11 octobre 2026 :
  - a chaque bulletin : le calendrier, le code-barre, la carte des provinces ;
  - chaque semaine, arretes a la DERNIERE SEMAINE COMPLETE (lundi-dimanche) :
    la part de chaque province, les nouveaux cas par semaine, le lieu des
    deces, les zones actives et calmes, zone apres zone ;
  - chaque mois, pour le DERNIER MOIS CLOS : nouvelles zones, nouveaux cas,
    nouveaux deces, part de chaque province.

Les visuels viennent des maquettes publiees sur X (tmp/proto-visuels,
tmp/proto-mensuel, tmp/proto-page-visuels-2-1011), reecrits ici pour trois
langues et pour que rien ne soit ecrit en dur : le mois mis en avant, la
semaine, les comptes se calculent. Regles reprises du site :
  - une zone se compare par cle normalisee, alias compris (« Gety » / « Gethy ») ;
  - chaque chiffre vient de data/, aucune valeur inventee ni interpolee ;
  - les volumes hebdomadaires du lieu du deces ne se comparent pas : parts.
Le swahili est redige par l'assistant, a faire relire."""
import datetime as dt
import html
import json
import math
import os
import re
import unicodedata
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = dt.date.fromisoformat

# ---------------------------------------------------------------- couleurs et polices du site
INK, INK_DIM, INK_LABEL, INK_FAINT = "#1F1A13", "#5A544C", "#635D54", "#777068"
BG, PANEL, LINE, LINE_SOFT = "#FDFAF6", "#FFFDFB", "#DEDAD5", "#E7E4E0"
BLUE, BLUE_STRONG, RED, GREEN, AMBER = "#005E82", "#005073", "#993A2E", "#327957", "#A06F30"
MAP = ["#EAE7E3", "#B7D3E1", "#88B3C8", "#5693AF", "#267294", "#015174", "#00324B"]
REDS = ["#F3E4E0", "#E5B7AE", "#D08A7D", "#B95F50", "#993A2E", "#6E271E"]
PROV = {"Ituri": BLUE, "Nord-Kivu": AMBER, "Haut-Uélé": GREEN, "Tshopo": "#6B5CA5",
        "Sud-Kivu": INK_DIM, "Bas-Uélé": RED, "Sud-Ubangi": "#B0487D"}
SERIF = "'Source Serif 4',Georgia,serif"
SANS = "'Public Sans',Helvetica,Arial,sans-serif"
CHIFFRES = "'Bricolage Grotesque','Public Sans',Helvetica,Arial,sans-serif"
W = 1200

# Les deux rattrapages administratifs du site (RATTRAPAGE_ADMIN dans app.js) :
# date -> part du jour publiee par le bulletin ; le reste est le rattrapage.
RATTRAPAGES = {"2026-07-22": 97, "2026-07-30": 73}

# ---------------------------------------------------------------- textes
TXT = {
 "fr": dict(
  moisLong=["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
  jours=["L", "M", "M", "J", "V", "S", "D"],
  kicker="17e ÉPIDÉMIE D'EBOLA · RÉPUBLIQUE DÉMOCRATIQUE DU CONGO",
  source="Sources : bulletins de l'INSP", domaine="ebola-tracker.org",
  situation="Dernières données : {d} (SitRep n°{n} de l'INSP)",
  semaine="Semaine du {a} au {b} (dernière semaine complète)",
  moisClos="Mois clos : {m} · données au {d}",
  # bulletin
  calTitre="Le calendrier de l'épidémie", calSous="Une case par jour, teintée et chiffrée : les cas en bleu, les décès en rouge",
  calCas="NOUVEAUX CAS CONFIRMÉS, LE CHIFFRE DU JOUR DANS CHAQUE CASE", calDeces="DÉCÈS DU JOUR",
  calRatt="Rattrapages administratifs : le {a}, {ta} cas déclarés dont {ra} rattrapés ; le {b}, {tb} dont {rb} pour les 28 et 29 juillet, sans bulletin.",
  calRattDeces="Les décès des {a} et {b} comportent aussi un rattrapage, dont le bulletin ne donne pas la part.",
  calHach="Case hachurée : pas de bulletin ce jour-là.",
  rayTitre="Le code-barre de l'épidémie", raySous="Du {a} au {b}, une rayure par jour : plus elle est sombre, plus il y a eu de cas",
  rayCas="NOUVEAUX CAS CONFIRMÉS, UN TRAIT PAR JOUR", rayDeces="DÉCÈS DU JOUR",
  rayManque="Les quelques jours sans bulletin sont coloriés à la moyenne des sept jours voisins.",
  provTitre="{n} provinces touchées", provSous="Cas confirmés cumulés par province, du 15 mai au {d}. Les {autres} autres provinces de la RDC n'ont déclaré aucun cas.",
  provLegende="CAS CONFIRMÉS", provPhrase="{cas} cas confirmés dans {zones} zones de santé, sur les {total} que comptent ces {np} provinces.",
  provPied=" · contours des zones de santé : OCHA",
  # semaine
  lundi="Sous chaque barre, le lundi de la semaine.",
  partTitre="La part de chaque province, semaine après semaine", partSous="Répartition des nouveaux cas confirmés de chaque semaine entre les provinces.",
  partPhrase="Le Nord-Kivu : {a} des nouveaux cas la semaine du {da}, {b} la semaine du {db}",
  partNote="Chaque barre vaut 100 % des nouveaux cas de la semaine.",
  casTitre="Les nouveaux cas, semaine après semaine", casSous="Cas confirmés déclarés chaque semaine, du lundi au dimanche, depuis la semaine du {d}.",
  casPhrase="Du {a} au {b} : {n} nouveaux cas, {v} par rapport à la semaine précédente.",
  casNote="Les semaines du 20 et du 27 juillet portent des rattrapages administratifs : {r1} cas le 22 juillet, {r2} le 30.",
  lieuTitre="Où meurent les malades", lieuSous="Part des décès survenus dans la communauté et en centre de traitement, semaine par semaine, depuis que les bulletins la publient.",
  lieuCom="décès dans la communauté", lieuCte="décès dans un centre de traitement",
  lieuPhrase="Du {a} au {b}, {p} des décès sont survenus hors d'un centre de traitement ({c} sur {t}).",
  lieuNote="Un décès dans la communauté est un malade qui n'a pas été isolé à temps.",
  zonTitre="Zones actives, zones calmes", zonSous="Chaque semaine, les zones de santé déjà touchées : celles qui ont eu un nouveau cas dans les trois dernières semaines, et celles qui n'en ont plus eu.",
  zonActive="active : un cas ou plus en 3 semaines", zonCalme="calme : aucun cas depuis 3 semaines", zonTouchees="{n} touchées",
  zonPhrase="Au {d}, {a} des {t} zones touchées ont eu un cas dans les trois dernières semaines.",
  zonNote="Trois semaines, soit 21 jours : la durée maximale d'incubation du virus.",
  tapTitre="Zone après zone", tapSous="{n} zones de santé touchées au {d}, dans l'ordre du premier cas, une case par semaine.",
  tapLegende="Nouveaux cas dans la semaine :", tapNote="Une ligne par zone, dans l'ordre de son premier cas ; une case par semaine, le lundi écrit dessous.",
  # mois
  moisCasTitre="{M} : {n} nouveaux cas, {p} {sens} qu'en {m}", moisCasSous="Nouveaux cas confirmés par mois.",
  moisDecTitre="{M} : {n} décès, {p} {sens} qu'en {m}", moisDecSous="Nouveaux décès confirmés par mois.",
  deMoins="de moins", dePlus="de plus", autant="autant",
  moisZonTitre="{M} : {n} nouvelle{s} zone{s} de santé touchée{s}, contre {k} en {m}", moisZonSous="Zones de santé qui déclarent leur premier cas confirmé dans le mois ; {t} touchées à la fin de {m2}.",
  moisZonTotal="total : {n}", moisZonNote="Le suivi par zone commence le 21 mai : les zones touchées avant comptent en mai.",
  moisPartTitre="Le Nord-Kivu : {a} des nouveaux cas en {M}, {b} en {m}", moisPartSous="Part de chaque province dans les nouveaux cas confirmés du mois.",
  moisMai="Mai : à partir du 14 mai, premier bulletin.",
  moisRattCas="Juillet inclut deux rattrapages administratifs, les 22 et 30 juillet ({n} cas au-delà des cas du jour).",
  moisRattDec="Juillet inclut deux rattrapages : le cumul des décès bondit les 22 et 30 juillet.",
 ),
 "en": dict(
  moisLong=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  jours=["M", "T", "W", "T", "F", "S", "S"],
  kicker="17TH EBOLA OUTBREAK · DEMOCRATIC REPUBLIC OF THE CONGO",
  source="Sources: INSP SitReps", domaine="ebola-tracker.org",
  situation="Latest data: {d} (INSP SitRep No. {n})",
  semaine="Week of {a} to {b} (last complete week)",
  moisClos="Closed month: {m} · data as of {d}",
  calTitre="The outbreak calendar", calSous="One cell per day, tinted and numbered: cases in blue, deaths in red",
  calCas="NEW CONFIRMED CASES, THE DAY'S FIGURE IN EACH CELL", calDeces="DEATHS OF THE DAY",
  calRatt="Administrative catch-ups: on {a}, {ta} cases reported, {ra} of them backlog; on {b}, {tb}, of which {rb} cover 28 and 29 July, days without a bulletin.",
  calRattDeces="Deaths on {a} and {b} also include a backlog, whose share the bulletin does not give.",
  calHach="Hatched cell: no bulletin that day.",
  rayTitre="The outbreak's barcode", raySous="From {a} to {b}, one stripe per day: the darker it is, the more cases that day",
  rayCas="NEW CONFIRMED CASES, ONE STRIPE PER DAY", rayDeces="DEATHS OF THE DAY",
  rayManque="The few days without a bulletin take the colour of the surrounding seven-day average.",
  provTitre="{n} affected provinces", provSous="Cumulative confirmed cases by province, 15 May to {d}. The other {autres} provinces of the DRC have reported no cases.",
  provLegende="CONFIRMED CASES", provPhrase="{cas} confirmed cases in {zones} health zones, out of the {total} in these {np} provinces.",
  provPied=" · health zone boundaries: OCHA",
  lundi="Under each bar, the Monday of the week.",
  partTitre="Each province's share, week by week", partSous="How each week's new confirmed cases are split between the provinces.",
  partPhrase="North Kivu: {a} of new cases in the week of {da}, {b} in the week of {db}",
  partNote="Each bar is 100% of the week's new cases.",
  casTitre="New cases, week by week", casSous="Confirmed cases reported each week, Monday to Sunday, since the week of {d}.",
  casPhrase="{a} to {b}: {n} new cases, {v} on the previous week.",
  casNote="The weeks of 20 and 27 July include administrative catch-ups: {r1} cases on 22 July, {r2} on the 30th.",
  lieuTitre="Where patients die", lieuSous="Share of deaths in the community and in treatment centres, week by week, since the bulletins started publishing it.",
  lieuCom="deaths in the community", lieuCte="deaths in a treatment centre",
  lieuPhrase="From {a} to {b}, {p} of deaths happened outside a treatment centre ({c} of {t}).",
  lieuNote="A death in the community is a patient who was not isolated in time.",
  zonTitre="Active zones, quiet zones", zonSous="Each week, the health zones already affected: those with a new case in the last three weeks, and those without.",
  zonActive="active: one case or more in 3 weeks", zonCalme="quiet: no case for 3 weeks", zonTouchees="{n} affected",
  zonPhrase="On {d}, {a} of the {t} affected zones had a case in the last three weeks.",
  zonNote="Three weeks, or 21 days: the virus's maximum incubation period.",
  tapTitre="Zone by zone", tapSous="{n} health zones affected as of {d}, in order of first case, one cell per week.",
  tapLegende="New cases in the week:", tapNote="One row per zone, in order of its first case; one cell per week, the Monday written underneath.",
  moisCasTitre="{M}: {n} new cases, {p} {sens} than in {m}", moisCasSous="New confirmed cases per month.",
  moisDecTitre="{M}: {n} deaths, {p} {sens} than in {m}", moisDecSous="New confirmed deaths per month.",
  deMoins="fewer", dePlus="more", autant="as many",
  moisZonTitre="{M}: {n} new health zone{s} affected, against {k} in {m}", moisZonSous="Health zones reporting their first confirmed case in the month; {t} affected by the end of {m2}.",
  moisZonTotal="total: {n}", moisZonNote="Zone-level tracking starts on 21 May: zones affected before then count in May.",
  moisPartTitre="North Kivu: {a} of new cases in {M}, {b} in {m}", moisPartSous="Each province's share of the month's new confirmed cases.",
  moisMai="May: from 14 May, the first bulletin.",
  moisRattCas="July includes two administrative catch-ups, on 22 and 30 July ({n} cases beyond that day's cases).",
  moisRattDec="July includes two catch-ups: the death toll jumps on 22 and 30 July.",
 ),
 "sw": dict(
  moisLong=["Januari", "Februari", "Machi", "Aprili", "Mei", "Juni", "Julai", "Agosti", "Septemba", "Oktoba", "Novemba", "Desemba"],
  jours=["Jt", "Jn", "Jt", "Al", "Ij", "Jm", "Jp"],
  kicker="MLIPUKO WA 17 WA EBOLA · JAMHURI YA KIDEMOKRASIA YA KONGO",
  source="Vyanzo: ripoti za INSP", domaine="ebola-tracker.org",
  situation="Takwimu za mwisho: {d} (SitRep Na. {n} ya INSP)",
  semaine="Wiki ya {a} hadi {b} (wiki kamili ya mwisho)",
  moisClos="Mwezi uliokamilika: {m} · takwimu kufikia {d}",
  calTitre="Kalenda ya mlipuko", calSous="Kisanduku kimoja kwa siku, chenye rangi na nambari: visa kwa buluu, vifo kwa nyekundu",
  calCas="VISA VIPYA VILIVYOTHIBITISHWA, NAMBARI YA SIKU KATIKA KILA KISANDUKU", calDeces="VIFO VYA SIKU",
  calRatt="Marekebisho ya kiutawala: tarehe {a}, visa {ta} vilitangazwa, {ra} kati yake vikiwa vya nyuma; tarehe {b}, {tb}, kati yake {rb} vya tarehe 28 na 29 Julai, siku zisizo na ripoti.",
  calRattDeces="Vifo vya tarehe {a} na {b} pia vina marekebisho, ambayo ripoti haitaji sehemu yake.",
  calHach="Kisanduku chenye mistari: hakuna ripoti siku hiyo.",
  rayTitre="Msimbo-pau wa mlipuko", raySous="Kuanzia {a} hadi {b}, mstari mmoja kwa siku: kadiri ulivyo mweusi, ndivyo visa vilivyokuwa vingi",
  rayCas="VISA VIPYA VILIVYOTHIBITISHWA, MSTARI MMOJA KWA SIKU", rayDeces="VIFO VYA SIKU",
  rayManque="Siku chache zisizo na ripoti zimepakwa rangi ya wastani wa siku saba za karibu.",
  provTitre="Majimbo {n} yaliyoathirika", provSous="Visa vilivyothibitishwa kwa jumla kwa kila jimbo, kuanzia 15 Mei hadi {d}. Majimbo mengine {autres} ya DRC hayajatangaza kisa chochote.",
  provLegende="VISA VILIVYOTHIBITISHWA", provPhrase="Visa {cas} vilivyothibitishwa katika kanda {zones} za afya, kati ya {total} zilizo katika majimbo haya {np}.",
  provPied=" · mipaka ya kanda za afya: OCHA",
  lundi="Chini ya kila nguzo, Jumatatu ya wiki hiyo.",
  partTitre="Sehemu ya kila jimbo, wiki baada ya wiki", partSous="Mgawanyo wa visa vipya vilivyothibitishwa vya kila wiki kati ya majimbo.",
  partPhrase="Kivu Kaskazini: {a} ya visa vipya wiki ya {da}, {b} wiki ya {db}",
  partNote="Kila nguzo ni asilimia 100 ya visa vipya vya wiki hiyo.",
  casTitre="Visa vipya, wiki baada ya wiki", casSous="Visa vilivyothibitishwa vilivyotangazwa kila wiki, Jumatatu hadi Jumapili, tangu wiki ya {d}.",
  casPhrase="{a} hadi {b}: visa vipya {n}, {v} ikilinganishwa na wiki iliyotangulia.",
  casNote="Wiki za 20 na 27 Julai zina marekebisho ya kiutawala: visa {r1} tarehe 22 Julai, {r2} tarehe 30.",
  lieuTitre="Wagonjwa wanafia wapi", lieuSous="Sehemu ya vifo vilivyotokea katika jamii na katika vituo vya matibabu, wiki baada ya wiki, tangu ripoti zianze kuichapisha.",
  lieuCom="vifo katika jamii", lieuCte="vifo katika kituo cha matibabu",
  lieuPhrase="Kuanzia {a} hadi {b}, {p} ya vifo vilitokea nje ya kituo cha matibabu ({c} kati ya {t}).",
  lieuNote="Kifo katika jamii ni mgonjwa ambaye hakutengwa kwa wakati.",
  zonTitre="Kanda hai, kanda tulivu", zonSous="Kila wiki, kanda za afya ambazo tayari zimeathirika: zile zilizopata kisa kipya katika wiki tatu zilizopita, na zile ambazo hazijapata.",
  zonActive="hai: kisa kimoja au zaidi ndani ya wiki 3", zonCalme="tulivu: hakuna kisa kwa wiki 3", zonTouchees="{n} zilizoathirika",
  zonPhrase="Kufikia {d}, kanda {a} kati ya {t} zilizoathirika zilipata kisa katika wiki tatu zilizopita.",
  zonNote="Wiki tatu, yaani siku 21: muda mrefu zaidi wa kupevuka kwa virusi.",
  tapTitre="Kanda baada ya kanda", tapSous="Kanda {n} za afya zilizoathirika kufikia {d}, kwa mpangilio wa kisa cha kwanza, kisanduku kimoja kwa wiki.",
  tapLegende="Visa vipya katika wiki:", tapNote="Mstari mmoja kwa kila kanda, kwa mpangilio wa kisa chake cha kwanza; kisanduku kimoja kwa wiki, Jumatatu imeandikwa chini.",
  moisCasTitre="{M}: visa vipya {n}, {p} {sens} kuliko {m}", moisCasSous="Visa vipya vilivyothibitishwa kwa mwezi.",
  moisDecTitre="{M}: vifo {n}, {p} {sens} kuliko {m}", moisDecSous="Vifo vipya vilivyothibitishwa kwa mwezi.",
  deMoins="pungufu", dePlus="zaidi", autant="sawa na",
  moisZonTitre="{M}: kanda {n} mpya za afya zimeathirika, dhidi ya {k} mwezi {m}", moisZonSous="Kanda za afya zinazotangaza kisa chao cha kwanza kilichothibitishwa katika mwezi; {t} zimeathirika mwishoni mwa {m2}.",
  moisZonTotal="jumla: {n}", moisZonNote="Ufuatiliaji kwa kanda unaanza tarehe 21 Mei: kanda zilizoathirika kabla zinahesabiwa Mei.",
  moisPartTitre="Kivu Kaskazini: {a} ya visa vipya mwezi {M}, {b} mwezi {m}", moisPartSous="Sehemu ya kila jimbo katika visa vipya vilivyothibitishwa vya mwezi.",
  moisMai="Mei: kuanzia 14 Mei, ripoti ya kwanza.",
  moisRattCas="Julai ina marekebisho mawili ya kiutawala, tarehe 22 na 30 Julai (visa {n} zaidi ya visa vya siku).",
  moisRattDec="Julai ina marekebisho mawili: jumla ya vifo inaruka tarehe 22 na 30 Julai.",
 ),
}

# Textes de la page (sections, lecture de chaque visuel).
PAGE = {
 "fr": dict(
  h1a="Visuels", h1b="de l'épidémie",
  lede="Les images de l'épidémie, redessinées au fil des bulletins : à chaque nouveau bulletin, chaque lundi pour la dernière semaine complète, et au début de chaque mois. Chacune se télécharge, avec sa date et sa source.",
  b_eyebrow="À chaque bulletin", b_titre="L'épidémie au dernier bulletin", b_sous="SitRep n°{n} · données au {d}", b_rythme="mis à jour à chaque nouveau bulletin",
  s_eyebrow="Chaque semaine", s_titre="La semaine du {a} au {b}", s_sous="Dernière semaine complète, du lundi au dimanche.", s_rythme="mis à jour le lundi",
  m_eyebrow="Chaque mois", m_titre="{M}", m_sous="Dernier mois clos, comparé aux précédents.", m_rythme="mis à jour au début du mois",
  png="Télécharger en PNG", agrandir="Agrandir", fermer="Fermer",
  lire=dict(calendrier="Chaque case est un jour. Les coins ambrés de juillet signalent des rattrapages administratifs ; les cases hachurées, les jours sans bulletin.",
            rayures="Sans axe ni chiffre : la montée de juin, le plateau d'août, le reflux de septembre se lisent comme une texture.",
            provinces="L'épidémie reste concentrée dans le nord-est : les autres provinces du pays n'ont déclaré aucun cas.",
            part="La part de chaque province dans les cas de chaque semaine : on y voit monter le Nord-Kivu face à l'Ituri.",
            cas="La tendance sans le bruit des jours : une semaine pleine lisse les jours sans bulletin.",
            lieu="Un décès dans la communauté est un malade qui n'a pas été isolé à temps : c'est ce qui échappe à la riposte.",
            zones="Une zone calme depuis trois semaines n'a plus de chaîne de transmission connue.",
            tapis="Une ligne par zone, dans l'ordre d'arrivée du virus : l'escalier dit l'extension, la teinte l'intensité.",
            mzones="Le rythme d'extension : combien de zones le virus a gagnées chaque mois.",
            mcas="Le mois clos face aux précédents.", mdeces="Les décès du mois clos face aux précédents.",
            mpart="Comment les nouveaux cas de chaque mois se répartissent entre les provinces."),
 ),
 "en": dict(
  h1a="Visuals", h1b="of the outbreak",
  lede="Images of the outbreak, redrawn as the bulletins come in: with every new bulletin, each Monday for the last complete week, and at the start of each month. Each one can be downloaded, with its date and source.",
  b_eyebrow="With every bulletin", b_titre="The outbreak at the latest bulletin", b_sous="SitRep No. {n} · data as of {d}", b_rythme="updated with every new bulletin",
  s_eyebrow="Every week", s_titre="The week of {a} to {b}", s_sous="Last complete week, Monday to Sunday.", s_rythme="updated on Mondays",
  m_eyebrow="Every month", m_titre="{M}", m_sous="Last closed month, compared with the previous ones.", m_rythme="updated at the start of the month",
  png="Download as PNG", agrandir="Enlarge", fermer="Close",
  lire=dict(calendrier="Each cell is a day. The amber corners in July mark administrative catch-ups; hatched cells, days without a bulletin.",
            rayures="No axis, no figure: the June rise, the August plateau and the September ebb read like a texture.",
            provinces="The outbreak remains concentrated in the north-east: the country's other provinces have reported no cases.",
            part="Each province's share of each week's cases: North Kivu rising against Ituri.",
            cas="The trend without the day-to-day noise: a full week smooths out the days without a bulletin.",
            lieu="A death in the community is a patient who was not isolated in time: what escapes the response.",
            zones="A zone quiet for three weeks no longer has a known chain of transmission.",
            tapis="One row per zone, in the order the virus arrived: the staircase shows the spread, the shade the intensity.",
            mzones="The pace of spread: how many zones the virus reached each month.",
            mcas="The closed month against the previous ones.", mdeces="The closed month's deaths against the previous ones.",
            mpart="How each month's new cases are split between the provinces."),
 ),
 "sw": dict(
  h1a="Michoro", h1b="ya mlipuko",
  lede="Picha za mlipuko, zinazochorwa upya kadiri ripoti zinavyotoka: kwa kila ripoti mpya, kila Jumatatu kwa wiki kamili ya mwisho, na mwanzoni mwa kila mwezi. Kila moja inaweza kupakuliwa, pamoja na tarehe na chanzo chake.",
  b_eyebrow="Kwa kila ripoti", b_titre="Mlipuko katika ripoti ya mwisho", b_sous="SitRep Na. {n} · takwimu kufikia {d}", b_rythme="husasishwa kwa kila ripoti mpya",
  s_eyebrow="Kila wiki", s_titre="Wiki ya {a} hadi {b}", s_sous="Wiki kamili ya mwisho, Jumatatu hadi Jumapili.", s_rythme="husasishwa Jumatatu",
  m_eyebrow="Kila mwezi", m_titre="{M}", m_sous="Mwezi wa mwisho uliokamilika, ukilinganishwa na iliyotangulia.", m_rythme="husasishwa mwanzoni mwa mwezi",
  png="Pakua kama PNG", agrandir="Panua", fermer="Funga",
  lire=dict(calendrier="Kila kisanduku ni siku moja. Pembe za rangi ya kahawia mwezi Julai zinaonyesha marekebisho ya kiutawala; visanduku vyenye mistari, siku zisizo na ripoti.",
            rayures="Bila mhimili wala nambari: kupanda kwa Juni, utulivu wa Agosti na kushuka kwa Septemba vinasomeka kama muundo.",
            provinces="Mlipuko bado umejikita kaskazini-mashariki: majimbo mengine ya nchi hayajatangaza kisa chochote.",
            part="Sehemu ya kila jimbo katika visa vya kila wiki: Kivu Kaskazini inapanda dhidi ya Ituri.",
            cas="Mwelekeo bila kelele za kila siku: wiki nzima inalainisha siku zisizo na ripoti.",
            lieu="Kifo katika jamii ni mgonjwa ambaye hakutengwa kwa wakati: kile kinachokwepa mapambano.",
            zones="Kanda iliyotulia kwa wiki tatu haina tena mnyororo wa maambukizi unaojulikana.",
            tapis="Mstari mmoja kwa kila kanda, kwa mpangilio wa kufika kwa virusi: ngazi zinaonyesha kuenea, rangi inaonyesha ukali.",
            mzones="Kasi ya kuenea: virusi vimefikia kanda ngapi kila mwezi.",
            mcas="Mwezi uliokamilika ukilinganishwa na iliyotangulia.", mdeces="Vifo vya mwezi uliokamilika ukilinganishwa na iliyotangulia.",
            mpart="Jinsi visa vipya vya kila mwezi vinavyogawanyika kati ya majimbo."),
 ),
}

# ---------------------------------------------------------------- outils
def _j(chemin):
    with open(os.path.join(ROOT, chemin), encoding="utf-8") as f:
        return json.load(f)

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _cle(t):
    t = unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", t)

def hexmix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

def ramp(cols, t):
    t = max(0.0, min(1.0, t)) * (len(cols) - 1); i = min(int(t), len(cols) - 2)
    return hexmix(cols[i], cols[i + 1], t - i)

def quantile(vals, p):
    v = sorted(x for x in vals if x is not None)
    return v[min(len(v) - 1, int(len(v) * p))] if v else 1

def parse_rings(d):
    rings, cur = [], []
    for cmd, xs, ys in re.findall(r"([MLZ])\s*([-\d.]*)\s*([-\d.]*)", d):
        if cmd == "M":
            if cur: rings.append(cur)
            cur = [(float(xs), float(ys))]
        elif cmd == "L":
            cur.append((float(xs), float(ys)))
        elif cmd == "Z":
            if cur: rings.append(cur); cur = []
    if cur: rings.append(cur)
    return rings

def centroide(ring):
    a = cx = cy = 0.0; n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]; x2, y2 = ring[(i + 1) % n]; f = x1 * y2 - x2 * y1
        a += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f
    if abs(a) < 1e-9:
        return ring[0], 0.0
    a *= 0.5
    return (cx / (6 * a), cy / (6 * a)), abs(a)


class Contexte:
    """Les donnees et les conventions d'une langue, lues une fois par page."""

    def __init__(self, lang, mois_courts):
        self.lang = lang; self.t = TXT[lang]; self.p = PAGE[lang]; self.r = RIP[lang]; self.mc = mois_courts
        self.latest = _j("data/latest.json"); self.sitreps = _j("data/sitreps.json")
        self.ph = _j("data/province-history.json"); self.zh = _j("data/zones-history.json")
        self.geo = _j("site/geo/zones-overview.json"); self.dl = _j("data/deces-lieu.json")["parDate"]
        al = ((_j("site/pages.json").get("zoneAliases") or {}).get("places") or {})
        self.alias = {_cle(k): _cle(v) for k, v in al.items()}
        self.FIN = D(self.latest["meta"]["reportingDate"]); self.SITREP = self.latest["meta"]["sitrepNumber"]
        self.DEBUT = D(self.sitreps[0]["date"])
        self.cum = {x["date"]: x for x in self.sitreps}
        # semaines completes (lundi-dimanche) depuis la premiere semaine pleine
        dim = self.FIN - dt.timedelta(days=(self.FIN.weekday() + 1) % 7)
        lun = self.DEBUT + dt.timedelta(days=(7 - self.DEBUT.weekday()) % 7)
        self.semaines = []
        while lun + dt.timedelta(6) <= dim:
            self.semaines.append((lun, lun + dt.timedelta(6))); lun += dt.timedelta(7)
        # serie par zone, cle normalisee + alias
        self.serie_z = OrderedDict()
        for s in sorted(self.zh, key=lambda s: s["date"]):
            for z in s["zones"]:
                k = (self.cle(z["name"]), _cle(z["province"]))
                self.serie_z.setdefault(k, []).append((D(s["date"]), z.get("cases") or 0, z["name"]))
        # mois clos
        self.mois = []
        m = (self.DEBUT.year, self.DEBUT.month)
        while True:
            fin = (dt.date(m[0] + (m[1] == 12), m[1] % 12 + 1, 1) - dt.timedelta(1))
            if fin > self.FIN: break
            self.mois.append((m, fin)); m = (m[0] + (m[1] == 12), m[1] % 12 + 1)
        # series quotidiennes (nouveaux cas et deces par bulletin)
        self.jours = OrderedDict(); prev = None
        for r in self.sitreps:
            d = D(r["date"]); nc = nd = None
            if prev:
                if r["confirmed"] is not None and prev["confirmed"] is not None: nc = max(0, r["confirmed"] - prev["confirmed"])
                if r["deaths"] is not None and prev.get("deaths") is not None: nd = max(0, r["deaths"] - prev["deaths"])
            self.jours[d] = (nc, nd)
            if r["confirmed"] is not None:
                prev = {"confirmed": r["confirmed"], "deaths": r["deaths"] if r["deaths"] is not None else (prev or {}).get("deaths")}
        self.tous_jours = [self.DEBUT + dt.timedelta(i) for i in range((self.FIN - self.DEBUT).days + 1)]

    # conventions de langue (memes regles que build_pages)
    def cle(self, nom):
        k = _cle(nom); return self.alias.get(k, k)
    def nb(self, n):
        s = "{:,}".format(int(round(n)))
        return s.replace(",", " ") if self.lang == "fr" else s
    def pc(self, v, d=0):
        s = ("%.*f" % (d, v))
        return s.replace(".", ",") + " %" if self.lang == "fr" else s + "%"
    def var(self, a, b):
        v = round(100 * (a - b) / b) if b else 0
        return ("+" if v > 0 else "−" if v < 0 else "") + self.pc(abs(v))
    def dc(self, d):
        return "%d %s" % (d.day, self.mc[d.month - 1])
    def dl_(self, d):
        m = self.t["moisLong"][d.month - 1]
        return "%d %s %d" % (d.day, m, d.year)
    def M(self, ym):
        m = self.t["moisLong"][ym[1] - 1]; return m[0].upper() + m[1:]
    def m(self, ym):
        return self.t["moisLong"][ym[1] - 1]
    def au(self, d):
        k = max(k for k in self.cum if k <= d.isoformat()); return self.cum[k]
    def prov_au(self, d):
        av = [s for s in self.ph if s["date"] <= d.isoformat()]
        if not av: return {}
        return {p["name"]: p for p in max(av, key=lambda s: s["date"])["provinces"]}
    def cum_zone(self, k, d):
        pts = [c for dd, c, _ in self.serie_z[k] if dd <= d]
        return max(pts) if pts else 0
    def zones_touchees(self, d):
        return {k for k in self.serie_z if self.cum_zone(k, d) > 0}
    def ordre_provinces(self):
        return [p["name"] for p in sorted(self.latest["provinces"], key=lambda p: -p["confirmed"])]

    # ------------------------------------------------------------ dessin
    def T(self, x, y, txt, size=15, fill=INK_DIM, anchor="start", weight=400, fam=SANS, extra=""):
        return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" font-weight="%d" fill="%s" text-anchor="%s"%s>%s</text>'
                % (x, y, fam, size, weight, fill, anchor, extra, esc(txt)))
    def legende(self, x, y, items, gap=24):
        out = []
        for lab, col in items:
            out.append('<rect x="%d" y="%d" width="14" height="14" rx="3" fill="%s"/>' % (x, y - 12, col) + self.T(x + 22, y, lab, 15, INK_DIM))
            x += 22 + int(len(lab) * 8.2) + gap
        return "".join(out)
    def axe_semaines(self, X0, bw, Y1, sems):
        return "".join('<text transform="translate(%.1f %d) rotate(-90)" text-anchor="end" font-family="%s" font-size="13" fill="%s">%s</text>'
                       % (X0 + i * bw + bw / 2 + 4, Y1 + 10, SANS, INK_FAINT, esc(self.dc(a))) for i, (a, b) in enumerate(sems))
    def carte(self, titre, sous, corps, h=1200, pied=None, source_plus=""):
        import textwrap
        # Un titre calcule peut etre long (« Septembre : 3 nouvelles zones de
        # sante touchees, contre 11 en aout ») : au-dela de la largeur, il
        # passe sur deux lignes et le sous-titre descend d'autant.
        tl = textwrap.wrap(titre, 46) if len(titre) > 50 else [titre]
        dy = 46 * (len(tl) - 1)
        l = textwrap.wrap(sous, 96)[:2]
        s = "".join(self.T(60, 146 + dy + i * 26, x, 19, INK_LABEL) for i, x in enumerate(l))
        pied = pied if pied is not None else self.t["situation"].format(d=self.dl_(self.FIN), n=self.SITREP)
        return ('<svg viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="%s"><rect width="%d" height="%d" fill="%s"/>'
                '<circle cx="66" cy="52" r="6" fill="%s"/>%s%s%s%s'
                '<line x1="60" x2="%d" y1="%d" y2="%d" stroke="%s"/>%s'
                '<text x="%d" y="%d" text-anchor="end" font-family="%s" font-size="15" fill="%s">%s · <tspan font-weight="700" fill="%s">%s</tspan></text></svg>') % (
            W, h, esc(titre + ". " + sous), W, h, BG, RED,
            self.T(82, 57, self.t["kicker"], 15, INK_LABEL, weight=700, extra=' letter-spacing=".08em"'),
            "".join(self.T(60, 110 + i * 46, x, 42 if len(tl) == 1 else 38, INK, weight=600, fam=SERIF) for i, x in enumerate(tl)), s, corps,
            W - 60, h - 92, h - 92, LINE, self.T(60, h - 58, pied, 15, INK_DIM, weight=600),
            W - 60, h - 58, SANS, INK_FAINT, esc(self.t["source"] + source_plus), INK_DIM, self.t["domaine"])
    def pied_semaine(self):
        a, b = self.semaines[-1]
        return self.t["semaine"].format(a=self.dc(a), b=self.dl_(b))
    def pied_mois(self):
        return self.t["moisClos"].format(m="%s %d" % (self.m(self.mois[-1][0]), self.mois[-1][0][0]), d=self.dl_(self.mois[-1][1]))


# ================================================================ a chaque bulletin
def calendrier(c):
    t = c.t
    out = ['<defs><pattern id="vx-hach" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#C9C4BE" stroke-width="1.2"/></pattern></defs>']
    mois = sorted({(d.year, d.month) for d in c.tous_jours})
    # Taille des cases calculee depuis le nombre de mois (11 octobre 2026) ;
    # sous 21 px, les mois passent sur deux lignes au lieu de se chevaucher.
    gap, mgap = 2, 16
    for par_ligne in range(len(mois), 0, -1):
        colw = (W - 120 - (par_ligne - 1) * mgap) / par_ligne
        cell = int((colw - 6 * gap) / 7)
        if cell >= 21: break
    pas = cell + gap; coin = round(cell * 0.4); hligne = 36 + 6 * pas + 52
    def bloc(vals, cols, y, titre):
        smax = quantile(vals.values(), 0.95)
        out.append(c.T(60, y, titre, 15, INK_DIM, weight=700, extra=' letter-spacing=".06em"'))
        y += 40
        for k, (yy, mm) in enumerate(mois):
            ligne, col = divmod(k, par_ligne)
            x0 = 60 + col * (colw + mgap); yl = y + ligne * hligne
            out.append(c.T(x0, yl, c.M((yy, mm)), 24, INK, weight=600, fam=SERIF))
            for i, l in enumerate(t["jours"]):
                out.append(c.T(x0 + i * pas + cell / 2, yl + 24, l, 10, INK_FAINT, "middle"))
            first = dt.date(yy, mm, 1); ndays = (dt.date(yy + (mm == 12), mm % 12 + 1, 1) - first).days
            for day in range(ndays):
                d = first + dt.timedelta(day); row = (day + first.weekday()) // 7
                cx = x0 + d.weekday() * pas; cy = yl + 36 + row * pas
                v = vals.get(d)
                if d < c.DEBUT or d > c.FIN: fill, stroke = "none", LINE_SOFT
                elif v is None: fill, stroke = "url(#vx-hach)", LINE
                else: fill, stroke = (ramp(cols, v / smax) if v > 0 else PANEL), LINE_SOFT
                out.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="3" fill="%s" stroke="%s"/>' % (cx, cy, cell, cell, fill, stroke))
                if v is not None:
                    out.append(c.T(cx + cell / 2, cy + cell / 2 + 3.5, str(v), 10 if v < 100 else 8.5, "#fff" if v / smax > 0.5 else INK, "middle", 600))
                if d.isoformat() in RATTRAPAGES:
                    out.append('<path d="M%.1f,%.1f h%d v%d z" fill="%s"/>' % (cx + cell - coin, cy, coin, coin, AMBER))
        lignes = (len(mois) - 1) // par_ligne + 1
        return y + (lignes - 1) * hligne + 36 + 6 * pas
    cas = {d: c.jours.get(d, (None, None))[0] for d in c.tous_jours}
    dec = {d: c.jours.get(d, (None, None))[1] for d in c.tous_jours}
    y = bloc(cas, MAP[1:], 240, t["calCas"])
    r1, r2 = sorted(RATTRAPAGES)
    def note(yy, texte):
        import textwrap
        out.append('<path d="M60,%d h11 v11 z" fill="%s"/>' % (yy - 11, AMBER))
        lignes = textwrap.wrap(texte, 150)
        for i, l in enumerate(lignes):
            out.append(c.T(78, yy + i * 20, l, 14, INK_DIM))
        return len(lignes)
    t1, t2 = cas[D(r1)], cas[D(r2)]
    n = note(y + 30, t["calRatt"].format(a=c.dc(D(r1)), ta=c.nb(t1), ra=c.nb(t1 - RATTRAPAGES[r1]), b=c.dc(D(r2)), tb=c.nb(t2), rb=c.nb(t2 - RATTRAPAGES[r2])))
    out.append(c.T(60, y + 34 + n * 20, t["calHach"], 14, INK_FAINT))
    y = bloc(dec, REDS, y + 100 + n * 20, t["calDeces"])
    n = note(y + 24, t["calRattDeces"].format(a=c.dc(D(r1)), b=c.dc(D(r2))))
    return c.carte(t["calTitre"], t["calSous"], "".join(out), h=int(y + 24 + (n - 1) * 20 + 130))


def rayures(c):
    t = c.t; n = len(c.tous_jours); x0, x1 = 60, W - 60; bw = (x1 - x0) / n
    cas = [c.jours.get(d, (None, None))[0] for d in c.tous_jours]
    dec = [c.jours.get(d, (None, None))[1] for d in c.tous_jours]
    out = []
    def voisins(vals, i):
        v = [vals[j] for j in range(max(0, i - 3), min(len(vals), i + 4)) if vals[j] is not None]
        return sum(v) / len(v) if v else 0
    def bande(vals, cols, y, hh):
        smax = quantile(vals, 0.95)
        for i, v in enumerate(vals):
            out.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"/>' % (x0 + i * bw, y, bw + 0.3, hh, ramp(cols, (v if v is not None else voisins(vals, i)) / smax)))
    out.append(c.T(60, 235, t["rayCas"], 15, INK_DIM, weight=700, extra=' letter-spacing=".06em"'))
    bande(cas, MAP[1:], 252, 380)
    out.append(c.T(60, 700, t["rayDeces"], 15, INK_DIM, weight=700, extra=' letter-spacing=".06em"'))
    bande(dec, REDS, 717, 300)
    for d in c.tous_jours:
        if (d.day == 1 or d == c.DEBUT) and (c.FIN - d).days > 12:
            x = x0 + (d - c.DEBUT).days * bw
            out.append('<line x1="%.1f" x2="%.1f" y1="1030" y2="1042" stroke="%s"/>' % (x, x, INK_FAINT) + c.T(x + 4, 1066, c.dc(d), 16, INK_DIM))
    out.append(c.T(x1, 1066, c.dc(c.FIN), 16, INK, "end", 700))
    out.append(c.T(60, 1098, t["rayManque"], 16, INK_DIM))
    return c.carte(t["rayTitre"], t["raySous"].format(a=c.dc(c.DEBUT), b=c.dl_(c.FIN)), "".join(out))


def carte_provinces(c):
    t = c.t; provs = {_cle(p["name"]): p for p in c.latest["provinces"]}
    seuils = [10, 100, 1000, 5000]; cols = [MAP[1], MAP[2], MAP[4], MAP[5], MAP[6]]
    labels = ["1–9", "10–99", "100–999", c.nb(1000) + "–" + c.nb(4999), c.nb(5000) + "+"]
    classe = lambda n: sum(n >= s for s in seuils)
    sc, ox, oy = 0.86, 60, 195
    out = ['<g transform="translate(%d,%d) scale(%s)">' % (ox, oy, sc)]
    par_prov = OrderedDict()
    for z in c.geo["zones"]:
        par_prov.setdefault(_cle(z["province"]), []).append(z)
    def contour(zs, couleur, largeur):
        for z in zs:
            gros = [r for r in parse_rings(z["d"]) if centroide(r)[1] >= 3]
            d = " ".join("M" + " L".join("%.1f %.1f" % p for p in r) + " Z" for r in gros)
            if d: out.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-linejoin="round"/>' % (d, couleur, largeur / sc))
    def remplissage(zs, couleur):
        for z in zs: out.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f" stroke-linejoin="round"/>' % (z["d"], couleur, couleur, 3 / sc))
    for pk, zs in par_prov.items():
        if pk not in provs: contour(zs, "#A9A39B", 7); remplissage(zs, "#F1EEE9")
    for pk, zs in par_prov.items():
        if pk in provs: contour(zs, INK, 7); remplissage(zs, cols[classe(provs[pk]["confirmed"])])
    kin = next(l for l in c.geo["landmarks"] if l["name"] == "Kinshasa")
    out.append('<circle cx="%s" cy="%s" r="%.1f" fill="%s"/>' % (kin["x"], kin["y"], 4 / sc, INK)
               + c.T(kin["x"] + 10 / sc, kin["y"] + 5 / sc, "Kinshasa", "%.1f" % (14 / sc), INK_DIM))
    out.append("</g>")
    DECAL = {"nordkivu": (0, -22), "sudkivu": (0, -6), "tshopo": (0, -10), "basuele": (0, -8), "hautuele": (0, -6), "sudubangi": (8, 4)}
    for pk, pinfo in provs.items():
        sx = sy = sa = 0.0
        for z in par_prov.get(pk, []):
            ring = max(parse_rings(z["d"]), key=lambda r: centroide(r)[1]); (cx, cy), a = centroide(ring)
            sx += cx * a; sy += cy * a; sa += a
        if not sa: continue
        cx = ox + (sx / sa) * sc + DECAL.get(pk, (0, 0))[0]; cy = oy + (sy / sa) * sc + DECAL.get(pk, (0, 0))[1]
        n = pinfo["confirmed"]; enc = "#fff" if classe(n) >= 2 else INK
        out.append(c.T(cx, cy - 6, pinfo["name"], 15, enc, "middle", 700) + c.T(cx, cy + 22, c.nb(n), 26, enc, "middle", 600, SERIF))
    lx, ly = 960, 250
    out.append(c.T(lx, ly, t["provLegende"], 15, INK_DIM, weight=700, extra=' letter-spacing=".06em"'))
    for i, l in enumerate(labels):
        out.append('<rect x="%d" y="%d" width="28" height="22" rx="3" fill="%s"/>' % (lx, ly + 20 + i * 34, cols[i]) + c.T(lx + 38, ly + 36 + i * 34, l, 15, INK_DIM))
    cas = sum(p["confirmed"] for p in c.latest["provinces"])
    zones = sum(p["healthZonesAffected"]["n"] for p in c.latest["provinces"])
    total = sum(p["healthZonesAffected"]["total"] for p in c.latest["provinces"])
    out.append(c.T(60, 1200 - 118, t["provPhrase"].format(cas=c.nb(cas), zones=zones, total=total, np=len(provs)), 22, INK, fam=SERIF))
    return c.carte(t["provTitre"].format(n=len(provs)) if c.lang != "fr" else t["provTitre"].format(n=["Zéro", "Une", "Deux", "Trois", "Quatre", "Cinq", "Six", "Sept", "Huit", "Neuf", "Dix"][len(provs)] if len(provs) <= 10 else len(provs)),
                   t["provSous"].format(d=c.dl_(c.FIN), autres=len(par_prov) - len(provs)), "".join(out), source_plus=t["provPied"])


# ================================================================ chaque semaine
def hebdo_prov(c):
    noms = c.ordre_provinces(); res = {n: [] for n in noms}
    for a, b in c.semaines:
        pa, pb = c.prov_au(b), c.prov_au(a - dt.timedelta(1))
        for n in noms:
            res[n].append(pa.get(n, {}).get("confirmed", 0) - pb.get(n, {}).get("confirmed", 0))
    return res


def h_part(c):
    t = c.t; hp = hebdo_prov(c); ordre = c.ordre_provinces()
    X0, X1, Y0, Y1 = 110, 1010, 300, 840
    n = len(c.semaines); bw = (X1 - X0) / n; out = []
    for v in (0, 25, 50, 75, 100):
        out.append(c.T(X0 - 12, Y1 - (Y1 - Y0) * v / 100 + 5, c.pc(v), 13, INK_FAINT, "end"))
    dernier = []
    for i, (a, b) in enumerate(c.semaines):
        vals = [(p, max(hp[p][i], 0)) for p in ordre]
        tot = sum(v for _, v in vals) or 1; y = Y1; x = X0 + i * bw + 2; segs = []
        for p, v in vals:
            if not v: continue
            h = (Y1 - Y0) * v / tot
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"><title>%s, %s : %s (%s)</title></rect>'
                       % (x, y - h, bw - 4, max(h - 1, 0.5), PROV.get(p, INK_DIM), esc(c.dc(a)), esc(p), c.nb(v), c.pc(100 * v / tot)))
            segs.append((p, y - h / 2, v / tot)); y -= h
        dernier = segs
    out.append(c.axe_semaines(X0, bw, Y1, c.semaines))
    for p, ym, part in dernier:
        if part >= 0.03:
            out.append(c.T(X1 + 10, ym + 5, "%s %s" % (p, c.pc(100 * part)), 14, INK, weight=600))
    out.append(c.legende(110, 262, [(p, PROV.get(p, INK_DIM)) for p in ordre], gap=14))
    nk = hp.get("Nord-Kivu", [0] * n); t0 = sum(max(hp[p][0], 0) for p in ordre) or 1; t1 = sum(max(hp[p][-1], 0) for p in ordre) or 1
    out.append(c.T(60, 975, t["partPhrase"].format(a=c.pc(100 * max(nk[0], 0) / t0), da=c.dc(c.semaines[0][0]), b=c.pc(100 * max(nk[-1], 0) / t1), db=c.dc(c.semaines[-1][0])), 24, INK, fam=SERIF))
    out.append(c.T(60, 1008, t["partNote"] + " " + t["lundi"], 15, INK_DIM))
    return c.carte(t["partTitre"], t["partSous"], "".join(out), h=1110, pied=c.pied_semaine())


def h_cas(c):
    t = c.t
    vals = [c.au(b)["confirmed"] - c.au(a - dt.timedelta(1))["confirmed"] for a, b in c.semaines]
    X0, X1, Y0, Y1 = 110, 1140, 290, 840
    mx = max(vals); bw = (X1 - X0) / len(vals); out = []
    for v in range(0, mx + 1, 100 if mx > 400 else 50):
        y = Y1 - (Y1 - Y0) * v / mx
        out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="%s"/>' % (X0, X1, y, y, LINE_SOFT) + c.T(X0 - 12, y + 5, c.nb(v), 13, INK_FAINT, "end"))
    for i, ((a, b), v) in enumerate(zip(c.semaines, vals)):
        x = X0 + i * bw + 3; h = (Y1 - Y0) * v / mx
        col = BLUE if i == len(vals) - 1 else ("#7EACC3" if i == len(vals) - 2 else "#B7D3E1")
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2" fill="%s"><title>%s → %s : %s</title></rect>' % (x, Y1 - h, bw - 6, h, col, esc(c.dc(a)), esc(c.dc(b)), c.nb(v)))
        out.append(c.T(x + (bw - 6) / 2, Y1 - h - 7, c.nb(v), 12, INK if i >= len(vals) - 2 else INK_DIM, "middle", 700 if i == len(vals) - 1 else 500))
    out.append(c.axe_semaines(X0, bw, Y1, c.semaines))
    a, b = c.semaines[-1]
    out.append(c.T(60, 975, t["casPhrase"].format(a=c.dc(a), b=c.dc(b), n=c.nb(vals[-1]), v=c.var(vals[-1], vals[-2])), 24, INK, fam=SERIF))
    r = [c.jours.get(D(k), (0, 0))[0] - v for k, v in sorted(RATTRAPAGES.items())]
    out.append(c.T(60, 1008, t["casNote"].format(r1=c.nb(r[0]), r2=c.nb(r[1])) + " " + t["lundi"], 15, INK_DIM))
    return c.carte(t["casTitre"], t["casSous"].format(d=c.dc(c.semaines[0][0])), "".join(out), h=1110, pied=c.pied_semaine())


def h_lieu(c):
    t = c.t; debut = min(x["date"] for x in c.dl); data = []
    for a, b in c.semaines:
        if b.isoformat() < debut: continue
        xs = [x for x in c.dl if a.isoformat() <= x["date"] <= b.isoformat()]
        co = sum(sum(p.get("communautaires") or 0 for p in x["provinces"].values()) for x in xs)
        ct = sum(sum(p.get("intraCte") or 0 for p in x["provinces"].values()) for x in xs)
        data.append((a, b, co, ct))
    X0, X1, Y0, Y1 = 110, 1140, 300, 820
    bw = (X1 - X0) / len(data); out = []
    for v in (0, 25, 50, 75, 100):
        out.append(c.T(X0 - 12, Y1 - (Y1 - Y0) * v / 100 + 5, c.pc(v), 13, INK_FAINT, "end"))
    for i, (a, b, co, ct) in enumerate(data):
        x = X0 + i * bw + 3
        if not co + ct:
            out.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="none" stroke="%s" stroke-dasharray="3 3"/>' % (x, Y0, bw - 6, Y1 - Y0, LINE)); continue
        h = (Y1 - Y0) * co / (co + ct)
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"><title>%s : %d / %d</title></rect>' % (x, Y1 - h, bw - 6, h, RED, esc(c.dc(a)), co, co + ct))
        out.append('<rect x="%.1f" y="%d" width="%.1f" height="%.1f" fill="#E5B7AE"/>' % (x, Y0, bw - 6, Y1 - Y0 - h - 2))
        out.append(c.T(x + (bw - 6) / 2, Y1 - h + 22, c.pc(100 * co / (co + ct)), 13, "#fff", "middle", 700))
    out.append(c.axe_semaines(X0, bw, Y1, [(d[0], d[1]) for d in data]))
    out.append(c.legende(110, 262, [(t["lieuCom"], RED), (t["lieuCte"], "#E5B7AE")]))
    a, b, co, ct = [d for d in data if d[2] + d[3]][-1]
    out.append(c.T(60, 960, t["lieuPhrase"].format(a=c.dc(a), b=c.dc(b), p=c.pc(100 * co / (co + ct)), c=co, t=co + ct), 24, INK, fam=SERIF))
    out.append(c.T(60, 994, t["lieuNote"] + " " + t["lundi"], 15, INK_DIM))
    return c.carte(t["lieuTitre"], t["lieuSous"], "".join(out), h=1110, pied=c.pied_semaine())


def h_zones(c):
    t = c.t; data = []
    for a, b in c.semaines:
        ac = ca = 0
        for k in c.serie_z:
            cf = c.cum_zone(k, b)
            if not cf: continue
            if cf > c.cum_zone(k, b - dt.timedelta(21)): ac += 1
            else: ca += 1
        data.append((a, b, ac, ca))
    mx = max(x[2] + x[3] for x in data)
    X0, X1, Y0, Y1 = 110, 1140, 300, 840
    bw = (X1 - X0) / len(data); out = []
    for v in range(0, mx + 1, 10):
        y = Y1 - (Y1 - Y0) * v / mx
        out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="%s"/>' % (X0, X1, y, y, LINE_SOFT) + c.T(X0 - 12, y + 5, str(v), 13, INK_FAINT, "end"))
    for i, (a, b, ac, ca) in enumerate(data):
        x = X0 + i * bw + 3; h1 = (Y1 - Y0) * ac / mx; h2 = (Y1 - Y0) * ca / mx
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"><title>%s : %d / %d</title></rect>' % (x, Y1 - h1, bw - 6, h1, BLUE, esc(c.dc(a)), ac, ac + ca))
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#B7D3E1"/>' % (x, Y1 - h1 - h2 - 2, bw - 6, h2))
    out.append(c.axe_semaines(X0, bw, Y1, [(d[0], d[1]) for d in data]))
    a, b, ac, ca = data[-1]
    out.append(c.T(X1, Y1 - (Y1 - Y0) * (ac + ca) / mx - 12, t["zonTouchees"].format(n=ac + ca), 15, INK, "end", 700))
    out.append(c.legende(110, 262, [(t["zonActive"], BLUE), (t["zonCalme"], "#B7D3E1")]))
    out.append(c.T(60, 975, t["zonPhrase"].format(d=c.dl_(b), a=ac, t=ac + ca), 24, INK, fam=SERIF))
    out.append(c.T(60, 1008, t["zonNote"] + " " + t["lundi"], 15, INK_DIM))
    return c.carte(t["zonTitre"], t["zonSous"], "".join(out), h=1110, pied=c.pied_semaine())


def h_tapis(c):
    t = c.t; fin = c.semaines[-1][1]; premiere = {}
    for k, pts in c.serie_z.items():
        d1 = min((dd for dd, cc, _ in pts if cc > 0), default=None)
        if d1 and d1 <= fin: premiere[k] = d1
    nom = {k: c.serie_z[k][-1][2] for k in premiere}
    ordre = sorted(premiere, key=lambda k: (premiere[k], nom[k]))
    rows = len(ordre); n = len(c.semaines)
    x0, y0 = 250, 250; cw = (1140 - x0) / n; rh = 11.2
    seuils = [1, 5, 20, 50, 100]
    col = lambda v: "#EFECE8" if v <= 0 else MAP[min(sum(v >= s for s in seuils), 5)]
    out = []
    for j, (a, b) in enumerate(c.semaines):
        if j == 0 or a.day <= 7:
            xm = x0 + j * cw
            out.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" stroke="%s" stroke-width="1.5"/>' % (xm, xm, y0 - 30, y0 - 4, INK_DIM)
                       + c.T(xm + 6, y0 - 12, c.M((a.year, a.month)), 14, INK, weight=600))
    for j, (a, b) in enumerate(c.semaines):
        x = x0 + j * cw
        for i, k in enumerate(ordre):
            if premiere[k] > b: continue
            v = c.cum_zone(k, b) - c.cum_zone(k, a - dt.timedelta(1))
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1.5" fill="%s"><title>%s, %s : %d</title></rect>' % (x + 1, y0 + i * rh + 1, cw - 2, rh - 2, col(v), esc(nom[k]), esc(c.dc(a)), max(v, 0)))
    for i, k in enumerate(ordre):
        out.append(c.T(x0 - 8, y0 + i * rh + rh * 0.78, nom[k], 9.5, INK_DIM, "end"))
    yb = y0 + rows * rh
    out.append(c.axe_semaines(x0, cw, yb, c.semaines))
    ly = yb + 80
    out.append(c.T(x0, ly, t["tapLegende"], 14, INK_DIM))
    for i, l in enumerate(["0", "1–4", "5–19", "20–49", "50–99", "100+"]):
        out.append('<rect x="%d" y="%d" width="22" height="16" rx="2" fill="%s"/>' % (x0 + 215 + i * 92, ly - 13, MAP[i] if i else "#EFECE8") + c.T(x0 + 243 + i * 92, ly, l, 13, INK_FAINT))
    out.append(c.T(x0, ly + 26, t["tapNote"], 13, INK_FAINT))
    return c.carte(t["tapTitre"], t["tapSous"].format(n=rows, d=c.dl_(fin)), "".join(out), h=int(ly + 150), pied=c.pied_semaine())


# ================================================================ chaque mois
def par_mois(c, f):
    out, prec = OrderedDict(), 0
    for ym, fin in c.mois:
        v = f(fin); out[ym] = v - prec; prec = v
    return out


def barres_mois(c, vals, couleur, fmt=None):
    fmt = fmt or c.nb
    x0, x1, y_top, y_bas = 100, 1120, 300, 960
    ymax = max(vals.values()) * 1.12 or 1; n = len(vals); pas = (x1 - x0) / n; bw = pas * 0.62; der = list(vals)[-1]
    s = '<line x1="%d" x2="%d" y1="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (x0, x1, y_bas, y_bas, LINE)
    for i, ym in enumerate(vals):
        v = vals[ym]; h = (y_bas - y_top) * v / ymax; x = x0 + pas * i + (pas - bw) / 2; y = y_bas - h
        hi = ym == der
        s += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="6" fill="%s"/>' % (x, y, bw, h, couleur if hi else hexmix(couleur, BG, 0.62))
        s += c.T(x + bw / 2, y - 12, fmt(v), 30 if hi else 24, couleur if hi else INK_DIM, "middle", 600, SERIF)
        s += c.T(x + bw / 2, y_bas + 40, c.M(ym), 22, INK if hi else INK_LABEL, "middle", 700 if hi else 500)
    return s


def titre_variation(c, cle, vals):
    ym = list(vals); a, b = vals[ym[-1]], vals[ym[-2]]
    v = round(100 * (a - b) / b) if b else 0
    sens = c.t["deMoins"] if v < 0 else c.t["dePlus"] if v > 0 else c.t["autant"]
    return c.t[cle].format(M=c.M(ym[-1]), n=c.nb(a), p=c.pc(abs(v)), sens=sens, m=c.m(ym[-2]))


def m_cas(c):
    vals = par_mois(c, lambda d: c.au(d)["confirmed"])
    ratt = sum(c.jours.get(D(k), (0, 0))[0] - v for k, v in RATTRAPAGES.items())
    notes = [c.t["moisRattCas"].format(n=c.nb(ratt)), c.t["moisMai"]]
    corps = barres_mois(c, vals, BLUE) + "".join(c.T(60, 1040 + i * 22, x, 15, INK_FAINT) for i, x in enumerate(notes))
    return c.carte(titre_variation(c, "moisCasTitre", vals), c.t["moisCasSous"], corps, pied=c.pied_mois())


def m_deces(c):
    vals = par_mois(c, lambda d: c.au(d)["deaths"])
    notes = [c.t["moisRattDec"], c.t["moisMai"]]
    corps = barres_mois(c, vals, RED) + "".join(c.T(60, 1040 + i * 22, x, 15, INK_FAINT) for i, x in enumerate(notes))
    return c.carte(titre_variation(c, "moisDecTitre", vals), c.t["moisDecSous"], corps, pied=c.pied_mois())


def m_zones(c):
    totaux, vals, prec = OrderedDict(), OrderedDict(), 0
    for ym, fin in c.mois:
        n = len(c.zones_touchees(fin)); totaux[ym] = n; vals[ym] = n - prec; prec = n
    corps = barres_mois(c, vals, GREEN, fmt=str)
    x0, x1 = 100, 1120; pas = (x1 - x0) / len(vals)
    for i, ym in enumerate(vals):
        corps += c.T(x0 + pas * i + pas / 2, 1032, c.t["moisZonTotal"].format(n=totaux[ym]), 17, INK_FAINT, "middle")
    corps += c.T(60, 1070, c.t["moisZonNote"], 15, INK_FAINT)
    ym = list(vals); n, k = vals[ym[-1]], vals[ym[-2]]
    titre = c.t["moisZonTitre"].format(M=c.M(ym[-1]), n=n, k=k, m=c.m(ym[-2]), s="s" if n > 1 and c.lang != "sw" else "")
    return c.carte(titre, c.t["moisZonSous"].format(t=totaux[ym[-1]], m2=c.m(ym[-1])), corps, pied=c.pied_mois())


def m_part(c):
    ordre = c.ordre_provinces()
    pdata = {p: par_mois(c, lambda d, p=p: c.prov_au(d).get(p, {}).get("confirmed", 0)) for p in ordre}
    x0, x1, y0, pas, hb = 200, 1060, 300, 120, 74; out = []
    out.append(c.legende(60, 262, [(p, PROV.get(p, INK_DIM)) for p in ordre], gap=14))
    der = c.mois[-1][0]
    for i, (ym, fin) in enumerate(c.mois):
        tot = sum(max(pdata[p][ym], 0) for p in ordre) or 1; y = y0 + i * pas; x = x0
        out.append(c.T(x0 - 20, y + hb / 2 + 9, c.M(ym), 24, INK if ym == der else INK_LABEL, "end", 700 if ym == der else 500))
        for p in ordre:
            v = max(pdata[p][ym], 0); w = (x1 - x0) * v / tot
            if w <= 0: continue
            out.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"%s/>' % (x, y, w, hb, PROV.get(p, INK_DIM), "" if ym == der else ' opacity=".55"'))
            if v / tot >= 0.06:
                out.append(c.T(x + w / 2, y + hb / 2 + 9, c.pc(100 * v / tot), 24 if ym == der else 20, "#fff", "middle", 600, SERIF))
            x += w
        out.append(c.T(x1 + 14, y + hb / 2 + 8, c.nb(tot), 17, INK_FAINT))
    ms = [ym for ym, _ in c.mois]
    part = lambda ym: 100 * max(pdata["Nord-Kivu"][ym], 0) / (sum(max(pdata[p][ym], 0) for p in ordre) or 1)
    titre = c.t["moisPartTitre"].format(a=c.pc(part(ms[-1])), M=c.m(ms[-1]), b=c.pc(part(ms[0])), m=c.m(ms[0]))
    out.append(c.T(60, 1080, c.t["moisMai"], 15, INK_FAINT))
    return c.carte(titre, c.t["moisPartSous"], "".join(out), pied=c.pied_mois())


# ================================================================ la riposte, jour par jour
# Les cinq graphiques quotidiens de la page Riposte (12 octobre 2026, demande
# du proprietaire), redessines en SVG avec les regles de app.js : axe
# calendaire, journee sans releve laissee en blanc, pont en pointilles au-dessus
# d'un trou (un repere, jamais une valeur), journee partielle du laboratoire
# hachuree, lits empruntes des CTE en point creux, cumul de vaccination revise
# porte a sa valeur corrigee. Seule la vue « par jour » de chaque cadre.
RIP = {
 "fr": dict(
  eyebrow="La riposte", titre="La riposte, jour par jour", sous="Les cinq graphiques quotidiens de la page Riposte, au SitRep n°{n}.",
  rythme="mis à jour à chaque nouveau bulletin",
  alTitre="Les alertes, jour par jour", alSous="Alertes reçues chaque jour par les équipes de surveillance, et celles validées comme cas suspects, du {a} au {b}.",
  alVal="Validées comme cas suspects", alAut="Autres alertes reçues",
  alPhrase="Le {d} : {n} alertes reçues, dont {v} validées comme cas suspects.",
  alNote="L'axe suit le calendrier : {lus} journées relevées sur {tot} ; une journée sans relevé reste en blanc.",
  laTitre="Le laboratoire, jour par jour", laSous="Échantillons analysés chaque jour, résultats positifs en couleur pleine, et positivité de la journée sur l'axe de droite, du {a} au {b}.",
  laPos="Résultats positifs", laNeg="Échantillons négatifs", laTaux="Positivité",
  laPhrase="Le {d} : {n} échantillons analysés, {p} positifs, soit {t}.",
  laNote="{lus} journées relevées sur {tot}. Hachures ({k} jours) : une province ne donne pas ses échantillons, seules les provinces complètes sont comptées.",
  laNote2="Pointillés : un repère au-dessus des jours sans relevé, jamais une valeur.",
  coTitre="Le suivi des contacts, jour par jour", coSous="Part des contacts vus dans les dernières 24 heures et, en barres claires sur l'axe de droite, nombre de contacts à suivre, du {a} au {b}.",
  coTaux="Part des contacts vus", coSuivre="Contacts à suivre",
  coPhrase="Le {d} : {p} des {n} contacts à suivre ont été vus.",
  coNote="L'INSP retient un seuil de 85 % depuis août ; l'OMS fixait une cible de 95 %. Pointillés : un repère au-dessus des jours sans relevé.",
  ctTitre="Patients pour 100 lits des CTE", ctSous="Patients hospitalisés, confirmés et suspects, rapportés aux lits que le bulletin déclare, province par province, du {a} au {b}.",
  ctNormees="Nord-Kivu, patients dans les lits des CTE",
  ctPhrase="Le {d} : {l}.", ctItem="{p} {v}",
  ctNote="Au-dessus de 100, il y a plus de malades que de lits. Provinces de moins de 20 lits écartées. Point creux : lits empruntés à un bulletin voisin.",
  ctNote2="Courbe claire et zone teintée : au Nord-Kivu, les patients des seuls lits des CTE ; l'écart, ceux soignés ailleurs.",
  vaTitre="{n} personnes vaccinées", vaSous="Cumul des personnes vaccinées avec l'ERVEBO, province par province, depuis le début de la campagne, le {a}.",
  vaPhrase="Au {d} : {l}.", vaItem="{p} {v}",
  vaNote="Le dernier cumul connu est reporté tant que le bulletin n'en publie pas de nouveau. Du 28 août au 2 septembre, aucun chiffre publié : la marche du 3 est un rattrapage.",
  vaRevision="Le {d}, le bulletin donnait {a} au {p}, corrigé ensuite à {b} : la courbe porte la valeur corrigée.",
  lire=dict(alertes="Le volume de signalements et ce que la surveillance en retient : les à-coups du jour, que la vue par semaine lisse.",
            labo="L'irrégularité des analyses d'un jour à l'autre, et la part de positifs : un positif n'est pas toujours un malade de plus.",
            contacts="Combien de personnes exposées sont vues chaque jour : quand la part baisse, des chaînes de transmission échappent au suivi.",
            cte="La pression sur les centres de traitement : au-dessus de 100, plus de malades que de lits.",
            vaccin="La campagne de vaccination, province par province : combien, et quand."),
 ),
 "en": dict(
  eyebrow="The response", titre="The response, day by day", sous="The five daily charts from the Response page, as of SitRep No. {n}.",
  rythme="updated with every new bulletin",
  alTitre="Alerts, day by day", alSous="Alerts received each day by surveillance teams, and those validated as suspected cases, {a} to {b}.",
  alVal="Validated as suspected cases", alAut="Other alerts received",
  alPhrase="On {d}: {n} alerts received, {v} of them validated as suspected cases.",
  alNote="The axis follows the calendar: {lus} days recorded out of {tot}; a day without a record stays blank.",
  laTitre="The laboratory, day by day", laSous="Samples tested each day, positive results in full colour, and the day's positivity on the right axis, {a} to {b}.",
  laPos="Positive results", laNeg="Negative samples", laTaux="Positivity",
  laPhrase="On {d}: {n} samples tested, {p} positive, or {t}.",
  laNote="{lus} days recorded out of {tot}. Hatching ({k} days): one province does not report its samples, only complete provinces are counted.",
  laNote2="Dotted lines: a guide over days without a record, never a value.",
  coTitre="Contact follow-up, day by day", coSous="Share of contacts seen in the previous 24 hours and, as light bars on the right axis, the number of contacts to follow, {a} to {b}.",
  coTaux="Share of contacts seen", coSuivre="Contacts to follow",
  coPhrase="On {d}: {p} of the {n} contacts to follow were seen.",
  coNote="The INSP has used an 85% threshold since August; WHO set a 95% target. Dotted lines: a guide over days without a record.",
  ctTitre="Patients per 100 treatment-centre beds", ctSous="Hospitalised patients, confirmed and suspected, relative to the beds the bulletin declares, province by province, {a} to {b}.",
  ctNormees="North Kivu, patients in treatment-centre beds",
  ctPhrase="On {d}: {l}.", ctItem="{p} {v}",
  ctNote="Above 100, there are more patients than beds. Provinces with fewer than 20 beds are left out. Hollow dot: beds taken from a neighbouring bulletin.",
  ctNote2="Pale line and shaded area: in North Kivu, patients in treatment-centre beds only; the gap, those cared for elsewhere.",
  vaTitre="{n} people vaccinated", vaSous="Cumulative number of people vaccinated with ERVEBO, province by province, since the campaign began on {a}.",
  vaPhrase="As of {d}: {l}.", vaItem="{p} {v}",
  vaNote="The last known total is carried forward until the bulletin publishes a new one. From 28 August to 2 September no figure was published: the step on the 3rd is a catch-up.",
  vaRevision="On {d}, the bulletin gave {a} in {p}, later corrected to {b}: the line carries the corrected value.",
  lire=dict(alertes="The volume of reports and what surveillance keeps from them: the day-to-day jolts that the weekly view smooths out.",
            labo="How uneven testing is from one day to the next, and the share of positives: a positive is not always one more patient.",
            contacts="How many exposed people are seen each day: when the share drops, chains of transmission escape follow-up.",
            cte="The pressure on treatment centres: above 100, more patients than beds.",
            vaccin="The vaccination campaign, province by province: how many, and when."),
 ),
 "sw": dict(
  eyebrow="Mapambano", titre="Mapambano, siku kwa siku", sous="Michoro mitano ya kila siku ya ukurasa wa Mapambano, kufikia SitRep Na. {n}.",
  rythme="husasishwa kwa kila ripoti mpya",
  alTitre="Tahadhari, siku kwa siku", alSous="Tahadhari zilizopokelewa kila siku na timu za ufuatiliaji, na zile zilizothibitishwa kama visa vinavyoshukiwa, {a} hadi {b}.",
  alVal="Zimethibitishwa kama visa vinavyoshukiwa", alAut="Tahadhari nyingine zilizopokelewa",
  alPhrase="Tarehe {d}: tahadhari {n} zilizopokelewa, {v} kati yake zimethibitishwa kama visa vinavyoshukiwa.",
  alNote="Mhimili unafuata kalenda: siku {lus} zimerekodiwa kati ya {tot}; siku bila rekodi inabaki tupu.",
  laTitre="Maabara, siku kwa siku", laSous="Sampuli zilizopimwa kila siku, matokeo chanya kwa rangi kamili, na kiwango cha chanya cha siku kwenye mhimili wa kulia, {a} hadi {b}.",
  laPos="Matokeo chanya", laNeg="Sampuli hasi", laTaux="Kiwango cha chanya",
  laPhrase="Tarehe {d}: sampuli {n} zilizopimwa, {p} chanya, yaani {t}.",
  laNote="Siku {lus} zimerekodiwa kati ya {tot}. Mistari ya mlalo (siku {k}): jimbo moja halitoi sampuli zake, majimbo kamili pekee yanahesabiwa.",
  laNote2="Vitone: kielelezo juu ya siku bila rekodi, kamwe si thamani.",
  coTitre="Ufuatiliaji wa walioguswa, siku kwa siku", coSous="Sehemu ya walioguswa walioonwa katika saa 24 zilizopita na, kama pau nyepesi kwenye mhimili wa kulia, idadi ya walioguswa wa kufuatiliwa, {a} hadi {b}.",
  coTaux="Sehemu ya walioguswa walioonwa", coSuivre="Walioguswa wa kufuatiliwa",
  coPhrase="Tarehe {d}: {p} ya walioguswa {n} wa kufuatiliwa walionwa.",
  coNote="INSP inatumia kiwango cha 85% tangu Agosti; WHO iliweka lengo la 95%. Vitone: kielelezo juu ya siku bila rekodi.",
  ctTitre="Wagonjwa kwa kila vitanda 100 vya vituo vya matibabu", ctSous="Wagonjwa waliolazwa, waliothibitishwa na wanaoshukiwa, ikilinganishwa na vitanda vinavyotangazwa na ripoti, jimbo kwa jimbo, {a} hadi {b}.",
  ctNormees="Kivu Kaskazini, wagonjwa katika vitanda vya vituo vya matibabu",
  ctPhrase="Tarehe {d}: {l}.", ctItem="{p} {v}",
  ctNote="Zaidi ya 100, kuna wagonjwa wengi kuliko vitanda. Majimbo yenye vitanda chini ya 20 yameachwa. Nukta tupu: vitanda vimechukuliwa kutoka ripoti jirani.",
  ctNote2="Mstari hafifu na eneo lenye rangi: Kivu Kaskazini, wagonjwa wa vitanda vya vituo pekee; tofauti, wale wanaotibiwa mahali pengine.",
  vaTitre="Watu {n} waliochanjwa", vaSous="Jumla ya watu waliochanjwa kwa ERVEBO, jimbo kwa jimbo, tangu kampeni ilipoanza tarehe {a}.",
  vaPhrase="Kufikia {d}: {l}.", vaItem="{p} {v}",
  vaNote="Jumla ya mwisho inayojulikana hubaki hadi ripoti itoe mpya. Kati ya 28 Agosti na 2 Septemba hakuna takwimu iliyochapishwa: hatua ya tarehe 3 ni kuchelewa kuchapisha.",
  vaRevision="Tarehe {d}, ripoti ilitoa {a} {p}, baadaye ikasahihishwa kuwa {b}: mstari unabeba thamani iliyosahihishwa.",
  lire=dict(alertes="Wingi wa taarifa na kile ufuatiliaji unachohifadhi: mabadiliko ya kila siku ambayo mwonekano wa wiki unalainisha.",
            labo="Jinsi vipimo vinavyobadilika siku hadi siku, na sehemu ya chanya: chanya si mara zote mgonjwa mwingine.",
            contacts="Watu wangapi walioathirika wanaonwa kila siku: sehemu inaposhuka, minyororo ya maambukizi inakwepa ufuatiliaji.",
            cte="Shinikizo kwa vituo vya matibabu: zaidi ya 100, wagonjwa wengi kuliko vitanda.",
            vaccin="Kampeni ya chanjo, jimbo kwa jimbo: wangapi, na lini."),
 ),
}

# Noms des provinces dans la langue de la page (memes que le site).
PROV_NOM = {"en": {"Nord-Kivu": "North Kivu", "Sud-Kivu": "South Kivu", "Haut-Uélé": "Haut-Uélé", "Bas-Uélé": "Bas-Uélé"},
            "sw": {"Nord-Kivu": "Kivu Kaskazini", "Sud-Kivu": "Kivu Kusini"}}


def _prov_canon(nom):
    plat = lambda s: re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower())
    for officiel in PROV:
        if plat(officiel) == plat(nom):
            return officiel
    return nom


def _calendrier(a, b):
    a, b = D(a) if isinstance(a, str) else a, D(b) if isinstance(b, str) else b
    return [a + dt.timedelta(i) for i in range((b - a).days + 1)]


def _graine(i):
    x = math.sin(i * 12.9898) * 43758.5453
    return x - math.floor(x)


def _pont(vals, max_trou=None, plafond=100):
    """Le pont de app.js (pontPointilles) : une droite entre les deux bords
    d'un trou, legerement tremblee pour ne pas se lire comme une mesure."""
    out = [None] * len(vals); i = 0
    while i < len(vals):
        if vals[i] is None:
            a, b = i - 1, i
            while b < len(vals) and vals[b] is None: b += 1
            if a >= 0 and b < len(vals) and (not max_trou or b - a - 1 <= max_trou):
                for j in range(a, b + 1):
                    droit = vals[a] + (vals[b] - vals[a]) * (j - a) / (b - a)
                    tremble = droit + (_graine(j) - 0.5) * 5
                    out[j] = droit if j in (a, b) else max(0, tremble if plafond is None else min(plafond, tremble))
            i = b
        else:
            i += 1
    return out


def _pas(mx, cible=5):
    brut = mx / cible; e = 10 ** math.floor(math.log10(brut or 1))
    for k in (1, 2, 2.5, 5, 10):
        if brut <= k * e: return k * e
    return 10 * e


class Repere:
    """Un cadre de graphique calendaire : x par jour, y gauche (et droite)."""
    X0, X1, Y0, Y1 = 110, 1110, 300, 830

    def __init__(self, c, jours, ymax, ydroite=None):
        self.c, self.jours = c, jours; self.n = len(jours); self.ymax = ymax or 1; self.yd = ydroite
        self.bw = (self.X1 - self.X0) / self.n

    def x(self, i): return self.X0 + (i + 0.5) * self.bw
    def y(self, v, droite=False):
        m = self.yd if droite else self.ymax
        return self.Y1 - (self.Y1 - self.Y0) * v / m

    def grille(self, fmt, droite_fmt=None, pas=None, pas_d=None, sans_trait=False):
        c = self.c; out = []; pas = pas or _pas(self.ymax); v = 0
        while v <= self.ymax + 1e-9:
            y = self.y(v)
            out.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="%s"/>' % (self.X0, self.X1, y, y, LINE_SOFT) + c.T(self.X0 - 12, y + 5, fmt(v), 13, INK_FAINT, "end"))
            v += pas
        if self.yd and droite_fmt:
            pas_d = pas_d or _pas(self.yd); v = 0
            while v <= self.yd + 1e-9:
                out.append(c.T(self.X1 + 12, self.y(v, True) + 5, droite_fmt(v), 13, INK_FAINT)); v += pas_d
        # dates : le 1er et le 15 de chaque mois
        for i, d in enumerate(self.jours):
            if d.day in (1, 15):
                x = self.x(i)
                out.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" stroke="%s"/>' % (x, x, self.Y1, self.Y1 + 6, INK_FAINT))
                out.append(c.T(x, self.Y1 + 26, c.dc(d), 13, INK_DIM if d.day == 1 else INK_FAINT, "middle", 600 if d.day == 1 else 400))
        out.append('<line x1="%d" x2="%d" y1="%d" y2="%d" stroke="%s" stroke-width="1.5"/>' % (self.X0, self.X1, self.Y1, self.Y1, LINE))
        return "".join(out)

    def barres(self, piles, droite=False):
        """piles : [(valeurs, couleur), ...] empilees du bas vers le haut ;
        une journee relevee a zero garde un trait (minBarLength de app.js)."""
        out = []; w = max(self.bw * 0.86, 0.8)
        for i in range(self.n):
            base = 0
            for vals, col in piles:
                v = vals[i]
                if v is None: continue
                y0, y1 = self.y(base, droite), self.y(base + v, droite)
                h = max(y0 - y1, 1.5)
                fill = col[i] if isinstance(col, list) else col
                out.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>' % (self.x(i) - w / 2, y0 - h, w, h, fill))
                base += v
        return "".join(out)

    def courbe(self, vals, col, larg=2.4, droite=False, pointille=False, points=None):
        segs, cur = [], []
        for i, v in enumerate(vals):
            if v is None:
                if cur: segs.append(cur); cur = []
            else:
                cur.append("%.1f,%.1f" % (self.x(i), self.y(v, droite)))
        if cur: segs.append(cur)
        dash = ' stroke-dasharray="5 5"' if pointille else ""
        out = "".join('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"%s/>' % (" ".join(s), col, larg, dash)
                      for s in segs if len(s) > 1)
        # un point isole (sans voisin) reste visible
        for i, v in enumerate(vals):
            if v is None: continue
            seul = (i == 0 or vals[i - 1] is None) and (i == len(vals) - 1 or vals[i + 1] is None)
            creux = points and points[i]
            if creux:
                out += '<circle cx="%.1f" cy="%.1f" r="4.2" fill="%s" stroke="%s" stroke-width="2"/>' % (self.x(i), self.y(v, droite), BG, col)
            elif seul and not pointille:
                out += '<circle cx="%.1f" cy="%.1f" r="2.8" fill="%s"/>' % (self.x(i), self.y(v, droite), col)
        return out


def _tint(col, t):
    return hexmix(col, "#FFFFFF", 1 - t)


def _phrase(c, txt, y=965):
    return c.T(60, y, txt, 24, INK, fam=SERIF)


def _notes(c, notes, y=1002):
    import textwrap
    lignes = [l for n in notes for l in textwrap.wrap(n, 140)]
    return "".join(c.T(60, y + i * 22, l, 15, INK_DIM) for i, l in enumerate(lignes[:4]))


def _jour(c, d):
    return c.dc(d)


def r_alertes(c):
    r = c.r; pts = _j("data/alertes.json")["parDate"]
    pts = [p for p in pts]
    jours = _calendrier(pts[0]["date"], pts[-1]["date"]); par = {D(p["date"]): (p.get("total") or {}) for p in pts}
    rec = [par.get(d, {}).get("recues") for d in jours]; val = [par.get(d, {}).get("validees") for d in jours]
    aut = [None if a is None or b is None else a - b for a, b in zip(rec, val)]
    val = [None if a is None else b for a, b in zip(aut, val)]
    lus = sum(1 for v in aut if v is not None)
    mx = max(a + b for a, b in zip(aut, val) if a is not None)
    R = Repere(c, jours, mx * 1.06)
    out = [c.legende(R.X0, 262, [(r["alVal"], BLUE), (r["alAut"], _tint(BLUE, .3))]), R.grille(c.nb),
           R.barres([(val, BLUE), (aut, _tint(BLUE, .3))])]
    k = max(i for i, v in enumerate(aut) if v is not None)
    out.append(_phrase(c, r["alPhrase"].format(d=_jour(c, jours[k]), n=c.nb(rec[k]), v=c.nb(val[k]))))
    out.append(_notes(c, [r["alNote"].format(lus=lus, tot=len(jours))]))
    return c.carte(r["alTitre"], r["alSous"].format(a=c.dc(jours[0]), b=c.dl_(jours[-1])), "".join(out), h=1160)


def r_labo(c):
    r = c.r; pts = []
    for p in _j("data/laboratoire.json")["parDate"]:
        n, t = p.get("national") or {}, p.get("total") or {}
        src = n if (n.get("echantillons") and n.get("positifs") is not None) else t
        separe = src.get("nouveauxCas") is not None
        pos = src["nouveauxCas"] if separe else src.get("positifs")
        if src.get("echantillons") is None or pos is None:
            provs = p.get("provinces") or {}
            pleines = [x for x in provs if provs[x].get("echantillons") is not None and provs[x].get("positifs") is not None]
            manq = [x for x in provs if x not in pleines]
            if pleines and manq:
                pts.append(dict(date=p["date"], ech=sum(provs[x]["echantillons"] for x in pleines),
                                pos=sum(provs[x]["nouveauxCas"] if provs[x].get("nouveauxCas") is not None else provs[x]["positifs"] for x in pleines),
                                partiel=manq)); continue
        pts.append(dict(date=p["date"], ech=src.get("echantillons"), pos=pos, partiel=None))
    lis = [p for p in pts if p["date"] >= "2026-06-02" and p["ech"] is not None and p["pos"] is not None]
    jours = _calendrier(lis[0]["date"], lis[-1]["date"]); par = {D(p["date"]): p for p in lis}
    pos = [par[d]["pos"] if d in par else None for d in jours]
    neg = [par[d]["ech"] - par[d]["pos"] if d in par else None for d in jours]
    taux = [round(par[d]["pos"] / par[d]["ech"] * 1000) / 10 if d in par and par[d]["ech"] else None for d in jours]
    partiel = [bool(d in par and par[d]["partiel"]) for d in jours]
    mx = max(a + b for a, b in zip(pos, neg) if a is not None)
    R = Repere(c, jours, mx * 1.06, 100)
    defs = ('<defs><pattern id="vx-hp" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="%s"/><line x1="0" y1="0" x2="0" y2="6" stroke="%s" stroke-width="1.4"/></pattern>'
            '<pattern id="vx-hn" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="%s"/><line x1="0" y1="0" x2="0" y2="6" stroke="%s" stroke-width="1.4"/></pattern></defs>'
            % (_tint(BLUE, .62), BLUE, _tint(_tint(BLUE, .3), .62), _tint(BLUE, .3)))
    cpos = ["url(#vx-hp)" if p else BLUE for p in partiel]; cneg = ["url(#vx-hn)" if p else _tint(BLUE, .3) for p in partiel]
    out = [defs, c.legende(R.X0, 262, [(r["laPos"], BLUE), (r["laNeg"], _tint(BLUE, .3)), (r["laTaux"], RED)]),
           R.grille(c.nb, lambda v: c.pc(v), pas_d=20), R.barres([(pos, cpos), (neg, cneg)]),
           R.courbe(_pont(taux), _tint(RED, .45), 1.6, True, True), R.courbe(taux, RED, 2.4, True, points=partiel)]
    # la phrase porte le dernier jour COMPLET : une journee hachuree ne compte
    # que les provinces completes, pas le pays
    k = max(i for i in range(len(jours)) if pos[i] is not None and not partiel[i])
    out.append(_phrase(c, r["laPhrase"].format(d=_jour(c, jours[k]), n=c.nb(pos[k] + neg[k]), p=c.nb(pos[k]), t=c.pc(taux[k], 1))))
    out.append(_notes(c, [r["laNote"].format(lus=len(par), tot=len(jours), k=sum(partiel)), r["laNote2"]]))
    return c.carte(r["laTitre"], r["laSous"].format(a=c.dc(jours[0]), b=c.dl_(jours[-1])), "".join(out), h=1160)


def r_contacts(c):
    r = c.r; cf = sorted(_j("data/contacts-followup.json"), key=lambda x: x["date"])
    jours = _calendrier(cf[0]["date"], cf[-1]["date"]); par = {D(x["date"]): x for x in cf}
    taux = [par[d].get("contactsFollowUpRate") if d in par else None for d in jours]
    suiv = [((par[d].get("contacts") or {}).get("aSuivre")) if d in par else None for d in jours]
    mxd = max(v for v in suiv if v is not None) * 1.06
    R = Repere(c, jours, 100, mxd)
    out = [c.legende(R.X0, 262, [(r["coTaux"], AMBER), (r["coSuivre"], _tint(AMBER, .22))]),
           R.grille(lambda v: c.pc(v), c.nb, pas=20), R.barres([(suiv, _tint(AMBER, .22))], droite=True),
           R.courbe(_pont(taux), _tint(AMBER, .45), 1.6, pointille=True), R.courbe(taux, AMBER, 2.4)]
    k = max(i for i in range(len(jours)) if taux[i] is not None and suiv[i] is not None)
    out.append(_phrase(c, r["coPhrase"].format(d=_jour(c, jours[k]), p=c.pc(taux[k]), n=c.nb(suiv[k]))))
    out.append(_notes(c, [r["coNote"]]))
    return c.carte(r["coTitre"], r["coSous"].format(a=c.dc(jours[0]), b=c.dl_(jours[-1])), "".join(out), h=1160)


def r_cte(c):
    r = c.r; pts = [p for p in _j("data/cte.json")["parDate"] if "occupation" in (p.get("total") or {})]
    jours = _calendrier(pts[0]["date"], pts[-1]["date"])
    par = {D(p["date"]): {_prov_canon(k): v for k, v in (p.get("provinces") or {}).items()} for p in pts}
    lisible = lambda v: bool(v) and v.get("occupation") is not None and (v.get("lits") or v.get("hospitalises") or 0) >= 20
    emprunte = lambda v: bool(v and (v.get("litsReportes") or v.get("litsEncadres")))
    noms = [n for n in PROV if any(lisible(par[d].get(n)) for d in par)]
    series = {n: [par[d][n]["occupation"] if d in par and lisible(par[d].get(n)) else None for d in jours] for n in noms}
    creux = {n: [emprunte(par.get(d, {}).get(n)) and series[n][i] is not None for i, d in enumerate(jours)] for n in noms}
    NK = "Nord-Kivu"; normees = None
    if NK in noms:
        def vn(d):
            v = par.get(d, {}).get(NK)
            return v["hospitalisesNormes"] / v["lits"] * 100 if v and lisible(v) and v.get("hospitalisesNormes") is not None and v.get("lits") else None
        normees = [vn(d) for d in jours]
        if all(v is None for v in normees): normees = None
    mx = max(v for s in series.values() for v in s if v is not None)
    R = Repere(c, jours, math.ceil(max(100, mx) / 20) * 20)
    nom = lambda n: PROV_NOM.get(c.lang, {}).get(n, n)
    leg = [(nom(n), PROV[n]) for n in noms] + ([(r["ctNormees"], _tint(PROV[NK], .5))] if normees else [])
    out = [c.legende(R.X0, 262, leg, 18), R.grille(lambda v: c.nb(v), pas=20)]
    if normees:
        base = series[NK]; poly = []
        seg = []
        for i in range(len(jours)):
            if normees[i] is not None and base[i] is not None: seg.append(i)
            elif seg: poly.append(seg); seg = []
        if seg: poly.append(seg)
        for s in poly:
            haut = " ".join("%.1f,%.1f" % (R.x(i), R.y(base[i])) for i in s)
            bas = " ".join("%.1f,%.1f" % (R.x(i), R.y(normees[i])) for i in reversed(s))
            out.append('<polygon points="%s %s" fill="%s" opacity=".16"/>' % (haut, bas, PROV[NK]))
        out.append(R.courbe(normees, _tint(PROV[NK], .5), 1.8))
    for n in noms:
        out.append(R.courbe(_pont(series[n], 5, None), _tint(PROV[n], .45), 1.4, pointille=True))
        out.append(R.courbe(series[n], PROV[n], 2.2, points=creux[n]))
    der = jours[-1]
    items = [r["ctItem"].format(p=nom(n), v=c.nb(series[n][-1])) for n in noms if series[n][-1] is not None]
    out.append(_phrase(c, r["ctPhrase"].format(d=_jour(c, der), l=", ".join(items))))
    out.append(_notes(c, [r["ctNote"]] + ([r["ctNote2"]] if normees else [])))
    return c.carte(r["ctTitre"], r["ctSous"].format(a=c.dc(jours[0]), b=c.dl_(jours[-1])), "".join(out), h=1160)


def r_vaccin(c):
    r = c.r
    cum = [dict(date=p["date"], prov={_prov_canon(k): v for k, v in ((p.get("vaccination") or {}).get("cumulParProvince") or {}).items()})
           for p in _j("data/piliers.json")["parDate"]]
    cum = [x for x in cum if x["prov"]]
    # un cumul ne recule pas : le point revise porte la valeur corrigee
    revisions, retenu = [], {}
    for x in reversed(cum):
        for n, v in list(x["prov"].items()):
            if n in retenu and v > retenu[n]:
                revisions.append((x["date"], n, v, retenu[n])); x["prov"][n] = retenu[n]
            else:
                retenu[n] = v
    jours = _calendrier(cum[0]["date"], cum[-1]["date"]); par = {D(x["date"]): x["prov"] for x in cum}
    noms = [n for n in PROV if any(n in x["prov"] for x in cum)]
    report, series = {}, {n: [] for n in noms}
    for d in jours:
        report.update(par.get(d, {}))
        for n in noms: series[n].append(report.get(n))
    mx = max(v for s in series.values() for v in s if v is not None)
    R = Repere(c, jours, mx * 1.08)
    nom = lambda n: PROV_NOM.get(c.lang, {}).get(n, n)
    out = [c.legende(R.X0, 262, [(nom(n), PROV[n]) for n in noms]), R.grille(c.nb)]
    for n in noms:
        out.append(R.courbe(series[n], PROV[n], 2.8))
        v = series[n][-1]
        if v is not None:
            out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (R.x(len(jours) - 1), R.y(v), PROV[n]))
    tot = sum(series[n][-1] or 0 for n in noms)
    items = [r["vaItem"].format(v=c.nb(series[n][-1]), p=nom(n)) for n in sorted(noms, key=lambda n: -(series[n][-1] or 0)) if series[n][-1]]
    out.append(_phrase(c, r["vaPhrase"].format(d=_jour(c, jours[-1]), l=", ".join(items))))
    notes = [r["vaNote"]]
    if revisions:
        d, n, a, b = revisions[0]
        notes.append(r["vaRevision"].format(d=c.dc(D(d)), a=c.nb(a), p=nom(n), b=c.nb(b)))
    out.append(_notes(c, notes))
    return c.carte(r["vaTitre"].format(n=c.nb(tot)), r["vaSous"].format(a=c.dl_(jours[0])), "".join(out), h=1160)


# ================================================================ nouveaux cas par jour, trois premieres provinces
# Le graphique quotidien des pages province (mode provinceEpidemic de app.js),
# pour les trois provinces qui comptent le plus de cas au dernier bulletin
# (12 octobre 2026, demande du proprietaire). Memes garde-fous : calendrier
# jour par jour, jour sans bulletin en blanc, pas de barre au retour d'un
# trou de plus de 3 jours (ventilation non publiee du 20 au 30 mai), les
# 22 et 30 juillet en entier dans la teinte claire du rattrapage, et l'axe
# plafonne au pic ordinaire quand un rattrapage l'ecraserait (barre coupee,
# total ecrit au-dessus). Sans la courbe des cas cumules (choix du
# proprietaire, 12 octobre 2026) : les barres seules.
PJ = {
 "fr": dict(titre="{p} : les nouveaux cas, jour par jour",
            sous="Nouveaux cas confirmés déclarés chaque jour dans la province, du {a} au {b}.",
            jour="Nouveaux cas quotidiens", ratt="Rattrapage",
            phrase="Le {d} : {n} nouveaux cas ; {s} en sept jours, {c} depuis le début.",
            blancs="{n} jours sans bulletin pour la province restent en blanc ; leurs cas sont comptés dans le relevé suivant.",
            trou="Aucune barre du {p} : les bulletins ne répartissent pas les cas entre les provinces.",
            rattNote="Les 22 et 30 juillet, rattrapages de données, en teinte claire : leur part n'est publiée qu'au niveau national.",
            coupe="Barre coupée : l'axe s'arrête au plus fort jour ordinaire, le total est écrit au-dessus.",
            lire="La courbe quotidienne de la province, comme sur sa page : les à-coups du jour que la vue par semaine lisse."),
 "en": dict(titre="{p}: new cases, day by day",
            sous="New confirmed cases reported each day in the province, {a} to {b}.",
            jour="New daily cases", ratt="Catch-up",
            phrase="On {d}: {n} new cases; {s} in seven days, {c} since the start.",
            blancs="{n} days without a bulletin for the province are left blank; their cases are counted in the next report.",
            trou="No bars from {p}: the bulletins do not break cases down by province.",
            rattNote="22 and 30 July, data catch-ups, in the lighter tone: their share is published only at national level.",
            coupe="Cut bar: the axis stops at the highest ordinary day, the total is written above.",
            lire="The province's daily chart, as on its page: the day-to-day jolts that the weekly view smooths out."),
 "sw": dict(titre="{p}: visa vipya, siku kwa siku",
            sous="Visa vipya vilivyothibitishwa vinavyoripotiwa kila siku katika jimbo, {a} hadi {b}.",
            jour="Visa vipya vya kila siku", ratt="Marekebisho",
            phrase="Tarehe {d}: visa vipya {n}; {s} katika siku saba, {c} tangu mwanzo.",
            blancs="Siku {n} bila ripoti kwa jimbo zimeachwa wazi; visa vyake vimehesabiwa katika ripoti inayofuata.",
            trou="Hakuna safu kutoka {p}: ripoti hazigawanyi visa kati ya majimbo.",
            rattNote="Tarehe 22 na 30 Julai, marekebisho ya takwimu, kwa rangi hafifu: sehemu yake imechapishwa kwa kiwango cha kitaifa pekee.",
            coupe="Safu iliyokatwa: mhimili unaishia kwenye siku ya kawaida ya juu zaidi, jumla imeandikwa juu.",
            lire="Mchoro wa kila siku wa jimbo, kama kwenye ukurasa wake: mabadiliko ya kila siku ambayo mwonekano wa wiki unalainisha."),
}
ECART_MAX_JOURS, MARGE_PLAFOND, DECLENCHE_RUPTURE = 3, 1.12, 1.4


def r_province(c, rang):
    r = PJ[c.lang]; nom = c.ordre_provinces()[rang]
    pnom = PROV_NOM.get(c.lang, {}).get(nom, nom); teinte = PROV.get(nom, BLUE)
    pts = []
    for h in sorted(c.ph, key=lambda h: h["date"]):
        for p in h.get("provinces") or []:
            if _prov_canon(p["name"]) == nom and p.get("confirmed") is not None:
                pts.append((D(h["date"]), p["confirmed"])); break
    par, trous = {}, []
    for (d0, c0), (d1, c1) in zip(pts, pts[1:]):
        if (d1 - d0).days > ECART_MAX_JOURS:
            trous.append("%s au %s" % (c.dc(d0 + dt.timedelta(1)), c.dc(d1)) if c.lang == "fr" else
                         "%s to %s" % (c.dc(d0 + dt.timedelta(1)), c.dc(d1)) if c.lang == "en" else
                         "%s hadi %s" % (c.dc(d0 + dt.timedelta(1)), c.dc(d1)))
            continue
        delta = max(0, c1 - c0); ratt = d1.isoformat() in RATTRAPAGES
        par[d1] = (None if ratt else delta, delta if ratt else None)
    jours = _calendrier(pts[0][0], pts[-1][0]); releves = dict(pts)
    rap = [par[d][0] if d in par else None for d in jours]
    rat = [par[d][1] if d in par else None for d in jours]
    ordinaire = max((v for v, k in zip(rap, rat) if v is not None and not k), default=0)
    plus_haute = max((v or 0) + (k or 0) for v, k in zip(rap, rat))
    plafond = None
    if ordinaire and plus_haute >= ordinaire * DECLENCHE_RUPTURE:
        brut = ordinaire * MARGE_PLAFOND; pas = 10 ** (math.floor(math.log10(brut)) - 1) * 2
        plafond = math.ceil(brut / pas) * pas
    ymax = plafond or plus_haute * 1.06
    R = Repere(c, jours, ymax)
    cap = lambda vals: [None if v is None else min(v, ymax) for v in vals]
    out = [c.legende(R.X0, 262, [(r["jour"], teinte), (r["ratt"], _tint(teinte, .35))]),
           R.grille(c.nb), R.barres([(cap(rap), teinte), (cap(rat), _tint(teinte, .35))])]
    coupees = [(i, (a or 0) + (b or 0)) for i, (a, b) in enumerate(zip(rap, rat)) if (a or 0) + (b or 0) > ymax]
    for i, tot in coupees:
        x, y = R.x(i), R.Y0
        out.append('<path d="M%.1f %.1f l%.1f -5 M%.1f %.1f l%.1f -5" stroke="%s" stroke-width="2"/>' % (x - 6, y + 12, 12, x - 6, y + 18, 12, BG))
        out.append(c.T(x, y - 8, c.nb(tot), 13, INK, "middle", 700))
    k = max(i for i, v in enumerate(rap) if v is not None)
    d = jours[k]; avant = [v for dd, v in pts if dd <= d - dt.timedelta(7)]
    sept = releves[d] - avant[-1] if avant else releves[d]
    out.append(_phrase(c, r["phrase"].format(d=c.dc(d), n=c.nb(rap[k]), s=c.nb(sept), c=c.nb(releves[d]))))
    notes = []
    blancs = sum(1 for d in jours if d not in releves)
    if blancs: notes.append(r["blancs"].format(n=blancs))
    if trous: notes.append(r["trou"].format(p=" ; ".join(trous)))
    if any(v for v in rat if v): notes.append(r["rattNote"])
    if coupees: notes.append(r["coupe"])
    out.append(_notes(c, notes))
    return c.carte(r["titre"].format(p=pnom), r["sous"].format(a=c.dc(jours[0]), b=c.dl_(jours[-1])), "".join(out), h=1160)


# ================================================================ la page
LISTE = [
    ("b", [("calendrier", "calTitre", calendrier, "calendrier"), ("code-barre", "rayTitre", rayures, "rayures"), ("provinces", None, carte_provinces, "provinces"),
           ("nouveaux-cas-province-1", None, lambda c: r_province(c, 0), "provjour"), ("nouveaux-cas-province-2", None, lambda c: r_province(c, 1), "provjour"),
           ("nouveaux-cas-province-3", None, lambda c: r_province(c, 2), "provjour")]),
    ("r", [("alertes-jour", None, r_alertes, "alertes"), ("laboratoire-jour", None, r_labo, "labo"), ("contacts-jour", None, r_contacts, "contacts"),
           ("cte-jour", None, r_cte, "cte"), ("vaccination-jour", None, r_vaccin, "vaccin")]),
    ("s", [("part-provinces", "partTitre", h_part, "part"), ("cas-semaine", "casTitre", h_cas, "cas"), ("lieu-deces", "lieuTitre", h_lieu, "lieu"),
           ("zones-actives", "zonTitre", h_zones, "zones"), ("zone-apres-zone", "tapTitre", h_tapis, "tapis")]),
    ("m", [("zones-par-mois", None, m_zones, "mzones"), ("cas-par-mois", None, m_cas, "mcas"), ("deces-par-mois", None, m_deces, "mdeces"), ("part-par-mois", None, m_part, "mpart")]),
]


def page_html(lang, mois_courts):
    """Le corps de la page Visuels pour une langue : trois etages, chacun avec
    ses visuels, leur titre, leur texte de lecture et le bouton PNG."""
    c = Contexte(lang, mois_courts); p = c.p
    a, b = c.semaines[-1]; ym = c.mois[-1][0]
    tetes = {
        "b": (p["b_eyebrow"], p["b_titre"], p["b_sous"].format(n=c.SITREP, d=c.dl_(c.FIN)), p["b_rythme"]),
        "r": (c.r["eyebrow"], c.r["titre"], c.r["sous"].format(n=c.SITREP), c.r["rythme"]),
        "s": (p["s_eyebrow"], p["s_titre"].format(a=c.dc(a), b=c.dl_(b)), p["s_sous"], p["s_rythme"]),
        "m": (p["m_eyebrow"], p["m_titre"].format(M="%s %d" % (c.M(ym), ym[0])), p["m_sous"], p["m_rythme"]),
    }
    out = ['<h1 class="vx-h1">%s <em>%s</em></h1><p class="vx-lede">%s</p>' % (esc(p["h1a"]), esc(p["h1b"]), esc(p["lede"]))]
    for etage, items in LISTE:
        eb, ti, so, ry = tetes[etage]
        figs = []
        for ident, _, fn, lire in items:
            svg = fn(c)
            m = re.findall(r'<text x="60\.0" y="(?:110|156)\.0"[^>]*font-size="(?:42|38)"[^>]*>([^<]*)</text>', svg)
            titre = html.unescape(" ".join(m)) if m else ident
            figs.append('<figure class="vx-fig" id="%s"><div class="vx-img" data-vx-nom="%s" role="button" tabindex="0" aria-label="%s">%s</div>'
                        '<figcaption><div><h3>%s</h3><p>%s</p></div><button type="button" class="vx-png" title="%s">PNG ↓</button></figcaption></figure>'
                        % (ident, ident, esc(p["agrandir"] + " : " + titre), svg, esc(titre), esc(p["lire"].get(lire) or c.r["lire"].get(lire) or PJ[lang]["lire"]), esc(p["png"])))
        out.append('<section class="vx-etage" id="vx-%s"><div class="vx-tete"><div><p class="vx-eyebrow">%s</p><h2 class="vx-h2">%s</h2><p class="vx-sous">%s</p></div>'
                   '<span class="vx-rythme">%s</span></div><div class="vx-grille">%s</div></section>' % (etage, esc(eb), esc(ti), esc(so), esc(ry), "".join(figs)))
    out.append('<div class="vx-lb" id="vxLb" hidden><button type="button" class="vx-fermer" aria-label="%s">×</button><div class="vx-lb-in"></div></div>' % esc(p["fermer"]))
    return "".join(out)


# ================================================================ la vitrine de l'accueil
# Bande « Visuels » de l'accueil, a la place de la Chronologie (13 octobre
# 2026, maquette tmp/proto-accueil-vitrine-1013, option 3 « le ruban pleine
# largeur ») : six visuels SANS AUCUN TEXTE — titres, axes, legendes, notes
# retires, cadres sur le dessin seul — pour attirer l'oeil, pas pour informer.
# Chaque image mene a son visuel sur la page Visuels ; app.js les fait
# defiler en boucle sans fin (initVitrineVisuels).
# (ancre sur la page Visuels, fonction, cadre x y l h dans le repere 1200)
def _nk(c):
    """Rang du Nord-Kivu parmi les provinces les plus touchees : son visuel
    quotidien est nouveaux-cas-province-<rang+1> sur la page Visuels."""
    return c.ordre_provinces().index("Nord-Kivu")


# Ordre du proprietaire (13 octobre 2026, deuxieme version) : code-barre,
# calendrier, laboratoire, lieu des deces, suivi des contacts, nouveaux cas du
# Nord-Kivu, nouveaux cas semaine apres semaine, zones actives et calmes, et
# zone apres zone en dernier. La part de chaque province a ete retiree.
# Ancre : une chaine, ou une fonction du contexte (le rang du Nord-Kivu peut changer).
VITRINE = [("code-barre", rayures, (60, 250, 1080, 770)), ("calendrier", calendrier, (50, 300, 1100, 510)),
           ("laboratoire-jour", r_labo, (100, 315, 1030, 525)), ("lieu-deces", h_lieu, (100, 290, 1050, 540)),
           ("contacts-jour", r_contacts, (100, 290, 1025, 545)),
           (lambda c: "nouveaux-cas-province-%d" % (_nk(c) + 1), lambda c: r_province(c, _nk(c)), (100, 315, 1025, 520)),
           ("cas-semaine", h_cas, (100, 285, 1045, 565)), ("zones-actives", h_zones, (100, 290, 1045, 560)),
           ("zone-apres-zone", h_tapis, (180, 245, 970, 725))]


def nombre_visuels():
    return sum(len(items) for _, items in LISTE)


def vitrine_html(lang, mois_courts, href):
    """Les six vignettes de la bande d'accueil, liens vers href#ancre. Le nom
    du visuel (son titre, dans la langue de la page) ne vit que dans
    l'aria-label : a l'ecran, rien que le dessin."""
    c = Contexte(lang, mois_courts); out = []
    for n, (ident, fn, (x, y, w, h)) in enumerate(VITRINE):
        if callable(ident):
            ident = ident(c)
        svg = fn(c)
        m = re.findall(r'<text x="60\.0" y="(?:110|156)\.0"[^>]*font-size="(?:42|38)"[^>]*>([^<]*)</text>', svg)
        titre = html.unescape(" ".join(m)) if m else ident
        svg = re.sub(r"<text\b.*?</text>", "", svg, flags=re.S)
        svg = re.sub(r'<path d="M60,\d+ h11 v11 z"[^>]*/>', "", svg)         # reperes des notes du calendrier
        svg = re.sub(r'<circle cx="66" cy="52" r="6"[^>]*/>', "", svg)        # point rouge du titre
        svg = re.sub(r'(<svg[^>]*>)<rect width="\d+" height="\d+" fill="[^"]*"/>', r"\1", svg, count=1)  # fond : celui de la bande
        svg = re.sub(r'role="img" aria-label="[^"]*"', 'aria-hidden="true" focusable="false"', svg, count=1)
        svg = re.sub(r'viewBox="[^"]*"', 'viewBox="%d %d %d %d" preserveAspectRatio="xMidYMid meet"' % (x, y, w, h), svg, count=1)
        # id internes (motifs de hachures) uniques : la page porte d'autres SVG
        for i in set(re.findall(r'id="([^"]+)"', svg)):
            svg = svg.replace('id="%s"' % i, 'id="%s-vt%d"' % (i, n)).replace("url(#%s)" % i, "url(#%s-vt%d)" % (i, n))
        out.append('<a class="vtr-t" href="%s#%s" style="--r:%.4f" aria-label="%s">%s</a>' % (esc(href), ident, w / h, esc(titre), svg))
    return "".join(out)
