/* Capture le panneau de graphique d'une page, apres avoir clique un sous-onglet.
 * node capture_onglet.mjs <url> <sortie.png> <data-mode> [largeur]
 */
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';

const [URL_PAGE, SORTIE, MODE] = process.argv.slice(2);
const W = Number(process.argv[5] || 1440);
// Chrome sous Windows, Brave (meme moteur) sur le Mac ; CHROME dans
// l'environnement pour tout autre chemin.
const CHROME = process.env.CHROME || (process.platform === 'darwin'
  ? '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
  : 'C:/Program Files/Google/Chrome/Application/chrome.exe');
const PORT = 9351;
const PROFILE = resolve(mkdtempSync(resolve(tmpdir(), 'onglet-')));

const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
  '--no-default-browser-check', '--disable-extensions',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`,
], { stdio: 'ignore' });

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function browserWs() {
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(`http://127.0.0.1:${PORT}/json/version`); return (await r.json()).webSocketDebuggerUrl; }
    catch { await sleep(250); }
  }
  throw new Error('Chrome ne repond pas');
}
function connect(url) {
  const ws = new WebSocket(url);
  const pending = new Map(); const listeners = []; let id = 0;
  ws.addEventListener('message', ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { const { resolve: res, reject } = pending.get(m.id); pending.delete(m.id);
      m.error ? reject(new Error(m.error.message)) : res(m.result); }
    else if (m.method) listeners.forEach(fn => fn(m));
  });
  const ready = new Promise((res, rej) => { ws.addEventListener('open', res); ws.addEventListener('error', rej); });
  return { ready,
    send(me, p = {}, s) { const mid = ++id;
      return new Promise((res, rej) => { pending.set(mid, { resolve: res, reject: rej });
        ws.send(JSON.stringify({ id: mid, method: me, params: p, sessionId: s })); }); },
    on(fn) { listeners.push(fn); }, close() { ws.close(); } };
}

const cdp = connect(await browserWs());
await cdp.ready;
const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
await cdp.send('Page.enable', {}, sessionId);
await cdp.send('Emulation.setDeviceMetricsOverride', { width: W, height: 1000, deviceScaleFactor: 2, mobile: false }, sessionId);
const loaded = new Promise(res => cdp.on(m => { if (m.method === 'Page.loadEventFired' && m.sessionId === sessionId) res(); }));
await cdp.send('Page.navigate', { url: URL_PAGE }, sessionId);
await loaded;
await sleep(2500);

const clic = await cdp.send('Runtime.evaluate', { expression: `(() => {
  const b = document.querySelector('[data-mode="${MODE}"]');
  if(!b) return 'bouton introuvable';
  b.click();
  return 'clic sur ' + b.textContent.trim();
})()`, returnByValue: true }, sessionId);
console.log(clic.result.value);
await sleep(1200);

// Second clic optionnel : la bascule de vue de la pyramide.
const VUE = process.argv[6];
if(VUE){
  const c2 = await cdp.send('Runtime.evaluate', { expression: `(() => {
    const b = document.querySelector('[data-vue="${VUE}"]');
    if(!b) return 'bascule introuvable';
    b.click();
    return 'clic sur ' + b.textContent.trim();
  })()`, returnByValue: true }, sessionId);
  console.log(c2.result.value);
}
await sleep(1500);

const diag = await cdp.send('Runtime.evaluate', { expression: `(() => {
  const c = document.querySelector('canvas[data-chart]');
  const ch = c && Chart.getChart(c);
  if(!ch) return JSON.stringify({erreur:'aucun graphique'});
  return JSON.stringify({
    type: ch.config.type,
    datasets: ch.data.datasets.map(d => ({label:d.label, sexe:d.sexe, stack:d.stack, data:d.data})),
    labels: ch.data.labels,
    note: (document.querySelector('.chart-note')||{}).textContent || '',
  });
})()`, returnByValue: true }, sessionId);
console.log(diag.result.value);

const geo = await cdp.send('Runtime.evaluate', { expression: `(() => {
  const s = document.querySelector('canvas[data-chart]').closest('.section');
  const r = s.getBoundingClientRect();
  return JSON.stringify({x:Math.max(0,Math.floor(r.left)-8), y:Math.max(0,Math.floor(r.top+window.scrollY)-8),
                         width:Math.ceil(r.width)+16, height:Math.ceil(r.height)+16});
})()`, returnByValue: true }, sessionId);
const clip = JSON.parse(geo.result.value);
const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { ...clip, scale: 2 } }, sessionId);
writeFileSync(SORTIE, Buffer.from(data, 'base64'));
console.log(`${SORTIE} ecrit (${clip.width}x${clip.height} css px)`);
cdp.close(); chrome.kill();
