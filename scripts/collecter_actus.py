"""Collecte les actualites de l'epidemie pour la page /actualites/.

Chaque source est lue par son flux public, filtree sur l'epidemie, et chaque
article nouveau entre dans data/actus.json avec un statut :

- « publie » d'emblee pour les sources institutionnelles dont le flux n'a
  donne aucun faux positif a l'essai du 23 septembre 2026 (MSF, OMS) ;
- « attente » pour ReliefWeb, qui agrege tout ce qui touche la RDC et dont
  la moitie des articles ne parle pas d'Ebola malgre la recherche. Un article
  en attente n'apparait pas sur le site tant qu'il n'a pas ete valide ;
- « attente » aussi pour les medias (RFI, France 24, The Guardian), lus par
  leur flux « Ebola » dans chaque langue ou ils en ont un. Un article de
  media porte « media »: true et ne s'affiche que sur la page de sa langue
  (voir build_pages.py) ;
- « publie » pour les autorites congolaises : les communiques de la
  Primature filtres sur le titre, et l'Agence congolaise de presse (ACP),
  lue sur sa page de recherche faute de flux.

Un article deja connu n'est jamais reecrit : un article ecarte le reste, un
titre corrige a la main n'est pas ecrase a la collecte suivante.

Chaque article recoit sa vignette, telechargee une fois et reduite dans
assets/actus/<id>.jpg : la page ne fait aucune requete vers un tiers. Elle
vient du flux (enclosure, media:thumbnail) ou, a defaut, de l'og:image de
l'article ; « image »: false dit qu'il n'y en avait pas, ou seulement le logo
generique de la source, et la page dessine alors une vignette a ses couleurs.

    python scripts/collecter_actus.py                 # collecter
    python scripts/collecter_actus.py --attente       # lister la file
    python scripts/collecter_actus.py --valider ID…   # publier
    python scripts/collecter_actus.py --ecarter ID…   # ne jamais publier

X/Twitter n'est pas collecte : l'API de lecture est payante et le reste est
interdit par ses conditions. Un tweet se saisit a la main (voir --ajouter).
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER = os.path.join(ROOT, "data", "actus.json")
VIGNETTES = os.path.join(ROOT, "assets", "actus")
LARGEUR_VIGNETTE = 480
UA = ("Mozilla/5.0 (compatible; ebola-tracker.org/actus; "
      "+https://ebola-tracker.org/a-propos/)")

# Rien avant la declaration de l'epidemie : les flux « Ebola » de MSF et de
# l'OMS remontent jusqu'aux epidemies precedentes.
DEBUT = "2026-05-15"

SOURCES = [
    {"id": "msf", "nom": "MSF", "url": "https://www.msf.org/rss/ebola",
     "statut": "publie"},
    # Deux flux generalistes : l'epidemie doit etre nommee dans le titre, ou
    # « Presidential dialogue on high-threat pathogens » passait pour une
    # actualite d'Ebola parce que son resume la cite.
    {"id": "msf-fr", "nom": "MSF", "url": "https://www.msf.fr/rss.xml",
     "statut": "publie", "filtre": "titre"},
    # Sans resume : le flux de l'OMS Afrique recopie le titre, l'adresse de
    # l'auteur et l'heure de mise en ligne avant la premiere phrase.
    {"id": "oms-afro", "nom": "OMS Afrique", "url": "https://www.afro.who.int/rss.xml",
     "statut": "publie", "filtre": "titre", "resume": False},
    {"id": "oms-don", "nom": "OMS", "type": "who-don", "statut": "publie",
     "url": "https://www.who.int/api/news/diseaseoutbreaknews"
            "?$orderby=PublicationDateAndTime%20desc&$top=20"
            "&$select=Title,PublicationDateAndTime,UrlName,Summary"},
    # Le flux RSS ne garde que les vingt derniers articles, soit deux a trois
    # jours : la collecte doit tourner au moins toutes les six heures. L'API,
    # qui filtrerait mieux et remonterait l'historique, demande un « appname »
    # approuve, a demander par le proprietaire.
    # Filtre sur le titre et le debut du texte : ReliefWeb donne le rapport
    # entier, et un point sur la securite alimentaire qui cite Ebola au
    # dixieme paragraphe n'est pas une actualite de l'epidemie.
    {"id": "reliefweb", "nom": "ReliefWeb", "statut": "attente", "filtre": "debut",
     "url": "https://reliefweb.int/updates/rss.xml?search=ebola&advanced-search=%28C75%29"},
    # Les medias : seulement ceux qui tiennent un flux « Ebola » (essai du
    # 24 septembre 2026). Reuters, AP, Al Jazeera et DW n'en ont pas ; les
    # lire par Google News demanderait de resoudre ses liens, a decider.
    # La langue est celle du flux, pas devinee : un titre court comme
    # « Ebola : le pic n'est pas atteint » trompe le detecteur.
    {"id": "rfi-fr", "nom": "RFI", "url": "https://www.rfi.fr/fr/tag/ebola/rss",
     "statut": "attente", "media": True, "langue": "fr"},
    {"id": "rfi-en", "nom": "RFI", "url": "https://www.rfi.fr/en/tag/ebola/rss",
     "statut": "attente", "media": True, "langue": "en"},
    {"id": "france24-fr", "nom": "France 24", "url": "https://www.france24.com/fr/tag/virus-ebola/rss",
     "statut": "attente", "media": True, "langue": "fr"},
    {"id": "france24-en", "nom": "France 24", "url": "https://www.france24.com/en/tag/ebola/rss",
     "statut": "attente", "media": True, "langue": "en"},
    {"id": "guardian", "nom": "The Guardian", "url": "https://www.theguardian.com/world/ebola/rss",
     "statut": "attente", "media": True, "langue": "en"},
    # Ajouts du 25 septembre 2026, apres le releve de 118 flux fait par Hermes
    # et recontrole ici. Radio Okapi et Africanews sont generalistes (4 et 2
    # articles sur Ebola sur 50) et publies SANS VALIDATION, a la demande du
    # proprietaire : le filtre est donc resserre au titre et au debut du
    # resume — « Beni : deux morts [...] au cimetiere » passe, Ebola y est
    # nomme des la deuxieme phrase. Radio Okapi a change d'adresse : son
    # ancien rss.xml est fige au 15 juillet.
    {"id": "okapi", "nom": "Radio Okapi", "url": "https://www.radiookapi.net/feed",
     "statut": "publie", "filtre": "debut", "media": True, "langue": "fr"},
    {"id": "africanews", "nom": "Africanews", "url": "https://www.africanews.com/feed/",
     "statut": "publie", "filtre": "debut", "media": True, "langue": "en"},
    # ALIMA, ONG medicale en premiere ligne en Ituri : son flux melange toute
    # son actualite, l'epidemie doit etre nommee dans le titre.
    {"id": "alima", "nom": "ALIMA", "url": "https://alima.ngo/feed/",
     "statut": "publie", "filtre": "titre", "langue": "fr"},
    # L'ECDC n'est pas lu (decision du proprietaire, 25 septembre 2026) : pas
    # de flux Ebola, et son rapport hebdomadaire sur les menaces couvre toutes
    # les maladies de la semaine, Ebola parmi huit ou dix.
    # Les autorites congolaises (essai du 24 septembre 2026). Le ministere de
    # la Sante n'a ni flux ni actualites sur son site : il communique sur X,
    # a saisir a la main (--ajouter).
    # L'INSP n'est pas lu : son flux ne donne que ses rapports de situation et
    # les comptes rendus du COUSP, ecartes de la page par le proprietaire.
    {"id": "primature", "nom": "Primature", "url": "https://primature.cd/feed/",
     "statut": "publie", "filtre": "titre", "langue": "fr"},
    # L'ACP n'a pas de flux (erreur 500) : sa page de recherche est lue telle
    # quelle et cassera au premier changement de maquette du site. Agence
    # d'Etat bilingue, elle suit la regle des medias : une langue par page.
    {"id": "acp", "nom": "ACP", "type": "acp", "statut": "publie", "filtre": "titre",
     "media": True, "url": "https://acp.cd/?s=ebola"},
]

# « BVD » et « Bundibugyo » : l'OMS Afrique titre parfois sans le mot Ebola.
EPIDEMIE = re.compile(r"\b(ebola|[ée]bola|bundibugyo|bdbv|bvd|mve)\b", re.I)
# Ce qui ne concerne que l'Ouganda ou une autre epidemie passe quand meme :
# l'epidemie est transfrontaliere. On exclut seulement l'espagnol, que
# ReliefWeb double des versions anglaise et francaise.
ESPAGNOL = re.compile(r"\b(brote|llama a|la directora|registrado|del)\b", re.I)
FRANCAIS = re.compile(r"\b(le|la|les|des|du|une|et|est|dans|pour|sur|à)\b", re.I)
# Les emetteurs relayes par ReliefWeb, sous leur sigle. Le sigle francais est
# garde : build_pages.py le traduit pour les autres langues.
SIGLES = {
    "World Health Organization": "OMS",
    "UN Office for the Coordination of Humanitarian Affairs": "OCHA",
    "International Organization for Migration": "OIM",
    "World Food Programme": "PAM",
    "UN Children's Fund": "UNICEF",
    "Africa Centres for Disease Control and Prevention": "Africa CDC",
    "Famine Early Warning System Network": "FEWS NET",
    "International Federation of Red Cross And Red Crescent Societies": "FICR",
    "Médecins Sans Frontières": "MSF",
}
PREFIXE_RW = re.compile(r"^(DR Congo|RD Congo|Democratic Republic of the Congo)\s*:\s*")


def lire(url):
    # Une adresse d'image peut porter un caractere non ASCII (« © » chez
    # ALIMA) : urllib refuse de l'envoyer tel quel.
    url = urllib.parse.quote(url, safe=":/?&=%#+,;@~!$'()*[]")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def texte(fragment):
    """Du HTML d'un flux au texte brut, espaces normalises."""
    fragment = re.sub(r"<[^>]+>", " ", html.unescape(fragment or ""))
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


