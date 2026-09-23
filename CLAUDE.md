# ebola-tracker.org — guide du dépôt

Site public de suivi de la **17ᵉ épidémie d'Ebola en RDC** (espèce Bundibugyo,
déclarée le 15 mai 2026). Il compile les bulletins officiels de l'INSP et les
rapports hebdomadaires de l'OMS. Trilingue FR/EN/SW, statique, servi par GitHub
Pages sur `ebola-tracker.org` depuis la branche `main`.

Dernier bulletin intégré à la rédaction de ce guide : **SitRep 130**, rapportage
du 21 septembre 2026 (publié le 22) — 7 773 cas confirmés, 3 759 décès,
létalité 48,4 %, 1 935 guéris, 839 patients en isolement/CTE, 63 zones touchées
sur 167 dans 7 provinces (aucune nouvelle), **40 nouveaux cas** (Ituri 19,
Nord-Kivu 13, Haut-Uélé 5, Tshopo 3) et 27 décès du jour (14 communautaires,
13 intra-CTE), suivi des contacts à 84,5 %. **Les 129 et 130 ont été intégrés
ensemble le 23 septembre 2026**, résumés des Défis rédigés pour les deux
(121 et 119 mots).

**DEUX BULLETINS D'UN COUP : `update_data` NE RETRAITE QUE LE PLUS RÉCENT.**
Le 129 était absent de `zones-history` et de `province-history`, qui sautaient
du 19 au 21 — alors que son PDF porte bien ses deux tableaux, vérifié. Rattrapé
par `backfill_zones_history` puis `backfill_province_history`, avec diffusion
avant/après : une seule date ajoutée, aucune autre valeur touchée, aucune
orthographe de zone changée. **Le réflexe à garder : après une intégration
multiple, compter les dates des historiques avant de publier.**

**La lettre du 129 n'existait pas non plus**, même cause — `_instantanes()` ne
fige que le dernier. Reconstruite en faisant repasser le pipeline à sa date,
`SITREP_MVE_130.pdf` écarté le temps d'une génération, puis remis. La lettre
est donc exactement celle qu'un traitement à la date aurait produite (122
rapports listés, Ituri à 5 947). Effet de bord **bienvenu** de l'aller-retour :
`sitreps.json` récupère les **1 902 guéris du 20 septembre**, que le traitement
en position non-dernière n'avait pas lus. Un seul fichier de `data/` modifié
par l'opération, et c'est ce gain.

**`check_coherence` sort avec DEUX ÉCARTS BLOQUANTS, tous deux imputables à la
source, publiés en l'état le 23 septembre 2026 :**
- **`vaccination : le cumul ne recule jamais` — 129 Bas-Uélé (874 après 987).**
  Le 128 publie « 987 dont 550 Buta, **324 Ganga**, 71 Poko, 42 Viadana », le
  129 « 874 dont 550 Buta, **211 Ganga**, 71 Poko, 42 Viadana ». Une seule zone
  bouge, chaque total tombe juste sur sa propre ventilation : la source s'est
  corrigée sur Ganga. Voir « Un cumul ne recule pas » ci-dessous.
- **`cte : taux publié = normés / lits` — 130 Nord-Kivu.** Le bulletin écrit
  « 338 hospitalisés dont 274 dans les structures normées pour 308 lits, soit
  66,2 % » — or 274/308 fait 89,0 %. Les 128 et 129 étaient cohérents (95,6 %
  et 91,2 %). C'est le jour où le CTE de Matanda ouvre à Katwa : la capacité a
  probablement bougé sans que le nombre de lits suive. Le site garde les deux,
  `occupationPubliee` et la série à définition constante.
  **Ni l'un ni l'autre n'est encore inscrit en « écart connu » — à trancher.**
  Mais **le saut de capacité qui va avec est désormais nommé dans la note du
  graphique** : le Nord-Kivu passe de 228 à 308 lits le 21 septembre, sa courbe
  tombe de 138,6 à 109,7 % pendant que les patients montent de 316 à 338, et
  `chartNoteCteCapacite` le dit en toutes lettres, calculé. Détail dans la
  skill `page-riposte`.

**UN CUMUL NE RECULE PAS : LE GRAPHIQUE DE VACCINATION PORTE LA VALEUR
RÉVISÉE** (23 septembre 2026, décision du propriétaire). Tracée telle quelle,
la courbe du Bas-Uélé redescendait de 987 à 874 — et lissée, la chute se lisait
comme une décrue progressive qui n'a jamais eu lieu. La correction de la source
est donc appliquée rétroactivement à sa propre série : le 19 septembre porte
874. Une première version sortait le point du tracé et le laissait en cercle
creux à 987 ; écartée le jour même — deux chiffres pour un même jour se
contredisaient à l'œil, et la note suffit. Le test est **générique**, la série
relue à rebours : tout cumul supérieur à un relevé postérieur est ramené à la
valeur retenue ensuite, et la note nomme date, province et les deux chiffres,
tous calculés. Détail sous « Le graphique » ci-dessous.

**Le 130 se contredit aussi dans ses Défis** : il écrit « 34,2 % des patients
hospitalisés hors structures normées » quand sa propre phrase de prise en
charge donne 64/338 = 18,9 %. Le 34,2 % est recopié du 129. Le résumé de la
lettre reprend le chiffre publié — règle du miroir.

**Le suivi des contacts tombe à 79,9 %**, sous le seuil de 85 % que l'INSP s'est
fixé, après cinq jours passés au-dessus. Le précédent décrochage datait du
13 septembre (78,6 %), lui aussi isolé entre deux séries hautes.

**La vaccination s'étend au Bas-Uélé** : deux zones de santé entrent dans la
campagne, **Poko** (71 vaccinés) et **Viadana** (42), où la vaccination
compassionnelle vient de démarrer, et Ganga passe de 158 à 324. La province
atteint 987 vaccinés, la Tshopo 3 576 (30,6 % de sa cible), soit **4 563 au
total** et dix zones de santé au tableau du cadre 05. **L'Ituri a tenu son
lancement officiel** au Grand Laboratoire de Bunia avec l'appui de MSF : elle
n'a pas encore de chiffre, mais sera la troisième province à vacciner. Le stock
de doses décongelées de la Tshopo descend de 631 à **424**, toujours à échéance
du 24 septembre.

**La lettre donne désormais le chiffre du jour de la vaccination**, à la
demande du propriétaire (21 septembre 2026) : « Depuis le bulletin précédent,
207 de plus dans la Tshopo et 279 de plus dans le Bas-Uélé, en deux jours. »
Le bulletin ne publiant **que des cumuls**, l'écart est dérivé du cumul
précédent de chaque province, et deux garde-fous étaient nécessaires. Une
province qui saute un bulletin donne un écart portant sur plusieurs jours : la
lettre l'écrit en toutes lettres (« en deux jours », « en onze jours » au 125,
qui enjambe la rupture de stock du Bas-Uélé). Et surtout, **une province
n'apparaît que si elle publie un cumul neuf ce jour-là** — sans cette
condition, le cumul reporté faisait réapparaître le même écart d'une lettre à
l'autre, et les 108 du Bas-Uélé du 17 septembre s'affichaient dans la lettre
126 *et* dans la 127.

**Ce que la nouvelle zone a demandé : rien.** Contrairement au Sud-Ubangi du
119, Dungu est dans une province déjà touchée, et le fond de carte OCHA la
porte sous le nom exact « Dungu » en Haut-Uélé : correspondance exacte sur la
clé normalisée, aucun alias à ajouter, la zone se colorie. `update_data`
l'a signalée comme « zone jamais vue dans aucun rapport antérieur, à vérifier
manuellement » — c'est le garde-fou qui fonctionne, et la une du bulletin
confirme : « Une nouvelle zone de santé a été touchée au cours des dernières
24 heures, notamment celle de Dungu dans la province du Haut-Uélé ». Elle
entre avec 1 cas, 1 décès, et sa ventilation du jour est déduite de la ligne
de province (1 décès communautaire).

**La page Riposte a une partie « La vaccination »** (21 septembre 2026),
en **cadre 05**, entre les centres de traitement et le lieu du décès — qui
passe en 06. Elle ferme la chaîne de la riposte : signaler, tester, suivre,
soigner, prévenir. C'est le seul pilier qui devance l'épidémie au lieu d'y
réagir.

**Ce que le cadre porte**, après trois tours de maquettes montrées en local :
un paragraphe unique qui dit qui est vacciné, le chiffre d'ensemble
(4 077 personnes), un graphique du cumul par province, un tableau par zone de
santé dans son propre cadre, et la note. Pas de couverture de la cible, pas de
stock de doses, pas d'état des provinces qui ne vaccinent pas encore : écartés
par le propriétaire, qui a recentré la partie sur **l'évolution** — qui est
vacciné, combien, quand et où.

**Le graphique : deux courbes non empilées, une par province.** L'aire empilée
essayée d'abord écrasait le Bas-Uélé (708 contre 3 369) et déformait sa
trajectoire, puisque dans un empilement seule la couche du bas a une base
plate. Séparées, les deux provinces redeviennent lisibles et le **palier de
onze jours du Bas-Uélé** — la rupture de stock d'Ervebo à Buta, du 5 au
16 septembre — se lit franchement. Chaque courbe porte son nom et son dernier
chiffre en bout, pour éviter l'aller-retour vers la légende. Le tracé est
**progressif** : l'escalier, plus fidèle aux relevés, a été essayé puis écarté
par le propriétaire.

