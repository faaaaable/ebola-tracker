---
name: page-riposte
description: La page Riposte & defis d'ebola-tracker : ses quatre cadres (alertes, laboratoire, contacts, CTE), les extracteurs qui l'alimentent et leurs trois principes de lecture, la frise des obstacles par semaine, les vues par jour et par semaine du laboratoire et des alertes, les comptes partiels et les journees ecartees. A charger avant de toucher a la page Riposte, a extraire_alertes, extraire_laboratoire, extraire_cte, extraire_defis ou defis_synthese.
---

# La page « Riposte & défis » (`/riposte/`, `/en/response/`, `/sw/mapambano/`)

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
