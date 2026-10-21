# -*- coding: utf-8 -*-
"""Mail d'alerte « nouveau SitRep » aux inscrits de la page Etre prevenu,
envoye par Brevo au meme moment que le mail de la Lettre (21 octobre 2026,
demande du proprietaire). Mise en page de la maquette tmp/proto-mail-1019 :
numero du bulletin, date des donnees, cas et deces avec le « + » du jour, un
bouton vers le site (pas vers la lettre).

Un envoi par langue, chacun a sa liste Brevo (site.brevoEnvoiAlerte dans
site/pages.json). data/envois-alerte.json garde le dernier numero envoye : un
SitRep ne part jamais deux fois, et un plus ancien jamais.

    python scripts/envoi_alerte.py --apercu          ecrit tmp/mail-alerte-<lang>.html
    python scripts/envoi_alerte.py --test ADRESSE    campagne + envoi test a cette adresse
    python scripts/envoi_alerte.py --envoi           envoi reel, si le SitRep est nouveau

Cle API, appels Brevo et attente de la mise en ligne : ceux d'envoi_lettre.py.
Sans cle ou sans listes : rien n'est envoye et le script sort sans erreur.
"""
import html, json, os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from envoi_lettre import ROOT, ORIGINE, CHEMIN, lire_json, cle_api, brevo, en_ligne, abonnes  # noqa: E402

ETAT = os.path.join(ROOT, "data", "envois-alerte.json")
SANS, SERIF = "Arial,Helvetica,sans-serif", "Georgia,'Times New Roman',serif"
MOIS = {"fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(),
        "en": "January February March April May June July August September October November December".split()}
T = {"fr": dict(objet="SitRep %s : %s cas, %s décès", apercu="+%s cas et +%s décès en 24 h, situation au %s.",
                titre="Nouveau SitRep n° %s", date="Situation au %s", cas="cas confirmés", dec="décès",
                jour="+%s en 24 h", bouton="Voir tous les détails sur le site", url=ORIGINE,
                source="Source : rapport de situation officiel de l'Institut national de santé publique (INSP) de la RDC.",
                pied="Vous recevez ce mail car vous êtes inscrit aux alertes d'ebola-tracker.org.", desinscr="Se désinscrire"),
     "en": dict(objet="SitRep %s: %s cases, %s deaths", apercu="+%s cases and +%s deaths in 24 h, as of %s.",
                titre="New SitRep no. %s", date="As of %s", cas="confirmed cases", dec="deaths",
                jour="+%s in 24 h", bouton="See all the details on the site", url=ORIGINE + "en/",
                source="Source: official situation report from the DRC National Institute of Public Health (INSP).",
                pied="You are receiving this email because you subscribed to ebola-tracker.org alerts.", desinscr="Unsubscribe")}


def nb(x, lang):
    return "{:,}".format(x or 0).replace(",", "\u202f" if lang == "fr" else ",")


def mail(lang):
    """(num, objet, apercu, html) du mail d'alerte du SitRep courant."""
    L = lire_json(os.path.join(ROOT, "data", "latest.json"))
    n, m, t = L["national"], L["meta"], T[lang]
    num, d = m["sitrepNumber"], date.fromisoformat(m["reportingDate"])
    jour = "%d %s %d" % (d.day, MOIS[lang][d.month - 1], d.year)
    objet = t["objet"] % (num, nb(n["confirmed"], lang), nb(n["deaths"], lang))
    apercu = t["apercu"] % (nb(n["newCases24h"], lang), nb(n["newDeaths24h"], lang), jour)

    def chiffre(val, lib, nouv, teinte):
        return ('<td width="50%%" valign="top" style="padding:18px 16px;border-top:3px solid %s;">'
                '<div style="font:700 34px/1.1 %s;letter-spacing:-.5px;color:%s;">%s</div>'
                '<div style="font:15px/1.4 %s;color:#4D473F;margin-top:4px;">%s</div>'
                '<div style="font:700 14px/1.4 %s;color:%s;margin-top:6px;">%s</div></td>'
                % (teinte, SANS, teinte, val, SANS, lib, SANS, teinte, t["jour"] % nouv))
    c1 = chiffre(nb(n["confirmed"], lang), t["cas"], nb(n["newCases24h"], lang), "#005E82")
    c2 = chiffre(nb(n["deaths"], lang), t["dec"], nb(n["newDeaths24h"], lang), "#993A2E")
    corps = f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(objet)}</title></head>
