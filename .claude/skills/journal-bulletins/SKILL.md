---
name: journal-bulletins
description: Journal d'integration bulletin par bulletin d'ebola-tracker, du SitRep 109 au 126 : tournures de phrase apprises, motifs regex ajoutes aux extracteurs, ecarts de la source constates et laisses visibles, verifications faites. A charger AVANT de toucher a un extracteur (update_data, extraire_*, extract_*), avant de reprendre un ancien bulletin, ou quand une tournure du SitRep ne se lit pas.
---

# Journal des bulletins — SitRep 109 a 126

Ce journal etait en tete de CLAUDE.md, ou il pesait environ 10 000 tokens
relus a chaque echange. Il est ici parce qu'il ne sert qu'a un moment precis :
quand une extraction achoppe, ou quand il faut savoir ce qu'un bulletin donne
et sous quelle forme. Les entrees du dernier bulletin integre restent, elles,
en tete du guide.

Les regles durables tirees de ces integrations n'ont pas bouge : elles vivent
dans CLAUDE.md, aux sections « Comment l'extraction fonctionne » et « Pieges
connus ». Ce qui suit est la trace datee, bulletin par bulletin.

Le SitRep 126, rapportage
du 17 septembre 2026 (publié le 18) — 7 541 cas confirmés, 3 639 décès,
létalité 48,3 %, 1 823 guéris, 930 patients en isolement/CTE, suivi des
contacts **87,2 %**, 62 zones touchées sur 167 dans 7 provinces (aucune
nouvelle), 66 nouveaux cas (Ituri 37, Nord-Kivu 20, Tshopo 5, Haut-Uélé 4) et
34 décès du jour (16 communautaires, 18 intra-CTE). Intégré **en local le
19 septembre 2026** ; sept provinces et 62 zones relues contre les pages 2 et 3
du PDF, zéro écart (la somme des zones de l'Ituri accuse les 477 décès « pas
encore attribués à une zone », écart attendu et visible par construction) ;
`check_coherence` sans écart bloquant, les deux écarts anciens de la source
inchangés ; résumé des Défis rédigé (131 mots). Rien de neuf à apprendre au
lecteur, et une tournure à connaître :
- **Le Nord-Kivu écrit « 20 échantillons résultats positifs (13 vivants et
  7 décès) sur 171 échantillons analysés »** — « échantillons » à la place de
  « nouveaux résultats », ce qu'aucun motif ne lit. La province est quand même
  sortie à 20 positifs par la déduction vivants + décès (`positifsDeduits`), et
  le garde-fou du jour repasse exactement : 37 + 20 + 4 + 5 + 0 = 66 positifs
  pour 66 nouveaux cas. Un motif dédié serait plus sûr que la déduction ; non
  fait, la déduction suffit tant que le bulletin publie la ventilation.
- Le tableau des zones porte, comme d'habitude, la ligne « Tshopo 1 0 0,0% 0 »
  de la zone de santé homonyme de sa province : lue comme une zone, pas comme
  un en-tête, et la Tshopo reste à 7 zones.

Le SitRep 125, rapportage
du 16 septembre 2026 (publié le 17) — 7 475 cas confirmés, 3 605 décès,
létalité 48,2 %, 1 798 guéris, 905 patients en CTE, suivi des contacts
**87,6 %** (26 181 vus sur 29 873), 62 zones touchées sur 167 dans 7
provinces, 71 nouveaux cas (Ituri 41, Nord-Kivu 27, Haut-Uélé 2, Tshopo 1) et
28 décès du jour (18 communautaires, 10 intra-CTE). Intégré **en local le
18 septembre 2026** ; sept provinces et 62 zones relues contre les pages 2 et
3 du PDF, zéro écart ; `check_coherence` sans écart bloquant ; résumé des
Défis rédigé (124 mots). Trois tournures apprises :
- **Dixième tournure des contacts** : « Parmi les 29 873 contacts en cours de
  suivi, 26 181 ont été vus au cours des dernières 24 heures, exprimant une
  proportion de suivi de 87,6% » — le mot « contacts » s'intercale et une
  incise sépare « vus » du taux. `CONTACTS_PARMI_LES_RE` élargi.
- **Contacts par province, deux formes neuves** : « 90,7 % (13 535/14 926) en
  Ituri » (effectifs entre le taux et la province) et « Au Bas-Uélé, 172
  contacts ont été vus sur 180 en cours de suivi, soit 95,6 % » (province en
  tête). `PROV_D3_RE` et `PROV_D4_RE`. **Ils ne lisent que le voisinage de la
  phrase nationale** : appliqués au texte entier, ils attrapaient au 051
  « 17,6 % (43/244) du Nord-Kivu », qui parle des cas suspects vivants
  validés, et le 4 juillet perdait ses vraies provinces.
- **`extraire_cte.py` : « 5 patients demeurent en isolement »** (Bas-Uélé),
  quatrième verbe après « sont pris en charge en », « restent en » et « sont
  placés en ». Effet de bord vérifié et gardé : le Bas-Uélé rentre aussi au
  **120** (833 → 839) et au **121** (916 → 923, exactement la bande du
  bulletin).

Le SitRep 124, rapportage
du 15 septembre 2026 (publié le 16) — 7 404 cas confirmés, 3 577 décès,
létalité 48,3 %, 1 776 guéris, 930 patients en CTE, suivi des contacts
**87,4 %** (28 065 vus sur 32 094), 62 zones touchées sur 167 dans 7
provinces, 59 nouveaux cas (Ituri 35, Nord-Kivu 21, Bas-Uélé 2, Tshopo 1) et
32 décès du jour (16 communautaires, 16 intra-CTE). Intégré **en local le
17 septembre 2026 avec le SitRep 123** — rapportage du 14 septembre (publié
le 15), 7 345 cas, 3 545 décès, 48,3 %, 1 753 guéris, 938 en CTE, 87 nouveaux
cas (Ituri 57, Nord-Kivu 21, Haut-Uélé 9), 35 décès du jour (26
communautaires, 9 intra-CTE), contacts 89,3 % (31 389 / 35 158) — par la
recette des deux bulletins. Sept provinces et 62 zones relues contre les
pages 2 et 3 des deux PDF, zéro écart (nouveaux cas du jour compris pour le
124) ; `check_coherence` sans écart bloquant ; résumés des Défis rédigés
(122 et 126 mots). Cinq choses apprises, chaque diff limité aux 14 et
15 septembre :
- **Le titre du tableau des zones perd « de santé » au 124** : « Répartition
  des cas et décès confirmés par province et zone du 15 septembre 2026 ».
  `ZONE_SECTION_TITLE_RE` (`update_data.py`) exigeait « zone de santé » :
  aucune zone lue, `zones-history.json` resté au 123 et décès du jour par
  province à `null`. « de santé » devient facultatif.
- **Les aires de santé du 123 sortaient à 3 246 sur 3 104** : la colonne de
  gauche recollée donne « dont 3 2 46 Aires de santé », le « 3 » venant d'une
  autre phrase. On garde le plus long suffixe de chiffres qui ne dépasse pas
  le total (246). Donnée que le site n'affiche pas, corrigée quand même.
- **Huitième et neuvième tournures des contacts** : « La proportion des
  contacts suivis est de 89,3 % (31 389/35 158) » (123) puis « … se situe à
  87,4 % (28 065/32 094) » (124). `CONTACTS_SITUE_RE` accepte les deux ; sans
  elles les deux points perdaient leurs effectifs nationaux.
- **Laboratoire du Nord-Kivu au 124** : « 21 échantillons reçus et testés
  (14 vivants et 7 décès) sur 160 échantillons analysés (positivité de
  13,1%) » — les 21 sont les positifs. `RECUS_TESTES_SUR_RE`
  (`extraire_laboratoire.py`) ne joue que si vivants + décès = 21 et 21/160
  = la positivité publiée ; le total du jour tombe à 59 positifs pour
  59 nouveaux cas.
- **Voyageurs aux PoE/PoC** : « Nombre de personnes passées aux 147 864 …
  PoE/PoC » (123 et 124), « passées aux » intercalé avant les nombres ;
  `extract_piliers.py` le tolère (260 546 et 275 520).

Le SitRep 122, rapportage
du 13 septembre 2026 (publié le 14) — 7 258 cas confirmés, 3 510 décès,
létalité 48,4 %, 1 726 guéris, 905 patients en CTE, suivi des contacts
**78,6 %** (21 935 vus sur 27 905), 62 zones touchées sur 167 dans 7
provinces, 58 nouveaux cas (Ituri 44, Nord-Kivu 12, Haut-Uélé 2) et 35
décès du jour (23 communautaires, 12 intra-CTE : 6 en Ituri, 6 au
Nord-Kivu). Intégré **en local le 15 septembre 2026**, sept provinces et
62 zones relues contre les pages 2 et 3 du PDF, zéro écart ;
`check_coherence` sans écart bloquant, les deux notes anciennes
inchangées ; résumé des Défis rédigé dans la foulée (137 mots). Le suivi
des contacts **recule de 91,3 % à 78,6 % en un jour** (Nord-Kivu 69,2 %,
Haut-Uélé 65,7 %), et le **Sud-Ubangi a ses premiers contacts suivis**
(16 vus sur 39, 41,0 %). Deux tournures apprises :
- **`extraire_cte.py` : « N patients sont pris en charge en hospitalisation
  pour M lits »** (Ituri 472/1 015, Haut-Uélé 69/134), « 332 patients sont
  pris en charge en hospitalisation, soit un taux d'occupation global en
  sursaturation (145,6 %) » (Nord-Kivu, sans lits) et « 7 patients restent
  en isolement » (Bas-Uélé). Un verbe s'intercale entre les patients et le
  mot qui les qualifie, ce que les motifs existants exigeaient collés :
  **quatre provinces sur six manquaient**, le total du site tombait à 25
  pour 905 en bande. Un motif ajouté (« sont pris en charge en », « restent
  en », « sont placés en » devant hospitalisation / isolement) et le 122
  tombe **exactement sur la bande, 905**. Effet de bord vérifié et gardé :
  le **106 (28 août)** gagne le Sud-Kivu, « 26 patients restent en
  isolement », total 869 → 895 pour **896 annoncés en bande** — l'écart
  tombe de 27 à 1, ce dernier patient étant celui du Bas-Uélé (« 1 patient
  confirmé est en cours de soins pour 3 lits disponibles »), tournure
  toujours non lue et déjà signalée ici. Aucune autre date ne bouge.
