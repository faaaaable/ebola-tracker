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
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
              expand_provinces=False):
    """Navigation de la colonne laterale. Les provinces forment une sous-liste
    toujours visible sous « Donnees detaillees » : dans une colonne verticale,
    un menu au survol serait inutilement fragile, et ces liens portent
    l'essentiel du maillage interne vers les pages province. Le JavaScript les
    reecrit ensuite a partir des donnees du jour."""
    by_id = {p["id"]: p for p in config["pages"]}
    items = []
    # Depuis le 4 septembre 2026, la barre est groupee en trois blocs sous
    # les memes intertitres que le pied de page (Explorer, Comprendre, Le
    # site) : a neuf entrees, une liste plate se parcourt au lieu de se lire.
    # mainNav est une liste de groupes { titleKey, pages } ; une liste plate
    # d'identifiants reste acceptee, sans intertitre.
    entrees = []
    for groupe in config["mainNav"]:
        if isinstance(groupe, dict):
            entrees.append(("titre", groupe["titleKey"]))
            entrees.extend(("page", pid) for pid in groupe["pages"])
        else:
            entrees.append(("page", groupe))
    for genre, page_id in entrees:
        if genre == "titre":
            items.append('      <div class="side-nav-title">%s</div>'
                         % esc(strings_lang[page_id]))
            continue
        page = by_id[page_id]
        label = esc(label_for(page, strings_lang, i18n_lang))
        current = ' aria-current="page"' if page_id == current_id else ""
        if page_id != "donnees":
            items.append('      <a href="%s"%s>%s</a>'
                         % (urls.path(page_id, lang), current, label))
            continue

        # « Donnees detaillees » n'est pas une destination : c'est la categorie
        # qui porte la page de tableaux et les six pages province. En faire un
        # lien vers /donnees/ doublonnait avec son premier enfant — deux lignes
        # de navigation pour une seule URL. C'est donc un bouton de depliage,
        # et la page de tableaux descend dans la liste sous son propre nom.
        # La liste reste repliee par defaut — sinon la navigation fait sept
        # lignes de plus — mais elle est deja dans le HTML, donc suivie par les
        # moteurs de recherche, et deployee d'office sur ces pages.
        # « Ensemble du pays » porte un anneau vide la ou les provinces ont
        # leur pastille de couleur : sans lui, le premier item de la liste
        # commencait un cran avant les six autres. Un cercle vide plutot
        # qu'un point d'une septieme couleur — c'est le contour qui contient
        # les six, pas une province de plus. Demande du proprietaire, 28 aout.
        links = ['          <a class="tab-dropdown-item"%s href="%s">'
                 '<span class="dot dot-all"></span>%s</a>'
                 % (current, urls.path("donnees", lang),
                    esc(strings_lang["navDataTables"]))]
        for province in provinces:
            name = province["name"]
            links.append(
                '          <a class="tab-dropdown-item" href="%s">'
                '<span class="dot" style="background:%s;"></span>%s</a>'
                % (urls.province_path(name, lang),
                   PROVINCE_COLORS.get(name, "var(--ink-faint)"), esc(name)))
        # Le bouton porte lui-meme le libelle : son nom accessible est donc
        # « Donnees detaillees », et aria-expanded dit le reste. Pas d'aria-label,
        # qui masquerait ce texte aux lecteurs d'ecran.
        items.append(
            '      <div class="side-group">\n'
            '        <button class="side-toggle" type="button" aria-expanded="%s"\n'
            '                aria-controls="zonesDropdown">\n'
            '          <span>%s</span>\n'
            '          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>\n'
            '        </button>\n'
            '        <div class="side-sub" id="zonesDropdown"%s>\n%s\n        </div>\n'
            '      </div>' % (
                "true" if expand_provinces else "false",
                label,
                "" if expand_provinces else " hidden",
                "\n".join(links)))
    return ('    <nav class="side-nav" aria-label="%s">\n%s\n    </nav>'
            % (esc(strings_lang["navLabel"]), "\n".join(items)))


def build_breadcrumb(urls, lang, strings_lang, trail):
    """trail : liste de (libellé, chemin ou None pour la page courante)."""
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


