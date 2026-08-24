/* Capture une section d'une page. node capture_page.mjs <url> <sortie.png> <selecteur> [largeur] */
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';
const [URL_PAGE, SORTIE, SEL] = process.argv.slice(2);
const W = Number(process.argv[5] || 1440);
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9371;
const PROFILE = resolve(mkdtempSync(resolve(tmpdir(), 'page-')));
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
await cdp.send('Emulation.setDeviceMetricsOverride',{width:W,height:1000,deviceScaleFactor:Number(process.argv[6]||2),mobile:false},sessionId);
const loaded = new Promise(r => cdp.on(m => { if(m.method==='Page.loadEventFired'&&m.sessionId===sessionId) r(); }));
await cdp.send('Page.navigate',{url:URL_PAGE},sessionId);
await loaded; await sleep(5000);
const geo = await cdp.send('Runtime.evaluate',{expression:`(()=>{
  const e=document.querySelector(${JSON.stringify(SEL)});
  if(!e) return JSON.stringify({erreur:'selecteur introuvable'});
  const r=e.getBoundingClientRect();
  return JSON.stringify({x:Math.max(0,Math.floor(r.left)-8),y:Math.max(0,Math.floor(r.top+window.scrollY)-8),
                         width:Math.ceil(r.width)+16,height:Math.ceil(r.height)+16});})()`,returnByValue:true},sessionId);
const clip=JSON.parse(geo.result.value);
if(clip.erreur){ console.log(clip.erreur); process.exit(1); }
const { data } = await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{...clip,scale:Number(process.argv[6]||2)}},sessionId);
writeFileSync(SORTIE, Buffer.from(data,'base64'));
console.log(`${SORTIE} ecrit (${clip.width}x${clip.height} css px)`);
cdp.close(); chrome.kill();
