'use strict';
/* Tableau de bord (/dashboard/, 9 octobre 2026) : toutes les donnees sur un
   seul ecran, filtre par province (#ituri, #nord-kivu...). Page a part : elle
   n'utilise ni app.js ni site.css, et lit directement les fichiers de data/,
   comme les autres pages. Les adresses (pages province, pays, accueil) et la
   langue viennent du generateur, dans le bloc JSON #dbConfig.

   Regles reprises du site, a ne pas perdre :
   - nouveaux cas et deces par jour : ecart de cumul d'un bulletin au suivant,
     revision a la baisse ramenee a zero, rattrapages des 22 et 30 juillet en
     teinte claire (partsQuotidiennes() d'app.js) ;
   - deces du jour d'une province : ecart de cumul, JAMAIS la somme des deces
     communautaires et intra-CTE (CLAUDE.md, pieges connus) ;
   - lieu du deces : des parts par semaine, pas des volumes ;
   - vaccination : dernier cumul de chaque province, le dernier total national
     publie l'emporte tant que la somme ne le depasse pas ;
   - ce que la source ne publie pas s'affiche « non publie », jamais 0. */

const CFG = JSON.parse(document.getElementById('dbConfig').textContent);
const LANG = CFG.lang in { fr:1, en:1, sw:1 } ? CFG.lang : 'fr';

/* Textes de la page, par langue. Le swahili est a faire relire. */
const TXT = {
  fr: {
    mois:['janv.','févr.','mars','avr.','mai','juin','juil.','août','sept.','oct.','nov.','déc.'],
    modeCumul:'cas confirmés cumulés', mode30:'nouveaux cas, 30 derniers jours', mode24:'nouveaux cas, 24 h',
    rdc:'RDC', rdcEntiere:'RDC entière',
    situation:(n, d, p, j) => `SitRep INSP <b>n° ${n}</b> · situation au <b>${d}</b><br>publié le ${p} · ${j}<sup>e</sup> jour depuis la déclaration`,
    k24:'en 24 h', kCas:'Cas confirmés', kDeces:'Décès', kLet:'Létalité', kLetD:'décès / cas confirmés',
    kMoy:'Cas par jour, 7 j', kMoyD:'semaine précédente :', kGueris:'Guéris', kGuerisD:'cumul publié', kGuerisNon:'Non publié par province',
    kZones:'Zones touchées', kZonesProv:'dans la province', kZonesNat:n => `dans ${n} provinces`, kNonPub:'Non publié',
    kContacts:'Contacts suivis', kContactsD:'vus sur contacts à suivre', kContactsNon:'Non publié pour cette province',
    kVac:'Personnes vaccinées', kVacD:'cumul', kVacNon:'Aucune vaccination publiée ici', au:d => ` · au ${d}`,
    carteAria:'Carte des zones de santé', bCas:'cas', bDeces:'décès',
    carteTitre:'Zones de santé touchées', carteProv:p => `Zones de santé — ${p}`,
    thProv:'Province', thCas:'Cas', th24:'24 h', th7:'7 j', thDeces:'Décès', thLet:'Létalité', th30:'30 j', cliquer:'cliquer pour filtrer',
    thCt:'Contacts vus', thHosp:'En CTE', thOcc:'Occupation', thPos:'Positivité',
    note:'7 j : 7 derniers bulletins · 30 j : nouveaux cas par bulletin · Riposte : provinces de 10 cas et plus · — : non publié',
    depuis:d => `30 j depuis le ${d}`, trenteJ:'30 jours',
    zonesProv:(n, d) => `Zones de santé <small>${n} touchées · par cas cumulés · ${d}</small>`,
    zonesNat:d => `Zones les plus actives <small>${d}</small>`,
    zZone:'Zone', zCumul:'Cumul', zAucun:'Aucun nouveau cas sur 30 jours.', horsRdc:'Hors RDC', casN:n => `${n} cas`,
    parBulletin:'par bulletin', rattrapage:'rattrapage', coupe:' (coupé)', moy7:'moyenne 7 j',
    lNouveauxCas:'Nouveaux cas', lNouveauxDeces:'Nouveaux décès', lMoy:'Moyenne 7 j',
    pas:{jour:['J','Par jour'], semaine:['S','Par semaine'], mois:['M','Par mois']},
    gCas:{jour:'Cas par jour', semaine:'Cas par semaine', mois:'Cas par mois'},
    gDeces:{jour:'Décès par jour', semaine:'Décès par semaine', mois:'Décès par mois'},
    enCours:'en cours', partiel:'période incomplète',
    lieuPeu:'Trop peu de décès ventilés par lieu pour une proportion.', enCom:'en communauté', enCentre:'en centre',
    lieuPart:(p, d) => `${p} % en communauté depuis le ${d}`, sem:'sem.', lCom:'En communauté (%)', lCentre:'En centre de traitement (%)',
    alNon:'Pas d’alertes publiées pour cette province.', recues:'reçues', validees:'validées',
    alSem:(d, r, v) => `semaine du ${d} : ${r} / ${v}`, lRecues:'Reçues', lValidees:'Validées',
    laboNon:'Pas de résultats de laboratoire publiés pour cette province.', positifs:'positifs', positivite:'positivité',
    le:d => `le ${d}`, lPos:'Positivité (%)', lPositifs:'Échantillons positifs',
    ctNon:'Pas de suivi des contacts publié pour cette province.', ctPart:'part des contacts vus', lCt:'Contacts vus (%)',
    accueil:'Accueil', accueilD:'Vue d’ensemble de l’épidémie', retour:'Retour à l’accueil', erreur:'Données indisponibles pour le moment.',
  },
  en: {
    mois:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    modeCumul:'cumulative confirmed cases', mode30:'new cases, last 30 days', mode24:'new cases, 24 h',
    rdc:'DRC', rdcEntiere:'Whole DRC',
    situation:(n, d, p, j) => `INSP SitRep <b>no. ${n}</b> · situation as of <b>${d}</b><br>published ${p} · day ${j} since the declaration`,
    k24:'in 24 h', kCas:'Confirmed cases', kDeces:'Deaths', kLet:'Fatality rate', kLetD:'deaths / confirmed cases',
    kMoy:'Cases per day, 7 d', kMoyD:'previous week:', kGueris:'Recovered', kGuerisD:'published total', kGuerisNon:'Not published by province',
    kZones:'Affected zones', kZonesProv:'in the province', kZonesNat:n => `in ${n} provinces`, kNonPub:'Not published',
    kContacts:'Contacts followed', kContactsD:'seen out of contacts to follow', kContactsNon:'Not published for this province',
    kVac:'People vaccinated', kVacD:'total', kVacNon:'No vaccination published here', au:d => ` · as of ${d}`,
    carteAria:'Map of health zones', bCas:'cases', bDeces:'deaths',
    carteTitre:'Affected health zones', carteProv:p => `Health zones — ${p}`,
    thProv:'Province', thCas:'Cases', th24:'24 h', th7:'7 d', thDeces:'Deaths', thLet:'Fatality', th30:'30 d', cliquer:'click to filter',
    thCt:'Contacts seen', thHosp:'In ETC', thOcc:'Occupancy', thPos:'Positivity',
    note:'7 d: last 7 bulletins · 30 d: new cases per bulletin · Response: provinces with 10+ cases · —: not published',
    depuis:d => `30 d since ${d}`, trenteJ:'30 days',
    zonesProv:(n, d) => `Health zones <small>${n} affected · by total cases · ${d}</small>`,
    zonesNat:d => `Most active zones <small>${d}</small>`,
    zZone:'Zone', zCumul:'Total', zAucun:'No new cases in 30 days.', horsRdc:'Outside the DRC', casN:n => `${n} case${n === '1' ? '' : 's'}`,
    parBulletin:'per bulletin', rattrapage:'catch-up', coupe:' (cut)', moy7:'7-day average',
    lNouveauxCas:'New cases', lNouveauxDeces:'New deaths', lMoy:'7-day average',
    pas:{jour:['D','Per day'], semaine:['W','Per week'], mois:['M','Per month']},
    gCas:{jour:'Cases per day', semaine:'Cases per week', mois:'Cases per month'},
    gDeces:{jour:'Deaths per day', semaine:'Deaths per week', mois:'Deaths per month'},
    enCours:'in progress', partiel:'incomplete period',
    lieuPeu:'Too few deaths broken down by place for a proportion.', enCom:'in the community', enCentre:'in a centre',
    lieuPart:(p, d) => `${p}% in the community since ${d}`, sem:'wk', lCom:'In the community (%)', lCentre:'In a treatment centre (%)',
    alNon:'No alerts published for this province.', recues:'received', validees:'validated',
    alSem:(d, r, v) => `week of ${d}: ${r} / ${v}`, lRecues:'Received', lValidees:'Validated',
    laboNon:'No laboratory results published for this province.', positifs:'positive', positivite:'positivity',
    le:d => `on ${d}`, lPos:'Positivity (%)', lPositifs:'Positive samples',
    ctNon:'No contact follow-up published for this province.', ctPart:'share of contacts seen', lCt:'Contacts seen (%)',
    accueil:'Home', accueilD:'Overview of the outbreak', retour:'Back to the home page', erreur:'Data unavailable for now.',
  },
  sw: {
    mois:['Jan','Feb','Mac','Apr','Mei','Jun','Jul','Ago','Sep','Okt','Nov','Des'],
    modeCumul:'visa vilivyothibitishwa kwa jumla', mode30:'visa vipya, siku 30 zilizopita', mode24:'visa vipya, saa 24',
    rdc:'DRC', rdcEntiere:'DRC nzima',
    situation:(n, d, p, j) => `SitRep ya INSP <b>na. ${n}</b> · hali kufikia <b>${d}</b><br>ilichapishwa ${p} · siku ya ${j} tangu kutangazwa`,
    k24:'ndani ya saa 24', kCas:'Visa', kDeces:'Vifo', kLet:'Kiwango cha vifo', kLetD:'vifo / visa vilivyothibitishwa',
    kMoy:'Visa kwa siku, siku 7', kMoyD:'wiki iliyopita:', kGueris:'Waliopona', kGuerisD:'jumla iliyochapishwa', kGuerisNon:'Haichapishwi kwa jimbo',
    kZones:'Maeneo ya afya', kZonesProv:'katika jimbo', kZonesNat:n => `katika majimbo ${n}`, kNonPub:'Haijachapishwa',
    kContacts:'Ufuatiliaji', kContactsD:'watu wa karibu walioonekana', kContactsNon:'Haijachapishwa kwa jimbo hili',
    kVac:'Waliochanjwa', kVacD:'jumla', kVacNon:'Hakuna chanjo iliyochapishwa hapa', au:d => ` · hadi ${d}`,
    carteAria:'Ramani ya maeneo ya afya', bCas:'visa', bDeces:'vifo',
    carteTitre:'Maeneo ya afya yaliyoathirika', carteProv:p => `Maeneo ya afya — ${p}`,
    thProv:'Jimbo', thCas:'Visa', th24:'Saa 24', th7:'Siku 7', thDeces:'Vifo', thLet:'Kiwango', th30:'Siku 30', cliquer:'bofya kuchuja',
    thCt:'Walioonekana', thHosp:'Katika CTE', thOcc:'Vitanda', thPos:'Chanya',
    note:'Siku 7: ripoti 7 za mwisho · Siku 30: visa vipya kwa kila ripoti · Mapambano: majimbo yenye visa 10 au zaidi · —: haijachapishwa',
    depuis:d => `siku 30 tangu ${d}`, trenteJ:'siku 30',
    zonesProv:(n, d) => `Maeneo ya afya <small>${n} yaliyoathirika · kwa visa vya jumla · ${d}</small>`,
    zonesNat:d => `Maeneo yenye visa vingi zaidi <small>${d}</small>`,
    zZone:'Eneo', zCumul:'Jumla', zAucun:'Hakuna kisa kipya katika siku 30.', horsRdc:'Nje ya DRC', casN:n => `visa ${n}`,
    parBulletin:'kwa kila ripoti', rattrapage:'ucheleweshaji', coupe:' (imekatwa)', moy7:'wastani wa siku 7',
    lNouveauxCas:'Visa vipya', lNouveauxDeces:'Vifo vipya', lMoy:'Wastani wa siku 7',
    pas:{jour:['S','Kwa siku'], semaine:['W','Kwa wiki'], mois:['M','Kwa mwezi']},
    gCas:{jour:'Visa kwa siku', semaine:'Visa kwa wiki', mois:'Visa kwa mwezi'},
    gDeces:{jour:'Vifo kwa siku', semaine:'Vifo kwa wiki', mois:'Vifo kwa mwezi'},
    enCours:'inaendelea', partiel:'kipindi kisichokamilika',
    lieuPeu:'Vifo vichache mno vilivyogawanywa kwa mahali.', enCom:'katika jamii', enCentre:'katika kituo',
    lieuPart:(p, d) => `${p} % katika jamii tangu ${d}`, sem:'wiki', lCom:'Katika jamii (%)', lCentre:'Katika kituo cha matibabu (%)',
    alNon:'Hakuna tahadhari zilizochapishwa kwa jimbo hili.', recues:'zilizopokelewa', validees:'zilizothibitishwa',
    alSem:(d, r, v) => `wiki ya ${d}: ${r} / ${v}`, lRecues:'Zilizopokelewa', lValidees:'Zilizothibitishwa',
    laboNon:'Hakuna matokeo ya maabara yaliyochapishwa kwa jimbo hili.', positifs:'chanya', positivite:'kiwango cha chanya',
    le:d => `tarehe ${d}`, lPos:'Kiwango cha chanya (%)', lPositifs:'Sampuli chanya',
    ctNon:'Hakuna ufuatiliaji wa watu wa karibu uliochapishwa kwa jimbo hili.', ctPart:'sehemu ya watu wa karibu walioonekana', lCt:'Walioonekana (%)',
    accueil:'Mwanzo', accueilD:'Muhtasari wa mlipuko', retour:'Rudi mwanzo', erreur:'Takwimu hazipatikani kwa sasa.',
  },
};
const T = k => (TXT[LANG] && TXT[LANG][k] !== undefined) ? TXT[LANG][k] : TXT.fr[k];

