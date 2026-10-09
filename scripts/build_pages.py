#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère le site statique multi-pages à partir de site/.

Le site était une page unique à onglets : une seule URL, un seul titre, une
seule description pour tout le contenu. Ce script assemble désormais, pour
chaque langue :

    site/layout.html  +  site/pages/<fragment>  ->  <slug>/index.html

Chaque page obtient sa propre URL, son titre, sa description, ses données
structurées et son fil d'Ariane. Les pages province sont générées à partir de
data/latest.json : une par province touchée.

Sources de texte :
  - assets/js/i18n.js   libellés déjà utilisés par le JavaScript (source unique,
                        lus via scripts/dump_i18n.mjs)
  - site/strings.json   textes des pages qui n'existaient pas dans la monopage
  - site/pages.json     structure du site, URL et métadonnées de chaque page

Usage :  python scripts/build_pages.py   (depuis la racine du dépôt)
"""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import defis_synthese  # maquette « Riposte & defis », seconde partie redigee
import base_donnees  # la base de donnees unifiee (9 octobre 2026)
import hors_rdc  # vue « Pays touches » de la carte de l'accueil (8 octobre 2026), en local
import bulletin  # maquette « Le bulletin » (8 septembre 2026), en local

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
MANIFEST = os.path.join(SITE, ".generated.json")

# Espace fine insécable : c'est le séparateur de milliers que produit
# Number.toLocaleString('fr-FR') côté navigateur. L'utiliser ici évite que les
# chiffres écrits en dur sautent visuellement quand le JavaScript les réécrit.
NNBSP = " "


# --------------------------------------------------------------------------
# Lecture des sources
# --------------------------------------------------------------------------

def read(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def read_json(path):
    return json.loads(read(path))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def load_i18n():
    """Extrait le dictionnaire de traduction via Node."""
    try:
        out = subprocess.run(
            ["node", "scripts/dump_i18n.mjs"],
            cwd=ROOT, capture_output=True, check=True,
        )
    except FileNotFoundError:
        sys.exit("Node est introuvable. Il sert à lire assets/js/i18n.js, "
                 "qui reste la source unique des libellés.")
    except subprocess.CalledProcessError as err:
        sys.exit("Échec de scripts/dump_i18n.mjs :\n"
                 + err.stderr.decode("utf-8", "replace"))
    return json.loads(out.stdout.decode("utf-8"))


# --------------------------------------------------------------------------
# Formatage — reproduit ce que fait le JavaScript, pour que le texte écrit en
# dur soit identique à celui que le navigateur affichera après le rendu.
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Conventions par langue
#
# Le generateur raisonnait en « si francais, sinon anglais » a dix-huit
# endroits : separateurs de nombres, prefixe d'URL, locale Open Graph, forme
# des ordinaux, et jusqu'a des libelles ecrits en dur. Une troisieme langue
# heritait donc silencieusement de l'anglais — pire, elle se serait publiee
# SOUS « /en/ », en collision avec lui. Tout passe desormais par cette table :
# ajouter une langue, c'est ajouter une entree ici, un bloc dans
# site/strings.json, un dans assets/js/i18n.js, et les slugs dans pages.json.
# --------------------------------------------------------------------------

SITE_LANGUAGES = []   # rempli par main() depuis site/pages.json

LOCALES = {
    "fr": {
        "thousands": NNBSP,          # espace fine insecable
        "decimal": ",",
        "percent": NNBSP + "%",      # « 48,0 % », insecable pour ne pas casser
        "urlPrefix": "",             # le francais est servi a la racine
        "ogLocale": "fr_FR",
        "htmlLang": "fr",
        "label": "Français",
    },
    "en": {
        "thousands": ",",
        "decimal": ".",
        "percent": "%",              # « 48.0% », colle au chiffre
        "urlPrefix": "/en",
        "ogLocale": "en_US",
        "htmlLang": "en",
        "label": "English",
    },
    "sw": {
        # Le swahili suit l'usage anglophone pour les nombres — c'est ce que
        # rend toLocaleString('sw'), et le JavaScript doit ecrire la meme
        # chaine que le generateur.
        "thousands": ",",
        "decimal": ".",
        "percent": "%",
        "urlPrefix": "/sw",
        "ogLocale": "sw_CD",         # swahili de RDC
        "htmlLang": "sw",
        "label": "Kiswahili",
    },
}


def loc(lang, key):
    """Une convention de langue, avec repli sur l'anglais si elle manque."""
    return LOCALES.get(lang, LOCALES["en"])[key]


def fmt(value, lang):
    """Équivalent de fmt() dans app.js (Number.toLocaleString)."""
    if value is None:
        return "—"
    return "{:,}".format(int(value)).replace(",", loc(lang, "thousands"))


def legend_steps_html(thresholds, lang):
    """La legende de la carte : une pastille par palier, bornee en chiffres.

    Les bornes se deduisent des seuils, jamais ecrites a la main : la classe
    « is-N » d'une zone et la ligne N de la legende sortent de la meme liste,
    elles ne peuvent pas diverger. Les libelles sont des nombres, donc les
    memes dans les trois langues, au separateur de milliers pres."""
    bornes = [1] + list(thresholds)
    lignes = []
    for i in range(len(thresholds)):
        debut, fin = bornes[i], bornes[i + 1] - 1
        libelle = fmt(debut, lang) if debut == fin else "%s\u2013%s" % (fmt(debut, lang), fmt(fin, lang))
        lignes.append((i + 1, libelle))
    lignes.append((len(thresholds) + 1, fmt(thresholds[-1], lang) + "+"))
    return "\n".join(
        ['            <div class="legend-steps">'] +
        ['              <div class="legend-step"><span class="legend-swatch" '
         'style="background:var(--map-%d)"></span><span>%s</span></div>' % (n, lib)
         for n, lib in lignes] +
        ['            </div>'])


def fmt_cfr(value, lang):
    """Un taux en pourcentage, dans la typographie de la langue.

    Le francais prend la virgule decimale et une espace avant le signe —
    « 48,0 % » —, l'anglais garde « 48.0% ». Le JavaScript reecrit les memes
    elements et doit produire exactement la meme chaine : voir fmtCfr() dans
    app.js. Les deux fonctions se corrigent ensemble, sinon un taux change
    d'ecriture au chargement de la page.

    L'espace est **fine insecable** (U+202F), la meme que celle qui separe les
    milliers. Avec une espace ordinaire, « 83,4 % » se coupait en deux dans une
    colonne etroite : sur telephone, le « % » passait a la ligne sous le
    nombre, dans la part du pays comme dans la letalite.
    """
    if value is None:
        return "—"
    text = "{:.1f}".format(float(value)).replace(".", loc(lang, "decimal"))
    return text + loc(lang, "percent")


def fmt_decimal(value, lang):
    """Nombre a une decimale, pour le texte redige : virgule en francais.

    Meme regle que fmt_cfr() pour la decimale ; fmt_cfr() y ajoute le signe
    pourcent et l'espace qui le precede en francais.
    """
    if value is None:
        return "—"
    return ("%.1f" % float(value)).replace(".", loc(lang, "decimal"))


def short_date(iso, i18n_lang):
    """Équivalent de frDate() : jour + mois abrégé, sans l'année."""
    if not iso:
        return i18n_lang.get("reportsUnknownDate", "—")
    year, month, day = iso.split("-")
    return "%d %s" % (int(day), i18n_lang["months"][int(month) - 1])


def long_date(iso, i18n_lang):
    """Jour + mois abrégé + année, pour les phrases rédigées."""
    if not iso:
        return i18n_lang.get("reportsUnknownDate", "—")
    return "%s %s" % (short_date(iso, i18n_lang), iso[:4])


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


PLURAL_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\?([^{}]*)\}")


def is_one(value):
    """La valeur vaut-elle exactement un ? Elle arrive déjà mise en forme —
    « 1 984 », « 4,447 » — donc on ne garde que les chiffres."""
    digits = "".join(c for c in str(value) if c.isdigit())
    return digits == "1"


def interp(template, values):
    """Remplace les {variables} d'une chaîne de site/strings.json.

    Volontairement plus simple que str.format : les accolades inconnues sont
    laissées telles quelles plutôt que de faire échouer la génération.

    Accepte en plus {clé?suffixe} : le suffixe n'apparaît que si la valeur
    n'est pas 1. L'anglais en a besoin — « 1 death » contre « 2 deaths » —
    là où le français écrit « 1 décès » comme « 2 décès ».
    """
    def plural(match):
        key, suffix = match.group(1), match.group(2)
        if key not in values:
            return match.group(0)
        return "" if is_one(values[key]) else suffix

    out = PLURAL_RE.sub(plural, template)
    for key, value in values.items():
        out = out.replace("{%s}" % key, str(value))
    return out


# --------------------------------------------------------------------------
# URL
# --------------------------------------------------------------------------

class Urls(object):
    """Calcule les URL de chaque page dans chaque langue."""

    def __init__(self, config):
        self.config = config
        self.origin = config["site"]["origin"].rstrip("/")
        self.slugs = {p["id"]: p["slug"] for p in config["pages"]}
        self.province_slugs = config["provinceSlugs"]

    def path(self, page_id, lang):
        # Le prefixe vient de LOCALES : sans lui, toute langue autre que le
        # francais atterrissait sous « /en/ », en collision avec l'anglais.
        slug = self.slugs[page_id][lang]
        return "%s/%s" % (loc(lang, "urlPrefix"), slug)

    def province_path(self, province, lang):
        # Les pages province sont filles de la page de donnees : /donnees/ituri/.
        slug = self.province_slugs[province]
        return self.path("donnees", lang) + slug + "/"

    def absolute(self, path):
        return self.origin + path

    def output_file(self, path):
        """/donnees/ -> <racine>/donnees/index.html"""
        return os.path.join(ROOT, *(path.strip("/").split("/") + ["index.html"])) \
            if path.strip("/") else os.path.join(ROOT, "index.html")


# --------------------------------------------------------------------------
# Blocs communs : navigation, fil d'Ariane, pied de page, liens connexes
# --------------------------------------------------------------------------

def province_forms(config, name, lang):
    """Variables de phrase d'une province.

    {name} le nom nu, {in} « en Ituri » / « au Nord-Kivu », {of} « la province
    d'Ituri » / « du Haut-Uele », {the} « l'Ituri » / « le Nord-Kivu », pour les
    tournures ou la province est complement direct.
    """
    if lang == "fr":
        grammar = config.get("provinceGrammar", {}).get(name, {})
        return {"name": name,
                "in": grammar.get("in", "en %s" % name),
                "of": grammar.get("of", "de %s" % name),
                "the": grammar.get("the", "le %s" % name)}
    if lang == "sw":
        # Le swahili n'a pas d'article : « katika Ituri », « ya Ituri », et le
        # nom nu la ou le francais dirait « l'Ituri ».
        return {"name": name, "in": "katika %s" % name,
                "of": "ya %s" % name, "the": name}
    return {"name": name, "in": "in %s" % name, "of": "of %s" % name, "the": name}


def by_id_page(config, page_id):
    return next(p for p in config["pages"] if p["id"] == page_id)


def label_for(page, strings_lang, i18n_lang):
    source, key = page["navLabelKey"].split(":", 1)
    return (i18n_lang if source == "i18n" else strings_lang)[key]


def build_nav(config, urls, lang, strings_lang, i18n_lang, current_id, provinces,
              current_province=None):
    """Barre de navigation : un groupe deroulant par intertitre.

    Depuis le 3 octobre 2026 il y a quatre groupes — Actualites, Explorer,
    Comprendre, Le site — et Explorer se deroule en DEUX COLONNES :
    TROIS COLONNES : « Evolution de l'epidemie » (Ensemble du pays puis
    chaque page province, empiles au meme niveau), « Face a l'epidemie »
    (Riposte, Defis) et « Donnees detaillees » (Sources & bulletins, Base de
    donnees). mainNav est une liste de groupes ; un groupe porte soit
    `pages` (une liste de liens), soit `columns` (des { titleKey, items }).
    Dans une colonne, l'entree speciale « @provinces » se developpe en une
    ligne par province — ces liens portent l'essentiel du maillage interne
    vers les pages province. Le meme HTML
    sert de menu plein ecran sur telephone, ou les colonnes s'empilent.

    Ce menu etait avant une colonne laterale, dont « Donnees detaillees »
    deroulait ses provinces au clic (side-toggle, zonesDropdown) ; le JS qui
    les reecrivait ne trouve plus son element et ne fait plus rien.
    """
    by_id = {p["id"]: p for p in config["pages"]}

    def lien(page_id):
        page = by_id[page_id]
        label = esc(label_for(page, strings_lang, i18n_lang))
        # Pastille a droite d'un onglet, pour annoncer une page : navBadge =
        # {key} dans pages.json (« Nouveau » : retiree a la main quand le
        # proprietaire le dit, decision du 7 septembre 2026 ; « Bientot » sur
        # la base de donnees), un « jusquau » facultatif (AAAA-MM-JJ) la fait
        # expirer seule.
        badge = page.get("navBadge")
        if badge and date.today().isoformat() <= badge.get("jusquau", "9999-12-31"):
            label += (' <span class="nav-badge%s">%s</span>'
                      % (" nav-badge-" + badge["style"] if badge.get("style") else "",
                         esc(strings_lang[badge["key"]])))
        current = ' aria-current="page"' if page_id == current_id else ""
        # Une ligne de description sous chaque lien dans les panneaux de
        # l'ordinateur (masquee sur telephone).
        desc = strings_lang.get("navDesc_" + page_id.replace("-", "_"))
        desc_html = '<span class="nav-desc">%s</span>' % esc(desc) if desc else ""
        return ('        <a href="%s"%s><span class="nav-t">%s</span>%s</a>'
                % (urls.path(page_id, lang), current, label, desc_html))

    def lignes_provinces():
        # Une ligne par province, au meme niveau que « Ensemble du pays », sans
        # pastille de couleur : le nom, et dessous le nombre de cas confirmes
        # d'apres le dernier bulletin (3 octobre 2026).
        liens = []
        for province in provinces:
            name = province["name"]
            current = ' aria-current="page"' if name == current_province else ""
            cas = interp(strings_lang["navProvCases"],
                         {"n": fmt(province.get("confirmed"), lang)})
            liens.append('        <a href="%s"%s title="%s"><span class="nav-t">%s</span>'
                         '<span class="nav-desc">%s</span></a>'
                         % (urls.province_path(name, lang), current,
                            esc(strings_lang["navProvTitle"]), esc(name), esc(cas)))
        return "\n".join(liens)

    def colonne(col):
        # compact : « Ensemble du pays » sur toute la largeur puis les provinces
        # sur deux colonnes (colonne « Evolution de l'epidemie »).
        compact = col.get("compact", False)
        parts = ['      <div class="nav-col%s">' % (" nav-col-compact" if compact else ""),
                 '        <div class="nav-col-titre">%s</div>' % esc(strings_lang[col["titleKey"]])]
        for item in col["items"]:
            parts.append(lignes_provinces() if item == "@provinces" else lien(item))
        parts.append('      </div>')
        return "\n".join(parts)

    groupes = []
    for groupe in config["mainNav"]:
        if "columns" in groupe:
            corps = ('      <div class="nav-cols">\n%s\n      </div>'
                     % "\n".join(colonne(c) for c in groupe["columns"]))
            classe = "nav-grp nav-grp-cols"
        else:
            corps = "\n".join(lien(pid).replace("        <a", "      <a", 1)
                              for pid in groupe["pages"])
            classe = "nav-grp"
        groupes.append(
            '      <div class="%s">\n'
            '      <button class="nav-grp-btn side-nav-title" type="button" aria-expanded="false">'
            '<span>%s</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            '<polyline points="6 9 12 15 18 9"/></svg></button>\n'
            '      <div class="nav-pop">\n%s\n      </div></div>'
            % (classe, esc(strings_lang[groupe["titleKey"]]), corps))
    return ('    <nav class="side-nav" aria-label="%s">\n%s\n    </nav>'
            % (esc(strings_lang["navLabel"]), "\n".join(groupes)))


def build_breadcrumb(urls, lang, strings_lang, trail):
    """trail : liste de (libellé, chemin ou None pour la page courante).

    La ligne visible est retiree le 7 octobre 2026 (demande du proprietaire) :
    avec la barre du haut, elle repetait le titre de la page. Le fil reste
    declare aux moteurs de recherche (BreadcrumbList, json-LD, plus haut)."""
    return ""
    if not trail:
        return ""
    parts = ['    <a href="%s">%s</a>' % (urls.path("accueil", lang),
                                          esc(strings_lang["breadcrumbHome"]))]
    for label, path in trail:
        parts.append('    <span class="sep" aria-hidden="true">/</span>')
        if path:
            parts.append('    <a href="%s">%s</a>' % (path, esc(label)))
        else:
            parts.append('    <span aria-current="page">%s</span>' % esc(label))
    return ('  <nav class="breadcrumb" aria-label="%s">\n%s\n  </nav>'
            % (esc(strings_lang["breadcrumbLabel"]), "\n".join(parts)))


X_ICONE = ('<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
           '<path d="M18.9 2H22l-7.2 8.3L23.2 22h-6.6l-5.2-6.8L5.5 22H2.3l7.7-8.8L1 2h6.8l4.7 6.2L18.9 2z"/></svg>')


def lien_x(config, libelle, classe=""):
    """Lien vers le compte X du site (site.xProfile dans pages.json, sans le
    @), ou chaine vide tant qu'il n'est pas renseigne — rien n'est rendu
    plutot qu'un lien mort (8 septembre 2026)."""
    compte = (config["site"].get("xProfile") or "").strip().lstrip("@")
    if not compte:
        return ""
    return ('<a href="https://x.com/%s" rel="me noopener" target="_blank" class="lien-x%s">%s %s</a>'
            % (esc(compte), (" " + classe) if classe else "", X_ICONE, esc(libelle)))


TELEGRAM_ICONE = ('<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
                  '<path d="M21.9 4.3 18.7 19c-.2 1-.9 1.3-1.8.8l-4.9-3.6-2.4 2.3c-.3.3-.5.5-1 .5l.4-5 9.1-8.2c.4-.4-.1-.6-.6-.2L6.2 12.7 1.4 11.2c-1-.3-1.1-1 .2-1.5L20.5 3c.9-.3 1.6.2 1.4 1.3z"/></svg>')


def lien_telegram(config, libelle):
    """Le canal Telegram (site.telegram dans pages.json, « @canal » ou son
    adresse complete), ou chaine vide tant qu'il n'est pas ouvert — meme
    regle que lien_x() : jamais de lien mort (22 septembre 2026)."""
    canal = (config["site"].get("telegram") or "").strip()
    if not canal:
        return ""
    url = canal if canal.startswith("http") else "https://t.me/%s" % canal.lstrip("@")
    return ('<a href="%s" rel="noopener" target="_blank" class="lien-telegram footer-x">%s %s</a>'
            % (esc(url), TELEGRAM_ICONE, esc(libelle)))


def build_footer(config, urls, lang, strings_lang, i18n_lang, provinces, avec_avertissement=True):
    by_id = {p["id"]: p for p in config["pages"]}
    columns = []
    def provinces_col():
        province_links = []
        for province in provinces:
            province_links.append(
                '        <li><a href="%s">%s</a></li>'
                % (urls.province_path(province["name"], lang), esc(province["name"])))
        return ('      <div class="footer-col">\n'
                '        <h2>%s</h2>\n'
                '        <ul>\n%s\n        </ul>\n'
                '      </div>' % (esc(strings_lang["footerProvincesTitle"]),
                                  "\n".join(province_links)))

    for column in config["footerNav"]:
        # La colonne des provinces se place ou footerNav la met (9 octobre
        # 2026 : avant « Ebola hors de RDC » et « Le site »).
        if column.get("provinces"):
            columns.append(provinces_col())
            continue
        links = []
        for page_id in column["pages"]:
            links.append('        <li><a href="%s">%s</a></li>'
                         % (urls.path(page_id, lang),
                            esc(label_for(by_id[page_id], strings_lang, i18n_lang))))
        # « Suivre sur X » ferme la colonne « Le site », quand le compte existe.
        if column["titleKey"] == "footerSiteTitle":
            lx = lien_x(config, strings_lang["footerFollowX"], "footer-x")
            if lx:
                links.append('        <li>%s</li>' % lx)
            # Le canal Telegram, seulement s'il est ouvert. LE FLUX RSS A ETE
            # RETIRE DU SITE le 23 septembre 2026 : plus de lien au pied, plus
            # de <link rel="alternate">, plus de feed.xml genere. Le module
            # `build_feeds` RESTE — `notifier_telegram` lui emprunte annonce(),
            # contexte() et _lettres(), et l'alerte Telegram tomberait avec lui.
            lt = lien_telegram(config, strings_lang["footerFollowTelegram"])
            if lt:
                links.append('        <li>%s</li>' % lt)
        columns.append(
            '      <div class="footer-col">\n'
            '        <h2>%s</h2>\n'
            '        <ul>\n%s\n        </ul>\n'
            '      </div>' % (esc(strings_lang[column["titleKey"]]), "\n".join(links)))

    if not any(c.get("provinces") for c in config["footerNav"]):
        columns.append(provinces_col())

    # Une seule ligne discrete plutot que deux pavas : l'avertissement doit
    # rester sur chaque page — un visiteur arrive de Google atterrit sur
    # n'importe laquelle, pas sur l'accueil — mais le texte complet, lui, n'a
    # besoin d'exister qu'une fois, sur la page A propos.
    # Sur l'accueil, la ligne d'avertissement est retiree (4 octobre 2026, a la
    # demande du proprietaire) : elle reste sur toutes les autres pages, et le
    # texte complet est sur A propos.
    notice = ('    <p class="footer-notice">%s <a href="%s">%s</a></p>\n'
              % (strings_lang["footerNotice"], urls.path("a-propos", lang) + "#avertissement",
                 esc(strings_lang["footerNoticeMore"]))) if avec_avertissement else ""
    return (
        '  <footer>\n'
        '    <div class="footer-nav">\n%s\n    </div>\n'
        '%s'
        '  </footer>' % ("\n".join(columns), notice))


def json_ld(payload):
    return ('<script type="application/ld+json">\n'
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + '\n</script>')


