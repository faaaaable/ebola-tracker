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

import io
import json
import os
import re
import subprocess
import sys
from datetime import date

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

def fmt(value, lang):
    """Équivalent de fmt() dans app.js (Number.toLocaleString)."""
    if value is None:
        return "—"
    sep = NNBSP if lang == "fr" else ","
    return "{:,}".format(int(value)).replace(",", sep)


def fmt_cfr(value):
    """Équivalent de cfr.toFixed(1) + '%' : toujours un point décimal."""
    if value is None:
        return "—"
    return "{:.1f}%".format(float(value))


def fmt_decimal(value, lang):
    """Nombre a une decimale, pour le texte redige : virgule en francais.

    Distinct de fmt_cfr(), qui reproduit volontairement le point decimal de
    toFixed() pour rester identique a ce que le JavaScript reecrit dans les
    memes elements.
    """
    if value is None:
        return "—"
    text = "%.1f" % float(value)
    return text.replace(".", ",") if lang == "fr" else text


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
        slug = self.slugs[page_id][lang]
        return "/" + slug if lang == "fr" else "/en/" + slug

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
    for page_id in config["mainNav"]:
        page = by_id[page_id]
        label = esc(label_for(page, strings_lang, i18n_lang))
        current = ' aria-current="page"' if page_id == current_id else ""
        if page_id != "donnees":
            items.append('      <a href="%s"%s>%s</a>'
                         % (urls.path(page_id, lang), current, label))
            continue

        # « Donnees detaillees » porte la liste des provinces. Elle reste repliee
        # par defaut — sinon la navigation fait sept lignes de plus — mais elle
        # est deja dans le HTML, donc suivie par les moteurs de recherche, et
        # deployee d'office quand on est sur une de ces pages.
        links = ['          <a class="tab-dropdown-item" href="%s">%s</a>'
                 % (urls.path("donnees", lang), esc(i18n_lang["zonesFilterAll"]))]
        for province in provinces:
            name = province["name"]
            links.append(
                '          <a class="tab-dropdown-item" href="%s">'
                '<span class="dot" style="background:%s;"></span>%s</a>'
                % (urls.province_path(name, lang),
                   PROVINCE_COLORS.get(name, "var(--ink-faint)"), esc(name)))
        items.append(
            '      <div class="side-group">\n'
            '        <a href="%s"%s>%s</a>\n'
            '        <button class="side-toggle" type="button" aria-expanded="%s"\n'
            '                aria-controls="zonesDropdown" aria-label="%s">\n'
            '          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>\n'
            '        </button>\n'
            '        <div class="side-sub" id="zonesDropdown"%s>\n%s\n        </div>\n'
            '      </div>' % (
                urls.path(page_id, lang), current, label,
                "true" if expand_provinces else "false",
                esc(strings_lang["navProvincesToggle"]),
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


def build_related(config, urls, lang, strings_lang, i18n_lang, related_ids):
    if not related_ids:
        return ""
    by_id = {p["id"]: p for p in config["pages"]}
    items = []
    for page_id in related_ids:
        page = by_id[page_id]
        items.append('        <li><a href="%s">%s</a></li>'
                     % (urls.path(page_id, lang),
                        esc(page["meta"][lang]["h1"])))
    return ('    <div class="related">\n'
            '      <h2>%s</h2>\n'
            '      <ul>\n%s\n      </ul>\n'
            '    </div>' % (esc(strings_lang["relatedTitle"]), "\n".join(items)))


# --------------------------------------------------------------------------
# Données structurées
# --------------------------------------------------------------------------

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
                "inLanguage": ["fr", "en"],
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


def zones_sub(national, meta, lang, i18n_lang):
    """Reproduit tr('zonesTableSub')(n, total, num, date) de app.js."""
    zones = (national or {}).get("healthZonesAffected") or {}
    count, total = zones.get("n", 0), zones.get("total", 151)
    number = (meta or {}).get("sitrepNumber", "")
    reporting = (meta or {}).get("reportingDate", "")
    if lang == "fr":
        text = "%s zones de santé touchées sur %s" % (count, total)
        if number:
            text += " · SitRep N°%s" % number
        if reporting:
            text += " du %s" % short_date(reporting, i18n_lang)
    else:
        text = "%s health zones affected out of %s" % (count, total)
        if number:
            text += " · SitRep N°%s" % number
        if reporting:
            text += " of %s" % short_date(reporting, i18n_lang)
    return esc(text)


def sitrep_ref(meta, lang, i18n_lang):
    """« SitRep N°097 du 19 août 2026 » — repère de fraîcheur sur les pages
    où le total national des zones touchées n'aurait pas de sens."""
    number = (meta or {}).get("sitrepNumber", "")
    reporting = (meta or {}).get("reportingDate", "")
    if not number:
        return ""
    joiner = " du " if lang == "fr" else " of "
    text = "SitRep N°%s" % number
    if reporting:
        text += joiner + long_date(reporting, i18n_lang)
    return esc(text)


def ordinal(n, lang):
    """« 2e » en francais, « 2nd » en anglais.

    L'anglais a trois exceptions (1st, 2nd, 3rd) et un piege : de 11 a 13, on
    dit bien 11th, 12th, 13th malgre le chiffre des unites.
    """
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
        share = ""
        if total:
            share = (' <span style="color:var(--ink-faint);">(%.1f%%)</span>'
                     % (province["confirmed"] / float(total) * 100))
        rows.append(
            "              <tr>\n"
            '                <td><div class="zone-name-cell">'
            '<span class="zdot" style="background:%s;"></span>%s</div></td>\n'
            "                <td>%s%s</td>\n"
            "                <td>%s</td>\n"
            '                <td><span class="zone-badge %s">%s</span></td>\n'
            "                <td>%s</td>\n"
            "                <td>%s</td>\n"
            "              </tr>" % (
                color, esc(province["name"]),
                fmt(province.get("confirmed"), lang), share,
                fmt(province.get("deaths"), lang),
                cfr_badge_class(province.get("cfr")), fmt_cfr(province.get("cfr")),
                zones_text, badge))
    return "\n".join(rows)


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
        marks.append(
            '          <g class="zm-mark is-%s" data-x="%s" data-y="%s" '
            'transform="translate(%s %s)">'
            '<circle r="3.2"><title>%s</title></circle>'
            '<text x="7" y="3.6">%s</text></g>'
            % (place["kind"], place["x"], place["y"], place["x"], place["y"],
               esc(title), esc(place["name"])))

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
        new_deaths = ((ours or {}).get("deathsCommunity24h") or 0) \
            + ((ours or {}).get("deathsIntraCTE24h") or 0)
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
            '          <g class="zm-mark is-%s" data-x="%s" data-y="%s" '
            'transform="translate(%s %s)">'
            '<circle r="3.2"/><text x="7" y="3.6">%s</text></g>'
            % (place["kind"], place["x"], place["y"], place["x"], place["y"],
               esc(place["name"])))

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
        "cfr": fmt_cfr(national.get("cfr")),
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
    first = None
    last = None
    previous = 0
    for date, value in points:
        if first is None and value > 0:
            first = date
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


def sparkline_svg(points, peak, width=132.0, height=30.0):
    """Vignette d'evolution, tracee a la generation.

    Toutes les provinces partagent le meme maximum : les six vignettes sont
    alors comparables d'un coup d'oeil, ce qui est tout l'interet de petits
    multiples. Un trace fige en SVG ne coute ni bibliotheque ni requete.
    """
    if len(points) < 2 or not peak:
        return ""
    span = len(points) - 1
    coords = []
    for index, (_date, value) in enumerate(points):
        x = index * width / span
        y = height - (value / float(peak)) * (height - 2) - 1
        coords.append("%.1f %.1f" % (x, y))
    line = "M" + "L".join(coords)
    area = "%s L%.1f %.1f L0 %.1f Z" % (line, width, height, height)
    return ('<svg class="spark" viewBox="0 0 %g %g" preserveAspectRatio="none" '
            'aria-hidden="true"><path class="spark-area" d="%s"/>'
            '<path class="spark-line" d="%s"/></svg>' % (width, height, area, line))


def province_cards_html(provinces, urls, lang, strings_lang, history=None, peak=None):
    cards = []
    for province in sorted(provinces, key=lambda p: -(p.get("confirmed") or 0)):
        zones = province.get("healthZonesAffected")
        zones_line = ""
        if zones:
            zones_line = ('\n        <div class="pc-zones">%s</div>'
                          % esc(interp(strings_lang["provincesCardZones"],
                                       {"n": zones["n"], "total": zones["total"]})))
        spark = ""
        if history is not None:
            drawing = sparkline_svg(province_series(history, province["name"]), peak)
            if drawing:
                spark = '\n        <div class="pc-spark">%s</div>' % drawing
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
            "        </div>%s%s\n"
            "      </a>" % (
                urls.province_path(province["name"], lang),
                PROVINCE_COLORS.get(province["name"], "var(--ink-faint)"),
                esc(province["name"]),
                esc(strings_lang["provincesCardCases"]), fmt(province.get("confirmed"), lang),
                esc(strings_lang["provincesCardDeaths"]), fmt(province.get("deaths"), lang),
                esc(strings_lang["provincesCardCfr"]), fmt_cfr(province.get("cfr")),
                zones_line, spark))
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
                cfr_badge_class(province.get("cfr")), fmt_cfr(province.get("cfr")),
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
            esc(label), DOWNLOAD_ICON, esc(date_text)))


