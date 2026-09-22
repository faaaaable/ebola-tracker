#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les flux RSS du site : /feed.xml, /en/feed.xml, /sw/feed.xml.

Un flux par langue, une entree par lettre, la plus recente en tete. La
source est la meme que celle des pages : data/lettres/<num>.json pour les
chiffres, data/bulletin-notes.json pour le resume redige a la parution.
Rien n'est saisi ici a la main — un flux qui raconterait autre chose que
la page qu'il annonce serait pire que pas de flux du tout.

Le flux est le socle des autres canaux : les services qui transforment un
flux en lettre par courriel (Brevo, Buttondown) et les relais Slack ou
Teams des organisations qui suivent l'epidemie s'y branchent sans que le
depot ait a les connaitre.

Appele par scripts/build_pages.py a chaque generation, et par le workflow
.github/workflows/flux-et-alertes.yml des qu'une lettre parait.
"""

import json
import os
import sys
from datetime import datetime, timezone
from email.utils import format_datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_pages import ROOT, esc, fmt, loc, long_date, load_i18n  # noqa: E402

LETTRES = os.path.join(ROOT, "data", "lettres")
NOTES = os.path.join(ROOT, "data", "bulletin-notes.json")
PAGES = os.path.join(ROOT, "site", "pages.json")
STRINGS = os.path.join(ROOT, "site", "strings.json")

# Combien d'entrees garder. Au-dela, un lecteur qui decouvre le flux
# recevrait des mois d'archives d'un coup ; les anciennes lettres restent
# accessibles sur le site.
MAX_ENTREES = 20


def _lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def _horodatage(iso):
    """RFC 822, ce qu'attend RSS. La lettre n'a qu'une date, pas d'heure :
    on la pose a midi UTC, ni la veille ni le lendemain sous aucun fuseau."""
    d = datetime.strptime(iso, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)
    return format_datetime(d)


def _lettres():
    """Les lettres du plus recent au plus ancien, numero et contenu."""
    nums = sorted((n[:-5] for n in os.listdir(LETTRES) if n.endswith(".json")),
                  reverse=True)
    return [(num, _lire(os.path.join(LETTRES, "%s.json" % num)))
            for num in nums[:MAX_ENTREES]]


def _url_lettre(origin, slugs, lang, num):
    """/lettre/128/, /en/letter/128/, /sw/barua/128/ — les memes adresses
    que celles que construit bulletin.pages_lettres()."""
    return "%s%s/%s%s/" % (origin, loc(lang, "urlPrefix"), slugs[lang], num)


def _resume(notes, num, lang):
    """Le resume des Defis, redige a chaque integration : c'est lui qui dit
    ce que la lettre apporte. A defaut, le flux se passe de description
    plutot que d'en inventer une."""
    note = (notes.get(num) or {}).get("defis") or {}
    return note.get(lang) or note.get("fr") or ""


def _chiffres(lettre, i18n_lang, lang):
    """Les trois chiffres de tete, avec les libelles des cartes du site
    (assets/js/i18n.js) : le flux nomme les choses comme les pages."""
    nat = lettre["national"]
    return "%s : %s · %s : %s · %s : %s" % (
        i18n_lang["labelConfirmed"], fmt(nat["confirmed"], lang),
        i18n_lang["labelDeaths"], fmt(nat["deaths"], lang),
        i18n_lang["labelCfr"],
        ("%.1f" % nat["cfr"]).replace(".", loc(lang, "decimal")) + loc(lang, "percent"))


def contexte():
    """Tout ce qu'il faut pour annoncer une lettre, lu une fois."""
    return {"config": _lire(PAGES), "strings": _lire(STRINGS),
            "notes": _lire(NOTES), "i18n": load_i18n()}


def annonce(num, lettre, lang, ctx):
    """Ce qu'on dit d'une lettre, quel que soit le canal.

    Le flux RSS et le message Telegram passent tous deux par ici : une
    annonce qui differerait d'un canal a l'autre finirait par contredire la
    page qu'elle annonce.
    """
    config, S, i18n_lang = ctx["config"], ctx["strings"][lang], ctx["i18n"][lang]
    origin = config["site"]["origin"]
    slugs = next(p for p in config["pages"] if p["id"] == "bulletin")["slug"]
    meta = lettre["meta"]
    return {
        # Le titre porte le numero ET la date de situation : hors du site,
        # dans un agregateur ou un fil de discussion, l'entree est lue sans
        # son contexte.
        "titre": "%s — %s" % (S["feedItemTitle"].replace("{num}", num),
                              long_date(meta["reportingDate"], i18n_lang)),
        "url": _url_lettre(origin, slugs, lang, num),
        "chiffres": _chiffres(lettre, i18n_lang, lang),
        "resume": _resume(ctx["notes"], num, lang),
        "date": meta.get("publicationDate") or meta["reportingDate"],
    }


def _canal(lang, ctx, lettres):
    config = ctx["config"]
    site, origin = config["site"], config["site"]["origin"]
    slugs = next(p for p in config["pages"] if p["id"] == "bulletin")["slug"]
    S = ctx["strings"][lang]
    feed_url = "%s%s/feed.xml" % (origin, loc(lang, "urlPrefix"))

    entrees = []
    for num, lettre in lettres:
        a = annonce(num, lettre, lang, ctx)
        url, titre = a["url"], a["titre"]
        corps = [a["chiffres"]] + ([a["resume"]] if a["resume"] else [])
        entrees.append("\n".join([
            "  <item>",
            "   <title>%s</title>" % esc(titre),
            "   <link>%s</link>" % esc(url),
            "   <guid isPermaLink=\"true\">%s</guid>" % esc(url),
            "   <pubDate>%s</pubDate>" % _horodatage(a["date"]),
            "   <description><![CDATA[%s]]></description>"
            % "\n\n".join("<p>%s</p>" % p for p in corps),
            "  </item>",
        ]))

    derniere = lettres[0][1]["meta"] if lettres else {}
    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        ' <channel>',
        '  <title>%s</title>' % esc(S["feedTitle"]),
        '  <link>%s%s/%s</link>' % (origin, loc(lang, "urlPrefix"), slugs[lang]),
        '  <description>%s</description>' % esc(S["feedDescription"]),
        '  <language>%s</language>' % loc(lang, "htmlLang"),
        '  <lastBuildDate>%s</lastBuildDate>'
        % _horodatage(derniere.get("publicationDate") or derniere.get("reportingDate")
                      or datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        '  <atom:link href="%s" rel="self" type="application/rss+xml"/>' % esc(feed_url),
        '  <image>',
        '   <url>%s</url>' % esc(origin + site["ogImage"]),
        '   <title>%s</title>' % esc(S["feedTitle"]),
        '   <link>%s%s/</link>' % (origin, loc(lang, "urlPrefix")),
        '  </image>',
        "\n".join(entrees),
        ' </channel>',
        '</rss>',
        '',
    ])


def build(verbose=True):
    ctx, lettres = contexte(), _lettres()
    config = ctx["config"]
    ecrits = []
    for lang in config["site"]["languages"]:
        chemin = os.path.join(ROOT, loc(lang, "urlPrefix").lstrip("/"), "feed.xml")
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(_canal(lang, ctx, lettres))
        ecrits.append(os.path.relpath(chemin, ROOT))
    if verbose:
        print("Flux : %s (%d lettres)" % (", ".join(ecrits), len(lettres)))
    return ecrits


if __name__ == "__main__":
    build()
