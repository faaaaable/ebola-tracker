# Outils de vérification visuelle

Neuf scripts Node qui pilotent Chrome en mode « headless » par le protocole
DevTools, pour contrôler le site rendu plutôt que son code source. Écrits le
24 août 2026 au fil des corrections de cette journée.

Ils ne font partie d'aucun pipeline. On les lance à la main, contre un serveur
local ou contre la production.

## Prérequis

Chrome installé à `C:/Program Files/Google/Chrome/Application/chrome.exe` —
le chemin est en dur en tête de chaque fichier, à adapter sur une autre
machine. Node 20+. Aucun paquet npm.

Pour le local, servir le site d'abord :

```bash
python -m http.server 8899 --bind 127.0.0.1
```

## Les cinq utiles

### `capture_canvas.mjs` — capturer un graphique, de façon fiable

```bash
node scripts/verif/capture_canvas.mjs <url> <sortie.png> [largeur] [data-mode]
```

**À préférer systématiquement pour les graphiques.** Il fige l'animation
(`chart.options.animation = false; chart.update('none')`) puis récupère
l'image du canevas lui-même par `toDataURL`.

Une capture d'écran de page ordinaire ne marche pas sur ces graphiques : ils
s'animent au chargement et se redessinent quand `captureBeyondViewport`
déclenche un recalcul, si bien qu'on attrape un tracé à moitié dessiné, ou un
canevas vide. Les deux cas se sont produits.

Le quatrième argument clique un sous-onglet avant de capturer.

### `capture_page.mjs` — capturer une section de page

```bash
node scripts/verif/capture_page.mjs <url> <sortie.png> <sélecteur> [largeur] [échelle]
```

Pour tout ce qui n'est pas un canevas : cartes SVG, tableaux, en-tête. Cadre
sur le sélecteur donné. L'échelle 1 plutôt que 2 quand l'image doit rester
légère — au-delà de 2 Mo, l'envoi échoue.

### `sonde_graph.mjs` — lire la configuration réelle d'un graphique

```bash
node scripts/verif/sonde_graph.mjs <url>
```

Renvoie le type, les axes, et pour chaque série son libellé, sa couleur, sa
dernière valeur. Sert à vérifier qu'une couleur est bien celle qu'on croit, ou
qu'une courbe se termine sur le chiffre affiché ailleurs sur la page.

### `mesure_provinces.mjs` — détecter les débordements

```bash
node scripts/verif/mesure_provinces.mjs <url> 1280 1440 1600 1728
```

Mesure, à chaque largeur donnée, la place disponible dans une carte de
province et celle qu'il faudrait. C'est lui qui a chiffré le défaut du
24 août : 75 px disponibles pour 135 px nécessaires à 1 280 px, si bien que le
nombre sortait de sa carte et passait **sous** la suivante, qui a un fond
opaque. D'où le « 4 » seul de « 4 607 ».

Le principe se transpose : mesurer plutôt que juger à l'œil.

### `test_onglets.mjs` — parcourir tous les onglets

```bash
node scripts/verif/test_onglets.mjs http://127.0.0.1:8899/donnees/
```

Clique chaque sous-onglet deux fois de suite, rapporte le type de graphique
obtenu, l'état du second cadre, et **toute erreur console**. À lancer après
chaque modification de `app.js`.

La liste des modes est en dur dans le fichier — la mettre à jour quand la
barre d'onglets change.

## Les quatre autres

Gardés pour ne rien perdre, mais redondants :

- **`capture_onglet.mjs`** — capture de page après clic d'onglet. Remplacé par
  `capture_canvas.mjs` avec son quatrième argument, plus fiable.
- **`capture_provinces.mjs`** — capture de la section « Provinces ».
  `capture_page.mjs` fait la même chose avec un sélecteur.
- **`sonde.mjs`** — sonde ponctuelle sur la hauteur d'un cadre. Elle a servi à
  trouver que `flex:1 1 0`, correct pour partager une largeur, porte sur la
  **hauteur** une fois le conteneur passé en colonne, et neutralise la
  propriété `height`.
- **`test_bascule.mjs`** — éprouve la bascule Effectifs / Parts de l'onglet
  « Âge et sexe ».

## Un piège à connaître

Sous Windows, `sys.stdin` décode en cp1252 : un motif Python contenant un
accent ne correspondra pas au HTML lu sur l'entrée standard. Un contrôle a
ainsi conclu à tort que cinq pages sur six étaient cassées, alors que seule la
phrase sans accent passait le filtre. Préférer `grep` puis `sed` sur le flux,
ou forcer l'encodage.