def reports_list_html(reports, lang, i18n_lang):
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
    situation = "Situation au %s" if lang == "fr" else "Situation as of %s"
    parts = []
    for key in order:
        group = groups[key]
        parts.append('        <div class="reports-month-header" data-month-key="%s">%s</div>'
                     % (esc(key), esc(group["label"])))
        for report in group["reports"]:
            reporting = report.get("reportingDate")
            when = (situation % long_date(reporting, i18n_lang)) if reporting \
                else i18n_lang["reportsUnknownDate"]
            searchable = "%s %s %s" % (report.get("sitrepNumber", ""),
                                       group["label"], reporting or "")
            parts.append(report_chip(prefix + str(report.get("sitrepNumber", "")),
                                     when, "/" + report["file"].lstrip("/"),
                                     i18n_lang["reportsDownload"],
                                     month=key, search=searchable))
    return "\n".join(parts)


def who_reports_list_html(who_reports, lang, i18n_lang):
    label = "Rapport N°%s" if lang == "fr" else "Report N°%s"
    situation = "Situation au %s" if lang == "fr" else "Situation as of %s"
    parts = []
    for report in sorted(who_reports, key=lambda r: r.get("number") or "", reverse=True):
        when = (situation % long_date(report.get("date"), i18n_lang)) \
            if report.get("date") else i18n_lang["reportsUnknownDate"]
        parts.append(report_chip(label % report.get("number", ""), when,
                                 "/" + report["file"].lstrip("/"),
                                 i18n_lang["reportsDownload"], variant="is-who"))
    return "\n".join(parts)


