# -*- coding: utf-8 -*-
"""Prototype local de la page « Riposte ».

Ne touche a aucune source du site : ecrit une page autonome dans tmp/riposte/,
qui emprunte la feuille de style du site pour donner une idee juste du rendu.
Rien n'est publie tant que la page n'est pas jugee.

Le prototype est bati sur le QUALITATIF, seule matiere dont la couverture est
demontree : 761 difficultes sur 74 des 91 rapports, continues a partir du
1er juin. Les etages chiffres que la page appelle — l'entonnoir des alertes,
la positivite du laboratoire — sont declares NON COUVERTS plutot qu'estimes :

  - laboratoire : 8 rapports sur 91 s'extraient avec les motifs actuels, les
    redactions changeant a chaque epoque ;
  - alertes : l'entonnoir n'existe qu'en epoque D et echoue au controle
    « recues = validees + invalidees » sur 13 dates sur 15.

Afficher ces series maintenant reviendrait a publier des chiffres
indefendables. La page dit donc ce qui manque, ce qui est plus utile qu'un
graphique faux.

    python scripts/prototype_riposte.py
    puis http://127.0.0.1:8765/tmp/riposte/
"""
import io
import json
import os
import re
import unicodedata
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tmp", "riposte")

MOIS = {"06": "juin", "07": "juillet", "08": "août", "05": "mai"}


def sa(t):
    return "".join(c for c in unicodedata.normalize("NFD", t or "")
                   if unicodedata.category(c) != "Mn").lower()


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def lire(chemin):
    with io.open(os.path.join(ROOT, chemin), encoding="utf-8") as fh:
        return json.load(fh)


def lignes(chemin):
    with io.open(os.path.join(ROOT, chemin), encoding="utf-8") as fh:
        return [json.loads(l) for l in fh]


qualitatif = lignes("data/corpus/qualitatif.jsonl")
carte = {f["id"]: f for f in lire("data/corpus/carte.json")}
insp = [f for f in carte.values() if f["source"] == "INSP"]

# Les themes ne sont pas un codage ferme : ce sont des comptages de mots-cles,
# donnes pour montrer ce qu'il y a dans la matiere. Le vrai classement demande
# un regard metier.
THEMES = [
    ("Ruptures de stock et intrants", "stock",
     ["rupture", "penurie", "insuffisance d", "intrant", "approvisionnement",
      "pre-rupture", "meg"]),
    ("Refus, rumeurs, résistance", "refus",
     ["refus", "resistance", "reticence", "rumeur", "mefiance", "reticent"]),
    ("Insécurité et attaques", "securite",
     ["insecurite", "attaque", "incident securitaire", "braquage", "enlevement",
      "ravi", "milic"]),
    ("Saturation des CTE", "cte",
     ["saturation", "capacite d accueil", "occupation", "plateau technique",
      "lits insuffisant", "capacite des cte"]),
    ("Non-paiement et grèves", "greve",
     ["non-paiement", "greve", "impaye", "prime", "salaire", "remuneration",
      "non payes"]),
    ("Points d'entrée et de contrôle", "poe",
     ["poe", "poc", "point d entree", "point de controle"]),
    ("Zones qui ne rapportent pas", "rapportage",
     ["completude", "n ont pas rapporte", "non rapport", "faible rapportage"]),
]


def theme_de(texte):
    t = sa(texte)
    for nom, cle, motifs in THEMES:
        if any(m in t for m in motifs):
            return nom, cle
    return None, None


groupes = defaultdict(list)
for e in qualitatif:
    nom, cle = theme_de(e["difficulte"] + " " + (e["impact"] or ""))
    if nom:
        groupes[nom].append(e)


def mois_couverts(items):
    return sorted({e["date"][:7] for e in items if e["date"]})


def barre(valeur, maxi, couleur):
    return ('<span class="pt-track"><span class="pt-fill" '
            'style="width:%.1f%%;background:%s"></span></span>'
            % (100.0 * valeur / maxi, couleur))


def verbatims(items, combien=2):
    """Les difficultes les plus completes : celles qui portent leur impact ET
    l'action annoncee. C'est l'appariement qui fait la valeur — un obstacle
    seul se lit comme un reproche, un obstacle avec sa reponse decrit un
    systeme qui bute et qui repond."""
    complets = [e for e in items if e["impact"] and e["action"]
                and len(e["difficulte"]) > 60]
    complets.sort(key=lambda e: (e["date"] or "", -len(e["difficulte"])),
                  reverse=True)
    vus, sortie = set(), []
    for e in complets:
        cle = sa(e["difficulte"])[:45]
        if cle in vus:
            continue
        vus.add(cle)
        sortie.append(e)
        if len(sortie) >= combien:
            break
    return sortie


def jour(iso):
    if not iso:
        return ""
    a, m, j = iso.split("-")
    return "%d %s %s" % (int(j), MOIS.get(m, m), a)


