/* Ebola Tracker — logique commune a toutes les pages.
   Extrait de l'ancienne monopage index.html, puis rendu tolerant aux
   elements absents : chaque page ne contient que les blocs qui la
   concernent, le script est le meme partout. */
/* La langue est fixee par la page generee (<html lang="…">) : chaque langue
   a desormais ses propres URL, indexees separement par les moteurs. Plus de
   detection ni de bascule cote client — le selecteur de langue de l'en-tete
   est un vrai lien vers l'URL equivalente dans l'autre langue. */
const currentLang = (document.documentElement.lang || 'fr').toLowerCase().startsWith('en') ? 'en' : 'fr';
function tr(key){ return I18N[currentLang][key]; }

/* ============ PALETTE ============ */
/* Lue une seule fois dans la feuille de style plutot qu'ecrite en dur ici : la
   carte, les graphiques et l'image de partage utilisent donc exactement les
   memes couleurs que le reste du site, et un changement de design n'a qu'un
   seul point d'entree. Les valeurs de repli servent si le CSS n'a pas encore
   ete applique au moment de la lecture. */
const PALETTE = (function(){
  const css = getComputedStyle(document.documentElement);
  const read = (name, fallback) => ((css.getPropertyValue(name) || '').trim() || fallback);
  const scale = ['--scale-0','--scale-1','--scale-2','--scale-3','--scale-4'];
  return {
    bg:        read('--bg', '#FDFAF6'),
    panel:     read('--bg-panel', '#FFFDFB'),
    ink:       read('--ink', '#1F1A13'),
    inkDim:    read('--ink-dim', '#5A544C'),
    inkFaint:  read('--ink-faint', '#777068'),
    line:      read('--line', '#DEDAD5'),
    lineSoft:  read('--line-soft', '#E7E4E0'),
    accent:    read('--accent', '#1B6C8C'),
    info:      read('--accent-info', '#005E82'),
    critical:  read('--accent-critical', '#993A2E'),
    stable:    read('--accent-stable', '#327957'),
    active:    read('--accent-active', '#A06F30'),
    scale:     scale.map((name, i) => read(name, ['#EAE7E3','#B7D3E1','#7EACC3','#317E9F','#005073'][i])),
    font:      "'Public Sans', Helvetica, Arial, sans-serif"
  };
})();