def resume(desc, limite=280):
    """La premiere phrase ou deux, coupees sur un mot."""
    desc = re.sub(r"^(Country|Source|Pays)\s*:.*?(?=[A-ZÀ-Ý«“\"][a-zà-ÿ])", "", desc)
    if len(desc) <= limite:
        return desc
    coupe = desc[:limite]
    fin = max(coupe.rfind(". "), coupe.rfind("! "), coupe.rfind("? "))
    if fin > limite // 2:
        return coupe[:fin + 1]
    return coupe[:coupe.rfind(" ")].rstrip(",;:") + "…"


def langue(*morceaux):
    t = " ".join(morceaux)
    if ESPAGNOL.search(t):
        return "es"
    return "fr" if len(FRANCAIS.findall(t)) >= 3 else "en"


NOMS_PROPRES = {"ebola": "Ebola", "bundibugyo": "Bundibugyo", "uganda": "Uganda",
                "congo": "Congo", "rdc": "RDC", "drc": "DRC", "bvd": "BVD", "mve": "MVE"}


def casse(titre):
    """« EBOLA BUNDIBUGYO VIRUS DISEASE OUTBREAK Democratic… » : l'OMS Afrique
    ouvre ses rapports en capitales. Les mots en capitales passent en
    minuscules, sauf les noms propres ; un sigle court (OMS, CTE) reste."""
    mots = titre.split(" ")
    if sum(m.isupper() and len(m) > 3 for m in mots) < 3:
        return titre
    sortie = []
    for m in mots:
        if m.isupper() and len(m) > 3:
            m = NOMS_PROPRES.get(m.lower(), m.lower())
        sortie.append(m)
    t = " ".join(sortie)
    return t[:1].upper() + t[1:]