maxi = max(len(v) for v in groupes.values())
blocs = []
for nom, cle, _ in THEMES:
    items = groupes.get(nom, [])
    if not items:
        continue
    rapports = len({e["rapport"] for e in items})
    ms = mois_couverts(items)
    tardif = ms and ms[0] >= "2026-07"
    lignes_v = []
    for e in verbatims(items):
        prov = " · ".join(e["provinces"]) if e["provinces"] else ""
        lignes_v.append(
            '        <blockquote class="vb">\n'
            '          <p class="vb-difficulte">%s</p>\n'
            '          <p class="vb-suite"><span class="vb-et">Impact</span> %s</p>\n'
            '          <p class="vb-suite"><span class="vb-et">Action annoncée</span> %s</p>\n'
            '          <p class="vb-src">SitRep n°%s · %s · page %s%s</p>\n'
            '        </blockquote>'
            % (esc(e["difficulte"]), esc(e["impact"]), esc(e["action"]),
               esc(e["rapport"].split("_")[1]), esc(jour(e["date"])),
               esc(e["page"]), (" · " + esc(prov)) if prov else ""))
    blocs.append(
        '      <section class="pt-theme" id="%s">\n'
        '        <div class="pt-head">\n'
        '          <h3>%s</h3>\n'
        '          <div class="pt-chiffres"><strong>%d</strong> mentions '
        'sur <strong>%d</strong> rapports</div>\n'
        '        </div>\n'
        '        %s\n'
        '        <p class="pt-mois">Présent en : %s%s</p>\n'
        '%s\n'
        '      </section>'
        % (cle, esc(nom), len(items), rapports,
           barre(len(items), maxi, "var(--accent-strong)"),
           " · ".join(MOIS.get(m[5:], m) for m in ms),
           (' <span class="pt-alerte">apparaît seulement en juillet</span>'
            if tardif else ""),
           "\n".join(lignes_v)))

total = sum(len(v) for v in groupes.values())
rapports_couverts = len({e["rapport"] for e in qualitatif})
dates = sorted(e["date"] for e in qualitatif if e["date"])

HTML = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prototype — Riposte</title>
<link rel="stylesheet" href="/assets/css/site.css">
<style>
  body{padding:0;}
  .pt-wrap{max-width:940px;margin:0 auto;padding:48px 28px 100px;}
  .pt-eyebrow{font-size:12px;font-weight:700;letter-spacing:.14em;
    text-transform:uppercase;color:var(--accent-strong);margin:0 0 14px;}
  .pt-wrap h1{font-family:var(--font-serif);font-size:38px;font-weight:600;
    line-height:1.1;margin:0 0 14px;letter-spacing:-.02em;}
  .pt-lede{font-family:var(--font-serif);font-size:19px;line-height:1.55;
    color:var(--ink-dim);margin:0 0 34px;max-width:62ch;}
  .pt-bandeau{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
    grid-template-columns:repeat(auto-fit,minmax(150px,1fr));border-radius:4px;
    overflow:hidden;margin-bottom:42px;}
  .pt-bandeau div{background:var(--bg-panel);padding:16px 18px;}
  .pt-bandeau .v{font-size:27px;font-weight:700;color:var(--accent-strong);
    line-height:1;font-variant-numeric:tabular-nums;}
  .pt-bandeau .k{font-size:12.5px;color:var(--ink-faint);margin-top:7px;line-height:1.35;}
  .pt-theme{padding:24px 0 8px;border-top:1px solid var(--line);}
  .pt-head{display:flex;justify-content:space-between;align-items:baseline;
    gap:16px;flex-wrap:wrap;margin-bottom:10px;}
  .pt-theme h3{font-family:var(--font-serif);font-size:21px;font-weight:600;margin:0;}
  .pt-chiffres{font-size:13px;color:var(--ink-faint);white-space:nowrap;}
  .pt-chiffres strong{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums;}
  .pt-track{display:block;height:8px;background:var(--bg-alt);border-radius:4px;
    overflow:hidden;border:1px solid var(--line-soft);}
  .pt-fill{display:block;height:100%;border-radius:3px;}
  .pt-mois{font-size:12.5px;color:var(--ink-faint);margin:10px 0 18px;}
  .pt-alerte{color:var(--accent-critical);font-weight:600;}
  .vb{margin:0 0 14px;padding:15px 18px;background:var(--bg-panel);
    border:1px solid var(--line);border-left:3px solid var(--accent);
    border-radius:0 var(--radius) var(--radius) 0;}
  .vb-difficulte{margin:0 0 9px;font-size:14.5px;line-height:1.6;color:var(--ink);}
  .vb-suite{margin:0 0 5px;font-size:13.5px;line-height:1.55;color:var(--ink-dim);}
  .vb-et{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.08em;
    text-transform:uppercase;color:var(--ink-faint);margin-right:7px;}
  .vb-src{margin:9px 0 0;font-size:12px;color:var(--ink-faint);
    font-variant-numeric:tabular-nums;}
  .pt-manque{margin-top:44px;padding:22px 24px;background:var(--wash-critical);
    border:1px solid var(--line);border-radius:var(--radius-card);}
  .pt-manque h2{font-family:var(--font-serif);font-size:22px;margin:0 0 10px;}
  .pt-manque p{font-size:14px;line-height:1.65;color:var(--ink-dim);margin:0 0 10px;max-width:66ch;}
  .pt-manque li{font-size:14px;line-height:1.6;color:var(--ink-dim);margin-bottom:7px;}