/* Teinte d'accompagnement translucide, pour les aplats sous les courbes. */
function tint(hex, alpha){
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if(!m) return hex;
  const n = parseInt(m[1], 16);
  return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${alpha})`;
}

/* ============ DONNÉES DE RÉFÉRENCE (au 14 août 2026) ============ */
const SEED_SITREPS = [
  { date:"2026-05-16", confirmed:8,    deaths:null, recovered:null },
  { date:"2026-05-31", confirmed:282,  deaths:null, recovered:null },
  { date:"2026-06-06", confirmed:515,  deaths:91,   recovered:12  },
  { date:"2026-06-16", confirmed:827,  deaths:194,  recovered:null },
  { date:"2026-06-18", confirmed:875,  deaths:202,  recovered:null },
  { date:"2026-06-22", confirmed:1048, deaths:267,  recovered:112 },
  { date:"2026-06-24", confirmed:1155, deaths:304,  recovered:null },
  { date:"2026-07-15", confirmed:2100, deaths:800,  recovered:null, approx:true },
  { date:"2026-07-19", confirmed:2423, deaths:967,  recovered:469 },
  { date:"2026-08-01", confirmed:3748, deaths:1657, recovered:708 },
  { date:"2026-08-03", confirmed:3874, deaths:1751, recovered:749 },
  { date:"2026-08-06", confirmed:4053, deaths:1850, recovered:793 },
  { date:"2026-08-08", confirmed:4294, deaths:1960, recovered:849 },
  { date:"2026-08-09", confirmed:4381, deaths:2011, recovered:869 },
  { date:"2026-08-10", confirmed:4449, deaths:2061, recovered:886 },
  { date:"2026-08-11", confirmed:4566, deaths:2128, recovered:918 },
  { date:"2026-08-12", confirmed:4665, deaths:2184, recovered:965 },
  { date:"2026-08-13", confirmed:4727, deaths:2214, recovered:null },
  { date:"2026-08-14", confirmed:4843, deaths:2272, recovered:1006 }
];

const PROVINCES = [
  { name:"Ituri",      share:0.853, epicenter:true },
  { name:"Nord-Kivu",  share:0.119, epicenter:false },
  { name:"Haut-Uélé",  share:0.026, epicenter:false },
  { name:"Tshopo",     share:0.002, epicenter:false },
  { name:"Sud-Kivu",   share:0.001, epicenter:false },
  { name:"Bas-Uélé",   share:0.0002, epicenter:false }
];
/* Répartition par province — INSP RDC, SitRep N°092/MVEBDB du 14/08/2026 (cas et
   décès cumulés, rapport le plus récent disponible) ; statut de transmission :
   Ituri (+85), Nord-Kivu (+19), Haut-Uélé (+12) ont rapporté des nouveaux cas
   confirmés au cours des dernières 24h. Sud-Kivu : aucun nouveau cas signalé —
   70 jours sans nouveau cas au 14 août, soit "inactif" au sens des critères OMS
   de 42 jours, sans être déclaré éradiqué. */
const PROVINCE_TABLE_DATA_SEED = [
  { name:"Ituri",     confirmed:4105, deaths:1791, cfr:43.6,  status:"active-epicenter", healthZonesAffected:{n:28,total:36}, newCases24h:85 },
  { name:"Nord-Kivu", confirmed:588,  deaths:411,  cfr:69.9,  status:"active",           healthZonesAffected:{n:12,total:34}, newCases24h:19 },
  { name:"Haut-Uélé", confirmed:135,  deaths:62,   cfr:45.9,  status:"active",           healthZonesAffected:{n:6, total:13}, newCases24h:12 },
  { name:"Tshopo",    confirmed:11,   deaths:6,    cfr:54.5,  status:"active",           healthZonesAffected:{n:7, total:23}, newCases24h:0  },
  { name:"Sud-Kivu",  confirmed:3,    deaths:1,    cfr:33.3,  status:"inactive", healthZonesAffected:{n:1,total:34}, newCases24h:0 },
  { name:"Bas-Uélé",  confirmed:1,    deaths:1,    cfr:100.0, status:"active",           healthZonesAffected:{n:1, total:11}, newCases24h:0  }
];

/* Indicateurs nationaux complémentaires — SitRep N°092/MVEBDB du 14/08/2026.
   Servent de repli si data/latest.json est indisponible (voir loadRemoteLatest). */
const NATIONAL_SEED = {
  inCTE:777, contactsFollowUpRate:83.2, provincesAffected:6,
  healthZonesAffected:{n:55,total:151}, healthAreasAffected:{n:246,total:3104},
  newCases24h:116, newDeaths24h:58, newDeathsCommunity24h:38, newDeathsIntraCTE24h:20
};

/* Occupation des Centres de Traitement Ebola (CTE) par province — même SitRep.
   Non encore affiché dans l'UI : préparé pour une étape ultérieure. */
const CTE_SEED = [
  { province:"Ituri", bedsInstalled:973, bedsConfirmed:496, bedsSuspect:477, occupiedConfirmed:179, occupiedSuspect:259, admissions24h:83, recovered24h:42, saturatedZonesConfirmed:["Bambu","Nizi"], saturatedZonesSuspect:["Nyankunde","Fataki","Rwankole","Kigonze"] },
  { province:"Nord-Kivu", admissionsCumulative:231, admissions24h:63, admissions24hConfirmed:6, admissions24hSuspect:57, recovered24h:5, deaths24h:10, nonCases24h:36, hospitalized:180, hospitalizedConfirmed:24, hospitalizedSuspect:146 },
  { province:"Haut-Uélé", admissions24h:11, admissions24hConfirmed:1, admissions24hSuspect:10, recovered24h:4, hospitalized:53, hospitalizedConfirmed:31, hospitalizedSuspect:22, bedsInstalled:78, occupancyRate:67.9 },
  { province:"Tshopo", admissions24h:2, admissions24hConfirmed:1, admissions24hSuspect:1, hospitalized:5, bedsInstalled:12, occupancyRate:41.7 },
  { province:"Sud-Kivu", hospitalized:11, hospitalizedDetail:{Katana:7,"Miti-Murhesa":4} }
];

/* Alertes de surveillance par province — même SitRep. Préparé pour une étape ultérieure. */
const SURVEILLANCE_SEED = [
  { province:"Haut-Uélé", alertsReceivedAlive:22, alertsReceivedDead:4, alertsTotal:26, alertsValidatedAlive:17, alertsValidatedDead:4, alertsInvalidatedAlive:5, alertsInvalidatedDead:0, suspectsInvestigated:21, suspectsTransferredCTE:14 },
  { province:"Ituri", alertsReceivedAlive:529, alertsReceivedDead:39, alertsTotal:568, alertsValidatedAlive:124, alertsValidatedDead:38, alertsInvalidatedAlive:270, alertsInvalidatedDead:0, suspectsInvestigated:122, suspectsTransferredCTE:98 },
  { province:"Nord-Kivu", alertsReceivedAlive:824, alertsReceivedDead:58, alertsTotal:882, alertsValidatedAlive:76, alertsValidatedDead:58, alertsInvalidatedAlive:741, alertsInvalidatedDead:0, suspectsInvestigated:132, suspectsTransferredCTE:67 },
  { province:"Sud-Kivu", alertsReceivedAlive:15, alertsReceivedDead:0, alertsTotal:15, alertsValidatedAlive:3, alertsValidatedDead:0, alertsInvalidatedAlive:12, alertsInvalidatedDead:0, suspectsInvestigated:3, suspectsTransferredCTE:3 },
  { province:"Tshopo", alertsReceivedAlive:39, alertsReceivedDead:1, alertsTotal:40, alertsValidatedAlive:7, alertsValidatedDead:1, alertsInvalidatedAlive:32, alertsInvalidatedDead:0, suspectsInvestigated:8, suspectsTransferredCTE:5 }
];
const SURVEILLANCE_TOTAL_SEED = { alertsReceivedAlive:1429, alertsReceivedDead:102, alertsTotal:1531, alertsValidatedAlive:227, alertsValidatedDead:101, alertsInvalidatedAlive:1060, alertsInvalidatedDead:0, suspectsInvestigated:286, suspectsTransferredCTE:187 };

/* Points de contrôle / points d'entrée (PoE/PoC) — même SitRep. Préparé pour une étape ultérieure. */
const POE_POC_SEED = [
  { province:"Ituri", travelersScreened:134082, activePoints:1, activePointsTotal:11 },
  { province:"Haut-Uélé", travelersScreened:18379, screeningRate:99.5, activePoints:10, activePointsTotal:38 },
  { province:"Tshopo", travelersScreened:6152, activePoints:7, activePointsTotal:20, screeningRate:99.3 }
];
const POE_POC_TOTAL_SEED = { travelersScreened:158613, screeningRate:97.4 };

/* Rapports de situation officiels archivés — préparé pour l'onglet "Rapports". */
const REPORTS_SEED = [
  { sitrepNumber:"087", reportingDate:"2026-08-09", publicationDate:"2026-08-10", file:"reports/SITREP_MVE_087.pdf", confirmed:4381, deaths:2011 },
  { sitrepNumber:"088", reportingDate:"2026-08-10", publicationDate:"2026-08-11", file:"reports/SITREP_MVE_088.pdf", confirmed:4449, deaths:2061 },
  { sitrepNumber:"089", reportingDate:"2026-08-11", publicationDate:"2026-08-12", file:"reports/SITREP_MVE_089.pdf", confirmed:4566, deaths:2128 },
  { sitrepNumber:"090", reportingDate:"2026-08-12", publicationDate:"2026-08-13", file:"reports/SITREP_MVE_090.pdf", confirmed:4665, deaths:2184 },
  { sitrepNumber:"091", reportingDate:"2026-08-13", publicationDate:"2026-08-14", file:"reports/SITREP_MVE_091.pdf", confirmed:4727, deaths:2214 },
  { sitrepNumber:"092", reportingDate:"2026-08-14", publicationDate:"2026-08-15", file:"reports/SITREP_MVE_092.pdf", confirmed:4843, deaths:2272 }
];

/* Chronologie des faits clés — même SitRep. Préparé pour une étape ultérieure. */
const TIMELINE_SEED = [
  { date:"2026-04-24", label:"Détection des premiers cas suspects" },
  { date:"2026-05-15", label:"Confirmation biologique du virus Ebola Bundibugyo — déclaration officielle de la 17ᵉ épidémie" },
  { date:"2026-05-17", label:"Déclaration de l'urgence de santé publique de portée nationale" },
  { date:"2026-05-18", label:"Déclaration de l'urgence de santé publique de portée continentale" }
];

/* Répartition par zone de santé — INSP RDC, SitRep N°090/MVEBDB du 12/08/2026.
   Ce SitRep publie pour la première fois le détail cumulé zone par zone pour les
   6 provinces touchées (pas seulement l'Ituri) : le total de chaque province
   correspond exactement à son total agrégé affiché ailleurs sur le site. */
/* [nom, cas cumulés, province, décès cumulés, nouveaux cas (24h), décès communautaires (24h), décès intra-CTE (24h)] */
const HEALTH_ZONES_SEED = [
  ["Nyankunde",120,"Ituri",35,0,0,0],["Rimba",9,"Ituri",4,0,0,0],["Rwampara",838,"Ituri",324,15,5,0],
  ["Tchomia",49,"Ituri",25,0,0,0],["Beni",90,"Nord-Kivu",66,4,1,0],["Butembo",110,"Nord-Kivu",91,2,0,0],
  ["Kalunguta",12,"Nord-Kivu",5,1,0,0],["Katwa",280,"Nord-Kivu",190,6,1,1],["Kyondo",15,"Nord-Kivu",12,1,0,0],
  ["Lubero",1,"Nord-Kivu",1,0,0,0],["Mabalako",2,"Nord-Kivu",1,0,0,0],["Masereka",7,"Nord-Kivu",4,0,0,0],
  ["Musienene",61,"Nord-Kivu",35,5,3,0],["Oicha",5,"Nord-Kivu",4,0,0,0],["Vuhovi",4,"Nord-Kivu",2,0,0,1],
  ["Boma Mangbetu",22,"Haut-Uélé",8,0,0,2],["Gombari",1,"Haut-Uélé",1,0,0,0],["Isiro",39,"Haut-Uélé",19,0,0,0],
  ["Pawa",19,"Haut-Uélé",14,0,0,0],["Wamba",53,"Haut-Uélé",20,12,2,1],["Kabondo",3,"Tshopo",2,0,0,0],
  ["Makiso-Kisangani",3,"Tshopo",3,0,0,0],["Mangobo",1,"Tshopo",1,0,0,0],["Miti-Murhesa",3,"Sud-Kivu",1,0,0,0],
  ["Buta",1,"Bas-Uélé",1,0,0,0],["Adja",11,"Ituri",1,0,0,0],["Aru",7,"Ituri",6,0,0,0],
  ["Ariwara",7,"Ituri",2,0,0,0],["Aungba",11,"Ituri",5,1,0,0],["Bambu",109,"Ituri",25,5,3,3],
  ["Boga",1,"Ituri",1,0,0,0],["Bunia",1116,"Ituri",338,16,5,5],["Damas",23,"Ituri",9,2,0,0],
  ["Drodro",13,"Ituri",6,0,0,0],["Fataki",63,"Ituri",30,1,0,0],["Gety",4,"Ituri",1,2,0,0],
  ["Kambala",2,"Ituri",0,0,0,0],["Kilo",31,"Ituri",12,0,0,0],["Komanda",45,"Ituri",31,2,2,2],
  ["Lita",172,"Ituri",97,3,0,0],["Logo",11,"Ituri",5,0,0,0],["Lolwa",14,"Ituri",4,0,0,0],
  ["Mahagi",4,"Ituri",1,0,0,0],["Mambasa",13,"Ituri",6,0,0,0],["Mandima",22,"Ituri",13,0,0,0],
  ["Mangala",141,"Ituri",83,19,7,7],["Mongbwalu",584,"Ituri",282,3,0,0],["Nia Nia",161,"Ituri",96,5,4,4],
  ["Nizi",524,"Ituri",236,11,5,5],["Goma",1,"Nord-Kivu",0,0,0,0],["Rungu",1,"Haut-Uélé",0,0,0,0],
  ["Bafwasende",1,"Tshopo",0,0,0,0],["Lubunga",1,"Tshopo",0,0,0,0],["Wanie-Rukula",1,"Tshopo",0,0,0,0]
].map(([name,cases,province,deaths,newCases24h,deathsCommunity24h,deathsIntraCTE24h])=>{
  const cfr = cases>0 ? +(deaths/cases*100).toFixed(1) : 0;
  return {name,cases,province,deaths,cfr,newCases24h,deathsCommunity24h,deathsIntraCTE24h};
});

/* Coordonnées approximatives des chefs-lieux de zone de santé, à des fins de
   visualisation — non issues d'un référentiel géographique officiel. Les zones
   d'Ituri sont assez fiables ; celles des autres provinces (ajoutées avec le
   SitRep N°090) sont des estimations moins précises, notamment pour les petites
   zones rurales du Haut-Uélé, de la Tshopo et du Sud-Kivu. */
/* Coordonnées corrigées le 17/08/2026 pour 19 zones via géocodage Nominatim
   (résultat dans la même province attendue, écart < 15 km avec l'ancienne
   estimation manuelle — voir scripts/geocode_health_zones.py). Les autres
   zones gardent leur estimation manuelle d'origine : soit le géocodage a
   renvoyé un homonyme dans une autre province (rejeté), soit un écart trop
   important dans la bonne province pour être appliqué sans vérification
   manuelle au cas par cas. Corrections du 17/08/2026 (3e passe) : 20 zones
   recalées sur un point garanti à l'intérieur de leur polygone officiel
   (HDX/OCHA, 519 zones de santé), uniquement là où ce point confirme le
   géocodage précédent (écart ≤15 km) — voir
   scripts/extract_health_zone_polygons.py. Les zones avec un écart
   important gardent leur position géocodée (probablement plus proche du
   bourg principal que le centre géométrique d'une grande zone irrégulière). */
const HEALTH_ZONE_COORDS = {
  "Bunia":[1.600,30.223], "Mongbwalu":[1.937,30.046], "Rwampara":[1.570,30.050],
  "Nizi":[1.729440,30.314455], "Lita":[1.65083,30.3511], "Nyankunde":[1.432525,30.029249],
  "Mangala":[1.95,30.25], "Nia Nia":[1.403507,27.614536], "Nia-Nia":[1.403507,27.614536], "Bambu":[1.80,30.2333],
  "Tchomia":[1.439591,30.478381], "Komanda":[1.362748,29.776272], "Kilo":[1.7974634611906029,30.225959540126386],
  "Fataki":[1.989241,30.565209], "Damas":[2.11130,30.10666], "Mandima":[1.346098,29.079158],
  "Adja":[3.01556,30.48028], "Drodro":[1.757552,30.542300], "Aungba":[2.549597,30.510272],
  "Logo":[2.205690,30.961575], "Mambasa":[1.359516,29.029140], "Rimba":[2.21727,30.65683],
  "Ariwara":[3.1374733302027606,30.705920358554426], "Lolwa":[1.351236,29.495759], "Aru":[2.859120,30.838451],
  "Mahagi":[2.307429,30.972622], "Kambala":[2.10,30.85], "Boga":[1.027596,29.954138],
  "Gety":[1.196007,30.167813], "Gethy":[1.196007,30.167813],
  "Beni":[0.490000,29.450000], "Butembo":[0.12750136509401047,29.29813274506823], "Goma":[-1.654,29.181],
  "Kalunguta":[0.3230854,29.3546773], "Katwa":[0.09321,29.31049], "Kyondo":[0.000056,29.409299],
  "Lubero":[-0.15445200325751043,29.241441551971747], "Mabalako":[0.462482,29.214432], "Masereka":[-0.139346,29.317167],
  "Musienene":[0.012396,29.253853], "Oicha":[0.697529,29.518461], "Vuhovi":[0.142500,29.406111],
  "Isiro":[2.774,27.621], "Wamba":[2.147109,27.983079], "Boma Mangbetu":[2.85,28.30],
  "Pawa":[2.411152,27.611239], "Rungu":[3.189322,27.872400], "Gombari":[2.705090,29.039446],
  "Bafwasende":[0.9995547589572337,27.15772063308612], "Kabondo":[0.530,25.223], "Lubunga":[0.486,25.188],
  "Makiso-Kisangani":[0.485,25.278], "Makiso--Kisangani":[0.485,25.278], "Mangobo":[0.523217,25.147176], "Wanie-Rukula":[0.199287,25.530352],
  "Miti-Murhesa":[-2.359276378701031,28.80003177502664],
  "Buta":[2.793,24.729],
  "Viadana":[2.8736143001709826,27.211588434391334]
};
/* Chefs-lieux provinciaux, utilisés uniquement pour représenter les totaux
   agrégés des provinces sans détail public par zone de santé. */
const PROVINCE_AGG_COORDS = {
  "Nord-Kivu":[-1.6796,29.2267],
  "Sud-Kivu":[-2.5085,28.8608],
  "Haut-Uélé":[2.7833,27.6167],
  "Tshopo":[0.5167,25.2],
  "Bas-Uélé":[2.795,24.734]
};
// Repère fixe pour la capitale — pas lié aux données épidémiques, affiché
// en permanence (aujourd'hui comme sur le curseur temporel), contrairement
// aux cercles de zone dont la taille/couleur varie avec les cas.
const KINSHASA_COORDS = [-4.4419,15.2663];
const KAMPALA_COORDS = [0.3476,32.5825];
const KAMPALA_DATA = {
  cases: 20, deaths: 2,
  lastCaseDate: "2026-06-16",
  declaredFreeDate: "2026-07-28"
};
// Date à partir de laquelle Kampala apparaît sur le curseur temporel de la
// carte : alignée sur la première date disponible pour les autres cercles
// (SitRep N°007, 21 mai), pas sur la date réelle du 1er cas (15 mai), par
// souci de cohérence visuelle avec le reste des données historiques.
const KAMPALA_TIMELINE_START = "2026-05-21";
// Nouveaux cas par date, source : autorités ougandaises. Permet de calculer
// le cumul réel à afficher (taille du cercle + KPI du popup) selon la date
// scrutée sur le curseur temporel, plutôt qu'un total fixe. La somme des
// newCases doit toujours égaler KAMPALA_DATA.cases (20) — vérifié.
const KAMPALA_CASE_TIMELINE = [
  { date:"2026-05-15", newCases:2 },
  { date:"2026-05-22", newCases:3 },
  { date:"2026-05-23", newCases:2 },
  { date:"2026-05-29", newCases:2 },
  { date:"2026-05-31", newCases:2 },
  { date:"2026-06-02", newCases:4 },
  { date:"2026-06-04", newCases:1 },
  { date:"2026-06-06", newCases:3 },
  { date:"2026-06-16", newCases:1 }
];
function kampalaCasesAt(dateStr){
  return KAMPALA_CASE_TIMELINE
    .filter(e=>e.date<=dateStr)
    .reduce((sum,e)=>sum+e.newCases, 0);
}
function kampalaDeathsAt(dateStr){
  // Pas de détail des décès par date disponible : on affiche le total
  // final uniquement une fois la dernière date connue atteinte, plutôt que
  // de risquer une létalité trompeuse (ex: "2 cas, 2 décès") en early view.
  const lastDate = KAMPALA_CASE_TIMELINE[KAMPALA_CASE_TIMELINE.length-1].date;
  return dateStr >= lastDate ? KAMPALA_DATA.deaths : null;
}

/* Les bulletins successifs orthographient parfois la même zone différemment
   d'un SitRep à l'autre (ex: "Nia Nia" vs "Nia-Nia", "Makiso-Kisangani" vs
   "Makiso--Kisangani") : espace, tiret simple ou double, casse. Plutôt que de
   maintenir une liste d'alias qui grandit à chaque nouvelle variante
   rencontrée, on normalise (espaces/tirets réduits à un seul espace,
   minuscules) avant toute recherche dans HEALTH_ZONE_COORDS, côté clé du
   dictionnaire ET côté nom recherché. Un cercle qui "apparaît et disparaît"
   sur le curseur temporel est presque toujours ce problème : la zone existe
   bien dans les données, mais son nom exact ne correspondait à aucune clé
   pour CE SitRep précis. */
function normalizeZoneName(name){
  return (name || '').trim().toLowerCase().replace(/[\s-]+/g, ' ');
}
const HEALTH_ZONE_COORDS_NORMALIZED = {};
for(const [key, coord] of Object.entries(HEALTH_ZONE_COORDS)){
  HEALTH_ZONE_COORDS_NORMALIZED[normalizeZoneName(key)] = coord;
}
function lookupZoneCoord(name){
  return HEALTH_ZONE_COORDS[name] || HEALTH_ZONE_COORDS_NORMALIZED[normalizeZoneName(name)];
}

const ITURI_BOUNDS = [[0.7,27.4],[3.3,31.2]];
const DRC_BOUNDS = [[-13.459,12.204],[5.386,33.2]];

/* ============ ÉTAT ============ */
let sitreps = [...SEED_SITREPS];
let PROVINCE_TABLE_DATA = PROVINCE_TABLE_DATA_SEED;
let HEALTH_ZONES = HEALTH_ZONES_SEED;

/* Les pages vivent desormais dans des sous-repertoires (/rapports/,
   /en/data/, /provinces/ituri/...) : tout chemin vers un fichier du depot
   doit partir de la racine, sinon il serait resolu relativement a la page
   courante. */
function assetUrl(path){
  if(!path) return '#';
  if(/^https?:\/\//.test(path)) return path;
  return '/' + String(path).replace(/^\/+/, '');
}

async function loadRemoteSitreps(){
  try{
    const res = await fetch('/data/sitreps.json', { cache:'no-store' });
    if(!res.ok) return;
    const remote = await res.json();
    if(Array.isArray(remote) && remote.length){
      sitreps = remote;
    }
  }catch(e){
    // Pas de connexion, fichier ouvert en local (file://), ou hébergement sans ce
    // fichier : on garde silencieusement les données de référence intégrées.
    console.warn('data/sitreps.json indisponible, utilisation des données de référence intégrées.', e);
  }
}
/* national/cte/surveillance/poePoc/timeline : variables mutables, écrasées par
   data/latest.json si disponible, sinon on garde les *_SEED ci-dessus. */
let national = NATIONAL_SEED;
let cteData = CTE_SEED;
let surveillanceData = SURVEILLANCE_SEED;
let surveillanceTotal = SURVEILLANCE_TOTAL_SEED;
let poePocData = POE_POC_SEED;
let poePocTotal = POE_POC_TOTAL_SEED;
let reportsData = REPORTS_SEED;
let whoReportsData = [];
let timelineData = TIMELINE_SEED;
let currentMeta = null;

/* Historique par zone (extraction rétrospective des SitRep archivés) — utilisé
   uniquement pour le curseur temporel de la carte. Pas de repli intégré : si le
   fichier est indisponible, le curseur reste simplement masqué. */
let ZONES_HISTORY = [];
async function loadZonesHistory(){
  try{
    const res = await fetch('/data/zones-history.json', { cache:'no-store' });
    if(!res.ok) return;
    const remote = await res.json();
    if(Array.isArray(remote) && remote.length){
      ZONES_HISTORY = [...remote].sort((a,b)=> a.date < b.date ? -1 : a.date > b.date ? 1 : 0);
    }
  }catch(e){
    console.warn('data/zones-history.json indisponible, curseur temporel masqué.', e);
  }
}

/* Décès communautaires vs intra-CTE, deltas quotidiens (pas un cumul —
   voir scripts/extract_community_deaths.py). Fenêtre partielle de
   l'épidémie seulement (pas depuis le début) : pas de repli intégré, si le
   fichier est indisponible l'onglet correspondant affiche un état vide. */
let COMMUNITY_DEATHS_DAILY = [];
async function loadCommunityDeathsDaily(){
  try{
    const res = await fetch('/data/community-deaths-daily.json', { cache:'no-store' });
    if(!res.ok) return;
    const remote = await res.json();
    if(Array.isArray(remote) && remote.length){
      COMMUNITY_DEATHS_DAILY = [...remote].sort((a,b)=> a.date < b.date ? -1 : a.date > b.date ? 1 : 0);
    }
  }catch(e){
    console.warn('data/community-deaths-daily.json indisponible.', e);
  }
}

/* Points de situation publiés sur les réseaux sociaux (X/Twitter) par une
   source officielle, entre deux SitRep PDF — fichier séparé de latest.json,
   jamais touché par le pipeline PDF habituel (update_data.py), pour éviter
   tout risque d'écrasement accidentel. N'inclut que les chiffres nationaux
   globaux (confirmed/deaths/recovered/inCTE), jamais de détail par
   zone/province, puisque ce niveau de détail n'existe pas dans un tweet. */
let SOCIAL_UPDATES = [];
async function loadSocialUpdates(){
  try{
    const res = await fetch('/data/social-updates.json', { cache:'no-store' });
    if(!res.ok) return;
    const remote = await res.json();
    if(Array.isArray(remote) && remote.length){
      SOCIAL_UPDATES = [...remote].sort((a,b)=> a.date < b.date ? -1 : a.date > b.date ? 1 : 0);
    }
  }catch(e){
    console.warn('data/social-updates.json indisponible.', e);
  }
}

/* Taux de suivi des contacts (%) — extrait des SitRep INSP, complété
   ponctuellement par une lecture manuelle des rapports hebdomadaires OMS
   quand le SitRep INSP correspondant n'a pas cette donnée (voir le champ
   "source" de chaque entrée). Affiché sans distinction visuelle entre les
   deux origines — inutile pour la lecture du graphique lui-même. */
/* Historique quotidien des cas confirmés cumulés par province, pour le
   graphique "Cas cumulés par province" — voir rebuild_province_history()
   côté pipeline. Toujours complet par construction (le total provincial
   est présent dans chaque SitRep), aucun trou de données attendu. */

/* Les bulletins n'orthographient pas toujours les provinces de la meme
   facon : le releve du 14 aout 2026 ecrit « Haut Uele » sans trait d'union.
   Les noms etant compares a l'identique aux cles de PROVINCE_COLORS, ce
   point etait silencieusement perdu — la courbe cumulee passait de 123 a
   138 sans passer par 135, masque par spanGaps. Sur des barres
   quotidiennes, la meme variante fausserait deux journees d'affilee.
   On normalise donc a l'entree, une fois, pour tous les consommateurs. */
function nomProvinceCanonique(nom){
  const plat = (nom || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z]/g, '');
  for(const officiel of Object.keys(PROVINCE_COLORS)){
    const ref = officiel.normalize('NFD').replace(/[̀-ͯ]/g, '')
      .toLowerCase().replace(/[^a-z]/g, '');
    if(ref === plat) return officiel;
  }
  return nom;
}

let PROVINCE_HISTORY = [];
async function loadProvinceHistory(){
  try{
    const res = await fetch('/data/province-history.json', { cache:'no-store' });
    if(!res.ok) return;
    const remote = await res.json();
    if(Array.isArray(remote) && remote.length){
      PROVINCE_HISTORY = [...remote]
        .sort((a,b)=> a.date < b.date ? -1 : a.date > b.date ? 1 : 0)
        .map(h => ({...h, provinces: (h.provinces || []).map(
          pr => ({...pr, name: nomProvinceCanonique(pr.name)}))}));
    }
  }catch(e){
    console.warn('data/province-history.json indisponible.', e);
  }
}

/* Repartition des deces entre communaute et centre de traitement, par
   province — voir scripts/extraire_deces_lieu.py. Fenetre bornee : les
   bulletins anterieurs au 13 juillet 2026 ne distinguent pas le lieu. */
let DECES_LIEU = null;
async function loadDecesLieu(){
  try{
    const res = await fetch('/data/deces-lieu.json', { cache:'no-store' });
    if(!res.ok) return;
    const remote = await res.json();
    if(remote && Array.isArray(remote.provinces)) DECES_LIEU = remote;
  }catch(e){
    console.warn('data/deces-lieu.json indisponible.', e);
  }
}

let CONTACTS_FOLLOWUP = [];
async function loadContactsFollowup(){
  try{
    const res = await fetch('/data/contacts-followup.json', { cache:'no-store' });
    if(!res.ok) return;
    const remote = await res.json();
    if(Array.isArray(remote) && remote.length){
      CONTACTS_FOLLOWUP = [...remote].sort((a,b)=> a.date < b.date ? -1 : a.date > b.date ? 1 : 0);
    }
  }catch(e){
    console.warn('data/contacts-followup.json indisponible.', e);
  }
}

/* Répartition par âge des cas et des décès. Contrairement aux autres séries,
   c'est un INSTANTANÉ et non un historique : l'INSP a cessé de publier la
   figure dont il est tiré après le 5 août 2026. Le graphique porte donc sa
   date, et le mode reste absent tant que le fichier n'est pas chargé. */
let DEMOGRAPHIE = null;

/* Les deux modes « age » et « sexe » lisent les MEMES deux figures : meme
   echantillon, donc meme denominateur et meme mise en garde. Une seule note
   pour les deux evite d'avoir deux verites a maintenir pour une seule donnee.
   fmt() applique le separateur de milliers du site — « 3 454 », pas « 3454 ». */
/* Le partage femmes/hommes des cas contre celui des deces : 3,3 points
   d'ecart, que ni la pyramide ni aucune barre ne rendent lisibles — il
   faudrait sommer cinq tranches a l'oeil. Une phrase le donne exactement, et
   ouvre la note plutot que de se perdre au milieu des mises en garde. */
function phraseSexe(){
  if(!DEMOGRAPHIE || !DEMOGRAPHIE.parSexe) return '';
  return tr('chartPyramideSexe')(DEMOGRAPHIE.parSexe.cas.partFeminin,
                                 DEMOGRAPHIE.parSexe.deces.partFeminin);
}
function noteDemographie(){
  if(!DEMOGRAPHIE) return '';
  /* Une seule date, portant l'annee. La note en donnait deux : elle ouvrait
     sur « instantane, non actualise depuis » et se fermait sur « l'INSP a
     cesse de publier cette repartition apres le 5 aout 2026 » — deux facons
     de dire la meme chose a quatre phrases d'intervalle. Fondues en une, la
     cause et la consequence tiennent ensemble : la serie s'arrete la parce
     que la source s'y est arretee. */
  const avecAnnee = frDate(DEMOGRAPHIE.date) + ' ' + DEMOGRAPHIE.date.slice(0, 4);
  return tr('chartNoteDemographie')(
    avecAnnee, fmt(DEMOGRAPHIE.totaux.cas), fmt(DEMOGRAPHIE.totaux.deces),
    DEMOGRAPHIE.couverture.partCas, DEMOGRAPHIE.couverture.partDeces);
}
async function loadDemographie(){
  try{
    const res = await fetch('/data/demographie.json', { cache:'no-store' });
    if(!res.ok) return;
    const remote = await res.json();
    if(remote && Array.isArray(remote.tranches) && remote.tranches.length){
      DEMOGRAPHIE = remote;
    }
  }catch(e){
    console.warn('data/demographie.json indisponible.', e);
  }
}


/* Détermine la source la plus récente pour les 4 chiffres nationaux
   affichés en cases d'en-tête : le dernier SitRep PDF (currentMeta) ou le
   dernier point de situation X/Twitter, selon lequel est postérieur.
   Le reste du site (carte, tableaux, provinces) continue TOUJOURS de
   refléter uniquement le SitRep PDF le plus récent — ce niveau de détail
   n'existe simplement pas dans un tweet. */
function effectiveNationalKPIs(){
  const pdfDate = currentMeta ? currentMeta.reportingDate : null;
  const pdfData = (national && pdfDate) ? {
    date: pdfDate,
    confirmed: national.confirmed, deaths: national.deaths,
    recovered: national.recovered, inCTE: national.inCTE,
    isSocialSource: false,
  } : null;

  const lastSocial = SOCIAL_UPDATES.length ? SOCIAL_UPDATES[SOCIAL_UPDATES.length-1] : null;
  const socialData = lastSocial ? {
    date: lastSocial.date,
    confirmed: lastSocial.confirmed, deaths: lastSocial.deaths,
    recovered: lastSocial.recovered, inCTE: lastSocial.inCTE,
    isSocialSource: true, sourceLabel: lastSocial.source, sourceUrl: lastSocial.url,
  } : null;

  if(!pdfData) return socialData;
  if(!socialData) return pdfData;
  return socialData.date > pdfData.date ? socialData : pdfData;
}

/* Regroupe les deltas quotidiens en semaines calendaires (lundi-dimanche).
   Un jour manquant dans une semaine réduit juste le total de CETTE semaine
   (pas d'effet cumulatif sur les semaines suivantes). */
function aggregateWeeklyCommunityDeaths(){
  function weekStartOf(dateStr){
    const d = new Date(dateStr+'T00:00:00');
    const day = (d.getDay()+6)%7; // lundi=0 ... dimanche=6
    d.setDate(d.getDate()-day);
    return d.toISOString().slice(0,10);
  }
  const weeks = {};
  for(const entry of COMMUNITY_DEATHS_DAILY){
    const ws = weekStartOf(entry.date);
    if(!weeks[ws]) weeks[ws] = { community:0, intra:0, daysReported:0 };
    weeks[ws].community += entry.nationalCommunityDeaths || 0;
    weeks[ws].intra += entry.nationalIntraCteDeaths || 0;
    weeks[ws].daysReported += 1;
  }
  return Object.keys(weeks).sort().map(ws => ({
    weekStart: ws,
    community: weeks[ws].community,
    intra: weeks[ws].intra,
    total: weeks[ws].community + weeks[ws].intra,
    daysReported: weeks[ws].daysReported
  }));
}

async function loadRemoteLatest(){
  try{
    const res = await fetch('/data/latest.json', { cache:'no-store' });
    if(!res.ok) return;
    const remote = await res.json();
    if(remote.national) national = remote.national;
    if(remote.cte) cteData = remote.cte;
    if(remote.surveillance) surveillanceData = remote.surveillance;
    if(remote.surveillanceTotal) surveillanceTotal = remote.surveillanceTotal;
    if(remote.poePoc) poePocData = remote.poePoc;
    if(remote.poePocTotal) poePocTotal = remote.poePocTotal;
    if(remote.reports) reportsData = remote.reports;
    if(remote.timeline) timelineData = remote.timeline;
    if(remote.provinces) PROVINCE_TABLE_DATA = remote.provinces;
    if(remote.healthZones && remote.healthZones.length) HEALTH_ZONES = remote.healthZones;
    if(remote.meta) currentMeta = remote.meta;
    // provinces (PROVINCE_TABLE_DATA) et zones de santé (HEALTH_ZONES) sont
    // désormais elles aussi pilotées par ce fichier quand il est disponible.
  }catch(e){
    console.warn('data/latest.json indisponible, utilisation des données de référence intégrées.', e);
  }
}

async function loadRemoteWhoReports(){
  // Source distincte de latest.json (donc fichier séparé) : ne doit jamais
  // être mélangée avec reportsData (INSP) dans le même tableau — deux
  // organismes différents, deux rythmes de publication différents.
  try{
    const res = await fetch('/data/who-reports.json', { cache:'no-store' });
    if(!res.ok) return;
    whoReportsData = await res.json();
  }catch(e){
    console.warn('data/who-reports.json indisponible.', e);
  }
}

/* Une page peut porter plusieurs graphiques : l'instance Chart.js et le
   dernier mode rendu sont donc ranges par canvas, et non dans une variable
   unique. Chaque canvas declare ce qu'il montre via data-chart. */
const chartSlots = {};
function chartSlot(canvas){
  const key = canvas.id || canvas.dataset.chart;
  return chartSlots[key] || (chartSlots[key] = { chart: null, lastMode: null });
}

function sortedSitreps(){
  return [...sitreps].filter(s=>s.date).sort((a,b)=>a.date.localeCompare(b.date));
}

/* Ajoute un point supplémentaire venant du dernier point de situation
   X/Twitter (SOCIAL_UPDATES), UNIQUEMENT si sa date est postérieure au
   dernier SitRep PDF déjà traité — pour les graphiques "Cas/décès
   cumulés" et "Nouveaux cas par jour" seulement (pas les cases d'en-tête,
   qui ont leur propre logique via effectiveNationalKPIs, ni la date
   "dernières données disponibles", qui reste volontairement basée sur le
   SitRep PDF). Dès qu'un vrai SitRep couvrant cette date est traité par le
   pipeline normal, il apparaît dans sitreps.json et ce point supplémentaire
   disparaît de lui-même — aucune action manuelle nécessaire. */
function sortedSitrepsWithSocial(){
  const base = sortedSitreps();
  const lastSocial = SOCIAL_UPDATES.length ? SOCIAL_UPDATES[SOCIAL_UPDATES.length-1] : null;
  if(!lastSocial) return base;
  const lastBaseDate = base.length ? base[base.length-1].date : null;
  if(lastBaseDate && lastSocial.date <= lastBaseDate) return base;
  return [...base, {
    date: lastSocial.date,
    confirmed: lastSocial.confirmed,
    deaths: lastSocial.deaths,
    recovered: lastSocial.recovered,
  }];
}

/* ============ RENDU KPI ============ */
function fmt(n){ return (n===null||n===undefined) ? '—' : n.toLocaleString(tr('locale')); }

/* Un taux en pourcentage, dans la typographie de la langue : « 48,0 % » en
   francais, « 48.0% » en anglais. Le generateur ecrit exactement la meme
   chaine dans les memes elements (fmt_cfr() dans build_pages.py) — les deux
   se corrigent ensemble, sinon un taux change d'ecriture au chargement. */
function fmtCfr(v){
  if(v===null||v===undefined) return '—';
  const t = Number(v).toFixed(1);
  return currentLang === 'fr' ? t.replace('.', ',') + ' %' : t + '%';
}

function renderKPIs(){
  // Les chiffres ne sont plus lies a un emplacement precis : ils vivent
  // partout ou un element porte data-kpi. Sans aucun, il n'y a rien a faire.
  if(!document.querySelector('[data-kpi]')) return;
  const s = sortedSitreps();
  const latest = s[s.length-1];

  function lastKnown(field){
    for(let i=s.length-1;i>=0;i--){
      if(s[i][field]!==null && s[i][field]!==undefined) return s[i];
    }
    return null;
  }
  function prevKnown(field, fromEntry){
    const idx = s.indexOf(fromEntry);
    for(let i=idx-1;i>=0;i--){
      if(s[i][field]!==null && s[i][field]!==undefined) return s[i];
    }
    return null;
  }

  const confirmedEntry = lastKnown('confirmed');
  const deathsEntry = lastKnown('deaths');
  const recoveredEntry = lastKnown('recovered');

  // Les 4 cases ci-dessous préfèrent le point de situation X/Twitter le
  // plus récent s'il est POSTÉRIEUR au dernier SitRep PDF (voir
  // effectiveNationalKPIs) — la carte et les tableaux, eux, continuent
  // toujours de refléter uniquement le dernier SitRep PDF, ce niveau de
  // détail n'existant pas dans un tweet.
  const eff = effectiveNationalKPIs();
  const usingSocial = eff && eff.isSocialSource;

  // Un meme chiffre peut vivre a plusieurs endroits de la page — le bandeau
  // superieur et le panneau a droite de la carte. On les met tous a jour.
  const setKpi = (key, value)=>{
    document.querySelectorAll(`[data-kpi="${key}"]`).forEach(el=>{ el.textContent = value; });
  };
  setKpi('confirmed', usingSocial ? fmt(eff.confirmed) : (confirmedEntry ? fmt(confirmedEntry.confirmed) : '—'));
  setKpi('deaths', usingSocial ? fmt(eff.deaths) : (deathsEntry ? fmt(deathsEntry.deaths) : '—'));
  setKpi('recovered', usingSocial ? fmt(eff.recovered) : (recoveredEntry ? fmt(recoveredEntry.recovered) : '—'));
  setKpi('active', usingSocial ? fmt(eff.inCTE) : ((national && national.inCTE!=null) ? fmt(national.inCTE) : '—'));
  const cfrBase = usingSocial ? eff : (deathsEntry && confirmedEntry ? {confirmed:confirmedEntry.confirmed, deaths:deathsEntry.deaths} : null);
  const cfr = (cfrBase && cfrBase.confirmed>0) ? (cfrBase.deaths/cfrBase.confirmed*100) : null;
  setKpi('cfr', fmtCfr(cfr));

  /* Ecart avec le bulletin precedent. En mode « point de situation reseaux
     sociaux », on compare au dernier SitRep connu, ce point n'ayant pas sa
     propre place dans la serie. */
  function deltaValue(field, entry){
    if(usingSocial){
      if(!latest || latest[field] == null) return null;
      return eff[field] - latest[field];
    }
    if(!entry) return null;
    const prev = prevKnown(field, entry);
    if(!prev) return null;
    return entry[field] - prev[field];
  }
  const setKpiDelta = (key, value)=>{
    const text = (value === null || value === undefined)
      ? '' : '(+' + fmt(Math.max(0, value)) + ')';
    document.querySelectorAll(`[data-kpi-delta="${key}"]`).forEach(el=>{
      el.textContent = text;
    });
  };
  setKpiDelta('confirmed', deltaValue('confirmed', confirmedEntry));
  setKpiDelta('deaths', deltaValue('deaths', deathsEntry));
  setKpiDelta('recovered', deltaValue('recovered', recoveredEntry));
}

function frDate(iso){
  if(!iso) return tr('reportsUnknownDate') || '—';
  const [y,m,d] = iso.split('-');
  const mois = tr('months');
  return `${parseInt(d,10)} ${mois[parseInt(m,10)-1]}`;
}

/* ============ GRAPHIQUE ============ */
let chartMode = 'epidemic';
/* Vue de la pyramide : « effectifs » (deux figures) ou « parts » (une
   seule, chaque serie ramenee a 100 % de son propre total). */
let pyramideVue = 'effectifs';
/* Rend un graphique dans le canvas donne. Le mode dit ce qu'il montre. */
function renderOneChart(canvas, chartMode){
  const slot = chartSlot(canvas);
  if(typeof Chart === 'undefined'){
    canvas.replaceWith(Object.assign(document.createElement('div'), {
      style:'display:flex;align-items:center;justify-content:center;height:100%;font-family:var(--font-mono);font-size:12px;color:var(--ink-faint);',
      textContent: tr('chartLoadError')
    }));
    return;
  }
  const s = sortedSitrepsWithSocial();
  const subEl = document.getElementById('chartSubText');
  if(subEl && s.length){
    subEl.textContent = tr('chartSub') + ' · ' + tr('chartSubRange')(s.length, frDate(s[0].date), frDate(s[s.length-1].date));
  }
  const wrap = canvas.closest('.chart-panel-wrap');
  const noteEl = wrap ? wrap.querySelector('.chart-note') : null;

  /* Second cadre : il n'existe que sur la page Donnees, et n'appartient qu'a
     la pyramide, seul mode a tracer deux figures. Tout autre mode le referme
     et detruit son graphique — sans quoi il resterait ouvert et vide apres un
     changement d'onglet. */
  const navVue = wrap ? wrap.querySelector('[data-pyramide-vue]') : null;
  if(navVue) navVue.style.display = (chartMode === 'pyramide') ? '' : 'none';
  /* La vue « Parts » loge dix barres la ou les autres modes en logent cinq :
     elle reclame un cadre plus haut, sans quoi l'axe des ages saute un
     libelle sur deux des que l'ecran retrecit. Le cadre reprend sa hauteur
     ordinaire pour tout le reste. */
  const panneau1 = canvas.closest('.chart-panel');
  if(panneau1) panneau1.classList.remove('is-parts');
  const canvasB = canvas.id ? document.getElementById(canvas.id + 'B') : null;
  if(canvasB && chartMode !== 'pyramide'){
    const slotB = chartSlot(canvasB);
    if(slotB.chart){ slotB.chart.destroy(); slotB.chart = null; slotB.lastMode = null; }
    const panneauB = canvasB.closest('.chart-panel');
    if(panneauB) panneauB.style.display = 'none';
  }
  if(noteEl){
    noteEl.textContent = ''; noteEl.style.display = 'none';
  }

  // Mode "Sexe" : deux barres empilées à 100%, cas puis décès. Un camembert
  // aurait été plus familier, mais l'écart à montrer est de 3,3 points — 12°
  // d'arc, invisibles, et illisibles d'un cercle à l'autre. Empilées sur une
  // base commune, les deux barres rendent le décalage lisible au décrochage
  // de la frontière entre les deux couleurs.
  if(chartMode==='sexes'){
    const wantedType = 'bar';
    if(slot.chart && (slot.chart.config.type !== wantedType || slot.lastMode !== 'sexes')){
      slot.chart.destroy();
      slot.chart = null;
    }
    if(!DEMOGRAPHIE || !DEMOGRAPHIE.parSexe){
      if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
      slot.lastMode = 'sexes';
      const ctx0 = canvas.getContext('2d');
      ctx0.clearRect(0,0,canvas.width,canvas.height);
      return;
    }

    const ps = DEMOGRAPHIE.parSexe;
    const effectifs = {
      [tr('chartSexCases')]:  { f:ps.cas.feminin,   h:ps.cas.masculin },
      [tr('chartSexDeaths')]: { f:ps.deces.feminin, h:ps.deces.masculin },
    };
    // Deux paliers de l'échelle bleue du site, et non deux couleurs neuves :
    // aucune des deux ne suggère une valeur, et le couple passe les contrôles
    // de séparation (ΔE 15,3 en deutéranopie) et de contraste.
    const data = {
      labels:[tr('chartSexCases'), tr('chartSexDeaths')],
      datasets:[
        { label:tr('chartSexFemale'), data:[ps.cas.partFeminin, ps.deces.partFeminin],
          backgroundColor:PALETTE.scale[4], stack:'s', borderColor:PALETTE.panel, borderWidth:2 },
        { label:tr('chartSexMale'), data:[ps.cas.partMasculin, ps.deces.partMasculin],
          backgroundColor:PALETTE.scale[3], stack:'s', borderColor:PALETTE.panel, borderWidth:2 },
      ]
    };
    const opts = {
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      scales:{
        x:{ stacked:true, min:0, max:100, ticks:{ color:PALETTE.inkFaint,
            font:{family:PALETTE.font, size:10}, callback:v=>v+'%' },
            grid:{ color:PALETTE.lineSoft } },
        y:{ stacked:true, ticks:{ color:PALETTE.inkDim, font:{family:PALETTE.font, size:12} },
            grid:{ display:false } }
      },
      plugins:{
        legend:{ labels:{ color:PALETTE.inkDim, font:{family:PALETTE.font, size:11},
                          boxWidth:10, usePointStyle:true } },
        tooltip:{
          backgroundColor:PALETTE.panel, borderColor:PALETTE.line, borderWidth:1,
          titleColor:PALETTE.ink, bodyColor:PALETTE.ink,
          titleFont:{family:PALETTE.font}, bodyFont:{family:PALETTE.font},
          callbacks:{ label: c => {
            const n = effectifs[c.label] || {};
            const effectif = c.datasetIndex === 0 ? n.f : n.h;
            return `${c.dataset.label} : ${String(c.parsed.x).replace('.', ',')} % (${fmt(effectif)})`;
          } }
        }
      }
    };
    if(slot.chart){ slot.chart.data = data; slot.chart.options = opts; slot.chart.update(); }
    else {
      // Le pourcentage au centre de chaque segment : il porte l'information
      // sans obliger à viser l'axe, et satisfait l'exigence de libellé visible.
      const pctDansSegment = {
        id:'pctSexes',
        afterDatasetsDraw(c){
          const {ctx} = c;
          c.data.datasets.forEach((dataset, i)=>{
            const meta = c.getDatasetMeta(i);
            if(meta.hidden) return;
            meta.data.forEach((bar, idx)=>{
              const value = dataset.data[idx];
              if(!value) return;
              const x = (bar.x + bar.base) / 2;
              ctx.save();
              ctx.fillStyle = PALETTE.panel;
              ctx.font = "700 12px 'Public Sans', sans-serif";
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillText(String(value).replace('.', ',') + ' %', x, bar.y);
              ctx.restore();
            });
          });
        }
      };
      slot.chart = new Chart(canvas.getContext('2d'),
                             { type:wantedType, data, options:opts, plugins:[pctDansSegment] });
    }
    if(noteEl){
      noteEl.textContent = noteDemographie();
      noteEl.style.display = 'block';
    }
    slot.lastMode = 'sexes';
    return;
  }

  // Mode "Âge" : catégories et non dates, et deux parts qui somment chacune
  // à 100% de leur série. Traité à part comme "Origine des décès", avant le
  // reste de la fonction qui suppose des SitRep (s) comme source.
  /* Mode « Pyramide des ages » : le croisement age x sexe, que le fichier
     porte depuis toujours (casFeminin, casMasculin, decesFeminin,
     decesMasculin) sans que rien ne le lise. Les deux onglets precedents
     n'en montraient chacun qu'une marge — la repartition par age d'un cote,
     le partage femmes/hommes de l'autre — et l'interaction tombait entre les
     deux. Or c'est elle qui porte le fait : l'excedent feminin n'est pas
     general, il se concentre sur les 18-29 ans (58,7 % contre 52,9 % au
     total), tandis que les moins de 5 ans sont a majorite masculine.

     DEUX FIGURES, PAS UNE. Un premier essai superposait cas et deces sur un
     axe commun. Illisible : les cas montent a 623, les deces plafonnent a
     166, et toute la variation des deces — de 69 a 166 selon la tranche —
     s'ecrasait dans 7 % de la largeur. Sur son propre axe borne a 200, la
     meme variation en occupe 24 %.

     Le partage a un second effet, qui vaut autant que le premier : tant que
     les deux series partagent un axe, l'oeil calcule un rapport deces/cas.
     Or ce rapport n'est pas publiable ici — la figure source ne voit que
     61 % des deces contre 85 % des cas, et le quotient tomberait a 32 % la
     ou le site affiche 46 % au niveau national. Separees, les deux echelles
     retirent la tentation au lieu de la corriger par une note. */
  if(chartMode==='pyramide'){
    const cible2 = canvasB;
    const panneau2 = cible2 ? cible2.closest('.chart-panel') : null;
    if(!DEMOGRAPHIE || !DEMOGRAPHIE.tranches){
      if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
      slot.lastMode = 'pyramide';
      const ctx0 = canvas.getContext('2d');
      ctx0.clearRect(0,0,canvas.width,canvas.height);
      if(noteEl){ noteEl.textContent = ''; noteEl.style.display = 'none'; }
      return;
    }

    // La tranche ouverte est en bas, les nourrissons en haut : c'est le sens
    // de lecture d'une pyramide, et l'inverse de l'ordre du fichier.
    const bandes = DEMOGRAPHIE.tranches.slice().reverse();
    const libelle = t => /^\d+-\d+$/.test(t)
      ? t.replace('-', '–') + ' ' + tr('chartAgesUnit')
      : tr('chartAgesOpenEnded');
    const F = tr('chartSexFemale'), H = tr('chartSexMale');

    // « Femmes » et « Hommes » ecrits au-dessus de leur moitie. Les deux mots
    // portent seuls l'orientation de la figure : il n'y a plus de legende,
    // chaque pyramide n'ayant qu'une couleur.
    const cotes = {
      id:'cotesPyramide',
      afterDraw(ch){
        const {ctx, chartArea:a, scales:{x}} = ch;
        const zero = x.getPixelForValue(0);
        ctx.save();
        ctx.font = '600 11px ' + PALETTE.font;
        ctx.fillStyle = PALETTE.inkFaint;
        ctx.textBaseline = 'bottom';
        ctx.textAlign = 'right';  ctx.fillText(F, zero - 10, a.top - 5);
        ctx.textAlign = 'left';   ctx.fillText(H, zero + 10, a.top - 5);
        ctx.restore();
      }
    };

    /* Vue « Parts » : une seule pyramide, les deux series ramenees chacune a
       100 % de son propre total.

       C'est la seule fusion legitime. Sur un axe d'effectifs, la longueur des
       barres de deces rapportee a celle des cas donne 32,5 %, quand le site
       affiche 47,9 % de letalite — la figure source voit 85 % des cas mais
       61 % des deces. En parts, aucun rapport entre les deux series n'est
       lisible : on compare deux repartitions, ce qui est exactement la
       question interessante. Et les deux tiennent la meme place a l'ecran,
       le probleme d'echelle qui imposait deux figures disparait.

       Ce qu'elle revele : les moins de 5 ans font 10,0 % des cas et 19,0 %
       des deces. Le double. Les 30-49 ans, tranche la plus touchee en volume,
       font 35,2 % des cas pour 27,2 % des deces. */
    if(pyramideVue === 'parts'){
      if(panneau1) panneau1.classList.add('is-parts');
      if(panneau2) panneau2.style.display = 'none';
      if(cible2){
        const s2 = chartSlot(cible2);
        if(s2.chart){ s2.chart.destroy(); s2.chart = null; s2.lastMode = null; }
      }
      const C = DEMOGRAPHIE.totaux.cas, D = DEMOGRAPHIE.totaux.deces;
      const part = (n, total) => n / total * 100;
      const series = [
        { label:tr('chartSexCases'),  sexe:F, pile:'cas',   teinte:PALETTE.info,
          v:bandes.map(b => -part(b.casFeminin, C)) },
        { label:tr('chartSexCases'),  sexe:H, pile:'cas',   teinte:PALETTE.info,
          v:bandes.map(b =>  part(b.casMasculin, C)) },
        { label:tr('chartSexDeaths'), sexe:F, pile:'deces', teinte:PALETTE.critical,
          v:bandes.map(b => -part(b.decesFeminin, D)) },
        { label:tr('chartSexDeaths'), sexe:H, pile:'deces', teinte:PALETTE.critical,
          v:bandes.map(b =>  part(b.decesMasculin, D)) },
      ];
      const borne = Math.ceil(Math.max(...series.flatMap(s => s.v.map(Math.abs))) / 5) * 5;
      const dataP = {
        labels: bandes.map(b => libelle(b.tranche)),
        datasets: series.map(s => ({
          label:s.label, sexe:s.sexe, stack:s.pile, data:s.v,
          backgroundColor:s.teinte, borderRadius:1,
          categoryPercentage:0.96, barPercentage:0.92,
        }))
      };
      // Les effectifs derriere chaque part, pour l'infobulle : une part seule
      // ne dit pas sur combien de personnes elle repose.
      const effectifs = bandes.map(b => ({
        [F+'cas']:b.casFeminin, [H+'cas']:b.casMasculin,
        [F+'deces']:b.decesFeminin, [H+'deces']:b.decesMasculin,
      }));
      const optsP = {
        indexAxis:'y', responsive:true, maintainAspectRatio:false,
        animation:false,
        layout:{ padding:{ top:6 } },
        scales:{
          x:{ stacked:true, min:-borne, max:borne,
              ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10},
                      callback:v => Math.abs(v) + ' %' },
              grid:{ color:PALETTE.lineSoft } },
          y:{ stacked:true,
              ticks:{ color:PALETTE.inkDim, font:{family:PALETTE.font, size:11} },
              grid:{ display:false } }
        },
        plugins:{
          title:{ display:true, text:tr('chartPyramidePartsTitre'),
                  color:PALETTE.ink, font:{family:PALETTE.font, size:12, weight:'600'},
                  padding:{ bottom:26 } },
          legend:{ position:'bottom',
                   labels:{ color:PALETTE.inkDim, font:{family:PALETTE.font, size:11},
                            boxWidth:10, usePointStyle:true,
                            // Le cote dit le sexe : deux entrees suffisent.
                            filter: item => item.datasetIndex === 0 || item.datasetIndex === 2 } },
          tooltip:{
            backgroundColor:PALETTE.panel, borderColor:PALETTE.line, borderWidth:1,
            titleColor:PALETTE.ink, bodyColor:PALETTE.ink,
            titleFont:{family:PALETTE.font}, bodyFont:{family:PALETTE.font},
            callbacks:{ label: c => {
              const cle = c.dataset.sexe + (c.dataset.stack === 'cas' ? 'cas' : 'deces');
              const n = (effectifs[c.dataIndex] || {})[cle];
              return c.dataset.sexe + ' · ' + c.dataset.label + ' : '
                   + Math.abs(c.parsed.x).toFixed(1).replace('.', ',') + ' %'
                   + (n != null ? ' (' + fmt(n) + ')' : '');
            } }
          }
        }
      };
      if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
      slot.chart = new Chart(canvas.getContext('2d'),
        { type:'bar', data:dataP, options:optsP, plugins:[cotes] });
      slot.lastMode = 'pyramide';
      if(noteEl){
        noteEl.textContent = phraseSexe() + ' ' + noteDemographie() + ' '
                           + tr('chartPyramideBandes') + ' '
                           + tr('chartPyramidePartsNote');
        noteEl.style.display = 'block';
      }
      return;
    }

    /* Une pyramide pour une serie : les deux colonnes du fichier, la teinte,
       le titre et l'effectif total qui l'accompagne. */
    const pyramide = (champF, champH, teinte, titre, total) => {
      const ampleur = Math.max(...bandes.flatMap(b => [b[champF], b[champH]]));
      // Arrondi au pas superieur : la centaine au-dessus de 200, la
      // cinquantaine en dessous, pour que la petite serie ne soit pas
      // ecrasee par un arrondi trop genereux.
      const pas = ampleur > 200 ? 100 : 50;
      const borne = Math.ceil(ampleur / pas) * pas;
      return {
        data:{
          labels: bandes.map(b => libelle(b.tranche)),
          // Barres jointives a un filet pres. Un plafond d'epaisseur laissait
          // 60 % de la ligne en blanc : la figure se lisait comme cinq barres
          // isolees, alors qu'une pyramide se lit comme un profil continu, ou
          // l'ecart d'une tranche a la suivante se voit au decrochage du bord.
          // categoryPercentage rend a la barre toute sa ligne, barPercentage
          // reprend les 6 % qui separent deux voisines.
          datasets:[
            { label:F, stack:'s', data:bandes.map(b => -b[champF]),
              backgroundColor:teinte, borderRadius:1,
              categoryPercentage:1, barPercentage:0.94 },
            { label:H, stack:'s', data:bandes.map(b =>  b[champH]),
              backgroundColor:teinte, borderRadius:1,
              categoryPercentage:1, barPercentage:0.94 },
          ]
        },
        options:{
          indexAxis:'y', responsive:true, maintainAspectRatio:false,
          // Le greffon d'en-tetes ne s'attache qu'a la construction : ce mode
          // reconstruit son graphique a chaque passage, et l'animation
          // repartirait de zero a chaque retour sur l'onglet. Elle n'apporte
          // rien a un instantane fige au 5 aout.
          animation:false,
          // Reserve la bande ou le greffon ecrit « Femmes » / « Hommes » : ce
          // texte est peint hors de la zone de trace, ou Chart.js ne prevoit
          // aucune place — sans cette marge il est rogne par le panneau.
          layout:{ padding:{ top:6 } },
          scales:{
            x:{ stacked:true, min:-borne, max:borne,
                ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10},
                        callback:v => fmt(Math.abs(v)) },
                grid:{ color:PALETTE.lineSoft } },
            y:{ stacked:true,
                ticks:{ color:PALETTE.inkDim, font:{family:PALETTE.font, size:11} },
                grid:{ display:false } }
          },
          plugins:{
            // L'effectif total est colle au titre : deux echelles differentes
            // cote a cote invitent a comparer les longueurs, le nombre dit
            // qu'elles ne sont pas comparables.
            title:{ display:true, text:titre + ' (' + fmt(total) + ')',
                    color:PALETTE.ink, font:{family:PALETTE.font, size:12, weight:'600'},
                    // 26 px sous le titre : le greffon ecrit « Femmes » /
                    // « Hommes » juste au-dessus de la zone de trace, et a
                    // 12 px les deux textes se chevauchaient.
                    padding:{ bottom:26 } },
            // Une seule couleur par figure : la legende n'apprendrait rien.
            legend:{ display:false },
            tooltip:{
              backgroundColor:PALETTE.panel, borderColor:PALETTE.line, borderWidth:1,
              titleColor:PALETTE.ink, bodyColor:PALETTE.ink,
              titleFont:{family:PALETTE.font}, bodyFont:{family:PALETTE.font},
              callbacks:{ label: c => c.dataset.label + ' : ' + fmt(Math.abs(c.parsed.x)) }
            }
          }
        }
      };
    };

    const gauche = pyramide('casFeminin', 'casMasculin', PALETTE.info,
                            tr('chartSexCases'), DEMOGRAPHIE.totaux.cas);
    if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
    slot.chart = new Chart(canvas.getContext('2d'),
      { type:'bar', data:gauche.data, options:gauche.options, plugins:[cotes] });
    slot.lastMode = 'pyramide';

    if(cible2 && panneau2){
      panneau2.style.display = '';
      const slot2 = chartSlot(cible2);
      const droite = pyramide('decesFeminin', 'decesMasculin', PALETTE.critical,
                              tr('chartSexDeaths'), DEMOGRAPHIE.totaux.deces);
      if(slot2.chart){ slot2.chart.destroy(); slot2.chart = null; }
      slot2.chart = new Chart(cible2.getContext('2d'),
        { type:'bar', data:droite.data, options:droite.options, plugins:[cotes] });
      slot2.lastMode = 'pyramide';
    }

    if(noteEl){
      noteEl.textContent = phraseSexe() + ' ' + noteDemographie() + ' '
                         + tr('chartPyramideBandes');
      noteEl.style.display = 'block';
    }
    return;
  }

  if(chartMode==='ages'){
    const wantedType = 'bar';
    if(slot.chart && (slot.chart.config.type !== wantedType || slot.lastMode !== 'ages')){
      slot.chart.destroy();
      slot.chart = null;
    }
    if(!DEMOGRAPHIE){
      if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
      slot.lastMode = 'ages';
      const ctx0 = canvas.getContext('2d');
      ctx0.clearRect(0,0,canvas.width,canvas.height);
      return;
    }

    const bandes = DEMOGRAPHIE.tranches;
    const libelle = t => /^\d+-\d+$/.test(t)
      ? t.replace('-', '–') + ' ' + tr('chartAgesUnit')
      : tr('chartAgesOpenEnded');

    // Des PARTS, jamais un taux de létalité par âge : la figure source ne voit
    // que 61 % des décès contre 85 % des cas, un taux en sortirait trop bas et
    // contredirait la létalité affichée ailleurs sur le site.
    const data = {
      labels: bandes.map(b => libelle(b.tranche)),
      datasets:[
        { label:tr('chartAgesCases'),  data:bandes.map(b=>b.partCas),
          backgroundColor:PALETTE.info,     borderRadius:2, maxBarThickness:16 },
        { label:tr('chartAgesDeaths'), data:bandes.map(b=>b.partDeces),
          backgroundColor:PALETTE.critical, borderRadius:2, maxBarThickness:16 },
      ]
    };
    const parN = {};
    bandes.forEach(b => { parN[libelle(b.tranche)] = { cas:b.cas, deces:b.deces }; });
    const opts = {
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      scales:{
        x:{ min:0, ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10},
                           callback:v=>v+'%' }, grid:{ color:PALETTE.lineSoft } },
        y:{ ticks:{ color:PALETTE.inkDim, font:{family:PALETTE.font, size:11} },
            grid:{ display:false } }
      },
      plugins:{
        legend:{ labels:{ color:PALETTE.inkDim, font:{family:PALETTE.font, size:11},
                          boxWidth:10, usePointStyle:true } },
        tooltip:{
          backgroundColor:PALETTE.panel, borderColor:PALETTE.line, borderWidth:1,
          titleColor:PALETTE.ink, bodyColor:PALETTE.ink,
          titleFont:{family:PALETTE.font}, bodyFont:{family:PALETTE.font},
          callbacks:{ label: c => {
            const n = parN[c.label] || {};
            const effectif = c.datasetIndex === 0 ? n.cas : n.deces;
            return `${c.dataset.label} : ${String(c.parsed.x).replace('.', ',')} % (${effectif})`;
          } }
        }
      }
    };
    if(slot.chart){ slot.chart.data = data; slot.chart.options = opts; slot.chart.update(); }
    else { slot.chart = new Chart(canvas.getContext('2d'), { type:wantedType, data, options:opts }); }
    if(noteEl){
      noteEl.textContent = noteDemographie();
      noteEl.style.display = 'block';
    }
    slot.lastMode = 'ages';
    return;
  }

  // Mode "Origine des décès" : structure de données et échelle (0-100%)
  // totalement différentes des deux autres modes — traité à part, avant le
  // reste de la fonction qui suppose des SitRep (s) comme source.
  /* Lieu du deces : part des deces survenus en communaute plutot qu'en centre
     de traitement, agregee sur le pays et regroupee par semaine.

     LECTURE PAR PROVINCE ABANDONNEE. Elle montrait un ecart reel — 66,8 % au
     Nord-Kivu contre 50,0 % au Haut-Uele — mais elle repondait a « ou ? »
     quand la question qui compte est « est-ce que ca s'ameliore ? ». Le
     detail par province reste dans le fichier, rien a re-extraire si on veut
     y revenir.

     CE QUE LA COURBE MONTRE, ET C'EST VOULU : rien ne bouge. Six semaines
     entre 53,6 et 68,5 %, sans direction, autour de 61,6 %. Avec 125 a 364
     deces par semaine, l'ecart-type attendu du seul hasard d'echantillonnage
     est de 3 a 4 points ; l'ecart-type observe est de 5. Les creux et les
     bosses ne racontent rien. C'est pour ca que la moyenne est tracee en
     pointilles : elle donne au lecteur la ligne a laquelle comparer, au lieu
     de le laisser chercher une tendance dans du bruit.

     ECHELLE DE 0 A 100 %, jamais resserree sur les valeurs. Un axe cadre sur
     50-70 % ferait de ces oscillations une montagne russe. Pleine echelle,
     la courbe est plate et haute — ce qu'elle est. */
  if(chartMode==='deathsPlace'){
    if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
    if(!DECES_LIEU || !DECES_LIEU.parDate || !DECES_LIEU.parDate.length){
      slot.lastMode = 'deathsPlace';
      const ctx0 = canvas.getContext('2d');
      ctx0.clearRect(0, 0, canvas.width, canvas.height);
      if(noteEl){ noteEl.textContent = ''; noteEl.style.display = 'none'; }
      return;
    }

    // Regroupement par semaine ISO, du lundi au dimanche.
    const lundi = iso => {
      const d = new Date(iso + 'T12:00:00');
      d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
      return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0')
           + '-' + String(d.getDate()).padStart(2, '0');
    };
    const semaines = new Map();
    for(const jour of DECES_LIEU.parDate){
      const cle = lundi(jour.date);
      const s = semaines.get(cle) || { debut: cle, fin: jour.date, comm: 0, cte: 0 };
      for(const v of Object.values(jour.provinces || {})){
        s.comm += v.communautaires || 0;
        s.cte  += v.intraCte || 0;
      }
      if(jour.date > s.fin) s.fin = jour.date;
      semaines.set(cle, s);
    }
    // Une semaine sans aucun deces classe ne porte aucune part : on l'ecarte
    // plutot que de tracer un zero qui se lirait comme « personne n'est mort
    // en communaute ».
    const serie = [...semaines.values()]
      .filter(s => s.comm + s.cte > 0)
      .sort((a, b) => a.debut.localeCompare(b.debut));

    const totalComm = serie.reduce((n, s) => n + s.comm, 0);
    const totalCte  = serie.reduce((n, s) => n + s.cte, 0);
    const moyenne   = Math.round(totalComm / (totalComm + totalCte) * 1000) / 10;

    /* Barres empilees a 100 %, une par semaine : les deux lieux sont montres
       explicitement, et la FRONTIERE entre les deux couleurs est la part. Une
       courbe unique aurait dit la meme chose, mais elle aurait laisse le
       lecteur reconstituer mentalement le complement.

       Meme idiome que le graphique par sexe, pour la meme raison : « empilees
       sur une base commune, les deux barres rendent le decalage lisible au
       decrochage de la frontiere entre les deux couleurs ».

       Deux nuances d'un meme rouge, pas deux teintes etrangeres : ce sont tous
       des deces, seul le lieu change. Le plein revient a la communaute, la
       part qui alarme. */
    const part = s => Math.round(s.comm / (s.comm + s.cte) * 1000) / 10;
    const data = {
      labels: serie.map(s => frDate(s.debut)),
      datasets: [
        { label: tr('chartDeathPlaceCommunity'), data: serie.map(part),
          backgroundColor: PALETTE.critical, stack: 'l',
          borderColor: PALETTE.panel, borderWidth: 2, order: 1 },
        { label: tr('chartDeathPlaceCte'),
          data: serie.map(s => Math.round((100 - part(s)) * 10) / 10),
          backgroundColor: tint(PALETTE.critical, .30), stack: 'l',
          borderColor: PALETTE.panel, borderWidth: 2, order: 2 },
        /* La moyenne vit sur un second axe, invisible et non empile : posee
           sur l'axe des barres, Chart.js l'empilerait par-dessus elles. */
        { type: 'line', label: tr('chartDeathPlaceAverage')(moyenne),
          data: serie.map(() => moyenne), yAxisID: 'y1',
          borderColor: PALETTE.ink, borderWidth: 1.5, borderDash: [5, 4],
          pointStyle: 'line', pointRadius: 0, fill: false, tension: 0, order: 3 },
      ]
    };
    const opts = {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: { stacked: true,
             ticks: { color: PALETTE.inkFaint, font: { family: PALETTE.font, size: 10 } },
             grid: { display: false } },
        y: { stacked: true, min: 0, max: 100,
             ticks: { color: PALETTE.inkFaint, font: { family: PALETTE.font, size: 10 },
                      callback: v => v + ' %' },
             grid: { color: PALETTE.lineSoft } },
        y1: { min: 0, max: 100, display: false }
      },
      plugins: {
        legend: { labels: { color: PALETTE.inkDim, font: { family: PALETTE.font, size: 11 },
                            boxWidth: 10, usePointStyle: true } },
        tooltip: {
          backgroundColor: PALETTE.panel, borderColor: PALETTE.line, borderWidth: 1,
          titleColor: PALETTE.ink, bodyColor: PALETTE.ink,
          titleFont: { family: PALETTE.font }, bodyFont: { family: PALETTE.font },
          callbacks: {
            title: items => tr('chartDeathPlaceWeekLabel')(
              frDate(serie[items[0].dataIndex].debut), frDate(serie[items[0].dataIndex].fin)),
            /* Les effectifs avec la part, toujours : 68 % sur 146 deces et
               61 % sur 364 ne se lisent pas de la meme facon. */
            label: c => {
              if(c.dataset.type === 'line') return c.dataset.label;
              const s = serie[c.dataIndex];
              const n = c.datasetIndex === 0 ? s.comm : s.cte;
              return `${c.dataset.label} : ${String(c.parsed.y).replace('.', ',')} % `
                   + `(${fmt(n)} décès)`;
            }
          }
        }
      }
    };
    slot.chart = new Chart(canvas.getContext('2d'), { type: 'bar', data, options: opts });
    slot.lastMode = 'deathsPlace';
    if(noteEl){
      noteEl.textContent = tr('chartDeathPlaceNoteTemps')(
        moyenne, serie.length, fmt(totalComm), fmt(totalCte), 7);
      noteEl.style.display = 'block';
    }
    return;
  }

  if(chartMode==='communityDeaths'){
    const weekly = aggregateWeeklyCommunityDeaths();
    const wantedType = 'bar';
    // Force la recréation en entrant dans ce mode (même si le type 'bar'
    // correspondrait déjà) : le plugin de pourcentage ne doit s'attacher
    // qu'à CETTE instance de graphique, jamais persister sur une autre.
    if(slot.chart && (slot.chart.config.type !== wantedType || slot.lastMode !== 'communityDeaths')){
      slot.chart.destroy();
      slot.chart = null;
    }

    if(!weekly.length){
      if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
      slot.lastMode = 'communityDeaths';
      const ctx0 = canvas.getContext('2d');
      ctx0.clearRect(0,0,canvas.width,canvas.height);
      return;
    }

    function frWeekLabel(iso){
      const start = new Date(iso+'T00:00:00');
      const end = new Date(start); end.setDate(start.getDate()+6);
      // Format JJ/MM compact plutôt que "13 juillet au 19 juillet" — prend
      // moins de place sur les écrans étroits (mobile).
      const f = d => String(d.getDate()).padStart(2,'0') + '/' + String(d.getMonth()+1).padStart(2,'0');
      return `${f(start)}–${f(end)}`;
    }

    // 3 semaines antérieures au 060 (le pipeline INSP n'a pas cette donnée
    // avant cette date, voir échanges du 19/08/2026), tirées du Weekly
    // External Situation Report (Figure 3 — semaines épidémio. 26 à 28,
    // découpage mercredi-mardi propre à ce rapport, différent du
    // regroupement lundi-dimanche utilisé pour le reste du graphique
    // ci-dessous). Codées en dur : ce sont 3 points ponctuels lus sur un
    // graphique publié, pas une extraction automatisée à reproduire.
    const WEEKLY_REPORT_PREFIX = [
      { label:"24/06–28/06", community:50.6, intra:49.4 },
      { label:"29/06–05/07", community:50.0, intra:50.0 },
      { label:"06/07–12/07", community:65.4, intra:34.6 },
    ];

    const labels = [...WEEKLY_REPORT_PREFIX.map(w=>w.label), ...weekly.map(w => frWeekLabel(w.weekStart))];
    const communityPct = [...WEEKLY_REPORT_PREFIX.map(w=>w.community), ...weekly.map(w => w.total>0 ? +(w.community/w.total*100).toFixed(1) : 0)];
    const intraPct = [...WEEKLY_REPORT_PREFIX.map(w=>w.intra), ...weekly.map(w => w.total>0 ? +(w.intra/w.total*100).toFixed(1) : 0)];

    const data = {
      labels,
      datasets:[
        // Deux paliers de l'echelle du site plutot que deux teintes etrangeres :
        // le bleu profond pour les deces communautaires, ceux qui echappent au
        // systeme de soins, le bleu clair pour ceux survenus en centre.
        { label:tr('communityDeathsLabel'), data:communityPct, backgroundColor:PALETTE.scale[4], stack:'s' },
        { label:tr('intraCteDeathsLabel'), data:intraPct, backgroundColor:PALETTE.scale[2], stack:'s' },
      ]
    };
    const opts = {
      responsive:true, maintainAspectRatio:false,
      scales:{
        x:{ stacked:true, ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10} }, grid:{ display:false } },
        y:{ stacked:true, min:0, max:100, ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10}, callback:v=>v+'%' }, grid:{ color:PALETTE.lineSoft } }
      },
      plugins:{
        legend:{ labels:{ color:PALETTE.inkDim, font:{family:PALETTE.font, size:11}, boxWidth:10, usePointStyle:true } },
        tooltip:{
          backgroundColor:PALETTE.panel, borderColor:PALETTE.line, borderWidth:1,
          titleColor:PALETTE.ink, bodyColor:PALETTE.ink, titleFont:{family:PALETTE.font}, bodyFont:{family:PALETTE.font},
          callbacks:{ label: c => `${c.dataset.label} : ${c.parsed.y}%` }
        }
      }
    };
    if(slot.chart){ slot.chart.data = data; slot.chart.options = opts; slot.chart.update(); }
    else {
      // Plugin maison pour afficher le % au centre de chaque segment de
      // barre, plutôt que d'ajouter une dépendance externe (chartjs-
      // plugin-datalabels) juste pour ce seul usage.
      const percentLabelsPlugin = {
        id:'percentLabels',
        afterDatasetsDraw(c){
          const {ctx} = c;
          c.data.datasets.forEach((dataset, i)=>{
            const meta = c.getDatasetMeta(i);
            if(meta.hidden) return;
            meta.data.forEach((bar, idx)=>{
              const value = dataset.data[idx];
              if(value===null || value===undefined || value===0) return;
              const y = (bar.y + bar.base) / 2;
              ctx.save();
              ctx.fillStyle = PALETTE.panel;
              ctx.font = "700 10px 'Public Sans', sans-serif";
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillText(value + '%', bar.x, y);
              ctx.restore();
            });
          });
        }
      };
      slot.chart = new Chart(canvas.getContext('2d'), { type:wantedType, data, options:opts, plugins:[percentLabelsPlugin] });
    }
    slot.lastMode = 'communityDeaths';
    return;
  }

  // Mode "Suivi des contacts" : source de données dédiée
  // (CONTACTS_FOLLOWUP), avec un pont en pointillés atténué et ondulé sur
  // les périodes sans donnée — jamais une vraie valeur, juste un repère
  // visuel pour ne pas casser la lecture (voir tr('chartNoteContactsGap')
  // pour l'explication affichée à l'utilisateur).
  if(chartMode==='contactsFollowUp'){
    const wantedType = 'line';
    if(slot.chart && (slot.chart.config.type !== wantedType || slot.lastMode === 'communityDeaths')){
      slot.chart.destroy();
      slot.chart = null;
    }

    if(!CONTACTS_FOLLOWUP.length){
      if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
      slot.lastMode = 'contactsFollowUp';
      const ctx0 = canvas.getContext('2d');
      ctx0.clearRect(0,0,canvas.width,canvas.height);
      return;
    }

    // Série calendaire jour par jour (pas juste les dates connues) pour que
    // les trous de données aient leur vraie largeur proportionnelle.
    // Entièrement en UTC (Date.UTC / getUTCDate / toISOString) : mélanger
    // dates locales et toISOString() (toujours en UTC) décale le calendrier
    // d'un jour pour tout visiteur dans un fuseau horaire positif — ex.
    // Kinshasa (UTC+1) — et fait silencieusement disparaître le tout
    // dernier point du graphique (vu le 20/08/2026 avec le SitRep 096).
    const byDate = {};
    CONTACTS_FOLLOWUP.forEach(r => { byDate[r.date] = r.contactsFollowUpRate; });
    const [sy,sm,sd] = CONTACTS_FOLLOWUP[0].date.split('-').map(Number);
    const [ey,em,ed] = CONTACTS_FOLLOWUP[CONTACTS_FOLLOWUP.length-1].date.split('-').map(Number);
    const start = new Date(Date.UTC(sy, sm-1, sd));
    const end = new Date(Date.UTC(ey, em-1, ed));
    const labels = [];
    const values = [];
    for(let d = new Date(start); d <= end; d.setUTCDate(d.getUTCDate()+1)){
      const iso = d.toISOString().slice(0,10);
      labels.push(frDate(iso));
      values.push(byDate[iso] !== undefined ? byDate[iso] : null);
    }

    function seededRand(i){
      const x = Math.sin(i * 12.9898) * 43758.5453;
      return x - Math.floor(x);
    }
    function buildBridge(vals){
      const out = vals.slice();
      let i = 0;
      while(i < vals.length){
        if(vals[i] === null){
          let start = i - 1, end = i;
          while(end < vals.length && vals[end] === null) end++;
          if(start >= 0 && end < vals.length){
            const v0 = vals[start], v1 = vals[end], span = end - start;
            for(let j = start + 1; j < end; j++){
              const t = (j - start) / span;
              const linear = v0 + (v1 - v0) * t;
              const wiggle = (seededRand(j) - 0.5) * 6;
              out[j] = Math.max(0, Math.min(100, linear + wiggle));
            }
          }
          i = end;
        } else { i++; }
      }
      return out;
    }
    const bridgeValues = buildBridge(values);

    /* La cible de 95 % vient des rapports hebdomadaires de l'OMS, pas des
       bulletins de l'INSP qui alimentent la courbe : « Overall follow-up
       performance remained substantially below the operational target of 95 %,
       leaving 3 376 contacts not seen during the reporting period » (WHO n°11),
       repris au n°14 — « remaining below the 95 % operational target ». La note
       l'attribue donc explicitement a l'OMS.

       Elle est dite, pas tracee. Une ligne a 95 % au-dessus d'une courbe qui
       plafonne a 80 % ouvre une bande vide sur le quart superieur du cadre, et
       ce blanc ne dit rien de plus que la phrase. */
    const CIBLE_OMS = 95;

    const data = {
      labels,
      datasets: [
        {
          data: bridgeValues,
          borderColor: tint(PALETTE.active, .35),
          borderWidth: 1.5,
          borderDash: [4,4],
          pointRadius: 0,
          fill: false,
          spanGaps: false,
          tension: 0.4,
          order: 2,
        },
        {
          data: values,
          borderColor: PALETTE.active,
          borderWidth: 2,
          pointRadius: 2,
          pointHoverRadius: 5,
          pointBackgroundColor: PALETTE.active,
          fill: false,
          tension: 0.15,
          spanGaps: false,
          order: 1,
        },
      ],
    };
    const opts = {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        // Aucune serie n'a de libelle : la courbe et son pont en pointilles se
        // passent d'une legende, la note dit le reste.
        legend: { display: false },
        tooltip: {
          backgroundColor:PALETTE.panel, borderColor:PALETTE.line, borderWidth:1,
          titleColor:PALETTE.ink, bodyColor:PALETTE.ink, titleFont:{family:PALETTE.font}, bodyFont:{family:PALETTE.font},
          filter: (item) => item.datasetIndex === 1,
          callbacks: { label: c => (c.parsed.y!==null ? c.parsed.y+'%' : '') },
        },
      },
      scales: {
        y: { min:0, max:100, ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10}, callback:v=>v+'%' }, grid:{ color:PALETTE.lineSoft } },
        x: { ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10}, maxRotation:45, minRotation:45, autoSkip:true, maxTicksLimit:22 }, grid:{ display:false } },
      },
    };
    if(slot.chart){ slot.chart.data = data; slot.chart.options = opts; slot.chart.update(); }
    else { slot.chart = new Chart(canvas.getContext('2d'), { type:wantedType, data, options:opts }); }
    slot.lastMode = 'contactsFollowUp';
    if(noteEl){
      noteEl.textContent = tr('chartNoteContacts')(CIBLE_OMS);
      noteEl.style.display = 'block';
    }
    return;
  }

  // Mode "Par province" : une courbe par province, à partir de
  // PROVINCE_HISTORY — toujours complet par construction (le total
  // provincial est présent dans chaque SitRep), donc pas de pont en
  // pointillés nécessaire comme pour le suivi des contacts.
  /* Meme lecture que sur l'accueil — barres quotidiennes, courbe cumulee —
     mais pour une seule province, sur une page province. Trois garde-fous,
     tous imposes par la donnee reelle :

     1. La ventilation par province n'est pas publiee entre le 20 et le
        30 mai, alors que le national l'est. La premiere barre couvrirait
        douze jours (+269 en Ituri) et se lirait comme le plus gros jour de
        l'epidemie. Au-dela de ECART_MAX_JOURS, on n'affiche pas de barre —
        la courbe cumulee, elle, reste continue et garde tous ses points.
     2. Les 22 et 30 juillet, le bulletin annonce lui-meme moins de nouveaux
        cas que le delta du cumul. Ce chiffre reel n'existe qu'au niveau
        national : impossible de le repartir sans inventer. On affiche donc
        la barre entiere en teinte de rattrapage plutot que d'attribuer un
        volume administratif a une journee.
     3. Les noms sont deja normalises au chargement (voir
        nomProvinceCanonique) : sans cela, le releve du 14 aout se perdait. */
  if(chartMode==='provinceEpidemic'){
    const ECART_MAX_JOURS = 3;
    const RATTRAPAGE = new Set(['2026-07-22', '2026-07-30']);
    const nom = nomProvinceCanonique(window.PROVINCE_NAME || '');

    const pts = [];
    for(const h of PROVINCE_HISTORY){
      const p = (h.provinces || []).find(pr => pr.name === nom);
      if(p && p.confirmed !== null && p.confirmed !== undefined){
        pts.push({ date: h.date, confirmed: p.confirmed,
                   deaths: (p.deaths === null || p.deaths === undefined) ? null : p.deaths });
      }
    }

    if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
    if(pts.length < 2){
      slot.lastMode = 'provinceEpidemic';
      const ctx0 = canvas.getContext('2d');
      ctx0.clearRect(0, 0, canvas.width, canvas.height);
      if(noteEl){ noteEl.textContent = tr('provinceChartNoData'); noteEl.style.display = 'block'; }
      return;
    }

    const jours = iso => Math.round(new Date(iso + 'T00:00:00').getTime() / 86400000);
    const rapporte = [null];
    const rattrape = [null];
    const trous = [];
    for(let i = 1; i < pts.length; i++){
      const ecart = jours(pts[i].date) - jours(pts[i-1].date);
      if(ecart > ECART_MAX_JOURS){
        const veille = new Date(pts[i-1].date + 'T12:00:00');
        veille.setDate(veille.getDate() + 1);
        const iso = veille.getFullYear() + '-'
          + String(veille.getMonth() + 1).padStart(2, '0') + '-'
          + String(veille.getDate()).padStart(2, '0');
        trous.push(frDate(iso) + ' au ' + frDate(pts[i].date));
        rapporte.push(null); rattrape.push(null);
        continue;
      }
      const delta = Math.max(0, pts[i].confirmed - pts[i-1].confirmed);
      const estRattrapage = RATTRAPAGE.has(pts[i].date);
      rapporte.push(estRattrapage ? 0 : delta);
      rattrape.push(estRattrapage ? delta : 0);
    }

    if(noteEl){
      const bouts = [];
      if(trous.length) bouts.push(tr('provinceChartGap')(trous.join(' ; ')));
      if(pts.some(pt => RATTRAPAGE.has(pt.date))) bouts.push(tr('provinceChartCatchup'));
      noteEl.textContent = bouts.join(' ');
      noteEl.style.display = bouts.length ? 'block' : 'none';
    }

    const teinte = PROVINCE_COLORS[nom] || PALETTE.info;
    const data = {
      labels: pts.map(pt => frDate(pt.date)),
      datasets: [
        { label: tr('dailyChartLabel'), data: rapporte, backgroundColor: teinte,
          borderRadius: 2, stack: 'd', categoryPercentage: 1, barPercentage: .96 },
        { label: tr('catchupLabel'), data: rattrape, backgroundColor: tint(teinte, .35),
          borderRadius: 2, stack: 'd', categoryPercentage: 1, barPercentage: .96 },
        /* La courbe des cas reprend la teinte des barres, et celle des deces
           le rouge du site. Meme encodage que le graphique de l'accueil : la
           couleur dit de quoi on parle, la forme dit quelle lecture.

           L'ambre precedent etait un piege discret — c'est la couleur
           d'identite du Nord-Kivu, dont le graphique affichait donc une courbe
           strictement invisible sur ses propres barres. Le probleme
           disparait avec la teinte de la province, quelle qu'elle soit. */
        { type: 'line', label: tr('chartCumulativeLabel'),
          data: pts.map(pt => pt.confirmed), yAxisID: 'y1',
          borderColor: teinte, borderWidth: 2, tension: .25,
          pointRadius: 0, fill: false, spanGaps: true, order: 0 },
        { type: 'line', label: tr('chartCumulativeDeathsLabel'),
          data: pts.map(pt => pt.deaths), yAxisID: 'y1',
          borderColor: PALETTE.critical, borderWidth: 2, tension: .25,
          pointRadius: 0, fill: false, spanGaps: true, order: 0 }
      ]
    };
    const opts = {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: PALETTE.inkDim, font: { family: PALETTE.font, size: 11 },
                            boxWidth: 10, usePointStyle: true } },
        tooltip: {
          backgroundColor: PALETTE.panel, borderColor: PALETTE.line, borderWidth: 1,
          titleColor: PALETTE.ink, bodyColor: PALETTE.ink,
          titleFont: { family: PALETTE.font }, bodyFont: { family: PALETTE.font },
          filter: item => item.parsed.y !== 0
        }
      },
      scales: {
        x: { ticks: { color: PALETTE.inkFaint, font: { family: PALETTE.font, size: 10 },
                      maxRotation: 45, minRotation: 45, autoSkip: true, maxTicksLimit: 20 },
             grid: { display: false } },
        y: { ticks: { color: PALETTE.inkFaint, font: { family: PALETTE.font, size: 10 },
                      callback: v => fmt(v) },
             grid: { color: PALETTE.lineSoft }, beginAtZero: true },
        y1: { position: 'right', beginAtZero: true,
              ticks: { color: PALETTE.inkFaint, font: { family: PALETTE.font, size: 10 },
                       callback: v => fmt(v) },
              grid: { display: false } }
      }
    };
    slot.chart = new Chart(canvas.getContext('2d'), { type: 'bar', data, options: opts });
    slot.lastMode = 'provinceEpidemic';
    return;
  }

  if(chartMode==='byProvince'){
    const wantedType = 'line';
    if(slot.chart && (slot.chart.config.type !== wantedType || slot.lastMode !== 'byProvince')){
      slot.chart.destroy();
      slot.chart = null;
    }

    if(noteEl){ noteEl.textContent = ''; noteEl.style.display = 'none'; }

    if(!PROVINCE_HISTORY.length){
      if(slot.chart){ slot.chart.destroy(); slot.chart = null; }
      slot.lastMode = 'byProvince';
      const ctx0 = canvas.getContext('2d');
      ctx0.clearRect(0,0,canvas.width,canvas.height);
      return;
    }

    const labels = PROVINCE_HISTORY.map(h => frDate(h.date));
    const provinceNames = Object.keys(PROVINCE_COLORS);
    const data = {
      labels,
      datasets: provinceNames.map(name => ({
        label: name,
        data: PROVINCE_HISTORY.map(h => {
          const p = h.provinces.find(pr => pr.name === name);
          return p ? p.confirmed : null;
        }),
        borderColor: PROVINCE_COLORS[name],
        backgroundColor: PROVINCE_COLORS[name],
        borderWidth: 2,
        pointRadius: 1,
        pointHoverRadius: 4,
        fill: false,
        tension: 0.15,
        spanGaps: true,
      })),
    };
    const opts = {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: true, position: 'bottom', labels: { color:PALETTE.inkDim, font:{family:PALETTE.font, size:11}, boxWidth:10, padding:12 } },
        tooltip: {
          backgroundColor:PALETTE.panel, borderColor:PALETTE.line, borderWidth:1,
          titleColor:PALETTE.ink, bodyColor:PALETTE.ink, titleFont:{family:PALETTE.font}, bodyFont:{family:PALETTE.font},
          callbacks: { label: c => `${c.dataset.label} : ${fmt(c.parsed.y)}` },
        },
      },
      scales: {
        y: { beginAtZero:true, ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10}, callback:v=>fmt(v) }, grid:{ color:PALETTE.lineSoft } },
        x: { ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10}, maxRotation:45, minRotation:45, autoSkip:true, maxTicksLimit:20 }, grid:{ display:false } },
      },
    };
    if(slot.chart){ slot.chart.data = data; slot.chart.options = opts; slot.chart.update(); }
    else { slot.chart = new Chart(canvas.getContext('2d'), { type:wantedType, data, options:opts }); }
    slot.lastMode = 'byProvince';
    return;
  }

  const labels = s.map(r=> (r.approx?'≈ ':'') + frDate(r.date));
  const ctx = canvas.getContext('2d');

  let datasets;
  /* « epidemic » est la representation canonique d'une epidemie, et le seul
     mode qui arrive jusqu'ici : les nouveaux cas quotidiens en barres, les
     cumuls en courbes sur un second axe.

     Deux modes morts ont ete retires avec la courbe des deces. « daily » et
     « cumulative » etaient les deux anciens onglets separes de la page
     d'accueil ; « epidemic » les avait remplaces sans que leur code parte.
     « cumulative » tracait justement les deux courbes de cumul seules — la
     redondance est devenue totale le jour ou la courbe des deces a rejoint
     ce graphique. */
  {
    // Différence avec le bulletin précédent ayant une valeur non nulle. Une
    // valeur négative (révision à la baisse) est ramenée à 0 plutôt que
    // d'afficher un creux trompeur sur un graphique d'incidence.
    function diffs(field){
      const out = []; let prev = null;
      for(const r of s){
        const v = r[field];
        if(v===null || v===undefined){ out.push(null); continue; }
        out.push(prev===null ? null : Math.max(0, v - prev));
        prev = v;
      }
      return out;
    }
    // Deux dates où le delta de cumul inclut bien plus qu'une seule journée
    // de vraies nouvelles notifications, vérifié manuellement en lisant le
    // texte des bulletins eux-mêmes (voir échanges du 19/08/2026) :
    // - 22 juillet : delta cumulé 369, mais le bulletin N°069 indique
    //   lui-même "+97 nouveaux cas" — le reste (272) vient d'une
    //   harmonisation de bases DHIS2 explicitement documentée dans le texte.
    // - 30 juillet : delta cumulé 245, mais le bulletin N°077 indique
    //   "+73 nouveaux cas" pour cette seule journée — le reste (172) couvre
    //   en réalité 2 jours (28-29 juillet) dont les bulletins 075/076 sont
    //   absents des archives publiques (vérifié introuvables même dans le
    //   dépôt de recherche indépendant INRB-UMIE/BDBV2026-Data).
    // Non généralisé automatiquement : ce sont deux corrections ponctuelles
    // documentées à la main, pas une règle détectée par le pipeline.
    const REPORTED_OVERRIDE = { '2026-07-22': 97, '2026-07-30': 73 };
    const casesDiffs = diffs('confirmed');
    const reportedPortion = s.map((r,i) => {
      const override = REPORTED_OVERRIDE[r.date];
      if(override===undefined || casesDiffs[i]===null) return casesDiffs[i];
      return Math.min(override, casesDiffs[i]);
    });
    const catchupPortion = s.map((r,i) => {
      const override = REPORTED_OVERRIDE[r.date];
      if(override===undefined || casesDiffs[i]===null) return 0;
      return Math.max(0, casesDiffs[i] - override);
    });
    // Barres verticales simples : couleur pleine pour la part vraiment
    // rapportée ce jour-là, teinte plus claire empilée par-dessus pour la
    // part de rattrapage — uniquement visible sur les 2 dates ci-dessus,
    // les autres barres restent d'une seule couleur (part de rattrapage
    // toujours à 0). Uniquement les cas ici — le détail des décès vit
    // désormais dans l'onglet "Origine des décès".
    datasets = [
      {
        label:tr('dailyChartLabel'),
        data:reportedPortion,
        backgroundColor:PALETTE.info,
        borderRadius:2,
        maxBarThickness:18,
        stack:'d'
      },
      {
        label:tr('catchupLabel'),
        data:catchupPortion,
        backgroundColor:tint(PALETTE.info, .35),
        borderRadius:2,
        maxBarThickness:18,
        stack:'d'
      }
    ];
  }

  // Le cumul vient se poser sur le quotidien, sur son propre axe : les deux
  // ordres de grandeur ne se comparent pas (une centaine contre plusieurs
  // milliers), un axe unique ecraserait les barres.
  if(chartMode === 'epidemic'){
    /* Deux courbes de cumul sur l'axe de droite, et un encodage a deux
       entrees seulement : la COULEUR dit de quoi on parle — bleu les cas,
       rouge les deces —, la FORME dit quelle lecture — barres le quotidien,
       courbe le cumul.

       Le cumul des cas etait ambre, pour ne pas se confondre avec les barres
       bleues qui decrivent pourtant le meme sujet. Cet ambre devient
       intenable des qu'une courbe rouge le rejoint : mesure faite, les deux
       teintes tombent a un ecart de 8 en deuteranopie, la ou le site s'impose
       15 ailleurs (voir le graphique par sexe). Deux longueurs d'onde longues
       que ce type de vision comprime l'une sur l'autre. Le bleu contre le
       rouge, lui, tient largement.

       Le graphique gagne donc une serie tout en perdant une famille de
       couleur. Et l'ecart entre les deux courbes se lit comme ce qu'il est :
       la letalite, 47,9 % au 22 aout, jusqu'ici un chiffre isole en haut de
       page. */
    datasets.push({
      type:'line',
      label: tr('chartCumulativeLabel'),
      data: s.map(r => r.confirmed),
      yAxisID: 'y1',
      borderColor: PALETTE.info,
      borderWidth: 2,
      tension: .25,
      pointRadius: 0,
      fill: false,
      spanGaps: true,
      order: 0
    });
    datasets.push({
      type:'line',
      label: tr('chartCumulativeDeathsLabel'),
      data: s.map(r => r.deaths === null || r.deaths === undefined ? null : r.deaths),
      yAxisID: 'y1',
      borderColor: PALETTE.critical,
      borderWidth: 2,
      tension: .25,
      pointRadius: 0,
      fill: false,
      spanGaps: true,
      order: 0
    });
  }

  const data = { labels, datasets };
  const opts = {
    responsive:true, maintainAspectRatio:false,
    interaction:{ mode:'index', intersect:false },
    plugins:{
      legend:{ labels:{ color:PALETTE.inkDim, font:{ family:PALETTE.font, size:11 }, boxWidth:10, usePointStyle:true } },
      tooltip:{
        backgroundColor:PALETTE.panel, borderColor:PALETTE.line, borderWidth:1,
        titleColor:PALETTE.ink, bodyColor:PALETTE.ink, titleFont:{family:PALETTE.font}, bodyFont:{family:PALETTE.font},
        filter: item => item.parsed.y !== 0
      }
    },
    scales:{
      x:{ ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10}, maxRotation:45, minRotation:45, autoSkip:true, maxTicksLimit:20 }, grid:{ display:false } },
      y:{ ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10}, callback:v=>fmt(v) }, grid:{ color:PALETTE.lineSoft }, beginAtZero:true }
    }
  };
  if(chartMode === 'epidemic'){
    opts.scales.y1 = {
      position:'right', beginAtZero:true,
      ticks:{ color:PALETTE.inkFaint, font:{family:PALETTE.font, size:10}, callback:v=>fmt(v) },
      grid:{ display:false }
    };
  }
  // Le type de graphique change selon le mode (barres pour le quotidien,
  // courbe pour le cumulé) : Chart.js ne permet pas de changer le type
  // d'une instance existante, donc on la détruit et on la recrée plutôt
  // que de la mettre à jour en place dans ce cas précis. On force aussi la
  // recréation en venant du mode "communityDeaths" (même type 'bar' que le
  // quotidien) pour ne jamais hériter du plugin de pourcentage attaché
  // à cette autre instance.
  const wantedType = 'bar';
  if(slot.chart && (slot.chart.config.type !== wantedType || slot.lastMode === 'communityDeaths')){
    slot.chart.destroy();
    slot.chart = null;
  }
  if(slot.chart){ slot.chart.data = data; slot.chart.options = opts; slot.chart.update(); }
  else { slot.chart = new Chart(ctx, { type:wantedType, data, options:opts }); }
  slot.lastMode = chartMode;
}
/* Rend tous les graphiques de la page. Chaque canvas declare son sujet :
   <canvas data-chart="epidemic">. Il n'y a plus de barre d'onglets — chaque
   graphique vit desormais sur la page dont il illustre les donnees. */
function renderChart(){
  document.querySelectorAll('canvas[data-chart]').forEach(canvas=>{
    renderOneChart(canvas, canvas.dataset.chart);
  });
}

/* Un graphique peut porter plusieurs vues, annoncees par une barre d'onglets
   qui designe son canvas : <nav data-chart-tabs="dataChart">. C'est le seul
   endroit du site ou des onglets se justifient — trois lectures d'un meme
   sujet, la ou l'accueil n'en montre qu'une. */
/* Bascule « Effectifs » / « Parts ». Elle ne vit que dans le cadre du
   graphique, et ne pilote que le mode pyramide : les autres modes la
   masquent. */
document.querySelectorAll('[data-pyramide-vue]').forEach(nav=>{
  nav.querySelectorAll('.subtab-btn').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      nav.querySelectorAll('.subtab-btn').forEach(b=>b.classList.toggle('active', b === btn));
      pyramideVue = btn.dataset.vue;
      const cible = document.getElementById('dataChart');
      if(cible) safeRun(()=>renderOneChart(cible, cible.dataset.chart), 'pyramideVue');
    });
  });
});

document.querySelectorAll('[data-chart-tabs]').forEach(nav=>{
  const canvas = document.getElementById(nav.dataset.chartTabs);
  if(!canvas) return;
  nav.querySelectorAll('.subtab-btn').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      nav.querySelectorAll('.subtab-btn').forEach(b=>b.classList.toggle('active', b === btn));
      canvas.dataset.chart = btn.dataset.mode;
      safeRun(()=>renderOneChart(canvas, canvas.dataset.chart), 'chartTab');
    });
  });
});

/* ============ CARTE ============ */
/* La carte est un SVG écrit en dur dans la page par le générateur : les 519
   zones de santé du pays, tracées d'après les contours officiels publiés par
   OCHA. Elle a remplacé Leaflet — plus de bibliothèque distante, plus de
   tuiles, plus de requête réseau. Elle est déjà là quand la page s'affiche et
   ne peut pas échouer, ce qui compte sur une connexion congolaise.

   Le JavaScript n'ajoute que ce qui bouge : recolorier les zones selon la date
   choisie au curseur, et cadrer la vue au clic. Sans lui, la carte reste
   exacte et lisible, simplement figée sur le dernier bulletin. */

let map = null;              // null tant qu'aucune carte n'est présente sur la page
let timelineIndex = null;    // null = « aujourd'hui » ; sinon index dans ZONES_HISTORY
let openPopupZoneName = null;

/* Marge autour d'une province quand on cadre dessus. */
const MAP_ZOOM_PADDING = 0.10;

function normaliseZoneName(text){
  return String(text || '')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[-_'\u2019.]/g, ' ')
    .toLowerCase().replace(/\s+/g, '');
}

/* Un nom de zone ne suffit pas : « Lubunga » existe en Tshopo et au
   Kasaï-Central. On indexe donc sur le couple zone + province. */
function zoneKey(name, province){
  return normaliseZoneName(name) + '|' + normaliseZoneName(province);
}

/* Mêmes seuils que ceux appliqués à la génération : une couleur doit vouloir
   dire la même chose avant et après l'exécution du script. */
function zoneLevel(cases){
  if(!cases) return 0;
  const steps = window.MAP_THRESHOLDS || [10, 50, 200];
  for(let i = 0; i < steps.length; i++){
    if(cases < steps[i]) return i + 1;
  }
  return steps.length + 1;
}

function initMap(){
  const svg = document.querySelector('.zonemap');
  if(!svg) return;
  const viewport = svg.querySelector('.zm-viewport');
  const box = (svg.getAttribute('viewBox') || '0 0 1000 1000').trim().split(/\s+/).map(Number);

  const zones = {};
  svg.querySelectorAll('.zm-zone').forEach(el=>{
    zones[zoneKey(el.dataset.name, el.dataset.sub)] = el;
  });

  map = { svg, viewport, width: box[2], height: box[3], zones,
          marks: [...svg.querySelectorAll('.zm-mark[data-x]')],
          full: { x: box[0], y: box[1], w: box[2], h: box[3] } };
  map.view = Object.assign({}, map.full);
  setupMapDragging();

  const country = document.getElementById('btnViewCountry');
  if(country) country.addEventListener('click', ()=>{
    resetMapView();
    setActiveMapBtn(country);
    if(window.mapClearSelection) window.mapClearSelection();
  });
  const epicentre = document.getElementById('btnViewIturi');
  if(epicentre) epicentre.addEventListener('click', ()=>{
    zoomToProvince('Ituri');
    setActiveMapBtn(epicentre);
  });

  /* Cliquer une zone cadre sur sa province. Le lien vers la page de la
     province reste dans le HTML — il fonctionne sans JavaScript, les moteurs
     le suivent, un clic milieu l'ouvre — et le panneau de détail à côté en
     propose un explicite.

     Sur la carte d'une province, il n'y a rien a cadrer : elle est deja
     cadree, et les rectangles de cadrage sont exprimes dans le repere de la
     carte du pays, pas dans le sien. */
  if(svg.dataset.scope === 'province') return;
  svg.querySelectorAll('.zm-zone').forEach(el=>{
    el.addEventListener('click', event=>{
      if(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if(event.button) return;
      event.preventDefault();
      zoomToProvince(el.dataset.sub, el.dataset.box);
      setActiveMapBtn(null);
    });
  });
}

/* ---------------- Cadrage, zoom et deplacement ----------------
   On ne touche pas au viewBox : on transforme le groupe qui porte le dessin.
   Le navigateur anime ca tout seul quand on le lui demande, et le reste du
   temps la transformation suit la souris sans latence. */

/* Bornes de zoom : jamais plus large que le pays, jamais plus serre que 1/14
   de sa largeur — au-dela on ne verrait plus qu'une poignee de zones. */
const MAP_MIN_SPAN_RATIO = 1 / 14;

function mapAspect(){ return map ? map.height / map.width : 1; }

function clampView(view){
  const full = map.full;
  view.w = Math.min(full.w, Math.max(full.w * MAP_MIN_SPAN_RATIO, view.w));
  view.h = view.w * mapAspect();
  view.x = Math.min(Math.max(view.x, full.x), full.x + full.w - view.w);
  view.y = Math.min(Math.max(view.y, full.y), full.y + full.h - view.h);
  return view;
}

function applyView(animate){
  if(!map || !map.viewport) return;
  clampView(map.view);
  const scale = map.width / map.view.w;
  const tx = -map.view.x * scale;
  const ty = -map.view.y * scale;
  // L'animation ne vaut que pour un cadrage commande : pendant un deplacement
  // a la souris, elle mettrait la carte en retard sur le geste.
  map.viewport.classList.toggle('is-animating', animate !== false);
  map.viewport.style.transform = `matrix(${scale},0,0,${scale},${tx},${ty})`;
  map.svg.classList.toggle('is-zoomed', scale > 1.05);
  // Les reperes suivent la carte mais ne grossissent pas avec elle : chacun
  // recoit l'echelle inverse autour de son propre point d'ancrage.
  if(map.marks) map.marks.forEach(mark=>{
    mark.setAttribute('transform',
      `translate(${mark.dataset.x} ${mark.dataset.y}) scale(${1 / scale})`);
  });
}

function mapIsZoomed(){
  return !!map && map.view.w < map.full.w - 0.5;
}

function zoomToBox(x, y, width, height){
  if(!map || !width || !height) return;
  const padX = width * MAP_ZOOM_PADDING, padY = height * MAP_ZOOM_PADDING;
  x -= padX; y -= padY; width += padX * 2; height += padY * 2;
  // On elargit la boite au format de la carte pour ne rien deformer.
  const wanted = Math.max(width, height / mapAspect());
  map.view = { x: x + width / 2 - wanted / 2,
               y: y + height / 2 - wanted * mapAspect() / 2,
               w: wanted, h: wanted * mapAspect() };
  applyView();
}

function resetMapView(){
  if(!map) return;
  map.view = Object.assign({}, map.full);
  applyView();
}

function zoomToProvince(province, fallbackBox){
  const boxes = window.MAP_PROVINCE_BOXES || {};
  let box = boxes[province];
  if(!box && fallbackBox) box = String(fallbackBox).trim().split(/\s+/).map(Number);
  if(!box || box.length !== 4) return;
  zoomToBox(box[0], box[1], box[2], box[3]);
}

/* Deplacement au clic maintenu — le geste attendu sur une carte. Il ne
   s'active qu'une fois zoome : a pleine etendue il n'y a rien a deplacer, et
   la carte laisse alors la page defiler normalement, y compris au doigt. */
function setupMapDragging(){
  const svg = map.svg;
  let drag = null;

  svg.addEventListener('pointerdown', event=>{
    if(event.button || !mapIsZoomed()) return;
    const ctm = map.viewport.getScreenCTM();
    if(!ctm || !ctm.a) return;
    drag = { x:event.clientX, y:event.clientY, scale:ctm.a,
             view:Object.assign({}, map.view), moved:0, id:event.pointerId };
    svg.classList.add('is-grabbing');
  });

  svg.addEventListener('pointermove', event=>{
    if(!drag) return;
    const dx = event.clientX - drag.x;
    const dy = event.clientY - drag.y;
    drag.moved = Math.max(drag.moved, Math.abs(dx) + Math.abs(dy));
    if(drag.moved < 4) return;
    if(svg.setPointerCapture && drag.id !== undefined && !drag.captured){
      try{ svg.setPointerCapture(drag.id); drag.captured = true; }
      catch(e){ /* sans importance : le deplacement fonctionne quand meme */ }
    }
    map.view = { x: drag.view.x - dx / drag.scale,
                 y: drag.view.y - dy / drag.scale,
                 w: drag.view.w, h: drag.view.h };
    applyView(false);
  });

  function end(){
    if(!drag) return;
    // Un deplacement n'est pas un clic : on neutralise celui qui suit, sinon
    // relacher la souris sur une zone la selectionnerait et cadrerait dessus.
    if(drag.moved > 4){
      svg.addEventListener('click', event=>{
        event.stopPropagation();
        event.preventDefault();
      }, { capture:true, once:true });
    }
    drag = null;
    svg.classList.remove('is-grabbing');
  }
  svg.addEventListener('pointerup', end);
  svg.addEventListener('pointercancel', end);
  svg.addEventListener('pointerleave', end);
}

function setActiveMapBtn(btn){
  // btn peut etre nul : la vue a ete cadree a la souris, aucun des deux
  // cadrages predefinis n'est alors actif.
  document.querySelectorAll('.map-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
}

function renderMap(){
  if(!map) return;

  const isHistorical = timelineIndex !== null && ZONES_HISTORY[timelineIndex];
  // « Aujourd'hui » s'appuie sur la derniere entree de ZONES_HISTORY plutot que
  // sur HEALTH_ZONES brut : cette derniere reflete le SitRep national tel quel,
  // sans le dedoublonnage ni le report de derniere valeur appliques a
  // l'historique.
  const latestEntry = ZONES_HISTORY.length ? ZONES_HISTORY[ZONES_HISTORY.length - 1] : null;
  const zonesToRender = isHistorical ? ZONES_HISTORY[timelineIndex].zones
    : (latestEntry ? latestEntry.zones : HEALTH_ZONES);

  // Evolution depuis le bulletin precedent : en vue historique on compare a
  // l'entree d'avant ; en vue « aujourd'hui » les bulletins donnent deja les
  // nouveaux cas et deces des dernieres 24 h.
  const previous = {};
  if(isHistorical && timelineIndex > 0){
    ZONES_HISTORY[timelineIndex - 1].zones.forEach(z=>{
      previous[zoneKey(z.name, z.province)] = z;
    });
  }
  const today = {};
  HEALTH_ZONES.forEach(z=>{ today[zoneKey(z.name, z.province)] = z; });

  // Toutes les zones repassent au gris : une zone touchee plus tard doit etre
  // eteinte quand on remonte le temps.
  Object.keys(map.zones).forEach(key=>{
    const el = map.zones[key];
    el.setAttribute('class', 'zm-zone is-0');
    delete el.dataset.cases;
    delete el.dataset.deaths;
    delete el.dataset.newCases;
    delete el.dataset.newDeaths;
  });

  zonesToRender.forEach(z=>{
    const key = zoneKey(z.name, z.province);
    const el = map.zones[key];
    if(!el) return;
    const cases = z.cases || 0;
    const deaths = z.deaths || 0;

    let newCases, newDeaths;
    if(isHistorical){
      const before = previous[key];
      newCases = before ? cases - (before.cases || 0) : cases;
      newDeaths = before ? deaths - (before.deaths || 0) : deaths;
    } else {
      const live = today[key] || z;
      newCases = live.newCases24h || 0;
      // Le total imprime par le bulletin, pas la somme des deux categories :
      // quand une seule est imprimee, l'autre colonne porte deja ce total et
      // l'addition le comptait deux fois (Bunia : +6 pour 3 deces reels).
      newDeaths = live.newDeaths24h != null
        ? live.newDeaths24h
        : (live.deathsCommunity24h || 0) + (live.deathsIntraCTE24h || 0);
    }

    el.setAttribute('class', 'zm-zone is-' + zoneLevel(cases));
    el.dataset.cases = fmt(cases);
    el.dataset.deaths = fmt(deaths);
    el.dataset.newCases = Math.max(0, newCases);
    el.dataset.newDeaths = Math.max(0, newDeaths);

    const title = el.querySelector('title');
    if(title){
      title.textContent = `${z.name} (${z.province}) — ${fmt(cases)} ${tr('cartoCasesShort')}, `
        + `${fmt(deaths)} ${tr('cartoDeathsShort')}`;
    }
  });

  if(window.majInfobulleZone) window.majInfobulleZone();
}

let timelinePlayTimer = null;
function stopTimelinePlay(){
  if(timelinePlayTimer){ clearInterval(timelinePlayTimer); timelinePlayTimer = null; }
  const btn = document.getElementById('timelinePlay');
  if(btn) btn.textContent = tr('timelinePlay');
}
function latestAvailableDateLabel(){
  // Date du dernier SNAPSHOT DE CARTE disponible (ZONES_HISTORY), pas
  // forcément celle du dernier SitRep national — les deux peuvent diverger
  // quand un SitRep est exclu de ZONES_HISTORY (voir
  // ZONES_HISTORY_EXCLUDED_SITREPS côté pipeline) tout en restant pris en
  // compte pour les chiffres nationaux. Afficher la date du SitRep exclu
  // ici serait trompeur : la carte à cette position montre en réalité les
  // données du dernier SitRep FIABLE précédent, pas celui-là.
  let latestDate = ZONES_HISTORY.length ? ZONES_HISTORY[ZONES_HISTORY.length - 1].date : null;
  if(!latestDate){
    latestDate = currentMeta ? currentMeta.reportingDate : null;
  }
  if(!latestDate){
    const s = sortedSitreps();
    latestDate = s.length ? s[s.length-1].date : null;
  }
  return latestDate ? (frDate(latestDate) + ' ' + latestDate.slice(0,4)) : tr('timelineToday');
}
function updateTimelineLabel(){
  const dateLabel = document.getElementById('timelineDate');
  const slider = document.getElementById('timelineSlider');
  if(!dateLabel || !slider) return;
  const todayBtn = document.getElementById('timelineToday');
  if(todayBtn) todayBtn.textContent = latestAvailableDateLabel();
  const v = parseInt(slider.value, 10);
  if(v >= ZONES_HISTORY.length){
    dateLabel.textContent = latestAvailableDateLabel();
  } else {
    const d = ZONES_HISTORY[v].date;
    dateLabel.textContent = frDate(d) + ' ' + d.slice(0,4);
  }
}
function setupTimeline(){
  if(!ZONES_HISTORY.length) return; // pas de données : le curseur reste masqué
  const wrap = document.getElementById('mapTimeline');
  const slider = document.getElementById('timelineSlider');
  const playBtn = document.getElementById('timelinePlay');
  const todayBtn = document.getElementById('timelineToday');
  if(!wrap || !slider || slider.dataset.built) return;
  slider.dataset.built = '1';

  wrap.style.display = 'block';
  // Une position "Aujourd'hui" distincte n'a de sens que si le dernier
  // SitRep national est VRAIMENT plus récent que le dernier instantané de
  // carte (ZONES_HISTORY) — sinon les deux pointent sur la même date et le
  // curseur affichait deux fois "17 août" à la suite, la seconde avec des
  // deltas à +0 puisque ZONES_HISTORY ne stocke pas les champs "24h" (vu
  // le 20/08/2026, une fois le SitRep 094 redevenu à jour et non-exclu).
  const lastHistoryDate = ZONES_HISTORY[ZONES_HISTORY.length - 1].date;
  const latestReportDate = currentMeta ? currentMeta.reportingDate : null;
  const needsTodaySlot = latestReportDate && latestReportDate > lastHistoryDate;
  slider.max = String(needsTodaySlot ? ZONES_HISTORY.length : ZONES_HISTORY.length - 1);
  slider.value = slider.max;
  updateTimelineLabel();

  slider.addEventListener('input', ()=>{
    const v = parseInt(slider.value, 10);
    timelineIndex = (v >= ZONES_HISTORY.length) ? null : v;
    updateTimelineLabel();
    renderMap();
  });

  todayBtn.addEventListener('click', ()=>{
    stopTimelinePlay();
    slider.value = slider.max;
    timelineIndex = (parseInt(slider.max,10) >= ZONES_HISTORY.length) ? null : parseInt(slider.max,10);
    updateTimelineLabel();
    renderMap();
  });

  playBtn.addEventListener('click', ()=>{
    if(timelinePlayTimer){ stopTimelinePlay(); return; }
    playBtn.textContent = tr('timelinePause');
    timelinePlayTimer = setInterval(()=>{
      let v = parseInt(slider.value, 10);
      v = (v >= parseInt(slider.max,10)) ? 0 : v + 1;
      slider.value = String(v);
      timelineIndex = (v >= ZONES_HISTORY.length) ? null : v;
      updateTimelineLabel();
      renderMap();
      if(v >= parseInt(slider.max,10)) stopTimelinePlay();
    }, 700);
  });
}

/* ============ RENDU GLOBAL ============ */
function safeRun(fn, label){
  try{ fn(); }catch(e){ console.error('Erreur lors du rendu:', label, e); }
}

function renderAll(){
  safeRun(renderZonesDropdown, 'zonesDropdown'); // menu de navigation : sur toutes les pages
  safeRun(renderKPIs, 'kpis');
  safeRun(renderChart, 'chart');
  safeRun(renderMap, 'map');
  safeRun(renderZonesTable, 'zonesTable');
  safeRun(renderReportsList, 'reportsList');
  safeRun(renderWhoReportsList, 'whoReportsList');
  safeRun(renderSocialUpdatesList, 'socialUpdatesList');
}

/* ============ RAPPORTS DE SITUATION OFFICIELS ============ */
/* Une carte de bulletin, cliquable dans son entier. Le meme balisage est
   produit a la generation par report_chip() dans scripts/build_pages.py :
   toute retouche doit etre faite des deux cotes. */
function reportCard(opts){
  const attrs = [
    opts.month ? `data-month="${opts.month}"` : '',
    opts.search ? `data-search="${opts.search}"` : ''
  ].filter(Boolean).join(' ');
  return `
    <a class="report-chip${opts.variant ? ' ' + opts.variant : ''}" href="${opts.href}"
       target="_blank" rel="noopener" ${attrs} title="${opts.title}">
      <span class="rc-head">
        <span class="rc-label">${opts.label}</span>
        <span class="rc-dl" aria-hidden="true"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3h7v7"/><path d="M10 14 21 3"/><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5"/></svg></span>
      </span>
      <span class="rc-date">${opts.date}</span>
    </a>`;
}

function renderReportsList(){
  const container = document.getElementById('reportsList');
  if(!container) return;
  if(!reportsData || reportsData.length===0){
    container.innerHTML = `<div class="map-note" style="text-align:center;grid-column:1/-1;">${tr('reportsEmpty')}</div>`;
    return;
  }
  const sorted = [...reportsData].sort((a,b)=>(b.sitrepNumber||'').localeCompare(a.sitrepNumber||''));

  // Regroupe par mois (à partir de reportingDate) pour éviter un mur plat
  // de ~90 puces identiques — les rapports sans date connue vont dans un
  // groupe à part, en dernier.
  const groups = [];
  const groupByKey = {};
  for(const r of sorted){
    let key = 'unknown', label = tr('reportsUnknownDate');
    if(r.reportingDate){
      const d = new Date(r.reportingDate+'T00:00:00');
      key = `${d.getFullYear()}-${d.getMonth()}`;
      label = `${tr('months')[d.getMonth()]} ${d.getFullYear()}`;
    }
    if(!groupByKey[key]){
      groupByKey[key] = { key, label, reports:[] };
      groups.push(groupByKey[key]);
    }
    groupByKey[key].reports.push(r);
  }

  container.innerHTML = groups.map(g => `
    <div class="reports-month-header" data-month-key="${g.key}">${g.label}</div>
    ${g.reports.map(r=>reportCard({
      label: tr('reportsSitrepLabel')(r.sitrepNumber),
      date: r.reportingDate ? tr('reportsReportingDate')(frDate(r.reportingDate) + ' ' + r.reportingDate.slice(0,4)) : tr('reportsUnknownDate'),
      href: assetUrl(r.file),
      title: tr('reportsDownload'),
      month: g.key,
      search: ((r.sitrepNumber||'')+' '+g.label+' '+(r.reportingDate||'')).toLowerCase()
    })).join('')}
  `).join('');

  renderReportsMonthNav(groups);
  applyReportsFilter();
}

/* Mois actuellement selectionne dans la barre de filtre. null = tous les mois.
   Par defaut on n'affiche que le mois le plus recent : la page listait sinon
   quatre-vingt-dix bulletins d'affilee, ce qui noyait le lecteur. */
let reportsMonthFilter = null;

function renderReportsMonthNav(groups){
  const nav = document.getElementById('reportsMonthNav');
  if(!nav) return;
  // Au premier rendu seulement : on se cale sur le mois le plus recent.
  if(reportsMonthFilter === null && groups.length) reportsMonthFilter = groups[0].key;

  const signature = groups.map(g=>g.key).join('|') + '#' + reportsMonthFilter;
  if(nav.dataset.built === signature) return;
  nav.dataset.built = signature;

  const buttons = [{key:null, label:tr('reportsFilterAll'), count:null}].concat(
    groups.map(g=>({key:g.key, label:g.label, count:g.reports.length})));

  nav.innerHTML = buttons.map(b=>{
    const active = (b.key === reportsMonthFilter) ? ' active' : '';
    const count = b.count ? ` <span class="count">${b.count}</span>` : '';
    return `<button type="button" class="subtab-btn${active}" data-month="${b.key === null ? '' : b.key}">${b.label}${count}</button>`;
  }).join('');

  nav.querySelectorAll('.subtab-btn').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      reportsMonthFilter = btn.getAttribute('data-month') || null;
      nav.querySelectorAll('.subtab-btn').forEach(b=>b.classList.toggle('active', b===btn));
      const search = document.getElementById('reportsSearch');
      if(search) search.value = '';   // un filtre chasse l'autre
      applyReportsFilter();
    });
  });
}

function applyReportsFilter(){
  const input = document.getElementById('reportsSearch');
  const container = document.getElementById('reportsList');
  if(!input || !container) return;
  const q = input.value.trim().toLowerCase();

  // Une recherche porte sur toute l'archive : taper un numero de bulletin ne
  // doit pas echouer sous pretexte qu'il appartient a un autre mois.
  const chips = container.querySelectorAll('.report-chip');
  chips.forEach(chip=>{
    const monthOk = q || !reportsMonthFilter || chip.dataset.month === reportsMonthFilter;
    const searchOk = !q || chip.dataset.search.includes(q);
    chip.style.display = (monthOk && searchOk) ? '' : 'none';
  });

  // Masque l'en-tête d'un mois si aucune puce de ce mois ne correspond au
  // filtre, pour ne pas laisser un titre de section vide affiché.
  container.querySelectorAll('.reports-month-header').forEach(header=>{
    let el = header.nextElementSibling, anyVisible = false;
    while(el && !el.classList.contains('reports-month-header')){
      if(el.classList.contains('report-chip') && el.style.display !== 'none'){ anyVisible = true; break; }
      el = el.nextElementSibling;
    }
    header.style.display = anyVisible ? '' : 'none';
  });
}
document.getElementById('reportsSearch')?.addEventListener('input', applyReportsFilter);

function renderWhoReportsList(){
  const section = document.getElementById('who-reports-section');
  const container = document.getElementById('whoReportsList');
  if(!container || !section) return;
  if(!whoReportsData || whoReportsData.length===0){
    // Au premier rendu, les donnees distantes ne sont pas encore chargees mais
    // la liste a deja ete ecrite en dur a la generation : la masquer ferait
    // clignoter la page. On ne masque que si la section est vraiment vide.
    if(!container.children.length) section.style.display = 'none';
    return;
  }
  section.style.display = 'block';
  const sorted = [...whoReportsData].sort((a,b)=>(b.number||'').localeCompare(a.number||''));
  container.innerHTML = sorted.map(r=>reportCard({
    label: tr('whoReportsLabel')(r.number),
    date: r.date ? tr('reportsReportingDate')(frDate(r.date) + ' ' + r.date.slice(0,4)) : tr('reportsUnknownDate'),
    href: assetUrl(r.file),
    title: tr('reportsDownload'),
    variant: 'is-who'
  })).join('');
}

function renderSocialUpdatesList(){
  const section = document.getElementById('social-updates-section');
  const container = document.getElementById('socialUpdatesList');
  if(!container || !section) return;
  if(!SOCIAL_UPDATES || SOCIAL_UPDATES.length===0){
    // Meme raison que pour les rapports OMS ci-dessus.
    if(!container.children.length) section.style.display = 'none';
    return;
  }
  section.style.display = 'block';
  const sorted = [...SOCIAL_UPDATES].sort((a,b)=>b.date.localeCompare(a.date));
  container.innerHTML = sorted.map(r=>reportCard({
    label: r.source || tr('socialUpdatesLabel'),
    date: tr('reportsReportingDate')(frDate(r.date) + ' ' + r.date.slice(0,4)),
    href: r.url,
    title: tr('socialUpdatesOpenLink'),
    variant: 'is-social'
  })).join('');
}

/* ============ FORMULAIRE DE CONTACT ============ */
const FORMSPREE_ENDPOINT = 'https://formspree.io/f/xaewpyqb';
const contactForm = document.getElementById('contactForm');
if(contactForm){
  contactForm.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const btn = document.getElementById('contactSubmitBtn');
    const successEl = document.getElementById('contactSuccess');
    const errorEl = document.getElementById('contactError');
    successEl.style.display = 'none';
    errorEl.style.display = 'none';
    btn.disabled = true;
    const btnLabel = btn.querySelector('span');
    const originalLabel = btnLabel.textContent;
    btnLabel.textContent = tr('contactSubmitBtnSending');
    try{
      const res = await fetch(FORMSPREE_ENDPOINT, {
        method:'POST',
        body:new FormData(contactForm),
        headers:{ 'Accept':'application/json' }
      });
      if(res.ok){
        successEl.style.display = 'block';
        contactForm.reset();
      } else {
        errorEl.style.display = 'block';
      }
    } catch(err){
      errorEl.style.display = 'block';
    } finally {
      btn.disabled = false;
      btnLabel.textContent = originalLabel;
    }
  });
}

/* ============ TABLEAU DES ZONES DE SANTÉ ============ */
let zonesSortKey = 'cases';
let zonesSortDir = 'desc';
let zonesFilterProvinceVal = 'all';
let zonesSearchVal = '';

/* Couleurs distinctes par province, pour le point dans le tableau des zones. */
const PROVINCE_COLORS = {
  "Ituri":PALETTE.info, "Nord-Kivu":PALETTE.active, "Haut-Uélé":PALETTE.stable,
  "Tshopo":"#6B5CA5", "Sud-Kivu":PALETTE.inkDim, "Bas-Uélé":PALETTE.critical
};
function cfrBadgeClass(cfr){
  if(cfr < 30) return 'zone-badge-low';
  if(cfr < 50) return 'zone-badge-mid';
  return 'zone-badge-high';
}

const ZONES_COLUMNS = [
  { key:'name',        i18n:'zonesTh1' },
  { key:'province',    i18n:'zonesTh2' },
  { key:'cases',       i18n:'zonesTh3', numeric:true },
  { key:'deaths',      i18n:'zonesTh4', numeric:true },
  { key:'cfr',         i18n:'zonesTh5', numeric:true },
  { key:'newCases24h', i18n:'zonesTh6', numeric:true }
];

function initZonesTableControls(){
  const search = document.getElementById('zonesSearch');
  if(search && !search.dataset.built){
    search.dataset.built = '1';
    search.addEventListener('input', ()=>{ zonesSearchVal = search.value.trim().toLowerCase(); renderZonesTable(); });
  }
  const headRow = document.getElementById('zonesTableHead');
  if(headRow && !headRow.dataset.built){
    headRow.dataset.built = '1';
    headRow.innerHTML = ZONES_COLUMNS.map(c=>
      `<th data-key="${c.key}" style="cursor:pointer;user-select:none;white-space:nowrap;" data-i18n="${c.i18n}"></th>`
    ).join('');
    headRow.querySelectorAll('th').forEach(th=>{
      th.addEventListener('click', ()=>{
        const key = th.getAttribute('data-key');
        if(zonesSortKey === key){ zonesSortDir = zonesSortDir==='asc' ? 'desc' : 'asc'; }
        else { zonesSortKey = key; zonesSortDir = ZONES_COLUMNS.find(c=>c.key===key).numeric ? 'desc' : 'asc'; }
        renderZonesTable();
      });
    });
  }
}

/* Les provinces se listent partout dans le meme ordre — du plus touche au
   moins touche — cote serveur comme cote client. L'ordre d'apparition dans
   HEALTH_ZONES ne le garantissait pas, et ces menus etant reecrits sur toutes
   les pages, ils defaisaient le tri du generateur. */
function provincesTriees(){
  const cas = Object.fromEntries(
    PROVINCE_TABLE_DATA.map(p => [p.name, p.confirmed || 0]));
  return [...new Set(HEALTH_ZONES.map(z=>z.province))]
    .sort((a,b) => (cas[b] || 0) - (cas[a] || 0));
}

function renderZonesSubtabs(){
  const nav = document.getElementById('zonesSubtabNav');
  if(!nav) return;
  const provinces = provincesTriees();
  // reconstruit seulement si la liste de provinces a changé (nouvelles données)
  const wanted = ['all', ...provinces].join('|');
  if(nav.dataset.built !== wanted){
    nav.dataset.built = wanted;
    const allBtn = `<button type="button" class="subtab-btn" data-province="all">${tr('zonesFilterAll')}</button>`;
    const provBtns = provinces.map(p=>{
      const color = PROVINCE_COLORS[p] || 'var(--ink-faint)';
      return `<button type="button" class="subtab-btn" data-province="${p}"><span class="dot" style="background:${color};"></span>${p}</button>`;
    }).join('');
    nav.innerHTML = allBtn + provBtns;
    nav.querySelectorAll('.subtab-btn').forEach(btn=>{
      btn.addEventListener('click', ()=>{
        zonesFilterProvinceVal = btn.getAttribute('data-province');
        renderZonesTable();
      });
    });
  }
  nav.querySelectorAll('.subtab-btn').forEach(btn=>{
    btn.classList.toggle('active', btn.getAttribute('data-province')===zonesFilterProvinceVal);
  });
}

function renderZonesDropdown(){
  const dd = document.getElementById('zonesDropdown');
  if(!dd) return;
  const provinces = provincesTriees();
  const wanted = ['all', ...provinces].join('|');
  if(dd.dataset.built === wanted) return;
  dd.dataset.built = wanted;
  /* De vrais liens, plus des boutons : chaque province a maintenant sa propre
     page indexable, et ce menu est le principal maillage interne vers elles.
     PROVINCE_LINKS / PROVINCES_INDEX_URL / DATA_PAGE_URL sont injectes par le
     generateur, dans la bonne langue. */
  const links = window.PROVINCE_LINKS || {};
  const dataUrl = window.DATA_PAGE_URL || '/donnees/';
  const allUrl = window.PROVINCES_INDEX_URL || dataUrl;
  /* Le premier element porte le nom de la page qu'il ouvre — « Tableaux et
     graphiques » — et non « Toutes les provinces », qui est le libelle du
     filtre du tableau et annoncait ici une liste de provinces. Le generateur
     y pose aria-current ; comme on reecrit le HTML, on le repose. */
  const ici = location.pathname.replace(/\/*$/, '/');
  const surTableaux = allUrl.replace(/\/*$/, '/') === ici;
  const marque = surTableaux ? ' aria-current="page"' : '';
  const allItem = `<a class="tab-dropdown-item"${marque} href="${allUrl}">${tr('navDataTables')}</a>`;
  const provItems = provinces.map(p=>{
    const color = PROVINCE_COLORS[p] || 'var(--ink-faint)';
    const href = links[p] || (dataUrl + '?province=' + encodeURIComponent(p));
    return `<a class="tab-dropdown-item" href="${href}"><span class="dot" style="background:${color};"></span>${p}</a>`;
  }).join('');
  dd.innerHTML = allItem + provItems;
}

let zonesActiveView = 'province';
function switchZonesView(view){
  zonesActiveView = view;
  const provinceEl = document.getElementById('zonesView-province');
  const zoneEl = document.getElementById('zonesView-zone');
  if(provinceEl) provinceEl.style.display = view==='province' ? 'block' : 'none';
  if(zoneEl) zoneEl.style.display = view==='zone' ? 'block' : 'none';
  document.querySelectorAll('#zonesViewNav .subtab-btn').forEach(btn=>{
    btn.classList.toggle('active', btn.getAttribute('data-view')===view);
  });
}
document.querySelectorAll('#zonesViewNav .subtab-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>switchZonesView(btn.getAttribute('data-view')));
});

function renderProvinceSummary(){
  const body = document.getElementById('provinceSummaryBody');
  if(!body) return;
  const rows = [...PROVINCE_TABLE_DATA].sort((a,b)=>b.confirmed-a.confirmed);
  const nationalTotal = national && national.confirmed ? national.confirmed : null;
  body.innerHTML = rows.map(p=>{
    const color = PROVINCE_COLORS[p.name] || 'var(--ink-faint)';
    const zonesAffected = p.healthZonesAffected ? `${p.healthZonesAffected.n} / ${p.healthZonesAffected.total}` : '—';
    const newBadge = p.newCases24h>0
      ? `<span class="zone-new-badge has-new">+${fmt(p.newCases24h)}</span>`
      : `<span class="zone-new-badge no-new">${fmt(p.newCases24h)}</span>`;
    const pctOfTotal = nationalTotal ? ` <span style="color:var(--ink-faint);">(${fmtCfr(p.confirmed/nationalTotal*100)})</span>` : '';
    return `
      <tr>
        <td><div class="zone-name-cell"><span class="zdot" style="background:${color};"></span>${p.name}</div></td>
        <td>${fmt(p.confirmed)}${pctOfTotal}</td>
        <td>${fmt(p.deaths)}</td>
        <td><span class="zone-badge ${cfrBadgeClass(p.cfr)}">${fmtCfr(p.cfr)}</span></td>
        <td>${zonesAffected}</td>
        <td>${newBadge}</td>
      </tr>
    `;
  }).join('');
}

function renderZonesTable(){
  initZonesTableControls();
  renderProvinceSummary();

  const subEl = document.getElementById('zonesTableSub');
  if(subEl){
    const n = (national && national.healthZonesAffected) ? national.healthZonesAffected.n : HEALTH_ZONES.length;
    const total = (national && national.healthZonesAffected) ? national.healthZonesAffected.total : 151;
    const dateStr = (currentMeta && currentMeta.reportingDate) ? frDate(currentMeta.reportingDate) : '';
    subEl.textContent = tr('zonesTableSub')(n, total, currentMeta ? currentMeta.sitrepNumber : '', dateStr);
  }

  renderZonesSubtabs();

  // en-têtes (texte + indicateur de tri)
  const zonesHead = document.getElementById('zonesTableHead');
  if(!zonesHead) return;   // page sans tableau détaillé : rien de plus à faire
  zonesHead.querySelectorAll('th').forEach(th=>{
    const key = th.getAttribute('data-key');
    const col = ZONES_COLUMNS.find(c=>c.key===key);
    let label = tr(col.i18n);
    if(zonesSortKey === key) label += zonesSortDir==='asc' ? ' ▲' : ' ▼';
    th.textContent = label;
  });

  let rows = HEALTH_ZONES.filter(z=>{
    if(zonesFilterProvinceVal!=='all' && z.province!==zonesFilterProvinceVal) return false;
    if(zonesSearchVal && !z.name.toLowerCase().includes(zonesSearchVal)) return false;
    return true;
  });

  rows = rows.slice().sort((a,b)=>{
    const col = ZONES_COLUMNS.find(c=>c.key===zonesSortKey);
    let av = a[zonesSortKey], bv = b[zonesSortKey];
    if(!col.numeric){ av = String(av).toLowerCase(); bv = String(bv).toLowerCase(); }
    let cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return zonesSortDir==='asc' ? cmp : -cmp;
  });

  const body = document.getElementById('zonesTableBody');
  const emptyState = document.getElementById('zonesEmptyState');
  const resultCount = document.getElementById('zonesResultCount');

  if(rows.length===0){
    body.innerHTML = '';
    emptyState.style.display = 'block';
  } else {
    emptyState.style.display = 'none';
    const maxCases = Math.max(...HEALTH_ZONES.map(z=>z.cases));
    body.innerHTML = rows.map(z=>{
      const barPct = maxCases>0 ? Math.max(2, Math.round(z.cases/maxCases*100)) : 0;
      const dotColor = PROVINCE_COLORS[z.province] || 'var(--ink-faint)';
      const newBadge = z.newCases24h>0
        ? `<span class="zone-new-badge has-new">+${fmt(z.newCases24h)}</span>`
        : `<span class="zone-new-badge no-new">${fmt(z.newCases24h)}</span>`;
      return `
      <tr>
        <td><div class="zone-name-cell"><span class="zdot" style="background:${dotColor};"></span>${z.name}</div></td>
        <td>${z.province}</td>
        <td><div class="zone-cases-cell"><span class="zone-cases-num">${fmt(z.cases)}</span><div class="zone-bar-track"><div class="zone-bar-fill" style="width:${barPct}%;background:${dotColor};"></div></div></div></td>
        <td>${fmt(z.deaths)}</td>
        <td><span class="zone-badge ${cfrBadgeClass(z.cfr)}">${fmtCfr(z.cfr)}</span></td>
        <td>${newBadge}</td>
      </tr>
    `;
    }).join('');
  }
  resultCount.textContent = tr('zonesResultCount')(rows.length, HEALTH_ZONES.length);
}

/* ============ LANGUE ============ */
function applyStaticI18n(){
  document.querySelectorAll('[data-i18n]').forEach(el=>{
    const key = el.getAttribute('data-i18n');
    const val = tr(key);
    if(typeof val === 'string') el.textContent = val;
  });
  document.querySelectorAll('[data-i18n-html]').forEach(el=>{
    const key = el.getAttribute('data-i18n-html');
    const val = tr(key);
    if(typeof val === 'string') el.innerHTML = val;
  });
  document.querySelectorAll('[data-i18n-aria]').forEach(el=>{
    el.setAttribute('aria-label', tr(el.getAttribute('data-i18n-aria')));
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>{
    el.setAttribute('placeholder', tr(el.getAttribute('data-i18n-placeholder')));
  });
  // Même logique que les cases d'en-tête (effectiveNationalKPIs) : préfère
  // la date du dernier point de situation X/Twitter si elle est plus
  // récente que le dernier SitRep PDF — pour rester cohérent avec les
  // chiffres affichés juste au-dessus, plutôt que d'afficher une date "en
  // retard" sur les chiffres qu'elle est censée dater.
  const effDate = effectiveNationalKPIs();
  const latestEntry = sortedSitreps()[sortedSitreps().length-1];
  const displayDate = (effDate && effDate.date > latestEntry.date) ? effDate.date : latestEntry.date;
  // « 19/08/26 » est sans ambiguite en francais mais pas en anglais, ou le
  // mois vient souvent en premier. Les deux lignes de fraicheur partagent
  // donc la meme date ecrite en toutes lettres, dans la langue de la page.
  const [fy,fm,fd] = displayDate.split('-');
  const lastUpdateDate = `${parseInt(fd,10)} ${tr('months')[parseInt(fm,10)-1]} ${fy}`;
  // Deux dates : celle du dernier bulletin officiel, puis celle de la derniere
  // verification. La seconde explique l'ecart plutot que de le laisser en
  // suspens — sans elle, un lecteur ne distingue pas « aucun nouveau bulletin »
  // de « site abandonne ».
  const autoEl = document.getElementById('autoUpdateNote');
  if(autoEl) autoEl.innerHTML = tr('autoUpdateNote')(lastUpdateDate);
  const today = new Date();
  const todayDate = `${today.getDate()} ${tr('months')[today.getMonth()]} ${today.getFullYear()}`;
  const todayEl = document.getElementById('todayUpdateNote');
  if(todayEl) todayEl.innerHTML = tr('todayUpdateNote')(todayDate);
  /* <title> et <html lang> sont ecrits par le generateur : chaque page a son
     propre titre indexable, on ne l'ecrase plus ici. */
}

/* setLang() a disparu avec la bascule cote client : voir le commentaire P1. */

/* ============ CARTE-RÉSUMÉ POUR PARTAGE ============ */
async function generateShareImage(){
  if(document.fonts && document.fonts.ready) await document.fonts.ready;
  const s = sortedSitreps();
  const latest = s[s.length-1];
  const W = 1080, H = 1350;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d');

  const bg = PALETTE.bg, ink = PALETTE.ink, inkDim = PALETTE.inkDim, inkFaint = PALETTE.inkFaint;
  const info = PALETTE.info, critical = PALETTE.critical, stable = PALETTE.stable, line = PALETTE.line;

  // fond
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, W, H);

  // bandeau haut
  ctx.fillStyle = ink;
  ctx.fillRect(0, 0, W, 8);

  const pad = 72;
  let y = 130;

  // eyebrow
  ctx.fillStyle = critical;
  ctx.beginPath(); ctx.arc(pad+6, y-8, 6, 0, Math.PI*2); ctx.fill();
  ctx.fillStyle = inkDim;
  ctx.font = "600 24px 'Public Sans', sans-serif";
  ctx.fillText(tr('eyebrow').toUpperCase(), pad+24, y);

  // titre
  y += 76;
  ctx.fillStyle = ink;
  ctx.font = '600 76px "Source Serif 4", Georgia, serif';
  ctx.fillText((tr('h1')+' / 2026').toUpperCase(), pad, y);

  // ligne
  y += 40;
  ctx.strokeStyle = line; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(W-pad, y); ctx.stroke();

  // KPI - grille 2x2
  const kpis = [
    { label: tr('labelConfirmed'), value: fmt(latest.confirmed), color: info },
    { label: tr('labelDeaths'), value: fmt(latest.deaths), color: critical },
    { label: tr('labelRecovered'), value: latest.recovered!=null ? fmt(latest.recovered) : '—', color: stable },
    { label: tr('labelCfr'), value: (latest.deaths!=null && latest.confirmed>0) ? fmtCfr(latest.deaths/latest.confirmed*100) : '—', color: ink }
  ];
  const gridTop = y + 60;
  const cellW = (W - pad*2) / 2, cellH = 190;
  kpis.forEach((k, i)=>{
    const col = i % 2, row = Math.floor(i/2);
    const cx = pad + col*cellW, cy = gridTop + row*cellH;
    ctx.fillStyle = inkFaint;
    ctx.font = "500 24px 'Public Sans', sans-serif";
    ctx.fillText(k.label.toUpperCase(), cx, cy);
    ctx.fillStyle = k.color;
    ctx.font = '600 88px "Source Serif 4", Georgia, serif';
    ctx.fillText(k.value, cx, cy + 90);
  });

  // ligne basse
  const lineY = gridTop + cellH*2 - 40;
  ctx.strokeStyle = line;
  ctx.beginPath(); ctx.moveTo(pad, lineY); ctx.lineTo(W-pad, lineY); ctx.stroke();

  // date + source
  ctx.fillStyle = inkDim;
  ctx.font = '500 26px "Public Sans", sans-serif';
  ctx.fillText(frDate(latest.date), pad, lineY + 50);
  ctx.fillStyle = inkFaint;
  ctx.font = '400 22px "Public Sans", sans-serif';
  ctx.fillText(location.hostname || 'ebola-tracker', pad, lineY + 84);

  return new Promise(resolve=>canvas.toBlob(blob=>resolve(blob), 'image/png'));
}

async function handleShare(){
  const btn = document.getElementById('btnShare');
  const original = btn.innerHTML;
  const shareUrl = location.href;
  btn.disabled = true;
  try{
    if(navigator.share){
      // Pas de fichier joint ici : beaucoup d'apps ignorent l'URL dès qu'une
      // image est présente. On privilégie le lien, mis aussi dans le texte
      // pour les apps qui n'affichent que "text".
      await navigator.share({
        title: tr('h1'),
        text: tr('eyebrow') + '\n' + shareUrl,
        url: shareUrl
      });
    } else if(navigator.clipboard && navigator.clipboard.writeText){
      await navigator.clipboard.writeText(shareUrl);
      btn.innerHTML = `<span>${tr('linkCopied')}</span>`;
      setTimeout(()=>{ btn.innerHTML = original; }, 2000);
      return;
    } else {
      // Repli ultime : sélection manuelle via un prompt
      window.prompt(tr('shareBtn'), shareUrl);
    }
  } catch(err){
    if(err.name !== 'AbortError') console.error('Partage impossible :', err);
  } finally {
    btn.disabled = false;
  }
}
document.getElementById('btnShare')?.addEventListener('click', handleShare);


/* ============ MENU DES PROVINCES ============ */
/* La liste des provinces est repliee par defaut sous « Donnees detaillees ».
   Les liens restent dans le HTML quoi qu'il arrive : le repli n'est qu'un
   confort de lecture, il ne cache rien aux moteurs de recherche. */
/* ---- menu mobile en plein ecran ----
   Sous 900 px la navigation n'est plus une barre qui defile : trois traits
   l'ouvrent en plein ecran sous l'en-tete. Le pied de page porte les memes
   liens, donc l'absence de JavaScript ne prive personne de rien. */
(function setupMenuMobile(){
  const bouton = document.getElementById('btnMenu');
  const barre = document.querySelector('.sidebar');
  if(!bouton || !barre) return;

  // La hauteur de l'en-tete varie avec la longueur de la marque et la
  // taille de police du lecteur : on la mesure plutot que de la figer.
  function mesurerEntete(){
    const tete = barre.querySelector('.side-head');
    if(!tete) return;
    const bas = tete.getBoundingClientRect().bottom - barre.getBoundingClientRect().top;
    barre.style.setProperty('--entete', Math.round(bas + 58) + 'px');
  }

  function poser(ouvert){
    barre.classList.toggle('menu-ouvert', ouvert);
    document.body.classList.toggle('menu-ouvert', ouvert);
    bouton.setAttribute('aria-expanded', String(ouvert));
    const etiquette = ouvert ? bouton.dataset.labelClose : bouton.dataset.labelOpen;
    if(etiquette) bouton.setAttribute('aria-label', etiquette);
    if(!ouvert) return;
    mesurerEntete();
    /* Dans un menu qui occupe toute la page, replier les provinces n'economise
       rien : on les deplie a l'ouverture. Le chevron continue de servir a les
       refermer si la liste gene. */
    const chevron = barre.querySelector('.side-toggle');
    const provinces = chevron && document.getElementById(
      chevron.getAttribute('aria-controls'));
    if(provinces && provinces.hidden){
      provinces.hidden = false;
      chevron.setAttribute('aria-expanded', 'true');
    }
  }

  bouton.addEventListener('click', ()=>{
    poser(bouton.getAttribute('aria-expanded') !== 'true');
  });

  // Echap referme, comme tout menu qui se respecte.
  document.addEventListener('keydown', e=>{
    if(e.key === 'Escape' && bouton.getAttribute('aria-expanded') === 'true'){
      poser(false);
      bouton.focus();
    }
  });

  // Un lien vers la page courante ne provoque aucun chargement : sans ca le
  // menu resterait ouvert par-dessus la page qu'on vient de demander.
  barre.querySelectorAll('.side-panel a').forEach(a=>{
    a.addEventListener('click', ()=>poser(false));
  });

  // Repasse en grand ecran : la colonne laterale reprend sa forme, et le
  // verrou de defilement n'a plus lieu d'etre.
  const grandEcran = window.matchMedia('(min-width:901px)');
  const surChangement = ()=>{ if(grandEcran.matches) poser(false); };
  if(grandEcran.addEventListener) grandEcran.addEventListener('change', surChangement);
  else if(grandEcran.addListener) grandEcran.addListener(surChangement);
  window.addEventListener('resize', mesurerEntete);
  mesurerEntete();
})();

(function setupProvinceMenu(){
  const toggle = document.querySelector('.side-toggle');
  if(!toggle) return;
  const list = document.getElementById(toggle.getAttribute('aria-controls'));
  if(!list) return;
  toggle.addEventListener('click', ()=>{
    const open = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!open));
    list.hidden = open;
    if(open) return;
    /* Sur petit ecran la navigation est une barre qui defile, et les
       provinces s'ouvrent a droite du chevron — donc hors du champ. Ouvrir un
       menu sans rien montrer ne vaut pas mieux que de ne pas l'ouvrir : on
       amene la premiere province sous les yeux. */
    const bar = toggle.closest('.side-nav');
    if(!bar || bar.scrollWidth <= bar.clientWidth) return;
    /* On cale sur le libelle, pas sur le chevron : sinon « Donnees
       detaillees » sortait du champ et l'on ne savait plus quel menu on
       venait d'ouvrir. */
    const libelle = toggle.previousElementSibling || toggle;
    const cible = Math.max(0, libelle.offsetLeft - 12);
    if(bar.scrollTo){
      bar.scrollTo({ left: cible, behavior: 'smooth' });
    } else {
      bar.scrollLeft = cible;   // vieux WebView Android
    }
  });
})();

/* ============ INFOBULLE DE ZONE (TELEPHONE) ============ */
/* Sur petit ecran, le panneau de detail vit 300 px sous le pli : toucher une
   zone mettait a jour quelque chose d'invisible. Une case ancree a la zone
   touchee prend le relais, refermee par une croix. Le panneau, lui, garde ses
   cinq chiffres nationaux — la case ne sert qu'aux zones. */
(function setupZonePopup(){
  const popup = document.getElementById('zonePopup');
  if(!popup) return;
  const scene = popup.closest('.zonemap-stage');
  if(!scene) return;
  const nom = document.getElementById('zonePopupName');
  const cas = document.getElementById('zonePopupCases');
  const deces = document.getElementById('zonePopupDeaths');
  const province = document.getElementById('zonePopupProvince');
  const lien = document.getElementById('zonePopupMore');
  const croix = document.getElementById('zonePopupClose');
  const petitEcran = window.matchMedia('(max-width:900px)');
  let courante = null;

  function ecart(valeur){
    if(valeur === undefined || valeur === null || valeur === '') return '';
    const n = parseInt(valeur, 10);
    return Number.isNaN(n) ? '' : ' <span class="d">(+' + fmt(Math.max(0, n)) + ')</span>';
  }

  function remplir(zone){
    nom.textContent = zone.dataset.name || '';
    cas.innerHTML = (zone.dataset.cases || '—') + ecart(zone.dataset.newCases);
    deces.innerHTML = (zone.dataset.deaths || '—') + ecart(zone.dataset.newDeaths);
    province.textContent = zone.dataset.sub || '';
    const href = zone.dataset.href;
    lien.hidden = !href;
    if(href) lien.setAttribute('href', href);
  }

  /* La case se pose au-dessus de la zone, ou en dessous s'il n'y a pas la
     place. Elle est bornee aux bords de la carte pour ne jamais sortir de
     l'ecran ; seule la pointe suit alors l'ancre. */
  function placer(zone){
    const rz = zone.getBoundingClientRect();
    const rs = scene.getBoundingClientRect();
    const ancre = rz.left + rz.width / 2 - rs.left;
    const largeur = popup.offsetWidth, hauteur = popup.offsetHeight;

    let haut = rz.top - rs.top - 13 - hauteur;
    const dessous = haut < 4;
    if(dessous) haut = rz.bottom - rs.top + 13;

    let gauche = Math.round(ancre - largeur / 2);
    gauche = Math.max(6, Math.min(gauche, rs.width - largeur - 6));

    popup.style.left = gauche + 'px';
    popup.style.top = Math.round(haut) + 'px';
    popup.classList.toggle('est-dessous', dessous);
    popup.style.setProperty('--pointe',
      Math.max(16, Math.min(ancre - gauche, largeur - 16)) + 'px');
  }

  function fermer(){
    popup.hidden = true;
    courante = null;
  }

  function ouvrir(zone){
    courante = zone;
    remplir(zone);
    popup.hidden = false;   // il faut l'afficher pour pouvoir le mesurer
    placer(zone);
  }

  croix.addEventListener('click', fermer);
  document.addEventListener('keydown', e=>{ if(e.key === 'Escape') fermer(); });

  document.querySelectorAll('.zm-zone').forEach(zone=>{
    zone.addEventListener('click', ()=>{
      if(!petitEcran.matches) return;
      if(courante === zone){ fermer(); return; }
      ouvrir(zone);
    });
  });

  /* Toucher une zone cadre aussi sur sa province : la carte glisse pendant
     une demi-seconde, et la case doit suivre son ancre. */
  const cadre = scene.querySelector('.zm-viewport');
  if(cadre) cadre.addEventListener('transitionend', ()=>{
    if(courante && !popup.hidden) placer(courante);
  });
  window.addEventListener('resize', ()=>{
    if(!petitEcran.matches) fermer();
    else if(courante && !popup.hidden) placer(courante);
  });

  /* Le curseur temporel reecrit les chiffres de chaque zone : la case ouverte
     doit dire la meme chose que la carte sous elle. */
  window.majInfobulleZone = function(){
    if(courante && !popup.hidden){ remplir(courante); placer(courante); }
  };
})();

/* ============ CARTOGRAMME ============ */
/* La carte des zones de sante est ecrite en dur a la generation : elle
   s'affiche et se lit sans JavaScript. On n'ajoute ici que le confort —
   survoler une zone met a jour le panneau de detail a cote, et le quitter
   revient au total national. */
(function setupCartogram(){
  const detail = document.getElementById('cartoDetail');
  if(!detail) return;
  const nameEl = document.getElementById('cartoName');
  const noteEl = document.getElementById('cartoNote');
  const casesEl = document.getElementById('cartoCases');
  const deathsEl = document.getElementById('cartoDeaths');
  const casesDeltaEl = document.getElementById('cartoCasesDelta');
  const deathsDeltaEl = document.getElementById('cartoDeathsDelta');
  const subEl = document.getElementById('cartoSub');
  const zones = document.querySelectorAll('.zm-zone');
  if(!zones.length) return;

  const base = {
    name: detail.dataset.defaultName || '',
    sub: detail.dataset.defaultSub || '',
    cases: detail.dataset.defaultCases || '',
    deaths: detail.dataset.defaultDeaths || '',
    hint: subEl ? subEl.innerHTML : ''
  };
  const moreLabel = detail.dataset.more || '';

  /* « (+12) », et « (+0) » quand rien n'a bouge depuis le bulletin precedent :
     l'absence de nouveau cas est une information, pas un vide. Rien ne
     s'affiche seulement quand la donnee n'existe pas du tout. */
  function delta(value){
    if(value === undefined || value === null || value === '') return '';
    const n = parseInt(value, 10);
    return Number.isNaN(n) ? '' : '(+' + fmt(Math.max(0, n)) + ')';
  }

  function fill(name, sub, cases, deaths, newCases, newDeaths, href){
    detail.classList.remove('is-empty');
    if(nameEl) nameEl.textContent = name;
    if(noteEl) noteEl.textContent = sub;
    if(casesEl) casesEl.textContent = cases || '—';
    if(deathsEl) deathsEl.textContent = deaths || '—';
    if(casesDeltaEl) casesDeltaEl.textContent = delta(newCases);
    if(deathsDeltaEl) deathsDeltaEl.textContent = delta(newDeaths);
    if(!subEl) return;
    if(href){
      const note = (delta(newCases) || delta(newDeaths))
        ? `<span class="cd-note">${tr('cartoDeltaNote') || ''}</span>` : '';
      subEl.innerHTML = `<a class="more" href="${href}">${moreLabel}</a>${note}`;
    } else {
      subEl.innerHTML = base.hint;
    }
  }

  const petitEcran = window.matchMedia('(max-width:900px)');

  function show(zone){
    /* Sur telephone, l'infobulle ancree a la zone repond a sa place, et le
       panneau conserve les cinq chiffres nationaux. */
    if(petitEcran.matches) return;
    fill(zone.dataset.name || '', zone.dataset.sub || '',
         zone.dataset.cases, zone.dataset.deaths,
         zone.dataset.newCases, zone.dataset.newDeaths,
         zone.dataset.href);
  }
  /* Etat de repos : les cinq chiffres nationaux, en permanence. Ils cedent la
     place au bilan d'une zone des qu'on la survole, et reviennent en sortant —
     sauf si une zone a ete cliquee, auquel cas elle reste affichee pour qu'on
     puisse atteindre son lien. */
  function showDefault(){
    detail.classList.add('is-empty');
    if(nameEl) nameEl.textContent = base.name;
    if(noteEl) noteEl.textContent = base.sub;
    if(subEl) subEl.innerHTML = base.hint;
  }

  /* La zone cliquee reste affichee dans le panneau. Sans ca, le lien « voir la
     province » disparaissait des que la souris quittait la carte : impossible
     de l'atteindre. Survoler une autre zone la previsualise, et en sortir
     revient a la zone retenue — pas au total national. */
  let pinned = null;

  function select(zone){
    if(petitEcran.matches) return;
    if(pinned === zone) return;
    if(pinned) pinned.classList.remove('is-selected');
    pinned = zone;
    if(zone){
      zone.classList.add('is-selected');
      // Aucune notion de plan en SVG : pour que le contour de la zone retenue
      // ne soit pas recouvert par ses voisines, on la redessine en dernier.
      if(zone.parentNode) zone.parentNode.appendChild(zone);
      show(zone);
    } else {
      showDefault();
    }
  }
  window.mapClearSelection = ()=>select(null);

  zones.forEach(zone=>{
    zone.addEventListener('mouseenter', ()=>show(zone));
    zone.addEventListener('focus', ()=>show(zone));
    zone.addEventListener('mouseleave', ()=>{ pinned ? show(pinned) : showDefault(); });
    zone.addEventListener('blur', ()=>{ pinned ? show(pinned) : showDefault(); });
    zone.addEventListener('click', ()=>select(zone));
  });
})();

/* ============ COMPATIBILITE DES ANCIENNES ANCRES ============ */
/* Le site etait monopage : les liens deja partages pointent vers /#zones,
   /#reports, /#about… On les redirige une fois vers la vraie page. La table
   est injectee par le generateur, uniquement sur les pages d'accueil. */
(function redirectLegacyHash(){
  const routes = window.LEGACY_HASH_ROUTES;
  if(!routes) return;
  const h = location.hash.replace('#','');
  if(h && routes[h]) location.replace(routes[h]);
})();

/* ============ INIT ============ */
function mergeHealthZonesWithHistory(){
  // Complète HEALTH_ZONES (données riches du SitRep le plus récent) avec
  // toute zone présente dans la dernière entrée de ZONES_HISTORY mais
  // absente de HEALTH_ZONES — même principe que côté pipeline
  // (rebuild_zones_history) : un SitRep qui cesse de citer une zone ne
  // doit jamais la faire disparaître, ni de la carte, ni du tableau
  // détaillé. Les champs "du jour" (nouveaux cas 24h, décès 24h) sont mis
  // à 0 pour ces zones reportées, faute de vraie donnée plus récente.
  if(!ZONES_HISTORY.length) return;
  const known = new Set(HEALTH_ZONES.map(z=>z.name));
  const lastEntry = ZONES_HISTORY[ZONES_HISTORY.length - 1];
  let carriedForward = 0;
  lastEntry.zones.forEach(z=>{
    if(known.has(z.name)) return;
    const cfr = z.cases>0 ? +((z.deaths||0)/z.cases*100).toFixed(1) : 0;
    HEALTH_ZONES.push({
      name:z.name, province:z.province, cases:z.cases, deaths:z.deaths||0, cfr,
      newCases24h:0, newDeaths24h:0, deathsCommunity24h:0, deathsIntraCTE24h:0
    });
    known.add(z.name);
    carriedForward++;
  });
  if(carriedForward){
    console.info(`${carriedForward} zone(s) reportée(s) depuis l'historique dans le tableau détaillé (absentes du SitRep le plus récent).`);
  }
}

