# ebola-tracker.org — guide du dépôt

Site public de suivi de la **17ᵉ épidémie d'Ebola en RDC** (espèce Bundibugyo,
déclarée le 15 mai 2026). Il compile les bulletins officiels de l'INSP et les
rapports hebdomadaires de l'OMS. Bilingue FR/EN, statique, servi par GitHub
Pages sur `ebola-tracker.org` depuis la branche `main`.

Dernier bulletin intégré à la rédaction de ce guide : **SitRep 101**, rapportage
du 23 août 2026 — 5 584 cas confirmés, 2 680 décès, létalité 48,0 %.

---

## Le principe qui gouverne tout

**Chaque chiffre affiché doit être traçable jusqu'à un PDF de `reports/`.**

Le site est un miroir, pas une source. Il n'invente pas de valeur, ne
réattribue pas un cas d'une province à une autre, ne comble pas un trou par
interpolation. Quand la source ne dit pas, le site ne dit pas — et le dit.

Deux illustrations à connaître, parce qu'elles reviendront :

- Les **décès « à ventiler »** de l'Ituri ne sont répartis sur aucune zone. Ils
  étaient 233 au SitRep 100, **250 au SitRep 101** : la somme des 28 zones donne
  1 838 décès quand la province en déclare 2 088. L'écart reste visible plutôt
  que comblé, et il grossit à chaque bulletin qui ajoute des décès intra-CTE non
  encore rattachés à une zone.
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

**Cinq onglets sur `/donnees/`** : `epidemic`, `byProvince`, `contactsFollowUp`,
`deathsPlace`, `pyramide`. Les modes `ages`, `sexes` et `communityDeaths`
restent dans le code sans bouton — décisions de publication, pas suppressions.

---

## La structure du site

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
(`provinceSummaryBody`), triées par cas décroissants. Colonnes : province, cas
cumulés avec sa part du pays, décès, létalité, zones touchées, nouveaux cas.
Chaque ligne porte la pastille de couleur de sa province.

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

### Les pages province

`province_zones_table_html()` produit un tableau statique des zones touchées de
la province, trié par cas décroissants, avec le delta 24 h entre parenthèses.
Suivi d'un lien vers le tableau complet filtré sur cette province.

### `/rapports/`

`report_chip()` produit une carte par bulletin, **cliquable dans son entier** —
auparavant seule la petite icône était un lien, cible minuscule et carte qui
paraissait inerte. Une navigation par mois et une recherche filtrent la liste
côté client. Les rapports OMS ont leur propre liste.

---

## Les graphiques

Neuf modes dans `app.js`. Chaque canevas déclare son sujet par `data-chart`,
chaque onglet par `data-mode`.

| Mode | Source | Où |
|---|---|---|
| `epidemic` | `sitreps.json` | accueil **et** premier onglet de `/donnees/` |
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

**`provinceEpidemic`** — même forme, aux couleurs de la province, avec sa
courbe de décès. Absent sous 50 cas cumulés. Signale les trous de plus de trois
jours au lieu de relier par-dessus.

**`byProvince`** — six courbes de cumul, une par province, chacune à sa teinte
d'identité.

**`contactsFollowUp`** — une courbe, plus un **pont en pointillés atténué** sur
les périodes sans donnée. Ce pont n'est jamais une valeur : c'est un repère
visuel, et la note le dit.

**`deathsPlace`** — six barres hebdomadaires empilées à 100 %, communauté
contre centre de traitement, avec la moyenne en pointillés sur un second axe
invisible.

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
et espace ordinaire avant le signe, jamais insecable — c'est la convention
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
