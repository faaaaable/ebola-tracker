# ebola-tracker.org — guide du dépôt

Site public de suivi de la **17ᵉ épidémie d'Ebola en RDC** (espèce Bundibugyo,
déclarée le 15 mai 2026). Il compile les bulletins officiels de l'INSP et les
rapports hebdomadaires de l'OMS. Trilingue FR/EN/SW, statique, servi par GitHub
Pages sur `ebola-tracker.org` depuis la branche `main`.

Dernier bulletin intégré à la rédaction de ce guide : **SitRep 128**, rapportage
du 19 septembre 2026 (publié le 20) — 7 672 cas confirmés, 3 699 décès,
létalité 48,2 %, 1 879 guéris, 886 patients en isolement/CTE, 63 zones touchées
sur 167 dans 7 provinces (aucune nouvelle), **58 nouveaux cas** (Ituri 38,
Nord-Kivu 14, Haut-Uélé 5, Tshopo 1) et 23 décès du jour. Intégré le
**21 septembre 2026** ; laboratoire 58 positifs pour 58 nouveaux cas, garde-fou
du jour vérifié ; `check_coherence` sans écart bloquant, les trois écarts
connus de la source inchangés ; résumé des Défis rédigé (110 mots).

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

**Un seul en-tête de page, en quatre couches, depuis le 5 septembre 2026.**
Le propriétaire avait relevé que chaque page commençait autrement — bille
ici, pas là ; chapeau en serif sur deux pages, en sans-serif sur sept ;
trois composants différents pour une bande de chiffres. Toutes les pages
hors accueil suivent désormais le même ordre, chaque couche pouvant
manquer mais jamais être remplacée par autre chose :

1. **Surtitre** (`.eyebrow`, capitales de 11 px, bille devant) : la rubrique
   de la barre latérale. « Données détaillées » avec la pastille d'identité
   sur les sept pages de données (couleur de la province, anneau vide pour
   le pays) ; sinon le groupe de la barre — `footerExploreTitle`
   (Riposte, Flux), `footerUnderstandTitle` (Chronologie, Le virus, FAQ),
   `footerSiteTitle` (Sources, À propos, Contact) — avec la bille bleue.