/* ======================================================================
   Donnees
   ====================================================================== */
const COULEURS = {"Ituri":"#005E82","Nord-Kivu":"#A06F30","Haut-Uélé":"#327957","Tshopo":"#6B5CA5",
                  "Sud-Kivu":"#5A544C","Bas-Uélé":"#993A2E","Sud-Ubangi":"#B0487D"};
const SLUGS = {"Ituri":"ituri","Nord-Kivu":"nord-kivu","Haut-Uélé":"haut-uele","Tshopo":"tshopo",
               "Sud-Kivu":"sud-kivu","Bas-Uélé":"bas-uele","Sud-Ubangi":"sud-ubangi"};
const DECLARATION = '2026-05-15';
/* Les deux rattrapages administratifs documentes dans app.js (22 et 30
   juillet) : la part du jour n'est connue qu'au niveau national et pour les
   cas ; le reste passe en teinte claire. */
const RATTRAPAGE = {'2026-07-22':97, '2026-07-30':73};
const SEUILS = { cumul:[10,50,200,500,1000], j30:[5,20,50,100,200], j1:[1,3,5,10,20] };
const MODE_TITRE = { cumul:T('modeCumul'), j30:T('mode30'), j1:T('mode24') };

/* Les nombres comme le reste du site : espace fine insecable en francais,
   virgule des milliers en anglais et en swahili ; « 48,2 % », « 48.2% ». */
