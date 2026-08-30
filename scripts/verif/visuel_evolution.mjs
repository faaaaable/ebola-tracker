/* Visuel a diffuser : la carte de l'accueil, cadree sur l'epicentre, a N dates
   regulierement espacees du premier instantane au dernier — l'evolution de
   l'epidemie sur une seule image, en grille de trois colonnes.

   node scripts/verif/visuel_evolution.mjs <n> [sortie.png] [--lang=en] [--dx=0] [--dy=0] [--zoom=1]

   n : 3, 6 ou 9 (un multiple de trois). dx/dy decalent le cadre, en unites du
   viewBox (1000 de large) ; zoom > 1 resserre, < 1 elargit. Le site doit etre
   servi en local sur le port 8899. Les sorties vont dans tmp/, hors du site. */
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { tmpdir } from 'node:os';

const args = process.argv.slice(2);
const opt = Object.fromEntries(args.filter(a => a.startsWith('--')).map(a => a.slice(2).split('=')));
const N = Number(args.find(a => !a.startsWith('--')) || 3);
const LANG = opt.lang || 'en';
const SORTIE = resolve(args.filter(a => !a.startsWith('--'))[1] || `tmp/visuels/evolution-${LANG}-${N}.png`);
const DX = Number(opt.dx || 0), DY = Number(opt.dy || 0), ZOOM = Number(opt.zoom || 1);
/* Provinces laissees hors du cadre (--sans=Sud-Kivu,…) : Miti-Murhesa, seule
   zone du Sud-Kivu, est a 330 unites au sud de l'Ituri et allongeait le
   cadre d'un tiers pour trois cas. Leurs zones restent coloriees si elles
   entrent quand meme dans l'image ; le pied le dit. */
const SANS = (opt.sans || '').split(',').map(s => s.trim()).filter(Boolean);
/* Et des zones nommees (--sans-zones=Goma,…) : Goma est au Nord-Kivu mais
   aussi loin au sud que le Sud-Kivu, pour un cas. */
const SANS_ZONES = (opt['sans-zones'] || '').split(',').map(s => s.trim()).filter(Boolean);
const URL_PAGE = `http://127.0.0.1:8899/${LANG === 'fr' ? '' : LANG + '/'}`;
const CHROME = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser';
const PORT = 9390;
const PROFILE = resolve(mkdtempSync(resolve(tmpdir(), 'visuel-')));
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
async function ouvrir(url, w, h, dsf){
  const { targetId } = await cdp.send('Target.createTarget',{url:'about:blank'});
  const { sessionId } = await cdp.send('Target.attachToTarget',{targetId,flatten:true});
  await cdp.send('Page.enable',{},sessionId);
  await cdp.send('Emulation.setDeviceMetricsOverride',{width:w,height:h,deviceScaleFactor:dsf,mobile:false},sessionId);
  const loaded = new Promise(r => cdp.on(m => { if(m.method==='Page.loadEventFired'&&m.sessionId===sessionId) r(); }));
  await cdp.send('Page.navigate',{url},sessionId);
  await loaded;
  return sessionId;
}
const evaluer = (s, expression) => cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},s).then(r => r.result.value);

/* ---- 1. la carte, date par date ---- */
const carte = await ouvrir(URL_PAGE, 1440, 1000, 2);
await sleep(3000);
await evaluer(carte, `(()=>{ const st=document.createElement('style'); st.textContent=
  '.map-toolbar,.map-mode,.map-legend,.zm-popup,.zm-marks{display:none!important}'+
  '.zm-viewport,.zm-mark,.zm-zone path{transition:none!important}'; document.head.appendChild(st); })()`);