</style>
</head>
<body>
<div class="pt-wrap">
  <p class="pt-eyebrow">Prototype local — non publié</p>
  <h1>La riposte, et là où elle bute</h1>
  <p class="pt-lede">Les bulletins ne décrivent pas seulement l'épidémie : ils disent chaque
  jour ce que la riposte parvient à faire et ce qui l'en empêche. Cette page rassemble ces
  obstacles, tels qu'ils sont écrits, datés et rattachés à leur bulletin.</p>

  <div class="pt-bandeau">
    <div><div class="v">{{total}}</div><div class="k">difficultés relevées</div></div>
    <div><div class="v">{{rapports}}<span style="font-size:16px;color:var(--ink-faint)">/91</span></div><div class="k">rapports en portent</div></div>
    <div><div class="v">{{themes}}</div><div class="k">obstacles récurrents</div></div>
    <div><div class="v">{{debut}}</div><div class="k">première mention retenue</div></div>
  </div>

{{blocs}}

  <div class="pt-manque">
    <h2>Ce que cette page ne montre pas encore</h2>
    <p>Elle devrait porter, à côté de chaque obstacle, l'indicateur chiffré correspondant :
    l'entonnoir des alertes pour la détection, le taux de positivité pour le dépistage. Ces
    deux séries <strong>ne s'extraient pas encore de façon fiable</strong>, et les afficher
    reviendrait à publier des chiffres indéfendables.</p>
    <ul>
      <li><strong>Laboratoire</strong> — 8 rapports sur 91 s'extraient avec les motifs
      actuels. La rédaction change à chaque époque : récit en mai, phrase type en juin,
      tableau en juillet, ventilation par province en août. Les relevés obtenus sont en
      revanche tous cohérents avec le taux imprimé.</li>
      <li><strong>Entonnoir des alertes</strong> — présent uniquement en époque D, et le
      contrôle « reçues = validées + invalidées » échoue sur 13 dates sur 15. Le tableau
      comporte des sous-colonnes vivants / décédés que l'aplatissement mélange.</li>
    </ul>
    <p>Une lacune déclarée vaut mieux qu'un graphique faux — c'est le principe qui a guidé
    tout le recensement.</p>
  </div>

  <div class="info-note" style="margin-top:34px;">
    Relevé sur les sections « Défis » des bulletins de l'INSP, du {{debut_long}} au {{fin_long}}.
    La couverture est quasi intégrale à partir du 1<sup>er</sup> juin (74 rapports sur 75) ;
    les bulletins de mai, d'un format antérieur, n'ont pas de section « Défis » — un seul en
    porte. Les regroupements par thème sont de simples comptages de mots-clés, donnés pour
    montrer la matière, non pour tenir lieu d'analyse. Trois thèmes n'apparaissent qu'à partir
    de juillet : impossible de dire si le problème est né alors ou si les bulletins ont
    commencé à en parler, le format des rapports ayant changé dans la même fenêtre.
  </div>
</div>
</body>
</html>
"""

if not os.path.isdir(OUT):
    os.makedirs(OUT)
# Substitution par marqueurs et non par %, le gabarit contenant du CSS
# truffe de pourcentages qu'il faudrait sinon tous echapper.
valeurs = {
    "total": total,
    "rapports": rapports_couverts,
    "themes": len([n for n, _c, _m in THEMES if groupes.get(n)]),
    "debut": jour(dates[0])[:-5] if dates else "—",
    "debut_long": jour(dates[0]),
    "fin_long": jour(dates[-1]),
    "blocs": "\n".join(blocs),
}
page = HTML
for cle, valeur in valeurs.items():
    page = page.replace("{{%s}}" % cle, str(valeur))
io.open(os.path.join(OUT, "index.html"), "w",
        encoding="utf-8", newline="\n").write(page)

print("%d difficultes classees sur %d relevees" % (total, len(qualitatif)))
for nom, _c, _m in THEMES:
    if groupes.get(nom):
        print("   %-32s %4d mentions  %2d rapports"
              % (nom, len(groupes[nom]), len({e["rapport"] for e in groupes[nom]})))
print("\nprototype : tmp/riposte/index.html")
