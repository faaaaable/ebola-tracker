'use strict';
/* La base de donnees (/base-de-donnees/, 9 octobre 2026) : toutes les donnees
   du site, une ligne par date et par territoire, epidemie et riposte, avec le
   bulletin source. Lit data/base-ebola-rdc.json, ecrit par
   scripts/base_donnees.py a chaque generation. Remplace, au chargement, le
   tableau du dernier bulletin que le generateur a ecrit en dur dans #bddApp.

   Vue d'ouverture : Pays, colonnes Epidemie (decision du 9 octobre 2026). Le
   choix de colonnes est garde d'un niveau a l'autre ; seule la vue Zones
   repasse en Epidemie, la riposte n'existant pas par zone. L'adresse retient
   les filtres (?niveau=zone&province=Ituri). Le tableau ne cree que les lignes
   visibles : la recherche du navigateur ne les trouve pas toutes, le champ
   Rechercher si. */

const CFG = JSON.parse(document.getElementById('bddConfig').textContent);
const LANG = CFG.lang in {fr:1, en:1, sw:1} ? CFG.lang : 'fr';

const TXT = {
  fr: {
    mois:['janv.','févr.','mars','avr.','mai','juin','juil.','août','sept.','oct.','nov.','déc.'],
    niveau:'Niveau', pays:'Pays', provinces:'Provinces', zones:'Zones', tout:'Tout',
    colonnes:'Colonnes', epi:'Épidémie', rip:'Riposte', province:'Province', toutes:'Toutes',
    rechercher:'Rechercher', aideRech:'Seules les lignes à l’écran existent dans la page : la recherche du navigateur (Ctrl+F) ne les trouve pas toutes, ce champ si.',
    placeholder:'Bunia, Ituri…', du:'Du', au:'Au', effacer:'Tout effacer', vue:'Télécharger la vue (CSV)',
    lignes:(n, t) => `<b>${n}</b> ligne${n === '1' ? '' : 's'} sur ${t}`, rdc:'RDC',
    nivPays:'Pays', nivProvince:'Province', nivZone:'Zone',
    c:{date:'Date', province:'Province', zone:'Zone de santé', niveau:'Niveau', sitrep:'SitRep',
       cas:['Cas','cumul'], nouveaux_cas:['Nouveaux cas','calculés'], deces:['Décès','cumul'], nouveaux_deces:['Nouveaux décès','calculés'],
       letalite:['Létalité','décès / cas'], gueris:['Guéris','cumul'], deces_communaute:['En communauté','décès du jour'], deces_cte:['En CTE','décès du jour'],
       alertes_recues:['Reçues','alertes'], alertes_validees:['Validées','alertes'], labo_echantillons:['Échantillons'], labo_positifs:['Positifs'], labo_positivite:['Positivité'],
       cte_hospitalises:['Hospitalisés'], cte_lits:['Lits'], cte_occupation:['Occupation'], contacts_a_suivre:['À suivre'], contacts_vus:['Vus'], contacts_vus_pct:['Vus','%'], vaccines_cumul:['Vaccinés','cumul']},
    g:{epi:'Épidémie', lieu:'Lieu du décès', surv:'Surveillance', labo:'Laboratoire', cte:'Prise en charge (CTE)', ct:'Contacts', vac:'Vaccination'},
    calc:'calc.', calcT:'Ligne reconstituée : SitRep non publié', rat:'R', ratT:'Rattrapage : l’écart couvre plus d’une journée',
    sur:n => `${n} j`, surT:n => `Écart sur ${n} jours : pas de relevé pour ce territoire entre-temps`, neg:'Révision à la baisse par la source', oms:'OMS',
    dicoT:'Les colonnes',
    dico:[['Cas, décès (cumul)','Cas confirmés et décès depuis le début de l’épidémie, tels que publiés par le bulletin du jour, pour le pays, la province ou la zone.'],
          ['Nouveaux cas, nouveaux décès','Écart de cumul avec le relevé précédent du même territoire, calculé par le site ; négatif = révision à la baisse ; « 3 j » = écart couvrant trois journées.'],
          ['Létalité','Décès cumulés divisés par cas confirmés cumulés.'], ['Guéris','Cumul publié, au niveau national seulement.'],
          ['Lieu du décès','Décès confirmés du jour en communauté ou en centre de traitement (CTE), depuis le 13 juillet.'],
          ['Alertes','Alertes reçues et validées comme cas suspects, par jour, depuis le 1er juin.'],
          ['Laboratoire','Échantillons analysés et positifs du jour ; la positivité n’est calculée que si les deux sont publiés.'],
          ['Prise en charge','Personnes hospitalisées en CTE, lits disponibles et taux d’occupation.'],
          ['Contacts','Contacts à suivre, contacts vus et part des contacts vus.'], ['Vaccinés','Cumul des personnes vaccinées publié pour la province.']],
    erreur:'La base n’a pas pu être chargée. Les fichiers restent téléchargeables ci-dessus.',
  },
  en: {
    mois:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    niveau:'Level', pays:'Country', provinces:'Provinces', zones:'Zones', tout:'All',
    colonnes:'Columns', epi:'Outbreak', rip:'Response', province:'Province', toutes:'All',
    rechercher:'Search', aideRech:'Only on-screen rows exist in the page: the browser search (Ctrl+F) does not find them all, this field does.',
    placeholder:'Bunia, Ituri…', du:'From', au:'To', effacer:'Clear all', vue:'Download this view (CSV)',
    lignes:(n, t) => `<b>${n}</b> row${n === '1' ? '' : 's'} out of ${t}`, rdc:'DRC',
    nivPays:'Country', nivProvince:'Province', nivZone:'Zone',
    c:{date:'Date', province:'Province', zone:'Health zone', niveau:'Level', sitrep:'SitRep',
       cas:['Cases','total'], nouveaux_cas:['New cases','computed'], deces:['Deaths','total'], nouveaux_deces:['New deaths','computed'],
       letalite:['Fatality','deaths / cases'], gueris:['Recovered','total'], deces_communaute:['Community','deaths of the day'], deces_cte:['In ETC','deaths of the day'],
       alertes_recues:['Received','alerts'], alertes_validees:['Validated','alerts'], labo_echantillons:['Samples'], labo_positifs:['Positive'], labo_positivite:['Positivity'],
       cte_hospitalises:['Hospitalised'], cte_lits:['Beds'], cte_occupation:['Occupancy'], contacts_a_suivre:['To follow'], contacts_vus:['Seen'], contacts_vus_pct:['Seen','%'], vaccines_cumul:['Vaccinated','total']},
    g:{epi:'Outbreak', lieu:'Place of death', surv:'Surveillance', labo:'Laboratory', cte:'Treatment (ETC)', ct:'Contacts', vac:'Vaccination'},
    calc:'calc.', calcT:'Reconstructed row: SitRep not published', rat:'C', ratT:'Catch-up: the difference covers more than one day',
    sur:n => `${n} d`, surT:n => `Difference over ${n} days: no reading for this area in between`, neg:'Downward revision by the source', oms:'WHO',
    dicoT:'The columns',
    dico:[['Cases, deaths (total)','Confirmed cases and deaths since the start of the outbreak, as published by the day’s bulletin, for the country, province or zone.'],
          ['New cases, new deaths','Difference from the previous reading for the same area, computed by the site; negative = downward revision; “3 d” = difference covering three days.'],
          ['Fatality','Total deaths divided by total confirmed cases.'], ['Recovered','Published total, national level only.'],
          ['Place of death','Confirmed deaths of the day in the community or in a treatment centre (ETC), since 13 July.'],
          ['Alerts','Alerts received and validated as suspected cases, per day, since 1 June.'],
          ['Laboratory','Samples analysed and positive results of the day; positivity is only computed when both are published.'],
          ['Treatment','People hospitalised in ETCs, available beds and occupancy rate.'],
          ['Contacts','Contacts to follow, contacts seen and share of contacts seen.'], ['Vaccinated','Published total of people vaccinated in the province.']],
    erreur:'The database could not be loaded. The files remain available for download above.',
  },
  sw: {
    mois:['Jan','Feb','Mac','Apr','Mei','Jun','Jul','Ago','Sep','Okt','Nov','Des'],
    niveau:'Kiwango', pays:'Nchi', provinces:'Majimbo', zones:'Maeneo', tout:'Yote',
    colonnes:'Safu', epi:'Mlipuko', rip:'Mapambano', province:'Jimbo', toutes:'Yote',
    rechercher:'Tafuta', aideRech:'Ni mistari iliyo kwenye skrini tu ndiyo ipo kwenye ukurasa: utafutaji wa kivinjari (Ctrl+F) hauipati yote, kisanduku hiki kinaipata.',
    placeholder:'Bunia, Ituri…', du:'Kuanzia', au:'Hadi', effacer:'Futa yote', vue:'Pakua mwonekano huu (CSV)',
    lignes:(n, t) => `Mistari <b>${n}</b> kati ya ${t}`, rdc:'DRC',
    nivPays:'Nchi', nivProvince:'Jimbo', nivZone:'Eneo',
    c:{date:'Tarehe', province:'Jimbo', zone:'Eneo la afya', niveau:'Kiwango', sitrep:'SitRep',
       cas:['Visa','jumla'], nouveaux_cas:['Visa vipya','vilivyohesabiwa'], deces:['Vifo','jumla'], nouveaux_deces:['Vifo vipya','vilivyohesabiwa'],
       letalite:['Kiwango cha vifo','vifo / visa'], gueris:['Waliopona','jumla'], deces_communaute:['Jamii','vifo vya siku'], deces_cte:['Katika CTE','vifo vya siku'],
       alertes_recues:['Zilizopokelewa','tahadhari'], alertes_validees:['Zilizothibitishwa','tahadhari'], labo_echantillons:['Sampuli'], labo_positifs:['Chanya'], labo_positivite:['Kiwango cha chanya'],
       cte_hospitalises:['Waliolazwa'], cte_lits:['Vitanda'], cte_occupation:['Vitanda vilivyojaa'], contacts_a_suivre:['Wa kufuatiliwa'], contacts_vus:['Walioonekana'], contacts_vus_pct:['Walioonekana','%'], vaccines_cumul:['Waliochanjwa','jumla']},
    g:{epi:'Mlipuko', lieu:'Mahali pa kifo', surv:'Ufuatiliaji', labo:'Maabara', cte:'Matibabu (CTE)', ct:'Watu wa karibu', vac:'Chanjo'},
    calc:'calc.', calcT:'Mstari uliojengwa upya: SitRep haikuchapishwa', rat:'R', ratT:'Ucheleweshaji: tofauti inajumuisha zaidi ya siku moja',
    sur:n => `siku ${n}`, surT:n => `Tofauti ya siku ${n}: hakuna takwimu za eneo hili katikati`, neg:'Marekebisho ya kupunguza na chanzo', oms:'WHO',
    dicoT:'Safu',
    dico:[['Visa, vifo (jumla)','Visa vilivyothibitishwa na vifo tangu mwanzo wa mlipuko, kama vilivyochapishwa na ripoti ya siku hiyo.'],
          ['Visa vipya, vifo vipya','Tofauti na takwimu iliyotangulia ya eneo hilo, iliyohesabiwa na tovuti; hasi = marekebisho ya kupunguza.'],
          ['Kiwango cha vifo','Vifo vya jumla kugawanywa kwa visa vya jumla.'], ['Waliopona','Jumla iliyochapishwa, kwa kiwango cha kitaifa tu.'],
          ['Mahali pa kifo','Vifo vya siku katika jamii au katika kituo cha matibabu (CTE), tangu 13 Julai.'],
          ['Tahadhari','Tahadhari zilizopokelewa na kuthibitishwa kama visa vinavyoshukiwa, kwa siku, tangu 1 Juni.'],
          ['Maabara','Sampuli zilizochambuliwa na chanya za siku; kiwango cha chanya kinahesabiwa tu zote mbili zikichapishwa.'],
          ['Matibabu','Waliolazwa katika CTE, vitanda na kiwango cha vitanda vilivyojaa.'],
          ['Watu wa karibu','Wa kufuatiliwa, walioonekana na sehemu ya walioonekana.'], ['Waliochanjwa','Jumla ya waliochanjwa iliyochapishwa kwa jimbo.']],
    erreur:'Hifadhidata haikuweza kupakiwa. Faili bado zinaweza kupakuliwa hapo juu.',
  },
};
const T = k => (TXT[LANG] && TXT[LANG][k] !== undefined) ? TXT[LANG][k] : TXT.fr[k];