**UN CUMUL NE RECULE PAS : LA COURBE PORTE LA VALEUR RÉVISÉE** (23 septembre
2026). Le 19 septembre le bulletin donne 987 vaccinés au Bas-Uélé, le lendemain
874 — une seule zone bouge, Ganga, de 324 à 211, les trois autres sont
identiques, et chaque total tombe juste sur sa propre ventilation. Personne
n'est dévacciné : c'est la source qui se corrige, et le tableau par zone de la
page affiche déjà 211. La correction est **appliquée rétroactivement à la
série** — le 19 septembre porte 874 —, comme le fait toute donnée de santé
publique révisée.

**Une première version a été montrée puis écartée le jour même** : elle sortait
le point du tracé et le laissait en cercle creux à 987, avec son entrée de
légende « Valeur révisée ». Deux chiffres pour un même jour se contredisaient à
l'œil, et la note suffit. La clé `vaccChartRevisee` a été supprimée avec elle —
**ne pas la refaire sans que le propriétaire le redemande.**

Le test est **générique**, jamais codé en dur sur une province : la série est
relue à rebours, et tout cumul supérieur à un relevé POSTÉRIEUR est ramené à la
valeur retenue ensuite. La note se recompose avec date, province, valeur
publiée et valeur retenue, toutes calculées (`vaccChartRevision`, trois
langues) — écrite en dur elle se périmerait au relevé suivant.

Piège rencontré : `boutsDeCourbe` étiquette tous les jeux, et l'étiquette de la
série retirée chevauchait celle du Bas-Uélé. Un jeu peut désormais refuser son
étiquette de bout avec `sansBout: true`.

**Deux plats qui ne disent pas la même chose, et le graphique doit les
distinguer.** Entre le **28 août et le 2 septembre, aucun chiffre n'est
publié** : la marche du 3 septembre est un rattrapage de publication, pas une
flambée de vaccinations en un jour. Un plugin `plageSansDonnees` grise cette
plage et l'étiquette « aucun chiffre publié ». Le palier du Bas-Uélé, lui, est
un arrêt réel et n'est pas grisé. Sans cette distinction, les deux se
lisent pareil et le graphique ment. La note sous le graphique le redit en
toutes lettres.

**Le tableau par zone de santé** est dans un cadre séparé, resserré à 376 px :
huit lignes, de Makiso-Kisangani (1 830) à Ganga (158). Des effectifs, pas des
taux — aucune cible par zone n'est publiée. La date n'y figure plus ligne par
ligne (décision du propriétaire) : c'est la légende qui dit que chaque province
est à son dernier relevé publié. **Le Bas-Uélé est donc au 17 septembre**, pas
au 18, faute de publication le dernier jour.

**Ce qui a été écarté en chemin, et pourquoi**, pour ne pas le réessayer :
- **Des barres du flux quotidien par zone** : les cumuls par zone reculent une
  fois (Mangobo passe de 368 à 352 le 16 septembre, la source se corrige) et
  une barre négative n'a pas de sens.
- **Un empilement par zone de santé** : huit couches demandent huit teintes
  séparables sur une même rampe, et `validate_palette.js` les refuse — la paire
  la plus claire reste sous le seuil de 15 même en écartant les paliers. Les
  deux couleurs de province, elles, passent tous les contrôles en clair comme
  en sombre (ΔE 18,9 ; #8D7FCC et #CE7A52 en sombre).
- **Des vignettes par zone de santé** (petits multiples) : montrées, puis
  retirées à la demande du propriétaire.
- **Le rythme hebdomadaire** : la seule forme qui montrerait l'essoufflement,
  et où le « Bas-Uélé : 0 » de la semaine du 7 au 13 septembre saute aux yeux.
  Prématuré à trois semaines et demie de données, et la barre de la deuxième
  semaine hérite du rattrapage de publication. **À reprendre vers la mi-octobre**,
  quand il y aura six à huit semaines et trois ou quatre provinces : le mode est
  déjà déclaré dans `RIPOSTE_MODES`, il ne manque qu'un bloc de dessin.

**Deux pièges de câblage rencontrés**, qui resserviront : une clé de texte
destinée au graphique doit aller dans **`assets/js/i18n.js`** et non dans
`site/strings.json` — le premier sert au client, le second au rendu serveur, et
un titre mis au mauvais endroit ne s'affiche jamais. Et le **`footer` de
l'infobulle Chart.js ne se rendait pas** ici : le total des deux provinces est
passé par `afterBody`.

**La vaccination est extraite en détail** (20 septembre 2026, avant toute
décision sur la page Riposte). La campagne Ervebo démarre le 26 août 2026 au
Bas-Uélé (20 PPL à Buta), la Tshopo suit le 27. Au 18 septembre, **deux
provinces sur sept vaccinent** : la Tshopo (3 369) et le Bas-Uélé (708).
L'Ituri lance le 19 septembre à Bunia avec MSF, le Nord-Kivu en est à la chaîne
de froid, le Sud-Ubangi à 300 doses, le Haut-Uélé et le Sud-Kivu à rien. La
cible n'est pas la population : ce sont les **PPL et TPL** (personnels et
travailleurs de première ligne), plus les contacts à haut risque au Bas-Uélé.

Une section **« 1.6. Vaccination »** existe depuis le SitRep 112 (3 septembre)
et figure dans les **seize bulletins suivants sans exception**, sous le même
numéro, avec « Principales actions » puis « Défis » — un ancrage bien plus sûr
que ce qu'on a pour les contacts ou les CTE. `extract_piliers.py` y lit
désormais, par province : `cumul`, `cible`, `couverture`, `zones` (la
ventilation par zone de santé) avec `zonesSomme`, `doses` (congelées,
décongelées, au niveau des zones, déployées, reçues/exprimées, date de
péremption) et `mapi`. Le `cumulParProvince` d'origine est inchangé, donc la
lettre ne bouge pas.

