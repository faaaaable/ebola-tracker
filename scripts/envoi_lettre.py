# -*- coding: utf-8 -*-
"""Mail aux abonnes de la Lettre, envoye par Brevo quand une nouvelle lettre
(un nouveau SitRep) est en ligne (20 octobre 2026, demande du proprietaire).

Depuis le 23 octobre 2026, c'est le SEUL mail d'un nouveau bulletin : il
remplace aussi l'alerte SitRep (scripts/envoi_alerte.py, retire du workflow)
et part aux deux listes de chaque langue, celle de la Lettre
(site.brevoEnvoiLettre) et celle de la page Etre prevenu
(site.brevoEnvoiAlerte) ; Brevo n'ecrit qu'une fois a une adresse inscrite
aux deux. Dessin retenu parmi les maquettes tmp/proto-mail-fusion-1022
(option « 1a ») : le nom du site et son favicon au-dessus, l'en-tete de la
Lettre, le titre et le chapeau, les cinq chiffres en bandeau, la courbe des
30 derniers jours, trois liens (carte, ensemble de la RDC, hors RDC) et le
bouton vers la lettre. Tout est lu dans la lettre generee
(lettre/NNN/index.html, en/letter/NNN/index.html). La courbe est dessinee
en tableau HTML, pas en image : les messageries n'affichent pas le SVG, et
le workflow n'a pas de navigateur pour en tirer un PNG. data/envois-lettre.json garde
le dernier numero envoye : une lettre ne part jamais deux fois, et une lettre
plus ancienne jamais.

    python scripts/envoi_lettre.py --apercu          ecrit tmp/mail-lettre-<lang>.html
    python scripts/envoi_lettre.py --test ADRESSE    campagne + envoi test a cette adresse
    python scripts/envoi_lettre.py --envoi           envoi reel, si la lettre est nouvelle

La cle API est lue dans BREVO_API_KEY (secret GitHub), sinon dans
~/.config/ebola-tracker/brevo.key. Sans cle ou sans listes : rien n'est
envoye et le script sort sans erreur.
"""
import base64, html, json, os, re, sys, time, urllib.request, urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ETAT = os.path.join(ROOT, "data", "envois-lettre.json")
CHEMIN = {"fr": "lettre/%s/index.html", "en": "en/letter/%s/index.html"}
ORIGINE = "https://ebola-tracker.org/"
SERIF, SANS = "Georgia,'Times New Roman',serif", "Arial,Helvetica,sans-serif"
INK, DIM, FAINT, LINE = "#1F1A13", "#5A544C", "#777068", "#DEDAD5"
TEINTE = {"is-cas": "#005E82", "is-deces": "#993A2E", "is-gueris": "#327957", "is-cte": "#A06F30"}
T = {"fr": dict(marque="La lettre", objet="La Lettre n° %s · %s", bouton="Lire la Lettre en entier",
                liens=[("La carte", ""), ("L’ensemble de la RDC", "donnees/"), ("Hors RDC", "autres-pays/")],
                source="Résumé du bulletin officiel de l’Institut national de santé publique (INSP) de la RDC.",
                desinscr="Se désinscrire"),
     "en": dict(marque="The letter", objet="The Letter no. %s · %s", bouton="Read the full Letter",
                liens=[("The map", "en/"), ("All of the DRC", "en/data/"), ("Outside the DRC", "en/other-countries/")],
                source="Summary of the official bulletin of the DRC National Institute of Public Health (INSP).",
                desinscr="Unsubscribe")}
# Le favicon du site en PNG (assets/img/mail-favicon.png, 96 px) : les
# messageries n'affichent pas favicon.svg.
FAVICON = ORIGINE + "assets/img/mail-favicon.png"


def txt(x):
    return html.unescape(re.sub(r"<[^>]+>", "", x)).strip()


ABREV = {"janv", "févr", "avr", "juil", "sept", "oct", "nov", "déc", "n°", "no"}


def premiere_phrase(s):
    """Jusqu'au premier point suivi d'une majuscule ou d'un chiffre, sauf
    apres une abreviation de mois (« 17 oct. 2026 »)."""
    for m in re.finditer(r"[.!?](?=\s+[A-ZÀÂÉÈÊÎÔÛÇ0-9])", s):
        mot = re.search(r"(\S+)$", s[:m.start()])
        if not mot or mot.group(1).lower() not in ABREV:
            return s[:m.end()]
    return s


def lire_json(chemin, defaut=None):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return defaut


def numero_courant():
    return lire_json(os.path.join(ROOT, "data", "latest.json"))["meta"]["sitrepNumber"]


