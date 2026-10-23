"""Mail d'accueil de La Lettre (23 octobre 2026) : envoye par Brevo une fois
l'inscription confirmee (double opt-in), en francais par le formulaire #3
(liste 3), en anglais par le formulaire #4 (liste 4, swahili compris).
Dessin : maquette 2 de tmp/proto-mail-accueil-1023 (en-tete LA LETTRE, mot
signe Pierre, sans bouton), meme enveloppe que le mail de la Lettre
(scripts/envoi_lettre.py).

    python scripts/mail_accueil.py --apercu          ecrit tmp/mail-accueil-<lang>.html
    python scripts/mail_accueil.py --brevo           cree ou met a jour les deux modeles Brevo
    python scripts/mail_accueil.py --test ADRESSE    envoie un test de chaque modele

Les identifiants des modeles sont gardes dans data/mail-accueil.json. Le
branchement sur les formulaires se fait dans l'interface Brevo (reglages du
double opt-in : mail de confirmation finale), l'API ne gerant pas les
formulaires.
"""
import html, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from envoi_lettre import ROOT, ORIGINE, FAVICON, SERIF, SANS, INK, DIM, FAINT, LINE, cle_api, brevo  # noqa: E402

ETAT = os.path.join(ROOT, "data", "mail-accueil.json")
MAIL = "contact@ebola-tracker.org"
T = {"fr": dict(objet="Bienvenue dans La Lettre", marque="La lettre",
                sous="Le suivi de l’épidémie d’Ebola, bulletin après bulletin",
                apercu="Merci pour votre inscription. Une question ? Répondez simplement à ce mail.",
                corps=["Bonjour,",
                       "Merci pour votre inscription à La Lettre d’ebola-tracker.org. Vous la recevrez chaque fois que l’INSP "
                       "publie un nouveau bulletin sur l’épidémie en RDC : un mail court, avec les chiffres du jour et "
                       "l’essentiel du bulletin.",
                       "Si vous avez une question, sur un chiffre, une source ou le site lui-même, répondez simplement à ce "
                       "mail. Je lis chaque message."],
                salut="Bien à vous,", desinscr="Se désinscrire", accueil=""),
     "en": dict(objet="Welcome to The Letter", marque="The letter",
                sous="Following the Ebola outbreak, bulletin by bulletin",
                apercu="Thank you for subscribing. Any questions? Just reply to this email.",
                corps=["Hello,",
                       "Thank you for subscribing to The Letter from ebola-tracker.org. You will receive it each time the "
                       "INSP publishes a new bulletin on the outbreak in the DRC: a short email with the day’s figures and "
                       "the key points of the bulletin.",
                       "If you have a question, about a figure, a source or the site itself, just reply to this email. "
                       "I read every message."],
                salut="Best regards,", desinscr="Unsubscribe", accueil="en/")}


def mail(lang):
    """(objet, html) du mail d'accueil."""
    t, esc = T[lang], html.escape
    accueil = ORIGINE + t["accueil"]
    para = "".join(f'\n <tr><td style="padding:{26 if i == 0 else 14}px 36px 0;font:17px/1.7 {SERIF};color:#2E2820;">{esc(p)}</td></tr>'
                   for i, p in enumerate(t["corps"]))
    corps = f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(t["objet"])}</title></head>
<body style="margin:0;padding:0;background:#F7F3EE;">
<div style="display:none;max-height:0;overflow:hidden;">{esc(t["apercu"])}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F7F3EE;"><tr><td align="center" style="padding:24px 10px;">
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 14px;"><tr>
 <td style="padding-right:9px;"><a href="{accueil}"><img src="{FAVICON}" width="24" height="24" alt="" style="display:block;border-radius:5px;"></a></td>
 <td><a href="{accueil}" style="font:700 17px/1.2 {SANS};letter-spacing:-.2px;color:{INK};text-decoration:none;">ebola-tracker<span style="color:#1B6C8C;">.org</span></a></td></tr></table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#FFFDFB;border:1px solid {LINE};border-radius:14px;">
 <tr><td style="height:10px;background:#005073;border-radius:14px 14px 0 0;font-size:0;line-height:0;">&nbsp;</td></tr>
 <tr><td align="center" style="padding:28px 24px 0;">
  <div style="font:700 40px/1 {SERIF};letter-spacing:5px;text-transform:uppercase;color:{INK};">{t["marque"]}</div>
  <div style="font:italic 15px/1.4 {SERIF};color:{DIM};margin-top:12px;">{esc(t["sous"])}</div>
  <div style="border-bottom:3px double {LINE};margin-top:22px;"></div></td></tr>{para}
 <tr><td style="padding:22px 36px 32px;font:17px/1.6 {SERIF};color:#2E2820;">{esc(t["salut"])}<br><span style="font-style:italic;font-size:21px;color:{INK};">Pierre</span></td></tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;"><tr><td style="padding:16px 26px;font:12px/1.6 {SANS};color:{FAINT};text-align:center;">
 Ebola Tracker · <a href="mailto:{MAIL}" style="color:#1B6C8C;">{MAIL}</a> · <a href="{accueil}" style="color:#1B6C8C;white-space:nowrap;">ebola-tracker.org</a> · <a href="{{{{ unsubscribe }}}}" style="color:#1B6C8C;">{t["desinscr"]}</a></td></tr></table>
</td></tr></table></body></html>"""
    return t["objet"], corps


def lire_etat():
    if os.path.exists(ETAT):
        with open(ETAT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    arg = sys.argv[1:]
    if arg[:1] == ["--apercu"]:
        for lang in T:
            chemin = os.path.join(ROOT, "tmp", "mail-accueil-%s.html" % lang)
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(mail(lang)[1])
            print(chemin)
        return
    cle = cle_api()
    if not cle:
        sys.exit("Pas de cle API Brevo.")
    with open(os.path.join(ROOT, "site", "pages.json"), encoding="utf-8") as f:
        expediteur = json.load(f)["site"]["brevoEnvoiLettre"]["expediteur"]
    etat = lire_etat()
    if arg[:1] == ["--brevo"]:
        for lang in T:
            objet, corps = mail(lang)
            donnees = {"templateName": "Accueil La Lettre (%s)" % lang, "subject": objet, "htmlContent": corps,
                       "sender": expediteur, "replyTo": MAIL, "isActive": True}
            if lang in etat:
                brevo(cle, "PUT", "/smtp/templates/%s" % etat[lang], donnees)
                print("modele %s mis a jour : %s" % (lang, etat[lang]))
            else:
                etat[lang] = brevo(cle, "POST", "/smtp/templates", donnees)["id"]
                print("modele %s cree : %s" % (lang, etat[lang]))
        with open(ETAT, "w", encoding="utf-8") as f:
            json.dump(etat, f, indent=2)
            f.write("\n")
    elif arg[:1] == ["--test"] and len(arg) == 2:
        for lang in T:
            if lang not in etat:
                sys.exit("Modele %s absent : lancer d'abord --brevo." % lang)
            brevo(cle, "POST", "/smtp/templates/%s/sendTest" % etat[lang], {"emailTo": [arg[1]]})
            print("test %s envoye (modele %s)" % (lang, etat[lang]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
