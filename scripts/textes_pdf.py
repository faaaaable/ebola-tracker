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


def texte_par_couches(chemin):
    """Le texte du PDF, une couche de police après l'autre.

    Le SitRep 105 imprime le tableau des alertes PAR-DESSUS une copie du
    tableau des zones : `extract_text` entremêle les deux caractère par
    caractère (« Itu0r i 89,9 % », « Kyondo 76169 vus su1r2 28 3727 »). Mais
    chaque couche a sa police et son corps : en regroupant les caractères par
    (police, corps) puis par ligne, chaque couche redevient lisible. La phrase
    des contacts sort intacte de la couche ArialMT 10,6, les lignes d'alertes
    de la couche ArialMT 10,1.

    Les couches sont concaténées page par page, chacune précédée d'un repère ;
    le texte n'est plus dans l'ordre de lecture, il ne sert qu'aux motifs qui
    n'en dépendent pas. Mis en cache comme le texte ordinaire."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    taille = os.path.getsize(chemin)
    cache = os.path.join(CACHE_DIR, "%s.%d.couches.txt" % (os.path.basename(chemin), taille))
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as fh:
            return fh.read()
    import pdfplumber
    blocs = []
    with pdfplumber.open(chemin) as pdf:
        for num, page in enumerate(pdf.pages, 1):
            couches = {}
            for c in page.chars:
                couches.setdefault((c["fontname"], round(c["size"], 1)), []).append(c)
            for (police, corps), chars in sorted(couches.items(), key=lambda kv: -len(kv[1])):
                if len(chars) < 30:
                    continue
                lignes = {}
                for c in chars:
                    lignes.setdefault(round(c["top"] / 3), []).append(c)
                texte = []
                for cle in sorted(lignes):
                    cs = sorted(lignes[cle], key=lambda c: c["x0"])
                    ligne, prec = "", None
                    for c in cs:
                        if prec is not None and c["x0"] - prec["x1"] > 1.5:
                            ligne += " "
                        ligne += c["text"]
                        prec = c
                    texte.append(ligne.strip())
                blocs.append("=== page %d · %s %s ===\n%s" % (num, police, corps, "\n".join(texte)))
    resultat = "\n".join(blocs)
    with open(cache, "w", encoding="utf-8") as fh:
        fh.write(resultat)
    return resultat


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
