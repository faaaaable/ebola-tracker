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

---

*To report an error, please give the SitRep number, the page, and the figure shown
versus the figure in the PDF. HTML pages are generated: edit `site/`, `scripts/` or
`assets/`, then rebuild.*