def social_updates_list_html(updates, lang, i18n_lang):
    situation = "Situation au %s" if lang == "fr" else "Situation as of %s"
    parts = []
    for update in sorted(updates, key=lambda u: u.get("date") or "", reverse=True):
        parts.append(report_chip(
            i18n_lang["socialUpdatesLabel"],
            situation % long_date(update.get("date"), i18n_lang),
            update.get("url", "#"), i18n_lang["socialUpdatesOpenLink"],
            variant="is-social"))
    return "\n".join(parts)


def province_arrival_events(config, province_history, strings_lang, lang, i18n_lang,
                            urls=None):
    """Date a laquelle chaque province enregistre son premier cas confirme.

    Elle se lit dans data/province-history.json, qui donne le cumul par province
    bulletin apres bulletin. La province de depart — celle dont la premiere date
    est la plus ancienne — est ecartee : son arrivee, c'est la declaration de
    l'epidemie, deja presente dans la chronologie.

    Le fichier contient des lignes parasites issues de l'extraction des PDF
    (« touchees », par exemple) : on ne retient que les provinces connues.
    """
    known = set(config["provinceSlugs"])
    first = {}
    for entry in sorted(province_history, key=lambda e: e.get("date") or ""):
        date = entry.get("date")
        if not date:
            continue
        for province in entry.get("provinces", []):
            name = province.get("name")
            if name not in known or name in first:
                continue
            if (province.get("confirmed") or 0) > 0:
                first[name] = date

    if len(first) < 2:
        return []
    origin = min(first, key=lambda n: first[n])

    events = []
    for name, date in sorted(first.items(), key=lambda item: item[1]):
        if name == origin:
            continue
        forms = province_forms(config, name, lang)
        events.append({
            "date": date,
            "kind": "spread",
            "title": interp(strings_lang["timelineSpreadTitle"], forms),
            "text": esc(interp(strings_lang["timelineSpreadText"], forms)),
            "source": None,
            "province": name,
        })
    return events