- **Septième tournure des contacts** : « Concernant le taux de suivi des
  contacts, il se situe à 78,6 % (21 935/27 905) » — le « taux de » du 122
  là où le 121 mettait « la proportion du », et « il » au lieu de
  « elle ». `CONTACTS_SITUE_RE` accepte les deux, mêmes garde-fous ; diff
  limité au 13 septembre. Sans cela le point gardait son taux et ses cinq
  provinces mais perdait ses effectifs nationaux.
Laboratoire : 58 positifs = 58 nouveaux cas, garde-fou vérifié ; le
Sud-Ubangi n'entre pas (« 3 échantillons collectés dont 2 sont expédiés à
Kinshasa (INRB) », aucun résultat).

Le **SitRep 121**, rapportage
du 12 septembre 2026 (publié le 13) — 7 200 cas confirmés, 3 475 décès,
létalité 48,3 %, 1 712 guéris, 923 patients en CTE, 62 zones touchées sur
167 dans 7 provinces (aucune nouvelle depuis Bulu au 119), 87 nouveaux cas
(Ituri 44, Nord-Kivu 37, Haut-Uélé 3, Tshopo 3) et 38 décès du jour (28
communautaires, 10 intra-CTE : 6 en Ituri, 4 au Nord-Kivu). Intégré **en
local le 14 septembre 2026 avec le SitRep 120** — rapportage du
11 septembre (publié le 12), 7 113 cas, 3 437 décès, 48,3 %, 1 692 guéris,
855 en CTE, 91 nouveaux cas (Nord-Kivu 50, Ituri 33, Haut-Uélé 6, Tshopo 1,
Bas-Uélé 1), 39 décès du jour (32 communautaires, 7 intra-CTE), suivi des
contacts 87,5 % (23 416 vus sur 26 763) — par la recette des deux bulletins
(le 121 mis de côté, `update_data` + `build_pages` sur le 120 pour figer sa
lettre, puis le 121). Sept provinces et 62 zones relues contre les pages 2
et 3 des deux PDF, zéro écart ; `check_coherence` sans écart bloquant, les
deux notes anciennes inchangées ; résumés des Défis rédigés pour les deux
(131 et 142 mots). Deux choses apprises :
- **Sixième tournure des contacts au 121** : « S'agissant de la proportion
  du suivi des contacts, elle se situe à 91,3% (24 476/26 816) » — le taux
  d'abord, la fraction vus / à suivre entre parenthèses sans « vus » ni « à
  suivre ». `CONTACTS_SITUE_RE` dans `extract_contacts_followup.py`, en
  dernier repli, mêmes garde-fous ; diff limité au 12 septembre. Sans lui
  le point avait son taux et ses cinq provinces mais pas ses effectifs.
