/* Audit mobile du site genere.
 *
 *   1. servir le site :   python -m http.server 8080
 *   2. lancer l'audit :   node scripts/audit_mobile.mjs 360 tmp/audit
 *
 * Le script pilote Chrome par le protocole DevTools. C'est indispensable :
 * sous Windows, --window-size ne descend pas sous ~500 px, si bien qu'une
 * capture « a 360 px » est en realite un rendu a 504 px rogne — le site
 * parait deborder alors qu'il ne deborde pas. Emulation.setDeviceMetricsOverride
 * impose une vraie largeur de viewport, et les media queries s'appliquent.
 *
 * Il produit, par page :
 *   - une capture pleine hauteur ;
 *   - la liste des elements qui debordent hors de l'ecran, en ecartant ceux
 *     qui vivent dans un conteneur defilant (un tableau large, la barre
 *     d'onglets : leur debordement est voulu) ;
 *   - les cibles tactiles sous 40 px ;
 *   - les textes sous 11,5 px.
 *
 * Largeurs utiles : 320 (vieux Android, pire cas), 360 (Android courant),
 * 390 (iPhone recent). Le public de ce site est surtout sur les deux
 * premieres.
 */
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const WIDTH = Number(process.argv[2]);
// Chrome exige un chemin absolu pour son profil, et refuse de demarrer
// autrement — avec un message qui ne dit pas lequel des deux a echoue.
const OUT = resolve(process.argv[3]);
const PAGES = process.argv.slice(4).map(a => {
  const i = a.indexOf(':');
  return { name: a.slice(0, i), url: a.slice(i + 1) };
});
mkdirSync(OUT, { recursive: true });

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9333;
const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
  '--no-default-browser-check', '--disable-extensions',
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${OUT}/profile`,
], { stdio: 'ignore' });

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function browserWs() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      return (await r.json()).webSocketDebuggerUrl;
    } catch { await sleep(250); }
  }
  throw new Error('Chrome ne repond pas');
}

/* Petit client CDP : un compteur de messages, une table de promesses. */
function connect(url) {
  const ws = new WebSocket(url);
  const pending = new Map();
  const listeners = [];
  let id = 0;
  ws.addEventListener('message', ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
    } else if (msg.method) {
      listeners.forEach(fn => fn(msg));
    }
  });
  const ready = new Promise((res, rej) => {
    ws.addEventListener('open', res);
    ws.addEventListener('error', rej);
  });
  return {
    ready,
    send(method, params = {}, sessionId) {
      const mid = ++id;
      return new Promise((resolve, reject) => {
        pending.set(mid, { resolve, reject });
        ws.send(JSON.stringify({ id: mid, method, params, sessionId }));
      });
    },
    on(fn) { listeners.push(fn); },
    close() { ws.close(); },
  };
}

/* La sonde tourne dans la page : elle rend les elements qui debordent, et le
   detail des ancetres du plus large d'entre eux. */
const PROBE = `(() => {
  const w = document.documentElement.clientWidth;
  const over = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (!r.width && !r.height) return;
    if (r.right <= w + 1 && r.left >= -1) return;
    if (el.closest('[style*="-9999"], .skip-link')) return;
    const cs = getComputedStyle(el);
    let scroller = false;
    for (let p = el.parentElement; p; p = p.parentElement) {
      const o = getComputedStyle(p).overflowX;
      if (o === 'auto' || o === 'scroll' || o === 'hidden') { scroller = true; break; }
    }
    const cls = el.getAttribute('class');
    over.push({
      sel: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (cls ? '.' + cls.trim().split(/\s+/).join('.') : ''),
      left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width),
      scroller, text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40),
    });
  });
  // Cibles tactiles trop petites : la recommandation courante est 44x44 px.
  const small = [];
  document.querySelectorAll('a, button, input, select, [role="button"]').forEach(el => {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    if (r.height >= 40 && r.width >= 40) return;
    if (el.closest('.breadcrumb, .side-nav, .footer, .tl-link, p, li')) return;
    const cls = el.getAttribute('class');
    small.push({ sel: el.tagName.toLowerCase() + (cls ? '.' + cls.trim().split(/\s+/)[0] : ''),
      w: Math.round(r.width), h: Math.round(r.height),
      text: (el.textContent || '').trim().slice(0, 24) });
  });
  // Texte minuscule.
  const tiny = new Map();
  document.querySelectorAll('body *').forEach(el => {
    if (!el.childNodes.length) return;
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!hasText) return;
    const size = parseFloat(getComputedStyle(el).fontSize);
    if (size >= 11.5) return;
    const cls = el.getAttribute('class');
    const key = el.tagName.toLowerCase() + (cls ? '.' + cls.trim().split(/\s+/)[0] : '');
    if (!tiny.has(key)) tiny.set(key, { sel: key, size: size, text: (el.textContent||'').trim().slice(0,30) });
  });
  return JSON.stringify({
    viewport: w, scrollWidth: document.documentElement.scrollWidth,
    over, small, tiny: [...tiny.values()],
    height: document.documentElement.scrollHeight,
  });
})()`;

const ws = await browserWs();
const cdp = connect(ws);
await cdp.ready;

const report = [];
for (const page of PAGES) {
  const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  await cdp.send('Page.enable', {}, sessionId);
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: WIDTH, height: 800, deviceScaleFactor: 1, mobile: true,
  }, sessionId);

  const loaded = new Promise(res => cdp.on(m => {
    if (m.method === 'Page.loadEventFired' && m.sessionId === sessionId) res();
  }));
  await cdp.send('Page.navigate', { url: page.url }, sessionId);
  await loaded;
  await sleep(1200);

  const { result } = await cdp.send('Runtime.evaluate',
    { expression: PROBE, returnByValue: true }, sessionId);
  const data = JSON.parse(result.value);

  const height = Math.min(data.height, 6000);
  const { data: png } = await cdp.send('Page.captureScreenshot', {
    format: 'png', captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: WIDTH, height, scale: 1 },
  }, sessionId);
  writeFileSync(`${OUT}/${page.name}.png`, Buffer.from(png, 'base64'));

  report.push({ page: page.name, ...data });
  await cdp.send('Target.closeTarget', { targetId });
}

cdp.close();
chrome.kill();

for (const r of report) {
  const debord = r.over.filter(o => !o.scroller);
  console.log(`\n=== ${r.page}  viewport ${r.viewport}px  page ${r.scrollWidth}px  hauteur ${r.height}px`);
  if (r.viewport !== WIDTH) console.log(`  !! viewport inattendu`);
  if (r.scrollWidth > r.viewport) console.log(`  !! defilement horizontal : +${r.scrollWidth - r.viewport}px`);
  if (!debord.length) console.log('  debordement : aucun');
  debord.slice(0, 8).forEach(o =>
    console.log(`  DEBORDE  ${o.sel}  [${o.left} -> ${o.right}] w=${o.width}  "${o.text}"`));
  const inScroller = r.over.length - debord.length;
  if (inScroller) console.log(`  (${inScroller} element(s) dans un conteneur defilant : normal)`);
  r.small.slice(0, 6).forEach(s =>
    console.log(`  CIBLE    ${s.sel} ${s.w}x${s.h}px  "${s.text}"`));
  r.tiny.slice(0, 6).forEach(t =>
    console.log(`  TEXTE    ${t.sel} ${t.size}px  "${t.text}"`));
}