def build_json_ld(kinds, context):
    blocks = []
    meta = context["meta"]
    lang = context["lang"]
    canonical = context["canonical"]

    for kind in kinds:
        if kind == "website":
            # Le NOM DE SITE que Google affiche au-dessus de l'adresse dans ses
            # resultats : il le lit ici (WebSite.name de la page d'accueil) et
            # dans og:site_name, et veut une valeur unique et stable — trois
            # noms differents selon la langue le faisaient retomber sur le
            # domaine. « Ebola Tracker » partout (site.brandName), les noms
            # traduits en alternateName (8 septembre 2026).
            blocks.append(json_ld({
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": context["brandName"],
                "alternateName": context["siteNameAlternates"],
                "url": context["origin"] + "/",
                "inLanguage": list(SITE_LANGUAGES),
            }))
        elif kind == "dataset":
            blocks.append(json_ld({
                "@context": "https://schema.org",
                "@type": "Dataset",
                "name": meta["title"],
                "description": meta["description"],
                "url": canonical,
                "inLanguage": lang,
                "license": "https://creativecommons.org/licenses/by/4.0/",
                "keywords": context["keywords"],
                "temporalCoverage": "2026-05-16/..",
                "spatialCoverage": context.get("spatialCoverage",
                                               "Democratic Republic of the Congo"),
                "distribution": {
                    "@type": "DataDownload",
                    "encodingFormat": "application/json",
                    "contentUrl": context["origin"] + "/data/latest.json",
                },
                "isBasedOn": [
                    {"@type": "WebSite",
                     "name": "Institut National de Santé Publique (INSP) RDC",
                     "url": "https://insp.cd/"},
                    {"@type": "WebSite",
                     "name": "Organisation mondiale de la Santé",
                     "url": "https://www.who.int/"},
                ],
            }))
        elif kind == "datasetBase":
            # La base de donnees (9 octobre 2026) : ce que lit Google Dataset
            # Search. Periode et taille recalculees a chaque generation.
            b = context["base"]
            blocks.append(json_ld({
                "@context": "https://schema.org",
                "@type": "Dataset",
                "name": meta["title"],
                "description": meta["description"],
                "url": canonical,
                "inLanguage": lang,
                "license": base_donnees.LICENCE,
                "isAccessibleForFree": True,
                "creator": {"@type": "Organization", "name": context["brandName"], "url": context["origin"] + "/"},
                "keywords": ["Ebola", "Bundibugyo", "RDC", "DRC", "INSP", "SitRep", "zone de santé",
                             "health zone", "épidémie", "outbreak", "données", "dataset", "CSV"],
                "temporalCoverage": "%s/%s" % (b["dates"][0], b["dates"][-1]),
                "spatialCoverage": {"@type": "Place", "name": "République démocratique du Congo",
                                    "geo": {"@type": "GeoShape", "box": "-13.46 12.2 5.39 31.31"}},
                "variableMeasured": ["cas confirmés", "décès", "nouveaux cas", "nouveaux décès", "létalité",
                                     "guéris", "décès en communauté", "décès en CTE", "alertes reçues",
                                     "alertes validées", "échantillons de laboratoire", "positivité",
                                     "hospitalisés en CTE", "occupation des lits", "contacts suivis",
                                     "personnes vaccinées"],
                "distribution": [
                    {"@type": "DataDownload", "encodingFormat": "text/csv",
                     "contentUrl": context["origin"] + "/data/base-ebola-rdc.csv"},
                    {"@type": "DataDownload", "encodingFormat": "application/json",
                     "contentUrl": context["origin"] + "/data/base-ebola-rdc.json"},
                ],
                "isBasedOn": [{"@type": "WebSite",
                               "name": "Institut National de Santé Publique (INSP) RDC",
                               "url": "https://insp.cd/"}],
                "dateModified": b["dates"][-1],
            }))
        elif kind in ("article", "collection"):
            blocks.append(json_ld({
                "@context": "https://schema.org",
                "@type": "CollectionPage" if kind == "collection" else "WebPage",
                "name": meta["title"],
                "headline": meta["h1"],
                "description": meta["description"],
                "url": canonical,
                "inLanguage": lang,
                "isPartOf": {"@type": "WebSite",
                             "name": context["brandName"],
                             "url": context["origin"] + "/"},
            }))
        elif kind == "faqPays" and context["faqPays"]:
            blocks.append(json_ld({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "inLanguage": lang,
                "mainEntity": [
                    {"@type": "Question",
                     "name": item["q"],
                     "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                    for item in context["faqPays"]
                ],
            }))
        elif kind == "faq":
            blocks.append(json_ld({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "inLanguage": lang,
                "mainEntity": [
                    {"@type": "Question",
                     "name": item["q"],
                     "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                    for item in context["faqPlain"]
                ],
            }))

    if context.get("breadcrumbTrail"):
        elements = [{"@type": "ListItem", "position": 1,
                     "name": context["breadcrumbHome"],
                     "item": context["origin"] + context["homePath"]}]
        for index, (label, path) in enumerate(context["breadcrumbTrail"], start=2):
            elements.append({"@type": "ListItem", "position": index, "name": label,
                             "item": context["origin"] + (path or context["path"])})
        blocks.append(json_ld({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": elements,
        }))

    return "\n".join(blocks)


# --------------------------------------------------------------------------
# Contenus pré-générés à partir des données
# --------------------------------------------------------------------------

# Pastilles de couleur par province, dans la palette du nouveau design.
PROVINCE_COLORS = {
    "Ituri": "#005E82", "Nord-Kivu": "#A06F30", "Haut-Uélé": "#327957",
    "Tshopo": "#6B5CA5", "Sud-Kivu": "#5A544C", "Bas-Uélé": "#993A2E",
    # Septieme province, SitRep 119 (10 septembre 2026) : un magenta, seule
    # teinte encore libre qui se separe du rouge et du violet en deuteranopie.
    "Sud-Ubangi": "#B0487D",
}


def zones_sub(national, meta, lang, i18n_lang, strings_lang):
    """Reproduit tr('zonesTableSub')(n, total, num, date) de app.js."""
    zones = (national or {}).get("healthZonesAffected") or {}
    count, total = zones.get("n", 0), zones.get("total", 151)
    number = (meta or {}).get("sitrepNumber", "")
    reporting = (meta or {}).get("reportingDate", "")
    text = interp(strings_lang["zonesSubAffected"], {"n": count, "total": total})
    if number:
        text += " · SitRep N°%s" % number
    if reporting:
        text += strings_lang["sitrepJoiner"] + short_date(reporting, i18n_lang)
    return esc(text)


def sitrep_ref(meta, lang, i18n_lang, strings_lang):
    """« SitRep N°097 du 19 août 2026 » — repère de fraîcheur sur les pages
    où le total national des zones touchées n'aurait pas de sens."""
    number = (meta or {}).get("sitrepNumber", "")
    reporting = (meta or {}).get("reportingDate", "")
    if not number:
        return ""
    joiner = strings_lang["sitrepJoiner"]
    text = "SitRep N°%s" % number
    if reporting:
        text += joiner + long_date(reporting, i18n_lang)
    return esc(text)


def ordinal(n, lang):
    """« 2e » en francais, « 2nd » en anglais.

    L'anglais a trois exceptions (1st, 2nd, 3rd) et un piege : de 11 a 13, on
    dit bien 11th, 12th, 13th malgre le chiffre des unites.
    """
    if lang == "sw":
        return str(n)          # « mlipuko wa 17 » : le rang reste un chiffre
    if lang != "en":
        return "1re" if n == 1 else "%dᵉ" % n
    if 11 <= n % 100 <= 13:
        return "%dth" % n
    return "%d%s" % (n, {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


def hint_pair(strings_lang, hover_key, touch_key):
    """Deux redactions d'une meme consigne, l'une pour la souris, l'autre pour
    le doigt. C'est la CSS qui tranche, sur (hover:none) : le texte est ecrit
    a la generation, donc juste meme sans JavaScript, et l'appareil n'a pas
    besoin d'etre devine."""
    return ('<span class="on-hover">%s</span>'
            '<span class="on-touch">%s</span>'
            % (esc(strings_lang[hover_key]), esc(strings_lang[touch_key])))


def cfr_badge_class(cfr):
    """Reprend a l'identique cfrBadgeClass() de app.js : memes seuils et memes
    noms de classe. Sans cela, les badges ecrits a la generation changeraient de
    couleur des que le JavaScript reecrit le tableau."""
    if cfr is None or cfr < 30:
        return "zone-badge-low"
    if cfr < 50:
        return "zone-badge-mid"
    return "zone-badge-high"


def province_rows_html(provinces, national, lang, province_history=None, strings_lang=None):
    """Lignes du tableau « par province » d'Ensemble du pays, sur le modele du
    tableau des zones des pages province (7 octobre 2026) : province, cas
    cumules, part du pays, nouveaux cas 24 h, courbe des nouveaux cas sur 30
    jours, deces cumules, nouveaux deces 24 h, letalite, zones touchees.
    Triable (table.zq.tri). renderProvinceSummary d'app.js ne le reecrit pas."""
    from datetime import date as _d, timedelta as _td
    total = (national or {}).get("confirmed")
    hist = sorted(province_history or [], key=lambda h: h["date"])
    fin = hist[-1]["date"] if hist else None
    debut = (_d.fromisoformat(fin) - _td(days=30)).isoformat() if fin else None
    series = {}
    for h in hist:
        if h["date"] < debut:
            continue
        for q in h.get("provinces", []):
            if q.get("confirmed") is not None:
                series.setdefault(q["name"], []).append((h["date"], q["confirmed"]))

    def plus(v):
        return ('<span class="z-plus">+%s</span>' % fmt(v, lang)) if v else '<span class="z-zero">0</span>'

    # Echelle commune au tableau, en racine carree (7 octobre 2026).
    tous = []
    for pts in series.values():
        tous += [max(0, pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts))]
    mx_commun = max(tous + [1]) ** .5

    def spark(vals, couleur, titre):
        if not vals:
            return ""
        w, h = 140, 28
        bw = w / float(len(vals))
        def haut(v):
            return max(1.5, v ** .5 / mx_commun * (h - 2)) if v else 0
        return ('<svg class="z-spark" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s" style="--t:%s">%s</svg>'
                % (w, h, w, h, esc(titre), couleur, "".join(
                    '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"%s/>'
                    % (i * bw + .5, h - haut(v), max(bw - 1, .6), haut(v),
                       ' class="is-der"' if i == len(vals) - 1 else "") for i, (_, v) in enumerate(vals))))

    rows = []
    for province in sorted(provinces, key=lambda p: -(p.get("confirmed") or 0)):
        nom = province["name"]
        color = PROVINCE_COLORS.get(nom, "var(--ink-faint)")
        zones = province.get("healthZonesAffected")
        zones_text = "%s / %s" % (zones["n"], zones["total"]) if zones else "—"
        part = province["confirmed"] / float(total) * 100 if total else 0
        n24 = max(0, province.get("newCases24h") or 0)
        d24 = (province.get("newDeathsCommunity24h") or 0) + (province.get("newDeathsIntraCTE24h") or 0)
        pts = series.get(nom, [])
        nv = [(pts[i][0], max(0, pts[i][1] - pts[i - 1][1])) for i in range(1, len(pts))]
        n30 = sum(v for _, v in nv)
        titre = interp(strings_lang["zonesSparkTitle"], {"zone": nom, "n": fmt(n30, lang)}) if strings_lang else ""
        rows.append(
            '              <tr><td><span class="zdot" style="background:%s;"></span>%s</td>'
            '<td class="zt z-cas" data-v="%d">%s</td><td data-v="%.1f">%s</td><td data-v="%d">%s</td>'
            '<td class="zs" data-v="%d">%s</td><td class="zt z-dec" data-v="%d">%s</td><td data-v="%d">%s</td>'
            '<td data-v="%.1f">%s</td><td data-v="%d">%s</td></tr>' % (
                color, esc(nom), province.get("confirmed") or 0, fmt(province.get("confirmed"), lang),
                part, fmt_cfr(part, lang) if total else "—", n24, plus(n24), n30, spark(nv, color, titre),
                province.get("deaths") or 0, fmt(province.get("deaths"), lang), d24, plus(d24),
                province.get("cfr") or 0, fmt_cfr(province.get("cfr"), lang),
                (zones or {}).get("n") or 0, zones_text))
    return "\n".join(rows)


def zone_points(config, geo):
    """Les points GPS de site/pages.json projetes dans le repere de la carte,
    indexes par nom normalise. Meme formule que build_geo.py : x depuis le
    meridien ouest du cadre, y depuis son parallele nord, a l'echelle du
    viewBox."""
    proj = geo["projection"]
    points = {}
    for name, (lat, lon) in config.get("zoneCoordinates", {}).get("places", {}).items():
        x = (lon - proj["minLon"]) * proj["scale"]
        y = (proj["maxLat"] - lat) * proj["scale"]
        points[normalise_zone(name)] = [round(x, 1), round(y, 1)]
    return points


def circle_legend_html(config, lang, i18n_lang):
    """La legende de la vue « cercles » : les cercles etalons, du plus petit
    au plus grand, chacun sous son nombre, au coefficient ordinateur. Les
    bulles sont dessinees en pixels ecran par app.js, qui redessine aussi
    cette legende (renderCircleLegend, meme geometrie) au coefficient en
    vigueur — sur telephone il est plus petit. Ce rendu statique est le point
    de depart, et le repli sans JavaScript (ou il n'y a pas de bulles)."""
    scale = config["cartogram"].get("circleScale", 1.0)
    plancher = config["cartogram"].get("circleMinRadius", 2.5)
    steps = config["cartogram"].get("circleLegend", [1, 10, 100, 1000])
    rayons = [max(plancher, scale * (v ** 0.5)) for v in steps]
    gap, haut_texte, marge = 9, 14, 6     # marge : le « 1 » sous le premier cercle deborde sinon
    largeur = marge * 2 + sum(2 * r for r in rayons) + gap * (len(rayons) - 1)
    hauteur = 2 * max(rayons) + haut_texte + 4
    x, parts = float(marge), []
    base = 2 * max(rayons)
    for v, r in zip(steps, rayons):
        cx = x + r
        parts.append(
            '<circle class="legend-circle" cx="%.1f" cy="%.1f" r="%.1f"/>'
            '<text x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
            % (cx, base - r, r, cx, base + haut_texte - 2, esc(fmt(v, lang))))
        x += 2 * r + gap
    return (
        '            <div class="map-legend" data-mode="circles">\n'
        '              <div class="title">%s</div>\n'
        '              <svg class="legend-circles" viewBox="0 0 %.1f %.1f" width="%.0f" height="%.0f" aria-hidden="true">%s</svg>\n'
        '            </div>'
        % (esc(i18n_lang["legendTitle"]), largeur, hauteur, largeur, hauteur, "".join(parts)))


def zone_map_html(config, geo, health_zones, provinces, urls, lang, strings_lang):
    """Carte d'apercu de l'accueil : les 519 zones de sante du pays.

    Elle remplace la grille schematique 7x6, qui ne se lisait pas comme la RDC.
    Colorier a la zone plutot qu'a la province est aussi plus honnete : l'Ituri
    fait 65 000 km2, le peindre entierement au maximum d'intensite exagererait
    enormement l'etendue reelle de l'epidemie.

    Le trace vient de site/geo/zones-overview.json, produit une fois pour
    toutes par scripts/build_geo.py ; seule la couleur change chaque jour. Tout
    est ecrit en dur : la carte s'affiche sans JavaScript, sans reseau, et sert
    de repli quand la carte Leaflet ne peut pas se charger.
    """
    thresholds = config["cartogram"]["zoneThresholds"]
    aliases = geo.get("aliases", {})

    def key_of(name):
        base = normalise_zone(name)
        return aliases.get(base, base)

    # Un nom de zone ne suffit pas a identifier une zone : « Lubunga » existe en
    # Tshopo et au Kasai-Central. On indexe donc par nom, puis on departage par
    # province — sans quoi la carte colorait une zone indemne a l'autre bout du
    # pays.
    by_key = {}
    for zone in health_zones:
        by_key.setdefault(key_of(zone["name"]), []).append(zone)
    province_url = {p["name"]: urls.province_path(p["name"], lang) for p in provinces}

    def ours_for(geo_zone):
        candidates = by_key.get(geo_zone["key"])
        if not candidates:
            return None
        if len(candidates) == 1 and len(
                [z for z in geo["zones"] if z["key"] == geo_zone["key"]]) == 1:
            return candidates[0]
        wanted = normalise_zone(geo_zone["province"])
        same = [c for c in candidates
                if normalise_zone(c.get("province")) == wanted]
        if same:
            return same[0]
        # Le nom existe plusieurs fois dans le fond de carte : sans accord sur
        # la province, on ne colorie rien plutot que de se tromper de zone.
        return None if len(candidates) > 1 or len(
            [z for z in geo["zones"] if z["key"] == geo_zone["key"]]) > 1 else candidates[0]

    def level(cases):
        if not cases:
            return 0
        for index, limit in enumerate(thresholds):
            if cases < limit:
                return index + 1
        return len(thresholds) + 1

    quiet, active, matched = [], [], set()
    touchees = []   # cadres des zones avec des cas : l'emprise de l'epidemie
    for zone in geo["zones"]:
        ours = ours_for(zone)
        if not ours:
            quiet.append('          <path d="%s"><title>%s (%s)</title></path>'
                         % (zone["d"], esc(zone["name"]), esc(zone["province"])))
            continue
        matched.add(zone["key"])
        cases = ours.get("cases") or 0
        if cases and len(zone.get("box", [])) == 4:
            touchees.append(zone["box"])
        href = province_url.get(ours.get("province"))
        label = interp(strings_lang["zoneMapLabel"], {
            "name": zone["name"],
            "province": ours.get("province", zone["province"]),
            "cases": fmt(cases, lang)})
        attrs = ('class="zm-zone is-%d" data-name="%s" data-sub="%s" data-value="%s" '
                 'data-note="%s"' % (level(cases), esc(zone["name"]),
                                     esc(ours.get("province", zone["province"])),
                                     fmt(cases, lang),
                                     esc(strings_lang["cartoCasesNote"])))
        box = " ".join(str(v) for v in zone.get("box", []))
        if href:
            active.append('          <a %s data-box="%s" href="%s" data-href="%s">'
                          '<path d="%s"><title>%s</title></path></a>'
                          % (attrs, box, href, href, zone["d"], esc(label)))
        else:
            active.append('          <g %s data-box="%s">'
                          '<path d="%s"><title>%s</title></path></g>'
                          % (attrs, box, zone["d"], esc(label)))

    unmatched = [z["name"] for z in health_zones if key_of(z["name"]) not in matched]
    if unmatched:
        print("  ! zones sans trace sur la carte d'apercu : %s" % ", ".join(unmatched))
        print("    (relancer scripts/build_geo.py pour rafraichir les correspondances)")

    # Repères géographiques : ce que le fond de tuiles apportait — quelques
    # villes nommées — mais choisi plutôt que subi, et dans la palette du site.
    marks = []
    for place in geo.get("landmarks", []):
        title = place["name"]
        if place.get("province"):
            title += " — %s" % place["province"]
        # data-name : le CSS masque certains reperes sur telephone, par nom.
        marks.append(
            '          <g class="zm-mark is-%s" data-name="%s" data-x="%s" data-y="%s" '
            'transform="translate(%s %s)">'
            '<circle r="3.2"><title>%s</title></circle>'
            '<text x="7" y="3.6">%s</text></g>'
            % (place["kind"], normalise_zone(place["name"]), place["x"], place["y"],
               place["x"], place["y"], esc(title), esc(place["name"])))

    # L'emprise de l'epidemie (les zones avec des cas, plus une marge) : sur
    # grand ecran la carte s'ouvre cadree dessus (3 octobre 2026), le pays
    # entier restant a un bouton. Ecrite ici, calculee a partir des cadres des
    # zones, pour que le cadrage suive l'epidemie quand elle s'etend.
    emprise = ""
    if touchees:
        marge = 40
        x0 = min(b[0] for b in touchees) - marge
        y0 = min(b[1] for b in touchees) - marge
        x1 = max(b[0] + b[2] for b in touchees) + marge
        y1 = max(b[1] + b[3] for b in touchees) + marge
        emprise = ' data-outbreak-box="%.1f %.1f %.1f %.1f"' % (x0, y0, x1 - x0, y1 - y0)

    return ('      <svg class="zonemap" viewBox="%s" role="img" aria-label="%s"%s '
            'preserveAspectRatio="xMidYMid meet">\n'
            '        <g class="zm-viewport">\n'
            '          <g class="zm-quiet">\n%s\n          </g>\n'
            '          <g class="zm-active">\n%s\n          </g>\n'
            '          <g class="zm-marks">\n%s\n          </g>\n'
            '        </g>\n'
            "      </svg>" % (
                geo["viewBox"],
                esc(interp(strings_lang["cartoZonesTouched"],
                           {"n": len(matched), "total": len(geo["zones"])})),
                emprise,
                "\n".join(quiet), "\n".join(active), "\n".join(marks)))


def zone_new_deaths(zone):
    """Nouveaux deces 24 h d'une zone, tels que le bulletin les totalise.

    `newDeaths24h` est le total imprime par le PDF. Le repli sur la somme des
    deux categories ne sert qu'a lire un latest.json produit avant la
    correction du 25 aout ; il redonne un chiffre double sur les lignes ou une
    seule categorie etait imprimee.
    """
    if not zone:
        return 0
    total = zone.get("newDeaths24h")
    if total is not None:
        return total
    return (zone.get("deathsCommunity24h") or 0) + (zone.get("deathsIntraCTE24h") or 0)


def province_map_html(geo_map, province_name, zones, config, lang, strings_lang, aliases):
    """Carte d'une province : ses zones de sante en detail, les voisines en gris.

    Meme composant que la carte de l'accueil — memes classes, memes attributs —
    de sorte que le survol, le panneau de detail et le curseur temporel
    fonctionnent sans une ligne de JavaScript supplementaire.
    """
    thresholds = config["cartogram"]["zoneThresholds"]

    def key_of(name):
        base = normalise_zone(name)
        return aliases.get(base, base)

    by_key = {}
    for zone in zones:
        by_key.setdefault(key_of(zone["name"]), []).append(zone)

    def level(cases):
        if not cases:
            return 0
        for index, limit in enumerate(thresholds):
            if cases < limit:
                return index + 1
        return len(thresholds) + 1

    quiet, active, touched = [], [], 0
    for zone in geo_map["zones"]:
        title = "%s (%s)" % (zone["name"], zone["province"])
        if not zone["inside"]:
            quiet.append('          <path d="%s"><title>%s</title></path>'
                         % (zone["d"], esc(title)))
            continue
        candidates = by_key.get(zone["key"], [])
        same = [c for c in candidates
                if normalise_zone(c.get("province")) == normalise_zone(province_name)]
        ours = same[0] if same else None
        cases = (ours or {}).get("cases") or 0
        deaths = (ours or {}).get("deaths") or 0
        if ours:
            touched += 1
            title = interp(strings_lang["zoneMapTitle"], {
                "name": zone["name"], "cases": fmt(cases, lang),
                "deaths": fmt(deaths, lang)})
        # Le total du bulletin, jamais la somme des deux categories : quand
        # une seule est imprimee, l'autre colonne porte deja ce total et
        # l'addition le comptait deux fois. Voir parse_zone_day_columns().
        new_deaths = zone_new_deaths(ours)
        active.append(
            '          <g class="zm-zone is-%d" data-name="%s" data-sub="%s" '
            'data-note="%s" data-cases="%s" data-deaths="%s" '
            'data-new-cases="%s" data-new-deaths="%s">'
            '<path d="%s"><title>%s</title></path></g>'
            % (level(cases), esc(zone["name"]), esc(province_name),
               esc(strings_lang["cartoCasesNote"]),
               fmt(cases, lang), fmt(deaths, lang),
               (ours or {}).get("newCases24h") or 0, new_deaths,
               zone["d"], esc(title)))

    marks = []
    for place in geo_map.get("landmarks", []):
        marks.append(
            '          <g class="zm-mark is-%s" data-name="%s" data-x="%s" data-y="%s" '
            'transform="translate(%s %s)">'
            '<circle r="3.2"/><text x="7" y="3.6">%s</text></g>'
            % (place["kind"], normalise_zone(place["name"]), place["x"], place["y"],
               place["x"], place["y"], esc(place["name"])))

    svg = ('      <svg class="zonemap" data-scope="province" viewBox="%s" role="img" '
           'aria-label="%s" preserveAspectRatio="xMidYMid meet">\n'
           '        <g class="zm-viewport">\n'
           '          <g class="zm-quiet">\n%s\n          </g>\n'
           '          <g class="zm-active">\n%s\n          </g>\n'
           '          <g class="zm-marks">\n%s\n          </g>\n'
           '        </g>\n'
           "      </svg>" % (
               geo_map["viewBox"],
               esc("%s — %s" % (strings_lang["provinceMapTitle"], province_name)),
               "\n".join(quiet), "\n".join(active), "\n".join(marks)))
    return svg, touched, sum(1 for z in geo_map["zones"] if z["inside"])


def normalise_zone(text):
    """Meme normalisation que scripts/build_geo.py : accents, casse, tirets et
    espaces. Les ecarts d'orthographe restants sont resolus par la table
    d'alias que build_geo.py ecrit dans le fichier de traces."""
    import unicodedata
    text = unicodedata.normalize("NFD", str(text or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    for char in "-_'\u2019.":
        text = text.replace(char, " ")
    return "".join(text.lower().split())


SIDE_STAT_KEYS = [
    ("confirmed", "labelConfirmed", "kpi-confirmed", "kpi-confirmed-delta", None),
    ("deaths", "labelDeaths", "kpi-deaths", "kpi-deaths-delta", None),
    ("recovered", "labelRecovered", "kpi-recovered", "kpi-recovered-delta", None),
    ("active", "labelIsolation", "kpi-isolation", None, "isolationDelta"),
    ("cfr", "labelCfr", "kpi-cfr", None, "cfrDelta"),
]


def panel_stats_html(national, lang, i18n_lang):
    """Les chiffres nationaux, en lignes compactes, pour le panneau de la
    carte (cas et deces seulement). Ils portent data-kpi et non un identifiant : renderKPIs()
    rafraichit les deux emplacements d'un coup, sans que l'un ait a connaitre
    l'existence de l'autre."""
    values = {
        "confirmed": fmt(national.get("confirmed"), lang),
        "deaths": fmt(national.get("deaths"), lang),
        "recovered": fmt(national.get("recovered"), lang),
        "active": fmt(national.get("inCTE"), lang),
        "cfr": fmt_cfr(national.get("cfr"), lang),
    }
    # Seuls les cumuls ont un ecart qui veut dire quelque chose : le nombre de
    # patients en isolement et le taux de letalite ne s'additionnent pas d'un
    # bulletin a l'autre.
    with_delta = {"confirmed", "deaths", "recovered"}
    rows = []
    for key, label_key, _value_id, _delta_id, _delta_key in SIDE_STAT_KEYS:
        # Depuis le 3 octobre 2026 le panneau de la carte ne garde que les cas
        # et les deces (choix du proprietaire) ; gueris, isolement et letalite
        # restent dans le bento sous la carte et sur les autres pages.
        if key not in ("confirmed", "deaths"):
            continue
        delta = ('<span class="d" data-kpi-delta="%s"></span>' % key) if key in with_delta else ""
        rows.append(
            '          <div class="cd-nat %s">\n'
            '            <span class="k" data-i18n="%s">%s</span>\n'
            '            <span class="n"><span class="v" data-kpi="%s">%s</span>%s</span>\n'
            '          </div>' % (key, label_key, esc(i18n_lang[label_key]),
                                  key, values[key], delta))
    return '        <div class="cd-national">\n%s\n        </div>' % "\n".join(rows)


def cles_chiffres_html(national, lang, i18n_lang, strings_lang):
    """« Les chiffres cles de l'epidemie » (accueil, 5 octobre 2026) : cinq
    chiffres du dernier bulletin — cas, deces, gueris, patients en isolement,
    taux de suivi des contacts. Les quatre premiers portent data-kpi (comme le
    panneau de la carte) : renderKPIs() les rafraichit si latest.json est plus
    recent que la page. Le taux de suivi vient de national.contactsFollowUpRate."""
    suivi = national.get("contactsFollowUpRate")
    cases = [
        ("confirmed", "is-grand", esc(i18n_lang["labelConfirmed"]),
         '<span class="v" data-kpi="confirmed">%s</span><span class="d" data-kpi-delta="confirmed"></span>'
         % fmt(national.get("confirmed"), lang)),
        ("deaths", "is-grand", esc(i18n_lang["labelDeaths"]),
         '<span class="v" data-kpi="deaths">%s</span><span class="d" data-kpi-delta="deaths"></span>'
         % fmt(national.get("deaths"), lang)),
        ("recovered", "is-moyen", esc(i18n_lang["labelRecovered"]),
         '<span class="v" data-kpi="recovered">%s</span><span class="d" data-kpi-delta="recovered"></span>'
         % fmt(national.get("recovered"), lang)),
        ("active", "is-moyen", esc(i18n_lang["labelIsolation"]),
         '<span class="v" data-kpi="active">%s</span>' % fmt(national.get("inCTE"), lang)),
        ("follow", "is-moyen", esc(strings_lang["keyFollow"]),
         '<span class="v">%s</span>' % (fmt_cfr(suivi, lang) if suivi is not None else "—")),
    ]
    return "\n".join(
        '        <div class="kc-stat is-%s %s"><span class="n">%s</span><span class="k">%s</span></div>'
        % (cle, span, corps, label) for cle, span, label, corps in cases)


def cles_courbe_svg(sitreps, lang, i18n_lang, strings_lang):
    """La courbe des cas confirmes cumules des « chiffres cles » (5 octobre
    2026) : elle occupe la largeur de la page — du bord gauche au bord droit de
    la colonne de contenu, sans deborder —, part fondue et devient nette vers la
    droite ; un point rouge marque le dernier bulletin.

    Le SVG est etire sans conserver ses proportions (preserveAspectRatio none,
    trait non redimensionnable) : il suit la largeur de l'ecran. Pour que rien
    ne se deforme, le point rouge, son etiquette et les mois sont des elements
    HTML places en pourcentages du meme cadre. Echelle en temps : les dates
    sans bulletin ne creusent pas la courbe. Aucun JavaScript requis."""
    from datetime import date as _d
    pts = [(r["date"], r["confirmed"]) for r in sorted(
        (r for r in sitreps if r.get("date") and r.get("confirmed") is not None), key=lambda r: r["date"])]
    if len(pts) < 2:
        return ""
    XFIN, YBAS, YHAUT = 0.985, 0.94, 0.13      # fin de la courbe, base, sommet (fractions du cadre)
    d0, d1 = _d.fromisoformat(pts[0][0]), _d.fromisoformat(pts[-1][0])
    duree = max(1, (d1 - d0).days)
    vmax = max(v for _, v in pts)
    def xy(date, v):
        x = (_d.fromisoformat(date) - d0).days / duree * XFIN
        y = YBAS - v / vmax * (YBAS - YHAUT)
        return x, y
    coords = [xy(dt, v) for dt, v in pts]
    U = 1000.0
    ligne = "M" + " L".join("%.2f %.2f" % (x * U, y * U) for x, y in coords)
    aire = ligne + " L%.2f %.2f L%.2f %.2f Z" % (coords[-1][0] * U, YBAS * U, 0, YBAS * U)
    guides = "".join('<line class="kc-guide" x1="0" x2="%d" y1="%.1f" y2="%.1f"/>'
                     % (U, (YBAS - f * (YBAS - YHAUT)) * U, (YBAS - f * (YBAS - YHAUT)) * U)
                     for f in (0.25, 0.5, 0.75, 1.0))
    xl, yl = coords[-1]
    return (
        '<svg class="kc-svg" viewBox="0 0 1000 1000" preserveAspectRatio="none" role="img" aria-label="%s">'
        '<defs><linearGradient id="kcAire" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#2F8FC0" stop-opacity=".24"/><stop offset="1" stop-color="#2F8FC0" stop-opacity="0"/>'
        '</linearGradient></defs>'
        '%s<line class="kc-base" x1="0" x2="%d" y1="%.1f" y2="%.1f"/>'
        '<path class="kc-aire" d="%s" fill="url(#kcAire)"/>'
        '<path class="kc-line" d="%s"/></svg>'
        '<div class="kc-fin" style="left:%.2f%%;top:%.2f%%">'
        '<span class="kc-dot"></span>'
        '<span class="kc-etiq"><b>%s</b><i>%s · %s</i></span></div>'
        % (esc(strings_lang["keyCurveLabel"]), guides, U, YBAS * U, YBAS * U, aire, ligne,
           xl * 100, yl * 100, fmt(pts[-1][1], lang), esc(strings_lang["keyLast"]),
           esc(long_date(pts[-1][0], i18n_lang))))


def province_case_window(history, name):
    """Date du premier cas confirme, et date du dernier cas signale.

    Le « dernier cas » est la derniere fois que le cumul a augmente : un
    bulletin qui reconduit le meme total ne signale aucun cas nouveau. C'est
    l'information qui dit si une province est encore active.
    """
    points = province_series(history, name)
    if not points:
        return None, None
    # « previous » part de la PREMIERE valeur observee, pas de zero. Aucune
    # province n'apparait jamais a zero dans ce fichier : chacune y entre avec
    # un cumul deja constitue — 30 cas pour l'Ituri, 4 pour la Tshopo, 3 pour
    # le Sud-Kivu. Initialiser a zero faisait donc passer le premier point
    # pour une hausse, c'est-a-dire pour un cas signale ce jour-la.
    #
    # Le Sud-Kivu en faisait les frais deux fois : sa seule « hausse » etait
    # cet artefact, si bien que premiere et derniere hausse tombaient sur la
    # meme date et que la page annonçait « Premier et seul cas confirme
    # signale le 31 mai 2026 » — alors que la province compte trois cas, tous
    # anterieurs a son entree dans le tableau.
    first = points[0][0]
    last = None
    previous = points[0][1]
    for date, value in points[1:]:
        if value > previous:
            last = date
        previous = value
    return first, last


def province_series(history, name):
    """Serie cumulee d'une province, tiree de data/province-history.json.

    Le fichier porte des lignes parasites issues de l'extraction des PDF
    (« touchees ») et des variantes d'orthographe (« Haut Uele » sans trait
    d'union) : on rapproche sur le nom normalise.
    """
    wanted = normalise_zone(name)
    points = []
    for entry in history:
        date = entry.get("date")
        if not date:
            continue
        for province in entry.get("provinces", []):
            if normalise_zone(province.get("name")) != wanted:
                continue
            if province.get("confirmed") is None:
                continue
            points.append((date, province["confirmed"]))
    points.sort()
    return points


def reports_calendar_html(reports, lang, i18n_lang, strings_lang):
    """Calendrier des bulletins de l'INSP : une case par jour, du premier
    bulletin au dernier, une colonne par semaine (lundi en haut). Une case est
    pleine quand un bulletin existe pour cette date de rapport ; les jours sans
    bulletin restent vides — ils se voient, ils ne sont pas combles."""
    jours = {}
    for r in reports:
        d = r.get("reportingDate")
        if d:
            jours[d] = r.get("sitrepNumber")
    if not jours:
        return ""
    debut = date.fromisoformat(min(jours)); fin = date.fromisoformat(max(jours))
    lundi = debut - timedelta(days=debut.weekday())
    semaines, mois = [], []
    d = lundi; vu = None
    while d <= fin:
        col = []
        for k in range(7):
            j = d + timedelta(days=k)
            iso = j.isoformat()
            if j < debut or j > fin:
                col.append('<i class="cal-d is-hors"></i>')
            elif iso in jours:
                col.append('<i class="cal-d is-on" title="%s — %s %s"></i>' % (
                    esc(long_date(iso, i18n_lang)), esc(strings_lang["calBulletin"]), jours[iso]))
            else:
                col.append('<i class="cal-d" title="%s — %s"></i>' % (
                    esc(long_date(iso, i18n_lang)), esc(strings_lang["calAucun"])))
        label = ""
        if (d + timedelta(days=6)).month != vu and (d + timedelta(days=3)).day <= 31:
            m = (d + timedelta(days=3))
            if vu is None or m.month != vu:
                label = i18n_lang["months"][m.month - 1]; vu = m.month
        mois.append('<span>%s</span>' % esc(label))
        semaines.append('<div class="cal-w">%s</div>' % "".join(col))
        d += timedelta(days=7)
    total = len(jours); possibles = (fin - debut).days + 1
    return ('<div class="cal" role="img" aria-label="%s">'
            '<div class="cal-mois" style="--w:%d">%s</div>'
            '<div class="cal-grille" style="--w:%d">%s</div>'
            '<p class="cal-note"><i class="cal-d is-on"></i> %s · <i class="cal-d"></i> %s — %s</p></div>' % (
                esc(strings_lang["calTitre"]), len(semaines), "".join(mois), len(semaines), "".join(semaines),
                esc(strings_lang["calLegendOn"]), esc(strings_lang["calAucun"]),
                esc(interp(strings_lang["calBilan"], {"n": fmt(total, lang), "m": fmt(possibles, lang)}))))


def national_spark_svg(sitreps):
    """Courbe du cumul national de cas depuis le premier bulletin (tuile du bento)."""
    pts = [(s["date"], s["confirmed"]) for s in sitreps if s.get("confirmed") is not None]
    if len(pts) < 2:
        return ""
    d0 = date.fromisoformat(pts[0][0]); span = max((date.fromisoformat(pts[-1][0]) - d0).days, 1)
    top = max(v for _, v in pts) or 1
    trace = "M" + " L".join("%.1f,%.1f" % ((date.fromisoformat(d) - d0).days / span * 300, 86 - v / top * 80) for d, v in pts)
    return ('<svg class="bt-spark" viewBox="0 0 300 90" preserveAspectRatio="none" aria-hidden="true">'
            '<defs><linearGradient id="btg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#267294" stop-opacity=".35"/>'
            '<stop offset="1" stop-color="#267294" stop-opacity="0"/></linearGradient></defs>'
            '<path d="%s L300,90 L0,90 Z" fill="url(#btg)"/>'
            '<path d="%s" fill="none" stroke="#015174" stroke-width="2.4" vector-effect="non-scaling-stroke" stroke-linejoin="round"/></svg>' % (trace, trace))



def province_mini_map(geo_map, province_name, health_zones, config, aliases):
    """Miniature d'une province pour les cartes de l'accueil : la silhouette de
    la province (ses seules zones de sante, cadrees au plus pres), chaque zone
    avec sa frontiere et coloree par le meme palier que la carte principale.
    Les zones sans cas restent grises ; les voisines ne sont pas dessinees."""
    if not geo_map:
        return ""
    thresholds = config["cartogram"]["zoneThresholds"]

    def key_of(name):
        base = normalise_zone(name)
        return aliases.get(base, base)

    by_key = {}
    for zone in health_zones:
        by_key.setdefault(key_of(zone["name"]), []).append(zone)

    def level(cases):
        if not cases:
            return 0
        for index, limit in enumerate(thresholds):
            if cases < limit:
                return index + 1
        return len(thresholds) + 1

    paths, xs, ys = [], [], []
    for zone in geo_map["zones"]:
        if not zone["inside"]:
            continue
        same = [c for c in by_key.get(zone["key"], [])
                if normalise_zone(c.get("province")) == normalise_zone(province_name)]
        ours = same[0] if same else {}
        cases = ours.get("cases") or 0
        nombres = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", zone["d"])]
        xs.extend(nombres[0::2]); ys.extend(nombres[1::2])
        # Nom et chiffres de la zone (5 octobre 2026) : l'en-tete des pages
        # province affiche une infobulle au survol de sa carte.
        paths.append('<path class="is-%d" data-zone="%s" data-cas="%d" data-deces="%d" d="%s"/>'
                     % (level(cases), esc(zone.get("name", "")), cases, ours.get("deaths") or 0, zone["d"]))
    if not paths:
        return ""
    marge = 0.04 * max(max(xs) - min(xs), max(ys) - min(ys))
    box = "%.1f %.1f %.1f %.1f" % (min(xs) - marge, min(ys) - marge,
                                   max(xs) - min(xs) + 2 * marge, max(ys) - min(ys) + 2 * marge)
    return ('        <svg class="pcol-map" viewBox="%s" preserveAspectRatio="xMidYMid meet" aria-hidden="true">'
            '%s</svg>\n' % (box, "".join(paths)))


def pays_hero_map(geo, health_zones, config):
    """La RDC entiere pour l'en-tete d'« Ensemble du pays » (6 octobre 2026),
    sur le modele de province_mini_map : les 519 zones, coloriees par palier,
    nom et chiffres sur les zones touchees pour l'infobulle au survol."""
    thresholds = config["cartogram"]["zoneThresholds"]
    aliases = geo.get("aliases", {})

    def key_of(name):
        base = normalise_zone(name)
        return aliases.get(base, base)

    by_key = {}
    for zone in health_zones:
        by_key.setdefault(key_of(zone["name"]), []).append(zone)
    compte = {}
    for zone in geo["zones"]:
        compte[zone["key"]] = compte.get(zone["key"], 0) + 1

    def level(cases):
        if not cases:
            return 0
        for index, limit in enumerate(thresholds):
            if cases < limit:
                return index + 1
        return len(thresholds) + 1

    paths = []
    for zone in geo["zones"]:
        candidats = by_key.get(zone["key"], [])
        meme = [c for c in candidats
                if normalise_zone(c.get("province")) == normalise_zone(zone["province"])]
        ours = meme[0] if meme else (candidats[0] if len(candidats) == 1 and compte[zone["key"]] == 1 else None)
        if not ours:
            paths.append('<path d="%s"/>' % zone["d"])
            continue
        cases = ours.get("cases") or 0
        paths.append('<path class="is-%d" data-zone="%s" data-cas="%d" data-deces="%d" d="%s"/>'
                     % (level(cases), esc(zone.get("name", "")), cases, ours.get("deaths") or 0, zone["d"]))
    return ('        <svg class="pcol-map" viewBox="%s" preserveAspectRatio="xMidYMid meet" aria-hidden="true">'
            '%s</svg>\n' % (geo["viewBox"], "".join(paths)))


def province_cards_html(provinces, urls, lang, strings_lang, history=None,
                        maps=None, health_zones=(), config=None, aliases=None):
    """Une colonne par province, coiffee d'un filet dans sa teinte d'identite.

    LA COULEUR EST DANS LE FILET, JAMAIS DANS LE TEXTE. Le nom du Nord-Kivu
    ecrit dans son ambre tombe a 3,9 de contraste quand le site s'impose 4,5 —
    et c'est deja la regle ailleurs : le chiffre porte l'encre, la pastille ou
    le trait a cote porte l'identite.

    Ce qui a remplace les cartes bordees a gauche (22 septembre 2026) : trois
    paires libelle/valeur en capitales dans une boite, c'etait le gabarit qu'on
    voit partout — « ca fait beaucoup trop IA », meme reproche que la police
    des chiffres du panneau de la carte le 10 septembre. La letalite est
    tombee au passage : a cet endroit la question est ou est l'epidemie, pas
    comment elle tue ; elle reste sur chaque page province. Six variantes
    montrees en local avant celle-ci.

    Le compte de deces s'ecrit en toutes lettres sous le chiffre des cas —
    plus aucun libelle en capitales : c'est le mot qui porte l'unite.
    """
    cards = []
    # Echelle commune a toutes les provinces (decision du 2 octobre 2026) : une
    # courbe a sa propre echelle ferait monter le Sud-Kivu (3 cas) aussi fort
    # que l'Ituri.
    top_commun = max([v for pr in provinces for _, v in province_series(history or [], pr["name"])] or [1]) or 1
    for province in sorted(provinces, key=lambda p: -(p.get("confirmed") or 0)):
        deces = province.get("deaths")
        # Refonte du 2 octobre 2026 : une courbe du cumul sous le chiffre, tiree
        # de province-history.json (depuis le 14 mai, chaque courbe a sa propre
        # echelle : elle dit la forme, pas le volume).
        spark = ""
        pts = [(d, v) for d, v in province_series(history or [], province["name"]) if d >= "2026-05-14"]
        mini = province_mini_map((maps or {}).get(province["name"]), province["name"],
                                 health_zones, config, aliases or {}) if maps and config else ""
        if mini:
            spark = mini
        elif len(pts) > 1:
            d0 = date.fromisoformat(pts[0][0]); span = max((date.fromisoformat(pts[-1][0]) - d0).days, 1)
            top = top_commun
            trace = "M" + " L".join("%.1f,%.1f" % ((date.fromisoformat(d) - d0).days / span * 200, 56 - v / top * 50)
                                    for d, v in pts)
            spark = ('        <svg class="pcol-spark" viewBox="0 0 200 60" preserveAspectRatio="none" aria-hidden="true">'
                     '<path d="%s L200,60 L0,60 Z" fill="var(--teinte)" opacity=".12"/>'
                     '<path d="%s" fill="none" stroke="var(--teinte)" stroke-width="2" '
                     'vector-effect="non-scaling-stroke" stroke-linejoin="round"/></svg>\n' % (trace, trace))
        cards.append((
            '      <a class="province-col" href="%s" style="--teinte:%s;">\n'
            '        <span class="pcol-nom">%s</span>\n'
            '        <span class="pcol-cas">%s</span>\n'
            + spark.replace("%", "%%") +
            '        <span class="pcol-deces">%s</span>\n'
            "      </a>") % (
                urls.province_path(province["name"], lang),
                PROVINCE_COLORS.get(province["name"], "var(--ink-faint)"),
                esc(province["name"]),
                fmt(province.get("confirmed"), lang),
                esc(interp(strings_lang["provincesCardDeathsInline"],
                           {"n": fmt(deces, lang)}))))
    return "\n".join(cards)


def province_mosaique_html(provinces, urls, lang, strings_lang, maps=None, health_zones=(),
                           config=None, aliases=None):
    """Les provinces de l'accueil en MOSAIQUE (5 octobre 2026, option B de la
    maquette tmp/proto-provinces-accueil) : des cases dont la taille suit le
    poids de la province. La premiere (l'Ituri) est grande, avec ses chiffres
    detailles ; la deuxieme est large ; les deux suivantes sont moyennes ; le
    reste tient en bandeau de petites cases. Les rangees tombent juste : grille
    de 12 colonnes, 262 + 262 px puis 92 px (voir site.css, .pm).

    Prevue pour sept provinces (1 grande, 1 large, 2 moyennes, 3 petites) ; avec
    un autre nombre, les petites se partagent la largeur (12 / n colonnes, a
    defaut trois)."""
    rangees = sorted(provinces, key=lambda p: -(p.get("confirmed") or 0))
    total = sum((p.get("confirmed") or 0) for p in rangees) or 1
    nb_petites = max(0, len(rangees) - 4)
    span_petite = 12 // nb_petites if nb_petites and 12 % nb_petites == 0 else 4
    out = []
    for i, pr in enumerate(rangees):
        nom = pr["name"]
        cas, deces = pr.get("confirmed") or 0, pr.get("deaths") or 0
        mini = province_mini_map((maps or {}).get(nom), nom, health_zones, config, aliases or {}) if maps and config else ""
        cls = ["is-grande", "is-large", "is-moy", "is-moy"][i] if i < 4 else "is-petite"
        style = "--teinte:%s;" % PROVINCE_COLORS.get(nom, "var(--ink-faint)")
        if cls == "is-petite":
            style += "grid-column:span %d;" % span_petite
        # La grande case ne garde que les deces en petit, comme les autres
        # (7 octobre 2026, demande de Fable) : letalite, part du pays et
        # nouveaux cas retires. Branche gardee mais eteinte.
        if False and cls == "is-grande":
            cfr = pr.get("cfr") if pr.get("cfr") is not None else (deces / cas * 100 if cas else 0)
            bas = ('<span class="pm-stats">'
                   '<span><b>%s</b>%s</span><span><b>%s</b>%s</span><span><b>%s</b>%s</span><span><b>+%s</b>%s</span></span>'
                   % (fmt(deces, lang), esc(strings_lang["provStatDeaths"]),
                      fmt_cfr(cfr, lang), esc(strings_lang["provStatCfr"]),
                      fmt_cfr(cas / total * 100, lang), esc(strings_lang["provStatShare"]),
                      fmt(pr.get("newCases24h") or 0, lang), esc(strings_lang["provStatNew"])))
        else:
            bas = '<span class="pm-dec">%s</span>' % esc(interp(strings_lang["provincesCardDeathsInline"], {"n": fmt(deces, lang)}))
        out.append('      <a class="pm-t %s" href="%s" style="%s">\n'
                   '        <span class="pm-nom">%s</span>\n        <span class="pm-cas">%s</span>\n'
                   '%s\n        %s\n      </a>'
                   % (cls, urls.province_path(nom, lang), style, esc(nom), fmt(cas, lang), mini, bas))
    return "\n".join(out)


def province_liste_html(provinces, urls, lang, strings_lang):
    """Les provinces de l'accueil en LISTE COMPACTE, pour le telephone (8 octobre
    2026) : la mosaique y prenait ~1 100 px pour sept nombres, ses mini-cartes
    repetant la grande carte juste au-dessus. Une ligne par province : pastille,
    nom, cas ; dessous une barre de sa part des cas du pays, et les deces. Le CSS
    montre cette liste sous 761 px et la mosaique au-dessus."""
    rangees = sorted(provinces, key=lambda p: -(p.get("confirmed") or 0))
    total = sum((p.get("confirmed") or 0) for p in rangees) or 1
    out = []
    for pr in rangees:
        nom = pr["name"]
        cas, deces = pr.get("confirmed") or 0, pr.get("deaths") or 0
        out.append('      <a class="pl-l" href="%s" style="--teinte:%s;--part:%.2f%%">'
                   '<span class="pl-nom">%s</span><span class="pl-cas">%s</span>'
                   '<span class="pl-barre" aria-hidden="true"><i></i></span>'
                   '<span class="pl-dec">%s</span></a>'
                   % (urls.province_path(nom, lang), PROVINCE_COLORS.get(nom, "var(--ink-faint)"),
                      cas / total * 100, esc(nom), fmt(cas, lang),
                      esc(interp(strings_lang["provincesCardDeathsInline"], {"n": fmt(deces, lang)}))))
    return "\n".join(out)


def province_table_rows_html(provinces, urls, lang):
    rows = []
    for province in sorted(provinces, key=lambda p: -(p.get("confirmed") or 0)):
        zones = province.get("healthZonesAffected")
        zones_text = "%s / %s" % (zones["n"], zones["total"]) if zones else "—"
        rows.append(
            "            <tr>\n"
            '              <td><div class="zone-name-cell">'
            '<span class="zdot" style="background:%s;"></span>'
            '<a href="%s">%s</a></div></td>\n'
            "              <td>%s</td>\n"
            "              <td>%s</td>\n"
            '              <td><span class="zone-badge %s">%s</span></td>\n'
            "              <td>%s</td>\n"
            "            </tr>" % (
                PROVINCE_COLORS.get(province["name"], "var(--ink-faint)"),
                urls.province_path(province["name"], lang), esc(province["name"]),
                fmt(province.get("confirmed"), lang),
                fmt(province.get("deaths"), lang),
                cfr_badge_class(province.get("cfr")), fmt_cfr(province.get("cfr"), lang),
                zones_text))
    return "\n".join(rows)


DOWNLOAD_ICON = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M14 3h7v7"/><path d="M10 14 21 3"/>'
    '<path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5"/></svg>')


def registre_ligne(numero, date_text, chiffres, href, title, label, month=None,
                   search=None, variant="", kicker=""):
    """Une ligne du registre des bulletins (6 octobre 2026, option 1 du
    proprietaire : « les cases font trop IA »). Garde la classe report-chip,
    sur laquelle reposent le filtre par mois et la recherche d'app.js, qui
    produit le meme balisage (registreLigne) : toute retouche des deux cotes.
    kicker : le mot ecrit en petit devant le numero (« SitRep », 9 octobre
    2026, pour que chaque ligne porte le nom du document)."""
    data = ""
    if month is not None:
        data += ' data-month="%s"' % esc(month)
    if search is not None:
        data += ' data-search="%s"' % esc(search.lower())
    return ('        <a class="report-chip rg-l%s" href="%s" target="_blank" rel="noopener"%s title="%s" aria-label="%s">'
            '<span class="rg-n">%s%s</span><span class="rg-d">%s</span><span class="rg-c">%s</span>'
            '<span class="rg-p" aria-hidden="true">PDF</span></a>'
            % ((" " + variant) if variant else "", esc(href), data, esc(title), esc(label),
               ('<small class="rg-k">%s</small>' % esc(kicker)) if kicker else "",
               esc(numero), esc(date_text), esc(chiffres)))


def report_chip(label, date_text, href, title, month=None, search=None,
                variant=""):
    """Une carte de bulletin, cliquable dans son entier.

    Auparavant seule la petite icone etait un lien : la cible etait minuscule
    et la carte paraissait inerte. Les attributs month et search reprennent
    ceux que pose app.js, pour que le filtre et la recherche s'appliquent aussi
    au HTML pre-genere.
    """
    data = ""
    if month is not None:
        data += ' data-month="%s"' % esc(month)
    if search is not None:
        data += ' data-search="%s"' % esc(search.lower())
    return (
        '        <a class="report-chip%s" href="%s" target="_blank" rel="noopener"%s '
        'title="%s">\n'
        '          <span class="rc-head">\n'
        '            <span class="rc-label">%s</span>\n'
        '            <span class="rc-dl" aria-hidden="true">%s</span>\n'
        "          </span>\n"
        '          <span class="rc-date">%s</span>\n'
        "        </a>" % (
            (" " + variant) if variant else "", esc(href), data, esc(title),
            esc(label), DOWNLOAD_ICON, date_text))


def situation_html(situation, date_long):
    """« Situation au 25 août 2026 », le prefixe dans un span que le telephone
    masque : sur une ligne par bulletin, sous un en-tete de mois, « Situation
    au » ne dit plus rien. Decoupe autour de {date} pour valoir dans les trois
    langues, quel que soit l'ordre des mots. Renvoie du HTML deja echappe —
    report_chip ne re-echappe pas date_text."""
    pre, _, post = situation.partition("{date}")
    return '<span class="rc-date-prefix">%s</span>%s%s' % (esc(pre), esc(date_long), esc(post))


def ages_papillon_html(demographie, lang, strings_lang):
    """Les ages en papillon (6 octobre 2026, option 3 de la page Le virus) :
    part des cas a gauche, part des deces a droite, tranche au milieu. Meme
    echelle des deux cotes, pour la meme raison que ages_rows_html."""
    tranches = demographie["tranches"]
    if not tranches:
        return ""
    plafond = max(max(t["partCas"], t["partDeces"]) for t in tranches) or 1
    lignes = []
    for t in tranches:
        libelle = t["tranche"]
        libelle = ("%s %s" % (libelle.replace("-", "–"), strings_lang["virusAgesUnit"])) \
            if re.match(r'^\d+-\d+$', libelle) else strings_lang["virusAgesOpenEnded"]
        lignes.append('<div class="pa-l"><div class="pa-g"><span>%s</span><i style="width:%.1f%%"></i></div>'
                      '<div class="pa-c">%s</div><div class="pa-d"><i style="width:%.1f%%"></i><span>%s</span></div></div>'
                      % (fmt_cfr(t["partCas"], lang), t["partCas"] / plafond * 100, esc(libelle),
                         t["partDeces"] / plafond * 100, fmt_cfr(t["partDeces"], lang)))
    return '<div class="pa">%s</div>' % "".join(lignes)


def ages_rows_html(demographie, lang, strings_lang):
    """Barres appariees : part des cas et part des deces, par tranche d'age.

    Deux parts et non deux taux. Un taux de letalite par age serait calcule sur
    un numerateur qui ne voit que 61 % des deces et un denominateur qui en voit
    85 % des cas : il sortirait systematiquement trop bas, et contredirait la
    letalite affichee ailleurs sur le site. La comparaison des parts, elle, se
    fait a l'interieur du meme echantillon.
    """
    tranches = demographie["tranches"]
    if not tranches:
        return ""
    # Echelle commune aux deux series, sinon l'ecart qu'on veut montrer
    # dependrait de la serie et non des donnees.
    plafond = max(max(t["partCas"], t["partDeces"]) for t in tranches) or 1
    unite = strings_lang["virusAgesUnit"]
    lignes = []
    for t in tranches:
        libelle = t["tranche"]
        # L'unite ne se suffixe qu'aux intervalles chiffres : « 50 et plus »
        # se termine deja par un mot, et donnait « 50 et plus ans ».
        if re.match(r'^\d+-\d+$', libelle):
            libelle = "%s %s" % (libelle.replace("-", "–"), unite)
        else:
            # La derniere tranche est ouverte et redigee en toutes lettres dans
            # la source ; elle doit donc etre traduite, pas suffixee.
            libelle = strings_lang["virusAgesOpenEnded"]
        barres = []
        for cle_part, cle_n, classe, intitule in (
                ("partCas", "cas", "is-cas", strings_lang["virusAgesCases"]),
                ("partDeces", "deces", "is-deces", strings_lang["virusAgesDeaths"])):
            part = t[cle_part]
            barres.append(
                '          <div class="age-bar %s">\n'
                '            <span class="age-track"><span class="age-fill" '
                'style="width:%.1f%%"></span></span>\n'
                '            <span class="age-val">%s&nbsp;%%</span>\n'
                '            <span class="visually-hidden">%s : %s</span>\n'
                '          </div>'
                % (classe, 100.0 * part / plafond,
                   esc(fmt_pct(part, lang)), esc(intitule),
                   esc(fmt(t[cle_n], lang))))
        lignes.append(
            '        <div class="age-row">\n'
            '          <div class="age-label">%s</div>\n%s\n'
            '        </div>' % (esc(libelle), "\n".join(barres)))
    return "\n".join(lignes)


def fmt_pct(valeur, lang):
    return ("%.1f" % valeur).replace(".", loc(lang, "decimal"))


def genomes_seeds(genomes, lang, strings_lang, i18n_lang):
    """Le bloc « genomes » de la page Le virus : trois chiffres, les mois, les
    zones. Comptes agreges lus dans Pathoplexus (data/genomes.json, produit a
    la main par scripts/extraire_genomes.py) — un chiffre de contexte, pas de
    suivi, d'ou la date de consultation ecrite dans la note.

    Les barres reprennent l'idiome mb-bar de la page Flux (une barre par zone,
    valeur a droite) ; les mois sont des colonnes, parce qu'un mois se lit
    dans le temps et une zone dans une liste.
    """
    if not genomes:
        return {}
    zones = genomes["parZone"]
    total = genomes["rdc2026"]
    deux = sum(r["n"] for r in zones if r["zone"] in ("Bunia", "Rwampara"))
    maxi = max(r["n"] for r in zones) if zones else 1
    # Douze lignes suffisent : au-dela, les barres font deux pixels et la queue
    # de la liste tient en une phrase. Les six premieres portent 90 % du total.
    tetes, queue = zones[:12], zones[12:]
    barres = []
    for r in tetes:
        barres.append('<div class="mb-bar"><div class="mb-bar-label">%s <span class="vg-prov">%s</span></div>'
                      '<div class="mb-bar-track"><div class="mb-bar-fill" style="width:%.1f%%"></div></div>'
                      '<div class="mb-bar-val">%s</div></div>'
                      % (esc(r["zone"]), esc(r.get("province") or ""), r["n"] / maxi * 100, fmt(r["n"], lang)))
    reste = ""
    if queue:
        reste = interp(strings_lang["virusGenomesReste"], {
            "n": fmt(len(queue), lang),
            "min": fmt(min(r["n"] for r in queue), lang),
            "max": fmt(max(r["n"] for r in queue), lang)})
    mois = [m for m in genomes["parMois"] if m["mois"] >= "2026-05"]
    maxm = max(m["n"] for m in mois) if mois else 1
    cols = []
    for m in mois:
        cols.append('<div class="vg-col"><div class="vg-n">%s</div><div class="vg-track"><div class="vg-fill" style="height:%.1f%%"></div></div>'
                    '<div class="vg-lab">%s</div></div>'
                    % (fmt(m["n"], lang), m["n"] / maxm * 100, esc(i18n_lang["months"][int(m["mois"][5:7]) - 1])))
    autres = sum(genomes.get("autresLieux", {}).values())
    return {
        "seed.genomesSeq": fmt(total, lang),
        "seed.genomesZones": fmt(len(zones), lang),
        "seed.genomesPart": fmt_pct(100.0 * deux / total, lang) + loc(lang, "percent") if total else "",
        "seed.genomesBarres": '<div class="mb-bars vg-bars">%s</div>%s' % (
            "".join(barres), ('<p class="vg-reste">%s</p>' % esc(reste)) if reste else ""),
        "seed.genomesMois": '<div class="vg-mois">%s</div>' % "".join(cols),
        "seed.genomesAutres": interp(strings_lang["virusGenomesOther"], {
            "n": fmt(autres, lang), "m": fmt(genomes.get("nonPrecise", 0), lang)}),
        "seed.genomesNote": interp(strings_lang["virusGenomesNote"], {
            "date": long_date(genomes["consulte"], i18n_lang),
            "ouganda": fmt(genomes.get("parPays2026", {}).get("Uganda", 0), lang),
            "ouvert": fmt(genomes.get("termes", {}).get("OPEN", 0), lang),
            "restreint": fmt(genomes.get("termes", {}).get("RESTRICTED", 0), lang)}),
    }


def sex_rows_html(demographie, lang, strings_lang):
    """Deux barres empilees a 100 % : repartition femmes/hommes des cas, puis
    des deces.

    Un camembert aurait ete plus familier, mais l'ecart a montrer est de 3,3
    points — 12 degres d'arc, invisibles, et illisibles d'un cercle a l'autre.
    Empilees l'une sous l'autre, les deux barres partagent une base et une
    echelle : le decalage se lit au decrochage de la frontiere entre les deux
    couleurs.

    Les deux teintes sont deux paliers de l'echelle bleue du site plutot que
    deux couleurs neuves — le vocabulaire chromatique reste celui du site, et
    aucune des deux ne suggere une valeur. Le couple passe les controles de
    separation (ΔE 15,3 en deuteranopie) et de contraste.
    """
    par_sexe = (demographie or {}).get("parSexe")
    if not par_sexe:
        return ""
    lignes = []
    for cle, intitule in (("cas", strings_lang["virusSexCases"]),
                          ("deces", strings_lang["virusSexDeaths"])):
        bloc = par_sexe[cle]
        segments = []
        for sexe, classe, libelle in (
                ("Feminin", "is-f", strings_lang["virusSexFemale"]),
                ("Masculin", "is-h", strings_lang["virusSexMale"])):
            part = bloc["part" + sexe]
            segments.append(
                '            <span class="sx-seg %s" style="width:%.1f%%">'
                '<span class="sx-pct">%s&nbsp;%%</span>'
                '<span class="visually-hidden"> %s, %s</span></span>'
                % (classe, part, esc(fmt_pct(part, lang)), esc(libelle),
                   esc(fmt(bloc[sexe.lower()], lang))))
        lignes.append(
            '        <div class="sex-row">\n'
            '          <div class="sex-label">%s</div>\n'
            '          <div class="sex-bar">\n%s\n          </div>\n'
            '        </div>' % (esc(intitule), "\n".join(segments)))
    return "\n".join(lignes)


def reports_list_html(reports, lang, i18n_lang, strings_lang):
    """Version écrite en dur de la liste des SitRep, groupée par mois.

    Le JavaScript la réécrit avec les mêmes données dès qu'il s'exécute ; elle
    existe pour que l'archive — et les liens vers les PDF — soient visibles
    sans JavaScript, donc indexables.
    """
    groups, order = {}, []
    for report in sorted(reports, key=lambda r: r.get("sitrepNumber") or "", reverse=True):
        reporting = report.get("reportingDate")
        if reporting:
            # Meme cle que celle calculee par app.js (annee-indice du mois),
            # pour que le HTML pre-genere et le rendu JavaScript concordent.
            key = "%d-%d" % (int(reporting[:4]), int(reporting[5:7]) - 1)
            label = "%s %s" % (i18n_lang["months"][int(reporting[5:7]) - 1], reporting[:4])
        else:
            key, label = "unknown", i18n_lang["reportsUnknownDate"]
        if key not in groups:
            groups[key] = {"label": label, "reports": []}
            order.append(key)
        groups[key]["reports"].append(report)

    prefix = "SitRep INSP N°"
    situation = strings_lang["reportSituation"]
    parts = []
    for key in order:
        group = groups[key]
        parts.append('        <div class="reports-month-header" data-month-key="%s">%s</div>'
                     % (esc(key), esc(group["label"])))
        for report in group["reports"]:
            reporting = report.get("reportingDate")
            when = situation_html(situation, long_date(reporting, i18n_lang)) \
                if reporting else esc(i18n_lang["reportsUnknownDate"])
            searchable = "%s %s %s" % (report.get("sitrepNumber", ""),
                                       group["label"], reporting or "")
            chiffres = interp(strings_lang["reportsCasDeces"], {
                "c": fmt(report["confirmed"], lang), "d": fmt(report.get("deaths"), lang)}) \
                if report.get("confirmed") is not None and report.get("deaths") is not None else ""
            parts.append(registre_ligne(str(report.get("sitrepNumber", "")),
                                        long_date(reporting, i18n_lang) if reporting
                                        else i18n_lang["reportsUnknownDate"], chiffres,
                                        "/" + report["file"].lstrip("/"),
                                        "%s%s — %s" % (prefix, report.get("sitrepNumber", ""),
                                                       i18n_lang["reportsDownload"]),
                                        prefix + str(report.get("sitrepNumber", "")),
                                        month=key, search=searchable, kicker="SitRep"))
    return "\n".join(parts)


def reports_manquants_html(reports, lang, strings_lang):
    """Note sous le registre des SitRep (7 octobre 2026) : les numeros que
    l'INSP n'a jamais mis en ligne, calcules a chaque generation — du n°1 au
    plus recent, ceux qu'aucun bulletin archive ne porte."""
    nums = sorted(int(r["sitrepNumber"]) for r in reports if str(r.get("sitrepNumber", "")).isdigit())
    if not nums:
        return ""
    manquants = sorted(set(range(1, nums[-1] + 1)) - set(nums))
    if not manquants:
        return ""
    et = {"fr": " et ", "en": " and ", "sw": " na "}.get(lang, " and ")
    liste = ["%03d" % n for n in manquants]
    liste = ", ".join(liste[:-1]) + et + liste[-1] if len(liste) > 1 else liste[0]
    return '<p class="reports-manquants">%s</p>' % esc(interp(strings_lang["reportsManquants"], {"liste": liste}))


def who_reports_list_html(who_reports, lang, i18n_lang, strings_lang):
    label = strings_lang["whoReportLabel"]
    situation = strings_lang["reportSituation"]
    parts = []
    for report in sorted(who_reports, key=lambda r: r.get("number") or "", reverse=True):
        when = situation_html(situation, long_date(report.get("date"), i18n_lang)) \
            if report.get("date") else esc(i18n_lang["reportsUnknownDate"])
        parts.append(registre_ligne("n°" + str(report.get("number", "")),
                                    long_date(report.get("date"), i18n_lang) if report.get("date")
                                    else i18n_lang["reportsUnknownDate"],
                                    strings_lang["reportsWhoWeekly"],
                                    "/" + report["file"].lstrip("/"), i18n_lang["reportsDownload"],
                                    interp(label, {"n": report.get("number", "")}), variant="is-who"))
    return "\n".join(parts)


def social_updates_list_html(updates, lang, i18n_lang, strings_lang):
    situation = strings_lang["reportSituation"]
    parts = []
    for update in sorted(updates, key=lambda u: u.get("date") or "", reverse=True):
        parts.append(report_chip(
            i18n_lang["socialUpdatesLabel"],
            situation_html(situation, long_date(update.get("date"), i18n_lang)),
            update.get("url", "#"), i18n_lang["socialUpdatesOpenLink"],
            variant="is-social"))
    return "\n".join(parts)


def province_arrival_events(config, arrivals, strings_lang, lang, i18n_lang,
                            urls=None):
    """Date a laquelle l'epidemie gagne chaque province, telle que les bulletins
    l'annoncent — et non telle qu'un calcul la devinerait.

    Ces dates etaient auparavant derivees de data/province-history.json, en
    prenant la premiere date ou une province y apparaissait avec un cumul non
    nul. Ce calcul ne pouvait pas etre juste : ce fichier ne dit pas quand une
    province a eu son premier cas, il dit quand elle a obtenu sa propre ligne
    dans le tableau. Trois dates sur cinq etaient fausses — le Sud-Kivu de dix
    jours, la Tshopo de dix, le Haut-Uele de quinze.

    L'ecart n'est pas un defaut d'extraction, c'est une convention de
    surveillance que les bulletins enoncent noir sur blanc : « Les cas importes
    a Wamba (Province de Haut Uele) sont comptabilises a Niania et ont ete
    retournes a Niania » (SitRep 046). Les premiers malades du Haut-Uele et de
    la Tshopo venaient de la zone de Nia-Nia et y restaient comptes ; leurs
    provinces n'ont recu de ligne que le 10 juillet, marquee d'un asterisque
    « Non comptabilise car deja inclus dans les cas de la Zone de Sante de
    Niania ».

    D'ou la regle suivie ici, qui vaut au-dela de ce cas : les dates dans la
    prose, les nombres dans les tableaux. Une chronologie peut dire que le
    virus a atteint le Haut-Uele le 25 juin, parce que c'est une affirmation
    narrative sourcee a une phrase de bulletin et qu'elle n'a besoin de
    s'additionner avec rien. Les cartes et les graphiques, eux, restent sur les
    tableaux officiels — aucun cas n'est deplace d'une province a l'autre.

    Les dates vivent donc dans site/strings.json, sous « provinceArrivals »,
    chacune avec le numero du bulletin qui l'etablit. L'Ituri n'y figure pas :
    son arrivee, c'est la declaration de l'epidemie, deja dans la chronologie.
    """
    events = []
    for arrival in arrivals:
        # L'Ituri porte « timeline: false » : son arrivee, c'est l'epidemie
        # elle-meme, deja racontee par les jalons rediges du 24 avril et du
        # 15 mai. Sa fiche sert en revanche a sa page province.
        if arrival.get("timeline") is False:
            continue
        name = arrival["province"]
        forms = province_forms(config, name, lang)
        events.append({
            "date": arrival["date"],
            "kind": "spread",
            "title": interp(strings_lang["timelineSpreadTitle"], forms),
            "text": esc(arrival[lang]),
            "source": None,
            "province": name,
        })
    return events


ZONE_MILESTONES = (10, 20, 30, 40, 50, 75, 100)


def _edit_distance(a, b):
    """Distance de Levenshtein, pour rapprocher « Gety » de « Gethy »."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def zone_list_text(arrivals, strings_lang):
    """« Aungba, Damas et Lita (Ituri) et Beni (Nord-Kivu) » — les zones
    groupees par province, dans l'ordre d'apparition des provinces."""
    et = strings_lang["timelineListAnd"]

    def join(items):
        return items[0] if len(items) == 1 else ", ".join(items[:-1]) + et + items[-1]

    groups = []
    for name, province in arrivals:
        for group in groups:
            if group[0] == province:
                group[1].append(name)
                break
        else:
            groups.append((province, [name]))
    return join(["%s (%s)" % (join(sorted(names)), province) for province, names in groups])


def zone_milestone_events(zones_history, geo, strings_lang, lang, health_zones=()):
    """Jalons de propagation : la 10e, 20e… zone de sante touchee.

    Le compte est celui des zones distinctes ayant declare au moins un cas
    confirme dans un bulletin, cumule dans l'ordre des instantanes de
    zones-history.json — une zone touchee le reste, meme si un bulletin
    ulterieur cesse de la citer ou la ramene a zero (Bambu, fin mai). C'est le
    sens de « zones touchees » dans les bulletins eux-memes.

    Une entree par seuil franchi, jamais une par zone : soixante arrivees
    noieraient les jalons rediges. Le texte nomme les zones arrivees le jour
    du franchissement, groupees par province.

    Deux pieges evites : une meme zone ecrite de deux facons (« Gety » le
    29 mai, « Gethy » le 9 aout ; « Makiso-Kisangani » avec une double
    espace) est rapprochee du fond de carte, cle exacte d'abord, puis a deux
    caracteres pres DANS LA MEME PROVINCE — Aru et Adi, voisines a deux
    lettres, existent toutes deux et gardent chacune leur cle exacte. Et le
    premier bulletin a detailler les zones en liste dix d'un coup : ce ne
    sont pas des arrivees du jour, le texte le dit autrement."""
    entries = zones_history if isinstance(zones_history, list) else (
        zones_history.get("entries") or zones_history.get("history") or [])
    entries = sorted([e for e in entries if e.get("date")], key=lambda e: e["date"])
    aliases = geo.get("aliases", {})
    geo_keys = {}
    for zone in geo["zones"]:
        geo_keys.setdefault(normalise_zone(zone["province"]), set()).add(zone["key"])

    def identity(name, province):
        base = normalise_zone(name)
        key = aliases.get(base, base)
        prov = normalise_zone(province)
        known = geo_keys.get(prov, set())
        if key in known:
            return (prov, key)
        # A deux caracteres pres, le PLUS proche s'il est seul a cette
        # distance : « gety » est a 1 de « gethy » et a 2 de « geti », deux
        # zones distinctes de l'Ituri — la plus proche gagne.
        close = sorted((_edit_distance(k, key), k) for k in known
                       if abs(len(k) - len(key)) <= 2 and _edit_distance(k, key) <= 2)
        if close and (len(close) == 1 or close[0][0] < close[1][0]):
            return (prov, close[0][1])
        return (prov, key)

    # Le nom affiche est celui du dernier bulletin quand la zone y figure
    # encore — « Nia-Nia » comme dans les tableaux du site, plutot que le
    # « Nia Nia » ou le « BAMBU » de la premiere mention.
    current_name = {identity(z["name"], z.get("province", "")): z["name"]
                    for z in health_zones}

    seen = set()
    reached = set()
    first_date = None
    events = []
    for entry in entries:
        arrivals = []
        for zone in entry.get("zones", []):
            if not (zone.get("cases") or 0) > 0:
                continue
            ident = identity(zone["name"], zone.get("province", ""))
            if ident in seen:
                continue
            seen.add(ident)
            name = current_name.get(ident) or (
                zone["name"].title() if zone["name"].isupper() else zone["name"])
            arrivals.append((name, zone.get("province", "")))
        if not arrivals:
            continue
        if first_date is None:
            first_date = entry["date"]
        total = len(seen)
        crossed = [s for s in ZONE_MILESTONES if total >= s and s not in reached]
        if not crossed:
            continue
        reached.update(crossed)
        text_key = ("timelineMilestoneZonesFirstText" if entry["date"] == first_date
                    else "timelineMilestoneZonesText")
        events.append({
            "date": entry["date"], "kind": "spread",
            "title": interp(strings_lang["timelineMilestoneZonesTitle"],
                            {"n": fmt(max(crossed), lang)}),
            "text": esc(interp(strings_lang[text_key], {
                "n": fmt(total, lang),
                "zones": zone_list_text(arrivals, strings_lang)})),
            "source": entry["date"],
        })
    return events


def timeline_events(strings, sitreps, lang, i18n_lang, config=None, urls=None,
                    zones_history=None, geo=None, latest_zones=None):
    """Chronologie : jalons rédigés + seuils franchis, calculés sur l'archive."""
    events = []
    for event in strings["timelineEvents"]:
        events.append({
            "date": event["date"],
            # Toutes les entrees redigees sont des jalons officiels : la
            # distinction critique/default de site/strings.json ne sert plus
            # qu'a marquer les plus lourdes.
            # Les jalons hors de RDC (Ouganda, France, Kenya ; 7 octobre 2026,
            # demande de Fable) ont leur propre couleur, « International ».
            "kind": "intl" if event.get("intl") else "official",
            "weight": event["kind"],
            "title": event[lang]["title"],
            "text": event[lang]["text"],
            "source": None,
            # Un jalon redige peut renvoyer vers une province : c'est le cas de
            # la detection des premiers cas, qui a eu lieu en Ituri. Les jalons
            # d'extension, eux, portent la leur automatiquement.
            "province": event.get("province"),
        })

    series = sorted([s for s in sitreps if s.get("date")], key=lambda s: s["date"])
    strings_lang = strings[lang]
    if series:
        first = series[0]
        events.append({
            "date": first["date"], "kind": "official",
            "title": strings_lang["timelineFirstSitrepTitle"],
            "text": interp(strings_lang["timelineFirstSitrepText"], {
                "cases": fmt(first.get("confirmed"), lang),
                "deaths": fmt(first.get("deaths"), lang)}),
            "source": first["date"],
        })

    def thresholds(field, steps, title_key, text_key, kind):
        reached = set()
        for entry in series:
            value = entry.get(field)
            if value is None:
                continue
            for step in steps:
                if value >= step and step not in reached:
                    reached.add(step)
                    events.append({
                        "date": entry["date"], "kind": kind,
                        "title": interp(strings_lang[title_key],
                                        {"n": fmt(step, lang)}),
                        "text": interp(strings_lang[text_key],
                                       {"n": fmt(step, lang)}),
                        "source": entry["date"],
                    })

    # Un jalon tous les 1 000 franchis, derives de la serie plutot
    # qu'ecrits en dur : la liste figee s'arretait a 5 000 quand le
    # SitRep 107 passait les 6 000 cas (31 aout) — un chiffre ecrit en dur
    # ne se recalcule jamais, regle du depot. Le prochain millier (7 000
    # cas, 3 000 deces) apparaitra seul, au bulletin qui le franchit.
    def paliers_1000(field):
        maxi = max((s.get(field) or 0) for s in series) if series else 0
        return range(1000, maxi + 1, 1000)

    thresholds("confirmed", paliers_1000("confirmed"),
               "timelineMilestoneCasesTitle", "timelineMilestoneCasesText", "milestone")
    thresholds("deaths", paliers_1000("deaths"),
               "timelineMilestoneDeathsTitle", "timelineMilestoneDeathsText", "milestone")

    if series:
        last = series[-1]
        events.append({
            "date": last["date"], "kind": "current",
            "title": strings_lang["timelineLatestTitle"],
            "text": interp(strings_lang["timelineLatestText"], {
                "cases": fmt(last.get("confirmed"), lang),
                "deaths": fmt(last.get("deaths"), lang)}),
            "source": last["date"],
        })

    if config is not None and strings.get("provinceArrivals"):
        events += province_arrival_events(
            config, strings["provinceArrivals"], strings_lang, lang, i18n_lang,
            urls=urls)
    if zones_history and geo is not None:
        events += zone_milestone_events(zones_history, geo, strings_lang, lang,
                                        health_zones=latest_zones or ())

    events.sort(key=lambda e: e["date"])
    attach_toll(events, series)
    return events


def attach_toll(events, series):
    """Attache a chaque jalon le bilan cumule connu a sa date.

    On retient le dernier bulletin publie a cette date ou avant : les jalons
    anterieurs au premier bulletin (la detection des cas suspects, par exemple)
    n'ont donc pas de bilan, ce qui est exact.
    """
    if not series:
        return
    peak = max((entry.get("confirmed") or 0) for entry in series) or 1
    for event in events:
        known = [e for e in series if e["date"] <= event["date"]
                 and e.get("confirmed") is not None]
        if not known:
            event["toll"] = None
            continue
        latest = known[-1]
        event["toll"] = {
            "confirmed": latest.get("confirmed"),
            "deaths": latest.get("deaths"),
            "share": min(100.0, (latest.get("confirmed") or 0) * 100.0 / peak),
        }



def render_timeline(events, strings_lang, i18n_lang, heading="h2"):
    """Piste horizontale, reservee a l'apercu de l'accueil : trois jalons, pas
    de defilement, une carte par jalon."""
    parts = []
    for event in events:
        parts.append(
            '          <li class="th-item is-%s">\n'
            '            <span class="th-dot" aria-hidden="true"></span>\n'
            '            <time class="th-date" datetime="%s">%s</time>\n'
            "            <%s class=\"th-title\">%s</%s>\n"
            '            <p class="th-text">%s</p>\n'
            "          </li>" % (
                classe_jalon(event), event["date"], esc(long_date(event["date"], i18n_lang)),
                heading, esc(event["title"]), heading, event["text"]))
    return "\n".join(parts)


def est_seuil_deces(event):
    return bool(re.search(r"d[ée]c[eè]s|death|vifo", event.get("title", ""), re.I))


def classe_jalon(event):
    """Classe d'un evenement de chronologie. Code couleur du 6 octobre 2026 :
    seuils de cas en bleu, seuils de deces en rouge, extensions en ocre,
    jalons officiels en vert fonce."""
    if event["kind"] == "milestone":
        return "milestone is-deces" if est_seuil_deces(event) else "milestone is-cas"
    return event["kind"]


def titre_jalon(event):
    """Titre d'un jalon. Les seuils franchis (« 1 000 cas confirmes ») portent
    leur nombre en tres grand (5 octobre 2026, option A de la maquette
    chronologie) : le chiffre devient le titre, la suite son libelle."""
    titre = esc(event["title"])
    if event.get("kind") == "milestone":
        m = re.match(r"^([\d\s\u202f\u00a0]+)\s+(.*)$", event["title"])
        if m:
            return '<span class="tl-big">%s</span> %s' % (esc(m.group(1).strip()), esc(m.group(2)))
    return titre


def render_timeline_vertical(events, strings_lang, i18n_lang, urls, lang,
                             province_slugs, heading="h2"):
    """Chronologie verticale de la page dediee.

    Elle se lit de haut en bas, groupee par mois, et chaque jalon porte le bilan
    cumule connu a sa date : la chronologie raconte alors la trajectoire, pas
    seulement une suite d'anecdotes. Le defilement vertical est le geste par
    defaut partout, et il laisse la place d'etoffer chaque entree — ce que le
    format horizontal interdisait.
    """
    parts = []
    current_month = None
    for event in events:
        month = event["date"][:7]
        if month != current_month:
            current_month = month
            label = "%s %s" % (i18n_lang["months"][int(month[5:7]) - 1], month[:4])
            parts.append('        <li class="tl-month"><span>%s</span></li>' % esc(label))

        toll = ""
        if event.get("toll"):
            # Les premiers bulletins ne chiffrent pas toujours les deces : on
            # tait alors la mention plutot que d'afficher un tiret.
            if event["toll"]["deaths"] is None:
                line = interp(strings_lang["timelineTollCasesOnly"],
                              {"cases": fmt(event["toll"]["confirmed"], lang)})
            else:
                line = interp(strings_lang["timelineTollLine"], {
                    "cases": fmt(event["toll"]["confirmed"], lang),
                    "deaths": fmt(event["toll"]["deaths"], lang)})
            toll = (
                '\n            <div class="tl-toll" title="%s">\n'
                '              <span class="tl-toll-bar" aria-hidden="true">'
                '<span style="width:%.1f%%;"></span></span>\n'
                "              <span class=\"tl-toll-line\">%s</span>\n"
                "            </div>" % (esc(strings_lang["timelineTollLabel"]),
                                        event["toll"]["share"], esc(line)))

        link = ""
        province = event.get("province")
        if province and urls is not None and province in province_slugs:
            link = ('\n            <a class="tl-link" href="%s">%s</a>'
                    % (urls.province_path(province, lang),
                       esc(strings_lang["timelineSeeProvince"])))

        parts.append(
            '        <li class="tl-item is-%s">\n'
            '          <span class="tl-dot" aria-hidden="true"></span>\n'
            '          <div class="tl-body">\n'
            '            <time class="tl-date" datetime="%s">%s</time>\n'
            "            <%s class=\"tl-title\">%s</%s>\n"
            '            <p class="tl-text">%s</p>%s%s\n'
            "          </div>\n"
            "        </li>" % (
                classe_jalon(event), event["date"], esc(long_date(event["date"], i18n_lang)),
                heading, titre_jalon(event), heading, event["text"], toll, link))
    # Refonte du 2 octobre 2026 : un jalon sur deux a gauche, un sur deux a
    # droite de la colonne centrale (feuille de style : .tl-zig, grand ecran).
    # 5 octobre 2026 : les cartes se font face (deux par rangee), et chaque
    # mois repart a gauche pour qu'aucune rangee ne commence par un trou.
    rang = [0]
    def alterner(m):
        if m.group(0).startswith('class="tl-month'):
            rang[0] = 0
            return m.group(0)
        rang[0] += 1
        return 'class="tl-item tl-%s is-' % ("l" if rang[0] % 2 else "r")
    return re.sub(r'class="tl-month"|class="tl-item is-', alterner, "\n".join(parts))


TAG_RE = re.compile(r"<[^>]+>")


def faq_items_html(strings, lang, url_values):
    """Rend la FAQ et renvoie aussi une version texte pour le balisage FAQPage."""
    parts, plain = [], []
    for item in strings["faqItems"]:
        question = item[lang]["q"]
        answer = interp(item[lang]["a"], url_values)
        parts.append(
            '      <details class="faq-item">\n'
            "        <summary>%s</summary>\n"
            '        <div class="faq-answer">%s</div>\n'
            "      </details>" % (esc(question), answer))
        plain.append({"q": question, "a": TAG_RE.sub("", answer).strip()})
    return "\n".join(parts), plain


def glossaire_items_html(strings, lang):
    """Le glossaire en dictionnaire (7 octobre 2026) : les termes dans l'ordre
    alphabetique de la langue, accents ignores, groupes sous leur lettre."""
    import unicodedata
    def cle(t):
        return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    items = sorted(strings["glossaireItems"], key=lambda it: cle(it[lang]["t"]))
    groupes, parts = [], []
    for it in items:
        lettre = cle(it[lang]["t"])[:1].upper()
        if not groupes or groupes[-1][0] != lettre:
            groupes.append((lettre, []))
        groupes[-1][1].append(it)
    for lettre, its in groupes:
        parts.append('    <div class="gl-l"><div class="gl-k" aria-hidden="true">%s</div><dl>%s</dl></div>'
                     % (lettre, "".join('<div class="gl-item"><dt>%s</dt><dd>%s</dd></div>'
                                        % (esc(it[lang]["t"]), esc(it[lang]["d"])) for it in its)))
    return "\n".join(parts)


# Les emetteurs sont enregistres par data/actus.json sous leur sigle
# francais ; les autres langues ont le leur.
SIGLES_ACTUS = {
    "OMS": {"en": "WHO", "sw": "WHO"},
    "OMS Afrique": {"en": "WHO Africa", "sw": "WHO Afrika"},
    "OIM": {"en": "IOM", "sw": "IOM"},
    "PAM": {"en": "WFP", "sw": "WFP"},
    "FICR": {"en": "IFRC", "sw": "IFRC"},
    "Primature": {"en": "DRC Prime Minister", "sw": "Waziri Mkuu wa DRC"},
}

# Un media qui publie dans plusieurs langues (RFI, France 24, ACP) couvre la meme
# nouvelle dans chacune : chaque page ne garde que ses articles dans sa
# langue, sinon la depeche apparaitrait deux fois. Pas de flux en swahili :
# la page swahilie prend le francais, langue de l'est de la RDC.
LANGUE_MEDIAS = {"fr": "fr", "en": "en", "sw": "fr"}


# Les categories de la page, dans l'ordre des filtres. Un emetteur absent
# d'ici tombe dans « Autres » (Africa CDC, ReliefWeb).
CATEGORIES_ACTUS = [
    ("onu", "actusCatOnu", {"OMS", "OMS Afrique", "OCHA", "OIM", "PAM", "UNICEF"}),
    ("ong", "actusCatOng", {"MSF", "CARE", "FICR", "Mercy Corps"}),
    ("rdc", "actusCatRdc", {"Primature", "ACP", "Ministère de la Santé"}),
    ("medias", "actusCatMedias", {"RFI", "France 24", "The Guardian"}),
]
# La teinte de chaque emetteur : pastille de la source et vignette dessinee
# quand l'article n'a pas d'image.
TEINTES_ACTUS = {
    "MSF": "#A8322A", "OMS": "#1B6C8C", "OMS Afrique": "#1B6C8C", "OCHA": "#2E5E8C",
    "OIM": "#3A4F8F", "Africa CDC": "#2F6F4B", "CARE": "#B0682A", "Mercy Corps": "#8C2F3F",
    "RFI": "#C8102E", "France 24": "#0B5CAD", "The Guardian": "#052962",
    "Primature": "#6B4A1F", "ACP": "#2A4B7C",
}
MOIS_LONGS_ACTUS = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
    "sw": ["Januari", "Februari", "Machi", "Aprili", "Mei", "Juni", "Julai", "Agosti",
           "Septemba", "Oktoba", "Novemba", "Desemba"],
}


def actus_choisis(actus, lang):
    """Les articles publies que montre la page de cette langue, du plus recent
    au plus ancien."""
    voulue = LANGUE_MEDIAS.get(lang, lang)
    items = [x for x in actus.get("items", []) if x.get("statut") == "publie"
             and (not x.get("media") or x.get("langue") == voulue)]
    # Un communique traduit (« paire » commune) : la version dans la langue
    # de la page, sinon la premiere venue.
    paires = {}
    for x in items:
        if x.get("paire"):
            garde = paires.get(x["paire"])
            if garde is None or (x.get("langue") == voulue and garde.get("langue") != voulue):
                paires[x["paire"]] = x
    items = [x for x in items if not x.get("paire") or paires[x["paire"]] is x]
    items.sort(key=lambda x: (x["date"], x["id"]), reverse=True)
    return items


JOURS_SEMAINE_ACTUS = {"fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
                      "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                      "sw": ["Jumatatu", "Jumanne", "Jumatano", "Alhamisi", "Ijumaa", "Jumamosi", "Jumapili"]}


def actus_items_html(actus, lang, i18n_lang, strings_lang):
    """La page Nouvelles en « fil de presse » (7 octobre 2026, option 1 des
    maquettes) : une colonne de lecture, jour par jour, la date entre deux
    filets ; pour chaque article la source en couleur, le titre, deux lignes
    de resume et une petite photo. Les filtres par source sont un sommaire
    entre filets ; app.js montre les articles par lots (« Voir plus »), et
    calcule « Aujourd'hui », « Hier » et « Nouveau » a l'heure du lecteur.
    Chaque article mene a sa source ; le site n'en reprend que le titre et
    le resume qu'elle publie."""
    items = actus_choisis(actus, lang)
    if not items:
        return '        <p class="actus-vide">%s</p>' % esc(strings_lang["actusVide"])
    mois_longs = MOIS_LONGS_ACTUS.get(lang, MOIS_LONGS_ACTUS["en"])
    semaine = JOURS_SEMAINE_ACTUS.get(lang, JOURS_SEMAINE_ACTUS["en"])

    def categorie(x):
        return next((cle for cle, _, noms in CATEGORIES_ACTUS if x["source"] in noms), "autres")

    comptes = {}
    for x in items:
        comptes[categorie(x)] = comptes.get(categorie(x), 0) + 1
    puces = ['<button type="button" class="actus-puce on" data-cat="">%s<b>%d</b></button>'
             % (esc(strings_lang["actusToutes"]), len(items))]
    for cle, libelle, _ in CATEGORIES_ACTUS + [("autres", "actusCatAutres", set())]:
        if comptes.get(cle):
            puces.append('<button type="button" class="actus-puce" data-cat="%s">%s<b>%d</b></button>'
                         % (cle, esc(strings_lang[libelle]), comptes[cle]))

    jours, courant = [], None
    for x in items:
        if not courant or courant[0] != x["date"]:
            courant = (x["date"], [])
            jours.append(courant)
        courant[1].append(x)
    blocs = []
    for jour, arts in jours:
        d = date.fromisoformat(jour)
        libelle = "%s %d %s" % (semaine[d.weekday()], d.day, mois_longs[d.month - 1])
        lignes = []
        for x in arts:
            source = SIGLES_ACTUS.get(x["source"], {}).get(lang, x["source"])
            teinte = TEINTES_ACTUS.get(x["source"], "#5A544C")
            if x.get("image") and os.path.exists(os.path.join(ROOT, "assets", "actus", x["id"] + ".jpg")):
                visuel = '<img class="af-img" src="/assets/actus/%s.jpg" alt="" loading="lazy" decoding="async">' % x["id"]
            else:
                visuel = '<span class="af-img af-sigle" style="--t:%s">%s</span>' % (teinte, esc(source))
            # La langue n'est dite que quand elle differe de celle de la page.
            lg = ""
            if x.get("langue") and x["langue"] != lang and lang != "sw":
                lg = ' <span class="actu-lg" title="%s">%s</span>' % (
                    esc(strings_lang["actusLangue_" + x["langue"]]), x["langue"].upper())
            lignes.append(
                '<a class="af-a" data-cat="%s" data-date="%s" href="%s" target="_blank" rel="noopener"%s>'
                '<div><span class="af-meta"><span class="af-src" style="--t:%s">%s</span>%s'
                ' <span class="actu-neuf">%s</span></span><h3>%s</h3>%s</div>%s</a>' % (
                    categorie(x), x["date"], esc(x["url"]),
                    ' hreflang="%s"' % x["langue"] if x.get("langue") else "",
                    teinte, esc(source), lg, esc(strings_lang["actusNouveau"]), esc(x["titre"]),
                    ('<p>%s</p>' % esc(x["resume"])) if x.get("resume") else "", visuel))
        blocs.append('          <section class="af-j" data-jour="%s"><h2><span>%s</span></h2>%s</section>'
                     % (jour, esc(libelle), "".join(lignes)))
    return ('        <nav class="actus-puces" aria-label="%s">%s</nav>\n'
            '        <div class="actus-fil" data-auj="%s" data-hier="%s">\n%s\n        </div>\n'
            '        <div class="af-plus"><button type="button">%s</button></div>' % (
                esc(strings_lang["actusFiltres"]), "".join(puces), esc(strings_lang["actusAujourdhui"]),
                esc(strings_lang["actusHier"]), "\n".join(blocs), esc(strings_lang["actusVoirPlus"])))


def province_map_values(province_maps, name, zones, config, lang, strings_lang, aliases):
    """Jetons de la carte d'une province, ou des valeurs vides si sa geometrie
    n'a pas encore ete produite."""
    geo_map = province_maps.get(name)
    if not geo_map:
        print("  ! pas de carte pour %s : relancer scripts/build_geo.py" % name)
        return {"province.name": esc(name), "province.map": "",
                "province.mapNote": "", "province.mapZones": ""}
    svg, touched, total = province_map_html(
        geo_map, name, zones, config, lang, strings_lang, aliases)
    return {
        "province.name": esc(name),
        "province.map": svg,
        "province.mapNote": hint_pair(strings_lang, "provinceMapNote",
                                      "provinceMapNoteTouch"),
        "province.mapZones": esc(interp(strings_lang["provinceMapZones"],
                                        {"n": fmt(touched, lang), "total": fmt(total, lang)})),
    }


def province_zones_table_html(zones, forms, lang, strings_lang, i18n_lang, zones_history=None, province=None):
    """Le tableau des zones touchees d'une province, en « mini-courbes »
    (7 octobre 2026, option 3 des maquettes) : la zone, ses cas cumules, la
    courbe de ses nouveaux cas sur les 30 derniers jours, ses deces cumules,
    la letalite et ses cas des 7 derniers jours. Les nouveaux cas d'un jour
    sont l'ecart de cumul entre deux instantanes de zones-history.json (un
    recul est ramene a zero, comme sur les graphiques). Triable par colonne
    (app.js, table.zq.tri).

    La note sur la somme des zones (`zonesSumNote`) reste rendue par le
    gabarit, sous le tableau."""
    if not zones:
        return ('      <p class="map-note">%s</p>'
                % esc(strings_lang["provinceZonesEmpty"]))
    from datetime import date as _d, timedelta as _td

    def cle(z):
        return normalise_zone(z.get("name"))

    hist = sorted(zones_history or [], key=lambda h: h["date"])
    fin = hist[-1]["date"] if hist else None
    debut = (_d.fromisoformat(fin) - _td(days=30)).isoformat() if fin else None
    series = {}
    for h in hist:
        if h["date"] < debut:
            continue
        for z in h["zones"]:
            if z.get("province") == province:
                series.setdefault(cle(z), []).append((h["date"], z.get("cases") or 0))

    def nouveaux(k):
        pts = series.get(k, [])
        return [(pts[i][0], max(0, pts[i][1] - pts[i - 1][1])) for i in range(1, len(pts))]

    # Echelle COMMUNE au tableau, compressee en racine carree (7 octobre
    # 2026) : une barre de 1 cas reste petite a cote d'une barre de 20 dans
    # une autre zone, sans que les petites zones disparaissent.
    mx_commun = max([v for k in series for _, v in nouveaux(k)] + [1])

    def spark(vals, titre):
        if not vals:
            return ""
        w, h = 140, 28
        mx = mx_commun ** .5
        bw = w / float(len(vals))
        def haut(v):
            return max(1.5, v ** .5 / mx * (h - 2)) if v else 0
        barres = "".join('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"%s/>'
                         % (i * bw + .5, h - haut(v), max(bw - 1, .6), haut(v),
                            ' class="is-der"' if i == len(vals) - 1 else "")
                         for i, (_, v) in enumerate(vals))
        return ('<svg class="z-spark" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">%s</svg>'
                % (w, h, w, h, esc(titre), barres))

    def plus(v):
        return ('<span class="z-plus">+%s</span>' % fmt(v, lang)) if v else '<span class="z-zero">0</span>'

    rows = []
    for zone in sorted(zones, key=lambda z: -(z.get("cases") or 0)):
        nv = nouveaux(cle(zone))
        n30 = sum(v for _, v in nv)
        n24 = max(0, zone.get("newCases24h") or 0)
        d24 = max(0, zone_new_deaths(zone) or 0)
        # Ordre du 7 octobre 2026 (proprietaire) : cumul, 24 h, 30 jours pour
        # les cas ; cumul et 24 h pour les deces ; puis la letalite.
        rows.append(
            '            <tr><td>%s</td><td class="zt z-cas" data-v="%d">%s</td><td data-v="%d">%s</td>'
            '<td class="zs" data-v="%d">%s</td><td class="zt z-dec" data-v="%d">%s</td><td data-v="%d">%s</td>'
            '<td data-v="%.1f">%s</td></tr>' % (
                esc(zone["name"]), zone.get("cases") or 0, fmt(zone.get("cases"), lang), n24, plus(n24),
                n30, spark(nv, interp(strings_lang["zonesSparkTitle"], {"zone": zone["name"], "n": fmt(n30, lang)})),
                zone.get("deaths") or 0, fmt(zone.get("deaths"), lang), d24, plus(d24),
                zone.get("cfr") or 0, fmt_cfr(zone.get("cfr"), lang)))

    entetes = "".join('<th>%s</th>' % esc(x) for x in [
        strings_lang["provinceThZone"], strings_lang["provinceThCases"], strings_lang["zonesTh24h"],
        strings_lang["zonesTh30"], strings_lang["provinceThDeaths"], strings_lang["zonesThDec24h"],
        strings_lang["provinceThCfr"]])
    return (
        '      <div class="table-scroll">\n'
        '        <table class="zones-province zq tri" id="zonesProvinceTable">\n'
        '          <caption class="visually-hidden">%s</caption>\n'
        '          <thead><tr>%s</tr></thead>\n'
        '          <tbody>\n%s\n          </tbody>\n'
        '        </table>\n'
        '      </div>' % (esc(interp(strings_lang["provinceZonesTitle"], forms)), entetes, "\n".join(rows)))


# --------------------------------------------------------------------------
# Assemblage
# --------------------------------------------------------------------------

PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_.\-]+)\}\}")


