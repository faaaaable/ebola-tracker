# -*- coding: utf-8 -*-
"""« La riposte et ses defis » sur l'accueil (13 octobre 2026, maquettes
tmp/proto-accueil-face-1013 : option g3 sur le fond h5). Remplace le carrousel
de cinq cartes.

Pas de graphique ni de carrousel : deux camps de part et d'autre de la courbe
des cas confirmes cumules. La riposte en haut a gauche, au-dessus de la courbe ;
les defis en bas a droite, en dessous. Le nom de chaque camp en filigrane
geant, trois chiffres cles devant, quelques mots sous chacun. Un seul degrade
du bleu (haut) au sable (bas) : c'est la courbe qui partage.

La courbe se devoile de gauche a droite AU FIL DU DEFILEMENT (app.js,
initFaceCourbe) : la riposte apparait au debut du trace, les defis vers la
fin, chaque fois le mot d'abord puis ses chiffres en long fondu (site.css) ;
le point rouge quand la courbe touche le dernier bulletin. Sans script, ou
si le systeme demande moins d'animations, tout est affiche d'emblee.

La courbe est un SEPARATEUR, pas un graphique : dessinee dans un repere
0-1000 et etiree a la taille du bloc (preserveAspectRatio="none", trait non
deforme). Sa forme est juste, son echelle ne l'est pas — c'est assume, ni axe
ni chiffre ne l'accompagnent. Le point rouge du dernier bulletin est un
element HTML : un cercle dans un SVG etire deviendrait une ellipse.

Les centres de traitement : le calcul du site (tous les patients / lits
declares, regle du 20 septembre), pour la province la plus chargee — les
bulletins ne donnent pas les lits centre par centre. Affiche en « patients pour
100 lits », sans « % » (regle du 12 octobre 2026) : le pourcentage reste
reserve au taux d'occupation imprime par le bulletin, sinon deux chiffres
differents se presenteraient pareil (Nord-Kivu au SitRep 149 : 134 patients
pour 100 lits ici, 94,9 % dans le bulletin). « 134 % saturation » essaye et
ecarte le 13 octobre 2026."""
import datetime as dt
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = dt.date.fromisoformat
esc = lambda s: html.escape(str(s), quote=True)
PROV_NOM = {"en": {"Nord-Kivu": "North Kivu", "Sud-Kivu": "South Kivu"},
            "sw": {"Nord-Kivu": "Kivu Kaskazini", "Sud-Kivu": "Kivu Kusini"}}
# ou s'arrete la courbe dans le repere 0-1000 : elle part en bas a gauche et
# finit en haut a droite ; sans fond, elle part du bord de la colonne
# (13 octobre 2026), le point garde un peu de marge a droite
X0, X1, Y_DEB, Y_FIN = 0, 975, 920, 180


def _j(chemin):
    with open(os.path.join(ROOT, chemin), encoding="utf-8") as fh:
        return json.load(fh)


def _nb(n, lang):
    s = "{:,}".format(int(round(n)))
    return s.replace(",", " ") if lang == "fr" else s


def chiffres():
    """Les six chiffres, au dernier bulletin."""
    latest = _j("data/latest.json")["national"]
    cf = _j("data/contacts-followup.json")[-1]["contacts"]
    cte = _j("data/cte.json")["parDate"][-1]
    sitreps = [x for x in _j("data/sitreps.json") if x.get("confirmed") is not None]
    # la province ou les centres sont le plus charges
    charges = [(100 * p["hospitalises"] / p["lits"], nom) for nom, p in cte["provinces"].items()
               if p.get("lits") and p.get("hospitalises") is not None]
    p100, prov = max(charges) if charges else (None, None)
    # Les bulletins ne comptent pas les attaques, ils les decrivent : on compte
    # les bulletins dont la section « Defis » en signale (obstacle « attaques »
    # du codage a la main, data/defis-codage.json).
    import defis_synthese
    ent = defis_synthese.entrees()
    att = len({e[1] for e in ent if any("attaques" in a["obstacles"] for a in e[3])})
    return {
        "vus": cf["vus"], "nonVus": cf["aSuivre"] - cf["vus"], "taux": latest.get("contactsFollowUpRate"),
        "p100": p100, "prov": prov, "attaques": att, "bulletins": len({e[1] for e in ent}),
        "serie": [(D(x["date"]), x["confirmed"]) for x in sitreps],
    }


