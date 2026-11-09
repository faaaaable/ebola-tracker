# The data

*[Version française](README.fr.md)*

Everything in this folder is produced from the bulletins archived in
[`../reports/`](../reports/), unless stated otherwise below. Licence:
[CC BY 4.0](../LICENSE-DATA.md).

**To reuse the figures, start from the database**: it brings everything else together
in a single table, with a column dictionary on the
[Database](https://ebola-tracker.org/en/database/) page.

File names are in French; the English database has English column names and values.

## The database

| File | Content |
|---|---|
| `ebola-drc-database.csv`, `ebola-drc-database.json` | the database in English: one record per day and per level (country, province, health zone), outbreak and response |
| `base-ebola-rdc.csv`, `base-ebola-rdc.json` | the same database, with French column names and values |

## The outbreak

| File | Content |
|---|---|
| `latest.json` | the latest bulletin: national totals, provinces, health zones |
| `sitreps.json` | national totals, bulletin by bulletin |
| `province-history.json` | cases and deaths by province, day by day |
| `zones-history.json` | cases and deaths by health zone, day by day |
| `deces-lieu.json`, `deces-lieu-zones.json` | deaths in the community or in a treatment centre, by province and by zone |
| `demographie.json` | cases and deaths by age and sex (latest published figure) |
| `jours-calcules.json` | days without a bulletin, reconstructed as the difference between two bulletins |
| `harmonisations.json` | series corrections announced by the bulletins themselves |

## The response

| File | Content |
|---|---|
| `alertes.json` | alerts received, investigated and validated, by province |
| `laboratoire.json` | samples tested, positive results, positivity rate |
| `contacts-followup.json` | contact follow-up rate |
| `cte.json` | treatment centres: patients in isolation, admissions, discharges, beds |
| `piliers.json` | vaccination, safe burials, ring prevention, travellers screened |
| `points-controle.json` | points of entry and control indicators, by province |
| `defis.json`, `defis-anciens.json`, `defis-complements.json` | the challenges reported by the bulletins, full text |
| `defis-codage.json`, `defis-synthese.json` | their classification into ten obstacles, and the written summary on the Challenges page |

## Maps

| File | Content |
|---|---|
| `health-zones.geojson` | DRC health zone boundaries (source: OCHA, via HDX) |
| `zones-supplementaires.geojson` | zones missing from the OCHA layer, traced from OpenStreetMap |

## Sources other than INSP bulletins

These files do not come from the bulletins; each one names its source in its header.

| File | Source |
|---|---|
| `who-reports.json` | WHO situation reports (`../reports/who/`) |
| `hors-rdc.json`, `autres-pays.json`, `parcours-kenya.json`, `parcours-nigeria.json` | statements by ministries of health and WHO on cases outside the DRC |
| `epidemies-ebola.json` | previous Ebola outbreaks, from the CDC (*History of Ebola Disease Outbreaks*) |
| `genomes.json` | number of genomes deposited in Pathoplexus (aggregates only) |

## Files used to run the site

`bulletin-notes.json` and `lettres/` (texts of the Letter), `envois-*.json`,
`envoi-test.json` and `mail-accueil.json` (email sending), `actus.json`,
`social-updates.json` and `community-deaths-daily.json` (retired features, kept for
the record), `diagnostic_report.json` (extraction check).