def render(template, values, origin_label):
    """Remplace les {{jetons}}. Un jeton inconnu arrête la génération."""
    missing = []

    def replace(match):
        key = match.group(1)
        if key not in values:
            missing.append(key)
            return match.group(0)
        return values[key]

    out = PLACEHOLDER_RE.sub(replace, template)
    if missing:
        sys.exit("Jetons inconnus dans %s : %s"
                 % (origin_label, ", ".join(sorted(set(missing)))))
    return out


def jeton_version(chemin_relatif):
    """Empreinte courte du contenu d'un fichier statique.

    Le HTML et le JavaScript changent souvent ensemble — un nouvel onglet dans
    la page a besoin du mode correspondant dans app.js. Or les deux n'ont pas
    la meme duree de cache : le HTML est revalide a chaque visite, les assets
    sont gardes dix minutes. Pendant ces dix minutes, un visiteur revenant
    recoit un HTML neuf et un JavaScript perime, et la fonctionnalite retombe
    silencieusement sur son comportement par defaut.

    Un jeton derive du contenu supprime la fenetre : l'URL change des que le
    fichier change, donc le navigateur va forcement le rechercher.
    """
    with open(os.path.join(ROOT, chemin_relatif), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:10]


# En deca de ce cumul, une courbe ne raconte rien : le Sud-Kivu compte 3 cas
# en trois mois, le Bas-Uele 2. La ligne est plate, les barres invisibles, et
# le lecteur croit a une panne d'affichage. Le seuil vaut pour l'avenir : une
# province qui le franchit gagne sa courbe au prochain build, sans code.
# Sous ce cumul, une province n'a pas de graphique : la courbe serait plate et
# les barres invisibles. Essaye a 20 le 15 septembre 2026 pour donner le sien
# a la Tshopo (28 cas, 16 journees avec au moins un cas), puis REMIS a 50 le
# meme jour — « on ne va pas garder cette idee la ». Ne pas y revenir sans
# qu'il le redemande.
SEUIL_COURBE_PROVINCE = 50

