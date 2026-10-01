---
name: gabarits-site
description: "La structure des pages d'ebola-tracker : l'en-tete a quatre couches, les quatre regles du corps, les deux graphies de titre, la colonne de titres section-split, le glossaire, les trois langues et leur generateur unique, les trois niveaux de texte (strings.json, i18n.js, gabarits) et la passe de coherence swahilie. A charger avant de toucher a un gabarit de site/pages/, a site/strings.json, a assets/js/i18n.js ou a la mise en page d'une page."
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

---

## Historique de la page `/donnees/`

*Déplacé depuis `CLAUDE.md` le 29 septembre 2026 (allègement du guide), texte inchangé.*

Huit pages, chacune en FR et EN : accueil, `donnees/` (+ sept pages province depuis le 119),
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

## Nom du site dans Google, compte X, alerte Telegram, rangée des provinces

*Déplacé depuis `CLAUDE.md` le 29 septembre 2026 (allègement du guide), texte inchangé.*

### Le nom du site dans Google

Google affiche un **nom de site** au-dessus de l'adresse dans ses résultats,
lu dans `WebSite.name` des données structurées de la page d'accueil et dans
`og:site_name`. Il veut une valeur unique et stable ; trois noms selon la
langue (« Suivi Ebola RDC », « DRC Ebola Tracker », « Ufuatiliaji… ») le
faisaient retomber sur le domaine — l'adresse s'affichait deux fois.
Depuis le 8 septembre 2026, `site.brandName` (« Ebola Tracker ») alimente
`WebSite.name`, `isPartOf` des articles et `og:site_name` sur toutes les
pages ; les noms traduits et le domaine sont en `alternateName`. La marque
de la barre latérale (« ebola-tracker.org ») et les titres de page ne
changent pas. Google met des jours à des semaines à reprendre un nom de
site ; demander l'inspection de l'accueil dans la Search Console accélère.

---

### Le compte X du site

`site.xProfile` dans `site/pages.json` (« EbolaTrackerRDC », sans le @,
renseigné le 8 septembre 2026) alimente trois emplacements : « Suivre
sur X » en dernière entrée de la colonne « Le site » du pied de page,
un chapitre « Suivre le site » sur À propos, une ligne sous le formulaire
de Contact — trois langues, icône X en trait (`X_ICONE`), lien `rel="me"`.
Tout passe par `lien_x()` dans `build_pages.py` : **champ vide, rien n'est
rendu**, jamais de lien mort. Les balises `twitter:` du gabarit ne
désignent pas ce compte (choix du propriétaire, points 1 et 3 d'une liste
de quatre écartés le 8 septembre : la carte de partage et la barre
latérale).

---

### L'alerte Telegram (22 septembre 2026)

Demande du propriétaire : « que les visiteurs puissent recevoir une
notification quand j'ajoute la mise à jour d'un nouveau SitRep ».

**LE FLUX RSS A ÉTÉ RETIRÉ DU SITE LE 23 SEPTEMBRE 2026.** Plus de
`/feed.xml`, `/en/feed.xml` ni `/sw/feed.xml`, plus de `<link
rel="alternate">` dans le gabarit, plus de lien au pied de page, plus
d'étape de régénération dans le workflow. `remove_stale` a effacé les
trois fichiers de lui-même dès qu'ils ont quitté le manifeste, et la clé
`footerFollowRss` est partie avec eux.

**MAIS `scripts/build_feeds.py` RESTE, ET IL NE FAUT PAS LE SUPPRIMER.**
`notifier_telegram.py` lui emprunte `annonce()`, `contexte()`,
`_lettres()` et `_resume()` : le module est devenu une bibliothèque de
composition de message, il n'est simplement plus exécuté comme script.
Les clés `feedTitle`, `feedDescription` et `feedItemTitle` de
`strings.json` restent pour la même raison — c'est le texte de l'annonce
Telegram. Sa fonction `build()` n'a plus d'appelant ; elle est laissée en
place pour que le flux puisse revenir sans être réécrit.