- **Le 121 publie deux taux de suivi** : 88,0 % dans la bande de chiffres
  clés, 91,3 % dans la phrase de surveillance, dont la fraction fait bien
  91,3. `latest.json` porte la bande (88,0, clé `contactsFollowUpRate`,
  que le site n'affiche nulle part), `contacts-followup.json` la phrase
  vérifiée (91,3, ce que la page Riposte montre) — même cas que le 099
  (84,7 / 84,4), même choix.
- **Deux tournures de laboratoire, « tous positifs »** : le 120 écrit
  « Bas-Uélé : 1 échantillon reçu et testé (1 vivant), s'est révélé
  positif » (idem Tshopo), le 121 « Tshopo : 3 échantillons reçus et
  testés (vivants) tous se sont révélés positifs ». Aucun nombre de
  positifs imprimé : les deux provinces sortaient à `null`, le total du
  jour aussi, et le garde-fou « positifs = nouveaux cas » ne jouait pas.
  `TOUS_POSITIFS_RE` dans `extraire_laboratoire.py` retient le nombre
  d'échantillons, symétrique du « tous négatifs » existant ; diff limité
  aux 11 et 12 septembre, et le garde-fou repasse (91 = 91, 87 = 87 ; le
  Bas-Uélé du 121, « tous se sont révélés négatifs », reste à 0).
Les six visuels pour X (dossier `tmp/proto-visuels/`, hors dépôt, copie
dans `~/Desktop/rapport ebola tracker/_mis-de-cote-2026-09-10/maquettes/
proto-visuels-x/`) sont refaits au 121 le même jour, en deux langues :
code-barre (ex-rayures), calendrier avec les deux rattrapages marqués,
tapis, « 1 point, 1 malade », escalier, et une carte des sept provinces
ajoutée le 13 septembre (contours par superposition trait épais puis
remplissage, province par province). Chaque image porte en bas à gauche
la date des dernières données et le numéro du bulletin.

Le **SitRep 119**, rapportage
du 10 septembre 2026 (publié le 11) — 7 022 cas confirmés, 3 398 décès,
létalité 48,4 %, 1 671 guéris, 837 patients en CTE, suivi des contacts 87,6 %
(25 117 vus sur 28 672 ; Ituri 90,0 %, Nord-Kivu 86,7 %, Bas-Uélé 77,6 %,
Haut-Uélé 76,1 %, Tshopo 72,9 %), **une septième province, le Sud-Ubangi,
par la zone de santé de Bulu** — un cas confirmé, décédé, « un sujet âgé de
23 ans, de sexe masculin, qui est parti de la province du Sud-Kivu depuis le
10 juillet 2026 » —, donc **62 zones touchées sur 167** (151 + les 16 du
Sud-Ubangi), 80 nouveaux cas (Nord-Kivu 43, Ituri 30, Haut-Uélé 6,
Sud-Ubangi 1) et 49 décès du jour (31 communautaires, 18 intra-CTE : 12 en
Ituri, 4 au Haut-Uélé, 2 au Nord-Kivu). Laboratoire 80 positifs = 80
nouveaux cas ; alertes 2 254 reçues, 1 846 vérifiées, 429 validées, le
Sud-Ubangi « ND ». Intégré **en local le 11 septembre**, résumé des Défis
rédigé dans la foulée, `check_coherence` sans écart bloquant, deux notes
anciennes inchangées. **Ce que la septième province a demandé** — la
première depuis le Bas-Uélé au 090, et la première hors du nord-est :
- `update_data.py` : « Sud Ubangi » / « Sud-Ubangi » dans
  `PROVINCE_NAMES_MAIN`, `PROVINCE_CANON`, `PROVINCE_NAMES`, les deux motifs
  du tableau 1 (`PROVINCE_SUMMARY_ROW_RE`, `_NEWFIRST_RE`) et
  `PROV_SUBTOTAL_RE`. Sans cela, le premier passage avait lu « Sud Ubangi »
  et « Bulu » comme **deux zones du Bas-Uélé** (63 zones, 6 provinces) — le
  message « zone(s) jamais vue(s) » est ce qui l'a révélé. Le total de
  zones **n'est plus le 151 écrit en dur** : c'est la somme des totaux des
  provinces (167). Et `PROV_SUBTOTAL_RE` accepte `Bas[ -]Uélé` : le 119
  écrit « Bas-Uélé 4 3 75,0% 0 0 0 0 » avec un tiret là où le 118 mettait
  une espace, et la province perdait ses décès du jour ; les sous-totaux
  sont désormais indexés par nom canonique.
- Extracteurs : la province dans `PROVINCES_RE` (alertes, laboratoire,
  CTE), dans les tables de canonisation (contacts, décès-lieu, piliers,
  défis, `defis_synthese`). Le laboratoire écrit « 1 nouveau résultat
  positif (1 décès) sur l'échantillon analysé » — singulier, sans chiffre :
  réécrit « 1 échantillon analysé » avant lecture, motif singulier ajouté,
  sinon 79 positifs pour 80 cas.
- Site : `provinceSlugs` (→ `/donnees/sud-ubangi/`, `/en/data/sud-ubangi/`,
  `/sw/takwimu/sud-ubangi/`, 146 fichiers générés au lieu de 143),
  `provinceGrammar`, le repère Gemena dans `mapLandmarks.places`,
  `PROVINCE_COLORS` dans `build_pages.py` et `app.js` (**#B0487D**, un
  magenta : seule teinte encore libre qui se sépare du rouge du Bas-Uélé et
  du violet de la Tshopo en deutéranopie), `PROVINCES`,
  `PROVINCE_TABLE_DATA_SEED` et `PROVINCE_AGG_COORDS` d'`app.js`,
  `provinceArrivals` (jalon du 10 septembre, la note du Bas-Uélé ne dit
  plus « dernière province ») et la FAQ « Sept provinces » (trois langues).
  `build_geo.py` relancé : `province-maps.json` a son septième cadrage,
  `zones-overview.json` et `health-zones.geojson` bougent d'une ligne.
- **Cinquième tournure des contacts** : « Parmi les 28 672 en cours de
  suivi, 25 117 ont été vus, correspondant à une proportion journalière de
  suivi à 87, 6% » — à suivre avant vus, « correspondant à », « de suivi
  à ». `CONTACTS_PARMI_LES_RE`, mêmes garde-fous.
- Non lu, et laissé tel quel : le Nord-Kivu n'imprime plus ses lits
  (« 311 patients … en sursaturation (141,4%) »), la lettre le cite avec
  son taux ; le Sud-Ubangi n'a pas de ligne CTE ni de contacts, et sa ligne
  d'alertes est « ND » (rendue en zéros, comme le Sud-Kivu).

Le **SitRep 118**, rapportage
du 9 septembre 2026 (publié le 10) — 6 942 cas confirmés, 3 349 décès, létalité
48,2 %, 1 647 guéris, 823 patients en CTE, suivi des contacts 84,4 % (19 945
vus sur 23 630 ; Nord-Kivu 86,1 %, Ituri 83,6 %, Bas-Uélé 80,3 %, Tshopo
83,5 %, Haut-Uélé 79,7 %), **61 zones touchées, aucune nouvelle**, 99 nouveaux
cas (Ituri 47, Nord-Kivu 46, Haut-Uélé 6) et 39 décès du jour (29
communautaires, 10 intra-CTE : 7 en Ituri, 2 au Nord-Kivu, 1 au Haut-Uélé).
Laboratoire 99 positifs = 99 nouveaux cas ; alertes 1 941 reçues, 1 666
vérifiées, 386 validées, 205 transférées. Intégré **en local le
11 septembre**, résumé des Défis rédigé dans la foulée (règle du
9 septembre), `check_coherence` sans écart bloquant, deux notes anciennes
inchangées. Une **quatrième tournure des contacts** apprise dans
`extract_contacts_followup.py` : « 19 945 parmi les 23 630 en cours de suivi
ont été vus, exprimant une proportion journalière de 84, 4% » — les vus
avant les à suivre, « parmi » à la place de « d'entre eux », et une espace
glissée après la virgule du taux. `CONTACTS_PARMI_RE` la lit (taux, puis
effectifs nationaux, mêmes garde-fous que les trois motifs précédents) et
`taux_texte()` retire les espaces autour du séparateur décimal ; sans lui le
118 sortait « sans cette donnée » alors que `latest.json` portait déjà
84,4 % par une autre voie. Les cinq provinces se lisent par `PROV_D2_RE`
inchangé. Les 823 patients en CTE de la bande ne se retrouvent pas dans
`cte.json`, qui somme 805 sur quatre provinces : le Sud-Kivu n'écrit que
« 18 cas suspects restent en isolement », sans lits ni « hospitalisés », et
805 + 18 = 823 — la bande compte les suspects isolés, le tableau des CTE ne
les voit pas. Deux lignes de zones (Rwampara, Pawa) ont une cellule vide
dans la grille des décès du jour ; `update_data` a déduit leur ventilation
de la ligne de province comme prévu, et le total national a été relu sur la
ligne « Total » du texte après une grille illisible (« 482 + 61151404 »),
repli déjà en place depuis le 099.

Le **SitRep 117**, rapportage
du 8 septembre 2026 (publié le 9) — 6 843 cas confirmés, 3 310 décès, létalité
48,4 %, 1 611 guéris, 833 patients en CTE (la somme des cinq provinces qui
rapportent égale la bande de chiffres clés), suivi des contacts 86,5 %
(21 723 vus sur 25 108, lu par `CONTACTS_DENTRE_EUX_RE` ajouté au 116),
**61 zones touchées, aucune nouvelle**, 86 nouveaux cas (Ituri 55, Nord-Kivu
27, Haut-Uélé 2, Tshopo 2) et 43 décès du jour (19 communautaires, 24
intra-CTE dont 21 en Ituri). Laboratoire 86 positifs = 86 nouveaux cas ;
alertes 2 140 reçues, 1 389 vérifiées, 408 validées, 229 transférées. Intégré
**en local le 10 septembre**, résumé des Défis rédigé dans la foulée
(règle du 9 septembre), `check_coherence` sans écart bloquant, deux notes
anciennes inchangées. La référence imprimée est « N°117/MVEBDB/08/09/2026 »
avec la date de rapportage, là où le 116 mettait sa date de publication
(« N°116/…/08/09 ») : deux bulletins portent la même date dans leur
référence, le site les distingue par `reportingDate`. Une tournure apprise
dans `extraire_cte.py` : le Nord-Kivu écrit « en sursaturation (130,5 % ;
287/220 lits disponibles) », la fraction du 108 et le « lits disponibles »
du 111 dans la même parenthèse — aucun des deux motifs ne la lisait, les
lits manquaient et `bulletin.py` plantait (`KeyError: 'lits'`) sur la
province saturée. `LITS_FRACTION_RE` accepte désormais « lits disponibles »
après la fraction (diff de `cte.json` limité au 8 septembre), et la lettre
ne tombe plus quand une province saturée n'a pas de lits : elle la cite
avec son taux (`lettreCteItemTaux`, trois langues) au lieu de ses lits.

Le **SitRep 116**, rapportage
du 7 septembre 2026 (publié le 8) — 6 757 cas confirmés, 3 267 décès, létalité
48,3 %, 1 590 guéris, 813 patients en CTE, suivi des contacts 88,3 % (21 359
vus sur 24 719), **61 zones touchées, aucune nouvelle**, 71 nouveaux cas
(Ituri 41, Nord-Kivu 27, Haut-Uélé 3) et 41 décès du jour (31
communautaires, 10 intra-CTE). Intégré **en local le 9 septembre**, avec le
**SitRep 115** — rapportage du 6 septembre (publié le 7), 6 686 cas, 3 226
décès, létalité 48,3 %, 1 563 guéris, 819 en CTE, suivi des contacts 85,3 %
(20 888 vus sur 24 479 ; Ituri 87,0 %, Nord-Kivu 85,4 %, Haut-Uélé 76,1 %,
Bas-Uélé 70,4 %, Tshopo 59,1 %), 61 zones sans nouvelle, 82 nouveaux cas
(Ituri 39, Nord-Kivu 39, Haut-Uélé 4) et 51 décès du jour (36
communautaires, 15 intra-CTE : 12 en Ituri, 2 au Nord-Kivu, 1 au Haut-Uélé).
Ce que ces deux bulletins ont appris :
- **Le 115 n'est pas dans la liste `insp.cd/category/sitrep/`** que parcourt
  `download_all_sitreps.py` (la liste saute du 114 au 116), mais son article
  existe (`/sitrep-n115-mvebdb-07-09-2026/`) et se trouve par la recherche
  du site (`insp.cd/?s=SitRep+115`), avec son PDF. Le propriétaire avait
  transmis un autre exemplaire, hébergé sur `administration.sante.gouv.cd` :
  **une autre édition du même bulletin**, signée « Incident Manager
  Adjoint » et non par le Directeur général de l'INSP, sections renumérotées
  2.x avec des « Défi majeur », 340 aires de santé au lieu de 246, une prose
  analytique (« Stabilisation des nouveaux cas à 82 ») — mêmes chiffres
  clés. Les extracteurs sont calés sur le format INSP (neuf blocs « Défis »,
  mêmes titres que le 114 et le 116) : c'est l'exemplaire d'insp.cd qui est
  dans `reports/`. Les sept anciens numéros manquants (003, 029…) ne
  répondent pas à cette recherche, vérifié le même jour. Un repli du script
  de téléchargement par la recherche, pour un numéro absent de la liste,
  serait utile ; non fait.
- **Deux bulletins d'un coup se traitent l'un après l'autre** :
  `update_data.py` ne lit en détail que le dernier PDF de `reports/`
  (`find_latest_report`), les autres n'entrent que par cas et décès dans la
  liste des rapports. Le 116 traité seul laissait le 115 sans guéris
  (`recovered: null` dans `sitreps.json`), sans instantané de zones ni de
  provinces, sans lettre figée. Recette : mettre le 116 de côté, lancer
  `update_data.py` puis `build_pages.py` (la lettre 115 se fige à la
  génération), remettre le 116, relancer les deux. Les autres extracteurs
  lisent tous les PDF et n'ont pas ce problème.
- **La phrase des contacts a changé une troisième fois au 116** : « Des
  24 719 contacts à suivre pour la journée du 07 septembre, 21 359 d'entre
  eux ont été vus, soit une proportion journalière de 88,3 % » — ni « suivi
  des contacts » ni « vus sur … à suivre ». `CONTACTS_DENTRE_EUX_RE` dans
  `extract_contacts_followup.py` lit les trois nombres (à suivre, vus, taux),
  en dernier repli pour le taux et à défaut de `NATIONAL_D_RE` pour les
  effectifs, mêmes garde-fous ; diff limité aux 6 et 7 septembre.
- **Le 116 imprime « Buta 1 1 1 0 »** : la létalité de cette zone du
  Bas-Uélé est rendue « 1 » et non « 100,0% ». Sans le « % » qui sert de
  repère, la ligne ne correspondait à rien et Buta manquait de `latest.json`
  (60 zones détaillées pour 61 déclarées, Bas-Uélé 3 cas pour 4, carte
  6 756 pour 6 757), publié ainsi le 9 septembre au matin. **Corrigé le
  même jour à la demande du propriétaire (« rajoute Buta »)** :
  `ZONE_LINE_RATIO_RE` et `zone_line_ratio_match()` dans `update_data.py`
  lisent un ratio brut 0 ou 1 à la place de la létalité, **seulement s'il
  redit les deux cumuls** (1 quand décès = cas > 0, 0 quand décès = 0),
  sur une ligne à nombres simples et à queue non vide — « Buta 1 1 1 0 »
  donne 1 cas, 1 décès, 100,0 %, 0 nouveau cas, 0 décès du jour, et le
  script l'annonce (« létalité imprimée « 1 » sans le signe %, relue
  100,0% = 1/1 »). Un « 1 » qui serait un nouveau cas (3 cas, 1 décès)
  ne passe pas. Les trois écarts ont disparu, 61 zones dans `latest.json`.