<body style="margin:0;padding:0;background:#F7F3EE;">
<div style="display:none;max-height:0;overflow:hidden;">{html.escape(apercu)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F7F3EE;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#FFFDFB;border:1px solid #DEDAD5;border-radius:14px;">
 <tr><td style="padding:22px 26px 0;font:700 15px {SANS};color:#1F1A13;">
  <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#C0503A;margin-right:7px;"></span>ebola-tracker<span style="color:#1B6C8C;">.org</span></td></tr>
 <tr><td style="padding:22px 26px 4px;">
  <div style="font:700 26px/1.2 {SERIF};color:#1F1A13;">{t["titre"] % num}</div>
  <div style="font:15px/1.5 {SANS};color:#5A544C;margin-top:6px;">{t["date"] % jour}</div></td></tr>
 <tr><td style="padding:16px 26px 6px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{c1}<td width="12"></td>{c2}</tr></table></td></tr>
 <tr><td style="padding:18px 26px 8px;"><a href="{t["url"]}" style="display:inline-block;background:#005073;color:#ffffff;font:700 15px {SANS};text-decoration:none;padding:13px 22px;border-radius:10px;">{t["bouton"]} →</a></td></tr>
 <tr><td style="padding:16px 26px 24px;font:13px/1.5 {SANS};color:#777068;">{html.escape(t["source"])}</td></tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;"><tr><td style="padding:16px 26px;font:12px/1.5 {SANS};color:#777068;text-align:center;">
 {t["pied"]} <a href="{{{{ unsubscribe }}}}" style="color:#1B6C8C;">{t["desinscr"]}</a><br>
 Ebola Tracker · <a href="mailto:contact@ebola-tracker.org" style="color:#1B6C8C;">contact@ebola-tracker.org</a> · <a href="{ORIGINE}" style="color:#1B6C8C;">ebola-tracker.org</a></td></tr></table>
</td></tr></table></body></html>"""
    return num, objet, apercu, corps


def campagne(cle, conf, lang, liste=None):
    num, objet, apercu, corps = mail(lang)
    donnees = {"name": "Alerte SitRep %s (%s)%s" % (num, lang, "" if liste else " - test"), "subject": objet,
               "previewText": apercu, "sender": conf["expediteur"], "htmlContent": corps}
    if liste:
        donnees["recipients"] = {"listIds": [liste]}
    return brevo(cle, "POST", "/emailCampaigns", donnees)["id"]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--apercu"
    if mode == "--apercu":
        for lang in T:
            num, objet, apercu, corps = mail(lang)
            sortie = os.path.join(ROOT, "tmp", "mail-alerte-%s.html" % lang)
            os.makedirs(os.path.dirname(sortie), exist_ok=True)
            with open(sortie, "w", encoding="utf-8") as f:
                f.write(corps)
            print(lang, "|", objet, "|", apercu, "->", sortie)
        return
    conf = json.load(open(os.path.join(ROOT, "site", "pages.json"), encoding="utf-8"))["site"].get("brevoEnvoiAlerte") or {}
    listes = {k: v for k, v in (conf.get("listes") or {}).items() if v}
    cle = cle_api()
    if not cle or not listes or not conf.get("expediteur"):
        print("Alerte SitRep non configuree (cle API, listes ou expediteur manquants) : rien n'est envoye.")
        return
    if mode == "--test":
        for lang in listes:
            cid = campagne(cle, conf, lang)
            brevo(cle, "POST", "/emailCampaigns/%d/sendTest" % cid, {"emailTo": [sys.argv[2]]})
            print("test", lang, "campagne", cid, "->", sys.argv[2])
        return
    if mode == "--envoi":
        num = lire_json(os.path.join(ROOT, "data", "latest.json"))["meta"]["sitrepNumber"]
        etat = lire_json(ETAT, {}) or {}
        if int(num) <= int(etat.get("dernier", 0)):
            print("Alerte du SitRep %s deja envoyee (dernier envoi : %s)." % (num, etat.get("dernier")))
            return
        # Le site doit montrer ce SitRep avant qu'on l'annonce : la lettre du
        # numero sert de temoin, comme pour le mail de la Lettre.
        if not en_ligne(ORIGINE + CHEMIN["fr"].replace("index.html", "") % num, num):
            sys.exit("Le SitRep %s n'est pas en ligne apres 30 minutes : rien n'est envoye." % num)
        envois = {}
        for lang, liste in listes.items():
            if not abonnes(cle, liste):
                print("liste %s (%s) sans abonne : rien a envoyer" % (liste, lang))
                continue
            cid = campagne(cle, conf, lang, liste)
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