const SEP = LANG === 'fr' ? ' ' : ',', DEC = LANG === 'fr' ? ',' : '.';
const fmt = n => (n === null || n === undefined) ? '—' : String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, SEP);
const dec1 = n => (Math.round(n * 10) / 10).toFixed(1).replace('.', DEC);
const pct = n => (n === null || n === undefined) ? '—' : dec1(n) + (LANG === 'en' ? '%' : ' %');
const MOIS = T('mois');
const dateC = iso => { const [, m, j] = iso.split('-'); return parseInt(j, 10) + ' ' + MOIS[parseInt(m, 10) - 1]; };
const dateL = iso => dateC(iso) + ' ' + iso.slice(0, 4);
const jours = (a, b) => Math.round((new Date(b + 'T12:00:00') - new Date(a + 'T12:00:00')) / 864e5);
const lundi = iso => { const d = new Date(iso + 'T12:00:00'); d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
const norm = t => String(t || '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[-_'’.]/g, ' ').toLowerCase().replace(/\s+/g, '');
const parDate = (a, b) => a.date < b.date ? -1 : a.date > b.date ? 1 : 0;
const esc = t => String(t).replace(/[&<>"]/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;'}[c]));

async function charger(chemin){
  const r = await fetch(chemin, {cache:'no-store'});
  if(!r.ok) throw new Error(chemin + ' : ' + r.status);
  return r.json();
}

let D = {};          // toutes les donnees
let PROV = null;     // province filtree, null = RDC entiere
let MODE = 'cumul';  // coloriage de la carte
const PAS = {cas:'jour', deces:'jour'};   // pas de temps de chaque graphique (jour, semaine, mois)
const charts = {};

/* Nouveaux cas (ou deces) d'un releve au suivant, comme partsQuotidiennes()
   d'app.js : une revision a la baisse vaut zero, la part de rattrapage est
   separee (cas, niveau national seulement ; ailleurs toute la journee passe en
   teinte claire). */
function quotidien(serie, champ, national){
  const out = []; let prev = null;
  for(const r of serie){
    const v = r[champ];
    if(v === null || v === undefined){ continue; }
    if(prev !== null){
      const delta = Math.max(0, v - prev);
      const jour = RATTRAPAGE[r.date];
      let rapporte = delta, rattrapage = 0;
      if(jour !== undefined){
        const part = (champ === 'confirmed' && national) ? jour : 0;
        rapporte = Math.min(part, delta); rattrapage = Math.max(0, delta - part);
      }
      out.push({date:r.date, rapporte, rattrapage, total:delta});
    }
    prev = v;
  }
  return out;
}

/* Les memes nouveaux cas (ou deces) par semaine (lundi-dimanche) ou par mois,
   comme agregeNouveauxCas() d'app.js. Le rattrapage du 30 juillet couvre les
   28 et 29 (bulletins 075 et 076 absents) : une periode qui contient ces trois
   jours le compte comme le sien, en couleur pleine. Celui du 22 juillet n'a pas
   d'empan connu : il reste en teinte claire a toutes les granularites. Une
   periode que la serie ne couvre pas en entier (mai commence le 14, la periode
   en cours n'est pas finie) est marquee « partielle ». */
const EMPAN_RATTRAPAGE = {'2026-07-30':['2026-07-28', '2026-07-30']};
const debutMois = iso => iso.slice(0, 8) + '01';
const finMois = iso => { const d = new Date(iso + 'T12:00:00'); d.setMonth(d.getMonth() + 1, 0);
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
const finSemaine = iso => { const d = new Date(iso + 'T12:00:00'); d.setDate(d.getDate() + 6);
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
function agrege(q, pas, premiere){
  if(pas === 'jour') return q;
  const mois = pas === 'mois';
  const derniere = q.length ? q[q.length - 1].date : null;
  const map = new Map();
  for(const x of q){
    const debut = mois ? debutMois(x.date) : lundi(x.date);
    const fin = mois ? finMois(debut) : finSemaine(debut);
    const p = map.get(debut) || {date:debut, fin, rapporte:0, rattrapage:0, total:0};
    p.rapporte += x.rapporte; p.total += x.total;
    const e = EMPAN_RATTRAPAGE[x.date];
    if(e && e[0] >= debut && e[1] <= fin) p.rapporte += x.rattrapage;
    else p.rattrapage += x.rattrapage;
    map.set(debut, p);
  }
  return [...map.values()].sort(parDate).map(p => Object.assign(p, {
    partiel: (premiere && p.date < premiere) || (derniere && p.fin > derniere),
    enCours: derniere && p.fin > derniere}));
}

function serieProvince(nom){
  return D.provHist.map(h => {
    const p = h.provinces.find(x => x.name === nom);
    return {date:h.date, confirmed:p ? p.confirmed : null, deaths:p ? p.deaths : null};
  }).filter(x => x.confirmed !== null);
}

/* Zones : cumul actuel, 24 h (bulletin), et 30 jours (cumul actuel moins le
   dernier releve d'il y a au moins 30 jours). */
function zonesCalculees(){
  const fin = D.zonesHist[D.zonesHist.length - 1];
  const cible = new Date(fin.date + 'T12:00:00'); cible.setDate(cible.getDate() - 30);
  const cIso = cible.toISOString().slice(0, 10);
  let avant = null;
  for(const z of D.zonesHist){ if(z.date <= cIso) avant = z; }
  const ancien = {};
  if(avant) avant.zones.forEach(z => { ancien[z.province + '|' + norm(z.name)] = z.cases || 0; });
  const j24 = {};
  D.latest.healthZones.forEach(z => { j24[z.province + '|' + norm(z.name)] = z.newCases24h; });
  return {
    depuis: avant ? avant.date : null,
    zones: fin.zones.map(z => {
      const k = z.province + '|' + norm(z.name);
      return {name:z.name, province:z.province, cases:z.cases || 0, deaths:z.deaths,
              j30: avant ? Math.max(0, (z.cases || 0) - (ancien[k] || 0)) : null,
              j1: j24[k] === undefined ? null : j24[k]};
    })
  };
}

/* Vaccination : la somme du dernier cumul connu de chaque province ; le
   dernier total national publie l'emporte tant que la somme ne le depasse
   pas (meme regle que la page Riposte). */
function vaccination(nom){
  const dernier = {}; let nat = null;
  for(const p of D.piliers.parDate){
    const v = p.vaccination || {};
    for(const [prov, x] of Object.entries(v.provinces || {})){
      if(x.cumul !== null && x.cumul !== undefined) dernier[prov] = {cumul:x.cumul, date:p.date};
    }
    if(v.national !== null && v.national !== undefined) nat = {cumul:v.national, date:p.date};
  }
  if(nom) return dernier[nom] || null;
  const vals = Object.values(dernier);
  if(!vals.length) return nat;
  const total = vals.reduce((s, x) => s + x.cumul, 0);
  const date = vals.map(x => x.date).sort().pop();
  if(nat && nat.cumul > total) return nat;
  return {cumul:total, date};
}

/* Dernier releve d'une serie qui porte une valeur pour la province (ou le
   total). */
function dernierReleve(points, lire){
  for(let i = points.length - 1; i >= 0; i--){
    const v = lire(points[i]);
    if(v !== null && v !== undefined) return {v, date:points[i].date};
  }
  return null;
}

/* ======================================================================
   Rendu
   ====================================================================== */
function sparkline(valeurs, couleur, w = 54, h = 20){
  const v = valeurs.filter(x => x !== null && x !== undefined);
  if(v.length < 2) return '';
  const max = Math.max(...v, 1), min = Math.min(...v, 0);
  const pts = v.map((x, i) => [(i / (v.length - 1)) * w, h - ((x - min) / (max - min || 1)) * h]);
  return `<svg class="sp" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><polyline fill="none" stroke="${couleur}" stroke-width="1.4" stroke-linejoin="round" points="${pts.map(p => p.map(n => n.toFixed(1)).join(',')).join(' ')}"/></svg>`;
}

function renderFiltres(){
  const noms = [null, ...D.provinces.map(p => p.name)];
  document.getElementById('filtres').innerHTML = noms.map(n =>
    `<button type="button" data-prov="${n || ''}" aria-pressed="${(n || null) === PROV}">${n ? `<i style="background:${COULEURS[n] || '#999'}"></i>${esc(n)}` : T('rdcEntiere')}</button>`).join('');
}

function renderSituation(){
  const m = D.latest.meta;
  document.getElementById('situation').innerHTML =
    T('situation')(parseInt(m.sitrepNumber, 10), dateL(m.reportingDate), dateC(m.publicationDate || m.reportingDate), jours(DECLARATION, m.reportingDate));
}

function kpi(classe, libelle, valeur, detail, spark){
  return `<div class="kpi ${classe}"><div class="l">${libelle}</div><div class="v">${valeur}</div><div class="d">${detail || '&nbsp;'}</div>${spark || ''}</div>`;
}
function kpiVide(libelle, texte){
  return `<div class="kpi is-vide"><div class="l">${libelle}</div><div class="v">${texte}</div></div>`;
}
const auDate = date => date && date !== D.latest.meta.reportingDate ? T('au')(dateC(date)) : '';

function renderKpis(){
  const nat = D.latest.national, date = D.latest.meta.reportingDate;
  const p = PROV ? D.provinces.find(x => x.name === PROV) : null;
  const serie = PROV ? serieProvince(PROV) : D.sitreps;
  const q = quotidien(serie, 'confirmed', !PROV).slice(-30).map(x => x.total);
  const cumul = serie.slice(-60);
  const h = [];

  const cas = p ? p.confirmed : nat.confirmed, deces = p ? p.deaths : nat.deaths;
  const casJ = p ? p.newCases24h : nat.newCases24h;
  // Province : l'ecart de cumul entre les deux derniers bulletins. Jamais la
  // somme des deces communautaires et intra-CTE du jour (CLAUDE.md, pieges).
  const derD = quotidien(serie, 'deaths', !PROV).pop();
  const decesJ = p ? (derD && derD.date === date ? derD.total : null) : nat.newDeaths24h;
  h.push(kpi('is-cas', T('kCas'), fmt(cas), `<b>+${fmt(casJ)}</b> ${T('k24')}`, sparkline(cumul.map(x => x.confirmed), 'var(--cas)')));
  h.push(kpi('is-deces', T('kDeces'), fmt(deces), `<b>+${fmt(decesJ)}</b> ${T('k24')}`, sparkline(cumul.map(x => x.deaths), 'var(--deces)')));
  h.push(kpi('', T('kLet'), pct(p ? p.cfr : nat.cfr), T('kLetD')));
  const moy7 = q.slice(-7).reduce((s, x) => s + x, 0) / Math.max(1, q.slice(-7).length);
  const moyAv = q.slice(-14, -7).reduce((s, x) => s + x, 0) / Math.max(1, q.slice(-14, -7).length);
  // Sous 10, une decimale : 0,9 cas par jour ne doit pas devenir 1.
  const moyF = v => v >= 10 ? fmt(v) : dec1(v);
  h.push(kpi('is-cas', T('kMoy'), moyF(moy7), `${moy7 >= moyAv ? '▲' : '▼'} ${T('kMoyD')} ${moyF(moyAv)}`, sparkline(q, 'var(--cas)')));
  if(!p) h.push(kpi('is-gueris', T('kGueris'), fmt(nat.recovered), T('kGuerisD')));
  else h.push(kpiVide(T('kGueris'), T('kGuerisNon')));
  const zi = p ? p.healthZonesAffected : nat.healthZonesAffected;
  h.push(zi ? kpi('', T('kZones'), `${fmt(zi.n)}<span class="sur"> / ${fmt(zi.total)}</span>`,
                  p ? T('kZonesProv') : T('kZonesNat')(fmt(nat.provincesAffected))) : kpiVide(T('kZones'), T('kNonPub')));

  const lireCt = x => PROV ? ((x.provinces || {})[PROV] || {}).taux : x.contactsFollowUpRate;
  const ct = dernierReleve(D.contacts, lireCt);
  h.push(ct ? kpi('', T('kContacts'), pct(ct.v), T('kContactsD') + auDate(ct.date), sparkline(D.contacts.slice(-30).map(lireCt), 'var(--ink-dim)'))
            : kpiVide(T('kContacts'), T('kContactsNon')));
  const vac = vaccination(PROV);
  h.push(vac ? kpi('', T('kVac'), fmt(vac.cumul), T('kVacD') + auDate(vac.date)) : kpiVide(T('kVac'), T('kVacNon')));
  document.getElementById('kpis').innerHTML = h.join('');
}

/* ---- carte ---- */
let SVG = null, ZONES_CALC = null;
function construireCarte(){
  const g = D.geo;
  const chemins = g.zones.map(z => `<path d="${z.d}" data-k="${z.key}" data-p="${z.province}"></path>`).join('');
  document.getElementById('carte').insertAdjacentHTML('afterbegin',
    `<svg viewBox="${g.viewBox}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${T('carteAria')}">${chemins}</svg>`);
  SVG = document.querySelector('#carte svg');
  const bulle = document.getElementById('bulle');
  SVG.addEventListener('mousemove', e => {
    const el = e.target.closest('path.touche');
    if(!el){ bulle.style.display = 'none'; return; }
    const z = el.__z;
    bulle.innerHTML = `<b>${esc(z.name)}</b> · ${esc(z.province)}<br>${fmt(z.cases)} ${T('bCas')} · ${fmt(z.deaths)} ${T('bDeces')}<br>` +
      `${T('th30')} : +${fmt(z.j30)} · ${T('th24')} : +${fmt(z.j1)}`;
    bulle.style.display = 'block';
    bulle.style.left = Math.min(e.clientX + 14, innerWidth - 250) + 'px';
    bulle.style.top = (e.clientY + 14) + 'px';
  });
  SVG.addEventListener('mouseleave', () => { bulle.style.display = 'none'; });
  SVG.addEventListener('click', e => {
    const el = e.target.closest('path.touche');
    if(el) choisir(el.__z.province === PROV ? null : el.__z.province);
  });
}

function palier(v, seuils){
  if(!v) return 0;
  let i = 0; while(i < seuils.length && v >= seuils[i]) i++;
  return i + 1;
}

// Le fond de carte ecrit « Haut-Uele », « Bas-Uele » : on compare les cles.
const boite = nom => { const k = Object.keys(D.geo.provinceBoxes).find(x => norm(x) === norm(nom)); return k ? D.geo.provinceBoxes[k] : null; };

function renderCarte(){
  const alias = Object.assign({}, D.geo.aliases || {}, {gety:'gethy'});
  const parCle = {};
  ZONES_CALC.zones.forEach(z => { const k = norm(z.name); parCle[alias[k] || k] = z; });
  const seuils = SEUILS[MODE];
  SVG.querySelectorAll('path').forEach(el => {
    const z = parCle[el.dataset.k];
    const v = z ? (MODE === 'cumul' ? z.cases : z[MODE]) : 0;
    const n = z && z.cases > 0 ? palier(v, seuils) : 0;
    el.style.fill = n ? `var(--m${n})` : 'var(--m0)';
    el.classList.toggle('touche', !!(z && z.cases > 0));
    el.__z = z;
    el.classList.toggle('hors', !!PROV && norm(el.dataset.p) !== norm(PROV));
  });
  // Cadrage : la boite de la province choisie, ou celle de toutes les
  // provinces touchees.
  let box;
  if(PROV && boite(PROV)){
    const [x, y, w, h] = boite(PROV); const m = Math.max(w, h) * .12;
    box = [x - m, y - m, w + 2 * m, h + 2 * m];
  } else {
    const bs = D.provinces.map(p => boite(p.name)).filter(Boolean);
    const x0 = Math.min(...bs.map(b => b[0])), y0 = Math.min(...bs.map(b => b[1]));
    const x1 = Math.max(...bs.map(b => b[0] + b[2])), y1 = Math.max(...bs.map(b => b[1] + b[3]));
    box = [x0 - 15, y0 - 15, x1 - x0 + 30, y1 - y0 + 30];
  }
  animerViewBox(box);
  const cases = seuils.map((_, i) => `<i style="background:var(--m${i + 1})"></i>`).join('') + `<i style="background:var(--m${seuils.length + 1})"></i>`;
  document.getElementById('legende').innerHTML = `<span>${MODE_TITRE[MODE]}</span> <span>1</span>${cases}<span>${fmt(seuils[seuils.length - 1])}+</span>`;
  document.getElementById('carteTitre').textContent = PROV ? T('carteProv')(PROV) : T('carteTitre');
}

let vbAnim = null;
function animerViewBox(cible){
  const actuel = (SVG.getAttribute('viewBox') || '').split(/\s+/).map(Number);
  if(actuel.length !== 4 || matchMedia('(prefers-reduced-motion: reduce)').matches){
    SVG.setAttribute('viewBox', cible.join(' ')); return;
  }
  cancelAnimationFrame(vbAnim);
  const t0 = performance.now(), duree = 450;
  const pas = t => {
    const k = Math.min(1, (t - t0) / duree), e = 1 - Math.pow(1 - k, 3);
    SVG.setAttribute('viewBox', actuel.map((a, i) => a + (cible[i] - a) * e).join(' '));
    if(k < 1) vbAnim = requestAnimationFrame(pas);
  };
  vbAnim = requestAnimationFrame(pas);
}

/* ---- tableau des provinces et de la riposte ---- */
function renderTableau(){
  /* Echelle commune aux sept provinces (9 octobre 2026) : la plus haute
     journee de toutes fixe la hauteur. Une journee a 1 ou 2 cas garde un
     trait d'un pixel, sans quoi les petites provinces disparaitraient. */
  const fen = p => quotidien(serieProvince(p.name), 'confirmed', false)
    .filter(x => !ZONES_CALC.depuis || x.date > ZONES_CALC.depuis).map(x => x.total);
  const maxCommun = Math.max(1, ...D.provinces.flatMap(fen));
  const lignes = D.provinces.map(p => {
    const q = quotidien(serieProvince(p.name), 'confirmed', false);
    const sept = q.slice(-7).reduce((a, x) => a + x.total, 0);
    const sp = fen(p);
    const haut = v => v ? Math.max(1, v / maxCommun * 18) : 0;
    const barres = sp.map((v, i) => `<rect x="${i * (70 / sp.length)}" y="${18 - haut(v)}" width="${Math.max(.6, 70 / sp.length - .5)}" height="${haut(v)}" fill="${COULEURS[p.name]}"/>`).join('');
    const j = p.newCases24h;
    return `<tr data-prov="${esc(p.name)}" class="${p.name === PROV ? 'choisi' : ''}">
      <td><i style="background:${COULEURS[p.name]}"></i>${esc(p.name)}</td>
      <td>${fmt(p.confirmed)}</td>
      <td class="${j ? 'plus' : 'zero'}">${j ? '+' + fmt(j) : '0'}</td>
      <td>${fmt(sept)}</td>
      <td>${fmt(p.deaths)}</td>
      <td>${pct(p.cfr)}</td>
      <td><svg viewBox="0 0 70 18" preserveAspectRatio="none" aria-hidden="true">${barres}</svg></td></tr>`;
  }).join('');
  const nat = D.latest.national;
  const septNat = quotidien(D.sitreps, 'confirmed', true).slice(-7).reduce((a, x) => a + x.total, 0);
  document.getElementById('tabProv').innerHTML =
    `<thead><tr><th>${T('thProv')}</th><th>${T('thCas')}</th><th>${T('th24')}</th><th>${T('th7')}</th><th>${T('thDeces')}</th><th>${T('thLet')}</th><th>${T('th30')}</th></tr></thead>
     <tbody>${lignes}</tbody>
     <tfoot><tr><td>${T('rdc')}</td><td>${fmt(nat.confirmed)}</td><td class="plus">+${fmt(nat.newCases24h)}</td><td>${fmt(septNat)}</td><td>${fmt(nat.deaths)}</td><td>${pct(nat.cfr)}</td><td></td></tr></tfoot>`;
  document.getElementById('provSous').textContent = T('cliquer');

  /* La riposte par province : le dernier releve de chaque serie, sa date sous
     l'en-tete, en exposant quand une province est en retard. « — » : la
     source ne publie pas la valeur pour cette province. */
  const SER = {
    ct:  [D.contacts, nom => x => nom ? ((x.provinces || {})[nom] || {}).taux : x.contactsFollowUpRate, pct],
    hosp:[D.cte.parDate, nom => x => nom ? ((x.provinces || {})[nom] || {}).hospitalises : (x.total || {}).hospitalises, fmt],
    occ: [D.cte.parDate, nom => x => nom ? ((x.provinces || {})[nom] || {}).occupation : (x.total || {}).occupation, pct],
    pos: [D.labo.parDate, nom => x => { const v = nom ? (x.provinces || {})[nom] : x.total; return v && v.positifs != null && v.echantillons ? Math.round(v.positifs / v.echantillons * 1000) / 10 : null; }, pct],
  };
  const dateSerie = {};
  for(const [k, [pts]] of Object.entries(SER)) dateSerie[k] = pts.length ? pts[pts.length - 1].date : null;
  const cellule = (k, nom) => {
    const [pts, lire, f] = SER[k];
    const r = dernierReleve(pts, lire(nom));
    if(!r) return '<span class="zero">—</span>';
    return f(r.v) + (r.date !== dateSerie[k] ? `<sup> ${dateC(r.date)}</sup>` : '');
  };
  const ligne = (nom, lib) => `<tr data-prov="${nom ? esc(nom) : ''}" class="${nom && nom === PROV ? 'choisi' : ''}">${nom ? `<td><i style="background:${COULEURS[nom]}"></i>${esc(lib)}</td>` : `<td>${lib}</td>`}
      <td>${cellule('ct', nom)}</td><td>${cellule('hosp', nom)}</td><td>${cellule('occ', nom)}</td><td>${cellule('pos', nom)}</td></tr>`;
  const th = (lib, k) => `<th>${lib}<small>${dateSerie[k] ? dateC(dateSerie[k]) : ''}</small></th>`;
  document.getElementById('tabRip').innerHTML =
    `<thead><tr><th>${T('thProv')}</th>${th(T('thCt'), 'ct')}${th(T('thHosp'), 'hosp')}${th(T('thOcc'), 'occ')}${th(T('thPos'), 'pos')}</tr></thead>
     <tbody>${D.provinces.filter(p => p.confirmed >= 10).map(p => ligne(p.name, p.name)).join('')}</tbody>
     <tfoot>${ligne(null, T('rdc')).replace('<tr data-prov=""', '<tr data-prov="" style="cursor:default"')}</tfoot>`;
  document.getElementById('tabNote').textContent = T('note');
}

/* ---- zones de sante + hors RDC ---- */
/* Nouveaux cas de chaque zone, bulletin par bulletin, sur la fenetre des
   30 jours : l'ecart de cumul d'un releve au suivant (une revision a la
   baisse vaut zero). Une zone absente d'un releve reprend au suivant. */
let SERIES_ZONES = null;
function seriesZones(){
  const depuis = ZONES_CALC.depuis;
  const dates = D.zonesHist.filter(h => !depuis || h.date > depuis).map(h => h.date);
  const dernier = {}, series = {};
  for(const h of D.zonesHist){
    for(const z of h.zones){
      const k = z.province + '|' + norm(z.name);
      const v = z.cases;
      if(v === null || v === undefined) continue;
      if(!depuis || h.date > depuis){
        series[k] = series[k] || {};
        // Une zone qui apparait dans la fenetre : tout son cumul est nouveau,
        // comme dans le « +30 j » (cumul actuel moins zero).
        series[k][h.date] = dernier[k] === undefined ? v : Math.max(0, v - dernier[k]);
      }
      dernier[k] = v;
    }
  }
  return {dates, series};
}
// Echelle commune a toutes les zones affichees : la hauteur d'une barre se
// compare d'une ligne a l'autre.
const valsZone = z => { const ser = SERIES_ZONES.series[z.province + '|' + norm(z.name)] || {}; return SERIES_ZONES.dates.map(d => ser[d] || 0); };
function barresZone(z, max){
  const vals = valsZone(z), w = 70 / SERIES_ZONES.dates.length;
  return `<svg viewBox="0 0 70 16" preserveAspectRatio="none" aria-hidden="true">${vals.map((v, i) => v ? `<rect x="${(i * w).toFixed(2)}" y="${(16 - v / max * 16).toFixed(2)}" width="${Math.max(.6, w - .4).toFixed(2)}" height="${(v / max * 16).toFixed(2)}" fill="${COULEURS[z.province] || 'var(--cas)'}"/>` : '').join('')}</svg>`;
}

function renderZones(){
  if(!SERIES_ZONES) SERIES_ZONES = seriesZones();
  const ul = document.getElementById('zones');
  const titre = document.getElementById('zonesTitre');
  const depuis = ZONES_CALC.depuis ? T('depuis')(dateC(ZONES_CALC.depuis)) : T('trenteJ');
  /* Province choisie : TOUTES ses zones touchees, dans l'ordre des cas
     cumules, avec leurs 30 jours ; la liste defile dans son cadre. Pays
     entier : les dix zones les plus actives sur 30 jours. */
  let zs;
  if(PROV){
    zs = ZONES_CALC.zones.filter(z => z.province === PROV && z.cases > 0).sort((a, b) => b.cases - a.cases || b.j30 - a.j30);
    titre.innerHTML = T('zonesProv')(zs.length, depuis);
  } else {
    zs = ZONES_CALC.zones.filter(z => z.j30 > 0).sort((a, b) => b.j30 - a.j30 || b.cases - a.cases).slice(0, 10);
    titre.innerHTML = T('zonesNat')(depuis);
  }
  ul.classList.toggle('toutes', !!PROV);
  const maxZ = Math.max(1, ...zs.flatMap(valsZone));
  const entete = `<li class="zt"><span>${T('zZone')}</span><span>${T('th30')}</span><span>+${T('th30')}</span><span>${T('zCumul')}</span></li>`;
  ul.innerHTML = zs.length ? entete + zs.map(z => `<li><span class="nom">${esc(z.name)}${PROV ? '' : `<small>${esc(z.province)}</small>`}</span>${barresZone(z, maxZ)}<span class="n ${z.j30 ? '' : 'zero'}">${z.j30 ? '+' + fmt(z.j30) : '0'}</span><span class="c">${fmt(z.cases)}</span></li>`).join('')
    : `<li class="vide-z">${T('zAucun')}</li>`;
  const lien = document.getElementById('lienProv');
  lien.hidden = !PROV;
  if(PROV) lien.href = CFG.provinces[PROV] || CFG.donnees;
  const hr = document.getElementById('horsRdc');
  hr.hidden = !!PROV;
  hr.innerHTML = `<h3>${T('horsRdc')}</h3>` + D.autresPays.pays.map(p =>
    `<div><a href="${CFG.pays[p.id] || CFG.autresPays}">${esc(p.nom[LANG] || p.nom.fr)}</a><b>${T('casN')(p.chiffres[0].n)}</b></div><div><span>${esc(p.statut[LANG] || p.statut.fr)}</span></div>`).join('');
}

/* ---- graphiques ---- */
const AXE = {ticks:{font:{size:9.5, family:"'Public Sans'"}, color:'#777068', maxRotation:0, autoSkip:true, maxTicksLimit:5}, grid:{display:false}, border:{color:'#DEDAD5'}};
const AXE_Y = {beginAtZero:true, ticks:{font:{size:9.5, family:"'Public Sans'"}, color:'#777068', maxTicksLimit:4}, grid:{color:'#EFECE7'}, border:{display:false}};
const pctAxe = v => v + (LANG === 'en' ? '%' : ' %');
function graphe(id, config){
  const zone = document.getElementById(id).parentElement;
  zone.querySelector('.vide')?.remove();
  if(charts[id]){ charts[id].destroy(); delete charts[id]; }
  if(!config) return;
  config.options = Object.assign({responsive:true, maintainAspectRatio:false, animation:{duration:250},
    interaction:{mode:'index', intersect:false},
    plugins:{legend:{display:false}, tooltip:{titleFont:{size:11}, bodyFont:{size:11}, padding:7, boxWidth:8, boxHeight:8}}}, config.options || {});
  charts[id] = new Chart(document.getElementById(id), config);
}
function vide(id, texte){
  graphe(id, null);
  document.getElementById(id).parentElement.insertAdjacentHTML('beforeend', `<div class="vide">${texte}</div>`);
}
const sous = (id, html) => { document.getElementById(id).innerHTML = html; };
const etiquettes = pts => pts.map(p => dateC(p.date));

/* Cas et deces par jour, semaine ou mois : chaque graphique a son propre pas
   (9 octobre 2026, demande de Fable) ; un clic ne redessine que le sien. La
   coupe des rattrapages, l'axe minimum des petites provinces et la moyenne
   sur 7 jours ne valent qu'en vue par jour : en semaines il n'y a plus de pic
   isole et les totaux sont plus grands. */
function renderCD(cle){
  const serie = PROV ? serieProvince(PROV) : D.sitreps;
  const pas = PAS[cle], jour = pas === 'jour';

  /* Provinces a petits nombres : l'axe des nouveaux cas et deces par jour
     monte au moins a 10, comme la courbe forcee de la Tshopo sur sa fiche ;
     sinon une journee a 1 ou 2 cas remplit toute la hauteur. Graduations
     entieres : un demi-cas n'existe pas. */
  const PETITES = ['Tshopo', 'Bas-Uélé', 'Sud-Kivu', 'Sud-Ubangi'];
  const axePetit = PETITES.includes(PROV) ? {suggestedMax:10, ticks:Object.assign({}, AXE_Y.ticks, {precision:0})} : {};
  /* RDC entiere et Ituri : l'axe s'arrete juste au-dessus des journees
     ordinaires, et les deux barres de rattrapage (22 et 30 juillet) sont
     coupees en haut. Elles gardent leur valeur dans la bulle et le
     sous-titre le dit. */
  const COUPE = PROV === null || PROV === 'Ituri';
  const axeCoupe = pts => {
    if(!COUPE) return {};
    const max = Math.max(1, ...pts.filter(x => RATTRAPAGE[x.date] === undefined).map(x => x.total));
    return {max: Math.ceil(max * 1.06 / 10) * 10};
  };
  const mentionCoupe = pts => COUPE && pts.some(x => RATTRAPAGE[x.date] !== undefined && x.total > axeCoupe(pts).max) ? T('coupe') : '';

  const premiere = serie.length ? serie[0].date : null;
  const lib = x => jour ? dateC(x.date) : pas === 'semaine' ? T('sem') + ' ' + dateC(x.date) : MOIS[parseInt(x.date.slice(5, 7), 10) - 1] + ' ' + x.date.slice(0, 4);
  const couleurs = (pts, c) => jour ? c : pts.map(x => x.partiel ? c + '66' : c);
  const bulleTitre = pts => ({callbacks:{title:items => { const x = pts[items[0].dataIndex]; return lib(x) + (x.enCours ? ' (' + T('enCours') + ')' : x.partiel ? ' (' + T('partiel') + ')' : ''); }}});
  const marque = pts => pts.some(x => x.partiel) ? ` · <i style="background:#B9B2A8"></i>${T('partiel')}` : '';
  const bulle = pts => Object.assign({titleFont:{size:11}, bodyFont:{size:11}, padding:7, boxWidth:8, boxHeight:8}, bulleTitre(pts));
  document.getElementById('t-' + cle).textContent = T(cle === 'cas' ? 'gCas' : 'gDeces')[pas];
  document.querySelectorAll(`.pas[data-g="${cle}"] button`).forEach(b => b.setAttribute('aria-pressed', b.dataset.pas === pas));

  if(cle === 'cas'){
    const q0 = quotidien(serie, 'confirmed', !PROV);
    const q = agrege(q0, pas, premiere);
    const moy = q0.map((_, i) => { const t = q0.slice(Math.max(0, i - 6), i + 1); return t.reduce((s, x) => s + x.total, 0) / t.length; });
    const c = COULEURS[PROV] || '#005E82';
    sous('s-cas', `<i style="background:${c}"></i>${T('parBulletin')} <i style="background:var(--cas-clair)"></i>${T('rattrapage')}${jour ? mentionCoupe(q) + ` <i style="background:var(--ink)"></i>${T('moy7')}` : marque(q)}`);
    graphe('c-cas', {type:'bar', data:{labels:q.map(lib), datasets:[
      ...(jour ? [{type:'line', label:T('lMoy'), data:moy, borderColor:'#1F1A13', borderWidth:1.3, pointRadius:0, tension:.3}] : []),
      {label:T('lNouveauxCas'), data:q.map(x => x.rapporte), backgroundColor:couleurs(q, c), stack:'s', barPercentage:jour ? 1 : .86, categoryPercentage:.92},
      {label:T('rattrapage'), data:q.map(x => x.rattrapage), backgroundColor:'#B7D3E1', stack:'s', barPercentage:jour ? 1 : .86, categoryPercentage:.92}]},
      options:{plugins:{legend:{display:false}, tooltip:bulle(q)},
        scales:{x:Object.assign({stacked:true}, AXE), y:Object.assign({stacked:true}, AXE_Y, jour ? axePetit : {}, jour ? axeCoupe(q) : {})}}});
  } else {
    const q = agrege(quotidien(serie, 'deaths', !PROV), pas, premiere);
    sous('s-deces', `<i style="background:var(--deces)"></i>${T('parBulletin')} <i style="background:var(--deces-clair)"></i>${T('rattrapage')}${jour ? mentionCoupe(q) : marque(q)} · ${esc(PROV || T('rdc'))}`);
    graphe('c-deces', {type:'bar', data:{labels:q.map(lib), datasets:[
      {label:T('lNouveauxDeces'), data:q.map(x => x.rapporte), backgroundColor:couleurs(q, '#993A2E'), stack:'s', barPercentage:jour ? 1 : .86, categoryPercentage:.92},
      {label:T('rattrapage'), data:q.map(x => x.rattrapage), backgroundColor:'#E9B9B0', stack:'s', barPercentage:jour ? 1 : .86, categoryPercentage:.92}]},
      options:{plugins:{legend:{display:false}, tooltip:bulle(q)},
        scales:{x:Object.assign({stacked:true}, AXE), y:Object.assign({stacked:true}, AXE_Y, jour ? axePetit : {}, jour ? axeCoupe(q) : {})}}});
  }
}

function renderGraphes(){
  renderCD('cas'); renderCD('deces');
  const nomZone = PROV || T('rdc');

  // 3. lieu des deces, par semaine
  const sem = {};
  D.decesLieu.parDate.forEach(p => {
    const prov = p.provinces || {};
    const vals = PROV ? [prov[PROV]].filter(Boolean) : Object.values(prov);
    if(!vals.length) return;
    const k = lundi(p.date);
    sem[k] = sem[k] || {date:k, com:0, cte:0};
    vals.forEach(v => { sem[k].com += v.communautaires || 0; sem[k].cte += v.intraCte || 0; });
  });
  /* Des PARTS, pas des volumes : des jours manquent a la fenetre et les
     volumes hebdomadaires ne se comparent pas (CLAUDE.md). Sous le seuil de
     lisibilite de deces-lieu.json (20 deces), une part ne dit rien. */
  const seuil = D.decesLieu.seuilLisibilite || 20;
  const sl = Object.values(sem).sort(parDate);
  const totLieu = sl.reduce((s, x) => s + x.com + x.cte, 0);
  if(!sl.length || totLieu < seuil) vide('c-lieu', T('lieuPeu'));
  else {
    const com = sl.reduce((s, x) => s + x.com, 0);
    const part = x => (x.com + x.cte) ? Math.round(x.com / (x.com + x.cte) * 1000) / 10 : null;
    sous('s-lieu', `<i style="background:#993A2E"></i>${T('enCom')} <i style="background:#E7DCD0"></i>${T('enCentre')} · ${T('lieuPart')(Math.round(com / totLieu * 100), dateC(sl[0].date))}`);
    graphe('c-lieu', {type:'bar', data:{labels:sl.map(x => T('sem') + ' ' + dateC(x.date)), datasets:[
      {label:T('lCom'), data:sl.map(part), backgroundColor:'#993A2E', stack:'s'},
      {label:T('lCentre'), data:sl.map(x => { const v = part(x); return v === null ? null : Math.round((100 - v) * 10) / 10; }), backgroundColor:'#E7DCD0', stack:'s'}]},
      options:{scales:{x:Object.assign({stacked:true}, AXE), y:Object.assign({stacked:true}, AXE_Y, {max:100, ticks:Object.assign({}, AXE_Y.ticks, {callback:pctAxe})})}}});
  }

  // 4. alertes par semaine (une ligne qui se contredit — validees > recues — est ecartee, comme sur Riposte)
  const as = {};
  D.alertes.parDate.forEach(p => {
    const v = PROV ? (p.provinces || {})[PROV] : p.total;
    if(!v || v.recues === null || v.recues === undefined) return;
    if(v.validees !== null && v.validees !== undefined && v.validees > v.recues) return;
    const k = lundi(p.date);
    as[k] = as[k] || {date:k, recues:0, validees:0};
    as[k].recues += v.recues; as[k].validees += v.validees || 0;
  });
  const al = Object.values(as).sort(parDate);
  if(!al.length) vide('c-alertes', T('alNon'));
  else {
    const d = al[al.length - 1];
    sous('s-alertes', `<i style="background:#D9D3CA"></i>${T('recues')} <i style="background:#A06F30"></i>${T('validees')} · ${T('alSem')(dateC(d.date), fmt(d.recues), fmt(d.validees))}`);
    graphe('c-alertes', {type:'bar', data:{labels:al.map(x => T('sem') + ' ' + dateC(x.date)), datasets:[
      {label:T('lRecues'), data:al.map(x => x.recues), backgroundColor:'#D9D3CA', grouped:false, barPercentage:.9, order:2},
      {label:T('lValidees'), data:al.map(x => x.validees), backgroundColor:'#A06F30', grouped:false, barPercentage:.55, order:1}]},
      options:{scales:{x:AXE, y:AXE_Y}}});
  }

  // 5. laboratoire : positifs par jour, taux de positivite quand les echantillons sont publies
  const lab = D.labo.parDate.map(p => {
    const v = PROV ? (p.provinces || {})[PROV] : p.total;
    if(!v) return null;
    const pos = v.positifs ?? null, ech = v.echantillons ?? null;
    return {date:p.date, pos, taux: (pos !== null && ech) ? Math.round(pos / ech * 1000) / 10 : null};
  }).filter(x => x && x.pos !== null).slice(-60);
  if(!lab.length) vide('c-labo', T('laboNon'));
  else {
    const dt = lab.filter(x => x.taux !== null).pop();
    sous('s-labo', `<i style="background:#6B5CA5"></i>${T('positifs')} <i style="background:#1F1A13"></i>${T('positivite')}${dt ? ` · ${pct(dt.taux)} ${T('le')(dateC(dt.date))}` : ''}`);
    graphe('c-labo', {type:'bar', data:{labels:etiquettes(lab), datasets:[
      {type:'line', label:T('lPos'), data:lab.map(x => x.taux), borderColor:'#1F1A13', borderWidth:1.2, pointRadius:0, spanGaps:false, yAxisID:'y2', tension:.25},
      {label:T('lPositifs'), data:lab.map(x => x.pos), backgroundColor:'#6B5CA5', barPercentage:1, categoryPercentage:.9}]},
      options:{scales:{x:AXE, y:AXE_Y, y2:Object.assign({}, AXE_Y, {position:'right', grid:{display:false}, ticks:Object.assign({}, AXE_Y.ticks, {callback:pctAxe})})}}});
  }

  // 6. contacts suivis
  const ct = D.contacts.map(x => ({date:x.date, taux: PROV ? ((x.provinces || {})[PROV] || {}).taux ?? null : x.contactsFollowUpRate}))
    .filter(x => x.taux !== null && x.taux !== undefined).slice(-90);
  if(!ct.length) vide('c-contacts', T('ctNon'));
  else {
    const d = ct[ct.length - 1];
    sous('s-contacts', `${T('ctPart')} · ${pct(d.taux)} ${T('le')(dateC(d.date))}`);
    graphe('c-contacts', {type:'line', data:{labels:etiquettes(ct), datasets:[
      {label:T('lCt'), data:ct.map(x => x.taux), borderColor:COULEURS[PROV] || '#005E82', backgroundColor:'rgba(0,94,130,.08)', fill:true, borderWidth:1.5, pointRadius:0, tension:.25}]},
      options:{scales:{x:AXE, y:Object.assign({}, AXE_Y, {beginAtZero:false, suggestedMin:50, max:100, ticks:Object.assign({}, AXE_Y.ticks, {callback:pctAxe})})}}});
  }
}

/* ======================================================================
   Filtre
   ====================================================================== */
function choisir(nom){
  PROV = nom || null;
  history.replaceState(null, '', PROV ? '#' + SLUGS[PROV] : location.pathname);
  renderTout();
}
function renderTout(){
  renderFiltres(); renderKpis(); renderCarte(); renderTableau(); renderZones(); renderGraphes();
}

/* ---- le tiroir du menu : le menu principal du site, lu dans la page
   d'accueil de la meme langue pour rester identique au site ---- */
let MENU_LU = false;
async function lireMenu(){
  if(MENU_LU) return; MENU_LU = true;
  const liste = document.getElementById('tiroirListe');
  try{
    const html = await (await fetch(CFG.accueil, {cache:'no-store'})).text();
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const grp = [...doc.querySelectorAll('nav.side-nav .nav-grp')];
    if(!grp.length) throw new Error('menu introuvable');
    liste.innerHTML = `<a class="l" href="${CFG.accueil}">${T('accueil')}<small>${T('accueilD')}</small></a>` + grp.map(g => {
      const titre = g.querySelector('.nav-grp-btn span')?.textContent.trim() || '';
      const liens = [...g.querySelectorAll('.nav-pop a')].map(a => {
        const t = a.querySelector('.nav-t')?.childNodes[0]?.textContent.trim() || a.textContent.trim();
        const d = a.querySelector('.nav-desc')?.textContent.trim() || '';
        const href = a.getAttribute('href');
        return `<a class="l${href === CFG.ici ? ' ici' : ''}" href="${esc(href)}">${esc(t)}${d ? `<small>${esc(d)}</small>` : ''}</a>`;
      }).join('');
      return `<h3>${esc(titre)}</h3>${liens}`;
    }).join('');
  }catch(e){
    MENU_LU = false;
    liste.innerHTML = `<a class="l" href="${CFG.accueil}">${T('retour')}</a>`;
  }
}
function tiroir(ouvrir){
  const t = document.getElementById('tiroir'), v = document.getElementById('voile'), b = document.getElementById('burger');
  t.hidden = v.hidden = !ouvrir; b.setAttribute('aria-expanded', ouvrir);
  if(ouvrir){ lireMenu(); document.getElementById('fermer').focus(); } else b.focus();
}

async function demarrer(){
  document.getElementById('burger').addEventListener('click', () => tiroir(true));
  document.getElementById('fermer').addEventListener('click', () => tiroir(false));
  document.getElementById('voile').addEventListener('click', () => tiroir(false));
  addEventListener('keydown', e => { if(e.key === 'Escape' && !document.getElementById('tiroir').hidden) tiroir(false); });
  const [latest, sitreps, provHist, zonesHist, decesLieu, alertes, labo, contacts, piliers, autresPays, geo, cte] = await Promise.all([
    '/data/latest.json', '/data/sitreps.json', '/data/province-history.json', '/data/zones-history.json',
    '/data/deces-lieu.json', '/data/alertes.json', '/data/laboratoire.json', '/data/contacts-followup.json',
    '/data/piliers.json', '/data/autres-pays.json', '/site/geo/zones-overview.json', '/data/cte.json'].map(charger));
  D = {latest, sitreps:[...sitreps].sort(parDate), provHist:[...provHist].sort(parDate), zonesHist:[...zonesHist].sort(parDate),
       decesLieu, alertes, labo, contacts:[...contacts].sort(parDate), piliers, autresPays, geo, cte,
       provinces:[...latest.provinces].sort((a, b) => (b.confirmed || 0) - (a.confirmed || 0))};
  ZONES_CALC = zonesCalculees();
  const h = decodeURIComponent(location.hash.slice(1));
  PROV = Object.keys(SLUGS).find(n => SLUGS[n] === h) || null;
  // ?pas=semaine ou ?pas=mois : ouvrir les graphiques sur ce pas (lien partageable).
  const pasDemande = new URLSearchParams(location.search).get('pas');
  if(['jour', 'semaine', 'mois'].includes(pasDemande)) PAS.cas = PAS.deces = pasDemande;
  renderSituation();
  document.querySelectorAll('.pas').forEach(el => { el.innerHTML = ['jour', 'semaine', 'mois'].map(k =>
    `<button type="button" data-pas="${k}" aria-pressed="${k === PAS[el.dataset.g]}" title="${T('pas')[k][1]}" aria-label="${T('pas')[k][1]}">${T('pas')[k][0]}</button>`).join(''); });
  construireCarte();
  renderTout();

  document.getElementById('filtres').addEventListener('click', e => {
    const b = e.target.closest('button'); if(b) choisir(b.dataset.prov || null);
  });
  ['tabProv', 'tabRip'].forEach(id => document.getElementById(id).addEventListener('click', e => {
    const tr = e.target.closest('tbody tr'); if(tr) choisir(tr.dataset.prov === PROV ? null : tr.dataset.prov);
  }));
  document.querySelectorAll('.pas').forEach(el => el.addEventListener('click', e => {
    const b = e.target.closest('button'), g = el.dataset.g; if(!b || b.dataset.pas === PAS[g]) return;
    PAS[g] = b.dataset.pas; renderCD(g);
  }));
  document.getElementById('modeCarte').addEventListener('click', e => {
    const b = e.target.closest('button'); if(!b) return;
    MODE = b.dataset.mode;
    document.querySelectorAll('#modeCarte button').forEach(x => x.setAttribute('aria-pressed', x === b));
    renderCarte();
  });
  addEventListener('hashchange', () => {
    const s = location.hash.slice(1);
    const n = Object.keys(SLUGS).find(k => SLUGS[k] === s) || null;
    if(n !== PROV){ PROV = n; renderTout(); }
  });
}
demarrer().catch(e => {
  console.error(e);
  document.getElementById('situation').insertAdjacentHTML('beforeend', `<br><b style="color:#993A2E">${T('erreur')}</b>`);
});