# Exceptions nommees au seuil, avec le plafond de l'axe des nouveaux cas
# quotidiens. La Tshopo (43 cas, 5 au plus en une journee) a son graphique a la
# demande du proprietaire le 28 septembre 2026, axe fixe a 10 : a cette echelle
# une journee a 1 cas reste lisible, et l'axe ne saute pas d'un bulletin a
# l'autre. Le seuil general, lui, reste a 50 ; les vues par semaine et par mois
# gardent leur axe automatique (une semaine peut depasser 10).
COURBE_PROVINCE_FORCEE = {"Tshopo": 10}


# Les provinces dont la fiche porte le cadre « La riposte » (decisions du
# proprietaire, 28 septembre 2026). D'abord un seuil a 40 cas, qui ecartait
# le Sud-Kivu, le Bas-Uele et le Sud-Ubangi (2 a 10 cas) ; puis, une fois les
# graphiques developpes montres, le Haut-Uele et la Tshopo aussi : « les
# donnees semblent trop instables a cause du petit echantillon » — 47
# echantillons en sept releves a la Tshopo, un centre de 31 lits, des lignes
# d'alertes qui se contredisent. Leur riposte reste sur la page Riposte, a
# cote des autres provinces.
PROVINCES_RIPOSTE_FICHE = ("Ituri", "Nord-Kivu")

