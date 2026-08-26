# ebola-tracker.org — guide du dépôt

Site public de suivi de la **17ᵉ épidémie d'Ebola en RDC** (espèce Bundibugyo,
déclarée le 15 mai 2026). Il compile les bulletins officiels de l'INSP et les
rapports hebdomadaires de l'OMS. Trilingue FR/EN/SW, statique, servi par GitHub
Pages sur `ebola-tracker.org` depuis la branche `main`.

Dernier bulletin intégré à la rédaction de ce guide : **SitRep 102**, rapportage
du 24 août 2026 — 5 656 cas confirmés, 2 715 décès, létalité 48,0 %,
**58 zones touchées** (Ganga, au Bas-Uélé, est la dernière arrivée).

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
| `province-history.json` | cumul par province et par date — **cas ET décès** |
| `zones-history.json` | instantané des zones de santé par bulletin, pour le curseur de temps des cartes |
| `contacts-followup.json` | taux de suivi des cas contacts par date |
| `deces-lieu.json` | décès communautaires vs intra-CTE, par province et par date |
| `demographie.json` | âge × sexe, **figé au 5 août 2026** — l'INSP a cessé de publier cette répartition |
| `health-zones.geojson` | contours des 519 zones de santé, produit par `build_geo.py` |

`community-deaths-daily.json` alimentait un onglet retiré le 24 août. Il ne
valide qu'une province, l'Ituri, alors que son libellé annonçait le pays
entier. **Ne pas le rallumer sans corriger ce défaut.**

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

Huit pages, chacune en FR et EN : accueil, `donnees/` (+ six pages province),
`rapports/`, `le-virus/`, `chronologie/`, `faq/`, `a-propos/`, `contact/`.

Les graphiques sont rendus côté client par `assets/js/app.js` avec Chart.js.
Chaque canevas déclare son sujet via `data-chart`, les onglets via `data-mode`.

**Sept onglets sur `/donnees/`**, dans cet ordre : `epidemic`, `newCases`,
`newDeaths`, `deathsPlace`, `byProvince`, `pyramide`, `contactsFollowUp`. La
barre repond a des questions successives — combien (l'ensemble, les cas, les
deces), ou (par province), qui (age et sexe), et que fait-on contre (suivi des
contacts). `newCases` et `newDeaths` restent **voisins** : ils partagent leur
bascule de pas de temps et son etat, ce qui ne se decouvre que si les deux
boutons se touchent. Les modes `ages`, `sexes` et
`communityDeaths` restent dans le code sans bouton — décisions de publication,
pas suppressions.

---

## La structure du site

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

**Le swahili n'a pas été relu par un locuteur.** Il couvre l'intégralité du
site — 220 chaînes de `strings.json`, 142 d'`i18n.js` dont 40 fonctions, la
FAQ, les jalons de chronologie, les textes d'arrivée par province, les slugs
(`/sw/takwimu/`, `/sw/ripoti/`, `/sw/matukio/`) et les `meta`. Ce qui est
vérifié mécaniquement l'est : aucune variable `{n}` perdue ni inventée, aucune
clé manquante dans les trois blocs. Ce qui ne l'est pas : la justesse des
formulations sanitaires — prévention, traitements et vaccins, avertissement.
À faire relire avant de s'y fier.

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

**Le croisement se fait par clé normalisée**, jamais par nom affiché. Chaque
zone porte une `key` (accents retirés, casse et séparateurs écrasés) qui sert
de pont entre le shapefile, `latest.json` et `zones-history.json`.

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

`province_zones_table_html()` produit un tableau statique des zones touchées de
la province, trié par cas décroissants. Les variations de 24 h ont **leur
propre colonne** depuis le 26 août : entre parenthèses, accolées au cumul,
elles empêchaient d'aligner les chiffres et se lisaient comme une note. Six
colonnes, dans l'ordre du tableau de `/donnees/`.
Suivi d'un lien vers le tableau complet filtré sur cette province.

### `/rapports/`

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

