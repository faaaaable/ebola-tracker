---
name: tableaux
description: Les tableaux d'ebola-tracker : la vue par province et la vue par zone de sante de /donnees/, les badges de letalite, la largeur des tableaux et les trois pieges de calage rencontres, les fausses pistes deja ecartees, les pages province et leurs cadres numerotes, la frise de province et la page /rapports/. A charger avant de toucher a un tableau, a province_zones_table_html ou a renderZonesTable.
---

# Les tableaux détaillés

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

**Cadres numérotés, depuis le 8 septembre 2026.** À la demande du propriétaire
(« ça structure le visuel »), la page Données et les pages province
reprennent l'idiome de Riposte & défis : `section.cadre-fiche` avec
`.fiche-tete` (numéro serif `.fiche-num`, `.frame-title`, `.section-sub`)
puis `.cadre-corps`. Données : 01 Combien, 02 Où, 03 Qui, 04 Que fait-on
(les anciens `.section-split` à deux colonnes ont disparu). Province : 01
carte, 02 zones, 03 courbe quand elle existe (seuil
`SEUIL_COURBE_PROVINCE`), puis la frise — 04, ou 03 sans courbe ; le
numéro se passe à `province_chart_html()` et `province_timeline_html()`.
La note « Comment lire ces chiffres » reste hors numérotation.

**La frise des pages province, depuis le 8 septembre 2026.** Le propriétaire
avait d'abord fait construire quatre blocs (riposte de la province, lieu du
décès, obstacles cités, chronologie verticale des zones), puis les a fait
retirer le jour même au profit d'une seule chose : **la piste horizontale
de l'accueil**, mêmes classes `.timeline-h.is-inline` / `.th-track` /
`.th-item.is-*`, mêmes flèches (`id="timelineTeaser"`, celui que
`initTimelineScroller` attend, absent ailleurs d'une page province), même
légende `.tl-legend`, mêmes couleurs — bleu jalon officiel, ambre extension
géographique, rouge seuil franchi, vert dernier bilan. Rendue par
`province_timeline_html()` via `common_seed["provinceTimelines"]` et le
jeton `province.timeline`. Les jalons : l'arrivée de l'épidémie
(`provinceArrivals`, dates dans la prose ; « Le foyer de l'épidémie » pour
l'Ituri), les seuils de cas et de décès, les paliers de zones touchées, le
dernier bilan. **Les seuils s'adaptent à la province** : `pas_arrondi()`
choisit un pas 1, 2 ou 5 fois une puissance de dix pour obtenir environ six
jalons quel que soit le maximum — 1 000 cas en Ituri, 200 au Nord-Kivu, 50
au Haut-Uélé, 5 dans la Tshopo, 1 au Sud-Kivu ; cinq paliers pour les
zones. Les zones gardent l'identité de `zone_milestone_events` (alias des
tracés, deux lettres près dans la province). Textes `provinceTimeline*`
dans `strings.json`, trois langues.

`province_zones_table_html()` produit un tableau statique des zones touchées de
la province, trié par cas décroissants. Les variations de 24 h ont **leur
propre colonne** depuis le 26 août : entre parenthèses, accolées au cumul,
elles empêchaient d'aligner les chiffres et se lisaient comme une note. Six
colonnes, dans l'ordre du tableau de `/donnees/`.
Suivi d'un lien vers le tableau complet filtré sur cette province.

### `/rapports/`

Le titre « Sources et bulletins officiels » (30 caractères) tient sur une
ligne depuis le 5 septembre 2026 : `.page-title` plafonne à 22ch, et cette
page seule porte `page-title--large` (`max-width:none`) — sans `nowrap`, le
titre se replie encore de lui-même sous 360 px. Les autres titres gardent
le plafond.

Un paragraphe d'introduction (`reportsPageIntro`, trois langues, classe
`page-intro` sous le titre) dit ce que la page est — le site ne produit
aucun chiffre, il compile ceux des institutions qui suivent l'épidémie, et
cette page en rassemble les documents tels que publiés, pour remonter à
l'original. Volontairement **général, sans nommer les sources** : une
première version les énumérait, le propriétaire l'a fait retirer le
5 septembre 2026 (« un paragraphe plus général sans préciser les
sources »). Les trois sections sont **numérotées** dans `i18n.js` —
« 1. SitRep quotidien (INSP) », « 2. Weekly External Situation Report
(OMS) », « 3. Autres sources » (ex-« Fond de carte », qui ne contient
encore que la provenance des contours) — ; le numéro fait partie de la
chaîne, il apparaît donc aussi dans l'`aria-label` du filtre par mois. Le
swahili n'est pas relu.

**Rapports OMS : 16 archivés, jusqu'au n°16 (données au 30 août 2026),
ajouté le 5 septembre.** Le propriétaire avait transmis un lien IRIS qui
était en fait le bitstream du n°12, déjà archivé (SHA-256 identique) ;
le n°16 a été retrouvé par l'API IRIS (`/discover/search/objects`, puis
`/core/items/<uuid>/bundles` → ORIGINAL → bitstreams), première page
vérifiée. La liste `WHO_REPORTS` de `download_who_sitreps.py` reste la
source de vérité ; `build_who_reports_index.py` reconstruit
`who-reports.json` depuis les noms de fichiers.

`report_chip()` produit une carte par bulletin, **cliquable dans son entier** —
auparavant seule la petite icône était un lien, cible minuscule et carte qui
paraissait inerte. Une navigation par mois et une recherche filtrent la liste
côté client. Les rapports OMS ont leur propre liste.

---
