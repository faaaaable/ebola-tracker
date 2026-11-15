/* Capture de l'affiche en relief, en deux calques (15 novembre 2026).
   node --experimental-websocket capture.mjs <url> <sortie-sans-extension>
   ecrit <sortie>-canevas.png (les pixels du canevas, 3200 x 4000, lus tels
   quels) et <sortie>-texte.png (l'affiche a l'echelle 2, canevas cache, fond
   transparent) ; carte_relief.py les superpose.
   Pourquoi : depuis le SitRep 181, la capture d'ecran de l'affiche entiere a
   l'echelle 2 restait figee (navigateur inactif, sans erreur) : l'image
   (environ 6 Mo) ne revient jamais par le WebSocket experimental de Node 20,
   alors que la page l'a bien faite. Le canevas revient donc par tranches,
   le texte (presque tout transparent, leger) en une capture. Le navigateur
   est ferme dans tous les cas (avant : il survivait a un echec et gardait le
   port de la capture suivante). */
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync, rmSync, readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';
const [URL_PAGE, SORTIE] = process.argv.slice(2);
const CHROME = process.env.CHROME || (process.platform === 'darwin'
  ? '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
  : 'C:/Program Files/Google/Chrome/Application/chrome.exe');
const PROFILE = resolve(mkdtempSync(resolve(tmpdir(), 'relief-')));
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
  '--no-default-browser-check', '--disable-extensions', '--remote-debugging-port=0', `--user-data-dir=${PROFILE}`], { stdio: 'ignore' });
let fini = false;
function fin(code) {
  if (fini) return; fini = true;
  try { chrome.kill('SIGKILL'); } catch {}
  setTimeout(() => { try { rmSync(PROFILE, { recursive: true, force: true }); } catch {} process.exit(code); }, 300);
}
process.on('SIGTERM', () => fin(1)); process.on('SIGINT', () => fin(1));
setTimeout(() => { console.error('delai depasse'); fin(1); }, 120000);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function ws() {
  // port choisi par le navigateur, note dans le profil
  for (let i = 0; i < 80; i++) {
    const f = resolve(PROFILE, 'DevToolsActivePort');
    if (existsSync(f)) {
      const port = readFileSync(f, 'utf8').split('\n')[0].trim();
      try { const r = await fetch(`http://127.0.0.1:${port}/json/version`); return (await r.json()).webSocketDebuggerUrl; } catch {}
    }
    await sleep(250);
  }
  throw new Error('navigateur muet');
}
function connect(u) {
  const s = new WebSocket(u); const p = new Map(); const l = []; let id = 0;
  s.addEventListener('message', e => { const m = JSON.parse(e.data);
    if (m.id && p.has(m.id)) { const { resolve: r, reject: j } = p.get(m.id); p.delete(m.id); m.error ? j(new Error(m.error.message)) : r(m.result); }
    else if (m.method) l.forEach(f => f(m)); });
  const ready = new Promise((r, j) => { s.addEventListener('open', r); s.addEventListener('error', j); });
  return { ready, send(me, pa = {}, se) { const i = ++id; return new Promise((r, j) => { p.set(i, { resolve: r, reject: j }); s.send(JSON.stringify({ id: i, method: me, params: pa, sessionId: se })); }); },
    on(f) { l.push(f); }, close() { s.close(); } };
}

try {
  const cdp = connect(await ws()); await cdp.ready;
  const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  const ev = (expression) => cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true }, sessionId).then(r => r.result.value);
  await cdp.send('Page.enable', {}, sessionId);
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 1000, deviceScaleFactor: 2, mobile: false }, sessionId);
  const loaded = new Promise(r => cdp.on(m => { if (m.method === 'Page.loadEventFired' && m.sessionId === sessionId) r(); }));
  await cdp.send('Page.navigate', { url: URL_PAGE }, sessionId);
  await loaded; await ev('document.fonts.ready.then(() => 1)'); await sleep(5000);
  // 1. le canevas, pixel pour pixel
  // par tranches d'un million de caracteres : un message de plusieurs Mo ne
  // revient jamais par le WebSocket de Node
  for (let i = 0; i < 240 && !(await ev('document.documentElement.dataset.pret || ""')); i++) await sleep(500);
  const n = await ev(`(window.__png = document.querySelector('.affiche canvas').toDataURL('image/png')).length`);
  let png = '';
  for (let k = 0; k < n; k += 1e6) png += await ev(`window.__png.slice(${k}, ${k + 1e6})`);
  if (!png.startsWith('data:image/png;base64,')) throw new Error('canevas illisible');
  writeFileSync(SORTIE + '-canevas.png', Buffer.from(png.split(',')[1], 'base64'));
  // 2. le texte seul, sur fond transparent
  const r = JSON.parse(await ev(`(() => {
    const st = document.createElement('style');
    st.textContent = 'html,body,.cadre,.affiche{background:transparent!important}.affiche canvas{visibility:hidden}';
    document.head.appendChild(st);
    const b = document.querySelector('.affiche').getBoundingClientRect();
    return JSON.stringify({ x: b.left + scrollX, y: b.top + scrollY, w: b.width, h: b.height });
  })()`));
  await cdp.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } }, sessionId);
  await sleep(500);
  const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true,
    clip: { x: r.x, y: r.y, width: r.w, height: r.h, scale: 1 } }, sessionId);
  writeFileSync(SORTIE + '-texte.png', Buffer.from(data, 'base64'));
  console.log(`${SORTIE} : canevas et texte ecrits (${r.w}x${r.h})`);
  cdp.close(); fin(0);
} catch (e) { console.error(String(e)); fin(1); }