const infos = await evaluer(carte, `JSON.stringify({
  dates: ZONES_HISTORY.map(e=>e.date),
  zones: ZONES_HISTORY.map(e=>e.zones.filter(z=>(z.cases||0)>0).length),
  sitreps: sortedSitreps().map(s=>[s.date, s.confirmed]),
  legende: [...document.querySelectorAll('.map-legend[data-mode="zones"] .legend-step')]
    .map(s=>[getComputedStyle(s.querySelector('.legend-swatch')).backgroundColor, s.textContent.trim()]),
  titreLegende: document.querySelector('.map-legend[data-mode="zones"] .title').textContent.trim(),
  locale: tr('locale'), mois: tr('months')
})`).then(JSON.parse);
const dates = infos.dates;
const d0 = new Date(dates[0]), d1 = new Date(dates[dates.length-1]);
const choisies = [];
for(let i=0;i<N;i++){
  const cible = new Date(d0.getTime() + (d1 - d0) * i / (N - 1)).toISOString().slice(0,10);
  const d = dates.filter(x => x <= cible).pop();
  if(!choisies.includes(d)) choisies.push(d);
}
const casA = date => { const k = infos.sitreps.filter(s => s[0] <= date).pop(); return k ? k[1] : null; };
const fmtN = n => n == null ? '—' : n.toLocaleString(infos.locale);
const dateLongue = iso => `${parseInt(iso.slice(8),10)} ${infos.mois[parseInt(iso.slice(5,7),10)-1]} ${iso.slice(0,4)}`;

/* Le cadre : l'emprise de TOUTES les zones touchees au dernier instantane,
   pour qu'aucune ne sorte de l'image — le zoom « epicentre » coupait celles
   de Kisangani, a l'ouest. Le meme cadre pour toutes les vignettes. */
const cadre = await evaluer(carte, `(()=>{
  const s=document.getElementById('timelineSlider'); s.value=${dates.length-1}; s.dispatchEvent(new Event('input'));
  let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;
  const sans = ${JSON.stringify(SANS)}, sansZones = ${JSON.stringify(SANS_ZONES.map(z => z.toLowerCase()))};
  document.querySelectorAll('.zm-zone:not(.is-0)').forEach(el=>{
    if(sans.includes(el.dataset.sub) || sansZones.includes(String(el.dataset.name||'').toLowerCase())) return;
    const b=String(el.dataset.box||'').split(/[\\s,]+/).map(Number); if(b.length<4||b.some(isNaN)) return;
    x0=Math.min(x0,b[0]); y0=Math.min(y0,b[1]); x1=Math.max(x1,b[0]+b[2]); y1=Math.max(y1,b[1]+b[3]); });
  return {x:x0,y:y0,w:x1-x0,h:y1-y0}; })()`);
console.log(`  cadre : ${cadre.w.toFixed(0)} x ${cadre.h.toFixed(0)} unites, depuis (${cadre.x.toFixed(0)}, ${cadre.y.toFixed(0)})`);

