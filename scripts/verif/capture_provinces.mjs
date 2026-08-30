/* Capture la section « Provinces » a une largeur donnee.
 * node capture_provinces.mjs http://127.0.0.1:8899/ sortie-prefixe 1280 1440
 */
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';

const URL_PAGE = process.argv[2];
const PREFIXE = process.argv[3];
const WIDTHS = process.argv.slice(4).map(Number);
// Chrome sous Windows, Brave (meme moteur) sur le Mac ; CHROME dans
// l'environnement pour tout autre chemin.
const CHROME = process.env.CHROME || (process.platform === 'darwin'
  ? '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
  : 'C:/Program Files/Google/Chrome/Application/chrome.exe');
const PORT = 9346;
const PROFILE = resolve(mkdtempSync(resolve(tmpdir(), 'capture-')));

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
  const pending = new Map(); const listeners = []; let id = 0;
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
    send(m, p = {}, s) {
      const mid = ++id;
      return new Promise((res, rej) => { pending.set(mid, { resolve: res, reject: rej }); ws.send(JSON.stringify({ id: mid, method: m, params: p, sessionId: s })); });
    },
    on(fn) { listeners.push(fn); }, close() { ws.close(); },
  };
}

const cdp = connect(await browserWs());
await cdp.ready;

for (const W of WIDTHS) {
  const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  await cdp.send('Page.enable', {}, sessionId);
  await cdp.send('Emulation.setDeviceMetricsOverride',
    { width: W, height: 900, deviceScaleFactor: 2, mobile: false }, sessionId);
  const loaded = new Promise(res => cdp.on(m => {
    if (m.method === 'Page.loadEventFired' && m.sessionId === sessionId) res();
  }));
  await cdp.send('Page.navigate', { url: URL_PAGE + '?cb=' + W + Math.floor(Math.random()*1e6) }, sessionId);
  await loaded;
  await sleep(900);
  const { result } = await cdp.send('Runtime.evaluate', {
    expression: `(() => {
      const s = document.querySelector('.province-grid').closest('.section');
      const r = s.getBoundingClientRect();
      return JSON.stringify({x:Math.max(0,Math.floor(r.left)-8),y:Math.max(0,Math.floor(r.top+window.scrollY)-8),
                             width:Math.ceil(r.width)+16,height:Math.ceil(r.height)+16});
    })()`, returnByValue: true }, sessionId);
  const clip = JSON.parse(result.value);
  const { data } = await cdp.send('Page.captureScreenshot', {
    format: 'png', captureBeyondViewport: true,
    clip: { ...clip, scale: 2 },
  }, sessionId);
  const f = `${PREFIXE}-${W}.png`;
  writeFileSync(f, Buffer.from(data, 'base64'));
  console.log(`${f}  (${clip.width}x${clip.height} css px)`);
  await cdp.send('Target.closeTarget', { targetId });
}

cdp.close(); chrome.kill();
