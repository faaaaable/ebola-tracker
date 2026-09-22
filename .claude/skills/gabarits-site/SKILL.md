---
name: gabarits-site
description: La structure des pages d'ebola-tracker : l'en-tete a quatre couches, les quatre regles du corps, les deux graphies de titre, la colonne de titres section-split, le glossaire, les trois langues et leur generateur unique, les trois niveaux de texte (strings.json, i18n.js, gabarits) et la passe de coherence swahilie. A charger avant de toucher a un gabarit de site/pages/, a site/strings.json, a assets/js/i18n.js ou a la mise en page d'une page.
---

# La structure du site

**Un seul en-tête de page, en quatre couches, depuis le 5 septembre 2026.**
Le propriétaire avait relevé que chaque page commençait autrement — bille
ici, pas là ; chapeau en serif sur deux pages, en sans-serif sur sept ;
trois composants différents pour une bande de chiffres. Toutes les pages
hors accueil suivent désormais le même ordre, chaque couche pouvant
manquer mais jamais être remplacée par autre chose :

1. **Surtitre** (`.eyebrow`, capitales de 11 px, bille devant) : la rubrique
   de la barre latérale. « Données détaillées » avec la pastille d'identité
   sur les sept pages de données (couleur de la province, anneau vide pour
   le pays) ; sinon le groupe de la barre — `footerExploreTitle`
   (Riposte, Flux), `footerUnderstandTitle` (Chronologie, Le virus, FAQ),
   `footerSiteTitle` (Sources, À propos, Contact) — avec la bille bleue.
