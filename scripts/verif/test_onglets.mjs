/* Clique tous les sous-onglets en boucle et rapporte les erreurs console. */
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';

const URL_PAGE = process.argv[2];
// Chrome sous Windows, Brave (meme moteur) sur le Mac ; CHROME dans
// l'environnement pour tout autre chemin.
const CHROME = process.env.CHROME || (process.platform === 'darwin'
  ? '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
  : 'C:/Program Files/Google/Chrome/Application/chrome.exe');
const PORT = 9358;
const PROFILE = resolve(mkdtempSync(resolve(tmpdir(), 'onglets-')));
const chrome = spawn(CHROME, ['--headless=new','--disable-gpu','--hide-scrollbars','--no-first-run',
  '--no-default-browser-check','--disable-extensions',
  `--remote-debugging-port=${PORT}`,`--user-data-dir=${PROFILE}`], { stdio:'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function browserWs(){ for(let i=0;i<60;i++){ try{ const r=await fetch(`http://127.0.0.1:${PORT}/json/version`); return (await r.json()).webSocketDebuggerUrl; }catch{ await sleep(250);} } throw new Error('Chrome muet'); }
function connect(url){ const ws=new WebSocket(url); const pending=new Map(); const ls=[]; let id=0;
  ws.addEventListener('message',ev=>{ const m=JSON.parse(ev.data);
    if(m.id&&pending.has(m.id)){ const {resolve:res,reject}=pending.get(m.id); pending.delete(m.id); m.error?reject(new Error(m.error.message)):res(m.result); }
    else if(m.method) ls.forEach(f=>f(m)); });
  const ready=new Promise((res,rej)=>{ws.addEventListener('open',res);ws.addEventListener('error',rej);});
  return { ready, send(me,p={},s){ const mid=++id; return new Promise((res,rej)=>{pending.set(mid,{resolve:res,reject:rej}); ws.send(JSON.stringify({id:mid,method:me,params:p,sessionId:s}));}); }, on(f){ls.push(f);}, close(){ws.close();} };
}
const cdp = connect(await browserWs());
await cdp.ready;
const { targetId } = await cdp.send('Target.createTarget',{url:'about:blank'});
const { sessionId } = await cdp.send('Target.attachToTarget',{targetId,flatten:true});
await cdp.send('Page.enable',{},sessionId);
await cdp.send('Runtime.enable',{},sessionId);
await cdp.send('Log.enable',{},sessionId);
const problemes = [];
cdp.on(m => {
  if(m.sessionId !== sessionId) return;
  if(m.method === 'Runtime.exceptionThrown')
    problemes.push('EXCEPTION ' + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
  if(m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error')
    problemes.push('CONSOLE.ERROR ' + m.params.args.map(a=>a.value||a.description).join(' '));
  if(m.method === 'Log.entryAdded' && m.params.entry.level === 'error')
    problemes.push('LOG ' + m.params.entry.text);
});
await cdp.send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false},sessionId);
const loaded = new Promise(res => cdp.on(m => { if(m.method==='Page.loadEventFired'&&m.sessionId===sessionId) res(); }));
await cdp.send('Page.navigate',{url:URL_PAGE},sessionId);
await loaded;
await sleep(2500);

const modes = ['epidemic','byProvince','contactsFollowUp','communityDeaths','ages','sexes','pyramide'];
// Deux tours, pour eprouver le retour sur un onglet deja visite.
for(const tour of [1,2]){
  for(const m of modes){
    const r = await cdp.send('Runtime.evaluate',{expression:
      `(()=>{const b=document.querySelector('[data-mode="${m}"]');if(!b)return 'ABSENT';b.click();
        const c=document.querySelector('canvas[data-chart]');const ch=c&&Chart.getChart(c);
        const pB=document.getElementById('dataChartB');
        const visible=pB && pB.closest('.chart-panel').style.display!=='none';
        const chB=pB&&Chart.getChart(pB);
        return (ch ? ch.config.type+'/'+ch.data.datasets.length+' jeux' : 'aucun graphique')
               +' | 2e cadre '+(visible?'OUVERT':'ferme')+(chB?' (graphique vivant)':'');})()`,
      returnByValue:true},sessionId);
    await sleep(350);
    console.log(`  tour ${tour} — ${m.padEnd(18)} ${r.result.value}`);
  }
}
console.log(problemes.length ? '\nPROBLEMES :\n' + problemes.join('\n') : '\nAucune erreur console.');
cdp.close(); chrome.kill();
