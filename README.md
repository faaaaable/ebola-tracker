# ebola-tracker.org

An independent tracker of the **17th Ebola outbreak in the Democratic Republic of the
Congo** (Bundibugyo species, declared on 15 May 2026), based on official reports.

**Website: [ebola-tracker.org](https://ebola-tracker.org/en/)** · in French, English and Swahili

*[Version française](README.fr.md)*

---

## What the site does

- **Daily figures**: confirmed cases, deaths, recoveries and case fatality rate, by
  province and by health zone, with their trend since May 2026.
- **The response**: alerts, laboratory testing, contact tracing, treatment centres,
  vaccination, points of entry, and the challenges reported in each bulletin.
- **The Letter**: a plain-language summary of each bulletin, sent by email to
  subscribers.
- **The virus, the timeline, frequently asked questions**, and the follow-up of
  confirmed cases outside the DRC.

## Where the figures come from

**Every figure shown on the site can be traced to a document in [`reports/`](reports/).**
The site mirrors its sources; it is not a source itself. It does not correct a
published value, move a case from one province to another, or fill a gap by
interpolation. When a bulletin is silent, the site is silent too, and says so.

| Source | Content | In this repository |
|---|---|---|
| INSP (DRC National Institute of Public Health), Presidential Ebola Task Force | daily situation reports (SitReps) | [`reports/`](reports/), one PDF per bulletin |
| World Health Organization | situation reports | [`reports/who/`](reports/who/) |
| Ministries of health (Kenya, Uganda, Nigeria…) | statements on cases outside the DRC | cited on each page |

The method (how bulletins are read, checks, known limitations) is described on the
[Methodology](https://ebola-tracker.org/en/methodology/) page.

## The data

The full database, one record per day, per province and per health zone, can be
downloaded as CSV or JSON, in English or in French:

| | English | Français |
|---|---|---|
| CSV | [`data/ebola-drc-database.csv`](data/ebola-drc-database.csv) | [`data/base-ebola-rdc.csv`](data/base-ebola-rdc.csv) |
| JSON | [`data/ebola-drc-database.json`](data/ebola-drc-database.json) | [`data/base-ebola-rdc.json`](data/base-ebola-rdc.json) |
| Column dictionary | [`data/ebola-drc-database-dictionary.csv`](data/ebola-drc-database-dictionary.csv) | [`data/base-ebola-rdc-dictionnaire.csv`](data/base-ebola-rdc-dictionnaire.csv) |

Country, province and zone rows overlap: **filter on the `level` column before
adding up**. The dictionary gives each column's unit, whether the value is published
by the bulletin or computed, and its definition; it is also on the
[Database](https://ebola-tracker.org/en/database/) page. The other files in [`data/`](data/) are described in
[`data/README.md`](data/README.md).

## Licences

- **Data, texts, charts and maps**: [CC BY 4.0](LICENSE-DATA.md). You may reuse them,
  including for commercial purposes, provided you credit ebola-tracker.org.
- **Code** (scripts, templates, JavaScript): [MIT](LICENSE).
- **Documents by other authors** (INSP bulletins, WHO reports, official statements)
  remain under their own terms; they are archived here only so that figures can be
  checked.

To cite the project, GitHub offers a ready-made format ("Cite this repository",
based on [`CITATION.cff`](CITATION.cff)).

## Repository layout

The site is static and served by GitHub Pages from the `main` branch. The HTML pages
at the root (`index.html`, `riposte/`, `en/`, `sw/`…) are **generated**: they are
never edited by hand.

```
reports/         INSP bulletins (PDF) and WHO reports (reports/who/): the sources
data/            data extracted from the bulletins, and the published database
scripts/         PDF extraction, checks, page generation
scripts/archives one-off investigation scripts, not part of the update
site/            page templates, texts in three languages (strings.json)
assets/          stylesheets, JavaScript, fonts, images
.github/         automation (page generation, sending the Letter)
```

## Rebuilding the site

You need Python 3.9 or later and Node 20 or later.

```bash
pip install requests beautifulsoup4 pdfplumber pyshp

python scripts/download_all_sitreps.py   # fetches new bulletins
python scripts/update_data.py            # extracts cases, deaths, provinces, zones
python scripts/extract_contacts_followup.py
python scripts/extraire_alertes.py       # then the other response extractors
python scripts/build_pages.py            # generates every page
python scripts/check_coherence.py        # final check, changes nothing
```

`check_coherence.py` checks the sum of provinces against the national total, the
recomputed case fatality rate, the sum of zones against each province, and that
every cited PDF is present. Each bulletin is integrated by hand and checked against
its PDF: automatic synchronisation has been switched off on purpose since August
2026, because the bulletin format has changed several times.

Script names and code comments are in French.

To preview: `python -m http.server 8080`, then
[http://localhost:8080](http://localhost:8080).

## Author and contact

A project by **Pierre-Emmanuel Moingt**, carried out in a personal capacity, with no
advertising or commercial activity ([About](https://ebola-tracker.org/en/about/)).

contact [at] ebola-tracker.org, or the [contact form](https://ebola-tracker.org/en/contact/).
Error reports are welcome; please give the bulletin number. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).
