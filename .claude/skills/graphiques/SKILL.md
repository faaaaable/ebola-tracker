---
name: graphiques
description: Les onze modes de graphique d'ebola-tracker (app.js, Chart.js) : ce que chacun montre et pourquoi, le plafond d'axe et la rupture des barres de rattrapage, les trois pas de temps, les plugins maison (largeurSemaine, plageSansDonnees, ruptureRattrapage), les deux gris, le partage de figure et de tableau, les conventions d'axes, d'infobulles et de legendes. A charger AVANT de toucher a un graphique, a assets/js/app.js ou a l'export d'une figure.
---

# Les graphiques

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

**L'AXE NE SE LAISSE PAS DICTER PAR UN RATTRAPAGE** (22 septembre 2026). Le
22 juillet vaut 369 cas quand la journée médiane en vaut 63 et le plus fort
jour ORDINAIRE 143 : l'axe montait à 400, la bande 150-400 ne servait qu'à deux
barres sur cent dix-neuf, et les cent dix-sept autres étaient tassées dans le
quart du bas — 16 % de la hauteur du cadre pour une journée moyenne. Le plafond
se cale désormais sur le plus fort jour ordinaire (`plafondSansRattrapage`,
× 1,12, arrondi au pas rond : 180), et les deux barres de rattrapage sortent du
cadre. Rien n'est caché : `ruptureRattrapage` les coupe en dent de scie et
écrit leur total dans le blanc de la coupe, l'infobulle donne toujours les deux
parts. C'est la nuance de la teinte claire poussée d'un cran — non seulement la
journée ne peut pas revendiquer ces cas, mais elle ne peut pas non plus donner
l'échelle.

**La coupe est dentelée, pas pointue.** Première version, un chevron unique :
il se lisait comme une flèche « ça continue de monter ». La dent de scie est le
signe reçu d'une rupture. Et aucun trait de couleur ne la souligne — un symbole
de plus à décoder n'ajoutait rien.

**RELEVER LES BARRES COÛTE LE CROISEMENT DES COURBES, ET LES DEUX RÉGLAGES SE
TIENNENT.** Tant que l'axe montait à 400, les cumuls couraient au-dessus des
barres sans jamais les rencontrer. À 180, les barres passent de 16 à 35 % de la
hauteur et la courbe des décès — 3 699 sur un axe à 8 000, soit 46 % — s'est
retrouvée en plein dans la forêt de septembre, qui en occupe 55 %. Un
écrasement réglé, un croisement créé. L'axe de droite part donc SOUS ZÉRO, d'un
quart de sa plage, graduations négatives muettes : un cumul ne descend jamais
sous zéro, l'axe ne ment sur rien. **Le quart est un compromis assumé** — il
dégage la fin de période, où le conflit est réel, mais la courbe des décès
frôle encore deux ou trois barres hautes ; dégager complètement demanderait
45 %, et les courbes s'aplatiraient au point de perdre la forme qu'on vient y
lire.

**LE SOCLE SOUS ZÉRO EST ABANDONNÉ LE 25 SEPTEMBRE 2026, à l'accueil comme sur
les pages province** (demande du propriétaire : « je n'aime pas que la courbe
des cumulés parte plus haut »). Les deux axes partagent leur zéro, au pied du
cadre ; la courbe des décès traverse les barres de fin de période, et c'est
accepté. `socleCumuls` et `RESERVE_BARRES` sont supprimés. Ne pas les
réintroduire sans que le propriétaire le demande.

**Deux constantes gouvernent le cadre**, en tête du plugin :
`MARGE_PLAFOND` (1,12) et `DECLENCHE_RUPTURE` (1,4).
Le déclencheur est ce qui neutralise la règle d'elle-même dès qu'une vue
agrège : par semaine, le 22 juillet se dilue dans les siens et ne dépasse plus
rien, donc aucune coupe.

**LA MÊME RÈGLE SUR LES PAGES PROVINCE** (22 septembre 2026), posée sur le bloc
`provinceEpidemic` après le retour de la vue agrégée. L'Ituri était le cas le
plus sévère du site : pic ordinaire 119, barre du 22 juillet 347, axe à 350 —
des barres courantes à 15 % de la hauteur. Son axe tombe à 140.

**Un seul bloc dessine les six provinces : la règle est branchée sur le bloc,
et `DECLENCHE_RUPTURE` fait le tri.** Vérifié page par page — le Nord-Kivu ne
bascule pas (pic 50, rattrapage 41, sous le seuil), le Haut-Uélé non plus (15
contre 14). **Seul l'Ituri coupe.** Côté province la journée entière de
rattrapage est en teinte claire, sa part rapportée n'étant pas publiée à cette
échelle : elle sort du calcul du pic ordinaire par la même porte qu'au
national — une barre qui porte du rattrapage ne donne pas l'échelle.

**Quatre provinces n'ont aucun graphique** et ne sont donc pas concernées :
`SEUIL_COURBE_PROVINCE = 50` dans `build_pages.py` (Bas-Uélé, Sud-Kivu,
Sud-Ubangi, Tshopo). Piège de test : on cherche un canevas qui n'existe pas.

**Reste non branché : la vue « par jour » de `/donnees/`** — l'onglet
« Nouveaux cas » de l'ensemble du pays, bloc distinct de celui de l'accueil. Il
porte les mêmes deux barres et le même écrasement, et le helper est partagé.

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
