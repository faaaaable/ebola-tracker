/* Outils communs de la carte en relief (scripts/carte_relief.py).
   Chaque page déclare une affiche de 1600 × 2000 px ; à l'écran elle est
   réduite à la fenêtre, `?export` la montre à taille réelle pour la capture. */
(function () {
  const C = window.CARTO;
  const NB = ' ';

  const fmt = n => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, NB);
  const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
    'août', 'septembre', 'octobre', 'novembre', 'décembre'];
  const dateFr = iso => {
    const [y, m, d] = iso.split('-').map(Number);
    return (d === 1 ? '1er' : d) + ' ' + MOIS[m - 1] + ' ' + y;
  };

  /* Plate-carrée corrigée de la latitude moyenne de la RDC (−4°). */
  const K = Math.cos(-4 * Math.PI / 180);
  function cadre(bbox, x, y, w, h) {
    const sx = w / ((bbox[2] - bbox[0]) * K), sy = h / (bbox[3] - bbox[1]);
    const s = Math.min(sx, sy);
    const ox = x + (w - (bbox[2] - bbox[0]) * K * s) / 2;
    const oy = y + (h - (bbox[3] - bbox[1]) * s) / 2;
    return {
      s, bbox,
      p: (lon, lat) => [ox + (lon - bbox[0]) * K * s, oy + (bbox[3] - lat) * s],
      km: km => km / 111.32 * s,
    };
  }

  function anneau(ctx, f, ring) {
    ring.forEach((pt, i) => {
      const [x, y] = f.p(pt[0], pt[1]);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    ctx.closePath();
  }
  function trait(ctx, f, line) {
    line.forEach((pt, i) => {
      const [x, y] = f.p(pt[0], pt[1]);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
  }
  function zone(ctx, f, z) { ctx.beginPath(); z.rings.forEach(r => anneau(ctx, f, r)); }
  function pays(ctx, f, a3) {
    const c = C.countries.find(c => c.a3 === a3);
    ctx.beginPath(); c.rings.forEach(r => anneau(ctx, f, r));
  }

  /* Altitude : R*256+G mètres, grille plate-carrée de C.dem. */
  function chargerRelief() {
    return new Promise(ok => {
      const img = new Image();
      img.onload = () => {
        const { w, h } = C.dem;
        const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
        const cx = cv.getContext('2d'); cx.drawImage(img, 0, 0);
        const d = cx.getImageData(0, 0, w, h).data;
        const z = new Float32Array(w * h);
        for (let i = 0; i < w * h; i++) z[i] = d[i * 4] * 256 + d[i * 4 + 1];
        ok(z);
      };
      img.src = 'data/dem.png';
    });
  }

  /* Ombrage : soleil au nord-ouest, rend une valeur 0..1 par cellule. */
  function ombrage(z, w, h, exag, azimut = 315, hauteur = 40) {
    const out = new Float32Array(w * h);
    const az = azimut * Math.PI / 180, alt = hauteur * Math.PI / 180;
    const cell = C.dem.step * 111320;
    const lx = Math.sin(az) * Math.cos(alt), ly = -Math.cos(az) * Math.cos(alt), lz = Math.sin(alt);
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const g = (a, b) => z[Math.min(h - 1, Math.max(0, b)) * w + Math.min(w - 1, Math.max(0, a))];
      const dx = (g(i + 1, j) - g(i - 1, j)) * exag / (2 * cell * K);
      const dy = (g(i, j + 1) - g(i, j - 1)) * exag / (2 * cell);
      const n = Math.hypot(dx, dy, 1);
      out[j * w + i] = Math.max(0, (-dx * lx + dy * ly + lz) / n);
    }
    return out;
  }

  /* Rastérise un dessin en coordonnées lon/lat sur la grille du relief. */
  function masque(dessin) {
    const { w, h, bbox, step } = C.dem;
    const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
    const ctx = cv.getContext('2d');
    const f = { p: (lon, lat) => [(lon - bbox[0]) / step, (bbox[3] - lat) / step], s: 1 / step };
    dessin(ctx, f);
    return ctx.getImageData(0, 0, w, h).data;
  }

  function affiche() {
    const el = document.querySelector('.affiche');
    const exp = new URLSearchParams(location.search).has('export');
    document.documentElement.classList.toggle('export', exp);
    const ajuste = () => {
      if (exp) return;
      const k = Math.min(1, (innerWidth - 32) / 1600, (innerHeight - 32) / 2000);
      el.style.transform = 'scale(' + k + ')';
      el.parentElement.style.height = (2000 * k + 32) + 'px';
    };
    addEventListener('resize', ajuste); ajuste();
    const cv = el.querySelector('canvas');
    cv.width = 1600 * 2; cv.height = 2000 * 2;
    const ctx = cv.getContext('2d'); ctx.scale(2, 2);
    return ctx;
  }

  /* Flou en boîte 3 × 3, `n` passes : adoucit les falaises du rift. */
  function lisse(z, w, h, n) {
    let a = z;
    for (let k = 0; k < n; k++) {
      const b = new Float32Array(w * h);
      for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
        let t = 0, c = 0;
        for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) {
          const x = i + di, y = j + dj;
          if (x >= 0 && y >= 0 && x < w && y < h) { t += a[y * w + x]; c++; }
        }
        b[j * w + i] = t / c;
      }
      a = b;
    }
    return a;
  }

  /* Vue inclinée d'un cadre lon/lat : le nord recule, `tilt` écrase la
     profondeur, `top` place le bord nord. Rend p(lon, lat, h) où h est une
     hauteur en pixels d'affiche. */
  function incline(bbox, x, w, top, tilt) {
    const f0 = cadre(bbox, x, 0, w, 99999);
    const yN = f0.p(0, bbox[3])[1];
    return {
      s: f0.s, bbox, tilt,
      p: (lon, lat, h = 0) => { const [px, py] = f0.p(lon, lat); return [px, top + (py - yN) * tilt - h]; },
      km: f0.km,
    };
  }

  /* Relief incliné rendu pixel par pixel dans le canevas (échelle 2).
     o : { f (incline), kz (px par mètre), Z, ZL, SH, teinte(e) -> [r,g,b],
     dehors (atténuation hors RDC), masqueRDC, couleur(c, u, v) facultatif }. */
  function rendreRelief(ctx, o) {
    const { w: GW, h: GH, step, bbox } = C.dem;
    const S = 2, W = 1600 * S, H = 2000 * S;
    const img = ctx.getImageData(0, 0, W, H), px = img.data;
    const bil = (A, u, v) => {
      const i = Math.floor(u), j = Math.floor(v), a = u - i, b = v - j;
      const i1 = Math.min(GW - 1, i + 1), j1 = Math.min(GH - 1, j + 1);
      return A[j * GW + i] * (1 - a) * (1 - b) + A[j * GW + i1] * a * (1 - b)
        + A[j1 * GW + i] * (1 - a) * b + A[j1 * GW + i1] * a * b;
    };
    const f = o.f, fb = f.bbox;
    const lon0 = fb[0], dlon = (fb[2] - fb[0]);
    const x0 = f.p(fb[0], fb[3])[0], x1 = f.p(fb[2], fb[3])[0];
    for (let X = Math.max(0, Math.round(x0 * S)); X < Math.min(W, x1 * S); X++) {
      const lon = lon0 + (X / S - x0) / (x1 - x0) * dlon;
      const u = (lon - bbox[0]) / step - .5;
      if (u < 0 || u > GW - 1.001) continue;
      let ymin = -1;
      const pas = Math.min(step, 1 / (f.s * f.tilt * S * 1.6));
      for (let lat = fb[1]; lat <= fb[3]; lat += pas) {
        const v = (bbox[3] - lat) / step - .5;
        if (v < 0 || v > GH - 1.001) continue;
        const e = bil(o.ZL, u, v);
        const Y = Math.round(f.p(lon, lat, e * o.kz)[1] * S);
        if (ymin < 0) ymin = Y + S;
        if (Y >= ymin) continue;
        const iu = Math.min(GW - 1, Math.round(u)), iv = Math.min(GH - 1, Math.round(v));
        const c = o.couleur(e, bil(o.SH, u, v), iv * GW + iu, lat);
        for (let y = Math.max(0, Y); y < Math.min(H, ymin); y++) {
          const i = (y * W + X) * 4; px[i] = c[0]; px[i + 1] = c[1]; px[i + 2] = c[2]; px[i + 3] = 255;
        }
        ymin = Math.max(0, Y);
      }
    }
    ctx.putImageData(img, 0, 0);
    return (lon, lat) => bil(o.ZL, (lon - bbox[0]) / step - .5, (bbox[3] - lat) / step - .5);
  }

  /* Zone extrudée en vue inclinée : flancs puis toit. */
  function prisme(ctx, f, z, h, toit, flancClair, flancSombre) {
    z.rings.forEach(ring => {
      for (let i = 0; i < ring.length - 1; i++) {
        const a = ring[i], b = ring[i + 1];
        const [ax, ay] = f.p(a[0], a[1]), [bx, by] = f.p(b[0], b[1]);
        if (bx === ax && by === ay) continue;
        ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.lineTo(bx, by - h); ctx.lineTo(ax, ay - h); ctx.closePath();
        ctx.fillStyle = (bx - ax) > 0 ? flancClair : flancSombre; ctx.fill();
      }
    });
    ctx.beginPath();
    z.rings.forEach(ring => ring.forEach((pt, i) => { const [x, y] = f.p(pt[0], pt[1], h); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }));
    ctx.closePath(); ctx.fillStyle = toit; ctx.fill();
  }

  /* Générateur pseudo-aléatoire stable (mulberry32). */
  function hasard(seed) {
    return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }
  function dedans(pt, z) {
    let ok = false;
    z.rings.forEach(r => {
      for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
        const [xi, yi] = r[i], [xj, yj] = r[j];
        if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) ok = !ok;
      }
    });
    return ok;
  }

  const kmEntre = (a, b) => {
    const r = Math.PI / 180, dl = (b[0] - a[0]) * r, p1 = a[1] * r, p2 = b[1] * r;
    return 6371 * Math.acos(Math.min(1, Math.sin(p1) * Math.sin(p2) + Math.cos(p1) * Math.cos(p2) * Math.cos(dl)));
  };

  function texte(ctx, x, y, lignes, align = 'left') {
    ctx.save();
    ctx.textAlign = align;
    if (THEME.ombre) { ctx.shadowColor = THEME.ombre; ctx.shadowBlur = 10; }
    let yy = y;
    lignes.forEach(([t, font, col, h, ls]) => {
      ctx.font = font; ctx.fillStyle = col; ctx.letterSpacing = ls || '0px'; ctx.fillText(t, x, yy); yy += h;
    });
    ctx.restore();
  }

  /* Étiquettes empilées en colonne, reliées à leur point par un filet.
     lab : [{ x, y, nom, val }] ; LX : bord de la colonne ; cote : -1 colonne
     à gauche des points (texte aligné à droite), 1 à droite. */
  function colonne(ctx, lab, LX, cote = -1, ecart = 64) {
    const T = THEME;
    lab = lab.slice().sort((a, b) => a.y - b.y);
    lab.forEach((l, i) => { l.ty = i ? Math.max(l.y, lab[i - 1].ty + ecart) : l.y; });
    lab.forEach(l => {
      ctx.strokeStyle = T.filet; ctx.lineWidth = 1;
      const bx = LX - cote * 40;
      ctx.beginPath(); ctx.moveTo(l.x + cote * 3, l.y); ctx.lineTo(bx, l.y); ctx.lineTo(LX - cote * 14, l.ty - 10); ctx.lineTo(LX - cote * 6, l.ty - 10); ctx.stroke();
      ctx.fillStyle = T.point; ctx.beginPath(); ctx.arc(l.x, l.y, 2.5, 0, 7); ctx.fill();
      const al = cote < 0 ? 'right' : 'left';
      if (l.val) texte(ctx, LX, l.ty - 32, [[l.nom.toUpperCase(), '600 15px "Public Sans"', T.nom, 32, '0.08em'],
        [l.val, '400 32px "Source Serif 4"', T.val, 0]], al);
      else texte(ctx, LX, l.ty - 4, [[l.nom, '500 19px "Public Sans"', T.val, 0]], al);
    });
  }

  /* Habillage : nuit (défaut) ou clair, façon site. */
  const THEMES = {
    nuit: { ombre: 'rgba(0,0,0,.95)', filet: 'rgba(213,236,248,.42)', point: '#F2F8FB', nom: '#B7D3E1', val: '#F2F8FB', ville: 'rgba(183,211,225,.8)' },
    clair: { ombre: null, filet: 'rgba(0,52,85,.4)', point: '#003455', nom: '#1B6C8C', val: '#1F1A13', ville: '#5A544C' },
  };
  let THEME = THEMES.nuit;
  function theme(nom) { THEME = THEMES[nom]; return THEME; }

  function fini() { document.documentElement.dataset.pret = '1'; }

  window.CARTE = { C, fmt, dateFr, cadre, anneau, trait, zone, pays, chargerRelief, ombrage, lisse, masque, affiche, fini, NB,
    incline, rendreRelief, prisme, hasard, dedans, kmEntre, texte, colonne, theme };
})();
