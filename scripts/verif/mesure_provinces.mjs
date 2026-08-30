/* Mesure la carte de province a plusieurs largeurs de viewport.
 * node mesure_provinces.mjs http://127.0.0.1:8899/ 1280 1366 1440 1512 1600 1728
 */
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';

const URL_PAGE = process.argv[2];
const WIDTHS = process.argv.slice(3).map(Number);
// Chrome sous Windows, Brave (meme moteur) sur le Mac ; CHROME dans
// l'environnement pour tout autre chemin.
const CHROME = process.env.CHROME || (process.platform === 'darwin'
  ? '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
  : 'C:/Program Files/Google/Chrome/Application/chrome.exe');
const PORT = 9345;
const PROFILE = resolve(mkdtempSync(resolve(tmpdir(), 'mesure-')));

const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
  '--no-default-browser-check', '--disable-extensions',
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`,
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

function connect(url) {
  const ws = new WebSocket(url);
  const pending = new Map();
  const listeners = [];
  let id = 0;
  ws.addEventListener('message', ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve: res, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : res(msg.result);
    } else if (msg.method) listeners.forEach(fn => fn(msg));
  });
  const ready = new Promise((res, rej) => {
    ws.addEventListener('open', res); ws.addEventListener('error', rej);
  });
  return {
    ready,
    send(method, params = {}, sessionId) {
      const mid = ++id;
      return new Promise((res, rej) => {
        pending.set(mid, { resolve: res, reject: rej });
        ws.send(JSON.stringify({ id: mid, method, params, sessionId }));
      });
    },
    on(fn) { listeners.push(fn); },
    close() { ws.close(); },
  };
}

const PROBE = `(() => {
  const cards = [...document.querySelectorAll('.province-card')];
  const grid = document.querySelector('.province-grid');
  const out = cards.map(card => {
    const cs = getComputedStyle(card);
    const r = card.getBoundingClientRect();
    const padL = parseFloat(cs.paddingLeft), padR = parseFloat(cs.paddingRight);
    const bL = parseFloat(cs.borderLeftWidth), bR = parseFloat(cs.borderRightWidth);
    const innerL = r.left + bL + padL, innerR = r.right - bR - padR;
    const stats = [...card.querySelectorAll('.pc-stat')].map(s => {
      const k = s.querySelector('.k').getBoundingClientRect();
      const v = s.querySelector('.v').getBoundingClientRect();
      return {
        label: s.querySelector('.k').textContent,
        kW: +k.width.toFixed(1), vW: +v.width.toFixed(1),
        vText: s.querySelector('.v').textContent,
        besoin: +(k.width + 6 + v.width).toFixed(1),
        debord: +(v.right - innerR).toFixed(1),
        vLignes: Math.round(v.height / parseFloat(getComputedStyle(s.querySelector('.v')).lineHeight)),
      };
    });
    return {
      nom: card.querySelector('h3').textContent,
      carte: +r.width.toFixed(1), interieur: +(innerR - innerL).toFixed(1),
      hauteur: +r.height.toFixed(1),
      stats,
    };
  });
  return JSON.stringify({
    viewport: document.documentElement.clientWidth,
    gridW: grid ? +grid.getBoundingClientRect().width.toFixed(1) : null,
    flow: grid ? getComputedStyle(grid).gridAutoFlow : null,
    cards: out,
  });
})()`;

const cdp = connect(await browserWs());
await cdp.ready;

for (const W of WIDTHS) {
  const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  await cdp.send('Page.enable', {}, sessionId);
  await cdp.send('Emulation.setDeviceMetricsOverride',
    { width: W, height: 900, deviceScaleFactor: 1, mobile: false }, sessionId);
  const loaded = new Promise(res => cdp.on(m => {
    if (m.method === 'Page.loadEventFired' && m.sessionId === sessionId) res();
  }));
  await cdp.send('Page.navigate', { url: URL_PAGE + '?cb=' + W }, sessionId);
  await loaded;
  await sleep(900);
  const { result } = await cdp.send('Runtime.evaluate',
    { expression: PROBE, returnByValue: true }, sessionId);
  const d = JSON.parse(result.value);

  console.log(`\n===== viewport ${d.viewport}px  |  grille ${d.gridW}px  |  flow ${d.flow} =====`);
  for (const c of d.cards) {
    const s = c.stats[0];
    const pire = Math.max(...c.stats.map(x => x.debord));
    console.log(
      `  ${c.nom.padEnd(11)} carte ${String(c.carte).padStart(6)}  interieur ${String(c.interieur).padStart(6)}` +
      `  | « ${s.label} » ${s.kW}px + valeur « ${s.vText} » ${s.vW}px = ${s.besoin}px requis` +
      `  | debordement max ${pire > 0 ? '+' + pire : pire}px`);
  }
  await cdp.send('Target.closeTarget', { targetId });
}

cdp.close();
chrome.kill();
