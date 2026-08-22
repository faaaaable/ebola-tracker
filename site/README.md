# Sources du site

Le site n'est plus une page unique à onglets : c'est un ensemble de pages
générées, une par URL et par langue. Les fichiers HTML de la racine, de `/en/`
et de `/provinces/` sont **produits** — les modifier à la main ne sert à rien,
la prochaine génération les écrase.

## Générer

```bash
python scripts/build_pages.py
```

Il faut Python 3 et Node (Node sert uniquement à lire `assets/js/i18n.js`, qui
reste la source unique des libellés partagés avec le JavaScript).

## Prévisualiser en local

```bash
python -m http.server 8080
```

puis ouvrir <http://127.0.0.1:8080/>. Un simple double-clic sur un fichier
`index.html` ne suffit pas : les pages utilisent des chemins absolus
(`/assets/…`, `/data/…`), qui ont besoin d'un serveur.

## Où se trouve quoi

| Fichier | Rôle |
|---|---|
| `site/pages.json` | Structure du site : URL de chaque page dans chaque langue, titres, descriptions, navigation, données structurées |
| `site/strings.json` | Textes des pages qui n'existaient pas dans la monopage (le virus, chronologie, FAQ, provinces) + navigation et pied de page |
| `site/layout.html` | Squelette commun : `<head>`, en-tête, navigation, pied de page |
| `site/pages/*.html` | Contenu propre à chaque page |
| `assets/js/i18n.js` | Dictionnaire de traduction, partagé entre le navigateur et le générateur |
| `assets/js/app.js` | Toute la logique : indicateurs, carte, graphiques, tableaux, rapports |
| `assets/css/site.css` | Feuille de style commune |
| `site/.generated.json` | Liste des fichiers produits, utilisée pour supprimer les pages devenues obsolètes |

## Ajouter une page

1. Créer le fragment `site/pages/ma-page.html` (juste le contenu, pas le
   `<head>` ni la navigation).
2. Ajouter une entrée dans `site/pages.json` : `id`, `fragment`, `slug` pour
   `fr` et `en`, `navLabelKey`, `meta` (titre, h1, description) dans les deux
   langues.
3. Ajouter les textes dans `site/strings.json`, sous `fr` et sous `en`.
4. Pour la faire apparaître dans la navigation, ajouter son `id` à `mainNav` ou
   à `footerNav`.
5. Regénérer. La page entre automatiquement dans `sitemap.xml`.

## Écrire dans un fragment

| Jeton | Remplacé par |
|---|---|
| `{{i18n.cle}}` | Libellé du dictionnaire `assets/js/i18n.js` |
| `{{t.cle}}` | Texte de `site/strings.json` |
| `{{url.identifiant}}` | URL d'une autre page, dans la langue courante |
| `{{meta.h1}}` | Titre `h1` défini dans `pages.json` |
| `{{seed.…}}` | Chiffres du dernier bulletin, écrits en dur |
| `{{provinceCards}}`, `{{timelineItems}}`, `{{faqItems}}` | Blocs construits à partir des données |

Un jeton inconnu arrête la génération avec un message explicite : rien n'est
publié à moitié.

## Deux règles à garder en tête

**Les chemins sont absolus.** Une page vit dans un sous-répertoire
(`/provinces/ituri/`) : `data/latest.json` y pointerait vers
`/provinces/ituri/data/latest.json`. Tout chemin vers un fichier du dépôt
commence donc par `/`, et côté JavaScript passe par `assetUrl()`.

**Les chiffres sont écrits deux fois.** Le générateur les inscrit dans le HTML
pour qu'ils soient lisibles sans JavaScript — donc indexables — et `app.js` les
réécrit ensuite avec les données fraîches. Les fonctions `fmt()` et `fmt_cfr()`
de `build_pages.py` reproduisent volontairement le formatage du JavaScript pour
que rien ne saute à l'écran au moment du remplacement.