**Trois pièges, et le contrôle qui va avec.** Le **124 recopie la ventilation
du 123** (somme 2 460 pour un cumul 2 544) : d'où `zonesSomme` à côté du cumul,
et un contrôle non bloquant dans `check_coherence` qui le signale — un
graphique qui empile les zones doit savoir qu'il lui manque 84 personnes ce
jour-là. La **cible oscille** — 11 703 au 117, 11 000 aux 118 et 119, 11 703
ensuite — et le taux publié suit la cible citée : on garde les deux nombres
bruts. Le bulletin ne publie **jamais de vaccinés du jour**, seulement des
cumuls (+197, +227, +147, +153, +84, +266, +253, +306) ; le 13 septembre en
couvre deux, le 121 ne disant rien de la Tshopo. Deux autres contrôles ont été
ajoutés : le cumul ne recule jamais (bloquant) et la couverture se recalcule
sur la cible à un demi-point près. **Ce dernier passe de justesse au 117** (14,0
publié contre 13,5 recalculé, 0,48 d'écart) : si la source arrondit encore plus
grossièrement, il faudra desserrer le seuil.

Une tournure à laquelle l'extraction a failli se laisser prendre : la province
**revient dans « Défis » après « Principales actions »**, et au 127 le second
paragraphe (« risque de péremption des 631 doses ») écrasait le premier, qui
portait le cumul. La fusion complète désormais sans jamais écraser.

**Les barres du 17 et du 18 septembre manquaient au graphique des contacts**
(vu par le propriétaire le 20 septembre 2026, corrigé le jour même). Les barres
du graphique de la riposte tracent les contacts *à suivre*, pas le taux : sans
`contacts.aSuivre`, la courbe passe et la barre manque. Les 126 et 127 avaient
leur taux — lu par le repli générique sur « taux de suivi des contacts … % » —
mais ni effectifs nationaux ni provinces, faute de motif. Deux tournures
apprises :
- **Onzième tournure des contacts (126)** : « **Sur les** 31 902 contacts en
  cours de suivi, 27 842 ont été vus au cours des dernières 24 heures, soit une
  proportion de suivi de 87,2% » — « Sur les » à la place de « Parmi les ».
  `CONTACTS_PARMI_LES_RE` accepte désormais les deux.
- **Douzième tournure des contacts (127)** : « Au cours des dernières 24
  heures, 26 803 **ont été vus parmi les** 30 541 contacts en cours de suivi,
  soit une proportion de suivi de 87,8% » — les vus ouvrent la phrase et
  « parmi les » ne vient qu'**après** « ont été vus », ce qu'aucun des deux
  motifs « parmi » ne lisait. Nouveau `CONTACTS_VUS_PARMI_RE`.

Comme les motifs de province ne lisent que le voisinage de la phrase nationale,
les deux dates ont retrouvé du même coup leurs six provinces. Effet de bord
voulu : la case nationale « Contacts vus (7 derniers relevés) » repasse de la
moyenne simple des taux (87,0 %, sans sous-titre) à la moyenne pondérée
(**87,1 %**, 186 691 vus sur 214 289 à suivre), les sept relevés portant de
nouveau leurs effectifs. Régénération complète, aucune autre date touchée.

**La courbe Nord-Kivu du graphique des CTE perdait 16 dates sur 59** (vu par
le propriétaire le 20 septembre 2026, corrigé le jour même). Trois causes, dont
une seule de notre fait :
- **Du 16 au 18 septembre, les lits étaient publiés et nous ne les lisions
  pas.** « 392 patients sont hospitalisés dont 224 dans les structures normées
  **avec une capacité d'accueil de 228 lits**, soit un taux d'occupation global
  de 98,2 % » (127) — `LITS_RE` n'attend que « pour N lits ». Nouveau
  `LITS_CAPACITE_RE`, ancré sur « lits » et non sur « de », parce que le 125
  glisse son numéro de page au milieu : « capacité d'accueil **6** de 228
  lits ».
- **Le taux porte sur les seules structures normées**, pas sur tous les
  hospitalisés : 224/228 font 98,2 %, quand 392/228 en feraient 172. D'où
  `HOSPITALISES_NORMES_RE` et le champ `hospitalisesNormes`, et une fonction
  `numerateur()` dans `extraire_cte.py` — le même numérateur sert au contrôle
  par province, au cumul `hospitalisesAvecLits`, à `check_coherence`, au
  sous-titre de la page province et à l'infobulle du graphique. Sans ça,
  ajouter les 228 lits déclenchait un écart bloquant et faussait le KPI
  national.
- **Du 10 au 15 septembre, la source ne publie aucun dénominateur** — « 311
  patients sont hospitalisés, soit un taux d'occupation global en sursaturation
  (141,4 %) ». Le filtre de la vue nationale traitait `lits` absent comme 0 lit
  et écartait le point, alors que la page province le traçait : **les deux vues
  jugeaient le même point différemment**. Le seuil porte désormais sur
  l'effectif connu — le dénominateur s'il est publié, les hospitalisés sinon —
  et la même règle vaut dans les deux vues. « Pas de lits publiés » et « moins
  de 20 lits » sont deux choses différentes ; les confondre coûtait au
  Nord-Kivu neuf jours de courbe pour 311 à 403 patients.
- **Les 7-12 et le 29 août (7 dates) sont irréparables** : le Nord-Kivu n'a pas
  de section de prise en charge chiffrée ces jours-là (le 086 ne donne que des
  admissions cumulées, le 107 ne le mentionne pas). Le trou du 7 au 12 août
  fait 6 jours, donc au-delà de `MAX_TROU_CTE` : pas de pointillé, par choix —
  la province passe de 141 à 206 lits pendant ce trou.

Effet mesuré de la règle, vérifié province par province avant de l'écrire : la
vue nationale gagne 6 dates au Nord-Kivu (plus 3 par l'extraction, soit les 9)
et 1 au Sud-Kivu ; les pages province perdent 4 points qui ne voulaient rien
dire — la Tshopo à 5 et 8 patients les 12 et 13 août, le Haut-Uélé à **4**
patients pour 100 % le 19 août, le Sud-Kivu à 19 le 8 septembre. C'est
exactement ce pour quoi le seuil existe. Le KPI national d'occupation passe de
42,8 % à **51,8 %** (731 sur 1 412 lits) : le Nord-Kivu rejoint le cumul, dont
il était absent faute de lits. Les lettres 125, 126 et 127 suivent.

**Le taux du Nord-Kivu change de sens le 15 septembre**, et la note sous le
graphique le dit désormais. **Attention : ce n'est pas le dénominateur qui
change, contrairement à ce que le premier jet de cette note et du commit
`5053475d` affirmaient.** Le nombre de lits ne bouge pas — 228 du 11 au
18 septembre, ce que confirme le dénominateur implicite reconstitué depuis le
taux publié (317/1,390 = 228, 342/1,50 = 228, 348/1,526 = 228). C'est le
**numérateur** qui change : jusqu'au 14, l'INSP rapporte *tous* les patients
hospitalisés à ces 228 lits ; depuis le 15, il ne retient que ceux des
structures normées (216 sur 373). Les 157 malades couchés hors des lits
prévus — ce que le dépassement de 100 % sert précisément à signaler —
sortent du calcul, et le taux tombe de 152,6 % à 94,7 % pendant que le nombre
de patients monte. Le SitRep 127 le dit lui-même dans ses Défis : « 42,9 % des
patients hospitalisés sont pris en charge en dehors des structures normées »
(168/392 = 42,9 %, nos chiffres tombent sur les siens).

**Le site trace donc la série à définition constante** — tous les hospitalisés
rapportés aux lits déclarés — décision du propriétaire le 20 septembre 2026,
après avoir vu la courbe plonger. À définition constante, la saturation
continue de monter : 152,6 % le 14, puis 163,6, 164,9, **176,8** le 17 et
171,9 le 18. Le taux du bulletin est conservé dans `occupationPubliee`, et
`numerateur()` rend désormais toujours le total hospitalisé.

**La capacité du 15 septembre est déduite, et confirmée.** Le SitRep 124 donne
« 216 dans les structures dédiées » et 94,7 % sans jamais écrire le nombre de
lits : 216/0,947 fait 228,1. `confirmer_lits_deduits()` ne retient une
déduction que si le bulletin a imprimé la même capacité à moins de trois lits
près dans les sept jours voisins — le 125 et le 126 impriment 228. Le nouveau
contrôle `check_coherence`, « taux publié = normés / lits là où la province
distingue », vérifie le couple et passe.

**Conséquence sur le KPI national, à surveiller.** L'occupation nationale
passe de 48,3 % le 14 septembre à **64,0 %** le 15 : le Nord-Kivu entre dans le
cumul (il n'avait pas de lits du 10 au 14) *et* y entre avec ses 373 patients.
C'est le défaut de périmètre qui avait fait retirer la ligne « Toutes
provinces » du graphique le 28 août — un cumul qui change de périmètre sans le
dire. Les lettres 124 à 127 portent la nouvelle valeur (64,0 / 62,7 / 64,0 /
63,7 %).

La chaîne `provinceKpiOccupationSubNormes` ajoutée le 20 septembre n'est plus
utilisée : le sous-titre redevient « 392 hospitalisés pour 228 lits », cohérent
avec le taux affiché. Elle reste dans `strings.json` en fr/en/sw.

Relu en local sur la page Riposte avant publication, puis **publié le
20 septembre 2026**.

**Le 6 août et le 7 septembre restent sans barre, et c'est correct.** Le 084 ne
publie aucun effectif (« Le suivi des contacts est à 83,7% », rien d'autre). Le
116 en publie, mais ils se contredisent : 21 359 vus sur 24 719 à suivre font
86,4 %, quand la même phrase imprime 88,3 % — `effectifs_verifies` les rejette
au-delà d'un point d'écart. Ne pas « réparer » ces deux-là.

Le **journal d'integration bulletin par bulletin (SitRep 109 a 126)** — les
tournures apprises, les motifs ajoutes aux extracteurs, les ecarts constates —
vit desormais dans la skill `journal-bulletins` (`.claude/skills/
journal-bulletins/SKILL.md`), chargee a la demande plutot que relue a chaque
echange. A ouvrir avant de toucher a un extracteur ou de reprendre un ancien
bulletin. Les regles durables qui en sont tirees sont restees ici, sous
« Comment l'extraction fonctionne » et « Pieges connus ».

---

## Le principe qui gouverne tout

**Chaque chiffre affiché doit être traçable jusqu'à un PDF de `reports/`.**

Le site est un miroir, pas une source. Il n'invente pas de valeur, ne
réattribue pas un cas d'une province à une autre, ne comble pas un trou par
interpolation. Quand la source ne dit pas, le site ne dit pas — et le dit.

Deux illustrations à connaître, parce qu'elles reviendront :

- Les **décès « à ventiler »** de l'Ituri ne sont répartis sur aucune zone. Ils
  étaient 233 au SitRep 100, 250 au 101, **266 au SitRep 102** : la somme des
  28 zones donne 1 853 décès quand la province en déclare 2 119. L'écart reste visible plutôt
  que comblé, et il grossit à chaque bulletin qui ajoute des décès intra-CTE non
  encore rattachés à une zone. **Depuis le 25 août il est aussi expliqué** :
  `zonesSumNote` accompagne le tableau des zones de chaque page province et
  celui de `/donnees/`. La formulation est volontairement générale — « le total
  d'une province peut différer de la somme de ses zones » — et ne porte **aucun
  chiffre** : un nombre écrit dans `strings.json` ne se recalcule jamais, c'est
  ce qui avait périmé les « 464 zones » de la carte. Elle vaut pour les cas
  autant que pour les décès : l'historique compte 48 dates où la somme des cas
  d'une province ne tombait pas sur son total, et deux dates où la somme
  dépassait le total d'une unité (Ituri le 17 juin, Haut-Uélé le 26 juillet) —
  d'où « peut différer » plutôt que « est inférieure ».
- Les premiers cas du **Haut-Uélé et de la Tshopo**, importés de la zone de
  Nia-Nia, sont restés comptés en Ituri jusqu'au 10 juillet. Le site n'a pas
  corrigé cette attribution : il l'explique.

Corollaire, formulé le 24 août : **les dates dans la prose, les nombres dans
les tableaux.** Une chronologie peut affirmer que le virus a atteint une
province le 25 juin, c'est une affirmation narrative sourcée à une phrase de
bulletin qui n'a besoin de s'additionner avec rien. Les cartes et les
graphiques, eux, restent sur les tableaux officiels.

---

## Le pipeline quotidien

Ordre exact, identique à `.github/workflows/sync-sitreps.yml` :

```bash
python scripts/download_all_sitreps.py       # récupère les nouveaux PDF depuis insp.cd
python scripts/update_data.py                # latest.json, sitreps.json, zones-history, province-history
python scripts/extract_contacts_followup.py  # contacts-followup.json
python scripts/extraire_deces_lieu.py        # deces-lieu.json
python scripts/extraire_alertes.py           # alertes.json      (page Riposte)
python scripts/extraire_laboratoire.py       # laboratoire.json  (page Riposte)
python scripts/extraire_cte.py               # cte.json          (page Riposte)
python scripts/extraire_defis.py             # defis.json        (page Riposte, « Défis » cités)
#   puis, À LA MAIN, le résumé des Défis du bulletin dans data/bulletin-notes.json
#   (fr/en/sw, langage courant) — à chaque bulletin, sans attendre de signal,
#   règle du 9 septembre 2026 ; check_coherence le note s'il manque
python scripts/extract_piliers.py            # piliers.json      (La lettre : EDS, rings, vaccination, PoC/PoE)
python scripts/build_pages.py                # régénère les 30 pages du site
python scripts/check_coherence.py            # contrôle, ne modifie rien
```

**La synchronisation automatique est en pause** depuis le 23 août, à la demande
du propriétaire — le format des SitRep a changé trois fois depuis mai, et une
extraction qui dérape sans témoin publie des chiffres faux. Le n°099 aurait
publié 57 151 377 décès en 24 h si personne n'avait regardé. Le workflow reste
déclenchable à la main depuis l'onglet Actions.

`check_coherence.py` doit sortir **sans aucun écart**. C'est le cas depuis le
24 août — auparavant il en signalait deux « connus de la source ».

### Dépendances

```bash
pip install requests beautifulsoup4 pdfplumber pyshp
```

**L'environnement vit hors du dépôt**, dans `~/.venvs/ebola-tracker` — construit
sur `/usr/bin/python3` (3.9.6, le seul Python de la machine). Il est dehors pour
une raison précise : GitHub Pages sert tout le dépôt, `.gitignore` ne couvre pas
`.venv/`, et un environnement commité deviendrait publiquement téléchargeable.

```bash
source ~/.venvs/ebola-tracker/bin/activate
```

Corollaire d'un `rm -rf` suivi d'un `git clone` : l'environnement disparaît avec
le reste du non-versionné — `data/corpus/`, `tmp/`, `assets/social/`. Les PDF de
`reports/`, eux, sont versionnés et reviennent seuls. Reconstruire coûte une
installation de paquets et deux minutes de corpus.

Plus **Node 20+** dans le `PATH` : `build_pages.py` appelle
`scripts/dump_i18n.mjs` pour lire `assets/js/i18n.js`. Aucun paquet npm, pas de
`package.json`.

`pyshp` ne sert qu'à `build_geo.py`, qui ne tourne pas quotidiennement.

Chrome n'est nécessaire que pour `scripts/audit_mobile.mjs` et les outils de
`scripts/verif/` — neuf scripts qui pilotent Chrome par le protocole DevTools
pour contrôler le site **rendu** plutôt que son code. Voir leur README.

`visuel_evolution.mjs` produit un **visuel a diffuser hors du site** : la
carte de l'accueil cadree sur l'epicentre a N dates regulierement espacees du
premier instantane au dernier (3, 6 ou 9, en grille de trois), chaque
vignette datee avec ses cas et ses zones, une legende commune, la source et
le domaine — l'evolution de l'epidemie sur une seule image. Il capture le SVG
date par date en pilotant le curseur, puis compose une page HTML avec les
polices du site et la photographie. `--dx`, `--dy`, `--zoom` ajustent le
cadre. **Les sorties vont dans `tmp/visuels/`, gitignore** : rien de ce qui
est produit n'entre dans le site.

Le plus utile : `capture_canvas.mjs`, seule façon fiable de capturer un
graphique — ils s'animent au chargement et se redessinent hors écran, une
copie d'écran ordinaire attrape un tracé à moitié dessiné ou un canevas vide.
Et `test_onglets.mjs`, à lancer après toute modification d'`app.js` : il
parcourt les onglets deux fois et rapporte les erreurs console.

---

## Architecture

### Les données (`data/`)

| Fichier | Contenu |
|---|---|
| `latest.json` | l'instantané du dernier bulletin : national, provinces, `healthZones`, `reports`, `timeline` |
| `sitreps.json` | série nationale par date : `confirmed`, `deaths`, `recovered` |
| `province-history.json` | cumul par province et par date — **cas ET décès** ; noms passés par `canon_province()` |
| `zones-history.json` | instantané des zones de santé par bulletin, pour le curseur de temps des cartes |
| `contacts-followup.json` | taux de suivi des cas contacts par date |
| `deces-lieu.json` | décès communautaires vs intra-CTE, par province et par date |
| `demographie.json` | âge × sexe, **figé au 5 août 2026** — l'INSP a cessé de publier cette répartition |
| `health-zones.geojson` | contours des 519 zones de santé, produit par `build_geo.py` |

`community-deaths-daily.json` alimentait un onglet retiré le 24 août. Il ne
valide qu'une province, l'Ituri, alors que son libellé annonçait le pays
entier. **Ne pas le rallumer sans corriger ce défaut.**

**Un nom de province n'entre dans l'historique que par `canon_province()`.**
Les bulletins écrivent tantôt « Haut-Uélé », tantôt « Haut Uélé » : celui du
14 août a produit la seconde forme, et la courbe du Haut-Uélé y perdait son
point en silence, `app.js` cherchant les provinces par leur nom exact dans
`PROVINCE_COLORS`. Un découpage raté avait par ailleurs fait entrer le 19 mai
une « province » nommée « touchées », avec des valeurs nulles. La table
dérive de `PROVINCE_CANON` — une province ajoutée là se retrouve reconnue
ici — et un nom absent est **écarté** plutôt que recopié : mieux vaut une
province manquante ce jour-là, visible comme telle, qu'une septième courbe
fantôme. Les deux entrées déjà écrites ont été corrigées à la main le 26 août,
sans relire les PDF : aucune valeur ne change, seuls deux noms.

### Le générateur

`scripts/build_pages.py` produit **30 fichiers** listés dans
`site/.generated.json`. Il lit :

- `site/pages.json` — les huit pages et leurs besoins
- `site/strings.json` — tous les textes FR/EN du générateur
- `assets/js/i18n.js` — les textes du JavaScript, via `dump_i18n.mjs`
- `site/layout.html` et `site/pages/*.html` — les gabarits

**Ne jamais éditer un `.html` à la racine ou dans `donnees/`, `en/`, etc.** :
ils sont régénérés. Modifier le gabarit ou `strings.json`, puis relancer.

Les assets portent une empreinte anti-cache : `site.css?v=<sha256 court>`.
**Toute modification de `assets/js/app.js`, `assets/js/i18n.js` ou
`assets/css/site.css` impose de relancer `build_pages.py`**, sinon les
visiteurs gardent l'ancienne version en cache sous l'ancienne URL.

### Le site

Huit pages, chacune en FR et EN : accueil, `donnees/` (+ sept pages province depuis le 119),
`rapports/`, `le-virus/`, `chronologie/`, `faq/`, `a-propos/`, `contact/`.

Les graphiques sont rendus côté client par `assets/js/app.js` avec Chart.js.
Chaque canevas déclare son sujet via `data-chart`, les onglets via `data-mode`.

**`/donnees/` est une page en chapitres depuis le 29 août, sans barre
d'onglets.** Combien (Nouveaux cas, Nouveaux décès — chacun dans son cadre,
avec sa courbe de cumul en vue quotidienne et son propre pas de temps
Jour / Semaine / Mois), Où (tableau par province, Nouveaux cas par province
en parts, tableau par zone de santé toujours visible avec sa recherche et son
filtre), Qui (Âge et sexe, Effectifs / Parts), Que fait-on (les quatre
chiffres de la riposte et le lien vers la page). Les onglets ne subsistent
que pour les lectures d'une même série. Née en maquette parallèle le
28 août, adoptée le 29 : l'ancienne page disait trois fois la même chose
(tableau, vignettes, premier onglet), cachait six graphiques derrière un
cadre et le tableau des zones derrière une bascule. « Évolution de
l'épidémie » a disparu — ses deux cumuls vivent dans le quotidien de chaque
série — ; « Suivi des contacts » et « Décès en communauté » sont sur la page
Riposte. Les modes `epidemic`, `contactsFollowUp`, `deathsPlace`,
`byProvince` restent dans `app.js`, sans cadre.

**« Nouveaux cas par province » a remplace « Cas par province » le 29 aout.**
Six cumuls sur un meme axe : l'Ituri (4 845) ecrasait tout, et quatre
courbes sur six se confondaient avec le zero. Le nouveau mode
(`newCasesByProvince`) empile les nouveaux cas par semaine calendaire, par
province, avec une bascule Parts / Cas — **Parts par defaut** : le volume
hebdomadaire est deja dans « Nouveaux cas · Par semaine », ce que ce cadre
montre seul, c'est d'ou viennent les cas (la part de l'Ituri passe de 95 % en
juin a 70 % fin aout). Memes regles que « Nouveaux cas » : semaine du lundi au
dimanche, semaine en cours ecartee, semaine sans releve gardee vide ; les
rattrapages des 22 et 30 juillet restent dans leur semaine — la province est
connue, pas la journee — et la note les nomme. La bascule est une
`data-chart-vue` generique portant `data-for-mode="newCasesByProvince"` :
`renderOneChart` ne l'affiche qu'avec ce mode.

**« Le lieu du deces » a des barres de largeur EGALE depuis le 29 aout.** Le
plugin `largeurSemaine` — partie pleine au prorata des releves, gris hachure
pour les jours manquants, gris uni pour les jours a venir — faisait grossir la
derniere barre de bulletin en bulletin, et le proprietaire ne voulait plus de
ce mouvement. Ce que la largeur encodait passe dans la note, en dates
calculees (« 7 jours sans releve du lieu (16 juil., 28 juil. → 29 juil.,
6 aout → 9 aout) », « la derniere barre est la semaine en cours, sur 4
releves sur sept ») : la note ecrivait « dont quatre d'affilee du 6 au
9 aout » en dur, ce qui se serait perime. Le plugin reste en service pour le
mois en cours de « Nouveaux cas ».

**Trois generalisations d'`app.js` pour des pages a plusieurs cadres**, faites
pour la maquette de `/donnees/` (voir ci-dessous) et sans effet sur les
pages existantes : la bascule Jour / Semaine / Mois et la bascule
Effectifs / Parts visent le canevas du cadre qui les porte (et non plus
`dataChart` en dur) ; le pas de temps vit par canevas (`vuePeriodeParCanvas`,
`vuePeriodeDe(canvas)`) — sur `/donnees/` cas et deces partagent le canevas et
donc l'etat, comme avant ; un canevas `data-cumul="1"` recoit, en vue
quotidienne de `newCases` / `newDeaths`, la courbe de cumul de sa serie sur un
second axe.

**Les sept pages de la rubrique « Données détaillées » ont la même tête**,
depuis le 29 août : au-dessus, la rubrique — « Données détaillées »
(`i18n.tabZones`) — avec la pastille d'identité (la couleur de la province,
l'anneau vide pour le pays, ceux de la barre latérale) ; en titre, ce qu'on a
cliqué — « Ensemble du pays » (`meta.h1` de la page `donnees`, le fil
d'Ariane suit ; `title` et `description` gardent « Données détaillées par
province et zone de santé » pour les moteurs), « Ebola en Ituri »… Le
surtitre de statut des pages province (« Épicentre de l'épidémie »,
« Transmission active ») a été retiré le même jour ; `province.statusLabel`
reste calculé mais n'est plus affiché. Proposition du propriétaire, après
deux essais écartés : le nom de la province en surtitre (il répétait le
titre), puis la pastille dans le titre (elle ne disait plus la rubrique).
L'introduction de la page pays est à l'échelle du pays, sans énumération
des provinces (`provincesIntro`).

**La maquette parallèle de `/donnees/` n'existe plus** : adoptée le 29 août,
son gabarit est devenu `site/pages/donnees.html`. Le générateur garde le
mécanisme `noindex: true` de `pages.json` (page servie, hors sitemap) pour la
prochaine maquette. Combien (Nouveaux cas, Nouveaux deces, chacun avec son cumul
et son pas de temps), Ou (tableau par province, Nouveaux cas par province,
tableau par zone), Qui (Age et sexe), Que fait-on (les quatre chiffres de la
riposte). Elle attend une decision. `newCases` et `newDeaths` restent **voisins** : ils partagent leur
bascule de pas de temps et son etat, ce qui ne se decouvre que si les deux
boutons se touchent. Les modes `ages`, `sexes` et
`communityDeaths` restent dans le code sans bouton — décisions de publication,
pas suppressions.

---

## La structure du site

Cette partie vit dans la skill `gabarits-site` (`.claude/skills/gabarits-site/SKILL.md`), chargee a la demande.

## La carte, et comment elle croise les données

Cette partie vit dans la skill `carte` (`.claude/skills/carte/SKILL.md`), chargee a la demande.

## Ne pas se tromper sur les noms de zones

**C'est le piège principal du projet.** Les bulletins écrivent le même nom de
plusieurs façons, parfois dans un même rapport : `BAMBU`/`Bambu`,
`Oicha**`/`Oicha`, `Nia-Nia`/`Nia Nia`, `Gety`/`Gethy`,
`Boma Mangbetu`/`Boma-Mangbetu`, `Wanie-Rukula`/`Wanierukula`.

**Deux normalisations, à ne pas confondre :**

- `normalize_zone_key()` dans `update_data.py` — dédoublonne à l'extraction.
  Insensible à la casse, aux tirets/espaces et aux **astérisques de note de bas
  de page**.
- `normalise()` dans `build_geo.py` et `normalise_zone()` dans
  `build_pages.py` — même principe, pour rapprocher nos noms de ceux du
  shapefile.

**Le rapprochement se fait en trois passes, de la plus stricte à la plus
tolérante, et refuse ce qui reste ambigu plutôt que de deviner** :

1. Correspondance exacte sur la clé normalisée.
2. Sinon, **dans la même province uniquement**, la plus proche par distance
   d'édition — acceptée si l'écart est **≤ 2 caractères**, et enregistrée comme
   alias.
3. Sinon « NON TROUVÉE ». Aucune supposition.

Deux alias sont actuellement retenus, dans `zones-overview.json` :
`mongbwalu → mongbalu` et `nyankunde → nyakunde`.

**Trois règles pratiques :**

- Ne jamais comparer deux noms de zone par égalité de chaîne. Toujours passer
  par la clé normalisée.
- **Une ré-extraction peut changer l'orthographe retenue.** Un rattrapage du
  24 août a produit « Makiso--Kisangani » avec deux tirets. Toujours diffuser
  avant/après avant de publier un rattrapage.
- Une zone peut porter le nom de sa province — la Tshopo est la seule du pays.
  Voir « Pièges connus ».

---

## Comment l'extraction fonctionne

Le format des SitRep a changé **quatre fois** depuis mai. `update_data.py` ne
suppose donc jamais une mise en page : il essaie, mesure, et se replie.

**Deux chemins, toujours.** Le tableau est lu d'abord par `pdfplumber`
(`parse_zone_detail`). S'il est absent — ou présent mais vide, cas fréquent
d'une table réduite à son en-tête — on retombe sur une lecture du texte brut
(`gap_fill_missing_zones`). Le repli n'est pas un pis-aller : sur le SitRep 100
il a reconstruit 24 lignes de zone que le tableau donnait avec des colonnes
décalées.

**Chaque ligne est jugée avant d'être crue.** `zone_row_looks_unreliable()`
écarte une ligne dont les colonnes ne tiennent pas debout — des cas sans décès
ni létalité, par exemple. `revalidate_zones()` reprend ensuite le texte pour
confirmer. Deux invariants simples attrapent l'essentiel des dérapages de
colonnes : **nouveaux cas ≤ cas cumulés**, et **décès du jour ≤ décès
cumulés**.

**Le script signale ses replis.** Toute exécution qui affiche « repli sur une
lecture du texte brut » ou « N ligne(s) jugée(s) non fiable(s) » mérite qu'on
recoupe le résultat avec le PDF avant de publier. C'est ainsi qu'on a validé le
SitRep 100 : les six lignes provinces et les 56 lignes zones relues une par une
contre les pages 2 et 3.

**`check_coherence.py` est le garde-fou final.** Somme des provinces contre le
national, létalité recalculée, somme des zones contre chaque province,
historiques cohérents, chaque rapport listé ayant son PDF. Il ne modifie rien.

---

## Le corpus gelé — la couche de recherche

`data/corpus/` (78 Mo, hors dépôt) est un **intermédiaire complet des 106
rapports**, construit pour ne plus jamais rouvrir un PDF pendant une analyse.
Il ne sert pas le site : il sert à décider ce que le site devrait montrer.

Reconstruction, dans cet ordre :

```bash
python scripts/geler_corpus.py         # manifeste.json + textes/ — gèle les 106 rapports
python scripts/cartographier_corpus.py # carte.json — époques éditoriales, sections
python scripts/recenser_corpus.py      # recensement-prose.json + recensement-tableaux.json
python scripts/extraire_cellules.py    # cellules.jsonl — aplatit 602 types de tableaux
python scripts/catalogue_corpus.py     # catalogue.json — fusion chiffrée avec couverture
python scripts/extraire_qualitatif.py  # qualitatif.jsonl — les sections « Défis »
python scripts/demographie_figures.py  # demographie.jsonl -> data/demographie.json
```

**Seul `geler_corpus.py` est long** — 102 s pour les 106 PDF, mesure du 24 août.
Les six suivants travaillent sur l'intermédiaire gelé et rendent la main en
quelques secondes : c'est tout l'intérêt du gel. Une reconstruction complète
coûte donc environ deux minutes, pas une demi-heure. `manifeste.json` porte le
SHA-256 de chaque PDF, son nombre de pages et de tableaux.

**Quatre époques éditoriales**, identifiées par `cartographier_corpus.py` :

| Époque | Rapports | Bulletins |
|---|---|---|
| A | 15 | 001 → 016 |
| B | 39 | 017 → 058 |
| C | 22 | 059 → 083 |
| D | 17 | 084 → 100 |
| OMS | 13 | rapports hebdomadaires |

C'est cette carte qui permet de répondre « depuis quand cette colonne
existe-t-elle ? » sans rouvrir cent PDF. Exemple : les quatre colonnes du lieu
du décès n'apparaissent qu'à l'époque C — d'où la fenêtre bornée au 13 juillet,
que rien ne pourra faire remonter.

**`extraire_cellules.py` mérite d'être compris.** Plutôt qu'un parseur par type
de tableau — il y en a 602 —, il applique le même traitement à tous et produit
des cellules nommées. `catalogue_corpus.py` les fusionne ensuite avec les
nombres de la prose et calcule la **couverture** de chaque indicateur : sur
combien de rapports il existe. C'est ce qui a permis de dire que 50 cellules
seulement, sur 17 313 cataloguées, portent la distinction communauté / CTE.

**`extraire_qualitatif.py`** est le seul à s'intéresser au non-chiffré : les
sections « Défis » des bulletins, unique source du corpus sur les **causes** de
persistance de l'épidémie. Rien du site ne l'exploite encore.

**`prototype_riposte.py`** écrit une page autonome dans `tmp/riposte/`, sans
toucher aux sources du site. Modèle à suivre pour prototyper une page nouvelle.

---

## Les scripts

`ls scripts/` donne la liste a jour (65 fichiers ; le guide en annoncait 52). Quatre
familles : le **pipeline** quotidien (ci-dessus), le **corpus** gele, les **rattrapages**
(`backfill_*`), et les **enquetes** ponctuelles (`scan_*`, `inspect_*`, `diagnose_*`),
gardees comme exemples — `inspect_report.py` et `scan_missing_dates.py` sont les plus
reutilisables. La verification visuelle vit dans `scripts/verif/` et `audit_mobile.mjs`.

## Les tableaux détaillés

Cette partie vit dans la skill `tableaux` (`.claude/skills/tableaux/SKILL.md`), chargee a la demande.

## Les graphiques

Cette partie vit dans la skill `graphiques` (`.claude/skills/graphiques/SKILL.md`), chargee a la demande.

## La page « Riposte & défis » (`/riposte/`, `/en/response/`, `/sw/mapambano/`)

Cette partie vit dans la skill `page-riposte` (`.claude/skills/page-riposte/SKILL.md`), chargee a la demande.

## La page « Le virus » et le bloc des génomes

Cette partie vit dans la skill `page-virus` (`.claude/skills/page-virus/SKILL.md`), chargee a la demande.

## Le nom du site dans Google

Google affiche un **nom de site** au-dessus de l'adresse dans ses résultats,
lu dans `WebSite.name` des données structurées de la page d'accueil et dans
`og:site_name`. Il veut une valeur unique et stable ; trois noms selon la
langue (« Suivi Ebola RDC », « DRC Ebola Tracker », « Ufuatiliaji… ») le
faisaient retomber sur le domaine — l'adresse s'affichait deux fois.
Depuis le 8 septembre 2026, `site.brandName` (« Ebola Tracker ») alimente
`WebSite.name`, `isPartOf` des articles et `og:site_name` sur toutes les
pages ; les noms traduits et le domaine sont en `alternateName`. La marque
de la barre latérale (« ebola-tracker.org ») et les titres de page ne
changent pas. Google met des jours à des semaines à reprendre un nom de
site ; demander l'inspection de l'accueil dans la Search Console accélère.

---

## Le compte X du site

`site.xProfile` dans `site/pages.json` (« EbolaTrackerRDC », sans le @,
renseigné le 8 septembre 2026) alimente trois emplacements : « Suivre
sur X » en dernière entrée de la colonne « Le site » du pied de page,
un chapitre « Suivre le site » sur À propos, une ligne sous le formulaire
de Contact — trois langues, icône X en trait (`X_ICONE`), lien `rel="me"`.
Tout passe par `lien_x()` dans `build_pages.py` : **champ vide, rien n'est
rendu**, jamais de lien mort. Les balises `twitter:` du gabarit ne
désignent pas ce compte (choix du propriétaire, points 1 et 3 d'une liste
de quatre écartés le 8 septembre : la carte de partage et la barre
latérale).

---

## Les flux RSS et l'alerte Telegram (22 septembre 2026)

Demande du propriétaire : « que les visiteurs puissent recevoir une
notification quand j'ajoute la mise à jour d'un nouveau SitRep ».

**Le flux est le socle, pas un canal de plus.** `scripts/build_feeds.py`
écrit `/feed.xml`, `/en/feed.xml` et `/sw/feed.xml`, vingt entrées
chacun, à partir de `data/lettres/<num>.json` et du résumé des Défis de
`data/bulletin-notes.json`. Rien n'y est saisi à la main : un flux qui
raconterait autre chose que la page qu'il annonce serait pire que pas de
flux. `build_pages.py` l'appelle en fin de génération et **déclare les
trois fichiers dans le manifeste** — sans quoi `remove_stale` les
effacerait au passage suivant. Le `<link rel="alternate">` du gabarit les
annonce depuis chaque page. C'est par là que passent les relais que le
dépôt n'a pas à connaître : Slack, Teams, et les services qui changent un
flux en lettre par courriel.

**Ce qu'on dit d'une lettre vit à un seul endroit.** `build_feeds.annonce()`
rend titre, adresse, chiffres de tête et résumé ; le flux et Telegram y
passent tous les deux.

**Le point d'entrée du visiteur** est la colonne « Le site » du pied de
page, sous « Suivre sur X » : « Suivre par flux RSS » (toujours) et
« Canal Telegram ». Ce dernier passe par `lien_telegram()` et
`site.telegram` dans `pages.json` — **vide tant que le canal n'est pas
ouvert, et alors rien n'est rendu**, exactement comme `xProfile` avant le
8 septembre. Ouvrir le canal, c'est renseigner ce champ et poser les
secrets ; aucun code à toucher.

**Telegram** : `scripts/notifier_telegram.py`, un canal public par langue,
appelé par `.github/workflows/flux-et-alertes.yml` quand `data/lettres/**`
ou `data/bulletin-notes.json` arrive sur `main`. Secrets
`TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID_FR` / `_EN` / `_SW` ; **une
langue sans canal est sautée**, on peut n'ouvrir que le français. Le dépôt
ne garde aucune adresse ni aucune donnée d'abonné — c'est Telegram qui
tient la liste. Deux garde-fous : `data/notifie.json` retient les numéros
déjà annoncés (une reprise du workflow ne renvoie pas la même lettre), et
**l'annonce attend le résumé des Défis** ; sans lui le message se
réduirait à trois chiffres, et le commit qui l'apporte relance le
workflow. `--essai` montre les messages sans rien envoyer.

**Écarté.** WhatsApp : la Cloud API demande un Business Manager vérifié, un
numéro dédié et des modèles approuvés un par un, pour une facturation au
message ; les Canaux WhatsApp sont gratuits mais n'ont pas d'API — une
publication à la main. Le courriel viendra du flux (Brevo, Buttondown)
plutôt que d'un formulaire maison : collecter des adresses, c'est un
double opt-in, un désabonnement, SPF/DKIM/DMARC sur le domaine et une
base à tenir.

---

## La rangée des provinces, en bas de l'accueil

**Les six vignettes sont devenues sept colonnes coiffées d'un filet**
(22 septembre 2026). C'étaient des boîtes à bordure gauche colorée portant
trois paires libellé/valeur en capitales — cas, décès, létalité. Reproche du
propriétaire : « ça fait beaucoup trop IA », le même qu'à la police des
chiffres du panneau de la carte le 10 septembre. La règle du 27 août « moins
de boîtes, plus de traits » les avait explicitement épargnées ; un mois plus
tard elles étaient le dernier endroit de l'accueil à porter une boîte.

Ne restent que **le filet, le nom, le chiffre, les décès**. `province_col` /
`.pcol-*` remplacent `.province-card` / `.pc-stat`.

- **LE FILET PORTE L'IDENTITÉ, LE TEXTE GARDE L'ENCRE.** La teinte arrive par
  `--teinte`, posée par le générateur depuis `PROVINCE_COLORS`. Écrire le nom
  dans la couleur de sa province était la première idée : l'ambre du Nord-Kivu
  tombe à **3,9 de contraste** sur son fond quand le site s'impose 4,5. C'est
  déjà la règle ailleurs — le chiffre porte l'encre, le trait à côté porte la
  province.
- **La létalité est tombée avec les libellés.** À cet endroit la question est
  où est l'épidémie, pas comment elle tue ; elle reste sur chaque page
  province. Décision du propriétaire.
- **Le compte de décès s'écrit en toutes lettres** sous le chiffre des cas,
  clé `provincesCardDeathsInline` : plus aucun libellé en capitales, c'est le
  mot qui porte l'unité. L'anglais accorde (`{n} death{n?s}` — « 1 death » au
  Sud-Kivu), le swahili place le nom devant le nombre (« vifo 850 »).
- **LE TEXTE GROSSIT AU SURVOL PAR `transform`, JAMAIS PAR `font-size`.**
  Agrandir la police relance la mise en page : la colonne survolée gagne trois
  pixels de haut et toute la rangée s'allonge. Mesuré après coup : la grille
  fait 102,06 px au repos **comme au survol**. Même principe pour le filet, qui
  passe de 2 à 5 px en reprenant l'épaisseur sur le padding.
- **La règle mobile `.pc-stat` a disparu**, avec le côte à côte libellé/valeur
  qu'elle rattrapait. La colonne empile par construction et encaisse un chiffre
  plus long — le cumul franchira 10 000 vers le 13 octobre 2026, ce qui cassait
  l'ancienne mise en page à 375 px. Deux colonnes dès 320 px, vérifié.

**Dix variantes montrées en local avant celle-ci**, en trois planches
(`tmp/propositions-provinces*.html`, gitignoré). Écartées : la liste-relevé à
filets horizontaux, la liste à jauges, le classement avec part du pays, le
relevé à sparklines (sous dix cas la courbe ne dit plus rien), les colonnes à
deux chiffres côte à côte, le carré à fond uni, le carré teinté à 9 % et le
carré teinté par paliers de la carte — celui-ci doublait le cartogramme du haut
de page et mettait l'Ituri et le Nord-Kivu dans la même teinte à un facteur
quatre d'écart.

**LA RÉSERVE QUI RESTE, ET QUI VAUT D'ÊTRE RELUE AVANT D'Y REVENIR : la
hiérarchie n'est pas encodée.** L'Ituri (5 913) et le Sud-Ubangi (1) occupent
la même largeur, la même taille de chiffre, le même poids — la forme dit « sept
provinces comparables » quand une seule fait 77 % des cas. C'est exactement ce
que la grille de cartes ratait, et la rangée le garde. La variante A3 du
troisième jeu le réglait pour le prix d'un filet à deux couleurs (partie
colorée = part des cas). Montrée, non retenue ce jour-là.

## Conventions établies

**Couleurs.** Bleu `#005E82` = cas, rouge `#993A2E` = décès, partout. Chaque
province a sa teinte d'identité (`PROVINCE_COLORS`), utilisée sur les pastilles
du menu, le tableau, les cartes de province et les barres de son graphique.

Vérifier la séparation avant d'apparier deux couleurs : le dépôt s'impose un
ΔE d'environ 15 en deutéranopie. L'ambre `#A06F30` et le rouge tombent à 8 —
c'est pourquoi la courbe de cumul est passée au bleu quand celle des décès l'a
rejointe.

**Accord.** Les chaînes acceptent `{clé?suffixe}` : le suffixe n'apparaît que
si la valeur n'est pas 1. En français, « cas » et « décès » sont invariables,
seuls les adjectifs prennent la marque. Le mecanisme n'etait pas applique a
« {n} zones touchées sur {total} », qui affichait « 1 zones touchées » pour le
Sud-Kivu ; corrige le 25 aout en « {n} zone{n?s} touchée{n?s} sur {total} ».
L'anglais n'a pas le probleme : « {n} of {total} zones affected » accorde sur
{total}.

**Typographie.** Espace fine insécable (U+202F) comme séparateur des milliers. Un
taux s'ecrit « 48,0 % » en francais et « 48.0% » en anglais : virgule decimale
et **espace fine insecable** (U+202F) avant le signe, la meme que pour les
milliers. Avec une espace ordinaire — essayee le 25 aout, corrigee le meme
jour — « 83,4 % » se coupait en deux dans une colonne etroite et le « % »
passait a la ligne sous le nombre, sur telephone, dans la part du pays comme
dans la letalite. Les cellules numeriques portent en plus `white-space:nowrap`
pour les valeurs a separateur, que l'insecable ne protege pas : « 28 / 36 ».
Ce n'est plus la convention de l'espace ordinaire — c'est la convention
deja suivie partout dans `app.js` et `strings.json`. `fmt_cfr()` (generateur)
et `fmtCfr()` (`app.js`) doivent produire **exactement** la meme chaine : le
JavaScript reecrit les elements que le generateur a remplis, et un taux qui
change d'ecriture au chargement se voit. Les deux se corrigent ensemble.

**Police des chiffres du panneau de la carte.** Depuis le 10 septembre 2026,
les cinq chiffres nationaux à droite de la carte d'accueil, et le bilan de la
zone survolée, sont en **Bricolage Grotesque** (graisse 700, écarts en 600,
largeur 87,5, chargée dans `site/layout.html`). Décision du propriétaire après
une maquette de six polices sur le panneau réel : Public Sans en gras sur cinq
lignes de couleurs différentes faisait « trop IA style ». Le choix s'est fait
entre Fraunces (serif, la plus proche du titre), Playfair Display (didone, dont
les déliés souffrent sur un petit écran Android) et Bricolage, retenue parce
qu'elle reste dans la famille des sans du site. Tout le reste — bandeau
`.kpis`, tableaux, graphiques — garde Public Sans ; l'étendre est possible
mais n'a pas été demandé. Les couleurs du panneau n'ont pas bougé.

**Notes de graphique.** Elles portent d'abord le fait, ensuite les réserves.
Un lecteur ne lit pas trois lignes de mise en garde avant d'atteindre
l'information.

**Seuils.** `SEUIL_COURBE_PROVINCE = 50` dans `build_pages.py` : sous 50 cas
cumulés, une province n'a pas de graphique — la courbe serait plate et les
barres invisibles. Tshopo, Sud-Kivu, Bas-Uélé et Sud-Ubangi sont concernés.
**Essayé à 20 le 15 septembre 2026** pour donner le sien à la Tshopo (28 cas,
16 journées avec au moins un cas, 3 au plus), montré, puis **remis à 50 le
même jour** — « on ne va pas garder cette idée là ». Ne pas y revenir sans
qu'il le redemande. Deux corrections nées de cet essai sont **gardées**,
justes indépendamment du seuil et invisibles tant qu'aucune province à
petits nombres n'a de graphique :
- **`precision: 0` sur les deux axes du mode `provinceEpidemic`.** Chart.js
  graduait l'axe 0 / 0,5 / 1 / 1,5 quand le maximum est 3 : chaque demi-cas
  est un effectif impossible. Sans effet sur l'Ituri, dont l'axe monte à 350.
- **Le jeu « Rattrapage » n'est ajouté en vue agrégée que s'il porte quelque
  chose** : une légende qui nomme une couleur absente du tracé est pire que
  pas de légende.
`seuilLisibilite = 20` dans `deces-lieu.json` écarte de même les provinces où
une proportion n'aurait aucun sens.

---

## Trois retouches du 6 septembre 2026

- **La démographie dit qu'elle est figée dans son cadre** : à droite du titre
  « Âge et sexe », `seed.agesFrozen` (« figée au 5 août 2026 : l'INSP ne
  publie plus cette répartition »), calculé depuis `demographie.json`.
- **Le virus, vaccins** : un paragraphe sobre après le tableau
  (`virusVaccinUpdate`), écrit d'après les orientations provisoires de l'OMS
  du 31 août 2026 lues sur IRIS (efficacité d'Ervebo contre Bundibugyo
  inconnue, usage réservé à un cadre de recherche, priorité aux soignants et
  au personnel de première ligne) et le SitRep 112 (vaccinations de ce
  personnel). Aucun chiffre en dur, volontairement : « nous ne sommes pas
  spécialistes ». Le « 0 vaccin homologué » reste vrai.
- Un filtre par type de jalon sur la légende de la chronologie a été
  construit, montré, puis **écarté par le propriétaire** le 6 septembre :
  ne pas le refaire sans qu'il le redemande.
- **L'historique des zones n'est chargé que là où il sert** : curseur des
  cartes et tableaux de zones (`besoinHistorique` dans l'init). Mesure
  faite avant : GitHub Pages compresse, `zones-history.json` fait 15 Ko
  sur le réseau pour 438 Ko sur disque, `app.js` 79 Ko pour 260 — le poids
  réel d'une page est dans le script, la feuille de style et Chart.js, pas
  dans les données. Le gain de cette retouche est donc modeste.

## Pièges connus

Les pieges d'extraction et de lecture des PDF vivent dans la skill
`journal-bulletins` (`.claude/skills/journal-bulletins/SKILL.md`), chargee a la
demande. **Trois regles en sortent et restent ici**, parce qu'elles se lisent sans
ouvrir quoi que ce soit :

- **Ne jamais additionner `deathsCommunity24h` et `deathsIntraCTE24h`** : passer par
  `zone_new_deaths()` cote generateur, `newDeaths24h` cote `app.js`. Le PDF n'imprime
  pas la cellule vide, et l'un des deux compteurs porte le total.
- **Ne jamais comparer deux noms de zone par egalite de chaine** : toujours la cle
  normalisee. La zone « Tshopo » porte le nom de sa province, seule du pays.
- **Les annotations `X | None` cassent sur le Python de la machine** (3.9.6) :
  `from __future__ import annotations` en tete de tout script repris d'ailleurs.

## Ce que les sources disent, et ne disent pas

**Les « community deaths » des rapports OMS ne sont pas des décès Ebola.** Ce
sont des **alertes validées** — des personnes trouvées mortes dont l'alerte a
été jugée conforme à la définition de cas suspect, en attente de prélèvement.
L'INSP écrit sobrement « cas suspects dont X décès ». À cette période l'entonnoir
d'alertes en signalait 60 à 90 par jour quand les décès confirmés tournaient
autour de 20. **Ne jamais mélanger avec les « décès communautaires » du tableau
par province**, qui sont des décès confirmés survenus hors CTE.

**L'OMS fixe une cible opérationnelle de 95 %** pour le suivi des cas contacts
(rapports n°11 et n°14). Le taux plafonne autour de 81 % — l'écart est le
nombre de personnes exposées qu'on ne voit pas chaque jour.

**Cette épidémie est la deuxième plus grande de l'histoire d'Ebola**, après
l'Afrique de l'Ouest 2013-2016, et la plus grande jamais causée par l'espèce
Bundibugyo (OMS n°12). Le site ne l'affiche pas encore.

**La liste des 16 épidémies précédentes n'est dans aucune de nos sources.** Les
bulletins portent l'étiquette « 17ème épidémie » sans jamais énumérer les
autres. Un tableau historique demanderait une source extérieure au corpus.

---

## Faits marquants de la donnée

- **Létalité en hausse continue** : 15,0 % fin mai, 28,3 % fin juin, 37,5 %
  mi-juillet, 47,9 % au 22 août, 48,0 % au 23 août. Elle a triplé en trois mois.
- **Les moins de 5 ans** font 10,0 % des cas et **19,0 % des décès**. Les
  30-49 ans, tranche la plus touchée en volume, font 35,2 % des cas pour 27,2 %
  des décès.
- **Les femmes** représentent 52,9 % des cas mais 49,6 % des décès. L'excédent
  féminin se concentre sur les 18-29 ans (58,7 %).
- **Près de deux décès sur trois** surviennent hors des centres de traitement,
  et cette part **ne bouge pas** depuis six semaines — 61,6 % en moyenne, sans
  tendance décelable au-delà du bruit d'échantillonnage.
- **Les tranches d'âge sont inégales** (5, 13, 12, 20 ans, puis ouverte).
  Rapporté à une année d'âge : 76,4 cas pour les 18-29 ans, 69,0 pour les 0-4,
  60,9 pour les 30-49 et 35,0 pour les 5-17. L'ordre s'inverse presque
  complètement par rapport aux barres brutes, où les 30-49 dominent.
- **Le lieu du décès varie fortement selon la province** : 66,8 % en communauté
  au Nord-Kivu, 60,7 % en Ituri, 50,0 % au Haut-Uélé. Cette lecture n'est plus
  affichée — le détail reste dans `deces-lieu.json`.
- **L'Ituri pèse 77,5 % des décès classés** : toute courbe nationale sur ce
  sujet suit d'abord la sienne.

---

## Décisions écartées, et pourquoi

Ce que le site refuse de faire compte autant que ce qu'il fait. Ces choix ont
été pesés une fois ; les rouvrir demande de reprendre l'argument, pas de le
redécouvrir.

**Aucun taux de létalité par âge ni par sexe.** La figure démographique ne voit
que 85,2 % des cas mais 60,8 % des décès. Un quotient calculé dessus donne
32,5 % quand le site affiche 47,9 % de létalité nationale. Les onglets montrent
donc des **parts** — part des cas, part des décès —, jamais un rapport entre
les deux. C'est aussi pourquoi la pyramide des âges sépare cas et décès en deux
figures à échelles distinctes : sur un axe commun, l'œil calcule le quotient
interdit.

**Aucune réattribution de cas d'une province à l'autre.** Les premiers malades
du Haut-Uélé et de la Tshopo sont restés comptés en Ituri. Les déplacer
demanderait d'inventer une série : deux cas à Wamba le 25 juin, cinq le
1er juillet, un seul sur la ligne créée le 10. Ces nombres ne se raccordent
pas, et les ajouter sans les retirer de Nia-Nia gonflerait le total national.

**Pas de graphique séparé pour les décès.** La courbe a rejoint le graphique
principal, sur l'axe des cumuls qui existait déjà. L'écart entre les deux
courbes se lit comme ce qu'il est : la létalité, devenue trajectoire au lieu
d'un nombre isolé.

**Pas de ligne de cible tracée sur le suivi des contacts.** Les 95 % de l'OMS
sont dits dans la note, pas dessinés : une ligne à 95 % au-dessus d'une courbe
qui plafonne à 81 % n'ouvre qu'une bande vide sur le quart supérieur du cadre.

**Les tranches d'âge ne sont jamais lissées ni mises à l'échelle de leur
largeur.** Elles sont inégales (5, 13, 12, 20 ans, puis ouverte) : mettre les
lignes à l'échelle ferait passer un artefact de découpage pour une forme.
Aucune spline non plus entre des points hebdomadaires — avec six points elle
dépasse les valeurs mesurées et invente des sommets.

**Les volumes hebdomadaires du lieu du décès ne sont pas comparables.** Sept
jours manquent à la fenêtre, dont quatre d'affilée du 6 au 9 août. Seules les
parts se comparent d'une semaine à l'autre.

---

## Comment travailler ici

Le propriétaire distingue strictement deux états, et il faut s'y tenir :

- **« en local »** — construire, régénérer, montrer. Ne rien commiter.
- **« commit »** — commiter **et pousser**. Décision du 28 août 2026 : « quand
  je dis commit à partir de maintenant, ça veut dire mets en ligne aussi ».
  « Mets en ligne » reste compris, c'est la même chose.

Jusqu'au 28 août il y avait un état intermédiaire, « commit » sans push. Il a
été abandonné le jour où l'on a constaté que le hook ci-dessous pousse la
branche entière dès que ce fichier bouge : un commit « local » partait de
toute façon en ligne au premier échange qui touchait au guide. L'état
n'était pas tenable, autant le dire.

**Une seule exception, décidée le 24 août : ce fichier.** Un hook `Stop` de Claude
Code (`~/.claude/hooks/pousser-claude-md.sh`) commite et pousse `CLAUDE.md` à la
fin de chaque échange, et uniquement lui — commit limité au chemin, silencieux
quand rien n'a changé. La raison : le guide doit survivre à un re-clone, et le
perdre coûte plus cher que de le publier. Le site, les données et le code gardent
les deux états intacts.

Corollaire pour qui écrit ici : **ce fichier part en ligne sans relecture**. Rien
qui ne puisse être public n'y a sa place — pas de jeton, pas de chemin privé
au-delà de ceux déjà cités, pas de brouillon.

**Montrer avant de publier.** Une capture d'écran, pas une description. Servir
le site sur `127.0.0.1:8899` et capturer avec les outils de `scripts/verif/`.

**Vérifier plutôt qu'affirmer.** Presque toutes les erreurs corrigées le
24 août venaient d'un calcul plausible appliqué à une donnée qui ne disait pas
ce qu'on croyait. Quand un chiffre peut se contrôler, le contrôler — y compris
ses propres affirmations d'il y a dix minutes.

**Les questions « tu en penses quoi ? » attendent un avis**, argumenté et
chiffré si possible, y compris un désaccord. Plusieurs bonnes décisions de
cette journée sont venues d'un « non, et voilà pourquoi » — la lecture par
province abandonnée au profit du temps, ou l'inverse pour les dates d'arrivée.

**Les messages de commit sont longs et détaillés**, en français sans accents.
Ils citent les passages de bulletin qui fondent chaque décision, gardent les
mesures qui ont tranché, et consignent ce qui a été écarté.

---

## Chantiers ouverts

Le detail des chantiers en attente et des maquettes mises de cote vit dans la
skill `chantiers-ouverts` (`.claude/skills/chantiers-ouverts/SKILL.md`),
chargee a la demande. Trois interdictions en sont extraites et restent ici,
parce qu'elles doivent etre lues sans avoir a ouvrir quoi que ce soit :
- **Ne pas refaire le filtre par type de jalon** de la chronologie (construit,
  montre, ecarte le 6 septembre 2026) sans que le proprietaire le redemande.
- **Ne pas redescendre `SEUIL_COURBE_PROVINCE` sous 50** (essaye a 20 le
  15 septembre 2026, remis a 50 le meme jour).
- **Ne pas rallumer `community-deaths-daily.json`** sans corriger son defaut :
  il ne valide qu'une province quand son libelle annonce le pays.

## Où chercher le reste

**Les messages de commit portent le raisonnement**, pas seulement le quoi. Ils
citent les passages de bulletin qui fondent chaque décision, gardent les
mesures qui ont tranché un choix de couleur ou de seuil, et consignent ce qui
a été écarté et pourquoi. `git log` est la mémoire longue de ce projet.

Les commentaires du code font le reste : ils expliquent systématiquement le
*pourquoi*, souvent avec la date et le numéro de bulletin qui ont révélé le
problème.