/* Filtre de province passe en query string (?province=Ituri), utilise par les
   liens venant des pages province et du menu de navigation. */
(function applyProvinceQuery(){
  const p = new URLSearchParams(location.search).get('province');
  if(!p || !document.getElementById('zonesTableBody')) return;
  zonesFilterProvinceVal = p;
  switchZonesView('zone');
})();

/* Defilement de l'apercu de chronologie.

   La piste defilait deja — 468 px de contenu hors cadre sur un ecran de
   1512 px —, mais rien ne le montrait : macOS pose des barres en
   superposition qui n'apparaissent qu'en cours de geste, et une souris a
   molette verticale n'a aucun axe horizontal. On voyait donc cinq cases
   figees sans moyen d'atteindre la sixieme.

   Les deux fleches sont activees ici, jamais dans le HTML : sans JavaScript
   elles restent masquees et la piste se parcourt au geste, comme avant. */
function initTimelineScroller(){
  const piste = document.getElementById('timelineTeaser');
  if(!piste) return;
  const boutons = [...document.querySelectorAll('.th-nav[data-th-nav]')];
  if(!boutons.length) return;

  // Un cran = presque une largeur de fenetre, en gardant une case en commun
  // pour ne pas perdre le fil entre deux clics.
  const pas = () => Math.max(160, piste.clientWidth - 232);

  function rafraichir(){
    const reste = piste.scrollWidth - piste.clientWidth;
    if(reste <= 1){                       // tout tient : pas de commandes
      boutons.forEach(b => { b.hidden = true; });
      return;
    }
    boutons.forEach(b => {
      b.hidden = false;
      const versLaDroite = Number(b.dataset.thNav) > 0;
      // Marge de 1 px : les navigateurs rendent des scrollLeft fractionnaires.
      b.disabled = versLaDroite ? piste.scrollLeft >= reste - 1
                                : piste.scrollLeft <= 1;
    });
  }

  boutons.forEach(b => b.addEventListener('click', () => {
    piste.scrollBy({ left: Number(b.dataset.thNav) * pas(), behavior: 'smooth' });
  }));
  piste.addEventListener('scroll', rafraichir, { passive: true });
  window.addEventListener('resize', rafraichir);
  rafraichir();
}

if(document.querySelector('.zonemap')) safeRun(initMap, 'initMap');
applyStaticI18n();
renderAll(); // premier rendu immediat avec les donnees de reference integrees
safeRun(initTimelineScroller, 'timelineScroller');
Promise.all([loadRemoteSitreps(), loadRemoteLatest(), loadZonesHistory(), loadCommunityDeathsDaily(), loadRemoteWhoReports(), loadSocialUpdates(), loadContactsFollowup(), loadProvinceHistory(), loadDemographie(), loadDecesLieu()]).then(()=>{
  safeRun(mergeHealthZonesWithHistory, 'mergeHealthZonesWithHistory');
  applyStaticI18n(); // la date "Dernière MAJ le ..." dans l'en-tête peut changer
  renderAll();        // puis on ré-affiche avec les données à jour si trouvées
  safeRun(setupTimeline, 'setupTimeline');
});