# L'OMS sert un logo par defaut, ReliefWeb une icone du type de catastrophe
# (« FL », inondation, pour un communique de l'OIM sur Ebola).
IMAGE_GENERIQUE = re.compile(r"whofallback|disaster-type", re.I)
MEDIA_NS = "{http://search.yahoo.com/mrss/}"


def image_du_flux(item):
    for el in [item.find("enclosure")] + item.findall(MEDIA_NS + "content") + item.findall(MEDIA_NS + "thumbnail"):
        if el is not None and el.get("url") and (el.tag != "enclosure" or el.get("type", "image").startswith("image")):
            return el.get("url")
    return ""


def og_image(url):
    try:
        page = lire(url)[:400000].decode("utf-8", "ignore")
    except Exception:
        return ""
    m = (re.search(r'<meta[^>]+(?:property|name)=["\']og:image["\'][^>]*content=["\']([^"\']+)', page)
         or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']og:image', page))
    return html.unescape(m.group(1)) if m else ""


def vignette(item, source_image=""):
    """Telecharge et reduit l'image de l'article ; True si elle est ecrite."""
    try:
        from PIL import Image
    except ImportError:  # sans Pillow, on reessaiera a la collecte suivante
        return None
    url = source_image or og_image(item["url"])
    if not url.startswith("http") or IMAGE_GENERIQUE.search(url):
        return False
    try:
        import io
        im = Image.open(io.BytesIO(lire(url))).convert("RGB")
        if im.width < 200:
            return False
        if im.width > LARGEUR_VIGNETTE:
            im = im.resize((LARGEUR_VIGNETTE, round(im.height * LARGEUR_VIGNETTE / im.width)), Image.LANCZOS)
        os.makedirs(VIGNETTES, exist_ok=True)
        im.save(os.path.join(VIGNETTES, item["id"] + ".jpg"), "JPEG", quality=72, optimize=True, progressive=True)
        return True
    except Exception as e:
        print("  ! vignette %s : %s" % (item["id"], e), file=sys.stderr)
        return False