const vignettes = [];
for(const date of choisies){
  const i = dates.indexOf(date);
  await evaluer(carte, `(()=>{ const s=document.getElementById('timelineSlider'); s.value=${i}; s.dispatchEvent(new Event('input'));
    zoomToBox(${cadre.x}, ${cadre.y}, ${cadre.w}, ${cadre.h});
    if(${ZOOM}!==1||${DX}||${DY}){ const v=map.view; const w=v.w/${ZOOM}, h=v.h/${ZOOM};
      map.view={x:v.x+(v.w-w)/2+${DX}, y:v.y+(v.h-h)/2+${DY}, w, h}; applyView(false); } })()`);
  await sleep(400);
  /* On ne photographie que l'emprise des zones (plus une marge), pas tout le
     cadre carre de la carte : un cadre large et bas laissait un tiers de
     vide sous les zones. Les coins de l'emprise passent par la matrice
     ecran du groupe transforme, la vignette prend leur rapport. */
  const clip = await evaluer(carte, `(()=>{
    const svg=document.querySelector('svg.zonemap'); const r=svg.getBoundingClientRect();
    const m=map.viewport.getScreenCTM(); const pt=svg.createSVGPoint();
    const coin=(x,y)=>{ pt.x=x; pt.y=y; const q=pt.matrixTransform(m); return [q.x,q.y]; };
    const marge=${cadre.w}*0.05;
    const [x0,y0]=coin(${cadre.x}-marge, ${cadre.y}-marge), [x1,y1]=coin(${cadre.x}+${cadre.w}+marge, ${cadre.y}+${cadre.h}+marge);
    const X0=Math.max(r.left,x0), Y0=Math.max(r.top,y0), X1=Math.min(r.right,x1), Y1=Math.min(r.bottom,y1);
    return {x:X0, y:Y0+window.scrollY, width:X1-X0, height:Y1-Y0}; })()`);
  const { data } = await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{...clip,scale:2}},carte);
  /* Les zones touchees que le cadre laisse dehors, a CETTE date : la
     vignette le dit, sinon « 10 zones » avec six taches visibles ment. */
  const horsCadre = await evaluer(carte, `(()=>{
    const sans=${JSON.stringify(SANS)}, sansZones=${JSON.stringify(SANS_ZONES.map(z => z.toLowerCase()))};
    return [...document.querySelectorAll('.zm-zone:not(.is-0)')].filter(el=>
      sans.includes(el.dataset.sub) || sansZones.includes(String(el.dataset.name||'').toLowerCase())).length; })()`);
  vignettes.push({ date, png: data, zones: infos.zones[i], cas: casA(date), horsCadre, rapport: clip.height / clip.width });
  console.log(`  ${date} : ${infos.zones[i]} zones (${horsCadre} hors cadre), ${fmtN(casA(date))} cas`);
}