2. **Titre** `.page-title`, sans plafond de largeur (le `22ch` est parti,
   `page-title--large` n'existe plus).
3. **À droite du titre**, dans `.section-sub`, une seule formule pour les
   pages qui vivent des bulletins : `seed.cartoAsOf` (« Situation au
   3 sept. 2026 ») sur Données, provinces et Riposte ; « Période
   observée : … » (`fluxSub`) sur Flux. Rien sur Sources, Chronologie,
   Le virus, FAQ, À propos, Contact. Conséquence sur `/donnees/` : la ligne
   « 60 zones touchées · SitRep N°112 » (`#zonesTableSub`, réécrite par le
   script) est descendue à droite du titre « Par zone de santé », qu'elle
   décrit ; la province ne montre plus « SitRep N°112 du 3 sept. »
   (`seed.sitrepRef` reste calculé, inutilisé).
4. **Chapeau** `.lede` : serif de 22 px, une ou deux phrases, 35 mots au
   plus. Ce qui dépasse descend dans un `.page-intro` sans-serif juste
   dessous (`.lede+.page-intro` resserre l'écart). Les chapeaux de
   Données, Riposte, Flux et Sources ont été scindés en deux clés
   (`ddLede`/`provincesIntro`, `riposteLede`/`riposteIntro`,
   `fluxLede`/`fluxIntro`, `reportsLede`/`reportsPageIntro`) ; le chapeau
   de province est `provinceIntro` en serif, le rang en dessous en
   `page-intro`. `about-lede` a fusionné dans `lede`.

Puis, quand ils existent : la **bande de chiffres**, toujours `.kpis
riposte-kpis` (Le virus a quitté `figure-band`, qui ne sert plus qu'à la
bande des génomes plus bas ; À propos a quitté sa liste `about-facts`, ses
repères sont en valeur courte + détail : « INSP et OMS / bulletins
officiels », « 121 / 105 INSP, 16 OMS ») ; puis les **ancres**
`.riposte-ancres` dès trois chapitres (Sources en a reçu trois, sur des
`id` `insp`, `who-reports-section`, `autres`). Deux modificateurs de
`.kpi` : `figure` (chiffre de contexte, bleu fort) et `alert` (rouge).
Vérifié par planche des dix en-têtes à 1 280 px (`tmp/verif/
planche-tetes-apres.png`) et trois pages à 360 px ; `test_onglets` sans
erreur sur Données, Riposte et Sources.

**Le glossaire (`/glossaire/`, `/en/glossary/`, `/sw/kamusi/`) existe depuis
le 10 septembre 2026.** Quinze entrées (cas confirmé, probable, suspect,
alerte, contact, suivi des contacts, décès communautaire, CTE, guéri,
létalité, zone de santé, épicentre, Bundibugyo, enterrement digne et
sécurisé, SitRep), définies comme le site les emploie, dans
`glossaireItems` de `strings.json` (`t` et `d` par langue, rendues par
`glossaire_items_html`), fragment `glossaire.html`, styles `.gl-list`.
**Décision du propriétaire : la page n'est reliée que depuis la colonne
« Comprendre » du pied de page** (`footerNav`), après FAQ — ni colonne
latérale, ni section sur l'accueil. Les deux autres formes ont été
maquettées et écartées le même jour (section en bas de l'accueil, entrée
dans la colonne). En-tête à quatre couches comme les autres pages :
surtitre `footerUnderstandTitle`, titre, chapeau `glossaireLede`, rien à
droite du titre. Le swahili est à faire relire.

**Le corps des pages suit quatre règles depuis le même jour** (analyse
de la planche `tmp/verif/planche-corps.png`, avant/après), décidées après
un « tu conseilles quoi ? » :

1. **Une page en chapitres a sa colonne de titres.** Le critère est
   l'existence d'ancres : Données, Le virus, Riposte, Flux et Sources sont
   en `section-split` (nom du chapitre et ligne italique dans la marge de
   220 px, contenu à droite). Provinces, Chronologie, FAQ, À propos et
   Contact restent pleine largeur. **Sources est revenue en pleine largeur
   le 6 septembre** : ses chapitres sont des listes de documents, et la
   colonne ne laissait que deux bulletins par ligne contre trois — le
   propriétaire l'a vu parce que la section OMS tombait déjà sous son
   titre : `app.js` (`renderWhoReports`) pose `style.display = 'block'` sur
   `#who-reports-section` au chargement, ce qui annulait la grille de
   `section-split` sur cette seule section. Règle affinée : la colonne va aux chapitres qui portent une
   figure ou un texte, pas à une grille de documents. Coût assumé : les graphiques de Riposte
   ont perdu 250 px à 1 280 px et prennent la largeur de ceux de Données.
   Sur Sources, le premier chapitre a quitté la section d'en-tête pour
   devenir une section à part (`#insp`).
2. **Deux graphies de titre.** Le chapitre en capitales sans-serif
   (`.section-title`) ; le cadre ou l'intertitre de texte en serif de
   22 px (`.frame-title`), une seule taille partagée par sélecteur avec
   `.prose h2`, `.tl-title`, `.data-note h2` et `.faq-more h2`. Sur
   Données, « Nouveaux cas », « Par province »… sont donc en serif, ce qui
   les distingue enfin des chapitres « Combien », « Où ».
3. **Sous un chapitre** : la ligne italique, puis le paragraphe, dans cet
   ordre.
4. **Un cadre est titré au-dessus, jamais dedans** : les `figcaption` de
   Flux et du bloc des génomes sont devenus des `h3.frame-title` dans un
   `.section-head` avant le cadre, leur sous-titre `.mb-sub` une
   `.section-sub`. Une seule graphie de note sous les cadres : `.mb-credit`
   et `.vcompare-note` alignés sur `.map-note` (11,5 px, gris).

5. **Chaque page longue se termine par une sortie** « Pour aller plus loin »
   (`#plus-loin`, liste `.plus-loin`) : deux liens choisis par sens, chacun
   suivi d'une ligne sans chiffre. Riposte → Données, Le virus ; Le virus →
   Riposte, FAQ ; Chronologie → Données, Sources. Les autres pages avaient
   déjà leur sortie (Données « Que fait-on », provinces note de lecture,
   Sources « Autres sources », FAQ « Votre question n'est pas là ? ») et
   n'ont pas bougé. Clés `plusLoinTitle`, `*Loin1Link/Text`, `*Loin2Link/Text`.

`test_onglets` sans erreur sur les cinq pages en chapitres.


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

**Le swahili n'a toujours pas été relu par un locuteur.** Il couvre
l'intégralité du site — 507 chaînes de `strings.json`, celles d'`i18n.js` dont
les fonctions, la FAQ, les jalons de chronologie, les textes d'arrivée par
province, les slugs (`/sw/takwimu/`, `/sw/ripoti/`, `/sw/matukio/`) et les
`meta`. Ce qui est vérifié mécaniquement l'est : aucune variable `{n}` perdue
ni inventée, aucune clé manquante dans les trois blocs, aucune chaîne restée en
français. Ce qui ne l'est pas : la justesse des formulations sanitaires.
**`python -c` d'export : `tmp/relecture-swahili.txt` met les 655 chaînes
français/swahili côte à côte, prêtes à envoyer** (régénérable, `tmp/` n'est pas
versionné).

**Une passe de cohérence terminologique a été faite le 21 septembre 2026**,
après remarque du propriétaire (« le swahili est toujours tel quel ») : ce qui
ne demande pas d'être locuteur, c'est-à-dire l'emploi d'un même terme partout.
Quatre écarts corrigés.

- **« Contacts » se disait de quatre façons.** Le terme établi est
  **`walioguswa`** (sept emplois dans `i18n.js`, dont le titre de la section).
  Trois exceptions traînaient dans `strings.json` : `lettreKpiContacts` disait
  *waliowasiliana*, « ceux qui ont **communiqué** entre eux » — un faux ami en
  épidémiologie ; `provinceRiposteSub` disait *waliokutana na wagonjwa* ; et
  `riposteVaccinAussi` comme le lede de la vaccination disaient *waliogusana na
  wagonjwa*, ajoutés la veille.
- **Le lexique définissait un mot que le site n'emploie pas** : l'entrée
  « zone de santé » s'intitulait *Kanda ya afya*, quand le site écrit *eneo la
  afya* vingt-quatre fois. Le lecteur cherchait la définition d'un terme sous un
  autre nom.
- `vaccChartUnite`, chaîne morte dans les trois langues depuis la
  simplification de l'infobulle, est supprimée.

Ce qui a été vérifié et laissé tel quel : les alternances *wamechanjwa* /
*waliochanjwa* et *wamelazwa* / *waliolazwa* suivent la construction — forme
relative pour les libellés, forme de phrase pour les phrases. Ce n'est pas du
désordre, ne pas « harmoniser » sans locuteur.

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
