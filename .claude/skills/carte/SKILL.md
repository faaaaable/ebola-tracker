---
name: carte
description: La carte d'ebola-tracker : source geographique OCHA, projection, simplification Douglas-Peucker, les six paliers de couleur, les cercles proportionnels et leur legende, le curseur de temps et ses dates absentes, le croisement par cle normalisee, les alias de zones, le panneau date et les regles mobiles. A charger avant de toucher a une carte, a build_geo.py ou au cartogramme.
---

# La carte, et comment elle croise les données

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
proprietaire — ne pas le rouvrir. Le titre reste tel quel par choix explicite.
**Les cartes de province, elles, ont fini par tomber le 22 septembre 2026** —
voir « La rangee des provinces » dans CLAUDE.md : la regle du 27 aout les avait
epargnees, un mois plus tard elles etaient le dernier endroit de l'accueil a
porter une boite a bordure coloree.

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
