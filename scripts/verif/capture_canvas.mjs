/* Recupere l'image du canevas Chart.js lui-meme, animation figee.
 * node capture_canvas.mjs <url> <sortie.png> [largeur] */
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';
const [URL_PAGE, SORTIE] = process.argv.slice(2);
const W = Number(process.argv[4] || 1440);
// Chrome sous Windows, Brave (meme moteur) sur le Mac ; CHROME dans
// l'environnement pour tout autre chemin.
const CHROME = process.env.CHROME || (process.platform === 'darwin'
  ? '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
  : 'C:/Program Files/Google/Chrome/Application/chrome.exe');
const PORT = 9381;
const PROFILE = resolve(mkdtempSync(resolve(tmpdir(), 'canvas-')));
const chrome = spawn(CHROME, ['--headless=new','--disable-gpu','--hide-scrollbars','--no-first-run',
  '--no-default-browser-check','--disable-extensions',
  `--remote-debugging-port=${PORT}`,`--user-data-dir=${PROFILE}`], { stdio:'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function ws(){ for(let i=0;i<60;i++){ try{ const r=await fetch(`http://127.0.0.1:${PORT}/json/version`); return (await r.json()).webSocketDebuggerUrl; }catch{ await sleep(250);} } throw new Error('muet'); }
function connect(u){ const s=new WebSocket(u); const p=new Map(); const l=[]; let id=0;
  s.addEventListener('message',e=>{ const m=JSON.parse(e.data);
    if(m.id&&p.has(m.id)){ const {resolve:r,reject:j}=p.get(m.id); p.delete(m.id); m.error?j(new Error(m.error.message)):r(m.result); } else if(m.method) l.forEach(f=>f(m)); });
  const ready=new Promise((r,j)=>{s.addEventListener('open',r);s.addEventListener('error',j);});
  return { ready, send(me,pa={},se){ const i=++id; return new Promise((r,j)=>{p.set(i,{resolve:r,reject:j}); s.send(JSON.stringify({id:i,method:me,params:pa,sessionId:se}));}); }, on(f){l.push(f);}, close(){s.close();} };
}
const cdp = connect(await ws()); await cdp.ready;
const { targetId } = await cdp.send('Target.createTarget',{url:'about:blank'});
const { sessionId } = await cdp.send('Target.attachToTarget',{targetId,flatten:true});
await cdp.send('Page.enable',{},sessionId);
await cdp.send('Emulation.setDeviceMetricsOverride',{width:W,height:1200,deviceScaleFactor:2,mobile:false},sessionId);
const loaded = new Promise(r => cdp.on(m => { if(m.method==='Page.loadEventFired'&&m.sessionId===sessionId) r(); }));
await cdp.send('Page.navigate',{url:URL_PAGE},sessionId);
await loaded; await sleep(2500);
// Clic optionnel sur un sous-onglet avant la capture.
const MODE = process.argv[5];
if(MODE){
  await cdp.send('Runtime.evaluate',{expression:
    `(()=>{const b=document.querySelector('[data-mode="${MODE}"]'); if(b) b.click();})()`},sessionId);
  await sleep(1500);
}
const r = await cdp.send('Runtime.evaluate',{expression:`(()=>{
  const c=document.querySelector('canvas[data-chart]');
  const ch=c && Chart.getChart(c);
  if(!ch) return JSON.stringify({erreur:'aucun graphique'});
  // Fige l'animation et redessine d'un coup : sinon la capture attrape un
  // etat intermediaire, ou un canevas vide apres un re-rendu.
  ch.options.animation = false;
  ch.options.animations = false;
  ch.update('none');
  return JSON.stringify({image: c.toDataURL('image/png'),
                         jeux: ch.data.datasets.length,
                         points: ch.data.labels.length});})()`,returnByValue:true},sessionId);
const d = JSON.parse(r.result.value);
if(d.erreur){ console.log(d.erreur); process.exit(1); }
writeFileSync(SORTIE, Buffer.from(d.image.split(',')[1],'base64'));
console.log(`${SORTIE} ecrit — ${d.jeux} jeux, ${d.points} points`);
cdp.close(); chrome.kill();
