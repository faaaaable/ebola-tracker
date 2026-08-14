#!/usr/bin/env python3
"""
Génère la version anglaise du site (en/index.html) à partir de la source
française (index.html), pour avoir deux URLs distinctes et indexables
séparément par les moteurs de recherche :
  - https://ebola-tracker.org/     (français, source éditée à la main)
  - https://ebola-tracker.org/en/  (anglais, généré automatiquement)

index.html reste le SEUL fichier à éditer manuellement. Ce script ne fait
que des remplacements ciblés (langue par défaut, balises <title>/meta,
canonical, hreflang) — le contenu (KPI, carte, courbe, textes FR/EN) est
déjà entièrement piloté par l'objet I18N existant dans le JS du site, donc
il n'y a rien d'autre à dupliquer.

Usage : python3 scripts/build_i18n.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "index.html"
OUTPUT_PATH = ROOT / "en" / "index.html"

FR_URL = "https://ebola-tracker.org/"
EN_URL = "https://ebola-tracker.org/en/"

# Remplacements simples appliqués tels quels (chaîne -> chaîne).
SIMPLE_REPLACEMENTS = [
    ('<html lang="fr">', '<html lang="en">'),
    ("let currentLang = 'fr';", "let currentLang = 'en';"),
    (f'<link rel="canonical" href="{FR_URL}">', f'<link rel="canonical" href="{EN_URL}">'),
    (f'<meta property="og:url" content="{FR_URL}">', f'<meta property="og:url" content="{EN_URL}">'),
    ('<meta property="og:locale" content="fr_FR">', '<meta property="og:locale" content="en_US">'),
    ('<meta property="og:locale:alternate" content="en_US">', '<meta property="og:locale:alternate" content="fr_FR">'),
    (
        '<title>Ebola RDC 2026 — Suivi de l\'épidémie</title>',
        '<title>DRC Ebola Tracker 2026 — Live outbreak monitoring</title>',
    ),
    (
        'content="Suivi en temps réel de la 17e épidémie d\'Ebola en RDC (2026) : cas confirmés, '
        'décès, guéris, carte interactive des zones de santé touchées et courbe épidémique, mis à '
        'jour automatiquement chaque jour depuis les sources officielles."',
        'content="Real-time tracking of the 17th Ebola outbreak in the DRC (2026): confirmed cases, '
        'deaths, recoveries, an interactive map of affected health zones, and an epidemic curve, '
        'automatically updated daily from official sources."',
    ),
    (
        'content="Ebola RDC 2026 — Suivi de l\'épidémie"',
        'content="DRC Ebola Tracker 2026 — Live outbreak monitoring"',
    ),
    (
        'content="Cas confirmés, décès, guéris et carte interactive de l\'épidémie d\'Ebola en RDC, '
        'mis à jour automatiquement chaque jour."',
        'content="Confirmed cases, deaths, recoveries, and an interactive map of the Ebola outbreak '
        'in the DRC, automatically updated daily."',
    ),
    (
        'content="Suivi Ebola RDC 2026 — cas confirmés, décès, guéris et carte de l\'épicentre en Ituri"',
        'content="DRC Ebola tracker 2026 — confirmed cases, deaths, recoveries and map of the Ituri epicentre"',
    ),
]

# Balises hreflang : sur la page FR elles pointent (fr=self, en=/en/) ; sur
# la page EN générée, il faut les inverser (en=self, fr=/).
HREFLANG_BLOCK_FR = (
    '<link rel="alternate" hreflang="fr" href="https://ebola-tracker.org/">\n'
    '<link rel="alternate" hreflang="en" href="https://ebola-tracker.org/en/">\n'
    '<link rel="alternate" hreflang="x-default" href="https://ebola-tracker.org/">'
)
HREFLANG_BLOCK_EN = (
    '<link rel="alternate" hreflang="fr" href="https://ebola-tracker.org/">\n'
    '<link rel="alternate" hreflang="en" href="https://ebola-tracker.org/en/">\n'
    '<link rel="alternate" hreflang="x-default" href="https://ebola-tracker.org/">'
)

# JSON-LD : les champs "url" pointant vers la racine doivent pointer vers /en/
# pour les deux blocs Dataset et WebSite (mais pas contentUrl, qui reste le
# même fichier de données JSON pour les deux langues).
JSONLD_URL_REPLACEMENTS = [
    (f'"url": "{FR_URL}",', f'"url": "{EN_URL}",'),
    (f'"url": "{FR_URL}"\n}}', f'"url": "{EN_URL}"\n}}'),
]


def build():
    if not SOURCE_PATH.exists():
        print(f"ERREUR : {SOURCE_PATH} introuvable.", file=sys.stderr)
        sys.exit(1)

    html = SOURCE_PATH.read_text(encoding="utf-8")

    for old, new in SIMPLE_REPLACEMENTS:
        if old not in html:
            print(f"AVERTISSEMENT : motif non trouvé (ignoré) : {old[:60]}...", file=sys.stderr)
            continue
        html = html.replace(old, new)

    if HREFLANG_BLOCK_FR not in html:
        print("AVERTISSEMENT : bloc hreflang non trouvé, non modifié.", file=sys.stderr)
    else:
        html = html.replace(HREFLANG_BLOCK_FR, HREFLANG_BLOCK_EN)

    for old, new in JSONLD_URL_REPLACEMENTS:
        html = html.replace(old, new)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Généré : {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
