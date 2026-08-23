/* Rend un fichier HTML en PNG a une taille exacte, via le protocole DevTools.
 * --screenshot en ligne de commande ne descend pas sous ~500 px de large sous
 * Windows et ne permet pas de fixer le facteur d'echelle ; setDeviceMetricsOverride
 * fait les deux.
 *
 *   node rendu.mjs <fichier.html> <sortie.png> <largeur> <hauteur> [echelle]
 */
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [src, out, w, h, scaleArg] = process.argv.slice(2);
const WIDTH = Number(w), HEIGHT = Number(h), SCALE = Number(scaleArg || 2);
const PORT = 9377;

const chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', [
  '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
  '--no-default-browser-check', '--force-color-profile=srgb',
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${resolve(out, '..')}/profil-rendu`,
], { stdio: 'ignore' });

const sleep = ms => new Promise(r => setTimeout(r, ms));
let wsUrl;
for (let i = 0; i < 80; i++) {
  try {
    wsUrl = (await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json()).webSocketDebuggerUrl;
    break;
  } catch { await sleep(250); }
}

const sock = new WebSocket(wsUrl);
const pending = new Map();
let id = 0;
sock.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) {
    const { res, rej } = pending.get(m.id);
    pending.delete(m.id);
    m.error ? rej(new Error(m.error.message)) : res(m.result);
  }
});
await new Promise(r => sock.addEventListener('open', r));
const send = (method, params = {}, sessionId) => new Promise((res, rej) => {
  const i = ++id;
  pending.set(i, { res, rej });
  sock.send(JSON.stringify({ id: i, method, params, sessionId }));
});

const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
await send('Page.enable', {}, sessionId);
await send('Emulation.setDeviceMetricsOverride',
  { width: WIDTH, height: HEIGHT, deviceScaleFactor: SCALE, mobile: false }, sessionId);
await send('Page.navigate', { url: pathToFileURL(resolve(src)).href }, sessionId);
await sleep(1500);

// Les polices Google arrivent par le reseau : on attend qu'elles soient posees,
// sinon le titre est rendu en Georgia de repli.
const { result } = await send('Runtime.evaluate', {
  expression: `document.fonts.ready.then(() => [...document.fonts]
    .filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight + ' ' + f.style).join(' | '))`,
  awaitPromise: true, returnByValue: true,
}, sessionId);
console.log('polices chargees :', result.value || '(aucune)');
await sleep(400);

const { data } = await send('Page.captureScreenshot', {
  format: 'png', captureBeyondViewport: true,
  // scale reste a 1 : le facteur d'echelle est deja porte par
  // setDeviceMetricsOverride, le cumuler donnait une image quatre fois trop
  // grande.
  clip: { x: 0, y: 0, width: WIDTH, height: HEIGHT, scale: 1 },
}, sessionId);
writeFileSync(resolve(out), Buffer.from(data, 'base64'));
console.log(`${out} — ${WIDTH * SCALE}x${HEIGHT * SCALE}`);

sock.close();
chrome.kill();
