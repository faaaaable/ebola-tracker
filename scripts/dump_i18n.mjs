/* Exporte en JSON les chaînes du dictionnaire assets/js/i18n.js.
 *
 * Le dictionnaire reste la source unique des libellés : il sert au rendu
 * dynamique dans le navigateur, et scripts/build_pages.py s'en sert — via ce
 * script — pour écrire le texte en dur dans les pages générées. Les moteurs
 * de recherche voient donc du vrai texte, et non des éléments remplis en
 * JavaScript après le chargement.
 *
 * Les chaînes et les tableaux de chaînes (les noms de mois) sont exportés ;
 * les fonctions de formatage sont ignorées, elles n'ont de sens qu'à
 * l'exécution — le générateur reproduit les quelques formats dont il a
 * besoin.
 *
 * Usage : node scripts/dump_i18n.mjs   (depuis la racine du dépôt)
 */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const root = process.cwd();
const file = path.join(root, 'assets', 'js', 'i18n.js');
const src = fs.readFileSync(file, 'utf8');

// i18n.js est écrit pour le navigateur : on l'évalue dans un contexte isolé,
// puis on récupère la constante en la ré-exposant depuis le même script.
const context = vm.createContext({});
vm.runInContext(`${src}\n;globalThis.__DUMP__ = I18N;`, context, { filename: 'i18n.js' });

const out = {};
for (const [lang, dict] of Object.entries(context.__DUMP__)) {
  out[lang] = {};
  for (const [key, value] of Object.entries(dict)) {
    if (typeof value === 'string') out[lang][key] = value;
    else if (Array.isArray(value) && value.every((v) => typeof v === 'string')) out[lang][key] = value;
  }
}

process.stdout.write(JSON.stringify(out, null, 1));
