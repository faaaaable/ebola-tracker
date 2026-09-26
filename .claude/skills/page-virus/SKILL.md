---
name: page-virus
description: La page Le virus d'ebola-tracker et son bloc des genomes (source Pathoplexus, licence, delai de depot), plus toute l'histoire de La lettre : mises en page essayees, adresse definitive, regle de langage courant, lexique, archives par numero, et la recette devenue sans objet pour publier sans le chantier Flux. A charger avant de toucher a la page Le virus, au bloc des genomes, a la lettre ou a extraire_genomes.
---

# La page « Le virus » et le bloc des génomes

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
blocs repliés. Le 119 fait 130 mots là où le 118 en faisait 400.
**Un peu plus fourni depuis le 26 septembre 2026** (« rédige légèrement plus
de contenu ») : environ 160 mots, toutes les provinces qui ont des Défis,
trois à cinq faits chacune. Le 133 (164 mots) est le modèle. (Jusqu'au 8 septembre au soir, la recette retirait aussi la lettre ; elle
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