- Écarts de la source, laissés visibles : occupation CTE du 115 (Nord-Kivu
  123,2 % publiés pour 262/220 = 119,1 % ; Haut-Uélé 50,8 % pour 68/128 =
  53,1 %) ; alertes du 115, Tshopo 100 vérifiées pour 99 reçues. Recoupement
  115 → 116 zone par zone : aucun écart signalé par `recouper_avec_la_veille`
  (les alertes vues au premier passage comparaient le 116 au 114).
- **Les lettres 090 à 099 existent depuis le 9 septembre 2026, en local**
  (« fais-le, grande vigilance à la cohérence des chiffres »), l'archive
  commence donc le 12 août. Méthode : un **bac à sable hors dépôt** (copie
  de `scripts/`, `data/`, `reports/`), les PDF postérieurs mis de côté, et
  `update_data.py` lancé dix fois, un PDF de plus à chaque passe — le
  lecteur d'aujourd'hui, pas l'historique git de `latest.json` (qui porte
  pour ces numéros des versions instables : 094 avec 76, 73 puis 54 zones,
  095 avec 0, 18 puis 20, et un 094 dont le texte disait « N°093 » avant
  que le fichier soit remplacé le 20 août). Chaque instantané a été comparé
  aux séries du site (`sitreps`, `province-history`, `zones-history`,
  `contacts-followup`) : national, provinces, 57 à 54 zones, cumuls et
  nouveaux cas identiques sur les dix jours. Trois choses corrigées en
  passant : (1) le 090 écrit « Haut Uélé * 119 55 46,2% 6/13 » — espace
  au lieu du tiret, espace AVANT l'astérisque — et la province manquait
  aussi bien de l'instantané que de `province-history.json` au 12 août ;
  `PROVINCE_SUMMARY_ROW_RE` et `_NEWFIRST_RE` acceptent `Haut[- ]Uélé`,
  `Bas[- ]Uélé` et `\s*\**`, les trois lecteurs passent par
  `canon_province()` (le 092 sortait « Haut Uélé » tel quel), et le 12 août
  a reçu Haut-Uélé 119/55 dans `province-history.json` ; (2) `sitreps.json`
  n'avait pas de guéris avant le 14 août — 965 (090) et 976 (091) ajoutés
  depuis la bande de chiffres clés, les 81 dates antérieures restent à
  `null` ; (3) le 099 imprime 84,7 % de suivi des contacts dans sa bande et
  84,4 % dans sa phrase de surveillance (19 829 vus sur 23 492 = 84,4 %) —
  l'instantané porte 84,4, la valeur vérifiée que le site affiche déjà.
  Les noms de zones des instantanés sont ceux de `latest.json` du jour
  (`Boma Mangbetu` et non `Boma-Mangbetu`), par clé normalisée. Le 116
  relu avec le lecteur corrigé ne bouge pas. Dix résumés des Défis rédigés
  (fr/en/sw), le swahili à faire relire. Avant le 090, pas d'instantané
  versionné et les Défis d'avant le 084 ont un autre format : on s'arrête là.
- **Les lettres 115 et 116 ont leur résumé rédigé des Défis** depuis le
  9 septembre (fr/en/sw dans `bulletin-notes.json`), et **la règle change
  ce jour, décision du propriétaire** : le résumé s'écrit à chaque
  intégration d'un bulletin, sans attendre son go (« que tu le fasses
  automatiquement à chaque fois »). `check_coherence` le rappelle par une
  note non bloquante quand le bulletin courant a des blocs « Défis » et pas
  de résumé. Voir la règle des Défis de la lettre, plus bas.

Le **SitRep 114**, rapportage
du 5 septembre 2026 (publié le 6) — 6 604 cas confirmés, 3 175 décès, létalité
48,1 %, 1 548 guéris, 851 patients en CTE (510 en Ituri pour 978 lits, 253 au
Nord-Kivu pour 220 lits soit 115 %, 65 au Haut-Uélé, 6 à la Tshopo, 17 au
Sud-Kivu — la somme égale la bande de chiffres clés), suivi des contacts
85,7 % (20 459 vus sur 23 880), **61 zones touchées, aucune nouvelle**,
82 nouveaux cas (Ituri 49, Nord-Kivu 31, Haut-Uélé 2) et 41 décès du jour
(32 communautaires, 9 intra-CTE dont 5 « à ventiler » en Ituri, qui en
compte désormais 366). Intégré et **publié le 7 septembre**, sans les deux
chantiers en local — « Flux & déplacés » et la maquette « Riposte & défis »
— par la recette « Publier sans publier », étendue ce jour à la maquette ;
ce commit publie en revanche sur `/riposte/` les « Défis » du dernier
bulletin cités sous chaque cadre (`defis_seed`, `data/defis.json`,
`extraire_defis.py` ajouté au workflow). **Corrigé le même jour, à la
demande du propriétaire** : la page avait été renommée « Riposte & défis »
et dotée d'un chapitre « Les autres fronts » sans qu'il l'ait demandé — la
page et son onglet redeviennent « La riposte », le chapitre est retiré
(gabarit, `defis_seed`, clés `defiAutres*` et `defiNone`), seules les
citations sous les quatre cadres restent.
**Suite du 7 septembre, publiée le jour même (commit `5ae7d35`)** : la
maquette « Riposte & défis » a pris l'adresse `/riposte/` (fragment, titres, onglet, pastille « Nouveau »), voir
la section de la page ; le corpus des Défis d'avant le 084 est gelé dans
`data/defis-anciens.json`. Recoupement avec le 113 : pour chacune des 61 zones, cumul du
114 moins cumul du 113 = nouveaux cas du jour, idem pour les décès, zéro
écart ; neuf ventilations déduites de la ligne de province (Bunia 6,
Mongbwalu 2, Nia-Nia 2, Nizi 5, Biena 1, Butembo 4, Kyondo 3, Mabalako 1,
Masereka 1, toutes communautaires). Laboratoire 82 positifs = 82 nouveaux
cas (Ituri 49/292, Nord-Kivu 31/96, Haut-Uélé 2/8, Bas-Uélé 0/3, Tshopo
0/5) ; alertes 1 628 reçues, 1 369 vérifiées, 286 validées, 136
transférées, le Sud-Kivu « n'a pas rapporté » (ND rendu en zéros) ; les
Défis lus sur neuf piliers. `check_coherence` sans écart bloquant, les deux
écarts « connus de la source » (positivité 038/065/072, occupation CTE
108/112) inchangés. Une lecture apprise : **le suivi des contacts par
province manquait depuis le 109**. La phrase de surveillance a inversé
l'ordre au 110 — « 90,9% en Ituri (10 302/11 339), 83,5% au Nord-Kivu
(8 491/10 163) » là où le 108 écrivait « Ituri 89,4 % (11 829/13 235) » —
et `PROV_D_RE` ne voyait plus rien. `PROV_D2_RE` dans
`extract_contacts_followup.py` lit le taux devant la province, avec les
mêmes garde-fous (vus ≤ à suivre, vus / à suivre à un point du taux) ; les
110 à 114 retrouvent leurs cinq provinces, le 109 n'en détaille aucune, les
points antérieurs n'ont pas bougé (diff en ajouts purs).

Le **SitRep 113**, rapportage
du 4 septembre 2026 (publié le 5) — 6 522 cas confirmés, 3 134 décès, létalité
48,1 %, 1 516 guéris, 817 patients en CTE (pour la première fois le total du
site égale la bande de chiffres clés, le Sud-Kivu ayant rapporté ses 16
patients pour 25 lits), suivi des contacts 86,0 % (21 909 vus sur 25 500),
**61 zones touchées, une nouvelle : Kayna, au Nord-Kivu** (1 cas), 86 nouveaux
cas (Ituri 53, Nord-Kivu 31, Haut-Uélé 2) et 39 décès du jour (30
communautaires, 9 intra-CTE dont 7 « à ventiler » en Ituri). Intégré et
**publié le 6 septembre** (commit `925bbf9`). Une lecture apprise, et
c'est la règle 11 proposée la veille devenue code : `recouper_avec_la_veille()`
dans `update_data.py` compare chaque zone à l'instantané précédent de
`zones-history.json`. Le 113 écrit « Wamba 83 31 37,3% 1 1 » — cumul de cas
inchangé, donc ce « 1 » est un décès (intra-CTE, la ligne de province le
dit) et son total, pas un nouveau cas ; le repli texte lisait 1 nouveau cas
et le Haut-Uélé sommait 3 pour 2 déclarés. La règle ne corrige que ce cas
(cumul inchangé et nouveaux cas annoncés → zéro, le nombre lu rejoint les
décès) ; tout autre écart entre cumul et colonnes du jour est **signalé,
jamais corrigé**. Aucun autre écart sur les 61 zones. Laboratoire 86
positifs = 86 nouveaux cas ; alertes 2 144 reçues, 1 955 vérifiées, 399
validées, 222 transférées, le Sud-Kivu de retour (8 reçues) ; les Défis
lus sur neuf piliers. `check_coherence` sans écart bloquant.