def ident(url):
    return hashlib.sha1(url.encode()).hexdigest()[:8]


def depuis_rss(source):
    racine = ET.fromstring(lire(source["url"]))
    for item in racine.iter("item"):
        brut = item.findtext("description") or ""
        # ReliefWeb ouvre sa description par des etiquettes « Country: … »,
        # « Source: … », « Please refer to the attached file » : l'emetteur
        # en est lu plus bas, le reste n'est pas un resume.
        corps = re.sub(r'<div class="tag[^"]*">.*?</div>', " ", html.unescape(brut), flags=re.S)
        corps = re.sub(r"Please refer to the attached \w+\.?|\*\*", " ", corps, flags=re.I)
        titre = casse(texte(item.findtext("title")))
        emetteur = source["nom"]
        if source["id"] == "reliefweb":
            titre = PREFIXE_RW.sub("", titre)
            m = re.search(r"Source:\s*([^<]+)</div>", html.unescape(brut))
            if m:
                emetteur = SIGLES.get(m.group(1).strip(), m.group(1).strip())
        try:
            date = parsedate_to_datetime(item.findtext("pubDate")).date().isoformat()
        except (TypeError, ValueError):
            continue
        yield {"url": item.findtext("link").strip(), "titre": titre,
               "source": emetteur, "via": source["nom"] if emetteur != source["nom"] else None,
               "date": date, "desc": texte(corps), "image": image_du_flux(item)}


def depuis_who_don(source):
    for x in json.loads(lire(source["url"]))["value"]:
        yield {"url": "https://www.who.int/emergencies/disease-outbreak-news/item/" + x["UrlName"],
               "titre": x["Title"].strip(), "source": source["nom"], "via": None,
               "date": x["PublicationDateAndTime"][:10], "desc": texte(x.get("Summary"))}


def depuis_acp(source):
    """La page de recherche de l'ACP : ses douze derniers articles sur Ebola.
    Elle ne se pagine pas (/page/2/ rend la premiere page) : l'historique est
    perdu, la collecte toutes les trois heures suffit pour la suite. La
    rubrique « Anglais » donne la langue."""
    doc = lire(source["url"]).decode("utf-8", "ignore")
    for bloc in doc.split('<div class="td_module_flex ')[1:]:
        m = re.search(r'<h[23] class="entry-title td-module-title"><a href="([^"]+)"[^>]*>(.*?)</a>', bloc, re.S)
        d = re.search(r'<time[^>]+datetime="(\d{4}-\d\d-\d\d)', bloc)
        if not m or not d:
            continue
        rubrique = re.search(r'class="td-post-category"\s*>([^<]+)<', bloc)
        fond = re.search(r"background-image:\s*url\('([^']+)'\)", bloc)
        extrait = re.search(r'<div class="td-excerpt">(.*?)</div>', bloc, re.S)
        desc = texte(extrait.group(1) if extrait else "")
        # « Beni, 23 septembre 2026 (ACP).- » : la dateline n'est pas un resume.
        desc = re.sub(r"^.{0,80}?\((ACP|CPA)\)\s*\.?\s*-\s*", "", desc).rstrip(".…") + "…"
        yield {"url": m.group(1), "titre": texte(m.group(2)), "source": source["nom"], "via": None,
               "date": d.group(1), "desc": desc,
               "langue": "en" if rubrique and rubrique.group(1).strip() == "Anglais" else "fr",
               "image": fond.group(1) if fond else ""}


def charger():
    if os.path.exists(FICHIER):
        with open(FICHIER, encoding="utf-8") as f:
            return json.load(f)
    return {"_comment": "Genere par scripts/collecter_actus.py. statut : publie "
                        "(visible), attente (a valider), ecarte (jamais publie). "
                        "Un article connu n'est jamais reecrit par la collecte.",
            "items": []}


def ecrire(etat):
    etat["items"].sort(key=lambda x: (x["date"], x["id"]), reverse=True)
    with open(FICHIER, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=1)
        f.write("\n")


