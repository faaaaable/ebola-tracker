# ebola-tracker.org — guide du dépôt

Site public de suivi de la **17ᵉ épidémie d'Ebola en RDC** (espèce Bundibugyo,
déclarée le 15 mai 2026). Il compile les bulletins officiels de l'INSP et les
rapports hebdomadaires de l'OMS. Bilingue FR/EN, statique, servi par GitHub
Pages sur `ebola-tracker.org` depuis la branche `main`.

Dernier bulletin intégré à la rédaction de ce guide : **SitRep 100**, rapportage
du 22 août 2026 — 5 514 cas confirmés, 2 642 décès, létalité 47,9 %.

---

## Le principe qui gouverne tout

**Chaque chiffre affiché doit être traçable jusqu'à un PDF de `reports/`.**

Le site est un miroir, pas une source. Il n'invente pas de valeur, ne
réattribue pas un cas d'une province à une autre, ne comble pas un trou par
interpolation. Quand la source ne dit pas, le site ne dit pas — et le dit.

Deux illustrations à connaître, parce qu'elles reviendront :

- Les **233 décès « à ventiler »** de l'Ituri ne sont répartis sur aucune zone.
  La somme des 28 zones donne 1 832 décès quand la province en déclare 2 065.
  L'écart reste visible plutôt que comblé.
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

Plus **Node 20+** dans le `PATH` : `build_pages.py` appelle
`scripts/dump_i18n.mjs` pour lire `assets/js/i18n.js`. Aucun paquet npm, pas de
`package.json`.

`pyshp` ne sert qu'à `build_geo.py`, qui ne tourne pas quotidiennement.

Chrome n'est nécessaire que pour `scripts/audit_mobile.mjs` et les captures.

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
seuls les adjectifs prennent la marque.

**Typographie.** Espace fine insécable (U+202F) comme séparateur des milliers.

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

**Les captures d'écran des graphiques sont instables** : ils s'animent au
chargement et se redessinent hors écran. Interroger le canevas
(`chart.options.animation = false; chart.update('none'); canvas.toDataURL()`)
plutôt que faire une copie d'écran de page.

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
  mi-juillet, 47,9 % au 22 août. Elle a triplé en trois mois.
- **Les moins de 5 ans** font 10,0 % des cas et **19,0 % des décès**. Les
  30-49 ans, tranche la plus touchée en volume, font 35,2 % des cas pour 27,2 %
  des décès.
- **Les femmes** représentent 52,9 % des cas mais 49,6 % des décès. L'excédent
  féminin se concentre sur les 18-29 ans (58,7 %).
- **Près de deux décès sur trois** surviennent hors des centres de traitement,
  et cette part **ne bouge pas** depuis six semaines — 61,6 % en moyenne, sans
  tendance décelable au-delà du bruit d'échantillonnage.
- **Les tranches d'âge sont inégales** (5, 13, 12, 20 ans, puis ouverte).
  Rapporté à une année d'âge, ce sont les 18-29 ans les plus touchés, devant
  les 0-4 ans — l'inverse de ce que suggèrent les barres brutes.

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