Le **SitRep 112**, rapportage
du 3 septembre 2026 (publié le 4) — 6 436 cas confirmés, 3 095 décès, létalité
48,1 %, 1 495 guéris, 738 patients en CTE, suivi des contacts 88,5 % (21 678
vus sur 24 497), 60 zones touchées (aucune nouvelle), 94 nouveaux cas (Ituri
60, Nord-Kivu 25, Haut-Uélé 9) et 23 décès du jour (17 communautaires, 6
intra-CTE dont 3 « à ventiler » en Ituri). Intégré et **publié le
5 septembre**, sans le chantier Flux (recette « Publier sans publier »). Même vérification qu'au 111 : pour
chacune des 60 zones, cumul du 112 moins cumul du 111 = nouveaux cas du jour,
idem pour les décès, zéro écart ; cinq ventilations déduites par
`ventiler_par_soustraction` (Bunia 2, Komanda 4, Nizi 1, Rwampara 3,
Kalunguta 1, toutes communautaires) ; laboratoire 94 positifs = 94 nouveaux
cas ; alertes 1 792 reçues, 1 512 vérifiées, 345 validées, 190 transférées
(le Sud-Kivu « n'a pas rapporté », ND rendu en zéros comme les cinq fois
précédentes). Deux lectures apprises. (1) La ligne Total du tableau 1 est
découpée une **troisième** façon : les chiffres seuls au-dessus, puis
« Total » suivi de la seule fraction de zones (« 94 6 436 3 095 48,1% » ⏎
« Total 60/151 (39,7 %) ») — `recoller_total_orphelin` recolle désormais
libellé + chiffres + fraction, sous le même garde-fou, `TOTAL_FRACTION_SEULE_RE`
n'acceptant après « Total » que la fraction (la ligne Total du tableau
détaillé, à huit nombres, ne peut pas mordre). (2) La phrase des contacts ne
nomme plus l'indicateur : « Une légère amélioration a été observée sur la
proportion, soit 88,5 % (21 678 vus sur 24 497 à suivre) » — aucun des trois
libellés de `CONTACTS_RE` n'y figure, le 112 sortait sans taux.
`CONTACTS_VUS_SUR_RE` reconnaît le taux par la parenthèse « vus sur … à
suivre » qui le suit, en dernier repli ; diff limité au 3 septembre. Les
autres extracteurs ont lu le 112 sans retouche. Écart de la source, laissé
visible : le Haut-Uélé publie 50,8 % d'occupation pour 62/128 = 48,4 % (note
non bloquante de `check_coherence`, comme Tshopo 108). Total CTE du site
727 pour 738 en bande de chiffres clés — Sud-Kivu et Bas-Uélé muets, comme au
111. Orthographe : le 112 rend « Boma Mangbetu » avec une espace (40
instantanés sur 47 l'écrivent ainsi, les 108-111 avec un tiret) ; la clé
normalisée absorbe la différence, rien à corriger. Sous Node 20, les outils
de `scripts/verif/` se lancent avec `node --experimental-websocket`.

Le **SitRep 111**, rapportage
du 2 septembre 2026 — 6 342 cas confirmés, 3 072 décès, létalité 48,4 %,
1 475 guéris, 770 patients en CTE, suivi des contacts 86,5 % (17 910 vus sur
20 711), 60 zones touchées (aucune nouvelle), 92 nouveaux cas (Ituri 60,
Nord-Kivu 25, Haut-Uélé 5, Tshopo 2) et 33 décès du jour (24 communautaires,
9 intra-CTE). Intégré **en local le 4 septembre**, non publié à cette date.
Vérification la plus forte à ce jour : pour chacune des 60 zones, cumul du
111 moins cumul du 110 = nouveaux cas du jour, et de même pour les décès —
zéro écart, et aucune ventilation communautaire / CTE restée vide (5 lignes
reconstruites depuis le texte, toutes résolues par la grille ou par
`ventiler_par_soustraction`). Une tournure apprise dans `extraire_cte.py` :
le Nord-Kivu écrit « en⏎sursaturation (118,6 % ; 220 lits disponibles) » —
le saut de ligne entre « en » et « sursaturation » échappait au motif du 108
(qui interdit `\n`), et « 220 lits disponibles » n'avait ni « pour » ni
fraction ; deux motifs ajoutés, le second exigeant « % ; » devant les lits,
sans quoi il mordait sur la synthèse du SitRep 018 (« 71 lits disponibles au
Nord-Kivu pour 8 patients »). Diff limité au 2 septembre. Le 111 ne dit rien
des CTE du Sud-Kivu ni du Bas-Uélé : le total CTE du site fait 758 pour 770
en bande de chiffres clés, l'écart est celui de la source. Coquille de la
source à connaître : « les données de la ZS de Wamba (province de la Tshopo)
n'ont pas été rapportées » — Wamba est au Haut-Uélé. Constaté au passage et
corrigé le même jour : le 1ᵉʳ juin (SitRep 018), `cte.json` portait 8
hospitalisés en Ituri qui étaient les 8 patients du Nord-Kivu — « Le
Nord-Kivu suit avec 8 patients en isolement » restait dans le morceau de
l'Ituri parce que `REPERE_RE` ne connaissait pas « Le » devant un nom de
province (seulement « L' », « En », « Au »…). « Le » ajouté, plus deux
tournures de ce bulletin (« des patients hospitalisés (158/171) », « file
active de 5 patients ») : le 1ᵉʳ juin lit désormais Ituri 158, Nord-Kivu 8,
Sud-Kivu 5, conformes au tableau 4 du bulletin (158 / 8 en isolement ; le
Sud-Kivu y est à 7, la prose dit 5, la prose est retenue faute de lecteur
pour ce format de tableau de l'époque A). Seule cette date a bougé.

Le **SitRep 110**, rapportage
du 1ᵉʳ septembre 2026 — 6 250 cas confirmés, 3 039 décès, létalité 48,6 %,
1 439 guéris, 869 patients en CTE, suivi des contacts 89,0 % (16 719 vus sur
18 784), **60 zones touchées** (aucune nouvelle zone), 64 nouveaux cas
(Ituri 39, Nord-Kivu 20, Haut-Uélé 4, Tshopo 1) et 32 décès du jour
(25 communautaires, 7 intra-CTE). Intégré **en local le 3 septembre**, non
publié à cette date, six provinces et 60 zones relues une à une contre les
pages 2 et 3 du PDF, zéro écart ; les cumuls prolongent exactement ceux du
109 (+64 cas, +32 décès, +30 guéris, par province aussi). Deux lectures
apprises : (1) la ligne Total du tableau des provinces est rendue sur deux
lignes de texte, le libellé **seul sous ses chiffres** (« 64 6 250 3 039
48,6% 60/151 (39,7 %) » puis « Total ») — aucun motif ne mordait, arrêt sur
« Table de répartition par province introuvable » ; `recoller_total_orphelin`
recolle un « Total » isolé à la ligne de chiffres voisine, seulement si la
ligne recollée correspond à l'un des deux motifs du tableau résumé ; (2) le
Haut-Uélé écrit « Au terme de la journée, 62 patients, soit un taux
d'occupation global de 51,7% (120 lits) », sans « hospitalisés » ni « pour
N lits » — deux motifs ajoutés en dernière position dans `extraire_cte.py`,
diff limité au 1ᵉʳ septembre, et le total CTE passe de 807 à **869, le
chiffre exact de la bande de chiffres clés**. Deux incohérences sont dans la
source, pas dans l'extraction, et restent visibles : le tableau 2 donne
**0 nouveau cas à la ligne Tshopo** quand sa zone Mangobo en porte 1 et que
le tableau 1 et les faits saillants disent 1 (le site retient 1) ; et la
section Laboratoire ne compte que 63 positifs du jour (39 + 20 + 4, rien pour
la Tshopo) pour 64 nouveaux cas — l'écart « 63 vs 64 » de `check_coherence`
est non bloquant et attendu. Rwampara et Beni avaient d'abord leur
ventilation des décès du jour à `None` (queues « 7 2 2 » et « 5 3 3 »
reconstruites depuis le texte, ambiguës par nature) ; le propriétaire a
confirmé 2 et 3 décès communautaires, et `ventiler_par_soustraction()` les
déduit désormais de la ligne de province (13 - 11 = 2 pour Rwampara,
12 - 9 = 3 pour Beni), voir les pièges connus. Le chemin grille
du tableau des provinces est hors jeu depuis que le 106 a mis le titre
« Tableau 1. » en première ligne de la grille (`extract_province_summary`
cherche « Province » en `t[0][0]`) : c'est le repli texte qui lit tout depuis.

Le **SitRep 109**, rapportage du 31 août 2026 — 6 186 cas confirmés, 3 007
décès, létalité 48,6 %, 60 zones touchées, 86 nouveaux cas et 57 décès du
jour (43 communautaires, 14 intra-CTE) — avait été intégré en local le
2 septembre. Il a fait tomber trois lectures, toutes corrigées le
même jour et vérifiées ligne à ligne contre les pages 2 et 3 du PDF (six
provinces et 60 zones, zéro écart) : (1) la grille pdfplumber du tableau des
provinces a éclaté son en-tête sur cinq lignes avec une colonne « Nouveaux
cas » en double, la lecture par en-tête est revenue vide et le repli texte ne
connaissait que l'ancien ordre (nouveaux cas en fin de ligne) —
`PROVINCE_SUMMARY_ROW_NEWFIRST_RE` lit désormais l'ordre du 104 dans le texte
brut, les deux motifs s'excluant l'un l'autre ; (2) la ligne Total du tableau
détaillé est rendue avec des `None` intercalés (`'48,6%', None, '86', None,
'43', None, '14', None, '57'`) et les index fixes publiaient **486 décès
communautaires** (la létalité) et 86 décès du jour (les nouveaux cas) — le
national exige maintenant communautaires + intra-CTE = total, sinon il relit
la ligne Total du texte ; (3) la section des CTE s'intitule « Prise en charge
holistique », inconnue d'`extraire_cte.py`, qui l'accepte désormais (le mot
« holistique » la distingue du « Prise en charge » des époques B et C), et
« Huit (8) patients sont en isolement » au Sud-Kivu demandait une parenthèse
optionnelle après le nombre. `check_coherence` repasse sans écart bloquant,
les deux écarts non bloquants (positivités 038, 065, 072 ; occupation Tshopo
108) étant antérieurs. Le 108 avait ses propres particularités : 7 lignes de
zone reconstruites depuis le texte brut (toutes vérifiées contre le PDF,
zéro écart sur les 60 zones) ; le bulletin publie 32,0 % d'occupation CTE à
la Tshopo quand ses propres nombres font 7/25 = 28 % (écart laissé visible,
note de check_coherence) ; deux formulations labo inédites — « 1 swab reçu
et testé » au Bas-Uélé, « 2 échantillons reçus, tous négatifs » à la
Tshopo — ont demandé trois motifs nouveaux dans `extraire_laboratoire.py`
(dont « dont 1 swab analysé » du 106) ; la réextraction n'a touché que les
Tshopo des 106-107 et le 30 août, diff relu ligne à ligne, et le garde-fou
« positifs du jour = nouveaux cas » repasse (59 = 59). Autre tournure
inédite, côté CTE : le Nord-Kivu écrit « en sursaturation (128,2 % ;
282/220) » — deux motifs ajoutés à `extraire_cte.py` (taux entre
parenthèses, lits au dénominateur de la fraction), diff limité au seul
30 août, national à 813/1 223 = 66,5 %. Le Sud-Kivu repasse à « ND » au
tableau des alertes là où le 107 disait des zéros.

---

# Pieges connus

Deplaces de CLAUDE.md le 22 septembre 2026 : ils decrivent des pieges d'extraction et de
lecture des PDF, exactement le perimetre de ce journal.

**La zone de santé « Tshopo » porte le nom de sa province.** C'est la seule du
pays. Les deux chemins d'extraction la prenaient pour un en-tête et
l'avalaient — corrigé le 24 août par la règle : une ligne qui porte le nom de
la province **en cours** décrit une zone homonyme, pas un nouvel en-tête.

**`province-history.json` ne dit pas quand une province a eu son premier cas.**
Aucune n'y apparaît jamais à zéro : chacune entre avec un cumul déjà constitué.
Les vraies dates d'arrivée sont curées dans `site/strings.json` sous
`provinceArrivals`, chacune avec le numéro du bulletin qui l'établit.

**Ré-extraire un ancien bulletin ne redonne pas toujours les mêmes noms de
zone.** Un rattrapage sur les 13 et 14 août a produit « Makiso--Kisangani »
avec deux tirets. Toujours diffuser avant de publier un rattrapage.

**Deux dates portent un rattrapage administratif** et non de vraies
notifications : le 22 juillet (+272 cas) et le 30 juillet (+172). Elles sont
codées en dur dans `RATTRAPAGE_ADMIN` (`app.js`), avec ce que chacune rattrape.
Seul le 22 juillet garde sa teinte distincte une fois agrégé — le 30 juillet
nomme ses journées, et la semaine comme le mois les contiennent.

**Sept bulletins manquent** à l'archive : 003, 029, 043, 045, 063, 075, 076.

**Les vignettes de province tiennent sur deux colonnes des 320 px.** Elles
s'empilaient sur une seule colonne sous ~420 px — 1 018 px de haut a 375 px,
soit 23 % de la page d'accueil — parce que la grille demandait 180 px minimum
par carte et qu'un ecran de 375 px n'offre que 335 px de contenu. Deux
colonnes ramenent le bloc a 611 px et la page de 4 339 a 3 932 px.

La raison n'est pas la place gagnee, c'est la **comparaison** : ces six cartes
n'existent que pour situer les provinces entre elles, et l'Ituri contre le
Nord-Kivu — 4 655 contre 728 — se lit d'un coup d'oeil quand les deux sont
cote a cote. Le site adoptait deja cette disposition des 430 px ; les
telephones etroits en heritaient d'une autre par accident de seuil.

**LA CHRONOLOGIE MARQUE LA 10e, 20e, 30e… ZONE TOUCHEE — JAMAIS UNE ENTREE
PAR ZONE.** Demande du proprietaire le 27 aout : voir la propagation zone par
zone. Une entree par arrivee aurait fait 60 lignes sur 32 dates, noyant les
jalons rediges ; le 29 mai seul en aurait apporte sept. `zone_milestone_events`
produit donc un jalon par seuil de `ZONE_MILESTONES` (10, 20, 30, 40, 50, 75,
100), de type `spread` comme les arrivees de province, dont le texte nomme les
zones arrivees le jour du franchissement, groupees par province — cinq entrees
au SitRep 103. Le compte est celui des zones DISTINCTES ayant declare au moins
un cas dans un bulletin, cumule dans l'ordre de `zones-history.json` : une
zone touchee le reste, meme ramenee a zero ensuite (Bambu), c'est le sens que
les bulletins donnent a « zones touchees ». Il tombe sur 58, le chiffre
officiel du jour.

Trois pieges, tous traites dans la fonction :
- **Le 21 mai n'est pas une arrivee de dix zones**, c'est le premier bulletin
  a publier un tableau par zone. Son texte le dit autrement
  (`timelineMilestoneZonesFirstText`).
- **Une meme zone ecrite de deux facons** — « Gety » le 29 mai, « Gethy »
  le 9 aout, « Makiso-Kisangani » avec une double espace — se rapproche du
  fond de carte : cle exacte d'abord, puis a deux caracteres pres DANS LA
  MEME PROVINCE, le plus proche gagnant s'il est seul a cette distance
  (« gety » est a 1 de « gethy » et a 2 de « rethy », autre zone de l'Ituri).
  Aru et Adi, voisines a deux lettres, ont chacune leur cle exacte et ne se
  melangent pas. Sans ce rapprochement le compte donnait 60, puis 59.
- **Le nom affiche est celui du dernier bulletin** (`latest.json`) quand la
  zone y figure — « Nia-Nia » comme dans les tableaux du site, pas le
  « Nia Nia » ou le « BAMBU » de la premiere mention.

Le titre porte le seuil (« 20 zones »), le texte le compte exact du jour
(« 22 zones … ») : meme convention que les jalons de cas, dont le titre dit
« 1 000 cas » quand le bilan du jour en dit 1 003.

**Un carrousel horizontal a ete propose puis ecarte.** La chronologie peut
defiler parce qu'elle est sequentielle ; six provinces ne se lisent pas dans
un ordre impose, et ce qui sort de l'ecran n'est pas lu — les quatre dernieres
provinces auraient disparu, alors que leur presence dit a elle seule que
l'epidemie touche six provinces. Deux carrousels sur une meme page se genent
aussi : on ne sait plus ce qui bouge lateralement.

**L'apercu de chronologie de l'accueil tient six jalons, et il faut deux
fleches pour les atteindre.** Il en montrait quatre, soit 928 px : sur un
ecran de 1920 px la piste dispose de 1 332 px, il restait donc **404 px de
vide a droite**. Six cases font 1 392 px — le vide disparait et le leger
debordement signale qu'il y a une suite. Sur mobile le defilement passe de
840 a 1 260 px. Ce sont les six **premiers** jalons, dans l'ordre : l'apercu
raconte le demarrage, « Toute la chronologie » mene au reste. Une selection
etalee sur toute la periode a ete essayee puis ecartee le 25 aout — sauter
d'avril a aout en six cases donne l'impression d'une chronologie trouee, et
l'accueil porte deja l'etat present plus haut (carte, compteurs, graphique).

La piste **defilait deja** mais personne ne pouvait s'en servir sur
ordinateur : macOS pose des barres en superposition qui n'apparaissent qu'en
cours de geste, et une souris a molette verticale n'a aucun axe horizontal.
D'ou deux fleches, activees par `initTimelineScroller()` dans `app.js` et
affichees sous `@media (pointer:fine)` seulement — au doigt le geste suffit.
Elles sont `hidden` dans le HTML et revelees par le script : sans JavaScript,
un bouton mort serait pire que pas de bouton. En bout de course elles
s'estompent au lieu de disparaitre, sinon la piste sauterait sous le curseur.
Aucune phrase n'accompagne la piste : `timelineScrollHint` a ete affichee une
journee puis **supprimee**, avec son style et sa cle. Elle disait ce que le
dessin montre deja — sur toutes les largeurs de telephone courantes, la case
suivante est coupee au bord droit et il en reste 52 a 86 % de visible, jamais
une coupure pile qui ferait croire la piste terminee ; sur ordinateur les
fleches tiennent ce role. Et l'accessibilite etait deja couverte sans texte
visible : la piste porte `role="region"` et l'etiquette « Chronologie de
l'epidemie, defilement horizontal ». Regle a retenir pour ce depot : **ne pas
ecrire ce que la mise en page montre**, et verifier la coupure avant de
conclure qu'elle se voit.

**Un chiffre ecrit dans `strings.json` ne se met jamais a jour.** La legende
de la carte annoncait « Les 464 zones sans cas rapporté restent en gris »
quand la carte en dessinait 462 : le total etait juste a 55 zones touchees et
n'a plus bouge depuis. Retire le 25 aout — le gris se comprend sans legende,
et un chiffre qu'aucun script ne recalcule finit toujours par mentir. Deux
autres survivent, sans consequence : `provincesTableIntro` parle de « 55 zones
touchées » en FR et EN, mais **cette cle n'est referencee nulle part**.

**Les captures d'écran des graphiques sont instables** : ils s'animent au
chargement et se redessinent hors écran. Interroger le canevas
(`chart.options.animation = false; chart.update('none'); canvas.toDataURL()`)
plutôt que faire une copie d'écran de page.

**Le format a change une CINQUIEME fois au SitRep 102, sur une seule ligne.**
La table de repartition par province etait la, lisible, ses six provinces
reconnues — mais le pipeline s'est arrete sur « Table de repartition par
province introuvable ». En cause, la ligne « Total » seule : pdfplumber a
rejete sa cellule « 58/151 (38,4 %) » sur les lignes qui l'encadrent.

```
58/151 (38,4
Total 5 656 2 715 48,0% 72
%)
```

`PROVINCE_SUMMARY_ROW_RE` exige cette fraction de zones — c'est elle qui
empeche le motif de mordre sur les autres tableaux du document. Sans total,
`parse_province_summary_from_text()` renvoie `(None, None)` et le script leve
une `ValueError`. **Il a echoue proprement** : `data/` intact, le site est
reste sur le bulletin precedent — c'est le comportement voulu.

Corrige par `PROVINCE_TOTAL_ROW_RE`, un motif dedie a cette seule ligne. Il ne
relache pas la garde : « Total » en tete est deja tres specifique, et les deux
cumuls, la letalite et **un unique** nombre en fin de ligne restent exiges — la
ligne Total du tableau detaille, qui en porte quatre (« 72 18 17 35 »), ne peut
pas correspondre. La fraction de zones n'est de toute facon pas conservee :
`total_row` la stocke deja a `None` et elle est recalculee depuis la somme des
provinces.

**Le meme bulletin a fait juger 50 lignes de zone « non fiables »** contre zero
au 101 — et pourtant les 58 zones sont sorties exactes, verifiees une par une
contre le PDF. Le repli sur le texte brut fait son travail ; le compteur de
lignes ecartees mesure la deformation du tableau, pas la qualite du resultat.
Il reste un signal a recouper, jamais un verdict.

**Le format a changé une SIXIÈME fois au SitRep 104 : les nouveaux cas sont
passés en deuxième colonne du tableau des provinces.** Jusqu'au 103, l'ordre
était nom, cas, décès, létalité, zones, nouveaux cas ; le 104 écrit
« Ituri 52 4802 2 159 45,0% 28/36 (77,8 %) ». La lecture par position de
`parse_province_summary()` — cas en `row[1]`, décès en `row[2]`, nouveaux cas
en `row[-1]` après retrait des cellules vides — a produit **sans aucun
avertissement** 52 cas confirmés en Ituri, 4 802 décès, 2 836 778 nouveaux
cas (la fraction de zones lue comme un entier) et 481 nouveaux cas nationaux
(la létalité « 48,1% » de la ligne Total, dont la cellule nouveaux cas est
vide). Ni repli, ni ligne jugée non fiable : le tableau était propre, seul son
ordre avait changé. C'est le cas d'école de la synchronisation en pause.

Depuis le 28 août, `roles_entete_resume()` lit l'en-tête du tableau (fusion
des lignes d'en-tête colonne par colonne, puis un rôle par colonne :
province, nouveaux cas, cas, décès, létalité, zones) et
`nouveaux_cas_en_tete()` décide : si les nouveaux cas précèdent les cas
cumulés, `parse_province_summary_par_entete()` lit chaque cellule **par
l'index de son en-tête, sur la ligne brute** — la ligne Total garde sa
cellule vide à sa place au lieu de se décaler. Sinon la lecture par position
est inchangée : vérifié sur les 67 bulletins où pdfplumber trouve le tableau,
68 lignes de province identiques à `province-history.json`, seul le 104
détecté. La ligne Total est rendue dans l'ordre historique parce que l'aval
la lit par position (`prov_total_row[1]`, `[2]`, `[3]`, `[-1]`) ; le total
national de nouveaux cas vient alors de la ligne Total du tableau détaillé,
qui le porte en clair (81).

À relire après chaque nouveau bulletin, tant que la synchronisation est
manuelle : **les six lignes de province de `latest.json` contre la page 2 du
PDF**, cas et décès. `check_coherence.py` l'aurait signalé en bout de chaîne
(somme des provinces contre le national : 81 pour 5 794), mais après que
`province-history.json` avait déjà reçu la ligne fausse du 26 août — le
contrôle arrête la publication, il ne répare pas l'historique, que seule une
nouvelle exécution d'`update_data.py` rafraîchit (c'est ce qui a été fait).

**Le SitRep 105 (27 août) superpose deux tableaux dans son PDF.** Ses pages 4
et 5 impriment le tableau des alertes PAR-DESSUS une seconde copie du tableau
des zones : le texte extrait y est illisible (« Alertes vér(Sifwiaébe+)s »,
« Itu0r i 89,9 % », « Kyondo 76169 vus su1r2 28 3727 »). Mais chaque couche a
sa police et son corps : `texte_par_couches()` dans `scripts/textes_pdf.py`
regroupe les caractères par (police, corps) puis par ligne, et chaque couche
redevient lisible — la phrase des contacts sort intacte de l'ArialMT 10,6
(« 24 769 vus sur 28 372 à suivre », cinq provinces), les lignes du tableau
des alertes de l'ArialMT 10,1 (six provinces, neuf nombres chacune, reçues =
vivants + décédés). Les scripts des contacts et des alertes n'y recourent
qu'en repli, quand la lecture ordinaire échoue ; pour les alertes, seulement
à partir du 087, premier bulletin à porter le tableau par province — appliqué
aux 084-086 il lisait 948 validées sur 1 141 reçues, leurs colonnes ne sont
pas celles-là. Le texte par couches n'est pas dans l'ordre de lecture : il ne
sert qu'aux motifs qui n'en dépendent pas.

Le même bulletin a fait tomber deux hypothèses du pipeline, toutes deux
corrigées le 29 août :

- **La section des zones n'avait plus de borne de fin.** `get_zone_section_text`
  la cherchait au titre « Situation des alertes notifiées » ou « Suivi des
  indicateurs aux PoE/PoC » ; sans l'un des deux, elle renvoyait `None`,
  aucune zone n'était lue, `latest.json` partait avec zéro zone et
  `zones-history.json` restait au 104 — sans autre message que « pas de
  détail par zone exploitable ». D'autres titres sont acceptés, et à défaut
  la section s'arrête à la ligne « Total » qui clôt le tableau des zones —
  ce qui, ici, laisse dehors la copie corrompue de la page 4.
- **La grille pdfplumber du tableau des provinces a éclaté sa ligne Total** :
  « 5 863 » et « 48,2% » sur une ligne, « 2 824 » seul sur la suivante, et
  une colonne vide intercalée avant « Zones de santé » (la fraction en
  colonne 5, l'en-tête en colonne 6). `parse_province_summary_par_entete`
  rattache les lignes de continuation à la précédente et lit la colonne
  voisine sans en-tête quand la cellule attendue est vide. Sans cela :
  décès nationaux `None`, zones par province `None`.

Et une troisième, plus ancienne : **une entrée de la liste des rapports dont
les cas avaient été lus mais pas les décès n'était jamais reprise** — seul
l'échec des cas déclenchait une relecture. `sitreps.json` gardait
« 5863/None » pour le 27 août et `check_coherence` bloquait. La relecture
vaut désormais aussi pour les décès, avec un drapeau
`deathsExtractionFailed` pour ne pas retenter à chaque run les bulletins qui
n'en publient pas. Effet de bord, assumé : quatre-vingts anciennes entrées
ont été relues une fois, et **deux points de `sitreps.json` ont changé** —
le 19 mai reçoit ses 4 décès (le SitRep 004 les imprime, « Total 33 4 ND »,
contrairement à ce que ce guide affirmait plus haut), et le 5 août passe de
1 850 à 1 851 décès : le SitRep 083 écrit 1 851 dans son tableau des
provinces et 1 850 dans sa bande de chiffres clés et son tableau détaillé.
Le site lit le tableau des provinces pour toutes les dates ; il le fait
maintenant aussi pour celle-là.

**Le SitRep 106 (28 août) a numéroté et renommé ses tableaux** : « Tableau 1.
Répartition des cas et décès confirmés par province touchée », « Tableau 2.
Répartition des cas et décès confirmés par province et zone de santé, au
28 août 2026 », « Tableau 3. Situation des alertes notifiées par province ».
Trois endroits d'`update_data.py` cherchaient le titre du tableau des zones
par comparaison exacte, sensible à la casse (« Cas et décès confirmés par
province et zone de santé ») ; aucun ne le trouvait plus. Même symptôme
qu'au 105, autre cause : « pas de détail par zone exploitable »,
`latest.json` sans zone, `zones-history.json` figé au 105 — et rien d'autre
ne bronchait, puisque les provinces et le national se lisaient bien.
Corrigé le 30 août : `find_zone_section_start()` cherche le cœur du libellé
sans égard à la casse ni à ce qui le précède, et sert aux trois lecteurs
(`parse_province_summary_from_text`, `extract_zone_detail_rows`,
`get_zone_section_text`). Second effet du même bulletin : la grille
pdfplumber lit de nouveau le tableau des zones (61 lignes, là où le 105 ne
rendait qu'une table PoE), et elle coupe « Makiso-⏎Kisangani » ; recollé par
un tiret, cela donnait « Makiso--Kisangani », zone jamais vue — la
recomposition n'ajoute plus de tiret quand la coupure en porte déjà un. Les
60 zones ont été relues une par une contre les pages 2 et 3 du PDF, ainsi
que les alertes (2 025 reçues, 1 639 vérifiées, 395 validées), le
laboratoire (82 positifs = 82 nouveaux cas), les CTE et les contacts
(84,4 %, 21 109 vus sur 25 015) : les autres extracteurs ont lu le 106 sans
retouche. Reste non lu, et déjà vrai avant : la phrase du Bas-Uélé sous
« Continuité des soins » (« 1 patient confirmé est en cours de soins pour
3 lits disponibles »), qui n'a pas la forme « N patients sont hospitalisés
pour M lits » attendue par `extraire_cte.py`. Les scripts d'inspection
`inspect_province_summary.py`, `inspect_zone_section.py` et
`scan_province_summary.py` gardent l'ancien libellé exact : ils ne sont pas
dans le pipeline, mais ils ne verront pas le tableau du 106 tel quel.

**Les outils de `scripts/verif/` et `audit_mobile.mjs` pointaient en dur sur
un Chrome Windows** (`C:/Program Files/Google/Chrome/…`), et la machine n'a
que Brave. Depuis le 30 août, `CHROME` dans l'environnement l'emporte, et à
défaut le chemin dépend de la plateforme : Brave sur macOS, Chrome ailleurs.
`visuel_evolution.mjs`, écrit sur le Mac, avait déjà Brave. Second
obstacle sur la même machine : ces scripts utilisent `WebSocket` en global,
qui n'existe qu'à partir de Node 22 — sous Node 20.20, lancer avec
`node --experimental-websocket scripts/verif/capture_page.mjs …`, sinon
`ReferenceError: WebSocket is not defined`. **Et ce plantage laisse un Brave
headless orphelin** : le script a déjà lancé le navigateur sur son port fixe
(9371 pour `capture_page`) quand il tombe, et ne le tue pas. Les lancements
suivants échouent à prendre le port, se raccordent à l'ancienne instance,
et celle-ci sert les pages déjà vues **depuis son cache** — le 5 septembre,
dix-huit instances traînaient, et la page /rapports/ se capturait avec un
CSS vieux de vingt minutes pendant que /en/reports/, jamais visitée par
l'orphelin, sortait juste. Symptôme : une capture qui contredit une sonde
DOM. Remède : `pkill -f 'headless=new.*remote-debugging-port=93'` (les
instances de `scripts/verif/` seulement, jamais le Brave du propriétaire).

**Dans une ligne de zone rendue par pdfplumber, `None` n'est pas une
cellule vide.** C'est une colonne absente de la grille, intercalée au
hasard de la mise en page. Le SitRep 107 rend la queue de Wamba
`['', None, None, '', None, '1', None, None, '1']` : l'index fixe de
`parse_zone_day_columns` tombait sur les `None`, le recoupement
comm + intra = total échouait, et le repli texte lisait « 1 1 » comme un
nouveau cas suivi d'un total — le Haut-Uélé sommait 8 nouveaux cas pour 7
déclarés, et Wamba affichait +1 pour un jour sans cas. Corrigé le 31 août :
le chemin grille écarte les `None` avant de tester les positions, le
recoupement reste exigé. La cellule vide `''` de Wamba dit alors zéro
nouveau cas, et 0 + 1 = 1 se recoupe. Le texte brut, lui, reste ambigu par
nature sur ces queues à deux nombres — c'est la grille qui tranche.

**Le libellé « Total » du tableau des provinces peut tomber seul sur la ligne
suivante.** Le SitRep 110 (1ᵉʳ septembre) rend la ligne Total du tableau 1 en
deux lignes de texte : « 64 6 250 3 039 48,6% 60/151 (39,7 %) » puis
« Total ». Les six provinces passaient, le total non, et le pipeline
s'arrêtait proprement sur « Table de répartition par province introuvable ».
Corrigé le 3 septembre : `recoller_total_orphelin()` recolle un « Total »
isolé à la ligne de chiffres qui le précède (ou le suit), à la seule
condition que la ligne recollée corresponde à l'un des deux motifs du tableau
résumé — un « Total » d'un autre tableau ne peut pas s'accrocher à n'importe
quelle suite de nombres. Le chemin grille, lui, ne voit plus ce tableau depuis
le 106 : sa première ligne est le titre « Tableau 1. … », et
`extract_province_summary` cherche « Province » en `t[0][0]`. La grille du
110 était pourtant propre (en-tête sur une ligne, colonne « Nouveaux cas »
en double mais vide) ; le remettre en service demanderait de sauter la ligne
de titre et de vérifier que `roles_entete_resume` supporte la colonne en
double. Non fait, le repli texte suffit et il est vérifié.

**Le tableau des zones porte QUATRE colonnes de jour, pas trois.** Apres la
letalite viennent : nouveaux cas, deces communautaires, deces intra-CTE, puis
un **total** des deces. Ce total etait ignore, et `zone_row_to_dict()` lisait
les colonnes par position. Or le PDF **n'imprime pas la cellule vide** quand
une zone n'a de deces que dans une seule des deux categories : la lecture
tombait alors sur le total en croyant lire l'intra-CTE, et « 3 deces
communautaires » devenait « 3 communautaires + 3 intra-CTE ». Le site publiait
le double sur neuf zones sur dix — Bunia (+6) pour 3 deces reels au SitRep 101,
le Nord-Kivu repartissant 16 deces sur trois zones quand la province en
declarait 8. Corrige le 25 aout : **le total fait foi**, il est la seule valeur
que le bulletin imprime toujours (`parse_zone_day_columns()`, champ
`newDeaths24h`). La ventilation communaute / CTE n'est renseignee que si la
ligne la donne sans ambiguite, `None` sinon — un des deux compteurs porte le
total, on ne sait pas lequel, et on ne devine pas. Les lignes de **province**,
elles, ont toujours ete justes : `PROV_SUBTOTAL_RE` capture les quatre valeurs.

Depuis le 3 septembre, une deduction ferme le trou sans deviner :
`ventiler_par_soustraction()` retranche des communautaires de la ligne de
province ceux des zones lues sans ambiguite, et attribue le reste aux zones
ambigues — seulement si le compte tombe juste (une seule zone ambigue dont
le total peut l'accueillir, ou plusieurs toutes a zero ou toutes au total).
Le calcul ne passe que par la colonne communautaire, parce que les lignes
« A ventiler », non conservees, ne portent que de l'intra-CTE. Sur le 110 :
Rwampara 2 communautaires (13 - 11), Beni 3 (12 - 9), zero intra-CTE pour
les deux, confirme par le proprietaire contre le PDF.

Deux consequences a retenir. **Ne jamais additionner `deathsCommunity24h` et
`deathsIntraCTE24h`** : passer par `zone_new_deaths()` cote generateur,
`fmtCfr`/`newDeaths24h` cote `app.js`. Et le controle qui manquait est
desormais dans `check_coherence.py` : *nouveaux deces des zones <= province*.
Inegalite large, car les lignes « a ventiler » restent hors des zones — ce qui
en fait un filet a trous : sur l'Ituri, ou 250 deces attendent leur zone, un
doublement passerait encore inapercu. Il attrape le Nord-Kivu et le Haut-Uele,
qui n'ont pas de reserve.

**Les annotations `X | None` cassent sur le Python de la machine.** Le seul
interpréteur disponible est 3.9.6, où PEP 604 n'existe pas : une signature
`def f() -> str | None` lève `TypeError: unsupported operand type(s) for |` à
l'import, avant la moindre ligne exécutée. `download_all_sitreps.py` en portait
trois — corrigé le 25 août par `from __future__ import annotations` en tête de
fichier, qui rend toutes les annotations paresseuses sans rien réécrire. Le
workflow GitHub ne l'avait jamais vu : il tourne sur un Python plus récent.
Vérifier ce point sur tout script repris d'ailleurs.

**Sous Windows, `sys.stdin` décode en cp1252.** Un motif contenant un accent ne
correspondra pas au HTML lu sur l'entrée standard.

---