def section_html(lang, t, vaccines, url_riposte, url_defis):
    """Le bloc des deux camps et de la courbe. `t` : chaines de la langue ;
    `vaccines` : le total deja calcule et formate pour la page Riposte
    (vaccination_seed de build_pages), pour que les deux pages disent le meme.
    Les grands mots Riposte et Defis sont les liens vers leurs pages (plus de
    liens sous le bloc depuis le 13 octobre 2026)."""
    c = chiffres(); nb = lambda n: _nb(n, lang)
    pc = lambda v: "%d%s" % (round(v), "\u202f%" if lang == "fr" else "%")
    prov = PROV_NOM.get(lang, {}).get(c["prov"], c["prov"])
    r = [(nb(c["vus"]), t["faKVus"]), (pc(c["taux"]) if c["taux"] is not None else "—", t["faKTaux"]), (vaccines or "—", t["faKVacc"])]
    d = [(nb(c["nonVus"]), t["faKNonVus"]),
         (nb(c["p100"]) if c["p100"] is not None else "—", t["faKP100"].replace("{p}", prov or "")),
         (nb(c["attaques"]), t["faKAtt"].replace("{t}", nb(c["bulletins"])))]
    # un retour a la ligne dans la chaine (« \n ») est un saut de ligne voulu
    li = lambda xs: "".join("<li><b>%s</b><span>%s</span></li>" % (esc(n), esc(m).replace("\n", "<br>")) for n, m in xs)

    serie = c["serie"]; d0, d1 = serie[0][0], serie[-1][0]; vmax = serie[-1][1]
    pts = [(X0 + (X1 - X0) * (dd - d0).days / (d1 - d0).days, Y_DEB - (Y_DEB - Y_FIN) * v / vmax) for dd, v in serie]
    trace = " ".join("%.1f,%.1f" % p for p in pts)
    xe, ye = pts[-1][0] / 10, pts[-1][1] / 10
    mini = " ".join("%.1f,%.1f" % (12 + x * 0.57, y * 0.2) for x, y in pts)
    return (
        '<div class="fa" id="faceRiposte">'
        '<svg class="fa-courbe" viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
        '<polyline points="{trace}" fill="none" stroke="#00324B" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>'
        '<span class="fa-pt" style="left:{xe:.1f}%;top:{ye:.1f}%" aria-hidden="true"></span>'
        '<div class="fa-r"><h3><a href="{ur}" title="{tr}">{mr}</a></h3><ul>{r}</ul></div>'
        '<div class="fa-mob" aria-hidden="true"><svg viewBox="0 0 600 200" focusable="false"><polyline points="{mini}" fill="none" stroke="#00324B" stroke-width="3.5" stroke-linejoin="round"/>'
        '<circle class="fa-mpt" cx="{mx:.1f}" cy="{my:.1f}" r="7" fill="#993A2E"/></svg></div>'
        '<div class="fa-d"><h3><a href="{ud}" title="{td}">{md}</a></h3><ul>{d}</ul></div>'
        '</div>'
    ).format(trace=trace, xe=xe, ye=ye, mr=esc(t["faMotRiposte"]), r=li(r), mini=mini,
             mx=12 + pts[-1][0] * .57, my=pts[-1][1] * .2, md=esc(t["faMotDefis"]), d=li(d),
             ur=esc(url_riposte), ud=esc(url_defis), tr=esc(t["crLinkRiposte"]), td=esc(t["crLinkDefis"]))
