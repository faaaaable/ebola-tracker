---
name: corpus-gele
description: "Le corpus gele d'ebola-tracker (data/corpus/, hors depot) : reconstruction en sept scripts, les quatre epoques editoriales A-D, extraire_cellules et la couverture des indicateurs, extraire_qualitatif (sections Defis), prototype_riposte. A ouvrir avant toute recherche dans les anciens bulletins."
---

# Le corpus gele — la couche de recherche

Sorti de CLAUDE.md le 11 octobre 2026 (chargement a la demande).

`data/corpus/` (78 Mo, hors dépôt) est un **intermédiaire complet des 106
rapports**, construit pour ne plus jamais rouvrir un PDF pendant une analyse.
Il ne sert pas le site : il sert à décider ce que le site devrait montrer.

Reconstruction, dans cet ordre :

```bash
python scripts/geler_corpus.py         # manifeste.json + textes/ — gèle les 106 rapports
python scripts/cartographier_corpus.py # carte.json — époques éditoriales, sections
python scripts/recenser_corpus.py      # recensement-prose.json + recensement-tableaux.json
python scripts/extraire_cellules.py    # cellules.jsonl — aplatit 602 types de tableaux
python scripts/catalogue_corpus.py     # catalogue.json — fusion chiffrée avec couverture
python scripts/extraire_qualitatif.py  # qualitatif.jsonl — les sections « Défis »
python scripts/demographie_figures.py  # demographie.jsonl -> data/demographie.json
```

**Seul `geler_corpus.py` est long** — 102 s pour les 106 PDF, mesure du 24 août.
Les six suivants travaillent sur l'intermédiaire gelé et rendent la main en
quelques secondes : c'est tout l'intérêt du gel. Une reconstruction complète
coûte donc environ deux minutes, pas une demi-heure. `manifeste.json` porte le
SHA-256 de chaque PDF, son nombre de pages et de tableaux.

**Quatre époques éditoriales**, identifiées par `cartographier_corpus.py` :

| Époque | Rapports | Bulletins |
|---|---|---|
| A | 15 | 001 → 016 |
| B | 39 | 017 → 058 |
| C | 22 | 059 → 083 |
| D | 17 | 084 → 100 |
| OMS | 13 | rapports hebdomadaires |

C'est cette carte qui permet de répondre « depuis quand cette colonne
existe-t-elle ? » sans rouvrir cent PDF. Exemple : les quatre colonnes du lieu
du décès n'apparaissent qu'à l'époque C — d'où la fenêtre bornée au 13 juillet,
que rien ne pourra faire remonter.

**`extraire_cellules.py` mérite d'être compris.** Plutôt qu'un parseur par type
de tableau — il y en a 602 —, il applique le même traitement à tous et produit
des cellules nommées. `catalogue_corpus.py` les fusionne ensuite avec les
nombres de la prose et calcule la **couverture** de chaque indicateur : sur
combien de rapports il existe. C'est ce qui a permis de dire que 50 cellules
seulement, sur 17 313 cataloguées, portent la distinction communauté / CTE.

**`extraire_qualitatif.py`** est le seul à s'intéresser au non-chiffré : les
sections « Défis » des bulletins, unique source du corpus sur les **causes** de
persistance de l'épidémie. Rien du site ne l'exploite encore.

**`prototype_riposte.py`** écrit une page autonome dans `tmp/riposte/`, sans
toucher aux sources du site. Modèle à suivre pour prototyper une page nouvelle.