**La periode en cours n'est pas affichee des qu'on agrege.** A un jour sur
sept, la barre de la semaine tombait de 561 a 72 cas et se lisait comme une
chute de l'epidemie. Le dernier point d'une courbe epidemique est toujours
incomplet, et un point incomplet se lit toujours comme une amelioration. Rien
n'est cache : la vue « par jour » montre ces journees a leur place, et la note
le dit. **Le mois en cours tombe sous la meme regle** — au 24 aout, la vue
mensuelle ne montre donc que mai, juin et juillet, et aout apparaitra le 1er
septembre. Trois barres pour quatre mois de donnees : c'est le prix de la
regle, et il se paiera de moins en moins cher a mesure que l'epidemie dure.

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

**Aucun encodage de couverture sur ces barres.** La vue hebdomadaire passait
`largeurSemaine` sans jamais lui donner de ratios — le plugin ne faisait donc
rien, et il est parti. Ce qu'il encode, c'est la couverture, et il ne le fait
honnetement que la ou la hauteur n'est pas un volume : les parts empilees a
100 % de `deathsPlace`. Ici la hauteur EST un volume, et une barre a demi
hachuree resterait comparable a tort. D'ou la regle qui precede : on masque
plutot qu'on ne nuance.

**`provinceEpidemic`** — même forme, aux couleurs de la province, avec sa
courbe de décès. Absent sous 50 cas cumulés. Signale les trous de plus de trois
jours au lieu de relier par-dessus.

**`byProvince`** — six courbes de cumul, une par province, chacune à sa teinte
d'identité. Il s'appelait « Cas cumulés / région » jusqu'au 26 août : ni la RDC
ni le reste du site n'emploient « région » — le découpage est la province —, et
le swahili disait `eneo`, qui désigne aussi la zone de santé, l'autre découpage
de la même page. Le `/` était par ailleurs le seul raccourci de ce genre dans
la barre. **Ce graphique ne trace que les cas**, alors que
`province-history.json` porte aussi les décès : la bascule de `newCases` s'y
transposerait telle quelle.

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

**Notes de graphique.** Elles portent d'abord le fait, ensuite les réserves.
Un lecteur ne lit pas trois lignes de mise en garde avant d'atteindre
l'information.

**Seuils.** `SEUIL_COURBE_PROVINCE = 50` dans `build_pages.py` : sous 50 cas
cumulés, une province n'a pas de graphique — la courbe serait plate et les
barres invisibles. Tshopo, Sud-Kivu et Bas-Uélé sont concernés.
`seuilLisibilite = 20` dans `deces-lieu.json` écarte de même les provinces où
une proportion n'aurait aucun sens.

---

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
codées en dur dans `REPORTED_OVERRIDE` (`app.js`) et affichées dans une teinte
distincte.

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

Le propriétaire distingue strictement trois états, et il faut s'y tenir :

- **« en local »** — construire, régénérer, montrer. Ne rien commiter.
- **« commit »** — commiter sans pousser.
- **« mets en ligne »** — commiter et pousser.

**Une seule exception, décidée le 24 août : ce fichier.** Un hook `Stop` de Claude
Code (`~/.claude/hooks/pousser-claude-md.sh`) commite et pousse `CLAUDE.md` à la
fin de chaque échange, et uniquement lui — commit limité au chemin, silencieux
quand rien n'a changé. La raison : le guide doit survivre à un re-clone, et le
perdre coûte plus cher que de le publier. Le site, les données et le code gardent
les trois états intacts.

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

## Où chercher le reste

**Les messages de commit portent le raisonnement**, pas seulement le quoi. Ils
citent les passages de bulletin qui fondent chaque décision, gardent les
mesures qui ont tranché un choix de couleur ou de seuil, et consignent ce qui
a été écarté et pourquoi. `git log` est la mémoire longue de ce projet.

Les commentaires du code font le reste : ils expliquent systématiquement le
*pourquoi*, souvent avec la date et le numéro de bulletin qui ont révélé le
problème.