/* ---- 2. la composition ---- */
const T = LANG === 'fr' ? {
  eyebrow: '17ᵉ épidémie d’Ebola · République démocratique du Congo',
  titre: 'La propagation, zone de santé par zone de santé',
  cas: 'cas confirmés', zones: 'zones touchées', horsCadre: n => `dont ${n} hors cadre`, source: 'Sources : SitReps INSP', site: 'ebola-tracker.org',
  interactif: 'Carte interactive et curseur de temps sur ebola-tracker.org',
} : LANG === 'sw' ? {
  eyebrow: 'Mlipuko wa 17 wa Ebola · Jamhuri ya Kidemokrasia ya Kongo',
  titre: 'Jinsi mlipuko ulivyoenea, eneo la afya kwa eneo la afya',
  cas: 'visa vilivyothibitishwa', zones: 'maeneo yaliyoathirika', horsCadre: n => `${n} nje ya fremu`, source: 'Vyanzo: Ripoti za INSP', site: 'ebola-tracker.org',
  interactif: 'Ramani shirikishi yenye kitelezi cha muda kwenye ebola-tracker.org',
} : {
  eyebrow: '17th Ebola outbreak · Democratic Republic of the Congo',
  titre: 'How the outbreak spread, health zone by health zone',
  cas: 'confirmed cases', zones: 'zones affected', horsCadre: n => `${n} outside the frame`, source: 'Sources: INSP SitReps', site: 'ebola-tracker.org',
  interactif: 'Interactive map with a time slider at ebola-tracker.org',
};
const COLS = 3, ROWS = Math.ceil(vignettes.length / COLS);
const PANEL = N <= 3 ? 500 : (N <= 6 ? 470 : 400);
const GAP = 22, MARGE = 44;
const LARGEUR = MARGE * 2 + PANEL * COLS + GAP * (COLS - 1);
const html = `<!doctype html><html lang="${LANG}"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<style>
  :root{--bg:#FDFAF6;--ink:#272017;--ink-dim:#5B5148;--ink-faint:#8B8178;--line:#E6E0D8;--accent:#005073;--critical:#9E2F1F;}
  html,body{margin:0;background:var(--bg);color:var(--ink);font-family:'Public Sans',system-ui,sans-serif;}
  .page{width:${LARGEUR}px;padding:${MARGE}px;box-sizing:border-box;}
  .eyebrow{font-size:15px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-dim);display:flex;align-items:center;gap:10px;}
  .eyebrow::before{content:"";width:10px;height:10px;border-radius:50%;background:var(--critical);}
  h1{font-family:'Source Serif 4',Georgia,serif;font-weight:600;font-size:${N<=3?40:36}px;line-height:1.15;margin:10px 0 26px;}
  .grille{display:grid;grid-template-columns:repeat(${COLS},${PANEL}px);gap:${GAP + 14}px ${GAP}px;}
  .v .date{font-family:'Source Serif 4',Georgia,serif;font-size:${N<=3?24:21}px;font-weight:600;color:var(--accent);}
  .v .stats{font-size:${N<=3?14:13}px;color:var(--ink-dim);margin:2px 0 8px;font-variant-numeric:tabular-nums;}
  .v .stats b{color:var(--ink);font-weight:600;}
  .v .stats .hc{color:var(--ink-faint);}
  .v img{display:block;width:${PANEL}px;height:${Math.round(PANEL * (vignettes[0].rapport || 1))}px;object-fit:cover;border:1px solid var(--line);border-radius:8px;background:#F4F1EC;}
  .pied{display:flex;justify-content:space-between;align-items:flex-end;margin-top:26px;padding-top:16px;border-top:1px solid var(--line);}
  .legende .t{font-size:12px;font-weight:700;margin-bottom:6px;}
  .legende .l{display:flex;gap:14px;font-size:12px;color:var(--ink-dim);}
  .legende .l span{display:flex;align-items:center;gap:5px;}
  .legende i{width:12px;height:12px;border-radius:3px;display:inline-block;}
  .src{text-align:right;font-size:13px;color:var(--ink-faint);line-height:1.5;}
  .src b{color:var(--accent);font-weight:700;font-size:15px;}
</style></head><body><div class="page">
  <div class="eyebrow">${T.eyebrow}</div>
  <h1>${T.titre}</h1>
  <div class="grille">${vignettes.map(v => `
    <div class="v"><div class="date">${dateLongue(v.date)}</div>
      <div class="stats"><b>${fmtN(v.cas)}</b> ${T.cas} · <b>${v.zones}</b> ${T.zones}${v.horsCadre ? ` <span class="hc">(${T.horsCadre(v.horsCadre)})</span>` : ''}</div>
      <img src="data:image/png;base64,${v.png}" alt=""></div>`).join('')}
  </div>
  <div class="pied">
    <div class="legende"><div class="t">${infos.titreLegende}</div>
      <div class="l">${infos.legende.map(([c,l]) => `<span><i style="background:${c}"></i>${l}</span>`).join('')}</div></div>
    <div class="src">${(SANS.length || SANS_ZONES.length) ? (LANG === 'fr' ? 'Hors cadre : ' : LANG === 'sw' ? 'Nje ya fremu: ' : 'Outside the frame: ') + [...SANS, ...SANS_ZONES].join(', ') + '<br>' : ''}${T.interactif}<br>${T.source} · <b>${T.site}</b></div>
  </div>
</div></body></html>`;
const fichierHtml = resolve(PROFILE, 'composition.html');
writeFileSync(fichierHtml, html);
const compo = await ouvrir('file://' + fichierHtml, LARGEUR, 1200, 1);
await evaluer(compo, 'document.fonts.ready.then(()=>true)');
await sleep(600);
const hauteur = await evaluer(compo, 'document.querySelector(".page").getBoundingClientRect().height');
await cdp.send('Emulation.setDeviceMetricsOverride',{width:LARGEUR,height:Math.ceil(hauteur),deviceScaleFactor:1,mobile:false},compo);
await sleep(300);
const { data } = await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,
  clip:{x:0,y:0,width:LARGEUR,height:Math.ceil(hauteur),scale:1}},compo);
mkdirSync(dirname(SORTIE), { recursive:true });
writeFileSync(SORTIE, Buffer.from(data,'base64'));
console.log(`${SORTIE} ecrit (${LARGEUR}x${Math.ceil(hauteur)})`);
cdp.close(); chrome.kill();
