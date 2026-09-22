---
name: chantiers-ouverts
description: Chantiers ouverts et mis de cote d'ebola-tracker : maquettes sorties du depot (accueil, provinces, Flux & deplaces, Riposte & defis), synthese des defis a ecrire, vue Par province des alertes en stash, et les dettes connues. A charger quand il faut reprendre un chantier en attente, retrouver ou une maquette a ete rangee, ou savoir ce qui a deja ete essaye et ecarte.
---

# Chantiers ouverts

Cette liste etait dans CLAUDE.md, relue a chaque echange pour un contenu qui
ne sert qu'au moment ou l'on reprend un chantier. Les interdictions qu'elle
portait — ne pas refaire sans qu'il le redemande — sont restees dans le guide.

- **Les maquettes de l'accueil (9 septembre 2026) sont hors dépôt**, dans
  `~/Desktop/rapport ebola tracker/_mis-de-cote-2026-09-10/maquettes/` avec
  leurs scripts : l'accueil en planche d'atlas ; en-tête, menu et carte
  gardés avec trois figures dessous (bande des bulletins, un trait par
  jour ; nouveaux cas et jalons sur un même axe ; provinces à l'échelle) ;
  la carte A « atlas » (cadrage épicentre, médaillon, zones étiquetées) et
  B « journal » (encadré en phrases, fond de rivières) ; trois habillages
  de l'encadré (registre, marge, cartouche) ; trois places de l'encadré
  (bandeau au-dessus, cartouche dans la carte avec infobulle sur la zone,
  règle sous la carte dont les chiffres suivent le curseur des dates).
  Décisions prises en chemin par le propriétaire, à garder si l'on
  reprend : la bascule Zones colorées / Cercles est jugée superflue sur
  l'accueil ; pas de rivières, carte épurée ; une seule couleur d'accent
  pour les chiffres, le bleu, les autres en encre ; barres des quatorze
  derniers jours sous l'encadré, avec infobulle date + cas, masquées au
  survol d'une zone ; « SitRep n°X » à droite de « Situation au … » ;
  nombres alignés à gauche de leur colonne. Aucune décision finale.
- **Le bloc des provinces de l'accueil, cinq propositions — mis de côté le
  6 septembre 2026, hors dépôt depuis le 10.** Le propriétaire ne veut plus des six cases (« un
  modèle que je retrouve sur d'autres sites »). Maquette autonome
  `tmp/proto-provinces/` écrite par `scripts/prototype_provinces.py` (non
  commité), qui charge la feuille de style du site : le bloc actuel en
  référence, puis (1) une ligne par province avec la part du pays en filet,
  (2) une barre pour le pays, cas puis décès, (3) les cercles à surface
  proportionnelle, (4) une courbe de cumul par province avec les chiffres
  du jour, (5) six colonnes de chiffres sans cadre. Avis donné : la 2 ou
  la 4. Aucune décision prise, rien dans le site. Relancer le script
  après un nouveau bulletin, il lit `latest.json` et `province-history.json`.

- **Maquette « Riposte & défis » en deux parties** (`/riposte-defis/`,
  `/en/response-challenges/`, `/sw/mapambano-changamoto/`), 6 septembre 2026,
  en local, `noindex` et hors sitemap. Alternative demandée par le
  propriétaire à la page Riposte & défis publiée : la première partie est
  la page Riposte telle quelle (cinq cadres, sans les citations), la
  seconde est **rédigée** — neuf obstacles depuis mai, chacun un paragraphe
  sourcé bulletin par bulletin — avec une mise en page qui n'existe nulle
  part ailleurs : une bande sombre d'ouverture (seul endroit du site en
  couleurs inversées), une frise « quand chaque obstacle apparaît dans les
  bulletins » (un trait par bulletin, la barre de la première à la dernière
  mention, calculée par mots-clés sur `data/corpus/qualitatif.jsonl` +
  `data/defis.json`), puis une fiche numérotée par obstacle en deux
  colonnes. Pièces : `data/defis-synthese.json` (textes fr/en, mots-clés —
  **brouillon d'auteur à relire**, le swahili affiche le français avec la
  note), `scripts/defis_synthese.py` (rendu écrit en dur), gabarit
  `site/pages/riposte-defis.html`, styles `.dossier`, `.frise-*`,
  `.fiche*`. Le générateur pose désormais la balise `robots` depuis
  `page.noindex` (`layout_values["robots"]`). Suite du même jour, sur
  demande : **la première partie a pris l'idiome de la seconde** — une bande
  claire jumelle de la bande sombre (« Première partie · Ce que fait la
  riposte », les quatre chiffres sur une rangée, le sommaire au pied), puis
  les cinq cadres en `.cadre-fiche` (numéro serif bleu, titre, ligne
  italique, paragraphe, cadre pleine largeur, sans colonne de titres) ; et
  **trois touches de bleu** dans la seconde partie (bande bleu nuit
  `#10283A`, barres de frise bleu pâle, numéros en `--accent-strong`),
  scopées `.dossier:not(.dossier-clair)` — la version non scopée avait
  assombri la bande claire. Puis (même jour) : le sommaire de six liens au
  pied de la bande claire retiré, la bande resserrée (354 px au lieu de
  555), le chapeau de la page annonce les deux parties (`maqLede`), et une
  **dixième fiche « Les équipes attaquées »** (`attaques`, entre insécurité
  et points de contrôle) — les bulletins rapportent des agressions d'équipes
  depuis le 17 juillet, sans jamais les chiffrer : pont Muchanga, PoC de
  Mukulia, Mungamba, Croix-Rouge près d'Isiro, Rwampara, un mort dans un
  accident à Bambu, un assassinat au Nord-Kivu, la menace de brûler le CTE
  de Katwa. Mots-clés sans « bless » (« Faiblesse » le contient). Si elle est adoptée, elle remplace le gabarit
  de `/riposte/` et les citations sous les cadres disparaissent ; sinon la
  supprimer avec ses trois pièces.

- **La synthèse des défis depuis mai**, décidée le 6 septembre 2026 avec
  le propriétaire : un chapitre rédigé sur la page Riposte & défis, une
  dizaine de difficultés datées (prestataires impayés, refus d'enterrement
  sécurisé, CTE saturés, sang indisponible, zones qui ne rapportent pas…),
  chacune avec les bulletins qui l'attestent, mise à jour à la main. Un
  script ne doit pas décider que deux formulations désignent le même
  problème. Matière première : `data/corpus/qualitatif.jsonl` (776
  entrées, époques B à D) et `data/defis.json` ; à trier par thème avec
  premières et dernières mentions avant d'écrire.

- **Page « Flux & déplacés » — intégrée au générateur le 4 septembre 2026,
  en local, non publiée à cette date ; SORTIE DU DÉPÔT le 10 septembre**
  (voir « Publier sans publier », en tête : tout est dans
  `~/Desktop/rapport ebola tracker/_mis-de-cote-2026-09-10/flux/`). `/flux-et-deplaces/`,
  `/en/flows-and-displacement/`, `/sw/mtiririko-na-wakimbizi/`, entrée
  « Flux & déplacés » dans le groupe Explorer de la barre, après La riposte.
  Elle décrit une PÉRIODE (ce que l'OIM a observé du 15 mai au 28 août 2026)
  et le dit en tête : elle ne se met pas à jour avec les bulletins, sauf une
  phrase, le compte des zones à transmission active du dernier bulletin
  (définition OIM appliquée à `latest.json`). Pièces : `site/pages/
  flux-deplaces.html` (gabarit), 72 clés `flux*` par langue dans
  `strings.json` (le swahili n'est pas relu), `scripts/flux_deplaces.py`
  (rendu écrit en dur : diagramme de flux SVG à trois colonnes, 149 rubans,
  survol en CSS `:has()` généré dans le SVG — nœud = entrants et sortants,
  ruban = la bande entière — ; tableaux ; barres), `data/flux-deplaces.json`
  (la matière : matrice mesurée sur les tracés vectoriels de la figure 9 du
  tableau de bord OIM de la semaine 34, sept points de contrôle, part des
  trajets liés aux zones actives, déplacés des zones touchées, seize
  documents avec leur page dtm.iom.int ; assemblé par `scripts/
  construire_flux_deplaces.py` depuis `report_iom/analyse/`, hors dépôt, à
  ne relancer que si les mesures changent), styles `mb-*` et `sk-*` en fin de
  `site.css`. Aucun document OIM hébergé, aucune carte reproduite : des
  nombres cités avec la ligne de crédit imposée. Décisions prises en route :
  la figure des dix couloirs (figure 7) retirée au profit de la matrice — les
  deux ne sont pas sur la même base, tous les trajets contre les 3 639
  renseignés, rapport constant 100/82, Bunia → Bunia 12,6 % contre 15,3 % — ;
  la tuile « trajets entre deux zones actives » retirée (l'indicateur OIM ne
  compte pas les trajets d'une zone active vers une zone indemne, pourtant le
  mécanisme d'extension) ; « Mouvements de population » écarté, trop IDP.
  Outils nés du chantier : `scripts/extraire_sankey_oim.py` (mesure des
  Sankey ; la figure 10 se mesure pareil mais ses étiquettes sont éclatées
  lettre à lettre, non fait), `scripts/telecharger_via_brave.mjs`
  (crisisresponse.iom.int et dtm.iom.int refusent curl et le headless ;
  fenêtre Brave visible `VISIBLE=1`, `NAVIGUER=1` pour les liens
  `dtm_download_track`), `scripts/verif/capture_survol.mjs` ;
  `scripts/prototype_mobilite.py` est remplacé par le générateur et peut
  être supprimé. Reste à faire avant publication : relire le swahili, écrire
  à dtmdrc@iom.int (classeur « destinations », accord sur la figure
  redessinée), ajouter la liste OIM à `/rapports/`.
  **Carte des flux (4 septembre, en local)** : dans la section des flux,
  avant le diagramme — fond OCHA de l'Ituri cadré sur Bunia (transformation
  carte nationale → carte de province déduite des tracés, `affine()`), sept
  points de contrôle en cercles (coordonnées lues sur la carte 1 du rapport,
  `coordPoints`, approximatives et dites telles), flux de zone à zone en
  arcs, et surtout **la charge des routes** : chacun des 105 trajets de la
  matrice suit le plus court chemin sur le réseau OpenStreetMap du départ au
  point de contrôle puis à l'arrivée — 71 en entier, 30 sur leur seule
  moitié connue (« Autres ZS d'Ituri », « Autres provinces / pays » n'ont
  pas de position), le Nord-Kivu ramené à la sortie sud de l'emprise sur la
  route de Beni avec une étiquette de direction, 4 sans chemin
  (`scripts/construire_flux_routes.py`, entrée `tmp/routes/osm-bunia.json`
  extrait Overpass hors dépôt, sortie `data/flux-routes.json`, 51 segments
  à jeu de trajets constant + 749 routes de fond, 123 Ko). `assets/js/
  flux.js` (chargé par le besoin `flux` de la page) : couches Points /
  Routes / Flux / Déplacés, filtre par chef-lieu qui recalcule la charge,
  infobulle, panneau départs / arrivées avec le point de passage, zoom et
  déplacement. La couche Déplacés est construite mais éteinte, « à
  confirmer avec l'OIM ». Chemins DÉDUITS, seul le point de contrôle est
  observé ; Aru, Mahagi, Boga hors emprise OSM (raccords en pointillé) ;
  attribution OpenStreetMap ODbL dans la note. Depuis le 4 septembre au
  soir : **deux cadrages** (Ituri / Bunia, boutons `data-cf-cadre`, la ville
  d'après l'emprise des rues extraites — second extrait Overpass
  `tmp/routes/osm-bunia-ville.json`, residential/service/track, rues de plus
  de 400 m gardées en fond) ; **les trajets internes à une zone sont routés
  du chef-lieu au point de contrôle** (une seule moitié, la suite est dans
  la zone) ; **échelle des traits** dans la légende, trois étalons 5, 15 et
  30 %, aux mêmes largeurs que les tronçons — largeurs en PIXELS ÉCRAN
  (`vector-effect: non-scaling-stroke`, `largeur_route()` côté Python et la
  même formule dans `chargerRoutes`), comme les cercles des points (rayon
  divisé par le zoom, `data-r0`), les halos et corps des étiquettes
  (`--cf-k`) et le décalage des étiquettes de points (recalculé en JS). Le
  chef-lieu de Bunia de `zoneCoordinates` est à 1,7 km de la route
  principale, d'où un raccord en pointillé dans la ville : à revoir si l'on
  touche à ce point, qui sert aussi aux bulles de l'accueil.

- **Maquette « Flux & déplacés en cinq chapitres » — 4 septembre 2026, en
  local, rien de publié.** La page en ligne n'existe toujours pas ; la page
  locale d'origine est intacte. À côté d'elle, une MAQUETTE autonome dans
  `tmp/proto-flux/` (gitignoré) écrite par `scripts/prototype_flux.py`, sur
  le modèle de `prototype_riposte.py` : elle reprend telles quelles les
  parties déjà construites (carte routée, diagramme, points, déplacés,
  frontière, sources) en les EXTRAYANT du rendu de `flux-et-deplaces/`, et y
  ajoute quatre chapitres neufs. Ordre proposé : où sont allés les habitants
  du foyer, ce qui était annoncé et ce qui est arrivé, ce qu'on a compté sur
  la route, où le virus peut aller maintenant, les déplacés et ce qui les
  déplace.
  - **Chapitre 1** : carte nationale des 519 zones, coloriée sur la rampe
    `is-1..is-6` du site (on ne recolorie pas le site pour une page), échelle
    logarithmique, QUATRE lectures au choix — part de cohorte détectée en mai,
    jours de présence en juin pour les cohortes de l'Ituri et du Nord-Kivu,
    jours de présence en juillet pour la cohorte de Kisangani. Légende bornée
    en chiffres, CALCULÉE depuis les mêmes seuils que le coloriage. Infobulle
    HTML au survol et au tap (idiome `cf-tip`), parce que le tableau ne montre
    que trente zones quand la carte en colorie 136 : sans elle, les deux tiers
    de la donnée sont visibles mais anonymes. Tableau à douze lignes, le reste
    replié.
  - **Trois gris à ne pas confondre**, et c'est le point d'honnêteté du
    chapitre : gris clair = aucun membre détecté ; gris foncé = zone écartée
    par Flowminder faute de données fiables (79 zones, dont Mangala et ses
    263 cas) ; hachuré = hors des 90 premières destinations, valeur non
    publiée (434 zones sur la vue Kisangani, le rapport ne publiant qu'un
    top 90). Colorier ces dernières en « aucun » aurait été faux.
  - **Chapitre 2, le seul bloc vivant** : les classements confrontés au
    dernier bulletin, recalculés à chaque SitRep. Au 111 : cohorte de l'Ituri,
    10 des 10 premières destinations touchées et 27 des 30 ; cohorte du
    Nord-Kivu, 25 des 30. Trois zones annoncées et encore indemnes (Watsa,
    Nyarambe, Biringi), neuf touchées sans avoir été vues, dont quatre étaient
    écartées de l'étude. Personne d'autre ne peut produire ce bloc, faute
    d'avoir la série des zones.
  - **Kisangani à part, pas dans les compteurs.** Flowminder signale la ville
    fin juin comme sans cas mais à risque ; le premier cas suit ; un rapport
    rapide du 17 juillet cartographie ses sorties. Géographie tournée vers
    l'ouest, 14 zones de Kinshasa dans les 50 premières. Bilan plus faible,
    6 des 10 premières et 13 des 30 — mêler ce chiffre au 10 sur 10 de l'Ituri
    abîmerait un message net avec un chiffre ambigu, alors que les deux ne se
    comparent pas. Le texte dit que l'écart peut venir de la transmission
    comme de la surveillance (les indemnes sont surtout des ports du fleuve)
    et ne tranche pas.
  - **`scripts/extraire_flowminder_tshopo.py`** : ce rapport n'a pas de
    tableau sur HDX, ses valeurs ne sont que dans le PDF, imprimées sur trois
    blocs de colonnes côte à côte — une lecture linéaire du texte en rend 83
    sur 90. Le script lit les mots par leur POSITION (quatre colonnes à
    abscisses fixes, trois blocs décalés d'un pas constant) et s'arrête si un
    rang manque, se répète, ou si les valeurs ne décroissent pas. 90 sur 90.
  - **Chapitre 4** : les dix zones les plus exposées à deux semaines selon le
    modèle d'invasion de l'INRB (dépôt public, sortie quotidienne), avec leurs
    intervalles, et le bilan rétrospectif calculé — sur les 12 zones ayant
    déclaré leur premier cas depuis le 31 juillet, 8 étaient dans les vingt
    premières du classement de ce jour-là. Demande d'écrire à l'INRB avant
    réutilisation ; sans réponse, ce chapitre se réduit à un paragraphe et un
    lien.
  - **Chapitre 5** : les déplacés de l'OIM tels quels, plus les dix plus
    grands déplacements de 2026 en Ituri et dans les Kivus d'après l'IDMC
    (108 événements, tous liés au conflit, aucun à Ebola).
  - **Postes frontaliers** : les sept points d'entrée vers l'Ouganda avec
    leurs passagers hebdomadaires (Busunga 9 158, Mpondwe 7 326, Goli 4 150),
    d'après un rapport d'Imperial College repris par l'INRB.
  - **Entrées, toutes hors dépôt** : `~/Desktop/rapport ebola tracker/`
    (42 fichiers, 218 Mo : Flowminder, OCHA, HOT OSM, Insecurity Insight, et
    les trois rapports Flowminder en PDF dont celui de Kisangani), le dépôt
    public `INRB-UMIE/BDBV2026-Data` et son modèle de risque, l'IDMC sur HDX.
    Un état des lieux complet du dossier est dans
    `~/Desktop/rapport ebola tracker/_ETAT-DES-LIEUX.md`.
  - **Reste à faire** : le chapeau du chapitre 1 parle encore de trois
    lectures alors qu'il y en a quatre ; la page est longue, environ quatre
    écrans avant la carte routée, et le chapitre 4 est le candidat au
    découpage s'il faut alléger ; basculer le fond de carte sur l'extraction
    HOT (routes, localités, au 5 août, ODbL) à la place des extraits Overpass
    faits à la main ; relire le swahili ; ajouter la liste des documents OIM à
    `/rapports/` ; écrire à l'OIM (couche des déplacés) et à l'INRB.
  - **`tmp/` est gitignoré** : la maquette elle-même ne survit pas à un
    re-clone, seuls les scripts la reconstruisent — et ils sont eux-mêmes non
    commités. Les commiter le jour où la page se publie. En attendant, une
    **copie de sauvegarde hors dépôt** existe dans
    `~/Desktop/rapport ebola tracker/_maquette-flux/` (19 fichiers, 1,4 Mo) :
    les sept scripts du chantier, le gabarit, `flux.js`, les deux fichiers de
    données, les 106 chaînes `flux*` par langue extraites de `strings.json`,
    l'entrée de `pages.json`, le rendu de la maquette, et un `LISEZ-MOI.md`
    qui donne la marche à suivre pour tout remettre en place après un
    re-clone. Fragilité connue et assumée : le modèle de risque de l'INRB,
    les événements de l'IDMC et les passages aux points d'entrée sont lus
    dans `/tmp`, effacé au redémarrage ; ils se retéléchargent en une
    minute, le LISEZ-MOI dit où.

- **La vue « Par province » des alertes attend dans un `git stash`** (31 août,
  « vue Par province des alertes (7 derniers bulletins) ») : troisième
  bascule du cadre des alertes de `/riposte/` — une barre par province à
  100 % de ses reçues (validées / invalidées / non vérifiées), effectif sous
  le nom, transférées en pied d'infobulle, même fenêtre glissante que les
  cases de tête. Construite, testée (`test_onglets` sans erreur), montrée,
  puis mise de côté à la demande du propriétaire. `git stash pop` la
  reprend ; elle touchait `app.js`, `i18n.js`, `site/pages/riposte.html` et
  `capture_canvas.mjs` (clic d'une bascule `data-vue`), plus les pages
  régénérées. Elle remplaçait un tableau essayé puis écarté le même jour —
  en volumes bruts rien n'était comparable, en parts tout l'est.

- **`.github/workflows/update_data.py`** : copie morte du script, 530 lignes
  contre 1 262, référencée nulle part. À examiner.
- **Bas-Uélé** porte le rouge `#993A2E` comme couleur d'identité. S'il franchit
  les 50 cas, ses barres seraient rouges sur un site où le rouge signifie la
  mort. Lui trouver une autre teinte le moment venu.
- **`daysNoCase`** a été retiré de `latest.json` : il s'incrémentait à chaque
  exécution du script et non par jour écoulé. Le commentaire laissé dans
  `update_data.py` explique comment le recalculer depuis les dates si le besoin
  revient.
- **La lecture par province du lieu du décès** — Nord-Kivu 66,8 % contre
  Haut-Uélé 50,0 % — n'est plus affichée. Le détail reste dans `deces-lieu.json`.
- **Tableau historique des 17 épidémies** : demandé, mis de côté faute de
  source interne.
- **`.cache/geo/RDC_Zone_de_sante_09092019.zip` est versionné** — 6 Mo, le
  shapefile OCHA que `build_geo.py` télécharge. Il pèse à lui seul plus que
  tout le reste du dépôt, et GitHub Pages le sert publiquement, ce qui est
  exactement la raison pour laquelle `tmp/`, `data/corpus/` et
  `assets/social/` en sont tenus à l'écart. Ce n'est pas un problème de
  confidentialité — la donnée est publique — mais c'est un cache
  reconstructible qui alourdit chaque clone. Constaté le 25 août en comptant
  les lignes du dépôt ; à sortir du dépôt et à ajouter au `.gitignore`.
- **`tmp/`, `assets/social/`, `data/corpus/`** restent hors dépôt. GitHub Pages
  sert tout le dépôt : ce qui est commité devient publiquement téléchargeable.

---
