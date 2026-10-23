"""Mails d'inscription a La Lettre, modeles Brevo.

Mail d'accueil (23 octobre 2026) : envoye par Brevo une fois
l'inscription confirmee (double opt-in), en francais par le formulaire #3
(liste 3), en anglais par le formulaire #4 (liste 4, swahili compris).
Dessin : maquette 2 de tmp/proto-mail-accueil-1023 (en-tete LA LETTRE, mot
signe Pierre, sans bouton), meme enveloppe que le mail de la Lettre
(scripts/envoi_lettre.py).

Mail de confirmation du double opt-in (24 octobre 2026), a la place du
modele standard de Brevo : meme dessin, « Encore une etape », un bouton
dont le lien est la balise {{ doubleoptin }} (Brevo ne la remplit que lors
d'une vraie inscription : dans un envoi test, le bouton ne mene nulle
part). Modele etiquete « optin », sans lien de desinscription (la personne
n'est pas encore inscrite). Maquette : tmp/proto-mail-optin-1024.

    python scripts/mail_accueil.py --apercu          ecrit tmp/mail-<accueil|optin>-<lang>.html
    python scripts/mail_accueil.py --brevo           cree ou met a jour les quatre modeles Brevo
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
OPTIN = {"fr": dict(objet="Confirmez votre inscription à La Lettre", apercu="Encore une étape : un clic pour confirmer.",
                    titre="Encore une étape",
                    texte="Pour recevoir La Lettre à chaque nouveau bulletin de l’INSP, confirmez votre adresse en "
                          "cliquant sur le bouton ci-dessous.",
                    bouton="Confirmer mon inscription",
                    note="Si vous n’avez pas demandé cette inscription, ignorez simplement ce mail : vous ne recevrez rien."),
         "en": dict(objet="Confirm your subscription to The Letter", apercu="One more step: one click to confirm.",
                    titre="One more step",
                    texte="To receive The Letter with each new INSP bulletin, confirm your address by clicking the "
                          "button below.",
                    bouton="Confirm my subscription",
                    note="If you did not ask to subscribe, simply ignore this email: you will not receive anything.")}


def enveloppe(lang, objet, apercu, contenu, desinscription=True):
    """Le mail entier autour du contenu de la carte (lignes <tr>) : marque,
    carte au bandeau bleu et en-tete LA LETTRE, pied de page."""
    t, esc = T[lang], html.escape
    accueil = ORIGINE + t["accueil"]
    desinscr = (' · <a href="{{ unsubscribe }}" style="color:#1B6C8C;">%s</a>' % t["desinscr"]) if desinscription else ""
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(objet)}</title></head>
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
  <div style="font:italic 15px/1.4 {SERIF};color:{DIM};margin-top:12px;">{esc(t["sous"])}</div>
  <div style="border-bottom:3px double {LINE};margin-top:22px;"></div></td></tr>{contenu}
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;"><tr><td style="padding:16px 26px;font:12px/1.6 {SANS};color:{FAINT};text-align:center;">
 Ebola Tracker · <a href="mailto:{MAIL}" style="color:#1B6C8C;">{MAIL}</a> · <a href="{accueil}" style="color:#1B6C8C;white-space:nowrap;">ebola-tracker.org</a>{desinscr}</td></tr></table>
</td></tr></table></body></html>"""


def mail(lang):
    """(objet, html) du mail d'accueil."""
    t, esc = T[lang], html.escape
    contenu = "".join(f'\n <tr><td style="padding:{26 if i == 0 else 14}px 36px 0;font:17px/1.7 {SERIF};color:#2E2820;">{esc(p)}</td></tr>'
                      for i, p in enumerate(t["corps"]))
    contenu += (f'\n <tr><td style="padding:22px 36px 32px;font:17px/1.6 {SERIF};color:#2E2820;">{esc(t["salut"])}<br>'
                f'<span style="font-style:italic;font-size:21px;color:{INK};">Pierre</span></td></tr>')
    return t["objet"], enveloppe(lang, t["objet"], t["apercu"], contenu)


def mail_optin(lang):
    """(objet, html) du mail de confirmation du double opt-in."""
    o, esc = OPTIN[lang], html.escape
    contenu = (f'\n <tr><td style="padding:26px 36px 0;"><div style="font:600 30px/1.15 {SERIF};letter-spacing:-.4px;color:{INK};">{esc(o["titre"])}</div></td></tr>'
               f'\n <tr><td style="padding:12px 36px 0;font:17px/1.7 {SERIF};color:#2E2820;">{esc(o["texte"])}</td></tr>'
               f'\n <tr><td align="center" style="padding:24px 36px 0;"><a href="{{{{ doubleoptin }}}}" style="display:inline-block;background:#005073;'
               f'color:#ffffff;font:700 16px {SANS};text-decoration:none;padding:15px 28px;border-radius:10px;">{esc(o["bouton"])} →</a></td></tr>'
               f'\n <tr><td style="padding:24px 36px 30px;font:14px/1.6 {SANS};color:{FAINT};">{esc(o["note"])}</td></tr>')
    return o["objet"], enveloppe(lang, o["objet"], o["apercu"], contenu, desinscription=False)


# (cle dans data/mail-accueil.json, nom du modele Brevo, fonction, langue, etiquette)
MODELES = [(lang, "Accueil La Lettre (%s)" % lang, mail, lang, None) for lang in T] + \
          [("optin-" + lang, "Confirmation double opt-in La Lettre (%s)" % lang, mail_optin, lang, "optin") for lang in T]


def lire_etat():
    if os.path.exists(ETAT):
        with open(ETAT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    arg = sys.argv[1:]
    if arg[:1] == ["--apercu"]:
        for cle_etat, _, f_mail, lang, _ in MODELES:
            chemin = os.path.join(ROOT, "tmp", "mail-%s.html" % (cle_etat if "-" in cle_etat else "accueil-" + lang))
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(f_mail(lang)[1])
            print(chemin)
        return
    cle = cle_api()
    if not cle:
        sys.exit("Pas de cle API Brevo.")
    with open(os.path.join(ROOT, "site", "pages.json"), encoding="utf-8") as f:
        expediteur = json.load(f)["site"]["brevoEnvoiLettre"]["expediteur"]
    etat = lire_etat()
    if arg[:1] == ["--brevo"]:
        for cle_etat, nom, f_mail, lang, tag in MODELES:
            objet, corps = f_mail(lang)
            donnees = {"templateName": nom, "subject": objet, "htmlContent": corps,
                       "sender": expediteur, "replyTo": MAIL, "isActive": True}
            if tag:
                donnees["tag"] = tag
            if cle_etat in etat:
                brevo(cle, "PUT", "/smtp/templates/%s" % etat[cle_etat], donnees)
                print("modele %s mis a jour : %s" % (cle_etat, etat[cle_etat]))
            else:
                etat[cle_etat] = brevo(cle, "POST", "/smtp/templates", donnees)["id"]
                print("modele %s cree : %s" % (cle_etat, etat[cle_etat]))
        with open(ETAT, "w", encoding="utf-8") as f:
            json.dump(etat, f, indent=2)
            f.write("\n")
    elif arg[:1] == ["--test"] and len(arg) == 2:
        for cle_etat, *_ in MODELES:
            if cle_etat not in etat:
                sys.exit("Modele %s absent : lancer d'abord --brevo." % cle_etat)
            brevo(cle, "POST", "/smtp/templates/%s/sendTest" % etat[cle_etat], {"emailTo": [arg[1]]})
            print("test %s envoye (modele %s)" % (cle_etat, etat[cle_etat]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