# Provinces qui ont commence a vacciner (29 septembre 2026, demande du
# proprietaire) : au moins un cumul publie dans les bulletins. Remplie par
# main() depuis piliers.json, avant la numerotation des cadres. Celles qui
# n'ont pas la fiche complete de la riposte (Tshopo, Bas-Uele) recoivent un
# cadre « La riposte » reduit a la vaccination.
VACCIN_PROVINCES = set()


def provinces_qui_vaccinent(piliers):
    pts = (piliers or {}).get("parDate") or []
    out = set()
    for p in pts:
        for nom, n in (((p.get("vaccination") or {}).get("cumulParProvince")) or {}).items():
            if n:
                out.add(_canon_prov(nom))
    return out

# Provinces dont la page porte, en dernier cadre, la grille des obstacles par
# semaine (29 septembre 2026) : les cinq qui ont assez de difficultes citees
# pour qu'une grille se lise. Le Sud-Kivu (29 mentions) et le Sud-Ubangi n'en
# ont pas.
PROVINCES_OBSTACLES = ("Ituri", "Nord-Kivu", "Tshopo", "Haut-Uélé", "Bas-Uélé")


def a_une_riposte(province):
    return province.get("name") in PROVINCES_RIPOSTE_FICHE


def a_une_courbe(province):
    return ((province.get("confirmed") or 0) >= SEUIL_COURBE_PROVINCE
            or province.get("name") in COURBE_PROVINCE_FORCEE)


# Provinces dont la page porte le cadre « Le lieu du deces » (16 septembre
# 2026) : les trois qui classent assez de deces chaque semaine pour qu'une part
# ait un sens. Les memes que les boutons du graphique de la page Riposte.
PROVINCES_LIEU_DECES = ("Ituri", "Nord-Kivu", "Haut-Uélé")


# Provinces dont la page porte le cadre « La riposte » : le Haut-Uele en a ete
# retire a la demande du proprietaire (16 septembre 2026), comme le cadre « Sur
# le terrain » de toutes les provinces, supprime le meme jour.
PROVINCES_RIPOSTE = ("Ituri", "Nord-Kivu")


def province_numeros(province):
    """Les numeros des cadres d'une page province, dans l'ordre de la page :
    [courbe des cas, courbe des deces et lieu du deces], zones,
    riposte, [obstacles], chronologie — le plan de la fiche du 28 septembre 2026.
    Un seul calcul pour le gabarit et les fonctions qui ecrivent les cadres :
    chaque ajout decalait la chronologie a la main (16 septembre 2026)."""
    # La carte des zones est partie le 6 octobre 2026 : celle de l'en-tete
    # suffit. Les cadres commencent donc a 01 avec la courbe des cas.
    n, nums = 0, {}
    def suivant(cle):
        nonlocal n
        n += 1
        nums[cle] = "%02d" % n
    if a_une_courbe(province):
        suivant("courbe")
        suivant("deces")
    suivant("zones")
    if a_une_riposte(province) or province.get("name") in VACCIN_PROVINCES:
        suivant("riposte")
    if province.get("name") in PROVINCES_OBSTACLES:
        suivant("obstacles")
    suivant("chrono")
    return nums


BOUTON_PARTAGE = (
    '      <div class="chart-actions" data-export-chart="%s">\n'
    '        <button type="button" class="share-btn">\n'
    '          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="10.6" x2="15.4" y2="6.4"/><line x1="8.6" y1="13.4" x2="15.4" y2="17.6"/></svg>\n'
    '          <span data-i18n="chartShareBtn">%s</span>\n'
    '        </button>\n'
    '      </div>\n')


def province_riposte_charts_html(province, strings_lang, i18n_lang, numero):
    """Cadre « La riposte » (16 septembre 2026) : les quatre graphiques de la
    page Riposte, restreints a la province, derriere des onglets sur un seul
    canevas — quatre cadres auraient allonge la page d'autant."""
    if province.get("name") not in PROVINCES_RIPOSTE:
        return ""
    onglets = [("contactsRiposte", "riposteContactsTitle"), ("cte", "riposteCteTitle"),
               ("alertes", "riposteAlertesTitle"), ("laboratoire", "riposteLaboTitle")]
    boutons = "".join(
        '        <button type="button" class="subtab-btn%s" data-mode="%s">%s</button>\n'
        % (" active" if i == 0 else "", mode, esc(strings_lang[cle]))
        for i, (mode, cle) in enumerate(onglets))
    return (
        '  <section class="section cadre-fiche" id="riposte">\n'
        '    <div class="fiche-tete"><span class="fiche-num">%s</span><div><h2 class="frame-title">%s</h2>'
        '<div class="section-sub">%s</div></div></div>\n'
        '    <div class="cadre-corps">\n'
        '    <nav class="subtab-nav" data-chart-tabs="provRiposteChart">\n%s    </nav>\n'
        '    <div class="panel chart-panel-wrap">\n%s'
        '      <div class="chart-panel">\n'
        '        <canvas id="provRiposteChart" data-chart="contactsRiposte" data-province="%s"></canvas>\n'
        '      </div>\n'
        # Les blancs et les pointilles : dits depuis le 27 septembre 2026 par
        # la phrase standard qu'app.js (annoterTrous) ajoute a la note, comme
        # sous tous les graphiques. Verifie le 16 septembre sur l'Ituri et le
        # Nord-Kivu : chaque blanc est une donnee absente du bulletin.
        '      <div class="map-note chart-note"></div>\n'
        '    </div>\n'
        '    </div>\n'
        '  </section>\n'
        % (esc(numero), esc(strings_lang["provinceRiposteTitle"]), esc(strings_lang["provinceRiposteSub"]),
           boutons, BOUTON_PARTAGE % ("provRiposteChart", esc(i18n_lang["chartShareBtn"])), esc(province["name"])))


def lieu_deces_bloc(province, strings_lang, i18n_lang):
    """Le lieu du deces, SOUS la courbe des deces de la fiche (28 septembre
    2026) : c'est la meme question — combien, puis ou ils meurent. Meme
    graphique que la page Riposte, restreint a la province par data-province,
    pour les trois provinces qui classent assez de deces."""
    if province.get("name") not in PROVINCES_LIEU_DECES:
        return ""
    return (
        '      <div class="section-head" style="margin-top:32px;">\n'
        '        <h3 class="frame-title">%s</h3>\n'
        '        <span class="section-sub">%s</span>\n'
        '      </div>\n'
        '      <p class="fiche-texte fiche-texte-centre">%s</p>\n'
        '      <div class="panel chart-panel-wrap">\n%s'
        '        <div class="chart-panel">\n'
        '          <canvas id="decesLieuChart" data-chart="deathsPlace" data-province="%s"></canvas>\n'
        '        </div>\n'
        '        <div class="map-note chart-note"></div>\n'
        '      </div>\n'
        % (esc(strings_lang["riposteDecesTitle"]), esc(strings_lang["provinceDecesLieuSub"]),
           esc(strings_lang["riposteDecesLede"]), BOUTON_PARTAGE % ("decesLieuChart", esc(i18n_lang["chartShareBtn"])), esc(province["name"])))


def province_deces_lieu_html(province, strings_lang, i18n_lang, numero="04"):
    """Le cadre « Le lieu du deces » d'une page province : le graphique de la
    page Riposte, restreint a la province par data-province. Place sous le
    tableau des zones, avant la chronologie."""
    if province.get("name") not in PROVINCES_LIEU_DECES:
        return ""
    return (
        '  <section class="section cadre-fiche" id="deces">\n'
        '    <div class="fiche-tete"><span class="fiche-num">%s</span><div><h2 class="frame-title">%s</h2>'
        '<div class="section-sub">%s</div></div></div>\n'
        '    <div class="cadre-corps">\n'
        '    <div class="panel chart-panel-wrap">\n'
        '      <div class="chart-actions" data-export-chart="decesLieuChart">\n'
        '        <button type="button" class="share-btn">\n'
        '          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="10.6" x2="15.4" y2="6.4"/><line x1="8.6" y1="13.4" x2="15.4" y2="17.6"/></svg>\n'
        '          <span data-i18n="chartShareBtn">%s</span>\n'
        '        </button>\n'
        '      </div>\n'
        '      <div class="chart-panel">\n'
        '        <canvas id="decesLieuChart" data-chart="deathsPlace" data-province="%s"></canvas>\n'
        '      </div>\n'
        '      <div class="map-note chart-note"></div>\n'
        '    </div>\n'
        '    </div>\n'
        '  </section>\n'
        % (esc(numero), esc(strings_lang["riposteDecesTitle"]), esc(strings_lang["provinceDecesLieuSub"]),
           esc(i18n_lang["chartShareBtn"]), esc(province["name"])))


def _cadre_courbe_province(province, strings_lang, i18n_lang, numero, canvas_id, champ,
                            cle_titre, cle_sous_titre, apres=""):
    plafond = COURBE_PROVINCE_FORCEE.get(province.get("name"))
    attrs = ' data-y-max="%d"' % plafond if plafond else ""
    if champ != "confirmed":
        attrs += ' data-champ="%s"' % champ
    # Cadre numerote, comme la page Riposte & defis (demande du proprietaire,
    # 8 septembre 2026) : carte 01, courbe 02, zones 03 depuis le 16 septembre
    # 2026, ou la courbe est remontee au-dessus du tableau des zones.
    return (
        '  <section class="section cadre-fiche">\n'
        '    <div class="fiche-tete"><span class="fiche-num">%s</span><div><h2 class="frame-title">%s</h2>'
        '<div class="section-sub">%s</div></div></div>\n'
        '    <div class="cadre-corps">\n'
        '    <div class="panel chart-panel-wrap">\n'
        # Le graphique de province se partage comme les autres : figure et note
        # comprises. Le libelle vient d'i18n, comme partout ailleurs.
        '      <div class="chart-actions" data-export-chart="%s">\n'
        '        <button type="button" class="share-btn">\n'
        '          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="10.6" x2="15.4" y2="6.4"/><line x1="8.6" y1="13.4" x2="15.4" y2="17.6"/></svg>\n'
        '          <span data-i18n="chartShareBtn">%s</span>\n'
        '        </button>\n'
        '      </div>\n'
        # Trois pas de temps, comme les cadres de /donnees/ (15 septembre 2026).
        # La bascule vise le canevas de SON cadre (`.chart-panel-wrap`), le
        # cablage d'`app.js` est generique : rien a declarer de plus.
        '      <nav class="subtab-nav chart-vue-nav" data-vue-periode>\n'
        '        <button type="button" class="subtab-btn active" data-vue="quotidien" data-i18n="chartVueDaily">%s</button>\n'
        '        <button type="button" class="subtab-btn" data-vue="hebdo" data-i18n="chartVueWeekly">%s</button>\n'
        '        <button type="button" class="subtab-btn" data-vue="mensuel" data-i18n="chartVueMonthly">%s</button>\n'
        '      </nav>\n'
        '      <div class="chart-panel">\n'
        '        <canvas id="%s" data-chart="provinceEpidemic"%s></canvas>\n'
        '      </div>\n'
        '      <div class="map-note chart-note"></div>\n'
        '    </div>\n'
        '%s'
        '    </div>\n'
        '  </section>\n'
        # Le titre porte le nom de la province entre parentheses. Sans lui,
        # « Evolution de l'epidemie » est mot pour mot l'intitule du premier
        # sous-onglet de /donnees/, qui lui trace le pays entier : un lecteur
        # arrive par le menu lateral n'a rien pour distinguer les deux courbes.
        % (esc(numero),
           esc(interp(strings_lang[cle_titre],
                      {"name": province["name"]})),
           esc(strings_lang[cle_sous_titre]),
           canvas_id,
           esc(i18n_lang["chartShareBtn"]),
           esc(i18n_lang["chartVueDaily"]),
           esc(i18n_lang["chartVueWeekly"]),
           esc(i18n_lang["chartVueMonthly"]),
           canvas_id, attrs, apres))


def province_chart_html(province, strings_lang, i18n_lang):
    """Les deux cadres de courbe d'une page province : les cas, puis les
    deces (demande du proprietaire, 28 septembre 2026, pour les quatre
    provinces qui ont une courbe). Meme dessin, memes trois pas de temps ;
    le cadre des deces porte le rouge du site et sa seule courbe de cumul."""
    if not a_une_courbe(province):
        return ""
    nums = province_numeros(province)
    return (_cadre_courbe_province(province, strings_lang, i18n_lang, nums["courbe"],
                                   "provinceChart", "confirmed",
                                   "provinceChartTitle", "provinceChartSub")
            + _cadre_courbe_province(province, strings_lang, i18n_lang, nums["deces"],
                                     "provinceDeathsChart", "deaths",
                                     "provinceDeathsChartTitle", "provinceDeathsChartSub",
                                     apres=lieu_deces_bloc(province, strings_lang, i18n_lang)))



# ---------------------------------------------------------------------------
# La frise des pages province (8 septembre 2026) : la piste horizontale de
# l'accueil, memes genres et memes couleurs, seuils a l'echelle de la
# province.
# ---------------------------------------------------------------------------
TH_FLECHE_PREV = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
                  'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>')
TH_FLECHE_NEXT = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
                  'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>')


def pas_arrondi(maxi, cible=6):
    """Un pas « rond » (1, 2 ou 5 fois une puissance de dix) tel que le
    maximum donne environ `cible` jalons : 5 326 cas -> 1 000, 1 000 ->
    200, 249 -> 50, 22 -> 5, 3 -> 1. Jamais moins de 1."""
    if not maxi or maxi <= 0:
        return 1
    brut = maxi / float(cible)
    if brut <= 1:
        return 1
    import math
    # Le nombre rond LE PLUS PROCHE (en logarithme), pas le premier au-dessus :
    # 28 zones sur cinq paliers font 5,6 — le premier au-dessus donnait 10,
    # et l'Ituri n'avait que deux jalons de zones.
    puissance = 10 ** math.floor(math.log10(brut))
    candidats = [m * puissance for m in (1, 2, 5, 10)]
    return int(min(candidats, key=lambda c: abs(math.log10(c) - math.log10(brut))))


def province_timeline_events(name, forms, strings, lang, i18n_lang, province_history,
                             zones_history, geo, latest_zones):
    strings_lang = strings[lang]
    events = []
    # 1. L'arrivee de l'epidemie, telle que les bulletins la racontent
    #    (provinceArrivals : dates dans la prose). Pour l'Ituri, le foyer.
    arrival = next((a for a in strings.get("provinceArrivals", []) if a["province"] == name), None)
    if arrival:
        texte = arrival.get("page" + lang.capitalize()) or arrival.get(lang) or ""
        titre = (strings_lang["provinceTimelineStartTitle"] if arrival.get("timeline") is False
                 else interp(strings_lang["timelineSpreadTitle"], forms))
        events.append({"date": arrival["date"], "kind": "official", "title": titre, "text": esc(texte)})

    # 2. La serie de la province : cas et deces cumules par date.
    serie = []
    for jour in sorted(province_history or [], key=lambda d: d["date"]):
        for pv in jour.get("provinces", []):
            if pv.get("name") == name:
                serie.append({"date": jour["date"], "confirmed": pv.get("confirmed"), "deaths": pv.get("deaths")})
    def seuils(champ, cle_texte):
        maxi = max((x.get(champ) or 0) for x in serie) if serie else 0
        pas = pas_arrondi(maxi)
        atteints = set()
        for x in serie:
            v = x.get(champ)
            if v is None:
                continue
            for seuil in range(pas, maxi + 1, pas):
                if v >= seuil and seuil not in atteints:
                    atteints.add(seuil)
                    titre_cle = "timelineMilestoneCasesTitle" if champ == "confirmed" else "timelineMilestoneDeathsTitle"
                    events.append({"date": x["date"], "kind": "milestone",
                                   "title": interp(strings_lang[titre_cle], {"n": fmt(seuil, lang)}),
                                   "text": esc(interp(strings_lang[cle_texte], dict(forms, n=fmt(seuil, lang))))})
    seuils("confirmed", "provinceTimelineCasesText")
    seuils("deaths", "provinceTimelineDeathsText")

    # 3. Les zones touchees, par paliers a l'echelle de la province — meme
    #    identite des zones que zone_milestone_events (alias + deux lettres).
    entries = sorted([e for e in zones_history if e.get("date")], key=lambda e: e["date"])
    aliases = geo.get("aliases", {})
    connues = {z["key"] for z in geo["zones"] if normalise_zone(z["province"]) == normalise_zone(name)}
    def identite(nom):
        base = normalise_zone(nom); key = aliases.get(base, base)
        if key in connues:
            return key
        proches = sorted((_edit_distance(k, key), k) for k in connues if abs(len(k) - len(key)) <= 2 and _edit_distance(k, key) <= 2)
        if proches and (len(proches) == 1 or proches[0][0] < proches[1][0]):
            return proches[0][1]
        return key
    nom_courant = {identite(z["name"]): z["name"] for z in latest_zones if z.get("province") == name}
    vues, arrivees_par_date = set(), []
    for e in entries:
        noms = []
        for z in e.get("zones", []):
            if z.get("province") != name or not (z.get("cases") or 0) > 0:
                continue
            k = identite(z["name"])
            if k in vues:
                continue
            vues.add(k)
            noms.append(nom_courant.get(k) or (z["name"].title() if z["name"].isupper() else z["name"]))
        if noms:
            arrivees_par_date.append((e["date"], sorted(noms, key=normalise_zone)))
    total_zones = len(vues)
    pas_z = pas_arrondi(total_zones, cible=4)
    cumul, atteints = 0, set()
    et = strings_lang["timelineListAnd"]
    def liste(items):
        return items[0] if len(items) == 1 else ", ".join(items[:-1]) + et + items[-1]
    for i, (d, noms) in enumerate(arrivees_par_date):
        cumul += len(noms)
        franchis = [x for x in range(pas_z, total_zones + 1, pas_z) if cumul >= x and x not in atteints]
        if not franchis:
            continue
        atteints.update(franchis)
        if i == 0 and len(noms) > 1:
            texte = interp(strings_lang["provinceTimelineZonesFirstText"], dict(forms, n=fmt(cumul, lang), zones=liste(noms)))
        else:
            texte = interp(strings_lang["provinceTimelineZonesText"], dict(forms, n=fmt(cumul, lang), k=len(noms), zones=liste(noms)))
        events.append({"date": d, "kind": "spread",
                       "title": interp(strings_lang["timelineMilestoneZonesTitle"], {"n": fmt(cumul, lang)}),
                       "text": esc(texte)})

    # 4. Le dernier bilan.
    if serie:
        last = serie[-1]
        events.append({"date": last["date"], "kind": "current",
                       "title": strings_lang["timelineLatestTitle"],
                       "text": esc(interp(strings_lang["provinceTimelineLatestText"],
                                          dict(forms, cases=fmt(last.get("confirmed"), lang), deaths=fmt(last.get("deaths"), lang))))})
    ordre = {"official": 0, "spread": 1, "milestone": 2, "current": 3}
    events.sort(key=lambda e: (e["date"], ordre.get(e["kind"], 9)))
    return events


def province_timeline_html(name, forms, strings, lang, i18n_lang, province_history,
                           zones_history, geo, latest_zones, numero="04"):
    """La section « Chronologie {in} » : la piste horizontale de l'accueil
    (memes classes, memes fleches — l'id timelineTeaser est celui que le
    script attend, il n'existe pas ailleurs sur une page province), une
    legende, et des jalons a l'echelle de la province."""
    strings_lang = strings[lang]
    events = province_timeline_events(name, forms, strings, lang, i18n_lang, province_history,
                                      zones_history, geo, latest_zones)
    if not events:
        return ""
    items = render_timeline(events, strings_lang, i18n_lang, heading="h3")
    legende = ('    <ul class="tl-legend">\n      <li class="is-official">%s</li>\n'
               '      <li class="is-spread">%s</li>\n      <li class="is-milestone">%s</li>\n    </ul>\n'
               % (esc(strings_lang["timelineKindOfficial"]), esc(strings_lang["timelineKindSpread"]),
                  esc(strings_lang["timelineKindMilestone"])))
    return ('  <section class="section cadre-fiche">\n'
            '    <div class="fiche-tete"><span class="fiche-num">%s</span><div><h2 class="frame-title">%s</h2><div class="section-sub">%s</div></div></div>\n'
            '    <div class="cadre-corps">\n'
            '%s'
            '    <div class="th-scroller">\n'
            '      <div class="timeline-h is-inline" id="timelineTeaser" tabindex="0" role="region" aria-label="%s">\n'
            '        <ol class="th-track">\n%s\n        </ol>\n      </div>\n'
            '      <button class="th-nav is-prev" type="button" data-th-nav="-1" aria-controls="timelineTeaser" aria-label="%s" hidden>%s</button>\n'
            '      <button class="th-nav is-next" type="button" data-th-nav="1" aria-controls="timelineTeaser" aria-label="%s" hidden>%s</button>\n'
            '    </div>\n    </div>\n  </section>\n'
            % (esc(numero), esc(interp(strings_lang["provinceTimelineTitle"], forms)), esc(strings_lang["provinceTimelineSub"]),
               legende, esc(interp(strings_lang["provinceTimelineTitle"], forms)), items,
               esc(strings_lang["timelineScrollPrev"]), TH_FLECHE_PREV,
               esc(strings_lang["timelineScrollNext"]), TH_FLECHE_NEXT))


def riposte_seed(riposte, meta_data, lang, strings_lang, i18n_lang):
    """Les quatre chiffres de tete de la page « Riposte », ecrits en dur.

    Chaque serie s'arrete a sa propre date : le laboratoire peut manquer au
    dernier bulletin quand les alertes y sont. Le sous-titre de chaque chiffre
    porte donc sa date des qu'elle differe de celle du bulletin, et un
    indicateur absent s'ecrit « non publie » plutot que de reprendre une
    valeur ancienne sans le dire."""
    date_bulletin = meta_data.get("reportingDate")

    def au(date):
        if not date or date == date_bulletin:
            return ""
        return " · " + interp(strings_lang["riposteKpiAsOf"],
                              {"date": long_date(date, i18n_lang)})

    def dernier(serie, cle="parDate", garde=lambda p: True):
        points = serie.get(cle, []) if isinstance(serie, dict) else serie
        for p in reversed(points):
            if garde(p):
                return p
        return None

    vide = {"value": "—", "sub": esc(strings_lang["riposteKpiNone"])}
    out = {}

    # Les trois premieres cases cumulent les SEPT derniers releves qui
    # publient la donnee, et nomment la periode couverte — decision du
    # proprietaire, 30 aout. La valeur du jour etait trop bruyante pour une
    # case de tete : alertes recues du simple au double d'un bulletin a
    # l'autre (1 164 le 22 aout, 2 371 le 25), positivite de 13,3 a 21,8
    # puis 13,9 % en trois jours sur 370 a 500 echantillons, et elle
    # contredisait le dernier point des graphiques, hebdomadaires. Une
    # moyenne depuis le debut a ete ecartee : dominee par juin-juillet, elle
    # ne bougerait plus (21,5 % pour 15,9 % sur sept releves). La periode
    # peut s'arreter avant le bulletin — le 106 ne chiffre pas les
    # echantillons de la Tshopo et du Bas-Uele, donc pas de total national
    # ce jour-la. L'occupation des CTE reste au jour : c'est un stock.
    RELEVES_GLISSANTS = 7

    def derniers_releves(points, extraire):
        """Les RELEVES_GLISSANTS derniers points ou `extraire` rend une
        valeur, du plus recent au plus ancien : [(date, valeur), ...]."""
        releves = []
        for p in reversed(points or []):
            v = extraire(p)
            if v is None:
                continue
            releves.append((p["date"], v))
            if len(releves) == RELEVES_GLISSANTS:
                break
        return releves

    def periode(releves):
        # Le libelle dit deja « 7 derniers releves » : ni bornes, ni date de
        # fin, meme quand la fenetre s'arrete avant le bulletin (la
        # positivite au 27 aout quand le 106 est du 28). Decision du
        # proprietaire, 30 aout, apres avoir vu les bornes puis la date
        # seule. Seule l'occupation des CTE, valeur du jour, reste datee
        # quand elle manque au dernier bulletin.
        return ""

    def alertes_du_jour(p):
        t = p.get("total") or {}
        return (t["recues"], t.get("validees")) if t.get("recues") is not None else None
    ra = derniers_releves(riposte["alertes"].get("parDate"), alertes_du_jour)
    if ra:
        recues = sum(v[0] for _, v in ra)
        validees = [v[1] for _, v in ra if v[1] is not None]
        sub = interp(strings_lang["riposteKpiAlertesSub"], {"validees": fmt(sum(validees), lang)}) \
            if len(validees) == len(ra) else ""
        out["ripAlertes"] = fmt(recues, lang)
        out["ripAlertesSub"] = esc(sub + periode(ra))
    else:
        out["ripAlertes"], out["ripAlertesSub"] = vide["value"], vide["sub"]

    def labo_du_jour(p):
        n = p.get("national") or {}
        t = p.get("total") or {}
        src = n if n.get("echantillons") and n.get("positifs") is not None else t
        if not src.get("echantillons") or src.get("positifs") is None:
            return None
        return (src["positifs"], src["echantillons"])
    rl = derniers_releves(riposte["laboratoire"].get("parDate"), labo_du_jour)
    if rl:
        positifs = sum(v[0] for _, v in rl)
        echantillons = sum(v[1] for _, v in rl)
        out["ripPositivite"] = fmt_cfr(round(positifs / echantillons * 100, 1), lang)
        sub = interp(strings_lang["riposteKpiPositiviteSub"], {
            "positifs": fmt(positifs, lang), "echantillons": fmt(echantillons, lang)})
        out["ripPositiviteSub"] = esc(sub + periode(rl))
    else:
        out["ripPositivite"], out["ripPositiviteSub"] = vide["value"], vide["sub"]

    # Contacts : vus cumules sur a-suivre cumules quand les sept releves
    # portent les effectifs (la moyenne ponderee, celle qui a un sens :
    # 21 109 sur 25 015 pese plus que 413 sur 413) ; a defaut, la moyenne
    # simple des taux publies, sans effectifs en sous-titre.
    def contacts_du_jour(p):
        if p.get("contactsFollowUpRate") is None:
            return None
        eff = p.get("contacts") or {}
        return (p["contactsFollowUpRate"], eff.get("vus"), eff.get("aSuivre"))
    rc = derniers_releves(riposte["contacts"] if isinstance(riposte["contacts"], list) else [],
                          contacts_du_jour)
    if rc:
        if all(v[1] is not None and v[2] for _, v in rc):
            vus = sum(v[1] for _, v in rc)
            a_suivre = sum(v[2] for _, v in rc)
            taux = round(vus / a_suivre * 100, 1)
            sub = interp(strings_lang["riposteKpiContactsSub"], {
                "vus": fmt(vus, lang), "aSuivre": fmt(a_suivre, lang)})
        else:
            taux = round(sum(v[0] for _, v in rc) / len(rc), 1)
            sub = ""
        out["ripContacts"] = fmt_cfr(taux, lang)
        out["ripContactsSub"] = esc(sub + periode(rc))
    else:
        out["ripContacts"], out["ripContactsSub"] = vide["value"], vide["sub"]

    k = dernier(riposte["cte"], garde=lambda p: (p.get("total") or {}).get("occupation") is not None)
    if k:
        t = k["total"]
        out["ripOccupation"] = fmt_cfr(t["occupation"], lang)
        sub = interp(strings_lang["riposteKpiOccupationSub"], {
            "hospitalises": fmt(t.get("hospitalisesAvecLits"), lang), "lits": fmt(t.get("lits"), lang)})
        out["ripOccupationSub"] = esc(sub + au(k["date"]))
    else:
        out["ripOccupation"], out["ripOccupationSub"] = vide["value"], vide["sub"]

    out.update(vaccination_seed(riposte.get("piliers"), date_bulletin, lang,
                                strings_lang, i18n_lang, vide, au))

    out["ripAsOf"] = esc(interp(strings_lang["cartoAsOf"],
                                {"date": long_date(date_bulletin or "", i18n_lang)}))
    return {"seed.%s" % k: v for k, v in out.items()}


