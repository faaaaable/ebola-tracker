# ebola-tracker.org — guide du dépôt

Site public de suivi de la **17ᵉ épidémie d'Ebola en RDC** (espèce Bundibugyo,
déclarée le 15 mai 2026). Il compile les bulletins officiels de l'INSP et les
rapports hebdomadaires de l'OMS. Trilingue FR/EN/SW, statique, servi par GitHub
Pages sur `ebola-tracker.org` depuis la branche `main`.

Dernier bulletin intégré à la rédaction de ce guide : **SitRep 110**, rapportage
du 1ᵉʳ septembre 2026 — 6 250 cas confirmés, 3 039 décès, létalité 48,6 %,
1 439 guéris, 869 patients en CTE, suivi des contacts 89,0 % (16 719 vus sur
18 784), **60 zones touchées** (aucune nouvelle zone), 64 nouveaux cas
(Ituri 39, Nord-Kivu 20, Haut-Uélé 4, Tshopo 1) et 32 décès du jour
(25 communautaires, 7 intra-CTE). Intégré **en local le 3 septembre**, non
publié à cette date, six provinces et 60 zones relues une à une contre les
pages 2 et 3 du PDF, zéro écart ; les cumuls prolongent exactement ceux du
109 (+64 cas, +32 décès, +30 guéris, par province aussi). Deux lectures
apprises : (1) la ligne Total du tableau des provinces est rendue sur deux
lignes de texte, le libellé **seul sous ses chiffres** (« 64 6 250 3 039
48,6% 60/151 (39,7 %) » puis « Total ») — aucun motif ne mordait, arrêt sur
« Table de répartition par province introuvable » ; `recoller_total_orphelin`
recolle un « Total » isolé à la ligne de chiffres voisine, seulement si la
ligne recollée correspond à l'un des deux motifs du tableau résumé ; (2) le
Haut-Uélé écrit « Au terme de la journée, 62 patients, soit un taux
d'occupation global de 51,7% (120 lits) », sans « hospitalisés » ni « pour
N lits » — deux motifs ajoutés en dernière position dans `extraire_cte.py`,
diff limité au 1ᵉʳ septembre, et le total CTE passe de 807 à **869, le
chiffre exact de la bande de chiffres clés**. Deux incohérences sont dans la
source, pas dans l'extraction, et restent visibles : le tableau 2 donne
**0 nouveau cas à la ligne Tshopo** quand sa zone Mangobo en porte 1 et que
le tableau 1 et les faits saillants disent 1 (le site retient 1) ; et la
section Laboratoire ne compte que 63 positifs du jour (39 + 20 + 4, rien pour
la Tshopo) pour 64 nouveaux cas — l'écart « 63 vs 64 » de `check_coherence`
est non bloquant et attendu. Rwampara et Beni avaient d'abord leur
ventilation des décès du jour à `None` (queues « 7 2 2 » et « 5 3 3 »
reconstruites depuis le texte, ambiguës par nature) ; le propriétaire a
confirmé 2 et 3 décès communautaires, et `ventiler_par_soustraction()` les
déduit désormais de la ligne de province (13 - 11 = 2 pour Rwampara,
12 - 9 = 3 pour Beni), voir les pièges connus. Le chemin grille
du tableau des provinces est hors jeu depuis que le 106 a mis le titre
« Tableau 1. » en première ligne de la grille (`extract_province_summary`
cherche « Province » en `t[0][0]`) : c'est le repli texte qui lit tout depuis.

Le **SitRep 109**, rapportage du 31 août 2026 — 6 186 cas confirmés, 3 007
décès, létalité 48,6 %, 60 zones touchées, 86 nouveaux cas et 57 décès du
jour (43 communautaires, 14 intra-CTE) — avait été intégré en local le
2 septembre. Il a fait tomber trois lectures, toutes corrigées le
même jour et vérifiées ligne à ligne contre les pages 2 et 3 du PDF (six
provinces et 60 zones, zéro écart) : (1) la grille pdfplumber du tableau des
provinces a éclaté son en-tête sur cinq lignes avec une colonne « Nouveaux
cas » en double, la lecture par en-tête est revenue vide et le repli texte ne
connaissait que l'ancien ordre (nouveaux cas en fin de ligne) —
`PROVINCE_SUMMARY_ROW_NEWFIRST_RE` lit désormais l'ordre du 104 dans le texte
brut, les deux motifs s'excluant l'un l'autre ; (2) la ligne Total du tableau
détaillé est rendue avec des `None` intercalés (`'48,6%', None, '86', None,
'43', None, '14', None, '57'`) et les index fixes publiaient **486 décès
communautaires** (la létalité) et 86 décès du jour (les nouveaux cas) — le
national exige maintenant communautaires + intra-CTE = total, sinon il relit
la ligne Total du texte ; (3) la section des CTE s'intitule « Prise en charge
holistique », inconnue d'`extraire_cte.py`, qui l'accepte désormais (le mot
« holistique » la distingue du « Prise en charge » des époques B et C), et
« Huit (8) patients sont en isolement » au Sud-Kivu demandait une parenthèse
optionnelle après le nombre. `check_coherence` repasse sans écart bloquant,
les deux écarts non bloquants (positivités 038, 065, 072 ; occupation Tshopo
108) étant antérieurs. Le 108 avait ses propres particularités : 7 lignes de
zone reconstruites depuis le texte brut (toutes vérifiées contre le PDF,
zéro écart sur les 60 zones) ; le bulletin publie 32,0 % d'occupation CTE à
la Tshopo quand ses propres nombres font 7/25 = 28 % (écart laissé visible,
note de check_coherence) ; deux formulations labo inédites — « 1 swab reçu
et testé » au Bas-Uélé, « 2 échantillons reçus, tous négatifs » à la
Tshopo — ont demandé trois motifs nouveaux dans `extraire_laboratoire.py`
(dont « dont 1 swab analysé » du 106) ; la réextraction n'a touché que les
Tshopo des 106-107 et le 30 août, diff relu ligne à ligne, et le garde-fou
« positifs du jour = nouveaux cas » repasse (59 = 59). Autre tournure
inédite, côté CTE : le Nord-Kivu écrit « en sursaturation (128,2 % ;
282/220) » — deux motifs ajoutés à `extraire_cte.py` (taux entre
parenthèses, lits au dénominateur de la fraction), diff limité au seul
30 août, national à 813/1 223 = 66,5 %. Le Sud-Kivu repasse à « ND » au
tableau des alertes là où le 107 disait des zéros.

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

