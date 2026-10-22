# -*- coding: utf-8 -*-
"""Mail aux abonnes de la Lettre, envoye par Brevo quand une nouvelle lettre
(un nouveau SitRep) est en ligne (20 octobre 2026, demande du proprietaire).

Le mail ne porte que l'en-tete de la lettre, ses chiffres et un bouton vers
elle ; tout est lu dans la lettre generee (lettre/NNN/index.html,
en/letter/NNN/index.html). Un envoi par langue, chacun a sa liste Brevo
(site.brevoEnvoiLettre dans site/pages.json). data/envois-lettre.json garde
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
T = {"fr": dict(marque="LA LETTRE", objet="La Lettre n° %s : %s", bouton="Lire la Lettre en entier",
                pied="Vous recevez ce mail car vous êtes abonné à la Lettre d’ebola-tracker.org.", desinscr="Se désinscrire"),
     "en": dict(marque="THE LETTER", objet="The Letter no. %s: %s", bouton="Read the full Letter",
                pied="You are receiving this email because you subscribed to the ebola-tracker.org Letter.", desinscr="Unsubscribe")}


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
    return {"url": ORIGINE + chemin.replace("index.html", ""),
            "edition": " · ".join(txt(x) for x in re.findall(r"<span>(.*?)</span>", edition)),
            "titre": txt(re.search(r'class="lq-titre">(.*?)</h1>', s, re.S).group(1)),
            "chapo": txt(re.search(r'class="lq-chapo">(.*?)</p>', s, re.S).group(1)),
            "chiffres": [(txt(b), txt(sp), cls) for cls, b, sp in re.findall(
                r'<div class="lq-chiffre ?([a-z-]*)"><b>(.*?)</b><span>(.*?)</span></div>', s, re.S)]}


def mail(num, lang):
    """(objet, apercu, html) du mail d'une lettre."""
    d, t = lettre(num, lang), T[lang]

    def case(c):
        v, lib, cls = c
        return ('<td width="50%%" valign="top" style="padding:12px 0;border-top:1px solid %s;">'
                '<div style="font:700 28px/1.1 %s;letter-spacing:-.5px;color:%s;">%s</div>'
                '<div style="font:13px/1.4 %s;color:%s;margin-top:3px;">%s</div></td>'
                % (LINE, SANS, TEINTE.get(cls, INK), html.escape(v), SANS, DIM, html.escape(lib)))
    ch = d["chiffres"]
    grille = "".join('<tr>%s</tr>' % ('<td width="16"></td>'.join(case(c) for c in ch[i:i + 2])
                                      + ("" if len(ch[i:i + 2]) == 2 else '<td width="16"></td><td></td>'))
                     for i in range(0, len(ch), 2))
    objet = t["objet"] % (num, d["titre"])
    apercu = premiere_phrase(d["chapo"])
    corps = f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(objet)}</title></head>
<body style="margin:0;padding:0;background:#F7F3EE;">
<div style="display:none;max-height:0;overflow:hidden;">{html.escape(apercu)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F7F3EE;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#FFFDFB;border:1px solid {LINE};border-radius:14px;">
 <tr><td style="height:6px;background:#005073;border-radius:14px 14px 0 0;font-size:0;line-height:0;">&nbsp;</td></tr>
 <tr><td align="center" style="padding:26px 28px 6px;">
  <div style="font:400 34px/1 {SERIF};letter-spacing:8px;color:{INK};">{t["marque"]}</div>
  <div style="font:700 11px/1.4 {SANS};letter-spacing:2px;text-transform:uppercase;color:{INK};margin-top:12px;">{html.escape(d["edition"])}</div></td></tr>
 <tr><td style="padding:14px 28px 4px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{grille}</table></td></tr>
 <tr><td align="center" style="padding:18px 28px 28px;"><a href="{d["url"]}" style="display:inline-block;background:#005073;color:#ffffff;font:700 15px {SANS};text-decoration:none;padding:14px 26px;border-radius:10px;">{t["bouton"]} →</a></td></tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;"><tr><td style="padding:16px 26px;font:12px/1.6 {SANS};color:{FAINT};text-align:center;">
 {t["pied"]} <a href="{{{{ unsubscribe }}}}" style="color:#1B6C8C;">{t["desinscr"]}</a><br>
 Ebola Tracker · <a href="mailto:contact@ebola-tracker.org" style="color:#1B6C8C;">contact@ebola-tracker.org</a> · <a href="{ORIGINE}" style="color:#1B6C8C;">ebola-tracker.org</a></td></tr></table>
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
    """Cree la campagne Brevo d'une lettre ; sans liste (envoi test), elle
    n'a pas de destinataires : Brevo refuse une liste vide."""
    objet, apercu, corps = mail(num, lang)
    donnees = {"name": "Lettre %s (%s)%s" % (num, lang, "" if liste else " - test"), "subject": objet,
               "previewText": apercu, "sender": conf["expediteur"], "htmlContent": corps}
    # Le lien {{ unsubscribe }} mene au formulaire de la langue, pas a la
    # page Brevo par defaut (22 octobre 2026).
    page = (conf.get("desinscription") or {}).get(lang)
    if page:
        donnees["unsubscriptionPageId"] = page
    if liste:
        donnees["recipients"] = {"listIds": [liste]}
    return brevo(cle, "POST", "/emailCampaigns", donnees)["id"]


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
    listes = {k: v for k, v in (conf.get("listes") or {}).items() if v}
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
            if not abonnes(cle, liste):
                print("liste %s (%s) sans abonne : rien a envoyer" % (liste, lang))
                continue
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