# Les provinces qui ne vaccinent pas encore, dans l'ordre ou la page les cite :
# celles qui ont commence d'abord, puis celles qui s'y preparent.
def vaccination_seed(piliers, date_bulletin, lang, strings_lang, i18n_lang, vide, au):
    """Les trois chiffres du cadre « La vaccination » et l'etat des provinces.

    Le cumul national additionne le DERNIER cumul connu de chaque province,
    comme la lettre : le Bas-Uele ne publie pas tous les jours, et son 708 du
    17 septembre vaut encore le 18. La couverture reste celle de la seule
    province qui publie une cible — il n'existe pas de cible nationale, et en
    inventer une en sommant les cibles connues donnerait un taux flatteur
    calcule sur les seules provinces avancees."""
    out = {}
    points = (piliers or {}).get("parDate") or []
    dernier = {}
    for p in points:
        for prov, v in (((p.get("vaccination") or {}).get("provinces")) or {}).items():
            if v.get("cumul") is not None:
                dernier[prov] = dict(v, date=p["date"])
    if not dernier:
        out["ripVaccines"], out["ripVaccinZones"] = vide["value"], ""
        return out

    total = sum(v["cumul"] for v in dernier.values())
    ordre = sorted(dernier, key=lambda n: -dernier[n]["cumul"])
    # Le dernier total national publie l'emporte tant que la somme des
    # provinces ne le depasse pas (choix de Fable, 7 octobre 2026).
    nats = [p["vaccination"]["national"] for p in points
            if (p.get("vaccination") or {}).get("national") is not None]
    if nats and nats[-1] > total:
        total = nats[-1]
    out["ripVaccines"] = fmt(total, lang)

    # Le detail par zone de sante, toutes provinces confondues, de la plus
    # vaccinee a la moins vaccinee. Chaque province porte la date de SON
    # dernier releve : le Bas-Uele ne publie pas tous les jours, et sa
    # ventilation du 17 vaut encore le 18.
    lignes = []
    for n in ordre:
        for zone, nb in (dernier[n].get("zones") or {}).items():
            lignes.append((zone, n, nb, dernier[n]["date"]))
    lignes.sort(key=lambda l: -l[2])
    if lignes:
        corps = "".join(
            "<tr><td>%s</td><td>%s</td><td class=\"is-num\">%s</td></tr>"
            % (esc(zone), esc(prov), fmt(nb, lang))
            for zone, prov, nb, date in lignes)
        # Le cadre n'existe que s'il y a un tableau : sans detail par zone dans
        # les derniers releves, il restait une case blanche vide (7 oct. 2026).
        out["ripVaccinZones"] = (
            '<div class="panel vaccin-zones">'
            '<table class="province-summary vaccin-table">'
            '<thead><tr><th>%s</th><th>%s</th><th class="is-num">%s</th></tr></thead>'
            '<tbody>%s</tbody></table>'
            '<p class="map-note vaccin-table-note">%s</p>'
            % (esc(strings_lang["riposteVaccinTableZone"]),
               esc(strings_lang["riposteVaccinTableProvince"]),
               esc(strings_lang["riposteVaccinTableN"]), corps,
               esc(strings_lang["riposteVaccinTableLegende"]))) + '</div>'
    else:
        out["ripVaccinZones"] = ""

    return out


# Provinces sans les deux cases de riposte en tete de page (decision du
# proprietaire, 16 septembre 2026) : trop peu de cas pour que le taux de
# contacts ou l'occupation des CTE disent quelque chose, et des series
# interrompues (Sud-Kivu depuis le 5 aout, rien pour les CTE du Bas-Uele et du
# Sud-Ubangi).
PROVINCES_SANS_CASES_RIPOSTE = {"Bas-Uélé", "Sud-Kivu", "Sud-Ubangi"}


def province_riposte_seed(riposte, name, meta_data, lang, strings_lang, i18n_lang):
    """Contacts vus et occupation des CTE d'UNE province, pour ses cases de tete
    (demande du proprietaire, 16 septembre 2026).

    Memes regles que les cases nationales de `riposte_seed` : les contacts
    cumulent les sept derniers releves ou la province publie son taux (vus
    sur a-suivre quand les sept portent les effectifs, sinon moyenne simple
    des taux) ; l'occupation reste la valeur du dernier releve, datee si ce
    n'est pas le dernier bulletin. Une province sans donnee affiche « non
    publie ». Le Nord-Kivu n'a pas publie son nombre de lits du 10 au
    14 septembre : son sous-titre ne donne alors que les hospitalises. Depuis
    le 15, le taux qu'il imprime ne porte plus que sur ses structures normees
    et le site retablit la definition constante (tous les hospitalises sur les
    228 lits) : le sous-titre redevient « 392 hospitalises pour 228 lits »."""
    date_bulletin = meta_data.get("reportingDate")
    au = lambda d: "" if (not d or d == date_bulletin) else " · " + interp(
        strings_lang["riposteKpiAsOf"], {"date": long_date(d, i18n_lang)})
    out = {}

    releves = []
    for pt in reversed(riposte["contacts"] if isinstance(riposte["contacts"], list) else []):
        v = (pt.get("provinces") or {}).get(name) or {}
        if v.get("taux") is None:
            continue
        releves.append(dict(v, date=pt["date"]))
        if len(releves) == 7:
            break
    if releves:
        if all(v.get("vus") is not None and v.get("aSuivre") for v in releves):
            vus = sum(v["vus"] for v in releves)
            a_suivre = sum(v["aSuivre"] for v in releves)
            taux = round(vus / a_suivre * 100, 1)
            sub = interp(strings_lang["riposteKpiContactsSub"],
                         {"vus": fmt(vus, lang), "aSuivre": fmt(a_suivre, lang)})
        else:
            taux, sub = round(sum(v["taux"] for v in releves) / len(releves), 1), ""
        # Datee quand la province a cesse de publier : le Sud-Kivu s'arrete
        # au 5 aout, et son 100 % se lisait comme un chiffre du jour.
        out["province.ripContacts"] = fmt_cfr(taux, lang)
        out["province.ripContactsSub"] = esc((sub + au(releves[0]["date"])).lstrip(" ·"))
    else:
        out["province.ripContacts"] = "—"
        out["province.ripContactsSub"] = esc(strings_lang["riposteKpiNone"])

    k = None
    for pt in reversed(riposte["cte"].get("parDate", [])):
        v = (pt.get("provinces") or {}).get(name) or {}
        if v.get("occupation") is not None:
            k = (pt["date"], v)
            break
    if k:
        date, v = k
        if v.get("lits") and v.get("hospitalises") is not None:
            sub = interp(strings_lang["riposteKpiOccupationSub"],
                         {"hospitalises": fmt(v["hospitalises"], lang), "lits": fmt(v["lits"], lang)})
        elif v.get("hospitalises") is not None:
            sub = interp(strings_lang["provinceKpiOccupationSubSansLits"],
                         {"hospitalises": fmt(v["hospitalises"], lang)})
        else:
            sub = ""
        out["province.ripOccupation"] = fmt_cfr(v["occupation"], lang)
        out["province.ripOccupationSub"] = esc((sub + au(date)).lstrip(" ·"))
    else:
        out["province.ripOccupation"] = "—"
        out["province.ripOccupationSub"] = esc(strings_lang["riposteKpiNone"])
    if name in PROVINCES_SANS_CASES_RIPOSTE:
        return dict(out, **{"province.ripKpis": "", "province.ripKpisClass": ""})
    return dict(out, **{
        "province.ripKpisClass": " has-riposte",
        "province.ripKpis": (
            '      <div class="kpi contacts">\n'
            '        <div class="label">%s</div>\n'
            '        <div class="value">%s</div>\n'
            '        <div class="delta">%s</div>\n'
            '      </div>\n'
            '      <div class="kpi cte">\n'
            '        <div class="label">%s</div>\n'
            '        <div class="value">%s</div>\n'
            '        <div class="delta">%s</div>\n'
            '      </div>\n'
            % (esc(strings_lang["riposteKpiContacts"]), out["province.ripContacts"], out["province.ripContactsSub"],
               esc(strings_lang["riposteKpiOccupation"]), out["province.ripOccupation"], out["province.ripOccupationSub"]))})


# --------------------------------------------------------------------------
# La fiche d'un territoire (28 septembre 2026)
#
# Le pays et chaque province suivent desormais le meme plan, a deux echelles :
# le point (chiffres cles et sept derniers jours), [carte], cas, deces (et le
# lieu du deces dessous), ou, [qui], la riposte, la chronologie. Demande du
# proprietaire apres l'avis du 28 septembre : « j'ai l'impression de devenir
# confus sur comment agencer toutes ces infos ». La regle qui en sort : une
# information a UNE page qui la detaille — les graphiques de la riposte vivent
# sur la page Riposte, ou l'on compare les provinces ; la fiche n'en garde que
# les chiffres et les difficultes du dernier bulletin, avec les liens.
# --------------------------------------------------------------------------

def point_sept_jours(serie):
    """{cas, deces, casAvant, decesAvant} sur deux fenetres de 7 jours
    CALENDAIRES, a partir d'une serie cumulee [(date, cas, deces)]. Le cumul
    retenu pour une date est le dernier releve a cette date ou avant : un jour
    sans bulletin ne compte ni zero ni double. None si l'une des bornes manque
    (province trop recente pour deux semaines pleines)."""
    serie = sorted((r for r in serie if r[0]), key=lambda r: r[0])
    if len(serie) < 2:
        return None
    fin = date.fromisoformat(serie[-1][0])

    def cumul(i, jours):
        borne = (fin - timedelta(days=jours)).isoformat()
        v = None
        for r in serie:
            if r[0] > borne:
                break
            if r[i] is not None:
                v = r[i]
        return v
    out = {}
    for i, cle in ((1, "cas"), (2, "deces")):
        a, b, c = cumul(i, 0), cumul(i, 7), cumul(i, 14)
        if a is None or b is None or c is None:
            return None
        out[cle], out[cle + "Avant"] = max(0, a - b), max(0, b - c)
    return out


def fiche_point_html(serie, lang, strings_lang):
    p = point_sept_jours(serie)
    if not p:
        return ""
    return '<p class="page-intro fiche-point">%s</p>' % esc(interp(
        strings_lang["fichePoint"], {k: fmt(v, lang) for k, v in p.items()}))


PHRASE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Ý])")


def difficultes_province(texte, name):
    """Les phrases du resume des Defis qui parlent de la province. Le resume
    est ecrit a la main a chaque bulletin, UNE phrase par province, ouverte
    par son nom (« Au Nord-Kivu, … », « In Nord-Kivu, … », « Nord-Kivu, … ») :
    le nom dans les quarante premiers caracteres suffit a la reconnaitre."""
    phrases = [x.strip() for x in PHRASE_RE.split(texte or "") if x.strip()]
    return " ".join(x for x in phrases if name in x[:40])


CHAINE_RIPOSTE = [("alerts", "ripVerbe1"), ("labo", "ripVerbe2"), ("contacts", "ripVerbe3"),
                  ("cte", "ripVerbe4"), ("vaccin", "ripVerbe5")]


def chaine_riposte_html(kpis, strings_lang):
    """La chaine de la page Riposte (signaler, tester, suivre, soigner,
    proteger) pour les pages province (7 octobre 2026) : les cases connues,
    dans l'ordre de la chaine, chacune renvoyant a son volet."""
    par = {k[0]: k for k in kpis}
    cases = []
    for cls, verbe in CHAINE_RIPOSTE:
        if cls in par:
            _, label, val, sub = par[cls]
            cases.append('<a class="rc-e" href="#rip-%s"><span class="rc-v">%s</span><b class="rc-n is-%s">%s</b><em>%s</em>%s</a>'
                         % (cls, esc(strings_lang[verbe]), cls, val, label, ("<small>%s</small>" % sub) if sub else ""))
    return ('      <div class="rc-chaine">%s</div>\n' % '<i aria-hidden="true">→</i>'.join(cases)) if cases else ""


def fiche_riposte_html(numero, kpis, difficultes, source, liens, strings_lang,
                       graphiques="", extraits="", avec_defis=True, sous_titre=None, chaine=False):
    """Le cadre « La riposte » d'une fiche : des chiffres (liste de
    (classe, libelle, valeur, sous-titre), deja echappes), les difficultes du
    dernier bulletin, leur source, puis les liens vers la page qui detaille."""
    cases = "".join(
        '        <div class="kpi %s">\n          <div class="label">%s</div>\n'
        '          <div class="value">%s</div>\n          <div class="delta">%s</div>\n        </div>\n'
        % k for k in kpis)
    bloc_kpis = '      <div class="kpis riposte-kpis">\n%s      </div>\n' % cases if kpis else ""
    if chaine:
        bloc_kpis = chaine_riposte_html(kpis, strings_lang)
    if not avec_defis:
        # Ni resume des difficultes, ni source, ni extraits pilier par pilier
        # (29 septembre 2026, demande du proprietaire) : les difficultes ont
        # leur cadre sur les pages province, et la page Riposte les detaille.
        # Ne jamais ecrire « resume ... redige par ebola-tracker.org ».
        # Les liens ne servent qu'au pays (vers la page Riposte).
        return (
            '  <section class="section cadre-fiche%s" id="riposte">\n'
            '    <div class="fiche-tete"><span class="fiche-num">%s</span><div><h2 class="frame-title">%s</h2>'
            '<div class="section-sub">%s</div></div></div>\n'
            '    <div class="cadre-corps">\n%s%s%s%s'
            '    </div>\n  </section>\n'
            % (" fiche-centree" if chaine else "", esc(numero), esc(strings_lang["ficheRiposteTitle"]),
               esc(sous_titre or strings_lang["ficheRiposteSub"]),
               # Ce qu'est la riposte, en une phrase sous le titre (7 octobre
               # 2026, demande de Fable).
               '      <p class="fiche-texte fiche-texte-centre">%s</p>\n' % esc(strings_lang["ficheRiposteLede"]),
               bloc_kpis, graphiques,
               '      <p class="drill">%s</p>\n' % " · ".join(
                   '<a href="%s">%s →</a>' % (esc(h), esc(t)) for h, t in liens) if liens else ""))
    return (
        '  <section class="section cadre-fiche" id="riposte">\n'
        '    <div class="fiche-tete"><span class="fiche-num">%s</span><div><h2 class="frame-title">%s</h2>'
        '<div class="section-sub">%s</div></div></div>\n'
        '    <div class="cadre-corps">\n%s%s'
        '      <h3 class="frame-title fiche-sous-titre">%s</h3>\n'
        '      <p class="fiche-texte">%s</p>\n'
        '      <p class="map-note">%s</p>\n%s'
        '      <p class="drill">%s</p>\n'
        '    </div>\n  </section>\n'
        % (esc(numero), esc(strings_lang["ficheRiposteTitle"]), esc(strings_lang["ficheRiposteSub"]),
           bloc_kpis, graphiques, esc(strings_lang["ficheDifficultesTitle"]), esc(difficultes), esc(source),
           extraits,
           " · ".join('<a href="%s">%s →</a>' % (esc(h), esc(t)) for h, t in liens)))


def _cadre_vaccination_seule(province, riposte, meta_data, lang, strings_lang, i18n_lang):
    """Le cadre « La riposte » des provinces qui vaccinent sans avoir la fiche
    complete (Tshopo, Bas-Uele ; 29 septembre 2026) : le chiffre des personnes
    vaccinees, puis la courbe de la vaccination de la province."""
    nom = province["name"]
    if nom not in VACCIN_PROVINCES or a_une_riposte(province):
        return ""
    vac, vac_sub = vaccines_province(riposte, nom, meta_data, lang, strings_lang, i18n_lang)
    # Un seul volet : son chiffre va a cote du graphique, sans chaine.
    graph = riposte_graphiques_province(riposte, nom, lang, strings_lang, i18n_lang, seulement={"vaccination"},
                                        chiffres={"vaccination": (vac, esc(strings_lang["ficheKpiVaccines"]), vac_sub)})
    return fiche_riposte_html(
        province_numeros(province)["riposte"], [], "", "", [], strings_lang,
        graphiques=graph, avec_defis=False, sous_titre=strings_lang["ficheRiposteSubVaccin"], chaine=True)


# La riposte developpee sur la fiche (28 septembre 2026, demande du
# proprietaire : « que chaque page province, en commencant par les 4 plus
# affectees, ait sur sa propre page la partie riposte/defis developpee, qui
# inclut notamment les graphiques »). Les memes graphiques que la page
# Riposte, restreints a la province par data-province, dans l'ordre de la
# chaine : signaler, tester, suivre, soigner, prevenir. Un graphique ne
# s'affiche que si la province a au moins RELEVES_MIN_GRAPHIQUE releves de sa
# serie (3 pour la vaccination, qui ne publie que des cumuls) : sinon un
# cadre presque vide se lirait comme une panne.
RELEVES_MIN_GRAPHIQUE = 10

PROVINCE_MARQUEUR_RE = re.compile(
    r"^(?:en|au|aux|à\s+la|a\s+la|dans\s+la|dans\s+le)\s+"
    r"(Ituri|Nord[\s-]Kivu|Haut[\s-]U[ée]l[ée]|Tshopo|Sud[\s-]Kivu|Bas[\s-]U[ée]l[ée]|Sud[\s-]Ubangi)\b",
    re.IGNORECASE)
PROVINCE_NOM_RE = re.compile(
    r"\b(Ituri|Nord[\s-]Kivu|Haut[\s-]U[ée]l[ée]|Tshopo|Sud[\s-]Kivu|Bas[\s-]U[ée]l[ée]|Sud[\s-]Ubangi)\b",
    re.IGNORECASE)


def _canon_prov(nom):
    n = re.sub(r"[\s-]+", "-", nom.strip())
    for c in PROVINCE_COLORS:
        if c.lower().replace("é", "e") == n.lower().replace("é", "e"):
            return c
    return n


def _propositions(item):
    """Coupe un bloc en propositions aux « ; », aux points et aux « : » suivis
    d'une province, JAMAIS a l'interieur d'une parenthese — « (50,0 % ; 1/2) »
    reste entier."""
    morceaux, cour, prof, i = [], "", 0, 0
    while i < len(item):
        c = item[i]
        prof += (c == "(") - (c == ")")
        coupe = prof == 0 and (c == ";" or (c in ".:" and item[i + 1:i + 2] == " "))
        if coupe and c == ":" and not PROVINCE_MARQUEUR_RE.match(item[i + 1:].lstrip()):
            coupe = False
        if coupe:
            morceaux.append(cour); cour = ""
        else:
            cour += c
        i += 1
    morceaux.append(cour)
    return [m.strip(" .;:") for m in morceaux if m.strip(" .;:")]


def extraits_defis_province(defis, name, zone_prov=None):
    """[(pilier, texte)] : ce que les blocs « Defis » du DERNIER bulletin
    disent de la province, cites tels quels. Un bloc melange souvent les
    provinces (« En Ituri, … ; au Nord-Kivu, … ») : il est coupe en
    propositions (point-virgule, point, deux-points), chacune rattachee a la
    province qu'elle ouvre (« Au Nord-Kivu, … »), a defaut a la seule
    province qu'elle nomme, a defaut a la province en cours."""
    points = (defis or {}).get("parDate") or []
    if not points:
        return [], None
    dernier = points[-1]
    out = []
    for pil in dernier.get("piliers", []):
        garde = []
        for item in pil.get("items", []):
            courante = None
            for prop in _propositions(item):
                m = PROVINCE_MARQUEUR_RE.match(prop)
                noms = {_canon_prov(x) for x in PROVINCE_NOM_RE.findall(prop)}
                # Une zone de sante nommee vaut sa province : « ruptures de
                # medicaments a Boma Mangbetu, Isiro, Wamba et Pawa » est un
                # defi du Haut-Uele sans que le bulletin le dise.
                for zone, prov in (zone_prov or {}).items():
                    if re.search(r"\b%s\b" % re.escape(zone), prop):
                        noms.add(prov)
                if m:
                    courante = _canon_prov(m.group(1))
                elif len(noms) == 1:
                    courante = next(iter(noms))
                # Une proposition qui nomme des provinces leur appartient
                # (« absence de donnees du Bas-Uele et du Haut-Uele » n'est
                # pas un defi de l'Ituri) ; sinon elle continue la courante.
                if (name in noms) if noms else (courante == name):
                    garde.append(prop)
        if garde:
            texte = " ; ".join(garde)
            out.append((pil.get("titre", ""), texte[0].upper() + texte[1:] + "."))
    return out, dernier.get("sitrepNumber")


def extraits_defis_html(extraits, num, strings_lang):
    if not extraits:
        return ""
    items = "".join('        <li><b>%s.</b> %s</li>\n' % (esc(t), esc(x)) for t, x in extraits)
    return ('      <details class="maq-methode fiche-extraits">\n'
            '        <summary>%s</summary>\n'
            '        <ul class="fiche-extraits-liste">\n%s        </ul>\n'
            '        <p class="map-note">%s</p>\n'
            '      </details>\n'
            % (esc(strings_lang["ficheDefisCitesTitle"]), items,
               esc(interp(strings_lang["ficheDefisCitesNote"], {"num": num or ""}))))


def _releves(serie, name, cle):
    pts = serie.get("parDate", []) if isinstance(serie, dict) else (serie or [])
    return sum(1 for p in pts if ((p.get("provinces") or {}).get(name) or {}).get(cle) is not None)


def vaccin_zones_province_html(piliers, name, lang, strings_lang, i18n_lang):
    pts = (piliers or {}).get("parDate") or []
    der = None
    for p in pts:
        v = (((p.get("vaccination") or {}).get("provinces")) or {}).get(name) or {}
        if v.get("zones"):
            der = (p["date"], v["zones"])
    if not der:
        return ""
    date_z, zones = der
    corps = "".join('<tr><td>%s</td><td class="is-num">%s</td></tr>' % (esc(z), fmt(n, lang))
                    for z, n in sorted(zones.items(), key=lambda kv: -kv[1]))
    return ('      <div class="panel vaccin-zones">\n'
            '        <table class="province-summary vaccin-table"><thead><tr><th>%s</th><th class="is-num">%s</th></tr></thead>'
            '<tbody>%s</tbody></table>\n'
            '        <p class="map-note vaccin-table-note">%s</p>\n      </div>\n'
            % (esc(strings_lang["riposteVaccinTableZone"]), esc(strings_lang["riposteVaccinTableN"]), corps,
               esc(interp(strings_lang["riposteKpiAsOf"], {"date": long_date(date_z, i18n_lang)}))))


def riposte_graphiques_province(riposte, name, lang, strings_lang, i18n_lang, seulement=None, chiffres=None):
    """Les graphiques de la page Riposte, restreints a la province. Depuis le
    7 octobre 2026, chaque volet a la mise en page de la page Riposte : a
    gauche le titre, le chiffre cle (chiffres[mode] = (valeur, libelle,
    precision)) et l'explication ; a droite le graphique."""
    chiffres = chiffres or {}
    def nav(canvas_id, vues):
        return ('        <nav class="subtab-nav chart-vue-nav" data-chart-vue="%s">\n%s        </nav>\n'
                % (canvas_id, "".join(
                    '          <button type="button" class="subtab-btn%s" data-vue="%s" data-i18n="%s">%s</button>\n'
                    % (" active" if i == 0 else "", v, k, esc(i18n_lang[k])) for i, (v, k) in enumerate(vues))))

    def lede(cle):
        # Le paragraphe explicatif de la page Riposte, repris tel quel sous
        # chaque titre (29 septembre 2026, demande du proprietaire).
        t = strings_lang.get(cle)
        return '      <p class="fiche-texte">%s</p>\n' % esc(t) if t else ""

    CLASSE = {"alertes": "alerts", "laboratoire": "labo", "contactsRiposte": "contacts", "cte": "cte", "vaccination": "vaccin"}

    def bloc(titre, sous_titre, canvas_id, mode, vues=None, apres=""):
        ch = chiffres.get(mode)
        cle = ('        <div class="rp-ch"><b class="rc-n is-%s">%s</b><span>%s</span><small>%s</small></div>\n'
               % (CLASSE.get(mode, ""), ch[0], ch[1], ch[2])) if ch else ""
        return ('      <div class="rp-v" id="rip-%s"><div class="rp-g">\n'
                '        <h3>%s</h3>\n        <p class="rp-sub">%s</p>\n%s%s'
                '      </div><div class="rp-d">\n'
                '      <div class="panel chart-panel-wrap">\n%s%s'
                '        <div class="chart-panel">\n'
                '          <canvas id="%s" data-chart="%s" data-province="%s"></canvas>\n'
                '        </div>\n        <div class="map-note chart-note"></div>\n      </div>\n%s'
                '      </div></div>\n'
                % (CLASSE.get(mode, mode), esc(strings_lang[titre]), esc(strings_lang[sous_titre]), cle,
                   lede(titre.replace("Title", "Lede")),
                   BOUTON_PARTAGE % (canvas_id, esc(i18n_lang["chartShareBtn"])),
                   nav(canvas_id, vues) if vues else "", canvas_id, mode, esc(name), apres))

    out = []
    def voulu(mode):
        return seulement is None or mode in seulement

    if voulu("alertes") and _releves(riposte["alertes"], name, "recues") >= RELEVES_MIN_GRAPHIQUE:
        out.append(bloc("riposteAlertesTitle", "riposteAlertesSub", "provAlertesChart", "alertes",
                        [("jour", "chartVueDaily"), ("volume", "chartVueWeekly"), ("taux", "chartVueTaux")]))
    if voulu("laboratoire") and _releves(riposte["laboratoire"], name, "echantillons") >= RELEVES_MIN_GRAPHIQUE:
        out.append(bloc("riposteLaboTitle", "riposteLaboSub", "provLaboChart", "laboratoire",
                        [("jour", "chartVueDaily"), ("semaine", "chartVueWeekly")]))
    contacts = riposte["contacts"] if isinstance(riposte["contacts"], list) else []
    if voulu("contacts") and sum(1 for p in contacts if ((p.get("provinces") or {}).get(name) or {}).get("taux") is not None) >= RELEVES_MIN_GRAPHIQUE:
        out.append(bloc("riposteContactsTitle", "riposteContactsSub", "provContactsChart", "contactsRiposte"))
    if voulu("cte") and _releves(riposte["cte"], name, "hospitalises") >= RELEVES_MIN_GRAPHIQUE:
        out.append(bloc("riposteCteTitle", "riposteCteSub", "provCteChart", "cte"))
    pil = riposte["piliers"]
    pts = pil.get("parDate", []) if isinstance(pil, dict) else []
    n_vacc = sum(1 for p in pts if ((p.get("vaccination") or {}).get("cumulParProvince") or {}).get(name))
    zones = vaccin_zones_province_html(pil, name, lang, strings_lang, i18n_lang)
    # Deux releves suffisent depuis le 29 septembre 2026 : l'Ituri a publie ses
    # premiers vaccines le 23 septembre, et le proprietaire veut la courbe
    # de toute province qui a commence.
    if n_vacc >= 2:
        # Le tableau des zones vaccinees n'est plus pose sous la courbe
        # (7 octobre 2026, demande de Fable) ; il ne reste que si la province
        # n'a pas encore de courbe (branche suivante).
        out.append(bloc("riposteVaccinTitle", "riposteVaccinSub", "provVaccinChart", "vaccination"))
    elif zones:
        out.append('      <div class="section-head" style="margin-top:32px;">\n'
                   '        <h3 class="frame-title">%s</h3>\n        <span class="section-sub">%s</span>\n      </div>\n%s%s'
                   % (esc(strings_lang["riposteVaccinTitle"]), esc(strings_lang["riposteVaccinSub"]),
                      lede("riposteVaccinLede"), zones))
    return "".join(out)


def alertes_province(riposte, name, lang, strings_lang):
    """Alertes recues sur les 7 derniers releves de la province, et celles
    validees comme cas suspects : la case « Signaler » de la chaine des pages
    province (7 octobre 2026), calculee comme la case nationale."""
    releves = []
    for pt in reversed(riposte["alertes"].get("parDate", [])):
        v = (pt.get("provinces") or {}).get(name) or {}
        if v.get("recues") is not None:
            releves.append(v)
            if len(releves) == 7:
                break
    if not releves:
        return None
    validees = [v.get("validees") for v in releves if v.get("validees") is not None]
    sub = interp(strings_lang["riposteKpiAlertesSub"], {"validees": fmt(sum(validees), lang)}) \
        if len(validees) == len(releves) else ""
    return fmt(sum(v["recues"] for v in releves), lang), esc(sub)


def positivite_province(riposte, name, lang, strings_lang):
    """Positivite des 7 derniers releves de la province : positifs cumules sur
    echantillons cumules, comme la case nationale."""
    releves = []
    for pt in reversed(riposte["laboratoire"].get("parDate", [])):
        v = (pt.get("provinces") or {}).get(name) or {}
        if v.get("echantillons") and v.get("positifs") is not None:
            releves.append(v)
            if len(releves) == 7:
                break
    if not releves:
        return "—", esc(strings_lang["riposteKpiNone"])
    pos = sum(v["positifs"] for v in releves)
    ech = sum(v["echantillons"] for v in releves)
    return (fmt_cfr(round(pos / ech * 100, 1), lang),
            esc(interp(strings_lang["riposteKpiPositiviteSub"],
                       {"positifs": fmt(pos, lang), "echantillons": fmt(ech, lang)})))