def collecter(etat):
    connus = {x["url"] for x in etat["items"]}
    titres = {(x["source"], x["titre"].lower()) for x in etat["items"]}
    aujourd_hui = datetime.now(timezone.utc).date().isoformat()
    ajouts, erreurs = [], 0
    for source in SOURCES:
        lecteur = {"who-don": depuis_who_don, "acp": depuis_acp}.get(source.get("type"), depuis_rss)
        try:
            articles = list(lecteur(source))
        except Exception as e:  # une source en panne n'arrete pas les autres
            print("  ! %s : %s" % (source["id"], e), file=sys.stderr)
            erreurs += 1
            continue
        for a in articles:
            if a["url"] in connus or a["date"] < DEBUT:
                continue
            champ = {"titre": a["titre"],
                     "debut": a["titre"] + " " + a["desc"][:400]}.get(
                         source.get("filtre"), a["titre"] + " " + a["desc"])
            if not EPIDEMIE.search(champ):
                continue
            lang = a.get("langue") or source.get("langue") or langue(a["titre"], a["desc"][:300])
            if lang == "es":
                continue
            # Le meme communique relaye deux fois (msf.org et son flux Ebola) :
            # meme emetteur, meme titre.
            if (a["source"], a["titre"].lower()) in titres:
                continue
            item = {"id": ident(a["url"]), "date": a["date"], "titre": a["titre"],
                    "source": a["source"], "url": a["url"], "langue": lang,
                    "resume": resume(a["desc"]) if source.get("resume", True) else "", "statut": source["statut"],
                    "collecte": aujourd_hui}
            if a["via"]:
                item["via"] = a["via"]
            if source.get("media"):
                item["media"] = True
            if item["statut"] != "ecarte":
                v = vignette(item, a.get("image", ""))
                if v is not None:
                    item["image"] = v
            etat["items"].append(item)
            connus.add(a["url"])
            titres.add((a["source"], a["titre"].lower()))
            ajouts.append(item)
    # Rattrapage : un article sans le champ « image » (collecte sans Pillow,
    # saisie a la main) cherche la sienne sur sa page.
    for x in etat["items"]:
        if "image" not in x and x["statut"] != "ecarte":
            v = vignette(x)
            if v is not None:
                x["image"] = v
    for x in ajouts:
        print("  + [%s] %s %s — %s" % (x["statut"], x["date"], x["source"], x["titre"][:90]))
    print("%d nouvel(s) article(s), dont %d en attente."
          % (len(ajouts), sum(x["statut"] == "attente" for x in ajouts)))
    # Pas d'horodatage de collecte dans le fichier : il changerait a chaque
    # passage, et le workflow commiterait toutes les trois heures pour rien.
    return erreurs == len(SOURCES)


def changer(etat, ids, statut):
    trouves = 0
    for x in etat["items"]:
        if x["id"] in ids:
            x["statut"] = statut
            trouves += 1
    manquants = set(ids) - {x["id"] for x in etat["items"]}
    if manquants:
        sys.exit("Identifiant(s) inconnu(s) : %s" % ", ".join(sorted(manquants)))
    print("%d article(s) passe(s) en « %s »." % (trouves, statut))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--attente", action="store_true", help="lister les articles a valider")
    p.add_argument("--valider", nargs="+", metavar="ID")
    p.add_argument("--ecarter", nargs="+", metavar="ID")
    p.add_argument("--ajouter", nargs=4, metavar=("DATE", "SOURCE", "URL", "TITRE"),
                   help="saisir un article a la main (tweet, communique hors flux)")
    args = p.parse_args()
    etat = charger()

    if args.attente:
        file = [x for x in etat["items"] if x["statut"] == "attente"]
        for x in file:
            print("%s  %s  %-14s %s\n          %s" % (x["id"], x["date"], x["source"][:14],
                                                   x["titre"], x["url"]))
        print("%d article(s) en attente." % len(file))
        return
    if args.valider:
        changer(etat, args.valider, "publie")
    elif args.ecarter:
        changer(etat, args.ecarter, "ecarte")
    elif args.ajouter:
        date, source, url, titre = args.ajouter
        if any(x["url"] == url for x in etat["items"]):
            sys.exit("Deja present : %s" % url)
        etat["items"].append({"id": ident(url), "date": date, "titre": titre,
                              "source": source, "url": url, "langue": langue(titre),
                              "resume": "", "statut": "publie", "saisie": "main"})
        print("Ajoute et publie.")
    elif collecter(etat):
        sys.exit("Aucune source n'a repondu : rien n'est ecrit.")
    ecrire(etat)


if __name__ == "__main__":
    main()