def lettre(num, lang):
    """Ce que le mail reprend de la lettre generee."""
    chemin = CHEMIN[lang] % num
    with open(os.path.join(ROOT, chemin), encoding="utf-8") as f:
        s = f.read()
    edition = re.search(r'<p class="ag-edition">(.*?)</p>', s, re.S).group(1)
    mini = re.search(r'<div class="lq-mini">(.*?)</div>', s, re.S).group(1)
    return {"url": ORIGINE + chemin.replace("index.html", ""),
            "edition": [txt(x) for x in re.findall(r"<span>(.*?)</span>", edition)],
            "sous": txt(re.search(r'<p class="ag-sous">(.*?)</p>', s, re.S).group(1)),
            "eyebrow": txt(re.search(r'class="lq-eyebrow">(.*?)</div>', s, re.S).group(1)),
            # (hauteur sur 56, dernier jour ?) de chaque barre de la courbe
            "barres": [(float(h), "is-der" in r) for r, h in re.findall(r'(<rect [^>]*height="([\d.]+)"[^>]*>)', mini)],
            "legende": txt(re.search(r"</svg>\s*<span>(.*?)</span>", mini, re.S).group(1)),
            "titre": txt(re.search(r'class="lq-titre">(.*?)</h1>', s, re.S).group(1)),
            "chapo": txt(re.search(r'class="lq-chapo">(.*?)</p>', s, re.S).group(1)),
            "chiffres": [(txt(b), txt(sp), cls) for cls, b, sp in re.findall(
                r'<div class="lq-chiffre ?([a-z-]*)"><b>(.*?)</b><span>(.*?)</span></div>', s, re.S)]}


def mail(num, lang):
    """(objet, apercu, html) du mail d'une lettre."""
    d, t = lettre(num, lang), T[lang]
    esc = html.escape

    def case(c):
        v, lib, cls = c
        nom, _, plus = lib.partition(" · ")
        teinte = TEINTE.get(cls, INK)
        return ('<div style="display:inline-block;vertical-align:top;width:104px;padding:10px 0;text-align:center;">'
                f'<div style="font:700 23px/1.1 {SANS};letter-spacing:-.4px;color:{teinte};">{esc(v)}</div>'
                f'<div style="font:12px/1.3 {SANS};color:{DIM};margin-top:4px;">{esc(nom)}</div>'
                f'<div style="font:700 12px/1.3 {SANS};color:{teinte};margin-top:2px;">{esc(plus) or "&nbsp;"}</div></div>')
    # Les cinq chiffres en bandeau : blocs en ligne de largeur fixe, qui passent
    # a la ligne d'eux-memes sur telephone.
    bandeau = "".join(case(c) for c in d["chiffres"])
    # La courbe : une cellule par jour, barre collee en bas, hauteur a
    # l'echelle de la lettre (56 unites -> 110 px).
    barres = "".join(f'<td valign="bottom" style="padding:0 1px;"><div style="height:{max(1, round(h / 56 * 110))}px;'
                     f'background:{"#005E82" if der else "#B3D0DD"};font-size:0;line-height:0;">&nbsp;</div></td>'
                     for h, der in d["barres"])
    liens = "".join(f'<a href="{ORIGINE}{u}" style="display:inline-block;margin:0 5px 8px;padding:10px 16px;border:1.5px solid #005073;'
                    f'border-radius:10px;color:#005073;font:700 14px {SANS};text-decoration:none;">{esc(l)} →</a>' for l, u in t["liens"])
    objet = t["objet"] % (num, d["titre"])
    apercu = premiere_phrase(d["chapo"])
    accueil = ORIGINE + ("en/" if lang == "en" else "")
    corps = f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(objet)}</title></head>