def vaccines_province(riposte, name, meta_data, lang, strings_lang, i18n_lang):
    """Dernier cumul de vaccines publie pour la province (le bulletin ne
    publie que des cumuls), date quand il n'est pas du dernier bulletin."""
    pts = riposte["piliers"]
    pts = pts.get("parDate", pts) if isinstance(pts, dict) else pts
    if isinstance(pts, dict):
        pts = [dict(v, date=v.get("date", k)) for k, v in sorted(pts.items())]
    for pt in reversed(pts or []):
        v = ((pt.get("vaccination") or {}).get("cumulParProvince") or {}).get(name)
        if v:
            # Toujours date : c'est un cumul, et la province peut avoir
            # cesse de le publier depuis plusieurs bulletins.
            d = pt.get("date")
            return fmt(v, lang), esc(interp(strings_lang["riposteKpiAsOf"],
                                            {"date": long_date(d, i18n_lang)}))
    return "—", esc(strings_lang["riposteKpiNone"])


def head_assets(needs):
    tags = []
    if "leaflet" in needs:
        tags.append('<link rel="stylesheet" '
                    'href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">')
        tags.append('<script defer '
                    'src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>')
    if "chart" in needs:
        tags.append('<script defer '
                    'src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>')
    # La base de donnees (9 octobre 2026) : sa feuille et son script a part.
    if "base" in needs:
        tags.append('<link rel="stylesheet" href="/assets/css/base.css?v=%s">' % jeton_version("assets/css/base.css"))
        tags.append('<script defer src="/assets/js/base.js?v=%s"></script>' % jeton_version("assets/js/base.js"))
    return "\n".join(tags)


BASE = None


def base_values(config, urls, lang, strings_lang, i18n_lang, latest_reports):
    """Ce que le generateur ecrit en dur dans la page Base de donnees : le
    resume, le tableau du dernier bulletin (pays et provinces), la liste des
    bulletins absents, la liste des zones et la citation. C'est le texte que
    lisent les moteurs de recherche ; base.js remplace le tableau par la base
    complete au chargement."""
    lignes, dates = BASE["lignes"], BASE["dates"]
    derniere = dates[-1]
    nums = sorted({int(r["sitrepNumber"]) for r in latest_reports if str(r.get("sitrepNumber", "")).isdigit()})
    manquants = [str(i).zfill(3) for i in range(1, nums[-1] + 1) if i not in nums] if nums else []
    jour = [o for o in lignes if o["date"] == derniere and o["niveau"] in ("pays", "province") and o.get("cas") is not None]
    jour.sort(key=lambda o: (o["niveau"] != "pays", -(o.get("cas") or 0)))
    def nouv(v):
        return "" if v is None else ("+" if v >= 0 else "−") + fmt(abs(v), lang)
    rangs = []
    for o in jour:
        nom = {"fr": "RDC"}.get(lang, "DRC") if o["niveau"] == "pays" else o["province"]
        lien = (urls.province_path(o["province"], lang) if o["niveau"] == "province" and o["province"] in config["provinceSlugs"]
                else urls.path("donnees", lang))
        rangs.append('          <tr class="%s"><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                     % ("is-pays" if o["niveau"] == "pays" else "", esc(lien), esc(nom), fmt(o.get("cas"), lang),
                        nouv(o.get("nouveaux_cas")), fmt(o.get("deces"), lang), fmt_cfr(o.get("letalite"), lang)))
    par_prov = {}
    for prov, zone in BASE["zones"]:
        par_prov.setdefault(prov, []).append(zone)
    zones_html = "".join(
        '        <p><a href="%s"><b>%s</b></a> : %s</p>\n'
        % (esc(urls.province_path(p, lang) if p in config["provinceSlugs"] else urls.path("donnees", lang)), esc(p),
           esc(", ".join(sorted(zs))))
        for p, zs in sorted(par_prov.items(), key=lambda x: -len(x[1])))
    rapports = {r["sitrepNumber"] for r in latest_reports}
    cfg = {"lang": lang, "contact": urls.path("contact", lang),
           "provinces": {p: urls.province_path(p, lang) for p in config["provinceSlugs"]}}
    return {
        "bdd.resume": esc(interp(strings_lang["bddResume"], {
            "lignes": fmt(len(lignes), lang), "bulletins": fmt(len(rapports), lang),
            "zones": fmt(len(BASE["zones"]), lang), "debut": long_date(dates[0], i18n_lang),
            "fin": long_date(derniere, i18n_lang)})),
        "bdd.dernierTitre": esc(interp(strings_lang["bddDernier"], {"date": long_date(derniere, i18n_lang)})),
        "bdd.dernierLignes": "\n".join(rangs),
        "bdd.manquants": esc(interp(strings_lang["bddN3"], {"liste": ", ".join(manquants)})),
        "bdd.zonesTitre": esc(interp(strings_lang["bddZonesT"], {"n": fmt(len(BASE["zones"]), lang)})),
        "bdd.zones": zones_html,
        "bdd.citation": esc(interp(strings_lang["bddCite"], {"date": long_date(date.today().isoformat(), i18n_lang)})),
        "bdd.config": json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"),
    }


def dashboard_values(config, urls, lang, strings_lang, i18n_lang, alt_paths,
                     national, meta_data, provinces):
    """Ce que le generateur ecrit dans le tableau de bord (9 octobre 2026) :
    la phrase de situation (le texte que lisent les moteurs de recherche, que
    dashboard.js remplace au chargement), le selecteur de langue et, en JSON,
    les adresses dans la langue de la page."""
    zones = national.get("healthZonesAffected") or {}
    resume = interp(strings_lang["dbResume"], {
        "date": long_date(meta_data.get("reportingDate"), i18n_lang),
        "num": str(int(meta_data.get("sitrepNumber") or 0)),
        "cases": fmt(national.get("confirmed"), lang), "deaths": fmt(national.get("deaths"), lang),
        "zones": fmt(zones.get("n"), lang), "provinces": fmt(national.get("provincesAffected"), lang)})
    cfg = {
        "lang": lang,
        "accueil": urls.path("accueil", lang),
        "ici": urls.path("dashboard", lang),
        "donnees": urls.path("donnees", lang),
        "autresPays": urls.path("autres-pays", lang),
        "provinces": {p["name"]: urls.province_path(p["name"], lang) for p in provinces},
        "pays": {p["pays"]: urls.path(p["id"], lang) for p in config["pages"] if p.get("pays")},
    }
    return {
        "db.resume": esc(resume),
        "db.langues": lang_switch_html(config, alt_paths, lang, strings_lang),
        # Dans un <script type="application/json"> : « </ » ne doit pas y
        # apparaitre, sans quoi le navigateur fermerait la balise.
        "db.config": json.dumps(cfg, ensure_ascii=False).replace("</", "<\\/"),
    }


def lettres_meta(config, strings):
    """Titre et description propres a chaque page /lettre/<num>/ (9 octobre
    2026, referencement) : les 56 lettres portaient la meme description, celle
    du modele. Date, numero et chiffres viennent de l'instantane
    data/lettres/<num>.json, comme la lettre elle-meme ; faute de chiffres du
    jour, la description ne garde que les totaux. La page /lettre/ (la
    derniere lettre) garde son titre, pour ne pas doubler celui de
    /lettre/<num>/, et prend une description a elle quand le jour est connu."""
    # Le tableau de bord (9 octobre 2026) : sa description porte la date de
    # situation du dernier bulletin, « Situation au {date} ».
    derniere = read_json(os.path.join(ROOT, "data", "latest.json"))["meta"]["reportingDate"]
    for page in config["pages"]:
        if page["id"] == "dashboard":
            for lang, meta in page["meta"].items():
                meta["description"] = interp(meta["description"], {"date": hors_rdc.date_longue(derniere, lang)})
            continue
        if page["id"] == "bulletin":
            snap = read_json(os.path.join(ROOT, "data", "latest.json"))
        elif page.get("lettreNum"):
            snap = read_json(os.path.join(ROOT, "data", "lettres", "%s.json" % page["lettreNum"]))
        else:
            continue
        nat, date = snap["national"], snap["meta"]["reportingDate"]
        for lang, meta in page["meta"].items():
            S = strings[lang]
            valeurs = {"num": str(int(snap["meta"]["sitrepNumber"])), "date": hors_rdc.date_longue(date, lang),
                       "cas": fmt(nat.get("confirmed"), lang), "deces": fmt(nat.get("deaths"), lang),
                       "jcas": fmt(nat.get("newCases24h"), lang), "jdeces": fmt(nat.get("newDeaths24h"), lang)}
            jour = nat.get("newCases24h") is not None and nat.get("newDeaths24h") is not None
            if page["id"] == "bulletin":
                if jour:
                    meta["description"] = interp(S["lettreHubDescription"], valeurs)
                continue
            meta["title"] = interp(S["lettreMetaTitle"], valeurs)
            meta["description"] = interp(S["lettreMetaDescription" if jour else "lettreMetaDescriptionTotal"], valeurs)


def main():
    config = read_json(os.path.join(SITE, "pages.json"))
    # Une page par lettre, /lettre/<num>/ (8 septembre 2026) : ajoutee
    # avant le calcul des URL pour que la navigation entre lettres les trouve.
    config["pages"] = config["pages"] + bulletin.pages_lettres(config)
    global SITE_LANGUAGES
    SITE_LANGUAGES = list(config["site"]["languages"])
    strings = read_json(os.path.join(SITE, "strings.json"))
    i18n = load_i18n()
    lettres_meta(config, strings)
    # La base de donnees unifiee : data/base-ebola-rdc.csv et .json, reecrits
    # a chaque generation depuis les fichiers du pipeline.
    global BASE
    BASE = base_donnees.ecrire(config["site"]["origin"])
    layout = read(os.path.join(SITE, "layout.html"))

    latest = read_json(os.path.join(ROOT, "data", "latest.json"))
    zones_history = read_json(os.path.join(ROOT, "data", "zones-history.json"))
    sitreps = read_json(os.path.join(ROOT, "data", "sitreps.json"))
    who_reports = read_json(os.path.join(ROOT, "data", "who-reports.json"))
    chemin_actus = os.path.join(ROOT, "data", "actus.json")
    actus = read_json(chemin_actus) if os.path.exists(chemin_actus) else {"items": []}
    social_updates = read_json(os.path.join(ROOT, "data", "social-updates.json"))
    province_history = read_json(os.path.join(ROOT, "data", "province-history.json"))
    # Repartition par age : instantane fige au 5 aout 2026, l'INSP ayant
    # cesse de publier la figure ensuite. Voir scripts/demographie_figures.py.
    demographie = read_json(os.path.join(ROOT, "data", "demographie.json"))
    # Genomes sequences (Pathoplexus, agregats) : data/genomes.json, a la main.
    genomes = read_json(os.path.join(ROOT, "data", "genomes.json"))
    # Les quatre series de la page « Riposte ». Chacune a sa profondeur et ses
    # trous ; la page ecrit le dernier point de chacune, avec sa date quand
    # elle n'est pas celle du bulletin.
    notes_bulletins = read_json(os.path.join(ROOT, "data", "bulletin-notes.json"))
    riposte = {
        "alertes": read_json(os.path.join(ROOT, "data", "alertes.json")),
        "laboratoire": read_json(os.path.join(ROOT, "data", "laboratoire.json")),
        "contacts": read_json(os.path.join(ROOT, "data", "contacts-followup.json")),
        "cte": read_json(os.path.join(ROOT, "data", "cte.json")),
        "defis": read_json(os.path.join(ROOT, "data", "defis.json")),
        "piliers": read_json(os.path.join(ROOT, "data", "piliers.json")),
    }
    VACCIN_PROVINCES.clear()
    VACCIN_PROVINCES.update(provinces_qui_vaccinent(riposte["piliers"]))
    # Traces des zones de sante : geometrie figee, produite a part par
    # scripts/build_geo.py. Elle ne change qu'en cas de nouvelle province
    # touchee ou de mise a jour de la source.
    geo = read_json(os.path.join(SITE, "geo", "zones-overview.json"))
    # Les alias ecrits a la main dans site/pages.json completent ceux que
    # build_geo.py a deduits : « Gety » (SitReps de juin) pour « Gethy », que
    # build_geo ne pouvait pas connaitre, latest.json ne l'ecrivant plus ainsi.
    geo["aliases"] = dict(geo.get("aliases", {}), **{
        normalise_zone(k): normalise_zone(v)
        for k, v in config.get("zoneAliases", {}).get("places", {}).items()})
    province_maps = read_json(os.path.join(SITE, "geo", "province-maps.json"))["maps"]

    national = latest.get("national") or {}
    meta_data = latest.get("meta") or {}
    # Trie une fois pour toutes, du plus touche au moins touche : la
    # navigation, le pied de page, les cartes et le tableau puisent tous dans
    # cette liste. Les trois derniers triaient chacun de leur cote, la
    # navigation prenait l'ordre du fichier — deux ordres possibles pour les
    # memes six provinces sur une meme page.
    provinces = sorted(
        [p for p in latest.get("provinces", [])
         if p.get("name") in config["provinceSlugs"]],
        key=lambda p: -(p.get("confirmed") or 0))
    unknown = [p["name"] for p in latest.get("provinces", [])
               if p.get("name") not in config["provinceSlugs"]]
    if unknown:
        print("  ! provinces sans slug, ignorées : %s" % ", ".join(unknown))

    zones_by_province = {}
    for zone in latest.get("healthZones", []):
        zones_by_province.setdefault(zone.get("province"), []).append(zone)

    urls = Urls(config)
    by_id = {p["id"]: p for p in config["pages"]}
    generated = []

    for lang in config["site"]["languages"]:
        strings_lang = strings[lang]
        i18n_lang = i18n[lang]
        url_values = {"url.%s" % page["id"]: urls.path(page["id"], lang)
                      for page in config["pages"]}

        faq_html, faq_plain = faq_items_html(strings, lang, url_values)
        # Toutes les vignettes partagent le maximum de la province la plus
        # touchee : c'est ce qui les rend comparables entre elles.
        cards = province_cards_html(provinces, urls, lang, strings_lang, province_history,
                                    province_maps, latest.get("healthZones", []), config, geo.get("aliases", {}))
        common_seed = {
            "seed.confirmed": fmt(national.get("confirmed"), lang),
            "seed.deaths": fmt(national.get("deaths"), lang),
            "seed.recovered": fmt(national.get("recovered"), lang),
            "seed.inCTE": fmt(national.get("inCTE"), lang),
            "seed.cfr": fmt_cfr(national.get("cfr"), lang),
            "seed.newCasesLine": esc(interp(strings_lang["provinceNewDeaths"],
                                            {"n": fmt(national.get("newCases24h") or 0, lang)})),
            "seed.newDeathsLine": esc(interp(strings_lang["provinceNewDeaths"],
                                             {"n": fmt(national.get("newDeaths24h") or 0, lang)})),
            "seed.zonesSub": zones_sub(national, meta_data, lang, i18n_lang, strings_lang),
            "seed.sitrepRef": sitrep_ref(meta_data, lang, i18n_lang, strings_lang),
            "seed.zonesN": fmt((national.get("healthZonesAffected") or {}).get("n"), lang),
            "seed.zonesTotal": fmt((national.get("healthZonesAffected") or {}).get("total"), lang),
            # Reperes de la page « A propos » : tires des donnees, jamais
            # saisis a la main, pour qu'ils ne puissent pas se perimer.
            "about.since": long_date(
                min((r["reportingDate"] for r in latest.get("reports", [])
                     if r.get("reportingDate")), default=None), i18n_lang),
            # Les deux sources archivees sont comptees : les SitRep quotidiens
            # de l'INSP et les bulletins hebdomadaires de l'OMS, tous deux
            # conserves en PDF et listes sur la page « Sources et bulletins ».
            "about.reports": esc(interp(strings_lang["aboutFactReportsValue"], {
                "total": fmt(len(latest.get("reports", [])) + len(who_reports), lang),
                "insp": fmt(len(latest.get("reports", [])), lang),
                "who": fmt(len(who_reports), lang)})),
            "about.reportsSub": esc(interp(strings_lang["aboutFactReportsSub"], {
                "insp": fmt(len(latest.get("reports", [])), lang),
                "who": fmt(len(who_reports), lang)})),
            "about.scope": esc(interp(strings_lang["aboutFactScopeValue"], {
                "provinces": fmt(len(provinces), lang),
                "zones": fmt(len(latest.get("healthZones", [])), lang)})),
            "about.scopeSub": esc(interp(strings_lang["aboutFactScopeSub"], {
                "zones": fmt(len(latest.get("healthZones", [])), lang)})),
            "mapHint": hint_pair(strings_lang, "cartoHint", "cartoHintTouch"),
            "seed.provinceRows": province_rows_html(provinces, national, lang, province_history, strings_lang),
            "seed.agesRows": ages_rows_html(demographie, lang, strings_lang),
            "seed.agesPapillon": ages_papillon_html(demographie, lang, strings_lang),
            "seed.vgeTitre": interp(strings_lang["vgeTitre"], {"n": fmt(genomes["rdc2026"], lang)}) if genomes else "",
            "seed.sexRows": sex_rows_html(demographie, lang, strings_lang),
            "seed.agesFrozen": esc(interp(strings_lang["ddAgesFrozen"], {
                "date": long_date(demographie["date"], i18n_lang)})),
            "seed.agesNote": interp(strings_lang["virusAgesNote"], {
                "date": long_date(demographie["date"], i18n_lang),
                "derniere": long_date(demographie["derniereFigurePubliee"], i18n_lang),
                "cas": fmt(demographie["totaux"]["cas"], lang),
                "deces": fmt(demographie["totaux"]["deces"], lang),
                "partCas": fmt_pct(demographie["couverture"]["partCas"], lang),
                "partDeces": fmt_pct(demographie["couverture"]["partDeces"], lang)}),
            **genomes_seeds(genomes, lang, strings_lang, i18n_lang),
            "seed.reportsList": reports_list_html(latest.get("reports", []), lang, i18n_lang, strings_lang),
            "seed.reportsManquants": reports_manquants_html(latest.get("reports", []), lang, strings_lang),
            "seed.reportsCalendar": reports_calendar_html(latest.get("reports", []), lang, i18n_lang, strings_lang),
            "seed.natSpark": national_spark_svg(read_json(os.path.join(ROOT, "data", "sitreps.json"))),
            "seed.whoReportsList": who_reports_list_html(who_reports, lang, i18n_lang, strings_lang),
            "seed.whoSectionStyle": "" if who_reports else "display:none;",
            "provinceCards": cards,
            "provinceCardsPlain": cards,
            "seed.provinceListe": province_liste_html(provinces, urls, lang, strings_lang),
            "seed.provinceMosaique": province_mosaique_html(provinces, urls, lang, strings_lang, province_maps,
                                                            latest.get("healthZones", []), config, geo.get("aliases", {})),
            "provinceTableRows": province_table_rows_html(provinces, urls, lang),
            "faqItems": faq_html,
            "glossaireItems": glossaire_items_html(strings, lang),
            "autresPaysItems": hors_rdc.page_html(lang, {"sources": strings_lang["autresPaysSources"], "premier": strings_lang["autresPaysPremier"]},
                                                  {x["pays"]: urls.path(x["id"], lang) for x in config["pages"] if x.get("pays")}),
            # La date vient de data/autres-pays.json (« maj »), a changer avec le texte.
            "autresPaysMaj": esc(interp(strings_lang["autresPaysMaj"], {
                "date": hors_rdc.date_longue(read_json(os.path.join(ROOT, "data", "autres-pays.json"))["maj"], lang)})),
            "actusItems": actus_items_html(actus, lang, i18n_lang, strings_lang),
        }

        events = timeline_events(strings, sitreps, lang, i18n_lang,
                                 config=config, urls=urls,
                                 zones_history=zones_history, geo=geo,
                                 latest_zones=latest.get("healthZones", []))
        common_seed["timelineItems"] = render_timeline_vertical(
            events, strings_lang, i18n_lang, urls, lang, config["provinceSlugs"])
        # L'apercu part du debut de l'epidemie et s'arrete au dixieme jalon :
        # on lit la chronologie dans son ordre, et le lien en dessous mene a
        # la suite. Six jusqu'au 5 octobre 2026 (la piste en tient 5,7 sur un
        # ecran de 1920 px) ; dix depuis, a la demande du proprietaire : la
        # piste defile, les fleches l'indiquent, et les quatre jalons ajoutes
        # (Nord-Kivu et Sud-Kivu atteints, 10 puis 20 zones touchees) montrent
        # la premiere extension de l'epidemie.
        common_seed["timelineTeaser"] = render_timeline(
            events[:10], strings_lang, i18n_lang, heading="h3")
        common_seed["cartogram"] = hors_rdc.greffer(zone_map_html(
            config, geo, latest.get("healthZones", []), provinces, urls, lang,
            strings_lang), geo, lang, config["cartogram"]["zoneThresholds"])
        common_seed["horsRdc"] = hors_rdc.encart_html(lang)
        common_seed["seed.heroMapPays"] = pays_hero_map(
            geo, latest.get("healthZones", []), config)
        common_seed["legendSteps"] = legend_steps_html(
            config["cartogram"]["zoneThresholds"], lang)
        common_seed["legendCircles"] = circle_legend_html(config, lang, i18n_lang)
        touched = len(latest.get("healthZones", []))
        # La derniere position du curseur porte la date des dernieres donnees,
        # ecrite dans la page : jamais un « Aujourd'hui » — meme avant que le
        # script ne tourne, ou sans lui.
        common_seed["timelineLatest"] = esc(long_date(
            (latest.get("meta") or {}).get("reportingDate", ""), i18n_lang))
        # Le panneau a cote de la carte est date, pas titre : ses cinq chiffres
        # sont le bilan national du dernier bulletin, quelle que soit la
        # position du curseur. Meme formule que les images partagees.
        # « Jour apres jour » de la page Le virus (6 octobre 2026) : la derniere
        # etape porte la letalite et les gueris du dernier bulletin.
        common_seed["seed.vjp5Text"] = interp(strings_lang["vjp5Text"], {
            "cfr": fmt_cfr(national.get("cfr"), lang)})
        common_seed["seed.vjp5Rip"] = interp(strings_lang["vjp5Rip"], {
            "recovered": fmt(national.get("recovered"), lang),
            "date": long_date(meta_data.get("reportingDate"), i18n_lang)})
        common_seed["seed.cartoAsOf"] = esc(interp(strings_lang["cartoAsOf"], {
            "date": long_date((latest.get("meta") or {}).get("reportingDate", ""), i18n_lang)}))
        # Sous « Situation au… », le numero du bulletin, lie a son PDF
        # (7 octobre 2026, demande de Fable).
        _num = (latest.get("meta") or {}).get("sitrepNumber") or ""
        common_seed["seed.cartoSitrep"] = (
            '<a class="cd-sitrep" href="/reports/SITREP_MVE_%s.pdf" target="_blank" rel="noopener">%s'
            '<span class="cd-rdc"> %s</span></a>'
            % (esc(_num), esc(interp(strings_lang["cartoSitrep"], {"n": _num})),
               esc(strings_lang["cartoRdcSeulement"]))) if _num else ""
        # « chiffres de la RDC », sous le numero : en vue « Pays touches », les chiffres du
        # panneau ne comptent que la RDC alors que la carte montre l'Ouganda et
        # le Kenya. Visible dans cette vue seulement (8 octobre 2026).
        common_seed["seed.clesChiffres"] = cles_chiffres_html(national, lang, i18n_lang, strings_lang)
        common_seed["seed.clesCourbe"] = cles_courbe_svg(sitreps, lang, i18n_lang, strings_lang)
        common_seed["seed.provincesTouched"] = esc(interp(
            strings_lang["cartoZonesTouched"],
            {"n": touched, "total": len(geo["zones"])}))
        common_seed["panelStats"] = panel_stats_html(national, lang, i18n_lang)
        common_seed.update(riposte_seed(riposte, meta_data, lang, strings_lang, i18n_lang))
        # Contacts vus et occupation des CTE de chaque province (16 sept. 2026).
        common_seed["provinceRiposte"] = {
            _p["name"]: province_riposte_seed(riposte, _p["name"], meta_data, lang, strings_lang, i18n_lang)
            for _p in provinces}
        # La fiche de chaque territoire (28 septembre 2026) : le point des
        # sept derniers jours et le cadre « La riposte ».
        num_notes = sorted((k for k, v in notes_bulletins.items()
                            if k.isdigit() and (v.get("defis") or {}).get(lang)), key=int)
        note = notes_bulletins[num_notes[-1]] if num_notes else {}
        common_seed["provinceFiche"] = {}
        common_seed["zonesHistory"] = zones_history   # tableau des zones des provinces
        for _p in provinces:
            _n = _p["name"]
            _serie = []
            for h in province_history:
                q = next((x for x in h.get("provinces", []) if x.get("name") == _n), None)
                if q:
                    _serie.append((h["date"], q.get("confirmed"), q.get("deaths")))
            _rs = common_seed["provinceRiposte"][_n]
            _kpis = []
            if _n not in PROVINCES_SANS_CASES_RIPOSTE:
                _pos, _pos_sub = positivite_province(riposte, _n, lang, strings_lang)
                _vac, _vac_sub = vaccines_province(riposte, _n, meta_data, lang, strings_lang, i18n_lang)
                _kpis = [
                    ("contacts", esc(strings_lang["riposteKpiContacts"]),
                     _rs["province.ripContacts"], _rs["province.ripContactsSub"]),
                    ("cte", esc(strings_lang["riposteKpiOccupation"]),
                     _rs["province.ripOccupation"], _rs["province.ripOccupationSub"]),
                    ("labo", esc(strings_lang["riposteKpiPositivite"]), _pos, _pos_sub),
                    ("vaccin", esc(strings_lang["ficheKpiVaccines"]), _vac, _vac_sub)]
                _al = alertes_province(riposte, _n, lang, strings_lang)
                if _al:
                    _kpis.insert(0, ("alerts", esc(strings_lang["riposteKpiAlertes"]), _al[0], _al[1]))
            _graph, _extr = "", ""
            if a_une_courbe(_p):
                _MODE = {"alerts": "alertes", "labo": "laboratoire", "contacts": "contactsRiposte", "cte": "cte", "vaccin": "vaccination"}
                _graph = riposte_graphiques_province(riposte, _n, lang, strings_lang, i18n_lang,
                                                     chiffres={_MODE[k[0]]: (k[2], k[1], k[3]) for k in _kpis})
                _ex, _num = extraits_defis_province(riposte["defis"], _n, {
                    z["name"]: z["province"] for z in latest.get("healthZones", [])
                    if len(z.get("name", "")) >= 4 and z.get("province")})
                _extr = extraits_defis_html(_ex, _num, strings_lang)
            common_seed["provinceFiche"][_n] = {
                "province.point": fiche_point_html(_serie, lang, strings_lang),
                "province.riposteIci": fiche_riposte_html(
                    province_numeros(_p)["riposte"], _kpis, "", "", [], strings_lang,
                    graphiques=_graph, extraits=_extr, avec_defis=False, chaine=True)
                if a_une_riposte(_p) else _cadre_vaccination_seule(
                    _p, riposte, meta_data, lang, strings_lang, i18n_lang),
            }
        # Le pays : meme plan, memes cases que l'ancien « Que fait-on ».
        common_seed["seed.point"] = fiche_point_html(
            [(r["date"], r.get("confirmed"), r.get("deaths")) for r in sitreps], lang, strings_lang)
        _liens = [(urls.path("riposte", lang), strings_lang["ficheLienRiposte"])]
        common_seed["seed.riposteIci"] = fiche_riposte_html(
            "04",
            [("alerts", esc(strings_lang["riposteKpiAlertes"]), common_seed["seed.ripAlertes"], common_seed["seed.ripAlertesSub"]),
             ("labo", esc(strings_lang["riposteKpiPositivite"]), common_seed["seed.ripPositivite"], common_seed["seed.ripPositiviteSub"]),
             ("contacts", esc(strings_lang["riposteKpiContacts"]), common_seed["seed.ripContacts"], common_seed["seed.ripContactsSub"]),
             ("cte", esc(strings_lang["riposteKpiOccupation"]), common_seed["seed.ripOccupation"], common_seed["seed.ripOccupationSub"]),
             ("vaccin", esc(strings_lang["riposteKpiVaccines"]), common_seed.get("seed.ripVaccines", "—"), "")],
            "", "", _liens, strings_lang, avec_defis=False, chaine=True)
        # La frise de chaque page province (8 septembre 2026).
        common_seed["provinceTimelines"] = {
            _p["name"]: province_timeline_html(_p["name"], province_forms(config, _p["name"], lang), strings, lang, i18n_lang,
                                               province_history, zones_history, geo, latest.get("healthZones", []),
                                               numero=province_numeros(_p)["chrono"])
            for _p in provinces}
        # La grille des obstacles de chaque page province (29 septembre 2026).
        common_seed["provinceObstacles"] = {
            _p["name"]: defis_synthese.grille_province(
                _p["name"], lang, i18n_lang, long_date, esc, province_numeros(_p)["obstacles"],
                urls.path("defis", lang),
                (lambda f: f[:1].upper() + f[1:])(province_forms(config, _p["name"], lang).get("in", _p["name"])))
            for _p in provinces if _p["name"] in PROVINCES_OBSTACLES}
        common_seed.update(defis_synthese.render(lang, strings_lang, i18n_lang, long_date, esc, PROVINCE_COLORS,
                                                  lien_defis=urls.path("defis", lang)))
        common_seed.update(bulletin.render(lang, strings_lang, i18n_lang, fmt, fmt_decimal, fmt_cfr, long_date, esc, interp, province_forms, PROVINCE_COLORS, urls))
        # A propos et Contact : un paragraphe vers le compte X, ou rien.
        compte_x = (config["site"].get("xProfile") or "").strip().lstrip("@")
        lx = lien_x(config, "@" + compte_x) if compte_x else ""
        common_seed["seed.suivreXApropos"] = ('<h2>%s</h2>\n      <p>%s %s</p>' % (esc(strings_lang["aboutFollowTitle"]), esc(strings_lang["aboutFollowBody"]), lx)) if lx else ""
        common_seed["seed.suivreXContact"] = ('<p class="map-note contact-x">%s %s</p>' % (esc(strings_lang["contactFollowBody"]), lx)) if lx else ""

        pages = [(page, None) for page in config["pages"]]
        pages += [(config["provincePage"], province) for province in provinces]

        for page, province in pages:
            if page.get("lettreNum"):
                common_seed["seed.lettreNum"] = common_seed["seed.lettres"][page["lettreNum"]]
            generated.append(render_page(
                page, province, lang, config, strings, strings_lang, i18n_lang,
                urls, layout, common_seed, url_values, faq_plain,
                zones_by_province, national, meta_data, provinces, geo,
                province_history, province_maps))

    write_sitemap(config, urls, provinces)
    generated.append("sitemap.xml")
    write_404(config, urls, strings, i18n, layout)
    generated.append("404.html")
    remove_stale(generated)
    write(MANIFEST, json.dumps(sorted(generated), ensure_ascii=False, indent=1) + "\n")

    print("%d fichiers générés." % len(generated))
    for path in sorted(generated):
        print("  ", path)