const COULEURS = {"Ituri":"#005E82","Nord-Kivu":"#A06F30","Haut-Uélé":"#327957","Tshopo":"#6B5CA5","Sud-Kivu":"#5A544C","Bas-Uélé":"#993A2E","Sud-Ubangi":"#B0487D"};
const SEP = LANG === 'fr' ? ' ' : ',', DEC = LANG === 'fr' ? ',' : '.';
const fmt = n => (n === null || n === undefined) ? '' : String(Math.round(Math.abs(n))).replace(/\B(?=(\d{3})+(?!\d))/g, SEP);
const pct = n => (n === null || n === undefined) ? '' : (Math.round(n * 10) / 10).toFixed(1).replace('.', DEC) + (LANG === 'en' ? '%' : ' %');
const dateC = iso => { const [a, m, j] = iso.split('-'); return `${parseInt(j, 10)} ${T('mois')[parseInt(m, 10) - 1]} ${a}`; };
const norm = t => String(t || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const esc = t => String(t).replace(/[&<>"]/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;'}[c]));

/* Les colonnes affichees : cle du fichier, type, groupe, figee ou non. */
const COLS = [
  {k:'date', t:'date', g:1, fixe:'f0'}, {k:'province', t:'prov', g:1, fixe:'f1'}, {k:'zone', t:'txt', g:1, fixe:'f2'},
  {k:'niveau', t:'niv', g:1}, {k:'sitrep', t:'pdf', g:1},
  {k:'cas', t:'n', grp:'epi', vue:'epi'}, {k:'nouveaux_cas', t:'d', grp:'epi', vue:'epi'}, {k:'deces', t:'n', grp:'epi', vue:'epi'},
  {k:'nouveaux_deces', t:'d', grp:'epi', vue:'epi'}, {k:'letalite', t:'p', grp:'epi', vue:'epi'}, {k:'gueris', t:'n', grp:'epi', vue:'epi'},
  {k:'deces_communaute', t:'n', grp:'lieu', vue:'rip'}, {k:'deces_cte', t:'n', grp:'lieu', vue:'rip'},
  {k:'alertes_recues', t:'n', grp:'surv', vue:'rip'}, {k:'alertes_validees', t:'n', grp:'surv', vue:'rip'},
  {k:'labo_echantillons', t:'n', grp:'labo', vue:'rip'}, {k:'labo_positifs', t:'n', grp:'labo', vue:'rip'}, {k:'labo_positivite', t:'p', grp:'labo', vue:'rip'},
  {k:'cte_hospitalises', t:'n', grp:'cte', vue:'rip'}, {k:'cte_lits', t:'n', grp:'cte', vue:'rip'}, {k:'cte_occupation', t:'p', grp:'cte', vue:'rip'},
  {k:'contacts_a_suivre', t:'n', grp:'ct', vue:'rip'}, {k:'contacts_vus', t:'n', grp:'ct', vue:'rip'}, {k:'contacts_vus_pct', t:'p', grp:'ct', vue:'rip'},
  {k:'vaccines_cumul', t:'n', grp:'vac', vue:'rip'},
];

let LIGNES = [], META = null, COLV = 'epi', NIVEAU = 'pays', TRI = {k:'date', sens:-1}, VUES = [];
const colonnes = () => COLS.filter(c => (!c.vue || COLV === 'tout' || c.vue === COLV) &&
  !((NIVEAU === 'pays' || NIVEAU === 'province') && (c.k === 'zone' || c.k === 'niveau')));

function interface_(){
  const provs = [...new Set(LIGNES.filter(o => o.province).map(o => o.province))].sort((a, b) => a.localeCompare(b));
  const zones = [...new Set(LIGNES.filter(o => o.zone).map(o => o.zone))].sort((a, b) => a.localeCompare(b));
  const seg = (id, items, actif) => `<div class="bdd-seg" id="${id}">${items.map(([v, l]) => `<button type="button" data-v="${v}" aria-pressed="${v === actif}">${l}</button>`).join('')}</div>`;
  document.getElementById('bddApp').innerHTML = `
    <div class="bdd-filtres">
      <div><span class="bdd-lab">${T('niveau')}</span>${seg('bNiveau', [['pays', T('pays')], ['province', T('provinces')], ['zone', T('zones')], ['tous', T('tout')]], NIVEAU)}</div>
      <div><span class="bdd-lab">${T('colonnes')}</span>${seg('bCol', [['epi', T('epi')], ['rip', T('rip')], ['tout', T('tout')]], COLV)}</div>
      <label><span class="bdd-lab">${T('province')}</span><select id="fProv"><option value="">${T('toutes')}</option>${provs.map(p => `<option>${esc(p)}</option>`).join('')}</select></label>
      <label title="${T('aideRech')}"><span class="bdd-lab">${T('rechercher')}</span><input type="search" id="fRech" placeholder="${T('placeholder')}" list="bddZones"></label>
      <datalist id="bddZones">${zones.map(z => `<option value="${esc(z)}">`).join('')}</datalist>
      <label><span class="bdd-lab">${T('du')}</span><input type="date" id="fDu" min="${META.debut}" max="${META.fin}"></label>
      <label><span class="bdd-lab">${T('au')}</span><input type="date" id="fAu" min="${META.debut}" max="${META.fin}"></label>
      <div class="bdd-actions"><button type="button" class="bdd-raz" id="bRaz">${T('effacer')}</button></div>
    </div>
    <div class="bdd-compte" id="bddCompte"></div>
    <div class="bdd-grille" id="bddGrille"><table><thead id="bddThead"></thead><tbody id="bddTbody"></tbody></table></div>`;
  document.getElementById('bddDico').innerHTML = `<table class="bdd-dico"><tbody>${T('dico').map(([a, b]) => `<tr><td>${a}</td><td>${b}</td></tr>`).join('')}</tbody></table>`;
}

function filtrer(){
  const p = document.getElementById('fProv').value, z = norm(document.getElementById('fRech').value.trim());
  const du = document.getElementById('fDu').value, au = document.getElementById('fAu').value;
  VUES = LIGNES.filter(o => (NIVEAU === 'tous' || o.niveau === NIVEAU) && (!p || o.province === p) &&
    (!z || norm(o.zone).includes(z) || norm(o.province).includes(z)) && (!du || o.date >= du) && (!au || o.date <= au));
  const k = TRI.k, s = TRI.sens, ordre = {pays:0, province:1, zone:2};
  VUES.sort((a, b) => {
    const x = a[k], y = b[k];
    if(x === y) return (ordre[a.niveau] - ordre[b.niveau]) || String(a.province).localeCompare(b.province) || String(a.zone).localeCompare(b.zone);
    if(x === null || x === undefined || x === '') return 1;
    if(y === null || y === undefined || y === '') return -1;
    return (x < y ? -1 : 1) * s;
  });
  document.getElementById('bddCompte').innerHTML = T('lignes')(fmt(VUES.length), fmt(LIGNES.length));
  document.getElementById('bddGrille').classList.toggle('is-melange', NIVEAU === 'tous');
  entete(); dessiner(true); adresse();
}

function entete(){
  const cols = colonnes(), lib = T('c');
  let rg = '';
  cols.forEach((c, k) => {
    if(!c.grp){ rg += `<th class="${c.fixe ? 'fixe ' + c.fixe : ''}"></th>`; return; }
    if(k && cols[k - 1].grp === c.grp) return;
    let n = 1; while(k + n < cols.length && cols[k + n].grp === c.grp) n++;
    rg += `<th class="gr" colspan="${n}">${T('g')[c.grp]}</th>`;
  });
  document.getElementById('bddThead').innerHTML = `<tr class="groupes">${rg}</tr><tr class="cols">` + cols.map((c, k) => {
    const l = lib[c.k], [t, sous] = Array.isArray(l) ? l : [l];
    return `<th class="${c.g ? 'g' : ''} ${c.fixe ? 'fixe ' + c.fixe : ''} ${k && c.grp && c.grp !== cols[k - 1].grp ? 'bdd-sep' : ''}" data-k="${c.k}" ${TRI.k === c.k ? `aria-sort="${TRI.sens > 0 ? 'ascending' : 'descending'}"` : ''}>${t}${sous ? `<small>${sous}</small>` : ''}</th>`;
  }).join('') + '</tr>';
}

function cellule(o, c){
  const v = o[c.k], vide = '<span class="vide">—</span>';
  switch(c.t){
    case 'date': return dateC(v);
    case 'pdf': {
      const m = o.mention || '';
      if(!v) return /OMS|WHO/.test(m) ? `<span title="${esc(m)}">${T('oms')}</span>` : vide;
      const f = META.pdf[String(v)];
      let h = f && !m.includes('reconstitue') ? `<a class="pdf" href="${f}" target="_blank" rel="noopener">n° ${v}</a>` : `n° ${v}`;
      if(m.includes('reconstitue')) h += `<span class="rec" title="${T('calcT')}">${T('calc')}</span>`;
      if(m.includes('rattrapage')) h += `<span class="rat" title="${T('ratT')}">${T('rat')}</span>`;
      return h;
    }
    case 'prov': return v ? (COULEURS[v] ? `<i class="pt" style="background:${COULEURS[v]}"></i>` : '') + esc(v) : (o.niveau === 'pays' ? T('rdc') : '');
    case 'niv': return {pays:T('nivPays'), province:T('nivProvince'), zone:T('nivZone')}[v];
    case 'txt': return esc(v || '');
    case 'n': return v === null || v === undefined ? vide : fmt(v);
    case 'd': {
      if(v === null || v === undefined) return vide;
      const s = v < 0 ? `<span class="neg" title="${T('neg')}">−${fmt(v)}</span>` : '+' + fmt(v);
      return s + (o.ecart_jours > 1 ? `<span class="sur" title="${T('surT')(o.ecart_jours)}">${T('sur')(o.ecart_jours)}</span>` : '');
    }
    case 'p': return v === null || v === undefined ? vide : pct(v);
  }
}

const H = 28, MARGE = 20;
function dessiner(remonter){
  const g = document.getElementById('bddGrille');
  if(remonter) g.scrollTop = 0;
  const debut = Math.max(0, Math.floor(g.scrollTop / H) - MARGE);
  const fin = Math.min(VUES.length, debut + Math.ceil(g.clientHeight / H) + 2 * MARGE);
  const cols = colonnes();
  let h = `<tr class="cale"><td colspan="${cols.length}" style="height:${debut * H}px"></td></tr>`;
  for(let i = debut; i < fin; i++){
    const o = VUES[i];
    h += `<tr class="niv-${o.niveau}">` + cols.map((c, k) => `<td class="${c.g ? 'g' : ''} ${c.fixe ? 'fixe ' + c.fixe : ''} ${k && c.grp && c.grp !== cols[k - 1].grp ? 'bdd-sep' : ''}">${cellule(o, c)}</td>`).join('') + '</tr>';
  }
  h += `<tr class="cale"><td colspan="${cols.length}" style="height:${(VUES.length - fin) * H}px"></td></tr>`;
  document.getElementById('bddTbody').innerHTML = h;
}

/* L'adresse retient la vue : ?niveau=zone&province=Ituri&colonnes=rip&q=Bunia */
function adresse(){
  const q = new URLSearchParams();
  if(NIVEAU !== 'pays') q.set('niveau', NIVEAU);
  if(COLV !== 'epi') q.set('colonnes', COLV);
  const p = document.getElementById('fProv').value, r = document.getElementById('fRech').value.trim();
  const du = document.getElementById('fDu').value, au = document.getElementById('fAu').value;
  if(p) q.set('province', p); if(r) q.set('q', r); if(du) q.set('du', du); if(au) q.set('au', au);
  history.replaceState(null, '', location.pathname + (q.toString() ? '?' + q : '') + location.hash);
}

const choisirSeg = (id, v) => document.querySelectorAll(`#${id} button`).forEach(b => b.setAttribute('aria-pressed', b.dataset.v === v));

async function demarrer(){
  const r = await fetch('/data/base-ebola-rdc.json', {cache:'no-store'});
  if(!r.ok) throw new Error(r.status);
  const doc = await r.json();
  META = doc.meta;
  const cles = META.colonnes.map(c => c.cle);
  LIGNES = doc.lignes.map(l => Object.fromEntries(cles.map((k, i) => [k, l[i]])));
  const q = new URLSearchParams(location.search);
  if(['pays', 'province', 'zone', 'tous'].includes(q.get('niveau'))) NIVEAU = q.get('niveau');
  if(['epi', 'rip', 'tout'].includes(q.get('colonnes'))) COLV = q.get('colonnes');
  if(NIVEAU === 'zone') COLV = 'epi';
  interface_();
  if(q.get('province')) document.getElementById('fProv').value = q.get('province');
  if(q.get('q')) document.getElementById('fRech').value = q.get('q');
  if(q.get('du')) document.getElementById('fDu').value = q.get('du');
  if(q.get('au')) document.getElementById('fAu').value = q.get('au');
  filtrer();

  document.getElementById('bddGrille').addEventListener('scroll', () => requestAnimationFrame(() => dessiner(false)));
  document.getElementById('bddThead').addEventListener('click', e => {
    const th = e.target.closest('th[data-k]'); if(!th) return;
    TRI = {k:th.dataset.k, sens: TRI.k === th.dataset.k ? -TRI.sens : (th.dataset.k === 'date' ? -1 : 1)}; filtrer();
  });
  document.getElementById('bNiveau').addEventListener('click', e => {
    const b = e.target.closest('button'); if(!b) return; NIVEAU = b.dataset.v; choisirSeg('bNiveau', NIVEAU);
    if(NIVEAU === 'zone'){ COLV = 'epi'; choisirSeg('bCol', COLV); }
    filtrer();
  });
  document.getElementById('bCol').addEventListener('click', e => {
    const b = e.target.closest('button'); if(!b) return; COLV = b.dataset.v; choisirSeg('bCol', COLV); filtrer();
  });
  ['fProv', 'fDu', 'fAu'].forEach(id => document.getElementById(id).addEventListener('input', filtrer));
  // Taper un nom de zone depuis la vue Pays ou Provinces ne trouverait rien :
  // on passe sur toutes les lignes, colonnes Epidemie.
  document.getElementById('fRech').addEventListener('input', e => {
    const v = norm(e.target.value.trim());
    if(v && (NIVEAU === 'pays' || (NIVEAU === 'province' && !LIGNES.some(o => o.niveau === 'province' && norm(o.province).includes(v))))){
      NIVEAU = 'tous'; choisirSeg('bNiveau', NIVEAU); COLV = 'epi'; choisirSeg('bCol', COLV);
    }
    filtrer();
  });
  document.getElementById('bRaz').addEventListener('click', () => {
    ['fProv', 'fRech', 'fDu', 'fAu'].forEach(id => document.getElementById(id).value = '');
    NIVEAU = 'pays'; COLV = 'epi'; choisirSeg('bNiveau', NIVEAU); choisirSeg('bCol', COLV); filtrer();
  });
}
/* Un lien vers une rubrique depliable (« En savoir plus » -> #erreurs) l'ouvre. */
function ouvrirAncre(){
  const d = location.hash && document.getElementById(location.hash.slice(1));
  if(d && d.tagName === 'DETAILS') d.open = true;
}
addEventListener('hashchange', ouvrirAncre);
ouvrirAncre();

demarrer().catch(e => {
  console.error(e);
  const c = document.querySelector('#bddApp .bdd-charge');
  if(c) c.textContent = T('erreur');
});
