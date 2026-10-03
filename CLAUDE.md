# ebola-tracker.org — guide du dépôt

Site public de suivi de la **17ᵉ épidémie d'Ebola en RDC** (espèce Bundibugyo,
déclarée le 15 mai 2026). Il compile les bulletins officiels de l'INSP et les
rapports hebdomadaires de l'OMS. Trilingue FR/EN/SW, statique, servi par GitHub
Pages sur `ebola-tracker.org` depuis la branche `main`.

**Journal des intégrations de septembre 2026** (SitRep 127 à 135 : CTE, vaccination,
contacts, audit des vides des graphiques) : skill `journal-bulletins`. La conception
de la partie vaccination de la page Riposte : skill `page-riposte`. Trois règles en
sortent et restent ici :
- **Plusieurs bulletins d'un coup : on les intègre UN PAR UN, dans l'ordre, en
  deux (ou trois) mises à jour séparées** (règle du propriétaire, 3 octobre 2026).
  `update_data` ne retraite que le plus récent ; `python scripts/update_data.py
  --sitrep N` intègre le bulletin N voulu. Pour chaque bulletin, dans l'ordre :
  `update_data --sitrep N`, les extracteurs, le codage des Défis et le résumé de
  la lettre, `build_pages` (qui fige l'instantané `data/lettres/N.json`),
  `check_coherence`, puis le commit / push de CE bulletin avant de passer au
  suivant. Chaque bulletin a ainsi sa lettre, son « + » du jour juste (cas, décès,
  guéris) et son commit. Le rattrapage par `backfill_zones_history` puis
  `backfill_province_history` ne sert plus qu'à réparer un lot déjà publié.
- **Un écart bloquant imputable à la source passe par `EXCEPTIONS_SOURCE`** de
  `check_coherence.py` (contrôle, bulletin, province et valeurs lues, avec la
  citation du bulletin) — jamais en corrigeant les données, jamais en rendant le
  contrôle non bloquant.
- **Ne pas refaire la clé `vaccChartRevisee`** (valeur révisée en cercle creux)
  sans que le propriétaire le redemande.

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

L'historique de la page `/donnees/` (chapitres, graphiques, maquettes, têtes de
page) vit dans la skill `gabarits-site`. Les modes `epidemic`, `contactsFollowUp`,
`deathsPlace`, `byProvince`, `ages`, `sexes` et `communityDeaths` restent dans
`app.js` sans cadre ni bouton : décisions de publication, pas suppressions.

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

## Nom du site, compte X, alerte Telegram, rangée des provinces

Cette partie vit dans la skill `gabarits-site` (`.claude/skills/gabarits-site/SKILL.md`), chargee a la demande.
**`scripts/build_feeds.py` ne doit pas être supprimé** : le flux RSS est retiré
depuis le 23 septembre 2026, mais `notifier_telegram.py` lui emprunte la
composition du message.

## Conventions établies

**La fiche d'un territoire (28 septembre 2026).** « Ensemble du pays » et les
pages province suivent le MEME plan, a deux echelles : en-tete (chiffres cles
et phrase des 7 derniers jours contre les 7 precedents, `point_sept_jours`),
[01 carte, province seulement — celle du pays reste a l'accueil], cas, deces
avec le lieu du deces dessous, ou (zones / provinces), [qui, pays seulement],
la riposte, la chronologie. Numeros calcules par `province_numeros()`.
**Regle : une information a UNE page qui la detaille.** Les graphiques de la
riposte vivent sur la page Riposte, ou l'on compare les provinces ; la fiche
n'en garde que quatre chiffres (contacts vus, occupation, positivite,
vaccines) et « Les difficultes signalees » — la phrase de la province dans le
resume des Defis de la lettre (`difficultes_province`, nom dans les 40
premiers caracteres), d'ou l'importance d'ecrire ce resume UNE phrase par
province, ouverte par son nom. Le lieu du deces a quitte la page Riposte. Les
graphiques de riposte a onglets de l'Ituri et du Nord-Kivu ont ete retires des
fiches. **Le cadre riposte n'est que sur `PROVINCES_RIPOSTE_FICHE` = Ituri et
Nord-Kivu** (28 septembre 2026) : un seuil a 40 cas a d'abord ecarte le
Sud-Kivu, le Bas-Uele et le Sud-Ubangi, puis le proprietaire a retire le
Haut-Uele et la Tshopo, « donnees trop instables a cause du petit
echantillon ». Sur ces deux fiches le cadre est DEVELOPPE : apres les
quatre chiffres, les graphiques de la page Riposte restreints par
`data-province` (alertes, laboratoire, contacts, CTE, vaccination avec son
tableau par zone), chacun seulement si la province a au moins
`RELEVES_MIN_GRAPHIQUE` (10) releves, 3 pour la vaccination ; puis les
difficultes et, replie, « Ce que dit le bulletin, pilier par pilier » :
les propositions des blocs « Defis » du dernier bulletin qui concernent la
province (`extraits_defis_province` : coupe aux « ; », points et « : »
suivis d'une province, jamais dans une parenthese ; une zone de sante nommee
vaut sa province).

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
  15 septembre 2026, remis a 50 le meme jour). Les exceptions passent par
  `COURBE_PROVINCE_FORCEE` (`build_pages.py`), province par province : la
  Tshopo y est depuis le 28 septembre 2026, a la demande du proprietaire,
  avec l'axe des nouveaux cas quotidiens fixe a 10 (`data-y-max`, vue par
  jour seulement).
- **Chaque province qui a une courbe a aussi celle des deces** (28 septembre
  2026) : meme bloc `provinceEpidemic` d'`app.js`, parametre par
  `data-champ="deaths"`, rouge du site, seule courbe de cumul des deces.
  `province_numeros()` numerote tous les cadres, zones compris.
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