def alternates_html(config, urls, alt_paths):
    """Les balises « alternate » qui declarent les traductions aux moteurs.

    Elles etaient cablees sur deux langues dans site/layout.html, alors que le
    sitemap, lui, bouclait deja sur la liste. Le swahili se retrouvait donc
    dans sitemap.xml sans etre annonce par les pages elles-memes — l'exacte
    incoherence qui empeche un moteur de proposer la bonne version.

    x-default pointe vers la langue par defaut : c'est ce que voit un visiteur
    dont aucune langue ne correspond.
    """
    defaut = config["site"].get("defaultLanguage", "fr")
    lignes = ['<link rel="alternate" hreflang="%s" href="%s">'
              % (code, esc(urls.absolute(alt_paths[code])))
              for code in config["site"]["languages"]]
    lignes.append('<link rel="alternate" hreflang="x-default" href="%s">'
                  % esc(urls.absolute(alt_paths[defaut])))
    return "\n".join(lignes)

def glyphe_x(config, strings_lang, classe):
    """Le glyphe X seul (sans texte visible), lien vers le compte du site,
    ou chaine vide sans compte. Libelle accessible dans la langue de la page."""
    compte = (config["site"].get("xProfile") or "").strip().lstrip("@")
    if not compte:
        return ""
    libelle = interp(strings_lang["followXLabel"], {"compte": compte})
    return ('<a class="%s" href="https://x.com/%s" rel="me noopener" target="_blank" '
            'title="@%s" aria-label="%s">%s</a>' % (classe, esc(compte), esc(compte), esc(libelle), X_ICONE))


def lang_switch_html(config, alt_paths, lang, strings_lang=None):
    """Le selecteur de langue, une entree par langue declaree.

    Il etait cable en dur sur deux boutons FR et EN, avec quatre jetons de
    gabarit — frActive, enActive, frCurrent, enCurrent. Ajouter une troisieme
    langue demandait d'en ajouter deux de plus a chaque fois ; il se construit
    desormais depuis config["site"]["languages"].
    """
    codes = config["site"]["languages"]
    labels = " / ".join(loc(code, "label") for code in codes)
    boutons = []
    for code in codes:
        courante = code == lang
        boutons.append(
            '        <a class="lang-btn%s" href="%s" hreflang="%s" lang="%s" '
            'title="%s"%s>\n          <span class="code">%s</span>\n        </a>'
            % (" active" if courante else "", esc(alt_paths[code]), code, code,
               esc(loc(code, "label")),
               ' aria-current="true"' if courante else "",
               esc(code.upper())))
    # Au bout de la rangee, sur ordinateur : le glyphe X vers le compte du
    # site (8 septembre 2026). Cache sous 900 px, ou l'en-tete est plein ;
    # le telephone a son lien dans le pied du menu.
    if strings_lang is not None:
        gx = glyphe_x(config, strings_lang, "lang-btn lang-x")
        if gx:
            boutons.append("        " + gx)
    return ('      <div class="lang-switch" role="group" aria-label="%s">\n%s\n      </div>'
            % (esc(labels), "\n".join(boutons)))

def render_page(page, province, lang, config, strings, strings_lang, i18n_lang,
                urls, layout, common_seed, url_values, faq_plain,
                zones_by_province, national, meta_data, provinces, geo,
                province_history, province_maps):
    site = config["site"]
    origin = urls.origin
    is_province = province is not None

    if is_province:
        name = province["name"]
        path = urls.province_path(name, lang)
        fragment_name = page["fragment"]
        forms = province_forms(config, name, lang)
        sentence = dict(forms)
        sentence.update({
            "date": long_date(meta_data.get("reportingDate"), i18n_lang),
            "cases": fmt(province.get("confirmed"), lang),
            "deaths": fmt(province.get("deaths"), lang),
            "cfr": fmt_decimal(province.get("cfr"), lang),
        })
        # Plus de date de premier cas : elle n'est pas dans la donnee. Ce que
        # province-history.json sait dire, c'est la derniere fois que le cumul
        # d'une province a monte — et, faute de hausse, depuis quand il ne
        # bouge plus. Les retrouver demanderait d'extraire les annonces de
        # nouvelle province du texte des bulletins, ce que rien ne fait.
        # Depuis quand : la meme table curee que la chronologie, dans une
        # redaction courte. Pour le Haut-Uele et la Tshopo, la phrase porte la
        # reattribution — sans elle, la date contredirait la carte de la meme
        # page, dont le curseur n'allume leurs zones qu'au 10 juillet.
        arrival = next((a for a in strings.get("provinceArrivals", [])
                        if a["province"] == name), None)
        arrival_line = esc(arrival["page" + lang.capitalize()]) if arrival else ""

        first_seen, last_case = province_case_window(province_history, name)
        window_line = ""
        if last_case:
            window_line = interp(strings_lang["provinceCaseLast"], {
                "last": long_date(last_case, i18n_lang)})
        elif first_seen:
            window_line = interp(strings_lang["provinceCaseNoneSince"], {
                "first": long_date(first_seen, i18n_lang)})

        # Les zones de sante touchees, nommees (9 octobre 2026, referencement) :
        # les trois plus touchees dans la phrase de situation, avec leurs cas,
        # et dans la description ; les autres sont comptees, pas nommees.
        zones_cas = sorted([z for z in zones_by_province.get(name, []) if (z.get("cases") or 0) > 0],
                           key=lambda z: -z["cases"])
        def liste(items):
            return (items[0] if len(items) == 1 else
                    ", ".join(items[:-1]) + strings_lang["timelineListAnd"] + items[-1]) if items else ""
        def zones_nommees(avec_cas):
            noms = ["%s (%s)" % (z["name"], fmt(z["cases"], lang)) if avec_cas else z["name"]
                    for z in zones_cas[:3]]
            if len(zones_cas) > 3 and not avec_cas:
                return interp(strings_lang["provinceZonesOthers"], {
                    "list": ", ".join(noms), "n": fmt(len(zones_cas) - 3, lang)})
            return liste(noms)
        sentence["zones"] = zones_nommees(False) or "—"

        meta = {
            "h1": interp(strings_lang["provinceH1"], forms),
            "title": interp(strings_lang["provinceMetaTitle"], forms),
            "description": interp(strings_lang["provinceMetaDescription"], sentence),
        }
        alt_paths = {code: urls.province_path(name, code) for code in site["languages"]}
        trail = [(label_for(by_id_page(config, "donnees"), strings_lang, i18n_lang),
                  urls.path("donnees", lang)),
                 (name, None)]
    else:
        path = urls.path(page["id"], lang)
        fragment_name = page["fragment"]
        meta = dict(page["meta"][lang])
        alt_paths = {code: urls.path(page["id"], code) for code in site["languages"]}
        trail = [] if page["id"] == "accueil" else [(meta["h1"], None)]
        # Kenya et Ouganda (9 octobre 2026) : sous « Autres pays ».
        if page.get("parent"):
            trail.insert(0, (by_id_page(config, page["parent"])["meta"][lang]["h1"],
                             urls.path(page["parent"], lang)))

    fragment = read(os.path.join(SITE, "pages", fragment_name))
    # Une page peut porter son propre gabarit (le tableau de bord, plein
    # ecran, 9 octobre 2026) ; les autres prennent site/layout.html.
    if page.get("layout"):
        layout = read(os.path.join(SITE, page["layout"]))

    values = dict(common_seed)
    values.update(url_values)
    values.update({"i18n.%s" % key: esc(value) if isinstance(value, str) else ""
                   for key, value in i18n_lang.items()})
    # Contient un <sup> volontaire : on ne l'echappe pas.
    values["i18n.topMeta"] = i18n_lang["topMeta"]
    # Les textes de site/strings.json peuvent citer une page du site sous la
    # forme {url.rapports} : on les resout ici, pour toutes les chaines et pas
    # seulement pour les reponses de la FAQ.
    values.update({"t.%s" % key: interp(value, url_values) if isinstance(value, str) else value
                   for key, value in strings_lang.items()})
    values["meta.h1"] = esc(meta["h1"])
    if page.get("id") == "base-de-donnees":
        values.update(base_values(config, urls, lang, strings_lang, i18n_lang,
                                  read_json(os.path.join(ROOT, "data", "latest.json")).get("reports", [])))
    if page.get("id") == "dashboard":
        values.update(dashboard_values(config, urls, lang, strings_lang, i18n_lang, alt_paths,
                                       national, meta_data, provinces))
    # Page d'un pays touche hors de RDC (Kenya, Ouganda : 9 octobre 2026) :
    # sa fiche d'« Autres pays » et ses questions, tirees de data/autres-pays.json.
    if page.get("pays"):
        values["meta.lede"] = esc(meta["lede"])
        values["pays.fiche"] = hors_rdc.pays_html(page["pays"], lang, {
            "sources": strings_lang["autresPaysSources"], "premier": strings_lang["autresPaysPremier"]})
        values["pays.questions"] = hors_rdc.questions_html(page["pays"], lang)
        values["pays.autres"] = " ".join(
            '<a href="%s">%s →</a>' % (urls.path(x["id"], lang), esc(x["meta"][lang]["h1"]))
            for x in config["pages"] if x.get("pays") and x["id"] != page["id"])
        # La France n'est pas sur la carte (retiree le 8 octobre 2026).
        values["pays.carte"] = ("" if page.get("carte") is False else
                                ' <a href="%s#pays-touches">%s →</a>'
                                % (urls.path("accueil", lang), esc(strings_lang["autresPaysCarte"])))
    # Une page « noindex » (maquette) le dit aussi dans sa balise robots, en
    # plus d'etre absente du sitemap (6 septembre 2026).
    values["robots"] = "noindex, follow" if page.get("noindex") else "index, follow"
    values["repository"] = site["repository"]

    if is_province:
        name = province["name"]
        zones = zones_by_province.get(name, [])
        zone_info = province.get("healthZonesAffected")
        if zone_info and zones_cas:
            cle = ("provinceIntroZonesOne" if len(zones_cas) == 1 else
                   "provinceIntroZonesTop" if len(zones_cas) > 3 else "provinceIntroZonesAll")
            zones_sentence = interp(strings_lang[cle],
                                    {"n": zone_info["n"], "total": zone_info["total"],
                                     "top": zones_nommees(True)})
        elif zone_info:
            zones_sentence = interp(strings_lang["provinceIntroZones"],
                                    {"n": zone_info["n"], "total": zone_info["total"]})
        else:
            zones_sentence = strings_lang["provinceIntroNoZones"]
        share = ""
        rank_line = ""
        if national.get("confirmed"):
            share_ratio = province["confirmed"] / float(national["confirmed"]) * 100
            # Une province a un seul cas pese 0,02 % : arrondi a une decimale,
            # « 0,0 % » ne dit rien. On le formule autrement.
            share_value = (strings_lang["shareLessThan"] if share_ratio < 0.1
                           else fmt_decimal(share_ratio, lang))
            share = interp(strings_lang["provinceShareSentence"], {"share": share_value})
            ordered = sorted(provinces, key=lambda p: -(p.get("confirmed") or 0))
            rank = [p["name"] for p in ordered].index(name) + 1
            key = "provinceRankFirst" if rank == 1 else "provinceRankLine"
            rank_line = interp(strings_lang[key], {
                "rank": ordinal(rank, lang), "total": len(ordered),
                "share": share_value})
        status = province.get("status") or "active"
        status_label = {
            "active-epicenter": strings_lang["provinceStatusEpicenter"],
            "inactive": strings_lang["provinceStatusInactive"],
        }.get(status, strings_lang["provinceStatusActive"])
        new_deaths = province.get("newDeathsCommunity24h") or 0
        new_deaths += province.get("newDeathsIntraCTE24h") or 0
        values.update({
            "province.statusLabel": esc(status_label),
            "province.name": esc(name),
            "province.color": PROVINCE_COLORS.get(name, "var(--ink-faint)"),
            "province.intro": interp(strings_lang["provinceIntro"], dict(
                sentence, zonesSentence=esc(zones_sentence))),
            # La carte de la province en fond de l'en-tete (5 octobre 2026,
            # option B de la maquette entete-province).
            "province.heroMap": province_mini_map((province_maps or {}).get(name), name, zones,
                                                  config, geo.get("aliases", {})) if province_maps else "",
            "province.cases": fmt(province.get("confirmed"), lang),
            "province.deaths": fmt(province.get("deaths"), lang),
            "province.cfr": fmt_cfr(province.get("cfr"), lang),
            "province.shareSentence": esc(share),
            "province.newDeaths": esc(interp(strings_lang["provinceNewDeaths"],
                                             {"n": fmt(new_deaths, lang)})),
            # Meme forme que les deces, demande du proprietaire le 8 septembre 2026.
            "province.newCases": esc(interp(strings_lang["provinceNewDeaths"],
                                            {"n": fmt(province.get("newCases24h") or 0, lang)})),
            "province.zonesTitle": esc(interp(strings_lang["provinceZonesTitle"], forms)),
            "province.zonesTable": province_zones_table_html(
                zones, forms, lang, strings_lang, i18n_lang, zones_history=common_seed.get("zonesHistory"), province=name),
            "province.fullTable": esc(interp(strings_lang["provinceOpenFullTable"], forms)),
            "province.baseLien": esc(interp(strings_lang["provinceBaseLien"], forms)),
            **province_map_values(province_maps, name, zones, config, lang,
                                  strings_lang, geo.get("aliases", {})),
            "province.chart": province_chart_html(province, strings_lang, i18n_lang),
            **common_seed.get("provinceFiche", {}).get(name, {}),
            "province.zonesNum": province_numeros(province)["zones"],
            "province.timeline": common_seed.get("provinceTimelines", {}).get(name, ""),
            "province.obstacles": common_seed.get("provinceObstacles", {}).get(name, ""),
            "province.query": name.replace(" ", "%20"),
            # Rang dans le pays, puis quand ca a commence, puis quand ca a
            # bouge pour la derniere fois : un bloc temporel qui se lit d'un
            # trait, sous le paragraphe qui porte la situation du jour.
            "province.rank": " ".join(
                x for x in (esc(rank_line), arrival_line, esc(window_line)) if x),
        })

    # « Ensemble du pays » (6 octobre 2026) : le paragraphe et le
    # sous-paragraphe suivent la trame des pages province — la situation du
    # jour, puis la province la plus touchee, le demarrage, le dernier cas.
    if not is_province and page["id"] == "donnees" and national.get("confirmed"):
        ordered = sorted(provinces, key=lambda p: -(p.get("confirmed") or 0))
        tete = ordered[0]
        zones_pays = (national.get("healthZonesAffected") or {}).get("n") or len(latest.get("healthZones", []))
        the = province_forms(config, tete["name"], lang)["the"]
        derniers = [province_case_window(province_history, p["name"])[1] for p in provinces]
        derniers = [d for d in derniers if d]
        values["seed.paysIntro"] = interp(strings_lang["paysIntro"], {
            "date": long_date(meta_data.get("reportingDate"), i18n_lang),
            "cases": fmt(national.get("confirmed"), lang),
            "deaths": fmt(national.get("deaths"), lang),
            "cfr": fmt_decimal(national.get("cfr"), lang),
            "zones": fmt(zones_pays, lang),
            "provinces": fmt(national.get("provincesAffected") or len(provinces), lang)})
        lignes = [interp(strings_lang["paysRank"], {
            "The": the[:1].upper() + the[1:],
            "share": fmt_decimal(tete["confirmed"] / float(national["confirmed"]) * 100, lang)})]
        if tete["name"] == "Ituri":
            lignes.append(strings_lang["paysOrigin"])
        if derniers:
            lignes.append(interp(strings_lang["provinceCaseLast"], {
                "last": long_date(max(derniers), i18n_lang)}))
        values["seed.paysRank"] = " ".join(esc(x) for x in lignes)

    content = render(fragment, values, fragment_name + " [" + lang + "]")
    # Les notes sous les graphiques restent visibles (7 octobre 2026, decision
    # du proprietaire : elles portent les reserves qui changent la lecture).

    # Chart.js pese 200 Ko : inutile de le charger sur une page province
    # qui n'a pas de graphique. « needs » est declare par type de page,
    # or ici le besoin varie d'une province a l'autre.
    besoins = list(page.get("needs", []))
    # Le cadre « La riposte » (29 septembre 2026) peut porter un graphique
    # (la vaccination du Bas-Uele) sans que la province ait de courbe des cas.
    if (is_province and "chart" in besoins and not values.get("province.chart")
            and "<canvas" not in (values.get("province.riposteIci") or "")):
        besoins.remove("chart")

    canonical = urls.absolute(path)
    schema_context = {
        "meta": meta, "lang": lang, "canonical": canonical, "origin": origin,
        "siteName": strings_lang["siteTitleMain"],
        "brandName": site.get("brandName") or strings_lang["siteTitleMain"],
        "siteNameAlternates": sorted({strings[code]["siteTitleMain"] for code in site["languages"]} | {"ebola-tracker.org"}),
        "keywords": ["Ebola", "RDC", "DRC", "épidémie", "santé publique",
                     "Bundibugyo", "SitRep"],
        "faqPlain": faq_plain,
        "faqPays": hors_rdc.questions_plain(page["pays"], lang) if page.get("pays") else [],
        "base": BASE,
        "breadcrumbTrail": trail,
        "breadcrumbHome": strings_lang["breadcrumbHome"],
        "homePath": urls.path("accueil", lang),
        "path": path,
    }
    if is_province:
        schema_context["spatialCoverage"] = province["name"] + ", Democratic Republic of the Congo"

    page_globals = []
    page_globals.append("window.PROVINCE_LINKS = %s;" % json.dumps(
        {p["name"]: urls.province_path(p["name"], lang) for p in provinces},
        ensure_ascii=False))
    if geo.get("aliases"):
        # Ecarts d'orthographe entre nos bulletins et le fond de carte officiel,
        # resolus par scripts/build_geo.py. Le JavaScript en a besoin pour
        # retrouver le polygone d'une zone.
        page_globals.append("window.ZONE_ALIASES = %s;"
                            % json.dumps(geo["aliases"], ensure_ascii=False))
    # Emprises des provinces et cadre global : le zoom au clic n'a aucun calcul
    # géométrique à refaire côté navigateur.
    page_globals.append("window.HERO_TIP_CASES = %s; window.HERO_TIP_DEATHS = %s;"
                        % (json.dumps(strings_lang["heroTipCases"], ensure_ascii=False),
                           json.dumps(strings_lang["heroTipDeaths"], ensure_ascii=False)))
    page_globals.append("window.MAP_VIEWBOX = %s;" % json.dumps(geo["viewBox"]))
    page_globals.append("window.MAP_THRESHOLDS = %s;"
                        % json.dumps(config["cartogram"]["zoneThresholds"]))
    page_globals.append("window.MAP_PROVINCE_BOXES = %s;"
                        % json.dumps(geo["provinceBoxes"], ensure_ascii=False))
    # Vue « cercles » : le point de chaque zone touchee, projete comme le
    # reste de la carte (plate-carree de build_geo.py), et l'echelle des
    # rayons. Les cercles se dessinent au navigateur, a chaque position du
    # curseur, a partir des memes instantanes que les couleurs.
    page_globals.append("window.ZONE_POINTS = %s;" % json.dumps(
        zone_points(config, geo), ensure_ascii=False))
    page_globals.append("window.MAP_CIRCLE_SCALE = %s;"
                        % json.dumps(config["cartogram"].get("circleScale", 1.0)))
    page_globals.append("window.MAP_CIRCLE_MIN = %s;"
                        % json.dumps(config["cartogram"].get("circleMinRadius", 2.5)))
    page_globals.append("window.MAP_CIRCLE_SCALE_PHONE = %s;"
                        % json.dumps(config["cartogram"].get("circleScalePhone",
                                                             config["cartogram"].get("circleScale", 1.0))))
    page_globals.append("window.MAP_CIRCLE_LEGEND = %s;"
                        % json.dumps(config["cartogram"].get("circleLegend", [1, 10, 100, 1000])))
    # Le graphique d'une page province a besoin de savoir laquelle : le nom
    # sert de cle dans province-history.json et dans PROVINCE_COLORS.
    if is_province and province is not None:
        page_globals.append("window.PROVINCE_NAME = %s;"
                            % json.dumps(province["name"], ensure_ascii=False))
    page_globals.append("window.PROVINCES_INDEX_URL = %s;"
                        % json.dumps(urls.path("donnees", lang)))
    page_globals.append("window.DATA_PAGE_URL = %s;"
                        % json.dumps(urls.path("donnees", lang)))
    if page.get("legacyHashRoutes"):
        page_globals.append("window.LEGACY_HASH_ROUTES = %s;" % json.dumps({
            "zones": urls.path("donnees", lang),
            "reports": urls.path("rapports", lang),
            "about": urls.path("a-propos", lang),
            "contact": urls.path("contact", lang),
            "virus": urls.path("le-virus", lang),
        }, ensure_ascii=False))

    layout_values = {
        "robots": values["robots"],
        # Classe de corps facultative (page.bodyClass) : les maquettes de la
        # lettre en ont besoin pour changer de chrome (8 septembre 2026).
        "bodyClass": (' class="%s"' % esc(page["bodyClass"])) if page.get("bodyClass") else "",
        "lang": lang,
        # Jetons de cache des fichiers statiques : c'est le gabarit qui porte
        # les balises <link> et <script>, donc c'est ici qu'ils doivent vivre.
        "v.css": jeton_version("assets/css/site.css"),
        "v.app": jeton_version("assets/js/app.js"),
        "v.i18n": jeton_version("assets/js/i18n.js"),
        "v.dash": jeton_version("assets/js/dashboard.js"),
        "v.dashcss": jeton_version("assets/css/dashboard.css"),
        "title": esc(meta["title"]),
        "description": esc(meta["description"]),
        "canonical": canonical,
        "alternates": alternates_html(config, urls, alt_paths),
        # Le flux de la langue courante, annonce dans le <head> : c'est par
        # cette balise que les lecteurs et les relais (Slack, Brevo) le
        # trouvent depuis n'importe quelle page.
        # og:site_name : le meme nom de marque que WebSite.name, pour Google.
        "siteName": esc(site.get("brandName") or strings_lang["siteTitleMain"]),
        "ogType": "website" if page.get("id") == "accueil" else "article",
        "ogLocale": loc(lang, "ogLocale"),
        "ogLocaleAlt": ", ".join(loc(other, "ogLocale")
                                 for other in config["site"]["languages"]
                                 if other != lang),
        "ogImage": origin + site["ogImage"],
        "verification": site["googleSiteVerification"],
        "analytics": site["analytics"],
        "jsonLd": build_json_ld(page.get("schema", []), schema_context),
        "headAssets": head_assets(besoins),
        "homeUrl": urls.path("accueil", lang),
        "t.siteTitleLinkLabel": esc(strings_lang["siteTitleLinkLabel"]),
        "langSwitch": lang_switch_html(config, alt_paths, lang, strings_lang),
        # Telephone : « Suivre » avec le glyphe, dans le pied du menu (a la
        # place de l'ancien bouton Partager). Rien sans compte.
        "suivreXMenu": ('      <a class="share-btn suivre-x" href="https://x.com/%s" rel="me noopener" target="_blank" aria-label="%s">%s <span>%s</span></a>'
                        % (esc((config["site"].get("xProfile") or "").strip().lstrip("@")),
                           esc(interp(strings_lang["followXLabel"], {"compte": (config["site"].get("xProfile") or "").strip().lstrip("@")})),
                           X_ICONE, esc(strings_lang["menuFollowX"]))) if (config["site"].get("xProfile") or "").strip() else "",
        "nav": build_nav(config, urls, lang, strings_lang, i18n_lang,
                         None if is_province else page.get("id"), provinces,
                         current_province=province["name"] if is_province else None),
        "breadcrumb": build_breadcrumb(urls, lang, strings_lang, trail),
        "content": content,
        "footer": build_footer(config, urls, lang, strings_lang, i18n_lang,
                               provinces,
                               avec_avertissement=(page.get("id") != "accueil")),
        "pageGlobals": "\n".join(page_globals),
        "bodyAssets": "",
        "t.skipToContent": esc(strings_lang["skipToContent"]),
        "t.menuOpen": esc(strings_lang["menuOpen"]),
        "t.menuClose": esc(strings_lang["menuClose"]),
        "i18n.shareBtn": esc(i18n_lang["shareBtn"]),
        # Contient un <sup> volontaire : on ne l'echappe pas.
        "i18n.topMeta": i18n_lang["topMeta"],
    }

    html = render(layout, layout_values, "layout.html [%s %s]" % (lang, path))
    out_path = urls.output_file(path)
    write(out_path, html)
    return os.path.relpath(out_path, ROOT).replace("\\", "/")


def write_sitemap(config, urls, provinces):
    entries = []
    for page in config["pages"]:
        # Une page « noindex » (la maquette de /donnees/) est servie mais ne
        # figure pas dans le sitemap ; robots.txt l'interdit aux moteurs.
        if page.get("noindex"):
            continue
        entries.append((page["id"], None, page["changefreq"], page["priority"]))
    province_page = config["provincePage"]
    for province in provinces:
        entries.append((None, province["name"],
                        province_page["changefreq"], province_page["priority"]))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
             '']
    today = date.today().isoformat()
    for lang in config["site"]["languages"]:
        for page_id, province_name, changefreq, priority in entries:
            if page_id:
                path = urls.path(page_id, lang)
                alternates = {code: urls.path(page_id, code)
                              for code in config["site"]["languages"]}
            else:
                path = urls.province_path(province_name, lang)
                alternates = {code: urls.province_path(province_name, code)
                              for code in config["site"]["languages"]}
            # Une traduction ne doit pas primer sur la langue par defaut.
            defaut = config["site"].get("defaultLanguage", "fr")
            adjusted = priority if lang == defaut else "%.1f" % max(
                0.1, float(priority) - 0.1)
            lines.append("  <url>")
            lines.append("    <loc>%s</loc>" % urls.absolute(path))
            for code, alt in alternates.items():
                lines.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>'
                             % (code, urls.absolute(alt)))
            lines.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>'
                         % urls.absolute(alternates["fr"]))
            lines.append("    <lastmod>%s</lastmod>" % today)
            lines.append("    <changefreq>%s</changefreq>" % changefreq)
            lines.append("    <priority>%s</priority>" % adjusted)
            lines.append("  </url>")
            lines.append("")
    lines.append("</urlset>")
    write(os.path.join(ROOT, "sitemap.xml"), "\n".join(lines))


def write_404(config, urls, strings, i18n, layout):
    """Page servie par GitHub Pages pour toute URL inconnue.

    Elle est bilingue : a ce stade on ne sait pas quelle langue le visiteur
    cherchait. Elle n'a pas de colonne laterale — la liste des pages tient
    lieu de navigation, et c'est tout ce dont on a besoin ici.
    """
    blocks = []
    for lang in config["site"]["languages"]:
        title = strings[lang]["notFoundTitle"]
        intro = strings[lang]["notFoundIntro"]
        links = []
        for page in config["pages"]:
            links.append('          <li><a href="%s">%s</a></li>'
                         % (urls.path(page["id"], lang),
                            esc(page["meta"][lang]["h1"])))
        # Un seul h1 par page : il revient au premier bloc, celui de la
        # langue par defaut ; les traductions suivent en h2.
        heading = "h1" if lang == config["site"].get("defaultLanguage", "fr") else "h2"
        blocks.append(
            '      <section class="section" lang="%s">\n'
            '        <%s class="page-title">%s</%s>\n'
            '        <p class="page-intro">%s</p>\n'
            '        <ul class="notfound-list">\n%s\n        </ul>\n'
            "      </section>" % (lang, heading, esc(title), heading,
                                  esc(intro), "\n".join(links)))

    html = [
        "<!DOCTYPE html>", '<html lang="fr">', "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "<title>404 — %s</title>" % esc(strings["fr"]["siteTitleMain"]),
        '<meta name="robots" content="noindex, follow">',
        '<meta name="theme-color" content="#FDFAF6">',
        '<link rel="icon" type="image/svg+xml" href="/favicon.svg">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700'
        '&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">',
        '<link rel="stylesheet" href="/assets/css/site.css?v=%s">'
        % jeton_version("assets/css/site.css"),
        "</head>", '<body>',
        '  <div class="wrap notfound">',
        '    <a class="brand" href="/">',
        '      <span class="dot" aria-hidden="true"></span>',
        '      <p class="site-title">ebola-tracker<span class="tld">.org</span></p>',
        "    </a>",
        "\n".join(blocks),
        "  </div>", "</body>", "</html>", "",
    ]
    write(os.path.join(ROOT, "404.html"), "\n".join(html))


def remove_stale(generated):
    """Supprime les pages générées lors d'un build précédent et devenues inutiles.

    Ne touche qu'aux fichiers listés dans le manifeste : les données, les PDF
    et tout fichier écrit à la main sont hors de portée.
    """
    if not os.path.exists(MANIFEST):
        return
    previous = read_json(MANIFEST)
    current = set(generated)
    for relative in previous:
        if relative in current:
            continue
        full = os.path.join(ROOT, relative)
        if os.path.exists(full):
            os.remove(full)
            print("  - supprimé (page disparue) :", relative)
            # On remonte tant que les dossiers sont vides : supprimer
            # /provinces/ituri/index.html doit aussi faire disparaître
            # /provinces/ quand il ne reste plus rien dedans.
            folder = os.path.dirname(full)
            while (os.path.isdir(folder) and not os.listdir(folder)
                   and os.path.abspath(folder) != ROOT):
                os.rmdir(folder)
                folder = os.path.dirname(folder)


if __name__ == "__main__":
    main()