def timeline_events(strings, sitreps, lang, i18n_lang, config=None,
                    province_history=None, urls=None):
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

    thresholds("confirmed", [1000, 2000, 3000, 4000, 5000],
               "timelineMilestoneCasesTitle", "timelineMilestoneCasesText", "milestone")
    thresholds("deaths", [1000, 2000],
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

    if config is not None and province_history:
        events += province_arrival_events(
            config, province_history, strings_lang, lang, i18n_lang, urls=urls)

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


def province_zones_table_html(zones, forms, lang, strings_lang):
    if not zones:
        return ('      <p class="map-note">%s</p>'
                % esc(strings_lang["provinceZonesEmpty"]))
    def delta(value):
        # « (+0) » compris : l'absence de nouveau cas est une information.
        if value is None:
            return ""
        return ' <span class="td-delta">(+%s)</span>' % fmt(max(0, value), lang)

    rows = []
    for zone in sorted(zones, key=lambda z: -(z.get("cases") or 0)):
        new_deaths = (zone.get("deathsCommunity24h") or 0) + (zone.get("deathsIntraCTE24h") or 0)
        rows.append(
            "            <tr>\n"
            "              <td>%s</td>\n"
            "              <td>%s%s</td>\n"
            "              <td>%s%s</td>\n"
            '              <td><span class="zone-badge %s">%s</span></td>\n'
            "            </tr>" % (
                esc(zone["name"]),
                fmt(zone.get("cases"), lang), delta(zone.get("newCases24h")),
                fmt(zone.get("deaths"), lang), delta(new_deaths),
                cfr_badge_class(zone.get("cfr")), fmt_cfr(zone.get("cfr"))))
    return (
        '      <div class="table-scroll">\n'
        "        <table>\n"
        "          <caption class=\"visually-hidden\">%s</caption>\n"
        "          <thead>\n"
        "            <tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>\n"
        "          </thead>\n"
        "          <tbody>\n%s\n          </tbody>\n"
        "        </table>\n"
        "      </div>" % (
            esc(interp(strings_lang["provinceZonesTitle"], forms)),
            esc(strings_lang["provinceThZone"]), esc(strings_lang["provinceThCases"]),
            esc(strings_lang["provinceThDeaths"]), esc(strings_lang["provinceThCfr"]),
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
    strings = read_json(os.path.join(SITE, "strings.json"))
    i18n = load_i18n()
    layout = read(os.path.join(SITE, "layout.html"))

    latest = read_json(os.path.join(ROOT, "data", "latest.json"))
    sitreps = read_json(os.path.join(ROOT, "data", "sitreps.json"))
    who_reports = read_json(os.path.join(ROOT, "data", "who-reports.json"))
    social_updates = read_json(os.path.join(ROOT, "data", "social-updates.json"))
    province_history = read_json(os.path.join(ROOT, "data", "province-history.json"))
    # Traces des zones de sante : geometrie figee, produite a part par
    # scripts/build_geo.py. Elle ne change qu'en cas de nouvelle province
    # touchee ou de mise a jour de la source.
    geo = read_json(os.path.join(SITE, "geo", "zones-overview.json"))
    province_maps = read_json(os.path.join(SITE, "geo", "province-maps.json"))["maps"]

    national = latest.get("national") or {}
    meta_data = latest.get("meta") or {}
    provinces = [p for p in latest.get("provinces", [])
                 if p.get("name") in config["provinceSlugs"]]
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
        spark_peak = max((p.get("confirmed") or 0) for p in provinces) if provinces else 0
        cards = province_cards_html(provinces, urls, lang, strings_lang,
                                    history=province_history, peak=spark_peak)
        # L'accueil garde des cartes nues : les vignettes n'y apportent qu'un
        # motif de plus sur une page qui doit rester sobre.
        cards_plain = province_cards_html(provinces, urls, lang, strings_lang)
        common_seed = {
            "seed.confirmed": fmt(national.get("confirmed"), lang),
            "seed.deaths": fmt(national.get("deaths"), lang),
            "seed.recovered": fmt(national.get("recovered"), lang),
            "seed.inCTE": fmt(national.get("inCTE"), lang),
            "seed.cfr": fmt_cfr(national.get("cfr")),
            "seed.zonesSub": zones_sub(national, meta_data, lang, i18n_lang),
            "seed.sitrepRef": sitrep_ref(meta_data, lang, i18n_lang),
            "mapHint": hint_pair(strings_lang, "cartoHint", "cartoHintTouch"),
            "seed.provinceRows": province_rows_html(provinces, national, lang),
            "seed.reportsList": reports_list_html(latest.get("reports", []), lang, i18n_lang),
            "seed.whoReportsList": who_reports_list_html(who_reports, lang, i18n_lang),
            "seed.socialUpdatesList": social_updates_list_html(social_updates, lang, i18n_lang),
            "seed.whoSectionStyle": "" if who_reports else "display:none;",
            "seed.socialSectionStyle": "" if social_updates else "display:none;",
            "provinceCards": cards,
            "provinceCardsPlain": cards_plain,
            "provinceTableRows": province_table_rows_html(provinces, urls, lang),
            "faqItems": faq_html,
        }

        events = timeline_events(strings, sitreps, lang, i18n_lang,
                                 config=config, province_history=province_history,
                                 urls=urls)
        common_seed["timelineItems"] = render_timeline_vertical(
            events, strings_lang, i18n_lang, urls, lang, config["provinceSlugs"])
        # L'apercu de l'accueil part du debut de l'epidemie : quatre jalons a
        # partir de la premiere date, et le lien en dessous mene a la suite.
        common_seed["timelineTeaser"] = render_timeline(
            events[:4], strings_lang, i18n_lang, heading="h3")
        common_seed["cartogram"] = zone_map_html(
            config, geo, latest.get("healthZones", []), provinces, urls, lang,
            strings_lang)
        touched = len(latest.get("healthZones", []))
        common_seed["seed.provincesTouched"] = esc(interp(
            strings_lang["cartoZonesTouched"],
            {"n": touched, "total": len(geo["zones"])}))
        common_seed["panelStats"] = panel_stats_html(national, lang, i18n_lang)

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
        first_case, last_case = province_case_window(province_history, name)
        window_line = ""
        if first_case and last_case and first_case != last_case:
            window_line = interp(strings_lang["provinceCaseWindow"], {
                "first": long_date(first_case, i18n_lang),
                "last": long_date(last_case, i18n_lang)})
        elif first_case:
            window_line = interp(strings_lang["provinceCaseWindowSingle"], {
                "first": long_date(first_case, i18n_lang)})

        meta = {
            "h1": interp(strings_lang["provinceH1"], forms),
            "title": interp(strings_lang["provinceMetaTitle"], forms),
            "description": interp(strings_lang["provinceMetaDescription"], sentence),
        }
        alt_paths = {code: urls.province_path(name, code) for code in site["languages"]}
        trail = [(label_for(by_id_page(config, "donnees"), strings_lang, i18n_lang),
                  urls.path("donnees", lang)),
                 (name, None)]
        related = ""
    else:
        path = urls.path(page["id"], lang)
        fragment_name = page["fragment"]
        meta = dict(page["meta"][lang])
        alt_paths = {code: urls.path(page["id"], code) for code in site["languages"]}
        trail = [] if page["id"] == "accueil" else [(meta["h1"], None)]
        related = build_related(config, urls, lang, strings_lang, i18n_lang,
                                page.get("related", []))

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
            "province.intro": interp(strings_lang["provinceIntro"], dict(
                sentence, zonesSentence=esc(zones_sentence))),
            "province.cases": fmt(province.get("confirmed"), lang),
            "province.deaths": fmt(province.get("deaths"), lang),
            "province.cfr": fmt_cfr(province.get("cfr")),
            "province.shareSentence": esc(share),
            "province.newDeaths": esc(interp(strings_lang["provinceNewDeaths"],
                                             {"n": fmt(new_deaths, lang)})),
            "province.zonesTitle": esc(interp(strings_lang["provinceZonesTitle"], forms)),
            "province.zonesTable": province_zones_table_html(
                zones, forms, lang, strings_lang),
            **province_map_values(province_maps, name, zones, config, lang,
                                  strings_lang, geo.get("aliases", {})),
            "province.query": name.replace(" ", "%20"),
            "province.rank": esc(" ".join(x for x in (rank_line, window_line) if x)),
        })
    values["t.provinceUpdatedNote"] = esc(interp(
        strings_lang["provinceUpdatedNote"],
        {"date": long_date(meta_data.get("reportingDate"), i18n_lang)}))

    content = render(fragment, values, fragment_name + " [" + lang + "]")

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
        "title": esc(meta["title"]),
        "description": esc(meta["description"]),
        "canonical": canonical,
        "altFr": urls.absolute(alt_paths["fr"]),
        "altEn": urls.absolute(alt_paths["en"]),
        "siteName": esc(strings_lang["siteTitleMain"]),
        "ogType": "website" if page.get("id") == "accueil" else "article",
        "ogLocale": "fr_FR" if lang == "fr" else "en_US",
        "ogLocaleAlt": "en_US" if lang == "fr" else "fr_FR",
        "ogImage": origin + site["ogImage"],
        "verification": site["googleSiteVerification"],
        "analytics": site["analytics"],
        "jsonLd": build_json_ld(page.get("schema", []), schema_context),
        "headAssets": head_assets(page.get("needs", [])),
        "homeUrl": urls.path("accueil", lang),
        "t.siteTitleLinkLabel": esc(strings_lang["siteTitleLinkLabel"]),
        "frActive": " active" if lang == "fr" else "",
        "enActive": " active" if lang == "en" else "",
        "frCurrent": ' aria-current="true"' if lang == "fr" else "",
        "enCurrent": ' aria-current="true"' if lang == "en" else "",
        "nav": build_nav(config, urls, lang, strings_lang, i18n_lang,
                         None if is_province else page.get("id"), provinces,
                         expand_provinces=is_province or page.get("id") in
                         ("donnees",)),
        "breadcrumb": build_breadcrumb(urls, lang, strings_lang, trail),
        "content": content,
        "related": related,
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
            # Une page anglaise ne doit pas primer sur son équivalent français.
            adjusted = priority if lang == "fr" else "%.1f" % max(
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


NOT_FOUND = {
    "fr": ("Page introuvable",
           "Cette adresse n'existe pas ou n'existe plus. "
           "Voici par où reprendre :"),
    "en": ("Page not found",
           "This address does not exist, or no longer does. "
           "Here is where to pick up:"),
}


def write_404(config, urls, strings, i18n, layout):
    """Page servie par GitHub Pages pour toute URL inconnue.

    Elle est bilingue : a ce stade on ne sait pas quelle langue le visiteur
    cherchait. Elle n'a pas de colonne laterale — la liste des pages tient
    lieu de navigation, et c'est tout ce dont on a besoin ici.
    """
    blocks = []
    for lang in config["site"]["languages"]:
        title, intro = NOT_FOUND[lang]
        links = []
        for page in config["pages"]:
            links.append('          <li><a href="%s">%s</a></li>'
                         % (urls.path(page["id"], lang),
                            esc(page["meta"][lang]["h1"])))
        heading = "h1" if lang == "fr" else "h2"
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
        '<link rel="stylesheet" href="/assets/css/site.css">',
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
