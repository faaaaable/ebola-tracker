# -*- coding: utf-8 -*-
"""Le texte des bulletins, lu une fois et gardé en cache.

Trois scripts de la page « Riposte » — alertes, laboratoire, CTE — relisent
tous les bulletins à chaque exécution, comme extract_contacts_followup.py.
Ouvrir 98 PDF avec pdfplumber coûte une bonne minute par script ; quatre
scripts, c'est cinq minutes par bulletin. Le texte d'un PDF ne change jamais :
on le garde dans `.cache/textes/<fichier>.txt`, dossier déjà ignoré par git
(`.cache/*` dans .gitignore), et seul le bulletin nouveau est réellement lu.

Le cache est invalidé par la taille du PDF, écrite dans le nom du fichier
texte : un PDF remplacé par une autre version est relu.

    from textes_pdf import texte_du_rapport, rapports
    for chemin in rapports():
        texte = texte_du_rapport(chemin)
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT, "reports")
CACHE_DIR = os.path.join(ROOT, ".cache", "textes")


def rapports():
    """Les PDF de l'INSP, dans l'ordre des numéros."""
    return sorted(glob.glob(os.path.join(REPORTS_DIR, "SITREP_MVE_*.pdf")))


def numero(chemin):
    m = re.search(r"_(\d+)\.pdf$", chemin)
    return m.group(1) if m else None


def texte_du_rapport(chemin):
    """Le texte de toutes les pages, séparées par un saut de ligne."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    taille = os.path.getsize(chemin)
    cache = os.path.join(CACHE_DIR, "%s.%d.txt" % (os.path.basename(chemin), taille))
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as fh:
            return fh.read()
    import pdfplumber  # importé ici : inutile quand tout est en cache
    with pdfplumber.open(chemin) as pdf:
        texte = "\n".join((p.extract_text() or "") for p in pdf.pages)
    with open(cache, "w", encoding="utf-8") as fh:
        fh.write(texte)
    return texte


def entier(s):
    """« 14 277 » -> 14277 ; None si rien de lisible."""
    if s is None:
        return None
    chiffres = re.sub(r"[^\d]", "", str(s))
    return int(chiffres) if chiffres else None


def pourcent(s):
    """« 82,3 % » -> 82.3 ; None si rien de lisible."""
    if s is None:
        return None
    m = re.search(r"(\d+(?:[,.]\d+)?)", str(s))
    return float(m.group(1).replace(",", ".")) if m else None
