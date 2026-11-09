# -*- coding: utf-8 -*-
"""« La Lettre » sur l'accueil (3 novembre 2026), entre « La
riposte et ses defis » et « L'epidemie en images ».

A gauche, la derniere lettre posee sur la pile des deux precedentes, dessinee
comme la vraie (bandeau bleu, manchette LA LETTRE, ligne d'edition et son
losange, sous-titre italique, « Le bilan du jour », titre, chapeau, cas et
deces, barres des 30 jours) ; tout l'encart mene a la lettre. A droite,
l'invitation a la recevoir : le VRAI formulaire Brevo de la langue (celui du
bas de chaque lettre, poste par app.js, form[data-brevo]), puis les trois
lettres precedentes. Pas de titre de section visible (h2 pour les lecteurs
d'ecran seulement).

Tout est lu dans le balisage des lettres deja rendues (seed.lettres de
bulletin.render) : la section dit exactement ce que dit la lettre, sans
second calcul. Sur telephone, le chapeau garde ses deux premieres phrases
(les autres en .ph-long, masquees sous 760 px)."""
import html
import re

MOIS_ABR = ("janv.", "févr.", "mars.", "avr.", "juil.", "sept.", "oct.", "nov.", "déc.",
            "Jan.", "Feb.", "Aug.", "Sept.", "Oct.", "Nov.", "Dec.")


def _txt(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def _lettre(n, x):
    L = {"n": n}
    L["titre"] = _txt(re.search(r'<h1 class="lq-titre">(.*?)</h1>', x, re.S).group(1))
    L["chapo"] = _txt(re.search(r'<p class="lq-chapo">(.*?)</p>', x, re.S).group(1))
    ed = re.search(r'<p class="ag-edition"><span>(.*?)</span><i></i><span>(.*?)</span></p>', x, re.S)
    L["edition"], L["situation"] = _txt(ed.group(1)), _txt(ed.group(2))
    L["sous"] = _txt(re.search(r'<p class="ag-sous">(.*?)</p>', x, re.S).group(1))
    L["chiffres_html"] = re.findall(r'<div class="lq-chiffre (?:is-cas|is-deces)">.*?</div>', x)
    b = re.search(r'<svg class="lq-barres".*?</svg>', x, re.S)
    L["barres"] = b.group(0).replace('class="lq-barres"', 'class="lq-barres o3b-b"', 1) if b else ""
    f = re.search(r'<form class="lq-abo".*?</form>', x, re.S)
    L["form"] = f.group(0) if f else ""
    return L


def _phrases(s):
    """Les phrases d'un texte, sans couper apres une date abregee."""
    out = []
    for morceau in re.split(r"(?<=[.!?])\s+", s.strip()):
        if out and out[-1].endswith(MOIS_ABR):
            out[-1] += " " + morceau
        else:
            out.append(morceau)
    return out


def section_html(lang, S, lettres, url_lettre, esc):
    """lettres : {numero: balisage de la lettre rendue} ; url_lettre(num) -> chemin."""
    if not lettres:
        return ""
    nums = sorted(lettres, key=lambda k: int(k) if str(k).isdigit() else -1)
    der = _lettre(nums[-1], lettres[nums[-1]])
    prec = [_lettre(n, lettres[n]) for n in nums[-4:-1]][::-1]
    url = url_lettre(der["n"])
    chapo = " ".join('<span class="%s">%s</span>' % ("ph" if i < 2 else "ph ph-long", esc(p))
                     for i, p in enumerate(_phrases(der["chapo"])))
    feuilles = "".join('<span class="o3-f f%d" aria-hidden="true"><span class="o3-fn">%s</span></span>'
                       % (i, esc(p["edition"])) for i, p in enumerate(prec[:2], 1))
    avant = S["lettreSituationAu"].split("{date}")[0]
    precs = "".join('<a href="%s"><span>%s · %s</span><b>%s</b></a>'
                    % (url_lettre(p["n"]), esc(p["edition"]), esc(p["situation"][len(avant):] if p["situation"].startswith(avant) else p["situation"]),
                       esc(p["titre"])) for p in prec)
    form = der["form"]
    if form:
        form = re.sub(r'<div class="lq-abo-t">.*?</div>', "", form, count=1, flags=re.S)
        form = form.replace('class="lq-abo" id="abonnement"', 'class="o3-form" id="abonnement-accueil"', 1)
    puces = "".join("<li>%s</li>" % esc(S[k]) for k in ("accLettrePuce1", "accLettrePuce2", "accLettrePuce3"))
    return """<section class="section home-sec o3 o3b" id="lettre">
    <h2 class="visually-hidden">%(h2)s</h2>
    <div class="o3-grille">
      <div class="o3-pile">
        %(feuilles)s
        <a class="o3-papier o3b-papier" href="%(url)s">
          <span class="o3b-barre" aria-hidden="true"></span>
          <span class="o3b-manch">
            <span class="o3b-marque">%(marque)s</span>
            <span class="o3b-edition"><span>%(edition)s</span><i></i><span>%(situation)s</span></span>
            <span class="o3b-sous">%(sous)s</span>
          </span>
          <span class="o3b-corps">
            <span class="o3b-princ">
              <span class="lq-eyebrow">%(eyebrow)s</span>
              <span class="o3b-titre">%(titre)s</span>
              <span class="o3b-chapo">%(chapo)s</span>
            </span>
            <span class="o3b-enc">%(chiffres)s
              <span class="o3b-mini">%(barres)s<span>%(courbe)s</span></span>
            </span>
          </span>
          <span class="o3b-lire">%(lire)s</span>
        </a>
      </div>
      <div class="o3-cote">
        <p class="o3-acc">%(accroche)s</p>
        <ul class="o3-puces">%(puces)s</ul>
        %(form)s
        <div class="o3-prec"><div class="o3-sur">%(precedentes)s</div>%(precs)s</div>
      </div>
    </div>
  </section>""" % dict(
        h2=esc(S["lettreEyebrow"]), feuilles=feuilles, url=url, marque=esc(S["lettreEyebrow"]),
        edition=esc(der["edition"]), situation=esc(der["situation"]), sous=esc(der["sous"]),
        eyebrow=esc(S["lettreUneEyebrow"]), titre=esc(der["titre"]), chapo=chapo,
        chiffres="".join(der["chiffres_html"]), barres=der["barres"], courbe=esc(S["lettreUneCourbe"]),
        lire=esc(S["accLettreLire"].replace("{n}", str(der["n"]))), accroche=esc(S["accLettreAccroche"]),
        puces=puces, form=form, precedentes=esc(S["accLettrePrecedentes"]), precs=precs)