**Ce que dit une lettre vit à un seul endroit.** `build_feeds.annonce()`
rend titre, adresse, chiffres de tête et résumé — c'est ce que Telegram
envoie.

**Ce qu'on dit d'une lettre vit à un seul endroit.** `build_feeds.annonce()`
rend titre, adresse, chiffres de tête et résumé ; le flux et Telegram y
passent tous les deux.

**Le point d'entrée du visiteur** est la colonne « Le site » du pied de
page, sous « Suivre sur X » : « Canal Telegram » seul depuis le retrait du
flux. Ce dernier passe par `lien_telegram()` et
`site.telegram` dans `pages.json` — **vide tant que le canal n'est pas
ouvert, et alors rien n'est rendu**, exactement comme `xProfile` avant le
8 septembre. Ouvrir le canal, c'est renseigner ce champ et poser les
secrets ; aucun code à toucher.

**Telegram** : `scripts/notifier_telegram.py`, un canal public par langue,
appelé par `.github/workflows/flux-et-alertes.yml` quand `data/lettres/**`
ou `data/bulletin-notes.json` arrive sur `main`. Secrets
`TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID_FR` / `_EN` / `_SW` ; **une
langue sans canal est sautée**, on peut n'ouvrir que le français. Le dépôt
ne garde aucune adresse ni aucune donnée d'abonné — c'est Telegram qui
tient la liste. Deux garde-fous : `data/notifie.json` retient les numéros
déjà annoncés (une reprise du workflow ne renvoie pas la même lettre), et
**l'annonce attend le résumé des Défis** ; sans lui le message se
réduirait à trois chiffres, et le commit qui l'apporte relance le
workflow. `--essai` montre les messages sans rien envoyer.

**Écarté.** WhatsApp : la Cloud API demande un Business Manager vérifié, un
numéro dédié et des modèles approuvés un par un, pour une facturation au
message ; les Canaux WhatsApp sont gratuits mais n'ont pas d'API — une
publication à la main. Le courriel viendra du flux (Brevo, Buttondown)
plutôt que d'un formulaire maison : collecter des adresses, c'est un
double opt-in, un désabonnement, SPF/DKIM/DMARC sur le domaine et une
base à tenir.

---

### La rangée des provinces, en bas de l'accueil

**Les six vignettes sont devenues sept colonnes coiffées d'un filet**
(22 septembre 2026). C'étaient des boîtes à bordure gauche colorée portant
trois paires libellé/valeur en capitales — cas, décès, létalité. Reproche du
propriétaire : « ça fait beaucoup trop IA », le même qu'à la police des
chiffres du panneau de la carte le 10 septembre. La règle du 27 août « moins
de boîtes, plus de traits » les avait explicitement épargnées ; un mois plus
tard elles étaient le dernier endroit de l'accueil à porter une boîte.

Ne restent que **le filet, le nom, le chiffre, les décès**. `province_col` /
`.pcol-*` remplacent `.province-card` / `.pc-stat`.

- **LE FILET PORTE L'IDENTITÉ, LE TEXTE GARDE L'ENCRE.** La teinte arrive par
  `--teinte`, posée par le générateur depuis `PROVINCE_COLORS`. Écrire le nom
  dans la couleur de sa province était la première idée : l'ambre du Nord-Kivu
  tombe à **3,9 de contraste** sur son fond quand le site s'impose 4,5. C'est
  déjà la règle ailleurs — le chiffre porte l'encre, le trait à côté porte la
  province.
- **La létalité est tombée avec les libellés.** À cet endroit la question est
  où est l'épidémie, pas comment elle tue ; elle reste sur chaque page
  province. Décision du propriétaire.
