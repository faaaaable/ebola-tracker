# Contributing

*[Version française plus bas](#contribuer)*

## Reporting an error

Most useful: the **bulletin (SitRep) number**, the page on the site, the figure shown
and the figure you read in the PDF. Open an *issue* or write to
contact [at] ebola-tracker.org.

The site copies the official bulletins without correcting them. If the discrepancy
comes from the bulletin itself (two tables that do not match, for instance), the site
keeps the published value and points it out.

## Suggesting a change

The HTML pages at the root, in `en/` and in `sw/` are **generated** by
`scripts/build_pages.py`: a change goes into `site/` (templates and texts),
`scripts/` or `assets/`, and the pages are then rebuilt. Before suggesting a change
to the data or to the extraction, run `python scripts/check_coherence.py`, which must
finish with no blocking discrepancy.

---

# Contribuer

## Signaler une erreur

Le plus utile : le **numéro du bulletin** (SitRep) concerné, la page du site, la
valeur affichée et celle que vous lisez dans le PDF. Ouvrez une *issue* ou écrivez à
contact [at] ebola-tracker.org.

Le site recopie les bulletins officiels sans les corriger. Si l'écart vient du
bulletin lui-même (deux tableaux qui ne concordent pas, par exemple), le site garde
la valeur publiée et le signale.

## Proposer une modification

Les pages HTML de la racine, de `en/` et de `sw/` sont **générées** par
`scripts/build_pages.py` : une modification porte sur `site/` (gabarits et textes),
`scripts/` ou `assets/`, puis on régénère. Avant de proposer un changement de
données ou d'extraction, lancez `python scripts/check_coherence.py`, qui doit finir
sans écart bloquant.