def build_footer(config, urls, lang, strings_lang, i18n_lang, provinces):
    by_id = {p["id"]: p for p in config["pages"]}
    columns = []
    for column in config["footerNav"]:
        links = []
        for page_id in column["pages"]:
            links.append('        <li><a href="%s">%s</a></li>'
                         % (urls.path(page_id, lang),
                            esc(label_for(by_id[page_id], strings_lang, i18n_lang))))
        columns.append(
            '      <div class="footer-col">\n'
            '        <h2>%s</h2>\n'
            '        <ul>\n%s\n        </ul>\n'
            '      </div>' % (esc(strings_lang[column["titleKey"]]), "\n".join(links)))

    province_links = []
    for province in provinces:
        province_links.append(
            '        <li><a href="%s">%s</a></li>'
            % (urls.province_path(province["name"], lang), esc(province["name"])))
    columns.append(
        '      <div class="footer-col">\n'
        '        <h2>%s</h2>\n'
        '        <ul>\n%s\n        </ul>\n'
        '      </div>' % (esc(strings_lang["footerProvincesTitle"]),
                          "\n".join(province_links)))

    # Une seule ligne discrete plutot que deux pavas : l'avertissement doit
    # rester sur chaque page — un visiteur arrive de Google atterrit sur
    # n'importe laquelle, pas sur l'accueil — mais le texte complet, lui, n'a
    # besoin d'exister qu'une fois, sur la page A propos.
    return (
        '  <footer>\n'
        '    <div class="footer-nav">\n%s\n    </div>\n'
        '    <p class="footer-notice">%s <a href="%s">%s</a></p>\n'
        '  </footer>' % (
            "\n".join(columns),
            strings_lang["footerNotice"],
            urls.path("a-propos", lang),
            esc(strings_lang["footerNoticeMore"]),
        ))


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
            blocks.append(json_ld({
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": context["siteName"],
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
                             "name": context["siteName"],
                             "url": context["origin"] + "/"},
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


def province_rows_html(provinces, national, lang):
    """Lignes du tableau « par province », identiques à renderProvinceSummary."""
    total = (national or {}).get("confirmed")
    rows = []
    for province in sorted(provinces, key=lambda p: -(p.get("confirmed") or 0)):
        color = PROVINCE_COLORS.get(province["name"], "var(--ink-faint)")
        zones = province.get("healthZonesAffected")
        zones_text = "%s / %s" % (zones["n"], zones["total"]) if zones else "—"
        new_cases = province.get("newCases24h") or 0
        badge = ('<span class="zone-new-badge has-new">+%s</span>' % fmt(new_cases, lang)
                 if new_cases > 0 else
                 '<span class="zone-new-badge no-new">%s</span>' % fmt(new_cases, lang))
        # La part du pays a sa propre colonne : accolee au cumul, elle
        # empechait d'aligner les chiffres et se lisait comme une note.
        share = fmt_cfr(province["confirmed"] / float(total) * 100, lang) if total else "—"
        # Les lignes de province portent les quatre colonnes de deces du
        # bulletin, la somme est donc exacte ici — a la difference des lignes
        # de zone, ou il faut passer par zone_new_deaths().
        new_deaths = ((province.get("newDeathsCommunity24h") or 0)
                      + (province.get("newDeathsIntraCTE24h") or 0))
        deaths_badge = (
            '<span class="zone-new-badge has-new">+%s</span>' % fmt(new_deaths, lang)
            if new_deaths > 0 else
            '<span class="zone-new-badge no-new">%s</span>' % fmt(new_deaths, lang))
        rows.append(
            "              <tr>\n"
            '                <td><div class="zone-name-cell">'
            '<span class="zdot" style="background:%s;"></span>%s</div></td>\n'
            '                <td class="is-num">%s</td>\n'
            '                <td class="is-num is-soft">%s</td>\n'
            '                <td class="is-num">%s</td>\n'
            '                <td class="is-num"><span class="zone-badge %s">%s</span></td>\n'
            '                <td class="is-num">%s</td>\n'
            '                <td class="is-num">%s</td>\n'
            '                <td class="is-num">%s</td>\n'
            "              </tr>" % (
                color, esc(province["name"]),
                fmt(province.get("confirmed"), lang), share,
                fmt(province.get("deaths"), lang),
                cfr_badge_class(province.get("cfr")), fmt_cfr(province.get("cfr"), lang),
                zones_text, badge, deaths_badge))
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
    for zone in geo["zones"]:
        ours = ours_for(zone)
        if not ours:
            quiet.append('          <path d="%s"><title>%s (%s)</title></path>'
                         % (zone["d"], esc(zone["name"]), esc(zone["province"])))
            continue
        matched.add(zone["key"])
        cases = ours.get("cases") or 0
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

    return ('      <svg class="zonemap" viewBox="%s" role="img" aria-label="%s" '
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
    """Les memes cinq chiffres, en lignes compactes, pour le panneau a droite
    de la carte. Ils portent data-kpi et non un identifiant : renderKPIs()
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
        delta = ('<span class="d" data-kpi-delta="%s"></span>' % key) if key in with_delta else ""
        rows.append(
            '          <div class="cd-nat %s">\n'
            '            <span class="k" data-i18n="%s">%s</span>\n'
            '            <span class="n"><span class="v" data-kpi="%s">%s</span>%s</span>\n'
            '          </div>' % (key, label_key, esc(i18n_lang[label_key]),
                                  key, values[key], delta))
    return '        <div class="cd-national">\n%s\n        </div>' % "\n".join(rows)


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


def province_cards_html(provinces, urls, lang, strings_lang):
    cards = []
    for province in sorted(provinces, key=lambda p: -(p.get("confirmed") or 0)):
        # Plus de « 28 zones touchees sur 36 » sous les trois chiffres : le
        # compte de zones vit en tete de /donnees/ et dans la chronologie, et
        # la carte au-dessus le montre. Demande du proprietaire, 27 aout.
        zones_line = ""
        cards.append(
            '      <a class="province-card" href="%s" style="border-left-color:%s;">\n'
            "        <h3>%s</h3>\n"
            '        <div class="pc-stats">\n'
            '          <div class="pc-stat"><span class="k">%s</span>'
            '<span class="v">%s</span></div>\n'
            '          <div class="pc-stat"><span class="k">%s</span>'
            '<span class="v">%s</span></div>\n'
            '          <div class="pc-stat"><span class="k">%s</span>'
            '<span class="v">%s</span></div>\n'
            "        </div>%s\n"
            "      </a>" % (
                urls.province_path(province["name"], lang),
                PROVINCE_COLORS.get(province["name"], "var(--ink-faint)"),
                esc(province["name"]),
                esc(strings_lang["provincesCardCases"]), fmt(province.get("confirmed"), lang),
                esc(strings_lang["provincesCardDeaths"]), fmt(province.get("deaths"), lang),
                esc(strings_lang["provincesCardCfr"]), fmt_cfr(province.get("cfr"), lang),
                zones_line))
    return "\n".join(cards)


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

    prefix = "SitRep N°"
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
            parts.append(report_chip(prefix + str(report.get("sitrepNumber", "")),
                                     when, "/" + report["file"].lstrip("/"),
                                     i18n_lang["reportsDownload"],
                                     month=key, search=searchable))
    return "\n".join(parts)


def who_reports_list_html(who_reports, lang, i18n_lang, strings_lang):
    label = strings_lang["whoReportLabel"]
    situation = strings_lang["reportSituation"]
    parts = []
    for report in sorted(who_reports, key=lambda r: r.get("number") or "", reverse=True):
        when = situation_html(situation, long_date(report.get("date"), i18n_lang)) \
            if report.get("date") else esc(i18n_lang["reportsUnknownDate"])
        parts.append(report_chip(interp(label, {"n": report.get("number", "")}), when,
                                 "/" + report["file"].lstrip("/"),
                                 i18n_lang["reportsDownload"], variant="is-who"))
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
            "kind": "official",
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
                event["kind"], event["date"], esc(long_date(event["date"], i18n_lang)),
                heading, esc(event["title"]), heading, event["text"]))
    return "\n".join(parts)


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
                event["kind"], event["date"], esc(long_date(event["date"], i18n_lang)),
                heading, esc(event["title"]), heading, event["text"], toll, link))
    return "\n".join(parts)


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


def province_zones_table_html(zones, forms, lang, strings_lang, i18n_lang):
    """Le tableau des zones touchees d'une province.

    Les variations de 24 h etaient accolees au cumul entre parentheses —
    « 1 298 (+19) ». Elles ont leur colonne depuis le 26 aout : entre
    parentheses, elles empechaient d'aligner les chiffres, se lisaient comme
    une note, et n'etaient ni triables ni comparables d'une ligne a l'autre.
    Les six colonnes reprennent l'ordre du tableau de /donnees/, dont les
    libelles de variation sont repris tels quels.

    La note sur la somme des zones (`zonesSumNote`) n'est plus rendue ici mais
    par le gabarit, SOUS le panneau. Dans le cadre, sa longue phrase dictait la
    largeur : le panneau se cale sur son contenu le plus large, et la note
    l'emportait sur le tableau — il restait alors 440 px de fond vide a droite.
    """
    if not zones:
        return ('      <p class="map-note">%s</p>'
                % esc(strings_lang["provinceZonesEmpty"]))

    def badge(value):
        # « 0 » reste affiche : l'absence de nouveau cas est une information.
        n = max(0, value or 0)
        classe = "has-new" if n > 0 else "no-new"
        texte = ("+%s" % fmt(n, lang)) if n > 0 else fmt(n, lang)
        return '<span class="zone-new-badge %s">%s</span>' % (classe, texte)

    rows = []
    for zone in sorted(zones, key=lambda z: -(z.get("cases") or 0)):
        rows.append(
            "            <tr>\n"
            "              <td>%s</td>\n"
            '              <td class="is-num">%s</td>\n'
            '              <td class="is-num">%s</td>\n'
            '              <td class="is-num"><span class="zone-badge %s">%s</span></td>\n'
            '              <td class="is-num">%s</td>\n'
            '              <td class="is-num">%s</td>\n'
            "            </tr>" % (
                esc(zone["name"]),
                fmt(zone.get("cases"), lang),
                fmt(zone.get("deaths"), lang),
                cfr_badge_class(zone.get("cfr")), fmt_cfr(zone.get("cfr"), lang),
                badge(zone.get("newCases24h")),
                badge(zone_new_deaths(zone))))

    entetes = "".join(
        '<th%s>%s</th>' % ("" if i == 0 else ' class="is-num"', esc(libelle))
        for i, libelle in enumerate([
            strings_lang["provinceThZone"], strings_lang["provinceThCases"],
            strings_lang["provinceThDeaths"], strings_lang["provinceThCfr"],
            i18n_lang["zonesTh6"], i18n_lang["zonesTh7"]]))

    return (
        '      <div class="table-scroll">\n'
        '        <table class="zones-province" id="zonesProvinceTable">\n'
        '          <caption class="visually-hidden">%s</caption>\n'
        "          <thead>\n"
        "            <tr>%s</tr>\n"
        "          </thead>\n"
        "          <tbody>\n%s\n          </tbody>\n"
        "        </table>\n"
        "      </div>" % (
            esc(interp(strings_lang["provinceZonesTitle"], forms)),
            entetes,
            "\n".join(rows)))


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
SEUIL_COURBE_PROVINCE = 50


def province_chart_html(province, strings_lang, i18n_lang):
    if (province.get("confirmed") or 0) < SEUIL_COURBE_PROVINCE:
        return ""
    return (
        '  <section class="section">\n'
        '    <div class="section-head">\n'
        '      <h2 class="section-title">%s</h2>\n'
        '      <span class="section-sub">%s</span>\n'
        '    </div>\n'
        '\n'
        '    <div class="panel chart-panel-wrap">\n'
        # Le graphique de province se partage comme les autres : figure et note
        # comprises. Le libelle vient d'i18n, comme partout ailleurs.
        '      <div class="chart-actions" data-export-chart="provinceChart">\n'
        '        <button type="button" class="share-btn">\n'
        '          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="10.6" x2="15.4" y2="6.4"/><line x1="8.6" y1="13.4" x2="15.4" y2="17.6"/></svg>\n'
        '          <span data-i18n="chartShareBtn">%s</span>\n'
        '        </button>\n'
        '      </div>\n'
        '      <div class="chart-panel">\n'
        '        <canvas id="provinceChart" data-chart="provinceEpidemic"></canvas>\n'
        '      </div>\n'
        '      <div class="map-note chart-note"></div>\n'
        '    </div>\n'
        '  </section>\n'
        # Le titre porte le nom de la province entre parentheses. Sans lui,
        # « Evolution de l'epidemie » est mot pour mot l'intitule du premier
        # sous-onglet de /donnees/, qui lui trace le pays entier : un lecteur
        # arrive par le menu lateral n'a rien pour distinguer les deux courbes.
        % (esc(interp(strings_lang["provinceChartTitle"],
                      {"name": province["name"]})),
           esc(strings_lang["provinceChartSub"]),
           esc(i18n_lang["chartShareBtn"])))


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

    out["ripAsOf"] = esc(interp(strings_lang["cartoAsOf"],
                                {"date": long_date(date_bulletin or "", i18n_lang)}))
    return {"seed.%s" % k: v for k, v in out.items()}


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
    return "\n".join(tags)


def main():
    config = read_json(os.path.join(SITE, "pages.json"))
    global SITE_LANGUAGES
    SITE_LANGUAGES = list(config["site"]["languages"])
    strings = read_json(os.path.join(SITE, "strings.json"))
    i18n = load_i18n()
    layout = read(os.path.join(SITE, "layout.html"))

    latest = read_json(os.path.join(ROOT, "data", "latest.json"))
    zones_history = read_json(os.path.join(ROOT, "data", "zones-history.json"))
    sitreps = read_json(os.path.join(ROOT, "data", "sitreps.json"))
    who_reports = read_json(os.path.join(ROOT, "data", "who-reports.json"))
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
    riposte = {
        "alertes": read_json(os.path.join(ROOT, "data", "alertes.json")),
        "laboratoire": read_json(os.path.join(ROOT, "data", "laboratoire.json")),
        "contacts": read_json(os.path.join(ROOT, "data", "contacts-followup.json")),
        "cte": read_json(os.path.join(ROOT, "data", "cte.json")),
    }
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
        cards = province_cards_html(provinces, urls, lang, strings_lang)
        common_seed = {
            "seed.confirmed": fmt(national.get("confirmed"), lang),
            "seed.deaths": fmt(national.get("deaths"), lang),
            "seed.recovered": fmt(national.get("recovered"), lang),
            "seed.inCTE": fmt(national.get("inCTE"), lang),
            "seed.cfr": fmt_cfr(national.get("cfr"), lang),
            "seed.zonesSub": zones_sub(national, meta_data, lang, i18n_lang, strings_lang),
            "seed.sitrepRef": sitrep_ref(meta_data, lang, i18n_lang, strings_lang),
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
            "seed.provinceRows": province_rows_html(provinces, national, lang),
            "seed.agesRows": ages_rows_html(demographie, lang, strings_lang),
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
            "seed.whoReportsList": who_reports_list_html(who_reports, lang, i18n_lang, strings_lang),
            "seed.whoSectionStyle": "" if who_reports else "display:none;",
            "provinceCards": cards,
            "provinceCardsPlain": cards,
            "provinceTableRows": province_table_rows_html(provinces, urls, lang),
            "faqItems": faq_html,
        }

        events = timeline_events(strings, sitreps, lang, i18n_lang,
                                 config=config, urls=urls,
                                 zones_history=zones_history, geo=geo,
                                 latest_zones=latest.get("healthZones", []))
        common_seed["timelineItems"] = render_timeline_vertical(
            events, strings_lang, i18n_lang, urls, lang, config["provinceSlugs"])
        # L'apercu part du debut de l'epidemie et s'arrete au sixieme jalon :
        # on lit la chronologie dans son ordre, et le lien en dessous mene a
        # la suite. Six et non quatre parce que la piste en tient 5,7 sur un
        # ecran de 1920 px — a quatre il restait un vide de 404 px a droite,
        # et sur mobile le defilement passe de 840 a 1 260 px.
        common_seed["timelineTeaser"] = render_timeline(
            events[:6], strings_lang, i18n_lang, heading="h3")
        common_seed["cartogram"] = zone_map_html(
            config, geo, latest.get("healthZones", []), provinces, urls, lang,
            strings_lang)
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
        common_seed["seed.cartoAsOf"] = esc(interp(strings_lang["cartoAsOf"], {
            "date": long_date((latest.get("meta") or {}).get("reportingDate", ""), i18n_lang)}))
        common_seed["seed.provincesTouched"] = esc(interp(
            strings_lang["cartoZonesTouched"],
            {"n": touched, "total": len(geo["zones"])}))
        common_seed["panelStats"] = panel_stats_html(national, lang, i18n_lang)
        common_seed.update(riposte_seed(riposte, meta_data, lang, strings_lang, i18n_lang))

        pages = [(page, None) for page in config["pages"]]
        pages += [(config["provincePage"], province) for province in provinces]

        for page, province in pages:
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

def lang_switch_html(config, alt_paths, lang):
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

    fragment = read(os.path.join(SITE, "pages", fragment_name))

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
    values["repository"] = site["repository"]

    if is_province:
        name = province["name"]
        zones = zones_by_province.get(name, [])
        zone_info = province.get("healthZonesAffected")
        if zone_info:
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
            "province.cases": fmt(province.get("confirmed"), lang),
            "province.deaths": fmt(province.get("deaths"), lang),
            "province.cfr": fmt_cfr(province.get("cfr"), lang),
            "province.shareSentence": esc(share),
            "province.newDeaths": esc(interp(strings_lang["provinceNewDeaths"],
                                             {"n": fmt(new_deaths, lang)})),
            "province.zonesTitle": esc(interp(strings_lang["provinceZonesTitle"], forms)),
            "province.zonesTable": province_zones_table_html(
                zones, forms, lang, strings_lang, i18n_lang),
            "province.fullTable": esc(interp(strings_lang["provinceOpenFullTable"], forms)),
            **province_map_values(province_maps, name, zones, config, lang,
                                  strings_lang, geo.get("aliases", {})),
            "province.chart": province_chart_html(province, strings_lang, i18n_lang),
            "province.query": name.replace(" ", "%20"),
            # Rang dans le pays, puis quand ca a commence, puis quand ca a
            # bouge pour la derniere fois : un bloc temporel qui se lit d'un
            # trait, sous le paragraphe qui porte la situation du jour.
            "province.rank": " ".join(
                x for x in (esc(rank_line), arrival_line, esc(window_line)) if x),
        })

    content = render(fragment, values, fragment_name + " [" + lang + "]")

    # Chart.js pese 200 Ko : inutile de le charger sur une page province
    # qui n'a pas de graphique. « needs » est declare par type de page,
    # or ici le besoin varie d'une province a l'autre.
    besoins = list(page.get("needs", []))
    if is_province and "chart" in besoins and not values.get("province.chart"):
        besoins.remove("chart")

    canonical = urls.absolute(path)
    schema_context = {
        "meta": meta, "lang": lang, "canonical": canonical, "origin": origin,
        "siteName": strings_lang["siteTitleMain"],
        "keywords": ["Ebola", "RDC", "DRC", "épidémie", "santé publique",
                     "Bundibugyo", "SitRep"],
        "faqPlain": faq_plain,
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
        "lang": lang,
        # Jetons de cache des fichiers statiques : c'est le gabarit qui porte
        # les balises <link> et <script>, donc c'est ici qu'ils doivent vivre.
        "v.css": jeton_version("assets/css/site.css"),
        "v.app": jeton_version("assets/js/app.js"),
        "v.i18n": jeton_version("assets/js/i18n.js"),
        "title": esc(meta["title"]),
        "description": esc(meta["description"]),
        "canonical": canonical,
        "alternates": alternates_html(config, urls, alt_paths),
        "siteName": esc(strings_lang["siteTitleMain"]),
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
        "langSwitch": lang_switch_html(config, alt_paths, lang),
        "nav": build_nav(config, urls, lang, strings_lang, i18n_lang,
                         None if is_province else page.get("id"), provinces,
                         expand_provinces=is_province or page.get("id") in
                         ("donnees",)),
        "breadcrumb": build_breadcrumb(urls, lang, strings_lang, trail),
        "content": content,
        "footer": build_footer(config, urls, lang, strings_lang, i18n_lang,
                               provinces),
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