- **Le compte de décès s'écrit en toutes lettres** sous le chiffre des cas,
  clé `provincesCardDeathsInline` : plus aucun libellé en capitales, c'est le
  mot qui porte l'unité. L'anglais accorde (`{n} death{n?s}` — « 1 death » au
  Sud-Kivu), le swahili place le nom devant le nombre (« vifo 850 »).
- **LE TEXTE GROSSIT AU SURVOL PAR `transform`, JAMAIS PAR `font-size`.**
  Agrandir la police relance la mise en page : la colonne survolée gagne trois
  pixels de haut et toute la rangée s'allonge. Mesuré après coup : la grille
  fait 102,06 px au repos **comme au survol**. Même principe pour le filet, qui
  passe de 2 à 5 px en reprenant l'épaisseur sur le padding.
- **La règle mobile `.pc-stat` a disparu**, avec le côte à côte libellé/valeur
  qu'elle rattrapait. La colonne empile par construction et encaisse un chiffre
  plus long — le cumul franchira 10 000 vers le 13 octobre 2026, ce qui cassait
  l'ancienne mise en page à 375 px. Deux colonnes dès 320 px, vérifié.

**Dix variantes montrées en local avant celle-ci**, en trois planches
(`tmp/propositions-provinces*.html`, gitignoré). Écartées : la liste-relevé à
filets horizontaux, la liste à jauges, le classement avec part du pays, le
relevé à sparklines (sous dix cas la courbe ne dit plus rien), les colonnes à
deux chiffres côte à côte, le carré à fond uni, le carré teinté à 9 % et le
carré teinté par paliers de la carte — celui-ci doublait le cartogramme du haut
de page et mettait l'Ituri et le Nord-Kivu dans la même teinte à un facteur
quatre d'écart.

**LA RÉSERVE QUI RESTE, ET QUI VAUT D'ÊTRE RELUE AVANT D'Y REVENIR : la
hiérarchie n'est pas encodée.** L'Ituri (5 913) et le Sud-Ubangi (1) occupent
la même largeur, la même taille de chiffre, le même poids — la forme dit « sept
provinces comparables » quand une seule fait 77 % des cas. C'est exactement ce
que la grille de cartes ratait, et la rangée le garde. La variante A3 du
troisième jeu le réglait pour le prix d'un filet à deux couleurs (partie
colorée = part des cas). Montrée, non retenue ce jour-là.

---

## Trois retouches du 6 septembre 2026

*Déplacé depuis `CLAUDE.md` le 29 septembre 2026 (allègement du guide), texte inchangé.*

- **La démographie dit qu'elle est figée dans son cadre** : à droite du titre
  « Âge et sexe », `seed.agesFrozen` (« figée au 5 août 2026 : l'INSP ne
  publie plus cette répartition »), calculé depuis `demographie.json`.
- **Le virus, vaccins** : un paragraphe sobre après le tableau
  (`virusVaccinUpdate`), écrit d'après les orientations provisoires de l'OMS
  du 31 août 2026 lues sur IRIS (efficacité d'Ervebo contre Bundibugyo
  inconnue, usage réservé à un cadre de recherche, priorité aux soignants et
  au personnel de première ligne) et le SitRep 112 (vaccinations de ce
  personnel). Aucun chiffre en dur, volontairement : « nous ne sommes pas
  spécialistes ». Le « 0 vaccin homologué » reste vrai.
- Un filtre par type de jalon sur la légende de la chronologie a été
  construit, montré, puis **écarté par le propriétaire** le 6 septembre :
  ne pas le refaire sans qu'il le redemande.
- **L'historique des zones n'est chargé que là où il sert** : curseur des
  cartes et tableaux de zones (`besoinHistorique` dans l'init). Mesure
  faite avant : GitHub Pages compresse, `zones-history.json` fait 15 Ko
  sur le réseau pour 438 Ko sur disque, `app.js` 79 Ko pour 260 — le poids
  réel d'une page est dans le script, la feuille de style et Chart.js, pas
  dans les données. Le gain de cette retouche est donc modeste.
