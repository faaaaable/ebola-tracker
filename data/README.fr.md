# Les données

*[English version](README.md)*

Tout ce dossier est produit à partir des bulletins archivés dans [`../reports/`](../reports/),
sauf mention contraire ci-dessous. Licence : [CC BY 4.0](../LICENSE-DATA.md).

**Pour réutiliser les chiffres, partez de la base** : elle réunit tout le reste en
un seul tableau, avec son dictionnaire des colonnes. Les lignes du pays, des provinces
et des zones se recouvrent : filtrer sur la colonne `niveau` avant d'additionner.

## La base

| Fichier | Contenu |
|---|---|
| `base-ebola-rdc.csv`, `base-ebola-rdc.json` | la base en français : un relevé par jour et par niveau (pays, province, zone de santé), épidémie et riposte |
| `ebola-drc-database.csv`, `ebola-drc-database.json` | la même base, colonnes et valeurs en anglais |
| `base-ebola-rdc-dictionnaire.csv`, `ebola-drc-database-dictionary.csv` | le dictionnaire des colonnes : unité, valeur publiée ou calculée, définition |

Le CSV est le format le plus léger. Le JSON donne chaque ligne avec le nom de ses
champs (une case vide y vaut `null`), et le dictionnaire dans son en-tête (`meta`).

## L'épidémie

| Fichier | Contenu |
|---|---|
| `latest.json` | le dernier bulletin : bilan national, provinces, zones de santé |
| `sitreps.json` | le bilan national, bulletin par bulletin |
| `province-history.json` | cas et décès par province, jour par jour |
| `zones-history.json` | cas et décès par zone de santé, jour par jour |
| `deces-lieu.json`, `deces-lieu-zones.json` | décès en communauté ou en centre de traitement, par province et par zone |
| `demographie.json` | répartition des cas et des décès par âge et par sexe (dernière figure publiée) |
| `jours-calcules.json` | journées sans bulletin, reconstituées par différence entre deux bulletins |
| `harmonisations.json` | corrections de séries annoncées par les bulletins eux-mêmes |

## La riposte

| Fichier | Contenu |
|---|---|
| `alertes.json` | alertes reçues, vérifiées et validées, par province |
| `laboratoire.json` | échantillons analysés, résultats positifs, positivité |
| `contacts-followup.json` | taux de suivi des contacts |
| `cte.json` | centres de traitement : patients isolés, admissions, sorties, lits |
| `piliers.json` | vaccination, enterrements sécurisés, ceintures de prévention, voyageurs contrôlés |
| `points-controle.json` | indicateurs des points d'entrée et de contrôle, par province |
| `defis.json`, `defis-anciens.json`, `defis-complements.json` | les difficultés citées par les bulletins, texte intégral |
| `defis-codage.json`, `defis-synthese.json` | leur classement en dix obstacles, et la synthèse rédigée de la page Défis |

## Les cartes

| Fichier | Contenu |
|---|---|
| `health-zones.geojson` | contours des zones de santé de la RDC (source : OCHA, via HDX) |
| `zones-supplementaires.geojson` | zones absentes du fond OCHA, tracées d'après OpenStreetMap |

## Sources extérieures aux bulletins de l'INSP

Ces fichiers ne viennent pas des bulletins ; chacun nomme sa source dans son en-tête.

| Fichier | Source |
|---|---|
| `who-reports.json` | rapports de situation de l'OMS (`../reports/who/`) |
| `hors-rdc.json`, `autres-pays.json`, `parcours-kenya.json`, `parcours-nigeria.json` | communiqués des ministères de la santé et de l'OMS sur les cas hors RDC |
| `epidemies-ebola.json` | épidémies d'Ebola antérieures, d'après le CDC (*History of Ebola Disease Outbreaks*) |
| `genomes.json` | nombre de génomes déposés dans Pathoplexus (agrégats seulement) |

## Fichiers de fonctionnement du site

`bulletin-notes.json` et `lettres/` (textes de la Lettre), `envois-*.json`,
`envoi-test.json` et `mail-accueil.json` (envoi des mails), `actus.json`,
`social-updates.json` et `community-deaths-daily.json` (fonctions retirées, gardées
pour l'historique), `diagnostic_report.json` (contrôle d'extraction), `base-page.json`
(la base sous une forme compacte, lue par la page Base de données).