<body style="margin:0;padding:0;background:#F7F3EE;">
<div style="display:none;max-height:0;overflow:hidden;">{esc(apercu)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F7F3EE;"><tr><td align="center" style="padding:24px 10px;">
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 14px;"><tr>
 <td style="padding-right:9px;"><a href="{accueil}"><img src="{FAVICON}" width="24" height="24" alt="" style="display:block;border-radius:5px;"></a></td>
 <td><a href="{accueil}" style="font:700 17px/1.2 {SANS};letter-spacing:-.2px;color:{INK};text-decoration:none;">ebola-tracker<span style="color:#1B6C8C;">.org</span></a></td></tr></table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#FFFDFB;border:1px solid {LINE};border-radius:14px;">
 <tr><td style="height:10px;background:#005073;border-radius:14px 14px 0 0;font-size:0;line-height:0;">&nbsp;</td></tr>
 <tr><td align="center" style="padding:28px 24px 0;">
  <div style="font:700 40px/1 {SERIF};letter-spacing:5px;text-transform:uppercase;color:{INK};">{t["marque"]}</div>
  <div style="margin:16px auto 0;max-width:460px;border-top:1px solid #B9B4AE;border-bottom:1px solid #B9B4AE;padding:7px 0;font:700 11px/1.6 {SANS};letter-spacing:2px;text-transform:uppercase;color:{INK};">
   {' <span style="color:#005073;font-size:10px;padding:0 6px;">&#9670;</span> '.join(f'<span style="white-space:nowrap;">{esc(e)}</span>' for e in d["edition"])}</div>
  <div style="font:italic 15px/1.4 {SERIF};color:{DIM};margin-top:12px;">{esc(d["sous"])}</div>
  <div style="border-bottom:3px double {LINE};margin-top:22px;"></div></td></tr>
 <tr><td style="padding:22px 28px 0;"><div style="font:700 11px/1.4 {SANS};letter-spacing:1.5px;text-transform:uppercase;color:#005073;">{esc(d["eyebrow"])}</div>
  <div style="font:600 32px/1.1 {SERIF};letter-spacing:-.5px;color:{INK};margin-top:4px;">{esc(d["titre"])}</div></td></tr>
 <tr><td style="padding:10px 28px 0;font:16px/1.6 {SANS};color:#3A342C;">{esc(d["chapo"])}</td></tr>
 <tr><td style="padding:18px 28px 0;"><div style="border-top:2px solid {INK};border-bottom:1px solid {LINE};text-align:center;font-size:0;">{bandeau}</div></td></tr>
 <tr><td style="padding:18px 28px 0;"><a href="{d["url"]}#bilan" style="text-decoration:none;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="height:110px;border:1px solid {LINE};border-radius:8px;padding:8px 6px 0;"><tr>{barres}</tr></table></a>
  <div style="font:13px/1.4 {SANS};color:{FAINT};margin-top:6px;">{esc(d["legende"])}</div></td></tr>
 <tr><td align="center" style="padding:20px 28px 0;">{liens}</td></tr>
 <tr><td align="center" style="padding:18px 28px 30px;"><a href="{d["url"]}" style="display:inline-block;background:#005073;color:#ffffff;font:700 15px {SANS};text-decoration:none;padding:14px 26px;border-radius:10px;">{t["bouton"]} →</a></td></tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;"><tr><td style="padding:16px 26px;font:12px/1.6 {SANS};color:{FAINT};text-align:center;">
 {t["source"]}<br>
 Ebola Tracker · <a href="mailto:contact@ebola-tracker.org" style="color:#1B6C8C;">contact@ebola-tracker.org</a> · <a href="{accueil}" style="color:#1B6C8C;">ebola-tracker.org</a> · <a href="{{{{ unsubscribe }}}}" style="color:#1B6C8C;">{t["desinscr"]}</a></td></tr></table>
</td></tr></table></body></html>"""
    return objet, apercu, corps


def cle_api():
    cle = os.environ.get("BREVO_API_KEY", "").strip()
    if not cle:
        chemin = os.path.expanduser("~/.config/ebola-tracker/brevo.key")
        if os.path.exists(chemin):
            with open(chemin) as f:
                cle = f.read().strip()
    # Brevo donne parfois la cle « enveloppee » : du base64 d'un JSON
    # {"api_key": "xkeysib-..."}. On la deballe.
    if cle.startswith("eyJ"):
        try:
            cle = json.loads(base64.b64decode(cle + "=" * (-len(cle) % 4)))["api_key"]
        except (ValueError, KeyError):
            pass
    return cle


def brevo(cle, methode, chemin, corps=None):
    req = urllib.request.Request("https://api.brevo.com/v3" + chemin, method=methode,
                                 data=json.dumps(corps).encode() if corps is not None else None,
                                 headers={"api-key": cle, "Content-Type": "application/json", "Accept": "application/json",
                                          # Sans User-Agent, Cloudflare renvoie 403 (erreur 1010) sur une partie de l'API.
                                          "User-Agent": "ebola-tracker-envoi-lettre/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            brut = r.read()
            return json.loads(brut) if brut else {}
    except urllib.error.HTTPError as e:
        sys.exit("Brevo %s %s : %s %s" % (methode, chemin, e.code, e.read().decode(errors="replace")))


def creer_campagne(cle, donnees):
    """Cree la campagne et rend son identifiant. Si Brevo refuse le formulaire
    de desinscription, la campagne est recreee sans lui (page Brevo par
    defaut) : un identifiant faux ne doit jamais bloquer l'envoi. Le
    22 octobre 2026, les deux premiers identifiants essayes etaient refuses
    (« Unsubscription page id does not exist »)."""
    try:
        return brevo(cle, "POST", "/emailCampaigns", donnees)["id"]
    except SystemExit as e:
        if "unsubscriptionPageId" not in donnees or "nsubscription page" not in str(e):
            raise
        print("! formulaire de desinscription %s refuse par Brevo, page par defaut : %s"
              % (donnees.pop("unsubscriptionPageId"), e))
        return brevo(cle, "POST", "/emailCampaigns", donnees)["id"]


def en_ligne(url, num, attente=1800):
    """Attend que la lettre soit servie par GitHub Pages (le deploiement peut
    prendre plusieurs minutes) : le mail ne doit pas pointer vers une 404."""
    fin = time.time() + attente
    while time.time() < fin:
        try:
            with urllib.request.urlopen(url + "?v=%d" % time.time(), timeout=30) as r:
                if r.status == 200 and str(num) in r.read().decode("utf-8", "replace"):
                    return True
        except urllib.error.URLError:
            pass
        time.sleep(30)
    return False


def campagne(cle, conf, num, lang, liste=None):
    """Cree la campagne Brevo d'une lettre pour une liste d'identifiants de
    listes ; sans liste (envoi test), elle n'a pas de destinataires : Brevo
    refuse une liste vide."""
    objet, apercu, corps = mail(num, lang)
    donnees = {"name": "Lettre %s (%s)%s" % (num, lang, "" if liste else " - test"), "subject": objet,
               "previewText": apercu, "sender": conf["expediteur"], "htmlContent": corps}
    # Le lien {{ unsubscribe }} mene au formulaire de la langue, pas a la
    # page Brevo par defaut (22 octobre 2026).
    page = (conf.get("desinscription") or {}).get(lang)
    if page:
        donnees["unsubscriptionPageId"] = page
    if liste:
        donnees["recipients"] = {"listIds": liste}
    return creer_campagne(cle, donnees)


def abonnes(cle, liste):
    return brevo(cle, "GET", "/contacts/lists/%d" % liste).get("uniqueSubscribers", 0)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--apercu"
    num = numero_courant()
    if mode == "--apercu":
        for lang in T:
            objet, apercu, corps = mail(num, lang)
            sortie = os.path.join(ROOT, "tmp", "mail-lettre-%s.html" % lang)
            os.makedirs(os.path.dirname(sortie), exist_ok=True)
            with open(sortie, "w", encoding="utf-8") as f:
                f.write(corps)
            print(lang, "|", objet, "|", apercu, "->", sortie)
        return
    conf = json.load(open(os.path.join(ROOT, "site", "pages.json"), encoding="utf-8"))["site"].get("brevoEnvoiLettre") or {}
    # Lettre et alertes : les deux listes de chaque langue (23 octobre 2026).
    alerte = json.load(open(os.path.join(ROOT, "site", "pages.json"), encoding="utf-8"))["site"].get("brevoEnvoiAlerte") or {}
    listes = {}
    for source in (conf, alerte):
        for k, v in (source.get("listes") or {}).items():
            if v and v not in listes.setdefault(k, []):
                listes[k].append(v)
    cle = cle_api()
    if not cle or not listes or not conf.get("expediteur"):
        print("Envoi de la Lettre non configure (cle API, listes ou expediteur manquants) : rien n'est envoye.")
        return
    if mode == "--test":
        adresse = sys.argv[2]
        for lang, liste in listes.items():
            cid = campagne(cle, conf, num, lang)
            brevo(cle, "POST", "/emailCampaigns/%d/sendTest" % cid, {"emailTo": [adresse]})
            print("test", lang, "campagne", cid, "->", adresse)
        return
    if mode == "--envoi":
        etat = lire_json(ETAT, {}) or {}
        if int(num) <= int(etat.get("dernier", 0)):
            print("Lettre %s deja envoyee (dernier envoi : %s)." % (num, etat.get("dernier")))
            return
        url = ORIGINE + CHEMIN["fr"].replace("index.html", "") % num
        if not en_ligne(url, num):
            sys.exit("La lettre %s n'est pas en ligne apres 30 minutes : rien n'est envoye." % num)
        envois = {}
        for lang, liste in listes.items():
            # Une liste vide est laissee de cote : une campagne sans aucun
            # destinataire est refusee par Brevo.
            pleines = [x for x in liste if abonnes(cle, x)]
            if not pleines:
                print("listes %s (%s) sans abonne : rien a envoyer" % (liste, lang))
                continue
            liste = pleines
            cid = campagne(cle, conf, num, lang, liste)
            brevo(cle, "POST", "/emailCampaigns/%d/sendNow" % cid)
            envois[lang] = cid
            print("envoye", lang, "campagne", cid)
        etat.update({"dernier": num, "campagnes": dict(etat.get("campagnes", {}), **{num: envois})})
        with open(ETAT, "w", encoding="utf-8") as f:
            f.write(json.dumps(etat, ensure_ascii=False, indent=1) + "\n")
        return
    sys.exit("Mode inconnu : %s" % mode)


if __name__ == "__main__":
    main()
