# ebola-tracker.org

Suivi indépendant de la **17ᵉ épidémie d'Ebola en République démocratique du Congo**
(espèce Bundibugyo, déclarée le 15 mai 2026), d'après les bulletins officiels.

**Site : [ebola-tracker.org](https://ebola-tracker.org)** · en français, anglais et swahili

*[English version](README.md)*

---

## Ce que fait le site

- **Le bilan du jour** : cas confirmés, décès, guéris, létalité, par province et par
  zone de santé, avec leur évolution depuis mai 2026.
- **La riposte** : alertes, laboratoire, suivi des contacts, centres de traitement,
  vaccination, points de contrôle, et les difficultés signalées par les bulletins.
- **La Lettre** : un résumé en langage courant de chaque bulletin, envoyé par mail
  aux abonnés.
- **Le virus, la chronologie, les questions fréquentes**, et le suivi des cas
  confirmés hors de RDC.

## D'où viennent les chiffres

**Chaque chiffre affiché renvoie à un document de [`reports/`](reports/).** Le site est
un miroir des sources, pas une source : il ne corrige pas une valeur publiée, ne
déplace pas un cas d'une province à une autre et ne comble pas un trou par
interpolation. Quand un bulletin ne dit rien, le site ne dit rien, et le signale.

| Source | Contenu | Dans ce dépôt |
|---|---|---|
| INSP, Task Force présidentielle Ebola 17 | bulletins quotidiens (SitRep) | [`reports/`](reports/), un PDF par bulletin |
| Organisation mondiale de la santé | rapports de situation | [`reports/who/`](reports/who/) |
| Ministères de la santé (Kenya, Ouganda, Nigeria…) | communiqués sur les cas hors RDC | cités page par page |

La méthode (lecture des bulletins, contrôles, limites connues) est décrite sur la
page [Méthodologie](https://ebola-tracker.org/methodologie/).

## Les données

La base complète, un relevé par jour, par province et par zone de santé, se
télécharge en CSV ou en JSON, en français ou en anglais :

| | Français | English |
|---|---|---|
| CSV | [`data/base-ebola-rdc.csv`](data/base-ebola-rdc.csv) | [`data/ebola-drc-database.csv`](data/ebola-drc-database.csv) |
| JSON | [`data/base-ebola-rdc.json`](data/base-ebola-rdc.json) | [`data/ebola-drc-database.json`](data/ebola-drc-database.json) |

Le dictionnaire des colonnes est sur la page
[Base de données](https://ebola-tracker.org/base-de-donnees/). Les autres fichiers
de [`data/`](data/) sont décrits dans [`data/README.fr.md`](data/README.fr.md).

## Licences

- **Données, textes, graphiques et cartes** : [CC BY 4.0](LICENSE-DATA.md). Vous pouvez
  les reprendre, y compris à des fins commerciales, en citant ebola-tracker.org.
- **Code** (scripts, gabarits, JavaScript) : [MIT](LICENSE).
- **Documents d'autres auteurs** (bulletins de l'INSP, rapports de l'OMS, communiqués
  officiels) : ils restent soumis à leurs propres conditions et ne sont archivés ici
  que pour permettre la vérification.

Pour citer le projet, GitHub propose un format prêt à l'emploi (« Cite this
repository », d'après [`CITATION.cff`](CITATION.cff)).

## Organisation du dépôt

Le site est statique et servi par GitHub Pages depuis la branche `main`. Les pages
HTML de la racine (`index.html`, `riposte/`, `en/`, `sw/`…) sont **générées** : on
ne les modifie jamais à la main.

```
reports/         bulletins INSP (PDF) et rapports OMS (reports/who/) : les sources
data/            données extraites des bulletins, et la base publiée
scripts/         extraction des PDF, contrôles, génération des pages
site/            gabarits des pages, textes en trois langues (strings.json)
assets/          feuilles de style, JavaScript, polices, images
.github/         automatisations (génération, envoi de la Lettre)
```

## Reconstruire le site

Il faut Python 3.9 ou plus récent et Node 20 ou plus récent.

```bash
pip install requests beautifulsoup4 pdfplumber pyshp

python scripts/download_all_sitreps.py   # récupère les nouveaux bulletins
python scripts/update_data.py            # extrait cas, décès, provinces, zones
python scripts/extract_contacts_followup.py
python scripts/extraire_alertes.py       # puis les autres extracteurs de la riposte
python scripts/build_pages.py            # génère toutes les pages
python scripts/check_coherence.py        # contrôle final, ne modifie rien
```

`check_coherence.py` recoupe la somme des provinces avec le total national, la
létalité recalculée, la somme des zones avec chaque province et la présence de
chaque PDF cité. Chaque bulletin est intégré à la main et relu contre son PDF : la
synchronisation automatique est volontairement arrêtée depuis août 2026, le format
des bulletins ayant changé plusieurs fois.

Pour prévisualiser : `python -m http.server 8080`, puis
[http://localhost:8080](http://localhost:8080).

## Auteur et contact

Projet de **Pierre-Emmanuel Moingt**, mené à titre personnel, sans publicité ni activité
commerciale ([À propos](https://ebola-tracker.org/a-propos/)).

contact [at] ebola-tracker.org, ou le [formulaire du site](https://ebola-tracker.org/contact/).
Les signalements d'erreur sont bienvenus, avec le numéro du bulletin concerné. Voir
[`CONTRIBUTING.md`](CONTRIBUTING.md).