Huit pages, chacune en FR et EN : accueil, `donnees/` (+ six pages province),
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

**La SEMAINE en cours n'est pas affichee.** A un jour sur sept, la barre
tombait de 561 a 72 cas et se lisait comme une chute de l'epidemie. Le dernier
point d'une courbe epidemique est toujours incomplet, et un point incomplet se
lit toujours comme une amelioration. Rien n'est cache : la vue « par jour »
montre ces journees a leur place, et la note le dit.

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

## La page « Riposte » (`/riposte/`, `/en/response/`, `/sw/mapambano/`)

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
  suivi des contacts), `spanGaps:false`.
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
`ReferenceError: WebSocket is not defined`.

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

- **Page « Mouvements de population » (prototype, mis de côté le 4 septembre
  2026 à la demande du propriétaire).** Tout est en local, non commité :
  `scripts/prototype_mobilite.py` écrit `tmp/mobilite/index.html` à partir de
  la coquille de `riposte/index.html` (barre latérale avec une entrée
  supplémentaire, fil d'Ariane, pied de page) et des transcriptions de
  `report_iom/analyse/` (hors dépôt, `report_iom/` ajouté au `.gitignore` le
  3 septembre — 192 Mo, dont 15 rapports de situation OIM multipays dans
  `report_iom/sitrep-oim/`, téléchargés par `scripts/telecharger_via_brave.mjs`
  parce que crisisresponse.iom.int et dtm.iom.int refusent curl et le
  headless ; le script ouvre une fenêtre Brave visible, `VISIBLE=1`, et
  `NAVIGUER=1` pour les liens `dtm_download_track`). La page : bandeau de
  période (15 mai – 28 août 2026, « ne se met pas à jour »), trois chiffres,
  un diagramme exhaustif origine → point de contrôle → destination (12, 7 et
  15 nœuds, 149 rubans) mesuré sur les tracés vectoriels de la figure 9 du
  tableau de bord OIM de la semaine 34 par `scripts/extraire_sankey_oim.py`
  (marges recoupées à moins d'un point, sortie `report_iom/analyse/
  sankey_fig9.json` ; la figure 10 se mesure pareil mais ses étiquettes sont
  éclatées lettre à lettre, non fait), survol d'un nœud = entrants et
  sortants ensemble, survol d'un ruban = la bande entière sur les deux
  tronçons, tout en CSS `:has()` généré (une règle par nœud et par ruban) ;
  tableau des sept points ; barres « que relient les trajets » ; déplacés
  (deux tuiles, un tableau) ; prose axes et frontière ; sources par famille,
  repliées. Décisions prises en route : titre « Mouvements de population »
  plutôt que « Mobilité » (proposé, appliqué au prototype, à confirmer), la
  figure des dix couloirs retirée au profit de la matrice, la tuile
  « trajets entre deux zones actives » retirée (l'indicateur OIM ne compte
  pas les trajets d'une zone active vers une zone indemne, qui sont pourtant
  le mécanisme d'extension), paragraphe de lecture retiré, palette de sept
  teintes validée en deutan. Piège d'unité : la figure 7 du rapport (dix
  couloirs) est en parts de TOUS les trajets, la figure 9 en parts des 3 639
  trajets renseignés — rapport constant 100/82, Bunia → Bunia 12,6 % contre
  15,3 %. Pour intégrer : passer par `site/pages.json` + `strings.json` +
  gabarit, traduire EN/SW, ajouter la liste OIM à `/rapports/`, écrire à
  dtmdrc@iom.int (classeur « destinations », accord sur la figure
  redessinée). Outil né du chantier : `scripts/verif/capture_survol.mjs`,
  capture d'une section pendant le survol d'un élément.

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

## Où chercher le reste

**Les messages de commit portent le raisonnement**, pas seulement le quoi. Ils
citent les passages de bulletin qui fondent chaque décision, gardent les
mesures qui ont tranché un choix de couleur ou de seuil, et consignent ce qui
a été écarté et pourquoi. `git log` est la mémoire longue de ce projet.

Les commentaires du code font le reste : ils expliquent systématiquement le
*pourquoi*, souvent avec la date et le numéro de bulletin qui ont révélé le
problème.