2. **Titre** `.page-title`, sans plafond de largeur (le `22ch` est parti,
   `page-title--large` n'existe plus).
3. **À droite du titre**, dans `.section-sub`, une seule formule pour les
   pages qui vivent des bulletins : `seed.cartoAsOf` (« Situation au
   3 sept. 2026 ») sur Données, provinces et Riposte ; « Période
   observée : … » (`fluxSub`) sur Flux. Rien sur Sources, Chronologie,
   Le virus, FAQ, À propos, Contact. Conséquence sur `/donnees/` : la ligne
   « 60 zones touchées · SitRep N°112 » (`#zonesTableSub`, réécrite par le
   script) est descendue à droite du titre « Par zone de santé », qu'elle
   décrit ; la province ne montre plus « SitRep N°112 du 3 sept. »
   (`seed.sitrepRef` reste calculé, inutilisé).
4. **Chapeau** `.lede` : serif de 22 px, une ou deux phrases, 35 mots au
   plus. Ce qui dépasse descend dans un `.page-intro` sans-serif juste
   dessous (`.lede+.page-intro` resserre l'écart). Les chapeaux de
   Données, Riposte, Flux et Sources ont été scindés en deux clés
   (`ddLede`/`provincesIntro`, `riposteLede`/`riposteIntro`,
   `fluxLede`/`fluxIntro`, `reportsLede`/`reportsPageIntro`) ; le chapeau
   de province est `provinceIntro` en serif, le rang en dessous en
   `page-intro`. `about-lede` a fusionné dans `lede`.

Puis, quand ils existent : la **bande de chiffres**, toujours `.kpis
riposte-kpis` (Le virus a quitté `figure-band`, qui ne sert plus qu'à la
bande des génomes plus bas ; À propos a quitté sa liste `about-facts`, ses
repères sont en valeur courte + détail : « INSP et OMS / bulletins
officiels », « 121 / 105 INSP, 16 OMS ») ; puis les **ancres**
`.riposte-ancres` dès trois chapitres (Sources en a reçu trois, sur des
`id` `insp`, `who-reports-section`, `autres`). Deux modificateurs de
`.kpi` : `figure` (chiffre de contexte, bleu fort) et `alert` (rouge).
Vérifié par planche des dix en-têtes à 1 280 px (`tmp/verif/
planche-tetes-apres.png`) et trois pages à 360 px ; `test_onglets` sans
erreur sur Données, Riposte et Sources.

**Le glossaire (`/glossaire/`, `/en/glossary/`, `/sw/kamusi/`) existe depuis
le 10 septembre 2026.** Quinze entrées (cas confirmé, probable, suspect,
alerte, contact, suivi des contacts, décès communautaire, CTE, guéri,
létalité, zone de santé, épicentre, Bundibugyo, enterrement digne et
sécurisé, SitRep), définies comme le site les emploie, dans
`glossaireItems` de `strings.json` (`t` et `d` par langue, rendues par
`glossaire_items_html`), fragment `glossaire.html`, styles `.gl-list`.
**Décision du propriétaire : la page n'est reliée que depuis la colonne
« Comprendre » du pied de page** (`footerNav`), après FAQ — ni colonne
latérale, ni section sur l'accueil. Les deux autres formes ont été
maquettées et écartées le même jour (section en bas de l'accueil, entrée
dans la colonne). En-tête à quatre couches comme les autres pages :
surtitre `footerUnderstandTitle`, titre, chapeau `glossaireLede`, rien à
droite du titre. Le swahili est à faire relire.

**Le corps des pages suit quatre règles depuis le même jour** (analyse
de la planche `tmp/verif/planche-corps.png`, avant/après), décidées après
un « tu conseilles quoi ? » :

1. **Une page en chapitres a sa colonne de titres.** Le critère est
   l'existence d'ancres : Données, Le virus, Riposte, Flux et Sources sont
   en `section-split` (nom du chapitre et ligne italique dans la marge de
   220 px, contenu à droite). Provinces, Chronologie, FAQ, À propos et
   Contact restent pleine largeur. **Sources est revenue en pleine largeur
   le 6 septembre** : ses chapitres sont des listes de documents, et la
   colonne ne laissait que deux bulletins par ligne contre trois — le
   propriétaire l'a vu parce que la section OMS tombait déjà sous son
   titre : `app.js` (`renderWhoReports`) pose `style.display = 'block'` sur
   `#who-reports-section` au chargement, ce qui annulait la grille de
   `section-split` sur cette seule section. Règle affinée : la colonne va aux chapitres qui portent une
   figure ou un texte, pas à une grille de documents. Coût assumé : les graphiques de Riposte
   ont perdu 250 px à 1 280 px et prennent la largeur de ceux de Données.
   Sur Sources, le premier chapitre a quitté la section d'en-tête pour
   devenir une section à part (`#insp`).
2. **Deux graphies de titre.** Le chapitre en capitales sans-serif
   (`.section-title`) ; le cadre ou l'intertitre de texte en serif de
   22 px (`.frame-title`), une seule taille partagée par sélecteur avec
   `.prose h2`, `.tl-title`, `.data-note h2` et `.faq-more h2`. Sur
   Données, « Nouveaux cas », « Par province »… sont donc en serif, ce qui
   les distingue enfin des chapitres « Combien », « Où ».
3. **Sous un chapitre** : la ligne italique, puis le paragraphe, dans cet
   ordre.
4. **Un cadre est titré au-dessus, jamais dedans** : les `figcaption` de
   Flux et du bloc des génomes sont devenus des `h3.frame-title` dans un
   `.section-head` avant le cadre, leur sous-titre `.mb-sub` une
   `.section-sub`. Une seule graphie de note sous les cadres : `.mb-credit`
   et `.vcompare-note` alignés sur `.map-note` (11,5 px, gris).

5. **Chaque page longue se termine par une sortie** « Pour aller plus loin »
   (`#plus-loin`, liste `.plus-loin`) : deux liens choisis par sens, chacun
   suivi d'une ligne sans chiffre. Riposte → Données, Le virus ; Le virus →
   Riposte, FAQ ; Chronologie → Données, Sources. Les autres pages avaient
   déjà leur sortie (Données « Que fait-on », provinces note de lecture,
   Sources « Autres sources », FAQ « Votre question n'est pas là ? ») et
   n'ont pas bougé. Clés `plusLoinTitle`, `*Loin1Link/Text`, `*Loin2Link/Text`.

`test_onglets` sans erreur sur les cinq pages en chapitres.


**Trois langues, un seul générateur — et une table pour les conventions.**
`LOCALES` dans `build_pages.py` porte, par langue : séparateur de milliers,
séparateur décimal, forme du pourcent, **préfixe d'URL**, locale Open Graph et
libellé du sélecteur. Ajouter une langue, c'est ajouter une entrée là, un bloc
dans `site/strings.json`, un dans `assets/js/i18n.js`, les slugs et `meta` dans
`site/pages.json`, et rien d'autre : le sélecteur de langue, les balises
`alternate` et le `sitemap.xml` bouclent sur `site.languages`.

Le 25 août, avant le swahili, le générateur raisonnait en « si français, sinon
anglais » à **dix-huit endroits**. Le plus grave était la construction d'URL :
`"/" + slug if lang == "fr" else "/en/" + slug` aurait publié le swahili
**sous `/en/`**, en collision avec l'anglais, sans lever la moindre erreur. Les
autres étaient plus discrets — nombres, dates, ordinaux — et deux familles de
libellés visibles (« Situation au », « Rapport N° ») vivaient en dur dans le
Python, contre la règle du dépôt ; elles sont dans `strings.json`.

**Le même piège existait côté JavaScript**, et il était pire parce qu'il ne se
voyait qu'à l'exécution : `currentLang` testait « ça commence par *en* ? alors
anglais, sinon français ». Une page swahili s'affichait correctement, puis
**se réécrivait en français** dès que `app.js` prenait la main. `currentLang`
valide désormais le code contre les clés d'`I18N`, et `NUM_CONVENTIONS` y
double `LOCALES` — les deux tables se corrigent ensemble, comme `fmt_cfr()` et
`fmtCfr()`.

**Méthode qui a marché : généraliser d'abord, traduire ensuite.** Après le
refactoring et avant d'ajouter la moindre chaîne swahili, les pages FR et EN
étaient identiques au caractère près, hormis le sélecteur. Sans ce jalon, une
régression se serait perdue dans les 725 lignes du chantier.

**Le swahili n'a toujours pas été relu par un locuteur.** Il couvre
l'intégralité du site — 507 chaînes de `strings.json`, celles d'`i18n.js` dont
les fonctions, la FAQ, les jalons de chronologie, les textes d'arrivée par
province, les slugs (`/sw/takwimu/`, `/sw/ripoti/`, `/sw/matukio/`) et les
`meta`. Ce qui est vérifié mécaniquement l'est : aucune variable `{n}` perdue
ni inventée, aucune clé manquante dans les trois blocs, aucune chaîne restée en
français. Ce qui ne l'est pas : la justesse des formulations sanitaires.
**`python -c` d'export : `tmp/relecture-swahili.txt` met les 655 chaînes
français/swahili côte à côte, prêtes à envoyer** (régénérable, `tmp/` n'est pas
versionné).

**Une passe de cohérence terminologique a été faite le 21 septembre 2026**,
après remarque du propriétaire (« le swahili est toujours tel quel ») : ce qui
ne demande pas d'être locuteur, c'est-à-dire l'emploi d'un même terme partout.
Quatre écarts corrigés.

- **« Contacts » se disait de quatre façons.** Le terme établi est
  **`walioguswa`** (sept emplois dans `i18n.js`, dont le titre de la section).
  Trois exceptions traînaient dans `strings.json` : `lettreKpiContacts` disait
  *waliowasiliana*, « ceux qui ont **communiqué** entre eux » — un faux ami en
  épidémiologie ; `provinceRiposteSub` disait *waliokutana na wagonjwa* ; et
  `riposteVaccinAussi` comme le lede de la vaccination disaient *waliogusana na
  wagonjwa*, ajoutés la veille.
- **Le lexique définissait un mot que le site n'emploie pas** : l'entrée
  « zone de santé » s'intitulait *Kanda ya afya*, quand le site écrit *eneo la
  afya* vingt-quatre fois. Le lecteur cherchait la définition d'un terme sous un
  autre nom.
- `vaccChartUnite`, chaîne morte dans les trois langues depuis la
  simplification de l'infobulle, est supprimée.

Ce qui a été vérifié et laissé tel quel : les alternances *wamechanjwa* /
*waliochanjwa* et *wamelazwa* / *waliolazwa* suivent la construction — forme
relative pour les libellés, forme de phrase pour les phrases. Ce n'est pas du
désordre, ne pas « harmoniser » sans locuteur.

**Le choix de langue est entièrement manuel**, décision du 25 août. Le site
est statique : aucun serveur ne peut négocier `Accept-Language`, et aucune
redirection JavaScript n'a été ajoutée — elle ferait sauter la page, piégerait
le bouton retour, et ne se déclencherait presque jamais (sur 90 jours, aucun
visiteur congolais n'avait son navigateur en swahili, 91 % en français). Le
seul canal automatique est le référencement, via les balises `alternate` —
qui étaient elles-mêmes câblées sur deux langues dans `site/layout.html` alors
que le `sitemap.xml` bouclait déjà : le swahili figurait dans le sitemap sans
être annoncé par les pages. Corrigé le même jour.

**Deux langues, un seul générateur.** `site/pages.json` déclare huit pages avec
un slug par langue — `donnees/` et `data/`, `le-virus/` et `the-virus/`. Les
six pages province se déclinent depuis `provinceSlugs` (`Haut-Uélé` →
`haut-uele`). Tout est calculé par la classe `Urls` ; **ne jamais écrire une
URL en dur**, les liens alternés et le `sitemap.xml` en dépendent.

**Le rythme de la maquette : `section-split`.** Une grille à deux colonnes —
une colonne de titre fixe de 220 px, le contenu à droite. C'est ce qui donne
au site son air de rapport plutôt que de tableau de bord. Sous 1 180 px elle
retombe sur une seule colonne.

Conséquence à connaître : le contenu ne dispose jamais de toute la largeur.
À 1 280 px il reste 692 px après la colonne latérale (240), les gouttières
(2 × 48) et la colonne de titre (220 + 32). C'est ce calcul qui a fait déborder
les cartes de province.

**Trois niveaux de texte.** `site/strings.json` pour le générateur,
`assets/js/i18n.js` pour le JavaScript, et les gabarits `site/pages/*.html`
pour la structure. Un texte visible ne doit jamais être écrit dans un gabarit
s'il varie selon la langue.

**Le contenu curé vit dans `strings.json`** : `timelineEvents` (jalons
rédigés), `provinceArrivals` (dates d'arrivée avec leur bulletin source),
`faqItems`. C'est le mécanisme prévu pour un fait historique qu'aucune
extraction ne produit.

---

## La carte, et comment elle croise les données

**Une seule source géographique.** `build_geo.py` lit le shapefile OCHA des 519
zones de santé et produit deux fichiers, **une fois pour toutes** :

- `site/geo/zones-overview.json` — les 519 tracés, la carte nationale
- `site/geo/province-maps.json` — un cadrage par province

Le jeu HDX `dr-congo-health-0` s'intitule « DR Congo - Health Zones » ; sa
source déclarée est le **Référentiel géographique commun** de la RDC, et
l'organisme qui le publie est **OCHA RDC**. C'est ce qu'il faut écrire quand on
cite la provenance des tracés — « contours officiels » laissait croire à un
document gouvernemental, et le sigle n'était développé nulle part sur le site.
La légende de la carte le dit depuis le 25 août : « Chaque forme est une zone
de santé, l'unité de référence des bulletins officiels. Délimitations
géographiques d'après les données d'OCHA. » C'est la **seule** mention de cette
provenance sur tout le site — la page « À propos » n'en parle pas.

Ils ne se régénèrent pas au quotidien. `build_pages.py` les lit et **colorie**
les zones d'après `data/latest.json`.

**La projection est une plate-carrée.** `(lon − minLon) × scale` en x,
`(maxLat − lat) × scale` en y, `scale = 1000 / (maxLon − minLon)`. Les repères
de `mapLandmarks` élargissent le cadre avant le calcul, pour que Kisangani ou
Goma ne collent pas au bord.

**Simplification Douglas-Peucker, à tolérance variable** :

| Constante | Valeur | Usage |
|---|---|---|
| `TOL_OVERVIEW` | 0,08 (~9 km) | zones sans cas, carte nationale |
| `TOL_OVERVIEW_AFFECTED` | 0,02 (~2 km) | zones touchées — plus de détail là où on regarde |
| `TOL_PROVINCE` | 0,009 (~1 km) | zones de la province affichée |
| `TOL_PROVINCE_AROUND` | 0,05 (~5 km) | voisines, réduites à une silhouette |
| `TOL_DETAIL` | 0,005 (~500 m) | réservé au GeoJSON |

`simplify_safely()` redescend par paliers (tolérance, /4, /16, 0) : une zone
urbaine — Goma, Bunia, celles de Kinshasa — est plus petite que la tolérance et
**disparaîtrait** de la carte si on la simplifiait telle quelle.

**LA NOTE SUR LES DATES ABSENTES DU CURSEUR N'APPARAIT QUE PENDANT QU'ON LE
MANIPULE.** Sur 95 bulletins, 12 n'ont pas de detail par zone (huit dans les
deux premieres semaines de mai, le 16 juin, du 6 au 8 aout) : le curseur n'a
que 83 positions et la date saute. La note l'explique — c'est le principe
« quand la source ne dit pas, le site le dit » — mais elle etait affichee en
permanence, a tous, avec le poids des boutons, pour une question que seul le
lecteur qui deplace le curseur se pose. Depuis le 27 aout, `.map-timeline`
recoit `is-historical` des que le curseur quitte sa derniere position, et la
note n'est visible que dans cet etat.

Piege : « au repos » se teste sur `slider.max`, PAS sur `ZONES_HISTORY.length`.
Quand le dernier instantane de zones porte la date du dernier bulletin, il n'y
a pas de cran « aujourd'hui » a part et la derniere position EST le dernier
instantane — un test sur la longueur de l'historique montrait la note en
permanence. Et cette derniere position PORTE LA DATE DES DERNIERES DONNEES,
jamais « Aujourd'hui » : le bouton est ecrit avec la date par `build_pages`
(`timelineLatest`, sur `meta.reportingDate`), donc juste avant que le script
ne tourne et sans lui ; la cle i18n `timelineToday` a disparu. Demande du
proprietaire du 27 aout — « aujourd'hui » n'est pas la date d'un bulletin. Le libelle a aussi perdu son sigle : « Certains bulletins ne
detaillent pas les zones : ces dates sont absentes du curseur. »

**L'ORDRE DE LA BARRE LATERALE SUIT LE PARCOURS DU LECTEUR.** Depuis le
27 aout : Vue d'ensemble, Donnees detaillees, Chronologie, Le virus, FAQ,
Sources & bulletins, A propos (`mainNav` dans `site/pages.json`). Que se
passe-t-il, en detail, comment en est-on arrive la, c'est quoi ce virus, une
question, d'ou viennent les chiffres, qui fait le site. La chronologie
remonte pres des donnees dont elle est calculee ; les sources descendent
pres d'A propos, la ou l'on vient verifier — leur signal de serieux, la
ligne « Dernier bulletin officiel » de la barre le donne deja sur chaque
page. Le pied de page avait deja cette logique (Explorer / Comprendre / Le
site) ; la barre lui est enfin coherente.

**MOINS DE BOITES, PLUS DE TRAITS.** Depuis le 27 aout, un etat actif est un
trait, pas un fond : les boutons de carte (`.map-btn`), les bascules
(`.subtab-btn`) et les langues (`.lang-btn`) sont des onglets — texte gris,
actif en encre avec un filet de 2 px dessous dans la couleur d'accent, filet
transparent sur les inactifs pour que rien ne saute au clic. Le lien courant
de la barre laterale porte un filet de 3 px a gauche (`box-shadow: inset`)
au lieu d'un fond bleu pale. Seul `.share-btn` garde sa bordure : c'est une
action, pas un etat. Sous la carte, un filet vertical discret separe le
cadrage (« RDC entiere / Epicentre ») de la lecture (« Zones / Cercles ») :
sans bordures, les quatre mots se lisaient comme un seul groupe. **Sur
telephone, ces quatre commandes redeviennent des encadres** (demande du
proprietaire) : au doigt, un cadre dit « ici on appuie » mieux qu'un mot
souligne ; le filet vertical disparait avec, la ligne s'enroulant. Idem pour
les bascules des graphiques et des tableaux (`.subtab-btn`) sous 900 px :
sept onglets soulignes enroules sur trois lignes se lisaient comme du texte.
Sur ordinateur, tout reste en traits. Le pied de
page a ete mis en une ligne puis REMIS en quatre colonnes a la demande du
proprietaire — ne pas le rouvrir. Le titre et les cartes de provinces restent
tels quels par choix explicite.

**LA PONCTUATION FRANCAISE EST INSECABLE.** Depuis le 27 aout, dans les
textes francais de `site/strings.json` (bloc `fr`, et les valeurs `fr` des
blocs cures) et d'`assets/js/i18n.js` (bloc `fr`) : fine insecable U+202F
avant `?`, `!`, `;`, insecable U+00A0 avant `:` et a l'interieur des
guillemets « ». Sur telephone, trois questions de la FAQ finissaient par un
« ? » seul en debut de ligne. Une nouvelle chaine francaise doit suivre la
regle — l'espace ordinaire avant `?` est une faute, pas une variante. Dans
`i18n.js`, le remplacement n'a touche que l'interieur des chaines : les
ternaires ` ? ` / ` : ` du code sont intacts, et `node --check` passe.

**LES BULLES SONT EN PIXELS ECRAN, ET LA LEGENDE LES SUIT.** Jusqu'au
27 aout, rayon = `circleScale` x racine(cas) en unites du viewBox (1 000 de
large), puis tout le dessin etait reduit a la largeur du cadre (x 0,70 sur
ordinateur, x 0,32 sur telephone) — sauf la legende, dessinee en pixels : le
cercle « 500 » y etait plus gros que Bunia et ses 1 317 cas. Le proprietaire
l'a vu. Depuis : `renderCircles()` et `applyView()` annulent, en plus du
zoom, la reduction du dessin (`pixelsParUnite()`), donc un rayon de 22 fait
22 px a l'ecran quelle que soit la largeur ; `coefficientCercles()` prend
`circleScalePhone` (0,5) sous 760 px et `circleScale` (1,0) au-dessus, parce
qu'une carte de 320 px ne porte pas les memes cercles ; et
`renderCircleLegend()` redessine la legende (meme geometrie que
`circle_legend_html`) au coefficient en vigueur, a chaque rendu et au
redimensionnement. Le SVG statique du generateur reste le point de depart et
le repli sans JavaScript. Verifie a 360 et 1 280 px, cadrage pays et
epicentre : Bunia 18,1 px / 36,3 px, exactement racine(1317) x k, et le
cercle « 1 000 » de la legende 15,8 / 31,5 px. Consequence visible sur
ordinateur : les bulles ont grossi de ~40 % (Bunia 25 -> 36 px) ;
`circleScale: 0.7` restituerait l'ancienne taille, legende comprise.

**SUR TELEPHONE, LES DEUX LEGENDES DE LA CARTE ONT LA MEME HAUTEUR.** La
legende des cercles (titre + SVG de 81 px, dimensions fixees par
`circle_legend_html`) fait 104 px, celle des paliers en faisait 61 : au clic
sur « Cercles », les commandes sautaient de 43 px. Depuis le 27 aout, sous
900 px, les six paliers sont en deux colonnes (trois rangees, pas d'orphelin)
et `.map-legend` a 104 px de hauteur minimale. Si la legende des cercles
change de taille dans `build_pages`, ajuster ce minimum.

**LES COMMANDES SONT DES ENCADRES, A TOUTES LES LARGEURS.** Depuis le
27 aout au soir, a la demande du proprietaire — qui a d'abord choisi les
encadres sur telephone, puis les a voulus aussi sur ordinateur : `.map-btn`
(cadrage et lecture de la carte, Lecture et bouton-date des pages province)
et `.subtab-btn` (onglets des graphiques et tableaux, mois de l'archive)
sont des boites a bord fin, 32 px de haut sur ordinateur, 40 sur telephone.
L'etat actif est un cadre, pas un fond : bord de 2 px dans `--accent-strong`
(le bleu de la date) et texte gras `--accent-hover`, le second pixel en
ombre interieure (`box-shadow: inset`) pour que la boite garde sa taille —
rien ne saute au clic. Choisi sur planche de cinq variantes ; le pastel
`--accent-light` d'origine n'existait nulle part ailleurs sur la page, et le
fond plein accent fort, essaye d'abord, pesait trop avec deux boutons pleins
cote a cote. Ceci REMPLACE, pour ces deux familles, le « moins de boites,
plus de traits » du 27 aout au matin ; les langues (`.lang-btn`) et le lien
courant de la barre laterale restent des traits. Sur ordinateur, le filet
vertical entre cadrage et lecture est conserve ; il disparait sur telephone
ou la ligne s'enroule.

**LE « 17e » DU TITRE EST BLEU.** Sur telephone seulement, par construction
(span `.num` a l'interieur du span `.on-phone` de `homeLede`, trois langues) :
un nombre dans la couleur de « chiffre apres chiffre », droit, pas italique.
Sur ordinateur le meme echo passe par le kicker, deja bleu.

**SUR TELEPHONE, L'ACCUEIL S'OUVRE SUR L'EPICENTRE.** Decisions du 27 aout
au soir, toutes sous 760 px, regles en fin de `site.css` (elles doivent
l'emporter sur des blocs ecrits plus haut) :
- la carte s'ouvre cadree sur l'Ituri (`zoomToProvince('Ituri')` a
  l'initialisation dans `app.js`, meme seuil que le CSS) ; « RDC entiere »
  reste a un tap. Consequence : la carte est deplacable des le chargement,
  et `touch-action:none` lui aurait confisque le defilement de la page sur
  330 px — `pan-y` sur telephone, la carte se deplace a l'horizontale ;
- `setActiveMapBtn()` ne touche plus qu'aux deux boutons de cadrage : il
  retirait l'etat actif de « Zones colorees / Cercles » a chaque cadrage,
  defaut ancien que le cadrage initial rendait visible ;
- trois reperes de villes disparaissent (Kisangani, Isiro, Buta — 5 px de
  texte SVG a 360 px), cibles par `data-name` que `build_pages` pose sur
  chaque `.zm-mark` ; restent Kinshasa et Bunia ;
- les cinq chiffres du panneau en deux colonnes, letalite en pleine largeur
  dessous (267 px au lieu de 330) ;
- `.section` a 28 px de rembourrage au lieu de 40 : ~150 px de moins sur
  la page.

**SUR TELEPHONE, MOINS DE COMMANDES ET DES LISTES PLUS COURTES.** Decisions
du 27 aout, toutes sous 760 px, rien ne change au-dessus :
- plus de bouton « Lecture » sur les cartes (accueil et provinces) — le
  curseur se deplace au doigt ; sur les pages province la date n'est ecrite
  qu'une fois, au bout du curseur, sans l'etiquette « Evolution dans le
  temps » ni le bouton-date (tirer le curseur au bout fait la meme chose) ;
- tableau des provinces : « % pays » au lieu de « Part du pays » (span
  `.on-phone` dans `provinceTh3`, le `th` est passe en `data-i18n-html`), et
  les noms de province ne se coupent plus. Le partage de tableau lit
  `innerText`, pas `textContent`, pour n'emporter que le libelle affiche ;
- Sources : une ligne par bulletin — numero, date, icone — au lieu d'une
  carte de 80 px ; la page passe de 6 700 a 4 500 px. Le prefixe
  « Situation au » vit dans un span `.rc-date-prefix` masque sur telephone,
  produit par `situation_html()` (Python) et `dateBulletin()` (JS), qui
  decoupent la chaine de traduction autour de la date pour valoir dans les
  trois langues ; `report_chip()` ne re-echappe donc plus `date_text` ;
- pied de page en 2 x 2 au lieu de quatre blocs empiles (640 px).

**SUR TELEPHONE, LA CARTE DE L'ACCUEIL TIENT DANS LE PREMIER ECRAN.** Depuis
le 27 aout, sous 760 px : le kicker « 17e epidemie d'Ebola en Republique
democratique du Congo » disparait — tout sauf « 17e » repetait le titre — et
le « 17e » passe dans le titre par des spans `.on-phone` / `.on-large` dans
`homeLede` (FR : « l' » devient « la 17e » ; EN et SW n'ont qu'un span).
Le libelle « Cas par zone de sante » (`.section-head-carto`) sort de la mise
en page mais reste lisible aux lecteurs d'ecran : la legende sous la carte
dit deja « Cas confirmes cumules ». A 360 px la carte commence a 248 px au
lieu de 320 et sa legende finit a 635 px — tout tient dans un ecran de
telephone. Sur ordinateur rien ne change : kicker et libelle restent. Le
choix du 27 aout etait celui-ci plutot qu'un paragraphe d'entree : un
paragraphe aurait repousse la carte plus bas qu'avant.

**SUR TELEPHONE, L'EN-TETE TIENT SUR UNE LIGNE.** Depuis le 27 aout : marque,
langues et bouton de menu sur la meme rangee, 77 px au lieu de 130 — sous
900 px `.sidebar` passe en ligne, le bouton (frere de `.side-head` dans le
gabarit) se pose a droite des langues au lieu d'occuper seul une seconde
rangee. Le budget est serre : marque 148 px sur une ligne (`white-space:
nowrap`, sinon « ebola- / tracker.org » rendait la rangee plus haute
qu'avant), langues a 35 px presque contigues, et un cran de plus sous 340 px
(titre 14,5 px, langues 31 px). `mesurerEntete()` dans `app.js` lit desormais
la hauteur de la barre elle-meme, panneau fixe exclu ; le repli CSS de
`--entete` est 77 px. Verifie a 360, 340 et 320 px.

**SOUS 1 600 PX, LE PANNEAU ET LA BARRE LATERALE SE RESSERRENT.** Le
proprietaire, ses deux ecrans cote a cote, trouvait le panneau a droite de la
carte « clairement plus grand » sur le 13 pouces. Il ne l'est pas en pixels —
300 px partout — mais en PART de la colonne : un quart sur un 13 (1 470 px de
large), un cinquieme sur un 15 (1 728). Tout ce qui est fixe pese plus lourd
sur un petit ecran. Palier a 1 600 px : panneau a 250 px, barre laterale a
210, chiffres un cran plus petits ; la carte recupere ~80 px, un dixieme de
sa largeur. Un 15/16 pouces en plein ecran ne voit rien changer — sauf si
la fenetre est plus etroite que 1 600 px, c'est la largeur de la fenetre qui
compte, pas l'ecran.

**RIEN NE FLOTTE SUR LA CARTE DE L'ACCUEIL.** Sur un 13 pouces, les quatre
boutons poses en haut de la carte — cadrage a gauche, zones/cercles a droite
— recouvraient le nord du pays, la ou sont les cas. Depuis le 27 aout, les
commandes vivent SOUS la carte, sur la ligne du curseur (`.map-controls` :
cadrage, lecture, date du curseur au bout), et la legende est seule sur la
carte, avec un voile a peine present. Meme demande d'epure, le meme jour :
plus de bouton date a cote de « Lecture » (ramener le curseur au bout fait
la meme chose ; `#timelineToday` n'existe plus sur l'accueil, le script le
tolere), plus d'etiquette « Evolution dans le temps » (un curseur date se
comprend seul), plus de note « Chaque forme est une zone de sante… OCHA »
sous la carte, et plus de « 28 zones touchees sur 36 » sous les cartes de
province. La provenance des traces vit desormais sur la page Sources
(`geoSourceTitle`/`geoSourceText`), avec les bulletins — la ou on vient la
chercher. Les pages province gardent leur curseur tel quel, avec son bouton
date : le chantier ne portait que sur l'accueil.

**LE PANNEAU A COTE DE LA CARTE EST DATE, PAS TITRE.** Depuis le 27 aout, son
etat de repos dit « Situation au 25 aout 2026 » — plus « Zones de sante
touchees », ni « 58 zones de sante touchees sur 519 » dessous. Ses cinq
chiffres sont le bilan national du dernier bulletin (`renderKPIs`), quelle
que soit la position du curseur : un titre de zones coiffait un total de
pays, et un compte de propagation detonnait dans une liste de bilan. La date
leve aussi une ambiguite : curseur sur le 15 juin, panneau au 25 aout — deux
dates, toutes deux ecrites. Le compte de zones vit en tete de `/donnees/`,
dans les jalons de la chronologie et dans l'`aria-label` de la carte.

Meme formule que les images partagees (`cartoAsOf` dans `strings.json`,
`chartShareAsOf` cote script), date DES DONNEES, ecrite par le generateur
(`seed.cartoAsOf`) et relue par `daterPanneauCarte` si `latest.json` est plus
recent que la page. Le survol ne change pas : nom de la zone, sa province en
note, retour a la date quand on quitte.

**LA CARTE A DEUX LECTURES, UNE BASCULE, JAMAIS LES DEUX A LA FOIS.** Depuis le
27 aout, la carte de l'accueil porte en haut a droite « Zones colorees /
Cercles ». Les zones colorees disent OU est l'epidemie ; les cercles disent
COMBIEN — leur SURFACE suit les cas (rayon = `circleScale` x racine des cas,
en unites du viewBox), la ou une zone rurale immense ecrase Bunia, une ville
de quelques kilometres carres. Une seule carte : meme cadre, meme curseur de
temps, meme panneau, meme zoom. Deux cartes auraient tout duplique et double
la hauteur sur telephone. Et jamais cercles sur zones colorees : ce serait
encoder deux fois la meme variable — en mode cercles, les zones touchees
gardent une teinte a peine marquee, pour que l'etendue reste lisible sous la
grandeur.

- **Les points viennent des coordonnees GPS de l'ancienne carte Leaflet**
  (`HEALTH_ZONE_COORDS` du site d'origine), reprises dans
  `site/pages.json` > `zoneCoordinates` : le chef-lieu ou l'hopital, pas le
  centre du polygone — Bunia, la ville, est au bord de sa zone. `zone_points()`
  les projette avec la meme plate-carree que `build_geo.py` et les emet dans
  `window.ZONE_POINTS`, indexes par `normalise_zone(nom)` — `pointKeyOf()` en
  JavaScript reproduit cette normalisation. Une zone sans GPS prend le centre
  de son emprise (`data-box`). Pour en ajouter une : `zoneCoordinates.places`,
  `[lat, lon]`.
- **Les cercles ne grossissent pas avec le zoom**, comme les reperes : chacun
  recoit l'echelle inverse autour de son point (`map.bubbles` dans
  `applyView`). La legende reste donc exacte a tout niveau de zoom.
- **Ils ne captent pas la souris** : la zone dessous porte le survol,
  l'infobulle et le clic. Les gros sont dessines d'abord, les petits restent
  visibles par-dessus.
- **La legende est dessinee par le generateur** (`circle_legend_html`), avec
  la meme formule que les cercles : six etalons (`circleLegend` : 1, 10, 50,
  100, 500, 1 000) a l'echelle exacte. Le plancher `circleMinRadius` (2,5)
  vaut pour les deux — sans lui une zone a un cas faisait un pixel.
- **Le curseur les anime** : `renderMap` collecte les cas de chaque zone au
  passage et `renderCircles` redessine la couche. Rien a synchroniser.

La bascule n'existe que sur l'accueil ; les pages province gardent les zones
colorees, `setupMapModes` se tait sans `#mapModeNav`.

**SIX PALIERS DE COULEUR, ET LA LEGENDE LES MONTRE TELS QUELS.** Depuis le
27 aout, `zoneThresholds` vaut `[10, 50, 200, 500, 1000]` dans
`site/pages.json` : six classes au lieu de quatre. A quatre, Bunia (1 317 cas)
portait la meme couleur que Lita (204) — la classe haute avalait les quatre
foyers qui font l'epidemie. La distribution du SitRep 103 se repartit
26 / 14 / 11 / 3 / 3 / 1, Bunia seule tout en haut.

Les six teintes sont `--map-1` a `--map-6`, distinctes de `--scale-1..4` qui
servent aussi a l'echelle d'incubation et a la pyramide des ages : changer la
carte ne doit pas repeindre le reste. Rampe calculee en OKLCH sur les teintes
existantes, six pas de luminance egaux (0,85 -> 0,30) — la contrainte d'une
echelle sequentielle est la monotonie de la luminance, pas l'ecart entre
voisins.

La legende etait un DEGRADE continu « faible -> eleve » alors que la carte n'a
jamais colorie qu'en classes : elle laissait croire a une echelle qui
n'existait pas. Elle liste desormais une pastille par palier, bornee en
chiffres (« 1–9 », … « 1 000+ »), generee par `legend_steps_html()` depuis la
MEME liste de seuils que les classes `is-N` : les deux ne peuvent pas
diverger. Les libelles sont des nombres, identiques dans les trois langues au
separateur de milliers pres. Sous 900 px elle passe en grille de trois par
ligne — en rangee libre, le sixieme palier restait seul a la ligne.

**MONGBWALU ETAIT GRISE SUR LA CARTE EN LIGNE, AVEC 605 CAS.** Decouvert le
27 aout en comparant, pour un visuel, les zones comptees et les zones
coloriees : le generateur colorie bien Mongbwalu et Nyankunde (il passe par
la table d'alias du fond de carte, « Mongbwalu » -> « Mongbalu » chez OCHA),
mais `renderMap` recolorie tout depuis l'historique des qu'il tourne, et
`zoneKey()` ignorait `window.ZONE_ALIASES` : les deux zones retombaient en
gris. Troisieme et septieme zones du pays, invisibles depuis la carte SVG.
`zoneKey` applique desormais les alias. **La verification a faire apres tout
changement de carte : compter les `.zm-zone:not(.is-0)` rendus contre les
zones a cas > 0 de l'instantane** — `scripts/verif/` n'a pas encore cet
outil, le script de session `manquantes.mjs` le faisait.

Corollaire : `zoneAliases` dans `site/pages.json` complete les alias que
`build_geo.py` deduit de `latest.json` — il ne peut pas connaitre « Gety »,
orthographe des bulletins de juin a aout, quand le dernier ecrit « Gethy ».
`build_pages` fusionne les deux tables au chargement de `geo`.

**Le croisement se fait par clé normalisée**, jamais par nom affiché. Chaque
zone porte une `key` (accents retirés, casse et séparateurs écrasés) qui sert
de pont entre le shapefile, `latest.json` et `zones-history.json`.

**Bambu clignote fin mai, et c'est voulu.** Colorée le 21 mai, grise le 22,
grise encore du 23 au 28, coloree a partir du 29. Relu dans les PDF le 27 aout :
le SitRep 007 (21 mai) lui compte 1 cas confirme — la colonne se somme a 83,
le total national du jour ; le 008 (22 mai) l'oublie dans son tableau, et cet
instantane de mai n'a pas recu le report de derniere valeur qui existe depuis ;
le 009 (23 mai) la remet a 0 confirme — c'est l'INSP qui retire le cas, pas
nous ; le 015 (29 mai) en compte 2, avec 2 deces, probablement les 2 deces
suspects du 23 confirmes post mortem. Trois faits, pas une erreur et son
correctif. Le proprietaire a tranche : **on ne touche a rien** — ni reecrire le
21 mai (ce serait le premier instantane a contredire son bulletin), ni
reprendre le 22 a la main. Ne pas rouvrir.

**Le curseur de temps** lit `zones-history.json` : un instantané des zones par
bulletin. Une zone absente d'un instantané n'est pas coloriée à cette date.
C'est pourquoi le rattrapage de la zone Tshopo a dû reprendre neuf instantanés
un par un.

---

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

## Les 52 scripts, par famille

- **Pipeline** — `download_all_sitreps`, `update_data`,
  `extract_contacts_followup`, `extraire_deces_lieu`, `build_pages`,
  `check_coherence`.
- **Corpus** — les sept ci-dessus, plus `prototype_riposte`.
- **Rattrapage** — `backfill_zones_history` (un bulletin précis),
  `backfill_province_history` (tout, depuis les PDF).
- **Géographie** — `build_geo` (contours OCHA → geojson),
  `geocode_health_zones` v1 et v2, `extract_health_zone_polygons`.
- **Images sociales** — `construire_og` v1/v2/v3, `construire_avatars`,
  `rendu_image.mjs`.
- **Enquête** — huit `scan_*`, huit `inspect_*`, deux `diagnose_*`. Écrits pour
  répondre à une question ponctuelle sur le corpus, gardés comme exemples.
  `inspect_report.py` et `scan_missing_dates.py` sont les plus réutilisables.
- **Vérification visuelle** — `audit_mobile.mjs` et `scripts/verif/`.
- **Divers** — `message_reseaux` (message X), `dump_i18n.mjs` (appelé par
  `build_pages`).

---

## Les tableaux détaillés

**Une règle traverse tout : ce qui compte est écrit en dur à la génération.**
Les chiffres du dernier bulletin sont dans le HTML, donc visibles sans
JavaScript, donc indexables — et lisibles sur une connexion qui laisse tomber
le script. Le JavaScript n'ajoute que ce qui bouge.

### `/donnees/` — deux vues

Un premier niveau d'onglets, `zonesViewNav`, bascule entre deux lectures :

**« Par province »** — six lignes **écrites en dur** par `build_pages.py`
(`provinceSummaryBody`), triées par cas décroissants. Huit colonnes depuis le
25 août : province, cas cumulés, **part du pays**, décès, létalité, zones
touchées, nouveaux cas 24 h, **nouveaux décès 24 h**. Chaque ligne porte la
pastille de couleur de sa province.

La part du pays était accolée au cumul, entre parenthèses ; elle a sa colonne,
sinon les chiffres ne pouvaient pas s'aligner. Les nouveaux décès d'une
province se calculent en additionnant communauté et intra-CTE — les lignes de
province portent les quatre colonnes du bulletin, la somme y est donc exacte,
**à la différence des lignes de zone** où il faut passer par le total (voir
« Pièges connus »).

**Ce tableau est écrit deux fois** : par le générateur, puis réécrit par
`renderProvinceSummary()` dès que `latest.json` charge. Toute colonne ajoutée
d'un côté doit l'être de l'autre, sinon elle disparaît une demi-seconde après
l'affichage.

**Les colonnes de chiffres sont alignées à droite** (`class="is-num"`), avec
des chiffres à chasse fixe : c'est la seule façon de comparer 4 655 et 728
d'une ligne à l'autre. Les en-têtes suivent, sinon ils flottent à gauche
au-dessus d'une colonne alignée à droite — piège vu le 25 août, les en-têtes
du tableau par zone étant écrits par le JavaScript et non par le gabarit.

**Ce qui élargit une colonne, c'est son en-tête, pas son chiffre.**
« NOUV. DÉCÈS (24H) », insécable, imposait 186 px pour afficher « +23 ». Le
remède est `white-space:normal` sur les en-têtes numériques, avec un plafond
calibré sur le mot le plus long (« TOUCHÉES », ~55 px) : à 8ch il débordait sur
la colonne voisine, 80 px le replie proprement. Les colonnes tombent alors de
107/166/186 px à 135/144/144.

**Fausse piste à ne pas rouvrir : `width:1%` sur les colonnes de chiffres.**
Il les réduit bien à 51-62 px, mais le tableau occupe 1 142 px quoi qu'il
arrive et les 743 px restants tombent sur le nom de province. Le vide ne
disparaît pas, il se déplace au milieu de chaque ligne. Le vide résiduel est
structurel : ~700 px de contenu pour 1 142 px de large.

**« Par zone de santé »** — **entièrement rendue par le JavaScript**
(`renderZonesTable`), zéro ligne dans le HTML. C'est le seul tableau du site
dans ce cas, parce qu'il est interactif :

- **Six colonnes triables** — nom, province, cas cumulés, décès, létalité,
  nouveaux cas 24 h. Tri par défaut : cas décroissants. L'en-tête affiche ▲/▼.
- **Une recherche** par nom de zone, insensible à la casse.
- **Un filtre par province** (`zonesSubtabNav`), rempli dynamiquement.
- **Un état vide** explicite quand le filtre ne donne rien.

### Les badges

**Létalité** — trois seuils dans `cfrBadgeClass()` : `low` sous 30 %, `mid`
sous 50 %, `high` au-delà. Ils sont repris à l'identique par le générateur pour
les tableaux statiques, pour que les deux lectures ne se contredisent pas.

**Nouveaux cas** — `has-new` avec un « + » quand il y en a, `no-new` sinon. Un
zéro reste affiché : l'absence de cas est une information, pas un vide.

### La largeur des tableaux

Trois tableaux ont ete resserres le 26 aout, sur le meme principe : les
colonnes de chiffres a **largeur egale**, la colonne de libelle a ce qu'il lui
faut, et le cadre cale sur le tableau au lieu de s'etirer sur toute la colonne.

| Tableau | Avant | Apres |
|---|---|---|
| zones d'une page province | 1 112 px | **670 px** |
| « par province » de `/donnees/` | 1 127 px | **878 px** |
| « par zone de sante » de `/donnees/` | 1 142 px | **896 px** |

**Trois pieges rencontres dans cet ordre, tous invisibles dans le code.**

1. `width:fit-content` sur le panneau ne suffit pas : le cadre interieur porte
   `overflow-x:auto`, ce qui en fait un bloc de formatage independant prenant
   100 % de la largeur offerte quel que soit son contenu. Il faut le caler lui
   aussi (`.panel-fit .table-scroll`).
2. Un bloc en `fit-content` se cale sur son enfant **le plus large**. La note
   `zonesSumNote`, une longue phrase, l'emportait sur le tableau et rendait le
   calage sans effet. Elle est sortie du panneau, dans un `.zones-block` qui
   enveloppe les deux, avec `width:0;min-width:100%` : largeur intrinseque
   nulle — donc invisible au calcul — puis etirement a 100 % du bloc une fois
   celui-ci dimensionne par le tableau. **`min-width:100%` a l'interieur d'un
   panneau lui-meme en `fit-content` se resout a zero** : la note doit etre
   soeur du panneau, pas sa fille.
3. Les en-tetes du tableau par zone sont ecrits par `app.js` avec un
   `white-space:nowrap` en style **inline**, qui l'emporte sur la feuille de
   style. A 104 px, « Nouv. décès (24h) » debordait de sa colonne. Le nowrap
   est desormais reserve aux colonnes de texte.

**Fausse piste deja ecartee, ne pas la rouvrir** : `width:1%` sur les colonnes
de chiffres. Elle les reduit bien, mais le tableau occupe alors toute la
largeur quand meme et le reliquat tombe sur la colonne de libelle — le vide ne
disparait pas, il se deplace au milieu de chaque ligne.

**La vue « par zone » garde sa barre de recherche et son filtre** : ils
s'adaptent a la largeur du tableau sans la dicter, comme la note.

### Les pages province

**Cadres numérotés, depuis le 8 septembre 2026.** À la demande du propriétaire
(« ça structure le visuel »), la page Données et les pages province
reprennent l'idiome de Riposte & défis : `section.cadre-fiche` avec
`.fiche-tete` (numéro serif `.fiche-num`, `.frame-title`, `.section-sub`)
puis `.cadre-corps`. Données : 01 Combien, 02 Où, 03 Qui, 04 Que fait-on
(les anciens `.section-split` à deux colonnes ont disparu). Province : 01
carte, 02 zones, 03 courbe quand elle existe (seuil
`SEUIL_COURBE_PROVINCE`), puis la frise — 04, ou 03 sans courbe ; le
numéro se passe à `province_chart_html()` et `province_timeline_html()`.
La note « Comment lire ces chiffres » reste hors numérotation.

**La frise des pages province, depuis le 8 septembre 2026.** Le propriétaire
avait d'abord fait construire quatre blocs (riposte de la province, lieu du
décès, obstacles cités, chronologie verticale des zones), puis les a fait
retirer le jour même au profit d'une seule chose : **la piste horizontale
de l'accueil**, mêmes classes `.timeline-h.is-inline` / `.th-track` /
`.th-item.is-*`, mêmes flèches (`id="timelineTeaser"`, celui que
`initTimelineScroller` attend, absent ailleurs d'une page province), même
légende `.tl-legend`, mêmes couleurs — bleu jalon officiel, ambre extension
géographique, rouge seuil franchi, vert dernier bilan. Rendue par
`province_timeline_html()` via `common_seed["provinceTimelines"]` et le
jeton `province.timeline`. Les jalons : l'arrivée de l'épidémie
(`provinceArrivals`, dates dans la prose ; « Le foyer de l'épidémie » pour
l'Ituri), les seuils de cas et de décès, les paliers de zones touchées, le
dernier bilan. **Les seuils s'adaptent à la province** : `pas_arrondi()`
choisit un pas 1, 2 ou 5 fois une puissance de dix pour obtenir environ six
jalons quel que soit le maximum — 1 000 cas en Ituri, 200 au Nord-Kivu, 50
au Haut-Uélé, 5 dans la Tshopo, 1 au Sud-Kivu ; cinq paliers pour les
zones. Les zones gardent l'identité de `zone_milestone_events` (alias des
tracés, deux lettres près dans la province). Textes `provinceTimeline*`
dans `strings.json`, trois langues.

`province_zones_table_html()` produit un tableau statique des zones touchées de
la province, trié par cas décroissants. Les variations de 24 h ont **leur
propre colonne** depuis le 26 août : entre parenthèses, accolées au cumul,
elles empêchaient d'aligner les chiffres et se lisaient comme une note. Six
colonnes, dans l'ordre du tableau de `/donnees/`.
Suivi d'un lien vers le tableau complet filtré sur cette province.

### `/rapports/`

Le titre « Sources et bulletins officiels » (30 caractères) tient sur une
ligne depuis le 5 septembre 2026 : `.page-title` plafonne à 22ch, et cette
page seule porte `page-title--large` (`max-width:none`) — sans `nowrap`, le
titre se replie encore de lui-même sous 360 px. Les autres titres gardent
le plafond.

Un paragraphe d'introduction (`reportsPageIntro`, trois langues, classe
`page-intro` sous le titre) dit ce que la page est — le site ne produit
aucun chiffre, il compile ceux des institutions qui suivent l'épidémie, et
cette page en rassemble les documents tels que publiés, pour remonter à
l'original. Volontairement **général, sans nommer les sources** : une
première version les énumérait, le propriétaire l'a fait retirer le
5 septembre 2026 (« un paragraphe plus général sans préciser les
sources »). Les trois sections sont **numérotées** dans `i18n.js` —
« 1. SitRep quotidien (INSP) », « 2. Weekly External Situation Report
(OMS) », « 3. Autres sources » (ex-« Fond de carte », qui ne contient
encore que la provenance des contours) — ; le numéro fait partie de la
chaîne, il apparaît donc aussi dans l'`aria-label` du filtre par mois. Le
swahili n'est pas relu.

**Rapports OMS : 16 archivés, jusqu'au n°16 (données au 30 août 2026),
ajouté le 5 septembre.** Le propriétaire avait transmis un lien IRIS qui
était en fait le bitstream du n°12, déjà archivé (SHA-256 identique) ;
le n°16 a été retrouvé par l'API IRIS (`/discover/search/objects`, puis
`/core/items/<uuid>/bundles` → ORIGINAL → bitstreams), première page
vérifiée. La liste `WHO_REPORTS` de `download_who_sitreps.py` reste la
source de vérité ; `build_who_reports_index.py` reconstruit
`who-reports.json` depuis les noms de fichiers.

`report_chip()` produit une carte par bulletin, **cliquable dans son entier** —
auparavant seule la petite icône était un lien, cible minuscule et carte qui
paraissait inerte. Une navigation par mois et une recherche filtrent la liste
côté client. Les rapports OMS ont leur propre liste.

---

## Les graphiques

Onze modes dans `app.js`. Chaque canevas déclare son sujet par `data-chart`,
chaque onglet par `data-mode`.

| Mode | Source | Où |
|---|---|---|
| `epidemic` | `sitreps.json` | accueil **et** premier onglet de `/donnees/` |
| `newCases` | `sitreps.json` | onglet, trois vues (jour, semaine, mois) |
| `newDeaths` | `sitreps.json` | onglet, **le meme bloc de code** que `newCases` |
| `provinceEpidemic` | `province-history.json` | les six pages province |
| `byProvince` | `province-history.json` | onglet |
| `contactsFollowUp` | `contacts-followup.json` | onglet |
| `deathsPlace` | `deces-lieu.json` | onglet |
| `pyramide` | `demographie.json` | onglet |
| `ages`, `sexes` | `demographie.json` | code sans bouton |
| `communityDeaths` | `community-deaths-daily.json` | code sans bouton, **défectueux** |

### Ce que chacun montre

**`epidemic`** — barres des nouveaux cas quotidiens sur l'axe gauche, deux
courbes de cumul (cas en bleu, décès en rouge) sur l'axe droit. Les deux ordres
de grandeur ne se comparent pas : une centaine contre plusieurs milliers, un
axe unique écraserait les barres. Une seconde série de barres, translucide,
isole les deux dates de rattrapage administratif.

`epidemic` **n'a plus de bascule** — elle appartient depuis le 26 aout a
l'onglet `newCases`, avec un troisieme pas de temps. Le graphique redevient ce
qu'il etait : le quotidien, et les cumuls par-dessus.

**`newCases` et `newDeaths`** — la meme serie que `epidemic`, lue a trois pas
de temps par une bascule interne, meme idiome que la pyramide des ages : « Par
jour », « Par semaine », « Par mois ». Les barres seules, sans les courbes de
cumul : la vue repond a « combien de cas — ou de deces — cette periode », pas a
la comparaison des deux series, que `epidemic` porte deja.

**Un seul bloc de code pour les deux onglets.** Seuls changent le champ lu
(`confirmed` ou `deaths`), la couleur — bleu les cas, rouge les deces, comme
partout ailleurs — et les notes. Deux blocs jumeaux auraient diverge au premier
correctif.

**Et une seule bascule pour les deux**, `data-vue-periode`, avec un seul etat :
passer des cas aux deces garde le pas de temps choisi, et les deux se comparent
sans avoir a le regler deux fois.

Agreger absorbe le bruit de notification — un bulletin manquant creuse dans la
serie quotidienne un trou qui ne dit rien de l'epidemie — mais deplace le
probleme : toutes les periodes ne portent pas le meme nombre de bulletins. La
note le dit a chaque vue.

**Un seul calcul pour les six vues, et pour `epidemic`.**
`partsQuotidiennes(s, champ)` produit les nouveaux cas — ou deces — d'un
bulletin au suivant, la part rapportee separee de la part de rattrapage ;
`agregeNouveauxCas(s, granularite, champ)` les regroupe par semaine ou par
mois, seules les bornes changeant. Les sept lectures ne peuvent donc pas
diverger. Les deux dates de rattrapage vivent dans une seule constante,
`RATTRAPAGE_ADMIN`.

**LA TEINTE CLAIRE NE DIT PAS « RATTRAPAGE », ELLE DIT « LA PERIODE NE PEUT PAS
REVENDIQUER CES CAS ».** La nuance decide de ce qu'on voit a chaque pas de
temps, parce que les deux rattrapages ne sont pas de meme nature :

- Le **30 juillet** nomme les journees qu'il rattrape — les 28 et 29, dont les
  bulletins manquent. La semaine du 27 et le mois de juillet contiennent ces
  trois dates : ces cas SONT les leurs, et ils y passent en couleur pleine.
  Les marquer aurait signale un doute la ou l'agregation venait de le lever.
- Le **22 juillet** est une harmonisation de bases DHIS2, et le bulletin ne dit
  pas quelle periode elle reprend. Aucune periode ne peut le revendiquer : il
  reste clair a toutes les granularites.

C'est ce que porte le champ `couvre` de `RATTRAPAGE_ADMIN` — les dates
rattrapees, ou `null` quand le bulletin se tait. `empanRattrapage(date)` en tire
l'empan des journees concernees, la date du bulletin comprise, et
`agregeNouveauxCas` bascule en couleur pleine tout empan qui tombe entierement
dans la periode. La vue quotidienne, elle, les separe tous les deux : a
l'echelle du jour, aucun des deux n'est a sa place.

**Le test porte sur l'empan, pas sur la part.** Cote deces la part du jour n'est
pas publiee, donc pas separable — mais les deces du 30 juillet sont ceux des 28,
29 ou 30, et une periode qui contient les trois les compte correctement quelle
que soit la repartition. Juillet passe ainsi de 444 a 272 cas en teinte claire,
et de 336 a 236 deces, sans qu'aucun total bouge.

**LE BOUTON DE PARTAGE VIT DANS LE CADRE DE CE QU'IL EXPORTE.** Pose au-dessus
du cadre, il partait a l'extreme droite de la colonne, au-dessus d'une zone
vide : les cadres de tableau sont en `panel-fit`, larges de leur contenu et non
de la page, si bien qu'un bouton range sur la largeur de la section se
retrouvait a 150 px du tableau, contre le bord de l'ecran. A cette place il se
lisait comme un element de page, pas comme une action sur la figure.

- Pour les graphiques, `.chart-actions` est le premier enfant du `.panel` : en
  haut a droite, DANS le cadre.
- Pour les tableaux, meme regle depuis le 27 aout : UN bouton par tableau,
  premier enfant du `.panel panel-fit`, donc aligne sur le bord droit du
  tableau lui-meme. Demande explicite du proprietaire, qui le voulait « juste
  en haut a droite de chaque tableau ». Trois cadres le portent — le resume par
  province et le detail par zone de `/donnees/`, le tableau de chaque page
  province — dans les trois langues.
- Le bloc d'actions n'elargit jamais son cadre : plus etroit que n'importe quel
  tableau, il ne pese pas sur le `width:fit-content` du panneau, et sous 390 px
  il reste cale sur la largeur visible pendant que le tableau defile dessous.

Le tableau de comparaison des especes de `/le-virus/` n'en recoit pas : ses
cellules portent de la prose, et `exporterTableau` est fait pour des chiffres —
il coupe le texte trop long.

**L'ALIGNEMENT D'UNE COLONNE EXPORTEE SE JUGE A SON CONTENU.** Il se lisait
dans la seule classe `is-num` de l'en-tete — et « Cas cumules » du tableau par
zone n'en porte pas, volontairement : a l'ecran son nombre est cale contre la
barre de proportion qui le suit DANS la cellule. L'image ne reprend que le
texte : la barre disparaissait, et le nombre restait seul a gauche au milieu
d'une colonne de chiffres alignes a droite.

`exporterTableau` complete donc l'en-tete par le corps — une colonne dont
toutes les valeurs sont des nombres (`EST_UN_NOMBRE`, les tirets et cellules
vides ne comptant ni pour ni contre) se cale a droite quel que soit son
`<th>`. Une regle plutot qu'une exception a retenir : le prochain tableau qui
melera une barre a un nombre sortira juste sans qu'on y pense. Les colonnes de
texte — « Zone de sante », « Province » — restent a gauche, verifie dans les
trois langues.

**Et le message de copie ne decrit plus le geste.** « Graphique copie — collez-le
ou vous voulez » est devenu « Graphique copie », a cote de « Tableau copie » :
le presse-papier n'a pas besoin qu'on explique a quoi il sert.

**L'IMAGE D'UN TABLEAU SE DATE, ELLE NE SE NUMEROTE PAS.** Sa legende haute
reprenait la ligne de fraicheur de la page — « 58 zones de sante touchees sur
151 · SitRep N°103 du 25 aout ». Elle porte desormais « Situation au 25 aout
2026 », dans les memes termes que les figures (`periodeTexte` sur
`currentMeta.reportingDate`, donc la date DES DONNEES et non celle de
publication). Un numero de bulletin ne se lit qu'ici ; une date se lit partout,
et l'annee est ecrite parce qu'une image circule longtemps apres. Ce que le
tableau montre — filtre de province, recherche en cours — reste devant, la date
ferme la legende. Effet de bord bienvenu : les pages province, qui n'ont pas de
`zonesTableSub`, exportaient une image sans aucune date. Le pied garde
« Sources : SitReps INSP » : c'est la provenance, pas un numero.

**ET LE MESSAGE DE CONFIRMATION NOMME CE QU'IL A COPIE.** Un tableau partage
disait « Graphique copie ». `partagerImage` prend donc une cle de message en
quatrieme argument, `chartShareCopied` par defaut, `tableShareCopied` pour les
tableaux — « Tableau copie », sans le « collez-le ou vous voulez » des figures :
demande du proprietaire, qui le voulait nu. Les deux autres etats (telechargee,
copie impossible) restent communs, ils ne nomment pas la figure.

**LES TABLEAUX SE PARTAGENT AUSSI.** Un tableau HTML ne sait pas s'exporter
comme un canevas : `exporterTableau` le redessine cellule par cellule, avec le
meme titre, le meme pied et la meme note que les figures. Aucune bibliotheque
de capture, rien qui s'execute avant le clic. Trois boutons : le resume par
province, le detail par zone, et le tableau de chaque page province.

Ce qui est exporte est ce qui est AFFICHE. Le corps du tableau des zones ne
contient que les lignes retenues par le filtre et la recherche : l'image reprend
donc l'etat lu, et le sous-titre nomme le filtre actif. Les colonnes prennent la
largeur de leur contenu ; si l'ensemble deborde, tout se resserre au prorata et
le texte trop long est coupe — jamais un nombre.

**Ce bouton a revele que le site publiait des chiffres faux.** Le tableau des
zones affichait « +312 nouveaux cas en 24 h » a Bunia quand le pays entier en
comptait 57. Les 28 zones de l'Ituri totalisaient 10 161. La cause : le SitRep
103 a decale d'un rang la cellule de letalite dans les lignes de zone, et
`row[4:]` lisait « 9,1% » comme 91 — `norm_int` retire la virgule.

`index_letalite_zone` repere desormais la letalite A SA FORME : un pourcentage
ne se confond avec rien sur cette ligne, tout ce qui l'entoure est un effectif.
Les cumules sont les cellules porteuses entre le nom et elle, la queue commence
apres. Les deux mises en page — celle du 102 et celle du 103 — se lisent avec le
meme code.

**Et `zone_row_looks_unreliable` ne testait que la TETE de la ligne.** Sur le
102, ses lignes etaient toutes jugees douteuses et reconstruites depuis le texte
brut, ce qui masquait le defaut ; sur le 103 elles ont des cas et des deces
justes, donc elles passaient, avec leur queue decalee. Le test porte maintenant
sur la letalite : si on ne sait pas la reperer, on ne sait pas non plus ou
commence la queue, et la ligne entiere est douteuse.

**Un controle de coherence manquait, il existe.** `check_coherence.py` comparait
les nouveaux DECES des zones au total de la province, jamais les nouveaux CAS.
La tolerance n'est pas zero — le bulletin lui-meme n'est pas toujours coherent
avec ses sous-totaux, et au 103 le Nord-Kivu comme le Haut-Uele depassent d'une
unite, ce que le site recopie fidelement. On alerte au-dela du double du total
declare : passe ce seuil, ce n'est plus une divergence de source, c'est une
colonne mal lue.

**L'IMAGE PARTAGEE EMBARQUE LES DEUX CADRES QUAND IL Y EN A DEUX.** La pyramide
des ages trace les cas a gauche et les deces a droite — deux ordres de grandeur
qui ne partagent pas d'axe, c'est justement pourquoi il y a deux cadres.
`exporterGraphique` n'en prenait que le premier : partagee, l'image disait
« voici les cas » quand le lecteur avait sous les yeux la comparaison des deux,
exactement ce que la note d'export cherche a empecher.

Le second cadre n'est joint que s'il porte un graphique ET qu'il est affiche —
jamais sur sa seule presence dans le HTML, sans quoi la vue « Parts », qui le
masque, aurait exporte un cadre vide. A deux figures, chacune recoit la moitie
de la largeur utile moins la gouttiere, garde SON rapport et se centre dans sa
moitie.

**Et la periode declaree s'arrete au dernier releve.** Le sous-titre de
« Deces en communaute » annoncait « du 13 juil. au 30 aout » quand les donnees
s'arretaient au 25 : c'etait le dimanche de la semaine en cours. La barre
couvre bien la semaine entiere — sa partie grisee le dit —, les donnees non.

**DEUX GRIS, ET LA DIFFERENCE EST REGLEE POUR TOUT LE SITE.** Hachure = une
donnee attendue qui manque. Gris uni = du temps qui n'a pas encore eu lieu.

Le graphique des deces par lieu confondait les deux : la semaine du 24 aout
portait deux releves sur sept, et son gris — cinq septiemes de l'emprise —
etait annonce « Jours sans donnee » alors qu'il ne contenait AUCUN jour
manquant, seulement cinq jours a venir. Une semaine se decompose donc en trois
parts et non deux : les releves recus, les journees passees sans lieu declare,
les journees a venir. Le plancher de lisibilite elargissant la barre au-dela de
sa part reelle, le gris se resserre d'autant, en gardant la proportion entre
les deux dernieres.

**Trois indices les separent, pas un.** Un seul aurait demande de comparer
deux carres cote a cote ; ensemble ils se lisent d'un coup d'oeil, sans crier.
Les deux styles vivent dans `GRIS_MANQUE` et `GRIS_A_VENIR`, definis une seule
fois : le plugin les dessine, la legende les montre, ils ne peuvent pas
diverger.

| | remplissage | texture | cadre |
|---|---|---|---|
| Jours sans donnee | aplat plein | hachures a 45 deg | trait continu |
| Jours a venir | aplat a 45 % | aucune | trait pointille |

Le sens commande la direction : « a venir » est le plus VIDE des deux, rien ne
s'y est encore passe. Aucun des deux ne prend de teinte : ce sont des neutres,
et une couleur en ferait une troisieme categorie de donnees.

Corollaire : la bande du mois en cours passe en gris UNI. Elle etait hachuree,
ce qui aurait fait dire a la hachure deux choses contraires d'un graphique a
l'autre. Et la pastille de legende de « Jours sans donnee » recoit un motif
hachure (`hachureLegende`) : sans lui, les deux cles sortaient comme deux
carres gris identiques, ce qui annulait la distinction qu'elles portent.

**Le compte de jours manquants de la note se calcule** — journees ecoulees de
la fenetre couverte moins journees documentees. Il etait ecrit en dur, juste au
moment ou il a ete ecrit, et perime au premier bulletin muet suivant.

**La bande grisee a sa cle de legende, un carre plutot qu'une pastille.**
Sans elle, ce gris pose a cote de deux couleurs pleines n'avait aucune cle de
lecture — il fallait descendre jusqu'a la note pour apprendre que le mois
n'etait pas fini. Meme mecanique que « Jours sans donnee » sur `deathsPlace` :
une entree poussee par `generateLabels`, sans jeu de donnees derriere, dont le
clic est neutralise puisqu'elle ne masque rien. Elle n'apparait qu'avec la
bande qu'elle explique — une legende qui nomme une couleur absente du trace est
pire que pas de legende —, donc jamais en vue quotidienne ni hebdomadaire.

**Le total s'affiche en pied d'infobulle des qu'une barre a deux parts.**
« Nouveaux cas : 1 996 » au-dessus de « Rattrapage : 272 » laissait l'addition
au lecteur, alors que c'est la somme qui repond a « combien de cas cette
periode ». `totalEmpile(items)` la pose, et il est branche sur les trois
infobulles qui empilent : `epidemic`, `newCases`/`newDeaths` a ses trois pas de
temps, et `provinceEpidemic`.

Il ne s'affiche QUE la ou il y a vraiment deux parts a additionner. Une journee
ordinaire n'en a qu'une, et le total repeterait la ligne du dessus. Les barres
de province non plus : la part du jour n'y etant connue qu'au niveau national,
la journee entiere bascule en teinte claire — le callback y est branche comme
ailleurs, il ne se declenche simplement jamais. Meme silence cote deces les
jours de rattrapage, ou la part du jour vaut zero et disparait du corps.

Les courbes de cumul sont ecartees de la somme — elles vivent sur l'autre axe,
et les ajouter aux barres donnerait un nombre qui ne veut rien dire. Le test
porte sur les items REELLEMENT affichees, celles que le filtre de l'infobulle a
laissees passer : c'est ce qui fait que la regle se tient sans cas particulier.

**La part de rattrapage n'est chiffree que pour les cas.** Les bulletins qui la
documentent annoncent « +97 » et « +73 nouveaux cas » ; rien d'equivalent pour
les deces, dont le cumul saute pourtant de 236 et de 100 ces jours-la. Faute de
part publiee, la journee entiere passe en teinte claire — meme choix que les
graphiques de province, ou la part n'est connue qu'au niveau national. On
marque l'incertitude, on ne la chiffre pas.

**Un bulletin peut paraitre sans porter le champ.** Deux ne donnent aucun total
de deces, les 17 et 19 mai : ils ne comptent pas comme releves de la periode,
et la note les enumere a cote des jours sans bulletin. La liste se recalcule,
comme le reste.

**La SEMAINE en cours est tracée depuis le 4 septembre 2026, comme le mois
en cours** (décision du propriétaire, « pour que les gens puissent vraiment
suivre en temps réel »), sur les quatre graphiques hebdomadaires : Nouveaux
cas et Nouveaux décès « par semaine », Nouveaux cas par province, alertes et
échantillons de la page Riposte. Même idiome que le mois : emprise pleine,
jours écoulés colorés au prorata du calendrier, jours à venir en gris uni à
droite jusqu'au sommet de la pile, entrée « Jours à venir » dans la légende,
« semaine en cours, arrêtée au … » dans l'infobulle, et la note nomme la
semaine et compte les jours grisés (`chartWeekOngoing`,
`chartWeekOngoingNote`, trois langues). `legendeAVenir()` ajoute l'entrée de
légende à n'importe quelle configuration, `semaineOuverte()` calcule les
ratios côté Riposte. Le masquage antérieur — à un jour sur sept la barre
tombait de 561 à 72 cas et se lisait comme une chute — n'est plus la règle ;
c'est la partie grisée qui empêche cette lecture, et la vue « par jour »
reste là pour le détail. Piège rencontré en le faisant : `GRIS_MANQUE`,
`GRIS_A_VENIR`, `hachureLegende` et le plugin `largeurSemaine` étaient
définis SANS indentation mais À L'INTÉRIEUR de `renderOneChart`, après le
bloc Riposte — « Cannot access 'largeurSemaine' before initialization » dès
que Riposte les appelait ; remontés au niveau du fichier, avant la fonction.
Le lieu du décès reçoit lui aussi le gris des jours à venir sur sa semaine
en cours (au prorata du calendrier, PAS des relevés : les barres restent
égales, décision du 29 août intacte), et les points des courbes — positivité
du laboratoire, moyenne du lieu du décès — suivent la partie colorée de la
barre ouverte au lieu du centre de l'emprise entière (second passage du
plugin sur les jeux `line`). Publié le 4 septembre.

**Le MOIS en cours, lui, est trace — depuis le 26 aout.** Il l'etait sous la
meme regle jusque-la, et le prix etait trop haut : trois barres pour quatre
mois de donnees, la plus recente etant justement celle qu'on vient chercher.
Ce qui separe les deux cas est le rapport entre ce qu'on voit et ce qu'on
attend. A un jour sur sept, une semaine ne montre que 14 % d'elle-meme et sa
barre ne dit rien ; au 24 aout, le mois en montrait 77 %.

**Il est trace de facon a rendre la lecture fausse difficile.** La barre garde
l'emprise pleine d'un mois ; la part correspondant aux jours ecoules est
coloree ; les jours qui restent a courir sont gris hachures a droite. Le vide
se voit avant la hauteur, et l'infobulle ouvre sur « mois en cours, arrete au
24 aout » plutot que sur « 24 releves sur 24 », qui se serait lu comme un mois
complet. C'est l'idiome de `largeurSemaine`, repris tel quel.

**Ce que la largeur encode ici, c'est du TEMPS, pas du volume.** La hauteur
reste ce qu'elle a toujours ete — les cas reellement rapportes, aucun chiffre
invente pour combler la fin du mois. C'est ce qui rend l'encodage admissible
alors que le paragraphe suivant l'ecarte des barres : il ne touche pas a l'axe
des valeurs. Et il ne porte que sur le mois OUVERT : mai commence au 14 et
couvre 18 jours sur 31, sa barre reste pleine, parce que ses jours manquants
sont passes et ne se rempliront jamais. Le gris dit « a venir », pas
« absent ».

Aucune date n'est ecrite : le mois cesse de lui-meme d'etre en cours au
bulletin qui le termine, et sa barre se colore alors entierement.

Le test porte sur « la periode est-elle finie » — le dernier bulletin va-t-il
jusqu'a son dimanche, jusqu'au dernier jour du mois — **et non** sur « a-t-elle
tous ses releves ». La distinction compte : une semaine passee amputee d'un
bulletin manquant reste affichee, son total etant definitif meme s'il est
sous-estime. Seule la derniere peut encore se remplir, et elle reparait
d'elle-meme au bulletin suivant, sans qu'aucune date soit ecrite dans le code.

**Les jours sans bulletin sont enumeres dans la note des trois vues, et
calcules.** Neuf sur la periode, de deux natures : les 15 et 16 mai, ou l'INSP
n'a rien publie — le n°001 du 14 mai est suivi du n°002 du 17 —, et sept dates
dont le bulletin manque a l'archive publique (003, 029, 043, 045, 063, 075,
076). La liste se recalcule a chaque rendu : un tel decompte se perime au
premier trou suivant.

**Le compte de releves d'une periode se rapporte aux jours ATTENDUS**, la
periode ramenee aux dates que la serie couvre : mai ne commence qu'au premier
bulletin, le 14, et ses 31 jours de calendrier le feraient passer pour un mois
a moitie renseigne. C'est ce compte que l'infobulle annonce — « 15 releves sur
18 » — et lui qui decide si la note compte la periode comme incomplete.

**Les barres sont jointives a 6 % pres.** Un large espace se lirait comme une
periode sans cas ; des barres collees empechaient de distinguer une periode de
sa voisine. Chaque colonne hebdomadaire porte sous elle la periode couverte sur
deux lignes ; un mois se nomme, il n'a pas besoin de ses bornes.

**Aucun encodage de COUVERTURE sur ces barres.** La vue hebdomadaire passait
`largeurSemaine` sans jamais lui donner de ratios — le plugin ne faisait donc
rien, et il est parti. Encoder la part de releves recus ne se fait honnetement
que la ou la hauteur n'est pas un volume : les parts empilees a 100 % de
`deathsPlace`. Ici la hauteur EST un volume, et une semaine a demi hachuree
parce qu'il lui manque trois bulletins resterait comparable a tort — son total
est pourtant definitif.

Le mois en cours n'est pas une exception a cette regle, il tombe a cote :
`largeurSemaine` y recoit des ratios de TEMPS ECOULE, pas de couverture. Une
barre ainsi hachuree n'est justement pas comparable, et c'est ce qu'elle
annonce. La distinction est la meme que celle qui gouverne le masquage — « la
periode est-elle finie », et non « a-t-elle tous ses releves ».

**`provinceEpidemic`** — même forme, aux couleurs de la province, avec sa
courbe de décès. Absent sous 50 cas cumulés. Signale les trous de plus de trois
jours au lieu de relier par-dessus.

**Son axe est un calendrier jour par jour depuis le 21 septembre 2026.** Il ne
portait que les jours de bulletin, collés les uns aux autres, et les journées
sans bulletin disparaissaient de la vue : vingt au Nord-Kivu (104 relevés pour
124 jours), dix-huit en Ituri, sept au Haut-Uélé. La barre du 17 juillet, qui
porte les cas du 16 et du 17, se lisait comme une journée ordinaire, et rien ne
distinguait une série continue d'une série à trous. Le calendrier rend à chaque
jour sa place : un jour sans bulletin est un blanc de la largeur d'une barre, et
le trou de douze jours du 20 au 31 mai se voit enfin pour ce qu'il est. Même
idiome que le suivi des contacts et les taux de la riposte, où il sert depuis le
début à donner aux trous leur vraie largeur. Trois conséquences :
- **Les cumuls traversent le blanc.** `spanGaps: true` sur les deux courbes,
  sans point aux jours manquants : le cumul, lui, ne s'interrompt pas.
- **Un zéro n'est pas un blanc.** Six journées du Nord-Kivu et six du
  Haut-Uélé sont relevées à 0 nouveau cas ; leur barre de hauteur nulle
  devenait indiscernable d'une journée sans donnée dès lors que le blanc
  signifie quelque chose. `minBarLength: 2` leur laisse un trait au ras de
  l'axe, et l'infobulle affiche ce 0 au lieu de le filtrer — en vue
  quotidienne le filtre ne retient plus que les nuls, la vue agrégée remet le
  filtre d'origine, où un zéro est une série vide. Corollaire : une journée
  n'est portée que par une des deux séries, l'autre est `null` et non 0, sans
  quoi deux traits se superposeraient sous la barre claire d'un rattrapage.
- **La note s'ouvre sur le compte**, `provinceChartBlanks` (fr/en/sw), avant
  la phrase des trous longs et celle des rattrapages. Sa réserve « sauf
  indication contraire » renvoie à la phrase suivante : les cas d'un trou de
  plus de trois jours ne sont reportés sur aucune journée.

La vue quotidienne seule change ; Semaine et Mois agrègent comme avant. Vérifié
sur les trois provinces, en 1 280 et 360 px, dans les trois langues —
`test_onglets` sans erreur sur les pages province, `/donnees/`, `/en/data/` et
`/sw/takwimu/`. En 360 px, 124 barres au lieu de 104 : le mur d'août-septembre
reste un mur, les blancs de mai-juillet se lisent.

**Il a ses trois pas de temps depuis le 15 septembre 2026** — Jour / Semaine /
Mois, la bascule de `/donnees/` posée dans le cadre de chaque page province
(Ituri, Nord-Kivu, Haut-Uélé ; les quatre autres n'ont pas de graphique). Le
câblage existait déjà et n'a pas bougé : `<nav data-vue-periode>` vise le
canevas de son propre `.chart-panel-wrap`. Trois choses ont dû suivre :
- **La part rapportée d'un rattrapage n'existe pas à l'échelle d'une
  province.** `partsQuotidiennes` et `agregeNouveauxCas` prennent un dernier
  argument `partConnue` ; à `false`, la journée entière bascule en teinte
  claire, comme du côté des décès. Sans lui l'Ituri aurait hérité des 97 cas
  du 22 juillet, qui sont ceux du pays. La règle d'empan, elle, joue comme au
  national : le 30 juillet nomme les journées qu'il rattrape, sa semaine et
  son mois les contiennent, ses cas y passent en couleur pleine.
- **Les deux courbes de cumul ne suivent pas en vue agrégée**, et le second
  axe part avec elles. C'est l'idiome du site — sur `/donnees/` le cumul n'est
  tracé qu'en vue quotidienne — et la raison se voit à l'écran : agrégées, les
  barres sont larges et jointives, et la courbe des cas, qui porte la teinte
  de la province, disparaît dedans. Le même piège que l'ambre du Nord-Kivu, à
  l'échelle de la barre.
- **La note se recompose.** `provinceChartCatchup` nomme les deux rattrapages
  et les dit clairs : vrai au jour le jour, faux dès qu'on agrège. La phrase
  agrégée est celle du pays, désormais **partagée** : `CATCHUP_AGREGE` en tête
  d'`i18n.js` (trois langues, deux formes selon la période) alimente
  `chartWeeklyNote`, `chartMonthlyNote` et la nouvelle clé
  `chartCatchupAggregated`. Écrite deux fois, elle aurait divergé au premier
  correctif ; vérifié que les notes nationales rendent le texte à l'identique
  avant / après. La phrase des trous, elle, ne vaut qu'en vue quotidienne :
  agréger rattache ces cas à la période du bulletin suivant au lieu de les
  laisser sans barre.

Piège rencontré en le faisant : la bascule est **masquée par défaut**
(`navNew.style.display = 'none'` dans `renderOneChart`, hors `newCases` et
`newDeaths`) — le HTML était correct et rien ne s'affichait.
`provinceEpidemic` est dans la liste depuis. Corrigé au passage, sans rapport
avec la bascule : le « au » de la note des trous était écrit en dur, et les
pages anglaise et swahilie affichaient « from 16 Jul au 21 Jul » ; il passe
par `chartDeathPlaceWeekLabel`, qui le porte dans les trois langues. Vérifié
par sonde à 1 280 et 360 px, trois langues, trois vues et retour :
`test_onglets` sans erreur sur `/donnees/` et sur les pages province, vues
nationales inchangées.

**`byProvince`** — six courbes de cumul, une par province, chacune à sa teinte
d'identité, sous le titre « Cas par province ». Il s'appelait « Cas cumulés /
région » jusqu'au 26 août : ni la RDC ni le reste du site n'emploient
« région » — le découpage est la province —, et le swahili disait `eneo`, qui
désigne aussi la zone de santé, l'autre découpage de la même page. Le `/` était
par ailleurs le seul raccourci de ce genre dans la barre.

**Ce graphique ne trace que les cas**, alors que `province-history.json` porte
aussi les décès. Une vue « Létalité » y a été écrite le 26 août puis retirée le
jour même : elle n'avait pas été demandée. Les décès cumulés bruts, eux,
n'ajouteraient rien — même forme que les cas, mêmes rangs, même écrasement par
l'Ituri.

**`contactsFollowUp`** — une courbe, plus un **pont en pointillés atténué** sur
les périodes sans donnée. Ce pont n'est jamais une valeur : c'est un repère
visuel, et la note le dit.

**`deathsPlace`** — des barres hebdomadaires empilées à 100 %, communauté
contre centre de traitement, avec la moyenne en pointillés sur un second axe
invisible.

**Chaque semaine occupe la même emprise, celle de sept jours** : les relevés
disponibles remplissent la gauche, ce qui manque reste en gris hachuré à
droite, avec une entrée de légende « Jours sans donnée ». Trois semaines sur
sept sont concernées — celle du 3 août n'a que trois relevés, quatre bulletins
d'affilée ne distinguant pas le lieu du décès. Elles s'affichaient jusqu'au
26 août comme des semaines pleines.

**Ce qui est encodé, c'est la couverture, pas le volume.** Encoder le nombre
de décès aurait fait de l'aire un volume, et invité à comparer d'une semaine à
l'autre des totaux que la note déclare non comparables.

**Quatrième plugin maison, `largeurSemaine`** : Chart.js ne fait pas varier la
largeur barre par barre — `barThickness` n'est pas scriptable en 4.4.1,
vérifié, les trois barres d'un test sortaient identiques. Le plugin
redimensionne les éléments après la mise en page et recale leur centre pour
que la partie pleine parte du bord gauche. Le gris se dessine en
`afterDatasetsDraw` : posé avant, les bordures blanches des segments empilés
le mordraient. Les hachures **doivent** passer par un `clip()` — calculées à
la main, elles dessinaient un sablier.

**L'infobulle annonce la semaine calendaire complète**, du lundi au dimanche,
et non la plage des jours renseignés : la barre représente une semaine,
incomplètement observée. Le compte de relevés qui suit dit ce qu'on en sait.
La moyenne en est filtrée — elle y répétait la même valeur sept fois — mais
reste dans la légende.

**`pyramide`** — deux vues par une bascule interne : « Effectifs » (deux
pyramides côte à côte, échelles distinctes) et « Parts » (une seule figure,
chaque série ramenée à 100 % de son total).

### Conventions partagées

**Axes.** Un second axe `y1` à droite dès que deux ordres de grandeur
coexistent. Toujours `beginAtZero`. Une échelle en pourcentage va de 0 à 100,
**jamais resserrée sur les valeurs** — un cadrage sur 50-70 % transforme du
bruit en montagnes russes.

**Infobulles.** Fond `PALETTE.panel`, bordure `PALETTE.line`, police du site.
Elles donnent **toujours l'effectif avec la part** : 100 % sur un décès et
61 % sur mille ne se lisent pas de la même façon.

**Légendes.** `usePointStyle: true` — Chart.js dessine alors les séries en
barres comme des pastilles pleines et celles en courbe comme des anneaux, ce
qui distingue les deux formes gratuitement. `pointStyle: 'line'` pour une
ligne de référence. Légende masquée quand aucune série n'a de libellé.

**Nombres.** `fmt()` partout, jamais `toLocaleString` directement.

**Trois plugins maison**, écrits plutôt qu'importés — `chartjs-plugin-datalabels`
aurait été une dépendance entière pour un seul usage :

- `percentLabels` et `pctSexes` — le pourcentage au centre de chaque segment,
  pour ne pas obliger à viser l'axe.
- `cotesPyramide` — « Femmes » et « Hommes » au-dessus de leur moitié.

**Un plugin ne s'attache qu'à la construction.** Un mode qui en utilise un doit
détruire et recréer son instance à chaque passage — et donc désactiver
l'animation, sinon elle repart de zéro à chaque retour sur l'onglet.

**Reconstruire plutôt que mettre à jour quand le type change.** Chart.js ne
permet pas de passer une instance de `bar` à `line`. Le code teste
`slot.chart.config.type` et détruit si besoin.

---

## La page « Riposte & défis » (`/riposte/`, `/en/response/`, `/sw/mapambano/`)

**Depuis le 7 septembre 2026 (publié le jour même, commit `5ae7d35`), c'est
l'ancienne maquette `riposte-defis` qui vit à cette adresse**, décision du propriétaire : l'adresse
ne bouge pas (indexée, liée, partagée), le fragment `site/pages/riposte.html`
est celui de la maquette, l'onglet dit « Riposte & défis » avec une pastille
« Nouveau » (`navBadge` dans `pages.json`, retirée à la main quand le
propriétaire le dira — un `jusquau` facultatif la ferait expirer seule). La
page a deux parties jumelles : une bande claire « La riposte » (quatre
chiffres, puis les cadres alertes, laboratoire, contacts, CTE, lieu du
décès, avec « Méthode et sources » replié sous le dernier), et une bande
sombre « Les principales difficultés » : une frise des dix obstacles en
**grille par semaine** (ordre de première mention ; une case par semaine
depuis le premier bulletin, teintée selon la **part** des bulletins parus
cette semaine-là qui citent l'obstacle — aucun, moins de la moitié, la
plupart, tous ; survol par case sur grand écran, « 13 juil. → 19 juil. ·
5 bulletins sur 7 »), puis dix fiches rédigées. La grille a remplacé le
7 septembre les traits par bulletin, essayés d'abord puis écartés : à
330 px ils faisaient un code-barres, et même à 1 000 px une ligne dense se
lisait comme une présence continue là où l'obstacle va et vient (les
« équipes attaquées » : deux semaines pleines, puis des vagues). La part
et non le nombre, parce que la semaine du 26 juillet n'a que cinq
bulletins (28 et 29 sans parution) et paraissait plus faible partout. La
fiche garde la trace au bulletin près. Pièces :
`scripts/defis_synthese.py` (rendu), `data/defis-synthese.json` (textes
fr/en/sw et mots-clés — **le swahili a été traduit le 7 septembre par
l'assistant depuis le français, à faire relire par un locuteur** ; jusque-là
la page swahilie affichait le français avec une note, et c'est encore le
repli pour toute autre langue ou un thème sans texte),
`data/defis.json` (084 et suivants) et **`data/defis-anciens.json`** —
les Défis des bulletins 017 à 083 gelés depuis le corpus par
`scripts/geler_defis_anciens.py`, parce que le corpus n'est pas versionné et
qu'un clone frais rendait une frise qui commençait le 6 août. Sur
téléphone (audit à 360 et 320 px du 7 septembre) : la bande sur la
variable de gouttière, l'étiquette de frise au-dessus de ses cases, une
colonne de fiches. Piège rencontré avec les traits : une bulle CSS en
`visibility:hidden` est cachée mais posée, et les dernières faisaient
défiler la page de 63 px — `display:none`, toujours. **La grille a autant de colonnes que de semaines, et c'est le HTML qui le
dit** : `defis_synthese.py` pose `style="--sem:N"` sur `.grille`, et
`site.css` lit `repeat(var(--sem,14), …)`. Jusqu'au 11 septembre 2026 le
« 14 » était écrit en dur : à la quinzième semaine (SitRep 119), la
dernière case de chaque ligne passait à la ligne sous juin, en « double
rectangle ». Les mots-clés d'un thème se vérifient contre les trous de sa ligne :
le 7 septembre, « capacité des CTE/CT insuffisante » (064-080) échappait au
thème saturation, trois clés l'ont comblé ; les autres trous sont réels.

Historique : la page avait reçu le 6 septembre les « Défis » du dernier
bulletin cités sous chaque cadre (`defis_seed`) et un chapitre « Les autres
fronts », publiés par erreur le 7 puis retirés le jour même ; la bascule
vers la maquette a ensuite remplacé tout cela. Le principe : la chaîne dit ce qu'on fait, le lieu du décès dit
ce qui échappe, les Défis disent pourquoi — et ils sont **sous le cadre
qu'ils expliquent**, pas dans un chapitre à part. `extraire_defis.py` lit
les sous-sections « Défis » en prose de l'époque D (084 et suivants) dans
`data/defis.json` : un bloc par pilier, items cités **mot pour mot**,
provinces citées, rattaché au titre numéroté qui précède (en sautant
« Principales actions » et les puces — la numérotation est capricieuse,
« 1.10.4 Défis » sous « 1.10.2 Sécurité »). `defis_seed()` dans
`build_pages.py` route le dernier bulletin : surveillance → le suivi des
contacts si le texte parle de contacts, sinon les alertes ; laboratoire →
le laboratoire ; prise en charge et « Continuité des soins » → les CTE ;
les autres piliers ne sont pas cités — le chapitre « Les autres fronts »
qui les portait (quatre piliers ouverts, quatre repliés) a été **retiré le
7 septembre 2026 à la demande du propriétaire**. Trois règles : **citer,
jamais reformuler ni classer** (le codage thématique demande un regard
métier) ; **en français sur toutes les langues**, avec une ligne qui le
dit (traduire un texte officiel automatiquement serait un risque) ; un
bulletin sans section Défis **le dit** plutôt que de montrer le précédent.
`check_coherence` vérifie que `defis.json` ne dépasse pas la date du
rapport. La synthèse rédigée « ce qui a freiné depuis mai » est un autre
objet, à la main, encore à écrire (voir chantiers ouverts).

Construite le 28 août 2026, **en local, non commitée à cette date**. Elle
répond à la question que `/donnees/` ne pose pas : que fait-on contre, et
est-ce que ça tient. Quatre cadres empilés dans l'ordre de la chaîne de
riposte — alertes, laboratoire, contacts, CTE — et non des onglets : ces
quatre graphiques se lisent ensemble, et ce qui n'est pas cliqué n'est pas lu
(l'argument du carrousel de provinces). Dans la barre latérale, juste après
« Données détaillées ». Quatre chiffres de tête écrits en dur par
`riposte_seed()` dans `build_pages.py`, chacun daté quand sa série s'arrête
avant le bulletin.

**Trois cases au glissant, une au jour.** Alertes reçues, positivité et
contacts vus **cumulent les sept derniers relevés** qui publient la donnée
(décision du propriétaire, 30 août — d'abord la positivité seule, puis les
trois) : reçues et validées additionnées ; positifs sur échantillons ; vus
cumulés sur à-suivre cumulés, la moyenne pondérée (à défaut d'effectifs sur
l'un des sept, moyenne simple des taux, sans sous-titre d'effectifs). La
valeur du jour était trop bruyante pour une case de tête — alertes du simple
au double d'un bulletin à l'autre (1 164 le 22 août, 2 371 le 25),
positivité de 13,3 à 21,8 puis 13,9 % en trois jours sur 370 à 500
échantillons — et contredisait le dernier point des graphiques,
hebdomadaires. **Une moyenne depuis le début a été écartée** : dominée par
juin-juillet (56 % du dénominateur), elle ne bougerait plus — 21,5 % pour
15,9 % sur sept relevés — et répondrait à une autre question que « où en est
la riposte ». Ni bornes ni date sous ces trois cases — le libellé « 7 derniers
relevés » suffit (les bornes ont été affichées une heure, puis la date de
fin seule, puis rien, à la demande du propriétaire). Conséquence assumée :
quand le bulletin ne chiffre pas la donnée, la fenêtre s'arrête un jour
plus tôt sans le dire — le 106 tait les échantillons de la Tshopo et du
Bas-Uélé, la positivité court donc du 21 au 27 août. `riposteKpiAsOf` ne
sert plus qu'à l'occupation des CTE. Les sept relevés ne coïncident
pas avec le dernier point des graphiques, semaine calendaire close : c'est
voulu, les deux se lisent ensemble. **L'occupation des CTE reste au jour** :
c'est un stock, pas un flux. Le libellé le dit — « (7 derniers relevés) », « (last 7
bulletins) », « (ripoti 7 za mwisho) » ; « 7 relevés » seul, essayé
d'abord, ne disait pas lesquels.

### Les données

| Fichier | Script | Profondeur | Ce qu'il lit |
|---|---|---|---|
| `alertes.json` | `extraire_alertes.py` | 77 dates dès le 1ᵉʳ juin | tableau « Gestion des alertes » (B, C) ; tableau « Situation des alertes notifiées par province » (D) |
| `laboratoire.json` | `extraire_laboratoire.py` | 78 dates dès le 21 mai | section « Laboratoire », découpée par province |
| `cte.json` | `extraire_cte.py` | 70 dates dès le 2 juin | tableau « Occupation des structures de soins » (B, C) ; prose « Continuité des soins » (D) |
| `contacts-followup.json` | `extract_contacts_followup.py` (étendu) | inchangée, + `contacts` (vus / à suivre) et `provinces` | lignes de province du tableau (B), bande de chiffres clés (C), phrase de surveillance (D) |

Tous lisent le texte des PDF via `scripts/textes_pdf.py`, qui le met en
cache dans `.cache/textes/` (ignoré par git) : seul le bulletin nouveau est
réellement ouvert. Le workflow GitHub porte les trois nouvelles étapes.

**Trois principes de lecture, nés des dérapages du premier passage.**

- **Le tableau avant la prose.** Sous « Prise en charge » (B, C), la prose
  aligne des cumuls qui ressemblent à des hospitalisés du jour — le 060
  donnait 753 hospitalisés au Nord-Kivu, son cumul de cas. La prose n'est
  lue que sous le titre de l'époque D, « Continuité des soins ».
- **Un morceau de province s'arrête avant `cumul`, `Au total` et les
  paragraphes de synthèse.** Sans cette coupure, la Tshopo héritait des
  « 152 échantillons pour 55 positifs » du commentaire qui suit sa ligne.
- **Un espace entre deux nombres est tantôt une colonne, tantôt un
  séparateur de milliers** (« 532 924 ND 27 ND 1 483 »). `decoupages()`
  énumère les lectures possibles et l'appelant retient celle que la colonne
  Total vérifie — ou, en D, celle où reçues = vivants + décédés. Sans
  vérification, le 020 lisait 6 409 alertes là où les provinces en font 403.

**Ce qui est déduit, et marqué.** Le laboratoire déduit les positifs du
produit échantillons × positivité quand le bulletin ne donne que ces
deux-là et que le produit tombe sur un entier (`positifsDeduits`) ; l'occupation
est recalculée quand le bulletin donne patients et lits sans le taux
(`occupationCalculee`). Rien d'autre.

**Le meilleur garde-fou du dépôt** est dans `check_coherence.py`, section 6 :
la somme des positifs du laboratoire du jour doit égaler les nouveaux cas du
bulletin (81 = 81 au SitRep 104). Une extraction qui dérape sur l'un des deux
se voit immédiatement. Les autres règles : positifs ≤ échantillons
(bloquant), validées ≤ vérifiées en D (bloquant), vus ≤ à suivre (bloquant),
positivité et occupation publiées = recalculées à 1,5 pt (notes).

**Deux entonnoirs d'alertes, pas un.** En B et C, « investiguées » et
« validées » comptent aussi les alertes reportées de la veille — elles
peuvent dépasser les reçues du jour, et les validées dépasser les
investiguées (Ituri, 061 : 318 pour 179). C'est la source. En D, les
colonnes ne portent que sur la journée. Le schéma commun garde `recues`,
`verifiees`, `validees` ; `suspectsInvestigues` et `transferes` n'existent
qu'en D. La note du graphique le dit.

### Les graphiques (`app.js`, modes `alertes`, `laboratoire`, `contactsRiposte`, `cte`)

- Les volumes (alertes, échantillons) sont **par semaine calendaire**, la
  semaine en cours écartée tant qu'elle n'est pas finie — même règle que
  « Nouveaux cas ». **Une semaine sans relevé reste une colonne vide** :
  deux barres collées se liraient comme deux semaines consécutives.
- Les taux sont quotidiens, sur un calendrier jour par jour (idiome du
  suivi des contacts), `spanGaps:false`. **Chaque courbe de taux porte son
  pont en pointillés** au-dessus des jours sans bulletin (`jeuPont`,
  tremblement déterministe, teinte atténuée, ignoré par la légende et
  l'infobulle) — contacts et CTE depuis le 28 août, la vue Taux des
  alertes depuis le 5 septembre à la demande du propriétaire, avec un
  plafond `null` parce que la part vérifiée dépasse 100 % jusqu'à début
  août. La note de chaque cadre dit « tracé purement illustratif — jamais
  une valeur ».
- **Les alertes ont trois vues depuis le 22 septembre 2026** (demande du
  propriétaire) : « Par semaine », « Par jour » et « Taux ». Les deux
  premières portent le même indicateur à deux échelles, la troisième en
  porte un autre — d'où les libellés de granularité, partagés avec le
  cadre du laboratoire, plutôt que l'ancien « Volume ». La série des
  alertes est **la mieux tenue du bulletin** : 95 journées relevées sur
  105, contre 98 sur 110 au laboratoire. La vue par semaine y cachait donc
  peu de choses, sauf l'à-coup du jour — de 257 à 2 819 signalements — et
  la montée de la recherche active, d'environ 450 alertes par jour début
  juin à 2 000 en septembre. Même idiome que le laboratoire : axe
  calendaire, blanc à chaque journée sans bulletin, `minBarLength` pour
  qu'une journée relevée à zéro garde son trait, et un pied d'infobulle
  qui donne le total reçu (`alertesRecuesTotal`).
- **Le 17 septembre est écarté des alertes** (`JOURNEES_ECARTEES` dans
  `scripts/extraire_alertes.py`, 22 septembre 2026). La vue par jour l'a
  fait voir d'un coup : 1 329 alertes validées comme cas suspects, contre
  350 à 430 les jours voisins. Le tableau 3 du SitRep 126 donne pour
  l'Ituri 1 058 validées et 140 invalidées, là où le 18 donne 232 pour 667
  et le 19, 238 pour 813 : **les colonnes « validées » et « invalidées »
  sont interverties dans ce bulletin**, et échangées elles rentrent
  exactement dans la série. La lecture est conforme à l'en-tête du tableau
  — l'erreur est en amont, et la corriger ici reviendrait à réécrire la
  source. La journée entière est retirée plutôt que la seule valeur
  fautive : son total reçu est vraisemblable, mais une barre sans sa part
  validée ne se lirait pas mieux, et cette part est justement ce que les
  trois vues montrent. **La liste est nominative et doit le rester** : on
  n'écarte pas une journée parce que son chiffre surprend, seulement
  lorsque le bulletin se contredit lui-même.
- **Les dépassements de juillet, eux, ne sont pas des erreurs.** L'Ituri y
  valide jusqu'à 212 % de ses alertes vérifiées (282 sur 133, le
  15 juillet) : à cette époque les vérifiées et validées comptent aussi
  celles de la veille, ce que la note du cadre dit déjà. Ne pas les
  écarter — ils sont expliqués, pas incohérents.
- **Bascule par canevas** : `<nav data-chart-vue="alertesChart">`, état dans
  `vuesParCanvas` — quatre cadres cohabitent, une variable globale ne
  suffisait plus. `legendesDuGraphique` lit le titre dans `.section-title`
  et la vue dans `.chart-vue-nav`, donc l'export porte les deux.
- **Sous 20 lits, pas de taux d'occupation** (`SEUIL_LITS`) : la Tshopo
  passait de 5 à 40 % pour un patient. Même seuil de lisibilité que le lieu
  du décès.
- Le laboratoire trace les **nouveaux cas** comme positifs quand le bulletin
  sépare les reprélèvements, la phrase nationale de l'époque D primant sur
  la somme des provinces.
- **La note disait l'inverse de la donnée jusqu'au 22 septembre 2026.**
  « Un positif n'est pas toujours un nouveau cas : les bulletins récents
  séparent les reprélèvements, les anciens non » — or **seuls ceux du 10
  au 14 août les séparent**, et aucun depuis, septembre compris. Le
  lecteur pouvait croire la partie récente de la courbe nettoyée des
  reprélèvements ; c'est la seule partie qui ne l'est pas. La phrase vit
  désormais dans `laboReprelevements`, **partagée par les deux vues**, et
  son compte est calculé au rendu sur les points réellement tracés : la
  vue par semaine annonce 3 bulletins (ceux dont le total national porte
  `nouveauxCas`, du 12 au 14 août), la vue par jour n'en annonce aucun —
  ces journées-là n'ont pas d'échantillons et y sont blanches. Les deux
  comptes sont justes parce qu'ils décrivent chacun ce que leur courbe
  montre. `noter()` normalise les espaces : les phrases se concatènent et
  certaines portent déjà le leur.
- **Le laboratoire a deux vues depuis le 22 septembre 2026** (demande du
  propriétaire) : « Par semaine », inchangée et toujours par défaut, et
  « Par jour », qui pose les mêmes échantillons sur un calendrier jour par
  jour. 81 journées sur 122 portent à la fois les échantillons et les
  positifs ; les 41 autres restent **en blanc, à leur vraie largeur** —
  collées, elles feraient croire à une série continue, et c'est
  précisément l'irrégularité de publication que la vue quotidienne montre
  (673 échantillons un jour, 292 un autre de la même semaine). La courbe
  de positivité y porte son pont en pointillés comme les autres taux, et
  `minBarLength:2` distingue une journée relevée à zéro d'une journée sans
  bulletin. Note dédiée `chartNoteLaboJour`, qui compte les blancs à
  chaque rendu — le compte se périmerait s'il était écrit en dur.
- **Le pied des infobulles était blanc sur fond clair — invisible sur tout
  le site** (relevé le 22 septembre 2026 en capturant une infobulle plutôt
  qu'en lisant son contenu). `infobulle()` posait `titleColor` et
  `bodyColor`, jamais `footerColor` : Chart.js appliquait donc son défaut,
  `#fff`. Tout ce qui passait par un pied était écrit sans être lu — le
  « Total » des barres empilées **depuis l'origine des graphiques**, et le
  nombre d'échantillons analysés du laboratoire. Corrigé dans
  `reglerInfobulles()`, appelé au premier rendu, **sur les défauts globaux
  de Chart.js** : posé dans `infobulle()`, le réglage ne prenait pas, les
  options réassignées à un graphique déjà construit retombant sur les
  défauts pour les clés que ceux-ci portent. Leçon : une valeur d'options
  qu'on croit posée se vérifie en sondant `chart.options`, et un rendu se
  vérifie en le regardant — le texte était bien dans `tooltip.footer`,
  parfaitement récupérable par sonde, et parfaitement illisible à l'écran.
- **Le pied de l'infobulle du laboratoire nomme le total** depuis le
  22 septembre 2026 : « Échantillons analysés : 292 » au lieu du
  `totalEmpile` générique « Total : 292 ». Positifs + négatifs redonnent
  par construction le nombre de tests, et c'est le chiffre que le lecteur
  cherche. `analysesEmpilees` remplace `totalEmpile` **dans les deux
  vues** du cadre — la même quantité ne peut pas s'appeler « Total » par
  semaine et « Échantillons analysés » par jour — et, contrairement à
  `totalEmpile`, il ne se tait pas quand une seule barre porte : une
  journée à zéro positif perdait justement son compte de tests.
- **Les comptes partiels rendent 17 journées à la vue par jour**
  (22 septembre 2026, après l'analyse ci-dessous et sur choix du
  propriétaire). Quand une seule province retient ses échantillons, la
  courbe somme les provinces complètes au lieu de perdre la journée :
  **98 journées tracées sur 122 au lieu de 81**, les blancs tombent de 41
  à 24. Ces journées portent la **hachure** `motifPartiel` — teintée de la
  couleur de la barre pour garder positifs et négatifs distincts —, une
  entrée de légende « Compte partiel » (`legendePartielle`, sur le modèle
  de `legendeAVenir`) et un pied d'infobulle qui **nomme la province
  manquante** : sans lui, les « 567 analyses » du 28 août se liraient
  comme un compte du pays entier. **Leur positivité est tracée, en point
  creux** — plein = le pays, creux = les provinces comptées —, et
  l'infobulle y remplace « Positivité » par « Positivité des provinces
  comptées » : le même mot ne peut pas désigner deux périmètres. Ce taux
  est **exact**, positifs et échantillons venant du même périmètre.
  **Deux estimations successives de son écart au taux national**, le
  22 septembre 2026 : par la médiane de la province sur toute la période,
  13 à 16 points en juin — chiffre **faux**, il prêtait au Nord-Kivu de
  juin les 93 échantillons quotidiens qu'il n'analyse qu'en août ; par les
  journées voisines de la province, **0,2 à 5 points**, le maximum étant
  le 6 juin. C'est la seconde qui vaut, et c'est elle qui a fait tracer le
  point. Leçon : un estimateur global sur une épidémie qui change d'échelle
  en trois mois ne vaut rien, il faut estimer localement. **La vue par semaine les ignore** : une barre
  hebdomadaire ne peut pas être à moitié hachurée, et une semaine mêlant
  journées complètes et partielles ne se lirait plus. Piège rencontré :
  l'entrée de légende n'a pas de jeu (`datasetIndex: -1`) et le filtre des
  ponts la lisait comme un dataset — `legendePartielle` la laisse passer
  avant de rendre la main au filtre d'origine.
- **La vue par jour commence au 2 juin** (`DEBUT_JOUR`, demande du
  propriétaire, 22 septembre 2026). Avant cette date la source ne donne que
  quatre relevés isolés — 20, 29, 30 et 31 mai —, séparés par des semaines
  entières sans rien : sur un axe calendaire ils tiraient un tiers de la
  largeur pour quatre barres, et leur positivité de dépistage ciblé (77 %
  le 29 mai, sur 70 échantillons) écrasait l'échelle de droite. La borne
  ramène la vue à 110 jours dont **12 blancs seulement**, contre 123 jours
  et 20 blancs, et les barres y gagnent le double de largeur. Ces journées
  restent dans les données et dans la vue par semaine, qui les agrège sans
  déformer l'échelle — c'est le partage de travail entre les deux vues.
- **Cinq journées récupérées à l'extraction** (22 septembre 2026).
  `scripts/extraire_laboratoire.py` ne lisait que deux formes : la phrase
  nationale et le tableau par province. Dix-neuf rapports n'en portaient
  aucune alors que leur section laboratoire existe — les bulletins de la
  fin mai tiennent le point dans un tableau « Indicateurs clés » à une ou
  deux colonnes, et le 059 l'écrit en prose, province par province. Deux
  replis ont été ajoutés, `point_du_jour()` et `provinces_redigees()`,
  **qui ne s'exécutent que si la lecture normale n'a rien rendu** : les
  102 journées déjà extraites ne peuvent pas bouger, et le contrôle
  avant/après l'a vérifié — 0 date perdue, 0 date modifiée. Gain : les
  20, 29, 30 et 31 mai (laboratoire de Bunia, sans détail provincial,
  `source: "SitRep INSP (point du jour)"`) et le 12 juillet (Ituri 203/27,
  Nord-Kivu 99/6).
- **La règle de sûreté de ces replis** : un tableau à deux colonnes colle
  ses nombres — « Nbre d'échantillons analysés 3 648 » vaut 3 puis 648,
  et aucun motif ne peut le trancher seul. Les deux hypothèses sont lues
  et **seule celle que le taux imprimé valide à 0,3 point près est
  gardée** ; si plusieurs passent, la journée est écartée. C'est ce qui
  fait tomber le 27 mai : son taux imprimé vaut 0 %, et un taux nul valide
  aussi bien 0 positif sur 3 que sur 3 648. Sans taux imprimé, on
  n'accepte qu'une lecture sans ambiguïté, un seul nombre de chaque côté.
- **Piège rencontré, et rattrapé par le contrôle avant/après** : le
  premier jet nommait ses constantes `POSITIFS_RES` et `NOMBRE_RE`,
  écrasant les constantes du même nom déjà utilisées par
  `lire_province()`. 95 journées se sont retrouvées corrompues — l'Ituri
  du 3 juin passait de 18 positifs à 0 — sans qu'aucune exception ne soit
  levée. D'où le préfixe `JOUR_` sur tout le bloc, et la règle : **après
  toute modification de l'extracteur, comparer l'ancien et le nouveau
  JSON date par date**, jamais se fier au seul compte de dates.
- **Pas de déduction supplémentaire à espérer.** Un solveur qui propage
  toutes les identités disponibles (positifs = échantillons × taux,
  positifs = vivants + décès, total = somme des provinces, et les
  réciproques à une inconnue) ne rend rien de plus. Les 50 entrées qui
  bloquent portent les positifs **sans** les échantillons et **sans** le
  taux : une province qui ne dit pas combien elle a analysé ne publie pas
  de pourcentage calculé dessus. Le seul cas inverse, l'Ituri du 4 juin
  (199 échantillons, 32,6 %, positifs absents), est refusé à raison par le
  seuil de `lire_province()` : aucun entier ne redonne 32,6 % — 65
  donnerait 32,7 %, 64 donnerait 32,2 %. La source est incohérente là.
- **Pourquoi 41 journées sont blanches** (analyse du 22 septembre 2026) :
  21 d'entre elles ont pourtant des données, mais **une seule province
  partielle suffit à annuler le total national** — le Nord-Kivu donne ses
  positifs sans ses échantillons 9 jours, le Sud-Kivu 7. Le 28 août,
  quatre provinces sont complètes et le seul Bas-Uélé fait disparaître la
  journée. S'y ajoutent 14 jours dont le bulletin n'a pas de section
  laboratoire exploitable (dont les onze premiers, du 22 mai au
  1er juin) et 6 jours sans bulletin. **Aucun trou depuis le
  1er septembre** : les 19 bulletins de septembre portent tous le total
  des provinces.
- **La vue par province a de l'air au-dessus de 100 %** (cadre à 110, aucune
  graduation au-dessus de 100) : Tshopo et Sud-Kivu y sont à 100 % des jours
  entiers, et leurs points se collaient au cadre. Demande du propriétaire du
  28 août, qui a choisi de garder cette vue malgré ses six courbes et ses
  trous — en connaissance de cause : le saut du Bas-Uélé de 18,7 % à 59,5 %
  entre les 18 et 19 août est dans la source (36 puis 131 contacts vus sur
  ~200 ; trois jours de compteur figé, puis les équipes arrivent), et le
  20 août le bulletin recopie 59,5 % pour 110/233 = 47,2 % — les effectifs
  sont écartés par le contrôle « à un point du taux », le taux imprimé reste.
- **Un nombre de la bande de chiffres clés (époque C) est un groupe de un à
  trois chiffres suivi de groupes de trois**, ou une suite de chiffres sans
  espace (« 17472 ») : « Sud-Kivu 16 14 466 / 18 276 vus » se lisait
  1 614 466 vus, et huit jours d'effectifs manquaient fin juillet. Le 077
  imprime les deux nombres **dans le mauvais ordre** (« 17 828/ 13 420
  vus ») ; ils ne sont retenus inversés que parce que 13 420 / 17 828 = 75,3 %,
  le taux de la même ligne.
- Le seuil de suivi des contacts est **85 %** dans les bulletins depuis août
  (« en dessous du seuil de 85 % »), quand l'OMS fixait 95 % : la note cite
  les deux, aucun n'est tracé.
- Bas-Uélé porte toujours le rouge des décès (`PROVINCE_COLORS`) et il
  apparaît ici bien avant ses 50 cas — le chantier ouvert devient visible.

L'onglet « Suivi des contacts » de `/donnees/` a été retiré le 29 août : la
page Riposte en porte la version enrichie, le doublon est réglé.

Vérification : `tmp/riposte/` (gitignoré) reçoit les 18 figures exportées par
le mécanisme « Partager » et les captures de page, à 1 440 et 360 px, par un
script de session ; `test_onglets.mjs` sur `/donnees/` sans erreur.

---

## La page « Le virus » et le bloc des génomes

**Publié le 4 septembre 2026.** La page a été réordonnée pour suivre le
parcours du lecteur — espèce, transmission, incubation, évolution,
**traitements et vaccins**, qui la maladie touche, génomes — au lieu de
placer le remède avant la maladie. Une ligne d'ancres cliquables sous la
bande de chiffres, même idiome que `/riposte/`. Deux sections retirées à la
demande du propriétaire : « Réduire le risque de transmission » (six chaînes,
trois langues) et l'avertissement médical de fin de page (`virusNote`).

**Le bloc « Le virus lu dans son génome »** compte les génomes séquencés :
trois chiffres, une colonne par mois de prélèvement, douze barres de zones
puis une phrase calculée pour la queue de liste. Sa source est
**Pathoplexus**, la base où l'INRB dépose ses séquences, interrogée par son
API LAPIS **en agrégats seulement** — aucune séquence, aucune métadonnée
individuelle n'est téléchargée, et c'est ce qui rend l'usage licite : sur
754 séquences RDC, 690 sont sous conditions « restreintes », qui autorisent
explicitement un travail non publié avec attribution et lien, mais réservent
aux déposants la première analyse publiée. La note porte donc le lien et
nomme le laboratoire de génomique des pathogènes de l'INRB.

`scripts/extraire_genomes.py` produit `data/genomes.json`. **Il ne tourne pas
dans le pipeline quotidien** : c'est un chiffre de contexte, rafraîchi à la
main. Les libellés de lieu de Pathoplexus sont libres (« BUNIA »,
« MUNGWALU », « rwampara », l'aire de santé « Hoho ») : ils passent par la
normalisation du site plus les alias connus, et ce qui ne correspond à
aucune zone est compté à part plutôt que deviné. Les 23 séquences de 2012,
prélevées à Isiro lors de l'épidémie précédente, sont écartées.

**Le creux d'août est un délai de dépôt, pas une baisse.** 114 génomes en
mai, 254 en juin, 323 en juillet, 39 en août — mais 573 séquences ont été
**mises en ligne** en août, dont 323 prélevées en juillet. Le mois le plus
récent attend toujours son lot. La note le dit, et rappelle que le nombre de
génomes suit la capacité de séquençage, pas le nombre de cas.

**Le résumé grand public s'appuie sur des faits, pas sur des phrases.** Les
résultats publiés par l'INRB et ses partenaires sur virological.org (9 juillet
et 25 août 2026), plus une réplication de l'Imperial College, sont réécrits
dans nos mots : nouveau passage depuis le réservoir animal (le virus ne
descend ni de 2007 ni de 2012), ancêtre commun fin février 2026 soit trois
mois avant la déclaration, doublement tous les 21 jours avec inflexion après
juin. Un fait scientifique ne s'approprie pas, seule sa formulation est
protégée : rien n'est recopié, aucune figure reproduite, la source est citée
et liée. La note de crédit porte les intervalles (mi-janvier à fin mars, 15 à
41 jours) — trois chiffres nus se seraient lus comme des certitudes.

**Un paragraphe dit ce que les génomes NE disent PAS** : quelle zone a
contaminé quelle autre. Première rédaction écartée par le propriétaire, qui
parlait des « branches de l'arbre », terme jamais introduit ; la version
publiée donne la raison concrète — le virus mute lentement au regard de la
vitesse à laquelle il se déplace, donc d'une zone à l'autre les échantillons
se ressemblent trop pour reconstituer les chaînes de transmission. Les
auteurs eux-mêmes mettent en garde contre cette lecture.

**Douze lignes, pas vingt-deux.** Neuf zones étaient à trois génomes ou
moins, leur barre faisait deux pixels, et la section pesait deux cinquièmes
de la page pour un chiffre de contexte. Les six premières lignes portent 90 %
du total.

**Chronologie** : jalon curé au 22 février 2026, « Le virus circule déjà,
sans être vu », en tête de la frise. Seul endroit du site qui situe le début
réel de la transmission face à la déclaration du 15 mai.

**Deux corrections de mise en page qui valent partout** : dans un cadre, une
figure garde 20 px d'air latéral (`.panel` n'a pas de rembourrage propre) ;
sur téléphone, la valeur d'une barre `mb-bar` reste sur la ligne du nom au
lieu de tomber sous la barre.

**Le pied de page suit les mêmes groupes que la barre latérale** depuis le
5 septembre 2026 : « Sources & bulletins » y était sous Explorer alors que
`mainNav` et le surtitre de la page la rangent sous « Le site »
(`footerNav` dans `site/pages.json` : Explorer = accueil, données,
riposte ; Comprendre = virus, chronologie, FAQ ; Le site = sources,
à propos, contact). Attention en publiant : `pages.json` est l'un des
trois fichiers mis de côté par la recette ci-dessous, ce déplacement doit
être réappliqué sur la version de HEAD tant que Flux reste en local.

### Publier sans publier « Flux & déplacés » (et, jusqu'au 8 septembre, la maquette « Le bulletin »)

**Depuis le 10 septembre 2026, cette recette ne sert plus : le chantier Flux
est HORS DU DÉPÔT.** À la demande du propriétaire (« tu mets tout de côté,
toutes les maquettes, ne fais rien apparaître quand je te demande de mettre
le site en local »), tout ce qui était en local sans être publié a été
déplacé dans `~/Desktop/rapport ebola tracker/_mis-de-cote-2026-09-10/`
(100 Mo, `LISEZ-MOI.md` à la racine) : `flux/` porte le chantier complet
(fichiers propres à leur chemin d'origine, `flux.patch` = le diff des trois
fichiers partagés, `fichiers-partages/` = leurs copies entières,
`tmp/routes/` les extraits OpenStreetMap, `tmp/proto-flux/` la maquette en
cinq chapitres) ; `maquettes/` porte les scripts `prototype_*.py` et leurs
rendus `tmp/proto-*` des 6 et 9 septembre (provinces, accueil en planche,
accueil en trois figures, carte A/B, trois habillages et trois places de
l'encadré), plus les deux fichiers Natural Earth des rivières et lacs. Le
dépôt est depuis identique au site publié, `tmp/` ne garde que `audit/`,
`verif/` et `visuels/`. Remise en place : copier les fichiers, `git apply
flux.patch`, régénérer. La section qui suit décrit l'état antérieur.

**La lettre est publiée depuis le 8 septembre 2026 au soir** (« commit and
push sauf flux et déplacés ») : `/bulletin/` et les quinze archives
`/bulletin/100/` à `/bulletin/114/` en trois langues, indexables (le
`noindex` a été retiré de l'entrée `bulletin` et `pages_lettres` reprend
celui du modèle), dans le sitemap, avec le menu resserré (Actualité /
Explorer / Comprendre), les deux pastilles « Nouveau », la page Sources &
bulletins en cadres numérotés, `scripts/extract_piliers.py` ajouté au
workflow après `extraire_defis.py`, `data/lettres/`, `data/piliers.json` et
`data/bulletin-notes.json` versionnés. La recette ci-dessous ne concerne
donc plus que Flux : tout ce qui touche à la lettre se publie avec le
reste. Le premier paragraphe qui suit décrit l'état antérieur.

**Depuis le 8 septembre 2026, une seconde maquette vit en local : « Le
bulletin »** (`scripts/bulletin.py`, gabarit `site/pages/bulletin.html`,
entrée `bulletin` de `pages.json` en `noindex`, clés `bul*`, `lettre*`,
`gz*`, `ag*` et `defiPilier_*` de `strings.json`, styles `.bul-*`,
`.lettre-*`, `.gz-*`, `.rv-*`, `.ag-*`, import `bulletin` et appel
`bulletin.render` dans `build_pages.py`, `data/bulletin-notes.json`).
**Trois mises en page** en comparaison depuis le 8 septembre, mêmes blocs
(`chapitres` dans `bulletin.py`, trois assembleurs) : `/bulletin/gazette/`
(journal d'un jour, manchette à double filet, sans barre latérale —
`page.bodyClass` = `lettre-gazette`, la classe de corps est posée par le
gabarit via `{{bodyClass}}`), `/bulletin/revue/` (couverture bleu nuit plein
écran avec numéro et sommaire, chapitres à bande bicolore et « en bref »
latéral) et `/bulletin/agence/` (bande ambre, prose à gauche et colonne
des chiffres collante à droite ; l'objet encadré a été retiré le
8 septembre 2026). **Seule la variante agence subsiste, sous `/bulletin/`**
(voir plus bas). **C'est la variante
retenue le 8 septembre 2026** : sa manchette est centrée (`.ag-manchette`),
« LA LETTRE » en très grand serif capitales, puis la ligne « Édition n° 114
◆ 5 sept. 2026 » entre deux filets, puis le sous-titre en italique
(`bulSousTitre`), le tout fermé par un double filet. **Même dessin sur
téléphone** (demande du 8 septembre) : pas de variante mobile, seules les
tailles du nom et du sous-titre suivent la largeur (`clamp` en `vw`), le
sous-titre restant sur une ligne.

**Ce que la lettre dit de plus depuis le 8 septembre 2026** (sept
suggestions acceptées d'un coup, « fais toutes les modifs en local ») :
- **Tendance** : dans le chapeau, le chiffre du jour est situé par rapport à
  la moyenne des sept derniers jours (au-dessus / en dessous / dans la
  moyenne, seuils ±10 %, clés `lettreJourNiveau*`) ; dans le bilan, la
  moyenne par jour de cas et de décès sur sept jours contre les sept
  précédents (`lettreTendance`). Calcul sur les cumuls de `sitreps.json` aux
  dates les plus proches de J-7 et J-14, divisés par l'écart réel en jours
  (les bulletins ne sont pas tous quotidiens).
- **Dernière zone nouvelle** : « Aucune nouvelle zone de santé depuis le
  {date} » (`lettreJourZonesDepuis`), date lue dans `zones-history.json`.
- **Zones actives sur 21 jours** dans « Où » (`lettreZonesActives`) : une
  zone est active si son cumul de cas a bougé depuis l'instantané le plus
  proche 21 jours avant.
- **Trois piliers de plus** dans « La riposte », lus par
  `scripts/extract_piliers.py` → `data/piliers.json` (une entrée par
  bulletin, prose en sections 1.2 PoC/PoE, 1.4 PCI/EDS, 1.6 Vaccination) :
  enterrements dignes et sécurisés (alertes, réalisés, corps prélevés, non
  prélevés pour résistance ; sommes des provinces qui donnent le chiffre),
  rings ouverts / attendus, personnes vaccinées Ervebo et rupture de stock,
  personnes passées aux points de contrôle, part screenée, refus de
  dépistage. Chaque phrase n'existe que si le bulletin donne le nombre ;
  deux cases de plus dans la colonne (EDS, vaccinés). Le nombre de
  vaccinés est cité tel quel (« le bulletin fait état de ») car le SitRep
  mélange chiffres du jour et cumuls. Le total PoC/PoE d'une ligne de
  tableau à chiffres espacés se retrouve par la segmentation dont le
  dernier nombre est la somme des autres (`_total_ligne`).
- **Une page par lettre, `/bulletin/<num>/`** (en `/en/bulletin/<num>/`,
  sw `/sw/ripoti/mpya/<num>/`), mise en page agence, `noindex` tant que la
  lettre est une maquette. Mécanisme : `data/lettres/<num>.json` est la
  **copie de `data/latest.json`** au moment où le bulletin est intégré
  (`bulletin._instantanes()` fige le dernier à chaque génération) ; les
  séries par date gardent l'historique d'elles-mêmes. Les n°100 à 113 ont
  été repris depuis l'historique git de `latest.json` (`git show
  <commit>:data/latest.json`). `bulletin.pages_lettres(config)` ajoute les
  pages à `config["pages"]` dans `build_pages.main` avant le calcul des URL ;
  gabarit `site/pages/bulletin-num.html` = `{{seed.lettreNum}}`, posé page
  par page dans la boucle. Navigation précédente / suivante sous la
  manchette (`.ag-nav`), liste de toutes les lettres dans le pied
  (`.ag-archive`). `/bulletin/agence/` reste la lettre du dernier bulletin.
- Le résumé des Défis du n°114 a été resserré et corrigé (les 2 581 refus
  de dépistage sont aux points de contrôle en Ituri, plus 228 au Haut-Uélé).
  Les résumés des n°100 à 113 ont été rédigés le 8 septembre 2026 (fr/en/sw,
  `bulletin-notes.json`), d'après les blocs de `defis.json`. Les lettres sans
  résumé rédigé retombent sur le sommaire composé.
- **Vaccination = cumuls, jamais un chiffre du jour** (analyse des
  bulletins 104 à 114, 8 septembre 2026). Le SitRep écrit « Au total, 1 834
  personnes vaccinées dont 1 375 à la Tshopo et 459 au Bas-Uélé » (n°112),
  « cumul personnes vaccinées : 486 » (n°113), « au profit de 500 personnes
  ... stock résiduel à zéro » (n°114, qui suit le cumul 486 de la veille),
  ou le chiffre du jour de lancement (20 à Buta le 26 août, 122 à Kisangani
  le 27), lui aussi un cumul ce jour-là. `extract_piliers.lire_vaccination`
  range donc tout en `cumulParProvince` (province = la première citée avant
  le nombre, sinon la phrase précédente, le texte des tableaux s'intercalant),
  et la lettre additionne le **dernier cumul connu de chaque province** à
  sa date, en datant ceux qui viennent d'un bulletin antérieur : « 1 875
  personnes vaccinées avec Ervebo depuis le début de la campagne, le
  26 août : 1 375 dans la Tshopo (chiffre du 3 sept.), 500 dans le
  Bas-Uélé ». Case « Vaccinés Ervebo (cumul) ».
- **Les maquettes cadres, gazette et revue ont été supprimées** le
  8 septembre (pages, gabarits, assembleurs, CSS `.gz-*`/`.rv-*`, clés
  `gzNumero`, `lettreEyebrowGz`, `lettreNumero`, `lettreObjetLabel`,
  `lettrePrecedent`). La page `bulletin` (`/bulletin/`, `/en/bulletin/`,
  `/sw/ripoti/mpya/`, gabarit `site/pages/bulletin.html` =
  `{{seed.bulletinAgence}}`) est la lettre du dernier bulletin, mise en page
  agence ; l'URL définitive et l'entrée de menu restent à décider avant la
  mise en ligne (toujours `noindex`).
- **Règle de lisibilité (8 septembre 2026, « il faut que la lecture soit
  claire pour les gens qui ne connaissent pas les termes »)** : la lettre
  et ses résumés s'écrivent en langage courant. Pas de « pilier »
  (→ « volet de la riposte » ou « équipe de la riposte »), « complétude »
  (→ « part des rapports attendus transmis »), « PPL » (→ « soignants »,
  « personnels de première ligne »), « PCI » (→ « hygiène »,
  « désinfection »), « screening » (→ « contrôle de température »),
  « swab / prélevé » pour un corps (→ « testé »), « isolement » refusé
  (→ « refus d'être hospitalisé »), « listage » (→ « recensement des
  contacts »), « ESS / structures non normées » (→ « structures non prévues
  pour Ebola »), « stratégie avancée » (→ « équipes mobiles »), « létalité »
  (→ « part des malades décédés »), « positivité » (→ « part des tests
  positifs »), « à ventiler » (→ « pas encore attribués à une zone »). Les
  phrases générées (`lettre*`) et les cases de la lettre ont leurs propres
  clés (`lettreKpi*`), distinctes de celles de la page Riposte. Un
  **lexique** replié ferme chaque lettre (`lettreLexiqueTitre`,
  `lettreLex*`, dix mots : cas confirmé, cas suspect, alerte, contact, zone
  de santé, CTE, enterrement sécurisé, ceinture de prévention, point de
  contrôle, volet de la riposte). Les quinze résumés ont été réécrits dans
  ce langage.
- **Menu resserré (8 septembre 2026, « go local »)** : colonne en trois
  groupes et sept entrées, `mainNav` = Actualité (`navNewsTitle` :
  Actualité / Latest / Habari mpya) avec La lettre seule, Explorer (Vue
  d'ensemble, Données détaillées, Riposte & défis, Flux en local),
  Comprendre (Chronologie, Le virus, Sources & bulletins). FAQ et À propos
  ne sont plus dans la colonne : le propriétaire a tranché qu'ils vivent
  dans le pied de page (`footerNav` : Explorer avec La lettre en deuxième,
  Comprendre avec Sources & bulletins puis FAQ, Le site avec À propos et
  Contact). La pastille « Nouveau » est sur les deux entrées, La lettre et
  Riposte & défis (« je veux les deux pastilles nouveau », 8 septembre). Publié le 8 septembre au soir avec la lettre ; les deux pastilles restent
  jusqu'au signal du propriétaire.
- **Retouches du 8 septembre (« go local »)** : dans la lettre, les cases
  reprennent les libellés du site « Patients en isolement » et « Taux de
  létalité » (clés `i18n`, les clés `lettreKpiHospitalises` /
  `lettreKpiLetalite` ont été retirées) ; le chapitre 05 s'appelle « Les
  difficultés rencontrées » (`lettreDefisTitle`). La page Sources &
  bulletins a ses trois parties en cadres numérotés 01, 02, 03
  (`cadre-fiche`), son surtitre dit « Comprendre » (elle a changé de
  groupe), et les préfixes « 1. », « 2. », « 3. » des titres `reportsTitle`,
  `whoReportsTitle`, `geoSourceTitle` ont été retirés de `i18n.js`.
- **Manchette sans redondance (8 septembre, « go local »)** : le sous-titre
  `bulSousTitre` ne porte plus ni date ni numéro, déjà sur la ligne
  d'édition ; il dit « Résumé du bulletin de l'INSP ». Le pied de lettre
  n'a plus de lien « Le PDF du bulletin » séparé : la référence du SitRep
  est elle-même le lien vers le PDF (`lettrePied` sans `{url}`). Le
  glossaire s'appelle « Glossaire · les mots du bulletin », dix mots en
  ordre alphabétique dans chaque langue.
- **Manchette et rythme (8 septembre, « go local »)** : la ligne d'édition
  dit « Bulletin n° 114 ◆ Situation au 5 sept. 2026 » (`agEdition`,
  `lettreSituationAu`), le sous-titre « Résumé du bulletin de l'INSP,
  à chaque nouvelle parution » ; le pied ajoute « Une lettre paraît à
  chaque bulletin de l'INSP ; le précédent date du {date} »
  (`lettreRythme` / `lettreRythmeSeul`, date du bulletin précédent passée à
  `_lettre` par `render`). On dit « bulletin », jamais « SitRep », sauf dans
  la référence exacte du pied. Sous 430 px la ligne d'édition passe sur
  deux lignes centrées sans filets ni losange.
- **Navigation répétée en bas** (8 septembre) : la barre « Lettre
  précédente / suivante » est sous la manchette et en tête du pied
  (`.ag-pied .ag-nav`), à gauche et à droite sur ordinateur, empilée sous
  900 px. Incident du même jour : la suppression des maquettes avait
  effacé la règle mobile `.ag-grille{grid-template-columns:minmax(0,1fr)}`
  (sa ligne commençait par `.rv-corps,`), la prose s'affichait un mot par
  ligne sur téléphone sans que l'audit de débordement le voie ; remise dans
  le bloc `@media (max-width:900px)`. Leçon : après un nettoyage CSS,
  regarder une capture mobile entière, pas seulement l'audit.
- **Adresse définitive (9 septembre 2026)** : `/lettre/`, `/en/letter/`,
  `/sw/barua/`, archives `/lettre/<num>/` etc. (slug de la page + numéro,
  `pages_lettres`). **L'archive commence au n°090 (12 août 2026)** depuis
  le 9 septembre au soir, voir en tête de guide. Les adresses `/bulletin/…` de la veille au soir ont été
  supprimées sans renvoi, la page ayant moins de deux heures d'existence et
  aucun lien partagé (choix du propriétaire : « supprimer l'ancienne adresse
  et la rajouter par la nouvelle »). Le pied de lettre ne cite plus d'URL.
- **La lettre est bleue, plus ambre (9 septembre 2026, « c'est mieux »)** :
  la bande de tête `.ag-barre`, le losange de la ligne d'édition, les
  titres de chapitres `.ag-titre`, les titres de blocs `.ag-bloc-titre`
  et le carré `.ag-objet i` sont en `--accent-strong`, le bleu des dates
  et des chapitres numérotés. L'ambre `--accent-active` est la couleur
  de sens de l'isolement et du suivi des contacts (case de l'accueil,
  extensions de la chronologie, badges de létalité moyenne) : en bandeau
  elle ne signifiait rien ; elle reste sur les cases « Contacts suivis »
  et « Zones touchées » de la colonne, où elle a son sens.
- **Vocabulaire** : les « rings » du bulletin (l'intervention PCI autour de
  chaque cas : décontamination du domicile et des structures fréquentées,
  kits, repérage des contacts) se disent **« ceintures de prévention
  (rings) »** dans la lettre et les résumés, choix du propriétaire du
  8 septembre ; pas « anneaux de décontamination ».
`/bulletin/` garde le format en cadres numérotés. Option 2 des propositions
du 8 septembre : une page par bulletin, avec archive ; la maquette ne rend
que le dernier, à `/bulletin/`, `/en/bulletin/`, `/sw/ripoti/mpya/`. **Règle du 8 septembre 2026 pour les Défis de la lettre** : le chapitre 05
affiche un **résumé rédigé par l'assistant**, pas des citations, **qui va
droit au but** (pas de phrase d'ouverture du type « Neuf piliers signalent
des obstacles » : on commence par le premier fait, demande du 8 septembre),
écrit **à chaque intégration d'un nouveau bulletin, sans attendre de
signal** — décision du propriétaire du 9 septembre 2026 (« que tu le fasses
automatiquement à chaque fois ») qui remplace le « c'est moi qui donne le
go » de la veille ; `check_coherence` le note s'il manque —, rangé dans `data/bulletin-notes.json`
(`<num>.defis.{fr,en,sw}`, `defisDate`), daté sur la page, les neuf blocs
mot pour mot restant repliés dessous. La rubrique manuscrite « À surveiller »
essayée le même jour a été retirée à la demande du propriétaire. Jamais généré en silence. Sans
résumé, la lettre retombe sur un sommaire composé (piliers et provinces
citées). Le résumé ne contient que des faits et des nombres présents dans
les blocs. **Et il est court, depuis le 11 septembre 2026** (« c'est
beaucoup trop long là, résume et synthétise plus ») : environ 120 mots,
une phrase par province, un à quatre faits chacune, les plus marquants du
bulletin — pas la liste des zones ni des postes, qui reste dans les neuf
blocs repliés. Le 119 fait 130 mots là où le 118 en faisait 400. (Jusqu'au 8 septembre au soir, la recette retirait aussi la lettre ; elle
est publiée depuis, voir en tête de section.)


Le chantier partage quatre fichiers avec le site publié, et la barre
latérale de chaque page générée porte l'onglet Flux. Recette suivie le
4 septembre, à reprendre telle quelle tant que Flux reste en local. (Du 6 au
7 septembre elle couvrait aussi la maquette `riposte-defis` ; celle-ci a
rejoint `/riposte/` le 7 et se publie désormais avec le reste.)

1. sauvegarder `site/strings.json`, `scripts/build_pages.py`,
   `assets/css/site.css`, `site/pages.json` hors dépôt ;
2. retirer de `pages.json` l'entrée `flux-deplaces` et son onglet du groupe
   Explorer ; retirer de `build_pages.py` l'import `flux_deplaces`, les
   lectures de `flux-deplaces.json` et `flux-routes.json`, le bloc
   `if "flux" in needs` et l'appel à `flux_seed` — **sinon le workflow GitHub
   plante sur un module non commité** ; retirer de `strings.json` les clés
   `flux*` et `navFlux` (324 clés sur les trois langues le 7 septembre) —
   **sinon les nombres de l'OIM sont publiquement lisibles sans page pour
   les rendre**. Tout ce qui sert à « Riposte & défis » (`defis_synthese`,
   clés `maq*`, `navBadgeNouveau`, `defis-synthese.json`,
   `defis-anciens.json`) reste : c'est publié ;
3. régénérer — le générateur supprime lui-même les trois pages Flux via
   `site/.generated.json` —, vérifier `grep -il "flux"` muet sur les pages
   suivies et le sitemap, commiter en excluant les fichiers du chantier ;
4. restaurer les quatre fichiers, régénérer. Le générateur supprime puis
   recrée les pages Flux via `site/.generated.json`.

Les styles `cf-*` et `sk-*` restent dans `site.css`, inertes : les `mb-*`
qu'ils accompagnent servent aux barres des génomes. La barre latérale groupée
(Explorer / Comprendre / Le site), née du chantier Flux, est publiée : elle se
tient à huit onglets comme à neuf.

---

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
