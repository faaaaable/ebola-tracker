#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Annonce une nouvelle lettre sur les canaux Telegram du site.

Un canal par langue, abonnement libre : le visiteur qui veut etre prevenu
rejoint le canal, le depot ne conserve aucune adresse ni aucune donnee le
concernant — c'est Telegram qui tient la liste, pas nous.

Ce que dit le message vient de scripts/build_feeds.annonce(), la meme
source que le flux RSS : le titre, les chiffres de tete et le resume des
Defis redige a l'integration de la lettre.

Configuration, en secrets du depot (Settings > Secrets > Actions) :
  TELEGRAM_BOT_TOKEN   le jeton donne par @BotFather
  TELEGRAM_CHAT_ID_FR  « @ebolatracker » ou l'identifiant numerique
  TELEGRAM_CHAT_ID_EN  facultatif ; sans lui, l'anglais n'est pas poste
  TELEGRAM_CHAT_ID_SW  facultatif
Une langue sans canal est simplement sautee : on peut n'ouvrir que le
francais aujourd'hui et ajouter les autres plus tard sans toucher au code.

Les numeros deja annonces sont notes dans data/notifie.json et commites
par le workflow : sans cette trace, une reprise du workflow ou un second
passage renverrait la meme lettre aux abonnes.

  python3 scripts/notifier_telegram.py             # la derniere lettre
  python3 scripts/notifier_telegram.py --num 128   # une lettre precise
  python3 scripts/notifier_telegram.py --essai     # montre, n'envoie rien
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_feeds  # noqa: E402
from build_pages import ROOT  # noqa: E402

ETAT = os.path.join(ROOT, "data", "notifie.json")
API = "https://api.telegram.org/bot%s/sendMessage"
# Telegram coupe a 4096 caracteres ; on garde de la marge pour le lien.
LIMITE = 3800


def echapper(texte):
    """parse_mode=HTML : seuls &, < et > sont a proteger."""
    return (str(texte).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def message(a):
    """Titre en gras, chiffres, resume, puis l'adresse de la lettre — que
    Telegram deplie en apercu au bas du message."""
    corps = ["<b>%s</b>" % echapper(a["titre"]), echapper(a["chiffres"])]
    if a["resume"]:
        corps.append(echapper(a["resume"]))
    texte = "\n\n".join(corps)
    if len(texte) > LIMITE:
        texte = texte[:LIMITE].rsplit(" ", 1)[0] + " […]"
    return "%s\n\n%s" % (texte, a["url"])


def envoyer(jeton, canal, texte):
    donnees = urllib.parse.urlencode({
        "chat_id": canal, "text": texte, "parse_mode": "HTML",
        # L'apercu du lien porte le titre et l'image de la lettre : c'est
        # lui qui donne envie d'ouvrir, on ne le desactive pas.
        "disable_web_page_preview": "false",
    }).encode("utf-8")
    requete = urllib.request.Request(API % jeton, data=donnees)
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return json.load(reponse)


def _etat():
    if os.path.exists(ETAT):
        with open(ETAT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _ecrire_etat(etat):
    with open(ETAT, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--num", help="numero de lettre ; par defaut la plus recente")
    ap.add_argument("--essai", action="store_true",
                    help="affiche les messages sans rien envoyer")
    ap.add_argument("--sans-resume", action="store_true", dest="sans_resume",
                    help="annonce meme si le resume des Defis manque encore")
    args = ap.parse_args()

    jeton = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not jeton and not args.essai:
        print("TELEGRAM_BOT_TOKEN absent : rien a faire.")
        return 0

    lettres = dict(build_feeds._lettres())
    num = args.num or max(lettres)
    if num not in lettres:
        sys.exit("Lettre %s introuvable dans data/lettres/." % num)

    ctx = build_feeds.contexte()

    # Le resume des Defis est redige a l'integration de la lettre, parfois
    # dans un second commit. Sans lui le message se reduirait a trois
    # chiffres : on attend plutot le commit qui l'apporte, qui relancera ce
    # workflow. --sans-resume passe outre.
    if not args.sans_resume and not build_feeds._resume(ctx["notes"], num, "fr"):
        print("Lettre %s : resume des Defis absent, annonce reportee." % num)
        return 0

    etat = _etat()
    envoyees = etat.setdefault("telegram", {})
    change = False

    for lang in ctx["config"]["site"]["languages"]:
        canal = os.environ.get("TELEGRAM_CHAT_ID_%s" % lang.upper(), "").strip()
        if not canal:
            continue
        deja = envoyees.setdefault(lang, [])
        if num in deja:
            print("%s : lettre %s deja annoncee." % (lang, num))
            continue
        texte = message(build_feeds.annonce(num, lettres[num], lang, ctx))
        if args.essai:
            print("--- %s -> %s ---\n%s\n" % (lang, canal, texte))
            continue
        try:
            envoyer(jeton, canal, texte)
        except urllib.error.HTTPError as err:
            # Un canal mal configure ne doit pas empecher les autres
            # langues de partir.
            print("ERREUR %s : %s %s" % (lang, err.code, err.read().decode("utf-8", "replace")),
                  file=sys.stderr)
            continue
        print("%s : lettre %s annoncee sur %s." % (lang, num, canal))
        deja.append(num)
        deja.sort()
        change = True

    if change:
        _ecrire_etat(etat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
